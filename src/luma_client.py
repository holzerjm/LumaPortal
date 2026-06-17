import asyncio
import logging
import httpx

from src.config import (
    LUMA_API_KEY,
    LUMA_API_BASE,
    EVENT_API_ID,
    APPROVE_SEND_EMAIL,
    WRITABLE_STATUSES,
)
from src.models import Guest
from src import database as db

logger = logging.getLogger(__name__)


def _headers() -> dict:
    return {
        "x-luma-api-key": LUMA_API_KEY,
        "accept": "application/json",
    }


async def fetch_guests(event_api_id: str = "") -> list[Guest]:
    """Fetch all guests from Luma API with cursor-based pagination."""
    if not LUMA_API_KEY:
        raise ValueError("LUMA_API_KEY not configured")

    event_id = event_api_id or EVENT_API_ID
    if not event_id:
        raise ValueError("EVENT_API_ID not configured")

    guests = []
    cursor = None

    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            params = {"event_api_id": event_id, "pagination_limit": 100}
            if cursor:
                params["pagination_cursor"] = cursor

            resp = await client.get(
                f"{LUMA_API_BASE}/event/get-guests",
                headers=_headers(),
                params=params,
            )
            resp.raise_for_status()
            data = resp.json()

            entries = data.get("entries", [])
            for entry in entries:
                guest_data = entry.get("guest", {})
                user_data = entry.get("user", {})

                # Extract registration answers for company/title
                reg_answers = guest_data.get("registration_answers", [])
                company = ""
                job_title = ""
                for qa in reg_answers:
                    if qa.get("question_type") == "company":
                        company = qa.get("answer_company", "") or ""
                        job_title = qa.get("answer_job_title", "") or ""
                        break
                # Fallback: search by label text
                if not company and not job_title:
                    for qa in reg_answers:
                        label = (qa.get("label") or "").lower()
                        if "company" in label or "university" in label:
                            answer = qa.get("answer", "")
                            company = str(answer) if answer else ""
                        elif "job title" in label:
                            answer = qa.get("answer", "")
                            job_title = str(answer) if answer else ""

                guests.append(
                    Guest(
                        api_id=guest_data.get("api_id", ""),
                        name=guest_data.get("name", "")
                        or guest_data.get("user_name", "")
                        or f"{guest_data.get('user_first_name', '')} {guest_data.get('user_last_name', '')}".strip(),
                        first_name=guest_data.get("user_first_name", "") or user_data.get("first_name", ""),
                        last_name=guest_data.get("user_last_name", "") or user_data.get("last_name", ""),
                        email=guest_data.get("email", "") or guest_data.get("user_email", "") or user_data.get("email", ""),
                        phone=guest_data.get("phone_number", "") or user_data.get("phone_number", ""),
                        company=company,
                        job_title=job_title,
                        ticket_type=guest_data.get("ticket_type_name", ""),
                        approval_status=guest_data.get("approval_status", "approved"),
                        data_source="luma_api",
                    )
                )

            # Check for next page
            cursor = data.get("next_cursor")
            if not cursor or not entries:
                break

    logger.info(f"Fetched {len(guests)} guests from Luma API")
    return guests


async def fetch_and_store_guests(event_api_id: str = "") -> int:
    """Fetch guests from Luma and store in database."""
    guests = await fetch_guests(event_api_id)
    if guests:
        await db.upsert_guests(guests)
    return len(guests)


async def update_guest_status(
    guest_api_id: str,
    status: str = "approved",
    *,
    event_api_id: str = "",
    send_email: bool | None = None,
    client: httpx.AsyncClient | None = None,
) -> None:
    """Write a guest's approval status to Luma.

    `status` must be one of approved | declined | pending_approval | waitlist.
    Check-in is NOT a writable status (Luma exposes it only as a read-only
    `checked_in_at` timestamp), so passing "checked_in" would 400 — this is why
    the old check-in write-back never worked.

    Uses POST /events/guests/update-status (flat schema: event_id, guest_id, status).
    Raises httpx.HTTPStatusError on non-2xx (e.g. 429), so callers can back off.
    """
    if status not in WRITABLE_STATUSES:
        raise ValueError(
            f"status must be one of {sorted(WRITABLE_STATUSES)}, got {status!r}"
        )
    if not LUMA_API_KEY:
        raise ValueError("LUMA_API_KEY not configured")

    event_id = event_api_id or EVENT_API_ID
    if not event_id:
        raise ValueError("EVENT_API_ID not configured")

    if send_email is None:
        send_email = APPROVE_SEND_EMAIL

    payload = {
        "event_id": event_id,
        "guest_id": guest_api_id,
        "status": status,
        "send_email": send_email,
    }

    own_client = client is None
    if own_client:
        client = httpx.AsyncClient(timeout=15.0)
    try:
        resp = await client.post(
            f"{LUMA_API_BASE}/events/guests/update-status",
            headers=_headers(),
            json=payload,
        )
        resp.raise_for_status()
    finally:
        if own_client:
            await client.aclose()


async def approve_guests(
    guest_api_ids: list[str],
    *,
    status: str = "approved",
    send_email: bool | None = None,
    throttle: float = 0.4,
) -> dict:
    """Approve many guests, one POST per guest (Luma has no bulk endpoint).

    Throttles between requests and retries on HTTP 429 to respect Luma's POST
    rate limit. Returns {"approved": [api_id, ...], "failed": [{"api_id", "error"}, ...]}.
    """
    approved: list[str] = []
    failed: list[dict] = []
    if not guest_api_ids:
        return {"approved": approved, "failed": failed}

    async with httpx.AsyncClient(timeout=15.0) as client:
        for i, gid in enumerate(guest_api_ids):
            ok = False
            for attempt in range(3):
                try:
                    await update_guest_status(
                        gid, status=status, send_email=send_email, client=client
                    )
                    ok = True
                    break
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 429 and attempt < 2:
                        retry_after = float(e.response.headers.get("retry-after", 5))
                        logger.warning(
                            f"Rate limited approving {gid}; backing off {retry_after}s"
                        )
                        await asyncio.sleep(retry_after)
                        continue
                    body = e.response.text[:200]
                    failed.append({"api_id": gid, "error": f"HTTP {e.response.status_code}: {body}"})
                    break
                except Exception as e:  # noqa: BLE001 — report, don't abort the batch
                    failed.append({"api_id": gid, "error": str(e)})
                    break
            if ok:
                approved.append(gid)
            # Spacing between guests (skip after the last) to stay under the POST budget.
            if throttle and i < len(guest_api_ids) - 1:
                await asyncio.sleep(throttle)

    logger.info(f"approve_guests: {len(approved)} approved, {len(failed)} failed")
    return {"approved": approved, "failed": failed}


async def sync_pending_approvals():
    """Drain queued guest approvals to Luma (e.g. door check-ins made while offline).

    Reuses the sync_queue: rows with action="approve" are pushed to Luma; any
    legacy rows (e.g. the old unusable "check_in" action) are simply cleared.
    """
    if not LUMA_API_KEY:
        return

    pending = await db.get_pending_sync()
    if not pending:
        return

    async with httpx.AsyncClient(timeout=15.0) as client:
        for item in pending:
            try:
                if item["action"] == "approve":
                    await update_guest_status(
                        item["guest_api_id"], status="approved", client=client
                    )
                    await db.set_approval_status(item["guest_api_id"], "approved")
                    logger.info(f"Synced approval for {item['guest_api_id']}")
                # Any other (legacy) action can't be synced — just clear it below.
                await db.mark_synced(item["id"])
            except Exception as e:
                logger.warning(f"Approval sync failed for {item['guest_api_id']}: {e}")
