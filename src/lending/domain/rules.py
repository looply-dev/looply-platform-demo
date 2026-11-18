"""Lending business rules.

This module holds pure functions only: same input, same output. They do not read
the clock or touch the database, so they are easy to unit test and to check in review.
All money is in integer cents. Never use float for money.
"""

from datetime import date, timedelta

from lending.domain.models import Member

LOAN_PERIOD_DAYS = 14
MAX_ACTIVE_LOANS = {"standard": 3, "premium": 5}
DAILY_LATE_FEE_CENTS = 50
MAX_LATE_FEE_CENTS = 2000
MAX_RENEWALS = 2


def due_date_for(borrowed_on: date) -> date:
    """Return the due date for a loan that starts on borrowed_on."""
    return borrowed_on + timedelta(days=LOAN_PERIOD_DAYS)


def can_borrow(member: Member, active_loan_count: int) -> bool:
    """Return True if the member can borrow one more book. Unknown tiers count as standard."""
    limit = MAX_ACTIVE_LOANS.get(member.tier, MAX_ACTIVE_LOANS["standard"])
    return active_loan_count < limit


def late_fee_cents(due_on: date, returned_on: date) -> int:
    """Return the late fee in cents: a daily fee with a cap. Early or on-time returns cost 0."""
    days_late = max(0, (returned_on - due_on).days)
    return min(days_late * DAILY_LATE_FEE_CENTS, MAX_LATE_FEE_CENTS)


def can_renew(renew_count: int) -> bool:
    """Return True if the loan can be renewed. A loan can be renewed at most MAX_RENEWALS times."""
    return renew_count <= MAX_RENEWALS
