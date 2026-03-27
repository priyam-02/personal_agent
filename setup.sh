#!/bin/bash
# Initialize the Jarvis agent environment inside a NemoClaw sandbox.
#
# Usage (from inside sandbox):
#   1. Copy .env.example to .env and fill in your values
#   2. bash setup.sh

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

# Create and activate virtual environment
if [ ! -d .venv ]; then
    python3 -m venv .venv
    echo "Created virtual environment at .venv/"
fi
source .venv/bin/activate

# Install Python dependencies
pip install -q -r requirements.txt

# Initialize the database
python3 -c "from src.database import get_db; get_db(); print('Database initialized at $DB_PATH')"

# Make scripts executable
chmod +x cron/check_email_cron.sh
chmod +x cron/start_poller.sh

echo ""
echo "Setup complete!"
echo ""
echo "To test email checking:"
echo "  source .venv/bin/activate && python3 -m src.tools.check_email --max 5"
echo ""
echo "To start the email poller (sends Telegram notifications for new emails):"
echo "  bash cron/start_poller.sh"
echo ""
echo "To start Telegram bridge (from host machine):"
echo "  export SANDBOX_NAME=jarvis"
echo "  nemoclaw start"
