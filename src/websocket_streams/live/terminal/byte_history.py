"""Keep terminal output bytes for issue #3671.

Why:
    Issue #3671 adds a browser terminal that reads raw output bytes by
    position. The history must let the page continue after a network break,
    and it must report when old bytes are no longer available.
"""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import logging  # The history logs state changes without output bytes.
import threading  # Reader threads and web threads share one history.
from dataclasses import dataclass  # The read answer is a small immutable value.

from src.websocket_streams.intake.fields import StreamRequestError  # Contract refusals use shared codes.

logger = logging.getLogger(__name__)  # Keep terminal history logs under this module.


@dataclass(frozen=True, slots=True)
class HistoryRead:
    """One bounded read from a terminal byte history.

    Attributes:
        data: The bytes after the requested position.
        first: The absolute position of the oldest kept byte.
        next_position: The position for the next read.
        gap: The count of bytes that are no longer available.
        closed: True when the terminal session ended.
    """

    data: bytes  # The answer holds at most one route payload.
    first: int  # The browser uses this to detect retained history.
    next_position: int  # The browser sends this value in the next read.
    gap: int  # The browser shows a notice for lost bytes.
    closed: bool  # Waiting reads return at once after close.


class ByteHistory:
    """A thread-safe history of the newest terminal output bytes."""

    READ_LIMIT = 512 * 1024  # The HTTP answer holds at most 512 KiB.

    def __init__(self, limit: int = 1_048_576) -> None:
        """Build an empty byte history.

        Args:
            limit: The largest count of output bytes to retain.
        """
        self.limit = limit  # The caller passes the configured byte cap.
        self._data = bytearray()  # A bytearray trims old bytes efficiently enough for the cap.
        self._first = 0  # Absolute position of the first retained byte.
        self._next = 0  # Absolute position after the newest byte.
        self._closed = False  # Close wakes waiters and marks the final read.
        self._condition = threading.Condition()  # Readers wait for append or close.

    def append(self, data: bytes) -> None:
        """Append output bytes and wake waiting reads.

        Args:
            data: The raw terminal output bytes.
        """
        if not data:  # Empty output changes no cursor.
            return  # Avoid a wake with no new data.
        logger.debug("Appending terminal output bytes length=%s", len(data))  # Debug level: output comes often.
        with self._condition:  # The data and cursors must change together.
            if self._closed:  # Ended histories ignore late output.
                logger.debug("Ignored terminal output because history is closed")  # Log the safe state.
                return  # A late runner callback cannot reopen history.
            self._data.extend(data)  # Keep the raw bytes for future reads.
            self._next += len(data)  # Move the absolute end position.
            self._trim()  # Drop the oldest bytes when the cap is exceeded.
            self._condition.notify_all()  # Wake each pending long poll.
        logger.debug("Appended terminal output bytes length=%s", len(data))  # Log only the safe byte count.

    def read(self, after: int, wait_seconds: float = 0.0) -> HistoryRead:
        """Read bytes after one absolute position.

        Args:
            after: The absolute position already held by the caller.
            wait_seconds: The maximum time to wait for new bytes.

        Returns:
            The bytes, cursors, gap, and closed state.

        Raises:
            StreamRequestError: The requested position is outside the valid range.
        """
        if after < 0:  # Negative positions are not meaningful.
            raise StreamRequestError("bad_request", "The terminal read position is not valid.")  # Contract error.
        if wait_seconds < 0.0:  # Negative waits are invalid.
            raise StreamRequestError("bad_request", "The terminal wait time is not valid.")  # Contract error.
        logger.debug("Reading terminal history after=%s wait=%s", after, wait_seconds)  # Log cursors only.
        with self._condition:  # The read snapshot must match the cursors.
            if after > self._next:  # A future cursor means the client state is wrong.
                raise StreamRequestError("bad_request", "The terminal read position is not valid.")  # Contract error.
            if self._must_wait(after, wait_seconds):  # No bytes are ready yet.
                self._condition.wait(timeout=wait_seconds)  # Bound the web thread wait.
            if after > self._next:  # A concurrent trim cannot make a future cursor valid.
                raise StreamRequestError("bad_request", "The terminal read position is not valid.")  # Contract error.
            result = self._snapshot(after)  # Build a bounded read answer.
        logger.debug("Read terminal history bytes length=%s", len(result.data))  # Log only the answer size.
        return result  # The gateway adds session metadata.

    def close(self) -> None:
        """Close the history and wake every waiting read."""
        logger.info("Closing terminal byte history")  # Log before waking readers.
        with self._condition:  # Close and wake must be atomic.
            self._closed = True  # Future reads report the closed state.
            self._condition.notify_all()  # Each waiting long poll returns at once.
        logger.debug("Closed terminal byte history")  # Log after wakeup.

    def _trim(self) -> None:
        """Trim old bytes until the history is within its cap."""
        extra = len(self._data) - self.limit  # Positive extra bytes exceed the cap.
        if extra <= 0:  # The history still fits.
            return  # No cursor change is needed.
        del self._data[:extra]  # Remove the oldest retained bytes.
        self._first += extra  # Move the first retained absolute position.

    def _must_wait(self, after: int, wait_seconds: float) -> bool:
        """Return whether a read should wait for new bytes.

        Args:
            after: The requested absolute position.
            wait_seconds: The requested wait time.

        Returns:
            True when no bytes or gap can be returned yet.
        """
        return wait_seconds > 0.0 and after == self._next and not self._closed  # Wait only at the live end.

    def _snapshot(self, after: int) -> HistoryRead:
        """Build one bounded read result under the condition lock.

        Args:
            after: The requested absolute position.

        Returns:
            The bounded read result.
        """
        start = max(after, self._first)  # Reads before retained data start at the first kept byte.
        offset = start - self._first  # The bytearray offset matches the absolute start.
        limit = min(len(self._data), offset + self.READ_LIMIT)  # One answer holds at most 512 KiB.
        chunk = bytes(self._data[offset:limit])  # Copy the bytes for the caller.
        next_position = start + len(chunk)  # The next cursor follows the returned bytes.
        gap = max(0, self._first - after)  # Report only lost bytes before the first kept byte.
        return HistoryRead(chunk, self._first, next_position, gap, self._closed)  # Return an immutable snapshot.


__all__ = ["ByteHistory", "HistoryRead"]  # Export the shared terminal history interface.
