"""Map documented snapshots to observation-hour records, never full-hour coverage."""

import logging
import math
from collections.abc import Mapping
from datetime import UTC, datetime
from types import MappingProxyType
from typing import Any

from src.interfaces.wan_performance.domain.identity import (
    CircuitIdentity,
    GatewayIdentity,
    PeerPathIdentity,
)
from src.interfaces.wan_performance.domain.measurement import (
    HourlyMeasurement,
    MetricMeasurement,
    SampleMeasurement,
)

logger = logging.getLogger(__name__)


class PeerSnapshotMetrics:
    """Map peer scalar fields only where the schema defines their units."""

    FIELDS: Mapping[str, str] = MappingProxyType({"loss": "%", "latency": "ms", "jitter": "ms"})

    @classmethod
    def parse(cls, row: Mapping[str, object]) -> Mapping[str, MetricMeasurement]:
        """Return stable peer metrics without inventing fields or units."""
        logger.info("Validate VPN peer snapshot metrics.")
        metrics = {name: cls._metric(name, row) for name in ("loss", "latency", "jitter", "mos")}
        logger.debug("Validated %d VPN peer snapshot metrics.", len(metrics))
        return MappingProxyType(metrics)

    @classmethod
    def _metric(cls, name: str, row: Mapping[str, object]) -> MetricMeasurement:
        """Retain scalar metrics only when the schema defines their units."""
        value = row.get(name)
        unit = cls.FIELDS.get(name)
        if unit is None:
            reason = (
                "The API snapshot has no value."
                if value is None
                else "The VPN peer stats schema does not define this field's unit."
            )
            return MetricMeasurement(None, "unknown", missing_reason=reason)
        if value is None:
            return MetricMeasurement(None, unit, missing_reason="The API snapshot has no value.")
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            raise ValueError(f"VPN peer source field {name} must be a non-negative finite number.")
        return MetricMeasurement(value, unit, sample_count=1)

    @staticmethod
    def raw_fields(row: Mapping[str, object]) -> dict[str, float | int | None]:
        """Retain all documented peer scalars and last-seen time without normalization."""
        fields: dict[str, float | int | None] = {}
        for name in ("loss", "latency", "jitter", "mos", "last_seen"):
            value = row.get(name)
            if value is not None and (
                isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)
            ):
                raise ValueError(f"VPN peer source field {name} must be a finite number or None.")
            fields[name] = value
        return fields

    @classmethod
    def sample(
        cls, row: dict[str, Any], org_id: str, sampled_at: datetime, collected_at: datetime, partial: bool
    ) -> SampleMeasurement:
        """Build a poll-time sample from the verified peer identity and scalar fields."""
        state = row.get("up")
        return SampleMeasurement(
            PeerPathIdentity.from_stats_row(row, org_id),
            sampled_at,
            collected_at,
            cls.parse(row),
            cls.raw_fields(row),
            "poll",
            partial,
            "live",
            state if isinstance(state, bool) else None,
        )


class SnapshotRecords:
    """Keep latest observations separate from inferred duration or availability."""

    @classmethod
    def build(cls, snapshot: dict[str, Any]) -> tuple[HourlyMeasurement, ...]:
        """Validate tenant identity and retain the actual collection timestamp."""
        if snapshot.get("provenance") != "live":
            raise ValueError("WAN snapshots must have live provenance.")
        instant = datetime.fromisoformat(snapshot["collected_at_utc"])
        logger.info("Normalize WAN snapshots into observation-hour records.")
        ports = tuple(cls._port(row, snapshot["org_id"], instant) for row in snapshot["ports"])
        peers = tuple(cls._peer(row, snapshot["org_id"], instant) for row in snapshot["peers"])
        insights = cls._insights(snapshot.get("insights", {}), snapshot["org_id"], instant)
        logger.debug("Normalized %d WAN observation records.", len(ports) + len(peers) + len(insights))
        return ports + peers + insights

    @classmethod
    def build_samples(cls, snapshot: dict[str, Any]) -> tuple[SampleMeasurement, ...]:
        """Keep every source observation outside the one-record-per-hour projection."""
        if snapshot.get("provenance") != "live":
            raise ValueError("WAN samples must have live provenance.")
        instant = datetime.fromisoformat(snapshot["collected_at_utc"])
        org_id = snapshot["org_id"]
        logger.info("Build timestamped raw samples from the WAN poll.")
        ports = tuple(
            PortSnapshotMetrics.sample(row, org_id, instant, instant, snapshot.get("ports_partial", False))
            for row in snapshot["ports"]
        )
        peers = tuple(
            PeerSnapshotMetrics.sample(row, org_id, instant, instant, snapshot.get("peers_partial", False))
            for row in snapshot["peers"]
        )
        insights = SnapshotRates.samples(snapshot.get("insights", {}), org_id, instant)
        samples = ports + peers + insights
        logger.debug("Built %d timestamped raw WAN samples.", len(samples))
        return samples

    @classmethod
    def _insights(cls, insight: dict[str, Any], org_id: str, instant: datetime) -> tuple[HourlyMeasurement, ...]:
        """Keep catalog units and source hourly timestamps in gateway history."""
        if not insight.get("samples"):
            return ()
        gateway = GatewayIdentity.from_stats_row(insight["gateway"], org_id)
        identity = CircuitIdentity(gateway, insight["port_id"]) if insight.get("port_id") is not None else gateway
        samples = insight["samples"]
        expected = {"rx_bps", "tx_bps"}
        if isinstance(identity, CircuitIdentity):
            expected.update(
                {
                    "avg_loss_pct",
                    "avg_jitter_ms",
                    "avg_latency_ms",
                    "utilization_pct",
                    "congestion_minutes_over_70_pct",
                    "congestion_minutes_over_80_pct",
                    "congestion_minutes_over_90_pct",
                    "up_minutes",
                    "down_minutes",
                    "flap_count",
                }
            )
        if len(samples) != len(expected) or {sample["metric"] for sample in samples} != expected:
            raise ValueError("Gateway insights require the requested hourly metric samples.")
        hours = {sample["hour_start_utc"] for sample in samples}
        if len(hours) != 1:
            raise ValueError("Gateway insight metrics must use the same UTC hour.")
        metrics = {sample["metric"]: SnapshotRates.parse_sample(sample) for sample in samples}
        return (HourlyMeasurement(identity, datetime.fromisoformat(hours.pop()), instant, metrics, "live"),)

    @classmethod
    def _port(cls, row: dict[str, Any], org_id: str, instant: datetime) -> HourlyMeasurement:
        """Store only bit rates, not cumulative counters or unverified speed units."""
        identity = CircuitIdentity(GatewayIdentity.from_stats_row(row, org_id), row["port_id"])
        metrics = PortSnapshotMetrics.parse(row)
        return HourlyMeasurement(
            identity,
            instant.replace(minute=0, second=0, microsecond=0),
            instant,
            metrics,
            "live",
            row.get("up") if isinstance(row.get("up"), bool) else None,
        )

    @classmethod
    def _peer(cls, row: dict[str, Any], org_id: str, instant: datetime) -> HourlyMeasurement:
        """Use the full peer path fields for a stable derived identity."""
        identity = PeerPathIdentity.from_stats_row(row, org_id)
        return HourlyMeasurement(
            identity,
            instant.replace(minute=0, second=0, microsecond=0),
            instant,
            PeerSnapshotMetrics.parse(row),
            "live",
            row.get("up") if isinstance(row.get("up"), bool) else None,
        )


class SnapshotRates:
    """Validate WAN metric values with explicit source or catalog units."""

    @staticmethod
    def parse(value: object, unit: str) -> MetricMeasurement:
        """Preserve zero while rejecting invalid or negative metric values."""
        if value is None:
            return MetricMeasurement(None, unit, missing_reason="The API snapshot has no value.")
        if isinstance(value, str):
            value = float(value)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
            raise ValueError("WAN metric value must be a non-negative finite number.")
        return MetricMeasurement(value, unit, sample_count=1)

    @staticmethod
    def parse_sample(sample: dict[str, Any]) -> MetricMeasurement:
        """Retain raw samples and explicit coverage for live insight measurements."""
        value = sample["value"]
        if isinstance(value, str):
            value = float(value)
        missing_reason = sample.get("missing_reason")
        if value is None:
            if not isinstance(missing_reason, str) or not missing_reason.strip():
                missing_reason = "The API snapshot has no value."
        elif missing_reason is not None:
            raise ValueError("Present insight values cannot have a missing reason.")
        raw_values = sample.get("raw_values")
        if raw_values is not None:
            raw_values = tuple(raw_values)
        return MetricMeasurement(
            value,
            sample["unit"],
            sample.get("sample_count"),
            sample.get("coverage_fraction"),
            missing_reason,
            raw_values,
        )

    @classmethod
    def samples(cls, insight: dict[str, Any], org_id: str, collected_at: datetime) -> tuple[SampleMeasurement, ...]:
        """Preserve API-timestamped rates and separately retain scalar port stats."""
        if not insight.get("samples") and insight.get("quality_fields") is None:
            return ()
        gateway = GatewayIdentity.from_stats_row(insight["gateway"], org_id)
        port_name = insight.get("port_id")
        identity = CircuitIdentity(gateway, port_name) if isinstance(port_name, str) else gateway
        rate_samples = cls._rate_samples(insight.get("samples", []), identity, collected_at)
        quality_sample = cls._quality_sample(insight, identity, collected_at)
        return rate_samples + ((quality_sample,) if quality_sample is not None else ())

    @classmethod
    def _rate_samples(
        cls, sources: list[dict[str, Any]], identity: GatewayIdentity | CircuitIdentity, collected_at: datetime
    ) -> tuple[SampleMeasurement, ...]:
        """Pair each rate value with its own API timestamp and verified unit."""
        grouped: dict[datetime, dict[str, MetricMeasurement]] = {}
        for source in sources:
            metric_name = source.get("metric")
            if metric_name not in {"rx_bps", "tx_bps"}:
                continue
            for point in source.get("points", []):
                timestamp = datetime.fromisoformat(point["timestamp"])
                grouped.setdefault(timestamp, {})[metric_name] = cls.parse(point["value"], source["unit"])
        missing = MetricMeasurement(None, "bit/s", missing_reason="The API insight has no value for this sample.")
        return tuple(
            SampleMeasurement(
                identity,
                timestamp,
                collected_at,
                {name: metrics.get(name, missing) for name in ("rx_bps", "tx_bps")},
                {},
                "api",
                False,
                "live",
            )
            for timestamp, metrics in sorted(grouped.items())
        )

    @classmethod
    def _quality_sample(
        cls, insight: dict[str, Any], identity: GatewayIdentity | CircuitIdentity, collected_at: datetime
    ) -> SampleMeasurement | None:
        """Store unnormalized port scalars at poll time, not an assumed source time."""
        fields = insight.get("quality_fields")
        if fields is None:
            return None
        metric_sources = {
            "loss": "avg_loss_pct",
            "jitter": "avg_jitter_ms",
            "latency": "avg_latency_ms",
        }
        metrics = {
            metric_name: MetricMeasurement(
                None,
                "unknown",
                missing_reason=(
                    "The API snapshot has no value."
                    if fields.get(source_name) is None
                    else "The gateway port stats schema does not define this field's unit."
                ),
            )
            for source_name, metric_name in metric_sources.items()
        }
        state = fields.get("up")
        return SampleMeasurement(
            identity,
            collected_at,
            collected_at,
            metrics,
            {name: fields[name] for name in ("loss", "jitter", "latency")},
            "poll",
            insight.get("quality_partial", False),
            "live",
            state if isinstance(state, bool) else None,
        )


class PortSnapshotMetrics:
    """Use documented gateway Mbps capacity for directional snapshot utilization."""

    @classmethod
    def parse(cls, row: dict[str, Any]) -> dict[str, MetricMeasurement]:
        """Keep optional invalid rates unknown without inventing observed duration."""
        logger.info("Validate directional port snapshot rates and utilization.")
        metrics = {name: cls._rate(name, row.get(name)) for name in ("rx_bps", "tx_bps")}
        utilization = {
            name.removesuffix("_bps") + "_utilization_percent": cls._utilization(metric, row.get("speed"))
            for name, metric in metrics.items()
        }
        quality = {
            metric: MetricMeasurement(
                None,
                "unknown",
                missing_reason=(
                    "The API snapshot has no value."
                    if row.get(source_name) is None
                    else "The gateway port stats schema does not define this field's unit."
                ),
            )
            for source_name, metric in (
                ("loss", "avg_loss_pct"),
                ("jitter", "avg_jitter_ms"),
                ("latency", "avg_latency_ms"),
            )
        }
        logger.debug("Validated %d directional port snapshot metrics.", len(metrics) + len(utilization) + len(quality))
        return {**metrics, **utilization, **quality}

    @staticmethod
    def raw_fields(row: dict[str, Any]) -> dict[str, float | int | None]:
        """Retain gateway port quality scalars without assigning undocumented units."""
        fields: dict[str, float | int | None] = {}
        for name in ("loss", "jitter", "latency"):
            value = row.get(name)
            if value is not None and (
                isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)
            ):
                raise ValueError(f"Gateway port source field {name} must be a finite number or None.")
            fields[name] = value
        return fields

    @classmethod
    def sample(
        cls, row: dict[str, Any], org_id: str, sampled_at: datetime, collected_at: datetime, partial: bool
    ) -> SampleMeasurement:
        """Build one raw gateway port observation with verified identity and poll time."""
        state = row.get("up")
        return SampleMeasurement(
            CircuitIdentity(GatewayIdentity.from_stats_row(row, org_id), row["port_id"]),
            sampled_at,
            collected_at,
            cls.parse(row),
            cls.raw_fields(row),
            "poll",
            partial,
            "live",
            state if isinstance(state, bool) else None,
        )

    @staticmethod
    def _rate(name: str, value: object) -> MetricMeasurement:
        """Report invalid optional rates instead of discarding valid adjacent observations."""
        try:
            return SnapshotRates.parse(value, "bit/s")
        except (ValueError, OverflowError):
            logger.error("Invalid port snapshot rate %s. The observation remains unknown.", name)
            return MetricMeasurement(None, "bit/s", missing_reason="Invalid API port rate.")

    @staticmethod
    def _utilization(rate: MetricMeasurement, speed: object) -> MetricMeasurement:
        """Convert Mbps to bit/s without treating an observation as full-hour coverage."""
        missing = "Utilization requires a valid rate and positive integer link speed in Mbps."
        if rate.value is None:
            return MetricMeasurement(None, "%", missing_reason=missing)
        if isinstance(speed, bool) or not isinstance(speed, int) or speed <= 0:
            if speed is not None:
                logger.error("Invalid port link speed. Snapshot utilization remains unknown.")
            return MetricMeasurement(None, "%", missing_reason=missing)
        try:
            return MetricMeasurement(rate.value / speed / 1_000_000 * 100, "%", sample_count=1)
        except (ValueError, OverflowError):
            logger.error("Port utilization is not a finite representable value.")
            return MetricMeasurement(None, "%", missing_reason=missing)


class SnapshotStates:
    """Keep current port and VPN state metadata outside historical numeric aggregates."""

    @classmethod
    def build(
        cls, snapshot: dict[str, Any], records: tuple[HourlyMeasurement, ...]
    ) -> dict[tuple[str, ...], dict[str, str]]:
        """Join validated source rows to their complete observation identities."""
        logger.info("Validate current WAN snapshot state metadata.")
        rows = snapshot["ports"] + snapshot["peers"]
        states = {}
        for row, record in zip(rows, records[: len(rows)], strict=True):
            values = {"Current link state": cls._boolean(row.get("up"), "Up", "Down")}
            if isinstance(record.identity, PeerPathIdentity):
                values["Redundant path"] = cls._boolean(row.get("is_active"), "Active", "Standby")
                values["Gateway-reported uptime (s)"] = cls._seconds(row.get("uptime"))
                values["Last observed (UTC)"] = cls._last_seen(row.get("last_seen"))
            states[record.natural_key] = values
        logger.debug("Validated current state metadata for %d WAN observations.", len(states))
        return states

    @staticmethod
    def _boolean(value: object, true_label: str, false_label: str) -> str:
        """Preserve actual booleans rather than interpreting truthy values."""
        if isinstance(value, bool):
            return true_label if value else false_label
        if value is not None:
            logger.error("Invalid WAN state value for %s/%s.", true_label, false_label)
        return "Unknown"

    @staticmethod
    def _seconds(value: object) -> str:
        """Preserve reported integer uptime, including zero, without inferring availability."""
        if value is None:
            return "Unknown"
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            logger.error("Invalid gateway-reported VPN uptime. Current uptime remains unknown.")
            return "Unknown"
        return str(value)

    @staticmethod
    def _last_seen(value: object) -> str:
        """Convert the documented epoch-second observation timestamp into explicit UTC."""
        if value is None:
            return "Unknown"
        try:
            if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
                raise ValueError("The observation timestamp must use non-negative epoch seconds.")
            return datetime.fromtimestamp(value, UTC).isoformat()
        except (ValueError, OverflowError, OSError):
            logger.error("Invalid VPN observation timestamp. The last observation time remains unknown.")
            return "Unknown"

    @staticmethod
    def gateways(records: tuple[HourlyMeasurement, ...]) -> tuple[GatewayIdentity, ...]:
        """List every distinct gateway returned by the bounded cached pages."""
        logger.info("Select distinct gateway identities from cached WAN observations.")
        identities = {
            record.identity if isinstance(record.identity, GatewayIdentity) else record.identity.gateway
            for record in records
        }
        result = tuple(sorted(identities, key=lambda identity: identity.natural_key))
        logger.debug("Selected %d distinct cached gateway identities.", len(result))
        return result
