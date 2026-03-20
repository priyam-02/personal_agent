#!/bin/bash
# Periodic email checker for NemoClaw sandbox.
# Runs check_email.py and writes results to pending_emails.json
# if new emails are found. The agent picks this up on next interaction.
#
# Register with: crontab -e
#   */2 * * * * /sandbox/cron/check_email_cron.sh

set -euo pipefail

cd /sandbox

RESULT=$(python -m src.tools.check_email --max 10 2>/dev/null) || exit 0

NEW_COUNT=$(echo "$RESULT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(len(data.get('new_emails', [])))
" 2>/dev/null) || exit 0

if [ "$NEW_COUNT" -gt "0" ]; then
    echo "$RESULT" > /sandbox/pending_emails.json
fi
