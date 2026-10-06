"""Prove request graphs and their resources do not cross operator boundaries."""

from __future__ import annotations  # Keep annotations independent from import order.

from concurrent.futures import ThreadPoolExecutor  # Overlap two authenticated request handlers.
from threading import Barrier  # Hold both handlers inside dependency resolution.
from typing import Any  # The fake database boundaries carry mixed records.

import pytest  # The test runner restores the constructor traps.

from src.interfaces.portals.upgrade_portal.runtime import identity  # Use the real browser and owner registry.
from tests.integration.upgrade_portal.issue_3834.test_default_provider import ProviderDoubles


def test_two_operators_receive_distinct_graphs_and_owned_resources(monkeypatch: pytest.MonkeyPatch) -> None:
    """Overlapping requests use their own cloud session, router, and client."""
    harness = ProviderDoubles()  # One holder records both request graphs.
    harness.install(monkeypatch)  # Every database connection remains a fake.
    harness.barrier = Barrier(2)  # Both route handlers must overlap before either response returns.
    application = harness.create_app()  # The provider rules live in app config, not the request graph.
    first_client, first_owner = harness.signed_client(application, "first.operator@example.invalid")
    second_client, second_owner = harness.signed_client(application, "second.operator@example.invalid")

    def read(client: Any) -> int:
        """Run one provider request through its own Flask client."""
        return client.get("/_test/request-dependencies").status_code  # The route waits at the shared barrier.

    try:  # Both registry entries remain available until both workers finish.
        with ThreadPoolExecutor(max_workers=2) as pool:
            statuses = list(pool.map(read, (first_client, second_client)))
    finally:
        identity.SESSION_REGISTRY.drop(first_owner.key)  # The registry outlives both request contexts.
        identity.SESSION_REGISTRY.drop(second_owner.key)  # Each test owner has one explicit cleanup.

    first, second = harness.dependencies  # The route recorded one graph from each request.
    assert statuses == [200, 200]  # Both providers completed their own graph.
    assert first is not second  # Flask g never shares one graph across requests.
    assert first.operator is not second.operator  # Each graph keeps its own registry record.
    assert first.resources.database_router is not second.resources.database_router  # Routers are request-owned.
    assert first.resources.database_client is not second.resources.database_client  # Clients are request-owned.
    assert first.services.capture.mist_client is first.operator.cloud_session  # Every call gets the first session.
    assert second.services.capture.mist_client is second.operator.cloud_session  # Every call gets the second session.
    assert all(client.closed for client in harness.clients)  # Teardown closes both owned document clients.
    assert all(writer.closed for writer in harness.writer_instances)  # Teardown closes each owned router writer.
    assert all(not session.closed for session in harness.sessions)  # Teardown leaves borrowed sessions open.


def test_partial_client_open_closes_once_and_later_request_recovers(monkeypatch: pytest.MonkeyPatch) -> None:
    """A document-client failure leaves no shared failure state for the next request."""
    harness = ProviderDoubles()  # Record the failed and recovered request resources.
    harness.install(monkeypatch)  # Use only fake connection boundaries.
    application = harness.create_app()  # The app stores no live resource.
    client, owner = harness.signed_client(application, "recovery.operator@example.invalid")
    original_db = ProviderDoubles.ArangoClient.db  # Preserve the supported fake method after the fault.
    attempts = 0  # Fail exactly the first owned client.

    def fail_first_open(
        current: ProviderDoubles.ArangoClient,
        name: str,
        username: str,
        password: str,
        verify: bool = False,
    ) -> ProviderDoubles.Database:
        """Refuse one document open, then use the strict fake method."""
        nonlocal attempts
        attempts += 1  # Count the partial-construction attempt.
        if attempts == 1:
            raise ConnectionError("fake store refusal")  # The provider logs only this safe type.
        return original_db(current, name, username, password, verify)  # Let the next request recover.

    monkeypatch.setattr(ProviderDoubles.ArangoClient, "db", fail_first_open)
    try:  # Keep the real owner registered across both requests.
        failed = client.get("/_test/request-dependencies")
        recovered = client.get("/_test/request-dependencies")
    finally:
        identity.SESSION_REGISTRY.drop(owner.key)  # Remove the registry record after recovery.

    assert failed.status_code == 500  # The test probe reports its dependency exception.
    assert recovered.status_code == 200  # A later request builds a fresh graph.
    assert harness.clients[0].closed is True  # Partial construction closes its owned client.
    assert harness.clients[1].closed is True  # Successful construction closes at request teardown.
    assert len(harness.dependencies) == 1  # Only the recovered request publishes a graph.
    assert harness.sessions[0].closed is False  # Neither request owns the registry session.


def test_capture_worker_owns_storage_after_request_teardown(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep the worker client open after the request and close it after collection."""
    from flask import jsonify  # The probe route returns no worker resources.

    from src.interfaces.portals.upgrade_portal.app.routes import capture as capture_routes

    harness = ProviderDoubles()  # The worker uses the same strict fake Arango boundary.
    harness.install(monkeypatch)  # No production database or cloud call can run.
    application = harness.create_app()  # The app stores provider settings only.
    client, owner = harness.signed_client(application, "worker.operator@example.invalid")
    observed: list[Any] = []  # The fake collector records only its bound session and resources.
    workers: list[Any] = []  # The test starts the worker after its request ends.

    class Collector:
        """Replace the cloud reads while keeping the production runner path."""

        @staticmethod
        def run_capture(job: dict[str, Any], resources: Any = None) -> None:
            """Record the request-bound session and storage."""
            del job  # The worker job stays out of test output.
            observed.append(resources)  # The resources remain live until this call returns.

    class DeferredWorker:
        """Hold a worker target until the request context has ended."""

        def __init__(self, target: Any, args: tuple[Any, ...], **kwargs: Any) -> None:
            """Keep the target and arguments without starting a thread."""
            del kwargs  # Thread naming does not change the ownership check.
            self.target = target  # The worker body owns cleanup.
            self.args = args  # The app context is created before the response.

        def start(self) -> None:
            """Record that the request handed off the worker."""
            workers.append(self)  # The test starts this exact worker after teardown.

    def launch_worker() -> Any:
        """Bind the signed session and start one deferred worker."""
        record = identity.current_session()  # The real browser registry owns this session.
        capture_routes.start_worker(
            {
                "capture_id": "cap-worker-lifetime",
                "cloud_session": record.cloud_session,
                "actor_email": record.owner.actor_email,
            }
        )  # Bind storage and session before the route returns.
        return jsonify({"queued": True})  # Keep the worker object out of the response.

    monkeypatch.setattr(capture_routes, "load_optional_module", lambda _name: Collector)
    monkeypatch.setattr(capture_routes.threading, "Thread", DeferredWorker)
    application.add_url_rule("/_test/start-worker", view_func=launch_worker)
    try:
        response = client.get("/_test/start-worker")
        worker_client = harness.clients[-1]  # The last client belongs to this worker.
        assert response.status_code == 200  # The request handed off its work.
        assert worker_client.closed is False  # Request teardown cannot close worker storage.
        assert harness.sessions[0].closed is False  # The worker borrows the registry session.
        workers[0].target(*workers[0].args)  # Finish the work after the request context has ended.
    finally:
        identity.SESSION_REGISTRY.drop(owner.key)  # Remove the test owner after worker completion.

    assert len(observed) == 1  # The production collector ran exactly once.
    assert observed[0].session is harness.sessions[0]  # The worker receives the authenticated session.
    assert worker_client.closed is True  # Worker teardown closes its own database client.
    assert harness.sessions[0].closed is False  # Worker teardown leaves the borrowed session open.


def test_upgrade_worker_bindings_own_their_database(monkeypatch: pytest.MonkeyPatch) -> None:
    """Bind the upgrade driver store before request teardown closes other handles."""
    from flask import jsonify  # The probe returns no worker details.

    from src.interfaces.portals.upgrade_portal.app import wiring

    harness = ProviderDoubles()  # The driver binds to a strict fake document client.
    harness.install(monkeypatch)  # No production database or Mist access is available.
    application = harness.create_app()  # The factory stores only portal settings and provider rules.
    client, owner = harness.signed_client(application, "upgrade.worker@example.invalid")
    bindings: list[dict[str, Any]] = []  # Hold the returned scope until the test simulates worker completion.
    monkeypatch.setattr(wiring, "read_lock_record", lambda _site_id: None)  # The fake operator holds no lock.

    def read_worker_bindings() -> Any:
        """Resolve one worker scope inside an authenticated request."""
        bindings.append(wiring.request_bindings({"run_id": "run-worker", "site_id": "site-worker"}))
        return jsonify({"ready": True})  # Do not serialize the worker session or database.

    application.add_url_rule("/_test/worker-bindings", view_func=read_worker_bindings)
    try:
        response = client.get("/_test/worker-bindings")
        worker_client = harness.clients[-1]  # The worker owns the newest client.
        worker_scope = bindings[0]  # The binding outlives this request.
        assert response.status_code == 200  # The signed request built the worker scope.
        assert worker_scope["store"].database is worker_client.database  # Run writes use worker-owned storage.
        assert worker_client.closed is False  # Request teardown cannot close the worker client.
        assert harness.sessions[0].closed is False  # The session remains owned by the registry.
        worker_scope["worker_cleanup"]()  # Simulate the final write of the driver thread.
    finally:
        if bindings and harness.clients and not harness.clients[-1].closed:
            bindings[0]["worker_cleanup"]()  # Release the worker client after a failed assertion.
        identity.SESSION_REGISTRY.drop(owner.key)  # Remove the signed registry record.

    assert worker_client.closed is True  # The worker closes its own client after its final write.
    assert harness.sessions[0].closed is False  # The worker never closes the borrowed session.
