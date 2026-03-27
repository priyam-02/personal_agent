#!/usr/bin/env python3
"""Get full details for a specific email by index, Gmail ID, or keyword search."""

import argparse
import json
import sys

from src.database import (
    get_db, get_recent_emails, get_email_by_gmail_id, search_emails,
    update_conversation_context,
)


def main():
    parser = argparse.ArgumentParser(description="Get email details")
    parser.add_argument("--index", type=int, help="1-based recency index")
    parser.add_argument("--gmail-id", help="Gmail message ID")
    parser.add_argument("--search", help="Search by sender/subject/snippet keywords")
    args = parser.parse_args()

    if not any([args.index, args.gmail_id, args.search]):
        json.dump({"error": "Provide --index, --gmail-id, or --search"}, sys.stdout, indent=2)
        sys.exit(1)

    db = get_db()

    if args.gmail_id:
        email = get_email_by_gmail_id(db, args.gmail_id)
        if not email:
            json.dump({"error": f"Email {args.gmail_id} not found"}, sys.stdout, indent=2)
            sys.exit(1)
        update_conversation_context(db, [email["gmail_id"]])
        json.dump({"email": _format(email)}, sys.stdout, indent=2)
        return

    if args.search:
        results = search_emails(db, args.search, limit=5)
        if not results:
            json.dump({"error": f"No emails matching '{args.search}'"}, sys.stdout, indent=2)
            sys.exit(1)
        if len(results) == 1:
            update_conversation_context(db, [results[0]["gmail_id"]])
            json.dump({"email": _format(results[0])}, sys.stdout, indent=2)
        else:
            json.dump({
                "candidates": [
                    {"gmail_id": e["gmail_id"], "sender": e["sender"], "subject": e["subject"]}
                    for e in results
                ]
            }, sys.stdout, indent=2)
        return

    # Index-based lookup (default, filters out skipped)
    all_emails = get_recent_emails(db, limit=100)
    visible = [e for e in all_emails if not e["summary"].startswith("[skipped")]

    if args.index < 1 or args.index > len(visible):
        json.dump({"error": f"Email #{args.index} not found"}, sys.stdout, indent=2)
        sys.exit(1)

    email = visible[args.index - 1]
    update_conversation_context(db, [email["gmail_id"]])
    json.dump({"email": _format(email)}, sys.stdout, indent=2)


def _format(email: dict) -> dict:
    return {
        "gmail_id": email["gmail_id"],
        "thread_id": email.get("thread_id", ""),
        "sender": email["sender"],
        "subject": email["subject"],
        "snippet": email.get("snippet", ""),
        "summary": email.get("summary", ""),
        "priority": email.get("priority", ""),
        "status": email.get("status", ""),
        "processed_at": email.get("processed_at", ""),
        "gmail_url": f"https://mail.google.com/mail/u/0/#inbox/{email['gmail_id']}",
    }


if __name__ == "__main__":
    main()
