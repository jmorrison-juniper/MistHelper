"""The public surface of the performance monitoring package.

Import the recorder, the span, and the event source from this module. The
default recorder stays off, so an import alone never adds a measurement cost.
"""

from __future__ import annotations  # Keep public imports lazy for type annotations.

from src.utils.performance.event import EventError, EventSource, PerformanceEvent  # Export event contract types.
from src.utils.performance.privacy import PerformancePrivacyPolicy  # Export the deny-by-default privacy policy.
from src.utils.performance.recorder import (  # Export recorder entry points and clock records.
    NULL_SPAN,
    Elapsed,
    Recorder,
    RecorderSettings,
    Span,
    Stopwatch,
)
from src.utils.performance.sink import BoundedSink  # Export the bounded queue and JSON Lines sink.

__all__ = [
    "NULL_SPAN",  # The shared span a forbidden family returns.
    "BoundedSink",  # The bounded queue and the JSON Lines writer.
    "Elapsed",  # The measured wall and CPU cost of one boundary.
    "EventError",  # The error a contract violation raises.
    "EventSource",  # The source area and symbol that produced an event.
    "PerformanceEvent",  # The bounded wire record.
    "PerformancePrivacyPolicy",  # The privacy filter and bucket helper class.
    "Recorder",  # The gate that decides which events survive.
    "RecorderSettings",  # The level, the sample rate, and the queue bound.
    "Span",  # The context manager that measures one boundary.
    "Stopwatch",  # The nanosecond clocks.
]  # Define the public import surface for src.utils.performance.
