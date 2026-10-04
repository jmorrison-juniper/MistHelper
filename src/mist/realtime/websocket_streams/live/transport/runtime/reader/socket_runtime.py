"""Own websocket-client receive, wait, and close operations."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import logging  # Socket actions use the shared structured logger.
import select  # Read waits must not change the shared socket timeout.
from typing import Any  # websocket-client is partly untyped.

from src.mist.realtime.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)  # Keep socket logs bounded and free of payload content.

logger = StructuredTransportLogger(logging.getLogger(__name__))  # Share the transport logging boundary.


class SocketReadiness:
    """Wait for raw socket or TLS-layer input."""

    @staticmethod
    def ready(socket: Any, timeout: float) -> bool:
        """Wait without changing the shared socket timeout."""
        raw_socket = getattr(socket, "sock", None)  # websocket-client stores its raw socket here.
        if raw_socket is None or SocketReadiness._tls_bytes_waiting(raw_socket):  # Fakes or TLS need no wait.
            return True  # Receive at once.
        return SocketReadiness._select(raw_socket, timeout)  # Wait for plain socket input.

    @staticmethod
    def _select(raw_socket: Any, timeout: float) -> bool:
        """Run one bounded select wait."""
        logger.emit(logging.DEBUG, "socket_wait_started", {"timeout_seconds": timeout})  # Log before select.
        readable, _writable, errored = select.select(
            [raw_socket], [], [raw_socket], max(0.0, timeout)
        )  # Wait without changing the socket timeout.
        status = SocketReadiness._status(readable, errored)  # Summarize without socket data.
        logger.emit(logging.DEBUG, "socket_wait_completed", {"status": status})  # Log the bounded outcome.
        return SocketReadiness._result(readable, errored)  # Return readiness or raise a socket error.

    @staticmethod
    def _status(readable: list[Any], errored: list[Any]) -> str:
        """Return the safe select outcome label."""
        return "error" if errored else "ready" if readable else "quiet"  # Report no socket identity.

    @staticmethod
    def _result(readable: list[Any], errored: list[Any]) -> bool:
        """Return readiness or raise an exceptional socket state."""
        if errored:  # Exceptional socket state is a transport loss.
            raise OSError("The WebSocket socket reported an error.")  # Let FrameReader map the failure.
        return bool(readable)  # A readable socket can receive a frame.

    @staticmethod
    def _tls_bytes_waiting(raw_socket: Any) -> bool:
        """Tell whether the TLS layer holds decrypted bytes."""
        pending = getattr(raw_socket, "pending", None)  # Only a TLS socket has pending().
        if not callable(pending):  # A plain TCP socket has no TLS buffer.
            return False  # Select alone is correct for plain TCP.
        waiting = int(pending())  # Count decrypted bytes that no read has taken.
        if waiting > 0:  # Log only the positive branch on this frequent check.
            logger.emit(logging.DEBUG, "tls_buffer_ready", {"byte_count": waiting})  # Log the byte count.
        return waiting > 0  # Held bytes mean recv_data can run now.


class SocketRuntime:
    """Own operations on one websocket-client socket."""

    def __init__(self, socket: Any) -> None:
        """Store the caller-owned websocket-client socket."""
        self._socket = socket  # The transport client controls socket lifetime.

    def receive(self, timeout: float) -> tuple[int, object] | None:
        """Receive one frame when the socket becomes ready."""
        if not SocketReadiness.ready(self._socket, timeout):  # Keep waits independent of socket timeout.
            return None  # Let the frame reader apply keepalive behavior.
        logger.emit(logging.DEBUG, "socket_receive_started")  # Log before receiving a frame.
        opcode, payload = self._socket.recv_data(control_frame=True)  # Receive data and control frames.
        logger.emit(logging.DEBUG, "socket_receive_completed", {"code": int(opcode)})  # Log safe metadata.
        return int(opcode), payload  # Return the normalized opcode and unlogged payload.

    def ping(self) -> None:
        """Send one WebSocket ping control frame."""
        self._socket.ping()  # websocket-client owns the control frame encoding.

    def close(self) -> None:
        """Abort, close, and shut down the socket."""
        logger.emit(logging.DEBUG, "socket_close_started")  # Log before the close sequence.
        if hasattr(self._socket, "abort"):  # websocket-client abort wakes a blocked reader.
            self._socket.abort()  # Abort before close so recv_data stops promptly.
        self._socket.close()  # Ask websocket-client to process close state.
        if hasattr(self._socket, "shutdown"):  # websocket-client shutdown handles CLOSE_WAIT sockets.
            self._socket.shutdown()  # Shutdown is safe after close.
        logger.emit(logging.DEBUG, "socket_close_completed", {"status": "closed"})  # Log completion.
