"""The recorder that gates, measures, and emits a performance event.

The recorder stays off by default. One setting selects the level. A level
decides which event families may emit. A sample rate limits the successful
high-frequency events, and the recorder keeps every failure.
"""

from __future__ import annotations

import logging
import os
import random
from collections.abc import Mapping
from dataclasses import dataclass
from types import TracebackType
from typing import Any, Final, Literal

from src.utils.performance.clock import Stopwatch
from src.utils.performance.event import EventSource, PerformanceEvent
from src.utils.performance.privacy import scrub_dimensions
from src.utils.performance.sink import BoundedSink

log = logging.getLogger(__name__)

LEVELS: Final = ("off", "base", "targeted", "diagnostic")  # The ordered level names.
_LEVEL_FAMILIES: Final = {
    "off": frozenset(),  # The default level emits nothing at all.
    "base": frozenset({"operation", "http", "database", "file", "cache"}),  # Resource work.
    "targeted": frozenset(
        {"operation", "http", "database", "file", "cache", "serialization", "startup"}
    ),  # Add the measured compute and startup boundaries.
    "diagnostic": frozenset(
        {
            "operation",
            "http",
            "database",
            "file",
            "cache",
            "serialization",
            "startup",
            "diagnostic",
        }
    ),  # The diagnostic level allows every family.
}  # A family outside the selected set never reaches the sink.


@dataclass(frozen=True, slots=True)
class RecorderSettings:
    """Hold the bounded controls for the recorder."""

    level: str = "off"  # The default keeps the whole feature disabled.
    sample_rate: float = 1.0  # The share of successful events the recorder keeps.
    capacity: int = 2048  # The queue bound the sink applies.
    measure_cpu: bool = True  # Read the process CPU clock as well as the wall clock.

    def __post_init__(self) -> None:
        """Reject a level or a rate that the contract does not allow."""
        if self.level not in LEVELS:  # Guard, because a typo would silently disable a layer.
            raise ValueError(f"unknown observability level: {self.level}")
        if not 0.0 < self.sample_rate <= 1.0:  # The schema requires a share above zero.
            raise ValueError(f"sample_rate must be above 0 and at most 1: {self.sample_rate}")

    @property
    def families(self) -> frozenset[str]:
        """Return the event families this level allows."""
        return _LEVEL_FAMILIES[self.level]  # The mapping holds one entry for each level.

    @classmethod
    def from_env(cls, environment: Mapping[str, str] | None = None) -> RecorderSettings:
        """Build the settings from the process environment.

        The reader keeps the feature off when a variable is absent or invalid,
        because an operator must never enable a measurement by accident.
        """
        source = environment if environment is not None else os.environ  # Allow a test map.
        log.info("Reading the performance monitoring settings")  # Announce the read.
        settings = cls(
            level=_read_level(source),  # The level decides which families may emit.
            sample_rate=_read_rate(source),  # The share of successful events to keep.
            capacity=_read_capacity(source),  # The bound on the queued event count.
            measure_cpu=source.get("MISTHELPER_PERF_CPU", "1") not in {"0", "false", "False"},
        )
        log.debug(
            "Performance monitoring level=%s sample_rate=%s capacity=%d cpu=%s",
            settings.level,
            settings.sample_rate,
            settings.capacity,
            settings.measure_cpu,
        )  # Record the resolved values, which hold no secret.
        return settings  # Give the caller one validated settings record.


def _read_level(source: Mapping[str, str]) -> str:
    """Return the requested level, or off when the value is unknown."""
    value = source.get("MISTHELPER_PERF_LEVEL", "off").strip().lower()  # Normalize the value.
    if value not in LEVELS:  # An unknown value must not enable a measurement.
        log.warning("Unknown performance level %s, using off", value)  # Name the bad value.
        return "off"  # Fail closed, because an accidental measurement costs latency.
    return value  # The value names a known level.


def _read_rate(source: Mapping[str, str]) -> float:
    """Return the sample rate, or one when the value cannot be read."""
    try:  # Guard the conversion, because an operator can type any text.
        rate = float(source.get("MISTHELPER_PERF_SAMPLE_RATE", "1.0"))  # Read the share.
    except ValueError:  # The value was not a number.
        log.warning("Invalid performance sample rate, using 1.0")  # Report the fallback.
        return 1.0  # Keep every event rather than drop an unknown share.
    return min(1.0, max(0.000001, rate))  # Clamp above zero, which the schema requires.


def _read_capacity(source: Mapping[str, str]) -> int:
    """Return the queue bound, or the default when the value cannot be read."""
    try:  # Guard the conversion, because an operator can type any text.
        capacity = int(source.get("MISTHELPER_PERF_CAPACITY", "2048"))  # Read the bound.
    except ValueError:  # The value was not a whole number.
        log.warning("Invalid performance capacity, using 2048")  # Report the fallback.
        return 2048  # Use the documented default bound.
    return min(65536, max(1, capacity))  # Clamp, so one setting cannot exhaust the memory.


class NullSpan:
    """Stand in for a span that the level forbids.

    The object reads no clock and allocates no mapping, so a disabled hook
    costs one attribute lookup and one method call.
    """

    __slots__ = ()  # No state, so one shared instance serves every disabled hook.

    status = "ok"  # A reader sees a valid outcome without a measurement.
    sampled = False  # A disabled span never needs labels or counters.

    def label(self, key: str, value: Any) -> NullSpan:
        """Accept and discard a label, so a caller needs no branch."""
        return self  # Return self, so a caller can chain the calls.

    def count(self, key: str, value: float) -> NullSpan:
        """Accept and discard a measurement, so a caller needs no branch."""
        return self  # Return self, so a caller can chain the calls.

    def __enter__(self) -> NullSpan:
        """Start nothing, because the level forbids this family."""
        return self  # Give the caller the same handle shape a real span gives.

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> Literal[False]:
        """Record nothing and never hide an exception."""
        return False  # Return False so the original exception keeps propagating.


NULL_SPAN: Final = NullSpan()  # One shared instance, because the class holds no state.


class Span:
    """Measure one boundary and emit one event when the level allows it."""

    __slots__ = (
        "_recorder",
        "_source",
        "_family",
        "_monitor",
        "_watch",
        "_labels",
        "_counts",
        "_sampled",
        "status",
    )

    def __init__(self, recorder: Recorder, source: EventSource, family: str, monitor: str, sampled: bool) -> None:
        """Bind one span to its recorder, its source, its family, and its monitor.

        Why:
            The span holds the owner, because the owner decides whether the
            event survives the level gate and the sampler.

        Args:
            recorder: The owner that decides whether this span emits an event.
            source: The file, the symbol, and the class this span measures.
            family: The event family that the level gate reads.
            monitor: The monitor name that the hook catalog defines.
            sampled: True when the pre-sampler selected this span to keep.
        """
        self._recorder = recorder  # The owner decides whether the event may be emitted.
        self._source = source  # The file, symbol, and class this span measures.
        self._family = family  # The event family that decides the level gate.
        self._monitor = monitor  # The monitor name from the hook catalog.
        self._watch = Stopwatch(recorder.measure_cpu)  # The clocks this level asked for.
        self._labels: dict[str, Any] = {}  # Labels the caller adds during the span.
        self._counts: dict[str, float] = {}  # Counters the caller adds during the span.
        self._sampled = sampled  # Keep this success only when the pre-sampler selected it.
        self.status = "ok"  # The outcome, which the exit path overwrites on an error.

    @property
    def family(self) -> str:
        """Return the event family this span belongs to."""
        return self._family  # The recorder compares this family against the level.

    @property
    def monitor(self) -> str:
        """Return the monitor name from the hook catalog."""
        return self._monitor  # The recorder reads this name when it logs a refusal.

    @property
    def sampled(self) -> bool:
        """Return True when this span will keep a successful event."""
        return self._sampled  # The caller can skip optional labels for dropped successes.

    def label(self, key: str, value: Any) -> Span:
        """Add one label. The privacy policy checks it before the sink sees it."""
        self._labels[key] = value  # Store it now, and scrub it once at the end.
        return self  # Return self, so a caller can chain the calls.

    def count(self, key: str, value: float) -> Span:
        """Add one measurement, such as an item count or a byte count."""
        self._counts[key] = value  # Store it now, and validate it at the end.
        return self  # Return self, so a caller can chain the calls.

    def __enter__(self) -> Span:
        """Start the selected clocks."""
        self._watch.__enter__()  # Read the clocks once, at the boundary start.
        return self  # Give the caller the handle that collects the labels.

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> Literal[False]:
        """Stop the clocks, record the outcome, and hand the event to the recorder."""
        self._watch.__exit__(exc_type, exc, traceback)  # Read the clocks once.
        if exc_type is not None:  # The measured work raised, so the outcome is an error.
            self.status = "error"  # Replace the default outcome before the emit step.
            self._labels.setdefault("error_class", exc_type.__name__)  # Class name only.
        self._recorder.submit(self)  # Let the owner apply the gate and the sampling.
        return False  # Return False so the original exception keeps propagating.

    def build(self, sample_rate: float) -> PerformanceEvent:
        """Return the bounded event for this span."""
        elapsed = self._watch.elapsed  # Read the measured cost once.
        counts: dict[str, float] = dict(self._counts)  # Copy the caller measurements.
        counts["wall_ns"] = elapsed.wall_ns  # Every event carries the wall cost.
        counts["process_cpu_ns"] = elapsed.cpu_ns  # And the process CPU cost.
        return PerformanceEvent(
            event_type=self._family,  # The event family.
            monitor_type=self._monitor,  # The catalog monitor name.
            source=self._source,  # The file, symbol, and class.
            status=self.status,  # The closed outcome value.
            measurements=counts,  # The measurements, which always hold the two clocks.
            dimensions=scrub_dimensions(self._labels),  # Apply the privacy policy.
            sample_rate=sample_rate,  # State the share this hook kept.
        )


class Recorder:
    """Own the settings and the sink, and decide which events survive the gate."""

    __slots__ = ("_settings", "_sink", "_random", "_families")

    def __init__(self, settings: RecorderSettings | None = None) -> None:
        """Build the recorder from the settings, the family set, and the sink.

        Why:
            The recorder reads the family set one time, because the measured
            path runs for every span and must do no repeated work.

        Args:
            settings: The recorder settings, or None to take the defaults.
        """
        self._settings = settings or RecorderSettings()  # The default level is off.
        self._families = self._settings.families  # Read the family set once, not per span.
        self._sink = BoundedSink(capacity=self._settings.capacity)  # Bound the memory use.
        self._random = random.Random(0)  # nosec B311 - The draw thins telemetry only, never security.

    @property
    def enabled(self) -> bool:
        """Return True when the selected level allows at least one family."""
        return bool(self._families)  # An empty family set means the feature is off.

    @property
    def measure_cpu(self) -> bool:
        """Return True when this level reads the process CPU clock."""
        return self._settings.measure_cpu  # The span reads this once at its start.

    @property
    def sink(self) -> BoundedSink:
        """Return the sink, so an operator can flush or inspect the drop count."""
        return self._sink  # The caller reads the queue and the counters through it.

    def span(
        self,
        source: EventSource,
        family: str = "operation",
        monitor: str = "operation_span",
    ) -> Span | NullSpan:
        """Return a span for one boundary, or a null span when the level forbids it.

        The level check runs before the span exists. A forbidden family therefore
        reads no clock and allocates no mapping.
        """
        if family not in self._families:  # The selected level forbids this family.
            return NULL_SPAN  # The shared instance costs nothing to return.
        sampled = self._keep("ok")  # Decide successful sampling before optional labels are built.
        return Span(self, source, family, monitor, sampled)  # A measuring span.

    def submit(self, span: Span) -> bool:
        """Apply the level gate and the sampling rule, then emit the event."""
        if span.family not in self._families:  # The level forbids this family.
            return False  # Drop it before any event is built, which costs almost nothing.
        if span.status == "ok" and not span.sampled:  # The sampling rule refused this success.
            return False  # Keep every failure and thin the successes.
        return self._emit(span)  # Build the event and hand it to the sink.

    def _keep(self, status: str) -> bool:
        """Return True when the sampling rule keeps this event."""
        if status != "ok":  # Always keep a failure, because it is rare and useful.
            return True  # A failure never passes through the sampler.
        if self._settings.sample_rate >= 1.0:  # The common setting keeps every event.
            return True  # Skip the random draw, which saves work in the measured path.
        return self._random.random() < self._settings.sample_rate  # Thin the successes.

    def _emit(self, span: Span) -> bool:
        """Build the event and give it to the sink, without raising."""
        try:  # Guard the build, because validation can reject a caller mistake.
            event = span.build(self._settings.sample_rate)  # Apply the contract rules.
        except ValueError:  # The caller broke the event contract.
            log.warning("Performance event refused monitor=%s", span.monitor)  # Name only.
            return False  # Never raise into the measured application path.
        return self._sink.emit(event)  # The sink applies its own bounds.
