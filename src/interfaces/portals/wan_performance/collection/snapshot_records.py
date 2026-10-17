"""Map documented snapshots to observation-hour records, never full-hour coverage."""

import hashlib
import json
import logging
from datetime import UTC, datetime
from typing import Any

from src.interfaces.portals.wan_performance.collection.peer_metrics import PeerSnapshotMetrics
from src.interfaces.portals.wan_performance.domain.identity import (
    CircuitIdentity,
    GatewayIdentity,
    PeerPathIdentity,
    SiteIdentity,
)
from src.interfaces.portals.wan_performance.domain.measurement import HourlyMeasurement, MetricMeasurement

logger = logging.getLogger(__name__)


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
    def _insights(cls, insight: dict[str, Any], org_id: str, instant: datetime) -> tuple[HourlyMeasurement, ...]:
        """Keep catalog units and source hourly timestamps in gateway history."""
        if not insight.get("samples"):
            return ()
        gateway = cls._gateway(insight["gateway"], org_id)
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

    @staticmethod
    def _gateway(row: dict[str, Any], org_id: str) -> GatewayIdentity:
        """Validate organization membership using explicit SDK row identifiers."""
        if not isinstance(row, dict) or row.get("org_id") != org_id:
            raise ValueError("WAN row organization does not match the selected organization.")
        return GatewayIdentity(SiteIdentity(org_id, row["site_id"]), row["mac"])

    @classmethod
    def _port(cls, row: dict[str, Any], org_id: str, instant: datetime) -> HourlyMeasurement:
        """Store only bit rates, not cumulative counters or unverified speed units."""
        identity = CircuitIdentity(cls._gateway(row, org_id), row["port_id"])
        metrics = PortSnapshotMetrics.parse(row)
        return HourlyMeasurement(
            identity,
            instant.replace(minute=0, second=0, microsecond=0),
            instant,
            metrics,
            "live",
            cls._up_observation(row.get("up")),
        )

    @classmethod
    def _peer(cls, row: dict[str, Any], org_id: str, instant: datetime) -> HourlyMeasurement:
        """Use all remote path fields for a stable derived key, not a claimed tunnel ID."""
        fields = [row.get(name) for name in ("peer_site_id", "peer_port_id", "type")]
        if any(not isinstance(value, str) or not value.strip() for value in fields):
            raise ValueError("WAN peer path requires peer_site_id, peer_port_id, and type.")
        path_key = hashlib.sha256(json.dumps(fields).encode()).hexdigest()
        identity = PeerPathIdentity(cls._gateway(row, org_id), row["port_id"], row["peer_mac"], path_key)
        return HourlyMeasurement(
            identity,
            instant.replace(minute=0, second=0, microsecond=0),
            instant,
            PeerSnapshotMetrics.parse(row),
            "live",
            cls._up_observation(row.get("up")),
        )

    @staticmethod
    def _up_observation(value: object) -> bool | None:
        """Retain only an explicitly reported up/down state."""
        return value if isinstance(value, bool) else None


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
        logger.debug("Validated %d directional port snapshot metrics.", len(metrics) + len(utilization))
        return {**metrics, **utilization}

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
