"""Organization WAN edge scorecard operation."""

from __future__ import annotations  # Keep type annotations import-safe.

import logging  # Log each fetch, transform, and export action.
from collections import defaultdict  # Group gateway rows by site for summaries.
from typing import Any  # Accept Mist gateway rows with optional fields.

from src.config.source_dependency_resolver import SourceDependencyResolver  # Reuse project runtime dependencies.
from src.reports.switch_scorecard.site_lookup import SiteNameLookup  # Enrich live stats with site names.
from src.reports.wan_edge_scorecard.client import WanEdgeGatewayStatsClient  # Reuse the shared fetch seam.
from src.reports.wan_edge_scorecard.models import DhcpPoolRow, GatewayScorecardRow, SiteScorecardRow
from src.reports.wan_edge_scorecard.scoring import WanEdgeScoring  # Reuse pure scoring helpers.

logger = logging.getLogger(__name__)  # Use the module name for report logs.


class WanEdgeScorecard:
    """Build and export the organization WAN edge scorecard."""

    GATEWAY_FIELDNAMES = [  # Keep the main report column order stable.
        "site",
        "site_id",
        "gateway_name",
        "gateway_id",
        "model",
        "version",
        "predominant_version",
        "version_compliant",
        "config_status",
        "ha_state",
        "cluster_peer_state",
        "service_status_summary",
        "dhcp_pool_count",
        "worst_pool_utilization_percent",
        "vpn_peers_up",
        "vpn_peers_down",
        "bgp_peers_established",
        "bgp_peers_not_established",
        "uptime_days",
        "last_trouble",
    ]
    DHCP_FIELDNAMES = [  # Keep the DHCP report column order stable.
        "site",
        "site_id",
        "gateway_name",
        "gateway_id",
        "pool_name",
        "leased",
        "total",
        "percent",
        "warn_threshold_percent",
        "over_threshold",
    ]
    SITE_FIELDNAMES = [  # Keep the site report column order stable.
        "site",
        "site_id",
        "gateway_count",
        "config_success_percent",
        "version_compliance_percent",
        "wan_edge_uptime_percent",
        "potential_anomalies_percent",
        "config_unknown_count",
    ]

    @staticmethod
    def run() -> None:
        """Run the scorecard operation for the active organization."""
        mh = SourceDependencyResolver  # Resolve org id and exporter through the source dependency seam.
        logger.info("Resolving organization for WAN edge scorecard")  # Log before org selection.
        org_id = mh.ConfigUtils.get_cached_or_prompted_org_id()  # Reuse the project organization selection behavior.
        logger.debug("Resolved organization for WAN edge scorecard: %s", bool(org_id))  # Log outcome without secrets.
        if not org_id:  # A missing organization id means the report cannot query Mist.
            logger.warning("No organization was selected. WAN edge scorecard was not generated.")  # Report clearly.
            return  # Stop before any API call.
        logger.info("Fetching WAN edge gateway statistics")  # Log before the fetch action.
        gateway_stats = WanEdgeGatewayStatsClient.fetch_gateway_stats(org_id)  # Fetch gateway rows through one seam.
        logger.debug("Fetched %s WAN edge gateway statistics rows", len(gateway_stats))  # Log fetch count.
        site_names = SiteNameLookup.fetch(org_id)  # Read sites once because gateway stats carry site_id only.
        logger.info("Transforming WAN edge gateway statistics")  # Log before report transformation.
        gateway_rows, dhcp_rows, site_rows, org_score = WanEdgeScorecard.build_reports(
            gateway_stats, site_names
        )  # Build rows.
        logger.debug(
            "Transformed WAN edge rows: gateways=%s, dhcp_pools=%s, sites=%s",
            len(gateway_rows),
            len(dhcp_rows),
            len(site_rows),
        )  # Log transform count.
        WanEdgeScorecard._export_reports(gateway_rows, dhcp_rows, site_rows)  # Write all required outputs.
        WanEdgeScorecard._print_org_summary(org_score)  # Print the operator summary.

    @staticmethod
    def build_reports(
        gateway_stats: list[dict[str, Any]],
        site_names: dict[str, str] | None = None,
    ) -> tuple[list[GatewayScorecardRow], list[DhcpPoolRow], list[SiteScorecardRow], Any]:
        """Build gateway, DHCP, site, and organization scorecard rows."""
        threshold = WanEdgeScoring.parse_dhcp_warn_percent()  # Resolve the DHCP threshold once per run.
        predominant_version = WanEdgeScoring.predominant_version(gateway_stats)  # Compute the organization baseline.
        site_lookup = site_names or {}  # Keep tests simple while live runs pass the listOrgSites map.
        gateway_rows: list[GatewayScorecardRow] = []  # Collect gateway rows for export and summaries.
        dhcp_rows: list[DhcpPoolRow] = []  # Collect DHCP pool evidence rows.
        for gateway in gateway_stats:  # Process each gateway statistics row.
            pools = WanEdgeScorecard._build_dhcp_rows(gateway, threshold, site_lookup)  # Extract DHCP rows.
            dhcp_rows.extend(pools)  # Add pool rows before the gateway summary uses them.
            gateway_rows.append(  # Add one enriched gateway scorecard row.
                WanEdgeScorecard._build_gateway_row(gateway, predominant_version, pools, site_lookup)
            )
        site_rows = WanEdgeScorecard._build_site_rows(
            gateway_rows, threshold
        )  # Build site score rows from gateway rows.
        org_score = WanEdgeScoring.calculate_org_score(
            gateway_rows, threshold
        )  # Build the organization score from rows.
        return gateway_rows, dhcp_rows, site_rows, org_score  # Return all report outputs to the caller.

    @staticmethod
    def _build_gateway_row(
        gateway: dict[str, Any],
        predominant_version: str,
        pools: list[DhcpPoolRow],
        site_names: dict[str, str],
    ) -> GatewayScorecardRow:
        """Build one gateway scorecard row."""
        version = WanEdgeScorecard._text(gateway.get("version"))  # Normalize the optional version value.
        vpn_up, vpn_down = WanEdgeScorecard._count_vpn_peers(gateway.get("vpn_peers"))  # Count VPN peer states.
        bgp_up, bgp_down = WanEdgeScorecard._count_bgp_peers(gateway.get("bgp_peers"))  # Count BGP peer states.
        worst_pool = WanEdgeScorecard._worst_pool_percent(pools)  # Find the highest safe DHCP pool percentage.
        uptime_days = WanEdgeScorecard._uptime_days(gateway.get("uptime"))  # Convert uptime seconds to days.
        return GatewayScorecardRow(  # Build the immutable report row.
            site=WanEdgeScorecard._site_name(gateway, site_names),  # Use a clear site display value.
            site_id=WanEdgeScorecard._text(gateway.get("site_id")),  # Preserve the site identifier.
            gateway_name=WanEdgeScorecard._gateway_name(gateway),  # Use the best available gateway name.
            gateway_id=WanEdgeScorecard._gateway_id(gateway),  # Use the stable gateway identity.
            model=WanEdgeScorecard._text(gateway.get("model")),  # Preserve the gateway model.
            version=version,  # Preserve the normalized version.
            predominant_version=predominant_version,  # Preserve the organization baseline.
            version_compliant=WanEdgeScoring.version_compliant(version, predominant_version),  # Compare versions.
            config_status=WanEdgeScorecard._text(gateway.get("config_status")),  # Preserve config status.
            ha_state=WanEdgeScorecard._ha_state(gateway),  # Summarize HA state.
            cluster_peer_state=WanEdgeScorecard._cluster_peer_state(gateway),  # Summarize cluster peer state.
            service_status_summary=WanEdgeScorecard._service_summary(gateway),  # Summarize service state.
            dhcp_pool_count=len(pools),  # Count pools safely when DHCP data is absent.
            worst_pool_utilization_percent=worst_pool,  # Preserve the highest DHCP utilization.
            vpn_peers_up=vpn_up,  # Preserve the VPN up count.
            vpn_peers_down=vpn_down,  # Preserve the VPN down count.
            bgp_peers_established=bgp_up,  # Preserve the BGP established count.
            bgp_peers_not_established=bgp_down,  # Preserve the BGP non-established count.
            uptime_days=uptime_days,  # Preserve converted uptime.
            last_trouble=WanEdgeScorecard._last_trouble(gateway),  # Preserve trouble evidence.
        )

    @staticmethod
    def _build_dhcp_rows(
        gateway: dict[str, Any],
        threshold: float,
        site_names: dict[str, str] | None = None,
    ) -> list[DhcpPoolRow]:
        """Build DHCP pool rows for one gateway."""
        pool_stats = gateway.get("dhcpd_stat") or {}  # Missing DHCP data must behave like no pools.
        if not isinstance(pool_stats, dict):  # Ignore unexpected shapes from optional API fields.
            return []  # Return no rows instead of failing the report.
        rows: list[DhcpPoolRow] = []  # Collect rows for this gateway.
        for pool_name, pool_data in pool_stats.items():  # Build one row for each pool key.
            if not isinstance(pool_data, dict):  # Ignore invalid pool values safely.
                continue  # Keep processing other pools.
            leased = WanEdgeScorecard._int_value(pool_data.get("num_leased"))  # Normalize leased addresses.
            total = WanEdgeScorecard._int_value(pool_data.get("num_ips"))  # Normalize total addresses.
            percent = WanEdgeScoring.safe_percent(leased, total)  # Calculate utilization only when safe.
            rows.append(  # Add one pool evidence row.
                DhcpPoolRow(
                    site=WanEdgeScorecard._site_name(gateway, site_names or {}),  # Preserve parent site name.
                    site_id=WanEdgeScorecard._text(gateway.get("site_id")),  # Preserve the parent site id.
                    gateway_name=WanEdgeScorecard._gateway_name(gateway),  # Preserve the parent gateway name.
                    gateway_id=WanEdgeScorecard._gateway_id(gateway),  # Preserve the parent gateway id.
                    pool_name=str(pool_name),  # Preserve the Mist DHCP pool key.
                    leased=leased,  # Preserve the leased address count.
                    total=total,  # Preserve the total address count.
                    percent=percent,  # Preserve the safe utilization percent.
                    warn_threshold_percent=threshold,  # Preserve the run threshold.
                    over_threshold=percent is not None and percent >= threshold,  # Mark threshold risk.
                )
            )
        return rows  # Return all pool rows for this gateway.

    @staticmethod
    def _build_site_rows(gateway_rows: list[GatewayScorecardRow], threshold: float) -> list[SiteScorecardRow]:
        """Build site scorecard rows from gateway rows."""
        grouped_rows: dict[tuple[str, str], list[GatewayScorecardRow]] = defaultdict(list)  # Group by site.
        for row in gateway_rows:  # Use the exact rows written to the gateway scorecard.
            grouped_rows[(row.site, row.site_id)].append(row)  # Add the row to its site group.
        return [  # Return deterministic site score rows.
            WanEdgeScoring.calculate_site_score(site, site_id, rows, threshold)  # Calculate from its rows.
            for (site, site_id), rows in sorted(grouped_rows.items())  # Sort for stable output order.
        ]

    @staticmethod
    def _export_reports(
        gateway_rows: list[GatewayScorecardRow],
        dhcp_rows: list[DhcpPoolRow],
        site_rows: list[SiteScorecardRow],
    ) -> None:
        """Export all scorecard reports through the project exporter."""
        mh = SourceDependencyResolver  # Resolve DataExporter through the project dependency seam.
        logger.info("Exporting WAN edge gateway scorecard rows")  # Log before gateway export.
        mh.DataExporter.write_with_format_selection(  # Use the existing project output behavior.
            [row.as_dict() for row in gateway_rows],  # Convert models into export dictionaries.
            "WanEdgeScorecard.csv",  # Write the required gateway scorecard file.
            api_function_name="listOrgDevicesStats",  # Route through the endpoint output strategy.
            fieldnames=WanEdgeScorecard.GATEWAY_FIELDNAMES,  # Keep empty exports column-stable.
        )
        logger.debug("Exported %s WAN edge gateway scorecard rows", len(gateway_rows))  # Log export count.
        logger.info("Exporting WAN edge DHCP pool rows")  # Log before DHCP export.
        mh.DataExporter.write_with_format_selection(  # Use the existing project output behavior.
            [row.as_dict() for row in dhcp_rows],  # Convert models into export dictionaries.
            "WanEdgeDhcpPools.csv",  # Write the required DHCP file.
            api_function_name="listOrgDevicesStats",  # Route through the endpoint output strategy.
            fieldnames=WanEdgeScorecard.DHCP_FIELDNAMES,  # Keep empty exports column-stable.
        )
        logger.debug("Exported %s WAN edge DHCP pool rows", len(dhcp_rows))  # Log export count.
        logger.info("Exporting WAN edge site scorecard rows")  # Log before site export.
        mh.DataExporter.write_with_format_selection(  # Use the existing project output behavior.
            [row.as_dict() for row in site_rows],  # Convert models into export dictionaries.
            "WanEdgeScorecardBySite.csv",  # Write the required site scorecard file.
            api_function_name="listOrgDevicesStats",  # Route through the endpoint output strategy.
            fieldnames=WanEdgeScorecard.SITE_FIELDNAMES,  # Keep empty exports column-stable.
        )
        logger.debug("Exported %s WAN edge site scorecard rows", len(site_rows))  # Log export count.

    @staticmethod
    def _print_org_summary(org_score: Any) -> None:
        """Print the organization scorecard summary."""
        logger.info("Printing WAN edge organization scorecard summary")  # Log before console output.
        print("WAN Edge Scorecard Summary")  # Print the summary heading for the operator.
        print(f"Gateways: {org_score.gateway_count}")  # Print the gateway count.
        print(f"Sites: {org_score.site_count}")  # Print the site count.
        print(f"Config Success: {org_score.config_success_percent}%")  # Print the configuration score.
        print(f"Version Compliance: {org_score.version_compliance_percent}%")  # Print the version score.
        print(f"WAN Edge Uptime: {org_score.wan_edge_uptime_percent}%")  # Print the uptime score.
        print(f"Potential Anomalies: {org_score.potential_anomalies_percent}%")  # Print the anomaly score.
        logger.debug("Printed WAN edge organization scorecard summary")  # Log after console output.

    @staticmethod
    def _count_vpn_peers(value: Any) -> tuple[int, int]:
        """Count up and down VPN peers."""
        peers = value if isinstance(value, list) else []  # Treat missing VPN peers as an empty list.
        up_count = sum(1 for peer in peers if isinstance(peer, dict) and peer.get("up") is True)  # Count up peers.
        down_count = sum(1 for peer in peers if isinstance(peer, dict) and peer.get("up") is False)  # Count down peers.
        return up_count, down_count  # Return both peer counts.

    @staticmethod
    def _count_bgp_peers(value: Any) -> tuple[int, int]:
        """Count established and non-established BGP peers."""
        peers = value if isinstance(value, list) else []  # Treat missing BGP peers as an empty list.
        established = 0  # Track peers in the established state.
        not_established = 0  # Track peers in any other state.
        for peer in peers:  # Inspect each BGP peer row.
            if not isinstance(peer, dict):  # Ignore malformed peer entries.
                continue  # Keep counting valid entries.
            state = str(peer.get("state", "")).strip().lower()  # Normalize the BGP state field.
            if state == "established":  # Mist schema names this as the healthy state.
                established += 1  # Count established peers.
            else:
                not_established += 1  # Count all other states as not established.
        return established, not_established  # Return both BGP counts.

    @staticmethod
    def _worst_pool_percent(pools: list[DhcpPoolRow]) -> float | None:
        """Return the highest known DHCP pool utilization."""
        percentages = [pool.percent for pool in pools if pool.percent is not None]  # Keep only safe percentages.
        return max(percentages) if percentages else None  # Return empty when no pool percent is available.

    @staticmethod
    def _uptime_days(value: Any) -> float | None:
        """Convert uptime seconds into days."""
        try:
            seconds = float(value)  # Normalize integer, float, and string values.
        except (TypeError, ValueError):
            return None  # Use an empty value when uptime is absent or invalid.
        return round(seconds / 86400.0, 2)  # Convert seconds into days for the scorecard.

    @staticmethod
    def _service_summary(gateway: dict[str, Any]) -> str:
        """Return a compact service status summary."""
        service_status = gateway.get("service_status") or gateway.get("service_stat") or {}  # Read service data.
        if not isinstance(service_status, dict):  # Unexpected service data cannot be summarized safely.
            return ""  # Keep the output clear and empty.
        pairs = [
            f"{key}={value}" for key, value in sorted(service_status.items()) if value not in (None, "")
        ]  # Summarize.
        return ", ".join(pairs)  # Return a compact stable summary string.

    @staticmethod
    def _ha_state(gateway: dict[str, Any]) -> str:
        """Return the available high-availability state."""
        cluster_stat = gateway.get("cluster_stat")  # Read gateway cluster statistics when present.
        if isinstance(cluster_stat, dict) and cluster_stat.get("state") is not None:  # Prefer explicit state.
            return WanEdgeScorecard._text(cluster_stat.get("state"))  # Return the HA state string.
        is_ha = gateway.get("is_ha")  # Fall back to the gateway HA boolean.
        return "ha" if is_ha is True else ""  # Show HA only when Mist reports it.

    @staticmethod
    def _cluster_peer_state(gateway: dict[str, Any]) -> str:
        """Return cluster peer state when available."""
        cluster_stat = gateway.get("cluster_stat")  # Read cluster statistics when present.
        if isinstance(cluster_stat, dict):  # Cluster stat can hold peer values.
            for key in ("peer_state", "cluster_peer_state", "peer_status"):  # Check common peer state names.
                if cluster_stat.get(key) is not None:  # Use the first known peer state field.
                    return WanEdgeScorecard._text(cluster_stat.get(key))  # Return the peer state value.
        return WanEdgeScorecard._text(gateway.get("cluster_peer_state"))  # Fall back to a top-level field.

    @staticmethod
    def _last_trouble(gateway: dict[str, Any]) -> str:
        """Return the latest available trouble evidence."""
        for key in ("last_trouble", "last_event", "last_alarm", "trouble", "last_trouble_reason"):  # Known fields.
            if gateway.get(key):  # Use the first present trouble value.
                return WanEdgeScorecard._text(gateway.get(key))  # Return a safe string value.
        return ""  # Keep missing optional trouble evidence empty.

    @staticmethod
    def _site_name(gateway: dict[str, Any], site_names: dict[str, str]) -> str:
        """Return the best available site display name."""
        site_id = WanEdgeScorecard._text(gateway.get("site_id"))  # Use the stable site identifier for lookup.
        return WanEdgeScorecard._text(
            gateway.get("site_name") or gateway.get("site") or site_names.get(site_id, site_id)
        )  # Prefer names and fall back to site ID.

    @staticmethod
    def _gateway_name(gateway: dict[str, Any]) -> str:
        """Return the best available gateway display name."""
        return WanEdgeScorecard._text(
            gateway.get("name") or gateway.get("device_name") or gateway.get("router_name") or gateway.get("hostname")
        )  # Name.

    @staticmethod
    def _gateway_id(gateway: dict[str, Any]) -> str:
        """Return the stable gateway identifier."""
        return WanEdgeScorecard._text(gateway.get("id") or gateway.get("mac"))  # Prefer UUID, then MAC address.

    @staticmethod
    def _text(value: Any) -> str:
        """Return a safe string for optional Mist values."""
        return "" if value is None else str(value)  # Keep missing optional values empty.

    @staticmethod
    def _int_value(value: Any) -> int:
        """Return a safe non-negative integer value."""
        try:
            return max(int(value), 0)  # Normalize numeric values and reject negative counts.
        except (TypeError, ValueError):
            return 0  # Missing or invalid counts become zero.
