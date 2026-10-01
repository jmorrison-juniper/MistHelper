"""Give every discovery test a controlled shared resolver and finite cleanup."""

from collections.abc import Iterator

import pytest
import structlog

from src.db import host_resolver
from src.upgrade_portal.capture import store
from tests.unit.db_discovery.fakes import ResolverHarness


@pytest.fixture(autouse=True)
def discovery(monkeypatch: pytest.MonkeyPatch) -> Iterator[ResolverHarness]:
    """Keep application DNS inside the test-owned stand-in."""
    monkeypatch.setattr(host_resolver, "logger", structlog.wrap_logger(None, cache_logger_on_first_use=False))
    harness = ResolverHarness(monkeypatch)
    store.reset_connection()
    try:
        yield harness
    finally:
        harness.close()
        store.reset_connection()
