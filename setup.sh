#!/bin/bash
# Initialize the Nemoclaw agent environment inside a NemoClaw sandbox.
#
# Usage (from inside sandbox):
#   bash /sandbox/setup.sh

set -euo pipefail

echo "Setting up Nemoclaw agent..."

# Install Python dependencies
pip install -q -r /sandbox/requirements.txt

# Initialize the database
python3 -c "from src.database import get_db; get_db(); print('Database initialized at', '/sandbox/nemoclaw.db')"

# Make cron script executable
chmod +x /sandbox/cron/check_email_cron.sh

# Register cron job (every 2 minutes)
(crontab -l 2>/dev/null | grep -v check_email_cron; echo "*/2 * * * * /sandbox/cron/check_email_cron.sh") | crontab -

echo "Nemoclaw agent setup complete."
echo ""
echo "Next steps:"
echo "  1. Set Gmail env vars (see .env.example)"
echo "  2. Apply network policy: openshell policy set /sandbox/network-policy.yaml"
echo "  3. Start Telegram bridge: nemoclaw start (with TELEGRAM_BOT_TOKEN set)"
echo "  4. Send 'check my email' via Telegram to test"
