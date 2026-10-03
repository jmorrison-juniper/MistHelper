"""Keep bounded terminal output bytes for issue #3671."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import logging  # Structured events use standard logging levels.
import threading  # Reader threads and web threads share one history.
from dataclasses import dataclass  # Read answers use an immutable value.

from src.websocket_streams.intake.fields.error import StreamRequestError  # Contract refusals use shared codes.
from src.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)  # Use the shared bounded logger from T072.

logger = StructuredTransportLogger(logging.getLogger(__name__))  # Apply the shared logging boundary.


@dataclass(frozen=True, slots=True)
class HistoryRead:
    """Hold one bounded terminal history read."""

    data: bytes  # The answer holds at most one route payload.
    first: int  # The browser uses this to detect retained history.
    next_position: int  # The browser sends this value in the next read.
    gap: int  # The browser shows a notice for lost bytes.
    closed: bool  # Waiting reads return at once after close.


class RetainedByteStore:
    """Store retained bytes and absolute cursor positions."""

    READ_LIMIT = 512 * 1024  # One HTTP answer holds at most 512 KiB.

    def __init__(self, limit: int) -> None:
        """Build an empty retained byte store."""
        self._limit = limit  # The caller controls the retained byte cap.
        self._data = bytearray()  # The mutable buffer supports prefix trimming.
        self.first = 0  # The first retained absolute position starts at zero.
        self.next = 0  # The next absolute position starts at zero.

    def append(self, data: bytes) -> int:
        """Append bytes and return the dropped byte count."""
        self._data.extend(data)  # Keep the new bytes in exact order.
        self.next += len(data)  # Advance the absolute end position.
        dropped = max(0, len(self._data) - self._limit)  # Measure bytes beyond the cap.
        if dropped:  # Trim only when the retained data exceeds the cap.
            del self._data[:dropped]  # Remove the oldest retained bytes.
            self.first += dropped  # Advance the first retained position.
        return dropped  # The caller logs the bounded trim count.

    def validate(self, after: int) -> None:
        """Refuse a position after the current history end."""
        if after > self.next:  # A future cursor means the client state is invalid.
            raise StreamRequestError("bad_request", "The terminal read position is not valid.")  # Refuse it.

    def snapshot(self, after: int, closed: bool) -> HistoryRead:
        """Build one bounded read from the retained bytes."""
        start = max(after, self.first)  # Start at the oldest available byte.
        offset = start - self.first  # Convert the absolute position to a buffer offset.
        end = min(len(self._data), offset + self.READ_LIMIT)  # Bound one route payload.
        chunk = bytes(self._data[offset:end])  # Copy bytes so later appends cannot change the answer.
        next_position = start + len(chunk)  # Place the next cursor after returned bytes.
        gap = max(0, self.first - after)  # Report bytes that the history no longer holds.
        return HistoryRead(chunk, self.first, next_position, gap, closed)  # Return one immutable answer.


class ByteHistory:
    """Coordinate synchronized terminal history reads and writes."""

    def __init__(self, limit: int = 1_048_576) -> None:
        """Build an empty byte history."""
        self._store = RetainedByteStore(limit)  # Delegate byte retention to one named store.
        self._closed = False  # Close wakes waiters and marks final reads.
        self._condition = threading.Condition()  # Readers wait for append or close.

    def append(self, data: bytes) -> None:
        """Append output bytes and wake waiting reads."""
        if not data:  # Empty output changes no cursor.
            return  # Avoid a wake with no new data.
        logger.emit(logging.DEBUG, "terminal_history_append_start", {"byte_count": len(data)})  # Log safely.
        with self._condition:  # Bytes and cursors must change together.
            if self._closed:  # Ended histories ignore late runner output.
                logger.emit(logging.DEBUG, "terminal_history_append_skipped", {"status": "closed"})  # Log state.
                return  # A late callback cannot reopen the history.
            dropped = self._store.append(data)  # Retain the newest bytes under the shared lock.
            self._condition.notify_all()  # Wake each pending long poll.
        fields = {"byte_count": len(data), "dropped": dropped}  # Use bounded operational fields only.
        logger.emit(logging.DEBUG, "terminal_history_append_complete", fields)  # Record the safe result.

    def read(self, after: int, wait_seconds: float = 0.0) -> HistoryRead:
        """Read bytes after one absolute position."""
        if after < 0:  # Negative positions are not meaningful.
            raise StreamRequestError("bad_request", "The terminal read position is not valid.")  # Refuse it.
        if wait_seconds < 0.0:  # Negative waits are invalid.
            raise StreamRequestError("bad_request", "The terminal wait time is not valid.")  # Refuse it.
        fields = {"count": after, "timeout_seconds": wait_seconds}  # Log bounded cursor and wait values.
        logger.emit(logging.DEBUG, "terminal_history_read_start", fields)  # Log before the synchronized read.
        with self._condition:  # The read snapshot must match the cursor state.
            self._store.validate(after)  # Refuse a future cursor before any wait.
            if self._must_wait(after, wait_seconds):  # Wait only at the live end.
                self._condition.wait(timeout=wait_seconds)  # Bound the web thread wait.
            self._store.validate(after)  # Recheck after the wait before making the snapshot.
            result = self._store.snapshot(after, self._closed)  # Copy one bounded answer.
        logger.emit(logging.DEBUG, "terminal_history_read_complete", {"byte_count": len(result.data)})  # Log size.
        return result  # The gateway adds session metadata.

    def close(self) -> None:
        """Close the history and wake all waiting reads."""
        logger.emit(logging.INFO, "terminal_history_close_start")  # Log before the state change.
        with self._condition:  # Close and wake must be atomic.
            self._closed = True  # Future reads report the closed state.
            self._condition.notify_all()  # Each waiting long poll returns at once.
        logger.emit(logging.DEBUG, "terminal_history_close_complete", {"status": "closed"})  # Log the result.

    def _must_wait(self, after: int, wait_seconds: float) -> bool:
        """Return whether the read must wait for new bytes."""
        return wait_seconds > 0.0 and after == self._store.next and not self._closed  # Wait only at the live end.
