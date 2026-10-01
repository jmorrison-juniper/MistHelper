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
from src.websocket_streams.live.sessions.manager import (
    RunnerFactory,
    StreamSessionManager,
)  # The tests cover the manager.
from src.websocket_streams.live.sessions.record import SessionState  # Tests finish sessions directly.
from src.websocket_streams.live.sessions.settings import StreamSettings  # The manager needs limits.


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
        session = manager._get(str(payload["session_id"]))  # Read the session for direct sink calls.
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
        assert factory.runners[0].stopped == 1  # The runner receives one stop call.
        manager._get(session_id).finish(SessionState.STOPPED, "done")  # End the session.
        filename, lines = manager.download(session_id)  # Build a download.
        assert filename.startswith("site.stats.devices-")  # The file name includes the key.
        assert list(lines) == []  # No messages were added.
        manager.delete(session_id)  # Ended sessions can be deleted.

    def test_shell_input_rules_and_audit(self, caplog: pytest.LogCaptureFixture) -> None:
        """Validate shell input and audit a shell start."""
        caplog.set_level(logging.WARNING)  # Capture the audit warning.
        manager, factory, _clock = self._manager(max_sessions=1)  # Build one manager.
        payload = manager.start(self._shell_request())  # Start a shell session.
        session = manager._get(str(payload["session_id"]))  # Read the session for direct state setup.
        with pytest.raises(StreamRequestError):  # Input is closed before first output.
            manager.send_input(session.session_id, "show version", None)  # Try early input.
        session.mark_live()  # Mark the shell as live.
        session.mark_input_ready()  # Open input after first output.
        manager.send_input(session.session_id, "show version", None)  # Send a command line.
        manager.send_input(session.session_id, None, "interrupt")  # Send a special key.
        assert factory.runners[0].inputs == ["show version\r", "\x03"]  # The manager shaped the inputs.
        assert "ex.shell" in caplog.text  # The audit line names the key.
        assert "device-a" in caplog.text  # The audit line names the device.
        assert "site-a" in caplog.text  # The audit line names the site.
        assert "show version" not in caplog.text  # The audit line never logs shell text.

    def test_reaper_stops_idle_and_prunes_old_ended(self) -> None:
        """Stop idle sessions, keep 5 ended sessions at most, and remove them after 10 minutes."""
        manager, _factory, clock = self._manager(
            max_sessions=10, idle_seconds=30
        )  # Build a manager with short idle time.
        payload = manager.start(self._channel_request("idle"))  # Start one session.
        clock.value = 31.0  # Move past the idle limit.
        manager.reap_once()  # Run one reaper pass.
        assert manager._get(str(payload["session_id"])).state.value == "stopping"  # The idle session was stopped.
        clock.value = 47.0  # Move past the stuck stopping limit.
        manager.reap_once()  # Run another reaper pass.
        assert manager._get(str(payload["session_id"])).state.value == "stopped"  # Stuck stopping became stopped.
        for index in range(6):  # Add six ended sessions to test retention.
            ended_payload = manager.start(self._channel_request(f"ended-{index}"))  # Start one extra session.
            ended = manager._get(str(ended_payload["session_id"]))  # Read it for a direct finish.
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
            manager._get(str(payload["session_id"])).finish(SessionState.FINISHED, "done")  # End it at once.
        clock.value = 200.0  # Start the live session last, so the list order is clear.
        live = manager.start(self._channel_request("live"))  # A live session never counts as ended.
        manager.reap_once()  # Apply the count limit.
        titles = [session["title"] for session in manager.list_payload()["sessions"]]  # Newest first.
        assert titles == ["live", "ended-6", "ended-5", "ended-4", "ended-3", "ended-2"]  # The two oldest left.
        assert manager._get(str(live["session_id"])).live is True  # The live session stays live.

    def test_not_found_bad_input_stop_all_and_shutdown(self) -> None:
        """Cover manager error paths and shutdown behavior."""
        manager, _factory, _clock = self._manager(max_sessions=2)  # Build one manager.
        with pytest.raises(StreamRequestError):  # Unknown sessions raise not_found.
            manager.read("missing", 0, 1)  # Try to read an unknown session.
        payload = manager.start(self._shell_request())  # Start one shell session.
        session = manager._get(str(payload["session_id"]))  # Read the session for state setup.
        session.mark_live()  # Make the shell live.
        session.mark_input_ready()  # Open shell input.
        with pytest.raises(StreamRequestError):  # Control characters are not allowed in lines.
            manager.send_input(session.session_id, "bad\x01", None)  # Try a bad line.
        with pytest.raises(StreamRequestError):  # Unknown keys are not allowed.
            manager.send_input(session.session_id, None, "bad")  # Try a bad key.
        assert manager.live_count() == 1  # One live session is counted.
        assert manager.stop_all("stop all") == 1  # The live session receives one stop.
        manager.shutdown()  # Shutdown is safe after stop_all.
        manager.shutdown()  # A second shutdown does nothing.

    def test_runner_factory_builds_each_runner_kind(self) -> None:
        """Build each concrete runner kind without starting the SDK."""
        factory = RunnerFactory(object())  # Build a factory with a fake API session.
        channel_runner = factory.build(self._channel_request("channel"), FakeSink())  # Build a channel runner.
        utility_runner = factory.build(self._utility_request(), FakeSink())  # Build a utility runner.
        shell_runner = factory.build(self._shell_request(), FakeSink())  # Build a shell runner.
        assert channel_runner.__class__.__name__ == "ChannelStreamRunner"  # Channel requests use the channel runner.
        assert utility_runner.__class__.__name__ == "UtilityRunner"  # Utility requests use the utility runner.
        assert shell_runner.__class__.__name__ == "ShellRunner"  # Shell requests use the shell runner.

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
