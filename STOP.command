#!/bin/bash
# ============================================
# LumaPortal - Stop the Check-In Server
# Double-click this file to stop the server
# ============================================

cd "$(dirname "$0")"

PID_FILE=".server.pid"

echo ""
echo "╔════════════════════════════════════════════╗"
echo "║     LumaPortal - Stopping Server           ║"
echo "╚════════════════════════════════════════════╝"
echo ""

if [ ! -f "$PID_FILE" ]; then
    echo "  ℹ️  No running server found."
    echo "     (PID file not present)"
    echo ""
    # Try to find and kill any uvicorn process for this project as fallback
    PIDS=$(pgrep -f "uvicorn src.main:app" 2>/dev/null)
    if [ -n "$PIDS" ]; then
        echo "  Found uvicorn process(es): $PIDS"
        echo "  Stopping..."
        kill $PIDS 2>/dev/null
        sleep 1
        echo "  ✅ Server stopped."
    else
        echo "  No uvicorn process running."
    fi
    echo ""
    echo "Press Enter to close..."
    read
    exit 0
fi

SERVER_PID=$(cat "$PID_FILE")

if kill -0 "$SERVER_PID" 2>/dev/null; then
    echo "  Stopping server (PID $SERVER_PID)..."
    kill "$SERVER_PID" 2>/dev/null

    # Wait up to 5 seconds for graceful shutdown
    for i in 1 2 3 4 5; do
        if ! kill -0 "$SERVER_PID" 2>/dev/null; then
            break
        fi
        sleep 1
    done

    # Force kill if still running
    if kill -0 "$SERVER_PID" 2>/dev/null; then
        echo "  Forcing shutdown..."
        kill -9 "$SERVER_PID" 2>/dev/null
    fi

    rm -f "$PID_FILE"
    echo ""
    echo "  ✅ Server stopped successfully."
else
    echo "  ℹ️  Server was not running (PID $SERVER_PID already exited)."
    rm -f "$PID_FILE"
fi

echo ""
echo "Press Enter to close..."
read
