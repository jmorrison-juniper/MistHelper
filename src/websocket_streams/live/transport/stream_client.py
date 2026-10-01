"""Open one Mist stream WebSocket connection.

Why:
    Issue #3671 needs subscription-before-trigger behavior. This client opens
    the stream, waits for each channel, and then yields data events.
"""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import json  # Subscribe requests use JSON text frames.
import logging  # The client logs safe connection state.
import threading  # Close can come from another thread.
import time  # The default clock is monotonic.
from collections.abc import Callable, Sequence  # Constructor types stay explicit.
from typing import Any  # websocket-client is not fully typed.

import websocket  # The feature uses websocket-client per the contract.
from src.websocket_streams.live.transport.endpoint import MistStreamEndpoint  # Endpoint builds safe connection values.
from src.websocket_streams.live.transport.frames import (  # Share frame parsing across stream clients.
    ConnectionClosed,
    FrameDecoder,
    FrameReader,
    SubscribeError,
)

logger = logging.getLogger(__name__)  # Keep stream client logs under this module.


class StreamClient:
    """Read data events from one Mist stream connection."""

    def __init__(
        self,
        endpoint: MistStreamEndpoint,
        channels: Sequence[str],
        factory: Callable[..., Any] = websocket.create_connection,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        """Build the stream client.

        Args:
            endpoint: The connection parameter source.
            channels: Channel paths to subscribe to.
            factory: The websocket factory, or a fake in tests.
            clock: The monotonic clock.
        """
        self._endpoint = endpoint  # The endpoint owns auth and TLS settings.
        self._channels = tuple(channels)  # The subscription set must not change during a connection.
        self._factory = factory  # Tests inject a controlled socket factory.
        self._clock = clock  # Tests can use a fake clock.
        self._socket: Any | None = None  # The socket exists after open.
        self._reader: FrameReader | None = None  # The frame reader exists after open.
        self._closed = threading.Event()  # close() wakes read loops quickly.
        self._lock = threading.Lock()  # Protect the socket reference and close state.

    def open(self) -> None:
        """Open the WebSocket connection and subscribe to every channel.

        Raises:
            SubscribeError: A channel refuses or fails to answer in time.
        """
        url = self._endpoint.stream_url()  # The endpoint builds the safe address.
        host = self._endpoint.host_label(url)  # Logs can hold only the host.
        logger.info("Opening Mist stream WebSocket to host %s", host)  # Log before the network connection.
        socket = self._factory(
            url,
            header=self._endpoint.headers(),
            cookie=self._endpoint.cookie(),
            sslopt=self._endpoint.sslopt(),
            enable_multithread=True,
            timeout=self._endpoint.profile.subscribe_timeout_seconds,  # Bound a stalled TCP or TLS handshake.
        )  # Open with thread-safe websocket-client mode.
        socket.settimeout(self._endpoint.profile.subscribe_timeout_seconds)  # Keep writes from using read timeouts.
        with self._lock:  # Publish the socket under the lock.
            self._socket = socket  # close() can now close the socket.
            self._reader = FrameReader(
                socket, self._closed, self._clock, self._endpoint.profile.read_timeout_seconds
            )  # Shared reader handles control frames.
        if self._closed.is_set():  # A stop can arrive while the factory connects.
            FrameReader.close_socket(socket)  # Do not leave a stopped connection subscribed.
            raise ConnectionClosed(code=None, dropped=False)  # The caller maps this to stopped.
        logger.debug("Opened Mist stream WebSocket to host %s", host)  # Do not log path or headers.
        self._subscribe_all(socket)  # Wait for every channel before returning.

    def next_event(self, timeout: float) -> dict[str, object] | None:
        """Return the next data event.

        Args:
            timeout: Maximum wait in seconds for a data event.

        Returns:
            A decoded data event, or None after the requested wait.

        Raises:
            ConnectionClosed: The connection ended or became silent.
        """
        deadline = self._clock() + timeout  # The caller controls the outer wait.
        while not self._closed.is_set():  # Local close ends the read loop quickly.
            wait_left = deadline - self._clock()  # Recompute so fake clocks work.
            if wait_left <= 0:  # The caller asked for a bounded wait.
                return None  # No data arrived in that interval.
            frame = self._recv_once(min(wait_left, self._read_slice()))  # Keep keepalive checks frequent.
            if frame is None:  # A socket timeout is not a closed connection.
                continue  # Keep waiting until the caller timeout expires.
            event = FrameDecoder.event(frame)  # Decode with SDK-compatible rules.
            if event.get("event") == "data":  # Runners need data events only here.
                return event  # The full event includes channel and data.
        raise ConnectionClosed(dropped=False)  # A local close is not a network drop.

    def run(self, on_event: Callable[[dict[str, object]], None]) -> None:
        """Call a callback for each data event until the connection ends.

        Args:
            on_event: Callback that receives each data event.

        Raises:
            ConnectionClosed: The connection dropped.
        """
        logger.info("Running Mist stream read loop for %s channel(s)", len(self._channels))  # Log before the loop.
        while not self._closed.is_set():  # The local close path returns cleanly.
            try:  # Keep local close separate from a dropped connection.
                event = self.next_event(
                    self._endpoint.profile.read_timeout_seconds
                )  # Keepalive uses the profile timeout.
            except ConnectionClosed as error:
                if error.dropped:  # Network drops must surface to the caller.
                    raise  # The runner decides how to reconnect or fail.
                return  # A local close is a normal stop.
            if event is not None:  # Timeouts are allowed while a stream stays quiet.
                on_event(event)  # Deliver only decoded data events.
        logger.debug("Stopped Mist stream read loop after local close")  # Local close is a normal end.

    def close(self) -> None:
        """Close the WebSocket from any thread."""
        logger.info("Closing Mist stream WebSocket")  # Log before changing state.
        self._closed.set()  # Reader loops see the local close within one socket timeout.
        with self._lock:  # Copy the socket while protected.
            socket = self._socket  # The socket can be None before open.
            self._socket = None  # Future sends cannot use a closing socket.
            self._reader = None  # Future reads cannot use the old socket.
        if socket is not None:  # close() before open is harmless.
            FrameReader.close_socket(socket)  # Abort, close, and shutdown to release CLOSE_WAIT sockets.
        logger.debug("Closed Mist stream WebSocket")  # Log after the close request.

    def _subscribe_all(self, socket: Any) -> None:
        """Send and confirm each subscription.

        Args:
            socket: The open websocket.

        Raises:
            SubscribeError: A subscription fails or times out.
        """
        pending = set(self._channels)  # Each channel must receive its own confirmation.
        logger.info("Subscribing to %s Mist stream channel(s)", len(pending))  # Log only a count.
        for channel in self._channels:  # Mist accepts one subscribe frame per channel.
            payload = json.dumps({"subscribe": channel})  # The stream contract defines this shape.
            socket.send(payload)  # Do not log the channel path.
        deadline = self._clock() + self._endpoint.profile.subscribe_timeout_seconds  # Bound the subscribe phase.
        while pending and not self._closed.is_set():  # Stop if close() interrupts open.
            if self._clock() >= deadline:  # Missing answers fail the open.
                raise SubscribeError(sorted(pending)[0], "timeout")  # Report one missing channel.
            frame = self._recv_once(self._read_slice())  # The application wait stays short for close().
            if frame is None:  # No subscription answer arrived yet.
                continue  # Keep waiting until the deadline.
            event = FrameDecoder.event(frame)  # Subscription answers are JSON events.
            self._record_subscription(event, pending)  # Remove confirmed channels or raise.
        if pending and self._closed.is_set():  # A local close interrupted the subscribe wait.
            raise ConnectionClosed(code=None, dropped=False)  # Do not report a false subscription success.
        logger.debug("Subscribed to %s Mist stream channel(s)", len(self._channels))  # Log only a count.

    def _record_subscription(self, event: dict[str, object], pending: set[str]) -> None:
        """Process one subscription event.

        Args:
            event: The decoded stream event.
            pending: The channels that still need confirmation.

        Raises:
            SubscribeError: The cloud refused a channel.
        """
        channel = event.get("channel")  # Subscription events name the channel.
        if not isinstance(channel, str):  # Non-subscription events can arrive early.
            return  # The runner filters data after open.
        if event.get("event") == "channel_subscribed":  # A channel is ready.
            pending.discard(channel)  # Unknown channels do not affect required channels.
            return  # The subscribe wait can continue.
        if event.get("event") == "subscribe_failed":  # Mist refused this channel.
            detail = event.get("detail")  # Mist can send a refusal detail.
            raise SubscribeError(channel, str(detail or "subscribe_failed"))  # Report the safe detail.

    def _recv_once(self, timeout: float) -> str | bytes | None:
        """Receive one frame with a short timeout.

        Args:
            timeout: The socket timeout for this attempt.

        Returns:
            The frame payload, or None on a timeout.

        Raises:
            ConnectionClosed: The socket ended.
        """
        reader = self._reader  # Copy the current frame reader.
        if reader is None:  # A local close removed the reader.
            raise ConnectionClosed(dropped=False)  # The caller should end cleanly.
        frame = reader.read(timeout)  # The shared reader handles keepalive and close codes.
        if frame is None:  # Control frames and timeouts are not stream data.
            return None  # The caller keeps waiting.
        if frame.opcode == websocket.ABNF.OPCODE_TEXT:  # Stream text events are JSON text.
            return frame.payload.decode("utf-8", errors="replace")  # Decode text frames for FrameDecoder.
        return frame.payload  # Binary frames go through FrameDecoder with NUL removal.

    def _read_slice(self) -> float:
        """Return one bounded socket wait slice.

        Returns:
            A short wait that lets keepalive fire before two intervals pass.
        """
        interval = self._endpoint.profile.read_timeout_seconds  # The profile controls keepalive timing.
        return max(0.01, min(0.1, interval / 2))  # Keep a lower bound so sockets do not spin.
