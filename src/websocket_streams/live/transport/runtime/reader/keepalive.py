"""Track receive activity and enforce WebSocket keepalive timing."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import logging  # Keepalive actions use the shared structured logger.
from collections.abc import Callable  # Tests inject a monotonic clock.

from src.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)  # Keep keepalive logs bounded and free of endpoint data.
from src.websocket_streams.live.transport.runtime.reader.contracts import (
    ConnectionClosed,
)  # Keepalive raises the shared close contract.
from src.websocket_streams.live.transport.runtime.reader.socket_runtime import (
    SocketRuntime,
)  # Keepalive closes through the socket owner.

logger = StructuredTransportLogger(logging.getLogger(__name__))  # Share the transport logging boundary.


class KeepaliveController:
    """Track peer activity and control keepalive actions."""

    def __init__(self, clock: Callable[[], float], read_timeout_seconds: float) -> None:
        """Store the clock and initialize live connection state."""
        self._clock = clock  # Tests can inject a fake monotonic clock.
        self._read_timeout_seconds = read_timeout_seconds  # The profile controls keepalive timing.
        self._last_rx = float(clock())  # A new controller starts with a live connection.
        self._ping_sent = False  # Only one ping can remain outstanding.

    def on_quiet(self, socket: SocketRuntime) -> None:
        """Send a ping or close a peer after a quiet read."""
        quiet = float(self._clock()) - self._last_rx  # Measure silence since the last received frame.
        if quiet >= self._read_timeout_seconds * 2:  # Two quiet intervals mean the peer is dead.
            socket.close()  # Close before raising so client loops wake.
            raise ConnectionClosed(code=None, dropped=True)  # Silent peer close has no status code.
        if quiet >= self._read_timeout_seconds and not self._ping_sent:  # One interval triggers keepalive.
            logger.emit(logging.DEBUG, "keepalive_ping_started", {"timeout_seconds": quiet})  # Log before ping.
            socket.ping()  # Send one websocket-client ping control frame.
            self._ping_sent = True  # Wait for any frame before another ping.
            logger.emit(logging.DEBUG, "keepalive_ping_completed", {"status": "sent"})  # Log completion.

    def on_receive(self) -> None:
        """Mark the peer as recently alive."""
        self._last_rx = float(self._clock())  # Reset the quiet timer.
        self._ping_sent = False  # A received frame answers any outstanding ping.
