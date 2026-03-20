#!/usr/bin/env python3
"""Show database statistics."""

import json
import sys

from src.database import get_db


def main():
    db = get_db()

    total = db.execute("SELECT COUNT(*) as c FROM processed_emails").fetchone()["c"]

    status_rows = db.execute(
        "SELECT status, COUNT(*) as c FROM processed_emails GROUP BY status"
    ).fetchall()
    by_status = {row["status"]: row["c"] for row in status_rows}

    priority_rows = db.execute(
        "SELECT priority, COUNT(*) as c FROM processed_emails GROUP BY priority"
    ).fetchall()
    by_priority = {row["priority"]: row["c"] for row in priority_rows}

    last_check = db.execute(
        "SELECT processed_at FROM processed_emails ORDER BY processed_at DESC LIMIT 1"
    ).fetchone()

    output = {
        "total_emails": total,
        "by_status": by_status,
        "by_priority": by_priority,
        "last_check": last_check["processed_at"] if last_check else None,
    }
    json.dump(output, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
