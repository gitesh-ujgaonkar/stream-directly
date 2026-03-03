import os
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

# Stream settings
CHUNK_SIZE = 512 * 1024          # 512 KB per chunk
IDLE_TIMEOUT = 30                # seconds before closing an idle stream
PORT = int(os.getenv("PORT", "10000"))
