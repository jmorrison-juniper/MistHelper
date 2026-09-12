"""Tests for the graceful shutdown path in the web portal.

Issue #1861 reported that nothing stopped the event bus heartbeat thread
or the operation pool. A restart aborted an in-flight run and leaked the
heartbeat thread. These tests hold the fix in place.
"""

import time

import pytest

from web_portal.app import WebPortalApp
from web_portal.menu_registry import build_static_menu_actions
from web_portal.services.event_bus import PortalEventBus
from web_portal.services.operation import OperationExecutor


def _menu_actions() -> dict:
    """Return one harmless menu entry for the executor under test."""
    return {"11": (lambda: None, "Export the organization inventory")}  # A no-op action needs no cleanup.


def _slow_menu_actions(hold_seconds: float) -> dict:
    """Return one menu entry whose action sleeps, so a run stays in flight."""
    # The sleep keeps the run active, so a test can call shutdown() while it runs.
    return {"11": (lambda: time.sleep(hold_seconds), "Sleep for a bounded time")}


@pytest.fixture
def event_bus():
    """Return a started PortalEventBus, stopped again after the test."""
    bus = PortalEventBus()  # Build one bus per test, so tests cannot share thread state.
    bus.start()  # Start the heartbeat thread, matching how app.py starts the real bus.
    yield bus
    bus.stop()  # A second stop() is a safe no-op, so an already-stopped bus raises nothing.


@pytest.fixture
def executor_factory():
    """Return a factory that builds an OperationExecutor, shut down after the test."""
    created = []  # Track every executor the test built, so teardown can shut down each one.

    def _build(menu_actions: dict) -> OperationExecutor:
        executor = OperationExecutor(menu_actions, None, None, None)  # No apisession/org_id/bus needed here.
        created.append(executor)  # Remember it, so teardown can find it.
        return executor

    yield _build
    for executor in created:
        executor.shutdown()  # A second shutdown() is a safe no-op, so a torn-down executor raises nothing.


def _build_test_app():
    """Return a real WebPortalApp Flask instance for shutdown tests."""
    # build_static_menu_actions avoids a MistHelper import, matching tests/e2e/conftest.py.
    menu_actions = build_static_menu_actions()
    return WebPortalApp.create_app(apisession=None, menu_actions=menu_actions, org_id="test-org-id")


def test_event_bus_stop_ends_the_heartbeat_thread(event_bus):
    """stop() ends the heartbeat thread, so it does not leak past the app."""
    thread = event_bus._heartbeat_thread  # Hold the handle, because stop() clears the attribute.
    assert thread.is_alive()  # The thread must be alive right after start().
    event_bus.stop()  # Run the code under test.
    assert not thread.is_alive()  # The thread must be gone right after stop() returns.


def test_event_bus_stop_is_idempotent(event_bus):
    """A second stop() call does not raise."""
    event_bus.stop()  # First call performs the real stop.
    event_bus.stop()  # Second call must return quietly, not raise.


def test_operation_executor_shutdown_stops_the_pool(executor_factory):
    """shutdown() closes the pool, so a new submit() is refused."""
    executor = executor_factory(_menu_actions())  # Build one executor for this test.
    executor.shutdown()  # Run the code under test.
    with pytest.raises(RuntimeError):  # A closed ThreadPoolExecutor refuses new work.
        executor._pool.submit(lambda: None)


def test_operation_executor_shutdown_is_idempotent(executor_factory):
    """A second shutdown() call does not raise."""
    executor = executor_factory(_menu_actions())  # Build one executor for this test.
    executor.shutdown()  # First call performs the real shutdown.
    executor.shutdown()  # Second call must return quietly, not raise.


def test_operation_executor_shutdown_waits_for_an_in_flight_run(executor_factory):
    """shutdown() waits for a short in-flight run within the grace period."""
    executor = executor_factory(_slow_menu_actions(0.2))  # The run sleeps 0.2s, well under the grace period.
    run = executor.start_operation("11", {})  # Start the run, so a future is in flight.
    executor.shutdown(grace_seconds=2)  # Wait up to 2s, far more than the run needs.
    future = executor._runs[run["run_id"]]["_future"]  # Read back the tracked future.
    assert future.done()  # The grace period must be enough for a 0.2s run to finish.


def test_webportalapp_shutdown_app_stops_the_event_bus():
    """shutdown_app() stops the event bus heartbeat thread for a real app."""
    app = _build_test_app()  # Build a real app, matching how wsgi.py builds one.
    bus = app.config["EVENT_BUS"]  # Read the bus create_app already started.
    thread = bus._heartbeat_thread  # Hold the handle, because stop() clears the attribute.
    assert thread.is_alive()  # The thread must be alive right after create_app().
    WebPortalApp.shutdown_app(app)  # Run the code under test.
    assert not thread.is_alive()  # The thread must be gone right after shutdown_app() returns.


def test_webportalapp_shutdown_app_stops_the_operation_executor():
    """shutdown_app() drains an operation executor a request already built."""
    app = _build_test_app()  # Build a real app, matching how wsgi.py builds one.
    # Simulate the lazy build routes/operations.py performs on the first request.
    executor = OperationExecutor(_menu_actions(), None, None, app.config["EVENT_BUS"])
    app.config["OPERATION_EXECUTOR"] = executor  # Store it under the real config key.
    WebPortalApp.shutdown_app(app)  # Run the code under test.
    with pytest.raises(RuntimeError):  # A closed ThreadPoolExecutor refuses new work.
        executor._pool.submit(lambda: None)


def test_webportalapp_shutdown_app_tolerates_a_missing_executor():
    """shutdown_app() does not raise when no operation ever ran."""
    app = _build_test_app()  # Build a real app that never served an operation request.
    WebPortalApp.shutdown_app(app)  # No OPERATION_EXECUTOR key exists, so this call must not raise.


def test_webportalapp_shutdown_app_is_idempotent():
    """A second shutdown_app() call for the same app does not raise."""
    app = _build_test_app()  # Build a real app for this test.
    WebPortalApp.shutdown_app(app)  # First call performs the real shutdown.
    WebPortalApp.shutdown_app(app)  # Second call must return quietly, not raise.
