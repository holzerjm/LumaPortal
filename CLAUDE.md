# LumaPortal - Event Check-In Portal

Web-based check-in portal for Luma.com events with badge printing.

## Quick Start

```bash
# Install dependencies
uv sync

# Copy and configure environment
cp .env.example .env
# Edit .env with your event name, Luma API key, printer settings

# Run the server
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

Then open:
- **Check-in page**: http://localhost:8000
- **Admin dashboard**: http://localhost:8000/admin

## Development Commands

- **Run server**: `uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload`
- **Run tests**: `uv run pytest tests/`
- **Add dependency**: `uv add <package>`

## Architecture

- **Backend**: Python FastAPI + SQLite (via aiosqlite)
- **Frontend**: Vanilla HTML/CSS/JS with Fuse.js for client-side fuzzy search
- **Badge rendering**: Pillow (300 DPI PNG for thermal labels)
- **Printer**: Brother QL via `brother_ql` library (USB)
- **Luma API**: httpx async client — background guest-list fetch + approval write-back

## Key Files

- `src/main.py` — FastAPI app entry point, lifespan, background sync
- `src/routes/api.py` — Public check-in API (search, check-in, stats)
- `src/routes/admin.py` — Admin API (CSV upload, force check-in, reprint)
- `src/database.py` — SQLite schema and CRUD operations
- `src/search.py` — Fuzzy name matching with thefuzz
- `src/badge.py` — Badge image generation with Pillow
- `src/printer.py` — Brother QL printer interface
- `src/luma_client.py` — Luma API wrapper with pagination
- `src/csv_import.py` — Luma CSV export parser
- `static/js/checkin.js` — Check-in page 5-screen state machine
- `static/js/admin.js` — Admin dashboard logic

## Data Flow

1. Load guests from CSV upload or Luma API → SQLite (includes approval_status: approved / pending_approval / waitlist)
2. Attendee scans QR → opens check-in page → types name
3. Fuse.js fuzzy search matches against cached guest list
4. Attendee confirms → (if pending/waitlist and AUTO_APPROVE_ON_CHECKIN, approve in Luma) → server marks checked in locally → generates badge PNG → prints
5. Background task drains queued guest **approvals** to Luma every 30s

## Approvals vs. check-in (important)

The Luma public API has **no check-in write endpoint** — `update-guest-status` only
accepts `approved | declined | pending_approval | waitlist`. So:

- **Approvals DO sync to Luma.** Admin "Approve Pending/Waitlist" (bulk + per-row) and
  door auto-approve call `POST /v1/events/guests/update-status` with `status="approved"`.
- **Check-in is LOCAL-ONLY.** The portal is the source of truth for attendance; check-ins
  are stored in `data/checkin.db` and never appear on the Luma dashboard. Use the admin
  **Export CSV** for the attendance record. (The old check-in write-back was removed — it
  always 400'd because `checked_in` is not a valid Luma status.)
