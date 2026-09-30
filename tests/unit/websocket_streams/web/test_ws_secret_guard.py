"""Secret guard tests for WebSocket routes.

Why:
    Issue #3551 requires the browser answers to exclude the API token, raw
    Mist channel paths, and Mist WebSocket addresses.
"""

from __future__ import annotations  # Keep annotations lazy for Flask imports.

from collections.abc import Iterator  # Type the fake download stream.
from typing import Any  # Type Flask test client answers.

import pytest  # Use fixtures for the portal app lifetime.

from src.websocket_streams.web.services import WebSocketsServices  # Inject the fake WebSocket service.
from web_portal.app import WebPortalApp  # Build the real portal app as the browser tests do.
from web_portal.menu_registry import build_static_menu_actions  # Supply normal menu actions.

SITE_ID = "11111111-2222-3333-4444-555555555555"  # A valid site identifier.
MAP_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"  # A valid map identifier.
API_TOKEN = "secret-token-123"  # The token that must never appear.
CHANNEL_PATH = f"/sites/{SITE_ID}/stats/devices"  # A raw channel path that must never appear.
WS_ADDRESS = "wss://api-ws.mist.com/api-ws/session"  # A WebSocket address that must never appear.


class SecretGuardServices:
    """Fake service with safe responses for all WebSocket routes."""

    def catalog_payload(self) -> dict[str, object]:
        """Return a safe catalog payload."""
        return {
            "ready": True,
            "reason": None,
            "flags": {},
            "limits": {"max_sessions": 5},
            "channels": [{"key": "site.stats.devices", "name": "Device statistics"}],
            "utilities": [],
        }  # Safe catalog.

    def start_session(self, _body: object) -> dict[str, object]:
        """Return a safe session payload."""
        return self._session("abc123")  # Session payload.

    def list_sessions(self) -> dict[str, object]:
        """Return a safe session list."""
        return {"sessions": [self._session("abc123")], "limits": {"max_sessions": 5, "live_count": 1}}  # List.

    def read_messages(self, session_id: str, _after: int, _limit: int) -> dict[str, object]:
        """Return a safe message payload."""
        return {
            "session": self._session(session_id),
            "messages": [{"seq": 1, "content": {"state": "ok"}}],
            "next_after": 1,
            "first_seq": 1,
            "gap": False,
        }  # Messages.

    def stop_session(self, session_id: str) -> dict[str, object]:
        """Return a safe stopped payload."""
        payload = self._session(session_id)  # Start with a safe session.
        payload["state"] = "stopped"  # Mark stopped.
        return payload  # Safe payload.

    def send_input(self, _session_id: str, _body: object) -> dict[str, object]:
        """Return a safe input answer."""
        return {"ok": True}  # No input text appears.

    def delete_session(self, _session_id: str) -> dict[str, object]:
        """Return a safe delete answer."""
        return {"ok": True}  # Safe delete answer.

    def download_session(self, _session_id: str) -> tuple[str, Iterator[str]]:
        """Return a safe download stream."""
        return "session.jsonl", iter(['{"seq":1,"content":"ok"}\n'])  # Safe stream.

    def devices(self, site_id: str) -> dict[str, object]:
        """Return a safe picker answer."""
        return self._picker(site_id)  # Picker payload.

    def maps(self, site_id: str) -> dict[str, object]:
        """Return a safe picker answer."""
        return self._picker(site_id)  # Picker payload.

    def assets(self, site_id: str) -> dict[str, object]:
        """Return a safe picker answer."""
        return self._picker(site_id)  # Picker payload.

    def sdkclients(self, site_id: str, map_id: str) -> dict[str, object]:
        """Return a safe picker answer."""
        return self._picker(site_id + map_id)  # Picker payload.

    def mxedges(self, site_id: str | None) -> dict[str, object]:
        """Return a safe picker answer."""
        return self._picker(site_id or "org")  # Picker payload.

    def shutdown(self) -> None:
        """Stop nothing in the fake service."""
        return None  # The fake has no threads.

    def _session(self, session_id: str) -> dict[str, object]:
        """Return a safe session payload."""
        return {
            "session_id": session_id,
            "title": "Device statistics",
            "state": "live",
            "live": True,
            "counters": {},
            "rate_per_second": 0,
            "last_seq": 0,
            "output": "json",
        }  # Safe session.

    def _picker(self, value: str) -> dict[str, object]:
        """Return one safe picker payload."""
        return {
            "rows": [{"id": value, "label": "Safe row", "family": "ex", "detail": "safe"}],
            "total_count": 1,
            "reason": None,
        }  # Safe picker.


@pytest.fixture
def portal_client() -> Iterator[Any]:
    """Build the real portal app with a fake WebSocket service."""
    app = WebPortalApp.create_app(apisession=object(), menu_actions=build_static_menu_actions(), org_id=SITE_ID)  # App.
    app.config["TESTING"] = True  # Surface route errors to the test.
    app.config["WTF_CSRF_ENABLED"] = False  # This test reads payload content, not the CSRF guard.
    app.config["APISESSION"] = {"token": API_TOKEN}  # Store a token-shaped value that must not leak.
    app.config[WebSocketsServices.CONFIG_KEY] = SecretGuardServices()  # Inject safe route behavior.
    try:  # Ensure shutdown runs even when an assertion fails.
        yield app.test_client()  # Give tests an in-process client.
    finally:
        WebPortalApp.shutdown_app(app)  # Stop portal background services.


def test_websocket_routes_do_not_leak_secrets(portal_client: Any) -> None:
    """No WebSocket route answer leaks token, path, or WebSocket address."""
    answers = [
        portal_client.get("/websockets"),
        portal_client.get("/api/websockets/catalog"),
        portal_client.get("/api/websockets/sessions"),
        portal_client.post("/api/websockets/sessions", json={"kind": "channel", "key": "site.stats.devices"}),
        portal_client.get("/api/websockets/sessions/abc123/messages?after=0"),
        portal_client.post("/api/websockets/sessions/abc123/stop"),
        portal_client.post("/api/websockets/sessions/abc123/input", json={"line": "show version"}),
        portal_client.delete("/api/websockets/sessions/abc123"),
        portal_client.get("/api/websockets/sessions/abc123/download"),
        portal_client.get(f"/api/websockets/sites/{SITE_ID}/devices"),
        portal_client.get(f"/api/websockets/sites/{SITE_ID}/maps"),
        portal_client.get(f"/api/websockets/sites/{SITE_ID}/assets"),
        portal_client.get(f"/api/websockets/sites/{SITE_ID}/maps/{MAP_ID}/sdkclients"),
        portal_client.get(f"/api/websockets/mxedges?site_id={SITE_ID}"),
    ]  # Every WebSocket route from the contract.
    bodies = "\n".join(answer.get_data(as_text=True) for answer in answers)  # Read all bodies once.
    assert all(answer.status_code < 400 for answer in answers)  # Every safe route answered.
    assert API_TOKEN not in bodies  # The API token did not leak.
    assert CHANNEL_PATH not in bodies  # The raw channel path did not leak.
    assert "wss://" not in bodies and WS_ADDRESS not in bodies  # No WebSocket address leaked.
