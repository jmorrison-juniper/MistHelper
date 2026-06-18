"""Site client insights export orchestration extracted from MistHelper high-CC offender."""

import importlib
import logging
from types import SimpleNamespace
from typing import Any


def _resolve_runtime_dependencies() -> SimpleNamespace:
    """Resolve MistHelper runtime dependencies without static cross-module imports."""
    misthelper_module = importlib.import_module("MistHelper")  # Late import avoids circular src->MistHelper dependency
    return SimpleNamespace(
        mistapi=misthelper_module.mistapi,
        apisession=misthelper_module.apisession,
        InsightMetricsUtils=misthelper_module.InsightMetricsUtils,
        ConstDefinitionsExporter=misthelper_module.ConstDefinitionsExporter,  # Canonical insight-metrics refresh exporter  # noqa: E501
        PromptUtils=misthelper_module.PromptUtils,
        InputUtils=misthelper_module.InputUtils,
        EnhancedSSHRunner=misthelper_module.EnhancedSSHRunner,
        DataProcessingUtils=misthelper_module.DataProcessingUtils,
        DataExporter=misthelper_module.DataExporter,
        SiteClientExporter=misthelper_module.SiteClientExporter,
    )


class SiteClientInsightsService:
    """Owns site client insights workflow formerly embedded in SiteClientExporter."""

    @staticmethod
    def _resolve_site_name(deps: SimpleNamespace, site_id: str) -> str:
        """Resolve the human-readable site name, falling back to the site id on failure."""
        try:  # Site name lookup is best-effort; any failure falls back to the id
            response = deps.mistapi.api.v1.sites.listSites(deps.apisession, site_id)  # Fetch site metadata
            sites = deps.mistapi.get_all(response=response, mist_session=deps.apisession)  # Page all returned sites
            return next((site["name"] for site in sites if site["id"] == site_id), site_id)  # Match id -> name
        except Exception:  # Any API/shape error - fall back to the raw id
            return site_id  # Use the id as the display name

    @staticmethod
    def _list_and_display_clients(deps: SimpleNamespace, site_id: str, site_name: str) -> list[dict[str, Any]]:
        """Fetch wireless clients for the site and print a short preview; return the client list."""
        clients: list[dict[str, Any]] = []  # Default to empty when retrieval fails
        try:  # Client listing is best-effort; failures are warned and yield an empty list
            response = deps.mistapi.api.v1.sites.stats.listSiteWirelessClientsStats(deps.apisession, site_id)  # Query
            clients = deps.mistapi.get_all(response=response, mist_session=deps.apisession) or []  # Page all clients

            if clients:  # Found at least one client - show a short preview
                print(f"\n! Found {len(clients)} clients at site {site_name}")  # Summary count
                print("Recent clients (showing first 5):")  # Preview header
                for index, client in enumerate(clients[:5]):  # Show only the first five for brevity
                    mac = client.get("mac", "Unknown")  # Client MAC (or placeholder)
                    hostname = client.get("hostname", "Unknown")  # Client hostname (or placeholder)
                    last_seen = client.get("last_seen", "Unknown")  # Last-seen timestamp (or placeholder)
                    print(
                        f"  [{index}] MAC: {mac}, Hostname: {hostname}, Last seen: {last_seen}"
                    )  # Indexed preview row
            else:  # No clients returned for the site
                print(f"! No clients found at site {site_name}")  # Inform the user
        except Exception as exception:  # Retrieval failed - warn and keep the empty list
            logging.warning(f"Could not retrieve client list: {exception}")  # Trace the failure
        return clients  # Hand back whatever clients were found (possibly empty)

    @staticmethod
    def _resolve_client_mac(client_input: str, clients: list[dict[str, Any]]) -> str | None:
        """Resolve a client MAC from raw input; return None to abort (message already printed)."""
        if not client_input.isdigit():  # Non-numeric input is treated as a literal MAC string
            return client_input  # Use the input directly as the MAC
        try:  # Numeric input is an index into the displayed client list
            index = int(client_input)  # Parse the index
        except (ValueError, IndexError):  # Parsing failed despite isdigit (defensive)
            print(f"! Invalid index: {client_input}")  # Inform the user
            return None  # Abort - message already printed
        if not (0 <= index < len(clients)):  # Index must reference an existing client
            print(f"! Invalid index {index}. Must be between 0 and {len(clients) - 1}")  # Inform the user
            return None  # Abort - message already printed
        client_mac = str(clients[index].get("mac", ""))  # Resolve MAC from the selected client (may be empty)
        print(f"! Selected client by index: {client_mac}")  # Echo the selection
        return client_mac  # Return the resolved MAC (possibly empty string)

    @staticmethod
    def _collect_client_metrics(
        deps: SimpleNamespace,
        site_id: str,
        site_name: str,
        normalized_client_mac: str,
        client_metrics: list[str],
    ) -> tuple[list[dict[str, Any]], int]:
        """Fetch each client-scope insight metric; return (collected records, retrieved count)."""
        all_client_data: list[dict[str, Any]] = []  # Accumulates one record per metric that returned data
        metrics_retrieved = 0  # Count of metrics that returned data
        for metric in client_metrics:  # Iterate every client-scope metric
            try:  # Per-metric failures are non-fatal and skip to the next metric
                response = deps.mistapi.api.v1.sites.insights.getSiteInsightMetricsForClient(
                    deps.apisession, site_id, normalized_client_mac, metrics=metric
                )  # Query one client insight metric
                client_insight_data = getattr(response, "data", response) or {}  # Normalize to the payload (or empty)
                if client_insight_data:  # Metric returned data
                    client_insight_data["metric_type"] = metric  # Tag the metric type
                    client_insight_data["site_id"] = site_id  # Tag the site id
                    client_insight_data["site_name"] = site_name  # Tag the site name
                    client_insight_data["client_mac"] = normalized_client_mac  # Tag the client MAC
                    all_client_data.append(client_insight_data)  # Accumulate the record
                    metrics_retrieved += 1  # Count this successful metric
                    logging.debug(f"Retrieved client insight data for metric: {metric}")  # Trace success
                else:  # Metric returned no data
                    logging.debug(f"No data available for client metric: {metric}")  # Trace empty result
            except Exception as metric_error:  # Per-metric API failure - log and continue
                logging.debug(f"Failed to get client insight data for metric {metric}: {metric_error}")  # Trace
                continue  # Skip to the next metric
        return all_client_data, metrics_retrieved  # Collected records plus success count

    @staticmethod
    def _export_client_data(
        deps: SimpleNamespace,
        all_client_data: list[dict[str, Any]],
        metrics_retrieved: int,
        filename: str,
        site_name: str,
    ) -> None:
        """Flatten and export collected client insight data, or write an empty file when none."""
        if all_client_data:  # Data was collected for at least one metric
            processed = deps.DataProcessingUtils.flatten_nested_fields(all_client_data)  # Flatten nested structures
            processed = deps.DataProcessingUtils.escape_multiline(processed)  # Escape multiline fields for CSV
            deps.DataExporter.save_data_to_output(processed, filename)  # Write the export file
            print(f"! {metrics_retrieved} client insight metrics exported to {filename}")  # User summary
            logging.info(f"Exported {metrics_retrieved} client insight metrics at {site_name} to {filename}")  # Trace
        else:  # No data collected for any metric
            print(f"! 0 client insights exported to {filename} (no data available)")  # User summary
            logging.warning(f"No client insight data available at {site_name}")  # Warn on empty run
            deps.DataExporter.save_data_to_output([], filename)  # Write an empty export for consistency

    @classmethod
    def execute(cls) -> None:
        """Run site client insights export workflow."""
        deps = _resolve_runtime_dependencies()  # Resolve MistHelper collaborators at call time
        print("Export Site Client Insights:")  # User-facing banner
        logging.info("Starting export of site client insights...")  # Trace workflow start

        print("! Refreshing available insight metrics from Mist API...")  # Inform about the metric refresh
        deps.ConstDefinitionsExporter(
            deps.apisession
        ).export_all()  # Canonical refresh; regenerates ConstInsightMetrics.csv

        site_id = deps.PromptUtils.select_site()  # Prompt for the target site
        if not site_id:  # No site chosen - nothing to export
            logging.error("No site selected. Exiting.")  # Trace the early exit
            return  # Abort the workflow

        site_name = cls._resolve_site_name(deps, site_id)  # Resolve display name (falls back to id)
        sanitized_site_name = deps.EnhancedSSHRunner.sanitize_filename(site_name or site_id)  # Filesystem-safe name

        clients = cls._list_and_display_clients(deps, site_id, site_name)  # Fetch + preview clients

        print("\nEnter client MAC address or index number (or press Enter to skip):")  # Prompt header
        client_input = deps.InputUtils.safe_input(
            "Client MAC/Index: ",
            context="site_client_insights_selection",
        ).strip()  # Read and trim the client selection

        if not client_input:  # User pressed Enter to skip
            print("! No client input provided. Skipping client insights export.")  # Inform the user
            return  # Abort the workflow

        client_mac = cls._resolve_client_mac(client_input, clients)  # Resolve MAC from input (None = abort)
        if client_mac is None:  # Invalid index/value - helper already printed the reason
            return  # Abort the workflow silently
        if not client_mac:  # Resolved to an empty MAC (selected client had no MAC)
            print("! Could not determine client MAC address.")  # Inform the user
            return  # Abort the workflow

        normalized_client_mac = deps.SiteClientExporter._normalize_client_mac_or_none(client_mac)  # Validate/normalize
        if not normalized_client_mac:  # MAC failed format validation
            print(f"! Invalid client MAC address format: {client_mac}")  # Inform the user
            logging.error(f"Invalid client MAC address format provided for client insights: {client_mac}")  # Trace
            return  # Abort the workflow

        filename = f"SiteClientInsights_{sanitized_site_name}_{normalized_client_mac.replace(':', '')}.csv"  # Out file
        client_metrics = deps.InsightMetricsUtils.get_by_scope("client")  # Client-scope metric list

        if not client_metrics:  # No client-scope metrics configured
            print("! No metrics found for client scope. Check ConstInsightMetrics.csv file.")  # Inform the user
            logging.error("No client-scope metrics found in const insight metrics")  # Trace the misconfiguration
            deps.DataExporter.save_data_to_output([], filename)  # Write an empty export for consistency
            return  # Abort the workflow

        print(f"! Retrieving {len(client_metrics)} different client insight metrics for selected client...")  # Info

        try:  # Guard the fetch+export so failures still write an empty file
            all_client_data, metrics_retrieved = cls._collect_client_metrics(
                deps, site_id, site_name, normalized_client_mac, client_metrics
            )  # Fetch every client-scope metric
            cls._export_client_data(deps, all_client_data, metrics_retrieved, filename, site_name)  # Export results
        except Exception as exception:  # Unexpected top-level failure
            print(f"! Error exporting client insights: {exception}")  # User-facing error
            logging.error(f"Failed to export client insights at {site_name}: {exception}")  # Trace the failure
            deps.DataExporter.save_data_to_output([], filename)  # Write empty export on failure
