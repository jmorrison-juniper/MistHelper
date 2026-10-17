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
            {name: MetricMeasurement(**metric) for name, metric in metrics.items()},
            "live",
            row.get("is_up_observation"),
        )

    @staticmethod
    def _identity(values: dict[str, str]) -> CircuitIdentity | GatewayIdentity | PeerPathIdentity:
        """Preserve complete circuit or peer-path identity through serialization."""
        gateway = GatewayIdentity(SiteIdentity(values["org_id"], values["site_id"]), values["gateway_id"])
        if "peer_mac" in values:
            return PeerPathIdentity(gateway, values["port_name"], values["peer_mac"], values["tunnel_identity"])
        if "port_name" not in values:
            return gateway
        return CircuitIdentity(gateway, values["port_name"])
