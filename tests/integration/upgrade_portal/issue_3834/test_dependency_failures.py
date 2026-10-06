"""Test authentication and construction refusal before external work."""

from __future__ import annotations

from types import SimpleNamespace  # Builds one stale operator record.

import pytest  # The tests replace each construction boundary.

from src.interfaces.portals.upgrade_portal.app import wiring  # The provider under test.
from tests.integration.upgrade_portal.issue_3834.test_default_provider import (
    FakeDatabaseConfig,
    FakeDatabaseRouter,
    build_application,
)


def test_absent_identity_constructs_no_router(monkeypatch: pytest.MonkeyPatch) -> None:
    """An absent operator fails before configuration or router construction."""
    application = build_application(monkeypatch)  # Block every real external connection.
    monkeypatch.setattr(wiring, "current_operator", lambda: None)  # Simulate an unsigned request.
    with application.test_request_context("/"):  # Give the provider a Flask request context.
        with pytest.raises(wiring.PortalAuthenticationError, match="operator session"):
            wiring.request_dependencies()  # Refuse before the database boundary.
    assert FakeDatabaseConfig.calls == 0  # Authentication must precede environment and DNS reads.
    assert FakeDatabaseRouter.instances == []  # No router exists for an absent identity.


def test_stale_identity_constructs_no_router(monkeypatch: pytest.MonkeyPatch) -> None:
    """An unusable borrowed session fails before storage construction."""
    application = build_application(monkeypatch)  # Block every real external connection.
    stale_operator = SimpleNamespace(cloud_session=object())  # Missing request methods marks the session stale.
    monkeypatch.setattr(wiring, "current_operator", lambda: stale_operator)  # Return the stale registry record.
    with application.test_request_context("/"):  # Give the provider a Flask request context.
        with pytest.raises(wiring.PortalAuthenticationError, match="operator session"):
            wiring.request_dependencies()  # Refuse before the database boundary.
    assert FakeDatabaseConfig.calls == 0  # A stale session must not read database settings.
    assert FakeDatabaseRouter.instances == []  # A stale session must not own storage.


def test_configuration_failure_reports_dependency_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """A request-time database configuration fault remains explicit."""
    application = build_application(monkeypatch)  # Register teardown without external connections.
    active_session = SimpleNamespace(get=lambda: None, post=lambda: None)  # Expose the required Mist methods.
    operator = SimpleNamespace(cloud_session=active_session)  # Build one usable operator record.
    monkeypatch.setattr(wiring, "current_operator", lambda: operator)  # Pass authentication.

    class RefusingConfig:
        """Raise at the real request-time configuration boundary."""

        @classmethod
        def from_env(cls) -> object:
            """Report a safe configuration failure."""
            raise RuntimeError("blocked test configuration")

    monkeypatch.setattr(wiring, "DatabaseConfig", RefusingConfig)  # Block construction at the first resource step.
    with application.test_request_context("/"):  # Give the provider a Flask request context.
        with pytest.raises(wiring.PortalDependencyError, match="database resources"):
            wiring.request_dependencies()  # Convert the implementation fault to the typed boundary.
    assert FakeDatabaseRouter.instances == []  # A failed configuration cannot create a router.
