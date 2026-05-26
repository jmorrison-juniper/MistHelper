"""Site insights exporter extracted from SiteExportUtils high-complexity branch."""

from __future__ import annotations

import logging
from typing import Any

apisession: Any = None
PromptUtils: Any = None
DataProcessingUtils: Any = None
DataExporter: Any = None
EnhancedSSHRunner: Any = None
InsightMetricsUtils: Any = None
PacketCaptureManager: Any = None
mistapi: Any = None


def configure_site_insights_exporter_dependencies(
    *,
    apisession_dependency: Any,
    prompt_utils: Any,
    data_processing_utils: Any,
    data_exporter: Any,
    enhanced_ssh_runner: Any,
    insight_metrics_utils: Any,
    packet_capture_manager: Any,
    mistapi_dependency: Any,
) -> None:
    """Configure runtime dependencies from MistHelper orchestration layer."""
    global apisession
    global PromptUtils
    global DataProcessingUtils
    global DataExporter
    global EnhancedSSHRunner
    global InsightMetricsUtils
    global PacketCaptureManager
    global mistapi

    apisession = apisession_dependency
    PromptUtils = prompt_utils
    DataProcessingUtils = data_processing_utils
    DataExporter = data_exporter
    EnhancedSSHRunner = enhanced_ssh_runner
    InsightMetricsUtils = insight_metrics_utils
    PacketCaptureManager = packet_capture_manager
    mistapi = mistapi_dependency


class SiteInsightsExporter:
    """Extracted site insights export implementation for menu paths 74 and 76."""

    @staticmethod
    def insight_metrics():  # type: ignore[no-untyped-def]  # noqa: PLR0915
        """Export general insight metrics for a selected site to SiteInsightMetrics_[SiteName].csv."""
        print("Export Site Insight Metrics:")
        logging.info("Starting export of site insight metrics...")

        site_id = PromptUtils.select_site()
        if not site_id:
            logging.error("No site selected. Exiting.")
            return

        try:
            response = mistapi.api.v1.sites.listSites(apisession, site_id)
            sites = mistapi.get_all(response=response, mist_session=apisession)
            site_name = next((site["name"] for site in sites if site["id"] == site_id), site_id)
        except Exception:
            site_name = site_id

        sanitized_site_name = EnhancedSSHRunner.sanitize_filename(site_name or site_id)
        filename = f"SiteInsightMetrics_{sanitized_site_name}.csv"

        print("! Refreshing available insight metrics from Mist API...")
        InsightMetricsUtils.export_legacy()

        site_metrics = InsightMetricsUtils.get_by_scope("site")

        if not site_metrics:
            print("! No metrics found for site scope. Check ConstInsightMetrics.csv file.")
            logging.error("No site-scope metrics found in const insight metrics")
            DataExporter.save_data_to_output([], filename)  # type: ignore[no-untyped-call]
            return

        all_insight_data = []
        metrics_retrieved = 0

        print(f"! Retrieving {len(site_metrics)} different site insight metrics...")

        try:
            for metric in site_metrics:
                try:
                    response = mistapi.api.v1.sites.insights.getSiteInsightMetrics(apisession, site_id, metric)
                    insight_data = getattr(response, "data", response) or {}

                    if insight_data:
                        insight_data["metric_type"] = metric
                        insight_data["site_id"] = site_id
                        insight_data["site_name"] = site_name
                        all_insight_data.append(insight_data)
                        metrics_retrieved += 1
                        logging.debug(f"Retrieved site insight data for metric: {metric}")
                    else:
                        logging.debug(f"No data available for metric: {metric}")
                except Exception as exception:
                    logging.debug(f"Failed to get site insight data for metric {metric}: {exception}")
                    continue

            if all_insight_data:
                processed = DataProcessingUtils.flatten_nested_fields(all_insight_data)
                processed = DataProcessingUtils.escape_multiline(processed)  # type: ignore[no-untyped-call]
                DataExporter.save_data_to_output(processed, filename)  # type: ignore[no-untyped-call]
                print(f"! {metrics_retrieved} site insight metrics exported to {filename}")
                logging.info(f"Exported {metrics_retrieved} site insight metrics for {site_name} to {filename}")
            else:
                print(f"! 0 insight metrics exported to {filename} (no data available)")
                logging.warning(f"No insight data available for site {site_name}")
                DataExporter.save_data_to_output([], filename)  # type: ignore[no-untyped-call]
        except Exception as exception:
            print(f"! Error exporting site insight metrics: {exception}")
            logging.error(f"Failed to export site insight metrics for {site_name}: {exception}")
            DataExporter.save_data_to_output([], filename)  # type: ignore[no-untyped-call]

    @staticmethod
    def device_insights():  # type: ignore[no-untyped-def]  # noqa: C901, PLR0912, PLR0915
        """Export device-specific insight metrics for a selected site to SiteDeviceInsights_[SiteName].csv."""
        print("Export Site Device Insights:")
        logging.info("Starting export of site device insights...")

        print("! Refreshing available insight metrics from Mist API...")
        InsightMetricsUtils.export_legacy()

        site_id = PromptUtils.select_site()
        if not site_id:
            logging.error("No site selected. Exiting.")
            return

        device_id = PromptUtils.select_device(site_id)
        if not device_id:
            logging.error("No device selected. Exiting.")
            return

        try:
            response = mistapi.api.v1.sites.listSites(apisession, site_id)
            sites = mistapi.get_all(response=response, mist_session=apisession)
            site_name = next((site["name"] for site in sites if site["id"] == site_id), site_id)
        except Exception:
            site_name = site_id

        try:
            response = mistapi.api.v1.sites.devices.listSiteDevices(apisession, site_id, type="all")
            devices = mistapi.get_all(response=response, mist_session=apisession)
            device = next((dev for dev in devices if dev["id"] == device_id), None)
            device_name = device["name"] if device else device_id
            device_mac = device["mac"] if device else None
            device_model = device.get("model", "") if device else ""
        except Exception:
            device_name = device_id
            device_mac = None
            device_model = ""

        if not device_mac:
            print(f"! Error: Could not find MAC address for device {device_name}")
            logging.error(f"Could not find MAC address for device {device_id}")
            return
        normalized_device_mac = SiteInsightsExporter._normalize_device_mac_or_none(device_mac)
        if not normalized_device_mac:
            print(f"! Invalid device MAC address format for {device_name}: {device_mac}")
            logging.error(f"Invalid device MAC address format for device {device_id}: {device_mac}")
            return

        sanitized_site_name = EnhancedSSHRunner.sanitize_filename(site_name or site_id)
        sanitized_device_name = EnhancedSSHRunner.sanitize_filename(device_name or device_id)
        filename = f"SiteDeviceInsights_{sanitized_site_name}_{sanitized_device_name}.csv"

        device_metrics = InsightMetricsUtils.get_by_scope("device")
        device_platform = SiteInsightsExporter._classify_device_platform(device_model)
        device_metrics = [
            metric
            for metric in device_metrics
            if SiteInsightsExporter._metric_compatible_with_platform(metric, device_platform)
        ]

        if not device_metrics:
            print("! No metrics found for device scope. Check ConstInsightMetrics.csv file.")
            logging.error("No device-scope metrics found in const insight metrics")
            DataExporter.save_data_to_output([], filename)  # type: ignore[no-untyped-call]
            return

        all_device_data = []
        metrics_retrieved = 0

        print(f"! Retrieving {len(device_metrics)} different device insight metrics for {device_name}...")

        try:
            for metric in device_metrics:
                try:
                    response = mistapi.api.v1.sites.insights.getSiteInsightMetricsForDevice(
                        apisession, site_id, metric, normalized_device_mac
                    )
                    device_insight_data = getattr(response, "data", response) or {}

                    if device_insight_data:
                        device_insight_data["metric_type"] = metric
                        device_insight_data["site_id"] = site_id
                        device_insight_data["site_name"] = site_name
                        device_insight_data["device_id"] = device_id
                        device_insight_data["device_name"] = device_name
                        device_insight_data["device_mac"] = normalized_device_mac
                        all_device_data.append(device_insight_data)
                        metrics_retrieved += 1
                        logging.debug(f"Retrieved device insight data for metric: {metric}")
                    else:
                        logging.debug(f"No data available for device metric: {metric}")
                except Exception as metric_error:
                    logging.debug(f"Failed to get device insight data for metric {metric}: {metric_error}")
                    continue

            if all_device_data:
                processed = DataProcessingUtils.flatten_nested_fields(all_device_data)
                processed = DataProcessingUtils.escape_multiline(processed)  # type: ignore[no-untyped-call]
                DataExporter.save_data_to_output(processed, filename)  # type: ignore[no-untyped-call]
                print(f"! {metrics_retrieved} device insight metrics exported to {filename}")
                logging.info(
                    "Exported %s device insight metrics for %s at %s to %s",
                    metrics_retrieved,
                    device_name,
                    site_name,
                    filename,
                )
            else:
                print(f"! 0 device insights exported to {filename} (no data available)")
                logging.warning(
                    "No device insight data available for %s at %s",
                    device_name,
                    site_name,
                )
                DataExporter.save_data_to_output([], filename)  # type: ignore[no-untyped-call]
        except Exception as exception:
            print(f"! Error exporting device insights: {exception}")
            logging.error(
                "Failed to export device insights for %s at %s: %s",
                device_name,
                site_name,
                exception,
            )
            DataExporter.save_data_to_output([], filename)  # type: ignore[no-untyped-call]

    @staticmethod
    def _classify_device_platform(device_model: str) -> str:
        """Classify Mist inventory model into ap/switch/gateway for metric filtering."""
        model = (device_model or "").upper()
        if model.startswith("AP"):
            return "ap"
        if model.startswith(("EX", "QFX")):
            return "switch"
        if model.startswith(("SRX", "SSR")):
            return "gateway"
        return "unknown"

    @staticmethod
    def _metric_compatible_with_platform(metric_name: str, device_platform: str) -> bool:
        """Skip clearly incompatible device metrics to prevent avoidable API 400 responses."""
        metric = (metric_name or "").lower()
        if "switch" in metric:
            return device_platform in {"switch", "unknown"}
        if any(token in metric for token in ("gateway", "wan", "srx", "ssr")):
            return device_platform in {"gateway", "unknown"}
        if "ap" in metric or "wifi" in metric:
            return device_platform in {"ap", "unknown"}
        return True

    @staticmethod
    def _normalize_device_mac_or_none(device_mac: str) -> str | None:
        """Validate and normalize device MAC for device insights endpoints."""
        if not device_mac:
            return None
        if not PacketCaptureManager.validate_mac_address(device_mac):
            return None
        return PacketCaptureManager.normalize_mac_address(device_mac)
