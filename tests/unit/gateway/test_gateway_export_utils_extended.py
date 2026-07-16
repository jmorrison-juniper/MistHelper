"""Wave 11 P2 coverage for src/gateway/gateway_export_utils.py (initiative #1018).

Covers the module-level helper functions and the ``GatewayExportUtils`` static methods that
are not exercised by the existing test_gateway_export_utils.py smoke tests. All external
collaborators (mistapi, CSV I/O helpers, cache utilities, exporters) are injected as
MagicMock(spec=...) fakes via the configure_gateway_export_utils_dependencies() DI hook.

No live network calls are made and no MistHelper import is touched.
"""

from __future__ import annotations  # WHY: PEP 604 union syntax used in helper type hints.

import csv  # WHY: build deterministic CSV fixtures for helper reads.
import logging  # WHY: caplog verification for structured log lines.
from pathlib import Path  # WHY: pathlib fixtures for tmp_path CSV round-trips.
from types import ModuleType, SimpleNamespace  # WHY: opaque namespaces stand in for injected modules.
from typing import Any, cast  # WHY: Any annotations mirror the SUT; cast(Any, x) for dynamic attr writes.
from unittest.mock import MagicMock, patch  # WHY: mandatory spec= mocks + patch.object for method injection.

import pytest  # WHY: fixtures + caplog for behaviour assertions.

from src.gateway.gateway_export_utils import (  # WHY: SUT direct import for helpers + class.
    EMPTY_CELL_MARKERS,
    MGMT_IP_MISSING_LABEL,
    NO_TEMPLATE_LABEL,
    STATUS_OFFLINE,
    STATUS_ONLINE,
    STATUS_UNKNOWN,
    TEMPLATE_ID_MISSING_LABEL,
    UNKNOWN_GATEWAY,
    UNKNOWN_SITE,
    GatewayExportUtils,
    _build_management_ip_row,
    _classify_connected_status,
    _fetch_site_name_lookup_from_api,
    _is_wan_port_column,
    _load_gateways_from_inventory_csv,
    _load_site_name_lookup_from_csv,
    _log_management_ip_row,
    _project_api_gateway_devices,
    _project_gateway_devices,
    _project_row_to_columns,
    _read_csv_rows,
    _resolve_template_name,
    _row_has_port_data,
    _select_wan_port_columns,
    _write_empty_filtered_port_marker,
    configure_gateway_export_utils_dependencies,
)

# WHY: capture pristine GatewayExportUtils methods at IMPORT TIME (before any test file
# mutates the class). The neighbouring test_gateway_export_utils.py reassigns
# GatewayExportUtils._get_devices_from_cache = MagicMock(...) without restoring it, so
# by the time our tests run the class attribute is polluted. Snapshotting here — while the
# class is still pristine — lets us reset it via the autouse fixture below.
_PRISTINE_GET_DEVICES_FROM_CACHE = staticmethod(GatewayExportUtils._get_devices_from_cache)
_PRISTINE_GET_DEVICES_FROM_API = staticmethod(GatewayExportUtils._get_devices_from_api)


@pytest.fixture(autouse=True)
def _restore_pristine_gateway_methods() -> None:
    """Restore pristine GatewayExportUtils methods before every test in this module."""
    cast(Any, GatewayExportUtils)._get_devices_from_cache = _PRISTINE_GET_DEVICES_FROM_CACHE  # WHY: undo pollution.
    cast(Any, GatewayExportUtils)._get_devices_from_api = _PRISTINE_GET_DEVICES_FROM_API  # WHY: undo pollution.


# -- Shared DI configuration helper -------------------------------------------------------


def _build_dependency_bundle(  # WHY: single-source keyword bundle for every configure() call.
    tmp_path: Path,
    *,
    apisession: Any = None,
    mistapi_dependency: Any = None,
    api_fetch_utils: Any = None,
    api_core_fetch_utils: Any = None,
    org_inventory_exporter: Any = None,
    org_site_exporter: Any = None,
    data_exporter: Any = None,
    data_processing_utils: Any = None,
    input_utils: Any = None,
    config_utils: Any = None,
) -> dict[str, Any]:
    """Return a minimal-but-complete dependency bundle for configure_gateway_export_utils_dependencies."""
    return {
        "apisession_dependency": apisession or object(),  # WHY: opaque object stand-in for the SDK session.
        "mistapi_dependency": mistapi_dependency or SimpleNamespace(),  # WHY: overridden per-test if needed.
        "config_utils": config_utils or SimpleNamespace(get_cached_or_prompted_org_id=MagicMock(return_value="org-1")),
        "cache_utils": SimpleNamespace(check_and_generate_csv=MagicMock()),  # WHY: no-op cache refresh.
        "file_path_utils": SimpleNamespace(get_csv_path=lambda name: str(tmp_path / name)),  # WHY: tmp fixture.
        "data_exporter": data_exporter or SimpleNamespace(write_with_format_selection=MagicMock()),
        "data_processing_utils": data_processing_utils
        or SimpleNamespace(
            flatten_nested_fields=MagicMock(side_effect=lambda rows: rows),
            escape_multiline=MagicMock(side_effect=lambda rows: rows),
        ),
        "api_fetch_utils": api_fetch_utils or SimpleNamespace(gateway_device_configs=MagicMock(return_value=[])),
        "api_core_fetch_utils": api_core_fetch_utils
        or SimpleNamespace(all_inventory_with_limit=MagicMock(return_value=[])),
        "org_inventory_exporter": org_inventory_exporter
        or SimpleNamespace(inventory=MagicMock(), gateways_with_site_info=MagicMock()),
        "org_site_exporter": org_site_exporter or SimpleNamespace(sites=MagicMock(), sites_list_api=MagicMock()),
        "input_utils": input_utils or SimpleNamespace(safe_input=MagicMock(return_value="yes")),
        "execute_fn": MagicMock(return_value=([], [])),
        "validation_utils": SimpleNamespace(validate_site_id=MagicMock(), validate_device_id=MagicMock()),
        "rate_limiting_utils": SimpleNamespace(get_rate_limited_delay=MagicMock(return_value=(None, 0))),
        "mist_wan_target_ports": ["ge-0/0/1", "ge-0/0/2"],
        "mist_site_exclude_prefix": "",
        "fast_mode_max_retries": 2,
        "fast_mode_retry_delay": 0.01,
        "api_usage_cache": {},
        "tqdm_module": lambda iterable, **_: iterable,
    }


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    """Write a CSV fixture with a stable header order."""
    with path.open("w", newline="", encoding="utf-8") as fh:  # WHY: newline='' per csv module docs.
        writer = csv.DictWriter(fh, fieldnames=fieldnames)  # WHY: dict-based writer for readability.
        writer.writeheader()  # WHY: emit header row for DictReader consumers.
        writer.writerows(rows)  # WHY: emit deterministic data rows.


# -- _classify_connected_status --------------------------------------------------------------


class TestClassifyConnectedStatus:
    """Legacy Online/Offline/Unknown mapping for the connected CSV cell."""

    @pytest.mark.parametrize("token", ["true", "TRUE", "1", "yes", "  Yes  "])
    def test_truthy_tokens_map_to_online(self, token: str) -> None:
        """All truthy tokens (any case, whitespace) map to Online."""
        assert _classify_connected_status(token) == STATUS_ONLINE  # WHY: legacy Online string preserved.

    @pytest.mark.parametrize("token", ["false", "FALSE", "0", "no"])
    def test_falsy_tokens_map_to_offline(self, token: str) -> None:
        """All falsy tokens map to Offline."""
        assert _classify_connected_status(token) == STATUS_OFFLINE  # WHY: legacy Offline string preserved.

    @pytest.mark.parametrize("token", ["", "maybe", "nan"])
    def test_unrecognised_tokens_map_to_unknown(self, token: str) -> None:
        """Anything else falls back to Unknown (legacy behaviour)."""
        assert _classify_connected_status(token) == STATUS_UNKNOWN  # WHY: legacy fallback preserved.


# -- _read_csv_rows -------------------------------------------------------------------------


class TestReadCsvRows:
    """Cache-name-driven CSV reader used by every management-IP correlation path."""

    def test_reads_rows_via_file_path_utils(self, tmp_path: Path) -> None:
        """Rows are returned as dict list; file path resolved via FilePathUtils.get_csv_path."""
        configure_gateway_export_utils_dependencies(**_build_dependency_bundle(tmp_path))  # WHY: wire DI.
        target = tmp_path / "SiteList.csv"  # WHY: pick one of the fixed input names.
        _write_csv(
            target,
            ["id", "name"],
            [{"id": "s1", "name": "Site 1"}, {"id": "s2", "name": "Site 2"}],
        )
        rows = _read_csv_rows("SiteList.csv")  # WHY: helper resolves and reads by logical name.
        assert rows == [{"id": "s1", "name": "Site 1"}, {"id": "s2", "name": "Site 2"}]


# -- _log_management_ip_row -----------------------------------------------------------------


class TestLogManagementIpRow:
    """Per-device debug logs preserve the two legacy phrasings."""

    def test_with_ip_uses_mgmt_ip_phrase(self, caplog: pytest.LogCaptureFixture) -> None:
        """When an IP is present the log includes the IP."""
        caplog.set_level(logging.DEBUG)  # WHY: helper emits at DEBUG level.
        _log_management_ip_row("gw1", "10.1.1.1", STATUS_ONLINE, "TplA")
        assert any("Management IP 10.1.1.1" in rec.getMessage() for rec in caplog.records)

    def test_without_ip_uses_no_management_ip_phrase(self, caplog: pytest.LogCaptureFixture) -> None:
        """When no IP is present the log uses the legacy 'no management IP configured' phrase."""
        caplog.set_level(logging.DEBUG)  # WHY: helper emits at DEBUG level.
        _log_management_ip_row("gw1", "", STATUS_OFFLINE, "TplA")
        assert any("No management IP configured" in rec.getMessage() for rec in caplog.records)


# -- _resolve_template_name -----------------------------------------------------------------


class TestResolveTemplateName:
    """Legacy 'No Template' fallback rules for the template lookup."""

    def test_empty_id_returns_no_template_label(self) -> None:
        """Empty template_id yields the legacy 'No Template' label."""
        assert _resolve_template_name({"t1": "TemplateA"}, "") == NO_TEMPLATE_LABEL

    def test_known_id_returns_template_name(self) -> None:
        """Known template_id returns the mapped display name."""
        assert _resolve_template_name({"t1": "TemplateA"}, "t1") == "TemplateA"

    def test_unknown_id_returns_no_template_label(self) -> None:
        """Unknown template_id falls back to the legacy label."""
        assert _resolve_template_name({"t1": "TemplateA"}, "t9") == NO_TEMPLATE_LABEL


# -- _build_management_ip_row ---------------------------------------------------------------


class TestBuildManagementIpRow:
    """Row-builder correlates device + lookups into the final management-IP row shape."""

    def test_full_correlation_populates_all_fields(self) -> None:
        """Every field is populated when device+lookups are complete."""
        device = {
            "name": "gw1",
            "site_id": "s1",
            "site_name": "Site One",
            "connected": "true",
        }
        lookups: dict[str, dict[Any, Any]] = {
            "site": {"s1": {"gatewaytemplate_id": "t1"}},
            "template": {"t1": "TplA"},
            "mgmt_ip": {"gw1": "10.0.0.1"},
        }
        row, mgmt_ip = _build_management_ip_row(device, lookups)  # WHY: exercise full correlation path.
        assert row["gateway_name"] == "gw1"  # WHY: preserves device name.
        assert row["management_ip"] == "10.0.0.1"  # WHY: uses looked-up mgmt IP.
        assert row["status"] == STATUS_ONLINE  # WHY: 'true' maps to Online.
        assert row["site_name"] == "Site One"  # WHY: preserves device site_name.
        assert row["gateway_template"] == "TplA"  # WHY: resolves via template lookup.
        assert row["template_id"] == "t1"  # WHY: preserves resolved template_id.
        assert mgmt_ip == "10.0.0.1"  # WHY: returned tuple includes raw mgmt_ip.

    def test_missing_mgmt_ip_uses_legacy_fallback_label(self) -> None:
        """Empty mgmt_ip yields legacy 'Not Configured' label; template_id fallback used."""
        device = {"name": "gw2", "site_id": "s1", "site_name": "Site Two", "connected": "false"}
        lookups: dict[str, dict[Any, Any]] = {"site": {}, "template": {}, "mgmt_ip": {}}  # WHY: no matches.
        row, mgmt_ip = _build_management_ip_row(device, lookups)
        assert row["management_ip"] == MGMT_IP_MISSING_LABEL  # WHY: legacy label.
        assert row["template_id"] == TEMPLATE_ID_MISSING_LABEL  # WHY: legacy 'None' fallback.
        assert row["gateway_template"] == NO_TEMPLATE_LABEL  # WHY: legacy template fallback.
        assert row["status"] == STATUS_OFFLINE  # WHY: 'false' maps to Offline.
        assert mgmt_ip == ""  # WHY: helper still returns the raw empty string.

    def test_missing_device_name_defaults_to_unknown_gateway(self) -> None:
        """Missing 'name' key falls back to 'Unknown Gateway'."""
        device: dict[str, Any] = {"connected": "yes"}  # WHY: no name/site_id/site_name.
        lookups: dict[str, dict[Any, Any]] = {"site": {}, "template": {}, "mgmt_ip": {}}  # WHY: no matches.
        row, _ = _build_management_ip_row(device, lookups)
        assert row["gateway_name"] == UNKNOWN_GATEWAY  # WHY: legacy fallback text.
        assert row["site_name"] == UNKNOWN_SITE  # WHY: legacy fallback text.


# -- _select_wan_port_columns / _project_row_to_columns / _is_wan_port_column ---------------


class TestPortColumnHelpers:
    """WAN column filter, per-row projection and predicate helpers."""

    def test_select_wan_port_columns_matches_regex_only(self) -> None:
        """Only ge-0/0/N port_config columns without _vpn_paths_ noise pass the filter."""
        row = {
            "mac": "aa",
            "port_config_ge-0/0/1_speed": "1G",  # WHY: matches WAN pattern.
            "port_config_ge-0/0/1_vpn_paths_index": "0",  # WHY: excluded by _vpn_paths_ guard.
            "port_config_ge-0/0/2_duplex": "full",  # WHY: matches WAN pattern.
            "some_other_field": "x",  # WHY: excluded by regex.
        }
        selected = _select_wan_port_columns(row)  # WHY: exercise the pure filter helper.
        assert "port_config_ge-0/0/1_speed" in selected  # WHY: expected WAN column.
        assert "port_config_ge-0/0/2_duplex" in selected  # WHY: expected WAN column.
        assert "port_config_ge-0/0/1_vpn_paths_index" not in selected  # WHY: VPN column excluded.
        assert "mac" not in selected  # WHY: non-WAN column excluded.

    def test_project_row_to_columns_uses_empty_string_fallback(self) -> None:
        """Missing keys are projected as empty strings to preserve downstream shape."""
        row = {"a": "1", "b": "2"}
        projected = _project_row_to_columns(row, ["a", "b", "c"])
        assert projected == {"a": "1", "b": "2", "c": ""}  # WHY: 'c' fallback preserved.

    @pytest.mark.parametrize(
        "column,expected",
        [
            ("port_config_ge-0/0/0_speed", True),  # WHY: matches WAN pattern.
            ("port_config_ge-0/0/0_vpn_paths_x", False),  # WHY: VPN column filtered.
            ("random_col", False),  # WHY: non-matching column.
            ("port_config_xe-0/0/1", False),  # WHY: not ge- prefix.
        ],
    )
    def test_is_wan_port_column_predicate_matrix(self, column: str, expected: bool) -> None:
        """Predicate returns True only for WAN port_config columns without VPN noise."""
        assert _is_wan_port_column(column) is expected  # WHY: verify boolean matrix.

    def test_row_has_port_data_returns_true_when_any_value_present(self) -> None:
        """Predicate returns True as long as at least one requested column has non-empty value."""
        row = {"p1": "", "p2": None, "p3": "42"}  # WHY: only p3 has real data.
        assert _row_has_port_data(row, ["p1", "p2", "p3"]) is True  # WHY: p3 counts.

    def test_row_has_port_data_returns_false_when_all_markers(self) -> None:
        """Predicate returns False when every requested column is in EMPTY_CELL_MARKERS."""
        row: dict[str, Any] = {
            marker_key: marker for marker_key, marker in zip(["a", "b", "c"], EMPTY_CELL_MARKERS, strict=False)
        }
        assert _row_has_port_data(row, ["a", "b", "c"]) is False  # WHY: all values are markers.


# -- _write_empty_filtered_port_marker -----------------------------------------------------


class TestEmptyFilteredPortMarker:
    """Empty-projection fallback writes the legacy marker file to disk."""

    def test_marker_file_contains_legacy_no_matching_data_message(self, tmp_path: Path) -> None:
        """Marker file exists and contains the legacy phrase 'No matching data found.'"""
        configure_gateway_export_utils_dependencies(**_build_dependency_bundle(tmp_path))  # WHY: DI wiring.
        _write_empty_filtered_port_marker()  # WHY: exercise the marker write path.
        marker_path = tmp_path / "FilteredGatewayPortConfigs.csv"
        assert marker_path.exists()  # WHY: file must be created.
        assert "No matching data found." in marker_path.read_text(encoding="utf-8")


# -- _load_gateways_from_inventory_csv + _load_site_name_lookup_from_csv --------------------


class TestInventoryCsvLoaders:
    """CSV loaders back the fast-mode gateway device projection."""

    def test_load_gateways_filters_non_gateway_and_missing_ids(self, tmp_path: Path) -> None:
        """Only gateway rows with populated site_id + id are returned."""
        configure_gateway_export_utils_dependencies(**_build_dependency_bundle(tmp_path))  # WHY: DI wiring.
        _write_csv(
            tmp_path / "OrgInventory.csv",
            ["type", "site_id", "id", "name"],
            [
                {"type": "gateway", "site_id": "s1", "id": "d1", "name": "n1"},  # WHY: kept.
                {"type": "switch", "site_id": "s1", "id": "d2", "name": "n2"},  # WHY: filtered.
                {"type": "gateway", "site_id": "", "id": "d3", "name": "n3"},  # WHY: filtered.
                {"type": "gateway", "site_id": "s2", "id": "", "name": "n4"},  # WHY: filtered.
            ],
        )
        rows = _load_gateways_from_inventory_csv()
        assert len(rows) == 1  # WHY: only the first row passes all guards.
        assert rows[0]["id"] == "d1"  # WHY: verify the surviving row.

    def test_load_site_name_lookup_preserves_unknown_fallback(self, tmp_path: Path) -> None:
        """Missing name column yields the legacy 'Unknown Site' fallback."""
        configure_gateway_export_utils_dependencies(**_build_dependency_bundle(tmp_path))  # WHY: DI wiring.
        _write_csv(
            tmp_path / "SiteList.csv",
            ["id", "name"],
            [{"id": "s1", "name": "Alpha"}, {"id": "s2", "name": ""}],  # WHY: blank name for fallback.
        )
        lookup = _load_site_name_lookup_from_csv()
        assert lookup["s1"] == "Alpha"  # WHY: verify normal path.
        assert lookup["s2"] == ""  # WHY: DictReader emits '' when column present but blank.


# -- _project_gateway_devices ---------------------------------------------------------------


class TestProjectGatewayDevices:
    """Tuple-projection helper for cached inventory rows."""

    def test_projects_rows_with_lookup_fallback(self) -> None:
        """Missing site names default to 'Unknown Site'; missing fields default to ''."""
        gateways = [
            {"site_id": "s1", "id": "d1", "name": "n1"},
            {"site_id": "s-missing", "id": "d2", "name": "n2"},
            {},  # WHY: fully empty row exercises every fallback branch.
        ]
        site_name_lookup = {"s1": "Alpha"}
        projected = _project_gateway_devices(gateways, site_name_lookup)
        assert projected[0] == ("s1", "d1", "n1", "Alpha")  # WHY: normal path.
        assert projected[1] == ("s-missing", "d2", "n2", UNKNOWN_SITE)  # WHY: legacy fallback.
        assert projected[2] == ("", "", "", UNKNOWN_SITE)  # WHY: empty-row fallback.


# -- _fetch_site_name_lookup_from_api + _project_api_gateway_devices ------------------------


class TestApiDrivenProjections:
    """API-path helpers use the injected mistapi + APICoreFetchUtils facades."""

    def test_fetch_site_name_lookup_uses_mistapi_and_get_all(self, tmp_path: Path) -> None:
        """Delegates to mistapi.get_all and returns id->name mapping."""
        list_org_sites = MagicMock(return_value=SimpleNamespace(data=[]))  # WHY: first-page response stub.
        mistapi_module = ModuleType("mistapi_stub")  # WHY: real ModuleType so nested attr chain works.
        cast(Any, mistapi_module).api = SimpleNamespace(
            v1=SimpleNamespace(
                orgs=SimpleNamespace(
                    sites=SimpleNamespace(listOrgSites=list_org_sites),
                ),
            ),
        )
        get_all_mock = MagicMock(  # WHY: exhaust-all-pages helper stubbed to fixed sites list.
            return_value=[{"id": "s1", "name": "Site A"}, {"id": "s2"}]  # WHY: 2nd site lacks name.
        )
        cast(Any, mistapi_module).get_all = get_all_mock  # WHY: cast(Any) satisfies mypy + ruff.
        bundle = _build_dependency_bundle(tmp_path, mistapi_dependency=mistapi_module)  # WHY: wire stub.
        configure_gateway_export_utils_dependencies(**bundle)
        lookup = _fetch_site_name_lookup_from_api("org-1")
        assert lookup["s1"] == "Site A"  # WHY: normal path.
        assert lookup["s2"] == UNKNOWN_SITE  # WHY: legacy fallback when name absent.
        list_org_sites.assert_called_once()  # WHY: first-page call invoked exactly once.
        get_all_mock.assert_called_once()  # WHY: pagination helper invoked exactly once.

    def test_project_api_gateway_devices_filters_and_shapes_tuples(self) -> None:
        """API projection applies the same gateway-only + site/id guards as cache path."""
        devices = [
            {"type": "gateway", "site_id": "s1", "id": "d1", "name": "n1"},  # WHY: kept.
            {"type": "switch", "site_id": "s1", "id": "d2", "name": "n2"},  # WHY: filtered by type.
            {"type": "gateway", "site_id": "", "id": "d3"},  # WHY: filtered by empty site_id.
            {"type": "gateway", "site_id": "s2", "id": "d4", "name": "n4"},  # WHY: kept (Unknown site).
        ]
        site_name_lookup = {"s1": "Alpha"}
        result = _project_api_gateway_devices(devices, site_name_lookup)
        assert result == [
            ("s1", "d1", "n1", "Alpha"),
            ("s2", "d4", "n4", UNKNOWN_SITE),
        ]


# -- GatewayExportUtils static methods ------------------------------------------------------


class TestGatewayExportUtilsStaticMethods:
    """Static methods orchestrate the DI-wired helpers we tested above."""

    def test_with_site_info_delegates_to_org_inventory_exporter(self, tmp_path: Path) -> None:
        """Single-line delegate forwards to OrgInventoryExporter.gateways_with_site_info."""
        exporter = SimpleNamespace(inventory=MagicMock(), gateways_with_site_info=MagicMock())
        bundle = _build_dependency_bundle(tmp_path, org_inventory_exporter=exporter)  # WHY: capture call.
        configure_gateway_export_utils_dependencies(**bundle)
        GatewayExportUtils._with_site_info()
        exporter.gateways_with_site_info.assert_called_once()  # WHY: verify delegation.

    def test_load_management_ip_csv_inputs_returns_none_when_file_missing(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """FileNotFoundError path returns None and logs the legacy error message."""
        configure_gateway_export_utils_dependencies(**_build_dependency_bundle(tmp_path))  # WHY: DI wiring.
        caplog.set_level(logging.ERROR)  # WHY: error log path exercised here.
        assert GatewayExportUtils._load_management_ip_csv_inputs() is None  # WHY: no CSVs = None.
        assert any("Required CSV file not found" in rec.getMessage() for rec in caplog.records)

    def test_load_management_ip_csv_inputs_returns_all_four_tables(self, tmp_path: Path) -> None:
        """Happy path returns a 4-tuple of tables in the fixed order."""
        configure_gateway_export_utils_dependencies(**_build_dependency_bundle(tmp_path))  # WHY: DI wiring.
        for name in (
            "SiteList.csv",
            "OrgGatewayTemplates.csv",
            "GatewaysWithSiteInfo.csv",
            "AllSiteGatewayConfigs.csv",
        ):
            _write_csv(tmp_path / name, ["id"], [{"id": name}])  # WHY: single-row deterministic content.
        result = GatewayExportUtils._load_management_ip_csv_inputs()
        assert result is not None  # WHY: happy path must not be None.
        sites, templates, devices, configs = result
        assert sites == [{"id": "SiteList.csv"}]  # WHY: verify order.
        assert configs == [{"id": "AllSiteGatewayConfigs.csv"}]  # WHY: fourth slot preserved.

    def test_build_management_ip_lookups_shapes_three_maps(self, tmp_path: Path) -> None:
        """Lookups builder returns (site_lookup, template_lookup, mgmt_ip_lookup)."""
        configure_gateway_export_utils_dependencies(**_build_dependency_bundle(tmp_path))  # WHY: DI wiring.
        sites = [{"id": "s1", "name": "Site 1"}, {"id": "s2"}]  # WHY: two sites for lookup.
        templates = [{"id": "t1", "name": "T1"}, {"id": "t2"}]  # WHY: legacy 'Unknown Template' fallback.
        configs = [
            {"name": "gw1", "gateway_mgmt_overlay_ip_ip": "10.1.1.1"},
            {"name": "gw2"},  # WHY: missing mgmt IP yields empty string in lookup.
        ]
        site_lookup, template_lookup, mgmt_ip_lookup = GatewayExportUtils._build_management_ip_lookups(
            sites, templates, configs
        )
        assert site_lookup["s1"] == {"id": "s1", "name": "Site 1"}  # WHY: full site preserved.
        assert template_lookup["t1"] == "T1"  # WHY: id -> name mapping.
        assert template_lookup["t2"] == "Unknown Template"  # WHY: legacy fallback for missing name.
        assert mgmt_ip_lookup == {"gw1": "10.1.1.1", "gw2": ""}  # WHY: verify shape.

    def test_build_management_ip_rows_counts_with_and_without_mgmt_ip(self, tmp_path: Path) -> None:
        """Row builder returns (rows, total_count, with_mgmt_ip_count)."""
        configure_gateway_export_utils_dependencies(**_build_dependency_bundle(tmp_path))  # WHY: DI wiring.
        devices = [
            {"name": "gw1", "site_id": "s1", "site_name": "S1", "connected": "true"},
            {"name": "gw2", "site_id": "s2", "site_name": "S2", "connected": "false"},
            {"name": "gw3", "site_id": "s3", "site_name": "S3", "connected": ""},
        ]
        site_lookup = {"s1": {"gatewaytemplate_id": "t1"}, "s2": {}, "s3": {}}
        template_lookup = {"t1": "TplA"}
        mgmt_ip_lookup = {"gw1": "10.0.0.1"}  # WHY: only gw1 has a mgmt IP.
        rows, total, with_ip = GatewayExportUtils._build_management_ip_rows(
            devices, site_lookup, template_lookup, mgmt_ip_lookup
        )
        assert total == 3  # WHY: three devices processed.
        assert with_ip == 1  # WHY: only gw1 counted.
        assert len(rows) == 3  # WHY: every device produces a row.

    def test_prime_management_ip_caches_calls_check_and_generate_csv_four_times(self, tmp_path: Path) -> None:
        """Cache-priming step refreshes all four CSVs via CacheUtils."""
        cache_calls: list[str] = []  # WHY: capture names in call order.
        bundle = _build_dependency_bundle(tmp_path)
        bundle["cache_utils"] = SimpleNamespace(
            check_and_generate_csv=MagicMock(side_effect=lambda name, fn: cache_calls.append(name))
        )
        configure_gateway_export_utils_dependencies(**bundle)
        GatewayExportUtils._prime_management_ip_caches(fast=False)
        assert cache_calls == [
            "SiteList.csv",
            "OrgGatewayTemplates.csv",
            "GatewaysWithSiteInfo.csv",
            "AllSiteGatewayConfigs.csv",
        ]

    def test_finalise_management_ip_output_sorts_rows_and_writes_via_exporter(self, tmp_path: Path) -> None:
        """Output rows are sorted then renamed and forwarded to DataExporter."""
        writer = MagicMock()
        bundle = _build_dependency_bundle(
            tmp_path,
            data_exporter=SimpleNamespace(write_with_format_selection=writer),
        )
        configure_gateway_export_utils_dependencies(**bundle)
        rows = [
            {
                "gateway_name": "gwB",
                "gateway_template": "TplB",
                "management_ip": "1.1.1.1",
                "status": STATUS_ONLINE,
                "site_name": "Site B",
            },
            {
                "gateway_name": "gwA",
                "gateway_template": "TplA",
                "management_ip": "2.2.2.2",
                "status": STATUS_OFFLINE,
                "site_name": "Site A",
            },
        ]
        GatewayExportUtils._finalise_management_ip_output(rows)
        writer.assert_called_once()  # WHY: single write invocation.
        renamed, filename = writer.call_args.args
        assert filename == "GatewayManagementIPs.csv"  # WHY: legacy output filename.
        assert renamed[0]["Gateway Template"] == "TplA"  # WHY: sorted by (template, name) ascending.
        assert renamed[1]["Gateway Name"] == "gwB"  # WHY: TplB entry sorts second.

    def test_emit_management_ip_summary_writes_completion_lines(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture
    ) -> None:
        """Summary emits legacy console lines and audit log entry."""
        configure_gateway_export_utils_dependencies(**_build_dependency_bundle(tmp_path))  # WHY: DI wiring.
        caplog.set_level(logging.INFO)  # WHY: audit line emitted at INFO.
        GatewayExportUtils._emit_management_ip_summary(gateways_processed=5, gateways_with_mgmt_ip=3)
        captured = capsys.readouterr().out  # WHY: assert on console output.
        assert "Gateway management IP export completed" in captured  # WHY: banner headline.
        assert "Total gateways processed: 5" in captured  # WHY: total line.
        assert "Gateways without management IPs: 2" in captured  # WHY: derived arithmetic.
        assert any("Gateway management IP export completed" in rec.getMessage() for rec in caplog.records)

    def test_management_ips_returns_early_when_load_fails(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """When _load_management_ip_csv_inputs returns None the outer flow exits without writing."""
        writer = MagicMock()
        bundle = _build_dependency_bundle(
            tmp_path,
            data_exporter=SimpleNamespace(write_with_format_selection=writer),
        )
        configure_gateway_export_utils_dependencies(**bundle)
        caplog.set_level(logging.ERROR)  # WHY: file-missing error surfaces at ERROR.
        # NOTE: CSVs are deliberately not created so the loader returns None.
        GatewayExportUtils.management_ips(fast=False)
        writer.assert_not_called()  # WHY: no writes on early exit.

    def test_management_ips_happy_path_writes_output(self, tmp_path: Path) -> None:
        """End-to-end management_ips writes the final CSV via the DataExporter."""
        writer = MagicMock()
        bundle = _build_dependency_bundle(
            tmp_path,
            data_exporter=SimpleNamespace(write_with_format_selection=writer),
        )
        configure_gateway_export_utils_dependencies(**bundle)
        _write_csv(
            tmp_path / "SiteList.csv",
            ["id", "gatewaytemplate_id"],
            [{"id": "s1", "gatewaytemplate_id": "t1"}],
        )
        _write_csv(tmp_path / "OrgGatewayTemplates.csv", ["id", "name"], [{"id": "t1", "name": "T1"}])
        _write_csv(
            tmp_path / "GatewaysWithSiteInfo.csv",
            ["name", "site_id", "site_name", "connected"],
            [{"name": "gw1", "site_id": "s1", "site_name": "S1", "connected": "true"}],
        )
        _write_csv(
            tmp_path / "AllSiteGatewayConfigs.csv",
            ["name", "gateway_mgmt_overlay_ip_ip"],
            [{"name": "gw1", "gateway_mgmt_overlay_ip_ip": "10.9.9.9"}],
        )
        GatewayExportUtils.management_ips(fast=False)
        writer.assert_called_once()  # WHY: single output write.
        rows, filename = writer.call_args.args
        assert filename == "GatewayManagementIPs.csv"  # WHY: legacy filename.
        assert rows[0]["Gateway Name"] == "gw1"  # WHY: single gateway processed.
        assert rows[0]["Management IP"] == "10.9.9.9"  # WHY: mgmt IP correlated.

    def test_build_filtered_port_rows_projects_wan_columns(self, tmp_path: Path) -> None:
        """Only rows with non-empty WAN ports are projected onto base + WAN column names."""
        configure_gateway_export_utils_dependencies(**_build_dependency_bundle(tmp_path))  # WHY: DI wiring.
        sanitized = [
            {"mac": "aa", "name": "gw1", "port_config_ge-0/0/1_speed": "1G"},
            {"mac": "bb", "name": "gw2", "port_config_ge-0/0/1_speed": ""},  # WHY: filtered out.
        ]
        rows = GatewayExportUtils._build_filtered_port_rows(sanitized)
        assert len(rows) == 1  # WHY: only gw1 survives filter.
        assert rows[0]["name"] == "gw1"  # WHY: base column preserved.
        assert rows[0]["port_config_ge-0/0/1_speed"] == "1G"  # WHY: WAN column preserved.

    def test_save_filtered_port_configs_writes_marker_when_empty(self, tmp_path: Path) -> None:
        """Empty projection triggers the legacy marker file write path."""
        configure_gateway_export_utils_dependencies(**_build_dependency_bundle(tmp_path))  # WHY: DI wiring.
        GatewayExportUtils._save_filtered_port_configs([], debug=False)
        marker = tmp_path / "FilteredGatewayPortConfigs.csv"
        assert marker.exists()  # WHY: marker file must be created.

    def test_save_filtered_port_configs_writes_via_data_exporter(self, tmp_path: Path) -> None:
        """Non-empty projection forwards rows to DataExporter.write_with_format_selection."""
        writer = MagicMock()
        bundle = _build_dependency_bundle(
            tmp_path,
            data_exporter=SimpleNamespace(write_with_format_selection=writer),
        )
        configure_gateway_export_utils_dependencies(**bundle)
        rows = [{"name": "gw1", "port_config_ge-0/0/1_speed": "1G"}]  # WHY: non-empty set.
        GatewayExportUtils._save_filtered_port_configs(rows, debug=True)  # WHY: also triggers sample log.
        writer.assert_called_once_with(rows, "FilteredGatewayPortConfigs.csv")  # WHY: verify args.

    def test_device_configs_returns_early_when_api_returns_nothing(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """No data from API leaves DataExporter untouched and logs the legacy warning."""
        writer = MagicMock()
        bundle = _build_dependency_bundle(
            tmp_path,
            api_fetch_utils=SimpleNamespace(gateway_device_configs=MagicMock(return_value=[])),
            data_exporter=SimpleNamespace(write_with_format_selection=writer),
        )
        configure_gateway_export_utils_dependencies(**bundle)
        caplog.set_level(logging.WARNING)  # WHY: no-data path emits a warning.
        GatewayExportUtils.device_configs(debug=False, fast=False)
        writer.assert_not_called()  # WHY: no writes on empty API response.

    def test_device_configs_writes_full_and_filtered_when_data_present(self, tmp_path: Path) -> None:
        """Happy path writes both AllSiteGatewayConfigs.csv and FilteredGatewayPortConfigs.csv."""
        writer = MagicMock()
        data = [{"mac": "aa", "name": "gw1", "port_config_ge-0/0/1_speed": "1G"}]  # WHY: 1 usable row.
        bundle = _build_dependency_bundle(
            tmp_path,
            api_fetch_utils=SimpleNamespace(gateway_device_configs=MagicMock(return_value=data)),
            data_exporter=SimpleNamespace(write_with_format_selection=writer),
        )
        configure_gateway_export_utils_dependencies(**bundle)
        GatewayExportUtils.device_configs(debug=False, fast=False)
        assert writer.call_count == 2  # WHY: full + filtered writes.
        first_args = writer.call_args_list[0].args
        second_args = writer.call_args_list[1].args
        assert first_args[1] == "AllSiteGatewayConfigs.csv"  # WHY: full write filename.
        assert second_args[1] == "FilteredGatewayPortConfigs.csv"  # WHY: filtered write filename.

    def test_templates_returns_early_when_no_templates(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Empty template list yields legacy warning log + operator message and no write."""
        writer = MagicMock()
        list_templates = MagicMock(return_value=SimpleNamespace(data=[]))
        mistapi_module = ModuleType("mistapi_stub")
        cast(Any, mistapi_module).api = SimpleNamespace(
            v1=SimpleNamespace(
                orgs=SimpleNamespace(gatewaytemplates=SimpleNamespace(listOrgGatewayTemplates=list_templates))
            )
        )
        bundle = _build_dependency_bundle(
            tmp_path,
            mistapi_dependency=mistapi_module,
            data_exporter=SimpleNamespace(write_with_format_selection=writer),
        )
        configure_gateway_export_utils_dependencies(**bundle)
        caplog.set_level(logging.WARNING)  # WHY: warn logged on empty template set.
        GatewayExportUtils.templates()
        writer.assert_not_called()  # WHY: no export when there are no templates.
        captured = capsys.readouterr().out
        assert "No gateway templates found" in captured  # WHY: legacy operator message.

    def test_templates_writes_export_when_templates_present(self, tmp_path: Path) -> None:
        """Happy path forwards flattened+escaped templates to DataExporter."""
        writer = MagicMock()
        templates_data = [{"id": "t1", "name": "TplA"}]  # WHY: 1 template.
        list_templates = MagicMock(return_value=SimpleNamespace(data=templates_data))
        mistapi_module = ModuleType("mistapi_stub")
        cast(Any, mistapi_module).api = SimpleNamespace(
            v1=SimpleNamespace(
                orgs=SimpleNamespace(gatewaytemplates=SimpleNamespace(listOrgGatewayTemplates=list_templates))
            )
        )
        bundle = _build_dependency_bundle(
            tmp_path,
            mistapi_dependency=mistapi_module,
            data_exporter=SimpleNamespace(write_with_format_selection=writer),
        )
        configure_gateway_export_utils_dependencies(**bundle)
        GatewayExportUtils.templates()
        writer.assert_called_once()  # WHY: single write.
        _, filename = writer.call_args.args
        assert filename == "OrgGatewayTemplates.csv"  # WHY: legacy filename preserved.

    def test_get_devices_with_sites_uses_api_when_fast_false(self, tmp_path: Path) -> None:
        """Non-fast path calls _get_devices_from_api and returns its output."""
        configure_gateway_export_utils_dependencies(**_build_dependency_bundle(tmp_path))  # WHY: DI wiring.
        expected = [("s1", "d1", "n1", "Alpha")]
        with patch.object(GatewayExportUtils, "_get_devices_from_api", return_value=expected):
            result = GatewayExportUtils._get_devices_with_sites("org-1", fast=False)
        assert result == expected  # WHY: pass-through of API-path result.

    def test_get_devices_from_api_uses_injected_fetchers(self, tmp_path: Path) -> None:
        """API-path aggregates APICoreFetchUtils inventory + mistapi site lookup."""
        inventory = [
            {"type": "gateway", "site_id": "s1", "id": "d1", "name": "gw1"},
            {"type": "switch", "site_id": "s1", "id": "d2"},  # WHY: filtered.
        ]
        list_org_sites = MagicMock(return_value=SimpleNamespace(data=[]))  # WHY: first-page response stub.
        mistapi_module = ModuleType("mistapi_stub")
        cast(Any, mistapi_module).api = SimpleNamespace(
            v1=SimpleNamespace(orgs=SimpleNamespace(sites=SimpleNamespace(listOrgSites=list_org_sites)))
        )
        cast(Any, mistapi_module).get_all = MagicMock(return_value=[{"id": "s1", "name": "SiteA"}])
        bundle = _build_dependency_bundle(
            tmp_path,
            mistapi_dependency=mistapi_module,
            api_core_fetch_utils=SimpleNamespace(all_inventory_with_limit=MagicMock(return_value=inventory)),
        )
        configure_gateway_export_utils_dependencies(**bundle)
        result = GatewayExportUtils._get_devices_from_api("org-1")
        assert result == [("s1", "d1", "gw1", "SiteA")]  # WHY: only the gateway row survives + resolved name.

    def test_get_devices_from_cache_falls_back_to_api_on_missing_csv(self, tmp_path: Path) -> None:
        """Missing cache CSVs trigger the except path which delegates to _get_devices_from_api."""
        # WHY: no CSV files exist in tmp_path so open() will raise FileNotFoundError.
        expected = [("s2", "d2", "gw2", "Beta")]
        bundle = _build_dependency_bundle(tmp_path)
        configure_gateway_export_utils_dependencies(**bundle)
        with patch.object(GatewayExportUtils, "_get_devices_from_api", return_value=expected) as api_stub:
            result = GatewayExportUtils._get_devices_from_cache()
        assert result == expected  # WHY: fallback result propagated.
        api_stub.assert_called_once_with("org-1")  # WHY: called with resolved org id.

    def test_get_devices_from_cache_happy_path(self, tmp_path: Path) -> None:
        """Present CSVs yield cache-driven projection with the injected exception guard bypassed."""
        _write_csv(
            tmp_path / "OrgInventory.csv",
            ["type", "site_id", "id", "name"],
            [{"type": "gateway", "site_id": "s1", "id": "d1", "name": "gw1"}],
        )
        _write_csv(tmp_path / "SiteList.csv", ["id", "name"], [{"id": "s1", "name": "Alpha"}])
        configure_gateway_export_utils_dependencies(**_build_dependency_bundle(tmp_path))
        result = GatewayExportUtils._get_devices_from_cache()
        assert result == [("s1", "d1", "gw1", "Alpha")]  # WHY: cache-driven projection succeeds.

    def test_get_site_ids_with_devices_dedupes_gateway_sites(self, tmp_path: Path) -> None:
        """Only distinct non-empty gateway site IDs are returned."""
        inventory = [
            {"type": "gateway", "site_id": "s1"},
            {"type": "gateway", "site_id": "s1"},  # WHY: dedupe target.
            {"type": "switch", "site_id": "s2"},  # WHY: filtered by type.
            {"type": "gateway", "site_id": ""},  # WHY: filtered by empty.
            {"type": "gateway", "site_id": "s3"},
        ]
        bundle = _build_dependency_bundle(
            tmp_path,
            api_core_fetch_utils=SimpleNamespace(all_inventory_with_limit=MagicMock(return_value=inventory)),
        )
        configure_gateway_export_utils_dependencies(**bundle)
        result = GatewayExportUtils._get_site_ids_with_devices("org-1")
        assert sorted(result) == ["s1", "s3"]  # WHY: dedupe + filter applied.

    def test_with_wan_overrides_delegates_to_walker(self, tmp_path: Path) -> None:
        """Static entry-point calls WanOverrideWalker.walk with the fast flag."""
        configure_gateway_export_utils_dependencies(**_build_dependency_bundle(tmp_path))  # WHY: DI wiring.
        from src.gateway.overrides import WanOverrideWalker  # WHY: explicit re-import from its true home.

        with patch.object(WanOverrideWalker, "walk") as stub:
            GatewayExportUtils.with_wan_overrides(fast=True)
        stub.assert_called_once_with(fast=True)  # WHY: verify delegation + fast flag.

    def test_wan2_variable_migration_invokes_migrator_execute(self, tmp_path: Path) -> None:
        """Entry-point wires deps into GatewayWan2VariableMigrator and calls execute()."""
        configure_gateway_export_utils_dependencies(**_build_dependency_bundle(tmp_path))  # WHY: DI wiring.
        import src.gateway.wan2_variable as wan2_module  # WHY: local import to allow patching.

        captured: dict[str, Any] = {}

        class _StubMigrator:
            """Test double capturing constructor + execute() invocations."""

            def __init__(self, deps: Any) -> None:
                captured["deps"] = deps  # WHY: verify deps forwarded verbatim.

            def execute(self, *, fast: bool, dry_run: bool) -> None:
                captured["fast"] = fast  # WHY: verify fast flag pass-through.
                captured["dry_run"] = dry_run  # WHY: verify dry_run flag pass-through.

        with patch.object(wan2_module, "GatewayWan2VariableMigrator", _StubMigrator):
            GatewayExportUtils.wan2_variable_migration(fast=True, dry_run=True)
        assert captured["fast"] is True  # WHY: flag forwarded to migrator.
        assert captured["dry_run"] is True  # WHY: flag forwarded to migrator.
        assert captured["deps"].org_id == "org-1"  # WHY: config utils returned 'org-1' in bundle.
