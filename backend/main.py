"""
FastAPI application — streams Telegram media to the web via an async pipe.
No files are saved to disk; everything flows through memory.
"""

import asyncio
import time
import logging
from io import BytesIO
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse

from config import API_ID, API_HASH, BOT_TOKEN, FRONTEND_URL, CHUNK_SIZE, IDLE_TIMEOUT, PORT
from bot import bot

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tg-stream")

# ---------------------------------------------------------------------------
# Pyrogram user-bot client (shares credentials with bot but runs as a
# separate client so streaming and bot commands don't block each other)
# ---------------------------------------------------------------------------
stream_client = bot  # reuse the same bot client for simplicity

# ---------------------------------------------------------------------------
# Activity tracker — per-stream last-access timestamps
# ---------------------------------------------------------------------------
active_streams: dict[str, float] = {}


# ---------------------------------------------------------------------------
# Lifespan — start / stop the Pyrogram client with FastAPI
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting Pyrogram client …")
    await stream_client.start()
    logger.info("✅ Pyrogram client ready")
    yield
    logger.info("🛑 Stopping Pyrogram client …")
    await stream_client.stop()
    logger.info("👋 Pyrogram client stopped")


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Telegram Stream API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow the Vercel frontend (and localhost for dev)
origins = [
    FRONTEND_URL,
    "http://localhost:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health")
async def health():
    return {"status": "ok", "uptime": time.strftime("%H:%M:%S")}


# ---------------------------------------------------------------------------
# Stream endpoint
# ---------------------------------------------------------------------------
@app.get("/stream/{file_id}")
async def stream_video(file_id: str):
    """
    Download the Telegram file identified by *file_id* into memory and
    stream it back to the client as chunked video/mp4.

    An **activity monitor** closes the generator if no chunk is consumed
    for IDLE_TIMEOUT seconds (saves server resources on abandoned tabs).
    """

    stream_key = file_id

    async def generate():
        try:
            logger.info(f"⬇️  Starting download for {file_id[:20]}…")
            active_streams[stream_key] = time.time()

            # Download entire file into a BytesIO buffer (in-memory)
            media = await stream_client.download_media(
                file_id,
                in_memory=True,
            )

            if media is None:
                logger.warning(f"❌ download_media returned None for {file_id[:20]}")
                return

            # media is a BytesIO object — seek to start
            if isinstance(media, BytesIO):
                buffer = media
            else:
                buffer = BytesIO(media)

            buffer.seek(0)
            total = buffer.getbuffer().nbytes
            sent = 0

            logger.info(f"📦 File ready — {total / (1024*1024):.1f} MB, streaming …")

            while True:
                # ---- activity monitor ----
                elapsed = time.time() - active_streams.get(stream_key, time.time())
                if elapsed > IDLE_TIMEOUT:
                    logger.info(f"⏰ Idle timeout ({IDLE_TIMEOUT}s) — closing stream {file_id[:20]}")
                    break

                chunk = buffer.read(CHUNK_SIZE)
                if not chunk:
                    break

                sent += len(chunk)
                active_streams[stream_key] = time.time()  # refresh on every chunk sent
                yield chunk

                # Small sleep to prevent CPU-spin and allow cooperative scheduling
                await asyncio.sleep(0)

            logger.info(f"✅ Stream complete — sent {sent / (1024*1024):.1f} MB")

        except Exception as e:
            logger.error(f"💥 Stream error: {e}")
        finally:
            active_streams.pop(stream_key, None)

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
    return {
        "active_streams": len(active_streams),
        "stream_ids": list(active_streams.keys())[:10],  # top 10 only
    }


# ---------------------------------------------------------------------------
# Run with: uvicorn main:app --host 0.0.0.0 --port 10000
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
