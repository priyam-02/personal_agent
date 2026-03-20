from __future__ import annotations

import os
import sqlite3
import json
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(os.getenv("DB_PATH", "/sandbox/nemoclaw.db"))


def get_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    _migrate(conn)
    return conn


def _migrate(conn: sqlite3.Connection):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS processed_emails (
            gmail_id       TEXT PRIMARY KEY,
            thread_id      TEXT,
            sender         TEXT,
            sender_email   TEXT,
            subject        TEXT,
            snippet        TEXT,
            summary        TEXT,
            telegram_msg_id INTEGER,
            priority       TEXT DEFAULT 'normal',
            status         TEXT DEFAULT 'summarized',
            received_at    TEXT,
            processed_at   TEXT
        );

        CREATE TABLE IF NOT EXISTS state (
            key   TEXT PRIMARY KEY,
            value TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_emails_status
            ON processed_emails(status);
        CREATE INDEX IF NOT EXISTS idx_emails_date
            ON processed_emails(processed_at);
    """)
    conn.commit()


def is_processed(conn: sqlite3.Connection, gmail_id: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM processed_emails WHERE gmail_id = ?", (gmail_id,)
    ).fetchone()
    return row is not None


def save_processed_email(
    conn: sqlite3.Connection,
    gmail_id: str,
    thread_id: str,
    sender: str,
    subject: str,
    snippet: str,
    summary: str,
    telegram_msg_id: int | None = None,
    priority: str = "normal",
    sender_email: str = "",
):
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """INSERT OR REPLACE INTO processed_emails
           (gmail_id, thread_id, sender, sender_email, subject, snippet, summary,
            telegram_msg_id, priority, status, processed_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'summarized', ?)""",
        (gmail_id, thread_id, sender, sender_email, subject, snippet, summary,
         telegram_msg_id, priority, now),
    )
    conn.commit()


def get_recent_emails(conn: sqlite3.Connection, limit: int = 20) -> list[dict]:
    rows = conn.execute(
        """SELECT * FROM processed_emails
           ORDER BY processed_at DESC LIMIT ?""",
        (limit,),
    ).fetchall()
    return [dict(r) for r in rows]


def get_email_by_index(conn: sqlite3.Connection, index: int) -> dict | None:
    """Get the Nth most recent email (1-indexed)."""
    rows = conn.execute(
        """SELECT * FROM processed_emails
           ORDER BY processed_at DESC LIMIT 1 OFFSET ?""",
        (index - 1,),
    ).fetchall()
    return dict(rows[0]) if rows else None


def update_email_status(conn: sqlite3.Connection, gmail_id: str, status: str):
    conn.execute(
        "UPDATE processed_emails SET status = ? WHERE gmail_id = ?",
        (status, gmail_id),
    )
    conn.commit()


def get_state(conn: sqlite3.Connection, key: str, default: str = "") -> str:
    row = conn.execute(
        "SELECT value FROM state WHERE key = ?", (key,)
    ).fetchone()
    return row["value"] if row else default


def set_state(conn: sqlite3.Connection, key: str, value: str):
    conn.execute(
        "INSERT OR REPLACE INTO state (key, value) VALUES (?, ?)",
        (key, value),
    )
    conn.commit()
