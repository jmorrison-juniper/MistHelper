"""Collect two bounded latest-stat pages through the existing Mist SDK session."""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol
from uuid import UUID

from mistapi.api.v1.const.insight_metrics import listInsightMetrics
from mistapi.api.v1.orgs.stats import listOrgDevicesStats, searchOrgPeerPathStats, searchOrgSwOrGwPorts
from mistapi.api.v1.sites.insights import getSiteInsightMetricsForGateway

from src.interfaces.portals.wan_performance.domain.identity import IdentityValidator
from src.interfaces.portals.wan_performance.domain.measurement import MetricMeasurement

logger = logging.getLogger(__name__)


class RequestAdmission(Protocol):
    """Require shared ownership before each outgoing API request."""

    def check(self) -> None:
        """Raise when ownership or request admission is unavailable."""


class SnapshotClient:
    """Never run a poll loop, arbitrary pagination, or an implicit retry."""

    def __init__(self, session: Any, admission: RequestAdmission) -> None:
        """Use the injected portal session rather than another token flow."""
        self.session = session
        self.admission = admission

    def collect(self, org_id: str) -> dict[str, object]:
        """Return at most 100 gateway ports and 100 VPN paths for one organization."""
        IdentityValidator.identifier(org_id, "org_id")
        logger.info("Collect bounded WAN snapshot pages for organization %s.", org_id)
        self.admission.check()
        ports = self._page(searchOrgSwOrGwPorts(self.session, org_id, device_type="gateway", limit=100))
        self.admission.check()
        peers = self._page(searchOrgPeerPathStats(self.session, org_id, duration="1h", limit=100))
        insights = GatewayInsights(self.session, self.admission).collect(org_id)
        snapshot = {
            "org_id": org_id,
            "collected_at_utc": datetime.now(UTC).isoformat(),
            "ports": ports[0],
            "peers": peers[0],
            "insights": insights,
            "partial": ports[1] or peers[1] or insights.get("partial", False),
            "provenance": "live",
        }
        logger.debug("Collected %d ports and %d peer paths.", len(ports[0]), len(peers[0]))
        return snapshot

    @staticmethod
    def _page(response: Any) -> tuple[list[dict[str, object]], bool]:
        """Validate one result page and retain an explicit truncation indicator."""
        if response.status_code != 200:
            logger.error("WAN snapshot request failed with HTTP %s.", response.status_code)
            raise ConnectionError(f"WAN snapshot request failed with HTTP {response.status_code}.")
        data = response.data
        if not isinstance(data, dict) or not isinstance(data.get("results"), list):
            raise ValueError("WAN snapshot results must be an array.")
        rows = SnapshotClient._rows(data["results"])
        total = data.get("total", len(rows))
        if isinstance(total, bool) or not isinstance(total, int) or total < 0:
            raise ValueError("WAN snapshot total must be a non-negative integer.")
        return rows, bool(data.get("next")) or total > len(rows)

    @staticmethod
    def _rows(rows: list[object]) -> list[dict[str, object]]:
        """Enforce the fixed page size and dictionary row shape."""
        if len(rows) > 100:
            raise ValueError("WAN snapshot results must contain at most 100 objects.")
        result = []
        for row in rows:
            if not isinstance(row, dict):
                raise ValueError("WAN snapshot results must contain objects.")
            result.append(row)
        return result


class GatewayInsights(SnapshotClient):
    """Read one actual gateway UUID and two independently mapped hourly metric pages."""

    def collect(self, org_id: str) -> dict[str, Any]:
        """Bound discovery to one gateway and never infer device UUIDs from MACs."""
        IdentityValidator.identifier(org_id, "org_id")
        self.admission.check()
        response = listOrgDevicesStats(self.session, org_id, type="gateway", limit=1, page=1)
        device = self._device(response, org_id)
        if device is None:
            return {"samples": [], "partial": False}
        self.admission.check()
        catalog = listInsightMetrics(self.session)
        end = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
        samples = [self._metric(device, name, self._metadata(catalog, name), end) for name in ("rx_bps", "tx_bps")]
        return {"gateway": device, "samples": samples, "partial": bool(getattr(response, "next", None))}

    @staticmethod
    def _device(response: Any, org_id: str) -> dict[str, Any] | None:
        """Reject non-array discovery, wrong tenant, and non-UUID endpoint identifiers."""
        if response.status_code != 200:
            raise ConnectionError(f"Gateway discovery failed with HTTP {response.status_code}.")
        if not isinstance(response.data, list) or len(response.data) > 1:
            raise ValueError("Gateway discovery requires an array with at most one gateway.")
        if not response.data:
            return None
        device = response.data[0]
        if not isinstance(device, dict) or device.get("org_id") != org_id:
            raise ValueError("Gateway discovery organization does not match the selected organization.")
        UUID(device["id"])
        IdentityValidator.identifier(device["site_id"], "site_id")
        IdentityValidator.identifier(device["mac"], "gateway MAC")
        return device

    @staticmethod
    def _metadata(response: Any, name: str) -> str:
        """Use catalog scope, unit, type, interval, and max-age rather than assumed metadata."""
        if response.status_code != 200:
            raise ConnectionError(f"Insight catalog failed with HTTP {response.status_code}.")
        if not isinstance(response.data, dict) or not isinstance(response.data.get(name), dict):
            raise ValueError("The insight catalog has no supported gateway metric.")
        metadata = response.data[name]
        scopes, unit = metadata.get("scopes"), metadata.get("unit")
        if not isinstance(scopes, list) or not {"gateway", "device"}.intersection(scopes):
            raise ValueError("The insight metric does not support gateway scope.")
        if metadata.get("type") != "timeseries":
            raise ValueError("The insight catalog must supply a timeseries unit.")
        unit = MetricMeasurement(None, unit, missing_reason="Catalog metadata validation.").unit
        interval = metadata.get("intervals", {}).get("1h", {})
        if interval.get("interval") != 3600 or interval.get("max_age", 0) < 3600:
            raise ValueError("The insight catalog does not support the requested hourly window.")
        return unit

    def _metric(self, device: dict[str, Any], name: str, unit: str, end: datetime) -> dict[str, Any]:
        """Request one completed UTC hour and one metric to avoid ambiguous series mapping."""
        start = end - timedelta(hours=1)
        self.admission.check()
        response = getSiteInsightMetricsForGateway(
            self.session,
            device["site_id"],
            device["id"],
            name,
            start=str(int(start.timestamp())),
            end=str(int(end.timestamp())),
            interval="1h",
            limit=1,
            page=1,
        )
        if response.status_code != 200:
            raise ConnectionError(f"Gateway insight request failed with HTTP {response.status_code}.")
        return self._sample(response.data, name, unit, start, end)

    @staticmethod
    def _sample(data: Any, name: str, unit: str, start: datetime, end: datetime) -> dict[str, Any]:
        """Validate exact timestamp alignment before assigning a catalog metric name."""
        if not isinstance(data, dict) or (data.get("start"), data.get("end"), data.get("interval")) != (
            int(start.timestamp()),
            int(end.timestamp()),
            3600,
        ):
            raise ValueError("Gateway insight response does not match the requested hourly window.")
        if (
            not isinstance(data.get("rt"), list)
            or not isinstance(data.get("results"), list)
            or len(data["rt"]) != 1
            or len(data["results"]) != 1
        ):
            raise ValueError("Gateway insight values and timestamps must contain one aligned sample.")
        if datetime.fromisoformat(data["rt"][0]) != start:
            raise ValueError("Gateway insight timestamp does not match the requested hour.")
        return {"metric": name, "unit": unit, "hour_start_utc": start.isoformat(), "value": data["results"][0]}
