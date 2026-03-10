import io
from fastapi import APIRouter, UploadFile, File, HTTPException

from src import database as db
from src.csv_import import parse_csv
from src.models import CheckInResponse
from src.routes.api import refresh_guest_cache

router = APIRouter(prefix="/admin/api")


@router.post("/upload-csv")
async def upload_csv(file: UploadFile = File(...)):
    content = await file.read()
    text = content.decode("utf-8-sig")
    guests = parse_csv(text)
    if not guests:
        raise HTTPException(status_code=400, detail="No guests found in CSV")
    await db.upsert_guests(guests)
    await refresh_guest_cache()
    return {"imported": len(guests)}


@router.get("/guests")
async def admin_list_guests():
    guests = await db.get_all_guests()
    return [
        {
            "api_id": g.api_id,
            "name": g.name,
            "company": g.company,
            "job_title": g.job_title,
            "email": g.email,
            "approval_status": g.approval_status,
            "checked_in_at": g.checked_in_at.isoformat() if g.checked_in_at else None,
            "checked_in_by": g.checked_in_by,
            "badge_printed_at": g.badge_printed_at.isoformat() if g.badge_printed_at else None,
        }
        for g in guests
    ]


@router.post("/force-checkin/{api_id}")
async def force_checkin(api_id: str) -> CheckInResponse:
    guest = await db.get_guest(api_id)
    if not guest:
        return CheckInResponse(status="not_found", message="Guest not found")

    updated = await db.check_in_guest(api_id, checked_in_by="staff")
    if not updated:
        return CheckInResponse(status="error", message="Check-in failed")

    # Print badge
    from src.badge import generate_badge_for_guest
    from src.printer import print_badge_async

    try:
        img = generate_badge_for_guest(updated)
        await print_badge_async(img, updated.api_id)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Badge print failed: {e}")

    await refresh_guest_cache()
    return CheckInResponse(
        status="success",
        name=updated.name,
        message=f"Checked in {updated.name}",
        checked_in_at=updated.checked_in_at,
    )


@router.post("/undo-checkin/{api_id}")
async def undo_checkin(api_id: str):
    guest = await db.undo_check_in(api_id)
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    await refresh_guest_cache()
    return {"status": "ok", "name": guest.name}


@router.post("/reprint/{api_id}")
async def reprint_badge(api_id: str):
    guest = await db.get_guest(api_id)
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")

    from src.badge import generate_badge_for_guest
    from src.printer import print_badge_async

    img = generate_badge_for_guest(guest)
    await print_badge_async(img, guest.api_id)
    return {"status": "ok", "name": guest.name}


@router.get("/printer-status")
async def printer_status():
    from src.printer import check_printer_status
    return check_printer_status()


@router.post("/sync-luma")
async def sync_luma():
    from datetime import datetime, timezone
    from src.luma_client import fetch_and_store_guests
    import src.main as main_module
    try:
        count = await fetch_and_store_guests()
        await refresh_guest_cache()
        main_module.last_sync_at = datetime.now(timezone.utc)
        return {"status": "ok", "synced": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear-data")
async def clear_data():
    await db.clear_all_guests()
    await refresh_guest_cache()
    return {"status": "ok"}
