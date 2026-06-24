"""Unit tests for the WAN override walker (no-target-ports early-exit path)."""

from unittest.mock import MagicMock

from src.gateway.overrides import (
    WanOverrideWalker,
    configure_gateway_override_dependencies,
)


def test_wan_override_walker_returns_when_ports_not_configured(tmp_path) -> None:
    """Walker exits safely when MIST_WAN_TARGET_PORTS is empty."""
    cache_utils = MagicMock()  # Stand-in for CacheUtils dependency
    file_path_utils = MagicMock()  # Stand-in for FilePathUtils dependency
    data_exporter = MagicMock()  # Stand-in for DataExporter dependency
    org_site_exporter = MagicMock()  # Stand-in for OrgSiteExporter dependency
    gateway_ref = MagicMock()  # Stand-in for GatewayExportUtilsRef dependency
    configure_gateway_override_dependencies(
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
    WanOverrideWalker.walk(fast=False)  # Empty target ports should trigger early return
    assert not data_exporter.write_with_format_selection.called  # No writes when ports unconfigured
