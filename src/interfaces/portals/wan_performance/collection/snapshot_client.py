"""Collect two bounded latest-stat pages through the existing Mist SDK session."""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol
from uuid import UUID

from mistapi.api.v1.const.insight_metrics import listInsightMetrics
from mistapi.api.v1.orgs.stats import listOrgDevicesStats, searchOrgPeerPathStats, searchOrgSwOrGwPorts
from mistapi.api.v1.sites.insights import getSiteInsightMetricsForDevice, getSiteInsightMetricsForGateway

from src.interfaces.portals.wan_performance.domain.identity import CircuitIdentity, GatewayIdentity, IdentityValidator
from src.interfaces.portals.wan_performance.domain.measurement import MetricMeasurement

logger = logging.getLogger(__name__)


class RequestAdmission(Protocol):
    """Require shared ownership before each outgoing API request."""

    def check(self) -> None:
        """Raise when ownership or request admission is unavailable."""


class SnapshotSession:
    """Share the existing portal session and admission contract between collectors."""

    def __init__(self, session: Any, admission: RequestAdmission) -> None:
        """Use the injected portal session rather than another token flow."""
        self.session = session
        self.admission = admission


class SnapshotClient(SnapshotSession):
    """Never run a poll loop, arbitrary pagination, or an implicit retry."""

    def collect(self, org_id: str, target: GatewayIdentity | None = None) -> dict[str, object]:
        """Return at most 100 gateway ports and 100 VPN paths for one organization."""
        IdentityValidator.identifier(org_id, "org_id")
        if target is not None and target.site.org_id != org_id:
            raise ValueError("The selected gateway organization does not match the portal.")
        logger.info("Collect bounded WAN snapshot pages for organization %s.", org_id)
        self.admission.check()
        ports = self._page(
            searchOrgSwOrGwPorts(
                self.session, org_id, device_type="gateway", mac=target.gateway_id if target else None, limit=100
            )
        )
        self.admission.check()
        peers = self._page(
            searchOrgPeerPathStats(
                self.session,
                org_id,
                mac=target.gateway_id if target else None,
                site_id=target.site.site_id if target else None,
                duration="1h",
                limit=100,
            )
        )
        self._scope(ports[0] + peers[0], target)
        insights = (
            GatewayInsights(self.session, self.admission).collect(org_id, target)
            if target is not None
            else {"samples": [], "partial": False}
        )
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
    def _scope(rows: list[dict[str, object]], target: GatewayIdentity | None) -> None:
        """Refuse returned rows outside the explicitly selected gateway and site."""
        if target is not None and any(
            (row.get("site_id"), row.get("mac")) != (target.site.site_id, target.gateway_id) for row in rows
        ):
            raise ValueError("WAN snapshot rows do not match the selected site and gateway.")

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
        total = data.get("total")
        if total is None:
            return rows, len(rows) == 100 or bool(data.get("next"))
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


class GatewayInsights(SnapshotSession):
    """Read one gateway UUID and its bounded gateway and device insight pages."""

    def collect(self, org_id: str, target: GatewayIdentity) -> dict[str, Any]:
        """Resolve one selected gateway and never infer device UUIDs from MACs."""
        return self._collect(org_id, target, None)

    def collect_for_port(self, org_id: str, target: CircuitIdentity) -> dict[str, Any]:
        """Use five bounded requests for one port and one completed UTC hour."""
        return self._collect(org_id, target.gateway, target.port_name)

    def _collect(self, org_id: str, target: GatewayIdentity, port_name: str | None) -> dict[str, Any]:
        """Share discovery and catalog checks without widening either collection scope."""
        IdentityValidator.identifier(org_id, "org_id")
        if target.site.org_id != org_id:
            raise ValueError("The selected gateway organization does not match the portal.")
        self.admission.check()
        response = listOrgDevicesStats(
            self.session,
            org_id,
            type="gateway",
            site_id=target.site.site_id,
            mac=target.gateway_id,
            limit=2,
            page=1,
        )
        device = self._device(response, org_id, target)
        self.admission.check()
        catalog = listInsightMetrics(self.session)
        end = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
        units = {name: self._metadata(catalog, name) for name in ("rx_bps", "tx_bps")}
        if port_name is not None and any(unit != "bit/s" for unit in units.values()):
            raise ValueError("Port insights require catalog rate units in bit/s.")
        selected = {**device, "selected_port": port_name}
        samples = [self._metric(selected, name, unit, end) for name, unit in units.items()]
        if port_name is not None:
            samples.extend(PortQualityInsights(self.session, self.admission).collect(device, port_name, end))
        return {"gateway": device, "port_id": port_name, "samples": samples, "partial": False}

    @staticmethod
    def _device(response: Any, org_id: str, target: GatewayIdentity) -> dict[str, Any]:
        """Reject non-array discovery, wrong tenant, and non-UUID endpoint identifiers."""
        if response.status_code != 200:
            raise ConnectionError(f"Gateway discovery failed with HTTP {response.status_code}.")
        if not isinstance(response.data, list) or len(response.data) > 1:
            raise ValueError("Gateway discovery requires an array with at most one gateway.")
        if not response.data:
            raise ValueError("The selected gateway is absent from organization discovery.")
        device = response.data[0]
        if not isinstance(device, dict) or device.get("org_id") != org_id:
            raise ValueError("Gateway discovery organization does not match the selected organization.")
        UUID(device["id"])
        IdentityValidator.identifier(device["site_id"], "site_id")
        IdentityValidator.identifier(device["mac"], "gateway MAC")
        if (device["site_id"], device["mac"]) != (target.site.site_id, target.gateway_id):
            raise ValueError("Gateway discovery does not match the selected site and MAC.")
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
            port_id=device.get("selected_port"),
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
    def _timestamps(value: object) -> list[str]:
        """Require string timestamps before date parsing."""
        if not isinstance(value, list) or not all(isinstance(timestamp, str) for timestamp in value):
            raise ValueError("Gateway insight timestamps must be a string array.")
        return [timestamp for timestamp in value if isinstance(timestamp, str)]

    @staticmethod
    def _sample_arrays(data: dict[str, Any], name: str) -> tuple[list[str], list[object]]:
        """Select one unambiguous result array and validate its paired timestamps."""
        has_metric, has_results = name in data, "results" in data
        if has_metric and has_results:
            raise ValueError("Gateway insight response has ambiguous metric values.")
        values = data[name] if has_metric else data.get("results")
        timestamps = GatewayInsights._timestamps(data.get("rt"))
        if not isinstance(values, list) or len(timestamps) != len(values) or len(timestamps) > 1:
            raise ValueError("Gateway insight values and timestamps must contain zero or one aligned sample.")
        return timestamps, values

    @staticmethod
    def _sample(data: Any, name: str, unit: str, start: datetime, end: datetime) -> dict[str, Any]:
        """Validate exact timestamp alignment before assigning a catalog metric name."""
        if not isinstance(data, dict) or (
            data.get("start"),
            data.get("end"),
            data.get("interval"),
            bool(data.get("next")),
        ) != (
            int(start.timestamp()),
            int(end.timestamp()),
            3600,
            False,
        ):
            raise ValueError("Gateway insight response does not match the requested hourly window.")
        timestamps, values = GatewayInsights._sample_arrays(data, name)
        if timestamps and datetime.fromisoformat(timestamps[0]) != start:
            raise ValueError("Gateway insight timestamp does not match the requested hour.")
        return {
            "metric": name,
            "unit": unit,
            "hour_start_utc": start.isoformat(),
            "value": values[0] if values else None,
        }


class PortQualityInsights(SnapshotSession):
    """Read bounded hourly loss, jitter, and latency for one selected gateway port."""

    _FIELDS = {
        "avg_loss": ("avg_loss_pct", "%"),
        "avg_jitter": ("avg_jitter_ms", "ms"),
        "avg_latency": ("avg_latency_ms", "ms"),
    }

    def collect(self, device: dict[str, Any], port_name: str, end: datetime) -> list[dict[str, Any]]:
        """Use the existing device-scoped Mist insight endpoint and shared admission."""
        start = end - timedelta(hours=1)
        mac = device["mac"].replace("-", "")[-12:]
        self.admission.check()
        response = getSiteInsightMetricsForDevice(
            self.session,
            device["site_id"],
            "wan_link_health",
            mac,
            port_id=port_name,
            start=str(int(start.timestamp())),
            end=str(int(end.timestamp())),
            interval="1h",
            limit=1,
            page=1,
        )
        if response.status_code != 200:
            raise ConnectionError(f"Port link-health request failed with HTTP {response.status_code}.")
        return self._samples(response.data, start, end)

    @classmethod
    def _samples(cls, data: Any, start: datetime, end: datetime) -> list[dict[str, Any]]:
        """Validate the requested hour and preserve absent fields as unknown values."""
        if not isinstance(data, dict) or (
            data.get("start"),
            data.get("end"),
            data.get("interval"),
            bool(data.get("next")),
        ) != (int(start.timestamp()), int(end.timestamp()), 3600, False):
            raise ValueError("Port link-health response does not match the requested hourly window.")
        timestamps = cls._timestamps(data.get("rt", []))
        return [
            cls._sample(data, field, metric, unit, timestamps, start) for field, (metric, unit) in cls._FIELDS.items()
        ]

    @staticmethod
    def _timestamps(value: object) -> list[datetime]:
        """Parse at most one UTC timestamp from the response."""
        if not isinstance(value, list) or len(value) > 1:
            raise ValueError("Port link-health timestamps must contain at most one value.")
        if not value:
            return []
        timestamp = value[0]
        if isinstance(timestamp, (int, float)) and not isinstance(timestamp, bool):
            return [datetime.fromtimestamp(timestamp, UTC)]
        if not isinstance(timestamp, str):
            raise ValueError("Port link-health timestamp must be text or epoch seconds.")
        return [datetime.fromisoformat(timestamp.replace("Z", "+00:00"))]

    @staticmethod
    def _sample(
        data: dict[str, Any],
        field: str,
        metric: str,
        unit: str,
        timestamps: list[datetime],
        start: datetime,
    ) -> dict[str, Any]:
        """Map one optional hourly series to its source-compatible name and unit."""
        values = data.get(field, [])
        if values is None:
            values = []
        if not isinstance(values, list) or len(values) > 1:
            raise ValueError(f"Port link-health field {field} must contain at most one value.")
        if values and timestamps and timestamps[0] != start:
            raise ValueError("Port link-health timestamp does not match the requested hour.")
        return {
            "metric": metric,
            "unit": unit,
            "hour_start_utc": start.isoformat(),
            "value": values[0] if values else None,
        }
