from fastapi import APIRouter, HTTPException

from src import database as db
from src.models import CheckInRequest, CheckInResponse, SearchResult
from src.search import search_guests

router = APIRouter(prefix="/api")

# In-memory guest cache for fast search
_guest_cache: list = []


async def refresh_guest_cache():
    global _guest_cache
    _guest_cache = await db.get_all_guests()


@router.get("/search")
async def search(q: str = "") -> list[SearchResult]:
    if not _guest_cache:
        await refresh_guest_cache()
    return search_guests(q, _guest_cache)


@router.get("/guests")
async def list_guests():
    """Return all guests for client-side Fuse.js search."""
    guests = await db.get_all_guests()
    return [
        {
            "api_id": g.api_id,
            "name": g.name,
            "first_name": g.first_name,
            "last_name": g.last_name,
            "email": g.email,
            "company": g.company,
            "job_title": g.job_title,
            "checked_in": g.checked_in_at is not None,
            "checked_in_at": g.checked_in_at.isoformat() if g.checked_in_at else None,
        }
        for g in guests
    ]


@router.get("/guest/{api_id}")
async def get_guest(api_id: str):
    guest = await db.get_guest(api_id)
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    return guest


@router.post("/checkin")
async def check_in(req: CheckInRequest) -> CheckInResponse:
    guest = await db.get_guest(req.api_id)
    if not guest:
        return CheckInResponse(status="not_found", message="Guest not found")

    if guest.checked_in_at:
        return CheckInResponse(
            status="duplicate",
            name=guest.name,
            message=f"Already checked in at {guest.checked_in_at.strftime('%I:%M %p')}",
            checked_in_at=guest.checked_in_at,
        )

    updated = await db.check_in_guest(req.api_id, checked_in_by="self")
    if not updated:
        return CheckInResponse(status="error", message="Check-in failed")

    # Trigger badge print (non-blocking)
    from src.badge import generate_badge_for_guest
    from src.printer import print_badge_async

    try:
        img = generate_badge_for_guest(updated)
        await print_badge_async(img, updated.api_id)
    except Exception as e:
        # Log but don't fail the check-in
        import logging
        logging.getLogger(__name__).warning(f"Badge print failed for {req.api_id}: {e}")

    await refresh_guest_cache()

    return CheckInResponse(
        status="success",
        name=updated.name,
        message=f"Welcome, {updated.first_name or updated.name}!",
        checked_in_at=updated.checked_in_at,
    )


@router.get("/stats")
async def stats():
    s = await db.get_stats()
    from src.config import EVENT_NAME, LUMA_API_KEY, SYNC_INTERVAL
    s["event_name"] = EVENT_NAME
    s["auto_sync_enabled"] = bool(LUMA_API_KEY) and SYNC_INTERVAL > 0
    s["sync_interval"] = SYNC_INTERVAL
    return s
