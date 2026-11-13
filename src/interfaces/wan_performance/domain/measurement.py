"""Validate UTC hourly WAN measurements before aggregation or storage."""

import math
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from types import MappingProxyType
from typing import Literal

from src.interfaces.wan_performance.domain.identity import CircuitIdentity, GatewayIdentity, PeerPathIdentity
from src.interfaces.wan_performance.domain.metric_validation import (
    validate_coverage_fraction,
    validate_sample_count,
    validate_unit,
    validate_value,
)

MeasurementIdentity = CircuitIdentity | GatewayIdentity | PeerPathIdentity


@dataclass(frozen=True, slots=True)
class MetricMeasurement:
    """Represent one finite metric or an explicitly missing measurement."""

    value: float | int | None
    unit: str
    sample_count: int | None = None
    coverage_fraction: float | None = None
    missing_reason: str | None = None
    raw_values: tuple[float | int, ...] | None = None

    def __post_init__(self) -> None:
        """Reject invalid numeric values and unexplained missing data."""
        validate_unit(self.unit)
        validate_value(self.value, self.missing_reason)
        validate_sample_count(self.sample_count)
        validate_coverage_fraction(self.coverage_fraction)
        self._validate_raw_values()

    def _validate_raw_values(self) -> None:
        """Keep retained source samples finite and aligned with their count."""
        if self.raw_values is None:
            return
        if not isinstance(self.raw_values, tuple):
            raise ValueError("raw_values must be a tuple of finite numbers.")
        for raw_value in self.raw_values:
            validate_value(raw_value, None)
        if self.sample_count is not None and self.sample_count != len(self.raw_values):
            raise ValueError("sample_count must match raw_values when raw samples are retained.")

    def to_dict(self) -> dict[str, object]:
        """Return JSON-compatible metric values and their units."""
        return {
            "value": self.value,
            "unit": self.unit,
            "sample_count": self.sample_count,
            "coverage_fraction": self.coverage_fraction,
            "missing_reason": self.missing_reason,
            "raw_values": self.raw_values,
        }


@dataclass(frozen=True, slots=True)
class HourlyMeasurement:
    """Represent a natural-keyed measurement for one UTC hour."""

    identity: MeasurementIdentity
    hour_start_utc: datetime
    collected_at_utc: datetime
    metrics: Mapping[str, MetricMeasurement]
    provenance: Literal["live", "synthetic"]
    is_up_observation: bool | None = None

    def __post_init__(self) -> None:
        """Validate time, provenance, and metric names before record use."""
        self._validate_utc_hour(self.hour_start_utc, "hour_start_utc", hour_aligned=True)
        self._validate_utc_hour(self.collected_at_utc, "collected_at_utc", hour_aligned=False)
        if self.collected_at_utc < self.hour_start_utc:
            raise ValueError("collected_at_utc cannot precede hour_start_utc.")
        if self.provenance not in {"live", "synthetic"}:
            raise ValueError("provenance must be live or synthetic.")
        self._validate_state()
        if not self.metrics or any(not isinstance(name, str) or not name.strip() for name in self.metrics):
            raise ValueError("metrics must contain named measurements.")
        if any(not isinstance(metric, MetricMeasurement) for metric in self.metrics.values()):
            raise ValueError("each metrics value must be a MetricMeasurement.")
        object.__setattr__(self, "metrics", MappingProxyType(dict(self.metrics)))

    def _validate_state(self) -> None:
        """Require status evidence to remain an explicit boolean."""
        if self.is_up_observation is not None and not isinstance(self.is_up_observation, bool):
            raise ValueError("is_up_observation must be a boolean or None.")

    @staticmethod
    def _validate_utc_hour(value: datetime, field_name: str, hour_aligned: bool) -> None:
        """Require an aware UTC time and an exact hour for interval identity."""
        if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
            raise ValueError(f"{field_name} must use an explicit UTC timezone.")
        if hour_aligned and any((value.minute, value.second, value.microsecond)):
            raise ValueError("hour_start_utc must align to the start of a UTC hour.")

    @property
    def natural_key(self) -> tuple[str, ...]:
        """Return the source identity with its canonical UTC hour."""
        return (*self.identity.natural_key, self.hour_start_utc.isoformat())

    def to_dict(self) -> dict[str, object]:
        """Return the record as JSON-compatible values for offline consumers."""
        return {
            "identity": self.identity.to_dict(),
            "hour_start_utc": self.hour_start_utc.isoformat(),
            "collected_at_utc": self.collected_at_utc.isoformat(),
            "metrics": {name: metric.to_dict() for name, metric in self.metrics.items()},
            "provenance": self.provenance,
            "is_up_observation": self.is_up_observation,
        }


class SampleMeasurementValidator:
    """Validate source samples before the immutable sample record is stored."""

    @staticmethod
    def timestamps(sampled_at: datetime, collected_at: datetime) -> None:
        """Require ordered, timezone-aware UTC sample timestamps."""
        for field_name, value in (("sampled_at_utc", sampled_at), ("collected_at_utc", collected_at)):
            if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
                raise ValueError(f"{field_name} must use an explicit UTC timezone.")
        if sampled_at > collected_at:
            raise ValueError("sampled_at_utc cannot follow collected_at_utc.")

    @staticmethod
    def source_state(timestamp_source: str, partial: bool, provenance: str, is_up_observation: bool | None) -> None:
        """Require supported timestamp provenance and explicit boolean states."""
        if timestamp_source not in {"poll", "api"}:
            raise ValueError("timestamp_source must be poll or api.")
        if not isinstance(partial, bool):
            raise ValueError("partial must be a boolean.")
        if provenance not in {"live", "synthetic"}:
            raise ValueError("provenance must be live or synthetic.")
        if is_up_observation is not None and not isinstance(is_up_observation, bool):
            raise ValueError("is_up_observation must be a boolean or None.")

    @staticmethod
    def metrics(values: Mapping[str, MetricMeasurement]) -> None:
        """Require named metrics with validated measurement records."""
        if not values or any(not isinstance(name, str) or not name.strip() for name in values):
            raise ValueError("metrics must contain named measurements.")
        if any(not isinstance(metric, MetricMeasurement) for metric in values.values()):
            raise ValueError("each metrics value must be a MetricMeasurement.")

    @staticmethod
    def raw_fields(values: Mapping[str, float | int | None]) -> None:
        """Require named source fields with finite numeric values or explicit nulls."""
        for name, value in values.items():
            if not isinstance(name, str) or not name.strip():
                raise ValueError("raw_fields must contain named source values.")
            if value is not None:
                SampleMeasurementValidator.raw_value(value)

    @staticmethod
    def raw_value(value: object) -> None:
        """Reject booleans and non-finite values from untyped source mappings."""
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError("raw_fields values must be finite numbers or None.")


@dataclass(frozen=True, slots=True)
class SampleMeasurement:
    """Keep one source observation with its full identity and exact UTC time."""

    identity: MeasurementIdentity
    sampled_at_utc: datetime
    collected_at_utc: datetime
    metrics: Mapping[str, MetricMeasurement]
    raw_fields: Mapping[str, float | int | None]
    timestamp_source: Literal["poll", "api"]
    partial: bool
    provenance: Literal["live", "synthetic"]
    is_up_observation: bool | None = None

    def __post_init__(self) -> None:
        """Validate sample timestamps, source state, and immutable values."""
        SampleMeasurementValidator.timestamps(self.sampled_at_utc, self.collected_at_utc)  # Validate sample time.
        SampleMeasurementValidator.source_state(  # Require source time and state provenance.
            self.timestamp_source, self.partial, self.provenance, self.is_up_observation
        )
        SampleMeasurementValidator.metrics(self.metrics)  # Reject empty or malformed metric records.
        SampleMeasurementValidator.raw_fields(self.raw_fields)  # Preserve only finite raw source fields.
        object.__setattr__(self, "metrics", MappingProxyType(dict(self.metrics)))  # Prevent mutation after validation.
        object.__setattr__(self, "raw_fields", MappingProxyType(dict(self.raw_fields)))  # Freeze source values too.

    @property
    def natural_key(self) -> tuple[str, ...]:
        """Return full source identity plus the exact UTC sample timestamp."""
        return (*self.identity.natural_key, self.sampled_at_utc.isoformat())

    def to_dict(self) -> dict[str, object]:
        """Return the sample and source fields as JSON-compatible values."""
        return {
            "identity": self.identity.to_dict(),
            "sampled_at_utc": self.sampled_at_utc.isoformat(),
            "collected_at_utc": self.collected_at_utc.isoformat(),
            "metrics": {name: metric.to_dict() for name, metric in self.metrics.items()},
            "raw_fields": dict(self.raw_fields),
            "timestamp_source": self.timestamp_source,
            "partial": self.partial,
            "provenance": self.provenance,
            "is_up_observation": self.is_up_observation,
        }

    def to_hourly(self) -> HourlyMeasurement:
        """Create a separate hour projection without changing this raw sample."""
        hour = self.sampled_at_utc.replace(minute=0, second=0, microsecond=0)
        return HourlyMeasurement(
            self.identity, hour, self.collected_at_utc, self.metrics, self.provenance, self.is_up_observation
        )
