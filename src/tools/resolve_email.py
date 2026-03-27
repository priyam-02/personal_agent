#!/usr/bin/env python3
"""Resolve a natural language email reference to a specific email."""

import argparse
import json
import re
import sys

from src.database import (
    get_db, get_conversation_context, get_recent_emails, search_emails,
)


CONTEXT_WORDS = {"that email", "the last one", "that one", "it", "the email", "this email"}


def main():
    parser = argparse.ArgumentParser(description="Resolve an email reference")
    parser.add_argument("--query", required=True, help="Natural language email reference")
    args = parser.parse_args()

    db = get_db()
    query = args.query.strip().lower()

    # 1. Check for #N index pattern
    index_match = re.match(r"#?(\d+)$", query)
    if index_match:
        index = int(index_match.group(1))
        all_emails = get_recent_emails(db, limit=100)
        visible = [e for e in all_emails if not e["summary"].startswith("[skipped")]
        if 1 <= index <= len(visible):
            email = visible[index - 1]
            json.dump({"email": _format(email), "match_type": "index"}, sys.stdout, indent=2)
        else:
            json.dump({"error": f"Email #{index} not found"}, sys.stdout, indent=2)
        return

    # 2. Check for context words ("that email", "the last one", etc.)
    if query in CONTEXT_WORDS:
        context = get_conversation_context(db)
        if context:
            # Return the most recently discussed email
            row = db.execute(
                "SELECT * FROM processed_emails WHERE gmail_id = ?",
                (context[0]["gmail_id"],),
            ).fetchone()
            if row:
                json.dump({"email": _format(dict(row)), "match_type": "context"}, sys.stdout, indent=2)
                return
        json.dump({"error": "No recently discussed email to reference."}, sys.stdout, indent=2)
        return

    # 3. Search by content (sender name, subject keywords, etc.)
    results = search_emails(db, query, limit=5)
    if len(results) == 1:
        json.dump({"email": _format(results[0]), "match_type": "search"}, sys.stdout, indent=2)
    elif len(results) > 1:
        candidates = [
            {"gmail_id": e["gmail_id"], "sender": e["sender"], "subject": e["subject"]}
            for e in results
        ]
        json.dump({"candidates": candidates, "match_type": "search_ambiguous"}, sys.stdout, indent=2)
    else:
        json.dump({"error": f"No emails matching '{args.query}'"}, sys.stdout, indent=2)


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
