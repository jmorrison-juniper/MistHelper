"""Tests for one WebSockets stream session record."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

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

    def _session(self, clock: FakeClock) -> StreamSession:
        """Build one test session.

        Args:
            clock: The fake clock.

        Returns:
            A new stream session.
        """
        definition = ChannelDefinition(
            "site.stats.devices", "site", "Device statistics", "Live data.", "/sites/{site_id}"
        )  # Build a minimal channel.
        request = StartRequest(
            "channel", definition, {"site_id": ("site-a",)}, {}, "Device statistics - HQ"
        )  # Build a checked request.
        return StreamSession("abc123", request, MessageBuffer(10, 9999), clock)  # Return a session with a small buffer.
