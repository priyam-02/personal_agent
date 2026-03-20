#!/bin/bash
# Periodic email checker for NemoClaw sandbox.
# Runs check_email.py and writes results to pending_emails.json
# if new emails are found. The agent picks this up on next interaction.

set -euo pipefail

cd /sandbox

# Load env vars
if [ -f /sandbox/.env ]; then
    set -a
    source /sandbox/.env
    set +a
fi

RESULT=$(python3 -m src.tools.check_email --max 10 2>/dev/null) || exit 0

NEW_COUNT=$(echo "$RESULT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(len(data.get('new_emails', [])))
" 2>/dev/null) || exit 0

if [ "$NEW_COUNT" -gt "0" ]; then
    echo "$RESULT" > /sandbox/pending_emails.json
fi
