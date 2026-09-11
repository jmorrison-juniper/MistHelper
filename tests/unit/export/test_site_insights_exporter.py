"""Unit tests for extracted SiteInsightsExporter helper logic (Pattern 1 constructor injection)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from src.export.site_insights_exporter import SiteInsightsExporter


def _build_exporter(validator_return: bool = True) -> SiteInsightsExporter:
    """Construct a SiteInsightsExporter with a stub PacketCaptureManager for MAC normalization tests."""
    return SiteInsightsExporter(
        PacketCaptureManager=SimpleNamespace(
            validate_mac_address=MagicMock(return_value=validator_return),
            normalize_mac_address=MagicMock(return_value="aa:bb:cc:dd:ee:ff"),
        )
    )


def test_classify_device_platform_by_model_prefix() -> None:
    """Device model prefixes should map to expected platform classification."""
    assert SiteInsightsExporter._classify_device_platform("AP32") == "ap"
    assert SiteInsightsExporter._classify_device_platform("EX4300") == "switch"
    assert SiteInsightsExporter._classify_device_platform("SSR120") == "gateway"
    assert SiteInsightsExporter._classify_device_platform("UNKNOWN") == "unknown"


def test_metric_compatible_with_platform_filters_expected_tokens() -> None:
    """Metric compatibility should enforce platform-specific keyword filters."""
    assert SiteInsightsExporter._metric_compatible_with_platform("switch_health", "switch") is True
    assert SiteInsightsExporter._metric_compatible_with_platform("switch_health", "ap") is False
    assert SiteInsightsExporter._metric_compatible_with_platform("gateway_uptime", "gateway") is True
    assert SiteInsightsExporter._metric_compatible_with_platform("wifi_capacity", "ap") is True
    assert SiteInsightsExporter._metric_compatible_with_platform("generic_metric", "ap") is True


def test_normalize_device_mac_or_none_respects_validator() -> None:
    """MAC normalizer should return None for invalid input and normalized value for valid input."""
    exporter_invalid = _build_exporter(validator_return=False)
    assert exporter_invalid._normalize_device_mac_or_none("") is None

    exporter_valid = _build_exporter(validator_return=True)
    assert exporter_valid._normalize_device_mac_or_none("aa-bb") == "aa:bb:cc:dd:ee:ff"
