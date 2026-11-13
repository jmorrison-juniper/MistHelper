"""Verify one Redis-elected worker refreshes and stops without duplicate writes."""

from threading import Event, Lock, Thread
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from src.interfaces.wan_performance.background_refresh import (
    WanBackgroundRefreshWorker,
)
from src.interfaces.wan_performance.collection.request_admission import RequestLedger
from src.interfaces.wan_performance.presentation.live_routes import LivePages
from web_portal.app import WebPortalApp


def service_with_client(client: MagicMock) -> MagicMock:
    """Create a live service boundary with the configured Redis client."""
    service = MagicMock()
    service.org_id = "org-one"
    service.store.client = client
    return service


def test_worker_refreshes_once_and_releases_its_lease_on_shutdown() -> None:
    """Run one bounded refresh and release only the owned Redis lease."""
    completed = Event()
    client = MagicMock()
    client.set.return_value = True
    client.eval.return_value = 1
    service = service_with_client(client)
    service.refresh.side_effect = lambda: completed.set() or {"ports": [], "peers": []}
    worker = WanBackgroundRefreshWorker(service)

    worker.start()
    assert completed.wait(1)
    worker.stop()

    assert service.refresh.call_count == 1
    assert client.set.call_args.args[0] == "misthelper:wan:v1:worker:org-one"
    assert client.set.call_args.kwargs == {"nx": True, "ex": 600}
    assert client.eval.call_count == 2
    thread = worker.thread
    assert isinstance(thread, Thread)
    assert not thread.is_alive()


def test_worker_without_lease_does_not_refresh() -> None:
    """Skip API and history writes when another process owns the lease."""
    attempted = Event()
    client = MagicMock()
    client.set.side_effect = lambda *args, **kwargs: (attempted.set(), False)[1]
    service = service_with_client(client)
    worker = WanBackgroundRefreshWorker(service)

    worker.start()
    assert attempted.wait(1)
    worker.stop()

    service.refresh.assert_not_called()
    client.eval.assert_not_called()


def test_workers_share_one_organization_lease() -> None:
    """Prevent two portal processes from refreshing the same organization."""
    attempts_lock = Lock()
    attempts = 0
    second_attempt = Event()
    refresh_started = Event()
    allow_refresh = Event()
    client = MagicMock()

    def acquire_lease(*_arguments: object, **_options: object) -> bool:
        nonlocal attempts
        with attempts_lock:
            attempts += 1
            attempt = attempts
        if attempt == 2:
            second_attempt.set()
        return attempt == 1

    client.set.side_effect = acquire_lease
    client.eval.return_value = 1
    service = service_with_client(client)

    def refresh_once() -> dict[str, list[object]]:
        refresh_started.set()
        allow_refresh.wait(1)
        return {"ports": [], "peers": []}

    service.refresh.side_effect = refresh_once
    workers = [WanBackgroundRefreshWorker(service) for _ in range(2)]

    workers[0].start()
    assert refresh_started.wait(1), "The lease owner did not start its refresh."
    workers[1].start()
    assert second_attempt.wait(1), "The second worker did not contend for the shared lease."
    allow_refresh.set()
    for worker in workers:
        worker.stop()

    assert service.refresh.call_count == 1, "More than one worker refreshed the organization."
    assert client.set.call_count == 2, "Both workers must attempt the same shared lease."


def test_worker_retries_lease_acquisition_after_the_configured_wait(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Retry a contended lease once the configured wait ends."""
    completed = Event()
    client = MagicMock()
    client.set.side_effect = [None, True]
    client.eval.return_value = 1
    service = service_with_client(client)
    service.refresh.side_effect = lambda: completed.set() or {"ports": [], "peers": []}
    monkeypatch.setattr(WanBackgroundRefreshWorker, "RETRY_INTERVAL_SECONDS", 0.01)
    worker = WanBackgroundRefreshWorker(service)

    worker.start()
    assert completed.wait(1), "The worker did not retry after its lease wait."
    worker.stop()

    assert client.set.call_count == 2, "The worker did not make exactly one retry."
    assert service.refresh.call_count == 1, "The worker refreshed more than once."


def test_worker_does_not_release_a_lease_after_ownership_changes() -> None:
    """Do not release a Redis lease after its renewal check fails."""
    completed = Event()
    client = MagicMock()
    client.set.return_value = True
    client.eval.return_value = 0
    service = service_with_client(client)
    service.refresh.side_effect = lambda: completed.set() or {"ports": [], "peers": []}
    worker = WanBackgroundRefreshWorker(service)

    worker.start()
    assert completed.wait(1), "The lease owner did not complete its refresh."
    worker.stop()

    assert client.eval.call_count == 1, "The worker evaluated a release after losing ownership."


def test_worker_refresh_failure_stops_cleanly() -> None:
    """Keep shutdown responsive after a bounded read or storage failure."""
    attempted = Event()
    client = MagicMock()
    client.set.return_value = True
    client.eval.return_value = 1
    service = service_with_client(client)

    def fail_refresh() -> None:
        attempted.set()
        raise ConnectionError("synthetic read failure")

    service.refresh.side_effect = fail_refresh
    worker = WanBackgroundRefreshWorker(service)

    worker.start()
    assert attempted.wait(1)
    worker.stop()

    service.refresh.assert_called_once()
    thread = worker.thread
    assert isinstance(thread, Thread)
    assert not thread.is_alive()
    assert client.eval.call_count == 2


def test_portal_shutdown_stops_the_configured_worker() -> None:
    """Stop the scheduled worker before the portal closes shared resources."""
    app = Flask(__name__)
    worker = MagicMock()
    app.config["WAN_BACKGROUND_REFRESH_WORKER"] = worker

    with (
        patch.object(WebPortalApp, "_stop_event_bus"),
        patch.object(WebPortalApp, "_stop_operation_executor"),
        patch.object(WebPortalApp, "_stop_websocket_sessions"),
    ):
        WebPortalApp.shutdown_app(app)

    worker.stop.assert_called_once_with()


def test_portal_starts_worker_with_shared_admission_and_history(monkeypatch: pytest.MonkeyPatch) -> None:
    """Start the worker only after existing portal services pass their gates."""
    from src.interfaces.wan_performance.background_refresh import (
        WanBackgroundRefreshWorker,
    )

    monkeypatch.setenv("WAN_BACKGROUND_REFRESH", "true")
    service = MagicMock()
    service.history = MagicMock()
    app = Flask(__name__)
    app.config["APISESSION"] = object()

    with (
        patch.object(RequestLedger, "enabled", return_value=True),
        patch.object(LivePages, "service", return_value=service),
        patch.object(WanBackgroundRefreshWorker, "start") as start,
    ):
        WebPortalApp._start_wan_refresh_worker(app)

    assert app.config["WAN_BACKGROUND_REFRESH_WORKER"].service is service
    start.assert_called_once_with()


def test_portal_skips_worker_when_shared_admission_is_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """Do not start automatic Mist reads without shared request accounting."""
    monkeypatch.setenv("WAN_BACKGROUND_REFRESH", "true")
    app = Flask(__name__)
    app.config["APISESSION"] = object()

    with patch.object(RequestLedger, "enabled", return_value=False):
        WebPortalApp._start_wan_refresh_worker(app)

    assert "WAN_BACKGROUND_REFRESH_WORKER" not in app.config
