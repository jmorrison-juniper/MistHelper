"""Normalize live WAN snapshots without inventing metric coverage."""

import hashlib
import json
import logging
from collections.abc import Mapping
from datetime import UTC, datetime
from types import MappingProxyType
from typing import Any

from src.interfaces.wan_performance.domain.identity import (
    CircuitIdentity,
    GatewayIdentity,
    IdentityValidator,
    PeerPathIdentity,
    SiteIdentity,
)
from src.interfaces.wan_performance.domain.measurement import HourlyMeasurement, MetricMeasurement

logger = logging.getLogger(__name__)


class SnapshotRates:
    """Validate WAN rates while preserving missing and zero values."""

    @staticmethod
    def parse(value: object, unit: str) -> MetricMeasurement:
        """Return a finite non-negative rate or an explained missing value."""
        if value is None:  # Source omissions do not mean zero.
            return MetricMeasurement(
                None, unit, missing_reason="The API snapshot has no value."
            )  # Keep absence explicit.
        if isinstance(value, str):  # Some API responses encode numbers as text.
            try:  # Convert only valid numeric text.
                value = float(value)  # Keep the original API unit.
            except ValueError as error:  # Invalid text cannot be a measurement.
                raise ValueError("WAN metric value must be numeric.") from error  # Report malformed source data.
        if isinstance(value, bool) or not isinstance(value, (int, float)):  # Reject booleans and objects.
            raise ValueError("WAN metric value must be numeric.")  # Refuse invalid data.
        if value < 0:  # Rates cannot be negative.
            raise ValueError("WAN metric value must not be negative.")  # Preserve only valid rates.
        return MetricMeasurement(value, unit, sample_count=1)  # Mark one point-in-time sample.

    @staticmethod
    def parse_sample(sample: Mapping[str, Any]) -> MetricMeasurement:
        """Validate one insight sample and retain its source coverage fields."""
        value = sample.get("value")  # Read the source sample value.
        unit = sample.get("unit")  # Read the catalog or source unit.
        if not isinstance(unit, str):  # Require source unit metadata.
            raise ValueError("WAN insight sample requires a unit.")  # Refuse ambiguous metrics.
        missing_reason = sample.get("missing_reason")  # Preserve any source explanation.
        if value is None and not isinstance(missing_reason, str):  # Explain missing samples.
            missing_reason = "The API snapshot has no value."  # Use a clear missing-value reason.
        if isinstance(value, str):  # Accept numeric text from the API.
            value = float(value)  # Let the domain validator reject non-finite text.
        raw_values = sample.get("raw_values")  # Read optional source values.
        return MetricMeasurement(  # Validate the full measurement before returning.
            value,  # Preserve the latest source value.
            unit,  # Preserve the source unit.
            sample.get("sample_count"),  # Preserve the reported count.
            sample.get("coverage_fraction"),  # Preserve known coverage only.
            missing_reason,  # Explain absent data.
            tuple(raw_values) if raw_values is not None else None,  # Freeze retained samples.
        )


class PeerSnapshotMetrics:
    """Read documented VPN peer metrics without inventing values."""

    FIELDS: Mapping[str, tuple[str, float | None]] = MappingProxyType(  # Keep the source field schema immutable.
        {  # Units match the documented peer fields.
            "latency": ("ms", None),  # Preserve latency in milliseconds.
            "jitter": ("ms", None),  # Preserve jitter in milliseconds.
            "loss": ("%", 100),  # Bound loss as a percentage.
            "mos": ("score", 5),  # Bound the MOS score.
        }
    )

    @classmethod
    def parse(cls, row: Mapping[str, object]) -> Mapping[str, MetricMeasurement]:
        """Return immutable peer metrics with explicit missing reasons."""
        logger.info("Validate WAN peer snapshot metrics.")  # Mark validation before processing source values.
        metrics = {name: cls._metric(name, row.get(name)) for name in cls.FIELDS}  # Validate every documented metric.
        logger.debug("Validated %d WAN peer snapshot metrics.", len(metrics))  # Record the validation result count.
        return MappingProxyType(metrics)  # Prevent mutation by later consumers.

    @classmethod
    def _metric(cls, name: str, value: object) -> MetricMeasurement:
        """Validate one peer metric against its unit and documented range."""
        unit, maximum = cls.FIELDS[name]  # Read the trusted schema entry.
        if value is None:  # Missing values remain unknown.
            return MetricMeasurement(None, unit, missing_reason="The API snapshot has no value.")  # Explain absence.
        if isinstance(value, bool) or not isinstance(value, (int, float)):  # Reject booleans and text.
            raise ValueError(f"Invalid {name} in WAN peer snapshot.")  # Refuse malformed data.
        metric = MetricMeasurement(value, unit)  # Reject non-finite numbers through domain validation.
        if value < 0 or (maximum is not None and value > maximum):  # Enforce metric-specific bounds.
            raise ValueError(f"Invalid {name} in WAN peer snapshot.")  # Do not normalize bad values.
        return metric  # Preserve the validated source value.


class PortSnapshotMetrics:
    """Normalize directional rates and use only reported link capacity."""

    @classmethod
    def parse(cls, row: Mapping[str, object]) -> dict[str, MetricMeasurement]:
        """Return rate and utilization metrics for one current port row."""
        logger.info("Validate WAN port snapshot rates.")  # Mark validation before transforming source data.
        rates = {name: cls._rate(name, row.get(name)) for name in ("rx_bps", "tx_bps")}  # Read directional rates.
        metrics = dict(rates)  # Keep rate measurements separate from utilization.
        for name, rate in rates.items():  # Derive utilization only from valid source capacity.
            label = name.removesuffix("_bps") + "_utilization_percent"  # Name each direction clearly.
            metrics[label] = cls._utilization(rate, row.get("speed"))  # Keep missing capacity explicit.
        logger.debug("Validated %d WAN port snapshot metrics.", len(metrics))  # Record the result count.
        return metrics  # Preserve validated numeric and missing values.

    @staticmethod
    def _rate(name: str, value: object) -> MetricMeasurement:
        """Keep invalid optional rates unknown without discarding adjacent data."""
        try:  # Validate one rate without affecting the other direction.
            return SnapshotRates.parse(value, "bit/s")  # Preserve the API rate unit.
        except (ValueError, OverflowError) as error:  # Invalid optional data remains unknown.
            logger.error("Invalid WAN port rate %s: %s", name, error)  # Report the source field failure.
            return MetricMeasurement(None, "bit/s", missing_reason="Invalid API port rate.")  # Preserve the valid row.

    @staticmethod
    def _utilization(rate: MetricMeasurement, speed: object) -> MetricMeasurement:
        """Calculate point-in-time utilization from reported Mbps capacity."""
        reason = "Utilization requires a valid rate and positive integer speed in Mbps."  # Explain missing capacity.
        if rate.value is None:  # A missing rate cannot produce utilization.
            return MetricMeasurement(None, "%", missing_reason=reason)  # Keep derived data unknown.
        if isinstance(speed, bool) or not isinstance(speed, int) or speed <= 0:  # Require valid capacity.
            return MetricMeasurement(None, "%", missing_reason=reason)  # Do not infer link speed.
        return MetricMeasurement(rate.value / speed / 1_000_000 * 100, "%", sample_count=1)  # Keep snapshot scope.


class SnapshotRecords:
    """Convert live port and peer rows into natural-keyed observations."""

    @classmethod
    def build(cls, snapshot: Mapping[str, Any]) -> tuple[HourlyMeasurement, ...]:
        """Validate a live snapshot and normalize each supported row."""
        if not isinstance(snapshot, Mapping) or snapshot.get("provenance") != "live":  # Reject non-live inputs.
            raise ValueError("WAN snapshots must have live provenance.")  # Keep cached source class explicit.
        org_id = IdentityValidator.identifier(snapshot.get("org_id"), "org_id")  # Validate tenant scope.
        instant = cls._collected_at(snapshot.get("collected_at_utc"))  # Validate source observation time.
        ports = tuple(cls._port(row, org_id, instant) for row in cls._rows(snapshot, "ports"))  # Normalize ports.
        peers = tuple(cls._peer(row, org_id, instant) for row in cls._rows(snapshot, "peers"))  # Normalize peers.
        insights = cls._insights(snapshot.get("insights", {}), org_id, instant)  # Normalize optional insights.
        logger.debug("Normalized %d live WAN observations.", len(ports) + len(peers) + len(insights))  # Record results.
        return ports + peers + insights  # Preserve stable port, peer, and insight ordering.

    @staticmethod
    def _rows(snapshot: Mapping[str, Any], name: str) -> list[Mapping[str, Any]]:
        """Require a list of object rows for each collection."""
        rows = snapshot.get(name, [])  # Allow an absent optional collection.
        if not isinstance(rows, list) or any(not isinstance(row, Mapping) for row in rows):  # Reject bad envelopes.
            raise ValueError(f"WAN snapshot {name} must be an array of objects.")  # Report the broken contract.
        return rows  # Keep validated source rows.

    @staticmethod
    def _collected_at(value: object) -> datetime:
        """Require an explicit UTC collection time."""
        if not isinstance(value, str):  # Require an ISO timestamp from the collector.
            raise ValueError("collected_at_utc must be an ISO 8601 timestamp.")  # Reject missing time.
        instant = datetime.fromisoformat(value.replace("Z", "+00:00"))  # Parse a standard UTC suffix.
        if instant.tzinfo is None or instant.utcoffset() != UTC.utcoffset(instant):  # Require UTC explicitly.
            raise ValueError("collected_at_utc must use UTC.")  # Reject local times.
        return instant.astimezone(UTC)  # Normalize to the canonical timezone.

    @staticmethod
    def _gateway(row: Mapping[str, Any], org_id: str) -> GatewayIdentity:
        """Validate tenant membership and source gateway values."""
        if row.get("org_id") != org_id:  # Never accept a cross-tenant row.
            raise ValueError("WAN row organization does not match the selected organization.")  # Fail closed.
        site_id = IdentityValidator.identifier(row.get("site_id"), "site_id")  # Validate the parent site.
        gateway_id = IdentityValidator.identifier(row.get("mac"), "gateway MAC")  # Validate the source gateway.
        return GatewayIdentity(SiteIdentity(org_id, site_id), gateway_id)  # Retain exact source identities.

    @classmethod
    def _port(cls, row: Mapping[str, Any], org_id: str, instant: datetime) -> HourlyMeasurement:
        """Normalize a current port row without creating interval coverage."""
        gateway = cls._gateway(row, org_id)  # Validate tenant and gateway scope first.
        port_id = IdentityValidator.port_name(row.get("port_id"), "port_id")  # Validate source interface notation.
        identity = CircuitIdentity(gateway, port_id)  # Keep the natural circuit identity.
        hour = instant.replace(minute=0, second=0, microsecond=0)  # Assign the observation hour only.
        metrics = PortSnapshotMetrics.parse(row)  # Validate rates and capacity.
        return HourlyMeasurement(identity, hour, instant, metrics, "live", cls._state(row.get("up")))  # Preserve state.

    @classmethod
    def _peer(cls, row: Mapping[str, Any], org_id: str, instant: datetime) -> HourlyMeasurement:
        """Normalize one peer row with all source path values."""
        peer_site_id = IdentityValidator.identifier(row.get("peer_site_id"), "peer_site_id")  # Require remote site.
        peer_type = IdentityValidator.identifier(row.get("type"), "type")  # Require source path type.
        gateway = cls._gateway(row, org_id)  # Validate tenant and gateway scope first.
        local_port_id = IdentityValidator.port_name(row.get("port_id"), "port_id")  # Validate local interface name.
        peer_port_id = IdentityValidator.port_name(row.get("peer_port_id"), "peer_port_id")  # Validate remote name.
        peer_mac = IdentityValidator.peer_mac(row.get("peer_mac"))  # Validate the remote device identity.
        fields = (peer_site_id, peer_port_id, peer_type)  # Keep every validated path field.
        path_hash = hashlib.sha256(
            json.dumps(fields, separators=(",", ":")).encode()
        ).hexdigest()  # Key all path fields.
        identity = PeerPathIdentity(  # Build a scoped peer identity.
            gateway,  # Preserve the local gateway.
            local_port_id,  # Preserve the local port.
            peer_port_id,  # Preserve the remote port.
            peer_mac,  # Preserve the remote MAC.
            path_hash,  # Distinguish the remaining source tunnel fields.
        )
        hour = instant.replace(minute=0, second=0, microsecond=0)  # Assign the observation hour only.
        return HourlyMeasurement(
            identity, hour, instant, PeerSnapshotMetrics.parse(row), "live", cls._state(row.get("up"))
        )  # Keep a point observation.

    @staticmethod
    def _state(value: object) -> bool | None:
        """Preserve only explicit boolean link state."""
        return value if isinstance(value, bool) else None  # Do not interpret truthy source values.

    @classmethod
    def _insights(cls, data: object, org_id: str, instant: datetime) -> tuple[HourlyMeasurement, ...]:
        """Normalize one gateway insight sample set when present."""
        if not isinstance(data, Mapping) or not data.get("samples"):  # Empty insight data is an allowed partial result.
            return ()  # Do not invent insight observations.
        gateway = cls._gateway(data.get("gateway", {}), org_id)  # Validate the scoped gateway.
        port_id = data.get("port_id")  # Read optional circuit scope.
        identity = CircuitIdentity(gateway, port_id) if port_id is not None else gateway  # Keep explicit scope.
        samples = data.get("samples")  # Read normalized insight samples.
        if not isinstance(samples, list) or any(not isinstance(sample, Mapping) for sample in samples):  # Check shape.
            raise ValueError("WAN insight samples must be an array of objects.")  # Reject malformed samples.
        return (InsightRecordBuilder.build(identity, samples, instant),)  # Emit one validated measurement per hour.


class InsightRecordBuilder:
    """Build one normalized gateway insight record from aligned samples."""

    @classmethod
    def build(
        cls, identity: GatewayIdentity | CircuitIdentity, samples: list[Mapping[str, Any]], instant: datetime
    ) -> HourlyMeasurement:
        """Validate one shared hour and unique metric names."""
        names = cls._metric_names(samples)  # Require unique named metrics.
        hour = cls._hour(samples)  # Require one shared UTC hour.
        metrics = cls._metrics(names, samples)  # Validate each measured rate.
        return HourlyMeasurement(identity, hour, instant, metrics, "live")  # Preserve only explicit source coverage.

    @staticmethod
    def _metric_names(samples: list[Mapping[str, Any]]) -> list[str]:
        """Require one non-empty name for every unique metric."""
        names = [sample.get("metric") for sample in samples]  # Read requested metric names.
        valid_names = [name for name in names if isinstance(name, str) and name]  # Keep valid names only.
        if len(valid_names) != len(samples) or len(set(valid_names)) != len(valid_names):  # Require unique keys.
            raise ValueError("WAN insight metrics must have unique names.")  # Reject ambiguous metrics.
        return valid_names  # Keep validated names in source order.

    @staticmethod
    def _hour(samples: list[Mapping[str, Any]]) -> datetime:
        """Require one explicit UTC hour across all samples."""
        hour_value = samples[0].get("hour_start_utc") if samples else None  # Read one source interval.
        if not isinstance(hour_value, str) or any(
            sample.get("hour_start_utc") != hour_value for sample in samples
        ):  # Require one shared interval key.
            raise ValueError("WAN insight metrics must use the same UTC hour.")  # Reject misaligned samples.
        hour = datetime.fromisoformat(hour_value.replace("Z", "+00:00"))  # Parse the source interval.
        if hour.tzinfo is None or hour.utcoffset() != UTC.utcoffset(hour):  # Require explicit UTC.
            raise ValueError("WAN insight metrics must use the same UTC hour.")  # Reject local times.
        return hour.astimezone(UTC)  # Normalize the source interval.

    @staticmethod
    def _metrics(names: list[str], samples: list[Mapping[str, Any]]) -> dict[str, MetricMeasurement]:
        """Parse each metric under its validated source name."""
        return {
            name: SnapshotRates.parse_sample(sample) for name, sample in zip(names, samples, strict=True)
        }  # Keep exact metric and sample alignment.


class SnapshotStates:
    """Keep current WAN status separate from numeric observations."""

    @classmethod
    def build(
        cls, snapshot: Mapping[str, Any], records: tuple[HourlyMeasurement, ...]
    ) -> dict[tuple[str, ...], dict[str, str]]:
        """Join current status fields to their matching port and peer identities."""
        rows = SnapshotRecords._rows(snapshot, "ports") + SnapshotRecords._rows(snapshot, "peers")  # Keep row order.
        states: dict[tuple[str, ...], dict[str, str]] = {}  # Build a separate status map.
        for row, record in zip(rows, records, strict=False):  # Pair only current rows with their records.
            values = {"Current link state": cls._boolean(row.get("up"), "Up", "Down")}  # Preserve link state.
            if isinstance(record.identity, PeerPathIdentity):  # Add peer-only status details.
                values["Redundant path"] = cls._boolean(
                    row.get("is_active"), "Active", "Standby"
                )  # Preserve active state.
                values["Gateway-reported uptime (s)"] = cls._seconds(row.get("uptime"))  # Preserve reported uptime.
                values["Last observed (UTC)"] = cls._last_seen(
                    row.get("last_seen")
                )  # Preserve source observation time.
            states[record.natural_key] = values  # Match state to the full natural key.
        return states  # Keep status separate from metric history.

    @staticmethod
    def _boolean(value: object, true_label: str, false_label: str) -> str:
        """Render only explicit booleans as known status."""
        if isinstance(value, bool):  # Accept true and false source values.
            return true_label if value else false_label  # Preserve the exact state.
        return "Unknown"  # Never infer state from truthy values.

    @staticmethod
    def _seconds(value: object) -> str:
        """Render a non-negative reported uptime without inference."""
        if value is None:  # Preserve an absent counter as unknown.
            return "Unknown"  # Do not claim uptime.
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:  # Reject invalid counters.
            return "Unknown"  # Do not infer a healthy state.
        return str(value)  # Preserve zero and positive source values.

    @staticmethod
    def _last_seen(value: object) -> str:
        """Render an epoch timestamp as explicit UTC or unknown."""
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:  # Reject invalid epochs.
            return "Unknown"  # Keep bad timestamps unknown.
        try:  # Guard the supported timestamp range.
            return datetime.fromtimestamp(value, UTC).isoformat()  # Preserve the source instant in UTC.
        except (OSError, OverflowError, ValueError):  # Reject timestamps outside the platform range.
            return "Unknown"  # Do not fabricate a timestamp.
