"""The public surface of the performance monitoring package.

Import the recorder, the span, and the event source from this module. The
default recorder stays off, so an import alone never adds a measurement cost.
"""

from __future__ import annotations

from src.utils.performance.clock import Elapsed, Stopwatch
from src.utils.performance.event import EventError, EventSource, PerformanceEvent
from src.utils.performance.privacy import bucket_size, status_class
from src.utils.performance.recorder import NULL_SPAN, Recorder, RecorderSettings, Span
from src.utils.performance.sink import BoundedSink

__all__ = [
    "NULL_SPAN",  # The shared span a forbidden family returns.
    "BoundedSink",  # The bounded queue and the JSON Lines writer.
    "Elapsed",  # The measured wall and CPU cost of one boundary.
    "EventError",  # The error a contract violation raises.
    "EventSource",  # The file, symbol, and class that produced an event.
    "PerformanceEvent",  # The bounded wire record.
    "Recorder",  # The gate that decides which events survive.
    "RecorderSettings",  # The level, the sample rate, and the queue bound.
    "Span",  # The context manager that measures one boundary.
    "Stopwatch",  # The nanosecond clocks.
    "bucket_size",  # The fixed bucket name for an item count.
    "status_class",  # The status family for an HTTP code.
]
