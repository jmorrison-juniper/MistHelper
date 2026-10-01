"""Tests for WebSocket web services.

Why:
    Issue #3551 needs one app-scoped service object that shuts down cleanly
    and reports a not-ready portal without leaking Mist details.
"""

from __future__ import annotations  # Keep annotations lazy for Flask imports.

from collections.abc import Iterator  # Type the fake download iterator.
from types import SimpleNamespace  # Return a checked request with a key attribute.

import pytest  # Assert contract errors from service calls.
from flask import Flask  # Build small app instances for the service tests.

from src.websocket_streams.intake.fields import StreamRequestError  # Not-ready errors use this type.
from src.websocket_streams.live.sessions.buffer import MessagePage  # The fake manager returns a read answer.
from src.websocket_streams.live.terminal.gateway import TerminalGateway  # The terminal routes use this gateway.
from src.websocket_streams.web.services import WebSocketsServiceParts, WebSocketsServices  # Classes under test.


class FakeCatalog:
    """Fake catalog that records payload reads."""

    def page_payload(self) -> dict[str, object]:
        """Return one safe catalog payload."""
        return {"flags": {}, "channels": [{"key": "site.stats.devices"}], "utilities": []}  # No path leaks.


class FakeSettings:
    """Fake settings that returns small limits."""

    def limits_payload(self) -> dict[str, int]:
        """Return the limits payload."""
        return {"max_sessions": 2, "idle_seconds": 30, "capture_seconds": 60}  # Stable test limits.


class FakeManager:
    """Fake manager for service unit tests."""

    def __init__(self) -> None:
        """Start with no actions."""
        self.shutdown_called = False  # Track shutdown calls.
        self.started = False  # Track start calls.

    def start(self, request: object) -> dict[str, object]:
        """Start one fake session."""
        self.started = True  # Prove that the manager ran.
        return {"session_id": "abc123", "title": "Started"}  # Session payload.

    def list_payload(self) -> dict[str, object]:
        """Return an empty session list."""
        return {"sessions": [], "limits": {"max_sessions": 2, "live_count": 0}}  # Empty list.

    def read(self, session_id: str, after: int, limit: int) -> MessagePage:
        """Return an empty read answer."""
        assert limit > 0  # The service passed the limit through.
        return MessagePage({"session_id": session_id}, [], after, 0, False)  # Read with no new message.

    def stop(self, session_id: str) -> dict[str, object]:
        """Return one stopped session."""
        return {"session_id": session_id, "state": "stopped"}  # Stop payload.

    def session(self, session_id: str) -> object:
        """Refuse each session, because the fake holds no session."""
        raise StreamRequestError("not_found", f"The session {session_id} was not found.")  # Contract error.

    def delete(self, session_id: str) -> None:
        """Accept a delete request."""
        assert session_id  # The service passed the session identifier.

    def download(self, session_id: str) -> tuple[str, Iterator[str]]:
        """Return a small download stream."""
        assert session_id  # The service passed the session identifier.
        return "download.jsonl", iter(['{"seq":1}\n'])  # JSON Lines stream.

    def shutdown(self) -> None:
        """Record shutdown."""
        self.shutdown_called = True  # Prove that shutdown reached the manager.


class FakeChecker:
    """Fake request checker."""

    def check(self, body: object) -> object:
        """Return a fake checked request."""
        assert isinstance(body, dict)  # The service passed the JSON body through.
        return SimpleNamespace(key="site.stats.devices")  # The service logs the checked key.


class FakePickers:
    """Fake picker service."""

    def devices(self, site_id: str) -> dict[str, object]:
        """Return one device row."""
        return self._payload(site_id)  # Common picker payload.

    def maps(self, site_id: str) -> dict[str, object]:
        """Return one map row."""
        return self._payload(site_id)  # Common picker payload.

    def assets(self, site_id: str) -> dict[str, object]:
        """Return one asset row."""
        return self._payload(site_id)  # Common picker payload.

    def sdkclients(self, site_id: str, map_id: str) -> dict[str, object]:
        """Return one client row."""
        return self._payload(site_id + map_id)  # Common picker payload.

    def mxedges(self, site_id: str | None) -> dict[str, object]:
        """Return one Mist Edge row."""
        return self._payload(site_id or "org")  # Common picker payload.

    def _payload(self, value: str) -> dict[str, object]:
        """Return one picker payload."""
        return {"rows": [{"id": value, "label": "Row"}], "total_count": 1, "reason": None}  # Payload.


def make_service(reason: str | None = None) -> tuple[WebSocketsServices, FakeManager]:
    """Build a service with fake parts."""
    manager = FakeManager()  # The test reads this object after the action.
    parts = WebSocketsServiceParts(
        FakeCatalog(), FakeChecker(), FakePickers(), manager, FakeSettings(), reason
    )  # Parts.
    return WebSocketsServices(parts), manager  # Return both objects.


def test_catalog_payload_adds_ready_and_limits() -> None:
    """The service adds readiness and limits to the catalog payload."""
    service, _manager = make_service()  # Build a ready service.
    payload = service.catalog_payload()  # Read the catalog payload.
    assert payload["ready"] is True  # Ready state is true.
    assert payload["limits"]["max_sessions"] == 2  # Limits came from settings.
    assert "path" not in str(payload)  # The payload does not expose a path field.


def test_not_ready_refuses_start_and_picker() -> None:
    """A not-ready service refuses starts and pickers."""
    service, _manager = make_service("The portal has no Mist session or organization.")  # Build not ready.
    with pytest.raises(StreamRequestError) as start_error:  # Start must fail.
        service.start_session({"kind": "channel"})  # Attempt a start.
    with pytest.raises(StreamRequestError) as picker_error:  # Picker must fail.
        service.devices("site1")  # Attempt a picker read.
    assert start_error.value.code == "not_ready"  # Start refusal code.
    assert picker_error.value.code == "not_ready"  # Picker refusal code.


def test_not_ready_refuses_the_terminal() -> None:
    """A not-ready service refuses the terminal routes before the gateway runs."""
    service, _manager = make_service("The portal has no Mist session or organization.")  # Build not ready.
    with pytest.raises(StreamRequestError) as terminal_error:  # The terminal must fail.
        service.terminal()  # Ask for the terminal gateway.
    assert terminal_error.value.code == "not_ready"  # The refusal uses the contract code.
    assert terminal_error.value.status == 503  # The page shows the not-ready state.


def test_ready_terminal_gateway_reaches_the_manager() -> None:
    """The ready service gives one gateway, and the gateway finds sessions through the manager."""
    service, _manager = make_service()  # Build a ready service.
    gateway = service.terminal()  # Ask for the terminal gateway.
    with pytest.raises(StreamRequestError) as read_error:  # The fake manager holds no session.
        gateway.read("missing", 0, 0.0)  # Read a session that does not exist.
    assert isinstance(gateway, TerminalGateway)  # The routes call the real gateway.
    assert service.terminal() is gateway  # One gateway counts the waiting reads of the process.
    assert read_error.value.code == "not_found"  # The manager refusal reaches the route.


def test_ready_service_delegates_to_manager_and_pickers() -> None:
    """A ready service delegates route work to the built parts."""
    service, manager = make_service()  # Build a ready service.
    started = service.start_session({"kind": "channel"})  # Start a fake session.
    listed = service.list_sessions()  # List sessions.
    read = service.read_messages("abc123", 4, 10)  # Read messages.
    stopped = service.stop_session("abc123")  # Stop session.
    deleted = service.delete_session("abc123")  # Delete session.
    filename, lines = service.download_session("abc123")  # Download session.
    picker = service.mxedges(None)  # Read a picker.
    device_picker = service.devices("site1")  # Read devices through the picker service.
    map_picker = service.maps("site1")  # Read maps through the picker service.
    asset_picker = service.assets("site1")  # Read assets through the picker service.
    client_picker = service.sdkclients("site1", "map1")  # Read SDK clients through the picker service.
    assert manager.started is True and started["session_id"] == "abc123"  # Manager start ran.
    assert listed["sessions"] == [] and read.next_after == 4  # Manager reads ran.
    assert stopped["state"] == "stopped"  # Stop ran.
    assert deleted == {"ok": True} and filename == "download.jsonl"  # Delete and download ran.
    assert list(lines) == ['{"seq":1}\n'] and picker["rows"][0]["label"] == "Row"  # Streams and picker ran.
    assert device_picker["rows"][0]["label"] == "Row" and map_picker["rows"][0]["label"] == "Row"  # Picker rows.
    assert asset_picker["rows"][0]["label"] == "Row" and client_picker["rows"][0]["label"] == "Row"  # More rows.


def test_for_app_reuses_injected_service() -> None:
    """for_app returns the service that a test injects."""
    app = Flask(__name__)  # Build a small Flask app.
    service, _manager = make_service()  # Build an injected service.
    app.config[WebSocketsServices.CONFIG_KEY] = service  # Inject the service.
    assert WebSocketsServices.for_app(app) is service  # The service is reused.


def test_for_app_builds_not_ready_service_without_credentials() -> None:
    """for_app builds a safe service when the portal has no Mist session."""
    app = Flask(__name__)  # Build a small Flask app.
    app.config["APISESSION"] = None  # Simulate a portal with no Mist session.
    app.config["ORG_ID"] = ""  # Simulate a portal with no organization.
    service = WebSocketsServices.for_app(app)  # Build the app-scoped service.
    catalog = service.catalog_payload()  # The catalog route can still answer.
    listed = service.list_sessions()  # The session list can still answer.
    with pytest.raises(StreamRequestError) as error:  # A start must refuse when not ready.
        service.start_session({"kind": "channel"})  # Attempt a start.
    service.shutdown()  # Shutdown the empty manager safely.
    assert catalog["ready"] is False  # The payload reports not ready.
    assert listed["sessions"] == []  # The empty manager returns no sessions.
    assert error.value.code == "not_ready"  # The refusal uses the contract code.


def test_fallback_not_ready_parts_have_limits() -> None:
    """Fallback parts provide limits when settings cannot import."""
    parts = WebSocketsServices._not_ready_parts("The engine is loading.")  # Build fallback parts.
    service = WebSocketsServices(parts)  # Build a service from fallback parts.
    payload = service.catalog_payload()  # Read the safe catalog payload.
    assert payload["limits"]["capture_seconds"] == 60  # Fallback settings keep capture seconds.


def test_stop_for_app_calls_shutdown() -> None:
    """stop_for_app shuts down an existing service."""
    app = Flask(__name__)  # Build a small Flask app.
    service, manager = make_service()  # Build an injected service.
    app.config[WebSocketsServices.CONFIG_KEY] = service  # Inject the service.
    WebSocketsServices.stop_for_app(app)  # Stop WebSocket services.
    assert manager.shutdown_called is True  # Shutdown reached the manager.


def test_stop_for_app_without_service_is_safe() -> None:
    """stop_for_app does nothing when the app has no service."""
    app = Flask(__name__)  # Build a small Flask app.
    WebSocketsServices.stop_for_app(app)  # Stop without a configured service.
    assert WebSocketsServices.CONFIG_KEY not in app.config  # No service was created.
