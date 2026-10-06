"""Test request graph isolation and cleanup."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Any

import pytest

from src.interfaces.portals.upgrade_portal.runtime import identity
from tests.integration.upgrade_portal.issue_3834.test_default_provider import (
    FakeArangoClient,
    ProviderHarness,
)


def test_concurrent_operators_receive_distinct_cleaned_resources(monkeypatch: pytest.MonkeyPatch) -> None:
    """Concurrent signed requests share no request-owned database client."""
    harness = ProviderHarness(monkeypatch)
    application = harness.application()
    first, first_owner, _ = harness.signed_client(application, "first@example.invalid")
    second, second_owner, _ = harness.signed_client(application, "second@example.invalid")

    def read(client: Any) -> int:
        """Resolve one complete graph."""
        return client.get("/_test/dependencies").status_code

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            statuses = list(executor.map(read, (first, second)))
    finally:
        identity.SESSION_REGISTRY.drop(first_owner.key)
        identity.SESSION_REGISTRY.drop(second_owner.key)
    assert statuses == [200, 200]
    assert len(FakeArangoClient.instances) == 2
    assert FakeArangoClient.instances[0] is not FakeArangoClient.instances[1]
    assert all(client.closed for client in FakeArangoClient.instances)
