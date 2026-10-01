"""Dataclasses for the organization WAN edge scorecard."""

from __future__ import annotations  # Allow forward-compatible annotations.

from dataclasses import dataclass  # Define compact immutable report row contracts.


@dataclass(frozen=True)
class GatewayScorecardRow:
    """One gateway row for `WanEdgeScorecard.csv`."""

    site: str  # Show the site name when Mist provides it.
    site_id: str  # Keep the stable Mist site identifier for filtering.
    gateway_name: str  # Show the gateway name for operator review.
    gateway_id: str  # Keep the stable gateway identifier for joins.
    model: str  # Show the hardware model for upgrade review.
    version: str  # Show the reported software version from statistics.
    predominant_version: str  # Show the organization baseline version.
    version_compliant: bool  # Mark gateways that match the baseline.
    config_status: str  # Show the configuration status from statistics.
    ha_state: str  # Show the HA state when available.
    cluster_peer_state: str  # Show the cluster peer state when available.
    service_status_summary: str  # Summarize available service state values.
    dhcp_pool_count: int  # Count DHCP pools without failing when data is absent.
    worst_pool_utilization_percent: float | None  # Show the highest safe DHCP utilization.
    vpn_peers_up: int  # Count VPN peers that report up.
    vpn_peers_down: int  # Count VPN peers that report down.
    bgp_peers_established: int  # Count BGP peers in the established state.
    bgp_peers_not_established: int  # Count BGP peers in all other states.
    uptime_days: float | None  # Convert uptime seconds into days when possible.
    last_trouble: str  # Show the latest trouble evidence when available.

    def as_dict(self) -> dict[str, object]:
        """Return the CSV and backend export shape."""
        return {  # Keep column names stable for the contract.
            "site": self.site,  # Preserve the site display name.
            "site_id": self.site_id,  # Preserve the site identifier.
            "gateway_name": self.gateway_name,  # Preserve the gateway display name.
            "gateway_id": self.gateway_id,  # Preserve the gateway identifier.
            "model": self.model,  # Preserve the gateway model.
            "version": self.version,  # Preserve the gateway version.
            "predominant_version": self.predominant_version,  # Preserve the organization baseline.
            "version_compliant": self.version_compliant,  # Preserve the baseline comparison result.
            "config_status": self.config_status,  # Preserve the configuration state.
            "ha_state": self.ha_state,  # Preserve the HA state.
            "cluster_peer_state": self.cluster_peer_state,  # Preserve the cluster peer state.
            "service_status_summary": self.service_status_summary,  # Preserve the service summary.
            "dhcp_pool_count": self.dhcp_pool_count,  # Preserve the DHCP pool count.
            "worst_pool_utilization_percent": self.worst_pool_utilization_percent,  # Preserve the DHCP risk value.
            "vpn_peers_up": self.vpn_peers_up,  # Preserve the up VPN peer count.
            "vpn_peers_down": self.vpn_peers_down,  # Preserve the down VPN peer count.
            "bgp_peers_established": self.bgp_peers_established,  # Preserve the established BGP count.
            "bgp_peers_not_established": self.bgp_peers_not_established,  # Preserve the non-established count.
            "uptime_days": self.uptime_days,  # Preserve the uptime score input.
            "last_trouble": self.last_trouble,  # Preserve the latest trouble evidence.
        }


@dataclass(frozen=True)
class DhcpPoolRow:
    """One DHCP pool row for `WanEdgeDhcpPools.csv`."""

    site: str  # Show the parent site name.
    site_id: str  # Keep the parent site identifier.
    gateway_name: str  # Show the parent gateway name.
    gateway_id: str  # Keep the parent gateway identifier.
    pool_name: str  # Show the DHCP pool name.
    leased: int  # Show the leased address count.
    total: int  # Show the total address count.
    percent: float | None  # Show utilization when total is safe.
    warn_threshold_percent: float  # Show the threshold used for this run.
    over_threshold: bool  # Mark pools at or above the threshold.

    def as_dict(self) -> dict[str, object]:
        """Return the CSV and backend export shape."""
        return {  # Keep column names stable for the contract.
            "site": self.site,  # Preserve the site display name.
            "site_id": self.site_id,  # Preserve the site identifier.
            "gateway_name": self.gateway_name,  # Preserve the gateway display name.
            "gateway_id": self.gateway_id,  # Preserve the gateway identifier.
            "pool_name": self.pool_name,  # Preserve the DHCP pool name.
            "leased": self.leased,  # Preserve the leased count.
            "total": self.total,  # Preserve the total count.
            "percent": self.percent,  # Preserve the utilization percentage.
            "warn_threshold_percent": self.warn_threshold_percent,  # Preserve the threshold value.
            "over_threshold": self.over_threshold,  # Preserve the threshold decision.
        }


@dataclass(frozen=True)
class SiteScorecardRow:
    """One site summary row for `WanEdgeScorecardBySite.csv`."""

    site: str  # Show the site name.
    site_id: str  # Keep the Mist site identifier.
    gateway_count: int  # Count gateways that contributed to the site score.
    config_success_percent: float  # Score configuration success for this site.
    version_compliance_percent: float  # Score version compliance for this site.
    wan_edge_uptime_percent: float  # Score uptime for this site.
    potential_anomalies_percent: float  # Score potential anomalies for this site.
    config_unknown_count: int  # Count gateways excluded from the configuration percentage.

    def as_dict(self) -> dict[str, object]:
        """Return the CSV and backend export shape."""
        return {  # Keep column names stable for the contract.
            "site": self.site,  # Preserve the site display name.
            "site_id": self.site_id,  # Preserve the site identifier.
            "gateway_count": self.gateway_count,  # Preserve the site gateway count.
            "config_success_percent": self.config_success_percent,  # Preserve the configuration score.
            "version_compliance_percent": self.version_compliance_percent,  # Preserve the version score.
            "wan_edge_uptime_percent": self.wan_edge_uptime_percent,  # Preserve the uptime score.
            "potential_anomalies_percent": self.potential_anomalies_percent,  # Preserve the anomaly score.
            "config_unknown_count": self.config_unknown_count,  # Preserve the unknown configuration count.
        }


@dataclass(frozen=True)
class OrganizationScorecard:
    """Organization score values printed to the console."""

    gateway_count: int  # Count gateways in the organization score.
    site_count: int  # Count sites that contain at least one gateway.
    config_success_percent: float  # Score organization configuration success.
    version_compliance_percent: float  # Score organization version compliance.
    wan_edge_uptime_percent: float  # Score organization uptime.
    potential_anomalies_percent: float  # Score organization anomaly state.
    config_unknown_count: int  # Count gateways excluded from the configuration percentage.
