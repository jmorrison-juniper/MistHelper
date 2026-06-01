"""Unit tests for extracted gateway override analyzer delegation."""

from unittest.mock import MagicMock

from src.gateway.gateway_override_analyzer import (
    GatewayOverrideAnalyzer,
    configure_gateway_override_analyzer_dependencies,
)


def test_gateway_override_analyzer_returns_when_ports_not_configured(tmp_path) -> None:
    """Analyzer exits safely when MIST_WAN_TARGET_PORTS is empty."""
    cache_utils = MagicMock()
    file_path_utils = MagicMock()
    data_exporter = MagicMock()
    org_site_exporter = MagicMock()
    gateway_ref = MagicMock()
    configure_gateway_override_analyzer_dependencies(
        apisession_dependency=MagicMock(),
        mistapi_dependency=MagicMock(),
        cache_utils=cache_utils,
        file_path_utils=file_path_utils,
        data_exporter=data_exporter,
        org_site_exporter=org_site_exporter,
        mist_wan_target_ports=[],
        connection_pool_fn=MagicMock(),
        gateway_export_utils_ref=gateway_ref,
    )
    GatewayOverrideAnalyzer.with_wan_overrides(fast=False)
    assert not data_exporter.save_data_to_output.called
