#!/bin/bash
# Start the email poller as a background process.
#
# Usage (from /sandbox/ or project root):
#   bash cron/start_poller.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$SCRIPT_DIR"

# Load env
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# Activate venv
source .venv/bin/activate

PID_FILE="/sandbox/poller.pid"

# Check if already running
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "Poller already running (PID $OLD_PID)"
        exit 0
    fi
    rm -f "$PID_FILE"
fi

# Start in background
nohup python3 -m src.email_poller >> /sandbox/poller.log 2>&1 &
echo $! > "$PID_FILE"
echo "Poller started (PID $!), logging to /sandbox/poller.log"
