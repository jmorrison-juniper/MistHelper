"""Tests for one WebSockets stream session record."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import json  # The read test decodes the stored JSON text.
import sys  # The thread test shortens the thread switch interval.
from concurrent.futures import ThreadPoolExecutor  # The thread test returns the writer error to the main thread.

from src.websocket_streams.catalog.model import ChannelDefinition  # Tests build a local definition.
from src.websocket_streams.intake.start_request import StartRequest  # Tests build checked requests by hand.
from src.websocket_streams.live.sessions.buffer import MessageBuffer  # Tests inject a small buffer.
from src.websocket_streams.live.sessions.record import SessionState, StreamSession  # The tests cover the session sink.


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

    def _session(self, clock: FakeClock, buffer: MessageBuffer | None = None) -> StreamSession:
        """Build one test session.

        Args:
            clock: The fake clock.
            buffer: The message buffer, or None for a small buffer.

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
        return StreamSession("abc123", request, kept, clock)  # Return a session with the chosen buffer.
