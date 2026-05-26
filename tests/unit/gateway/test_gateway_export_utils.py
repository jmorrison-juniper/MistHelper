"""Unit tests for extracted GatewayExportUtils module."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from src.gateway.gateway_export_utils import GatewayExportUtils
from src.gateway.gateway_export_utils import configure_gateway_export_utils_dependencies


def _configure_dependencies() -> None:
    """Configure minimal dependency graph for gateway export utility tests."""
    configure_gateway_export_utils_dependencies(
        apisession_dependency=object(),
        mistapi_dependency=SimpleNamespace(),
        config_utils=SimpleNamespace(get_cached_or_prompted_org_id=MagicMock(return_value="org-1")),
        cache_utils=SimpleNamespace(check_and_generate_csv=MagicMock()),
        file_path_utils=SimpleNamespace(get_csv_path=MagicMock(return_value="test.csv")),
        data_exporter=SimpleNamespace(save_data_to_output=MagicMock()),
        data_processing_utils=SimpleNamespace(flatten_nested_fields=MagicMock(side_effect=lambda rows: rows), escape_multiline=MagicMock(side_effect=lambda rows: rows)),
        api_fetch_utils=SimpleNamespace(gateway_device_configs=MagicMock(return_value=[])),
        api_core_fetch_utils=SimpleNamespace(all_inventory_with_limit=MagicMock(return_value=[])),
        org_inventory_exporter=SimpleNamespace(inventory=MagicMock(), gateways_with_site_info=MagicMock()),
        org_site_exporter=SimpleNamespace(sites=MagicMock(), sites_list_api=MagicMock()),
        input_utils=SimpleNamespace(safe_input=MagicMock(return_value="yes")),
        connection_pool_fn=MagicMock(return_value=([], [])),
        validation_utils=SimpleNamespace(validate_site_id=MagicMock(), validate_device_id=MagicMock()),
        rate_limiting_utils=SimpleNamespace(get_rate_limited_delay=MagicMock(return_value=(None, 0))),
        mist_wan_target_ports=["ge-0/0/1"],
        mist_site_exclude_prefix="",
        fast_mode_max_retries=2,
        fast_mode_retry_delay=0.1,
        api_usage_cache={},
        tqdm_module=MagicMock(side_effect=lambda rows, **kwargs: rows),
    )


def test_get_devices_with_sites_uses_cache_when_fast_enabled() -> None:
    """Gateway device lookup should use cache path when fast mode is enabled."""
    _configure_dependencies()

    expected_devices = [("site-1", "dev-1", "gw-1", "Site A")]
    GatewayExportUtils._get_devices_from_cache = MagicMock(return_value=expected_devices)

    actual_devices = GatewayExportUtils._get_devices_with_sites("org-1", fast=True)

    assert actual_devices == expected_devices
    GatewayExportUtils._get_devices_from_cache.assert_called_once()


def test_get_site_ids_with_devices_filters_gateway_entries_only() -> None:
    """Site-id helper should return only non-empty site IDs from gateway devices."""
    _configure_dependencies()

    from src.gateway import gateway_export_utils as module

    module.APICoreFetchUtils.all_inventory_with_limit = MagicMock(
        return_value=[
            {"type": "gateway", "site_id": "site-1"},
            {"type": "switch", "site_id": "site-2"},
            {"type": "gateway", "site_id": ""},
            {"type": "gateway", "site_id": "site-3"},
        ]
    )

    site_ids = GatewayExportUtils._get_site_ids_with_devices("org-1")

    assert sorted(site_ids) == ["site-1", "site-3"]


def test_with_wan_overrides_delegates_to_override_analyzer() -> None:
    """WAN override entrypoint should delegate execution to extracted override analyzer."""
    _configure_dependencies()

    from src.gateway import gateway_export_utils as module

    override_mock = MagicMock()
    original_method = module.GatewayOverrideAnalyzer.with_wan_overrides
    module.GatewayOverrideAnalyzer.with_wan_overrides = override_mock

    try:
        GatewayExportUtils.with_wan_overrides(fast=True)
        override_mock.assert_called_once_with(fast=True)
    finally:
        module.GatewayOverrideAnalyzer.with_wan_overrides = original_method
