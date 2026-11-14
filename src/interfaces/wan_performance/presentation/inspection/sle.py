"""Inspect documented site SLE responses without inventing score or duration semantics."""

import logging
import math
from dataclasses import dataclass
from typing import Any

from mistapi.api.v1.sites.sle import listSiteSleImpactedGateways, listSiteSlesMetrics

from src.interfaces.wan_performance.collection.live_service import LiveService
from src.interfaces.wan_performance.collection.snapshot_records import SnapshotRecords, SnapshotStates
from src.interfaces.wan_performance.domain.identity import IdentityValidator

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SleResult:
    """Keep enabled choices and unconverted response values separate from WAN history."""

    metrics: tuple[str, ...]
    gateways: tuple[dict[str, Any], ...] = ()
    total: int | None = None


class SleValidation:
    """Reject malformed responses instead of presenting them as empty successful queries."""

    @staticmethod
    def body(response: Any) -> dict[str, Any]:
        """Require one successful object response from the installed SDK."""
        if response.status_code != 200:
            raise ConnectionError(f"SLE request failed with HTTP {response.status_code}.")
        if not isinstance(response.data, dict):
            raise ValueError("SLE response must be an object.")
        return response.data

    @classmethod
    def catalog(cls, response: Any) -> tuple[str, ...]:
        """Allow only explicitly supported and enabled metric identifiers."""
        body = cls.body(response)
        supported, enabled = body.get("supported"), body.get("enabled")
        if not isinstance(supported, list) or not isinstance(enabled, list):
            raise ValueError("SLE catalog requires supported and enabled arrays.")
        for value in supported + enabled:
            IdentityValidator.identifier(value, "SLE metric")
        return tuple(sorted(set(supported).intersection(enabled)))

    @classmethod
    def gateways(cls, response: Any, metrics: tuple[str, ...], metric: str) -> SleResult:
        """Preserve at most one bounded page with an optional reported total."""
        body = cls.body(response)
        if body.get("metric", metric) != metric:
            raise ValueError("SLE response metric does not match the requested catalog choice.")
        rows, total = body.get("gateways"), body.get("total_count")
        if not isinstance(rows, list) or len(rows) > 1000:
            raise ValueError("SLE gateways require an array with at most 1000 rows.")
        if total is not None and (isinstance(total, bool) or not isinstance(total, int) or total < len(rows)):
            raise ValueError("SLE total must be an integer no smaller than the returned row count.")
        for row in rows:
            cls.row(row)
        return SleResult(metrics, tuple(rows), total)

    @staticmethod
    def row(row: Any) -> None:
        """Validate identity and numeric source fields without assigning units."""
        if not isinstance(row, dict):
            raise ValueError("SLE gateway rows must be objects.")
        gateway_mac = row.get("gateway_mac")
        if not isinstance(gateway_mac, str):
            raise ValueError("SLE gateway rows require a gateway_mac string.")
        IdentityValidator.peer_mac(gateway_mac)
        SleValidation.text(row)
        for field in ("degraded", "total", "duration"):
            value = row.get(field)
            if value is not None and (
                isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0
            ):
                raise ValueError(f"SLE {field} must be a finite nonnegative number or absent.")

    @staticmethod
    def text(row: dict[str, Any]) -> None:
        """Accept only bounded optional labels for the displayed source fields."""
        for field in ("name", "gateway_model"):
            value = row.get(field)
            if value is not None and (not isinstance(value, str) or len(value) > 256):
                raise ValueError(f"SLE {field} must be absent or a string of at most 256 characters.")


class SleReader:
    """Use cached tenant membership and shared ownership for explicit read-only SDK requests."""

    @staticmethod
    def sites(service: LiveService) -> tuple[str, ...]:
        """Restrict the operator to sites already verified in the cached organization."""
        snapshot = service.store.cached(service.org_id)
        if snapshot is None or snapshot.get("org_id") != service.org_id:
            raise ValueError("SLE inspection requires a cached snapshot for the selected organization.")
        gateways = SnapshotStates.gateways(SnapshotRecords.build(snapshot))
        if any(gateway.site.org_id != service.org_id for gateway in gateways):
            raise ValueError("SLE cached site membership conflicts with the selected organization.")
        return tuple(sorted({gateway.site.site_id for gateway in gateways}))

    @staticmethod
    def read(service: LiveService, site_id: str, metric: str) -> SleResult:
        """Read a catalog and optionally one impacted-gateway page through the same lease."""
        IdentityValidator.identifier(site_id, "site_id")
        if site_id not in SleReader.sites(service):
            raise ValueError("SLE site is absent from the cached organization.")
        if metric:
            IdentityValidator.identifier(metric, "SLE metric")
        logger.info("Read the SLE catalog for cached site %s.", site_id)
        lease = service.store.acquire(service.org_id)
        lease.check()
        metrics = SleValidation.catalog(listSiteSlesMetrics(service.session, site_id, "site", site_id))
        logger.debug("Read %s enabled SLE catalog choices.", len(metrics))
        if not metric:
            return SleResult(metrics)
        if metric not in metrics:
            raise ValueError("SLE metric is not both supported and enabled for the selected site.")
        logger.info("Read one impacted-gateway SLE page for site %s and metric %s.", site_id, metric)
        lease.check()
        result = SleValidation.gateways(
            listSiteSleImpactedGateways(service.session, site_id, "site", site_id, metric, duration="1h"),
            metrics,
            metric,
        )
        logger.debug("Read %s SLE gateway rows with reported total %s.", len(result.gateways), result.total)
        return result
