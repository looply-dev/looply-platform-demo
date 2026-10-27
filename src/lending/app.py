"""Composition root: the only place that knows about storage, services, and api together."""

from lending.services.clock import Clock, SystemClock
from lending.services.lending_service import LendingService
from lending.storage.db import connect
from lending.storage.repository import LibraryRepository


def build_service(db_path: str, clock: Clock | None = None) -> tuple[LendingService, LibraryRepository]:
    """Build a LendingService for a database path. Also return the repository for seeding data."""
    repo = LibraryRepository(connect(db_path))
    return LendingService(repo, clock or SystemClock()), repo
