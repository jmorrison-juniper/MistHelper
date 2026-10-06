"""Test the normal-startup request resource provider."""

from __future__ import annotations

from types import SimpleNamespace  # Builds small operator records without production credentials.
from typing import Any  # The stand-ins accept the production constructor shapes.

import pytest  # The tests replace every external construction boundary.
from flask import Flask, g  # The startup and ownership tests read the Flask application state.

from src.interfaces.portals.upgrade_portal.app import factory, wiring  # The two authorized production modules.


class FakeCloudSession:
    """Stand for one registry-owned Mist session."""

    def __init__(self) -> None:
        """Start with no close call."""
        self.close_count = 0  # A request must never close this borrowed session.

    def get(self, *_args: Any, **_kwargs: Any) -> None:
        """Expose the Mist session read method without a cloud call."""

    def post(self, *_args: Any, **_kwargs: Any) -> None:
        """Expose the Mist session write method without a cloud call."""

    def close(self) -> None:
        """Record an incorrect ownership decision."""
        self.close_count += 1  # Any nonzero value fails the ownership tests.


class FakeDatabaseConfig:
    """Record each request-time configuration build."""

    calls = 0  # Tests reset this shared count before each application.

    @classmethod
    def from_env(cls) -> object:
        """Return one opaque configuration without environment access."""
        cls.calls += 1  # One authenticated request must build one configuration.
        return object()  # The fake router only checks object identity.


class FakeDatabaseRouter:
    """Stand for one real request-owned database router."""

    instances: list[FakeDatabaseRouter] = []  # Tests inspect construction and cleanup.

    def __init__(self, config: object, strategies: dict[str, Any] | None = None) -> None:
        """Record the real constructor shape without an external connection."""
        self.config = config  # The provider must pass the result of `from_env`.
        self.strategies = strategies  # The provider must keep the optional default.
        self.close_count = 0  # Factory teardown must close this router once.
        self.instances.append(self)  # Each request must add a distinct owned router.

    def close(self) -> None:
        """Record request teardown."""
        self.close_count += 1  # A second close would show duplicate lifecycle ownership.


def install_resource_stand_ins(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replace request resource construction and existing startup connections."""
    FakeDatabaseConfig.calls = 0  # Each test starts with no request configuration.
    FakeDatabaseRouter.instances = []  # Each test owns its router evidence.
    monkeypatch.setattr(wiring, "DatabaseConfig", FakeDatabaseConfig)  # Block DNS and environment reads.
    monkeypatch.setattr(wiring, "DatabaseRouter", FakeDatabaseRouter)  # Block all database connections.
    monkeypatch.setattr(
        wiring,
        "_install_action_repository",
        lambda app: app.config.setdefault("RUN_ACTION_STORE", object()),
    )  # Keep the existing startup seam without its database probe.
    monkeypatch.setattr(wiring, "prepare_storage", lambda: None)  # Keep startup independent from a real store.


def build_application(monkeypatch: pytest.MonkeyPatch) -> Flask:
    """Build the normal WSGI application with external connections blocked."""
    install_resource_stand_ins(monkeypatch)  # Replace each external construction boundary first.
    return factory.create_app()  # Use the same no-argument path as Gunicorn.


def build_operator(session: FakeCloudSession | object) -> SimpleNamespace:
    """Build one operator record with a borrowed cloud session."""
    return SimpleNamespace(cloud_session=session)  # The provider reads this existing identity shape.


def test_default_startup_preserves_existing_order_and_installs_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Normal startup installs construction rules and preserves all existing calls."""
    events: list[str] = []  # Record the existing startup order without external work.

    class StartupConfigTrap:
        """Refuse request configuration during application startup."""

        @classmethod
        def from_env(cls) -> object:
            """Fail if the new provider constructs a startup resource."""
            raise AssertionError("The provider built request configuration during startup.")

    def record_action(app: Flask) -> None:
        """Record the action repository call after provider installation."""
        assert isinstance(
            app.config.get(wiring.PORTAL_DEPENDENCY_PROVIDER_KEY),
            wiring.PortalDependencyProvider,
        )  # The provider must follow the run seams and precede existing startup work.
        events.append("action")  # Preserve the first existing dependency call.

    def recorder(name: str) -> Any:
        """Build one service installer recorder."""

        def record(_app: Flask) -> None:
            """Record one unchanged service installation position."""
            events.append(name)  # The sequence proves no service installer moved.

        return record  # The monkeypatch needs one callable for each installer.

    monkeypatch.setattr(wiring, "DatabaseConfig", StartupConfigTrap)  # Detect eager provider construction.
    monkeypatch.setattr(
        wiring,
        "DatabaseRouter",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("The provider built a database router during startup.")
        ),
    )  # Detect a new startup connection.
    monkeypatch.setattr(wiring, "_install_action_repository", record_action)  # Preserve the first existing call.
    monkeypatch.setattr(wiring, "_install_capture_service", recorder("capture"))  # Preserve capture installation.
    monkeypatch.setattr(wiring, "_install_upgrade_service", recorder("upgrade"))  # Preserve upgrade installation.
    monkeypatch.setattr(wiring, "_install_settle_gate_service", recorder("settle"))  # Preserve settle installation.
    monkeypatch.setattr(wiring, "_install_comparison_service", recorder("comparison"))  # Preserve comparison setup.
    monkeypatch.setattr(wiring, "prepare_storage", lambda: events.append("storage"))  # Preserve final bootstrap.
    application = factory.create_app()  # Build the normal WSGI target.
    assert isinstance(application, Flask)  # Startup must still return the application.
    assert events == ["action", "capture", "upgrade", "settle", "comparison", "storage"]  # Exact existing order.


def test_authenticated_resolution_builds_real_resource_shape(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The first authenticated resolution builds the configured real boundary."""
    application = build_application(monkeypatch)  # Register normal teardown with blocked connectors.
    cloud_session = FakeCloudSession()  # The identity registry owns this borrowed object.
    operator = build_operator(cloud_session)  # Use the real operator attribute shape.
    monkeypatch.setattr(wiring, "current_operator", lambda: operator)  # Supply one authenticated request.
    with application.test_request_context("/"):  # Open one lifecycle boundary.
        dependencies = wiring.request_dependencies()  # Construct one request resource graph.
        router = dependencies.database_router  # Keep the owned handle for post-teardown checks.
        assert dependencies.operator is operator  # Preserve the validated operator by reference.
        assert dependencies.cloud_session is cloud_session  # Borrow the registry session by reference.
        assert router is FakeDatabaseRouter.instances[0]  # Use the real router constructor seam.
        assert FakeDatabaseConfig.calls == 1  # Build configuration only when the request resolves.
        assert not hasattr(g, "mist_session")  # Keep the borrowed Mist session outside factory teardown.
    assert router.close_count == 1  # Existing factory teardown closes the owned router.
    assert cloud_session.close_count == 0  # Teardown never closes the borrowed Mist session.
