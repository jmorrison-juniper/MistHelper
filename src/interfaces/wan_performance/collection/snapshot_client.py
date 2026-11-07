"""Collect bounded current WAN data through the Mist SDK."""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol
from uuid import UUID

from mistapi.api.v1.const.insight_metrics import listInsightMetrics
from mistapi.api.v1.orgs.stats import listOrgDevicesStats, searchOrgPeerPathStats, searchOrgSwOrGwPorts
from mistapi.api.v1.sites.insights import getSiteInsightMetricsForGateway

from src.interfaces.wan_performance.collection.snapshot_records import SnapshotRates
from src.interfaces.wan_performance.domain.identity import GatewayIdentity, IdentityValidator
from src.interfaces.wan_performance.domain.measurement import MetricMeasurement

logger = logging.getLogger(__name__)
SNAPSHOT_PAGE_LIMIT = 100  # Keep each current-state page bounded.
RATE_METRICS = ("rx_bps", "tx_bps")  # Collect only directional rates.


class RequestAdmission(Protocol):
    """Require shared ownership before each outgoing request."""

    def check(self) -> None:
        """Raise when admission or refresh ownership is unavailable."""


class SnapshotPageValidator:
    """Validate bounded SDK pages and report source truncation."""

    @classmethod
    def parse(cls, response: Any) -> tuple[list[dict[str, Any]], bool]:
        """Return one validated result page and its completeness state."""
        if response.status_code != 200:  # HTTP failures are not empty snapshots.
            raise ConnectionError(f"WAN snapshot request failed with HTTP {response.status_code}.")  # Report status.
        data = response.data  # Read the SDK response body.
        if not isinstance(data, dict):  # Require the documented response object.
            raise ValueError("WAN snapshot results must be an array.")  # Reject malformed bodies.
        rows = data.get("results")  # Read the single source page.
        if not isinstance(rows, list) or len(rows) > SNAPSHOT_PAGE_LIMIT:  # Enforce the page bound.
            raise ValueError("WAN snapshot results must contain at most 100 objects.")  # Reject oversized pages.
        if any(not isinstance(row, dict) for row in rows):  # Require object rows.
            raise ValueError("WAN snapshot results must contain at most 100 objects.")  # Reject malformed rows.
        total = data.get("total")  # Read optional source count evidence.
        if not cls._valid_total(total):  # Require well-formed completeness evidence.
            raise ValueError("WAN snapshot total must be a non-negative integer.")  # Reject invalid totals.
        partial = bool(data.get("next")) or cls._is_truncated(rows, total)  # Preserve continuation evidence.
        return rows, partial  # Keep rows and completeness separate.

    @staticmethod
    def _valid_total(total: object) -> bool:
        """Accept only a missing or non-negative integer total."""
        return total is None or (
            isinstance(total, int) and not isinstance(total, bool) and total >= 0
        )  # Reject booleans and negative counts.

    @staticmethod
    def _is_truncated(rows: list[dict[str, Any]], total: object) -> bool:
        """Detect a full page without a total or a known additional row."""
        return (
            len(rows) == SNAPSHOT_PAGE_LIMIT
            if total is None
            else isinstance(total, int) and not isinstance(total, bool) and total > len(rows)
        )  # Keep a conservative bound.


class SnapshotClient:
    """Collect at most one bounded page of ports and peer paths."""

    def __init__(self, session: Any, admission: RequestAdmission) -> None:
        """Reuse the selected portal session and current refresh lease."""
        self.session = session  # Keep the existing authenticated SDK session.
        self.admission = admission  # Keep shared request ownership.

    def collect(self, org_id: str, target: GatewayIdentity | None = None) -> dict[str, object]:
        """Return one live snapshot with an explicit partial-result flag."""
        valid_org = IdentityValidator.identifier(org_id, "org_id")  # Validate tenant scope before requests.
        if target is not None and target.site.org_id != valid_org:  # Enforce selected organization context.
            raise ValueError("The selected gateway organization does not match the portal.")  # Reject scope mismatch.
        logger.info("Collect bounded WAN snapshot pages for organization %s.", valid_org)  # Log safe request scope.
        ports, ports_partial = self._ports(valid_org, target)  # Request one port page.
        peers, peers_partial = self._peers(valid_org, target)  # Request one peer page.
        self._scope(ports + peers, valid_org, target)  # Validate every returned tenant and gateway identity.
        insights = (
            GatewayInsights(self.session, self.admission).collect(valid_org, target)
            if target
            else {  # Keep org scope bounded.
                "gateway": None,  # No gateway was selected for insight collection.
                "port_id": None,  # No circuit was selected for insight collection.
                "samples": [],  # Do not invent insight observations.
                "partial": False,  # No insight request ran.
            }
        )
        snapshot = {  # Return a complete source envelope.
            "org_id": valid_org,  # Preserve tenant scope.
            "collected_at_utc": datetime.now(UTC).isoformat(),  # Record the collection instant.
            "ports": ports,  # Preserve source port rows.
            "peers": peers,  # Preserve source peer rows.
            "insights": insights,  # Keep gateway insights separate.
            "partial": ports_partial or peers_partial or bool(insights["partial"]),  # Report source truncation.
            "provenance": "live",  # Mark the actual source class.
        }
        logger.debug("Collected %d ports and %d peer paths.", len(ports), len(peers))  # Record result counts.
        return snapshot  # Return only validated page shapes.

    def _ports(self, org_id: str, target: GatewayIdentity | None) -> tuple[list[dict[str, Any]], bool]:
        """Request one bounded gateway-port page."""
        self.admission.check()  # Refuse before transport if the refresh lease expired.
        response = searchOrgSwOrGwPorts(  # Use the Mist SDK method.
            self.session,  # Reuse the authenticated session.
            org_id,  # Scope the request to one organization.
            device_type="gateway",  # Request gateway ports only.
            mac=target.gateway_id if target else None,  # Narrow to the selected gateway when present.
            limit=SNAPSHOT_PAGE_LIMIT,  # Bound source response size.
        )
        return SnapshotPageValidator.parse(response)  # Validate the SDK response.

    def _peers(self, org_id: str, target: GatewayIdentity | None) -> tuple[list[dict[str, Any]], bool]:
        """Request one bounded peer-path page."""
        self.admission.check()  # Refuse before transport if the refresh lease expired.
        response = searchOrgPeerPathStats(  # Use the Mist SDK method.
            self.session,  # Reuse the authenticated session.
            org_id,  # Scope the request to one organization.
            mac=target.gateway_id if target else None,  # Narrow to the selected gateway when present.
            site_id=target.site.site_id if target else None,  # Preserve selected site scope.
            duration="1h",  # Limit peer statistics to the previous hour.
            limit=SNAPSHOT_PAGE_LIMIT,  # Bound source response size.
        )
        return SnapshotPageValidator.parse(response)  # Validate the SDK response.

    @staticmethod
    def _scope(rows: list[dict[str, Any]], org_id: str, target: GatewayIdentity | None) -> None:
        """Reject rows outside the selected organization and gateway."""
        for row in rows:  # Validate every returned row before publication.
            if row.get("org_id") != org_id:  # Prevent cross-tenant leakage.
                raise ValueError("WAN snapshot row organization does not match the request.")  # Fail closed.
            if target and (row.get("site_id"), row.get("mac")) != (
                target.site.site_id,
                target.gateway_id,
            ):  # Keep selected scope.
                raise ValueError(
                    "WAN snapshot row does not match the selected site and gateway."
                )  # Reject wrong device.


class GatewayInsightValidator:
    """Validate gateway discovery, catalog metadata, and rate samples."""

    @staticmethod
    def device(response: Any, org_id: str, target: GatewayIdentity) -> dict[str, Any]:
        """Require one discovered gateway with a matching tenant and UUID."""
        if response.status_code != 200:  # HTTP failure is not an absent device.
            raise ConnectionError(f"Gateway discovery failed with HTTP {response.status_code}.")  # Report status.
        rows = response.data  # Read the SDK response body.
        if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):  # Require one exact row.
            raise ValueError("Gateway discovery requires one matching gateway.")  # Reject ambiguity.
        device = rows[0]  # Select the unique gateway.
        if device.get("org_id") != org_id:  # Enforce tenant scope.
            raise ValueError("Gateway discovery organization does not match.")  # Refuse cross-tenant data.
        if (device.get("site_id"), device.get("mac")) != (target.site.site_id, target.gateway_id):  # Match selection.
            raise ValueError("Gateway discovery does not match the selected site and MAC.")  # Refuse wrong device.
        try:  # Validate that the API identifier is a UUID.
            UUID(device["id"])  # Require the returned UUID rather than deriving one from a MAC.
        except (KeyError, TypeError, ValueError) as error:  # Reject absent or malformed identifiers.
            raise ValueError("Gateway discovery requires a valid device UUID.") from error  # Preserve the cause.
        return device  # Keep the exact SDK row for insight calls.

    @staticmethod
    def unit(response: Any, name: str) -> str:
        """Use catalog metadata for the supported one-hour gateway metrics."""
        if response.status_code != 200:  # Catalog failure prevents safe metric interpretation.
            raise ConnectionError(f"Insight catalog failed with HTTP {response.status_code}.")  # Report status.
        data = response.data  # Read the SDK response body.
        item = data.get(name) if isinstance(data, dict) else None  # Read only the named catalog entry.
        if not isinstance(item, dict):  # Require the named metric.
            raise ValueError("Insight catalog has no supported gateway metric.")  # Reject absent metadata.
        supports_gateway, supports_hour = GatewayInsightValidator._catalog_contract(item)  # Check scope and interval.
        if not supports_gateway:  # Require gateway scope and time-series data.
            raise ValueError("Insight metric does not support gateway time-series data.")  # Reject incompatible metric.
        if not supports_hour:  # Require a bounded hourly contract.
            raise ValueError("Insight metric does not support a bounded one-hour window.")  # Reject stale contract.
        unit = item.get("unit")  # Read the source unit.
        if not isinstance(unit, str) or unit not in {"Bps", "bit/s"}:  # Accept only known rate units.
            raise ValueError("Gateway rate insights must use Bps or bit/s catalog units.")  # Reject unknown units.
        MetricMeasurement(None, unit, missing_reason="Catalog metadata validation.")  # Validate unit shape.
        return unit  # Preserve the validated catalog unit.

    @staticmethod
    def _catalog_contract(item: dict[str, Any]) -> tuple[bool, bool]:
        """Report gateway support and bounded-hour support separately."""
        scopes = item.get("scopes")  # Read supported entity scopes.
        intervals = item.get("intervals")  # Read source interval metadata.
        interval = intervals.get("1h") if isinstance(intervals, dict) else None  # Read the one-hour entry.
        gateway_supported = isinstance(scopes, list) and "gateway" in scopes and item.get("type") == "timeseries"
        hour_supported = (
            isinstance(interval, dict) and interval.get("interval") == 3600 and interval.get("max_age", 0) >= 3600
        )
        return gateway_supported, hour_supported  # Preserve exact contract failure context.

    @classmethod
    def samples(
        cls, response: Any, units: dict[str, str], start: datetime, end: datetime
    ) -> tuple[list[dict[str, Any]], bool]:
        """Validate named metric arrays and align them to one bounded hour."""
        if response.status_code != 200:  # HTTP errors are not missing metrics.
            raise ConnectionError(f"Gateway insight request failed with HTTP {response.status_code}.")  # Report status.
        data = response.data  # Read the SDK response body.
        if not isinstance(data, dict):  # Require the documented insight object.
            raise ValueError("Gateway insight response must be an object.")  # Reject malformed bodies.
        expected = (int(start.timestamp()), int(end.timestamp()), 3600, False)  # Define the bounded query.
        actual = (data.get("start"), data.get("end"), data.get("interval"), bool(data.get("next")))  # Read metadata.
        if actual != expected:  # Reject another window or a continuation page.
            raise ValueError("Gateway insight response does not match the requested window.")  # Fail closed.
        timestamps = data.get("rt")  # Read source timestamps.
        if not isinstance(timestamps, list) or not all(
            isinstance(value, str) for value in timestamps
        ):  # Validate times.
            raise ValueError("Gateway insight timestamps must be a string array.")  # Reject malformed time data.
        if len(timestamps) > 1:  # One-hour interval allows one sample.
            raise ValueError("Gateway insight response exceeds the fixed one-sample page.")  # Enforce response bound.
        metrics = [
            GatewayInsightSampleBuilder.build(data, name, unit, timestamps, start) for name, unit in units.items()
        ]  # Validate rates.
        partial = any(metric["sample_count"] != 1 for metric in metrics)  # Mark absent samples as partial.
        return metrics, partial  # Keep completeness explicit.


class GatewayInsightSampleBuilder:
    """Convert one validated insight metric array into normalized rate data."""

    @classmethod
    def build(
        cls, data: dict[str, Any], name: str, unit: str, timestamps: list[str], start: datetime
    ) -> dict[str, Any]:
        """Build one rate sample from an aligned source array."""
        raw_values = cls._values(data, name, unit, timestamps, start)  # Validate and normalize all source values.
        return {  # Preserve one named metric and its interval.
            "metric": name,  # Keep the source metric name.
            "unit": "bit/s",  # Normalize rates for consumers.
            "hour_start_utc": start.isoformat(),  # Preserve the requested interval.
            "value": raw_values[-1] if raw_values else None,  # Keep the latest valid sample.
            "raw_values": tuple(raw_values),  # Preserve source values for later analysis.
            "sample_count": len(raw_values),  # Record the number of valid values.
            "coverage_fraction": float(len(raw_values)),  # A single hourly sample has zero or full coverage.
            "missing_reason": None if raw_values else "The API snapshot has no value.",  # Explain absence.
        }

    @staticmethod
    def _values(data: dict[str, Any], name: str, unit: str, timestamps: list[str], start: datetime) -> list[float]:
        """Validate one paired value array and normalize its measured rates."""
        values = data.get(name)  # Read the exact requested array.
        if not isinstance(values, list) or len(values) != len(timestamps):  # Require paired source values.
            raise ValueError("Gateway insight values and timestamps must align.")  # Reject malformed arrays.
        if timestamps and not GatewayInsightSampleBuilder._matches_hour(timestamps[0], start):
            raise ValueError("Gateway insight timestamp does not match the requested hour.")  # Reject stale data.
        factor = 8 if unit == "Bps" else 1  # Convert bytes per second to bits per second.
        parsed_values = [SnapshotRates.parse(value, unit).value for value in values]  # Validate every source rate.
        return [float(value) * factor for value in parsed_values if value is not None]  # Keep measured values.

    @staticmethod
    def _matches_hour(timestamp: str, start: datetime) -> bool:
        """Require an explicit timestamp that matches the requested UTC hour."""
        instant = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))  # Parse the source time.
        return instant.tzinfo is not None and instant.astimezone(UTC) == start  # Match the requested instant.


class GatewayInsights:
    """Collect one bounded gateway rate insight through the Mist SDK."""

    def __init__(self, session: Any, admission: RequestAdmission) -> None:
        """Reuse the selected authenticated session and refresh lease."""
        self.session = session  # Keep the existing SDK session.
        self.admission = admission  # Keep shared request ownership.

    def collect(self, org_id: str, target: GatewayIdentity | None) -> dict[str, Any]:
        """Collect named one-hour rate metrics for one selected gateway."""
        if target is None:  # Organization snapshots have no selected insight target.
            return {"gateway": None, "port_id": None, "samples": [], "partial": False}  # Do not widen scope.
        valid_org = IdentityValidator.identifier(org_id, "org_id")  # Validate tenant scope.
        if target.site.org_id != valid_org:  # Refuse cross-organization selection.
            raise ValueError("The selected gateway organization does not match the request.")  # Fail closed.
        self.admission.check()  # Reserve before gateway discovery.
        device_response = listOrgDevicesStats(  # Use the Mist SDK inventory method.
            self.session, valid_org, type="gateway", site_id=target.site.site_id, mac=target.gateway_id, limit=2, page=1
        )
        device = GatewayInsightValidator.device(device_response, valid_org, target)  # Validate the returned identity.
        self.admission.check()  # Reserve before catalog lookup.
        catalog = listInsightMetrics(self.session)  # Read units and intervals from the Mist SDK catalog.
        units = {
            name: GatewayInsightValidator.unit(catalog, name) for name in RATE_METRICS
        }  # Validate both rate types.
        end = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)  # End at the current UTC hour.
        start = end - timedelta(hours=1)  # Request the previous complete hour.
        self.admission.check()  # Reserve before insight collection.
        response = getSiteInsightMetricsForGateway(  # Use the Mist SDK insight method.
            self.session,
            device["site_id"],
            device["id"],
            ",".join(RATE_METRICS),
            start=str(int(start.timestamp())),
            end=str(int(end.timestamp())),
            interval="1h",
            limit=1,
            page=1,
        )
        samples, partial = GatewayInsightValidator.samples(
            response, units, start, end
        )  # Validate data and completeness.
        logger.debug("Collected %d gateway insight metrics.", len(samples))  # Record the result count.
        return {"gateway": device, "port_id": None, "samples": samples, "partial": partial}  # Preserve source scope.
