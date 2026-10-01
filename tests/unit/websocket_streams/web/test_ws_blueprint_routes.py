"""Tests for WebSocket blueprint routes.

Why:
    Issue #3551 routes must translate service answers and refusals into the
    HTTP contract without a Mist connection.
    Issue #3671 adds the terminal read route, the terminal input route, and the
    terminal size route. The input route must send the text without a change.
"""

from __future__ import annotations  # Keep annotations lazy for Flask imports.

from collections.abc import Iterator  # Type the fake download stream.
from pathlib import Path  # Build the app template path.
from typing import Any  # Type fake request bodies without concrete service classes.

import pytest  # Use pytest fixtures for the route app.
from flask import Flask  # Build a small app around the blueprint.

from src.websocket_streams.intake.fields import StreamRequestError  # Raise contract errors from the fake.
from src.websocket_streams.live.sessions.buffer import MessagePage, StreamMessage  # The fake read returns records.
from src.websocket_streams.web.blueprint import websockets_bp  # The blueprint under test.
from src.websocket_streams.web.services import WebSocketsServices  # The config key for dependency injection.
from web_portal.services.config import SecurityMiddleware  # The portal installs the form token check with this class.

ROOT = Path(__file__).resolve().parents[4]  # Repository root for template lookup.
SITE_ID = "11111111-2222-3333-4444-555555555555"  # A valid site identifier.
MAP_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"  # A valid map identifier.
TERMINAL_PATH = "/api/websockets/sessions/{session_id}/{route}"  # The terminal routes share one path shape.
MAX_INPUT_BYTES = 16 * 1024  # The contract accepts 16 KiB of UTF-8 text in one input request.


class FakeTerminalGateway:
    """Fake terminal gateway that records each terminal call."""

    def __init__(self) -> None:
        """Start with no recorded terminal calls."""
        self.reads: list[tuple[str, int, float]] = []  # Record each read position and wait.
        self.sends: list[tuple[str, str]] = []  # Record each sent text without a change.
        self.sizes: list[tuple[str, int, int]] = []  # Record each terminal size.

    def read(self, session_id: str, after: int, wait_seconds: float) -> dict[str, object]:
        """Return two terminal bytes after the position, or refuse a message session."""
        if session_id == "stream1":  # The test asks for a session that has no terminal.
            raise StreamRequestError("not_terminal", "The session is not a terminal.")  # Contract error.
        self.reads.append((session_id, after, wait_seconds))  # Keep the checked query values.
        return {
            "data": "aGk=",
            "first": 0,
            "next": after + 2,
            "gap": 0,
            "state": "live",
            "reason": "",
            "input_ready": True,
            "read_only": False,
            "expires_at": "2026-10-01T09:30:00Z",
        }  # The contract read answer with the two bytes "hi".

    def send(self, session_id: str, data: str) -> dict[str, object]:
        """Record the sent text, or refuse a screen session and an oversized text."""
        if session_id == "screen1":  # The test asks for a read-only session.
            raise StreamRequestError("read_only", "The terminal is read-only.")  # Contract error.
        accepted = len(data.encode("utf-8"))  # The contract counts UTF-8 bytes.
        if accepted > MAX_INPUT_BYTES:  # The test sends more than 16 KiB.
            raise StreamRequestError("too_large", "The terminal input is too large.")  # Contract error.
        self.sends.append((session_id, data))  # Keep the exact text for the assertion.
        return {"accepted": accepted, "queued": False}  # The contract input answer.

    def resize(self, session_id: str, cols: int, rows: int) -> dict[str, object]:
        """Record one terminal size."""
        self.sizes.append((session_id, cols, rows))  # Keep the checked size values.
        return {"cols": cols, "rows": rows}  # The contract size answer.


class FakeWebSocketServices:
    """Fake service object used by blueprint tests."""

    def __init__(self) -> None:
        """Start with no recorded actions."""
        self.deleted: list[str] = []  # Record deleted sessions for assertions.
        self.gateway = FakeTerminalGateway()  # The terminal routes use this fake gateway.

    def terminal(self) -> FakeTerminalGateway:
        """Return the fake terminal gateway."""
        return self.gateway  # The routes call read, send, and resize on it.

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

    def read_messages(self, session_id: str, after: int, limit: int) -> MessagePage:
        """Return one message after the query values, or refuse an unknown session."""
        if session_id == "missing":  # The test asks for a refusal.
            raise StreamRequestError("not_found", "The session was not found.")  # Contract error.
        assert limit > 0  # The route passed the checked limit.
        message = StreamMessage(after + 1, "2026-01-01T00:00:00Z", "text", '"ok"', 4, False)  # One message record.
        return MessagePage(self._session(session_id), [message], after + 1, 1, False)  # Read.

    def stop_session(self, session_id: str) -> dict[str, object]:
        """Return a stopped session."""
        payload = self._session(session_id)  # Start with the base session.
        payload["state"] = "stopped"  # Mark the stop result.
        payload["live"] = False  # Stopped sessions are not live.
        return payload  # Return the stopped payload.

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


class RouteTestApp:
    """Build the small Flask app that holds the blueprint under test."""

    @staticmethod
    def build(form_token_check: bool) -> Flask:
        """Build one app with fake WebSocket services.

        Args:
            form_token_check: True to install the portal form token check.

        Returns:
            The Flask app with the blueprint and the fake services.
        """
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
        if form_token_check:  # The token test needs the same check that the portal installs.
            flask_app.config["WTF_CSRF_ENABLED"] = True  # Turn on the form token check.
            SecurityMiddleware()._configure_csrf(flask_app)  # Install the portal handler that answers JSON.
        else:  # The other tests send no form token.
            flask_app.jinja_env.globals["csrf_token"] = lambda: "test-csrf"  # Let the base template render.
        RouteTestApp._add_base_links(flask_app)  # The base template links to these endpoints.
        flask_app.register_blueprint(websockets_bp)  # Register the routes under test.
        return flask_app  # Give the test client a complete app.

    @staticmethod
    def _add_base_links(flask_app: Flask) -> None:
        """Add the endpoints that the base template links to.

        Args:
            flask_app: The app under test.
        """
        flask_app.add_url_rule("/", endpoint="dashboard.dashboard", view_func=lambda: "dashboard")  # Base link.
        flask_app.add_url_rule("/data", endpoint="data.data_browser", view_func=lambda: "data")  # Base link.
        flask_app.add_url_rule("/operations", endpoint="operations.operations_page", view_func=lambda: "ops")  # Base.
        flask_app.add_url_rule("/maps", endpoint="maps.maps_page", view_func=lambda: "maps")  # Base link.


@pytest.fixture
def app() -> Flask:
    """Build a small Flask app with fake WebSocket services."""
    return RouteTestApp.build(form_token_check=False)  # The route tests send no form token.


@pytest.fixture
def client(app: Flask) -> Any:
    """Return a Flask test client."""
    return app.test_client()  # Use Flask's in-process client.


@pytest.fixture
def gateway(app: Flask) -> FakeTerminalGateway:
    """Return the fake terminal gateway of the app."""
    return app.config[WebSocketsServices.CONFIG_KEY].gateway  # The terminal routes call this fake.


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
    assert read.mimetype == "application/json"  # The joined text keeps the JSON type.
    message = read.get_json()["messages"][0]  # The one returned message.
    assert (message["seq"], message["content"]) == (3, "ok")  # The message text joins the answer.
    assert stopped.status_code == 202 and stopped.get_json()["state"] == "stopped"  # Stop returns accepted.
    assert deleted.get_json() == {"ok": True}  # Delete confirms success.
    assert download.mimetype == "application/x-ndjson"  # Download uses JSON Lines.


def test_errors_use_contract_codes(client: Any) -> None:
    """Route errors use the shared error payload."""
    bad_start = client.post("/api/websockets/sessions", json={"kind": "channel", "key": "bad"})  # Unknown key.
    bad_query = client.get("/api/websockets/sessions/abc123/messages?after=x")  # Bad after.
    missing = client.get("/api/websockets/sessions/missing/messages")  # Unknown session.
    bad_delete = client.delete("/api/websockets/sessions/live")  # Live delete.
    assert bad_start.status_code == 404 and bad_start.get_json()["code"] == "unknown_key"  # Unknown key.
    assert missing.status_code == 404 and missing.get_json()["code"] == "not_found"  # Read refusal.
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


class TestTerminalReadRoute:
    """The terminal read route checks the query and passes it to the gateway."""

    def test_read_passes_the_position_and_the_wait(self, client: Any, gateway: FakeTerminalGateway) -> None:
        """A good query reaches the gateway, and the answer keeps the contract fields."""
        path = TERMINAL_PATH.format(session_id="shell1", route="terminal")  # The read route of one shell.
        answer = client.get(f"{path}?after=5&wait=2.5")  # Read after byte 5 and wait 2.5 seconds.
        default = client.get(path)  # Read with no query values.
        assert answer.status_code == 200  # The read answers at once in the fake.
        assert answer.get_json()["next"] == 7  # The gateway answer reaches the page.
        assert answer.get_json()["data"] == "aGk="  # The bytes stay base64 text.
        assert default.status_code == 200  # The defaults are valid values.
        assert gateway.reads == [("shell1", 5, 2.5), ("shell1", 0, 0.0)]  # Each checked query reached the gateway.

    @pytest.mark.parametrize(
        ("query", "field"),
        [
            ("after=-1", "after"),
            ("after=x", "after"),
            ("after=", "after"),
            ("after=%C2%B2", "after"),
            ("wait=26", "wait"),
            ("wait=-1", "wait"),
            ("wait=nan", "wait"),
            ("wait=inf", "wait"),
            ("wait=abc", "wait"),
        ],
    )
    def test_read_refuses_a_bad_query(self, client: Any, gateway: FakeTerminalGateway, query: str, field: str) -> None:
        """A bad position or a bad wait gets bad_request, and no read starts."""
        path = TERMINAL_PATH.format(session_id="shell1", route="terminal")  # The read route of one shell.
        answer = client.get(f"{path}?{query}")  # Send the bad query value.
        assert answer.status_code == 400  # The contract status of bad_request.
        assert answer.get_json()["code"] == "bad_request"  # The error shape names the code.
        assert answer.get_json()["field"] == field  # The error names the bad field.
        assert gateway.reads == []  # No thread waits for a refused read.

    def test_read_returns_the_gateway_refusal(self, client: Any) -> None:
        """A session without a terminal gets not_terminal in the standard error shape."""
        answer = client.get(TERMINAL_PATH.format(session_id="stream1", route="terminal"))  # Read a stream session.
        assert answer.status_code == 409  # The contract status of not_terminal.
        assert set(answer.get_json()) >= {"error", "code"}  # The standard error shape.
        assert answer.get_json()["code"] == "not_terminal"  # The gateway code reaches the page.


class TestTerminalInputRoute:
    """The terminal input route sends the text without a change."""

    @pytest.mark.parametrize(
        "text",
        ["show arp\r", "\x1b[A", "\x03", "line one\rline two\r", "caf\u00e9 \u2603\r"],
    )
    def test_input_sends_the_text_without_a_change(self, client: Any, gateway: FakeTerminalGateway, text: str) -> None:
        """Typed keys, control keys, pasted lines, and Unicode text reach the gateway byte for byte."""
        path = TERMINAL_PATH.format(session_id="shell1", route="input")  # The input route of one shell.
        answer = client.post(path, json={"data": text})  # Send the exact text.
        assert answer.status_code == 202  # The contract status of an accepted input.
        assert answer.get_json() == {"accepted": len(text.encode("utf-8")), "queued": False}  # Count UTF-8 bytes.
        assert gateway.sends == [("shell1", text)]  # The gateway received the text without a change.

    @pytest.mark.parametrize(
        "body",
        [{"line": "show version"}, {"key": "interrupt"}, {"data": ""}, {"data": 5}, {"data": None}, ["show arp"]],
    )
    def test_input_refuses_a_body_without_text(self, client: Any, gateway: FakeTerminalGateway, body: object) -> None:
        """The old line and key shapes, an empty text, and a value that is not text get bad_request."""
        answer = client.post(TERMINAL_PATH.format(session_id="shell1", route="input"), json=body)  # Send the body.
        assert answer.status_code == 400  # The contract status of bad_request.
        assert answer.get_json()["field"] == "data"  # The error names the missing data field.
        assert gateway.sends == []  # The gateway received nothing.

    def test_input_refuses_a_body_that_is_not_json(self, client: Any, gateway: FakeTerminalGateway) -> None:
        """A body that is not JSON gets bad_request instead of a server error."""
        path = TERMINAL_PATH.format(session_id="shell1", route="input")  # The input route of one shell.
        answer = client.post(path, data="{not json", content_type="application/json")  # Send broken JSON.
        empty = client.post(path)  # Send no body.
        assert answer.status_code == 400 and empty.status_code == 400  # Both bodies get bad_request.
        assert answer.get_json()["code"] == "bad_request"  # The standard error shape.
        assert gateway.sends == []  # The gateway received nothing.

    def test_input_returns_the_gateway_refusals(self, client: Any) -> None:
        """A screen session gets read_only, and an oversized text gets too_large."""
        screen = client.post(
            TERMINAL_PATH.format(session_id="screen1", route="input"), json={"data": "q"}
        )  # Send a key to a screen command.
        oversized = client.post(
            TERMINAL_PATH.format(session_id="shell1", route="input"), json={"data": "x" * (MAX_INPUT_BYTES + 1)}
        )  # Send one byte more than the limit.
        assert screen.status_code == 409 and screen.get_json()["code"] == "read_only"  # Read-only refusal.
        assert oversized.status_code == 413 and oversized.get_json()["code"] == "too_large"  # Size refusal.


class TestTerminalResizeRoute:
    """The terminal size route checks the value types and passes them to the gateway."""

    def test_resize_passes_the_size(self, client: Any, gateway: FakeTerminalGateway) -> None:
        """A good size reaches the gateway and comes back in the answer."""
        answer = client.post(
            TERMINAL_PATH.format(session_id="shell1", route="resize"), json={"cols": 120, "rows": 40}
        )  # Send one terminal size.
        assert answer.status_code == 202  # The contract status of an accepted size.
        assert answer.get_json() == {"cols": 120, "rows": 40}  # The stored size comes back.
        assert gateway.sizes == [("shell1", 120, 40)]  # The gateway received the size.

    @pytest.mark.parametrize(
        ("body", "field"),
        [
            ({"cols": "120", "rows": 40}, "cols"),
            ({"cols": True, "rows": 40}, "cols"),
            ({"cols": 120.5, "rows": 40}, "cols"),
            ({"cols": 120}, "rows"),
            ({"cols": 120, "rows": None}, "rows"),
            ([120, 40], "cols"),
        ],
    )
    def test_resize_refuses_a_bad_size(
        self, client: Any, gateway: FakeTerminalGateway, body: object, field: str
    ) -> None:
        """A size value that is not a whole number gets bad_request."""
        answer = client.post(TERMINAL_PATH.format(session_id="shell1", route="resize"), json=body)  # Send the body.
        assert answer.status_code == 400  # The contract status of bad_request.
        assert answer.get_json()["field"] == field  # The error names the bad field.
        assert gateway.sizes == []  # The gateway received nothing.


class TestTerminalFormToken:
    """The terminal routes that change a device need the form token."""

    @pytest.mark.parametrize(
        ("route", "body"), [("input", {"data": "show arp\r"}), ("resize", {"cols": 80, "rows": 24})]
    )
    def test_post_without_the_form_token_is_refused(self, route: str, body: dict[str, object]) -> None:
        """A POST without the token gets csrf_expired, and the gateway receives nothing."""
        token_app = RouteTestApp.build(form_token_check=True)  # The app that checks the form token.
        answer = token_app.test_client().post(TERMINAL_PATH.format(session_id="shell1", route=route), json=body)
        fake_gateway = token_app.config[WebSocketsServices.CONFIG_KEY].gateway  # The fake behind the routes.
        assert answer.status_code == 400  # The portal keeps the status of the token library.
        assert answer.get_json()["code"] == "csrf_expired"  # The page can tell the operator to reload.
        assert (fake_gateway.sends, fake_gateway.sizes) == ([], [])  # No text and no size reached the gateway.

    def test_read_needs_no_form_token(self) -> None:
        """A GET read changes nothing on the device, so it needs no token."""
        token_app = RouteTestApp.build(form_token_check=True)  # The app that checks the form token.
        answer = token_app.test_client().get(TERMINAL_PATH.format(session_id="shell1", route="terminal"))  # Read.
        assert answer.status_code == 200  # The read answers without a token.
        assert answer.get_json()["state"] == "live"  # The gateway answer reaches the page.
