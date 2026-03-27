#!/usr/bin/env python3
"""Send a staged reply after user confirmation. Requires a valid token from stage_reply."""

import argparse
import json
import sys
from datetime import datetime, timezone

from src.config import Config
from src.database import get_db, get_state, set_state, update_email_status
from src.gmail_client import GmailClient


def main():
    parser = argparse.ArgumentParser(description="Confirm and send a staged reply")
    parser.add_argument("--confirm-token", required=True, help="Token from stage_reply")
    args = parser.parse_args()

    db = get_db()

    # Load the pending reply
    raw = get_state(db, "pending_reply")
    if not raw:
        json.dump({"error": "No pending reply found. Use stage_reply first."}, sys.stdout, indent=2)
        sys.exit(1)

    pending = json.loads(raw)

    # Verify token
    if pending["token"] != args.confirm_token:
        json.dump({"error": "Invalid confirmation token. Stage a new reply."}, sys.stdout, indent=2)
        sys.exit(1)

    # Check if staged reply is too old (30 min)
    staged_at = datetime.fromisoformat(pending["staged_at"])
    age_minutes = (datetime.now(timezone.utc) - staged_at).total_seconds() / 60
    if age_minutes > 30:
        set_state(db, "pending_reply", "")
        json.dump({"error": "Staged reply expired (>30 min). Please draft again."}, sys.stdout, indent=2)
        sys.exit(1)

    # Send via Gmail
    config = Config.from_env()
    gmail = GmailClient(
        client_id=config.gmail_client_id,
        client_secret=config.gmail_client_secret,
        refresh_token=config.gmail_refresh_token,
    )

    sent_id = gmail.send_reply(
        thread_id=pending["thread_id"],
        to=pending["recipient"],
        subject=pending["subject"],
        body=pending["body"],
    )

    # Clean up and update status
    set_state(db, "pending_reply", "")
    update_email_status(db, pending["gmail_id"], "replied")

    output = {
        "success": True,
        "sent_message_id": sent_id,
        "replied_to": pending["sender_name"],
        "subject": pending["subject"],
    }
    json.dump(output, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
