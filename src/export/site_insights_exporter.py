"""Site insights exporter extracted from SiteExportUtils high-complexity branch."""

from __future__ import annotations  # WHY: PEP 563 postponed annotations for forward references.

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


def _allowed_platforms_for_metric(metric: str) -> frozenset[str] | None:  # WHY: table-driven compat lookup helper.
    """Return the platform set allowed for the given metric name, or None if unrestricted."""
    for tokens, allowed in _METRIC_PLATFORM_RULES:  # WHY: iterate the ordered dispatch table.
        if any(token in metric for token in tokens):  # WHY: first matching rule wins.
            return allowed  # WHY: matched rule dictates allowed platforms.
    return None  # WHY: no matching rule means metric is not platform-restricted.


class SiteInsightsExporter:
    """Extracted site insights export implementation for menu paths 74 and 76."""

    def __init__(self, *, PacketCaptureManager) -> None:  # WHY: constructor injection replaces module globals.
        """Store injected dependencies on the instance for use by exporter methods."""
        self.PacketCaptureManager = PacketCaptureManager  # WHY: bind MAC validator/normalizer to instance.

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

    def _normalize_device_mac_or_none(self, device_mac: str) -> str | None:
        """Validate and normalize device MAC for device insights endpoints."""
        if not device_mac:  # WHY: empty MAC has no meaningful normalization.
            return None  # WHY: signal absence to caller.
        if not self.PacketCaptureManager.validate_mac_address(device_mac):  # WHY: reject invalid MAC format.
            return None  # WHY: signal invalid input to caller.
        return self.PacketCaptureManager.normalize_mac_address(device_mac)  # WHY: normalized canonical form.
