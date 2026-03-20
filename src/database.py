import aiosqlite
from datetime import datetime, timezone
from pathlib import Path

from src.config import DB_PATH
from src.models import Guest

SCHEMA = """
CREATE TABLE IF NOT EXISTS guests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    api_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    first_name TEXT DEFAULT '',
    last_name TEXT DEFAULT '',
    email TEXT DEFAULT '',
    phone TEXT DEFAULT '',
    company TEXT DEFAULT '',
    job_title TEXT DEFAULT '',
    ticket_type TEXT DEFAULT '',
    approval_status TEXT DEFAULT 'approved',
    checked_in_at TIMESTAMP,
    checked_in_by TEXT,
    badge_printed_at TIMESTAMP,
    data_source TEXT DEFAULT 'csv',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sync_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guest_api_id TEXT NOT NULL,
    action TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    synced_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS event_config (
    key TEXT PRIMARY KEY,
    value TEXT
);
"""


async def get_db() -> aiosqlite.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = await aiosqlite.connect(str(DB_PATH))
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    return db


async def init_db():
    db = await get_db()
    try:
        await db.executescript(SCHEMA)
        await db.commit()
    finally:
        await db.close()


async def upsert_guest(guest: Guest):
    db = await get_db()
    try:
        await db.execute(
            """INSERT INTO guests (api_id, name, first_name, last_name, email, phone,
               company, job_title, ticket_type, approval_status, checked_in_at, data_source)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(api_id) DO UPDATE SET
               name=excluded.name, first_name=excluded.first_name,
               last_name=excluded.last_name, email=excluded.email,
               phone=excluded.phone, company=excluded.company,
               job_title=excluded.job_title, ticket_type=excluded.ticket_type,
               approval_status=excluded.approval_status,
               data_source=excluded.data_source""",
            (
                guest.api_id, guest.name, guest.first_name, guest.last_name,
                guest.email, guest.phone, guest.company, guest.job_title,
                guest.ticket_type, guest.approval_status,
                guest.checked_in_at.isoformat() if guest.checked_in_at else None,
                guest.data_source,
            ),
        )
        await db.commit()
    finally:
        await db.close()


async def upsert_guests(guests: list[Guest]):
    db = await get_db()
    try:
        await db.executemany(
            """INSERT INTO guests (api_id, name, first_name, last_name, email, phone,
               company, job_title, ticket_type, approval_status, checked_in_at, data_source)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(api_id) DO UPDATE SET
               name=excluded.name, first_name=excluded.first_name,
               last_name=excluded.last_name, email=excluded.email,
               phone=excluded.phone, company=excluded.company,
               job_title=excluded.job_title, ticket_type=excluded.ticket_type,
               approval_status=excluded.approval_status,
               data_source=excluded.data_source""",
            [
                (
                    g.api_id, g.name, g.first_name, g.last_name,
                    g.email, g.phone, g.company, g.job_title,
                    g.ticket_type, g.approval_status,
                    g.checked_in_at.isoformat() if g.checked_in_at else None,
                    g.data_source,
                )
                for g in guests
            ],
        )
        await db.commit()
    finally:
        await db.close()


async def get_all_guests(allowed_statuses: list[str] | None = None) -> list[Guest]:
    db = await get_db()
    try:
        if allowed_statuses:
            placeholders = ",".join("?" for _ in allowed_statuses)
            cursor = await db.execute(
                f"SELECT * FROM guests WHERE approval_status IN ({placeholders}) ORDER BY name",
                allowed_statuses,
            )
        else:
            cursor = await db.execute("SELECT * FROM guests ORDER BY name")
        rows = await cursor.fetchall()
        return [_row_to_guest(row) for row in rows]
    finally:
        await db.close()


async def get_guest(api_id: str) -> Guest | None:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM guests WHERE api_id = ?", (api_id,))
        row = await cursor.fetchone()
        return _row_to_guest(row) if row else None
    finally:
        await db.close()


async def check_in_guest(api_id: str, checked_in_by: str = "self") -> Guest | None:
    now = datetime.now(timezone.utc)
    db = await get_db()
    try:
        await db.execute(
            "UPDATE guests SET checked_in_at = ?, checked_in_by = ? WHERE api_id = ?",
            (now.isoformat(), checked_in_by, api_id),
        )
        # Queue sync to Luma
        await db.execute(
            "INSERT INTO sync_queue (guest_api_id, action) VALUES (?, ?)",
            (api_id, "check_in"),
        )
        await db.commit()
        cursor = await db.execute("SELECT * FROM guests WHERE api_id = ?", (api_id,))
        row = await cursor.fetchone()
        return _row_to_guest(row) if row else None
    finally:
        await db.close()


async def undo_check_in(api_id: str) -> Guest | None:
    db = await get_db()
    try:
        await db.execute(
            "UPDATE guests SET checked_in_at = NULL, checked_in_by = NULL, badge_printed_at = NULL WHERE api_id = ?",
            (api_id,),
        )
        await db.commit()
        cursor = await db.execute("SELECT * FROM guests WHERE api_id = ?", (api_id,))
        row = await cursor.fetchone()
        return _row_to_guest(row) if row else None
    finally:
        await db.close()


async def mark_badge_printed(api_id: str):
    now = datetime.now(timezone.utc)
    db = await get_db()
    try:
        await db.execute(
            "UPDATE guests SET badge_printed_at = ? WHERE api_id = ?",
            (now.isoformat(), api_id),
        )
        await db.commit()
    finally:
        await db.close()


async def get_stats(allowed_statuses: list[str] | None = None) -> dict:
    db = await get_db()
    try:
        if allowed_statuses:
            placeholders = ",".join("?" for _ in allowed_statuses)
            where = f"WHERE approval_status IN ({placeholders})"
            cursor = await db.execute(
                f"SELECT COUNT(*) FROM guests {where}", allowed_statuses
            )
            total = (await cursor.fetchone())[0]
            cursor = await db.execute(
                f"SELECT COUNT(*) FROM guests {where} AND checked_in_at IS NOT NULL",
                allowed_statuses,
            )
            checked_in = (await cursor.fetchone())[0]
        else:
            cursor = await db.execute("SELECT COUNT(*) FROM guests")
            total = (await cursor.fetchone())[0]
            cursor = await db.execute(
                "SELECT COUNT(*) FROM guests WHERE checked_in_at IS NOT NULL"
            )
            checked_in = (await cursor.fetchone())[0]
        return {
            "total_guests": total,
            "checked_in": checked_in,
            "remaining": total - checked_in,
        }
    finally:
        await db.close()


async def get_pending_sync() -> list[dict]:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM sync_queue WHERE synced_at IS NULL ORDER BY created_at"
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def mark_synced(sync_id: int):
    now = datetime.now(timezone.utc)
    db = await get_db()
    try:
        await db.execute(
            "UPDATE sync_queue SET synced_at = ? WHERE id = ?",
            (now.isoformat(), sync_id),
        )
        await db.commit()
    finally:
        await db.close()


async def clear_all_guests():
    db = await get_db()
    try:
        await db.execute("DELETE FROM guests")
        await db.execute("DELETE FROM sync_queue")
        await db.commit()
    finally:
        await db.close()


def _row_to_guest(row) -> Guest:
    return Guest(
        id=row["id"],
        api_id=row["api_id"],
        name=row["name"],
        first_name=row["first_name"] or "",
        last_name=row["last_name"] or "",
        email=row["email"] or "",
        phone=row["phone"] or "",
        company=row["company"] or "",
        job_title=row["job_title"] or "",
        ticket_type=row["ticket_type"] or "",
        approval_status=row["approval_status"] or "",
        checked_in_at=datetime.fromisoformat(row["checked_in_at"])
        if row["checked_in_at"]
        else None,
        checked_in_by=row["checked_in_by"],
        badge_printed_at=datetime.fromisoformat(row["badge_printed_at"])
        if row["badge_printed_at"]
        else None,
        data_source=row["data_source"] or "csv",
        created_at=datetime.fromisoformat(row["created_at"])
        if row["created_at"]
        else None,
    )
