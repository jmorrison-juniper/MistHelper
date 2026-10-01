"""Test the shell runner against the fake Mist cloud."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import logging  # caplog checks that logs contain no terminal secrets.
import threading  # Raw-output tests delay close until after the client starts reading.
import time  # Tests use bounded waits for the reader thread.

import pytest  # The tests use fixtures and exception assertions.

from src.websocket_streams.catalog.model import FieldKind, FieldSpec, Safety, UtilityDefinition  # Build requests.
from src.websocket_streams.intake.start_request import StartRequest  # Runner input is already checked.
from src.websocket_streams.live.runners.shell import ShellRunner  # The device shell runner under test.
from src.websocket_streams.live.sessions.buffer import MessageBuffer  # A session needs a small event buffer.
from src.websocket_streams.live.sessions.record import SessionState, StreamSession  # The runner writes here.
from src.websocket_streams.live.terminal.byte_history import ByteHistory  # Terminal output is byte history.
from src.websocket_streams.live.terminal.input_queue import TerminalInput  # Shell input queues until output.
from src.websocket_streams.live.terminal.state import TerminalState  # The terminal stores size and history.
from src.websocket_streams.live.transport.endpoint import MistStreamEndpoint, TransportProfile  # Test endpoint.
from tests.support.fake_mist_cloud.api import FakeApiSession  # Offline SDK-shaped session.
from tests.support.fake_mist_cloud.devices import ShellDevice  # Fake shell endpoint.
from tests.support.fake_mist_cloud.server import FakeConnection, FakeMistCloud  # Fake RFC 6455 server.


def _definition() -> UtilityDefinition:
    """Return a minimal shell catalog definition."""
    return UtilityDefinition(
        "ex.createShellSession",
        "ex",
        "createShellSession",
        "Remote shell",
        "Open a remote command shell.",
        (),
        Safety.SHELL,
        "terminal",
        (FieldSpec("site_id", "Site", FieldKind.UUID), FieldSpec("device_id", "Device", FieldKind.UUID)),
    )  # Only the key, safety, output, and targets matter to the runner.


def _request() -> StartRequest:
    """Return one checked shell start request."""
    return StartRequest(
        "shell",
        _definition(),
        {"site_id": ("site-a",), "device_id": ("device-a",)},
        {},
        "Remote shell - switch-a",
    )  # The trigger table reads the site and device targets.


def _terminal() -> TerminalState:
    """Return one writable terminal state."""
    return TerminalState(ByteHistory(), TerminalInput(), time.monotonic() + 60.0, "2026-10-01T09:30:00Z")  # State.


def _session(terminal: TerminalState | None = None) -> StreamSession:
    """Return one shell stream session."""
    return StreamSession(
        "shell-test",
        _request(),
        MessageBuffer(20, 99999),
        time.monotonic,
        terminal if terminal is not None else _terminal(),
    )  # Return a real session sink, as the manager would.


def _endpoint(api: FakeApiSession) -> MistStreamEndpoint:
    """Return a loopback-capable endpoint with short waits."""
    profile = TransportProfile(allow_loopback=True, read_timeout_seconds=0.05)  # Keep each test wait short.
    return MistStreamEndpoint(api, profile)  # The runner passes it to ShellClient.


def _runner(api: FakeApiSession, session: StreamSession) -> ShellRunner:
    """Return a bound shell runner."""
    runner = ShellRunner(api, _endpoint(api), session.request, session)  # Construct without RunnerFactory.
    assert session.terminal is not None and session.terminal.input is not None  # Shell sessions must be writable.
    session.terminal.input.bind(runner.send_input)  # Match the manager input binding.
    return runner  # Tests start and stop this runner directly.


def _wait_for_state(session: StreamSession, states: set[SessionState], timeout: float = 2.0) -> None:
    """Wait until the session reaches one expected state."""
    deadline = time.monotonic() + timeout  # Bound each asynchronous assertion.
    while time.monotonic() < deadline:  # Poll the session for a short time.
        if session.state in states:  # The runner reached the target state.
            return  # The assertion can continue.
        time.sleep(0.01)  # Keep waits short without a busy loop.
    assert session.state in states  # Report the observed state on timeout.


def _history(session: StreamSession) -> bytes:
    """Return all terminal history bytes."""
    assert session.terminal is not None  # Shell sessions always hold a terminal.
    return session.terminal.history.read(0).data  # Read all retained bytes from the start.


class RawOutputDevice:
    """A device that sends exact raw bytes and then closes."""

    def __init__(self, chunks: tuple[bytes, ...]) -> None:
        """Store the output chunks."""
        self._chunks = chunks  # Tests use split UTF-8 and control sequences.

    def on_connect(self, connection: FakeConnection) -> None:
        """Send configured chunks to the client."""
        for chunk in self._chunks:  # Each chunk becomes one text frame.
            connection.send_binary(chunk)  # Binary frames keep split UTF-8 bytes exact.
        timer = threading.Timer(0.05, connection.send_close, args=(1000,))  # Let the client enter its read loop.
        timer.daemon = True  # A test failure must not keep the process alive.
        timer.start()  # End the shell normally after the output frames.


class RaisingSession(StreamSession):
    """A session that fails when terminal bytes arrive."""

    def add_bytes(self, data: bytes) -> None:
        """Raise to exercise the runner's unexpected-exception path."""
        raise RuntimeError("sink boom")  # The runner must convert this into a plain failure.


def test_shell_trigger_posts_expected_path_and_body() -> None:
    """The shell trigger uses the SDK path and an empty body."""
    with FakeMistCloud() as cloud:  # Start a bounded fake cloud.
        cloud.register("/shell/default", ShellDevice())  # Default FakeApiSession shell URL uses this path.
        api = FakeApiSession(cloud)  # The REST trigger returns the fake shell URL.
        session = _session()  # Build a real session sink.
        runner = _runner(api, session)  # Bind runner input before start.
        runner.start()  # Start the background reader.
        _wait_for_state(session, {SessionState.LIVE})  # Wait until the open completed.
        runner.stop()  # Stop the reader thread.
        _wait_for_state(session, {SessionState.STOPPED})  # Wait for clean shutdown.
    assert api.calls[0].method == "POST"  # The shell trigger uses POST.
    assert api.calls[0].uri == "/api/v1/sites/site-a/devices/device-a/shell"  # The path matches the contract.
    assert api.calls[0].body == {}  # Shell trigger sends an empty body.


@pytest.mark.parametrize(("status", "data"), [(403, {"error": "denied"}), (200, {})])
def test_shell_trigger_refusal_or_missing_url_fails_without_websocket(status: int, data: dict[str, object]) -> None:
    """A refused trigger and a missing URL end as failed without a WebSocket open."""
    with FakeMistCloud() as cloud:  # The server lets us assert no connection opened.
        api = FakeApiSession(cloud)  # Build the fake REST session.
        api.add_override("/shell", status, data)  # Force the trigger result.
        session = _session()  # Build a real sink.
        runner = _runner(api, session)  # Bind input for a manager-like shell.
        runner.start()  # Start the reader thread.
        _wait_for_state(session, {SessionState.FAILED})  # The open must fail.
    assert cloud.requests == []  # The runner never opened a WebSocket.
    assert "terminal" in session.reason  # The reason stays plain and operator-facing.


def test_shell_address_policy_refuses_non_mist_non_loopback_url() -> None:
    """An unsafe shell address fails before any WebSocket connection."""
    with FakeMistCloud() as cloud:  # The server should receive no request.
        api = FakeApiSession(cloud)  # Build the fake REST session.
        api.add_override("/shell", 200, {"url": "ws://example.net/shell/secret"})  # Refuse non-loopback ws.
        session = _session()  # Build a real sink.
        runner = _runner(api, session)  # Bind input before start.
        runner.start()  # Start the open path.
        _wait_for_state(session, {SessionState.FAILED})  # The URL policy must fail the open.
    assert cloud.requests == []  # No unsafe host connection was attempted.
    assert session.reason == "The shell address is outside the Mist cloud domain."  # The policy reason is plain.


def test_shell_open_sends_initial_and_later_resize_frames() -> None:
    """The shell sends the stored size first and sends later resizes."""
    with FakeMistCloud() as cloud:  # Start a fake shell server.
        device = ShellDevice()  # The device records resize frames.
        cloud.register("/shell/default", device)  # Route the shell URL.
        api = FakeApiSession(cloud)  # REST returns the shell route.
        terminal = _terminal()  # Build a terminal to set size before start.
        terminal.set_size(132, 40)  # Store the initial browser size.
        session = _session(terminal=terminal)  # Use that terminal in the sink.
        runner = _runner(api, session)  # Bind runner input.
        runner.resize(140, 45)  # Resize before open must not raise.
        runner.start()  # Open the shell.
        first_resize = device.wait_for_resize(1, 2.0)  # Wait for the stored start size.
        runner.resize(100, 30)  # Send a resize after the open.
        all_resize = device.wait_for_resize(2, 2.0)  # Wait for the live resize.
        runner.stop()  # Stop the shell thread.
        _wait_for_state(session, {SessionState.STOPPED})  # Wait for clean shutdown.
    assert first_resize[0] == {"resize": {"width": 132, "height": 40}}  # The first client frame is the start size.
    assert all_resize[1] == {"resize": {"width": 100, "height": 30}}  # Live resize sends a JSON frame.


def test_shell_first_output_marks_live_and_releases_queued_input() -> None:
    """The first output opens input and sends queued keys in order."""
    with FakeMistCloud() as cloud:  # Start a fake shell server.
        device = ShellDevice()  # The device records raw input frames.
        cloud.register("/shell/default", device)  # Route the shell URL.
        api = FakeApiSession(cloud)  # REST returns the shell route.
        session = _session()  # Build a real session.
        runner = _runner(api, session)  # Bind input before queuing.
        assert session.terminal is not None and session.terminal.input is not None  # Narrow terminal type.
        session.terminal.input.submit("show ")  # Queue text before output.
        session.terminal.input.submit("version\r")  # Queue a second part before output.
        runner.start()  # The shell banner releases the queued text.
        received = device.wait_for_input(len("show version\r"), 2.0)  # Wait for both queued parts.
        runner.stop()  # Stop the reader thread.
        _wait_for_state(session, {SessionState.STOPPED})  # Wait for the final state.
    assert session.input_ready is True  # The first output marked input ready.
    assert received == b"show version\r"  # The device saw the exact queued order.
    assert device.received_frames[:2] == [b"\x00show ", b"\x00version\r"]  # Each input kept the NUL prefix.
    assert session.buffer.snapshot()[0].content_json == '"The shell opened."'  # The page sees the open event.


def test_shell_close_drop_stop_and_stop_during_trigger() -> None:
    """Shell close, drop, operator stop, and stop during trigger map to final states."""
    with FakeMistCloud() as cloud:  # Run all subcases against one server.
        close_device = ShellDevice()  # The exit command sends close code 1000.
        drop_device = ShellDevice()  # This device is dropped by the test.
        cloud.register("/shell/close", close_device)  # Route close subcase.
        cloud.register("/shell/drop", drop_device)  # Route drop subcase.
        close_session = _session()  # Build the close sink.
        close_api = FakeApiSession(cloud)  # Build the close API.
        close_api.add_override("/shell", 200, {"url": f"{cloud.base_ws_url}/shell/close"})  # Route close.
        close_runner = _runner(close_api, close_session)  # Bind close runner.
        close_runner.start()  # Open close subcase.
        _wait_for_state(close_session, {SessionState.LIVE})  # Wait until connected.
        assert close_session.terminal is not None and close_session.terminal.input is not None  # Narrow type.
        close_session.terminal.input.submit("exit\r")  # Ask the fake shell to close normally.
        _wait_for_state(close_session, {SessionState.FINISHED})  # Wait for device close.
        drop_session = _session()  # Build the drop sink.
        drop_api = FakeApiSession(cloud)  # Build the drop API.
        drop_api.add_override("/shell", 200, {"url": f"{cloud.base_ws_url}/shell/drop"})  # Route drop.
        drop_runner = _runner(drop_api, drop_session)  # Bind drop runner.
        drop_runner.start()  # Open drop subcase.
        _wait_for_state(drop_session, {SessionState.LIVE})  # Wait until connected.
        drop_device.drop()  # Drop TCP without a close frame.
        _wait_for_state(drop_session, {SessionState.FAILED})  # Wait for dropped outcome.
        stop_session = _session()  # Build the stop sink.
        stop_runner = _runner(FakeApiSession(cloud), stop_session)  # Bind stop runner.
        stop_runner.start()  # Open stop subcase.
        _wait_for_state(stop_session, {SessionState.LIVE})  # Wait until connected.
        stop_runner.stop()  # Operator stop closes locally.
        _wait_for_state(stop_session, {SessionState.STOPPED})  # Wait for stopped outcome.
        slow_api = FakeApiSession(cloud)  # Build the slow trigger API.
        slow_session = _session()  # Build the slow trigger sink.
        slow_runner = _runner(slow_api, slow_session)  # Bind slow runner.
        slow_api.before_post_return = lambda _uri, _body: slow_runner.stop()  # Stop during REST trigger.
        slow_runner.start()  # Start slow subcase.
        _wait_for_state(slow_session, {SessionState.STOPPED})  # The stop must win.
    assert close_session.reason == "The device closed the shell."  # Close code 1000 is finished.
    assert drop_session.reason == "The connection to the device dropped."  # TCP loss is failed.
    assert stop_session.reason == "The operator stopped the session."  # Local stop stays stopped.
    assert slow_session.reason == "The operator stopped the session."  # Stop during trigger opens no socket.


def test_shell_unexpected_sink_exception_fails_plainly() -> None:
    """A sink exception becomes the documented plain failure reason."""
    with FakeMistCloud() as cloud:  # The fake cloud sends one output frame.
        cloud.register("/shell/default", ShellDevice())  # Shell output triggers add_bytes.
        api = FakeApiSession(cloud)  # REST returns the shell URL.
        session = RaisingSession("boom", _request(), MessageBuffer(20, 99999), time.monotonic, _terminal())  # Sink.
        runner = _runner(api, session)  # Bind input to the raising sink.
        runner.start()  # Start the shell.
        _wait_for_state(session, {SessionState.FAILED})  # The runner catches the exception.
    assert session.reason == "The terminal failed. Read the portal log for the cause."  # User text is plain.


def test_shell_logs_do_not_hold_address_input_or_output(caplog: pytest.LogCaptureFixture) -> None:
    """Shell logs omit the URL path, typed text, and output text."""
    caplog.set_level(logging.DEBUG)  # Capture debug logs to check high-frequency records.
    with FakeMistCloud() as cloud:  # Start a fake shell server.
        device = ShellDevice(prompt="SECRET-OUTPUT> ")  # Put output text in the prompt.
        cloud.register("/shell/default", device)  # Route the shell URL.
        api = FakeApiSession(cloud)  # REST returns the shell URL.
        session = _session()  # Build the shell sink.
        runner = _runner(api, session)  # Bind input.
        runner.start()  # Open the shell.
        _wait_for_state(session, {SessionState.LIVE})  # Wait for first output.
        assert session.terminal is not None and session.terminal.input is not None  # Narrow type.
        session.terminal.input.submit("SECRET-TYPED")  # Send typed text that logs must not contain.
        device.wait_for_input(len("SECRET-TYPED"), 2.0)  # Ensure the input was sent.
        runner.stop()  # Stop the shell.
        _wait_for_state(session, {SessionState.STOPPED})  # Wait for shutdown.
    assert cloud.base_ws_url not in caplog.text  # Logs must not hold the shell address.
    assert "/shell/default" not in caplog.text  # Logs must not hold the URL path.
    assert "SECRET-TYPED" not in caplog.text  # Logs must not hold typed text.
    assert "SECRET-OUTPUT" not in caplog.text  # Logs must not hold output text.


def test_shell_history_preserves_raw_control_and_split_utf8_bytes() -> None:
    """Raw shell output reaches byte history byte for byte."""
    chunks = (b"\x1b[31m", b"\xe2", b"\x82\xac", b"\x1b[0m")  # Include control codes and split UTF-8.
    with FakeMistCloud() as cloud:  # Start the fake server.
        cloud.register("/shell/raw", RawOutputDevice(chunks))  # Route raw output.
        api = FakeApiSession(cloud)  # Build the fake REST session.
        api.add_override("/shell", 200, {"url": f"{cloud.base_ws_url}/shell/raw"})  # Return the raw path.
        session = _session()  # Build a real sink.
        runner = _runner(api, session)  # Bind input.
        runner.start()  # Start the shell.
        _wait_for_state(session, {SessionState.FINISHED})  # The raw device closes normally.
    assert _history(session) == b"".join(chunks)  # The history keeps exact bytes.
