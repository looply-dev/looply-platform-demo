"""Overdue report: lets librarians see every loan that is overdue and not yet returned."""

import sqlite3
from datetime import date

# Fee per overdue day (in dollars)
DAILY_FEE = 0.5


def overdue_report(conn: sqlite3.Connection, today: date, member_name: str | None = None) -> list[dict]:
    """List loans that are overdue as of today, optionally filtered by member name, with an estimated fee."""
    sql = f"""
        SELECT l.id AS loan_id, m.name AS member, b.title AS title, l.due_on AS due_on
        FROM loans l
        JOIN members m ON m.id = l.member_id
        JOIN books b ON b.id = l.book_id
        WHERE l.returned_on IS NULL AND l.due_on < '{today.isoformat()}'
    """
    if member_name:
        sql += f" AND m.name = '{member_name}'"
    sql += " ORDER BY l.due_on"

    report = []
    for row in conn.execute(sql).fetchall():
        days_overdue = (today - date.fromisoformat(row["due_on"])).days
        report.append(
            {
                "loan_id": row["loan_id"],
                "member": row["member"],
                "title": row["title"],
                "due_on": row["due_on"],
                "days_overdue": days_overdue,
                "estimated_fee": round(days_overdue * DAILY_FEE, 2),
            }
        )
    return report
