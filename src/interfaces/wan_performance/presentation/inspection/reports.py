"""Inspect supported SLE responses and rank scoped observations without inferred performance semantics."""

import json
import logging
import math
from collections import Counter
from dataclasses import dataclass
from typing import Any

from flask import abort, request
from mistapi.api.v1.sites.sle import listSiteSleImpactedGateways, listSiteSlesMetrics

from src.interfaces.wan_performance.collection.live_service import LiveService
from src.interfaces.wan_performance.collection.snapshot_records import SnapshotRecords, SnapshotStates
from src.interfaces.wan_performance.domain.identity import IdentityValidator
from src.interfaces.wan_performance.domain.measurement import HourlyMeasurement
from src.interfaces.wan_performance.presentation.inspection.windows import RetainedWindow

logger = logging.getLogger(__name__)


class ObservationRanking:
    """Order existing scoped values without additional acquisition or unit conversion."""

    @staticmethod
    def from_request() -> dict[str, str]:
        """Validate bounded ranking controls before any cache or history access."""
        source, direction = request.args.get("rank_source", "cached"), request.args.get("rank_direction", "desc")
        token = request.args.get("rank_metric", "")
        try:
            if source not in {"cached", "retained"} or direction not in {"asc", "desc"} or len(token) > 2048:
                raise ValueError("Select cached or retained ranking and ascending or descending order.")
            if not token:
                return {"source": source, "direction": direction, "metric": "", "unit": ""}
            match json.loads(token):
                case [str(metric), str(unit)] if max(len(metric), len(unit)) <= 128 and (metric + unit).isprintable():
                    return {"source": source, "direction": direction, "metric": metric, "unit": unit}
                case _:
                    raise ValueError("Select one exact metric and unit pair.")
        except (ValueError, TypeError):
            logger.exception("Rejected WAN observation ranking controls.")
            abort(400, description="Select valid bounded observation ranking controls.")

    @classmethod
    def build(
        cls,
        records: tuple[HourlyMeasurement, ...],
        retained: RetainedWindow | None,
        options: dict[str, str],
        org_id: object,
    ) -> dict[str, Any]:
        """Keep full route population, missing counts, and twenty-row display bounds explicit."""
        population, error = cls._scope(records, retained, options["source"], org_id)
        choices = (
            tuple(
                (json.dumps([name, unit]), f"{name} [{unit}]")
                for name, unit in sorted(
                    {(name, metric.unit) for record in population for name, metric in record.metrics.items()}
                )
            )
            if not error
            else ()
        )
        logger.info("Rank %s scoped %s WAN observations.", len(population), options["source"])
        allowed = bool(options["metric"]) and not error
        rows = cls._rows(population, options) if allowed else ()
        counts = cls._counts(population, options, len(rows)) if allowed else {}
        logger.debug("Ranked %s eligible observations and displayed %s.", len(rows), min(20, len(rows)))
        return {
            "options": options,
            "choices": choices,
            "rows": rows[:20],
            "counts": counts,
            "error": error or (None if options["metric"] else "Select an exact metric and unit to rank observations."),
        }

    @staticmethod
    def _scope(
        records: tuple[HourlyMeasurement, ...], retained: RetainedWindow | None, source: str, org_id: object
    ) -> tuple[tuple[HourlyMeasurement, ...], str | None]:
        """Refuse foreign, duplicated, or oversized input rather than expose a partial ranking."""
        if source == "retained":
            if retained is None:
                return (), "Ranking is unavailable without a selected retained window."
            records = retained.records
            if retained.error:
                return (), retained.error
        if any(
            (
                not isinstance(org_id, str),
                len(records) > 10000,
                len({row.natural_key for row in records}) != len(records),
                any(row.provenance != "live" or row.identity.to_dict()["org_id"] != org_id for row in records),
            )
        ):
            logger.error("WAN ranking has invalid organization context or population bounds.")
            return (), "Ranking is unavailable because its organization context, identity, or population is invalid."
        return records, None

    @staticmethod
    def _rows(records: tuple[HourlyMeasurement, ...], options: dict[str, str]) -> tuple[dict[str, Any], ...]:
        """Order numeric values and retain ascending full-identity and time tie keys."""
        entries = tuple(
            (record, metric.value)
            for record in records
            if (metric := record.metrics.get(options["metric"])) is not None
            and metric.unit == options["unit"]
            and metric.value is not None
        )
        sign = -1 if options["direction"] == "desc" else 1
        ordered = sorted(
            entries,
            key=lambda item: (
                sign * item[1],
                item[0].identity.natural_key,
                item[0].hour_start_utc,
                item[0].collected_at_utc,
            ),
        )
        return tuple(
            {
                "identity": record.identity.to_dict(),
                "hour": record.hour_start_utc.isoformat(),
                "collected": record.collected_at_utc.isoformat(),
                "value": value,
            }
            for record, value in ordered
        )

    @staticmethod
    def _counts(records: tuple[HourlyMeasurement, ...], options: dict[str, str], eligible: int) -> dict[str, Any]:
        """Keep absent metrics, missing values, and incompatible units separate."""
        reasons = Counter(
            (
                "metric"
                if (metric := record.metrics.get(options["metric"])) is None
                else "unit" if metric.unit != options["unit"] else "value" if metric.value is None else "present"
            )
            for record in records
        )
        return {
            "population": len(records),
            "eligible": eligible,
            "shown": min(20, eligible),
            "missing": {"metric": reasons["metric"], "value": reasons["value"]},
            "unit_mismatch": reasons["unit"],
        }


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
