"""The bounded performance event and its validation rules.

The record matches `specs/2448-misthelper-performance-monitoring/contracts/
performance-event.schema.json`. The `source` block names the file, the symbol,
and the class, which gives per-file, per-function, and per-class attribution.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from functools import lru_cache
from typing import Any, Final

from src.utils.performance.privacy import PerformancePrivacyPolicy  # Scrub source labels before JSON storage.

SCHEMA_VERSION: Final = "1.0.0"  # The single contract version this build emits.
DIMENSION_KEY_RE: Final = re.compile(r"^[a-z][a-z0-9_]{0,47}$")  # Bounded label key.
MEASUREMENT_KEY_RE: Final = re.compile(r"^[a-z][a-z0-9_.]{0,63}$")  # Bounded measurement key.
RUN_ID_RE: Final = re.compile(r"^[A-Za-z0-9_-]{8,64}$")  # The correlation identifier shape.

EVENT_TYPES: Final = frozenset(
    {"operation", "http", "database", "file", "serialization", "cache", "startup", "diagnostic"}
)  # The eight event families the contract allows.
STATUS_VALUES: Final = frozenset({"ok", "error", "cancelled", "timeout"})  # Closed outcomes.

MAX_DIMENSIONS: Final = 16  # The schema rejects a seventeenth label.
MAX_MEASUREMENTS: Final = 32  # The schema rejects a thirty-third measurement.
MAX_DIMENSION_VALUE: Final = 96  # A longer value suggests raw user data.
MAX_MONITOR_TYPE: Final = 64  # The monitor name stays short and bounded.


class EventError(ValueError):
    """Raised when a caller builds an event that breaks the contract."""


def _require(condition: bool, message: str) -> None:
    """Raise a contract error when a rule fails."""
    if not condition:  # Check the rule the caller passed in.
        raise EventError(message)  # Fail early, so no invalid event reaches a sink.


# The hook catalog fixes every key, so the key cardinality cannot grow with the
# traffic. A bounded cache therefore removes a repeated match from the hot path.
@lru_cache(maxsize=256)
def _dimension_key_ok(key: str) -> bool:
    """Return True when the label key matches the bounded pattern."""
    return bool(DIMENSION_KEY_RE.fullmatch(key))  # One match for each distinct key.


@lru_cache(maxsize=512)
def _measurement_key_ok(key: str) -> bool:
    """Return True when the measurement key matches the bounded pattern."""
    return bool(MEASUREMENT_KEY_RE.fullmatch(key))  # One match for each distinct key.


@dataclass(frozen=True, slots=True)
class EventSource:
    """Name the exact code location that produced an event."""

    file: str  # The repository path of the measured module.
    symbol: str  # The function or method name inside that module.
    class_name: str | None = None  # The owning class, when the symbol is a method.

    def __post_init__(self) -> None:
        """Check that the location names a real file and symbol."""
        _require(bool(self.file), "source file cannot be empty")
        _require(bool(self.symbol), "source symbol cannot be empty")

    def to_dict(self) -> dict[str, Any]:
        """Return the source block the schema expects."""
        return {
            "file": PerformancePrivacyPolicy.scrub_source_label(self.file),  # Store a source area, never a raw path.
            "symbol": PerformancePrivacyPolicy.scrub_value(self.symbol),  # Store only a bounded symbol label.
            "class": None if self.class_name is None else PerformancePrivacyPolicy.scrub_value(self.class_name),
        }  # The schema allows a null class and safe source labels.


@dataclass(frozen=True, slots=True)
class PerformanceEvent:
    """One measured boundary, ready for a sink."""

    event_type: str  # The family this boundary belongs to.
    monitor_type: str  # The monitor name from the hook catalog.
    source: EventSource  # The file, symbol, and class that produced the event.
    status: str  # The closed outcome value for the boundary.
    measurements: dict[str, float] = field(default_factory=dict)  # Bounded counters.
    dimensions: dict[str, Any] = field(default_factory=dict)  # Bounded labels.
    sample_rate: float = 1.0  # The share of events this hook kept.
    run_id: str | None = None  # The correlation identifier for one run.
    timestamp_ns: int = 0  # The event time as an integer, formatted only at output.

    def __post_init__(self) -> None:
        """Validate every field, because a sink must never repair a record."""
        self._check_identity()  # Check the family, the monitor, and the outcome.
        self._check_sampling()  # Check the share and the correlation identifier.
        _validate_dimensions(self.dimensions)  # Check the label count, keys, and values.
        _validate_measurements(self.measurements)  # Check the measurement count and keys.
        if not self.timestamp_ns:  # Read the wall clock only when the caller left it empty.
            object.__setattr__(self, "timestamp_ns", time.time_ns())  # Frozen record.

    def _check_identity(self) -> None:
        """Check the event family, the monitor name, and the outcome."""
        _require(self.event_type in EVENT_TYPES, "invalid event_type")
        _require(bool(self.monitor_type), "monitor_type cannot be empty")
        _require(len(self.monitor_type) <= MAX_MONITOR_TYPE, "monitor_type too long")
        _require(self.status in STATUS_VALUES, "invalid status")

    def _check_sampling(self) -> None:
        """Check the sample share and the optional correlation identifier."""
        _require(0 < self.sample_rate <= 1, "sample_rate must be above 0 and at most 1")
        no_run_id = self.run_id is None  # The identifier is optional in the contract.
        _require(no_run_id or bool(RUN_ID_RE.fullmatch(str(self.run_id))), "invalid run_id")

    def to_dict(self) -> dict[str, Any]:
        """Return the wire record that matches the JSON Schema."""
        record: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,  # Pin the contract version on every event.
            "event_type": self.event_type,  # Carry the event family.
            "timestamp_utc": _format_time(self.timestamp_ns),  # Format at output time only.
            "monitor_type": self.monitor_type,  # Carry the catalog monitor name.
            "source": self.source.to_dict(),  # Carry the file, symbol, and class.
            "status": self.status,  # Carry the closed outcome value.
            "sample_rate": self.sample_rate,  # State the share this hook kept.
            "dimensions": dict(self.dimensions),  # Copy, so a later mutation cannot leak.
            "measurements": dict(self.measurements),  # Copy, for the same reason.
        }
        if self.run_id is not None:  # Add the correlation identifier when the run set one.
            record["run_id"] = self.run_id  # The schema marks this field optional.
        return record


def _validate_dimensions(dimensions: dict[str, Any]) -> None:
    """Check the label count, each key pattern, and each value."""
    _require(len(dimensions) <= MAX_DIMENSIONS, "too many dimensions")
    for key, value in dimensions.items():  # Check one label at a time.
        _require(_dimension_key_ok(key), f"invalid dimension key: {key}")
        _require(
            isinstance(value, (str, int, float, bool)) or value is None,
            f"unsupported dimension value: {key}",
        )
        if isinstance(value, str):  # A text value also carries a length bound.
            _require(len(value) <= MAX_DIMENSION_VALUE, f"dimension value too long: {key}")


def _validate_measurements(measurements: dict[str, float]) -> None:
    """Check the measurement count, each key pattern, and each value."""
    _require(bool(measurements), "an event carries at least one measurement")
    _require(len(measurements) <= MAX_MEASUREMENTS, "too many measurements")
    for key, value in measurements.items():  # Check one measurement at a time.
        _require(_measurement_key_ok(key), f"invalid measurement key: {key}")
        _require(
            isinstance(value, (int, float)) and not isinstance(value, bool),
            f"not a number: {key}",
        )
        _require(value >= 0, f"measurement cannot be negative: {key}")


def _format_time(timestamp_ns: int) -> str:
    """Return a UTC timestamp in the format the schema expects."""
    seconds = timestamp_ns / 1_000_000_000  # Convert the integer to fractional seconds.
    moment = datetime.fromtimestamp(seconds, UTC)  # Build the aware UTC value.
    return moment.isoformat(timespec="microseconds").replace("+00:00", "Z")
