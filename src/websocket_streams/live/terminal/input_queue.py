"""Queue terminal input until the first output for issue #3671.

Why:
    Issue #3671 lets an operator type before the shell prints its first
    prompt. The queue preserves that early input order, then sends later input
    directly to the device.
"""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import logging  # The input queue logs counts, never typed text.
import threading  # Web threads can submit input at the same time.
import time  # The default rate clock uses monotonic time.
from collections import deque  # The rate window drops old request times.
from collections.abc import Callable  # The sender and clock are injected callables.

from src.websocket_streams.intake.fields import StreamRequestError  # Contract refusals use shared codes.

logger = logging.getLogger(__name__)  # Keep input queue logs under this module.


class TerminalInput:
    """A thread-safe input queue for one writable terminal session."""

    PENDING_LIMIT = 4096  # The portal keeps at most 4,096 characters before first output.
    RATE_LIMIT = 60  # One session accepts 60 input or resize requests each second.

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        """Build an empty input queue.

        Args:
            clock: The monotonic clock used by the rate limiter.
        """
        self._clock = clock  # Tests inject a fake clock for rate checks.
        self._lock = threading.RLock()  # Queue state and sends share one ordering lock.
        self._pending: list[str] = []  # Text before first output waits here.
        self._ready = False  # False means the first output has not arrived.
        self._closed = False  # Closed queues refuse later input.
        self._sender: Callable[[str], None] | None = None  # The runner send method is bound later.
        self._times: deque[float] = deque()  # The rate limiter stores the newest request times.

    def bind(self, sender: Callable[[str], None]) -> None:
        """Bind the device sender.

        Args:
            sender: The callable that sends text to the device.
        """
        logger.info("Binding terminal input sender")  # Log before the state change.
        with self._lock:  # Bind must not race with release.
            self._sender = sender  # Store the runner send callable.
        logger.debug("Bound terminal input sender")  # Log after the state change.

    def submit(self, text: str) -> bool:
        """Submit text to the terminal session.

        Args:
            text: The exact text that the device must receive.

        Returns:
            True when the text was queued, or False when it was sent.

        Raises:
            StreamRequestError: The input is closed, full, or not bound.
        """
        logger.debug("Submitting terminal input length=%s", len(text))  # Debug level: the gateway logs each request.
        with self._lock:  # The queue check and send order must be atomic.
            self._ensure_open()  # Closed sessions cannot accept input.
            if self._ready:  # After first output, input goes to the device at once.
                self._send_locked(text)  # Keep the lock so two web threads preserve order.
                logger.debug("Sent terminal input length=%s", len(text))  # Log only the safe character count.
                return False  # The input did not wait in the queue.
            pending_chars = sum(len(item) for item in self._pending)  # Calculate the queued character count.
            if pending_chars + len(text) > self.PENDING_LIMIT:  # Early input has a strict cap.
                raise StreamRequestError("input_full", "The terminal input queue is full.")  # Contract error.
            self._pending.append(text)  # Keep this input until first output arrives.
        logger.debug("Queued terminal input length=%s", len(text))  # Log only the safe character count.
        return True  # The caller can report that the input waits.

    def release(self) -> None:
        """Release queued input after the first terminal output."""
        logger.info("Releasing terminal input queue")  # Log before sending queued input.
        with self._lock:  # Release and later submits share one send order.
            if self._closed:  # Ended sessions drop queued input.
                logger.debug("Skipped terminal input release because queue is closed")  # Log the safe state.
                return  # A closed queue sends nothing.
            if self._ready:  # Release is safe to call more than once.
                logger.debug("Skipped terminal input release because queue is ready")  # Log the safe state.
                return  # The queue already flushed.
            self._ready = True  # Later submit calls send at once.
            pending = list(self._pending)  # Copy the queue while holding the order lock.
            self._pending.clear()  # Drop queued text after copying it.
            for item in pending:  # Preserve the order of early input.
                self._send_locked(item)  # Send each queued text with the same lock held.
        logger.debug("Released terminal input queue count=%s", len(pending))  # Log only the queued count.

    def close(self) -> None:
        """Close the input queue and drop queued text."""
        logger.info("Closing terminal input queue")  # Log before the state change.
        with self._lock:  # Close must not race with submit.
            self._closed = True  # Later submit calls fail.
            self._pending.clear()  # Early input cannot be sent after close.
        logger.debug("Closed terminal input queue")  # Log after the state change.

    def check_rate(self) -> None:
        """Count one request and refuse requests beyond the rate cap.

        Raises:
            StreamRequestError: More than 60 requests arrived in one second.
        """
        now = self._clock()  # Use one clock value for the sliding window.
        logger.debug("Checking terminal input rate")  # Debug level avoids noisy route logs.
        with self._lock:  # The rate window is shared by input and resize.
            while self._times and now - self._times[0] >= 1.0:  # Drop requests outside the newest second.
                self._times.popleft()  # Remove the oldest request time.
            if len(self._times) >= self.RATE_LIMIT:  # The next request would exceed the cap.
                raise StreamRequestError("rate_limited", "The terminal request rate is too high.")  # Contract error.
            self._times.append(now)  # Count the accepted request.
        logger.debug("Checked terminal input rate count=%s", len(self._times))  # Log the safe count.

    def _ensure_open(self) -> None:
        """Refuse input when the queue is closed.

        Raises:
            StreamRequestError: The queue is closed.
        """
        if self._closed:  # The session has ended.
            raise StreamRequestError("not_open", "The terminal session is not open.")  # Contract error.

    def _send_locked(self, text: str) -> None:
        """Send text while the caller holds the queue lock.

        Args:
            text: The exact text that the device must receive.

        Raises:
            StreamRequestError: No sender is bound.
        """
        if self._sender is None:  # A shell runner must bind the sender before release.
            raise StreamRequestError("not_open", "The terminal input sender is not ready.")  # Contract error.
        self._sender(text)  # Send exact text without logging it.


__all__ = ["TerminalInput"]  # Export the shared terminal input interface.
