"""Unit tests for extracted SiteInsightsExporter helper logic."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock
import pytest

from src.export.site_insights_exporter import SiteInsightsExporter, configure_site_insights_exporter_dependencies


@pytest.fixture(autouse=True)
def clean_insights_dependencies():
    """Isolate tests by restoring dependencies after each test run."""
    yield
    configure_site_insights_exporter_dependencies(
        apisession_dependency=None,
        prompt_utils=None,
        data_processing_utils=None,
        data_exporter=None,
        enhanced_ssh_runner=None,
        insight_metrics_utils=None,
        packet_capture_manager=None,
        mistapi_dependency=None,
    )


def _configure_dependencies() -> None:
    """Configure minimal dependencies for insights helper tests."""
    configure_site_insights_exporter_dependencies(
        apisession_dependency=object(),
        prompt_utils=SimpleNamespace(select_site=MagicMock(), select_device=MagicMock()),
        data_processing_utils=SimpleNamespace(flatten_nested_fields=MagicMock(), escape_multiline=MagicMock()),
        data_exporter=SimpleNamespace(save_data_to_output=MagicMock()),
        enhanced_ssh_runner=SimpleNamespace(sanitize_filename=MagicMock(side_effect=lambda value: value)),
        insight_metrics_utils=SimpleNamespace(export_legacy=MagicMock(), get_by_scope=MagicMock(return_value=[])),
        packet_capture_manager=SimpleNamespace(
            validate_mac_address=MagicMock(return_value=True),
            normalize_mac_address=MagicMock(return_value="aa:bb:cc:dd:ee:ff"),
        ),
        mistapi_dependency=SimpleNamespace(),
    )


def test_classify_device_platform_by_model_prefix() -> None:
    """Device model prefixes should map to expected platform classification."""
    _configure_dependencies()

    assert SiteInsightsExporter._classify_device_platform("AP32") == "ap"
    assert SiteInsightsExporter._classify_device_platform("EX4300") == "switch"
    assert SiteInsightsExporter._classify_device_platform("SSR120") == "gateway"
    assert SiteInsightsExporter._classify_device_platform("UNKNOWN") == "unknown"


def test_metric_compatible_with_platform_filters_expected_tokens() -> None:
    """Metric compatibility should enforce platform-specific keyword filters."""
    _configure_dependencies()

    assert SiteInsightsExporter._metric_compatible_with_platform("switch_health", "switch") is True
    assert SiteInsightsExporter._metric_compatible_with_platform("switch_health", "ap") is False
    assert SiteInsightsExporter._metric_compatible_with_platform("gateway_uptime", "gateway") is True
    assert SiteInsightsExporter._metric_compatible_with_platform("wifi_capacity", "ap") is True
    assert SiteInsightsExporter._metric_compatible_with_platform("generic_metric", "ap") is True


def test_normalize_device_mac_or_none_respects_validator() -> None:
    """MAC normalizer should return None for invalid input and normalized value for valid input."""
    _configure_dependencies()

    assert SiteInsightsExporter._normalize_device_mac_or_none("") is None
    assert SiteInsightsExporter._normalize_device_mac_or_none("aa-bb") == "aa:bb:cc:dd:ee:ff"
