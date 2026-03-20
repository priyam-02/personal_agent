#!/usr/bin/env python3
"""List recent processed emails from the database."""

import argparse
import json
import sys

from src.database import get_db, get_recent_emails


def main():
    parser = argparse.ArgumentParser(description="List recent emails")
    parser.add_argument("--limit", type=int, default=10, help="Number of emails to show")
    args = parser.parse_args()

    db = get_db()
    emails = get_recent_emails(db, limit=args.limit)

    # Filter out skipped emails and format
    visible = []
    for i, em in enumerate(emails, 1):
        if em["summary"].startswith("[skipped"):
            continue
        visible.append({
            "index": i,
            "gmail_id": em["gmail_id"],
            "sender": em["sender"],
            "subject": em["subject"],
            "priority": em["priority"],
            "status": em["status"],
            "summary": em["summary"],
            "processed_at": em["processed_at"],
        })

    output = {
        "emails": visible,
        "total_count": len(visible),
    }
    json.dump(output, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
