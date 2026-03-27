#!/usr/bin/env python3
"""Background email poller that sends Telegram notifications for new emails.

Polls Gmail every 2 minutes and sends a brief Telegram nudge when new
important emails arrive. The agent handles full summarization when the
user responds.

Usage:
    python3 -m src.email_poller
"""

import json
import logging
import os
import signal
import sys
import time

import requests

from src.config import Config
from src.database import get_db
from src.gmail_client import GmailClient
from src.tools.check_email import check_for_new_emails

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [poller] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("poller")

POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "120"))  # seconds
PENDING_FILE = os.getenv("PENDING_FILE", "/sandbox/pending_emails.json")

_running = True


def _handle_signal(signum, frame):
    global _running
    logger.info(f"Received signal {signum}, shutting down...")
    _running = False


def send_telegram_message(bot_token: str, chat_id: str, text: str):
    """Send a message via Telegram Bot API."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    try:
        resp = requests.post(url, json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
        }, timeout=10)
        if not resp.ok:
            logger.warning(f"Telegram API error: {resp.status_code} {resp.text[:200]}")
    except Exception as e:
        logger.warning(f"Failed to send Telegram message: {e}")


def format_notification(email: dict) -> str:
    """Format a brief email notification for Telegram."""
    priority_icon = "\U0001f534" if email["priority"] == "high" else "\U0001f4e9"
    snippet = email.get("snippet", "")[:200]
    return (
        f"{priority_icon} <b>New email</b>\n"
        f"From: {email['sender']}\n"
        f"Subject: {email['subject']}\n\n"
        f"{snippet}\n\n"
        f"Say <i>\"reply to #{email['index']}\"</i> to respond."
    )


def main():
    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_ids_raw = os.getenv("ALLOWED_CHAT_IDS", "")

    if not bot_token or not chat_ids_raw:
        logger.error("TELEGRAM_BOT_TOKEN and ALLOWED_CHAT_IDS must be set")
        sys.exit(1)

    chat_ids = [cid.strip() for cid in chat_ids_raw.split(",") if cid.strip()]

    config = Config.from_env()
    logger.info(f"Starting email poller (interval={POLL_INTERVAL}s)")

    while _running:
        try:
            db = get_db()
            gmail = GmailClient(
                client_id=config.gmail_client_id,
                client_secret=config.gmail_client_secret,
                refresh_token=config.gmail_refresh_token,
            )

            result = check_for_new_emails(config, db, gmail)

            if result["new_emails"]:
                logger.info(f"Found {len(result['new_emails'])} new email(s)")

                # Send Telegram notifications
                for email in result["new_emails"]:
                    msg = format_notification(email)
                    for chat_id in chat_ids:
                        send_telegram_message(bot_token, chat_id, msg)

                # Write full details to pending file as fallback
                with open(PENDING_FILE, "w") as f:
                    json.dump(result, f, indent=2)
            else:
                logger.info("No new emails")

            db.close()
        except Exception as e:
            logger.error(f"Poll error: {e}")

        # Sleep in small increments to respond to signals quickly
        for _ in range(POLL_INTERVAL):
            if not _running:
                break
            time.sleep(1)

    logger.info("Poller stopped")


if __name__ == "__main__":
    main()
