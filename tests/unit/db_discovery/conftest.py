"""Give every discovery test a controlled shared resolver and finite cleanup."""

from collections.abc import Iterator

import pytest
import structlog

from src.foundation.persistence.db import DatabaseConfig
from src.foundation.persistence.db.backends import arango_writer
from src.foundation.persistence.db.support import host_resolver
from src.interfaces.portals.upgrade_portal.capture import store
from tests.unit.db_discovery.fakes import ResolverHarness


@pytest.fixture(autouse=True)
def discovery(monkeypatch: pytest.MonkeyPatch) -> Iterator[ResolverHarness]:
    """Keep application DNS inside the test-owned stand-in."""
    monkeypatch.setattr(
        host_resolver,
        "logger",
        structlog.wrap_logger(structlog.testing.CapturingLogger(), cache_logger_on_first_use=False),
    )
    monkeypatch.setattr(
        arango_writer,
        "logger",
        structlog.wrap_logger(structlog.testing.CapturingLogger(), cache_logger_on_first_use=False),
    )
    harness = ResolverHarness(monkeypatch)
    store.reset_connection()
    try:
        yield harness
    finally:
        harness.close()
        store.reset_connection()


@pytest.fixture
def remote_arango_config() -> DatabaseConfig:
    """Keep the exact URL and credentials separate from driver execution."""
    return DatabaseConfig(
        arango_host="https://uri-user:controlled-value@external-arango.invalid:9443",
        arango_database="misthelper-tmp-issue3318-preflight",
        arango_username="controlled-user",
        arango_password="controlled" + "-value",
    )
