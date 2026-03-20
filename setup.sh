#!/bin/bash
# Initialize the Jarvis agent environment inside a NemoClaw sandbox.
#
# Usage (from inside sandbox):
#   1. Copy .env.example to .env and fill in your values
#   2. bash /sandbox/setup.sh

set -euo pipefail

# Work from the directory where this script lives
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Create .env from .env.example if it doesn't exist
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cat .env.example > .env
        echo "Created .env from .env.example — edit it with your values, then re-run this script."
        exit 0
    else
        echo "Error: no .env or .env.example found."
        exit 1
    fi
fi
set -a
source .env
set +a

echo "Setting up Jarvis agent..."

# Install Python dependencies
pip install -q -r requirements.txt

# Initialize the database
python3 -c "from src.database import get_db; get_db(); print('Database initialized at $DB_PATH')"

# Make cron script executable
chmod +x cron/check_email_cron.sh

# Register cron job (every 2 minutes), passing env vars
(crontab -l 2>/dev/null | grep -v check_email_cron; echo "*/2 * * * * cd $SCRIPT_DIR && set -a && . $SCRIPT_DIR/.env && set +a && $SCRIPT_DIR/cron/check_email_cron.sh") | crontab -

# Apply network policy
echo "Applying network policy..."
openshell policy set "$SCRIPT_DIR/network-policy.yaml"

# Start Telegram bridge
echo "Starting Telegram bridge..."
nemoclaw start

echo ""
echo "Jarvis is ready! Send 'check my email' via Telegram to test."
