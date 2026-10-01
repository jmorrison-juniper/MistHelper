"""Tests for the WebSockets stream session manager."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import json  # The read test decodes the joined JSON text.
import logging  # caplog checks the audit line.

import pytest  # The tests check contract errors.

from src.websocket_streams.catalog.model import (
    ChannelDefinition,
    FieldKind,
    FieldSpec,
    Safety,
    UtilityDefinition,
)  # Tests build local definitions.
from src.websocket_streams.intake.fields import StreamRequestError  # The manager raises these errors.
from src.websocket_streams.intake.start_request import StartRequest  # Tests build checked requests by hand.
from src.websocket_streams.live.runners.channel import ChannelStreamRunner  # Factory tests assert runner classes.
from src.websocket_streams.live.runners.shell import ShellRunner  # Factory tests assert runner classes.
from src.websocket_streams.live.runners.text import ShellAddressFilter  # The filter test counts redaction filters.
from src.websocket_streams.live.runners.utility.runner import UtilityRunner  # Factory tests assert runner classes.
from src.websocket_streams.live.runners.utility.screen import ScreenRunner  # Factory tests assert runner classes.
from src.websocket_streams.live.sessions.manager import (
    RunnerFactory,
    StreamSessionManager,
)  # The tests cover the manager.
from src.websocket_streams.live.sessions.record import SessionState  # Tests finish sessions directly.
from src.websocket_streams.live.sessions.settings import StreamSettings  # The manager needs limits.
from src.websocket_streams.live.transport.endpoint import TransportProfile  # Factory tests avoid real Mist sockets.
from tests.support.fake_mist_cloud.api import FakeApiSession  # Factory tests need SDK-shaped session data.


class FakeClock:
    """A clock that tests can move."""

    def __init__(self) -> None:
        """Build a clock at zero seconds."""
        self.value = 0.0  # Tests mutate this value directly.

    def __call__(self) -> float:
        """Return the fake time."""
        return self.value  # The manager uses this as monotonic time.


class FakeRunner:
    """A runner that records calls."""

    def __init__(self) -> None:
        """Build a runner with no calls."""
        self.started = 0  # Count start calls.
        self.stopped = 0  # Count stop calls.
        self.inputs: list[str] = []  # Keep sent input text.
        self.sizes: list[tuple[int, int]] = []  # TerminalRunner needs resize for runtime protocol checks.

    def start(self) -> None:
        """Record a start call."""
        self.started += 1  # The manager calls this after storing a session.

    def stop(self) -> None:
        """Record a stop call."""
        self.stopped += 1  # The manager calls this at most once per stop.

    def send_input(self, text: str) -> None:
        """Record shell input.

        Args:
            text: The checked shell input.
        """
        self.inputs.append(text)  # Tests verify shaped input text.

    def resize(self, cols: int, rows: int) -> None:
        """Record terminal size changes.

        Args:
            cols: The accepted terminal column count.
            rows: The accepted terminal row count.
        """
        self.sizes.append((cols, rows))  # The protocol method lets manager bind shell input.


class FakeFactory:
    """A runner factory that returns fake runners."""

    def __init__(self) -> None:
        """Build an empty factory."""
        self.runners: list[FakeRunner] = []  # Keep each runner for assertions.

    def build(self, request: StartRequest, sink: object) -> FakeRunner:
        """Build one fake runner.

        Args:
            request: The checked start request.
            sink: The session sink.

        Returns:
            A fake runner.
        """
        runner = FakeRunner()  # Build one runner for this session.
        self.runners.append(runner)  # Keep it for assertions.
        return runner  # The manager calls start on this runner.


class FakeSink:
    """A fake sink for runner factory tests."""

    terminal = None  # Factory tests build runners without a real terminal sink.

    def mark_live(self, note: str = "") -> None:
        """Ignore live transitions."""
        return None  # Factory tests do not start runners.

    def add_message(self, kind: str, content: object, *, source: str | None = None, summary: str | None = None) -> None:
        """Ignore stream messages."""
        return None  # Factory tests do not start runners.

    def finish(self, state: SessionState, reason: str) -> None:
        """Ignore final states."""
        return None  # Factory tests do not start runners.

    def mark_input_ready(self) -> None:
        """Ignore shell readiness."""
        return None  # Factory tests do not start runners.

    def add_bytes(self, data: bytes) -> None:
        """Ignore terminal output bytes.

        Args:
            data: Terminal output bytes from a runner.
        """
        return None  # Factory tests do not start runners.


class TestStreamSessionManager:
    """Verify manager behavior."""

    def test_start_limit_lists_live_titles(self) -> None:
        """Refuse a session when the live limit is reached."""
        manager, _factory, _clock = self._manager(max_sessions=1)  # Allow one live session.
        manager.start(self._channel_request("first"))  # Fill the limit.
        with pytest.raises(StreamRequestError) as error:  # The next start must fail.
            manager.start(self._channel_request("second"))  # Try one too many.
        assert error.value.code == "limit_reached"  # The contract code is stable.
        assert error.value.extra["live"] == ["first"]  # The live title helps the page.

    def test_read_clamps_limit_and_gap(self) -> None:
        """Clamp read limits and report a gap."""
        manager, _factory, _clock = self._manager(max_sessions=1, buffer_messages=2)  # Keep only two messages.
        payload = manager.start(self._channel_request("first"))  # Start one session.
        session = manager.session(str(payload["session_id"]))  # Read the session for direct sink calls.
        session.mark_live()  # Allow messages.
        for index in range(3):  # Add three messages to force one drop.
            session.add_message("text", str(index))  # Store one message.
        read = manager.read(str(payload["session_id"]), 0, 999)  # Ask for more than the max.
        _filename, lines = manager.download(str(payload["session_id"]))  # Build a download of the kept messages.
        assert read.gap is True  # The page missed a dropped message.
        assert read.first_seq == 2 and read.next_after == 3  # The oldest kept sequence is two, and the newest is three.
        decoded = json.loads(read.to_json_text())  # Decode the answer that the route sends.
        assert [message["content"] for message in decoded["messages"]] == ["1", "2"]  # The kept messages.
        assert [json.loads(line)["seq"] for line in lines] == [2, 3]  # Each download line holds one kept message.

    def test_stop_repeat_delete_and_download(self) -> None:
        """Stop once, reject live delete, and stream download lines."""
        manager, factory, _clock = self._manager(max_sessions=1)  # Build one manager.
        payload = manager.start(self._channel_request("first"))  # Start one session.
        session_id = str(payload["session_id"])  # Store the public identifier.
        with pytest.raises(StreamRequestError):  # Live sessions cannot be deleted.
            manager.delete(session_id)  # Try to delete a live session.
        first = manager.stop(session_id)  # Request a stop.
        second = manager.stop(session_id)  # Repeat the stop.
        assert first["state"] == "stopping"  # A stop request moves to stopping.
        assert second["state"] == "stopping"  # A repeat stop returns the same state.
        assert factory.runners[0].stopped == 2  # Each live Stop request wakes the runner.
        manager.session(session_id).finish(SessionState.STOPPED, "done")  # End the session.
        filename, lines = manager.download(session_id)  # Build a download.
        assert filename.startswith("site.stats.devices-")  # The file name includes the key.
        assert list(lines) == []  # No messages were added.
        manager.delete(session_id)  # Ended sessions can be deleted.

    def test_shell_audit_and_terminal_input_queue(self, caplog: pytest.LogCaptureFixture) -> None:
        """Audit a shell start and bind queued terminal input to the runner."""
        caplog.set_level(logging.WARNING)  # Capture the audit warning.
        manager, factory, _clock = self._manager(max_sessions=1)  # Build one manager.
        payload = manager.start(self._shell_request())  # Start a shell session.
        session = manager.session(str(payload["session_id"]))  # Read the public session handle.
        assert session.terminal is not None  # Shell sessions get a terminal state.
        assert session.terminal.input is not None  # Shell sessions get a writable input queue.
        first = session.terminal.input.submit("show ")  # Queue early input before first output.
        second = session.terminal.input.submit("version\r")  # Queue another part to verify order.
        session.mark_live()  # Mark the shell as live.
        session.mark_input_ready()  # Open input after first output.
        third = session.terminal.input.submit("exit\r")  # Later input sends at once.
        assert (first, second, third) == (True, True, False)  # Only input before readiness is queued.
        assert factory.runners[0].inputs == ["show ", "version\r", "exit\r"]  # The runner receives exact order.
        assert "ex.shell" in caplog.text  # The audit line names the key.
        assert "device-a" in caplog.text  # The audit line names the device.
        assert "site-a" in caplog.text  # The audit line names the site.
        assert "show " not in caplog.text  # The audit line never logs shell text.

    def test_session_returns_handle_and_unknown_session_raises(self) -> None:
        """Return known sessions through the public lookup."""
        manager, _factory, _clock = self._manager(max_sessions=1)  # Build one manager.
        payload = manager.start(self._channel_request("first"))  # Start one session.
        session = manager.session(str(payload["session_id"]))  # Read the public session handle.
        assert session.session_id == payload["session_id"]  # The lookup returns the same record.
        with pytest.raises(StreamRequestError) as error:  # Unknown sessions use the contract error.
            manager.session("missing")  # Look up an absent session.
        assert error.value.code == "not_found"  # The route depends on this code.

    def test_terminal_shape_and_expiry_for_each_session_kind(self) -> None:
        """Build the expected terminal state for shell, screen, channel, and utility sessions."""
        manager, _factory, clock = self._manager(max_sessions=4)  # Build one manager with room for four sessions.
        shell = manager.session(str(manager.start(self._shell_request())["session_id"]))  # Start shell session.
        screen = manager.session(str(manager.start(self._screen_request())["session_id"]))  # Start screen session.
        channel = manager.session(str(manager.start(self._channel_request("channel"))["session_id"]))  # Channel.
        utility = manager.session(str(manager.start(self._utility_request())["session_id"]))  # Start utility.
        assert shell.terminal is not None and shell.terminal.input is not None  # Shell accepts input.
        assert screen.terminal is not None and screen.terminal.input is None  # Screen is read-only.
        assert channel.terminal is None  # Channel sessions use the message list.
        assert utility.terminal is None  # Non-screen utility sessions use the message list.
        assert shell.terminal.expires_mono == clock.value + 1800.0  # The monotonic expiry uses settings.
        assert shell.terminal.expires_at.endswith("Z")  # The public expiry is UTC text.

    def test_reaper_stops_idle_and_prunes_old_ended(self) -> None:
        """Stop idle sessions, keep 5 ended sessions at most, and remove them after 10 minutes."""
        manager, _factory, clock = self._manager(
            max_sessions=10, idle_seconds=30
        )  # Build a manager with short idle time.
        payload = manager.start(self._channel_request("idle"))  # Start one session.
        clock.value = 31.0  # Move past the idle limit.
        manager.reap_once()  # Run one reaper pass.
        assert manager.session(str(payload["session_id"])).state.value == "stopping"  # The idle session stopped.
        clock.value = 47.0  # Move past the stuck stopping limit.
        manager.reap_once()  # Run another reaper pass.
        assert manager.session(str(payload["session_id"])).state.value == "stopped"  # Stuck stopping became stopped.
        for index in range(6):  # Add six ended sessions to test retention.
            ended_payload = manager.start(self._channel_request(f"ended-{index}"))  # Start one extra session.
            ended = manager.session(str(ended_payload["session_id"]))  # Read it for a direct finish.
            ended.finish(SessionState.FINISHED, "done")  # Mark the session ended.
        manager.reap_once()  # Seven new ended sessions exist, so the count limit applies.
        assert len(manager.list_payload()["sessions"]) == 5  # The manager keeps five ended sessions at most.
        clock.value = 47.0 + 600.0  # Move to the exact edge of the age limit.
        manager.reap_once()  # Run pruning at the edge.
        assert len(manager.list_payload()["sessions"]) == 5  # A session that is exactly 10 minutes old stays.
        clock.value = 700.0  # Move past the ended retention age.
        manager.reap_once()  # Run pruning.
        assert manager.list_payload()["sessions"] == []  # Each ended session older than 10 minutes left.

    def test_prune_keeps_the_newest_ended_sessions(self) -> None:
        """Remove the oldest ended sessions first when more than five ended sessions exist."""
        manager, _factory, clock = self._manager(max_sessions=10)  # Allow enough live sessions for the setup.
        for index in range(7):  # End seven sessions at different times.
            clock.value = 100.0 + index  # Each session ends one second after the previous session.
            payload = manager.start(self._channel_request(f"ended-{index}"))  # Start one session.
            manager.session(str(payload["session_id"])).finish(SessionState.FINISHED, "done")  # End it at once.
        clock.value = 200.0  # Start the live session last, so the list order is clear.
        live = manager.start(self._channel_request("live"))  # A live session never counts as ended.
        manager.reap_once()  # Apply the count limit.
        titles = [session["title"] for session in manager.list_payload()["sessions"]]  # Newest first.
        assert titles == ["live", "ended-6", "ended-5", "ended-4", "ended-3", "ended-2"]  # The two oldest left.
        assert manager.session(str(live["session_id"])).live is True  # The live session stays live.

    def test_not_found_bad_input_stop_all_and_shutdown(self) -> None:
        """Cover manager error paths and shutdown behavior."""
        manager, _factory, _clock = self._manager(max_sessions=2)  # Build one manager.
        with pytest.raises(StreamRequestError):  # Unknown sessions raise not_found.
            manager.read("missing", 0, 1)  # Try to read an unknown session.
        manager.start(self._shell_request())  # Start one shell session.
        assert manager.live_count() == 1  # One live session is counted.
        assert manager.stop_all("stop all") == 1  # The live session receives one stop.
        manager.shutdown()  # Shutdown is safe after stop_all.
        manager.shutdown()  # A second shutdown does nothing.

    def test_runner_factory_builds_each_runner_kind(self) -> None:
        """Build each concrete runner kind and install shell filters once."""
        factory = self._runner_factory_for_class_tests()  # Build a factory with a fake API session.
        mist_logger = logging.getLogger("mistapi")  # The factory installs the redaction filter here.
        original_filters = list(mist_logger.filters)  # Restore shared logger state after the test.
        original_flag = RunnerFactory._filter_installed  # Restore class state after the test.
        mist_logger.filters = [
            item for item in mist_logger.filters if not isinstance(item, ShellAddressFilter)
        ]  # Reset.
        RunnerFactory._filter_installed = False  # Force the test to measure one installation.
        try:  # Always restore logger state for later tests.
            channel_runner = factory.build(self._channel_request("channel"), FakeSink())  # Build channel runner.
            utility_runner = factory.build(self._utility_request(), FakeSink())  # Build command runner.
            shell_runner = factory.build(self._shell_request(), FakeSink())  # Build shell runner.
            screen_runner = factory.build(self._screen_request(), FakeSink())  # Build screen runner.
            filters = [item for item in mist_logger.filters if isinstance(item, ShellAddressFilter)]  # Count filters.
        finally:  # Put back the global logger state even when assertions fail.
            mist_logger.filters = original_filters  # Restore the previous logger filter list.
            RunnerFactory._filter_installed = original_flag  # Restore the previous class flag.
        assert isinstance(channel_runner, ChannelStreamRunner)  # Channel requests use the channel runner.
        assert isinstance(utility_runner, UtilityRunner)  # Line utilities use the utility runner.
        assert isinstance(shell_runner, ShellRunner)  # Shell requests use the shell runner.
        assert isinstance(screen_runner, ScreenRunner)  # Screen utilities use the screen runner.
        assert len(filters) == 1  # Shell and screen share one redaction filter.

    def _runner_factory_for_class_tests(self) -> RunnerFactory:
        """Build a real runner factory for class-selection tests.

        Returns:
            A runner factory with loopback transport settings.
        """
        profile = TransportProfile(
            stream_url="ws://127.0.0.1:1/api-ws/v1/stream", allow_loopback=True
        )  # Avoid deriving a production address in the test.
        return RunnerFactory(FakeApiSession(), profile)  # Return a factory with SDK-shaped attributes.

    def _manager(
        self, max_sessions: int, buffer_messages: int = 500, idle_seconds: int = 120
    ) -> tuple[StreamSessionManager, FakeFactory, FakeClock]:
        """Build a manager with fakes.

        Args:
            max_sessions: The live session limit.
            buffer_messages: The message buffer limit.
            idle_seconds: The idle limit.

        Returns:
            The manager, factory, and clock.
        """
        clock = FakeClock()  # Use deterministic time.
        factory = FakeFactory()  # Use fake runners.
        settings = StreamSettings(
            max_sessions=max_sessions, buffer_messages=buffer_messages, idle_seconds=idle_seconds
        )  # Use small limits.
        return StreamSessionManager(settings, factory, clock), factory, clock  # Return the assembled manager.

    def _channel_request(self, title: str) -> StartRequest:
        """Build a checked channel request.

        Args:
            title: The session title.

        Returns:
            A channel start request.
        """
        definition = ChannelDefinition(
            "site.stats.devices", "site", "Device statistics", "Live data.", "/sites/{site_id}"
        )  # Build a channel.
        return StartRequest("channel", definition, {"site_id": ("site-a",)}, {}, title)  # Return a checked request.

    def _shell_request(self) -> StartRequest:
        """Build a checked shell request.

        Returns:
            A shell start request.
        """
        target = FieldSpec("device_id", "Device", FieldKind.UUID, picker="devices")  # Build the device target field.
        definition = UtilityDefinition(
            "ex.shell", "ex", "createShellSession", "Shell", "Open a shell.", (), Safety.SHELL, "terminal", (target,)
        )  # Build a shell utility.
        return StartRequest(
            "shell", definition, {"site_id": ("site-a",), "device_id": ("dev-a",)}, {}, "Shell", device_name="device-a"
        )  # Return a checked request.

    def _utility_request(self) -> StartRequest:
        """Build a checked utility request.

        Returns:
            A utility start request.
        """
        target = FieldSpec("device_id", "Device", FieldKind.UUID, picker="devices")  # Build the device target field.
        definition = UtilityDefinition(
            "ex.ping", "ex", "ping", "Ping", "Send ping.", (), Safety.READ, "lines", (target,)
        )  # Build a read utility.
        return StartRequest(
            "utility", definition, {"site_id": ("site-a",), "device_id": ("dev-a",)}, {}, "Ping"
        )  # Return a checked request.

    def _screen_request(self) -> StartRequest:
        """Build a checked screen utility request.

        Returns:
            A screen start request.
        """
        target = FieldSpec("device_id", "Device", FieldKind.UUID, picker="devices")  # Build the device target field.
        definition = UtilityDefinition(
            "ex.topCommand", "ex", "topCommand", "Top", "Run top.", (), Safety.READ, "screen", (target,)
        )  # Build a screen utility.
        return StartRequest(
            "utility", definition, {"site_id": ("site-a",), "device_id": ("dev-a",)}, {}, "Top"
        )  # Return a checked request.
