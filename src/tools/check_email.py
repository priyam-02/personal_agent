#!/usr/bin/env python3
"""Fetch unread emails, classify them, and store in the database.

Outputs JSON with new important emails (suitable for agent summarization).
"""

import argparse
import json
import sys

from src.config import Config
from src.database import get_db, is_processed, save_processed_email, get_recent_emails, update_conversation_context
from src.gmail_client import GmailClient
from src.classifier import classify_email


def check_for_new_emails(config, db, gmail, max_results=10):
    """Core email checking logic. Returns dict with new_emails, skipped_count, total_fetched."""
    emails = gmail.fetch_new_messages(max_results=max_results)

    # Count existing emails for index numbering
    existing_count = len(get_recent_emails(db, limit=10000))
    counter = existing_count

    new_emails = []
    skipped_count = 0

    for em in emails:
        if is_processed(db, em.id):
            continue

        result = classify_email(
            sender_email=em.sender_email,
            subject=em.subject,
            category=em.category,
            labels=em.labels,
            skip_categories=config.skip_categories,
        )

        if not result.should_notify:
            save_processed_email(
                db,
                gmail_id=em.id,
                thread_id=em.thread_id,
                sender=em.sender,
                subject=em.subject,
                snippet=em.snippet,
                summary=f"[skipped: {result.reason}]",
                priority="low",
                sender_email=em.sender_email,
            )
            skipped_count += 1
            continue

        counter += 1
        save_processed_email(
            db,
            gmail_id=em.id,
            thread_id=em.thread_id,
            sender=em.sender,
            subject=em.subject,
            snippet=em.snippet,
            summary="[pending agent summarization]",
            priority=result.priority,
            sender_email=em.sender_email,
        )

        new_emails.append({
            "index": counter,
            "gmail_id": em.id,
            "sender": em.sender,
            "subject": em.subject,
            "priority": result.priority,
            "classification_reason": result.reason,
            "snippet": em.snippet,
            "body_text": em.body_text or em.snippet,
            "date": em.date,
        })

    # Track new important emails in conversation context
    if new_emails:
        update_conversation_context(db, [e["gmail_id"] for e in new_emails])

    return {
        "new_emails": new_emails,
        "skipped_count": skipped_count,
        "total_fetched": len(emails),
    }


def main():
    parser = argparse.ArgumentParser(description="Check Gmail for new emails")
    parser.add_argument("--max", type=int, default=10, help="Max emails to fetch")
    args = parser.parse_args()

    config = Config.from_env()
    db = get_db()
    gmail = GmailClient(
        client_id=config.gmail_client_id,
        client_secret=config.gmail_client_secret,
        refresh_token=config.gmail_refresh_token,
    )

    output = check_for_new_emails(config, db, gmail, max_results=args.max)
    json.dump(output, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
