"""Tests for the WebSockets shell runner."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import pytest  # The tests check input refusal.

from src.websocket_streams.catalog.model import (
    FieldKind,
    FieldSpec,
    Safety,
    UtilityDefinition,
)  # Tests build local definitions.
from src.websocket_streams.intake.fields import StreamRequestError  # Input refusal uses this error.
from src.websocket_streams.intake.start_request import StartRequest  # Tests build checked requests by hand.
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

    def mark_live(self, note: str = "") -> None:
        """Record a live transition."""
        self.live_notes.append(note)  # Tests verify shell open.

    def add_message(self, kind: str, content: object, *, source: str | None = None, summary: str | None = None) -> None:
        """Record one shell output message."""
        self.messages.append(str(content))  # Store plain output.

    def finish(self, state: SessionState, reason: str) -> None:
        """Record the final state."""
        self.finished.append((state, reason))  # Tests verify the end state.

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
