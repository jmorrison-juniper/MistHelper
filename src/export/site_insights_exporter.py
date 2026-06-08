"""Site insights exporter extracted from SiteExportUtils high-complexity branch."""

from __future__ import annotations

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
