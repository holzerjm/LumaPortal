# Release Notes

## v0.2.0 — March 11, 2026

### Printing Overhaul
- **Direct USB printing** — Bypasses CUPS entirely and sends raster data directly to the Brother QL-820NWB via pyusb. Eliminates "Install an address label" errors and CUPS job queue stalls.
- **Two-color raster format** — The QL-820NWB requires `red=True` (two-color raster mode) even for black-only DK-2205 rolls. Previous single-color mode caused "Check the print data" errors.
- **Reliable consecutive prints** — USB interface is now properly released after each print (`usb.util.dispose_resources`), fixing "Access denied (insufficient permissions)" errors on the second and subsequent prints.
- **Stale status draining** — Reads and discards any leftover status bytes from the printer before sending new data, preventing corrupted print sessions.

### Badge Design
- **Landscape layout** — Badges now print in landscape orientation (100mm × 62mm) instead of portrait, matching standard name badge holders.
- **Larger name text** — Attendee name font increased to up to 180pt (auto-shrinks to fit), making names readable from a distance.
- **Larger centered logo** — Event logo is now 2× bigger and horizontally centered at the top of the badge.
- **Improved layout hierarchy** — "Innovate Together" tagline centered directly beneath the logo, followed by event name, separator line, then the name/company/title block vertically centered in the remaining space.

### Auto-Sync from Luma API
- **Background auto-sync** — Guest list automatically refreshes from the Luma API at a configurable interval (default: every 5 minutes). New registrations appear without manual CSV uploads or clicking "Sync."
- **Configurable interval** — Set `SYNC_INTERVAL` in `.env` to control how often the auto-sync runs (in seconds). Set to `0` to disable.
- **Last-sync timestamp** — Admin dashboard now shows the time of the last successful Luma sync, so you can verify data freshness.
- **Auto-sync status indicator** — Dashboard displays "Auto-sync: ON" or "Auto-sync: OFF" with the configured interval.

### Admin Dashboard
- **Clickable stat cards** — The Registered / Checked In / Remaining cards at the top of the dashboard now act as filters. Click "Checked In" to show only checked-in guests, "Remaining" to show only those who haven't checked in, etc. Click again to clear the filter.

### Configuration Changes
- `LABEL_SIZE` default changed from `62x100` to `62red` (required for QL-820NWB two-color raster)
- `BADGE_WIDTH` / `BADGE_HEIGHT` changed to `1182×696` (landscape at 300 DPI)
- New `SYNC_INTERVAL` setting (default: 300 seconds)
