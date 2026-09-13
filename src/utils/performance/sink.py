"""A bounded sink that never changes the result of a measured operation.

The sink holds a fixed count and a fixed approximate byte budget. It drops the
oldest event when either limit needs space, and it counts every drop. A sink
failure opens a circuit, so a broken writer cannot raise inside the application
path.
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
DEFAULT_MAX_BYTES: Final = 4 * 1_024 * 1_024  # The queue keeps worst case events near four MB.
MAX_EVENT_BYTES: Final = 4_096  # A larger encoded event is a defect, so the sink drops it.
FAILURE_LIMIT: Final = 5  # This many write failures open the circuit.
_EVENT_BASE_BYTES: Final = 512  # The fixed part covers the event, source, and timestamp fields.
_DIMENSION_BASE_BYTES: Final = 80  # One label dict entry costs about this much before text.
_MEASUREMENT_BASE_BYTES: Final = 80  # One measurement dict entry costs about this much.
_TEXT_FACTOR_BYTES: Final = 2  # Python stores many strings near two bytes per character.


class QueuedEvent:
    """Hold one event with its cheap byte estimate."""

    __slots__ = ("event", "estimated_bytes")

    def __init__(self, event: PerformanceEvent, estimated_bytes: int) -> None:
        """Bind the event to the estimate used by the queue."""
        self.event = event  # Keep the record that a later drain encodes.
        self.estimated_bytes = estimated_bytes  # Keep the charge so eviction stays cheap.


class BoundedSink:
    """Collect events in memory and write them as JSON Lines on request."""

    __slots__ = (  # Keep instances small, because one recorder owns one sink.
        "_queue",
        "_lock",
        "_dropped",
        "_failures",
        "_open_circuit",
        "_max_bytes",
        "_queued_bytes",
        "_capacity",
    )

    def __init__(self, capacity: int = DEFAULT_CAPACITY, max_bytes: int = DEFAULT_MAX_BYTES) -> None:
        """Build the bounded queue, the lock, and the failure counters.

        Why:
            Several requests share one sink, so the queue needs a lock. The
            queue also needs count and byte limits, because one large event can
            cost much more memory than one small event.

        Args:
            capacity: The largest number of events the queue holds.
            max_bytes: The largest estimated bytes the queue holds.
        """
        self._queue: deque[QueuedEvent] = deque()  # Store estimates beside records for eviction.
        self._lock = threading.Lock()  # Guard the queue, because requests share the sink.
        self._dropped = 0  # Count every event the sink refused or evicted.
        self._failures = 0  # Count write failures, to decide when to open the circuit.
        self._open_circuit = False  # An open circuit stops every later write attempt.
        self._max_bytes = max(1, max_bytes)  # Keep a positive byte limit for comparisons.
        self._queued_bytes = 0  # Track the charged bytes without scanning the queue.
        self._capacity = max(1, capacity)  # Keep a positive entry limit for comparisons.

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
        estimated_bytes = self._estimate_bytes(event)  # Charge the event with a cheap estimate.
        if estimated_bytes > self._max_bytes:  # Refuse an event that can never fit the byte budget.
            self._count_drop()  # Count the refused event, because the sink lost it.
            return False  # Report refusal without raising into the measured path.
        return self._append(event, estimated_bytes)  # Append under the lock and report the outcome.

    def _append(self, event: PerformanceEvent, estimated_bytes: int) -> bool:
        """Append one event and report whether it evicted an older event."""
        with self._lock:  # Hold the lock only for the append.
            self._make_room(estimated_bytes)  # Evict old events until both limits permit append.
            self._queue.append(QueuedEvent(event, estimated_bytes))  # Keep the event and the charge.
            self._queued_bytes += estimated_bytes  # Update the running byte charge.
        return True  # The sink accepted the new event.

    def _make_room(self, estimated_bytes: int) -> None:
        """Evict old events until the new event fits both bounds."""
        while self._queue and self._entry_limit_hit():  # Remove old records when the entry limit wins.
            self._evict_oldest()  # Count the eviction and subtract its byte charge.
        while self._queue and self._byte_limit_hit(estimated_bytes):  # Remove old records for byte space.
            self._evict_oldest()  # Count the eviction and subtract its byte charge.

    def _entry_limit_hit(self) -> bool:
        """Return True when the next append would exceed the entry bound."""
        return len(self._queue) >= self._capacity  # Compare before append, so the new event fits.

    def _byte_limit_hit(self, estimated_bytes: int) -> bool:
        """Return True when the next append would exceed the byte bound."""
        return self._queued_bytes + estimated_bytes > self._max_bytes  # Use the running charge only.

    def _evict_oldest(self) -> None:
        """Remove one old event and update the counters."""
        queued = self._queue.popleft()  # Drop the oldest event, matching the former deque policy.
        self._queued_bytes -= queued.estimated_bytes  # Keep the charge in step with the queue.
        self._dropped += 1  # Count byte and entry evictions the same way.

    def _estimate_bytes(self, event: PerformanceEvent) -> int:
        """Return a cheap estimate of retained bytes for one event."""
        total = _EVENT_BASE_BYTES  # Start with the fixed event and source charge.
        total += self._mapping_text_bytes(event.dimensions, _DIMENSION_BASE_BYTES)  # Charge labels.
        total += self._mapping_text_bytes(event.measurements, _MEASUREMENT_BASE_BYTES)  # Charge counters.
        total += _TEXT_FACTOR_BYTES * len(event.monitor_type)  # Charge the monitor text.
        total += _TEXT_FACTOR_BYTES * len(event.event_type)  # Charge the family text.
        return total  # Return an approximate charge, not an exact object graph size.

    def _mapping_text_bytes(self, mapping: dict[str, object], entry_bytes: int) -> int:
        """Return the estimated bytes for one bounded mapping."""
        total = entry_bytes * len(mapping)  # Charge dict entries without walking object graphs.
        for key, value in mapping.items():  # Add the bounded text that the event already holds.
            total += _TEXT_FACTOR_BYTES * len(key)  # Charge the bounded key string.
            if isinstance(value, str):  # Text labels dominate the worst case event size.
                total += _TEXT_FACTOR_BYTES * len(value)  # Charge the bounded value string.
        return total  # Return the cheap mapping charge.

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
            self._queued_bytes = 0  # Reset the byte charge with the queue.
        lines: list[str] = []  # Collect the encoded lines outside the lock.
        for queued in events:  # Encode one event at a time, off the measured path.
            line = self._encode(queued.event)  # The encode step counts its own drops.
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

    @property
    def queued_bytes(self) -> int:
        """Return the current estimated bytes in the queue."""
        with self._lock:  # Read under the lock, because emit updates the charge.
            return self._queued_bytes  # Report the approximate retained byte charge.

    @property
    def queued_count(self) -> int:
        """Return the current number of events in the queue."""
        with self._lock:  # Read under the lock, because emit updates the queue.
            return len(self._queue)  # Report the retained event count without draining.

    @property
    def max_bytes(self) -> int:
        """Return the configured approximate byte bound."""
        return self._max_bytes  # Report the byte bound for tests and reports.
