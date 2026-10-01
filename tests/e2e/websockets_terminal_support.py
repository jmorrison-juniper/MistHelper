"""Shared browser helpers for the WebSockets terminal journeys.

Why:
    Issue #3671 needs browser proof that the terminal page uses the real
    WebSockets service stack with the fake Mist cloud.
"""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import logging  # Keep e2e helper records visible.
import socket  # Bind the Flask server to a free local port.
import threading  # Run Flask beside Playwright.
from collections.abc import Iterator  # Type fixture yields and helper results.
from pathlib import Path  # Store screenshots under test-artifacts.
from typing import Any  # Playwright objects are duck typed in these helpers.

import pytest  # Skip journeys until lead-owned code is present.

from src.websocket_streams.intake.start_request import DeviceFacts  # Fake picker returns real device facts.
from src.websocket_streams.live.sessions.settings import StreamSettings  # Tests enable shell starts.
from src.websocket_streams.web.services import WebSocketsServiceParts, WebSocketsServices  # Install real services.
from tests.support.fake_mist_cloud.api import FakeApiSession  # Fake Mist REST seam.
from tests.support.fake_mist_cloud.devices import (
    MonitorFramingScreenDevice,
    ScreenDevice,
    ShellDevice,
    StreamDevice,
)  # Fake live devices.
from tests.support.fake_mist_cloud.server import FakeMistCloud  # Fake WebSocket cloud.

logger = logging.getLogger(__name__)  # Keep helper logs under this module.

ARTIFACT_DIR = Path(__file__).resolve().parents[2] / "test-artifacts" / "websockets-terminal"  # Screenshot folder.
ORG_ID = "99999999-8888-7777-6666-555555555555"  # Fake organization identifier.
SITE_ID = "11111111-2222-3333-4444-555555555555"  # Fake site identifier.
DEVICE_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"  # Fake EX switch identifier.
READY_TIMEOUT_MS = 15000  # Bound each browser wait.


class FakePickerService:
    """Picker service used by the real start checker."""

    def devices(self, _site_id: str) -> dict[str, object]:
        """Return the fake EX switch row."""
        row = {"id": DEVICE_ID, "label": "EX Switch 1", "family": "ex", "detail": "EX4100"}  # Device row.
        return {"rows": [row], "total_count": 1, "reason": None}  # Picker payload.

    def maps(self, _site_id: str) -> dict[str, object]:
        """Return no maps for terminal tests."""
        return {"rows": [], "total_count": 0, "reason": "The site has no maps."}  # Empty picker.

    def assets(self, _site_id: str) -> dict[str, object]:
        """Return no assets for terminal tests."""
        return {"rows": [], "total_count": 0, "reason": "The site has no assets."}  # Empty picker.

    def sdkclients(self, _site_id: str, _map_id: str) -> dict[str, object]:
        """Return no SDK clients for terminal tests."""
        return {"rows": [], "total_count": 0, "reason": "The map has no SDK clients."}  # Empty picker.

    def mxedges(self, _site_id: str | None) -> dict[str, object]:
        """Return no Mist Edges for terminal tests."""
        return {"rows": [], "total_count": 0, "reason": "No Mist Edge is available."}  # Empty picker.

    def describe_device(self, _site_id: str, _device_id: str) -> DeviceFacts:
        """Return the fake EX switch facts."""
        return DeviceFacts(name="EX Switch 1", family="ex")  # Start checks need the name and family.


class PortalFakeApiSession(FakeApiSession):
    """Fake API session that also accepts the Mist SDK site-list call shape."""

    def mist_get(self, uri: str, query: object | None = None) -> object:
        """Record a GET and ignore query fields that the fake does not need."""
        return super().mist_get(uri)  # The fake site override supplies deterministic site rows.


class DelayedShellDevice(ShellDevice):
    """Fake shell that delays the first banner for non-final state journeys."""

    def __init__(self, delay_seconds: float) -> None:
        """Build a delayed shell."""
        super().__init__()  # Reuse the normal fake shell input and resize behavior.
        self.delay_seconds = delay_seconds  # Tests keep the delay short and deterministic.

    def on_connect(self, connection: Any) -> None:
        """Delay the banner while the portal read route remains non-final."""
        import time  # Import locally so normal harness startup stays small.

        time.sleep(self.delay_seconds)  # Delay output past the first long-read timeout.
        super().on_connect(connection)  # Send the normal banner and prompt after the delay.


class QuietShellDevice(ShellDevice):
    """Fake shell that records large paste input without echoing each byte."""

    def _process_input(self, connection: Any, data: bytes) -> None:
        """Record input through the base receive path and avoid large echo output."""
        if data.endswith(b"exit\r") or data.endswith(b"exit\n"):  # Keep normal close available for cleanups.
            connection.send_text("\r\nlogout\r\n")  # Send the small close notice.
            connection.send_close(1000)  # Close the fake shell normally.


class PlainPromptShellDevice(ShellDevice):
    """Fake shell that leaves bracketed paste off for visible paste echo checks."""

    def _send_prompt(self) -> None:
        """Send the prompt without bracketed paste mode."""
        if self._connection is not None:  # A prompt can be sent only after connect.
            self._send_output(self._connection, self.prompt.encode())  # Keep paste echo visible for screenshots.


class PushableShellDevice(ShellDevice):
    """Fake shell that sends output and closes while the browser shows another session."""

    def push_output(self, payload: bytes) -> None:
        """Send one output frame on the open shell connection.

        Args:
            payload: The terminal bytes without the Mist channel marker.
        """
        logger.info("Fake shell sends %d bytes with no browser input", len(payload))  # Record the device-side event.
        self._send_output(self._open_connection(), payload)  # Answer the pending long read of this shell.
        logger.debug("Fake shell sent the pushed output")  # Record the send result.

    def close_shell(self) -> None:
        """Close the shell with the empty close frame that real Mist sends after exit."""
        logger.info("Fake shell closes with no browser input")  # Record the device-side close.
        self._open_connection().send_close(None)  # Real Mist sends an empty close payload.
        logger.debug("Fake shell sent the close frame")  # Record the close result.

    def _open_connection(self) -> Any:
        """Return the open shell connection, or fail with a clear harness error."""
        if self._connection is None:  # The browser must start the shell before a test pushes output.
            raise RuntimeError("The fake shell has no open connection.")  # Stop the journey with a clear cause.
        return self._connection  # Later sends use this shell connection.


class TerminalPortalHarness:
    """Own one fake cloud and one portal server for terminal journeys."""

    def __init__(self, shell: ShellDevice | None = None, screen: ScreenDevice | None = None) -> None:
        """Create a stopped harness."""
        self.cloud = FakeMistCloud()  # Fake cloud starts in start().
        self.stream = StreamDevice()  # Channel stream device.
        self.shell = shell or ShellDevice()  # Shell terminal device.
        self.screen = screen or ScreenDevice(updates=100)  # Screen terminal device.
        self.api: FakeApiSession | None = None  # Built after the cloud has a port.
        self.base_url = ""  # Flask URL becomes available after start().
        self._server: Any | None = None  # Werkzeug server handle.
        self._thread: threading.Thread | None = None  # Server thread handle.

    def start(self) -> TerminalPortalHarness:
        """Start the fake cloud and the Flask app."""
        self.cloud.start()  # Bind the fake cloud to a free port.
        self._register_devices()  # Register WebSocket paths before starts.
        self.api = self._api_session()  # Build the API session with shell path overrides.
        app = self._app()  # Build the portal app with real WebSocket services.
        self._server = self._server_for(app)  # Bind Flask to a free port.
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)  # Serve beside Playwright.
        self._thread.start()  # Start the HTTP server.
        self.base_url = f"http://127.0.0.1:{self._server.server_port}"  # Publish the browser URL.
        return self  # Fixtures use this value.

    def stop(self) -> None:
        """Stop the Flask server and fake cloud."""
        if self._server is not None:  # The server exists after start().
            self._server.shutdown()  # Stop HTTP serving.
        if self._thread is not None:  # The thread exists after start().
            self._thread.join(timeout=5)  # Bound server shutdown.
        self.cloud.stop()  # Stop WebSocket worker threads.

    def open_page(self, page: Any) -> None:
        """Open the WebSockets page and wait for the terminal catalog."""
        page.goto(f"{self.base_url}/websockets", wait_until="networkidle", timeout=READY_TIMEOUT_MS)  # Open page.
        page.context.grant_permissions(["clipboard-read", "clipboard-write"], origin=self.base_url)  # Clipboard.
        page.get_by_test_id("ws-catalog-entry-ex.createShellSession").wait_for(
            state="visible", timeout=READY_TIMEOUT_MS
        )  # Wait for shell catalog.

    def start_shell(self, page: Any) -> None:
        """Start one shell terminal session."""
        page.get_by_test_id("ws-catalog-entry-ex.createShellSession").click()  # Choose the shell entry.
        self._choose_device(page)  # Fill site and device fields.
        page.get_by_test_id("ws-confirmation-input").fill("EX Switch 1")  # Confirm the live shell.
        page.get_by_test_id("ws-start-button").click()  # Start the session.
        page.get_by_test_id("ws-terminal-screen").wait_for(state="visible", timeout=READY_TIMEOUT_MS)  # Terminal.

    def screenshot(self, page: Any, name: str) -> Path:
        """Save one full-page screenshot."""
        ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)  # Ensure the artifact folder exists.
        path = ARTIFACT_DIR / name  # Build the screenshot path.
        page.evaluate("window.scrollTo(0, 0)")  # Keep the sticky navigation at the top of full-page shots.
        page.screenshot(path=str(path), full_page=True)  # Save the browser evidence.
        return path  # Tests and reports use this path.

    def _register_devices(self) -> None:
        """Register fake cloud WebSocket paths."""
        self.cloud.register("/api-ws/v1/stream", self.stream)  # Channel, command, and capture stream path.
        self.cloud.register("/shell/default", self.shell)  # Default shell trigger path.
        self.cloud.register("/shell/" + DEVICE_ID, self.shell)  # Device-specific shell trigger path.
        self.cloud.register("/screen/default", self.screen)  # Default screen trigger path.
        self.cloud.register("/screen/" + DEVICE_ID, self.screen)  # Device-specific screen trigger path.

    def _api_session(self) -> FakeApiSession:
        """Return the fake API session with terminal URL overrides."""
        api = PortalFakeApiSession(self.cloud)  # The portal site picker uses the SDK GET signature.
        api.add_override("/orgs/" + ORG_ID + "/sites", 200, [{"id": SITE_ID, "name": "Mist Lab"}])  # Sites.
        api.add_override("/shell", 200, {"url": f"{self.cloud.base_ws_url}/shell/{DEVICE_ID}"})  # Shell path.
        api.add_override("/run_top", 200, {"url": f"{self.cloud.base_ws_url}/screen/{DEVICE_ID}"})  # Screen path.
        api.add_override("/monitor_traffic", 200, {"url": f"{self.cloud.base_ws_url}/screen/{DEVICE_ID}"})  # Screen.
        return api  # Return configured fake API.

    def _app(self) -> Any:
        """Build the Flask app with real WebSocket services."""
        from web_portal.app import WebPortalApp  # Build the normal portal app.
        from web_portal.menu_registry import build_static_menu_actions  # Supply normal menus.

        if self.api is None:  # start() builds the fake API before the app.
            raise RuntimeError("The fake API session is not ready.")  # Fail with a clear harness error.
        app = WebPortalApp.create_app(self.api, build_static_menu_actions(), ORG_ID)  # Build app.
        app.config["TESTING"] = True  # Raise route errors during tests.
        app.config[WebSocketsServices.CONFIG_KEY] = self._services(app)  # Install real services with fake parts.
        return app  # Return configured app.

    def _services(self, _app: Any) -> WebSocketsServices:
        """Build real WebSocket services with fake app dependencies."""
        from src.websocket_streams.catalog.channels import ChannelCatalog  # Real channel catalog.
        from src.websocket_streams.catalog.registry import StreamCatalog  # Real catalog registry.
        from src.websocket_streams.catalog.utilities import UtilityCatalog  # Real utility catalog.
        from src.websocket_streams.intake.start_request import StartRequestChecker  # Real start checker.
        from src.websocket_streams.live.sessions.manager import RunnerFactory, StreamSessionManager  # Real manager.
        from src.websocket_streams.live.transport.endpoint import TransportProfile  # Loopback profile.

        picker = FakePickerService()  # Use deterministic site and device rows.
        settings = StreamSettings(shell_enabled=True, max_sessions=8, idle_seconds=120)  # Enable shell starts.
        catalog = StreamCatalog(
            ChannelCatalog(), UtilityCatalog(), changes_enabled=False, shell_enabled=True
        )  # Catalog.
        checker = StartRequestChecker(catalog, picker, ORG_ID)  # Real checker protects starts.
        profile = TransportProfile(
            stream_url=f"{self.cloud.base_ws_url}/api-ws/v1/stream",
            allow_loopback=True,
            read_timeout_seconds=1.0,
            subscribe_timeout_seconds=1.0,
        )  # Short fake-cloud timeouts keep tests fast.
        if self.api is None:  # start() builds the fake API before services.
            raise RuntimeError("The fake API session is not ready.")  # Fail with a clear harness error.
        manager = StreamSessionManager(settings, RunnerFactory(self.api, profile))  # Real manager and runners.
        parts = WebSocketsServiceParts(catalog, checker, picker, manager, settings, None)  # Ready service parts.
        return WebSocketsServices(parts)  # Routes call the real service facade.

    def _server_for(self, app: Any) -> Any:
        """Return a Werkzeug server on a free port."""
        from werkzeug.serving import make_server  # Import only when a browser test runs.

        server = make_server("127.0.0.1", self._free_port(), app, threaded=True)  # Bind an ephemeral port.
        return server  # The caller starts serve_forever in a thread.

    def _choose_device(self, page: Any) -> None:
        """Choose the fake site and device in the start form."""
        page.locator('[data-testid="ws-field-site_id"]').select_option(SITE_ID)  # Choose site.
        page.locator('[data-testid="ws-field-device_id"]').select_option(DEVICE_ID)  # Choose device.

    @staticmethod
    def _free_port() -> int:
        """Return an unused loopback TCP port."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:  # Ask the OS for a port.
            probe.bind(("127.0.0.1", 0))  # Port zero selects a free port.
            return int(probe.getsockname()[1])  # Return the selected port.


@pytest.fixture()
def terminal_harness() -> Iterator[TerminalPortalHarness]:
    """Return a started terminal portal harness."""
    harness = TerminalPortalHarness().start()  # Start the fake cloud and portal.
    try:
        yield harness  # Run the journey.
    finally:
        harness.stop()  # Clean up all server threads.


@pytest.fixture()
def delayed_terminal_harness() -> Iterator[TerminalPortalHarness]:
    """Return a terminal harness whose shell delays its first output."""
    harness = TerminalPortalHarness(shell=DelayedShellDevice(delay_seconds=0.8)).start()  # Delay first output.
    try:
        yield harness  # Run the delayed journey.
    finally:
        harness.stop()  # Clean up all server threads.


@pytest.fixture()
def quiet_terminal_harness() -> Iterator[TerminalPortalHarness]:
    """Return a terminal harness whose shell records paste input without echo."""
    harness = TerminalPortalHarness(shell=QuietShellDevice()).start()  # Use a quiet shell for large paste input.
    try:
        yield harness  # Run the large paste journey.
    finally:
        harness.stop()  # Clean up all server threads.


@pytest.fixture()
def paste_echo_terminal_harness() -> Iterator[TerminalPortalHarness]:
    """Return a terminal harness whose shell shows pasted text plainly."""
    harness = TerminalPortalHarness(shell=PlainPromptShellDevice()).start()  # Use plain prompt for dialog evidence.
    try:
        yield harness  # Run the paste dialog journey.
    finally:
        harness.stop()  # Clean up all server threads.


@pytest.fixture()
def monitor_terminal_harness() -> Iterator[TerminalPortalHarness]:
    """Return a terminal harness with live Mist monitor framing."""
    harness = TerminalPortalHarness(screen=MonitorFramingScreenDevice()).start()  # Use fixed 40-row screen output.
    try:
        yield harness  # Run the fixed screen journey.
    finally:
        harness.stop()  # Clean up all server threads.


@pytest.fixture()
def pushable_terminal_harness() -> Iterator[TerminalPortalHarness]:
    """Return a terminal harness whose shell can send output with no browser input."""
    harness = TerminalPortalHarness(shell=PushableShellDevice()).start()  # Let the test drive late shell output.
    try:
        yield harness  # Run the session switch journey.
    finally:
        harness.stop()  # Clean up all server threads.
