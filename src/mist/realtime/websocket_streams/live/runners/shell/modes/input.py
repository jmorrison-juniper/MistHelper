"""Handle writable shell input and deferred input release."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import logging  # Input actions use structured JSON records.

from src.mist.realtime.websocket_streams.live.runners.shell.modes.behavior import (
    TerminalBehavior,
)  # Input is terminal behavior.
from src.mist.realtime.websocket_streams.live.sessions.record.state import (
    SessionSink,  # First output releases the session input queue.
)
from src.mist.realtime.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)
from src.mist.realtime.websocket_streams.live.transport.shell_client import (
    ShellClient,
)  # Input uses the owned shell protocol.

logger = StructuredTransportLogger(logging.getLogger(__name__))  # Apply the shared bounded logging boundary.


class ShellInput(TerminalBehavior):
    """Send shell input and release deferred input after first output."""

    def __init__(self, sink: SessionSink, client: ShellClient) -> None:
        """Store the shell input collaborators."""
        self._input_sink = sink  # The session queue owns deferred input ordering and rate limits.
        self._input_client = client  # The client adds the required NUL prefix and binary frame.

    def send_input(self, text: str) -> None:
        """Send exact terminal input without logging its content."""
        byte_count = len(text.encode("utf-8"))  # Log the encoded size, not operator text.
        logger.emit(logging.DEBUG, "shell_input_started", {"byte_count": byte_count})  # Log before the write.
        self._input_client.send(text)  # Send one exact input frame through the owned client.
        logger.emit(logging.DEBUG, "shell_input_completed", {"byte_count": byte_count})  # Log after the write.

    def first_output(self) -> None:
        """Release queued input after the device sends its first output."""
        logger.emit(logging.INFO, "shell_input_release_started")  # Log before the queue release.
        self._input_sink.mark_input_ready()  # Send deferred keys in their original order.
        logger.emit(logging.DEBUG, "shell_input_release_completed", {"status": "ready"})  # Log the result.
