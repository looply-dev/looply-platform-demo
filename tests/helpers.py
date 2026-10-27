"""Shared test setup: in-memory database plus a fixed clock."""

from datetime import date

from lending.app import build_service
from lending.services.clock import FixedClock

START = date(2026, 1, 5)


def make_env():
    """Return (service, repo, clock) backed by an empty in-memory SQLite database, with the date fixed at START."""
    clock = FixedClock(START)
    service, repo = build_service(":memory:", clock)
    return service, repo, clock
