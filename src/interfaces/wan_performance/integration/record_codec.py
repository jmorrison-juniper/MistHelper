"""Serialize validated WAN records without losing source identities or provenance."""

import json
import logging
import math
from datetime import UTC, datetime
from typing import Any, Literal, cast

from src.interfaces.wan_performance.domain.calendar import MAX_HISTORY_RECORDS, MAX_HISTORY_WINDOW_DAYS
from src.interfaces.wan_performance.domain.identity import (
    CircuitIdentity,
    GatewayIdentity,
    PeerPathIdentity,
    SiteIdentity,
)
from src.interfaces.wan_performance.domain.measurement import (
    HourlyMeasurement,
    MeasurementIdentity,
    MetricMeasurement,
    SampleMeasurement,
)


class DeclarationCodec:
    """Validate explicit metadata without changing source observations or network configuration."""

    @classmethod
    def decode(cls, payload: bytes) -> dict[str, Any]:
        """Admit a bounded version-one declaration and normalize its effective interval."""
        logging.getLogger(__name__).info("Validate a bounded WAN metadata declaration.")
        if len(payload) > 65536:
            raise ValueError("A declaration must not exceed 64 KiB.")
        value = ArchiveCodec._json(payload)
        if not isinstance(value, dict) or set(value) != {"version", "provenance", "identity", "effective", "values"}:
            raise ValueError("A declaration must contain only its five required fields.")
        if type(value["version"]) is not int or value["version"] != 1 or value["provenance"] != "operator-declaration":
            raise ValueError("A declaration requires version 1 and operator-declaration provenance.")
        identity, interval, values = (
            cls.identity(value["identity"]),
            cls.window(value["effective"]),
            cls.values(value["values"]),
        )
        logging.getLogger(__name__).debug("Validated one scoped metadata declaration with %s values.", len(values))
        return {
            **value,
            "identity": identity.to_dict(),
            "effective": {"start_utc": interval[0].isoformat(), "end_utc": interval[1].isoformat()},
            "values": values,
        }

    @staticmethod
    def identity(value: Any) -> MeasurementIdentity:
        """Require the complete exact identity shape and preserve every validated source identifier."""
        if not isinstance(value, dict):
            raise ValueError("A replacement identity must be an object.")
        identity = RecordCodec._identity(value)
        if identity.to_dict() != value:
            raise ValueError("A replacement identity contains unknown or incomplete fields.")
        if any(not identifier.isprintable() for identifier in value.values()):
            raise ValueError("A replacement identity must contain printable identifiers.")
        return identity

    @staticmethod
    def window(value: Any) -> tuple[datetime, datetime]:
        """Require two increasing aware UTC timestamps without inferred duration or sampling coverage."""
        if not isinstance(value, dict) or set(value) != {"start_utc", "end_utc"}:
            raise ValueError("An effective interval requires exact start_utc and end_utc fields.")
        if not all(isinstance(timestamp, str) for timestamp in value.values()):
            raise ValueError("Effective timestamps must be ISO 8601 strings.")
        start, end = datetime.fromisoformat(value["start_utc"]), datetime.fromisoformat(value["end_utc"])
        if any(
            timestamp.tzinfo is None or timestamp.utcoffset() != UTC.utcoffset(timestamp) for timestamp in (start, end)
        ):
            raise ValueError("Effective timestamps must use explicit UTC.")
        if start >= end:
            raise ValueError("Effective timestamps must define an increasing interval.")
        return start, end

    @staticmethod
    def capacity(value: Any) -> float | int:
        """Reject boolean, absent, nonpositive, and nonfinite capacity values in bit/s."""
        if isinstance(value, bool) or not isinstance(value, (float, int)):
            raise ValueError("Declared capacity must be a finite positive number in bit/s.")
        try:
            valid = math.isfinite(value) and value > 0
        except OverflowError as error:
            raise ValueError("Declared capacity exceeds the finite numeric range.") from error
        if not valid:
            raise ValueError("Declared capacity must be a finite positive number in bit/s.")
        return value

    @classmethod
    def values(cls, value: Any) -> dict[str, Any]:
        """Validate explicitly supplied capacity, region, and role without a guessed taxonomy."""
        if not isinstance(value, dict) or not value or set(value) - {"capacity_bps", "region", "role"}:
            raise ValueError("Declare at least one supported metadata value.")
        result = dict(value)
        if "capacity_bps" in result:
            result["capacity_bps"] = cls.capacity(result["capacity_bps"])
        for name in {"region", "role"} & result.keys():
            text = result[name]
            if not isinstance(text, str) or not text.strip() or not text.isprintable() or len(text) > 128:
                raise ValueError("Declared region and role require 1 through 128 printable characters.")
        return result


class ArchiveCodec:
    """Validate independent projection archives without synthesizing source history or weakening live codecs."""

    @staticmethod
    def _json(payload: bytes) -> Any:
        """Require bounded UTF-8 JSON with unique object fields before interpreting any archive record."""
        if not isinstance(payload, bytes) or len(payload) > 8 * 1024 * 1024:
            raise ValueError("An archive must contain at most eight MiB of UTF-8 JSON.")

        def unique_fields(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
            """Reject duplicate JSON keys instead of silently selecting a later provenance or value."""
            result = dict(pairs)
            if len(result) != len(pairs):
                raise ValueError("Archive JSON contains duplicate object fields.")
            return result

        logging.getLogger(__name__).info("Parse bounded independent WAN replacement JSON.")
        try:
            value = json.loads(payload.decode("utf-8"), object_pairs_hook=unique_fields)
        except RecursionError as error:
            raise ValueError("Replacement JSON nesting exceeds the supported parser limit.") from error
        logging.getLogger(__name__).debug("Parsed bounded replacement JSON without duplicate fields.")
        return value

    @classmethod
    def decode(cls, payload: bytes) -> dict[str, Any]:
        """Require exact version, identity, provenance, and explicitly incomplete half-open UTC bounds."""
        value = cls._json(payload)
        if not isinstance(value, dict) or set(value) != {"version", "provenance", "identity", "window", "records"}:
            raise ValueError("An archive must contain only its five required fields.")
        if any(
            (type(value["version"]) is not int, value["version"] != 1, value["provenance"] not in ("live", "synthetic"))
        ):
            raise ValueError("An archive requires version 1 and explicit live or synthetic provenance.")
        window = value["window"]
        if not isinstance(window, dict):
            raise ValueError("An archive window must be an object.")
        if set(window) != {"start_utc", "end_utc", "complete"}:
            raise ValueError("An archive window must contain exact UTC bounds and completeness.")
        if window["complete"] is not False:
            raise ValueError("An archive window must explicitly declare complete: false.")
        bounds = DeclarationCodec.window({name: window[name] for name in ("start_utc", "end_utc")})
        if (bounds[1] - bounds[0]).total_seconds() > MAX_HISTORY_WINDOW_DAYS * 86400:
            raise ValueError("An archive window must span at most 397 days.")
        identity = DeclarationCodec.identity(value["identity"])
        records = cls._records(value["records"], identity, bounds, value["provenance"])
        logging.getLogger(__name__).debug("Validated %s archive projections without a history write.", len(records))
        return {**value, "identity": identity, "window": bounds, "records": records}

    @classmethod
    def _records(
        cls,
        values: Any,
        identity: MeasurementIdentity,
        bounds: tuple[datetime, datetime],
        provenance: Literal["live", "synthetic"],
    ) -> tuple[HourlyMeasurement, ...]:
        """Reject duplicate, foreign, or out-of-window hours before any storage decision."""
        if not isinstance(values, list) or not 1 <= len(values) <= MAX_HISTORY_RECORDS:
            raise ValueError("An archive requires 1 through 9528 projection records.")
        records = tuple(cls._record(value, identity, provenance) for value in values)
        if len({record.natural_key for record in records}) != len(records):
            raise ValueError("An archive contains duplicate full-identity hour keys.")
        if any(not bounds[0] <= record.hour_start_utc < bounds[1] for record in records):
            raise ValueError("An archive contains an out-of-window hour.")
        return records

    @classmethod
    def _record(
        cls, value: Any, identity: MeasurementIdentity, provenance: Literal["live", "synthetic"]
    ) -> HourlyMeasurement:
        """Preserve exact identities, declared provenance, timestamps, values, and missing states."""
        fields = {"identity", "provenance", "metrics", "hour_start_utc", "collected_at_utc", "is_up_observation"}
        if not isinstance(value, dict) or set(value) != fields:
            raise ValueError("Each archive record must contain exactly its six projection fields.")
        if value["identity"] != identity.to_dict() or value["provenance"] != provenance:
            raise ValueError("Archive record identity or provenance does not match its envelope.")
        if not all(isinstance(value[name], str) for name in ("hour_start_utc", "collected_at_utc")):
            raise ValueError("Archive record timestamps must be ISO 8601 strings.")
        return HourlyMeasurement(
            identity,
            datetime.fromisoformat(value["hour_start_utc"]),
            datetime.fromisoformat(value["collected_at_utc"]),
            cls._metrics(value["metrics"]),
            provenance,
            value["is_up_observation"],
        )

    @staticmethod
    def _metrics(value: Any) -> dict[str, MetricMeasurement]:
        """Validate projection-only fields and reject raw arrays or unsafe metric labels."""
        if not isinstance(value, dict):
            raise ValueError("Archive metrics must be a nonempty object.")
        fields = {"value", "unit", "sample_count", "coverage_fraction", "missing_reason", "raw_values"}
        result = {}
        for name, metric in value.items():
            if not isinstance(name, str):
                raise ValueError("Archive metric names require 1 through 128 printable characters.")
            if any((not name.isprintable(), not 1 <= len(name) <= 128)):
                raise ValueError("Archive metric names require 1 through 128 printable characters.")
            if not isinstance(metric, dict):
                raise ValueError("Archive metrics contain unsupported fields.")
            if any((set(metric) - fields, not {"value", "unit"} <= metric.keys())):
                raise ValueError("Archive metrics contain unsupported or missing fields.")
            unit = metric.get("unit")
            if not isinstance(unit, str):
                raise ValueError("Archive metric units require printable strings.")
            if any((not unit.isprintable(), not 1 <= len(unit) <= 128, metric.get("raw_values") is not None)):
                raise ValueError("Archive units must remain bounded and raw-sample import is unsupported.")
            try:
                result[name] = RecordCodec._metric(metric)
            except OverflowError as error:
                raise ValueError("An archive metric exceeds the finite numeric range.") from error
        return result


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
