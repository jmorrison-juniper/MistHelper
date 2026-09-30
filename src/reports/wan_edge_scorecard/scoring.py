"""Pure scoring helpers for the organization WAN edge scorecard."""

from __future__ import annotations  # Allow modern annotations on all supported runtimes.

import logging  # Record invalid threshold values without exposing secrets.
import os  # Read the DHCP threshold environment override.
from collections import Counter  # Count versions for the predominant version.
from collections.abc import Iterable  # Type iterable row inputs without forcing lists.
from typing import Any  # Accept Mist rows with optional fields.

from src.reports.wan_edge_scorecard.models import (  # Reuse shared scorecard models.
    GatewayScorecardRow,
    OrganizationScorecard,
    SiteScorecardRow,
)

logger = logging.getLogger(__name__)  # Use the module name for report scoring logs.
DEFAULT_DHCP_POOL_WARN_PERCENT = 80.0  # Use the required default DHCP warning threshold.
UPTIME_OK_DAYS = 1.0  # Treat gateways with at least one day of uptime as healthy.


class WanEdgeScoring:
    """Pure scoring functions for WAN edge report rows."""

    @staticmethod
    def safe_percent(part: int | float, whole: int | float) -> float | None:
        """Return a rounded percent, or None when the denominator is unsafe."""
        if whole <= 0:  # Avoid division by zero and invalid negative totals.
            return None  # Use an empty output value when a safe percent cannot be calculated.
        percent = (float(part) / float(whole)) * 100.0  # Convert the ratio into a percentage.
        return round(percent, 2)  # Keep exported values readable and deterministic.

    @staticmethod
    def parse_dhcp_warn_percent(value: str | None = None) -> float:
        """Return the valid DHCP warning threshold, or the default value."""
        raw_value = os.getenv("DHCP_POOL_WARN_PERCENT") if value is None else value  # Read override or test input.
        if raw_value is None or raw_value == "":  # Missing or empty override means use the default.
            return DEFAULT_DHCP_POOL_WARN_PERCENT  # Return the required default threshold.
        try:
            threshold = float(raw_value)  # Parse user input as a numeric percent.
        except ValueError:
            logger.warning("Invalid DHCP_POOL_WARN_PERCENT value %s. Using 80 percent.", raw_value)  # Warn clearly.
            return DEFAULT_DHCP_POOL_WARN_PERCENT  # Fall back without stopping the safe report.
        if threshold < 0 or threshold > 100:  # A percent outside 0 through 100 is invalid.
            logger.warning("Invalid DHCP_POOL_WARN_PERCENT value %s. Using 80 percent.", raw_value)  # Warn clearly.
            return DEFAULT_DHCP_POOL_WARN_PERCENT  # Fall back without stopping the safe report.
        return threshold  # Return the valid operator threshold.

    @staticmethod
    def predominant_version(gateways: Iterable[dict[str, Any]]) -> str:
        """Return the most common non-empty gateway version."""
        versions = [str(row.get("version", "")).strip() for row in gateways if row.get("version")]  # Collect values.
        if not versions:  # No reported version exists in the organization data.
            return ""  # Keep the export empty when there is no safe baseline.
        counts = Counter(versions)  # Count each reported version value.
        version, _count = counts.most_common(1)[0]  # Pick the most common version deterministically.
        return version  # Return the organization baseline version.

    @staticmethod
    def version_compliant(version: str, predominant_version: str) -> bool:
        """Return True when the gateway version matches the organization baseline."""
        return bool(version) and bool(predominant_version) and version == predominant_version  # Compare known values.

    @staticmethod
    def config_success(config_status: str) -> bool:
        """Return True when a configuration status is successful."""
        normalized = config_status.strip().lower()  # Normalize Mist values and fixture values.
        return normalized in {"success", "synced", "in_sync", "ok", "connected"}  # Accept known success states.

    @staticmethod
    def uptime_success(uptime_days: float | None) -> bool:
        """Return True when uptime meets the WAN edge score rule."""
        return uptime_days is not None and uptime_days >= UPTIME_OK_DAYS  # Require a known uptime at least one day.

    @staticmethod
    def anomaly_free(row: GatewayScorecardRow, dhcp_warn_percent: float = DEFAULT_DHCP_POOL_WARN_PERCENT) -> bool:
        """Return True when a gateway row has no scorecard anomaly."""
        has_dhcp_risk = (  # Use the same DHCP warning threshold that marks pool rows.
            row.worst_pool_utilization_percent is not None and row.worst_pool_utilization_percent >= dhcp_warn_percent
        )
        has_peer_risk = row.vpn_peers_down > 0 or row.bgp_peers_not_established > 0  # Peer problems create risk.
        cluster_state = row.cluster_peer_state.lower()  # Normalize cluster text before keyword checks.
        has_cluster_risk = any(
            keyword in cluster_state for keyword in ("down", "fail", "error", "degraded")
        )  # Count clear cluster problem words as potential anomalies.
        has_status_risk = (
            bool(row.last_trouble) or "down" in row.service_status_summary.lower()
        )  # Trouble creates risk.
        return not (has_dhcp_risk or has_peer_risk or has_cluster_risk or has_status_risk)  # True means no risk.

    @staticmethod
    def calculate_site_score(
        site: str, site_id: str, rows: list[GatewayScorecardRow], dhcp_warn_percent: float
    ) -> SiteScorecardRow:
        """Build one site scorecard row from gateway rows."""
        gateway_count = len(rows)  # Count gateways used in this site score.
        config_ok = sum(1 for row in rows if WanEdgeScoring.config_success(row.config_status))  # Count config success.
        version_ok = sum(1 for row in rows if row.version_compliant)  # Count version-compliant gateways.
        uptime_ok = sum(1 for row in rows if WanEdgeScoring.uptime_success(row.uptime_days))  # Count uptime success.
        anomaly_ok = sum(
            1 for row in rows if WanEdgeScoring.anomaly_free(row, dhcp_warn_percent)
        )  # Count anomaly-free gateways.
        return SiteScorecardRow(  # Create the export model for this site.
            site=site,  # Preserve the site display name.
            site_id=site_id,  # Preserve the site identifier.
            gateway_count=gateway_count,  # Preserve the gateway count.
            config_success_percent=WanEdgeScoring.safe_percent(config_ok, gateway_count) or 0.0,  # Score config.
            version_compliance_percent=WanEdgeScoring.safe_percent(version_ok, gateway_count) or 0.0,  # Score version.
            wan_edge_uptime_percent=WanEdgeScoring.safe_percent(uptime_ok, gateway_count) or 0.0,  # Score uptime.
            potential_anomalies_percent=WanEdgeScoring.safe_percent(anomaly_ok, gateway_count) or 0.0,  # Score risk.
        )

    @staticmethod
    def calculate_org_score(rows: list[GatewayScorecardRow], dhcp_warn_percent: float) -> OrganizationScorecard:
        """Build the organization scorecard from gateway rows."""
        site_ids = {row.site_id for row in rows if row.site_id}  # Count only sites with at least one gateway.
        site_count = len(site_ids)  # Store the organization site count.
        gateway_count = len(rows)  # Store the organization gateway count.
        config_ok = sum(1 for row in rows if WanEdgeScoring.config_success(row.config_status))  # Count config success.
        version_ok = sum(1 for row in rows if row.version_compliant)  # Count version compliance.
        uptime_ok = sum(1 for row in rows if WanEdgeScoring.uptime_success(row.uptime_days))  # Count uptime success.
        anomaly_ok = sum(
            1 for row in rows if WanEdgeScoring.anomaly_free(row, dhcp_warn_percent)
        )  # Count anomaly-free gateways.
        return OrganizationScorecard(  # Create the organization score model.
            gateway_count=gateway_count,  # Preserve the gateway count.
            site_count=site_count,  # Preserve the site count.
            config_success_percent=WanEdgeScoring.safe_percent(config_ok, gateway_count) or 0.0,  # Score config.
            version_compliance_percent=WanEdgeScoring.safe_percent(version_ok, gateway_count) or 0.0,  # Score version.
            wan_edge_uptime_percent=WanEdgeScoring.safe_percent(uptime_ok, gateway_count) or 0.0,  # Score uptime.
            potential_anomalies_percent=WanEdgeScoring.safe_percent(anomaly_ok, gateway_count) or 0.0,  # Score risk.
        )
