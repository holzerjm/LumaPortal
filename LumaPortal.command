#!/bin/bash
# ============================================
# LumaPortal - Event Check-In Portal
# Double-click to start or stop the server
# ============================================

cd "$(dirname "$0")"

PID_FILE=".server.pid"

# ---- Check if server is already running ----
is_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            return 0
        else
            rm -f "$PID_FILE"
        fi
    fi
    return 1
}

# ---- Stop the server ----
stop_server() {
    local pid=$(cat "$PID_FILE")
    echo ""
    echo "  Stopping server (PID $pid)..."

    kill "$pid" 2>/dev/null

    for i in 1 2 3 4 5; do
        if ! kill -0 "$pid" 2>/dev/null; then
            break
        fi
        sleep 1
    done

    if kill -0 "$pid" 2>/dev/null; then
        kill -9 "$pid" 2>/dev/null
    fi

    rm -f "$PID_FILE"
    echo ""
    echo "  ✅ Server stopped."
    echo ""
}

# ---- Start the server ----
start_server() {
    echo ""
    echo "╔════════════════════════════════════════════╗"
    echo "║     LumaPortal - Event Check-In Portal     ║"
    echo "╚════════════════════════════════════════════╝"
    echo ""

    # Check/install uv
    if ! command -v uv &> /dev/null; then
        echo ">> Installing uv (Python package manager)..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
        echo ""
    fi
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"

    if ! command -v uv &> /dev/null; then
        echo "ERROR: Could not install uv. Please ask for help."
        echo "Press Enter to close..."
        read
        exit 1
    fi

    echo ">> uv found: $(uv --version)"

    # Install dependencies
    echo ">> Installing dependencies (first run may take a minute)..."
    uv sync --quiet 2>/dev/null || uv sync

    # Create .env if needed
    if [ ! -f .env ]; then
        cp .env.example .env
        echo ">> Created .env from template"
    fi

    # Find local IP
    LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "localhost")

    echo ""
    echo "╔════════════════════════════════════════════╗"
    echo "║  ✅ Server starting!                       ║"
    echo "║                                            ║"
    echo "║  Check-in page:                            ║"
    echo "║    http://${LOCAL_IP}:8000"
    echo "║                                            ║"
    echo "║  Admin dashboard:                          ║"
    echo "║    http://${LOCAL_IP}:8000/admin"
    echo "║                                            ║"
    echo "║  To stop: double-click LumaPortal.command  ║"
    echo "║           or press Ctrl+C here             ║"
    echo "╚════════════════════════════════════════════╝"
    echo ""

    # Open admin page
    sleep 1
    open "http://localhost:8000/admin" &

    # Clean up on exit
    cleanup() {
        rm -f "$PID_FILE"
        echo ""
        echo "  Server stopped."
        echo ""
    }
    trap cleanup EXIT

    # Start server
    uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 &
    SERVER_PID=$!
    echo "$SERVER_PID" > "$PID_FILE"

    wait $SERVER_PID

    echo "Press Enter to close this window..."
    read
}

# ════════════════════════════════════════════
#  Main: toggle start / stop
# ════════════════════════════════════════════

if is_running; then
    echo ""
    echo "╔════════════════════════════════════════════╗"
    echo "║     LumaPortal - Server Running            ║"
    echo "╚════════════════════════════════════════════╝"
    echo ""
    echo "  The server is currently running."
    echo ""
    echo "  1) Stop the server"
    echo "  2) Open admin dashboard"
    echo "  3) Cancel"
    echo ""
    printf "  Choose [1/2/3]: "
    read choice

    case "$choice" in
        1)
            stop_server
            echo "Press Enter to close..."
            read
            ;;
        2)
            open "http://localhost:8000/admin"
            ;;
        3|"")
            echo "  Cancelled."
            ;;
    esac
else
    start_server
fi
