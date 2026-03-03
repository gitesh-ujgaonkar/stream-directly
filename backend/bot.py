"""
Telegram bot handler — listens for forwarded videos and replies with the
streaming URL pointing at the Vercel frontend.
"""

from pyrogram import Client, filters
from pyrogram.types import Message
from config import API_ID, API_HASH, BOT_TOKEN, FRONTEND_URL

bot = Client(
    "stream_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    in_memory=True,
)


@bot.on_message(filters.video | filters.document)
async def handle_video(client: Client, message: Message):
    """When a user sends or forwards a video / document, reply with the web URL."""

    # Get file_id from the media
    media = message.video or message.document
    if media is None:
        return

    file_id = media.file_id
    file_name = getattr(media, "file_name", None) or "Untitled"
    file_size_mb = round((media.file_size or 0) / (1024 * 1024), 2)

    watch_url = f"{FRONTEND_URL}/watch?id={file_id}"

    text = (
        "🎬 **Your stream is ready!**\n\n"
        f"📄 **File:** `{file_name}`\n"
        f"📦 **Size:** `{file_size_mb} MB`\n\n"
        f"🔗 [▶️ Watch Now]({watch_url})\n\n"
        f"`{watch_url}`"
    )

    await message.reply_text(text, disable_web_page_preview=True)


@bot.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    await message.reply_text(
        "👋 **Welcome to Telegram Stream!**\n\n"
        "Send or forward any video file to me, and I'll give you a direct "
        "web streaming link.\n\n"
        "⚡ No downloads needed — watch instantly in your browser!",
    )
