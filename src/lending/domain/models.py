"""Domain models: data shapes only. No dependency on storage, services, or api."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Book:
    """A book and the number of copies the library owns."""

    id: int
    title: str
    author: str
    total_copies: int


@dataclass(frozen=True)
class Member:
    """A library member. The tier sets how many books they can borrow at once."""

    id: int
    name: str
    tier: str  # "standard" | "premium"


@dataclass(frozen=True)
class Loan:
    """A single loan. returned_on is None while the book is still out."""

    id: int
    book_id: int
    member_id: int
    borrowed_on: date
    due_on: date
    returned_on: date | None = None
    late_fee_cents: int = 0

    @property
    def is_active(self) -> bool:
        """True while the loan is still active (not returned)."""
        return self.returned_on is None
