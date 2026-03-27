#!/usr/bin/env python3
"""Stage a reply draft for user confirmation. Does NOT send."""

import argparse
import json
import secrets
import sys
from datetime import datetime, timezone

from src.database import get_db, set_state


def main():
    parser = argparse.ArgumentParser(description="Stage a reply draft")
    parser.add_argument("--gmail-id", required=True, help="Gmail message ID to reply to")
    parser.add_argument("--body-file", required=True, help="Path to file containing reply body")
    args = parser.parse_args()

    # Read reply body from file
    try:
        with open(args.body_file) as f:
            body = f.read().strip()
    except FileNotFoundError:
        json.dump({"error": f"Body file not found: {args.body_file}"}, sys.stdout, indent=2)
        sys.exit(1)

    if not body:
        json.dump({"error": "Reply body is empty"}, sys.stdout, indent=2)
        sys.exit(1)

    db = get_db()

    # Look up email in DB for thread context
    row = db.execute(
        "SELECT thread_id, sender, sender_email, subject FROM processed_emails WHERE gmail_id = ?",
        (args.gmail_id,),
    ).fetchone()

    if not row:
        json.dump({"error": f"Email {args.gmail_id} not found in database"}, sys.stdout, indent=2)
        sys.exit(1)

    # Generate confirmation token and store the draft
    token = secrets.token_hex(4)
    pending = json.dumps({
        "gmail_id": args.gmail_id,
        "thread_id": row["thread_id"],
        "recipient": row["sender_email"] or row["sender"],
        "sender_name": row["sender"],
        "subject": row["subject"],
        "body": body,
        "token": token,
        "staged_at": datetime.now(timezone.utc).isoformat(),
    })
    set_state(db, "pending_reply", pending)

    output = {
        "staged": True,
        "confirm_token": token,
        "draft_preview": body,
        "recipient": row["sender_email"] or row["sender"],
        "recipient_name": row["sender"],
        "subject": row["subject"],
        "instructions": "Show this draft to the user. Only call confirm_send after they approve.",
    }
    json.dump(output, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
