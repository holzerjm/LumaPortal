import asyncio
import logging
from datetime import datetime, timezone

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from src.config import STATIC_DIR, EVENT_NAME, LUMA_API_KEY, SYNC_INTERVAL
from src import database as db
from src.routes.api import router as api_router, refresh_guest_cache
from src.routes.admin import router as admin_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

_sync_task: asyncio.Task | None = None
_fetch_task: asyncio.Task | None = None
last_sync_at: datetime | None = None


async def _background_sync():
    """Background task to sync check-ins to Luma API every 30 seconds."""
    from src.luma_client import sync_checkins

    while True:
        try:
            await sync_checkins()
        except Exception as e:
            logger.warning(f"Background sync error: {e}")
        await asyncio.sleep(30)


async def _background_fetch():
    """Background task to fetch latest guest list from Luma API at a configurable interval."""
    from src.luma_client import fetch_and_store_guests

    global last_sync_at
    while True:
        await asyncio.sleep(SYNC_INTERVAL)
        try:
            count = await fetch_and_store_guests()
            await refresh_guest_cache()
            last_sync_at = datetime.now(timezone.utc)
            logger.info(f"Auto-sync: refreshed {count} guests from Luma API")
        except Exception as e:
            logger.warning(f"Auto-sync fetch error: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _sync_task

    # Initialize database
    await db.init_db()
    logger.info("Database initialized")

    # Try to fetch guests from Luma API on startup
    global last_sync_at
    if LUMA_API_KEY:
        try:
            from src.luma_client import fetch_and_store_guests
            count = await fetch_and_store_guests()
            last_sync_at = datetime.now(timezone.utc)
            logger.info(f"Loaded {count} guests from Luma API")
        except Exception as e:
            logger.warning(f"Could not fetch from Luma API: {e}")

    # Refresh the in-memory guest cache
    await refresh_guest_cache()

    stats = await db.get_stats()
    logger.info(
        f"Ready: {stats['total_guests']} guests loaded, "
        f"{stats['checked_in']} already checked in"
    )

    # Start background tasks
    if LUMA_API_KEY:
        # Note: check-in sync back to Luma is disabled — the Luma API
        # does not support updating guest status (returns 400).
        # _sync_task = asyncio.create_task(_background_sync())
        if SYNC_INTERVAL > 0:
            _fetch_task = asyncio.create_task(_background_fetch())
            logger.info(f"Auto-sync enabled: fetching guests every {SYNC_INTERVAL}s")

    yield

    # Shutdown
    for task in (_sync_task, _fetch_task):
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass


app = FastAPI(title="Luma Check-In Portal", lifespan=lifespan)

# API routes
app.include_router(api_router)
app.include_router(admin_router)

# Static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
async def index():
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/admin")
async def admin_page():
    return FileResponse(str(STATIC_DIR / "admin.html"))
