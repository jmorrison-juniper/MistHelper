"""Unit tests for extracted GatewayStatsExporter module."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from src.gateway.gateway_stats_exporter import GatewayStatsExporter, configure_gateway_stats_exporter_dependencies


def _configure_dependencies() -> None:
    """Configure minimal dependency graph for gateway stats exporter tests."""
    configure_gateway_stats_exporter_dependencies(
        apisession_dependency=object(),
        mistapi_dependency=SimpleNamespace(),
        config_utils=SimpleNamespace(get_cached_or_prompted_org_id=MagicMock(return_value="org-1")),
        validation_utils=SimpleNamespace(validate_site_id=MagicMock(), validate_device_id=MagicMock()),
        data_processing_utils=SimpleNamespace(flatten_dict=MagicMock(side_effect=lambda row: row)),
        data_exporter=SimpleNamespace(write_with_format_selection=MagicMock()),
        rate_limiting_utils=SimpleNamespace(get_rate_limited_delay=MagicMock(return_value=(None, 0))),
        cache_utils=SimpleNamespace(check_and_generate_csv=MagicMock(return_value=True)),
        file_path_utils=SimpleNamespace(get_csv_path=MagicMock(return_value="test.csv")),
        connection_pool_fn=MagicMock(return_value=([], [])),
        fast_mode_max_retries=2,
        fast_mode_retry_delay=0.1,
        api_usage_cache={},
        tqdm_module=MagicMock(side_effect=lambda rows, **kwargs: rows),
        gateway_export_utils_ref=SimpleNamespace(_get_devices_with_sites=MagicMock(return_value=[])),
    )


def test_collect_device_wan_ips_ignores_empty_and_invalid_values() -> None:
    """WAN IP collection should keep only non-empty, non-null values mapped by port."""
    _configure_dependencies()

    row = {
        "if_stat_ge-0/0/0_ips": "10.0.0.1",
        "if_stat_ge-0/0/1_ips": "",
        "if_stat_ge-0/0/2_ips": "null",
    }

    device_ips = GatewayStatsExporter._collect_device_wan_ips(row)

    assert device_ips == {"10.0.0.1": ["0/0/0"]}


def test_find_ip_conflicts_returns_only_multi_port_ips() -> None:
    """Conflict finder should return only entries whose IP appears on multiple ports."""
    _configure_dependencies()

    conflicts = GatewayStatsExporter._find_ip_conflicts(
        {
            "10.0.0.1": ["0/0/0", "0/0/1"],
            "10.0.0.2": ["0/0/2"],
        },
        "gw-1",
    )

    assert conflicts == [{"value": "10.0.0.1", "ports": ["0/0/0", "0/0/1"]}]


def test_build_conflict_records_creates_port_level_rows() -> None:
    """Conflict record builder should generate one row per conflicting port."""
    _configure_dependencies()

    records = GatewayStatsExporter._build_conflict_records(
        [{"value": "10.0.0.1", "ports": ["0/0/0", "0/0/1"]}],
        "gw-1",
        "site-a",
    )

    assert len(records) == 2
    assert {record["port_name"] for record in records} == {"ge-0/0/0", "ge-0/0/1"}
    assert all(record["port_ip"] == "10.0.0.1" for record in records)
