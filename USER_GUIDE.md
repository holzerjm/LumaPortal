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

1. Download the LumaPortal folder to your Mac
2. Double-click **START.command**
3. If macOS shows a security warning:
   - Right-click the file instead > click **Open** > click **Open** in the dialog
   - Or go to **System Settings > Privacy & Security** and click **Open Anyway**
4. A Terminal window opens and the system installs what it needs (first time only)
5. Your browser opens to the admin dashboard automatically

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

### 4. Connect the Printer (Optional)

1. Plug the Brother QL printer into your laptop via USB
2. Load a roll of labels (DK-11202 recommended)
3. The admin dashboard should show **"Printer: Connected"** in the top right
4. If it still says "Not connected", try unplugging and re-plugging the USB cable

If you don't have a printer, the system still works — it just skips the badge printing step. Badge images are saved in the `data/` folder if you need to print them later.

### 5. Print the QR Code Poster

1. In the admin dashboard, click **Generate QR Code**
2. A QR code appears on the page
3. Right-click the QR code image > **Save Image As** to save it
4. Print it large (ideally on a full sheet of paper or poster)
5. Display it at the venue entrance so attendees can scan it with their phones

The QR code links to your check-in page. When attendees scan it, the check-in page opens on their phone.

### 6. Test the Flow

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

### "Cannot be opened because it is from an unidentified developer"

This is a macOS security feature. Fix it:
1. Right-click `START.command` > click **Open**
2. In the dialog, click **Open** again
3. This only needs to be done once

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

1. Check the admin dashboard — does it say "Printer: Connected"?
2. Try unplugging and re-plugging the USB cable
3. Make sure labels are loaded in the printer
4. Try the **Reprint** button in the admin dashboard for a specific guest

### Badge images look wrong

If names are cut off or text is too small, this may happen with very long names. The system automatically shrinks text to fit, but extremely long names may wrap to two lines.

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
