"""Tests for the WebSockets channel runner."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import pytest  # The tests check input refusal.

from src.websocket_streams.catalog.model import (
    ChannelDefinition,
    FieldKind,
    FieldSpec,
)  # Tests build local definitions.
from src.websocket_streams.intake.fields import StreamRequestError  # Input refusal uses this error.
from src.websocket_streams.intake.start_request import StartRequest  # Tests build checked requests by hand.
from src.websocket_streams.live.runners.channel import ChannelStreamRunner  # The tests cover the channel runner.
from src.websocket_streams.live.sessions.record import SessionState  # Fake sinks record final state.


class FakeClient:
    """A fake SDK WebSocket client."""

    last: FakeClient | None = None  # Tests inspect the newest client.

    def __init__(self, session: object, **kwargs: object) -> None:
        """Build one fake client.

        Args:
            session: The fake API session.
            kwargs: SDK constructor options.
        """
        self.kwargs = kwargs  # Tests assert the constructor settings.
        self.callbacks: dict[str, object] = {}  # Store callbacks by name.
        self.connected = False  # Record connect calls.
        self.disconnected = False  # Record disconnect calls.
        FakeClient.last = self  # Keep this instance for assertions.

    def on_open(self, callback: object) -> None:
        """Store the open callback."""
        self.callbacks["open"] = callback  # The runner registers this callback.

    def on_message(self, callback: object) -> None:
        """Store the message callback."""
        self.callbacks["message"] = callback  # The runner registers this callback.

    def on_error(self, callback: object) -> None:
        """Store the error callback."""
        self.callbacks["error"] = callback  # The runner registers this callback.

    def on_close(self, callback: object) -> None:
        """Store the close callback."""
        self.callbacks["close"] = callback  # The runner registers this callback.

    def connect(self, run_in_background: bool) -> None:
        """Record a connect call."""
        self.connected = run_in_background  # The runner must request background mode.

    def disconnect(self, wait: bool) -> None:
        """Record a disconnect call."""
        self.disconnected = not wait  # The runner must not wait in the web request.


class FakeSink:
    """A fake session sink."""

    def __init__(self) -> None:
        """Build an empty sink."""
        self.live_notes: list[str] = []  # Keep live notes.
        self.messages: list[tuple[str, object, str | None]] = []  # Keep added messages.
        self.finished: list[tuple[SessionState, str]] = []  # Keep final states.

    def mark_live(self, note: str = "") -> None:
        """Record a live transition."""
        self.live_notes.append(note)  # Tests verify the callback.

    def add_message(self, kind: str, content: object, *, source: str | None = None, summary: str | None = None) -> None:
        """Record one message."""
        self.messages.append((kind, content, source))  # Tests verify shaped content.

    def finish(self, state: SessionState, reason: str) -> None:
        """Record a final state."""
        self.finished.append((state, reason))  # Tests verify end state mapping.

    def mark_input_ready(self) -> None:
        """Ignore shell input readiness."""
        return None  # Channel streams never call this method.


class TestChannelStreamRunner:
    """Verify channel runner behavior."""

    def setup_method(self) -> None:
        """Forget the fake client of an earlier test."""
        FakeClient.last = None  # Each test reads only the client that it built.

    def test_start_message_error_close_and_stop(self) -> None:
        """Drive every SDK callback with a fake client."""
        sink = FakeSink()  # Record runner output.
        runner = ChannelStreamRunner(
            object(), self._request(), sink, client_class=FakeClient
        )  # Build a runner with a fake SDK.
        runner.start()  # Start the fake client.
        client = FakeClient.last  # Read the newest fake client.
        assert client is not None and client.connected is True  # The runner built a client and connected it.
        assert client.kwargs["auto_reconnect"] is True  # The runner enables reconnect.
        assert client.kwargs["max_reconnect_attempts"] == 3  # The runner uses three attempts.
        client.callbacks["open"]()  # Simulate an SDK open callback.
        client.callbacks["message"](
            {"channel": "/sites/site-a/stats/devices", "data": '{"ok": true}'}
        )  # Simulate data.
        assert sink.live_notes == ["The WebSocket connection opened."]  # The sink became live.
        assert sink.messages[0][2] == "site-a"  # The runner mapped path to source.
        client.callbacks["error"](RuntimeError("boom"))  # Simulate an SDK error.
        assert sink.finished[-1][0] == SessionState.FAILED  # Errors fail the session.
        runner.stop()  # Request a stop.
        client.callbacks["close"](1000, "closed")  # Simulate the final close.
        assert client.disconnected is True  # Stop did not wait for the SDK.
        assert sink.finished[-1][0] == SessionState.STOPPED  # Stop maps close to stopped.

    def test_send_input_is_refused(self) -> None:
        """Reject input for channel sessions."""
        runner = ChannelStreamRunner(object(), self._request(), FakeSink(), client_class=FakeClient)  # Build a runner.
        with pytest.raises(StreamRequestError):  # Channel runners are not shells.
            runner.send_input("show version")  # Try shell input.

    def _request(self) -> StartRequest:
        """Build a repeatable channel request.

        Returns:
            A checked start request.
        """
        site = FieldSpec("site_id", "Site", FieldKind.UUID, picker="sites")  # Build a site identifier.
        definition = ChannelDefinition(
            "site.stats.devices",
            "site",
            "Device statistics",
            "Live data.",
            "/sites/{site_id}/stats/devices",
            (site,),
            "site_id",
        )  # Build a repeatable channel.
        return StartRequest(
            "channel", definition, {"site_id": ("site-a",)}, {}, "Device statistics - HQ"
        )  # Return a checked request.
