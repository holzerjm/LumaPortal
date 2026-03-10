import logging
import httpx

from src.config import LUMA_API_KEY, LUMA_API_BASE, EVENT_API_ID
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
                reg_answers = guest_data.get("registration_answers", {})
                company = ""
                job_title = ""
                for question, answer in reg_answers.items():
                    q_lower = question.lower()
                    if "company" in q_lower or "university" in q_lower:
                        company = str(answer) if answer else ""
                    elif "job title" in q_lower:
                        job_title = str(answer) if answer else ""

                guests.append(
                    Guest(
                        api_id=guest_data.get("api_id", ""),
                        name=guest_data.get("name", "")
                        or f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip(),
                        first_name=user_data.get("first_name", ""),
                        last_name=user_data.get("last_name", ""),
                        email=user_data.get("email", ""),
                        phone=user_data.get("phone_number", ""),
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


async def sync_checkins():
    """Sync pending check-ins back to Luma API."""
    if not LUMA_API_KEY:
        return

    pending = await db.get_pending_sync()
    if not pending:
        return

    async with httpx.AsyncClient(timeout=15.0) as client:
        for item in pending:
            try:
                if item["action"] == "check_in":
                    resp = await client.post(
                        f"{LUMA_API_BASE}/event/update-guest-status",
                        headers=_headers(),
                        json={
                            "guest_api_id": item["guest_api_id"],
                            "status": "checked_in",
                        },
                    )
                    resp.raise_for_status()

                await db.mark_synced(item["id"])
                logger.info(f"Synced {item['action']} for {item['guest_api_id']}")

            except Exception as e:
                logger.warning(
                    f"Sync failed for {item['guest_api_id']}: {e}"
                )
