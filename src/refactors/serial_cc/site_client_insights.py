"""Site client insights export orchestration extracted from MistHelper high-CC offender."""

import importlib
import logging
from types import SimpleNamespace
from typing import Any


def _resolve_runtime_dependencies() -> SimpleNamespace:
    """Resolve MistHelper runtime dependencies without static cross-module imports."""
    misthelper_module = importlib.import_module("MistHelper")
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
    def execute():  # noqa: C901, PLR0912, PLR0915
        """Run site client insights export workflow."""
        deps = _resolve_runtime_dependencies()
        print("Export Site Client Insights:")
        logging.info("Starting export of site client insights...")

        print("! Refreshing available insight metrics from Mist API...")
        deps.ConstDefinitionsExporter(
            deps.apisession
        ).export_all()  # Canonical refresh; regenerates ConstInsightMetrics.csv

        site_id = deps.PromptUtils.select_site()
        if not site_id:
            logging.error("No site selected. Exiting.")
            return

        try:
            response = deps.mistapi.api.v1.sites.listSites(deps.apisession, site_id)
            sites = deps.mistapi.get_all(response=response, mist_session=deps.apisession)
            site_name = next((site["name"] for site in sites if site["id"] == site_id), site_id)
        except Exception:
            site_name = site_id

        sanitized_site_name = deps.EnhancedSSHRunner.sanitize_filename(site_name or site_id)

        clients: list[dict[str, Any]] = []
        try:
            response = deps.mistapi.api.v1.sites.stats.listSiteWirelessClientsStats(deps.apisession, site_id)
            clients = deps.mistapi.get_all(response=response, mist_session=deps.apisession) or []

            if clients:
                print(f"\n! Found {len(clients)} clients at site {site_name}")
                print("Recent clients (showing first 5):")
                for index, client in enumerate(clients[:5]):
                    mac = client.get("mac", "Unknown")
                    hostname = client.get("hostname", "Unknown")
                    last_seen = client.get("last_seen", "Unknown")
                    print(f"  [{index}] MAC: {mac}, Hostname: {hostname}, Last seen: {last_seen}")
            else:
                print(f"! No clients found at site {site_name}")
        except Exception as exception:
            logging.warning(f"Could not retrieve client list: {exception}")

        print("\nEnter client MAC address or index number (or press Enter to skip):")
        client_input = deps.InputUtils.safe_input(
            "Client MAC/Index: ",
            context="site_client_insights_selection",
        ).strip()

        if not client_input:
            print("! No client input provided. Skipping client insights export.")
            return

        client_mac = None
        if client_input.isdigit():
            try:
                index = int(client_input)
                if 0 <= index < len(clients):
                    client_mac = clients[index].get("mac", "")
                    print(f"! Selected client by index: {client_mac}")
                else:
                    print(f"! Invalid index {index}. Must be between 0 and {len(clients) - 1}")
                    return
            except (ValueError, IndexError):
                print(f"! Invalid index: {client_input}")
                return
        else:
            client_mac = client_input

        if not client_mac:
            print("! Could not determine client MAC address.")
            return

        normalized_client_mac = deps.SiteClientExporter._normalize_client_mac_or_none(client_mac)
        if not normalized_client_mac:
            print(f"! Invalid client MAC address format: {client_mac}")
            logging.error(f"Invalid client MAC address format provided for client insights: {client_mac}")
            return

        filename = f"SiteClientInsights_{sanitized_site_name}_{normalized_client_mac.replace(':', '')}.csv"
        client_metrics = deps.InsightMetricsUtils.get_by_scope("client")

        if not client_metrics:
            print("! No metrics found for client scope. Check ConstInsightMetrics.csv file.")
            logging.error("No client-scope metrics found in const insight metrics")
            deps.DataExporter.save_data_to_output([], filename)
            return

        all_client_data = []
        metrics_retrieved = 0

        print(f"! Retrieving {len(client_metrics)} different client insight metrics for selected client...")

        try:
            for metric in client_metrics:
                try:
                    response = deps.mistapi.api.v1.sites.insights.getSiteInsightMetricsForClient(
                        deps.apisession, site_id, normalized_client_mac, metrics=metric
                    )
                    client_insight_data = getattr(response, "data", response) or {}

                    if client_insight_data:
                        client_insight_data["metric_type"] = metric
                        client_insight_data["site_id"] = site_id
                        client_insight_data["site_name"] = site_name
                        client_insight_data["client_mac"] = normalized_client_mac
                        all_client_data.append(client_insight_data)
                        metrics_retrieved += 1
                        logging.debug(f"Retrieved client insight data for metric: {metric}")
                    else:
                        logging.debug(f"No data available for client metric: {metric}")
                except Exception as metric_error:
                    logging.debug(f"Failed to get client insight data for metric {metric}: {metric_error}")
                    continue

            if all_client_data:
                processed = deps.DataProcessingUtils.flatten_nested_fields(all_client_data)
                processed = deps.DataProcessingUtils.escape_multiline(processed)
                deps.DataExporter.save_data_to_output(processed, filename)
                print(f"! {metrics_retrieved} client insight metrics exported to {filename}")
                logging.info(f"Exported {metrics_retrieved} client insight metrics at {site_name} to {filename}")
            else:
                print(f"! 0 client insights exported to {filename} (no data available)")
                logging.warning(f"No client insight data available at {site_name}")
                deps.DataExporter.save_data_to_output([], filename)
        except Exception as exception:
            print(f"! Error exporting client insights: {exception}")
            logging.error(f"Failed to export client insights at {site_name}: {exception}")
            deps.DataExporter.save_data_to_output([], filename)
