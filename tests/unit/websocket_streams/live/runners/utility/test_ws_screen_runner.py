"""Test the read-only screen runner against the fake Mist cloud."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import json  # The recording screen parses resize JSON frames.
import threading  # The recording screen exposes bounded wait helpers.
import time  # Tests use monotonic waits.

from src.websocket_streams.catalog.model import FieldKind, FieldSpec, Safety, UtilityDefinition  # Build requests.
from src.websocket_streams.intake.start_request import StartRequest  # Runners accept checked requests.
from src.websocket_streams.live.runners.utility.screen import ScreenRunner  # The screen runner under test.
from src.websocket_streams.live.runners.utility.triggers import UtilityTriggerTable  # Tests shorten the time limit.
from src.websocket_streams.live.sessions.buffer import MessageBuffer  # A stream session needs an event buffer.
from src.websocket_streams.live.sessions.record import SessionState, StreamSession  # The runner writes here.
from src.websocket_streams.live.terminal.byte_history import ByteHistory  # Screen output is raw byte history.
from src.websocket_streams.live.terminal.gateway import TerminalRunner  # Writable terminal runners satisfy this.
from src.websocket_streams.live.terminal.state import TerminalState  # Screen terminal state is read-only.
from src.websocket_streams.live.transport.endpoint import MistStreamEndpoint, TransportProfile  # Test endpoint.
from tests.support.fake_mist_cloud.api import FakeApiSession  # Offline SDK-shaped session.
from tests.support.fake_mist_cloud.server import FakeConnection, FakeMistCloud  # Fake RFC 6455 server.


def _definition(key: str) -> UtilityDefinition:
    """Return a minimal screen catalog definition."""
    return UtilityDefinition(
        key,
        key.split(".", 1)[0],
        key.split(".", 1)[1],
        "Screen command",
        "Show a live screen command.",
        (),
        Safety.READ,
        "screen",
        (FieldSpec("site_id", "Site", FieldKind.UUID), FieldSpec("device_id", "Device", FieldKind.UUID)),
    )  # Only key, output, and targets matter to the runner.


def _request(key: str, parameters: dict[str, object] | None = None) -> StartRequest:
    """Return one checked screen start request."""
    return StartRequest(
        "utility",
        _definition(key),
        {"site_id": ("site-a",), "device_id": ("device-a",), "org_id": ("org-a",)},
        parameters or {},
        "Screen command - device-a",
    )  # The trigger table reads targets and parameters.


def _terminal() -> TerminalState:
    """Return a read-only terminal state."""
    return TerminalState(ByteHistory(), None, time.monotonic() + 60.0, "2026-10-01T09:30:00Z")  # No input queue.


def _session(request: StartRequest) -> StreamSession:
    """Return one screen stream session."""
    return StreamSession(
        "screen-test",
        request,
        MessageBuffer(20, 99999),
        time.monotonic,
        _terminal(),
    )  # Use a real session sink.


def _endpoint(api: FakeApiSession) -> MistStreamEndpoint:
    """Return a loopback endpoint with short read waits."""
    profile = TransportProfile(allow_loopback=True, read_timeout_seconds=0.05)  # Keep tests fast.
    return MistStreamEndpoint(api, profile)  # The runner passes this to ShellClient.


def _runner(
    api: FakeApiSession,
    session: StreamSession,
    triggers: UtilityTriggerTable | None = None,
) -> ScreenRunner:
    """Return a screen runner."""
    return ScreenRunner(api, _endpoint(api), session.request, session, triggers)  # Construct without RunnerFactory.


def _wait_for_state(session: StreamSession, states: set[SessionState], timeout: float = 2.5) -> None:
    """Wait until the session reaches one expected state."""
    deadline = time.monotonic() + timeout  # Bound each asynchronous assertion.
    while time.monotonic() < deadline:  # Poll for a short time.
        if session.state in states:  # The runner reached the target state.
            return  # The assertion can continue.
        time.sleep(0.01)  # Avoid a busy loop.
    assert session.state in states  # Report the observed state on timeout.


def _history(session: StreamSession) -> bytes:
    """Return all screen history bytes."""
    assert session.terminal is not None  # Screen sessions always hold a terminal.
    return session.terminal.history.read(0).data  # Read all retained bytes.


class RecordingScreenDevice:
    """A screen handler that records resize frames."""

    def __init__(self, *, close: bool = True, updates: int = 1) -> None:
        """Store handler behavior."""
        self.close = close  # Tests choose close or silence.
        self.updates = updates  # Tests choose how many updates to send.
        self.resize_frames: list[dict[str, object]] = []  # Keep resize frame bodies.
        self._condition = threading.Condition()  # Wait helpers use this condition.
        self._closed = False  # Close only one time after the initial resize.

    def on_connect(self, connection: FakeConnection) -> None:
        """Send split screen output."""
        for index in range(self.updates):  # Each update splits an escape sequence.
            connection.send_text("\x1b[")  # Split inside the CSI sequence.
            connection.send_text(f"2J\x1b[1;1Hscreen update {index}\r\n")  # Complete the screen draw.

    def receive(self, _connection: FakeConnection, opcode: int, payload: bytes) -> None:
        """Record resize frames from the client."""
        if opcode != 0x1:  # Resize frames use text.
            return  # Ignore any other opcode.
        with self._condition:  # Protect records and wake waiters.
            self.resize_frames.append(json.loads(payload.decode("utf-8")))  # Record exact resize body.
            self._condition.notify_all()  # Wake wait_for_resize.
        if self.close and not self._closed:  # The initial resize proves the client finished opening.
            self._closed = True  # Prevent duplicate close frames after later resizes.
            _connection.send_close(1000)  # End normally after output.

    def wait_for_resize(self, expected_count: int, timeout: float) -> list[dict[str, object]]:
        """Wait until enough resize frames arrive."""
        deadline = time.monotonic() + timeout  # Bound every wait.
        with self._condition:  # Wait with the receive condition.
            while len(self.resize_frames) < expected_count:  # Stop when enough records exist.
                remaining = deadline - time.monotonic()  # Calculate the remaining time.
                if remaining <= 0:  # The timeout expired.
                    break  # Return what arrived for failure evidence.
                self._condition.wait(timeout=remaining)  # Sleep until a resize arrives.
            return list(self.resize_frames)  # Return a stable snapshot.


class OneSecondTriggerTable(UtilityTriggerTable):
    """A trigger table with a one-second total limit."""

    _DEFAULT_TOTAL_SECONDS = 1.0  # Keep the time-limit test under 20 seconds.


def test_screen_top_and_monitor_triggers_send_expected_requests() -> None:
    """Top and Monitor Traffic use the correct REST path and body."""
    with FakeMistCloud() as cloud:  # Start a fake screen server.
        cloud.register("/screen/default", RecordingScreenDevice())  # The default screen URL uses this path.
        top_api = FakeApiSession(cloud)  # Build the top fake API.
        top_session = _session(_request("ex.topCommand"))  # Build the top sink.
        top_runner = _runner(top_api, top_session)  # Build the top runner.
        top_runner.start()  # Start the top command.
        _wait_for_state(top_session, {SessionState.FINISHED})  # The device closes after output.
        cloud.register("/screen/default", RecordingScreenDevice())  # Give the monitor run a fresh handler.
        monitor_api = FakeApiSession(cloud)  # Build the monitor fake API.
        monitor_session = _session(_request("srx.monitorTraffic", {"port_id": "ge-0/0/0"}))  # Build monitor sink.
        monitor_runner = _runner(monitor_api, monitor_session)  # Build monitor runner.
        monitor_runner.start()  # Start monitor traffic.
        _wait_for_state(monitor_session, {SessionState.FINISHED})  # The device closes after output.
    assert top_api.calls[0].uri == "/api/v1/sites/site-a/devices/device-a/run_top"  # Top path matches SDK.
    assert top_api.calls[0].body is None  # Top sends no body.
    assert monitor_api.calls[0].uri == "/api/v1/sites/site-a/devices/device-a/monitor_traffic"  # Monitor path.
    assert monitor_api.calls[0].body == {"duration": 60, "port": "ge-0/0/0"}  # Monitor body matches SDK.


def test_screen_history_preserves_split_control_bytes_and_read_only_state() -> None:
    """Screen output reaches byte history unchanged, and input is read-only."""
    with FakeMistCloud() as cloud:  # Start a fake screen server.
        cloud.register("/screen/default", RecordingScreenDevice(updates=2))  # Send two split updates.
        api = FakeApiSession(cloud)  # Build the fake REST session.
        session = _session(_request("ex.topCommand"))  # Build a read-only session.
        runner = _runner(api, session)  # Build the runner.
        runner.start()  # Start the screen command.
        _wait_for_state(session, {SessionState.FINISHED})  # Wait for the device close.
    assert b"\x1b[2J\x1b[1;1Hscreen update 0\r\n" in _history(session)  # Split bytes rejoined in history.
    assert b"\x1b[2J\x1b[1;1Hscreen update 1\r\n" in _history(session)  # Second update also arrived.
    assert b"\x00" not in _history(session)  # The client removes the Mist screen channel markers.
    assert session.terminal is not None and session.terminal.read_only is True  # Screen terminal is read-only.
    assert session.terminal.input is None  # The gateway refuses input and resize with read_only before runner calls.
    assert isinstance(runner, TerminalRunner) is False  # A screen runner is not a writable terminal runner.


def test_screen_resize_sends_json_frame() -> None:
    """Resize sends the terminal size JSON frame."""
    with FakeMistCloud() as cloud:  # Start a fake screen server.
        device = RecordingScreenDevice(close=False)  # Keep the screen open.
        cloud.register("/screen/default", device)  # Route the screen URL.
        api = FakeApiSession(cloud)  # Build the fake API.
        session = _session(_request("ex.topCommand"))  # Build the screen session.
        runner = _runner(api, session)  # Build the runner.
        runner.start()  # Start the screen command.
        _wait_for_state(session, {SessionState.LIVE})  # Wait until connected.
        runner.resize(120, 35)  # Send a live resize.
        frames = device.wait_for_resize(2, 2.0)  # Initial size and live resize must arrive.
        runner.stop()  # Stop the open screen.
        _wait_for_state(session, {SessionState.STOPPED})  # Wait for clean shutdown.
    assert frames[0] == {"resize": {"width": 80, "height": 24}}  # Open sends default size first.
    assert frames[1] == {"resize": {"width": 120, "height": 35}}  # Resize sends JSON dimensions.


def test_screen_time_limit_stop_and_device_close_outcomes() -> None:
    """Time limit, operator stop, and device close map to documented outcomes."""
    with FakeMistCloud() as cloud:  # Run subcases against one fake server.
        cloud.register("/screen/limit", RecordingScreenDevice(close=False))  # Limit case stays silent.
        limit_api = FakeApiSession(cloud)  # Build limit API.
        limit_api.add_override("/run_top", 200, {"url": f"{cloud.base_ws_url}/screen/limit"})  # Route limit.
        limit_session = _session(_request("ex.topCommand"))  # Build limit session.
        limit_runner = _runner(limit_api, limit_session, OneSecondTriggerTable())  # Use one-second limit.
        limit_runner.start()  # Start limit case.
        _wait_for_state(limit_session, {SessionState.FINISHED}, timeout=2.5)  # Wait for the time limit.
        cloud.register("/screen/stop", RecordingScreenDevice(close=False))  # Stop case stays open.
        stop_api = FakeApiSession(cloud)  # Build stop API.
        stop_api.add_override("/run_top", 200, {"url": f"{cloud.base_ws_url}/screen/stop"})  # Route stop.
        stop_session = _session(_request("ex.topCommand"))  # Build stop session.
        stop_runner = _runner(stop_api, stop_session, OneSecondTriggerTable())  # Build stop runner.
        stop_runner.start()  # Start stop case.
        _wait_for_state(stop_session, {SessionState.LIVE})  # Wait until live.
        stop_runner.stop()  # Stop before the limit.
        _wait_for_state(stop_session, {SessionState.STOPPED})  # Wait for stopped state.
        cloud.register("/screen/close", RecordingScreenDevice(close=True))  # Close case ends normally.
        close_api = FakeApiSession(cloud)  # Build close API.
        close_api.add_override("/run_top", 200, {"url": f"{cloud.base_ws_url}/screen/close"})  # Route close.
        close_session = _session(_request("ex.topCommand"))  # Build close session.
        close_runner = _runner(close_api, close_session)  # Build close runner.
        close_runner.start()  # Start close case.
        _wait_for_state(close_session, {SessionState.FINISHED})  # Wait for device close.
    assert limit_session.reason.startswith("The screen command reached its time limit")  # Limit reason prefix.
    assert stop_session.reason == "The operator stopped the session."  # Stop before limit stays stopped.
    assert close_session.reason == "The device ended the screen command."  # Device close is finished.
