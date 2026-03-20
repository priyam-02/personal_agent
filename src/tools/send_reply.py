#!/usr/bin/env python3
"""Send a reply to an email via Gmail within the original thread."""

import argparse
import json
import sys

from src.config import Config
from src.database import get_db, update_email_status
from src.gmail_client import GmailClient


def main():
    parser = argparse.ArgumentParser(description="Send email reply")
    parser.add_argument("--gmail-id", required=True, help="Gmail message ID to reply to")
    parser.add_argument("--body-file", required=True, help="Path to file containing reply body")
    args = parser.parse_args()

    # Read reply body from file (avoids shell escaping issues)
    try:
        with open(args.body_file) as f:
            body = f.read().strip()
    except FileNotFoundError:
        json.dump({"error": f"Body file not found: {args.body_file}"}, sys.stdout, indent=2)
        sys.exit(1)

    if not body:
        json.dump({"error": "Reply body is empty"}, sys.stdout, indent=2)
        sys.exit(1)

    config = Config.from_env()
    db = get_db()

    # Look up email in DB for thread context
    row = db.execute(
        "SELECT thread_id, sender, sender_email, subject FROM processed_emails WHERE gmail_id = ?",
        (args.gmail_id,),
    ).fetchone()

    if not row:
        json.dump({"error": f"Email {args.gmail_id} not found in database"}, sys.stdout, indent=2)
        sys.exit(1)

    gmail = GmailClient(
        client_id=config.gmail_client_id,
        client_secret=config.gmail_client_secret,
        refresh_token=config.gmail_refresh_token,
    )

    sent_id = gmail.send_reply(
        thread_id=row["thread_id"],
        to=row["sender_email"] or row["sender"],
        subject=row["subject"],
        body=body,
    )

    update_email_status(db, args.gmail_id, "replied")

    output = {
        "success": True,
        "sent_message_id": sent_id,
        "replied_to": row["sender"],
        "subject": row["subject"],
    }
    json.dump(output, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
