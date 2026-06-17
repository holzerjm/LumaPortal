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
LABEL_SIZE = os.getenv("LABEL_SIZE", "62red")
PRINTER_URI = os.getenv("PRINTER_URI", "")

# Server
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# Check-in
# Which Luma registration statuses are eligible to be found + checked in.
# Include pending_approval and waitlist so those guests can be approved/checked in
# at the door (see AUTO_APPROVE_ON_CHECKIN).
ALLOWED_STATUSES = [
    s.strip()
    for s in os.getenv(
        "ALLOWED_STATUSES", "approved,pending_approval,waitlist"
    ).split(",")
    if s.strip()
]


def _env_bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


# Approvals (writeback to Luma)
# When a pending_approval/waitlist guest checks in via the portal, also approve
# them in Luma ("Going"). Set false for an "approve first, then check in" workflow.
AUTO_APPROVE_ON_CHECKIN = _env_bool("AUTO_APPROVE_ON_CHECKIN", True)
# Whether Luma sends its standard approval email when we approve a guest.
APPROVE_SEND_EMAIL = _env_bool("APPROVE_SEND_EMAIL", True)
# Statuses the API can write (check-in is NOT writable — it has no status value).
WRITABLE_STATUSES = {"approved", "declined", "pending_approval", "waitlist"}

# Sync
SYNC_INTERVAL = int(os.getenv("SYNC_INTERVAL", "300"))  # seconds between auto-fetches from Luma

# Database
DB_PATH = DATA_DIR / "checkin.db"

# Badge dimensions — landscape: 100mm × 62mm at 300 DPI.
# Generated as 1182×696 (landscape), brother_ql rotate="auto" rotates to fit roll.
BADGE_WIDTH = 1182
BADGE_HEIGHT = 696
