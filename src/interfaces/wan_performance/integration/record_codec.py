"""Serialize validated WAN records without losing source identities or provenance."""

import json
from datetime import datetime
from typing import Literal, cast

from src.interfaces.wan_performance.domain.identity import (
    CircuitIdentity,
    GatewayIdentity,
    PeerPathIdentity,
    SiteIdentity,
)
from src.interfaces.wan_performance.domain.measurement import (
    HourlyMeasurement,
    MetricMeasurement,
    SampleMeasurement,
)


class RecordCodec:
    """Validate stored JSON before it returns to domain consumers."""

    @staticmethod
    def encode(record: HourlyMeasurement) -> str:
        """Reject preview data and encode a live record deterministically."""
        if record.provenance != "live":
            raise ValueError("History cannot contain synthetic records.")
        return json.dumps(record.to_dict(), sort_keys=True, allow_nan=False)

    @classmethod
    def decode(cls, payload: str) -> HourlyMeasurement:
        """Revalidate every stored record instead of trusting database contents."""
        row = json.loads(payload)
        if not isinstance(row, dict) or row.get("provenance") != "live":
            raise ValueError("History must contain a live record.")
        metrics = row["metrics"]
        if not isinstance(metrics, dict):
            raise ValueError("History metrics must be an object.")
        return HourlyMeasurement(
            cls._identity(row["identity"]),
            datetime.fromisoformat(row["hour_start_utc"]),
            datetime.fromisoformat(row["collected_at_utc"]),
            {name: cls._metric(metric) for name, metric in metrics.items()},
            "live",
            row.get("is_up_observation"),
        )

    @staticmethod
    def _metric(values: dict[str, object]) -> MetricMeasurement:
        """Restore JSON arrays as validated immutable sample tuples."""
        return MetricMeasurement(
            value=RecordCodec._number(values.get("value"), "value", optional=True),
            unit=RecordCodec._unit(values.get("unit")),
            sample_count=RecordCodec._sample_count(values.get("sample_count")),
            coverage_fraction=RecordCodec._coverage(values.get("coverage_fraction")),
            missing_reason=RecordCodec._missing_reason(values.get("missing_reason")),
            raw_values=RecordCodec._raw_values(values.get("raw_values")),
        )

    @staticmethod
    def _number(value: object, name: str, optional: bool) -> float | int | None:
        """Validate a stored numeric field before domain construction."""
        if value is None and optional:
            return None
        return RecordCodec._required_number(value, name)

    @staticmethod
    def _required_number(value: object, name: str) -> float | int:
        """Reject missing, boolean, and non-numeric stored values."""
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"Stored {name} must be a finite number.")
        return value

    @staticmethod
    def _unit(value: object) -> str:
        """Require the stored unit to remain a string."""
        if not isinstance(value, str):
            raise ValueError("Stored metric unit must be a string.")
        return value

    @staticmethod
    def _sample_count(value: object) -> int | None:
        """Validate an optional sample count from JSON."""
        if value is None:
            return None
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError("Stored sample count must be an integer.")
        return value

    @staticmethod
    def _coverage(value: object) -> float | None:
        """Validate an optional coverage fraction from JSON."""
        if value is None:
            return None
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("Stored coverage fraction must be numeric.")
        return float(value)

    @staticmethod
    def _missing_reason(value: object) -> str | None:
        """Validate the optional missing-value explanation from JSON."""
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("Stored missing reason must be a string.")
        return value

    @staticmethod
    def _raw_values(value: object) -> tuple[float | int, ...] | None:
        """Restore JSON sample arrays as finite numeric tuples."""
        if value is None:
            return None
        if not isinstance(value, list):
            raise ValueError("Stored raw samples must be a JSON array.")
        return tuple(RecordCodec._required_number(item, "raw sample") for item in value)

    @staticmethod
    def _identity(values: dict[str, str]) -> CircuitIdentity | GatewayIdentity | PeerPathIdentity:
        """Preserve complete circuit or peer-path identity through serialization."""
        gateway = GatewayIdentity(SiteIdentity(values["org_id"], values["site_id"]), values["gateway_id"])
        if "peer_mac" in values:
            return PeerPathIdentity(
                gateway,
                values["port_name"],
                values["peer_port_id"],
                values["peer_mac"],
                values["tunnel_identity"],
            )
        if "port_name" not in values:
            return gateway
        return CircuitIdentity(gateway, values["port_name"])


class SampleRecordCodec:
    """Serialize immutable raw samples without changing hourly records."""

    @staticmethod
    def encode(sample: SampleMeasurement) -> str:
        """Reject synthetic samples and encode each live poll deterministically."""
        if sample.provenance != "live":
            raise ValueError("History cannot contain synthetic samples.")
        return json.dumps(sample.to_dict(), sort_keys=True, allow_nan=False)

    @classmethod
    def decode(cls, payload: str) -> SampleMeasurement:
        """Revalidate stored raw sample shape, identity, and provenance."""
        row = json.loads(payload)
        if not isinstance(row, dict) or row.get("provenance") != "live":
            raise ValueError("History must contain a live sample.")
        source, partial, is_up = row.get("timestamp_source"), row.get("partial"), row.get("is_up_observation")
        if source not in {"poll", "api"} or not isinstance(partial, bool):
            raise ValueError("Stored sample timestamp source and partial state must be valid.")
        if is_up is not None and not isinstance(is_up, bool):
            raise ValueError("Stored sample link state must be a boolean or None.")
        identity = row.get("identity")
        if not isinstance(identity, dict):
            raise ValueError("Stored sample identity must be an object.")
        return SampleMeasurement(
            RecordCodec._identity(identity),
            cls._timestamp(row.get("sampled_at_utc")),
            cls._timestamp(row.get("collected_at_utc")),
            cls._metric_map(row.get("metrics")),
            cls._raw_fields(row.get("raw_fields")),
            cast(Literal["poll", "api"], source),
            partial,
            "live",
            is_up,
        )

    @staticmethod
    def _timestamp(value: object) -> datetime:
        """Require one stored ISO timestamp before domain validation."""
        if not isinstance(value, str):
            raise ValueError("Stored sample timestamps must be ISO 8601 strings.")
        return datetime.fromisoformat(value)

    @staticmethod
    def _metric_map(value: object) -> dict[str, MetricMeasurement]:
        """Rebuild each metric only from a named JSON object."""
        if not isinstance(value, dict) or any(not isinstance(metric, dict) for metric in value.values()):
            raise ValueError("Stored sample metrics must be an object of metric objects.")
        return {name: RecordCodec._metric(metric) for name, metric in value.items()}

    @staticmethod
    def _raw_fields(value: object) -> dict[str, float | int | None]:
        """Keep source scalar fields numeric and reject malformed stored values."""
        if not isinstance(value, dict):
            raise ValueError("Stored raw fields must be an object.")
        for name, field_value in value.items():
            if not isinstance(name, str) or (
                field_value is not None and (isinstance(field_value, bool) or not isinstance(field_value, (int, float)))
            ):
                raise ValueError("Stored raw fields must contain named numeric values or None.")
        return value


class SampleReplayPolicy:
    """Keep immutable source samples idempotent without masking changed data."""

    @classmethod
    def unique(cls, samples: tuple[SampleMeasurement, ...]) -> tuple[SampleMeasurement, ...]:
        """Remove identical natural-key replays from one pending batch."""
        selected: dict[tuple[str, ...], SampleMeasurement] = {}
        for sample in samples:
            previous = selected.get(sample.natural_key)
            if previous is None:
                selected[sample.natural_key] = sample
            else:
                cls._require_same_source_data(previous, sample)
        return tuple(selected.values())

    @classmethod
    def validate_existing(cls, payload: str, sample: SampleMeasurement) -> None:
        """Accept unchanged stored data and reject a changed source payload."""
        cls._require_same_source_data(SampleRecordCodec.decode(payload), sample)

    @classmethod
    def _require_same_source_data(cls, previous: SampleMeasurement, current: SampleMeasurement) -> None:
        """Ignore only collection time because an API sample may recur on later polls."""
        if cls._source_payload(previous) != cls._source_payload(current):
            raise ValueError("WAN sample replay conflicts with stored source data for the same natural key.")

    @staticmethod
    def _source_payload(sample: SampleMeasurement) -> str:
        """Compare every persisted source field except its later collection time."""
        payload = sample.to_dict()
        payload.pop("collected_at_utc")
        return json.dumps(payload, sort_keys=True, allow_nan=False)
