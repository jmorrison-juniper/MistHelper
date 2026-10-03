"""Tests for one WebSockets stream session record."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import json  # The read test decodes the stored JSON text.
import sys  # The thread test shortens the thread switch interval.
from concurrent.futures import ThreadPoolExecutor  # The thread test returns the writer error to the main thread.

import pytest  # Terminal close tests capture contract errors.

from src.mist.realtime.websocket_streams.catalog.model import ChannelDefinition  # Tests build a local definition.
from src.mist.realtime.websocket_streams.intake.fields.error import (
    StreamRequestError,
)  # Terminal close tests verify contract errors.
from src.mist.realtime.websocket_streams.intake.start_request.models import (
    StartRequest,
)  # Tests build checked requests by hand.
from src.mist.realtime.websocket_streams.live.sessions.buffer.message_buffer import (
    MessageBuffer,
)  # Tests inject a small buffer.
from src.mist.realtime.websocket_streams.live.sessions.record.session import (
    StreamSession,
)  # The tests cover the session sink.
from src.mist.realtime.websocket_streams.live.sessions.record.state import (
    SessionResources,
    SessionState,
)  # Build resources.
from src.mist.realtime.websocket_streams.live.terminal.byte_history import (
    ByteHistory,
)  # Terminal tests inspect raw byte history.
from src.mist.realtime.websocket_streams.live.terminal.input_queue import (
    TerminalInput,
)  # Terminal tests verify input release.
from src.mist.realtime.websocket_streams.live.terminal.state.terminal_state import (
    TerminalState,
)  # Attach terminal state.


class FakeClock:
    """A clock that tests can move."""

    def __init__(self) -> None:
        """Build a clock at zero seconds."""
        self.value = 0.0  # Tests mutate this value directly.

    def __call__(self) -> float:
        """Return the current fake time."""
        return self.value  # The session uses this as monotonic time.


class TestStreamSession:
    """Verify state transitions and payload data."""

    def test_live_message_and_payload(self) -> None:
        """Mark a session live and add one message."""
        clock = FakeClock()  # Use deterministic time.
        session = self._session(clock)  # Build one connecting session.
        session.mark_live("subscribed")  # Mark the stream as live.
        session.add_message("json", {"ok": True}, source="site-a")  # Add one message.
        payload = session.payload()  # Build the public payload.
        assert payload["state"] == "live"  # The live state is public.
        assert payload["live"] is True  # The session counts against the live limit.
        assert payload["last_seq"] == 2  # The note and data message both increment the sequence.
        assert payload["counters"]["received"] == 2  # The counters match the buffer.

    def test_first_finish_wins(self) -> None:
        """Keep the first final state."""
        session = self._session(FakeClock())  # Build one connecting session.
        session.finish(SessionState.FAILED, "first")  # End the session once.
        session.finish(SessionState.FINISHED, "second")  # Try to change the final state.
        payload = session.payload()  # Build the public payload.
        assert payload["state"] == "failed"  # The first final state remains.
        assert payload["reason"] == "first"  # The first reason remains.

    def test_stopped_finish_keeps_stop_request_reason(self) -> None:
        """Keep the earlier stop reason when the runner later finishes."""
        session = self._session(FakeClock())  # Build one connecting session.
        session.request_stop("The session was idle for 15 minutes.")  # Store the reaper stop reason.
        session.finish(SessionState.STOPPED, "The operator stopped the session.")  # Runner reports a generic stop.
        payload = session.payload()  # Build the public payload.
        assert payload["state"] == "stopped"  # The final state is stopped.
        assert payload["reason"] == "The session was idle for 15 minutes."  # The original stop reason wins.

    def test_stopped_finish_without_stop_request_uses_given_reason(self) -> None:
        """Use the finish reason when no prior stop request exists."""
        session = self._session(FakeClock())  # Build one connecting session.
        session.finish(SessionState.STOPPED, "The operator stopped the session.")  # Finish without a stop request.
        payload = session.payload()  # Build the public payload.
        assert payload["state"] == "stopped"  # The final state is stopped.
        assert payload["reason"] == "The operator stopped the session."  # The finish reason is visible.

    def test_stop_repeat_and_input_ready(self) -> None:
        """Make stop idempotent and record shell input readiness."""
        session = self._session(FakeClock())  # Build one connecting session.
        assert session.request_stop("stop") is True  # The first stop changes state.
        assert session.request_stop("stop again") is False  # The second stop is idempotent.
        session.mark_input_ready()  # Shell output opened input.
        payload = session.payload()  # Build the public payload.
        assert payload["state"] == "stopping"  # The stop state remains live.
        assert payload["input_ready"] is True  # The input flag is public.

    def test_late_live_call_keeps_the_stopping_state(self) -> None:
        """Keep the stopping state when a runner marks the session live after a stop."""
        session = self._session(FakeClock())  # Build one connecting session.
        session.request_stop("stop")  # The operator asks for a stop first.
        session.mark_live("accepted")  # A late runner callback arrives after the stop.
        payload = session.payload()  # Build the public payload.
        assert payload["state"] == "stopping"  # A stop in progress never goes back to live.
        assert payload["last_seq"] == 1  # The note still reaches the message list.

    def test_read_and_download_copy_the_records(self) -> None:
        """Copy the kept records, and copy the download list at the moment of the call."""
        session = self._session(FakeClock())  # Build one connecting session.
        session.mark_live()  # Allow messages.
        session.add_message("json", {"port": "ge-0/0/1", "up": True}, source="site-a")  # Add one message.
        records, first_seq, gap = session.read_records(0, 10)  # Read every kept record.
        download = session.snapshot_records()  # Copy the kept records for a download.
        session.add_message("json", {"port": "ge-0/0/2", "up": False})  # This message arrives after the copy.
        assert json.loads(records[0].content_json) == {"port": "ge-0/0/1", "up": True}  # The record holds the content.
        assert (first_seq, gap) == (1, False)  # The read reports the kept range.
        assert [record.seq for record in download] == [1]  # The download holds the records of the call time.
        assert session.payload()["counters"]["bytes"] == session.buffer.bytes_used  # The card shows the memory total.

    def test_reads_are_safe_while_a_runner_adds_messages(self) -> None:
        """Read and copy the buffer while another thread adds messages, with no deque error."""
        session = self._session(FakeClock(), MessageBuffer(500, 8 * 1024 * 1024))  # Use the default buffer size.
        session.mark_live()  # Allow messages. A call without a note adds no message.

        def write() -> None:
            """Add messages fast, like an SDK callback thread."""
            for index in range(3000):  # Add many messages so that reads overlap the adds.
                session.add_message("json", {"index": index})  # Store one message under the session lock.

        previous = sys.getswitchinterval()  # Restore the interpreter setting after the test.
        sys.setswitchinterval(1e-6)  # Switch threads often, so a missing lock fails fast.
        try:  # Always restore the switch interval.
            with ThreadPoolExecutor(max_workers=1) as pool:  # The pool thread acts as the runner thread.
                writer = pool.submit(write)  # Start the adds.
                while not writer.done():  # Read during the adds.
                    session.read_records(0, 500)  # A read copies the records under the lock.
                    session.snapshot_records()  # A download copies the records under the lock.
                writer.result()  # Raise any writer error in this thread.
        finally:  # Restore the interpreter setting for other tests.
            sys.setswitchinterval(previous)  # Put back the old interval.
        assert session.payload()["counters"]["received"] == 3000  # Every add reached the buffer.

    def test_terminal_payload_and_bytes(self) -> None:
        """Expose terminal state and count terminal bytes."""
        terminal = TerminalState(ByteHistory(), TerminalInput(), 10.0, "2026-10-01T09:30:00Z")  # Build terminal.
        session = self._session(FakeClock(), terminal=terminal)  # Build a terminal session.
        session.mark_live()  # Allow terminal output.
        session.add_bytes(b"abc")  # Add one raw output chunk.
        payload = session.payload()  # Build the public payload.
        read = terminal.history.read(0)  # Read the terminal history.
        assert payload["terminal"] is True  # Terminal sessions mark the terminal panel.
        assert payload["counters"]["received"] == 1  # Raw output chunks count as messages.
        assert payload["counters"]["bytes"] == 3  # Raw output bytes count on the card.
        assert read.data == b"abc"  # The terminal history kept the bytes.

    def test_terminal_input_releases_outside_record_lock(self) -> None:
        """Release queued terminal input when the session becomes input ready."""
        sent: list[str] = []  # Keep exact sent text.
        terminal_input = TerminalInput()  # Build the input queue.
        terminal_input.bind(sent.append)  # Bind a fake sender.
        terminal = TerminalState(ByteHistory(), terminal_input, 10.0, "2026-10-01T09:30:00Z")  # Build terminal.
        session = self._session(FakeClock(), terminal=terminal)  # Build a terminal session.
        queued = terminal_input.submit("show version\r")  # Queue early input.
        session.mark_input_ready()  # Release the terminal input queue.
        assert queued is True  # The input waited for first output.
        assert sent == ["show version\r"]  # The queued input was released exactly once.
        assert session.payload()["input_ready"] is True  # The public flag remains set.

    def test_finish_closes_terminal_and_late_bytes_do_nothing(self) -> None:
        """Close terminal state when the session finishes."""
        terminal = TerminalState(ByteHistory(), TerminalInput(), 10.0, "2026-10-01T09:30:00Z")  # Build terminal.
        session = self._session(FakeClock(), terminal=terminal)  # Build a terminal session.
        session.mark_live()  # Allow terminal output.
        session.finish(SessionState.FINISHED, "done")  # End the session and close the terminal.
        session.add_bytes(b"late")  # Late output must not change the history.
        read = terminal.history.read(0)  # Read after close.
        assert read.data == b""  # Late bytes were ignored.
        assert read.closed is True  # Finish closed the terminal history.
        assert session.payload()["terminal"] is True  # The ended payload still marks terminal state.
        with pytest.raises(StreamRequestError) as error:  # Terminal input is closed with the session.
            terminal.input.submit("late")  # A late submit must fail after finish.
        assert error.value.code == "not_open"  # The input queue reports the contract code.

    def _session(
        self, clock: FakeClock, buffer: MessageBuffer | None = None, terminal: TerminalState | None = None
    ) -> StreamSession:
        """Build one test session.

        Args:
            clock: The fake clock.
            buffer: The message buffer, or None for a small buffer.
            terminal: The terminal state, or None.

        Returns:
            A new stream session.
        """
        definition = ChannelDefinition(
            "site.stats.devices", "site", "Device statistics", "Live data.", "/sites/{site_id}"
        )  # Build a minimal channel.
        request = StartRequest(
            "channel", definition, {"site_id": ("site-a",)}, {}, "Device statistics - HQ"
        )  # Build a checked request.
        kept = buffer if buffer is not None else MessageBuffer(10, 9999)  # Most tests need only a small buffer.
        resources = SessionResources(kept, clock, terminal)  # Group the bounded session collaborators.
        return StreamSession("abc123", request, resources)  # Return a session with the chosen resources.
