"""Tests for the issue #3671 WebSockets channel runner."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import threading  # Fake sinks use a condition to wait for runner callbacks.
import time  # Reconnect timing tests compare elapsed time.

from src.websocket_streams.catalog.model import (
    ChannelDefinition,
    FieldKind,
    FieldSpec,
)  # Tests build local definitions.
from src.websocket_streams.intake.start_request import StartRequest  # Tests build checked requests by hand.
from src.websocket_streams.live.runners.channel import ChannelStreamRunner  # The tests cover the channel runner.
from src.websocket_streams.live.sessions.record import SessionState  # Fake sinks record final state.
from src.websocket_streams.live.transport.endpoint import MistStreamEndpoint, TransportProfile  # Transport setup.
from tests.support.fake_mist_cloud.api import FakeApiSession  # Fake endpoint authentication.
from tests.support.fake_mist_cloud.devices import StreamDevice  # Fake stream device.
from tests.support.fake_mist_cloud.server import FakeMistCloud  # Loopback WebSocket server.


class FakeSink:
    """A fake session sink."""

    def __init__(self) -> None:
        """Build an empty sink."""
        self.live_notes: list[str] = []  # Keep live notes.
        self.messages: list[tuple[str, object, str | None]] = []  # Keep added messages.
        self.finished: list[tuple[SessionState, str]] = []  # Keep final states.
        self._condition = threading.Condition()  # Tests wait for callbacks with a bound.

    def mark_live(self, note: str = "") -> None:
        """Record a live transition."""
        with self._condition:  # Protect the callback records.
            self.live_notes.append(note)  # Tests verify the callback.
            self._condition.notify_all()  # Wake tests waiting for live state.

    def add_message(self, kind: str, content: object, *, source: str | None = None, summary: str | None = None) -> None:
        """Record one message."""
        _summary_length = len(summary or "")  # Read the optional summary without changing channel assertions.
        with self._condition:  # Protect the callback records.
            self.messages.append((kind, content, source))  # Tests verify shaped content and source.
            self._condition.notify_all()  # Wake tests waiting for messages.

    def finish(self, state: SessionState, reason: str) -> None:
        """Record a final state."""
        with self._condition:  # Protect the callback records.
            self.finished.append((state, reason))  # Tests verify end state mapping.
            self._condition.notify_all()  # Wake tests waiting for final state.

    def wait_for_live(self, count: int, timeout: float) -> list[str]:
        """Wait for a live transition count."""
        with self._condition:  # Wait on the callback condition.
            self._condition.wait_for(lambda: len(self.live_notes) >= count, timeout=timeout)  # Bound the wait.
            return list(self.live_notes)  # Return a snapshot for assertions.

    def wait_for_messages(self, count: int, timeout: float) -> list[tuple[str, object, str | None]]:
        """Wait for a message count."""
        with self._condition:  # Wait on the callback condition.
            self._condition.wait_for(lambda: len(self.messages) >= count, timeout=timeout)  # Bound the wait.
            return list(self.messages)  # Return a snapshot for assertions.

    def wait_for_finished(self, count: int, timeout: float) -> list[tuple[SessionState, str]]:
        """Wait for a finish count."""
        with self._condition:  # Wait on the callback condition.
            self._condition.wait_for(lambda: len(self.finished) >= count, timeout=timeout)  # Bound the wait.
            return list(self.finished)  # Return a snapshot for assertions.


class DropDuringSubscribeDevice:
    """A fake stream device that drops each connection during subscribe."""

    def __init__(self) -> None:
        """Build a drop counter."""
        self.drop_count = 0  # Tests verify that every open attempt reached subscribe.
        self._lock = threading.Lock()  # The fake server can call this handler from several threads.

    def receive(self, connection: object, opcode: int, payload: bytes) -> None:
        """Drop after the subscribe frame arrives.

        Args:
            connection: The fake WebSocket connection.
            opcode: The frame opcode.
            payload: The frame payload.
        """
        _payload_size = len(payload)  # Read the payload without logging channel content.
        if opcode != 0x1:  # Subscribe frames use text frames.
            return  # Ignore non-text frames.
        with self._lock:  # Protect the drop count.
            self.drop_count += 1  # Count the subscribe attempt before dropping.
        connection.drop()  # Drop before any channel_subscribed answer.


class TestChannelStreamRunner:
    """Verify channel runner behavior."""

    def test_source_map_and_message_shape_use_owned_stream_client(self) -> None:
        """Map channel paths to the public source value."""
        with FakeMistCloud() as cloud:  # Start a loopback fake cloud.
            device = StreamDevice()  # Build a stream device.
            cloud.register("/api-ws/v1/stream", device)  # Route the stream path.
            sink = FakeSink()  # Record runner callbacks.
            runner = ChannelStreamRunner(self._endpoint(cloud), self._request(("site-a", "site-b")), sink)  # Runner.
            try:
                runner.start()  # Start the daemon reader thread.
                assert sink.wait_for_live(1, 1.0) == ["The WebSocket connection opened."]  # Subscription done.
                device.publish("/sites/site-b/stats/devices", {"ok": True})  # Send one site-b event.
                messages = sink.wait_for_messages(2, 1.0)  # Live note plus channel message.
                assert messages[-1][0] == "json"  # Channel data stays JSON.
                assert messages[-1][1] == {
                    "event": "data",
                    "channel": "/sites/site-b/stats/devices",
                    "data": {"ok": True},
                }  # Existing page shape stays stable.
                assert messages[-1][2] == "site-b"  # Source map uses the repeatable value.
            finally:
                runner.stop()  # Ensure the reader thread stops.

    def test_reconnects_three_times_after_drops(self) -> None:
        """Reconnect after drops using the profile delays."""
        with FakeMistCloud() as cloud:  # Start a loopback fake cloud.
            device = StreamDevice()  # Build a stream device.
            cloud.register("/api-ws/v1/stream", device)  # Route the stream path.
            sink = FakeSink()  # Record runner callbacks.
            endpoint = self._endpoint(cloud, reconnect_delays=(0.05, 0.05, 0.05))  # Use short waits.
            runner = ChannelStreamRunner(endpoint, self._request(("site-a",)), sink)  # Build the runner.
            start = time.monotonic()  # Measure that reconnect waits occurred.
            try:
                runner.start()  # Start the daemon reader thread.
                cloud.wait_for_requests(1, 1.0)  # Wait for the initial connection.
                device.drop()  # Drop the first connection.
                cloud.wait_for_requests(2, 1.0)  # Wait for retry one.
                device.drop()  # Drop retry one.
                cloud.wait_for_requests(3, 1.0)  # Wait for retry two.
                device.drop()  # Drop retry two.
                requests = cloud.wait_for_requests(4, 1.0)  # Wait for retry three.
                assert len(requests) == 4  # The runner made three new connections.
                assert time.monotonic() - start >= 0.15  # The reconnect delays were used.
            finally:
                runner.stop()  # Ensure the reader thread stops.

    def test_failed_open_finishes_after_retry_budget(self) -> None:
        """Fail after the third reconnect delay when subscribe never answers."""
        with FakeMistCloud() as cloud:  # Start a loopback fake cloud.
            cloud.register("/api-ws/v1/stream", object())  # This handler never confirms subscription.
            sink = FakeSink()  # Record runner callbacks.
            endpoint = self._endpoint(
                cloud, reconnect_delays=(0.01, 0.01, 0.01), subscribe_timeout=0.02
            )  # Use short waits.
            runner = ChannelStreamRunner(endpoint, self._request(("site-a",)), sink)  # Build the runner.
            try:
                runner.start()  # Start the daemon reader thread.
                finished = sink.wait_for_finished(1, 1.0)  # Wait for the retry budget to end.
                assert len(cloud.requests) == 4  # Initial attempt plus three retries.
                assert finished == [(SessionState.FAILED, "The WebSocket connection failed after retry attempts.")]
            finally:
                runner.stop()  # Ensure the reader thread stops.

    def test_drop_during_subscribe_consumes_retry_budget(self) -> None:
        """Fail after retry attempts when every subscribe wait drops."""
        with FakeMistCloud() as cloud:  # Start a loopback fake cloud.
            device = DropDuringSubscribeDevice()  # Build a device that drops during subscribe.
            assert callable(device.receive)  # The fake server calls this handler by reflection.
            cloud.register("/api-ws/v1/stream", device)  # Route the stream path.
            sink = FakeSink()  # Record runner callbacks.
            delays = (0.01, 0.01)  # Keep the retry budget short.
            endpoint = self._endpoint(cloud, reconnect_delays=delays, subscribe_timeout=0.2)  # Use short waits.
            runner = ChannelStreamRunner(endpoint, self._request(("site-a",)), sink)  # Build the runner.
            try:
                runner.start()  # Start the daemon reader thread.
                finished = sink.wait_for_finished(1, 1.0)  # Wait for the retry budget to end.
                expected_attempts = len(delays) + 1  # The budget is initial attempt plus retries.
                assert len(cloud.requests) == expected_attempts  # The runner did not retry forever.
                assert device.drop_count == expected_attempts  # Each open attempt reached subscribe.
                assert finished == [(SessionState.FAILED, "The WebSocket connection failed after retry attempts.")]
            finally:
                runner.stop()  # Ensure the reader thread stops.

    def test_refused_channel_fails_without_path_in_reason(self) -> None:
        """Fail at once when a channel subscription is refused."""
        with FakeMistCloud() as cloud:  # Start a loopback fake cloud.
            device = StreamDevice()  # Build a stream device.
            device.refuse("/sites/site-a/stats/devices", "denied")  # Refuse the requested channel.
            cloud.register("/api-ws/v1/stream", device)  # Route the stream path.
            sink = FakeSink()  # Record runner callbacks.
            runner = ChannelStreamRunner(self._endpoint(cloud), self._request(("site-a",)), sink)  # Runner.
            try:
                runner.start()  # Start the daemon reader thread.
                finished = sink.wait_for_finished(1, 1.0)  # Wait for the subscription failure.
                assert finished == [(SessionState.FAILED, "The stream subscription failed: denied.")]  # Safe reason.
            finally:
                runner.stop()  # Ensure the reader thread stops.

    def test_stop_during_reconnect_wait_stops_at_once(self) -> None:
        """Wake a reconnect wait when the operator stops the runner."""
        with FakeMistCloud() as cloud:  # Start a loopback fake cloud.
            cloud.register("/api-ws/v1/stream", object())  # This handler never confirms subscription.
            sink = FakeSink()  # Record runner callbacks.
            endpoint = self._endpoint(cloud, reconnect_delays=(1.0,), subscribe_timeout=0.02)  # Long retry wait.
            runner = ChannelStreamRunner(endpoint, self._request(("site-a",)), sink)  # Build the runner.
            runner.start()  # Start the daemon reader thread.
            cloud.wait_for_requests(1, 1.0)  # Wait for the first failed attempt.
            start = time.monotonic()  # Measure the stop latency.
            runner.stop()  # Stop should wake the reconnect wait.
            finished = sink.wait_for_finished(1, 1.0)  # Wait for stopped state.
            assert time.monotonic() - start < 0.5  # Stop woke the wait promptly.
            assert finished == [(SessionState.STOPPED, "The operator stopped the session.")]  # Stop state.

    def test_quiet_channel_stays_open_when_pongs_arrive(self) -> None:
        """Keep a quiet channel alive when the fake cloud answers pings."""
        with FakeMistCloud() as cloud:  # Start a loopback fake cloud.
            device = StreamDevice()  # Build a stream device that stays quiet.
            cloud.register("/api-ws/v1/stream", device)  # Route the stream path.
            sink = FakeSink()  # Record runner callbacks.
            endpoint = self._endpoint(cloud, read_timeout=0.05)  # Use a short keepalive interval.
            runner = ChannelStreamRunner(endpoint, self._request(("site-a",)), sink)  # Build the runner.
            try:
                runner.start()  # Start the daemon reader thread.
                sink.wait_for_live(1, 1.0)  # Wait for subscription.
                pings = cloud.wait_for_pings(3, 1.0)  # A healthy quiet channel should keep pinging.
                assert len(pings) >= 3  # Pongs prevent a false drop.
                assert len(sink.finished) == 0  # The session did not fail while pongs arrived.
            finally:
                runner.stop()  # Ensure the reader thread stops.

    def _endpoint(
        self,
        cloud: FakeMistCloud,
        reconnect_delays: tuple[float, ...] = (0.05, 0.05, 0.05),
        read_timeout: float = 20.0,
        subscribe_timeout: float = 1.0,
    ) -> MistStreamEndpoint:
        """Build a loopback stream endpoint."""
        profile = TransportProfile(
            stream_url=f"{cloud.base_ws_url}/api-ws/v1/stream",
            allow_loopback=True,
            read_timeout_seconds=read_timeout,
            subscribe_timeout_seconds=subscribe_timeout,
            reconnect_delays=reconnect_delays,
        )  # Configure short offline timeouts.
        return MistStreamEndpoint(FakeApiSession(), profile)  # Return the endpoint under test.

    def _request(self, sites: tuple[str, ...]) -> StartRequest:
        """Build a repeatable channel request."""
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
        return StartRequest("channel", definition, {"site_id": sites}, {}, "Device statistics - HQ")  # Request.
