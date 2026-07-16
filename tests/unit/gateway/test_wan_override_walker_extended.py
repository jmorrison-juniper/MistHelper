"""Extended unit tests for WanOverrideWalker covering the private helpers.

The pre-existing test_wan_override_walker.py exercises the happy path with an
empty override set; this extended file targets the remaining branches so the
walker's private helpers are locked against silent regressions.
"""

from __future__ import annotations

import csv
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from src.gateway.overrides import (
    GatewayOverrideDependencies,
    WanOverrideWalker,
    configure_gateway_override_dependencies,
)
from src.gateway.overrides import _deps as override_deps  # Module-level DI slots


class _PathResolver:
    """Simple path resolver to emulate FilePathUtils.get_csv_path."""

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir  # Fixture root for CSV files during the test

    def get_csv_path(self, filename: str) -> str:
        return str(self.base_dir / filename)  # Resolve to fixture path on disk


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    """Write deterministic CSV fixtures for the WAN override walker tests."""
    with path.open("w", newline="", encoding="utf-8") as file_handle:  # Open fixture file for write
        writer = csv.DictWriter(file_handle, fieldnames=fieldnames)  # DictWriter for headered CSV
        writer.writeheader()  # Emit the header row first
        writer.writerows(rows)  # Emit all data rows in deterministic order


def _configure_default_deps(tmp_path: Path) -> _PathResolver:
    """Wire the module-level dependency slots with tmp_path-based fakes."""
    resolver = _PathResolver(tmp_path)  # Path resolver pointed at the per-test tmp dir
    configure_gateway_override_dependencies(
        GatewayOverrideDependencies(
            apisession_dependency=object(),  # Not exercised by the walker directly
            mistapi_dependency=SimpleNamespace(),  # Not exercised by the walker directly
            cache_utils=SimpleNamespace(check_and_generate_csv=MagicMock()),  # No-op cache refresh
            file_path_utils=SimpleNamespace(get_csv_path=resolver.get_csv_path),  # CSV path helper
            data_exporter=SimpleNamespace(write_with_format_selection=MagicMock()),  # Report writer stub
            org_site_exporter=SimpleNamespace(sites_list_api=MagicMock()),  # Site list exporter stub
            mist_wan_target_ports=["ge-0/0/1"],  # Non-empty by default; tests may reassign
            execute_fn=MagicMock(return_value=([], [])),  # Pool exec stub for fast mode
            gateway_export_utils_ref=SimpleNamespace(  # Gateway export helper stubs
                device_configs=MagicMock(),
                templates=MagicMock(),
            ),
        )
    )
    return resolver  # Caller may use it to compose additional fixture paths


def test_walk_early_exits_when_no_target_ports_configured(tmp_path: Path, capsys, caplog) -> None:
    """walk() must short-circuit with a warning when MIST_WAN_TARGET_PORTS is empty."""
    _configure_default_deps(tmp_path)  # Wire dependencies with a non-empty default
    override_deps.MIST_WAN_TARGET_PORTS = []  # Force the early-exit branch under test

    with caplog.at_level("WARNING"):  # Capture the operator-visible warning
        WanOverrideWalker.walk(fast=False)  # Should return without touching CSVs

    stdout = capsys.readouterr().out  # Capture the legacy console message emitted before return
    assert "MIST_WAN_TARGET_PORTS not configured" in stdout  # Legacy console line preserved
    assert any(  # The warning is what operators grep for; verify it fires
        "MIST_WAN_TARGET_PORTS" in record.message for record in caplog.records
    )
    output_path = tmp_path / "GatewayOverriddenPorts.csv"  # Report file must NOT be produced
    assert not output_path.exists()  # Walker exits before invoking the report writer


def test_run_live_passes_invokes_second_and_third_pass_helpers(tmp_path: Path) -> None:
    """_run_live_passes must call DeviceDataFetcher.fetch_all and OverrideReportWriter.write_full."""
    _configure_default_deps(tmp_path)  # Wire dependencies for the write path

    devices_with_overrides = {  # Two flagged devices to prove the loop iterates
        "dev-1": {
            "device_id": "dev-1",
            "device_name": "gw-1",
            "site_id": "site-1",
            "site_name": "Site A",
            "template_id": "tmpl-1",
            "template_name": "Template A",
            "row_data": {},
            "overridden_ports": ["ge-0/0/1"],
        },
    }
    configs = [{"id": "dev-1"}]  # Represents the raw first-pass input
    fake_cache = {"dev-1": ({"ge-0/0/1": {"description": "wan"}}, {"ge-0/0/1": {"up": True}})}

    with (
        patch(
            "src.gateway.overrides.wan_override_walker.DeviceDataFetcher.fetch_all",
            return_value=fake_cache,
        ) as fetch_all,
        patch("src.gateway.overrides.wan_override_walker.OverrideReportWriter.write_full") as write_full,
    ):
        WanOverrideWalker._run_live_passes(
            fast=True,  # Fast mode selects the pool-managed fetch path
            target_ports=["ge-0/0/1"],
            configs=configs,
            devices_with_overrides=devices_with_overrides,
        )

    fetch_all.assert_called_once_with(devices_with_overrides, True)  # Delegates with fast flag
    write_full.assert_called_once()  # Report writer invoked exactly once
    _, kwargs = write_full.call_args  # Inspect the keyword payload for correctness
    assert kwargs["total_gateways"] == len(configs)  # Sourced from configs length
    assert kwargs["devices_with_overrides_count"] == len(devices_with_overrides)  # Distinct count
    assert kwargs["target_ports"] == ["ge-0/0/1"]  # Passed through verbatim
    assert kwargs["entries"], "Third pass must produce at least one port entry"  # Loop ran


def test_run_pipeline_invokes_write_empty_when_no_overrides(tmp_path: Path) -> None:
    """_run_pipeline must call OverrideReportWriter.write_empty() when zero devices have overrides."""
    _configure_default_deps(tmp_path)  # Wire dependencies for the walker
    _write_csv(
        tmp_path / "AllSiteGatewayConfigs.csv",
        ["id", "name", "site_id"],
        [{"id": "dev-1", "name": "gw-1", "site_id": "site-1"}],
    )
    _write_csv(
        tmp_path / "SiteList_ListAPI.csv",
        ["id", "name", "gatewaytemplate_id"],
        [{"id": "site-1", "name": "Site A", "gatewaytemplate_id": ""}],
    )
    _write_csv(
        tmp_path / "OrgGatewayTemplates.csv",
        ["id", "name"],
        [],
    )

    with (
        patch(
            "src.gateway.overrides.wan_override_walker.OverrideClassifier.classify",
            return_value=[],  # Force _classify_row to return None -> no overrides accumulated
        ),
        patch("src.gateway.overrides.wan_override_walker.OverrideReportWriter.write_empty") as write_empty,
        patch("src.gateway.overrides.wan_override_walker.OverrideReportWriter.write_full") as write_full,
    ):
        WanOverrideWalker._run_pipeline(fast=False, target_ports=["ge-0/0/1"])

    write_empty.assert_called_once()  # Compliant fleet -> header-only CSV branch
    write_full.assert_not_called()  # No live passes when nothing to fetch


def test_run_pipeline_dispatches_live_passes_when_overrides_detected(tmp_path: Path) -> None:
    """_run_pipeline must delegate to _run_live_passes when at least one device has overrides."""
    _configure_default_deps(tmp_path)  # Wire dependencies for the walker
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

    with (
        patch(
            "src.gateway.overrides.wan_override_walker.OverrideClassifier.classify",
            return_value=["ge-0/0/1"],  # Non-empty -> _classify_row returns a device_info dict
        ),
        patch("src.gateway.overrides.wan_override_walker.WanOverrideWalker._run_live_passes") as live,
    ):
        WanOverrideWalker._run_pipeline(fast=False, target_ports=["ge-0/0/1"])

    live.assert_called_once()  # Delegation must fire exactly once


def test_extract_row_identifiers_returns_none_for_missing_fields() -> None:
    """_extract_row_identifiers must return None when any identifier is blank."""
    assert (
        WanOverrideWalker._extract_row_identifiers(  # Missing device name
            {"name": "", "site_id": "site-1", "id": "dev-1"}
        )
        is None
    )
    assert (
        WanOverrideWalker._extract_row_identifiers(  # Whitespace-only site_id
            {"name": "gw-1", "site_id": "   ", "id": "dev-1"}
        )
        is None
    )
    assert (
        WanOverrideWalker._extract_row_identifiers({"name": "gw-1", "site_id": "site-1", "id": ""})  # Empty device id
        is None
    )


def test_extract_row_identifiers_returns_tuple_when_all_fields_present() -> None:
    """_extract_row_identifiers must return the trimmed (name, site_id, device_id) tuple."""
    result = WanOverrideWalker._extract_row_identifiers(  # Well-formed row
        {"name": " gw-1 ", "site_id": " site-1 ", "id": " dev-1 "}
    )
    assert result == ("gw-1", "site-1", "dev-1")  # Whitespace stripped from all three fields


def test_resolve_template_name_returns_no_template_when_site_unassigned() -> None:
    """_resolve_template_name must return ('', 'No Template') when the site has no template."""
    template_id, template_name = WanOverrideWalker._resolve_template_name(
        site_id="site-1",
        site_to_template={"site-1": ""},  # Empty means the site is not template-assigned
        template_lookup={},
    )
    assert template_id == ""  # No template UUID recorded
    assert template_name == "No Template"  # Legacy display label preserved


def test_resolve_template_name_returns_named_template_when_assigned() -> None:
    """_resolve_template_name must return (template_id, name) when the site is assigned."""
    template_id, template_name = WanOverrideWalker._resolve_template_name(
        site_id="site-1",
        site_to_template={"site-1": "tmpl-1"},  # Assignment exists
        template_lookup={"tmpl-1": "Template A"},  # Name is resolvable
    )
    assert template_id == "tmpl-1"  # UUID preserved
    assert template_name == "Template A"  # Human-readable name preserved


def test_classify_row_returns_none_when_identifiers_missing() -> None:
    """_classify_row must return None when _extract_row_identifiers guards the row out."""
    result = WanOverrideWalker._classify_row(
        row={"name": "", "site_id": "", "id": ""},  # Blank identifiers
        site_lookup={},
        site_to_template={},
        template_lookup={},
        target_ports=["ge-0/0/1"],
    )
    assert result is None  # Guard triggered before OverrideClassifier.classify runs


def test_classify_row_returns_none_when_no_overridden_ports_detected() -> None:
    """_classify_row must return None when OverrideClassifier reports no overridden ports."""
    with patch(
        "src.gateway.overrides.wan_override_walker.OverrideClassifier.classify",
        return_value=[],  # No overrides on this row
    ):
        result = WanOverrideWalker._classify_row(
            row={"name": "gw-1", "site_id": "site-1", "id": "dev-1"},
            site_lookup={"site-1": "Site A"},
            site_to_template={"site-1": "tmpl-1"},
            template_lookup={"tmpl-1": "Template A"},
            target_ports=["ge-0/0/1"],
        )
    assert result is None  # Empty override list must yield None to skip the device


def test_classify_row_returns_device_info_when_overrides_present() -> None:
    """_classify_row must return an 8-key device-info dict when overrides are detected."""
    with patch(
        "src.gateway.overrides.wan_override_walker.OverrideClassifier.classify",
        return_value=["ge-0/0/1"],  # One overridden port drives the full path
    ):
        result = WanOverrideWalker._classify_row(
            row={"name": "gw-1", "site_id": "site-1", "id": "dev-1", "extra": "keep"},
            site_lookup={"site-1": "Site A"},
            site_to_template={"site-1": "tmpl-1"},
            template_lookup={"tmpl-1": "Template A"},
            target_ports=["ge-0/0/1"],
        )
    assert result is not None  # Full path must materialize the device-info dict
    assert result["device_id"] == "dev-1"  # Key used by _identify_devices
    assert result["device_name"] == "gw-1"  # Reporting key
    assert result["site_id"] == "site-1"  # Cross-reference to Mist site
    assert result["site_name"] == "Site A"  # Resolved human-readable label
    assert result["template_id"] == "tmpl-1"  # Cross-reference to Mist template
    assert result["template_name"] == "Template A"  # Resolved template label
    assert result["overridden_ports"] == ["ge-0/0/1"]  # Passed through verbatim
    assert result["row_data"]["extra"] == "keep"  # Full row_data preserved for downstream


def test_identify_devices_skips_none_entries_and_keys_by_device_id() -> None:
    """_identify_devices must skip _classify_row -> None and key survivors by device_id."""
    configs = [  # One valid row and one row that should be filtered by the guard
        {"name": "gw-1", "site_id": "site-1", "id": "dev-1"},
        {"name": "", "site_id": "", "id": ""},  # Guarded out by _extract_row_identifiers
    ]
    with patch(
        "src.gateway.overrides.wan_override_walker.OverrideClassifier.classify",
        return_value=["ge-0/0/1"],  # Non-empty for the valid row
    ):
        result = WanOverrideWalker._identify_devices(
            configs=configs,
            lookups={
                "site_name": {"site-1": "Site A"},
                "site_template": {"site-1": "tmpl-1"},
                "template_name": {"tmpl-1": "Template A"},
            },
            target_ports=["ge-0/0/1"],
        )
    assert list(result.keys()) == ["dev-1"]  # Only the surviving row was accumulated
    assert result["dev-1"]["site_name"] == "Site A"  # Full device_info dict stored


def test_build_device_info_returns_full_8_key_dict() -> None:
    """_build_device_info must return the exact 8-key structure documented in the class."""
    result = WanOverrideWalker._build_device_info(
        identifiers=("gw-1", "site-1", "dev-1"),
        row={"name": "gw-1", "extra_col": "keep"},
        site_lookup={"site-1": "Site A"},
        template=("tmpl-1", "Template A"),
        overridden_ports=["ge-0/0/1"],
    )
    assert result == {  # Structural expectation locked so pipeline consumers don't drift
        "device_name": "gw-1",
        "site_id": "site-1",
        "device_id": "dev-1",
        "site_name": "Site A",
        "template_id": "tmpl-1",
        "template_name": "Template A",
        "row_data": {"name": "gw-1", "extra_col": "keep"},
        "overridden_ports": ["ge-0/0/1"],
    }


def test_build_device_info_defaults_site_name_to_unknown_when_missing() -> None:
    """_build_device_info must default site_name to 'Unknown Site' when lookup misses."""
    result = WanOverrideWalker._build_device_info(
        identifiers=("gw-1", "site-missing", "dev-1"),
        row={},
        site_lookup={},  # No entry for site-missing
        template=("", "No Template"),
        overridden_ports=[],
    )
    assert result["site_name"] == "Unknown Site"  # Legacy default label preserved


def test_assemble_entries_builds_one_row_per_device_port_pair() -> None:
    """_assemble_entries must iterate devices AND ports, producing one CSV row per pair."""
    devices_with_overrides = {  # Two devices with distinct port sets
        "dev-1": {
            "device_id": "dev-1",
            "device_name": "gw-1",
            "site_id": "site-1",
            "site_name": "Site A",
            "template_id": "tmpl-1",
            "template_name": "Template A",
            "row_data": {},
            "overridden_ports": ["ge-0/0/1", "ge-0/0/2"],  # Two overridden ports
        },
        "dev-2": {
            "device_id": "dev-2",
            "device_name": "gw-2",
            "site_id": "site-2",
            "site_name": "Site B",
            "template_id": "tmpl-2",
            "template_name": "Template B",
            "row_data": {},
            "overridden_ports": ["ge-0/0/3"],  # One overridden port
        },
    }
    cache = {  # port_configs + interface_stats for the third pass
        "dev-1": (
            {"ge-0/0/1": {"description": "wan1"}, "ge-0/0/2": {"description": "wan2"}},
            {"ge-0/0/1": {"up": True}, "ge-0/0/2": {"up": False}},
        ),
        # dev-2 intentionally missing from cache to exercise the ({}, {}) fallback
    }
    with patch(
        "src.gateway.overrides.wan_override_walker.OverrideClassifier.build_port_entry",
        side_effect=lambda device_info, port_name, **_: {  # Return unique identifier per pair
            "device_id": device_info["device_id"],
            "port_name": port_name,
        },
    ) as build_entry:
        result = WanOverrideWalker._assemble_entries(devices_with_overrides, cache)

    assert build_entry.call_count == 3  # 2 ports on dev-1 + 1 on dev-2 = 3 build calls
    assert result == [  # Order follows dict iteration then per-device port iteration
        {"device_id": "dev-1", "port_name": "ge-0/0/1"},
        {"device_id": "dev-1", "port_name": "ge-0/0/2"},
        {"device_id": "dev-2", "port_name": "ge-0/0/3"},
    ]
