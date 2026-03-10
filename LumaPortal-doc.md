# Building a web-based event check-in portal with badge printing

**A lightweight local server running Python or Node.js on a laptop is the best architecture for most events** — it provides direct thermal printer control, works offline, and keeps complexity manageable. The Luma API fully supports external check-in systems with dedicated endpoints for guest lookup and status updates, and both DYMO and Brother printers can be driven silently from JavaScript or Python without print dialogs. Below is a complete technical breakdown of every component, four architecture options with honest trade-offs, and a recommended stack you could build in a weekend.

---

## The Luma API has everything you need for live check-in

Luma's public REST API at `https://public-api.luma.com/v1/` provides a complete set of endpoints purpose-built for check-in workflows. Authentication uses an API key passed via the `x-luma-api-key` header, and **a Luma Plus subscription is required** to access the API. The key is calendar-specific, generated in your Luma calendar settings.

The three endpoints that matter most for check-in are:

- **`GET /event/get-guests?event_api_id=evt-xxx`** — fetches the full attendee list with cursor-based pagination (use `pagination_cursor` and `pagination_limit` parameters). Each guest record includes `name`, `email`, `approval_status`, ticket information, check-in status, custom registration question responses, and social profile URLs.
- **`GET /event/get-guest?id={key}`** — looks up a single guest by guest key (`g-abc123`) or ticket key (`xyz789`). This auto-detects key type and returns full guest details.
- **`POST /event/update-guest-status`** — updates a guest's status, including marking them as checked in. This is your write-back endpoint for syncing check-in state to Luma.

Rate limits are **500 GET requests per 5 minutes** and **100 POST requests per 5 minutes** per calendar, with a 1-minute lockout on `429` responses. For a 500-person event, these limits are more than adequate — you'd pre-fetch the full guest list at startup and only POST when someone checks in.

Luma also supports **webhooks** for real-time notifications. The `guest.updated` event type fires when a guest's status changes, including check-ins. You can create webhooks via `POST /webhooks/create`. This enables multi-station architectures where a central server broadcasts check-in events. Luma even publishes a dedicated help page on external check-in integration at `help.luma.com/p/external-check-in-integration`, confirming this is a supported use case.

**CORS and security consideration**: the API key must never be exposed in browser-side JavaScript. You need a server-side proxy — even a single-file Flask or Express server will work. This constraint alone rules out a purely static/browser-only approach for the Luma API path.

### CSV fallback is straightforward

Luma's CSV export (from the event Manage → Guests tab) includes name, email, phone, registration date, approval status, ticket type, check-in status, QR code URL, payment details, and all custom registration question responses. Parsing this in the browser is trivial with **Papa Parse** (`papaparse.com`), which handles streaming, auto-delimiter detection, and header mapping. Store parsed records in **IndexedDB** via **Dexie.js** for structured querying and persistence across page reloads — this handles 100,000+ records easily and survives browser crashes.

---

## Thermal printer options narrow down to three practical paths

Browser-to-printer communication is the trickiest piece of this system. Every approach requires some form of local software — no browser can silently send data to a USB thermal printer without a bridge. Here are the three paths worth considering, in order of recommendation.

### Path 1: DYMO Connect Framework (JavaScript SDK)

DYMO's approach installs a local **web service daemon** (DYMO Connect Software) that listens on `https://127.0.0.1:41951`. The DYMO Connect Framework JavaScript SDK (`dymo.connect.framework.js`, hosted on GitHub at `dymosoftware/dymo-connect-framework`) communicates with this service to discover printers, render label previews, and print silently.

The workflow is: create a `.dymo` or `.label` XML template with named objects → load it via `dymo.label.framework.openLabelXml()` → set object text via `label.setObjectText("objectName", "John Smith")` → print with `dymo.label.framework.printLabel()`. Labels are XML-defined, which means badge layout is template-driven and easy to customize.

**Best label for badges**: DYMO **30857** (2.25" × 4" die-cut name badge labels, 250/roll, ~$0.08 each) or **30256** shipping labels (2.31" × 4", 300/roll) as a cheaper alternative. The **LabelWriter 450 Turbo** prints ~71 labels/minute; the **550 Turbo** prints ~62/min but requires DYMO-branded RFID-chipped labels (a real limitation).

**Key limitation**: DYMO Connect installs a self-signed root CA certificate trusted for all domains, not just localhost. This is a documented security risk. It also only runs on Windows and macOS — no Linux support.

### Path 2: Brother QL via WebUSB (zero-install, browser-only)

The `brother_ql-webusb` TypeScript library (GitHub: `ThomasPoinsot/brother_ql-webusb`) enables **direct USB communication** from Chrome/Edge to Brother QL printers using the WebUSB API. No drivers, no SDK, no browser extensions — just plug in the printer, open the page, and grant USB access once via a user gesture.

This is the most modern approach. The library auto-detects the printer model and loaded media, then sends raster data directly. It works on Windows, macOS, and Linux. The **Brother QL-820NWB** (~$200-250) is the top recommendation — **110 labels/minute**, built-in auto-cutter, and connectivity via USB, Wi-Fi, Bluetooth, and Ethernet. Best label: **DK-11202** (62mm × 100mm die-cut, 300/roll, ~$0.06 each).

**Catch**: WebUSB only works in Chrome and Edge (no Firefox, no Safari). On Windows, the printer driver may exclusively claim the USB device, requiring Zadig to switch to the WinUSB driver. The page must be served over HTTPS (or localhost). These are manageable constraints for a controlled event environment where you own the check-in station.

### Path 3: QZ Tray (universal bridge, any printer)

**QZ Tray** (`qz.io`, open-source LGPL on GitHub at `qzind/tray`) is a Java-based local application that creates a WebSocket server on the client machine. Your browser JavaScript connects via `qz.websocket.connect()`, discovers printers with `qz.printers.find("DYMO")`, and sends print jobs as images, HTML, PDFs, or raw printer commands. It supports every browser, every OS (Windows/Mac/Linux), and virtually every thermal printer brand.

The trade-off is setup overhead: QZ Tray needs Java 11+ (bundled since v2.2) and the free version shows a confirmation dialog on each print. The commercial license (~$250) enables silent printing via signed certificates. For a multi-brand printer environment or Firefox/Safari requirement, QZ Tray is the clear winner.

### Server-side printing via Python's brother_ql

For the local server architecture, the **`brother_ql`** Python package (`pip install brother_ql`) is the gold standard. It bypasses the OS print system entirely, talking to Brother QL printers via USB (pyusb), network (TCP), or Linux kernel interfaces. Generate a badge image with **Pillow**, then print it in one command: `brother_ql -b pyusb -m QL-820NWB -p usb://0x04f9:0x209d print -l 62x100 badge.png`. The companion project **`brother_ql_web`** provides a ready-made REST API and web UI for label printing, complete with a Docker image.

---

## Four architectures compared: which fits your event?

### Option 1 — Fully browser-based (static HTML/JS, CSV-only)

The attendee CSV is uploaded and parsed client-side with Papa Parse. Records are stored in IndexedDB. Attendees search their name using a fuzzy search powered by **Fuse.js** (Bitap algorithm, configurable threshold of ~0.3-0.4 catches typos). The check-in page is a PWA with service worker caching for full offline capability.

Printing uses either `window.print()` with CSS `@media print` rules (unreliable, shows dialog, requires manual printer selection each time) or the DYMO Connect Framework JS SDK (silent, but requires DYMO Connect Software installed). The entire app can be a single HTML file hosted on GitHub Pages, Netlify, or even opened from a USB drive via `file://`.

- **Works offline**: Yes, completely
- **Printer integration**: Poor (print dialogs) to good (with DYMO Connect installed)
- **Multi-station sync**: None — each device is independent
- **Best for**: Events under 200 people with minimal setup time and a single check-in iPad/laptop
- **Setup time**: Under 1 hour
- **Biggest weakness**: No centralized check-in tracking, no Luma API integration (would expose API key), and printing is either clunky or requires local software anyway

### Option 2 — Lightweight local server (Python/Node on a laptop)

A **FastAPI** (Python) or **Express** (Node.js) server runs on a laptop at the event, serving both the check-in web UI and handling printer communication. SQLite stores attendee data and check-in state. On startup, the server optionally fetches the guest list from the Luma API and caches it locally for offline resilience.

Multiple devices (tablets, phones) on the same Wi-Fi network access the check-in page at `http://laptop-ip:8000`. When someone checks in, the server writes a check-in record to SQLite, calls Luma's `update-guest-status` endpoint (if online), generates a badge image with Pillow, and prints it via `brother_ql` or DYMO Connect.

- **Works offline**: Yes, after initial data sync
- **Printer integration**: Excellent — direct, silent, no browser extension needed
- **Multi-station sync**: Yes — all devices share the same server/database
- **Best for**: Events of 200-1,000 people, single venue, 1-3 check-in stations
- **Setup time**: 2-4 hours (including testing)
- **Biggest weakness**: Single point of failure (the laptop). Bring a backup

This is the recommended architecture for most events. A minimal Python implementation needs ~200 lines of code: FastAPI for the web layer, Papa Parse or Python's `csv` module for CSV import, `brother_ql` for printing, and SQLite for state. The web UI is a simple responsive page with a large search input and confirmation button.

### Option 3 — Cloud-hosted with local print agent

The web application lives on **Vercel**, **Railway**, or **Fly.io** with a PostgreSQL database. It handles the Luma API integration, attendee management, check-in tracking, and admin dashboard. A small local agent on the event laptop connects to the cloud app and handles printing.

The local print agent can be implemented three ways: **QZ Tray** (browser JavaScript talks to local printer via WebSocket), a **polling agent** (small Python/Node script that checks a cloud API endpoint every few seconds for pending print jobs), or a **WebSocket agent** (stays connected to the cloud server and receives push notifications for immediate printing).

- **Works offline**: Partially — the local agent can cache data, but the main app needs internet
- **Printer integration**: Good, via the local agent
- **Multi-station sync**: Excellent — centralized database is the source of truth
- **Best for**: Large events (1,000+), multiple venues, or when remote monitoring is needed
- **Setup time**: 1-2 days of development, plus deployment
- **Biggest weakness**: Internet dependency. If venue Wi-Fi dies, check-in degrades to whatever's cached locally. The most complex architecture with the most failure modes

### Option 4 — Adapt an existing open-source project

Several open-source projects can be adapted rather than building from scratch:

- **badgeprint** (`sammyfung/badgeprint`) — Django app with Brother QL-720NW support, CSV import from Eventbrite, QR code check-in, multi-printer support. The closest match to this use case. Replace the Eventbrite CSV format with Luma's and it's nearly ready.
- **Alf.io** (`alfio-event/alf.io`, ~1,564 GitHub stars) — Java/Spring Boot event platform with a remarkable Raspberry Pi-based check-in station system (`alf.io-PI`) that supports offline operation, thermal label printing, and duplicate prevention across multiple stations. Overkill for a single event but excellent for recurring conference organizers.
- **Pretix** (`pretix/pretix`, ~2,300 stars) — The most mature open-source event platform, with Python/Django backend, badge printing, QR check-in, and a desktop scan app. Best if you want a full event management solution, but complex to self-host.
- **checkin-booth** (`LosAltosHacks/checkin-booth`) — Node.js + DYMO LabelWriter, designed for hackathon check-in with badge printing. Simple, purpose-built, easy to understand and modify.
- **triblondon/eventbadge** — Node.js app that polls Eventbrite for new check-ins and automatically prints badges on a Brother QL-570 via IPP. The polling-and-print pattern could be adapted for Luma's webhook system.

---

## Practical implementation details that matter on event day

### QR code generation and the check-in flow

Generate a static QR code encoding your check-in URL (e.g., `https://checkin.yourevent.com` or `http://192.168.1.100:8000`) using **QRCode.js** in the browser or **python-qrcode** server-side. Print it large on a poster at the venue entrance. Use error correction level **M or Q** (15-25% recovery) for reliability. The URL should be short — QR codes with fewer characters are denser and scan faster.

The attendee flow: scan QR → phone opens check-in page → type name → fuzzy search shows matches → tap their name → server verifies against registration data → prints badge → shows confirmation. The whole interaction should take under 15 seconds.

### Fuzzy name matching avoids the "I can't find myself" problem

**Fuse.js** is the right tool for browser-side fuzzy search. Configure it with `threshold: 0.4`, `ignoreLocation: true`, and weighted keys on `[name (weight: 1.0), email (weight: 0.8), company (weight: 0.5)]`. This catches common problems: "Steven" vs. "Stephen", "MacDonald" vs. "McDonald", partial matches on long names. Display the top 5 matches and let the attendee confirm which one is them. For server-side Python, **thefuzz** (formerly fuzzywuzzy) with `process.extractBests()` gives similar results.

### Badge layout for thermal labels

For a **2.25" × 4"** DYMO label or **62mm × 100mm** Brother label, a clean badge design includes: attendee name in **bold 28-36pt** text centered vertically, company or title in 14-18pt below, and event name in small 10pt text at the bottom. Optionally add a small QR code encoding the attendee's unique ID for session scanning later. Generate the badge as a **PNG image at 300 DPI** (675 × 1200 pixels for DYMO 30857) using Pillow in Python or Canvas in Node.js. Avoid hairline fonts — thermal printers render bold text much more crisply.

### Offline resilience is non-negotiable

Event Wi-Fi is unreliable. Design for offline-first: cache the full attendee list locally at startup (SQLite for local server, IndexedDB for browser-only). Queue check-in state changes and Luma API write-backs for when connectivity returns. A service worker caches the web UI assets so the check-in page loads even without internet. The printer connection is always local (USB), so printing never depends on network.

### Duplicate check-in prevention

Store a `checked_in_at` timestamp per attendee. When a duplicate is attempted, show a clear warning: "Already checked in at 2:34 PM" with the option for staff to override (for legitimate re-entry scenarios). In a multi-station setup with a shared SQLite database, this is straightforward. For the browser-only approach with independent devices, duplicates across stations cannot be prevented without a shared backend.

---

## The recommended stack for most events

For a typical event of 100-1,000 attendees at a single venue, build **Architecture 2** with these specific technologies:

- **Server**: Python 3.11+ with **FastAPI**, running on a MacBook or Windows laptop
- **Database**: **SQLite** via `aiosqlite` for async access
- **Data source**: Luma API at startup + CSV upload fallback via the admin page
- **Search**: **thefuzz** (Python) for server-side fuzzy matching, or serve Fuse.js to the browser
- **Printer**: **Brother QL-820NWB** with **`brother_ql`** Python library (USB connection)
- **Badge rendering**: **Pillow** — generate PNG images at 300 DPI
- **Frontend**: Single-page responsive HTML with vanilla JavaScript, served by FastAPI
- **QR code**: **python-qrcode** to generate the venue poster; display as a downloadable PNG in the admin interface
- **Offline**: Pre-fetch and cache all attendee data in SQLite at startup; queue API write-backs

The total hardware cost is roughly **$250** (Brother QL-820NWB) plus **$15-20** per roll of 300 labels. The software cost is zero. Setup takes an afternoon of development and 30 minutes of on-site configuration. Bring a spare USB cable and an extra roll of labels. Test the full flow end-to-end the night before — thermal printer quirks always surface at the worst possible time.

---

## Conclusion

The Luma API is surprisingly well-suited for external check-in systems, with guest lookup, status updates, and webhook support all available. The real technical challenge is the browser-to-printer bridge, where **Brother QL + `brother_ql` Python library** offers the most reliable path with zero driver dependencies. A local FastAPI server provides the ideal balance of simplicity, offline resilience, and direct printer control. Start with Architecture 2, use CSV as your day-one fallback, and layer in the Luma API integration once the core flow is solid. The browser-only approach (Architecture 1) works for small events where you can tolerate `window.print()` dialogs, and the cloud approach (Architecture 3) only makes sense for multi-venue operations or events large enough to justify the infrastructure complexity.