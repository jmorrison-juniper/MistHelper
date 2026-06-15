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
    def refresh_insight_metrics_cache() -> None:
        """Refresh ConstInsightMetrics output using canonical const endpoint path.

        This is the canonical replacement for legacy compatibility refresh hooks.
        """
        logging.info("Refreshing const insight metrics cache via canonical endpoint")
        if mistapi is None or apisession is None:
            logging.warning("Cannot refresh insight metrics cache because mistapi dependencies are not configured")
            return
        if DataExporter is None:
            logging.warning("Cannot refresh insight metrics cache because DataExporter dependency is not configured")
            return
        try:
            response = mistapi.api.v1.const.insight_metrics.listInsightMetrics(apisession)
            payload = getattr(response, "data", response) or {}
            rows: list[dict[str, Any]] = []
            if isinstance(payload, dict):
                for metric_name, metric_details in payload.items():
                    metric_dict = metric_details if isinstance(metric_details, dict) else {}
                    rows.append(
                        {
                            "metric_name": metric_name,
                            "description": metric_dict.get("description", ""),
                            "type": metric_dict.get("type", ""),
                            "unit": metric_dict.get("unit", ""),
                            "scopes": ", ".join(metric_dict.get("scopes", [])),
                            "report_scopes": ", ".join(metric_dict.get("report_scopes", [])),
                        }
                    )
            elif isinstance(payload, list):
                for item in payload:
                    if isinstance(item, dict):
                        rows.append(item)
            DataExporter.save_data_to_output(rows, "ConstInsightMetrics.csv")  # type: ignore[no-untyped-call]
            logging.info("Refreshed const insight metrics cache with %d rows", len(rows))
        except Exception as exception:
            logging.warning("Failed to refresh const insight metrics cache: %s", exception)

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
        # Use PacketCaptureManager fallback when dependencies not fully configured (e.g. in test env)
        if PacketCaptureManager is not None:
            if not PacketCaptureManager.validate_mac_address(device_mac):
                return None
            return PacketCaptureManager.normalize_mac_address(device_mac)

        # Fallback local MAC validation and normalization
        clean = device_mac.replace(":", "").replace("-", "").replace(".", "").lower()
        if len(clean) != 12 or not all(c in "0123456789abcdef" for c in clean):
            return None
        return ":".join(clean[i : i + 2] for i in range(0, 12, 2))
