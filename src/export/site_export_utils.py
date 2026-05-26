"""Site export utilities extracted from MistHelper.py."""

from __future__ import annotations

import inspect
import logging
import os
import re
from typing import Any

from src.export.site_insights_exporter import SiteInsightsExporter
from src.export.site_insights_exporter import configure_site_insights_exporter_dependencies

apisession: Any = None
PromptUtils: Any = None
ConfigUtils: Any = None
DataProcessingUtils: Any = None
DataExporter: Any = None
TimeUtils: Any = None
EnhancedSSHRunner: Any = None
InsightMetricsUtils: Any = None
PacketCaptureManager: Any = None
APICoreFetchUtils: Any = None
is_debug_mode: Any = None
PrettyTable: Any = None
tqdm: Any = None
mistapi: Any = None


def configure_site_export_utils_dependencies(
    *,
    apisession_dependency: Any,
    prompt_utils: Any,
    config_utils: Any,
    data_processing_utils: Any,
    data_exporter: Any,
    time_utils: Any,
    enhanced_ssh_runner: Any,
    insight_metrics_utils: Any,
    packet_capture_manager: Any,
    api_core_fetch_utils: Any,
    is_debug_mode_fn: Any,
    pretty_table_class: Any,
    tqdm_module: Any,
    mistapi_dependency: Any,
) -> None:
    """Configure runtime dependencies from MistHelper orchestration layer."""
    global apisession
    global PromptUtils
    global ConfigUtils
    global DataProcessingUtils
    global DataExporter
    global TimeUtils
    global EnhancedSSHRunner
    global InsightMetricsUtils
    global PacketCaptureManager
    global APICoreFetchUtils
    global is_debug_mode
    global PrettyTable
    global tqdm
    global mistapi

    apisession = apisession_dependency
    PromptUtils = prompt_utils
    ConfigUtils = config_utils
    DataProcessingUtils = data_processing_utils
    DataExporter = data_exporter
    TimeUtils = time_utils
    EnhancedSSHRunner = enhanced_ssh_runner
    InsightMetricsUtils = insight_metrics_utils
    PacketCaptureManager = packet_capture_manager
    APICoreFetchUtils = api_core_fetch_utils
    is_debug_mode = is_debug_mode_fn
    PrettyTable = pretty_table_class
    tqdm = tqdm_module
    mistapi = mistapi_dependency

    configure_site_insights_exporter_dependencies(
        apisession_dependency=apisession_dependency,
        prompt_utils=prompt_utils,
        data_processing_utils=data_processing_utils,
        data_exporter=data_exporter,
        enhanced_ssh_runner=enhanced_ssh_runner,
        insight_metrics_utils=insight_metrics_utils,
        packet_capture_manager=packet_capture_manager,
        mistapi_dependency=mistapi_dependency,
    )


class SiteExportUtils(SiteInsightsExporter):
    """Centralized site-level data export utilities."""

    @staticmethod
    def _export_data(api_call, data_type, sort_key="name", **api_kwargs):  # type: ignore[no-untyped-def]  # noqa: C901, PLR0912, PLR0915
        """Generic function to export site-specific data to CSV."""
        logging.info(f"Starting export of site {data_type}...")

        site_id = PromptUtils.select_site()
        if not site_id:
            logging.error("No site selected. Exiting.")
            return

        try:
            response = mistapi.api.v1.orgs.sites.listOrgSites(apisession, ConfigUtils.get_cached_or_prompted_org_id())
            sites = mistapi.get_all(response=response, mist_session=apisession)
            site_name = next((site["name"] for site in sites if site["id"] == site_id), site_id)
        except Exception as e:
            logging.error(f"Error getting site name: {e}")
            site_name = site_id

        logging.info(f"Exporting {data_type} for site: {site_name}")

        safe_data_type = data_type.replace(" ", "").replace("-", "").title()
        safe_site_name = site_name.replace(" ", "_").replace("-", "_")
        filename = f"Site{safe_data_type}_{safe_site_name}.csv"

        try:
            logging.debug(f"Making site-specific API call: {api_call.__name__} with site_id: {site_id}")

            try:
                sig = inspect.signature(api_call)
                supports_limit = "limit" in sig.parameters
            except Exception:
                supports_limit = True

            if supports_limit:
                response = api_call(apisession, site_id, limit=1000, **api_kwargs)
            else:
                logging.debug(f"API function {api_call.__name__} does not support 'limit' parameter")
                response = api_call(apisession, site_id, **api_kwargs)

            rawdata = mistapi.get_all(response=response, mist_session=apisession)
            if rawdata is None:
                logging.warning(f"! No data returned from API for {data_type} at site {site_name}. Skipping.")
                return

            logging.info(f"Fetched {len(rawdata)} raw records for {data_type} from site {site_name}.")

            if sort_key:
                rawdata = sorted(rawdata, key=lambda x: x.get(sort_key, ""))

            data = DataProcessingUtils.flatten_nested_fields(rawdata)
            data = DataProcessingUtils.escape_multiline(data)  # type: ignore[no-untyped-call]
            DataExporter.save_data_to_output(data, filename)  # type: ignore[no-untyped-call]

            if not os.path.dirname(filename):
                full_file_path = os.path.join("data", filename)
            else:
                full_file_path = filename

            print(f"! {len(data)} records exported to {full_file_path}")
            logging.info(f"Site {data_type} data written to {filename} ({len(data)} rows).")

            if is_debug_mode():  # type: ignore[no-untyped-call]
                fields = DataProcessingUtils.get_unique_keys(data)  # type: ignore[no-untyped-call]
                table = PrettyTable()
                table.field_names = fields
                table.valign = "t"
                for item in tqdm(data, desc="Processing", unit="record"):  # type: ignore[no-untyped-call]
                    row = [item.get(field, "") for field in table.field_names]
                    table.add_row(row)
                print(table)
                logging.debug("Site data displayed in table format (debug mode).")
            else:
                logging.info(f"Site {data_type} export completed - {len(data)} records saved to {filename}.")

        except Exception as e:
            logging.error(f"! Error during site {data_type} export for {site_name}: {e}")
            raise

    @staticmethod
    def insights():  # type: ignore[no-untyped-def]
        """Export SLE metric availability for a selected site."""
        logging.info("Starting export of site SLE metric insights...")

        site_id = PromptUtils.select_site()
        if not site_id:
            logging.error("No site selected. Exiting.")
            return

        try:
            response = mistapi.api.v1.orgs.sites.listOrgSites(apisession, ConfigUtils.get_cached_or_prompted_org_id())
            sites = mistapi.get_all(response=response, mist_session=apisession)
            site_name = next((site["name"] for site in sites if site["id"] == site_id), site_id)
        except Exception as exception:
            logging.error(f"Error getting site name: {exception}")
            site_name = site_id

        safe_site_name = site_name.replace(" ", "_").replace("-", "_")
        filename = f"SiteSleMetricsInsights_{safe_site_name}.csv"

        try:
            response = mistapi.api.v1.sites.sle.listSiteSlesMetrics(
                apisession,
                site_id,
                scope="site",
                scope_id=site_id,
            )
            metrics_payload = getattr(response, "data", response) or {}

            rows = []
            enabled_metrics = metrics_payload.get("enabled", [])
            supported_metrics = metrics_payload.get("supported", [])

            for metric_name in sorted(set(enabled_metrics + supported_metrics)):
                rows.append(
                    {
                        "site_id": site_id,
                        "site_name": site_name,
                        "metric_name": metric_name,
                        "enabled": metric_name in enabled_metrics,
                        "supported": metric_name in supported_metrics,
                    }
                )

            if rows:
                DataExporter.save_data_to_output(rows, filename)  # type: ignore[no-untyped-call]
                print(f"! {len(rows)} records exported to data\\{filename}")
                logging.info(f"Exported {len(rows)} site SLE metric insight records to {filename}")
            else:
                print(f"! 0 records exported to data\\{filename} (no metrics available)")
                logging.warning(f"No site SLE metric insight data available for site {site_name}")
                DataExporter.save_data_to_output([], filename)  # type: ignore[no-untyped-call]
        except Exception as exception:
            print(f"! Error exporting site SLE metric insights: {exception}")
            logging.error(f"Failed to export site SLE metric insights for site {site_name}: {exception}")
            DataExporter.save_data_to_output([], filename)  # type: ignore[no-untyped-call]

    @staticmethod
    def _system_events():  # type: ignore[no-untyped-def]
        """Export system events for a site to SiteSystemEvents.csv."""
        hours = TimeUtils.get_dynamic_lookback_hours(24, 1)
        TimeUtils.log_dynamic_lookback("site system events export", hours)
        SiteExportUtils._export_data(  # type: ignore[no-untyped-call]
            api_call=mistapi.api.v1.sites.events.searchSiteSystemEvents,
            data_type="system events",
            sort_key="timestamp",
            duration=f"{hours}h",
        )

    @staticmethod
    def _fast_roam_events():  # type: ignore[no-untyped-def]
        """Export fast roam events for a site to SiteFastRoamEvents.csv."""
        hours = TimeUtils.get_dynamic_lookback_hours(24, 1)
        TimeUtils.log_dynamic_lookback("site fast roam events export", hours)
        SiteExportUtils._export_data(  # type: ignore[no-untyped-call]
            api_call=mistapi.api.v1.sites.events.searchSiteFastRoamEvents,
            data_type="fast roam events",
            sort_key="timestamp",
            duration=f"{hours}h",
        )

    @staticmethod
    def ospf_stats():  # type: ignore[no-untyped-def]
        """Export OSPF adjacency statistics for a selected site to SiteOspfStats.csv."""
        SiteExportUtils._export_data(  # type: ignore[no-untyped-call]
            api_call=mistapi.api.v1.sites.stats.searchSiteOspfStats,
            data_type="ospf stats",
            sort_key="mac",
        )

    @staticmethod
    def mxedge_upgrade_status():  # type: ignore[no-untyped-def]
        """Export MxEdge upgrade status for a selected site to SiteMxEdgeUpgrades.csv."""
        SiteExportUtils._export_data(  # type: ignore[no-untyped-call]
            api_call=mistapi.api.v1.sites.mxedges.listSiteMxEdgeUpgrades,
            data_type="mxedge upgrade status",
            sort_key="id",
        )

    @staticmethod
    def auto_map_assignment_status():  # type: ignore[no-untyped-def]
        """Export auto-map assignment status for a selected site to SiteAutoMapAssignmentStatus.csv."""
        SiteExportUtils._export_data(  # type: ignore[no-untyped-call]
            api_call=mistapi.api.v1.sites.auto_map_assignment.getSiteAutoMapAssignmentStatus,
            data_type="auto map assignment status",
            sort_key="id",
        )

    @staticmethod
    def site_stats() -> None:  # type: ignore[no-untyped-def]
        """Export aggregate health and capacity statistics for a selected site to SiteSiteStats.csv."""
        logging.info("Starting export of site statistics...")
        site_id = PromptUtils.select_site()
        if not site_id:
            logging.error("No site selected. Aborting site stats export.")
            return
        try:
            response = mistapi.api.v1.sites.stats.getSiteStats(apisession, site_id)
            raw = getattr(response, "data", response) or {}
            rows = [raw] if isinstance(raw, dict) else (raw if isinstance(raw, list) else [])
            rows = DataProcessingUtils.flatten_nested_fields(rows)
            filename = "SiteSiteStats.csv"
            DataExporter.save_data_to_output(rows, filename, api_function_name="getSiteStats")
            logging.info("Exported %d site stats records to %s", len(rows), filename)
        except Exception as exception:
            logging.error("Failed to export site stats: %s", exception, exc_info=True)

    @staticmethod
    def gateway_metrics() -> None:  # type: ignore[no-untyped-def]
        """Export gateway performance metrics summary for a selected site to SiteGatewayMetrics.csv."""
        logging.info("Starting export of site gateway metrics...")
        site_id = PromptUtils.select_site()
        if not site_id:
            logging.error("No site selected. Aborting gateway metrics export.")
            return
        try:
            response = mistapi.api.v1.sites.stats.getSiteGatewayMetrics(apisession, site_id)
            raw = getattr(response, "data", response) or {}
            rows = [raw] if isinstance(raw, dict) else (raw if isinstance(raw, list) else [])
            rows = DataProcessingUtils.flatten_nested_fields(rows)
            filename = "SiteGatewayMetrics.csv"
            DataExporter.save_data_to_output(rows, filename, api_function_name="getSiteGatewayMetrics")
            logging.info("Exported %d gateway metric records to %s", len(rows), filename)
        except Exception as exception:
            logging.error("Failed to export gateway metrics: %s", exception, exc_info=True)

    @staticmethod
    def switches_metrics() -> None:  # type: ignore[no-untyped-def]
        """Export switch performance metrics summary for a selected site to SiteSwitchesMetrics.csv."""
        logging.info("Starting export of site switches metrics...")
        site_id = PromptUtils.select_site()
        if not site_id:
            logging.error("No site selected. Aborting switches metrics export.")
            return
        try:
            response = mistapi.api.v1.sites.stats.getSiteSwitchesMetrics(apisession, site_id)
            raw = getattr(response, "data", response) or {}
            rows = [raw] if isinstance(raw, dict) else (raw if isinstance(raw, list) else [])
            rows = DataProcessingUtils.flatten_nested_fields(rows)
            filename = "SiteSwitchesMetrics.csv"
            DataExporter.save_data_to_output(rows, filename, api_function_name="getSiteSwitchesMetrics")
            logging.info("Exported %d switches metric records to %s", len(rows), filename)
        except Exception as exception:
            logging.error("Failed to export switches metrics: %s", exception, exc_info=True)

    @staticmethod
    def beacons_stats() -> None:  # type: ignore[no-untyped-def]
        """Export BLE beacon statistics for a selected site to SiteBeaconsStats.csv."""
        logging.info("Starting export of site BLE beacon statistics...")
        SiteExportUtils._export_data(  # type: ignore[no-untyped-call]
            api_call=mistapi.api.v1.sites.stats.listSiteBeaconsStats,
            data_type="beacons stats",
            sort_key="id",
        )

    @staticmethod
    def wxrules_usage() -> None:  # type: ignore[no-untyped-def]
        """Export WxLAN rule usage statistics for a selected site to SiteWxrulesUsage.csv."""
        logging.info("Starting export of site WxLAN rules usage statistics...")
        site_id = PromptUtils.select_site()
        if not site_id:
            logging.error("No site selected. Aborting WxRules usage export.")
            return
        try:
            response = mistapi.api.v1.sites.stats.getSiteWxRulesUsage(apisession, site_id)
            raw = getattr(response, "data", response) or {}
            rows = [raw] if isinstance(raw, dict) else (raw if isinstance(raw, list) else [])
            rows = DataProcessingUtils.flatten_nested_fields(rows)
            filename = "SiteWxrulesUsage.csv"
            DataExporter.save_data_to_output(rows, filename, api_function_name="getSiteWxRulesUsage")
            logging.info("Exported %d WxRules usage records to %s", len(rows), filename)
        except Exception as exception:
            logging.error("Failed to export WxRules usage: %s", exception, exc_info=True)

    @staticmethod
    def assets_stats() -> None:  # type: ignore[no-untyped-def]
        """Export asset statistics for a selected site to SiteAssetsStats.csv."""
        logging.info("Starting export of site asset statistics...")
        SiteExportUtils._export_data(  # type: ignore[no-untyped-call]
            api_call=mistapi.api.v1.sites.stats.listSiteAssetsStats,
            data_type="assets stats",
            sort_key="mac",
        )

    @staticmethod
    def current_channel_planning() -> None:  # type: ignore[no-untyped-def]
        """Export current RRM channel and power plan per AP radio for a selected site."""
        logging.info("Starting export of site current channel planning (RRM)...")
        site_id = PromptUtils.select_site()
        if not site_id:
            logging.error("No site selected. Aborting channel planning export.")
            return
        try:
            response = mistapi.api.v1.sites.rrm.getSiteCurrentChannelPlanning(apisession, site_id)
            raw = getattr(response, "data", response) or {}
            if isinstance(raw, dict):
                rows = []
                for ap_mac, bands in raw.items():
                    if isinstance(bands, dict):
                        for band, assignment in bands.items():
                            row = {"ap": ap_mac, "band": band, "site_id": site_id}
                            row.update(assignment if isinstance(assignment, dict) else {"value": assignment})
                            rows.append(row)
                    else:
                        rows.append({"ap": ap_mac, "site_id": site_id, "value": bands})
            else:
                rows = raw if isinstance(raw, list) else [raw]
            rows = DataProcessingUtils.flatten_nested_fields(rows)
            filename = "SiteCurrentChannelPlanning.csv"
            DataExporter.save_data_to_output(rows, filename, api_function_name="getSiteCurrentChannelPlanning")
            logging.info("Exported %d channel planning records to %s", len(rows), filename)
        except Exception as exception:
            logging.error("Failed to export channel planning: %s", exception, exc_info=True)

    @staticmethod
    def zone_config_analysis() -> None:
        """Zone, engagement, and occupancy config analysis (Menu #6). Delegates to src.analytics.zone_analyzer."""
        from src.analytics.zone_analyzer import ZoneConfigurationAnalyzer as _ZCA  # noqa: PLC0415

        _ZCA.analyze(
            apisession=apisession,
            get_org_id_fn=ConfigUtils.get_cached_or_prompted_org_id,
            check_stop_fn=ConfigUtils.check_stop_signal,
            all_sites_fn=APICoreFetchUtils.all_sites_with_limit,
            save_data_fn=DataExporter.save_data_to_output,
        )
