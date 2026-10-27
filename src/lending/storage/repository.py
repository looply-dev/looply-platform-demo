"""Data access layer: turns SQL rows into domain models. All SQL must be parameterized."""

import sqlite3
from datetime import date

from lending.domain.models import Book, Loan, Member


def _to_loan(row: sqlite3.Row) -> Loan:
    """Convert a row of the loans table to a Loan. Dates are stored as ISO strings."""
    return Loan(
        id=row["id"],
        book_id=row["book_id"],
        member_id=row["member_id"],
        borrowed_on=date.fromisoformat(row["borrowed_on"]),
        due_on=date.fromisoformat(row["due_on"]),
        returned_on=date.fromisoformat(row["returned_on"]) if row["returned_on"] else None,
        late_fee_cents=row["late_fee_cents"],
        renew_count=row["renew_count"],
    )


class LibraryRepository:
    """Reads and writes books, members, and loans. Contains no business decisions."""

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    @property
    def connection(self) -> sqlite3.Connection:
        """The underlying database connection, shared with read-only queries such as reports."""
        return self._conn

    # ---- books / members ----

    def add_book(self, title: str, author: str, total_copies: int) -> Book:
        """Insert a book and return it with its id."""
        cur = self._conn.execute(
            "INSERT INTO books (title, author, total_copies) VALUES (?, ?, ?)",
            (title, author, total_copies),
        )
        self._conn.commit()
        return Book(cur.lastrowid, title, author, total_copies)

    def get_book(self, book_id: int) -> Book | None:
        """Get a book by id, or None if it does not exist."""
        row = self._conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
        return Book(row["id"], row["title"], row["author"], row["total_copies"]) if row else None

    def add_member(self, name: str, tier: str = "standard") -> Member:
        """Insert a member and return it with its id."""
        cur = self._conn.execute("INSERT INTO members (name, tier) VALUES (?, ?)", (name, tier))
        self._conn.commit()
        return Member(cur.lastrowid, name, tier)

    def get_member(self, member_id: int) -> Member | None:
        """Get a member by id, or None if it does not exist."""
        row = self._conn.execute("SELECT * FROM members WHERE id = ?", (member_id,)).fetchone()
        return Member(row["id"], row["name"], row["tier"]) if row else None

    # ---- loans ----

    def count_active_loans_for_member(self, member_id: int) -> int:
        """Number of active (not returned) loans of a member."""
        row = self._conn.execute(
            "SELECT COUNT(*) FROM loans WHERE member_id = ? AND returned_on IS NULL",
            (member_id,),
        ).fetchone()
        return row[0]

    def count_active_loans_for_book(self, book_id: int) -> int:
        """Number of copies of a book that are currently on loan."""
        row = self._conn.execute(
            "SELECT COUNT(*) FROM loans WHERE book_id = ? AND returned_on IS NULL",
            (book_id,),
        ).fetchone()
        return row[0]

    def create_loan(self, book_id: int, member_id: int, borrowed_on: date, due_on: date) -> Loan:
        """Insert a new loan."""
        cur = self._conn.execute(
            "INSERT INTO loans (book_id, member_id, borrowed_on, due_on) VALUES (?, ?, ?, ?)",
            (book_id, member_id, borrowed_on.isoformat(), due_on.isoformat()),
        )
        self._conn.commit()
        return Loan(cur.lastrowid, book_id, member_id, borrowed_on, due_on)

    def get_loan(self, loan_id: int) -> Loan | None:
        """Get a loan by id, or None if it does not exist."""
        row = self._conn.execute("SELECT * FROM loans WHERE id = ?", (loan_id,)).fetchone()
        return _to_loan(row) if row else None

    def mark_returned(self, loan_id: int, returned_on: date, late_fee_cents: int) -> Loan:
        """Mark a loan as returned and record its late fee."""
        self._conn.execute(
            "UPDATE loans SET returned_on = ?, late_fee_cents = ? WHERE id = ?",
            (returned_on.isoformat(), late_fee_cents, loan_id),
        )
        self._conn.commit()
        loan = self.get_loan(loan_id)
        assert loan is not None
        return loan

    def renew_loan(self, loan_id: int, new_due_on: date) -> Loan:
        """Set a new due date and increment the renewal count."""
        self._conn.execute(
            "UPDATE loans SET due_on = ?, renew_count = renew_count + 1 WHERE id = ?",
            (new_due_on.isoformat(), loan_id),
        )
        self._conn.commit()
        loan = self.get_loan(loan_id)
        assert loan is not None
        return loan

    def list_loans_for_member(self, member_id: int) -> list[Loan]:
        """List all loans of a member (including returned ones), ordered by borrow date."""
        rows = self._conn.execute(
            "SELECT * FROM loans WHERE member_id = ? ORDER BY borrowed_on, id",
            (member_id,),
        ).fetchall()
        return [_to_loan(r) for r in rows]
