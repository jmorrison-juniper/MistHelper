"""Open one Mist shell or screen WebSocket connection."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import json  # Resize frames use JSON text.
import logging  # Structured records use repository logging handlers.
import threading  # Send and read can occur on different threads.
import time  # The default clock is monotonic.
from collections.abc import Callable  # Collaborator contracts stay explicit.
from typing import Any  # websocket-client is not fully typed.

import websocket  # The transport uses websocket-client.
from websocket import ABNF  # Binary fallback uses the websocket-client opcode.

from src.mist.realtime.websocket_streams.intake.fields.error import (
    StreamRequestError,
)  # Closed writes use the HTTP contract.
from src.mist.realtime.websocket_streams.live.transport.endpoint import (
    MistStreamEndpoint,
    ShellAddressPolicy,
)  # Connection rules.
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


class ShellConnection:
    """Own one shell socket and its shared frame reader."""

    _socket: Any | None  # The socket exists only after open.
    _reader: FrameReader | None  # The reader follows the socket lifetime.

    def __init__(
        self,
        endpoint: MistStreamEndpoint,
        policy: ShellAddressPolicy,
        factory: Callable[..., Any],
        clock: Callable[[], float],
    ) -> None:
        """Store the connection dependencies."""
        self._endpoint, self._policy = endpoint, policy  # Store connection settings and address policy.
        self._factory, self._clock = factory, clock  # Store the socket factory and clock.
        self._closed, self._lock = threading.Event(), threading.Lock()  # Coordinate close and state access.
        self._socket, self._reader = None, None  # Create empty connection references.
        self._log = StructuredTransportLogger(logging.getLogger(__name__))  # Emit bounded JSON records.

    def open(self, url: str) -> None:
        """Validate, open, and publish one shell socket."""
        socket = self._create(url)  # Validate the address and build the configured socket.
        with self._lock:  # Publish both connection objects together.
            self._socket = socket  # Writers can now use the connection.
            self._closed.clear()  # A new open starts with a live read state.
            self._reader = FrameReader(socket, self._closed, self._clock, self._endpoint.profile.read_timeout_seconds)
        self._log.emit(logging.DEBUG, "shell_open_ready", {"status": "open"})  # Log safe readiness.

    def _create(self, url: str) -> Any:
        """Create one validated websocket-client socket."""
        safe_url, timeout = (
            self._policy.check(url),
            self._endpoint.profile.subscribe_timeout_seconds,
        )  # Validate the address and read the connect timeout.
        self._log.emit(logging.INFO, "shell_open_start", {"timeout_seconds": timeout})  # Log safe timing.
        socket = self._factory(
            safe_url,
            header=self._endpoint.headers(),
            cookie=self._endpoint.cookie(),
            sslopt=self._endpoint.sslopt(),
            enable_multithread=True,
            skip_utf8_validation=True,
            timeout=timeout,
        )  # Leave proxy selection to websocket-client and the host environment.
        socket.settimeout(timeout)  # Keep later writes bounded.
        return socket  # Open publishes the socket and reader together.

    def close(self) -> None:
        """Close the shell socket from any thread."""
        self._log.emit(logging.INFO, "shell_close_start", {"action": "close"})  # Log before changing state.
        self._closed.set()  # Wake all bounded read loops.
        with self._lock:  # Detach both connection objects together.
            socket = self._socket  # Copy the socket for closure outside the lock.
            self._socket = None  # Future writes report not_open.
            self._reader = None  # Future reads report a local close.
        if socket is not None:  # Closing before open remains harmless.
            SocketRuntime(socket).close()  # Abort, close, and shutdown the socket.
        self._log.emit(logging.DEBUG, "shell_close_ready", {"status": "closed"})  # Log safe completion.

    def resource(self, kind: str) -> Any:
        """Return the active socket or reader for one collaborator."""
        resource = self._socket if kind == "socket" else self._reader  # Select the requested live resource.
        if resource is None or self._closed.is_set():  # Closed operations must fail before network access.
            if kind == "socket":  # Writes use the stable HTTP request error.
                raise StreamRequestError("not_open", "The shell connection is not open.")  # Preserve the contract.
            raise ConnectionClosed(dropped=False)  # Reads report a clean local close.
        return resource  # The caller owns the short operation scope.


class ShellFrameReader:
    """Read shell output and remove only the Mist channel marker."""

    def __init__(self, connection: ShellConnection, clock: Callable[[], float], interval: float) -> None:
        """Store the read dependencies."""
        self._connection = connection  # One collaborator owns the frame reader lifetime.
        self._clock = clock  # Tests can control outer read deadlines.
        self._interval = interval  # The profile controls keepalive timing.

    def read(self, timeout: float | None = None) -> bytes | None:
        """Return one output frame or no data after a quiet interval."""
        deadline = None if timeout is None else self._clock() + timeout  # None requests one quiet interval.
        while True:  # The connection reader reports local or remote closure.
            wait = self._slice() if deadline is None else min(self._slice(), max(0.0, deadline - self._clock()))
            if deadline is not None and wait <= 0:  # The requested wait expired.
                return None  # A quiet shell remains valid.
            payload = self._receive(wait)  # Read one application frame.
            if payload is not None:  # A data frame arrived.
                return self._strip(payload)  # Remove exactly one Mist marker byte.
            if deadline is None:  # The caller requested one quiet interval.
                return None  # Preserve the existing quiet result.

    def _receive(self, timeout: float) -> bytes | None:
        """Return one frame payload or no payload."""
        frame = self._connection.resource("reader").read(timeout)  # Shared logic handles keepalive and close frames.
        return None if frame is None else frame.payload  # Shell output stays as bytes.

    def _slice(self) -> float:
        """Return one short receive interval."""
        return max(0.01, min(0.1, self._interval / 2))  # Prevent busy loops and delayed keepalive checks.

    def _strip(self, frame: bytes) -> bytes:
        """Remove one leading Mist channel marker byte."""
        return frame[1:] if frame.startswith(b"\x00") else frame  # Keep all remaining output bytes unchanged.


class ShellFrameWriter:
    """Serialize terminal input and resize frames on one socket."""

    def __init__(self, connection: ShellConnection, send_lock: threading.Lock) -> None:
        """Store the write dependencies."""
        self._connection = connection  # The connection validates the open socket.
        self._send_lock = send_lock  # One lock preserves input and resize order.
        self._log = StructuredTransportLogger(logging.getLogger(__name__))  # Emit bounded JSON records.

    def send(self, text: str) -> None:
        """Send terminal input as one binary frame."""
        payload = b"\x00" + text.encode("utf-8")  # Mist input requires one leading channel marker.
        self._log.emit(logging.DEBUG, "shell_input_start", {"byte_count": len(payload)})  # Log only byte count.
        self._write(payload, binary=True)  # Preserve the exact UTF-8 bytes on the wire.
        self._log.emit(logging.DEBUG, "shell_input_ready", {"byte_count": len(payload)})  # Log only byte count.

    def resize(self, cols: int, rows: int) -> None:
        """Send the terminal size as one text frame."""
        message = json.dumps({"resize": {"width": cols, "height": rows}})  # Preserve the protocol shape.
        self._log.emit(logging.DEBUG, "shell_resize_start", {"count": 2})  # Do not log unbounded dimensions.
        self._write(message, binary=False)  # Keep resize order with input writes.
        self._log.emit(logging.DEBUG, "shell_resize_ready", {"status": "sent"})  # Log safe completion.

    def _write(self, payload: str | bytes, binary: bool) -> None:
        """Write one frame and close the connection on failure."""
        try:  # A broken link must close the terminal session.
            with self._send_lock:  # Preserve input and resize frame order.
                socket = self._connection.resource("socket")  # Refuse writes after close.
                if binary and hasattr(socket, "send_binary"):  # Real sockets expose a binary helper.
                    socket.send_binary(payload)  # Send the binary input frame.
                elif binary:  # Fakes and older clients use the opcode form.
                    socket.send(payload, opcode=ABNF.OPCODE_BINARY)  # Preserve the binary opcode.
                else:  # Resize uses a text frame.
                    socket.send(payload)  # Send the JSON resize message.
        except (websocket.WebSocketException, OSError) as error:
            self._connection.close()  # Stop the reader after a failed write.
            raise StreamRequestError("not_open", "The shell connection is not open.") from error  # Stable refusal.


class ShellLifecycle:
    """Provide the shared close operation for shell clients."""

    _connection: ShellConnection  # Subclasses create the connection collaborator.

    def close(self) -> None:
        """Close the shell connection from any thread."""
        self._connection.close()  # The connection owns socket detachment and shutdown.


class ShellClient(ShellLifecycle):
    """Coordinate one Mist shell connection and its collaborators."""

    def __init__(
        self,
        endpoint: MistStreamEndpoint,
        policy: ShellAddressPolicy,
        factory: Callable[..., Any] = websocket.create_connection,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        """Build the shell collaborators."""
        self._connection = ShellConnection(endpoint, policy, factory, clock)  # Own socket and reader state.
        self._reader = ShellFrameReader(
            self._connection, clock, endpoint.profile.read_timeout_seconds
        )  # Own bounded output reads.
        self._writer = ShellFrameWriter(self._connection, threading.Lock())  # Own ordered input and resize writes.

    def open(self, url: str, cols: int, rows: int) -> None:
        """Open the shell connection and send its initial size."""
        self._connection.open(url)  # Validate and publish the socket first.
        self._writer.resize(cols, rows)  # Send the initial dimensions immediately.

    def read(self, timeout: float | None = None) -> bytes | None:
        """Return one shell output frame or no data."""
        return self._reader.read(timeout)  # The reader owns keepalive and marker behavior.

    def send(self, text: str) -> None:
        """Send terminal input as one binary frame."""
        self._writer.send(text)  # The writer owns ordering and failure closure.

    def resize(self, cols: int, rows: int) -> None:
        """Send the current terminal dimensions."""
        self._writer.resize(cols, rows)  # The writer preserves ordering with input.
