"""Prove issue #3977 mutation routes use fake request-owned resources."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from flask import Flask

from src.interfaces.portals.upgrade_portal.api.run_controls import (
    routes as run_control_routes,
)  # Check the action seam.
from src.interfaces.portals.upgrade_portal.app import wiring  # Install fake request resources.
from src.interfaces.portals.upgrade_portal.app.routes import comparison  # Exercise the registered approval route.


class FakeCloudSession:
    """Reject any unexpected external call from a mutation-route test."""

    def get(self, *args: Any, **kwargs: Any) -> None:
        """Fail if a route sends a live read request."""
        raise AssertionError("The fake cloud session must not make a request.")  # Stop any live network access.

    def post(self, *args: Any, **kwargs: Any) -> None:
        """Fail if a route sends a live mutation request."""
        raise AssertionError("The fake cloud session must not make a request.")  # Stop any live network access.


class FakeDatabaseRouter:
    """Hold request-local database data without connecting to a store."""

    instances: list[FakeDatabaseRouter] = []  # Track routers so request isolation is measurable.

    def __init__(self, config: object) -> None:
        """Record construction so tests can prove request isolation."""
        self.config = config  # Keep the fake settings for construction assertions.
        self.approval_updates: list[dict[str, Any]] = []  # Record approval writes without a store.
        self.run_updates: list[dict[str, Any]] = []  # Record run completion without a store.
        self.audit_entries: list[dict[str, Any]] = []  # Record audit entries without a store.
        type(self).instances.append(self)  # Prove each request receives a new router.

    def get_comparison(self, run_id: str) -> dict[str, Any]:
        """Return a fake unapproved comparison."""
        return {"run_id": run_id, "approved": False}  # Allow one approval attempt.

    def update_comparison(self, run_id: str, update: dict[str, Any]) -> None:
        """Record a fake comparison approval write."""
        self.approval_updates.append(update)  # Keep the submitted update for assertions.

    def update_run(self, run_id: str, update: dict[str, Any]) -> None:
        """Record a fake run-completion write."""
        self.run_updates.append(update)  # Keep the completion update for assertions.

    def write(self, **values: Any) -> SimpleNamespace:
        """Record the audit document without opening a database connection."""
        self.audit_entries.extend(values["data"])  # Record only the fake audit write.
        return SimpleNamespace(success=True, backend=None)  # Match the router write result contract.


class FakeUpgradeService:
    """Capture the request-bound firmware dependencies without doing upgrade work."""

    instances: list[FakeUpgradeService] = []  # Track service ownership across requests.

    def __init__(self, mist_client: Any, db_router: Any, audit_logger: Any) -> None:
        """Record the resources supplied by the request provider."""
        self.mist_client = mist_client  # Hold the authenticated request session.
        self.db_router = db_router  # Hold the request-owned database router.
        self.audit_logger = audit_logger  # Hold the request-owned audit service.
        type(self).instances.append(self)  # Prove service isolation across requests.


class FakeSettleGateService:
    """Capture the request-bound settle-gate dependencies without cloud calls."""

    def __init__(self, mist_client: Any, db_router: Any, audit_logger: Any) -> None:
        """Keep the request resources visible for comparison-service assertions."""
        self.mist_client = mist_client  # Hold the authenticated request session.
        self.db_router = db_router  # Hold the request-owned database router.
        self.audit_logger = audit_logger  # Hold the request-owned audit service.


class FakeComparisonService:
    """Capture comparison dependencies and expose the audit logger to approval."""

    def __init__(self, settle_gate_service: Any, db_router: Any, audit_logger: Any) -> None:
        """Keep the request-scoped collaborators without performing comparison work."""
        self.settle_gate_service = settle_gate_service  # Preserve the settle prerequisite.
        self.db_router = db_router  # Hold the request-owned database router.
        self.audit_logger = audit_logger  # Hold the request-owned audit service.


def _durable_action_store() -> SimpleNamespace:
    """Return a fake durable repository with the complete route contract."""
    names = (  # Match the durable action-store contract.
        "initialize",
        "find_request",
        "read",
        "claim_item",
        "write_outcome",
        "commit_success",
        "finalize",
    )
    return SimpleNamespace(**{name: lambda *args, **kwargs: None for name in names})  # No fake method reaches storage.


def _install_request_fakes(
    monkeypatch: pytest.MonkeyPatch,
    operator: Any,
    action_store: Any = None,
) -> Flask:
    """Install fake request resources and refuse any production connection."""
    FakeDatabaseRouter.instances.clear()  # Isolate this test from earlier fake requests.
    FakeUpgradeService.instances.clear()  # Isolate service assertions.
    monkeypatch.setattr(wiring, "DatabaseConfig", SimpleNamespace(from_env=lambda: object()))  # Block env access.
    monkeypatch.setattr(wiring, "DatabaseRouter", FakeDatabaseRouter)  # Block production storage.
    monkeypatch.setattr(wiring, "current_operator", lambda: operator)  # Supply one test identity.
    modules = {
        wiring.UPGRADE_SERVICE_MODULE: SimpleNamespace(UpgradeService=FakeUpgradeService),
        wiring.SETTLE_GATE_SERVICE_MODULE: SimpleNamespace(SettleGateService=FakeSettleGateService),
        wiring.COMPARISON_SERVICE_MODULE: SimpleNamespace(ComparisonService=FakeComparisonService),
    }
    monkeypatch.setattr(wiring, "load_module", lambda name: modules.get(name))  # Supply fake services only.
    application = Flask(__name__)  # Create a portal without production startup installers.
    application.config[wiring.PORTAL_DEPENDENCY_PROVIDER_KEY] = wiring.PortalDependencyProvider()  # Install provider.
    application.config[wiring.ACTION_STORE_RESOLVER_KEY] = wiring.ActionStoreResolver()  # Install store access.
    application.config["RUN_ACTION_STORE"] = action_store  # Keep the durable store fake.
    return application  # Return the isolated test app.


def _operator(email: str) -> SimpleNamespace:
    """Build one authenticated operator with an isolated fake Mist session."""
    owner = SimpleNamespace(actor_email=email)  # Give the actor a verified identity field.
    return SimpleNamespace(owner=owner, cloud_session=FakeCloudSession())  # Keep every cloud call blocked.


def test_mutation_services_are_cached_per_request_and_isolated_by_operator(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Each request must receive services bound to its own session and router."""
    action_store = _durable_action_store()  # Preserve one process-owned durable repository.
    application = _install_request_fakes(monkeypatch, _operator("first@example.com"), action_store)  # Install fakes.
    request_graphs = []  # Compare request-owned routers after each context.
    upgrade_services = []  # Compare request-owned firmware services after each context.

    for email in ("first@example.com", "second@example.com"):  # Build two independent operator requests.
        operator = _operator(email)  # Keep each session distinct.
        monkeypatch.setattr(wiring, "current_operator", lambda operator=operator: operator)  # Select this actor.
        with application.test_request_context("/"):  # Give the provider one real Flask request scope.
            request_graph = wiring.request_dependencies()  # Resolve the first request graph.
            service = request_graph.mutation_services.resolve(
                wiring.UPGRADE_SERVICE_KEY
            )  # Build fake firmware service.
            assert wiring.request_dependencies() is request_graph  # Reuse the graph inside this request.
            assert request_graph.mutation_services.resolve(wiring.UPGRADE_SERVICE_KEY) is service  # Reuse the service.
            assert request_graph.mutation_services.action_store is action_store  # Keep durable actions process-owned.
            assert service.mist_client is operator.cloud_session  # Bind the service to the signed-in session.
            assert service.db_router is request_graph.database_router  # Bind the service to its request router.
            assert service.audit_logger.db_router is request_graph.database_router  # Bind audit writes to that router.
            request_graphs.append(request_graph)  # Retain the request graph for isolation checks.
            upgrade_services.append(service)  # Retain the service for isolation checks.

    assert request_graphs[0].database_router is not request_graphs[1].database_router  # Prevent router sharing.
    assert upgrade_services[0] is not upgrade_services[1]  # Prevent service sharing.


def test_comparison_approval_uses_authenticated_actor_and_request_audit_store(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Approval must ignore a spoofed actor header and write through fake resources."""
    operator = _operator("verified@example.com")  # Supply the authenticated actor.
    application = _install_request_fakes(monkeypatch, operator, _durable_action_store())  # Install only fake stores.
    application.register_blueprint(comparison.comparison_bp)  # Mount the production approval route.

    response = application.test_client().post(
        "/api/runs/run-1/comparison/approve",
        json={"approved_items": ["delta-1"], "rejected_items": [], "approve_all": False},
        headers={"X-User-ID": "spoofed@example.com"},
    )

    assert response.status_code == 200  # Confirm approval completed with fake dependencies.
    router = FakeDatabaseRouter.instances[0]  # Read the request-owned fake router.
    assert router.approval_updates[0]["approved_by"] == "verified@example.com"  # Ignore the spoofed header.
    assert router.run_updates[0]["status"] == "completed"  # Preserve the durable run status update.
    assert router.audit_entries[0]["user_id"] == "verified@example.com"  # Preserve the trusted audit actor.
    assert router.audit_entries[0]["operation"] == "approve_comparison"  # Preserve the audit event.


def test_comparison_approval_refuses_without_authenticated_operator(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Approval must refuse before database construction when the actor is absent."""
    application = _install_request_fakes(monkeypatch, None, _durable_action_store())  # Remove the authenticated actor.
    application.register_blueprint(comparison.comparison_bp)  # Mount the production approval route.

    response = application.test_client().post(
        "/api/runs/run-1/comparison/approve",
        json={"approved_items": [], "rejected_items": [], "approve_all": True},
        headers={"X-User-ID": "spoofed@example.com"},
    )

    assert response.status_code == 401  # Keep the standard unauthenticated refusal.
    assert FakeDatabaseRouter.instances == []  # Refuse before opening the request database router.


def test_comparison_approval_refuses_when_request_provider_is_missing() -> None:
    """Approval must refuse before a write when mutation wiring is absent."""
    FakeDatabaseRouter.instances.clear()  # Isolate the no-provider check.
    application = Flask(__name__)  # Create an app with no request provider.
    application.register_blueprint(comparison.comparison_bp)  # Mount the production approval route.

    response = application.test_client().post(
        "/api/runs/run-1/comparison/approve",
        json={"approved_items": [], "rejected_items": [], "approve_all": True},
    )

    assert response.status_code == 503  # Refuse when mutation wiring is missing.
    assert FakeDatabaseRouter.instances == []  # Do not construct any database resource.


def test_run_control_action_store_comes_from_the_request_graph(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Run-control routes must resolve durable storage without opening a request router."""
    action_store = _durable_action_store()  # Keep a process-owned repository.
    application = _install_request_fakes(monkeypatch, _operator("operator@example.com"), action_store)  # Install fakes.

    with application.test_request_context("/"):  # Use the provider inside one authenticated request.
        assert run_control_routes._action_store() is action_store  # Return the durable repository.
    assert FakeDatabaseRouter.instances == []  # The shared store does not require a request router.


def test_run_control_action_store_refuses_when_request_provider_is_missing() -> None:
    """Run-control routes must refuse when request resources are not installed."""
    application = Flask(__name__)  # Omit the provider to exercise the fail-closed path.
    application.config["RUN_ACTION_STORE"] = _durable_action_store()  # A global store must not bypass the provider.

    with application.test_request_context("/"):  # Supply the Flask request required by the route helper.
        with pytest.raises(run_control_routes.ActionStoreUnavailable):  # Require a typed refusal.
            run_control_routes._action_store()  # Do not proceed without durable action storage.


def test_e2e_dependency_installation_keeps_the_request_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    """E2E overrides must expose their fake action store through the request provider."""
    FakeDatabaseRouter.instances.clear()  # Isolate the no-router assertion from earlier tests.
    action_store = _durable_action_store()  # Keep the test repository isolated from production storage.
    overrides = SimpleNamespace(config_values=lambda: {"RUN_ACTION_STORE": action_store})  # Supply only fake seams.
    application = Flask(__name__)  # Create an app with no production startup.
    monkeypatch.setattr(wiring, "prepare_storage", lambda: pytest.fail("E2E installation opened production storage"))

    wiring.install_seams(application, overrides)  # Install the same provider used by production routes.

    with application.test_request_context("/"):  # Resolve dependencies only inside one fake request.
        assert wiring.request_action_store() is action_store  # Return the configured fake repository.
    assert FakeDatabaseRouter.instances == []  # E2E action access must not construct a production router.
