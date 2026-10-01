"""Tests for the WebSockets shell runner."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import threading  # The start test waits for the reader thread.
from types import SimpleNamespace  # The tests build a fake SDK family module.

import pytest  # The tests check input refusal.

from src.websocket_streams.catalog.model import (
    ChannelDefinition,
    FieldKind,
    FieldSpec,
    Safety,
    UtilityDefinition,
)  # Tests build local definitions.
from src.websocket_streams.intake.fields import StreamRequestError  # Input refusal uses this error.
from src.websocket_streams.intake.start_request import StartRequest  # Tests build checked requests by hand.
from src.websocket_streams.live.runners import shell as shell_module  # The tests replace the SDK module loader.
from src.websocket_streams.live.runners.shell import ShellRunner  # The tests cover the shell runner.
from src.websocket_streams.live.sessions.record import SessionState  # Fake sinks record final state.


class FakeShell:
    """A fake SDK shell session."""

    def __init__(self) -> None:
        """Build one fake shell."""
        self.connected = True  # The read loop starts while connected.
        self.sent: list[str] = []  # Keep sent input.
        self.outputs: list[bytes | None] = [b"\x1b[31mhello\x1b[0m", None]  # Send one output and then idle.
        self.closed = False  # Record disconnect calls.

    def recv(self, timeout: float) -> bytes | None:
        """Return one fake output item.

        Args:
            timeout: The read timeout.

        Returns:
            Output bytes or None.
        """
        if self.outputs:  # Output is available.
            return self.outputs.pop(0)  # Return the next fake item.
        self.connected = False  # End the loop after outputs are consumed.
        return None  # No more output exists.

    def send_text(self, text: str) -> None:
        """Record sent text."""
        self.sent.append(text)  # Tests verify shaped input.

    def disconnect(self) -> None:
        """Close the fake shell."""
        self.closed = True  # Record the close call.
        self.connected = False  # End the read loop.


class FakeSink:
    """A fake session sink."""

    def __init__(self) -> None:
        """Build an empty sink."""
        self.messages: list[str] = []  # Keep shell output.
        self.live_notes: list[str] = []  # Keep live notes.
        self.ready = 0  # Count input-ready events.
        self.finished: list[tuple[SessionState, str]] = []  # Keep final states.
        self.done = threading.Event()  # The start test waits for the final state.

    def mark_live(self, note: str = "") -> None:
        """Record a live transition."""
        self.live_notes.append(note)  # Tests verify shell open.

    def add_message(self, kind: str, content: object, *, source: str | None = None, summary: str | None = None) -> None:
        """Record one shell output message."""
        self.messages.append(str(content))  # Store plain output.

    def finish(self, state: SessionState, reason: str) -> None:
        """Record the final state."""
        self.finished.append((state, reason))  # Tests verify the end state.
        self.done.set()  # Release a test that waits for the reader thread.

    def mark_input_ready(self) -> None:
        """Record that shell input is ready."""
        self.ready += 1  # The runner calls this after first output.


class TestShellRunner:
    """Verify shell runner behavior."""

    def test_first_output_gate_send_input_and_close(self) -> None:
        """Refuse early input, then send after first output."""
        sink = FakeSink()  # Record runner output.
        runner = ShellRunner(object(), self._request(), sink, sleeper=lambda _delay: None)  # Build a shell runner.
        runner._session = FakeShell()  # Inject a fake SDK shell.
        with pytest.raises(StreamRequestError):  # First output did not arrive.
            runner.send_input("show version\r")  # Try early input.
        runner._read_loop()  # Read one output and close.
        assert sink.messages == ["hello"]  # ANSI control text was removed.
        assert sink.ready == 1  # First output opened input.
        runner.send_input("show version\r")  # Send input after readiness.
        assert runner._session.sent == ["show version\r"]  # The text reached the SDK shell.
        runner.stop()  # Close the fake shell.
        assert runner._session.closed is True  # Stop closed the SDK shell.
        runner._finish_after_loop()  # Map the close to a final state.
        assert sink.finished[-1][0] == SessionState.STOPPED  # Stop maps to stopped.

    def test_start_opens_shell_reads_output_and_reports_remote_close(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Open the SDK shell on the reader thread and map a remote close."""
        shell = FakeShell()  # The fake SDK shell that the factory returns.
        shell.outputs = [b"one", b"two", None]  # Two outputs, then one empty read.
        opened: list[tuple[object, ...]] = []  # Record the factory arguments.

        def open_shell(*args: object, **kwargs: object) -> FakeShell:
            """Record the factory call and return the fake shell."""
            opened.append(args + (kwargs,))  # Keep the positional and the keyword arguments.
            return shell  # The runner reads this fake shell.

        self._patch_factory(monkeypatch, open_shell)  # The runner loads the fake SDK factory.
        sink = FakeSink()  # Record runner output.
        runner = ShellRunner(object(), self._request(), sink, sleeper=lambda _delay: None)  # Build a shell runner.
        runner.start()  # Start the reader thread.
        assert sink.done.wait(5.0) is True  # The reader thread reached a final state.
        assert opened[0][1:] == ("site-a", "dev-a", {"rows": 24, "cols": 80})  # The factory got the checked targets.
        assert sink.live_notes == ["The shell opened."]  # The page learned that the shell opened.
        assert sink.messages == ["one", "two"]  # Each output became one message.
        assert sink.ready == 1  # Only the first output opened input.
        assert sink.finished == [(SessionState.FINISHED, "The shell closed.")]  # A remote close finishes.

    def test_open_failure_reports_a_plain_reason(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Report a failed state when the SDK cannot open the shell."""

        def refuse(*_args: object, **_kwargs: object) -> object:
            """Fail like an SDK call that cannot reach the device."""
            raise RuntimeError("")  # An empty message needs the fallback reason.

        self._patch_factory(monkeypatch, refuse)  # The SDK factory fails.
        sink = FakeSink()  # Record runner output.
        runner = ShellRunner(object(), self._request(), sink, sleeper=lambda _delay: None)  # Build a shell runner.
        runner._run()  # Run the reader on this thread.
        assert sink.finished == [(SessionState.FAILED, "The shell failed.")]  # The page gets a plain reason.

    def test_input_after_close_and_wrong_definition_are_refused(self) -> None:
        """Refuse input after the shell closed and refuse a channel definition."""
        runner = ShellRunner(object(), self._request(), FakeSink(), sleeper=lambda _delay: None)  # Build a runner.
        runner._input_ready.set()  # The first output arrived before the close.
        runner._session = None  # The SDK shell closed.
        with pytest.raises(StreamRequestError, match="not open"):  # No shell can take the input.
            runner.send_input("show version\r")  # Try input after the close.
        channel = ChannelDefinition("site.stats.devices", "site", "Devices", "Device statistics.", "/sites/x")  # Wrong.
        bad_request = StartRequest("shell", channel, {}, {}, "Devices")  # A request that breaks the contract.
        bad_runner = ShellRunner(object(), bad_request, FakeSink(), sleeper=lambda _delay: None)  # Build a runner.
        with pytest.raises(StreamRequestError, match="not valid"):  # The runner needs a utility definition.
            bad_runner._shell_definition()  # Read the definition.

    def _patch_factory(self, monkeypatch: pytest.MonkeyPatch, factory: object) -> None:
        """Replace the SDK module loader with a fake shell factory.

        Args:
            monkeypatch: The pytest patch fixture.
            factory: The fake ``createShellSession`` function.
        """
        module = SimpleNamespace(createShellSession=factory)  # A fake EX device utility module.
        loader = SimpleNamespace(import_module=lambda _name: module)  # A fake importlib for the runner.
        monkeypatch.setattr(shell_module, "importlib", loader)  # The runner loads the fake module.

    def _request(self) -> StartRequest:
        """Build a checked shell request.

        Returns:
            A shell start request.
        """
        target = FieldSpec("device_id", "Device", FieldKind.UUID, picker="devices")  # Build a device target.
        definition = UtilityDefinition(
            "ex.shell", "ex", "createShellSession", "Shell", "Open shell.", (), Safety.SHELL, "terminal", (target,)
        )  # Build a shell utility.
        return StartRequest(
            "shell", definition, {"site_id": ("site-a",), "device_id": ("dev-a",)}, {}, "Shell"
        )  # Return a checked request.
