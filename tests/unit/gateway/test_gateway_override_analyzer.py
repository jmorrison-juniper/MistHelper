"""Unit tests for extracted GatewayOverrideAnalyzer module."""

from __future__ import annotations

import csv
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from src.gateway.gateway_override_analyzer import GatewayOverrideAnalyzer
from src.gateway.gateway_override_analyzer import configure_gateway_override_analyzer_dependencies


class _PathResolver:
    """Simple path resolver to emulate FilePathUtils.get_csv_path."""

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir

    def get_csv_path(self, filename: str) -> str:
        return str(self.base_dir / filename)


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    """Write deterministic CSV fixtures for override analyzer unit tests."""
    with path.open("w", newline="", encoding="utf-8") as file_handle:
        writer = csv.DictWriter(file_handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_with_wan_overrides_writes_empty_header_when_no_overrides(tmp_path: Path) -> None:
    """Override analyzer should emit header-only CSV when no override rows are detected."""
    resolver = _PathResolver(tmp_path)

    _write_csv(
        tmp_path / "AllSiteGatewayConfigs.csv",
        ["id", "name", "site_id"],
        [{"id": "dev-1", "name": "gw-1", "site_id": "site-1"}],
    )
    _write_csv(
        tmp_path / "SiteList_ListAPI.csv",
        ["id", "name", "gatewaytemplate_id"],
        [{"id": "site-1", "name": "Site A", "gatewaytemplate_id": "tmpl-1"}],
    )
    _write_csv(
        tmp_path / "OrgGatewayTemplates.csv",
        ["id", "name"],
        [{"id": "tmpl-1", "name": "Template A"}],
    )

    configure_gateway_override_analyzer_dependencies(
        apisession_dependency=object(),
        mistapi_dependency=SimpleNamespace(),
        cache_utils=SimpleNamespace(check_and_generate_csv=MagicMock()),
        file_path_utils=SimpleNamespace(get_csv_path=resolver.get_csv_path),
        data_exporter=SimpleNamespace(save_data_to_output=MagicMock()),
        org_site_exporter=SimpleNamespace(sites_list_api=MagicMock()),
        mist_wan_target_ports=["ge-0/0/1"],
        connection_pool_fn=MagicMock(return_value=([], [])),
        gateway_export_utils_ref=SimpleNamespace(device_configs=MagicMock(), templates=MagicMock()),
    )

    GatewayOverrideAnalyzer.with_wan_overrides(fast=False)

    output_path = tmp_path / "GatewayOverriddenPorts.csv"
    assert output_path.exists()
    output_content = output_path.read_text(encoding="utf-8")
    assert "gateway_device_name" in output_content
    assert "template_name" in output_content
