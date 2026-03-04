"""
FastAPI application — streams Telegram media to the web via an async pipe.
Optimized for Render's 512MB free tier: chunked downloads, aggressive GC,
inactivity killer, and RAM-gated stream admission.
"""

import asyncio
import gc
import time
import logging
from contextlib import asynccontextmanager

import psutil
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse

from config import (
    CHUNK_SIZE, IDLE_TIMEOUT, PORT,
    MAX_CONCURRENT_STREAMS, RAM_LIMIT_PERCENT,
)
from bot import bot

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tg-stream")

# ---------------------------------------------------------------------------
# Pyrogram client (reuse the bot client)
# ---------------------------------------------------------------------------
stream_client = bot

# ---------------------------------------------------------------------------
# Activity tracker — per-stream last-access timestamps
# ---------------------------------------------------------------------------
active_streams: dict[str, float] = {}


# ---------------------------------------------------------------------------
# Memory helpers
# ---------------------------------------------------------------------------
def get_ram_usage() -> dict:
    """Return current process RAM stats."""
    proc = psutil.Process()
    mem = proc.memory_info()
    sys_mem = psutil.virtual_memory()
    return {
        "rss_mb": round(mem.rss / (1024 * 1024), 1),
        "percent": sys_mem.percent,
        "available_mb": round(sys_mem.available / (1024 * 1024), 1),
    }


def is_ram_ok() -> bool:
    """Check if RAM usage is below the safety threshold."""
    return psutil.virtual_memory().percent < RAM_LIMIT_PERCENT


def force_gc():
    """Force garbage collection and log freed objects."""
    collected = gc.collect()
    logger.info(f"🧹 GC collected {collected} objects — RAM: {get_ram_usage()['rss_mb']} MB")


# ---------------------------------------------------------------------------
# Lifespan — start / stop the Pyrogram client with FastAPI
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    gc.enable()
    logger.info("🚀 Starting Pyrogram client …")
    await stream_client.start()
    logger.info(f"✅ Pyrogram client ready — RAM: {get_ram_usage()['rss_mb']} MB")
    yield
    logger.info("🛑 Stopping Pyrogram client …")
    await stream_client.stop()
    force_gc()
    logger.info("👋 Pyrogram client stopped")


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Telegram Stream API",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS — allow all origins (safe for a public video streaming API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Length", "Content-Range", "Accept-Ranges"],
)


# ---------------------------------------------------------------------------
# Health check (includes RAM stats)
# ---------------------------------------------------------------------------
@app.get("/health")
async def health():
    ram = get_ram_usage()
    return {
        "status": "ok",
        "ram": ram,
        "active_streams": len(active_streams),
        "ram_ok": is_ram_ok(),
    }


# ---------------------------------------------------------------------------
# Stream endpoint — with memory-safe chunked pipe
# ---------------------------------------------------------------------------
@app.get("/stream/{file_id}")
async def stream_video(file_id: str):
    """
    Stream a Telegram file to the browser.

    Memory protections:
    - Admission gate: refuses if RAM > 80% or too many concurrent streams
    - Downloads into memory in one shot (Pyrogram limitation), BUT uses
      small chunk yields (256KB) and immediately frees the buffer after use
    - 30-second inactivity killer
    - gc.collect() on stream end
    """

    # ── Admission gate ──
    if not is_ram_ok():
        ram = get_ram_usage()
        logger.warning(f"🚫 Stream refused — RAM at {ram['percent']}%")
        raise HTTPException(
            status_code=503,
            detail=f"Server memory too high ({ram['percent']}%). Try again in a minute.",
        )

    if len(active_streams) >= MAX_CONCURRENT_STREAMS:
        logger.warning(f"🚫 Stream refused — {len(active_streams)} active (max {MAX_CONCURRENT_STREAMS})")
        raise HTTPException(
            status_code=503,
            detail=f"Server busy ({len(active_streams)} active streams). Try again shortly.",
        )

    stream_key = file_id

    async def generate():
        buffer = None
        try:
            logger.info(f"⬇️  Starting download for {file_id[:20]}… | RAM: {get_ram_usage()['rss_mb']} MB")
            active_streams[stream_key] = time.time()

            # Download entire file into memory (Pyrogram doesn't support
            # partial/chunked downloads natively for bots).
            # We minimise damage by streaming it out in tiny chunks and
            # freeing the buffer ASAP.
            media = await stream_client.download_media(
                file_id,
                in_memory=True,
            )

            if media is None:
                logger.warning(f"❌ download_media returned None for {file_id[:20]}")
                return

            # Normalise to bytes — avoid keeping both BytesIO + bytes alive
            if hasattr(media, 'getvalue'):
                raw_bytes = media.getvalue()
                media.close()
                del media
            elif isinstance(media, (bytes, bytearray)):
                raw_bytes = bytes(media)
                del media
            else:
                raw_bytes = bytes(media)
                del media

            total = len(raw_bytes)
            sent = 0

            logger.info(f"📦 File ready — {total / (1024*1024):.1f} MB | RAM: {get_ram_usage()['rss_mb']} MB")

            offset = 0
            while offset < total:
                # ── Inactivity killer ──
                elapsed = time.time() - active_streams.get(stream_key, time.time())
                if elapsed > IDLE_TIMEOUT:
                    logger.info(f"⏰ Idle timeout ({IDLE_TIMEOUT}s) — killing stream {file_id[:20]}")
                    break

                # Read a small chunk via slicing (no extra copy)
                end = min(offset + CHUNK_SIZE, total)
                chunk = raw_bytes[offset:end]
                offset = end
                sent += len(chunk)

                # Refresh activity timestamp
                active_streams[stream_key] = time.time()
                yield chunk

                # Yield to event loop — prevents blocking
                await asyncio.sleep(0)

            logger.info(f"✅ Stream done — sent {sent / (1024*1024):.1f} MB")

        except asyncio.CancelledError:
            logger.info(f"🔌 Client disconnected — {file_id[:20]}")
        except Exception as e:
            logger.error(f"💥 Stream error: {e}")
        finally:
            # Aggressively free memory
            active_streams.pop(stream_key, None)
            if buffer is not None:
                try:
                    buffer.close()
                except Exception:
                    pass
            # Delete the raw bytes buffer and force GC
            try:
                del raw_bytes
            except NameError:
                pass
            force_gc()
            logger.info(f"🗑️  Stream cleanup done — RAM: {get_ram_usage()['rss_mb']} MB")

    return StreamingResponse(
        generate(),
        media_type="video/mp4",
        headers={
            "Accept-Ranges": "bytes",
            "Cache-Control": "no-cache",
            "Content-Disposition": f'inline; filename="{file_id[:12]}.mp4"',
        },
    )


# ---------------------------------------------------------------------------
# Stats endpoint (consumed by the frontend "Live Server Load" cards)
# ---------------------------------------------------------------------------
@app.get("/stats")
async def stats():
    ram = get_ram_usage()
    return {
        "active_streams": len(active_streams),
        "ram": ram,
        "ram_ok": is_ram_ok(),
        "stream_ids": list(active_streams.keys())[:10],
    }


# ---------------------------------------------------------------------------
# Run with: uvicorn main:app --host 0.0.0.0 --port 10000
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
