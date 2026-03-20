#!/usr/bin/env python3
"""Get full details for a specific email by recency index (skips noise)."""

import argparse
import json
import sys

from src.database import get_db, get_recent_emails


def main():
    parser = argparse.ArgumentParser(description="Get email details by index")
    parser.add_argument("--index", type=int, required=True, help="1-based recency index")
    args = parser.parse_args()

    db = get_db()
    # Get enough emails to find the Nth non-skipped one
    all_emails = get_recent_emails(db, limit=100)
    visible = [e for e in all_emails if not e["summary"].startswith("[skipped")]

    if args.index < 1 or args.index > len(visible):
        json.dump({"error": f"Email #{args.index} not found"}, sys.stdout, indent=2)
        sys.exit(1)

    email = visible[args.index - 1]

    output = {
        "email": {
            "gmail_id": email["gmail_id"],
            "thread_id": email["thread_id"],
            "sender": email["sender"],
            "subject": email["subject"],
            "snippet": email["snippet"],
            "summary": email["summary"],
            "priority": email["priority"],
            "status": email["status"],
            "processed_at": email["processed_at"],
            "gmail_url": f"https://mail.google.com/mail/u/0/#inbox/{email['gmail_id']}",
        }
    }
    json.dump(output, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
