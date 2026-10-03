"""Read WebSocket frames with close and keepalive handling."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import logging  # Reader actions use the shared structured logger.
import threading  # The close event can come from another thread.
from collections.abc import Callable  # Tests inject a monotonic clock.
from typing import Any  # websocket-client is partly untyped.

import websocket  # The reader maps websocket-client exceptions.
from src.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)  # Keep reader logs bounded and free of payload data.
from src.websocket_streams.live.transport.runtime.reader.contracts import (
    ConnectionClosed,
    FrameRead,
    FrameValues,
)  # Share close, frame, and value contracts.
from src.websocket_streams.live.transport.runtime.reader.keepalive import (
    KeepaliveController,
)  # Delegate all quiet timing state.
from src.websocket_streams.live.transport.runtime.reader.socket_runtime import (
    SocketRuntime,
)  # Delegate socket receive and close operations.
from websocket import ABNF  # Opcode constants come from websocket-client.

logger = StructuredTransportLogger(logging.getLogger(__name__))  # Share the transport logging boundary.


class FrameReader:
    """Coordinate socket reads, keepalive state, and frame contracts."""

    def __init__(
        self,
        socket: Any,
        closed: threading.Event,
        clock: Callable[[], float],
        read_timeout_seconds: float,
    ) -> None:
        """Build the socket and keepalive collaborators."""
        self._socket = SocketRuntime(socket)  # One collaborator owns all socket operations.
        self._closed = closed  # Local close changes the dropped marker.
        self._keepalive = KeepaliveController(clock, read_timeout_seconds)  # One collaborator owns timing.

    def read(self, timeout: float) -> FrameRead | None:
        """Read one application frame or one control frame."""
        logger.emit(logging.DEBUG, "frame_read_started", {"timeout_seconds": timeout})  # Log before reading.
        if self._closed.is_set():  # A local close should not wait for network data.
            raise ConnectionClosed(code=None, dropped=False)  # Report a local close to the runner.
        try:  # Map websocket-client errors to the runner close contract.
            frame = self._socket.receive(timeout)  # Wait for and receive one frame when available.
        except websocket.WebSocketTimeoutException:
            frame = None  # Apply the normal quiet-read behavior.
        except (websocket.WebSocketConnectionClosedException, websocket.WebSocketException, OSError) as exc:
            logger.emit(logging.DEBUG, "frame_read_completed", {"status": "closed"})  # Log the mapped outcome.
            raise ConnectionClosed(code=None, dropped=not self._closed.is_set()) from exc  # Preserve origin.
        if frame is None:  # A normal wait timeout has no application frame.
            self._keepalive.on_quiet(self._socket)  # Send a ping or close a dead peer.
            logger.emit(logging.DEBUG, "frame_read_completed", {"status": "quiet"})  # Log the quiet outcome.
            return None  # A quiet period is not application data.
        return self._frame_or_control(*frame)  # Process control and application frames.

    def _frame_or_control(self, opcode: int, payload: object) -> FrameRead | None:
        """Process one received frame."""
        data = FrameValues.payload_bytes(payload)  # Normalize payloads without logging content.
        if opcode == ABNF.OPCODE_CLOSE:  # A close frame carries an optional code.
            code = FrameValues.close_code(data)  # Decode only the two-byte status value.
            raise ConnectionClosed(code=code, dropped=not self._closed.is_set())  # End reading.
        return self._active_frame(opcode, data)  # Process known peer activity or ignore unknown opcodes.

    def _active_frame(self, opcode: int, data: bytes) -> FrameRead | None:
        """Process one non-close frame."""
        if opcode not in {ABNF.OPCODE_PING, ABNF.OPCODE_PONG, ABNF.OPCODE_TEXT, ABNF.OPCODE_BINARY}:
            return None  # Unknown non-close frames do not produce data or liveness.
        self._keepalive.on_receive()  # Reset keepalive state after known peer activity.
        if opcode in {ABNF.OPCODE_PING, ABNF.OPCODE_PONG}:  # A control reply proves peer liveness.
            result = None  # Control frames are not application output.
        else:
            result = FrameRead(opcode, data)  # Preserve raw application payload behavior.
        logger.emit(
            logging.DEBUG,
            "frame_read_completed",
            {"code": opcode, "status": "data" if result else "control"},
        )  # Log completion without payload data.
        return result  # Return application data or None for a control frame.
