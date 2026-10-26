"""Verify one Redis-elected worker refreshes and stops without duplicate writes."""

from threading import Event, Thread
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
