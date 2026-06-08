"""Unit tests for the WanOverrideWalker end-to-end behavior."""

from __future__ import annotations

import csv
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from src.gateway.overrides import (
    WanOverrideWalker,
    configure_gateway_override_dependencies,
)


class _PathResolver:
    """Simple path resolver to emulate FilePathUtils.get_csv_path."""

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir  # Root directory where CSV fixtures live

    def get_csv_path(self, filename: str) -> str:
        return str(self.base_dir / filename)  # Resolve to fixture path on disk


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    """Write deterministic CSV fixtures for the WAN override walker tests."""
    with path.open("w", newline="", encoding="utf-8") as file_handle:  # Open fixture file for write
        writer = csv.DictWriter(file_handle, fieldnames=fieldnames)  # Build dict-based CSV writer
        writer.writeheader()  # Emit the header row first
        writer.writerows(rows)  # Emit all data rows in deterministic order


def test_walk_writes_empty_header_when_no_overrides(tmp_path: Path) -> None:
    """WanOverrideWalker.walk should emit header-only CSV when no override rows are detected."""
    resolver = _PathResolver(tmp_path)  # Path resolver pointed at the per-test tmp dir

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

    configure_gateway_override_dependencies(
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

    WanOverrideWalker.walk(fast=False)  # Run the orchestrator end-to-end

    output_path = tmp_path / "GatewayOverriddenPorts.csv"  # Report file written by the writer
    assert output_path.exists()  # Walker should always produce the report file
    output_content = output_path.read_text(encoding="utf-8")  # Read header for assertion
    assert "gateway_device_name" in output_content  # Header must include the device name column
    assert "template_name" in output_content  # Header must include the template name column
