"""Serialize validated WAN records without losing source identities or provenance."""

import json
from datetime import datetime

from src.interfaces.portals.wan_performance.domain.identity import (
    CircuitIdentity,
    GatewayIdentity,
    PeerPathIdentity,
    SiteIdentity,
)
from src.interfaces.portals.wan_performance.domain.measurement import HourlyMeasurement, MetricMeasurement


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
