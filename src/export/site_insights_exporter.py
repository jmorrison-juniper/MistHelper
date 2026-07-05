"""Site insights exporter extracted from SiteExportUtils high-complexity branch."""

from __future__ import annotations  # WHY: PEP 563 postponed annotations for forward Any typing.

from typing import Any  # WHY: dependencies are unknown-type runtime injections.

# Module-level constants - centralize platform tokens so branch logic stays low-complexity.
_PLATFORM_AP: str = "ap"  # WHY: canonical AP platform identifier for metric routing.
_PLATFORM_SWITCH: str = "switch"  # WHY: canonical switch platform identifier for metric routing.
_PLATFORM_GATEWAY: str = "gateway"  # WHY: canonical gateway platform identifier for metric routing.
_PLATFORM_UNKNOWN: str = "unknown"  # WHY: fallback classification for unmatched Mist inventory models.
_AP_PREFIXES: tuple[str, ...] = ("AP",)  # WHY: Mist inventory model prefixes mapped to AP platform.
_SWITCH_PREFIXES: tuple[str, ...] = ("EX", "QFX")  # WHY: Mist inventory model prefixes mapped to switch platform.
_GATEWAY_PREFIXES: tuple[str, ...] = ("SRX", "SSR")  # WHY: Mist inventory model prefixes mapped to gateway platform.
_SWITCH_TOKENS: tuple[str, ...] = ("switch",)  # WHY: metric-name tokens routed to the switch compatibility rule.
_GATEWAY_TOKENS: tuple[str, ...] = ("gateway", "wan", "srx", "ssr")  # WHY: gateway compatibility metric tokens.
_AP_TOKENS: tuple[str, ...] = ("ap", "wifi")  # WHY: AP compatibility metric tokens.

# Table-driven metric → allowed-platforms map so _metric_compatible_with_platform stays under complexity 5.
_METRIC_PLATFORM_RULES: tuple[tuple[tuple[str, ...], frozenset[str]], ...] = (  # WHY: ordered dispatch table.
    (_SWITCH_TOKENS, frozenset({_PLATFORM_SWITCH, _PLATFORM_UNKNOWN})),  # WHY: switch metrics + unknown allowed.
    (_GATEWAY_TOKENS, frozenset({_PLATFORM_GATEWAY, _PLATFORM_UNKNOWN})),  # WHY: gateway metrics + unknown allowed.
    (_AP_TOKENS, frozenset({_PLATFORM_AP, _PLATFORM_UNKNOWN})),  # WHY: AP metrics + unknown allowed.
)

# Dependency-injection keys - accepted kwargs from configure_site_insights_exporter_dependencies.
_DEP_KEY_APISESSION: str = "apisession_dependency"  # WHY: mistapi session handle key.
_DEP_KEY_PROMPT: str = "prompt_utils"  # WHY: operator-prompt helpers key.
_DEP_KEY_PROCESSING: str = "data_processing_utils"  # WHY: row-flattening helpers key.
_DEP_KEY_EXPORTER: str = "data_exporter"  # WHY: CSV/format writer key.
_DEP_KEY_SSH: str = "enhanced_ssh_runner"  # WHY: SSH runner for filename sanitization key.
_DEP_KEY_METRICS: str = "insight_metrics_utils"  # WHY: insight metric helpers key.
_DEP_KEY_PCAP: str = "packet_capture_manager"  # WHY: MAC validation/normalization key.
_DEP_KEY_MISTAPI: str = "mistapi_dependency"  # WHY: mistapi client module key.

apisession: Any = None  # WHY: injected mistapi session handle used by exporter methods.
PromptUtils: Any = None  # WHY: injected operator-prompt helpers used during interactive flows.
DataProcessingUtils: Any = None  # WHY: injected row-flattening + escape helpers for CSV output.
DataExporter: Any = None  # WHY: injected backend writer supporting CSV and SQLite formats.
EnhancedSSHRunner: Any = None  # WHY: injected SSH runner used for filename sanitization.
InsightMetricsUtils: Any = None  # WHY: injected insight metric helpers for scope + metric lookups.
PacketCaptureManager: Any = None  # WHY: injected MAC address validator and normalizer.
mistapi: Any = None  # WHY: injected mistapi client module for API call dispatch.


def configure_site_insights_exporter_dependencies(**deps: Any) -> None:  # WHY: **kwargs bundles 8 DI params.
    """Configure runtime dependencies from MistHelper orchestration layer."""
    global apisession, PromptUtils, DataProcessingUtils, DataExporter  # WHY: publish session/prompt/processing/writer.
    global EnhancedSSHRunner, InsightMetricsUtils, PacketCaptureManager, mistapi  # WHY: publish SSH/metrics/pcap/api.
    apisession = deps[_DEP_KEY_APISESSION]  # WHY: bind session for exporters.
    PromptUtils = deps[_DEP_KEY_PROMPT]  # WHY: bind prompt helpers.
    DataProcessingUtils = deps[_DEP_KEY_PROCESSING]  # WHY: bind flatten/escape helpers.
    DataExporter = deps[_DEP_KEY_EXPORTER]  # WHY: bind CSV/format writer.
    EnhancedSSHRunner = deps[_DEP_KEY_SSH]  # WHY: bind SSH runner.
    InsightMetricsUtils = deps[_DEP_KEY_METRICS]  # WHY: bind insight metrics helpers.
    PacketCaptureManager = deps[_DEP_KEY_PCAP]  # WHY: bind packet capture manager.
    mistapi = deps[_DEP_KEY_MISTAPI]  # WHY: bind mistapi module.


def _allowed_platforms_for_metric(metric: str) -> frozenset[str] | None:  # WHY: table-driven compat lookup helper.
    """Return the platform set allowed for the given metric name, or None if unrestricted."""
    for tokens, allowed in _METRIC_PLATFORM_RULES:  # WHY: iterate the ordered dispatch table.
        if any(token in metric for token in tokens):  # WHY: first matching rule wins.
            return allowed  # WHY: matched rule dictates allowed platforms.
    return None  # WHY: no matching rule means metric is not platform-restricted.


class SiteInsightsExporter:
    """Extracted site insights export implementation for menu paths 74 and 76."""

    @staticmethod
    def _classify_device_platform(device_model: str) -> str:
        """Classify Mist inventory model into ap/switch/gateway for metric filtering."""
        model = (device_model or "").upper()  # WHY: normalize to uppercase for prefix matching.
        if model.startswith(_AP_PREFIXES):  # WHY: AP model prefix maps to AP platform.
            return _PLATFORM_AP  # WHY: matched AP family.
        if model.startswith(_SWITCH_PREFIXES):  # WHY: switch model prefix (EX/QFX).
            return _PLATFORM_SWITCH  # WHY: matched switch family.
        if model.startswith(_GATEWAY_PREFIXES):  # WHY: gateway model prefix (SRX/SSR).
            return _PLATFORM_GATEWAY  # WHY: matched gateway family.
        return _PLATFORM_UNKNOWN  # WHY: fallback classification for unmatched models.

    @staticmethod
    def _metric_compatible_with_platform(metric_name: str, device_platform: str) -> bool:
        """Skip clearly incompatible device metrics to prevent avoidable API 400 responses."""
        metric = (metric_name or "").lower()  # WHY: normalize metric name for token matching.
        allowed = _allowed_platforms_for_metric(metric)  # WHY: table-driven compatibility lookup.
        if allowed is None:  # WHY: metric matches no known platform token.
            return True  # WHY: unrestricted metrics are compatible with any platform.
        return device_platform in allowed  # WHY: only compatible when platform is in allowed set.

    @staticmethod
    def _normalize_device_mac_or_none(device_mac: str) -> str | None:
        """Validate and normalize device MAC for device insights endpoints."""
        if not device_mac:  # WHY: empty MAC has no meaningful normalization.
            return None  # WHY: signal absence to caller.
        if not PacketCaptureManager.validate_mac_address(device_mac):  # WHY: reject invalid MAC format.
            return None  # WHY: signal invalid input to caller.
        return PacketCaptureManager.normalize_mac_address(device_mac)  # WHY: normalized canonical form.
