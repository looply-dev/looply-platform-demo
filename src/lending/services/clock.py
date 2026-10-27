"""Clock abstraction. Business code asks a Clock for "today", so tests can inject a fixed date."""

from datetime import date, timedelta
from typing import Protocol


class Clock(Protocol):
    """Interface that supplies the current date."""

    def today(self) -> date: ...


class SystemClock:
    """The real clock, used in production."""

    def today(self) -> date:
        return date.today()


class FixedClock:
    """Test clock: returns a fixed date that advance() moves forward."""

    def __init__(self, current: date):
        self.current = current

    def today(self) -> date:
        return self.current

    def advance(self, days: int) -> None:
        """Move the clock forward by the given number of days."""
        self.current = self.current + timedelta(days=days)
