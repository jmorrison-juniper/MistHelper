"""Test safe dependency refusal behavior."""

from __future__ import annotations

from typing import Any

import pytest
from flask import jsonify

from src.interfaces.portals.upgrade_portal.runtime import identity
from tests.integration.upgrade_portal.issue_3834.test_default_provider import (
    FakeArangoClient,
    ProviderHarness,
)


def _failure_probe() -> Any:
    """Map provider failures to the established response statuses."""
    from src.interfaces.portals.upgrade_portal.app import wiring

    try:
        wiring.request_dependencies()
    except wiring.PortalAuthenticationError:
        return jsonify({"error": "not_authenticated"}), 401
    except wiring.PortalDependencyError:
        return jsonify({"error": "service_unavailable"}), 503
    return jsonify({"ready": True})


def test_missing_identity_refuses_before_storage(monkeypatch: pytest.MonkeyPatch) -> None:
    """An unsigned request opens no database client."""
    harness = ProviderHarness(monkeypatch)
    application = harness.application()
    application.add_url_rule("/_test/failure", view_func=_failure_probe)
    response = application.test_client().get("/_test/failure")
    assert response.status_code == 401
    assert FakeArangoClient.instances == []


def test_database_failure_returns_service_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    """A failed database verification returns 503 and closes the partial client."""
    harness = ProviderHarness(monkeypatch)
    application = harness.application()
    application.add_url_rule("/_test/failure", view_func=_failure_probe)
    client, owner, session = harness.signed_client(application, "operator@example.invalid")

    def refuse_database(*args: Any, **kwargs: Any) -> Any:
        """Refuse the database after client construction."""
        del args, kwargs
        raise ConnectionError("fake database refusal")

    monkeypatch.setattr(FakeArangoClient, "db", refuse_database)
    try:
        response = client.get("/_test/failure")
    finally:
        identity.SESSION_REGISTRY.drop(owner.key)
    assert response.status_code == 503
    assert FakeArangoClient.instances[0].closed is True
    assert session.get.call_count == 0
    assert session.post.call_count == 0


def test_legacy_query_adapter_rejects_unbound_input() -> None:
    """The service query adapter rejects text outside its fixed safe shape."""
    from src.interfaces.portals.upgrade_portal.app.wiring import PortalDatabaseGateway

    gateway = PortalDatabaseGateway(FakeArangoClient("fake", 1.0).database)
    with pytest.raises(ValueError, match="unsupported"):
        gateway.query("FOR doc IN upgrade_runs RETURN doc")
