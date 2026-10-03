"""Queue terminal input until the first output for issue #3671."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import logging  # Structured events use standard logging levels.
import threading  # Web threads can submit input at the same time.
import time  # The default rate clock uses monotonic time.
from collections import deque  # The rate window drops old request times.
from collections.abc import Callable  # Senders and clocks use callable contracts.

from src.websocket_streams.intake.fields.error import StreamRequestError  # Contract refusals use shared codes.
from src.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)  # Use the shared bounded logger from T072.

logger = StructuredTransportLogger(logging.getLogger(__name__))  # Apply the shared logging boundary.


class PendingInputBuffer:
    """Keep bounded early input in exact submission order."""

    LIMIT = 4096  # The portal keeps at most 4,096 early characters.

    def __init__(self) -> None:
        """Build an empty early input buffer."""
        self._items: list[str] = []  # Preserve each submission boundary and order.
        self._characters = 0  # Track the cap without rescanning queued text.

    def add(self, text: str) -> None:
        """Add text or refuse input beyond the character cap."""
        if self._characters + len(text) > self.LIMIT:  # Early input has a strict cap.
            raise StreamRequestError("input_full", "The terminal input queue is full.")  # Refuse overflow.
        self._items.append(text)  # Keep this input until first output arrives.
        self._characters += len(text)  # Update the bounded character count.

    def drain(self) -> list[str]:
        """Remove and return all queued input."""
        items = self._items  # Keep the current list for ordered sending.
        self._items = []  # Start a new empty queue before any sender call.
        self._characters = 0  # Reset the cap with the new queue.
        return items  # The caller sends these items in exact order.

    def clear(self) -> None:
        """Drop all queued input."""
        self._items.clear()  # Remove text that cannot be sent after close.
        self._characters = 0  # Reset the bounded character count.


class BoundInputSender:
    """Bind and call the device input sender."""

    def __init__(self) -> None:
        """Build an unbound sender."""
        self._sender: Callable[[str], None] | None = None  # The runner binds after creation.

    def bind(self, sender: Callable[[str], None]) -> None:
        """Bind the device sender."""
        self._sender = sender  # Store the active runner input method.

    def send(self, text: str) -> None:
        """Send exact text or refuse an unbound sender."""
        if self._sender is None:  # A runner must bind before direct sends.
            raise StreamRequestError("not_open", "The terminal input sender is not ready.")  # Refuse it.
        self._sender(text)  # Send exact text without logging its content.


class RequestRateLimiter:
    """Apply one sliding request window to input and resize."""

    LIMIT = 60  # One session accepts 60 input or resize requests each second.

    def __init__(self, clock: Callable[[], float]) -> None:
        """Build an empty rate window."""
        self._clock = clock  # Tests inject a deterministic monotonic clock.
        self._times: deque[float] = deque()  # Keep accepted request times in order.

    def check(self) -> int:
        """Count one request and return the current window count."""
        now = self._clock()  # Use one clock value for this decision.
        while self._times and now - self._times[0] >= 1.0:  # Remove expired request times.
            self._times.popleft()  # Drop the oldest time first.
        if len(self._times) >= self.LIMIT:  # The next request exceeds the cap.
            raise StreamRequestError("rate_limited", "The terminal request rate is too high.")  # Refuse it.
        self._times.append(now)  # Count the accepted request.
        return len(self._times)  # The caller logs the safe window count.


class TerminalInput:
    """Coordinate early input, direct sends, close, and rate state."""

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        """Build an empty input coordinator."""
        self._lock = threading.RLock()  # Queue state and sends share one ordering lock.
        self._pending = PendingInputBuffer()  # One collaborator owns early input limits.
        self._sender = BoundInputSender()  # One collaborator owns the runner binding.
        self.rate = RequestRateLimiter(clock)  # Input and resize share this request window.
        self._ready = False  # False means the first output has not arrived.
        self._closed = False  # Closed input refuses later submissions.

    def bind(self, sender: Callable[[str], None]) -> None:
        """Bind the device sender."""
        logger.emit(logging.INFO, "terminal_input_bind_start")  # Log before the state change.
        with self._lock:  # Bind must not race with release.
            self._sender.bind(sender)  # Store the runner input method.
        logger.emit(logging.DEBUG, "terminal_input_bind_complete", {"status": "bound"})  # Log the result.

    def submit(self, text: str) -> bool:
        """Queue early text or send ready text in exact order."""
        logger.emit(logging.DEBUG, "terminal_input_submit_start", {"count": len(text)})  # Log only text length.
        with self._lock:  # Queue checks and sends must preserve submission order.
            if self._closed:  # Ended sessions cannot accept input.
                raise StreamRequestError("not_open", "The terminal session is not open.")  # Refuse it.
            if self._ready:  # Input goes directly to the device after first output.
                self._sender.send(text)  # Keep the lock so concurrent submissions stay ordered.
                queued = False  # The input did not wait in the queue.
            else:  # Early input must wait for first output.
                self._pending.add(text)  # Enforce the early character cap.
                queued = True  # The caller reports that the input waits.
        fields = {"count": len(text), "status": "queued" if queued else "sent"}  # Use safe bounded fields.
        logger.emit(logging.DEBUG, "terminal_input_submit_complete", fields)  # Log the safe result.
        return queued  # Preserve the route contract.

    def release(self) -> None:
        """Release queued input after the first terminal output."""
        logger.emit(logging.INFO, "terminal_input_release_start")  # Log before sending queued input.
        with self._lock:  # Release and later submissions share one send order.
            if self._closed or self._ready:  # Closed or released input needs no action.
                status = "closed" if self._closed else "ready"  # Report the safe skip reason.
                logger.emit(logging.DEBUG, "terminal_input_release_skipped", {"status": status})  # Log it.
                return  # Do not send or drain the queue.
            self._ready = True  # Preserve direct-send state if a bound sender fails.
            pending = self._pending.drain()  # Remove queued text before sender calls.
            for item in pending:  # Preserve the exact early input order.
                self._sender.send(item)  # Send each queued submission under the order lock.
        logger.emit(logging.DEBUG, "terminal_input_release_complete", {"count": len(pending)})  # Log count.

    def close(self) -> None:
        """Close input and drop queued text."""
        logger.emit(logging.INFO, "terminal_input_close_start")  # Log before the state change.
        with self._lock:  # Close must not race with submit or release.
            self._closed = True  # Later submissions fail.
            self._pending.clear()  # Early input cannot be sent after close.
        logger.emit(logging.DEBUG, "terminal_input_close_complete", {"status": "closed"})  # Log the result.
