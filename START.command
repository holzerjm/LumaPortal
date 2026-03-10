#!/bin/bash
# ============================================
# LumaPortal - Event Check-In Portal
# Double-click this file to start the server
# ============================================

# Move to the script's directory (wherever the project folder is)
cd "$(dirname "$0")"

echo ""
echo "============================================"
echo "  LumaPortal - Event Check-In Portal"
echo "============================================"
echo ""

# ---- Step 1: Check/install uv (Python package manager) ----
if ! command -v uv &> /dev/null; then
    echo ">> Installing uv (Python package manager)..."
    echo "   This only happens once."
    echo ""
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
    echo ""
fi

# Ensure uv is on PATH even if installed in a previous run
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"

if ! command -v uv &> /dev/null; then
    echo "ERROR: Could not install uv. Please ask for help."
    echo "Press Enter to close..."
    read
    exit 1
fi

echo ">> uv found: $(uv --version)"

# ---- Step 2: Install Python dependencies ----
echo ">> Installing dependencies (first run may take a minute)..."
uv sync --quiet 2>/dev/null || uv sync

# ---- Step 3: Create .env if it doesn't exist ----
if [ ! -f .env ]; then
    cp .env.example .env
    echo ">> Created .env from template"
fi

# ---- Step 4: Find the local IP address for other devices ----
LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "localhost")

echo ""
echo "============================================"
echo "  Server starting!"
echo ""
echo "  Check-in page:  http://${LOCAL_IP}:8000"
echo "  Admin dashboard: http://${LOCAL_IP}:8000/admin"
echo ""
echo "  Other devices on the same Wi-Fi can"
echo "  open the check-in page URL above."
echo ""
echo "  Press Ctrl+C to stop the server."
echo "============================================"
echo ""

# ---- Step 5: Open the admin page in the default browser ----
sleep 1
open "http://localhost:8000/admin" &

# ---- Step 6: Start the server ----
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000

# If server stops, keep window open so user can see any errors
echo ""
echo "Server stopped. Press Enter to close this window..."
read
