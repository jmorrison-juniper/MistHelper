"""Open one Mist stream WebSocket connection."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import json  # Subscribe requests use JSON text frames.
import logging  # Structured records use repository logging handlers.
import threading  # Close can occur from another thread.
import time  # The default clock is monotonic.
from collections.abc import Callable, Sequence  # Collaborator contracts stay explicit.
from typing import Any  # websocket-client is not fully typed.

import websocket  # The transport uses websocket-client.

from src.mist.realtime.websocket_streams.live.transport.endpoint import (
    MistStreamEndpoint,
)  # Endpoint owns auth and TLS values.
from src.mist.realtime.websocket_streams.live.transport.runtime.frame_decoder import (
    FrameDecoder,
    SubscribeError,
)  # Decode events.
from src.mist.realtime.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)  # T072 provides the safe JSON logging boundary.
from src.mist.realtime.websocket_streams.live.transport.runtime.reader.contracts import (
    ConnectionClosed,
)  # Share close details.
from src.mist.realtime.websocket_streams.live.transport.runtime.reader.frame_reader import (
    FrameReader,
)  # Share keepalive reads.
from src.mist.realtime.websocket_streams.live.transport.runtime.reader.socket_runtime import (
    SocketRuntime,
)  # Own socket closure.


class StreamConnection:
    """Own one stream socket and its shared frame reader."""

    _socket: Any | None  # The socket exists only after open.
    _reader: FrameReader | None  # The reader follows the socket lifetime.

    def __init__(
        self,
        endpoint: MistStreamEndpoint,
        factory: Callable[..., Any],
        clock: Callable[[], float],
        closed: threading.Event,
    ) -> None:
        """Store the connection dependencies."""
        self._endpoint, self._factory = endpoint, factory  # Store connection settings and the socket factory.
        self._clock, self._closed = clock, closed  # Store timing and close coordination.
        self._lock = threading.Lock()  # Protect the socket and reader references.
        self._socket, self._reader = None, None  # Create empty connection references.
        self._log = StructuredTransportLogger(logging.getLogger(__name__))  # Emit bounded JSON records.

    def open(self) -> Any:
        """Open and publish one websocket-client socket."""
        socket = self._create()  # Build the socket with authentication, TLS, and host proxy settings.
        with self._lock:  # Publish both connection objects together.
            self._socket = socket  # Close can now reach the live socket.
            self._reader = FrameReader(socket, self._closed, self._clock, self._endpoint.profile.read_timeout_seconds)
        if self._closed.is_set():  # A close can occur while the factory blocks.
            SocketRuntime(socket).close()  # Release the socket before any subscription leaves.
            raise ConnectionClosed(code=None, dropped=False)  # Report a local stop.
        self._log.emit(logging.DEBUG, "stream_open_ready", {"status": "open"})  # Log safe readiness.
        return socket  # The subscription collaborator needs the open socket.

    def _create(self) -> Any:
        """Create one configured websocket-client socket."""
        timeout = self._endpoint.profile.subscribe_timeout_seconds  # Bound TCP and TLS setup.
        self._log.emit(logging.INFO, "stream_open_start", {"timeout_seconds": timeout})  # Log safe timing.
        socket = self._factory(
            self._endpoint.stream_url(),
            header=self._endpoint.headers(),
            cookie=self._endpoint.cookie(),
            sslopt=self._endpoint.sslopt(),
            enable_multithread=True,
            timeout=timeout,
        )  # Leave proxy selection to websocket-client and the host environment.
        socket.settimeout(timeout)  # Keep write operations bounded after the handshake.
        return socket  # Open publishes the socket only after the factory returns.

    def receive(self, timeout: float) -> str | bytes | None:
        """Return one decoded frame payload or no payload."""
        reader = self._reader  # Copy the reader without extending the lock scope.
        if reader is None:  # Close removes the reader before it closes the socket.
            raise ConnectionClosed(dropped=False)  # Report a clean local stop.
        frame = reader.read(timeout)  # The shared reader handles ping, pong, and close frames.
        if frame is None:  # A timeout or control frame has no application payload.
            return None  # The caller can continue its bounded wait.
        return (
            frame.payload.decode("utf-8", errors="replace")
            if frame.opcode == websocket.ABNF.OPCODE_TEXT
            else frame.payload
        )  # Decode text events and preserve binary event bytes.

    def close(self) -> None:
        """Close the stream socket from any thread."""
        self._log.emit(logging.INFO, "stream_close_start", {"action": "close"})  # Log before changing state.
        self._closed.set()  # Wake all bounded read loops.
        with self._lock:  # Detach both connection objects together.
            socket = self._socket  # Copy the socket for closure outside the lock.
            self._socket = None  # Future operations cannot use the old socket.
            self._reader = None  # Future reads report a local close.
        if socket is not None:  # Closing before open remains harmless.
            SocketRuntime(socket).close()  # Abort, close, and shutdown the socket.
        self._log.emit(logging.DEBUG, "stream_close_ready", {"status": "closed"})  # Log safe completion.


class SubscriptionCoordinator:
    """Send channel requests and confirm each subscription."""

    def __init__(self, channels: Sequence[str], clock: Callable[[], float], timeout: float) -> None:
        """Store immutable subscription settings."""
        self._channels = tuple(channels)  # One connection uses one stable channel set.
        self._clock = clock  # Tests can control subscription deadlines.
        self._timeout = timeout  # The endpoint bounds the complete subscribe phase.
        self._log = StructuredTransportLogger(logging.getLogger(__name__))  # Emit bounded JSON records.

    def subscribe(self, socket: Any, connection: StreamConnection, closed: threading.Event) -> None:
        """Send and confirm every configured channel."""
        pending = self._start(socket)  # Send each request and return the pending channel set.
        deadline = self._clock() + self._timeout  # Bound the full confirmation phase.
        read_slice = max(0.01, min(0.1, self._timeout / 2))  # Keep close and keepalive checks frequent.
        while pending and not closed.is_set():  # A local close interrupts the wait.
            if self._clock() >= deadline:  # Missing confirmation fails the open.
                raise SubscribeError(sorted(pending)[0], "timeout")  # Preserve the existing error contract.
            payload = connection.receive(read_slice)  # Read one bounded subscription frame.
            if payload is not None:  # Control frames and timeouts have no subscription event.
                self._record(FrameDecoder.event(payload), pending)  # Update or fail the pending set.
        self._finish(pending)  # Report a local close or successful completion.

    def _record(self, event: dict[str, object], pending: set[str]) -> None:
        """Apply one subscription event to the pending set."""
        channel = event.get("channel")  # Subscription answers identify one channel.
        if not isinstance(channel, str):  # Early data and malformed events do not confirm a channel.
            return  # Continue waiting for the required confirmations.
        if event.get("event") == "channel_subscribed":  # The cloud accepted this channel.
            pending.discard(channel)  # Unknown channels do not affect required channels.
        elif event.get("event") == "subscribe_failed":  # The cloud refused this channel.
            detail = event.get("detail")  # Preserve the existing refusal detail.
            raise SubscribeError(channel, str(detail or "subscribe_failed"))  # Report the same contract error.

    def _start(self, socket: Any) -> set[str]:
        """Send each channel request and return the pending set."""
        pending = set(self._channels)  # Each channel needs one confirmation.
        self._log.emit(logging.INFO, "stream_subscribe_start", {"count": len(pending)})  # Log only the count.
        for channel in self._channels:  # Mist accepts one request for each channel.
            socket.send(json.dumps({"subscribe": channel}))  # Do not log the channel path.
        return pending  # The subscribe loop removes confirmed channels.

    def _finish(self, pending: set[str]) -> None:
        """Validate the completed subscription phase."""
        if pending:  # Only a local close can leave pending channels here.
            raise ConnectionClosed(code=None, dropped=False)  # Do not report false success.
        self._log.emit(logging.DEBUG, "stream_subscribe_ready", {"count": len(self._channels)})  # Log the count.


class StreamEventReader:
    """Read decoded data events from one stream connection."""

    def __init__(
        self,
        connection: StreamConnection,
        closed: threading.Event,
        clock: Callable[[], float],
        interval: float,
    ) -> None:
        """Store the read-loop collaborators."""
        self._connection, self._closed = connection, closed  # Store frame and close collaborators.
        self._clock, self._interval = clock, interval  # Store timing values.

    def next_event(self, timeout: float) -> dict[str, object] | None:
        """Return the next data event within the requested wait."""
        deadline = self._clock() + timeout  # Bound the complete application wait.
        while not self._closed.is_set():  # A local close ends the loop.
            wait_left = deadline - self._clock()  # Recompute after every frame.
            if wait_left <= 0:  # The requested interval expired.
                return None  # A quiet stream remains valid.
            event = self._read(wait_left)  # Read and decode one application event.
            if event is None:  # A timeout or control frame is not an application event.
                continue  # Continue until data or the outer deadline.
            if event.get("event") == "data":  # Callers consume data events only.
                return event  # Preserve channel and data fields.
        raise ConnectionClosed(dropped=False)  # A local close is not a network drop.

    def _read(self, wait_left: float) -> dict[str, object] | None:
        """Read and decode one stream event."""
        read_slice = max(0.01, min(0.1, self._interval / 2))  # Keep keepalive checks frequent.
        payload = self._connection.receive(min(wait_left, read_slice))  # Read one bounded frame.
        return None if payload is None else FrameDecoder.event(payload)  # Decode only application payloads.


class StreamClient:
    """Coordinate one Mist stream connection and its collaborators."""

    def __init__(
        self,
        endpoint: MistStreamEndpoint,
        channels: Sequence[str],
        factory: Callable[..., Any] = websocket.create_connection,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        """Build the stream collaborators."""
        self._closed = threading.Event()  # One event coordinates the complete client.
        self._connection = StreamConnection(endpoint, factory, clock, self._closed)  # Own socket state.
        self._subscriptions = SubscriptionCoordinator(
            channels, clock, endpoint.profile.subscribe_timeout_seconds
        )  # Own subscription protocol state.
        self._events = StreamEventReader(
            self._connection, self._closed, clock, endpoint.profile.read_timeout_seconds
        )  # Own event wait behavior.
        self._log = StructuredTransportLogger(logging.getLogger(__name__))  # Emit bounded JSON records.

    def open(self) -> None:
        """Open the socket and confirm every channel subscription."""
        socket = self._connection.open()  # Publish the live socket before subscription.
        self._subscriptions.subscribe(socket, self._connection, self._closed)  # Confirm every required channel.

    def next_event(self, timeout: float) -> dict[str, object] | None:
        """Return the next data event within the requested wait."""
        return self._events.next_event(timeout)  # The reader owns frame filtering and timeout behavior.

    def run(self, on_event: Callable[[dict[str, object]], None]) -> None:
        """Deliver data events until close or a dropped connection."""
        self._log.emit(logging.INFO, "stream_run_start", {"action": "read_loop"})  # Log the safe action.
        while not self._closed.is_set():  # A local close ends the callback loop.
            try:  # Distinguish a local close from a dropped connection.
                event = self._events.next_event(0.1)  # Keep stop checks frequent.
            except ConnectionClosed as error:
                if error.dropped:  # The caller must decide whether to reconnect.
                    raise  # Preserve dropped connection behavior.
                return  # A local close is a normal stop.
            if event is not None:  # Quiet intervals need no callback.
                on_event(event)  # Deliver the complete decoded data event.

    def close(self) -> None:
        """Close the stream connection from any thread."""
        self._connection.close()  # The connection owns socket detachment and shutdown.
