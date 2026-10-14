"""Map documented snapshots to observation-hour records, never full-hour coverage."""

import hashlib
import json
import logging
from datetime import datetime
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
        samples = insight["samples"]
        if len(samples) != 2 or {sample["metric"] for sample in samples} != {"rx_bps", "tx_bps"}:
            raise ValueError("Gateway insights require the two requested metric samples.")
        hours = {sample["hour_start_utc"] for sample in samples}
        if len(hours) != 1:
            raise ValueError("Gateway insight metrics must use the same UTC hour.")
        metrics = {sample["metric"]: SnapshotRates.parse(sample["value"], sample["unit"]) for sample in samples}
        return (HourlyMeasurement(gateway, datetime.fromisoformat(hours.pop()), instant, metrics, "live"),)

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
        metrics = {name: SnapshotRates.parse(row.get(name), "bit/s") for name in ("rx_bps", "tx_bps")}
        return HourlyMeasurement(identity, instant.replace(minute=0, second=0, microsecond=0), instant, metrics, "live")

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
        )


class SnapshotRates:
    """Validate source rate values with explicit source or catalog units."""

    @staticmethod
    def parse(value: object, unit: str) -> MetricMeasurement:
        """Preserve zero while rejecting invalid or negative bit rates."""
        if value is None:
            return MetricMeasurement(None, unit, missing_reason="The API snapshot has no value.")
        if isinstance(value, str):
            value = float(value)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
            raise ValueError("WAN bit rate must be a non-negative finite number.")
        return MetricMeasurement(value, unit, sample_count=1)
