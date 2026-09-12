"""GatewayHaExporter -- per-site HA gateway cluster info exporter.

Extracted from MistHelper.py during initiative 1013 (Cat B, position 23).
Menu #87 -- Gateway HA Cluster Info. All methods are static -- no state
is kept on the class. Callers continue to reach it through the
``MistHelper.GatewayHaExporter`` re-export alias.
"""

from __future__ import annotations  # WHY: PEP 604 unions for return types.

import importlib  # WHY: lazy MistHelper import avoids circular load at module init.
import logging  # WHY: structured trace for export lifecycle events.
from typing import Any  # WHY: raw gateway rows are duck-typed dicts from mistapi.

import mistapi  # WHY: direct SDK access for site device stats + HA cluster endpoints.

from src.data.data_processing_utils import (
    DataProcessingUtils,
)  # WHY: 1015 T-10 canonical import (eliminates mh.DataProcessingUtils).


class GatewayHaExporter:
    """Exporter for HA (High-Availability) gateway cluster information.

    Collects per-site HA gateway stats and cluster node membership,
    then exports the combined dataset to the configured output backend.

    Menu #87 -- Gateway HA Cluster Info.
    """

    # Field names preserved from the stats_gateway response that describe HA state
    HA_STAT_FIELDS = [  # HA stat columns.
        "mac",
        "name",
        "model",
        "serial",
        "site_id",
        "is_ha",
        "node_name",
        "vc_mac",
        "status",
        "version",
        "ip",
        "uptime",
        "cluster_config",
        "cluster_stat",
    ]

    EMPTY_HA_PAIR = {  # Empty/fallback HA node pair structure.
        "ha_cluster_node0_mac": None,
        "ha_cluster_node1_mac": None,
        "ha_cluster_node_count": 0,
    }

    @staticmethod
    def _persist_ha_export(rows: list[Any]) -> None:
        """Flatten + write HA gateway rows to CSV/backend and log the count."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of DataProcessingUtils + DataExporter helpers.
        flat_rows = DataProcessingUtils.flatten_nested_fields(rows)  # Flatten nested dicts for CSV/DB.
        filename = "GatewayHaClusterInfo.csv"  # Output filename for the export.
        mh.DataExporter.write_with_format_selection(
            flat_rows, filename, api_function_name="listSiteGatewayHaStats"
        )  # Persist to configured backend.
        logging.info("Exported %d HA gateway records to %s", len(flat_rows), filename)  # Log export success.

    @staticmethod
    def _collect_ha_gateways(site_id: str) -> list[Any] | None:
        """Fetch site gateway stats and return HA-enabled gateways; ``None`` when none exist (operator notified)."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of APICoreFetchUtils + apisession.
        logging.info("Fetching gateway device stats for site %s", site_id)  # Trace before API call
        stats_resp = mistapi.api.v1.sites.stats.listSiteDevicesStats(mh.apisession, site_id, type="gateway")  # API call
        all_gateways = mh.APICoreFetchUtils.get_api_response_data(stats_resp)  # Unwrap list from response
        logging.debug("Received %d gateway stat records for site %s", len(all_gateways), site_id)  # Trace count
        ha_gateways = [gw for gw in all_gateways if gw.get("is_ha") is True]  # Filter to HA-enabled gateways
        logging.info("Found %d HA gateways in site %s", len(ha_gateways), site_id)  # Trace HA gateway count
        if not ha_gateways:  # No HA gateways -> tell user and signal abort
            # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
            logging.info("No HA gateways found for the selected site.")
            return None
        return ha_gateways  # Caller proceeds with cluster export

    @staticmethod
    def ha_cluster_info() -> None:  # Export HA cluster info.
        """Export HA gateway cluster info for a selected site (Menu #87)."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of ConfigUtils + PromptUtils helpers.
        logging.info("Starting Gateway HA Cluster Info export (Menu #87)")  # Trace entry point
        try:
            org_id = mh.ConfigUtils.get_cached_or_prompted_org_id()  # Resolve or prompt for org ID
            logging.debug("Gateway HA export resolved org %s", org_id)  # Record resolved org
            site_id = mh.PromptUtils.select_site()  # Pick a site (uses SiteList.csv)
            if not site_id:  # User cancelled or no sites
                logging.warning("No site selected -- aborting HA cluster export")
                return
            ha_gateways = GatewayHaExporter._collect_ha_gateways(site_id)  # Fetch + filter + early-exit on none
            if ha_gateways is None:  # Helper already notified user
                return
            rows = GatewayHaExporter._build_ha_rows(ha_gateways, site_id)  # Merge stats + cluster node info
            GatewayHaExporter._print_ha_summary(rows)  # Print tabular summary to the terminal
            GatewayHaExporter._persist_ha_export(rows)  # Flatten + write + log
        except Exception as exception:  # Catch any API or processing error
            logging.exception("Failed to export HA gateway cluster info: %s", exception)  # Log full traceback

    @staticmethod
    def _fetch_ha_pair_for_gateway(site_id: str, device_id: str) -> dict[str, Any]:
        """Call /sites/{site_id}/devices/{device_id}/ha and return node0/node1 MAC + count (empty pair on error)."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of APICoreFetchUtils + apisession.
        try:
            ha_resp = mistapi.api.v1.sites.devices.GetSiteDeviceHaClusterNode(  # Get node pair.
                mh.apisession, site_id, device_id
            )
            ha_data = mh.APICoreFetchUtils.get_api_response_data(ha_resp)  # Unwrap the response body.
            logging.debug("HA cluster node response for %s: %s", device_id, ha_data)  # Log raw response.
            if isinstance(ha_data, dict):  # Expect a gateway_cluster object with a "nodes" list.
                nodes = ha_data.get("nodes", [])  # Extract the nodes array.
                return {
                    "ha_cluster_node0_mac": nodes[0].get("mac") if len(nodes) > 0 else None,  # Node 0 MAC.
                    "ha_cluster_node1_mac": nodes[1].get("mac") if len(nodes) > 1 else None,  # Node 1 MAC.
                    "ha_cluster_node_count": len(nodes),  # Number of nodes in cluster.
                }
            return dict(GatewayHaExporter.EMPTY_HA_PAIR)  # Bad shape -- empty pair.
        except Exception as exception:  # HA endpoint may 404 for partial cluster states.
            logging.warning("Could not fetch HA node info for %s: %s", device_id, exception)  # Log soft failure.
            return dict(GatewayHaExporter.EMPTY_HA_PAIR)  # Error fallback -- empty pair.

    @staticmethod
    def _build_ha_rows(ha_gateways: list[Any], site_id: str) -> list[dict[str, Any]]:  # Build HA summary rows.
        """For each HA gateway, merge stats fields with the cluster node-pair info from /ha endpoint."""
        rows: list[dict[str, Any]] = []  # Accumulate merged rows here.
        for gateway in ha_gateways:  # Iterate over each HA-enabled gateway device.
            device_id = gateway.get("id", "")  # Get device ID (UUID) from stats record.
            row = {field: gateway.get(field) for field in GatewayHaExporter.HA_STAT_FIELDS}  # Copy HA stat fields.
            row["site_id"] = site_id  # Ensure site_id is always present in the row.
            logging.info(
                "Fetching HA cluster node info for gateway %s (%s)", gateway.get("name"), device_id
            )  # Log per-device call.
            row.update(GatewayHaExporter._fetch_ha_pair_for_gateway(site_id, device_id))  # Merge node-pair fields.
            rows.append(row)  # Add merged row to results list.
        logging.debug("Built %d merged HA gateway rows", len(rows))  # Log total built.
        return rows  # Return the complete merged dataset.

    @staticmethod
    def _print_ha_summary(rows: list[dict[str, Any]]) -> None:  # Print the HA summary.
        """Print a formatted summary of HA gateway cluster pairs to the terminal.

        Args:
            rows: List of merged HA gateway rows to display.
        """
        logging.info("Printing HA gateway cluster summary table to terminal")  # Log before display
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logging.info("\n=== HA Gateway Cluster Summary ===\n")  # Section header for the terminal output
        # Build column header string for the HA cluster summary table
        header = (
            f"{'Name':<30} {'Node':<8} {'Status':<12}" f" {'Node0 MAC':<20} {'Node1 MAC':<20} {'Cluster MAC':<18}"
        )  # Column headers
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logging.info(header)  # Print headers to terminal
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logging.info("-" * len(header))  # Print separator line
        for row in rows:  # Iterate each HA gateway record
            name = str(row.get("name", ""))[:28]  # Truncate long names for display
            node_name = str(row.get("node_name", ""))  # Which node (node0 / node1)
            status = str(row.get("status", ""))  # Connected / Disconnected / and so on
            node0_mac = str(row.get("ha_cluster_node0_mac") or "")  # MAC of node0 in the pair
            node1_mac = str(row.get("ha_cluster_node1_mac") or "")  # MAC of node1 in the pair
            vc_mac = str(row.get("vc_mac") or "")  # Shared cluster MAC address
            # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
            logging.info(
                "%-30s %-8s %-12s %-20s %-20s %-18s",
                name,
                node_name,
                status,
                node0_mac,
                node1_mac,
                vc_mac,
            )  # Print row
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logging.info("")  # Blank line after table for readability
