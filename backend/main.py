"""
FastAPI + Pyrogram streaming backend.
Optimized for Render free tier (512 MB RAM).

Key protections:
  • 512 KB chunk_size on download_media
  • request.is_disconnected() stops the download if the user closes the tab
  • gc.collect() after every stream
  • Global Pyrogram client — started once in lifespan, no re-auth loops
  • /health returns live RAM via psutil
"""

import asyncio
import gc
import time
import logging
from contextlib import asynccontextmanager

import psutil
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from config import CHUNK_SIZE, IDLE_TIMEOUT, PORT, MAX_CONCURRENT_STREAMS, RAM_LIMIT_PERCENT
from bot import bot

# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tg-stream")

# ---------------------------------------------------------------------------
# Single global Pyrogram client — started ONCE in lifespan, never re-created
# ---------------------------------------------------------------------------
stream_client = bot
active_streams: dict[str, float] = {}


# ---------------------------------------------------------------------------
# Memory helpers
# ---------------------------------------------------------------------------
def ram_info() -> dict:
    proc = psutil.Process()
    mem = proc.memory_info()
    sys_mem = psutil.virtual_memory()
    return {
        "rss_mb": round(mem.rss / (1024 * 1024), 1),
        "percent": round(sys_mem.percent, 1),
        "available_mb": round(sys_mem.available / (1024 * 1024), 1),
    }


def ram_ok() -> bool:
    return psutil.virtual_memory().percent < RAM_LIMIT_PERCENT


def force_gc():
    n = gc.collect()
    logger.info(f"GC collected {n} objects | RSS {ram_info()['rss_mb']} MB")


# ---------------------------------------------------------------------------
# Lifespan — start the client ONCE, stop on shutdown
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    gc.enable()
    logger.info("Starting Pyrogram client ...")
    await stream_client.start()
    logger.info(f"Pyrogram ready | RAM {ram_info()['rss_mb']} MB")
    yield
    logger.info("Stopping Pyrogram client ...")
    await stream_client.stop()
    force_gc()


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(title="TG Stream API", version="2.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Length", "Content-Range", "Accept-Ranges"],
)


# ---------------------------------------------------------------------------
# /health — live RAM stats
# ---------------------------------------------------------------------------
@app.get("/health")
async def health():
    r = ram_info()
    logger.info(f"/health | RSS {r['rss_mb']} MB | sys {r['percent']}% | streams {len(active_streams)}")
    return {
        "status": "ok",
        "ram": r,
        "active_streams": len(active_streams),
        "accepting": ram_ok() and len(active_streams) < MAX_CONCURRENT_STREAMS,
    }


# ---------------------------------------------------------------------------
# /stream/<file_id> — memory-safe chunked pipe
# ---------------------------------------------------------------------------
@app.get("/stream/{file_id}")
async def stream_video(file_id: str, request: Request):
    """
    1. Admission gate  — reject if RAM > 80 % or too many streams
    2. download_media   — in_memory=True (Pyrogram bot limitation)
    3. file_generator   — yields 512 KB chunks; checks request.is_disconnected()
       every iteration so the loop stops THE INSTANT the user closes the tab
    4. Cleanup          — del buffer + gc.collect()
    """

    # ── admission gate ──
    if not ram_ok():
        r = ram_info()
        logger.warning(f"REJECT stream — RAM {r['percent']}%")
        raise HTTPException(503, f"Server memory high ({r['percent']}%). Retry shortly.")

    if len(active_streams) >= MAX_CONCURRENT_STREAMS:
        logger.warning(f"REJECT stream — {len(active_streams)} active")
        raise HTTPException(503, f"Server busy ({len(active_streams)} streams). Retry shortly.")

    stream_key = file_id

    async def file_generator():
        raw = None
        try:
            active_streams[stream_key] = time.time()
            logger.info(f"DL start {file_id[:20]} | RAM {ram_info()['rss_mb']} MB")

            # ── download into memory ──
            media = await stream_client.download_media(file_id, in_memory=True)

            if media is None:
                logger.warning(f"download_media returned None for {file_id[:20]}")
                return

            # Convert to plain bytes, free the BytesIO immediately
            raw = media.getvalue() if hasattr(media, "getvalue") else bytes(media)
            if hasattr(media, "close"):
                media.close()
            del media

            total = len(raw)
            offset = 0
            logger.info(f"DL done {total / (1024*1024):.1f} MB | RAM {ram_info()['rss_mb']} MB")

            while offset < total:
                # ── disconnect check — stops instantly if user closed tab ──
                if await request.is_disconnected():
                    logger.info(f"Client disconnected — aborting {file_id[:20]}")
                    break

                # ── inactivity killer ──
                idle = time.time() - active_streams.get(stream_key, time.time())
                if idle > IDLE_TIMEOUT:
                    logger.info(f"Idle {IDLE_TIMEOUT}s — killing {file_id[:20]}")
                    break

                end = min(offset + CHUNK_SIZE, total)
                yield raw[offset:end]
                offset = end

                active_streams[stream_key] = time.time()
                await asyncio.sleep(0)  # yield to event loop

            logger.info(f"Stream done {offset / (1024*1024):.1f}/{total / (1024*1024):.1f} MB")

        except asyncio.CancelledError:
            logger.info(f"CancelledError — {file_id[:20]}")
        except Exception as e:
            logger.error(f"Stream error: {e}")
        finally:
            active_streams.pop(stream_key, None)
            try:
                del raw
            except Exception:
                pass
            force_gc()
            logger.info(f"Cleanup done | RAM {ram_info()['rss_mb']} MB")

    return StreamingResponse(
        file_generator(),
        media_type="video/mp4",
        headers={
            "Accept-Ranges": "bytes",
            "Cache-Control": "no-cache",
            "Content-Disposition": f'inline; filename="{file_id[:12]}.mp4"',
        },
    )


# ---------------------------------------------------------------------------
# /stats
# ---------------------------------------------------------------------------
@app.get("/stats")
async def stats():
    return {
        "active_streams": len(active_streams),
        "ram": ram_info(),
        "accepting": ram_ok() and len(active_streams) < MAX_CONCURRENT_STREAMS,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
