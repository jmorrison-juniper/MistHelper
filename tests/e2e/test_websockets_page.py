"""Browser journey for the WebSockets page.

Why:
    Issue #3551 needs proof that the new tab lets an operator start, view,
    limit, lock, and interact with WebSocket-style sessions in a browser.
"""

from __future__ import annotations  # Keep annotations lazy for Playwright imports.

import json  # The fake keeps JSON message text, like the real buffer.
import logging  # Keep browser test records under this module.
import socket  # Find an unused local port.
import threading  # Serve Flask and fake stream output beside the browser.
import time  # Let fake runners emit messages on a short timer.
from collections.abc import Iterator  # Type fixtures and download streams.
from dataclasses import dataclass, field  # Store fake session state clearly.
from pathlib import Path  # Save screenshots under the test artifact folder.
from types import SimpleNamespace  # Build fake SDK answers.
from typing import Any  # Type Playwright objects without importing private types.

import pytest  # Use fixtures and Playwright integration.

from src.websocket_streams.live.sessions.buffer import MessagePage, StreamMessage  # The fake keeps real records.

logger = logging.getLogger(__name__)  # Keep this test module visible in logs.

pytest.importorskip("playwright", reason="playwright is absent, so the browser journey cannot run")  # Browser guard.

READY_TIMEOUT_MS = 15000  # Bound every browser wait.
# The container mounts data/, so the screenshots stay in the test-artifacts/ folder instead.
ARTIFACT_DIR = Path(__file__).resolve().parents[2] / "test-artifacts" / "websockets"  # Git ignores this folder.
ORG_ID = "99999999-8888-7777-6666-555555555555"  # Fake organization identifier.
SITE_ID = "11111111-2222-3333-4444-555555555555"  # First fake site identifier.
SITE_ID_2 = "22222222-3333-4444-5555-666666666666"  # Second fake site identifier.
DEVICE_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"  # Fake device identifier.
ROUTE_TABLE_TEXT = (
    '{"columns":[{"id":"Destination","display_name":"Destination"},{"id":"Gateway","display_name":"Gateway"}],'
    '"rows":[{"Destination":"10.0.0.0/24","Gateway":"192.168.1.1"}],"status":"SUCCESS","message":""}'
)  # A route table as the device sends it, as JSON text.


@dataclass
class BrowserSession:
    """One fake browser-visible session."""

    session_id: str  # Stable session identifier.
    kind: str  # channel, utility, or shell.
    key: str  # Catalog key.
    title: str  # Card title.
    output: str  # json, lines, packets, or terminal.
    safety: str  # read, capture, change, or shell.
    messages: list[StreamMessage] = field(default_factory=list)  # Buffered message records.
    state: str = "live"  # Current state.
    live: bool = True  # Live sessions count toward the limit.
    reason: str = ""  # Plain end reason.
    input_ready: bool = True  # Shell input is ready in the fake.


class FakeWebSocketServices:
    """Fake WebSocket service with timer-driven runners."""

    def __init__(self) -> None:
        """Build the fake catalog and empty session store."""
        self._lock = threading.Lock()  # Protect sessions while timer threads write.
        self._sessions: dict[str, BrowserSession] = {}  # Active and ended sessions.
        self._next_id = 1  # Deterministic identifiers make tests easy to read.
        self.shell_inputs: list[dict[str, object]] = []  # Record shell input forms.

    def reset(self) -> None:
        """Clear sessions before one browser story."""
        with self._lock:  # Timer threads can still be ending.
            self._sessions.clear()  # Remove all prior sessions.
            self._next_id = 1  # Reset identifiers.
            self.shell_inputs.clear()  # Remove prior shell input.

    def catalog_payload(self) -> dict[str, object]:
        """Return the catalog shown by the page."""
        return {
            "ready": True,
            "reason": None,
            "flags": {},
            "limits": {"max_sessions": 2, "idle_seconds": 120, "capture_seconds": 60},
            "channels": [self._channel()],
            "utilities": self._utilities(),
        }  # Catalog.

    def start_session(self, body: object) -> dict[str, object]:
        """Start one fake session or return a contract-like refusal."""
        if not isinstance(body, dict):  # The page must send a JSON object.
            return {"error": "The request body is not valid.", "code": "bad_request"}  # Defensive answer.
        with self._lock:  # Session limit and identifier allocation must be atomic.
            live = [session.title for session in self._sessions.values() if session.live]  # Current live titles.
            if len(live) >= 2:  # The fake limit is two sessions.
                from src.websocket_streams.intake.fields import StreamRequestError  # Import only on refusal.

                raise StreamRequestError(
                    "limit_reached", "The live session limit is reached.", {"live": live}
                )  # Limit.
            session = self._new_session(body)  # Build the fake session.
            self._sessions[session.session_id] = session  # Store it before the runner starts.
        self._start_runner(session)  # Start timer output after the session exists.
        return self._payload(session)  # Return the session card payload.

    def list_sessions(self) -> dict[str, object]:
        """Return all fake sessions."""
        with self._lock:  # Copy while no timer mutates the store.
            sessions = [self._payload(session) for session in self._sessions.values()]  # Session payloads.
            live_count = sum(1 for session in self._sessions.values() if session.live)  # Live count.
        return {"sessions": sessions, "limits": {"max_sessions": 2, "live_count": live_count}}  # List payload.

    def read_messages(self, session_id: str, after: int, _limit: int) -> MessagePage:
        """Return messages after the given sequence."""
        with self._lock:  # Copy while timer threads can write.
            session = self._sessions[session_id]  # The test always names a known session.
            messages = [message for message in session.messages if message.seq > after]  # New messages.
            next_after = messages[-1].seq if messages else after  # Highest returned sequence.
            payload = self._payload(session)  # Copy the session card state.
        return MessagePage(payload, messages, next_after, 1, False)  # Read.

    def stop_session(self, session_id: str) -> dict[str, object]:
        """Stop one fake session."""
        with self._lock:  # Update state atomically.
            session = self._sessions[session_id]  # The browser stops a visible session.
            session.state = "stopped"  # Mark stopped.
            session.live = False  # Remove it from the live limit.
            session.reason = "The operator stopped the session."  # Plain reason.
            return self._payload(session)  # Return the stopped card.

    def send_input(self, session_id: str, body: object) -> dict[str, object]:
        """Accept shell input and echo a safe output line."""
        payload = body if isinstance(body, dict) else {}  # Keep only JSON objects.
        self.shell_inputs.append(payload)  # Prove line and key routes were used.
        with self._lock:  # Append output with a sequence number.
            session = self._sessions[session_id]  # The selected shell session.
            self._add_message(session, "text", "device> output accepted", None)  # Echo safe text only.
        return {"ok": True}  # Confirm input.

    def delete_session(self, _session_id: str) -> dict[str, object]:
        """Confirm delete for ended sessions."""
        return {"ok": True}  # The browser journey does not delete live sessions.

    def download_session(self, session_id: str) -> tuple[str, Iterator[str]]:
        """Return the fake session messages as JSON Lines."""
        with self._lock:  # Copy while timer threads can write.
            count = len(self._sessions[session_id].messages)  # Count messages for the stream.
        return "fake-session.jsonl", iter([f'{{"count":{count}}}\n'])  # Safe JSON Lines.

    def devices(self, _site_id: str) -> dict[str, object]:
        """Return one EX device for utility stories."""
        row = {"id": DEVICE_ID, "label": "EX Switch 1", "family": "ex", "detail": "EX4100"}  # Device row.
        return {"rows": [row], "total_count": 1, "reason": None}  # Picker payload.

    def maps(self, site_id: str) -> dict[str, object]:
        """Return no maps for these stories."""
        return {"rows": [], "total_count": 0, "reason": f"The site {site_id} has no maps."}  # Empty picker.

    def assets(self, site_id: str) -> dict[str, object]:
        """Return no assets for these stories."""
        return {"rows": [], "total_count": 0, "reason": f"The site {site_id} has no assets."}  # Empty picker.

    def sdkclients(self, site_id: str, map_id: str) -> dict[str, object]:
        """Return no SDK clients for these stories."""
        return {
            "rows": [],
            "total_count": 0,
            "reason": f"The map {map_id} in site {site_id} has no SDK clients.",
        }  # Empty.

    def mxedges(self, _site_id: str | None) -> dict[str, object]:
        """Return no Mist Edges for these stories."""
        return {"rows": [], "total_count": 0, "reason": "No Mist Edge is available."}  # Empty picker.

    def shutdown(self) -> None:
        """Stop all fake sessions."""
        with self._lock:  # Stop sessions atomically.
            for session in self._sessions.values():  # Visit each fake session.
                session.live = False  # End the fake session.
                session.state = "stopped"  # Mark stopped.

    def _channel(self) -> dict[str, object]:
        """Return one channel catalog entry."""
        site_field = {"name": "site_id", "label": "Site", "kind": "uuid", "required": True, "picker": "sites"}  # Site.
        return {
            "key": "site.stats.devices",
            "scope": "site",
            "name": "Device statistics",
            "description": "Live device statistics.",
            "identifiers": [site_field],
            "repeatable": "site_id",
        }  # Channel.

    def _utilities(self) -> list[dict[str, object]]:
        """Return the fake utility catalog entries."""
        targets = [
            self._field("site_id", "Site", "uuid", "sites"),
            self._field("device_id", "Device", "uuid", "devices"),
        ]  # Targets.
        host = {"name": "host", "label": "Host", "kind": "host", "required": True, "default": "8.8.8.8"}  # Host field.
        count = {
            "name": "count",
            "label": "Count",
            "kind": "integer",
            "required": False,
            "minimum": 1,
            "maximum": 100,
            "default": 3,
        }  # Count.
        packets = {
            "name": "num_packets",
            "label": "Packets",
            "kind": "integer",
            "minimum": 1,
            "maximum": 10000,
            "default": 5,
        }  # Packets.
        duration = {
            "name": "duration",
            "label": "Duration (seconds)",
            "kind": "integer",
            "required": True,
            "minimum": 60,
            "maximum": 3600,
            "default": 60,
        }
        return [
            self._utility("ex.ping", "Ping", "read", "lines", targets, [host, count], False),
            self._utility("ex.retrieveRoutes", "Routes", "read", "lines", targets, [], False),
            self._utility("ex.remotePcap", "Packet capture", "capture", "packets", targets, [packets, duration], False),
            self._utility("ex.bouncePort", "Bounce port", "change", "lines", targets, [], True),
            self._utility("ex.shell", "Remote shell", "shell", "terminal", targets, [], False),
        ]  # Utilities.

    def _field(self, name: str, label: str, kind: str, picker: str) -> dict[str, object]:
        """Return one identifier field."""
        return {"name": name, "label": label, "kind": kind, "required": True, "picker": picker}  # Field.

    def _utility(
        self,
        key: str,
        name: str,
        safety: str,
        output: str,
        targets: list[dict[str, object]],
        fields: list[dict[str, object]],
        locked: bool,
    ) -> dict[str, object]:
        """Return one utility entry."""
        return {
            "key": key,
            "family": "ex",
            "name": name,
            "description": name + " from a switch.",
            "safety": safety,
            "locked": locked,
            "output": output,
            "targets": targets,
            "fields": fields,
            "scope": "site",
        }  # Utility.

    def _new_session(self, body: dict[str, object]) -> BrowserSession:
        """Create one fake session from a start body."""
        session_id = f"fake{self._next_id}"  # Deterministic identifier.
        self._next_id += 1  # Advance for the next session.
        key = str(body.get("key") or "")  # Read the catalog key.
        kind = str(body.get("kind") or "utility")  # Read the request kind.
        output = (
            "json"
            if kind == "channel"
            else {"ex.ping": "lines", "ex.remotePcap": "packets", "ex.shell": "terminal"}.get(key, "lines")
        )  # View.
        safety = "read" if key != "ex.remotePcap" else "capture"  # Safety for the card.
        return BrowserSession(session_id, kind, key, self._title(key), output, safety)  # Session record.

    def _start_runner(self, session: BrowserSession) -> None:
        """Start the fake timer runner for one session."""
        thread = threading.Thread(target=self._run_messages, args=(session.session_id,), daemon=True)  # Runner.
        thread.start()  # Emit messages beside the browser.

    def _run_messages(self, session_id: str) -> None:
        """Emit fake messages for one session."""
        for index in range(3):  # Three messages are enough for the browser waits.
            time.sleep(0.1)  # A short delay proves polling without slowing the suite.
            with self._lock:  # Timer thread writes the session buffer.
                session = self._sessions.get(session_id)  # The session may have stopped.
                if session is None or not session.live:  # A stopped session emits no more messages.
                    return  # End the fake runner.
                self._emit_kind(session, index)  # Add one message by output kind.

    def _emit_kind(self, session: BrowserSession, index: int) -> None:
        """Append one message for the session output type."""
        if session.output == "packets":  # Packet view reads summaries.
            self._add_message(
                session, "packet", {"length": 64 + index}, "12:00 source destination tcp " + str(64 + index)
            )  # Packet.
        elif session.output == "terminal":  # Terminal view reads text.
            self._add_message(session, "text", "device> ready", None)  # Prompt.
        elif session.key == "ex.retrieveRoutes":  # The route utility sends a table as JSON text.
            self._add_message(session, "text", ROUTE_TABLE_TEXT, None)  # Route table.
        elif session.output == "lines":  # Line view reads text lines.
            self._add_message(session, "text", "reply from 8.8.8.8", None)  # Ping line.
        else:  # Channel view reads JSON.
            self._add_message(session, "json", {"site": session.title, "count": index}, None)  # JSON row.

    def _add_message(self, session: BrowserSession, kind: str, content: object, summary: str | None) -> None:
        """Append one message record with the next sequence number, like the real buffer."""
        seq = len(session.messages) + 1  # Sequence numbers start at one.
        content_json = json.dumps(content, sort_keys=True, separators=(",", ":"))  # The real buffer keeps JSON text.
        message = StreamMessage(
            seq, "2026-09-29T20:00:00Z", kind, content_json, len(content_json), False, "HQ", summary
        )  # Record.
        session.messages.append(message)  # Add the message to the buffer.

    def _payload(self, session: BrowserSession) -> dict[str, object]:
        """Return one session payload."""
        counters = {"received": len(session.messages), "dropped": 0, "shortened": 0, "bytes": 0}  # Counters.
        return {
            "session_id": session.session_id,
            "kind": session.kind,
            "key": session.key,
            "title": session.title,
            "output": session.output,
            "safety": session.safety,
            "state": session.state,
            "live": session.live,
            "reason": session.reason,
            "input_ready": session.input_ready,
            "started_at": "2026-09-29T20:00:00Z",
            "ended_at": None,
            "counters": counters,
            "rate_per_second": 1.0,
            "last_seq": len(session.messages),
        }  # Payload.

    def _title(self, key: str) -> str:
        """Return a title for one catalog key."""
        return {
            "site.stats.devices": "Device statistics - HQ and Branch",
            "ex.ping": "Ping - EX Switch 1",
            "ex.retrieveRoutes": "Routes - EX Switch 1",
            "ex.remotePcap": "Packet capture - EX Switch 1",
            "ex.shell": "Remote shell - EX Switch 1",
        }.get(
            key, key
        )  # Title.


@pytest.fixture(scope="module")
def fake_services() -> FakeWebSocketServices:
    """Return the fake services object shared by the server."""
    return FakeWebSocketServices()  # One fake backs the app fixture.


def free_port() -> int:
    """Return an unused local TCP port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:  # Ask the operating system for a port.
        probe.bind(("127.0.0.1", 0))  # Port zero means any free port.
        return int(probe.getsockname()[1])  # Return the selected port.


@pytest.fixture(scope="module")
def websocket_portal(fake_services: FakeWebSocketServices) -> Iterator[str]:
    """Serve the web portal with fake WebSocket services."""
    import mistapi  # Patch the site picker SDK seam.
    from werkzeug.serving import make_server  # Start an in-process server.

    from src.websocket_streams.web.services import WebSocketsServices  # Inject the fake services.
    from web_portal.app import WebPortalApp  # Build the same app as the portal.
    from web_portal.menu_registry import build_static_menu_actions  # Supply normal menu actions.

    def list_sites(_session: object, _org_id: str) -> SimpleNamespace:
        """Return two sites for the multi-site picker."""
        rows = [{"id": SITE_ID, "name": "HQ"}, {"id": SITE_ID_2, "name": "Branch"}]  # Sites.
        return SimpleNamespace(data=rows)  # SDK answer shape.

    with pytest.MonkeyPatch.context() as patcher:  # Undo SDK patches when the server stops.
        patcher.setattr(mistapi.api.v1.orgs.sites, "listOrgSites", list_sites)  # Patch site picker.
        app = WebPortalApp.create_app(SimpleNamespace(), build_static_menu_actions(), ORG_ID)  # Build app.
        app.config["TESTING"] = True  # Raise route errors during the test.
        app.config[WebSocketsServices.CONFIG_KEY] = fake_services  # Inject the fake service.
        server = make_server("127.0.0.1", free_port(), app, threaded=True)  # Bind a free port.
        thread = threading.Thread(target=server.serve_forever, daemon=True)  # Serve beside Playwright.
        logger.info("Starting the WebSocket portal on port %d", server.server_port)  # Log server start.
        thread.start()  # Start the server loop.
        try:
            yield f"http://127.0.0.1:{server.server_port}"  # Give tests the base URL.
        finally:
            server.shutdown()  # Stop the server loop.
            thread.join(timeout=10)  # Wait for server thread exit.
            WebPortalApp.shutdown_app(app)  # Stop portal background threads.


@pytest.fixture(autouse=True)
def reset_fake(fake_services: FakeWebSocketServices) -> Iterator[None]:
    """Reset fake state before each story."""
    fake_services.reset()  # Remove prior sessions.
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)  # Ensure screenshot folder exists.
    yield  # Run the browser story.
    fake_services.reset()  # Stop sessions that the story left live.


def screenshot(page: Any, name: str) -> Path:
    """Save one full-page screenshot."""
    path = ARTIFACT_DIR / name  # Build the requested artifact path.
    page.screenshot(path=str(path), full_page=True)  # Save visual evidence.
    return path  # Return the path for assertions and reports.


def open_page(page: Any, portal: str) -> None:
    """Open the WebSockets page and wait for the catalog."""
    page.goto(f"{portal}/websockets", wait_until="networkidle", timeout=READY_TIMEOUT_MS)  # Open page.
    page.get_by_test_id("nav-websockets").wait_for(state="visible", timeout=READY_TIMEOUT_MS)  # Nav item.
    page.get_by_test_id("ws-catalog-entry-site.stats.devices").wait_for(
        state="visible", timeout=READY_TIMEOUT_MS
    )  # Catalog.


def choose_device(page: Any) -> None:
    """Choose the fake site and device in the start form."""
    page.locator('[data-testid="ws-field-site_id"]').select_option(SITE_ID)  # Choose site.
    page.locator('[data-testid="ws-field-device_id"]').select_option(DEVICE_ID)  # Choose device.


def test_channel_stream_with_multi_site_selection(page: Any, websocket_portal: str) -> None:
    """US1: a channel stream starts with two sites and shows JSON messages."""
    open_page(page, websocket_portal)  # Load the WebSockets page.
    page.get_by_test_id("ws-catalog-entry-site.stats.devices").click()  # Choose the channel.
    page.locator('[data-testid="ws-field-site_id"]').select_option([SITE_ID, SITE_ID_2])  # Choose two sites.
    page.get_by_test_id("ws-start-button").click()  # Start the stream.
    page.get_by_test_id("ws-session-title").wait_for(timeout=READY_TIMEOUT_MS)  # Session card.
    page.locator('[data-testid="ws-output"]').get_by_text('"count"').nth(0).wait_for(timeout=READY_TIMEOUT_MS)  # JSON.
    shot = screenshot(page, "01-channel-stream.png")  # Keep evidence.
    assert shot.exists()  # The screenshot was written.


def test_read_only_ping_journey(page: Any, websocket_portal: str) -> None:
    """US2: a read-only ping shows output lines."""
    open_page(page, websocket_portal)  # Load the WebSockets page.
    page.get_by_test_id("ws-catalog-entry-ex.ping").click()  # Choose ping.
    choose_device(page)  # Choose site and device.
    page.get_by_test_id("ws-start-button").click()  # Start ping.
    page.locator('[data-testid="ws-output"]').get_by_text("reply from 8.8.8.8").nth(0).wait_for(
        timeout=READY_TIMEOUT_MS
    )  # Output.
    shot = screenshot(page, "02-ping-lines.png")  # Keep evidence.
    assert shot.exists()  # The screenshot was written.


def test_packet_capture_journey(page: Any, websocket_portal: str) -> None:
    """US3: a capture shows packet rows."""
    open_page(page, websocket_portal)  # Load the WebSockets page.
    page.get_by_test_id("ws-catalog-entry-ex.remotePcap").click()  # Choose capture.
    choose_device(page)  # Choose site and device.
    page.get_by_test_id("ws-start-button").click()  # Start capture.
    page.locator('[data-testid="ws-output"]').get_by_text("source destination tcp").nth(0).wait_for(
        timeout=READY_TIMEOUT_MS
    )  # Packet.
    shot = screenshot(page, "03-packet-capture.png")  # Keep evidence.
    assert shot.exists()  # The screenshot was written.


def test_session_limit_message(page: Any, websocket_portal: str) -> None:
    """US4: the page shows the live session titles when the limit is reached."""
    open_page(page, websocket_portal)  # Load the WebSockets page.
    page.get_by_test_id("ws-catalog-entry-ex.ping").click()  # Choose ping.
    choose_device(page)  # Choose site and device.
    page.get_by_test_id("ws-start-button").click()  # Start first session.
    page.get_by_test_id("ws-start-button").click()  # Start second session.
    page.get_by_test_id("ws-start-button").click()  # Ask for one too many.
    page.get_by_text("The live session limit is reached.").wait_for(timeout=READY_TIMEOUT_MS)  # Limit message.
    shot = screenshot(page, "04-session-limit.png")  # Keep evidence.
    assert shot.exists()  # The screenshot was written.


def test_locked_change_utility(page: Any, websocket_portal: str) -> None:
    """US5: a locked change utility shows the lock and disables start."""
    open_page(page, websocket_portal)  # Load the WebSockets page.
    page.get_by_test_id("ws-catalog-entry-ex.bouncePort").click()  # Choose locked utility.
    page.get_by_text("PORTAL_WS_ENABLE_CHANGES").wait_for(timeout=READY_TIMEOUT_MS)  # Lock warning.
    assert page.get_by_test_id("ws-start-button").is_disabled()  # Locked start cannot run.
    shot = screenshot(page, "05-locked-change.png")  # Keep evidence.
    assert shot.exists()  # The screenshot was written.


def test_shell_with_line_and_key(page: Any, websocket_portal: str, fake_services: FakeWebSocketServices) -> None:
    """US6: a shell accepts a line and a key and shows terminal output."""
    open_page(page, websocket_portal)  # Load the WebSockets page.
    page.get_by_test_id("ws-catalog-entry-ex.shell").click()  # Choose shell.
    choose_device(page)  # Choose site and device.
    page.get_by_test_id("ws-confirmation-input").fill("EX Switch 1")  # Confirm the shell.
    page.get_by_test_id("ws-start-button").click()  # Start shell.
    page.get_by_test_id("ws-terminal").wait_for(state="visible", timeout=READY_TIMEOUT_MS)  # Terminal view.
    page.get_by_test_id("ws-shell-line").fill("show version")  # Type a line.
    page.get_by_test_id("ws-shell-send").click()  # Send the line.
    page.get_by_test_id("ws-key-interrupt").click()  # Send a key.
    page.get_by_text("output accepted").wait_for(timeout=READY_TIMEOUT_MS)  # Output echo.
    shot = screenshot(page, "06-shell-terminal.png")  # Keep evidence.
    assert {"line": "show version"} in fake_services.shell_inputs  # Line reached the fake.
    assert {"key": "interrupt"} in fake_services.shell_inputs  # Key reached the fake.
    assert shot.exists()  # The screenshot was written.


def test_route_table_shows_columns(page: Any, websocket_portal: str) -> None:
    """US2: a table that the device sends as JSON text shows as aligned columns."""
    open_page(page, websocket_portal)  # Load the WebSockets page.
    page.get_by_test_id("ws-catalog-entry-ex.retrieveRoutes").click()  # Choose the route utility.
    choose_device(page)  # Choose site and device.
    page.get_by_test_id("ws-start-button").click()  # Start the route read.
    output = page.locator('[data-testid="ws-output"]')  # The message view.
    output.get_by_text("10.0.0.0/24").nth(0).wait_for(timeout=READY_TIMEOUT_MS)  # The table row shows.
    text = output.inner_text()  # Read the drawn view text.
    shot = screenshot(page, "07-route-table.png")  # Keep evidence.
    assert "Destination  Gateway" in text  # The header cells show in aligned columns.
    assert '"columns"' not in text  # The raw JSON text does not show.
    assert shot.exists()  # The screenshot was written.
