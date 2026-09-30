"""Tests for WebSocket blueprint routes.

Why:
    Issue #3551 routes must translate service answers and refusals into the
    HTTP contract without a Mist connection.
"""

from __future__ import annotations  # Keep annotations lazy for Flask imports.

from collections.abc import Iterator  # Type the fake download stream.
from pathlib import Path  # Build the app template path.
from typing import Any  # Type fake request bodies without concrete service classes.

import pytest  # Use pytest fixtures for the route app.
from flask import Flask  # Build a small app around the blueprint.

from src.websocket_streams.intake.fields import StreamRequestError  # Raise contract errors from the fake.
from src.websocket_streams.web.blueprint import websockets_bp  # The blueprint under test.
from src.websocket_streams.web.services import WebSocketsServices  # The config key for dependency injection.

ROOT = Path(__file__).resolve().parents[4]  # Repository root for template lookup.
SITE_ID = "11111111-2222-3333-4444-555555555555"  # A valid site identifier.
MAP_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"  # A valid map identifier.


class FakeWebSocketServices:
    """Fake service object used by blueprint tests."""

    def __init__(self) -> None:
        """Start with no recorded actions."""
        self.deleted: list[str] = []  # Record deleted sessions for assertions.
        self.inputs: list[tuple[str, object]] = []  # Record input requests without using Mist.

    def catalog_payload(self) -> dict[str, object]:
        """Return a small catalog answer."""
        return {"ready": True, "reason": None, "channels": [], "utilities": [], "limits": {"max_sessions": 5}}  # Shape.

    def start_session(self, body: object) -> dict[str, object]:
        """Return a new session, or raise the requested error."""
        if isinstance(body, dict) and body.get("key") == "bad":  # The test asks for a refusal.
            raise StreamRequestError("unknown_key", "The key is unknown.")  # Contract error.
        return self._session("abc123")  # New session payload.

    def list_sessions(self) -> dict[str, object]:
        """Return one session in the list."""
        return {"sessions": [self._session("abc123")], "limits": {"max_sessions": 5, "live_count": 1}}  # List.

    def read_messages(self, session_id: str, after: int, limit: int) -> dict[str, object]:
        """Return one message after the query values."""
        return {
            "session": self._session(session_id),
            "messages": [{"seq": after + 1, "content": "ok"}],
            "next_after": after + 1,
            "first_seq": 1,
            "gap": False,
        }  # Read.

    def stop_session(self, session_id: str) -> dict[str, object]:
        """Return a stopped session."""
        payload = self._session(session_id)  # Start with the base session.
        payload["state"] = "stopped"  # Mark the stop result.
        payload["live"] = False  # Stopped sessions are not live.
        return payload  # Return the stopped payload.

    def send_input(self, session_id: str, body: object) -> dict[str, object]:
        """Record shell input without logging its text."""
        self.inputs.append((session_id, body))  # Keep the input for the assertion.
        return {"ok": True}  # Confirm acceptance.

    def delete_session(self, session_id: str) -> dict[str, object]:
        """Delete an ended session or refuse a live one."""
        if session_id == "live":  # The test asks for a live-session refusal.
            raise StreamRequestError("session_live", "The session is still live.")  # Contract error.
        self.deleted.append(session_id)  # Record the deletion.
        return {"ok": True}  # Confirm deletion.

    def download_session(self, session_id: str) -> tuple[str, Iterator[str]]:
        """Return a small JSON Lines stream."""
        return "ws-20260929T000000Z.jsonl", iter(['{"seq":1}\n'])  # Download stream.

    def devices(self, site_id: str) -> dict[str, object]:
        """Return one device picker row."""
        return self._picker(site_id, "Device 1")  # Device picker payload.

    def maps(self, site_id: str) -> dict[str, object]:
        """Return one map picker row."""
        return self._picker(site_id, "Map 1")  # Map picker payload.

    def assets(self, site_id: str) -> dict[str, object]:
        """Return one asset picker row."""
        return self._picker(site_id, "Asset 1")  # Asset picker payload.

    def sdkclients(self, site_id: str, map_id: str) -> dict[str, object]:
        """Return one SDK client picker row."""
        return self._picker(site_id + map_id, "Client 1")  # SDK client picker payload.

    def mxedges(self, site_id: str | None) -> dict[str, object]:
        """Return one Mist Edge picker row."""
        return self._picker(site_id or "org", "Mist Edge 1")  # Mist Edge picker payload.

    def shutdown(self) -> None:
        """Stop nothing in the fake."""
        return None  # The fake has no thread.

    def _session(self, session_id: str) -> dict[str, object]:
        """Return one session payload."""
        return {
            "session_id": session_id,
            "title": "Device statistics",
            "state": "live",
            "live": True,
            "counters": {},
            "rate_per_second": 0,
            "last_seq": 0,
            "output": "json",
        }  # Payload.

    def _picker(self, identifier: str, label: str) -> dict[str, object]:
        """Return one picker payload."""
        return {
            "rows": [{"id": identifier, "label": label, "family": "ex", "detail": "EX"}],
            "total_count": 1,
            "reason": None,
        }  # Picker.


@pytest.fixture
def app() -> Flask:
    """Build a small Flask app with fake WebSocket services."""
    template_dir = ROOT / "web_portal" / "templates"  # Base template lives in the portal folder.
    flask_app = Flask(__name__, template_folder=str(template_dir))  # Build a minimal app.
    flask_app.secret_key = "test-secret"  # Flask needs a key for the base template CSRF helper.
    flask_app.config["PORTAL"] = {
        "title": "MistHelper Test",
        "theme": "dark",
        "accent_color": "#c000ff",
        "logo_url": "",
    }  # Base.
    flask_app.config[WebSocketsServices.CONFIG_KEY] = FakeWebSocketServices()  # Inject the fake service.
    flask_app.jinja_env.globals["csrf_token"] = lambda: "test-csrf"  # Let the base template render.
    flask_app.add_url_rule("/", endpoint="dashboard.dashboard", view_func=lambda: "dashboard")  # Base link.
    flask_app.add_url_rule("/data", endpoint="data.data_browser", view_func=lambda: "data")  # Base link.
    flask_app.add_url_rule("/operations", endpoint="operations.operations_page", view_func=lambda: "ops")  # Base.
    flask_app.add_url_rule("/maps", endpoint="maps.maps_page", view_func=lambda: "maps")  # Base link.
    flask_app.register_blueprint(websockets_bp)  # Register the routes under test.
    return flask_app  # Give the test client a complete app.


@pytest.fixture
def client(app: Flask) -> Any:
    """Return a Flask test client."""
    return app.test_client()  # Use Flask's in-process client.


def test_page_and_catalog_routes_answer(client: Any) -> None:
    """The page and catalog route answer successfully."""
    page = client.get("/websockets")  # Request the page shell.
    catalog = client.get("/api/websockets/catalog")  # Request the catalog JSON.
    assert page.status_code == 200  # The page route rendered.
    assert b"WebSockets" in page.data  # The page title is present.
    assert catalog.status_code == 200  # The catalog route answered.
    assert catalog.get_json()["ready"] is True  # The fake is ready.


def test_session_routes_cover_start_read_stop_delete_and_download(client: Any) -> None:
    """Session routes call the fake service and return contract statuses."""
    started = client.post("/api/websockets/sessions", json={"kind": "channel", "key": "ok"})  # Start.
    listed = client.get("/api/websockets/sessions")  # List.
    read = client.get("/api/websockets/sessions/abc123/messages?after=2&limit=4")  # Read messages.
    stopped = client.post("/api/websockets/sessions/abc123/stop")  # Stop.
    deleted = client.delete("/api/websockets/sessions/abc123")  # Delete.
    download = client.get("/api/websockets/sessions/abc123/download")  # Download.
    assert started.status_code == 201  # Start returns created.
    assert listed.get_json()["limits"]["live_count"] == 1  # List includes the live count.
    assert read.get_json()["next_after"] == 3  # Read uses the after value.
    assert stopped.status_code == 202 and stopped.get_json()["state"] == "stopped"  # Stop returns accepted.
    assert deleted.get_json() == {"ok": True}  # Delete confirms success.
    assert download.mimetype == "application/x-ndjson"  # Download uses JSON Lines.


def test_errors_use_contract_codes(client: Any) -> None:
    """Route errors use the shared error payload."""
    bad_start = client.post("/api/websockets/sessions", json={"kind": "channel", "key": "bad"})  # Unknown key.
    bad_query = client.get("/api/websockets/sessions/abc123/messages?after=x")  # Bad after.
    bad_delete = client.delete("/api/websockets/sessions/live")  # Live delete.
    assert bad_start.status_code == 404 and bad_start.get_json()["code"] == "unknown_key"  # Unknown key.
    assert bad_query.status_code == 400 and bad_query.get_json()["field"] == "after"  # Query refusal.
    assert bad_delete.status_code == 409 and bad_delete.get_json()["code"] == "session_live"  # Live refusal.


def test_picker_routes_validate_identifiers(client: Any) -> None:
    """Picker routes reject bad identifiers and answer valid identifiers."""
    bad = client.get("/api/websockets/sites/not-a-uuid/devices")  # Bad route identifier.
    devices = client.get(f"/api/websockets/sites/{SITE_ID}/devices")  # Device picker.
    maps = client.get(f"/api/websockets/sites/{SITE_ID}/maps")  # Map picker.
    assets = client.get(f"/api/websockets/sites/{SITE_ID}/assets")  # Asset picker.
    clients = client.get(f"/api/websockets/sites/{SITE_ID}/maps/{MAP_ID}/sdkclients")  # Client picker.
    mxedges = client.get(f"/api/websockets/mxedges?site_id={SITE_ID}")  # Mist Edge picker.
    assert bad.status_code == 400 and bad.get_json()["field"] == "site_id"  # Bad UUID refused.
    assert devices.get_json()["rows"][0]["label"] == "Device 1"  # Device row.
    assert maps.get_json()["rows"][0]["label"] == "Map 1"  # Map row.
    assert assets.get_json()["rows"][0]["label"] == "Asset 1"  # Asset row.
    assert clients.get_json()["rows"][0]["label"] == "Client 1"  # Client row.
    assert mxedges.get_json()["rows"][0]["label"] == "Mist Edge 1"  # Mist Edge row.


def test_shell_input_route_accepts_line_and_key(client: Any, app: Flask) -> None:
    """The input route passes line and key requests to the service."""
    line = client.post("/api/websockets/sessions/shell1/input", json={"line": "show version"})  # Send line.
    key = client.post("/api/websockets/sessions/shell1/input", json={"key": "interrupt"})  # Send key.
    service = app.config[WebSocketsServices.CONFIG_KEY]  # Read the fake service.
    assert line.status_code == 202 and key.status_code == 202  # Both inputs are accepted.
    assert service.inputs == [("shell1", {"line": "show version"}), ("shell1", {"key": "interrupt"})]  # Calls.
