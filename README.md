# LumaPortal - Event Check-In & Badge Printing

## Setup (one time)

1. Download/copy this entire `LumaPortal` folder to your computer
2. **Clear the macOS quarantine** (required for downloaded files):
   - Open **Terminal** (search "Terminal" in Spotlight)
   - Run: `xattr -d com.apple.quarantine ~/Downloads/LumaPortal/START.command`
   - (Adjust the path if you saved the folder somewhere else)
3. Double-click **`START.command`** in Finder
4. If macOS still blocks it: right-click the file > **Open** > click **Open** in the dialog

The first run will automatically install everything needed (~1 minute).

See **[USER_GUIDE.md](USER_GUIDE.md)** for detailed setup and event-day instructions.

## Running the Portal

1. Double-click **`START.command`**
2. The admin dashboard opens automatically in your browser
3. Upload your guest CSV file using the **"Upload CSV"** button
4. Open the **Check-In Page** link on tablets/phones for attendees

## At the Event

- Print the QR code from the admin dashboard and display it at the entrance
- Attendees scan the QR code on their phone, type their name, and check in
- Badges print automatically on the connected Brother QL printer
- Staff can use the admin dashboard to force check-ins, undo, or reprint badges

## Connecting a Printer

- Plug in a **Brother QL-820NWB** (or similar QL model) via USB
- The admin dashboard shows printer status in the top-right corner
- If no printer is connected, badge images are saved in the `data/` folder

## Troubleshooting

- **Server won't start**: Make sure no other app is using port 8000
- **Printer not detected**: Try unplugging and re-plugging the USB cable
- **Guests not showing**: Upload the CSV again from the admin dashboard
- **Need to start fresh**: Delete the `data/checkin.db` file and restart
