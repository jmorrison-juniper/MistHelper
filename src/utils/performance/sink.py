"""A bounded sink that never changes the result of a measured operation.

The sink holds a fixed number of events. It drops the oldest event when the
queue is full, and it counts every drop. A sink failure opens a circuit, so a
broken writer cannot raise inside the application path.
"""
from __future__ import annotations

import json
import logging
import threading
from collections import deque
from pathlib import Path
from typing import Final

from src.utils.performance.event import PerformanceEvent

log = logging.getLogger(__name__)

DEFAULT_CAPACITY: Final = 2_048  # The queue holds this many events before it drops one.
MAX_EVENT_BYTES: Final = 4_096  # A larger encoded event is a defect, so the sink drops it.
FAILURE_LIMIT: Final = 5  # This many write failures open the circuit.


class BoundedSink:
    """Collect events in memory and write them as JSON Lines on request."""

    __slots__ = ("_queue", "_lock", "_dropped", "_failures", "_open_circuit")

    def __init__(self, capacity: int = DEFAULT_CAPACITY) -> None:
        self._queue: deque[PerformanceEvent] = deque(maxlen=max(1, capacity))  # Bound memory.
        self._lock = threading.Lock()  # Guard the queue, because requests share the sink.
        self._dropped = 0  # Count every event the sink refused or evicted.
        self._failures = 0  # Count write failures, to decide when to open the circuit.
        self._open_circuit = False  # An open circuit stops every later write attempt.

    def emit(self, event: PerformanceEvent) -> bool:
        """Add one event. Return False when the sink refused it.

        The method never encodes the event. The contract already bounds the
        label count, the value length, and the measurement count, so the
        encoded size is bounded by construction. Encoding at flush time keeps
        that cost out of the measured application path.
        """
        if self._open_circuit:  # Stop at once when an earlier write failed too often.
            self._count_drop()  # Record the refusal, so the loss stays visible.
            return False  # Never raise, because the caller is inside a measured path.
        return self._append(event)  # Append under the lock and report the outcome.

    def _append(self, event: PerformanceEvent) -> bool:
        """Append one event and report whether it evicted an older event."""
        with self._lock:  # Hold the lock only for the append.
            evicted = len(self._queue) == self._queue.maxlen  # A full queue drops the oldest.
            self._queue.append(event)  # The deque removes the oldest event on its own.
            if evicted:  # Count the eviction, so the report can state the loss.
                self._dropped += 1  # One older event left the queue unread.
        return True  # The sink accepted the new event.

    def _encode(self, event: PerformanceEvent) -> str | None:
        """Return the JSON line for an event, or None when it is unusable."""
        try:  # Guard the encode, because a sink must not raise into the caller.
            line = json.dumps(event.to_dict(), separators=(",", ":"), sort_keys=True)
        except (TypeError, ValueError):  # The record held a value json cannot write.
            self._count_drop()  # Record the loss rather than propagate the error.
            return None  # Tell the caller that this event is gone.
        if len(line) > MAX_EVENT_BYTES:  # Refuse an event that breaks the size bound.
            self._count_drop()  # Record the loss, because an oversized event is a defect.
            return None  # Tell the caller that this event is gone.
        return line  # The line is bounded and valid.

    def _count_drop(self) -> None:
        """Increase the drop counter under the lock."""
        with self._lock:  # Guard the counter, because threads share it.
            self._dropped += 1  # One event never reached the queue.

    def drain(self) -> list[str]:
        """Remove every queued event and return it as a JSON line."""
        with self._lock:  # Hold the lock while the queue changes.
            events = list(self._queue)  # Copy the queued events for the caller.
            self._queue.clear()  # Empty the queue, so a later flush cannot repeat a line.
        lines: list[str] = []  # Collect the encoded lines outside the lock.
        for event in events:  # Encode one event at a time, off the measured path.
            line = self._encode(event)  # The encode step counts its own drops.
            if line is not None:  # Keep only the events that encoded inside the bound.
                lines.append(line)  # Add the bounded JSON line.
        return lines  # Return the lines the caller must persist.

    def flush_to(self, path: Path) -> int:
        """Append every queued line to a file. Return the written line count."""
        if self._open_circuit:  # Refuse the write while the circuit stays open.
            log.warning("performance sink circuit open, skipping flush")
            return 0  # Report that nothing reached the file.
        lines = self.drain()  # Take the queued lines before touching the file.
        if not lines:  # Skip the file work when the queue held nothing.
            return 0  # Report an empty flush.
        return self._write_lines(path, lines)  # Persist the lines and report the count.

    def _write_lines(self, path: Path, lines: list[str]) -> int:
        """Append lines to the file and manage the failure circuit."""
        log.info("performance sink flush starting lines=%d", len(lines))
        try:  # Guard the file work, because a sink must not raise into the caller.
            path.parent.mkdir(parents=True, exist_ok=True)  # Create the directory once.
            with path.open("a", encoding="utf-8") as handle:  # Append, never truncate.
                handle.write("\n".join(lines) + "\n")  # One write call for the whole batch.
        except OSError:  # The file system refused the write.
            self._record_failure(len(lines))  # Count the failure and the lost lines.
            return 0  # Report that nothing reached the file.
        log.debug("performance sink flush complete lines=%d", len(lines))
        return len(lines)  # Report the number of persisted lines.

    def _record_failure(self, lost: int) -> None:
        """Count a write failure and open the circuit at the limit."""
        with self._lock:  # Guard both counters together.
            self._failures += 1  # One more failed write attempt.
            self._dropped += lost  # The drained lines never reached the file.
            self._open_circuit = self._failures >= FAILURE_LIMIT  # Stop after the limit.
        log.warning("performance sink write failed failures=%d lost=%d", self._failures, lost)

    @property
    def dropped(self) -> int:
        """Return the number of events the sink lost."""
        with self._lock:  # Read under the lock, because threads update the counter.
            return self._dropped  # Report the loss so a report can state it.

    @property
    def circuit_open(self) -> bool:
        """Return True when repeated failures stopped the sink."""
        return self._open_circuit  # A plain read, because one bool assignment is atomic.
