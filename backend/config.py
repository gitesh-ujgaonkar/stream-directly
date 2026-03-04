import os
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

# Stream settings
CHUNK_SIZE = 256 * 1024          # 256 KB per chunk (small to avoid RAM spikes)
IDLE_TIMEOUT = 30                # seconds before killing an idle stream
MAX_CONCURRENT_STREAMS = 2       # max simultaneous streams (protect 512MB RAM)
RAM_LIMIT_PERCENT = 80           # refuse new streams above this RAM usage %
PORT = int(os.getenv("PORT", "10000"))
