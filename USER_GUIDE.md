# LumaPortal User Guide

This guide walks you through setting up and running the event check-in portal. No technical experience required.

---

## What You Need

- A Mac laptop (the "check-in server")
- Wi-Fi at the venue
- Optional: a Brother QL label printer (QL-820NWB recommended) + USB cable
- Optional: label rolls (Brother DK-11202, 62mm x 100mm)
- Your guest list as a CSV file exported from Luma

---

## Before the Event

### 1. First-Time Setup (5 minutes)

1. Download the LumaPortal folder to your Mac (from GitHub or a zip file)
2. **Before anything else**, open **Terminal** (search "Terminal" in Spotlight) and run this command — copy and paste it exactly, then press Enter:
   ```
   xattr -d com.apple.quarantine ~/Downloads/LumaPortal/START.command
   ```
   Adjust the path if you put the folder somewhere other than Downloads (e.g. `~/Desktop/LumaPortal/START.command`). This tells macOS the file is safe to run. You only need to do this once.
3. Double-click **START.command** in Finder
4. If macOS still shows a security warning ("cannot be opened"):
   - Click **Done** (not "Move to Trash")
   - **Right-click** the file > click **Open** > click **Open** in the dialog
   - Or go to **System Settings > Privacy & Security** and click **Open Anyway**
5. A Terminal window opens and the system installs what it needs (first time only)
6. Your browser opens to the admin dashboard automatically

### 2. Export Your Guest List from Luma

1. Go to your event on [lu.ma](https://lu.ma)
2. Click **Manage** on your event page
3. Go to the **Guests** tab
4. Click **Export** (top right) to download the CSV file
5. Save it somewhere easy to find (like your Desktop)

### 3. Load the Guest List

1. In the admin dashboard, click the purple **Upload CSV** button
2. Select the CSV file you exported from Luma
3. You should see a green message: "Imported X guests"
4. The guest table below now shows all your attendees

You can re-upload the CSV at any time to update the list (new registrations, etc.). Existing check-in data is preserved.

### 4. Set Up Luma API Integration (Optional)

Instead of manually exporting and uploading CSV files, you can connect directly to the Luma API to pull your guest list automatically and sync check-ins back to Luma in real time.

**Prerequisites:**
- You need a **Luma Plus** subscription (the API is not available on free plans)
- The API key is tied to a specific **calendar**, not a single event — so it works for all events under that calendar

**Step 1 — Get your API key:**

1. Log in to [lu.ma](https://lu.ma)
2. Go to your **Calendar** page (the calendar that contains your event)
3. Click **Settings** (gear icon)
4. Go to the **API Keys** section — or navigate directly to [luma.com/calendar/manage/api-keys](https://luma.com/calendar/manage/api-keys)
5. Click **Create API Key**
6. Copy the key — you'll only see it once, so save it somewhere safe

**Step 2 — Get your Event API ID:**

Your event's API ID is in the Luma URL for your event. It looks like `evt-XXXXXXXXXXXXXXX`. You can also find it in the CSV export — it's part of the `qr_code_url` column.

**Step 3 — Configure the portal:**

1. Open the `.env` file in the LumaPortal folder using TextEdit
   - If you don't see it in Finder, press **Cmd+Shift+.** to show hidden files
2. Fill in these two values:
   ```
   LUMA_API_KEY=your-api-key-here
   EVENT_API_ID=evt-your-event-id-here
   ```
3. Save the file and restart the server (close Terminal, double-click START.command again)

**What happens when the API is configured:**
- On startup, the portal automatically fetches the full guest list from Luma
- You can also click **"Sync from Luma API"** on the admin dashboard at any time to pull the latest registrations
- When someone checks in, the portal syncs their check-in status back to Luma every 30 seconds
- You can still upload a CSV as a backup — both data sources work together

**Security note:** Your API key gives full access to your Luma calendar. Never share it publicly or post it online. The `.env` file is already excluded from git, so it won't be accidentally uploaded to GitHub.

**If you don't set up the API**, everything still works — you just need to export and upload CSV files manually from Luma before your event.

### 5. Set Up the Badge Printer (Optional)

If you don't have a printer, everything still works — check-ins proceed normally and badge images are saved as PNG files in the `data/` folder so you can print them later from any printer.

#### What You Need to Buy

- **Printer**: Brother QL-820NWB (recommended) — about $170 on Amazon
  - Other compatible models: QL-800, QL-810W, QL-1100, QL-1110NWB
- **Labels**: Brother DK-11202 shipping labels (62mm x 100mm) — about $15 for a roll of 300
  - These are the white rectangular labels, not the continuous tape
- **Cable**: USB-A to USB-B cable (the square-shaped connector, like an older printer cable)
  - The QL-820NWB also supports Wi-Fi, but USB is more reliable for events

#### Unboxing and Loading Labels

1. **Unbox the printer** — remove all tape and packaging materials
2. **Open the label compartment** — lift the cover on the top/front of the printer
3. **Insert the label roll:**
   - Hold the roll so the labels feed from the bottom (the label surface faces up)
   - Place the roll into the compartment — it sits in the guides on each side
   - Pull the end of the label strip out through the front slot
   - Feed it past the cutter opening so a few inches stick out
4. **Close the cover** — press down until it clicks shut
5. **Plug in the power cable** and turn the printer on (power button on the back or side)
6. **Press the feed button** (on the front of the printer) once — it should pull the label through and cut it. If this works, your labels are loaded correctly

#### Connecting to Your Mac

1. **Plug the USB cable** from the printer into your Mac
   - If your Mac only has USB-C ports, you'll need a USB-C to USB-A adapter (or a USB-C to USB-B cable)
2. **macOS may show a pop-up** asking to allow the accessory to connect — click **Allow**
3. You do **not** need to install any printer drivers — the portal talks directly to the printer over USB

#### Verifying the Connection

1. Start the portal (double-click `START.command`)
2. Open the admin dashboard
3. Look at the **top right** of the dashboard:
   - **"Printer: Connected"** (green dot) = ready to print
   - **"Printer: Not connected"** (red dot) = see troubleshooting below

#### If You Have a Different Printer Model

The default setting is for the QL-820NWB. If you bought a different Brother QL model:

1. Open the `.env` file in TextEdit (press **Cmd+Shift+.** in Finder to show hidden files)
2. Change the `PRINTER_MODEL` line to match your printer:
   ```
   PRINTER_MODEL="QL-800"
   ```
   Common values: `QL-800`, `QL-810W`, `QL-820NWB`, `QL-1100`, `QL-1110NWB`
3. If you're using different label sizes, also change:
   ```
   LABEL_SIZE="62x100"
   ```
   The `62x100` setting works with DK-11202 labels. For other labels, see the size printed on the label box (e.g. `62` for continuous 62mm tape, `29x90` for address labels)
4. Save the file and restart the server

#### Testing a Badge Print

1. Make sure at least one guest is loaded (upload a CSV or sync from Luma)
2. In the admin dashboard guest table, click **Check In** next to any guest
3. A badge should print within a few seconds
4. If it doesn't print, click **Reprint** to try again
5. Check the admin dashboard for the printer status indicator

#### Printer Troubleshooting

| Problem | Solution |
|---------|----------|
| "Printer: Not connected" | Unplug the USB cable, wait 5 seconds, plug it back in. Check that the printer is powered on. |
| macOS asks about an accessory | Click **Allow** to let the printer connect |
| Badge prints but is blank | The labels may be loaded upside down — open the cover and flip the roll |
| Badge prints but is cut off | Check that `LABEL_SIZE` in `.env` matches your actual labels (should be `62x100` for DK-11202) |
| "Print failed" error in dashboard | Try the **Reprint** button. If it still fails, check that no label is jammed in the cutter |
| Labels are jamming | Open the cover, gently pull out any stuck label, close the cover, and press the feed button |
| Printer works but badges look small | Make sure `PRINTER_MODEL` in `.env` matches your actual printer model |
| Nothing happens at all | The badge is saved as a PNG in the `data/` folder — you can print it manually from any printer |

#### No Printer? No Problem

Without a printer connected, the portal:
- Still checks in guests normally
- Shows the success screen to attendees
- Saves badge images as PNG files in the `data/` folder inside LumaPortal
- Files are named `badge_gst-XXXXX.png` — you can print them later from any computer and printer

### 6. Print the QR Code Poster

1. In the admin dashboard, click **Generate QR Code**
2. A QR code appears on the page
3. Right-click the QR code image > **Save Image As** to save it
4. Print it large (ideally on a full sheet of paper or poster)
5. Display it at the venue entrance so attendees can scan it with their phones

The QR code links to your check-in page. When attendees scan it, the check-in page opens on their phone.

### 7. Test the Flow

Before the event, do a test run:

1. Open the check-in page URL shown in the Terminal window on your phone
   - The URL looks like `http://192.168.x.x:8000` (your laptop's Wi-Fi address)
2. Type a guest name
3. Tap the matching result
4. Confirm the check-in
5. Check the admin dashboard — the guest should now show "Checked In"
6. If a printer is connected, a badge should print

---

## Event Day

### Starting the Server

1. Connect your laptop to the venue Wi-Fi
2. Double-click **START.command**
3. The Terminal window shows your check-in URLs:
   ```
   Check-in page:  http://192.168.1.50:8000
   Admin dashboard: http://192.168.1.50:8000/admin
   ```
4. The admin dashboard opens automatically

**Important:** Keep the Terminal window open the entire event. Closing it stops the server.

### The Attendee Experience

1. Attendee scans the QR code poster with their phone camera
2. The check-in page opens in their browser
3. They type their name in the search box
4. Matching names appear — they tap theirs
5. A confirmation screen shows their name, company, and title
6. They tap **"Yes, check me in"**
7. Success screen appears, badge prints automatically
8. The page resets for the next person after 5 seconds

### If an Attendee Can't Find Their Name

- They may have registered under a different name or spelling
- Ask them for their email and search for part of it
- If they're not in the system at all, you can:
  - Add them by uploading an updated CSV from Luma
  - Or direct them to register on your Luma event page

### Using the Admin Dashboard

The admin dashboard is your command center during the event.

**Stats Bar (top)**
- **Registered** — total number of guests in the system
- **Checked In** — how many have checked in so far
- **Remaining** — how many haven't checked in yet

**Guest Table**
- Shows every guest with their check-in status
- Use the **Filter** box to search for a specific guest
- Each row has action buttons:
  - **Check In** — manually check someone in from the dashboard
  - **Undo** — reverse a check-in (if someone was checked in by mistake)
  - **Reprint** — print another badge for someone already checked in

**Buttons**
- **Upload CSV** — load or refresh the guest list
- **Sync from Luma API** — pull the latest guest list directly from Luma (requires API key in settings)
- **Generate QR Code** — create/show the venue QR code
- **Open Check-In Page** — opens the attendee-facing page in a new tab

### Multiple Check-In Stations

You can run multiple check-in points using one laptop:

1. Place tablets or phones at different check-in stations
2. Connect them all to the same Wi-Fi as your laptop
3. Open the check-in page URL on each device
4. All devices share the same data — if someone checks in at Station A, Station B sees it immediately

### Keeping Track of Capacity

Watch the stats bar on the admin dashboard. The numbers update automatically every 10 seconds.

---

## After the Event

### Getting Your Check-In Data

Your check-in data is stored in `data/checkin.db` inside the LumaPortal folder. The admin dashboard also shows who checked in and at what time.

If you configured the Luma API key, check-in data is automatically synced back to Luma, so you can see it on your Luma event page too.

### Preparing for the Next Event

1. Delete the file `data/checkin.db` inside the LumaPortal folder (this clears all guest and check-in data)
2. Update the event name in the `.env` file:
   - Open the `.env` file in TextEdit
   - Change `EVENT_NAME="Build AI with Podman"` to your new event name
   - Save the file
3. Start the server and upload your new guest CSV

---

## Troubleshooting

### "START.command Not Opened" / "Cannot verify" / "Unidentified developer"

This is macOS Gatekeeper blocking files downloaded from the internet. Three ways to fix it (try in order):

**Option A — Remove the quarantine flag (recommended):**
1. Open **Terminal** (search "Terminal" in Spotlight)
2. Copy and paste this command, then press Enter:
   ```
   xattr -d com.apple.quarantine ~/Downloads/LumaPortal/START.command
   ```
   (Change the path if your folder is somewhere else, e.g. `~/Desktop/LumaPortal/...`)
3. Now double-click `START.command` — it should work

**Option B — Right-click to open:**
1. Click **Done** on the warning dialog (not "Move to Trash")
2. **Right-click** `START.command` in Finder
3. Click **Open** from the menu
4. Click **Open** again in the dialog that appears
5. This only needs to be done once

**Option C — System Settings:**
1. Click **Done** on the warning dialog
2. Go to **System Settings > Privacy & Security**
3. Scroll down — you'll see a message about `START.command` being blocked
4. Click **Open Anyway**

### Server won't start / "Port already in use"

Another copy of the server may still be running:
1. Close all Terminal windows
2. Try double-clicking `START.command` again

### Check-in page won't load on phones

Make sure:
- The phone is on the **same Wi-Fi** as your laptop
- You're using the correct URL (the one shown in Terminal, not "localhost")
- Your laptop hasn't gone to sleep (disable sleep in System Settings > Energy)

### Printer not printing

See the detailed **Printer Troubleshooting** table in Section 5 above. The most common fix is unplugging and re-plugging the USB cable.

### Need to undo a check-in

In the admin dashboard, find the guest in the table and click **Undo**. This reverses their check-in so they can check in again.

### Laptop goes to sleep

Prevent this during the event:
1. Go to **System Settings > Energy** (or Battery > Options)
2. Set "Turn display off" to **Never** (or a long time like 3 hours)
3. Check "Prevent automatic sleeping when the display is off"

### Wi-Fi is unreliable or drops out

The system works offline after the initial guest list is loaded. Check-ins are saved locally. If you configured the Luma API, check-in data will sync back to Luma once the connection is restored.

---

## Quick Reference Card

| Task | How |
|------|-----|
| Start the server | Double-click `START.command` |
| Stop the server | Close the Terminal window, or press Ctrl+C |
| Load guest list | Admin dashboard > Upload CSV |
| Check someone in manually | Admin dashboard > find guest > Check In |
| Undo a check-in | Admin dashboard > find guest > Undo |
| Reprint a badge | Admin dashboard > find guest > Reprint |
| See check-in progress | Admin dashboard stats bar (auto-refreshes) |
| Change event name | Edit `EVENT_NAME` in the `.env` file |
| Start fresh for new event | Delete `data/checkin.db`, restart server |
