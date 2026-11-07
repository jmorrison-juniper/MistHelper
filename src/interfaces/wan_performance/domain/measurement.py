"""Represent validated WAN measurements with explicit UTC observation times."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from types import MappingProxyType
from typing import Literal

from src.interfaces.wan_performance.domain.identity import CircuitIdentity, GatewayIdentity, PeerPathIdentity
from src.interfaces.wan_performance.domain.metric_validation import MetricValueValidator

MeasurementIdentity = CircuitIdentity | GatewayIdentity | PeerPathIdentity  # Limit records to supported WAN entities.


@dataclass(frozen=True, slots=True)
class MetricMeasurement:
    """Represent a finite metric or an explicitly missing value."""

    value: float | int | None
    unit: str
    sample_count: int | None = None
    coverage_fraction: float | None = None
    missing_reason: str | None = None
    raw_values: tuple[float | int, ...] | None = None

    def __post_init__(self) -> None:
        """Reject invalid values before a metric enters a snapshot."""
        MetricValueValidator.unit(self.unit)  # Require readable units.
        MetricValueValidator.value(self.value, self.missing_reason)  # Keep absence explicit.
        MetricValueValidator.sample_count(self.sample_count)  # Validate the source count.
        MetricValueValidator.coverage_fraction(self.coverage_fraction)  # Validate interval coverage.
        MetricValueValidator.raw_values(self.raw_values, self.sample_count)  # Validate retained samples.

    def to_dict(self) -> dict[str, object]:
        """Return JSON-compatible metric values and metadata."""
        return {  # Keep each metric field explicit for offline consumers.
            "value": self.value,  # Preserve measured zero and absence.
            "unit": self.unit,  # Preserve the source or catalog unit.
            "sample_count": self.sample_count,  # Preserve the source count.
            "coverage_fraction": self.coverage_fraction,  # Preserve known coverage only.
            "missing_reason": self.missing_reason,  # Explain missing values.
            "raw_values": self.raw_values,  # Keep optional source samples.
        }


@dataclass(frozen=True, slots=True)
class HourlyMeasurement:
    """Represent a natural-keyed observation assigned to one UTC hour."""

    identity: MeasurementIdentity
    hour_start_utc: datetime
    collected_at_utc: datetime
    metrics: Mapping[str, MetricMeasurement]
    provenance: Literal["live", "synthetic"]
    is_up_observation: bool | None = None

    def __post_init__(self) -> None:
        """Validate timestamps, provenance, state, and metric names."""
        self._validate_time(self.hour_start_utc, "hour_start_utc", True)  # Require an aligned hour key.
        self._validate_time(
            self.collected_at_utc, "collected_at_utc", False
        )  # Require an explicit UTC collection time.
        if self.collected_at_utc < self.hour_start_utc:  # A collection cannot precede its observation hour.
            raise ValueError("collected_at_utc cannot precede hour_start_utc.")  # Reject inconsistent chronology.
        if self.provenance not in {"live", "synthetic"}:  # Keep source class explicit.
            raise ValueError("provenance must be live or synthetic.")  # Reject unknown provenance.
        if self.is_up_observation is not None and not isinstance(
            self.is_up_observation, bool
        ):  # Preserve strict state.
            raise ValueError("is_up_observation must be a boolean or None.")  # Reject truthy status values.
        self._validate_metrics(self.metrics)  # Validate names and values before freezing the mapping.
        object.__setattr__(self, "metrics", MappingProxyType(dict(self.metrics)))  # Prevent cross-consumer mutation.

    @staticmethod
    def _validate_time(value: datetime, field_name: str, aligned: bool) -> None:
        """Require explicit UTC times and an exact hour for the interval key."""
        if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):  # Reject local or naive times.
            raise ValueError(f"{field_name} must use an explicit UTC timezone.")  # Keep all times comparable.
        if aligned and any((value.minute, value.second, value.microsecond)):  # Require an exact hour boundary.
            raise ValueError("hour_start_utc must align to the start of a UTC hour.")  # Preserve natural interval keys.

    @staticmethod
    def _validate_metrics(metrics: Mapping[str, MetricMeasurement]) -> None:
        """Require named metrics with validated measurement objects."""
        if not isinstance(metrics, Mapping) or not metrics:  # Every observation needs at least one metric.
            raise ValueError("metrics must contain named measurements.")  # Reject empty observations.
        for name, metric in metrics.items():  # Inspect every metric entry.
            if not isinstance(name, str) or not name.strip():  # Reject blank or non-string names.
                raise ValueError("metric names must be non-empty strings.")  # Keep metric lookup stable.
            if not isinstance(metric, MetricMeasurement):  # Reject raw values without units.
                raise ValueError("each metric must be a MetricMeasurement.")  # Preserve the domain contract.

    @property
    def natural_key(self) -> tuple[str, ...]:
        """Return source identity and canonical UTC hour."""
        return (*self.identity.natural_key, self.hour_start_utc.isoformat())  # Avoid generated identifiers.

    def to_dict(self) -> dict[str, object]:
        """Return the observation as JSON-compatible values."""
        return {  # Keep identity and metrics separate.
            "identity": self.identity.to_dict(),  # Preserve the source identity.
            "hour_start_utc": self.hour_start_utc.isoformat(),  # Keep the interval key explicit.
            "collected_at_utc": self.collected_at_utc.isoformat(),  # Keep the observation time exact.
            "metrics": {
                name: metric.to_dict() for name, metric in self.metrics.items()
            },  # Serialize validated metrics.
            "provenance": self.provenance,  # Preserve the source class.
            "is_up_observation": self.is_up_observation,  # Preserve only explicit status.
        }
