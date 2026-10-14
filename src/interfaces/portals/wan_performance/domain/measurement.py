"""Validate UTC hourly WAN measurements before aggregation or storage."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from types import MappingProxyType
from typing import Literal

from src.interfaces.portals.wan_performance.domain.identity import CircuitIdentity, GatewayIdentity, PeerPathIdentity
from src.interfaces.portals.wan_performance.domain.metric_validation import (
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

    def __post_init__(self) -> None:
        """Reject invalid numeric values and unexplained missing data."""
        validate_unit(self.unit)
        validate_value(self.value, self.missing_reason)
        validate_sample_count(self.sample_count)
        validate_coverage_fraction(self.coverage_fraction)

    def to_dict(self) -> dict[str, float | int | str | None]:
        """Return JSON-compatible metric values and their units."""
        return {
            "value": self.value,
            "unit": self.unit,
            "sample_count": self.sample_count,
            "coverage_fraction": self.coverage_fraction,
            "missing_reason": self.missing_reason,
        }


@dataclass(frozen=True, slots=True)
class HourlyMeasurement:
    """Represent a natural-keyed measurement for one UTC hour."""

    identity: MeasurementIdentity
    hour_start_utc: datetime
    collected_at_utc: datetime
    metrics: Mapping[str, MetricMeasurement]
    provenance: Literal["live", "synthetic"]

    def __post_init__(self) -> None:
        """Validate time, provenance, and metric names before record use."""
        self._validate_utc_hour(self.hour_start_utc, "hour_start_utc", hour_aligned=True)
        self._validate_utc_hour(self.collected_at_utc, "collected_at_utc", hour_aligned=False)
        if self.collected_at_utc < self.hour_start_utc:
            raise ValueError("collected_at_utc cannot precede hour_start_utc.")
        if self.provenance not in {"live", "synthetic"}:
            raise ValueError("provenance must be live or synthetic.")
        if not self.metrics or any(not isinstance(name, str) or not name.strip() for name in self.metrics):
            raise ValueError("metrics must contain named measurements.")
        if any(not isinstance(metric, MetricMeasurement) for metric in self.metrics.values()):
            raise ValueError("each metrics value must be a MetricMeasurement.")
        object.__setattr__(self, "metrics", MappingProxyType(dict(self.metrics)))

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
        }
