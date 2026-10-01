"""Tests for the issue #3671 Mist stream client."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import threading  # Thread tests verify close from another thread.
import time  # Tests measure bounded close behavior.
from collections.abc import Callable  # The recorder helper returns a callback.

import pytest  # Tests assert expected transport errors.

from src.websocket_streams.live.transport.endpoint import MistStreamEndpoint, TransportProfile  # Need endpoints.
from src.websocket_streams.live.transport.frames import ConnectionClosed, SubscribeError  # Test structured errors.
from src.websocket_streams.live.transport.stream_client import StreamClient  # Test the stream transport client.
from tests.support.fake_mist_cloud.api import FakeApiSession  # Fake sessions provide endpoint fields.
from tests.support.fake_mist_cloud.devices import StreamDevice  # Stream tests need a fake stream endpoint.
from tests.support.fake_mist_cloud.server import FakeMistCloud  # Fake cloud provides WebSocket I/O.


class TestStreamClient:
    """Verify stream client behavior against the fake cloud."""

    def test_open_waits_for_each_channel_and_returns_data_event(self) -> None:
        """Subscribe before returning from open."""
        with FakeMistCloud() as cloud:  # Start a loopback fake cloud.
            device = StreamDevice()  # Build a stream device.
            cloud.register("/api-ws/v1/stream", device)  # Route the stream path.
            client = self._client(cloud, ["/one", "/two"])  # Build client with two channels.
            try:  # Always close the client after the data-event path.
                client.open()  # Open and wait for both subscription answers.
                device.publish("/two", {"value": "snowman \u2603"})  # Publish Unicode data on one channel.
                event = client.next_event(1.0)  # Read the next data event.
                assert event == {
                    "event": "data",
                    "channel": "/two",
                    "data": '{"value": "snowman \\u2603"}',
                }  # The full event must be returned.
            finally:
                client.close()  # Ensure the socket and server thread stop.

    def test_open_raises_on_subscribe_failed(self) -> None:
        """Raise SubscribeError when the cloud refuses a channel."""
        with FakeMistCloud() as cloud:  # Start a loopback fake cloud.
            device = StreamDevice()  # Build a stream device.
            device.refuse("/bad", "denied")  # Force a refused channel.
            cloud.register("/api-ws/v1/stream", device)  # Route the stream path.
            client = self._client(cloud, ["/bad"])  # Build client with refused channel.
            try:  # Always close the client after the refusal path.
                with pytest.raises(SubscribeError) as caught:  # open() must fail.
                    client.open()  # Wait for the refused subscription.
                assert caught.value.channel == "/bad"  # The error names the channel.
                assert caught.value.detail == "denied"  # The error keeps the refusal detail.
            finally:
                client.close()  # Ensure the socket and server thread stop.

    def test_open_raises_on_subscribe_timeout(self) -> None:
        """Raise SubscribeError when no subscribe answer arrives."""
        with FakeMistCloud() as cloud:  # Start a loopback fake cloud.
            cloud.register("/api-ws/v1/stream", object())  # This handler sends no subscription answer.
            client = self._client(cloud, ["/quiet"], subscribe_timeout=0.2)  # Use a short timeout.
            try:  # Always close the client after the timeout path.
                with pytest.raises(SubscribeError) as caught:  # open() must fail.
                    client.open()  # Wait for the missing subscription answer.
                assert caught.value.channel == "/quiet"  # The timeout names the missing channel.
                assert caught.value.detail == "timeout"  # The detail marks the timeout.
            finally:
                client.close()  # Ensure the socket and server thread stop.

    def test_quiet_connection_stays_open_when_pongs_arrive(self) -> None:
        """Keep a quiet connection open when pongs arrive."""
        with FakeMistCloud() as cloud:  # Start a loopback fake cloud.
            device = StreamDevice()  # Build a stream device that stays quiet.
            cloud.register("/api-ws/v1/stream", device)  # Route the stream path.
            client = self._client(cloud, ["/quiet"], read_timeout=0.05)  # Use short keepalive intervals.
            try:  # Always close the client after the keepalive success path.
                client.open()  # Subscribe successfully first.
                result = client.next_event(0.25)  # Wait for more than four keepalive intervals.
                pings = cloud.wait_for_pings(3, 1.0)  # The fake cloud records received pings.
                assert result is None  # No application data arrived.
                assert len(pings) >= 3  # Pongs kept the quiet connection alive.
            finally:
                client.close()  # Ensure the socket and server thread stop.

    def test_quiet_connection_closes_when_pongs_do_not_arrive(self) -> None:
        """Close a quiet connection after two silent intervals without pongs."""
        with FakeMistCloud() as cloud:  # Start a loopback fake cloud.
            cloud.answer_pings = False  # Simulate a dead peer that does not answer pings.
            device = StreamDevice()  # Build a stream device that stays quiet.
            cloud.register("/api-ws/v1/stream", device)  # Route the stream path.
            client = self._client(cloud, ["/quiet"], read_timeout=0.05)  # Use short keepalive intervals.
            try:  # Always close the client after the keepalive failure path.
                client.open()  # Subscribe successfully first.
                with pytest.raises(ConnectionClosed) as caught:  # Silence should end as a drop.
                    client.next_event(0.5)  # Wait through two quiet intervals.
                assert caught.value.dropped is True  # The client marks this as a dropped connection.
                assert caught.value.code is None  # A silent peer has no close code.
            finally:
                client.close()  # Ensure the socket and server thread stop.

    def test_close_from_another_thread_ends_blocked_read_quickly(self) -> None:
        """Close from another thread while next_event waits."""
        with FakeMistCloud() as cloud:  # Start a loopback fake cloud.
            device = StreamDevice()  # Build a stream device that stays quiet.
            cloud.register("/api-ws/v1/stream", device)  # Route the stream path.
            client = self._client(cloud, ["/quiet"], read_timeout=5.0)  # Keep keepalive out of this test.
            errors: list[ConnectionClosed] = []  # The reader records the close error.
            client.open()  # Subscribe before starting the reader thread.
            thread = threading.Thread(target=self._read_until_close, args=(client, errors), daemon=True)  # Reader.
            started = time.monotonic()  # Measure the close duration.
            thread.start()  # Start the blocked read.
            time.sleep(0.1)  # Let recv block.
            client.close()  # Close from this thread.
            thread.join(timeout=1.0)  # The reader must stop within one second.
            assert thread.is_alive() is False  # The blocked read ended quickly.
            assert len(errors) == 1  # The reader observed one close.
            assert errors[0].dropped is False  # A local close is not a drop.
            assert time.monotonic() - started < 1.0  # The close met the contract.

    def test_run_calls_callback_and_returns_after_local_close(self) -> None:
        """Run the callback loop until the caller closes the client."""
        with FakeMistCloud() as cloud:  # Start a loopback fake cloud.
            device = StreamDevice()  # Build a stream device.
            cloud.register("/api-ws/v1/stream", device)  # Route the stream path.
            client = self._client(cloud, ["/events"], read_timeout=5.0)  # Keep keepalive out of this test.
            events: list[dict[str, object]] = []  # The callback records events.
            delivered = threading.Event()  # The test waits for the callback without polling.
            client.open()  # Subscribe before the run loop starts.
            thread = threading.Thread(
                target=client.run, args=(self._recorder(events, delivered),), daemon=True
            )  # Build the run loop thread.
            thread.start()  # Start the read loop.
            device.publish("/events", {"value": 1})  # Send one data event.
            assert delivered.wait(timeout=1.0) is True  # The callback received the event.
            client.close()  # A local close should make run() return.
            thread.join(timeout=1.0)  # The run loop must stop quickly.
            assert thread.is_alive() is False  # run() returned after local close.
            assert events == [{"event": "data", "channel": "/events", "data": '{"value": 1}'}]  # Full event.

    def test_connection_error_from_factory_surfaces(self) -> None:
        """Raise a connection error when the socket cannot open."""
        client = self._client_for_url("ws://127.0.0.1:1/api-ws/v1/stream", ["/one"])  # Port 1 should not accept.
        with pytest.raises(Exception) as caught:  # websocket-client raises its own connection error type.
            client.open()  # Attempt a connection to an unused port.
        assert caught.value.__class__.__name__ in {"ConnectionRefusedError", "WebSocketProxyException"}  # Exact class.

    def _client(
        self,
        cloud: FakeMistCloud,
        channels: list[str],
        read_timeout: float = 20.0,
        subscribe_timeout: float = 1.0,
    ) -> StreamClient:
        """Build a client pointed at the fake cloud."""
        url = f"{cloud.base_ws_url}/api-ws/v1/stream"  # Use the fake stream path.
        return self._client_for_url(url, channels, read_timeout, subscribe_timeout)  # Reuse URL builder.

    def _client_for_url(
        self,
        url: str,
        channels: list[str],
        read_timeout: float = 20.0,
        subscribe_timeout: float = 1.0,
    ) -> StreamClient:
        """Build a stream client for a URL."""
        profile = TransportProfile(
            stream_url=url,
            allow_loopback=True,
            read_timeout_seconds=read_timeout,
            subscribe_timeout_seconds=subscribe_timeout,
        )  # Configure loopback and short test timeouts.
        endpoint = MistStreamEndpoint(FakeApiSession(), profile)  # Build endpoint with fake auth.
        return StreamClient(endpoint, channels)  # Return the client under test.

    def _read_until_close(self, client: StreamClient, errors: list[ConnectionClosed]) -> None:
        """Read until a local close occurs."""
        try:  # Record any close error from the background read.
            client.next_event(5.0)  # This call should block until close().
        except ConnectionClosed as error:
            errors.append(error)  # Record the structured close error.

    def _recorder(
        self, events: list[dict[str, object]], delivered: threading.Event
    ) -> Callable[[dict[str, object]], None]:
        """Build a callback that records events."""

        def record(event: dict[str, object]) -> None:
            events.append(event)  # Keep the exact event for assertion.
            delivered.set()  # Wake the test after the callback runs.

        return record  # StreamClient.run calls this callback.
