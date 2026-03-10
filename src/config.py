import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
FONTS_DIR = BASE_DIR / "fonts"
STATIC_DIR = BASE_DIR / "static"

load_dotenv(BASE_DIR / ".env")

# Event
EVENT_NAME = os.getenv("EVENT_NAME", "Event Check-In")
EVENT_API_ID = os.getenv("EVENT_API_ID", "")

# Luma API
LUMA_API_KEY = os.getenv("LUMA_API_KEY", "")
LUMA_API_BASE = "https://public-api.luma.com/v1"

# Printer
PRINTER_MODEL = os.getenv("PRINTER_MODEL", "QL-820NWB")
LABEL_SIZE = os.getenv("LABEL_SIZE", "62x100")
PRINTER_URI = os.getenv("PRINTER_URI", "")

# Server
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# Check-in
ALLOWED_STATUSES = [
    s.strip()
    for s in os.getenv("ALLOWED_STATUSES", "approved,pending_approval").split(",")
]

# Sync
SYNC_INTERVAL = int(os.getenv("SYNC_INTERVAL", "300"))  # seconds between auto-fetches from Luma

# Database
DB_PATH = DATA_DIR / "checkin.db"

# Badge dimensions (62mm x 100mm at 300 DPI)
BADGE_WIDTH = 732
BADGE_HEIGHT = 1182
