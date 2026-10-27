"""Domain errors. The API layer maps them to HTTP status codes."""


class LendingError(Exception):
    """Base class for all business rule errors. Maps to HTTP 409."""


class NotFound(LendingError):
    """The requested member, book, or loan does not exist. Maps to HTTP 404."""


class BorrowLimitReached(LendingError):
    """The member already has the maximum number of active loans."""


class NoCopiesAvailable(LendingError):
    """All copies of the book are on loan."""


class LoanAlreadyReturned(LendingError):
    """The loan was already returned and cannot change."""
