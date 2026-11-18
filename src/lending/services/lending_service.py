"""Lending use cases: combine domain rules with storage reads and writes. The API layer calls only this module."""

from dataclasses import dataclass
from datetime import date

from lending.domain import rules
from lending.domain.errors import (
    BorrowLimitReached,
    LoanAlreadyReturned,
    NoCopiesAvailable,
    NotFound,
    RenewLimitReached,
)
from lending.domain.models import Loan
from lending.services.clock import Clock
from lending.storage.repository import LibraryRepository


@dataclass(frozen=True)
class ReturnReceipt:
    """Return receipt: the returned loan and the late fee it produced."""

    loan: Loan
    late_fee_cents: int


class LendingService:
    """Entry point for borrowing, returning, and listing loans."""

    def __init__(self, repo: LibraryRepository, clock: Clock):
        self._repo = repo
        self._clock = clock

    def borrow(self, member_id: int, book_id: int) -> Loan:
        """Borrow a book for a member. Checks the member, the book, the loan limit, and stock, in that order."""
        member = self._repo.get_member(member_id)
        if member is None:
            raise NotFound(f"member {member_id} not found")
        book = self._repo.get_book(book_id)
        if book is None:
            raise NotFound(f"book {book_id} not found")

        active = self._repo.count_active_loans_for_member(member_id)
        if not rules.can_borrow(member, active):
            raise BorrowLimitReached(f"member {member_id} already has {active} active loans")

        if self._repo.count_active_loans_for_book(book_id) >= book.total_copies:
            raise NoCopiesAvailable(f"no copies of book {book_id} available")

        today = self._clock.today()
        return self._repo.create_loan(book_id, member_id, today, rules.due_date_for(today))

    def return_book(self, loan_id: int) -> ReturnReceipt:
        """Return a loan and charge the late fee as of today."""
        loan = self._repo.get_loan(loan_id)
        if loan is None:
            raise NotFound(f"loan {loan_id} not found")
        if not loan.is_active:
            raise LoanAlreadyReturned(f"loan {loan_id} was already returned")

        today = self._clock.today()
        fee = rules.late_fee_cents(loan.due_on, today)
        return ReturnReceipt(self._repo.mark_returned(loan_id, today, fee), fee)

    def renew(self, loan_id: int) -> Loan:
        """Renew a loan: a full new loan period starts today."""
        loan = self._repo.get_loan(loan_id)
        if loan is None:
            raise NotFound(f"loan {loan_id} not found")
        if not loan.is_active:
            raise LoanAlreadyReturned(f"loan {loan_id} was already returned")
        if not rules.can_renew(loan.renew_count):
            raise RenewLimitReached(f"loan {loan_id} has been renewed {loan.renew_count} times")

        new_due_on = rules.due_date_for(date.today())
        return self._repo.renew_loan(loan_id, new_due_on)

    def member_loans(self, member_id: int) -> list[Loan]:
        """List all loans of a member."""
        if self._repo.get_member(member_id) is None:
            raise NotFound(f"member {member_id} not found")
        return self._repo.list_loans_for_member(member_id)
