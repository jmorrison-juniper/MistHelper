"""Extended unit tests for WAN2MigrationManager targeting Wave 15 coverage lift."""

from __future__ import annotations  # WHY: postpone hint evaluation for forward refs.

import builtins  # WHY: patch builtin open when injecting IO faults.
import io  # WHY: build in-memory CSV payloads for open() shims.
from types import SimpleNamespace  # WHY: lightweight fakes for injected modules.
from typing import Any  # WHY: type hints for fixture builder helpers.
from unittest.mock import MagicMock  # WHY: attach call assertions and side effects.

import pytest  # WHY: fixture support and monkeypatch access.

from src.gateway import wan2_migration_manager as module  # WHY: patch module-level slots directly.
from src.gateway.wan2_migration_manager import (
    OverrideAnalysisContext,  # WHY: build override analysis contexts in helper tests.
    WAN2MigrationDependencies,  # WHY: dependency bundle for wiring helper.
    WAN2MigrationManager,  # WHY: system under test.
    _is_meaningful_override_value,  # WHY: module-level predicate under test.
    _looks_like_subif_type_field,  # WHY: subif column predicate under test.
    _looks_like_wan2_field,  # WHY: WAN2 column predicate under test.
    _parse_json_ip_payload,  # WHY: shared JSON parser under test.
    _subif_name_from_type_column,  # WHY: subif name extractor under test.
    configure_wan2_migration_dependencies,  # WHY: wire fake deps into module.
)

# ---------- Shared fixtures ------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_module_state() -> Any:
    """Reset module-level dependency slots after each test to prevent cross-test pollution."""
    yield  # WHY: run test body first.
    module.apisession = None  # WHY: undo apisession injection.
    module.ConfigUtils = None  # WHY: undo ConfigUtils injection.
    module.CacheUtils = None  # WHY: undo CacheUtils injection.
    module.OrgSiteExporter = None  # WHY: undo exporter injection.
    module.GatewayExportUtils = None  # WHY: undo gateway export injection.
    module.FilePathUtils = None  # WHY: undo path resolver injection.
    module.InputUtils = None  # WHY: undo input helper injection.
    module.DataExporter = None  # WHY: undo data exporter injection.
    module.mistapi = None  # WHY: undo mistapi injection.
    module.MIST_SITE_EXCLUDE_PREFIX = ""  # WHY: undo prefix injection.


def _wire(
    *,
    site_exclude_prefix: str = "",
    safe_input: Any = None,
    site_settings_data: Any = None,
    update_status_code: int = 200,
    stop_signal: bool = False,
    csv_path_map: dict[str, str] | None = None,
) -> tuple[WAN2MigrationManager, dict[str, Any]]:
    """Build a WAN2MigrationManager wired with SimpleNamespace fakes.

    Returns the manager and a dict of the mocks/fakes for assertion.
    """
    safe_input_mock = safe_input if safe_input is not None else MagicMock(return_value="yes")  # WHY: default yes.
    write_mock = MagicMock()  # WHY: capture DataExporter writes.
    get_csv_path_mock = MagicMock(  # WHY: return caller-supplied filenames.
        side_effect=lambda name: (csv_path_map or {}).get(name, name)
    )
    check_stop_mock = MagicMock(return_value=stop_signal)  # WHY: cancel-signal toggle.

    update_response = SimpleNamespace(status_code=update_status_code)  # WHY: simulate API response envelope.
    site_settings_response = SimpleNamespace(data=site_settings_data or {})  # WHY: simulate getSetting envelope.

    mistapi_fake = SimpleNamespace(  # WHY: mimic mistapi.api.v1.sites.setting nested modules.
        api=SimpleNamespace(
            v1=SimpleNamespace(
                sites=SimpleNamespace(
                    setting=SimpleNamespace(
                        getSiteSetting=MagicMock(return_value=site_settings_response),
                        updateSiteSettings=MagicMock(return_value=update_response),
                    )
                )
            )
        )
    )

    configure_wan2_migration_dependencies(  # WHY: publish fakes into module globals.
        WAN2MigrationDependencies(
            apisession=object(),
            config_utils=SimpleNamespace(
                get_cached_or_prompted_org_id=MagicMock(return_value="org-1"),
                check_stop_signal=check_stop_mock,
            ),
            cache_utils=SimpleNamespace(check_and_generate_csv=MagicMock()),
            org_site_exporter=SimpleNamespace(sites=MagicMock()),
            gateway_export_utils=SimpleNamespace(device_configs=MagicMock(), templates=MagicMock()),
            file_path_utils=SimpleNamespace(get_csv_path=get_csv_path_mock),
            input_utils=SimpleNamespace(safe_input=safe_input_mock),
            data_exporter=SimpleNamespace(write_with_format_selection=write_mock),
            mistapi=mistapi_fake,
            site_exclude_prefix=site_exclude_prefix,
        )
    )

    manager = WAN2MigrationManager()  # WHY: instantiate SUT after wiring.
    return manager, {
        "safe_input": safe_input_mock,
        "write": write_mock,
        "get_csv_path": get_csv_path_mock,
        "check_stop": check_stop_mock,
        "mistapi": mistapi_fake,
        "update_response": update_response,
        "site_settings_response": site_settings_response,
    }


# ---------- Module-level pure helpers -------------------------------------


def test_is_meaningful_override_value_recognises_nullish_tokens() -> None:
    """Nullish tokens should not qualify as meaningful overrides."""
    assert _is_meaningful_override_value("") is False  # WHY: empty string is nullish.
    assert _is_meaningful_override_value(" null ") is False  # WHY: null token normalised via strip+lower.
    assert _is_meaningful_override_value("NONE") is False  # WHY: uppercase none normalised via lower.
    assert _is_meaningful_override_value("static") is True  # WHY: any real value qualifies.


def test_looks_like_wan2_field_matches_all_variants() -> None:
    """WAN2 field predicate accepts literal and variablised prefixes."""
    assert _looks_like_wan2_field("port_config_ge-0/0/1_ip_config") is True  # WHY: literal base-port scalar.
    assert _looks_like_wan2_field("port_config_ge-0/0/1.100_ip_config_type") is True  # WHY: subif variant.
    assert _looks_like_wan2_field("port_config_{{wan2_interface}}_ip_config") is True  # WHY: variablised scalar.
    assert _looks_like_wan2_field("port_config_ge-0/0/0_ip_config") is False  # WHY: different port rejected.
    assert _looks_like_wan2_field("random_column") is False  # WHY: unrelated column rejected.


def test_looks_like_subif_type_field_requires_both_prefix_and_suffix() -> None:
    """Subif-type predicate requires both subif prefix and _ip_config_type suffix."""
    assert _looks_like_subif_type_field("port_config_ge-0/0/1.100_ip_config_type") is True  # WHY: literal subif.
    assert _looks_like_subif_type_field("port_config_{{wan2_interface}}.42_ip_config_type") is True  # WHY: var subif.
    assert _looks_like_subif_type_field("port_config_ge-0/0/1_ip_config_type") is False  # WHY: base-port not subif.
    assert _looks_like_subif_type_field("port_config_ge-0/0/1.100_ip_config") is False  # WHY: wrong suffix.


def test_subif_name_from_type_column_strips_prefix_and_suffix() -> None:
    """Subif name recovery strips port_config_ prefix and _ip_config_type suffix."""
    assert _subif_name_from_type_column("port_config_ge-0/0/1.100_ip_config_type") == "ge-0/0/1.100"
    assert _subif_name_from_type_column("port_config_ge-0/0/1.42_ip_config_type") == "ge-0/0/1.42"


def test_parse_json_ip_payload_handles_all_paths() -> None:
    """JSON payload parser covers empty, malformed, static, and non-static branches."""
    assert _parse_json_ip_payload("") == ("", "", "", "")  # WHY: empty payload fast-path.
    assert _parse_json_ip_payload("{bad json}") == ("parse_error", "", "", "")  # WHY: parse error branch.
    assert _parse_json_ip_payload('{"type": "static", "ip": "10.1.1.1", "netmask": "24", "gateway": "10.1.1.254"}') == (
        "static",
        "10.1.1.1",
        "24",
        "10.1.1.254",
    )
    assert _parse_json_ip_payload('{"type": "dhcp"}') == ("dhcp", "", "", "")  # WHY: dhcp normalisation.
    assert _parse_json_ip_payload('{"type": ""}') == ("not_configured", "", "", "")  # WHY: empty type sentinel.


# ---------- WAN2MigrationManager helpers ----------------------------------


def test_apply_exclude_prefix_and_log_exclusion_result(capsys: pytest.CaptureFixture[str]) -> None:
    """apply_exclude_prefix removes matches; log_exclusion_result prints security banner."""
    manager, _ = _wire(site_exclude_prefix="LAB-")

    filtered = manager._apply_exclude_prefix(
        [{"name": "LAB-Test"}, {"name": "Prod-One"}, {"name": "LAB-Other"}], "LAB-"
    )
    assert [entry["name"] for entry in filtered] == ["Prod-One"]  # WHY: only non-matching kept.

    manager._log_exclusion_result(3, 1)  # WHY: exercise the removed>0 branch.
    stdout = capsys.readouterr().out
    assert "SECURITY" in stdout  # WHY: security banner emitted when removals happen.


def test_log_exclusion_result_reports_when_all_filtered(capsys: pytest.CaptureFixture[str]) -> None:
    """log_exclusion_result emits 'No sites remaining' when filtered_count is zero."""
    _wire(site_exclude_prefix="LAB-")

    WAN2MigrationManager._log_exclusion_result(2, 0)  # WHY: all-filtered branch.
    stdout = capsys.readouterr().out
    assert "No sites remaining" in stdout  # WHY: operator warning shown.


def test_filter_excluded_sites_returns_input_when_no_prefix_configured() -> None:
    """Site filter returns unmodified list when prefix is empty."""
    manager, _ = _wire(site_exclude_prefix="")

    sites = [{"name": "A"}, {"name": "B"}]
    assert manager._filter_excluded_sites(sites) == sites  # WHY: no-op when prefix blank.


def test_confirm_site_variable_operation_true_and_false(capsys: pytest.CaptureFixture[str]) -> None:
    """Confirmation returns True on 'yes' input and False on other input."""
    manager, mocks = _wire(safe_input=MagicMock(return_value="YES"))  # WHY: case-insensitive yes.
    assert manager._confirm_site_variable_operation(3) is True

    mocks["safe_input"].return_value = "no"  # WHY: switch to negative reply.
    assert manager._confirm_site_variable_operation(3) is False
    stdout = capsys.readouterr().out
    assert "Operation cancelled" in stdout  # WHY: cancel banner emitted.


def test_initialize_site_result_creates_expected_shape() -> None:
    """Initialised result dict has expected keys and zeroed counters."""
    manager, _ = _wire()
    result = manager._initialize_site_result("site-x", "Site X")

    assert result["site_id"] == "site-x"
    assert result["site_name"] == "Site X"
    assert result["variable_set"] is False
    assert result["critical_override_count"] == 0
    assert result["error"] == ""


def test_add_override_info_to_result_populates_counts_and_details() -> None:
    """add_override_info populates counters and formatted details when overrides present."""
    manager, _ = _wire()
    manager.site_overrides_map = {
        "site-1": [
            {
                "device_name": "gw-a",
                "port_identifier": "ge-0/0/1",
                "template_ip_type": "DHCP",
                "device_ip_type": "STATIC",
                "device_static_ip": "10.0.0.1",
                "device_netmask": "24",
                "device_gateway": "10.0.0.254",
                "override_severity": "CRITICAL",
                "ip_type_conflict": True,
            }
        ]
    }
    result = manager._initialize_site_result("site-1", "Site One")
    manager._add_override_info_to_result(result, "site-1")

    assert result["has_overrides"] is True
    assert result["override_devices"] == ["gw-a"]
    assert result["critical_override_count"] == 1
    assert result["total_override_count"] == 1
    assert "CRITICAL" in result["override_details"]


def test_add_override_info_to_result_returns_early_when_no_overrides() -> None:
    """add_override_info leaves result untouched when no overrides recorded."""
    manager, _ = _wire()
    manager.site_overrides_map = {}
    result = manager._initialize_site_result("site-y", "Site Y")
    manager._add_override_info_to_result(result, "site-y")

    assert result["has_overrides"] is False  # WHY: unchanged.
    assert result["override_devices"] == []  # WHY: unchanged.


def test_count_severity_buckets_ignores_unknown_severity() -> None:
    """Severity bucketing ignores UNKNOWN and typos while tallying known buckets."""
    counts = WAN2MigrationManager._count_severity_buckets(
        [
            {"override_severity": "CRITICAL"},
            {"override_severity": "CRITICAL"},
            {"override_severity": "WARNING"},
            {"override_severity": "INFO"},
            {"override_severity": "UNKNOWN"},
            {"override_severity": "typo"},
        ]
    )
    assert counts == {"CRITICAL": 2, "WARNING": 1, "INFO": 1}


def test_format_single_override_covers_all_branches() -> None:
    """format_single_override produces different strings for full/ip-only/type-only cases."""
    full = WAN2MigrationManager._format_single_override(
        {
            "device_name": "gw-a",
            "port_identifier": "ge-0/0/1",
            "override_severity": "CRITICAL",
            "template_ip_type": "DHCP",
            "device_ip_type": "STATIC",
            "device_static_ip": "10.0.0.1",
            "device_netmask": "24",
        }
    )
    assert "10.0.0.124" in full  # WHY: static+netmask concatenated per format string.

    ip_only = WAN2MigrationManager._format_single_override(
        {
            "device_name": "gw-b",
            "port_identifier": "ge-0/0/1",
            "override_severity": "WARNING",
            "template_ip_type": "STATIC",
            "device_ip_type": "DHCP",
            "device_static_ip": "10.0.0.2",
            "device_netmask": "",
        }
    )
    assert ip_only.endswith(":10.0.0.2)")  # WHY: netmask omitted branch.

    types_only = WAN2MigrationManager._format_single_override(
        {
            "device_name": "gw-c",
            "port_identifier": "ge-0/0/1",
            "override_severity": "INFO",
            "template_ip_type": "DHCP",
            "device_ip_type": "DHCP",
            "device_static_ip": "",
            "device_netmask": "",
        }
    )
    assert types_only.endswith("DHCP->DHCP)")  # WHY: fallback branch with types only.


def test_format_override_details_joins_multiple_records() -> None:
    """format_override_details joins entries with '; ' separator."""
    manager, _ = _wire()
    details = manager._format_override_details(
        [
            {
                "device_name": "gw-1",
                "port_identifier": "ge-0/0/1",
                "override_severity": "INFO",
                "template_ip_type": "DHCP",
                "device_ip_type": "DHCP",
                "device_static_ip": "",
                "device_netmask": "",
            },
            {
                "device_name": "gw-2",
                "port_identifier": "ge-0/0/1",
                "override_severity": "CRITICAL",
                "template_ip_type": "DHCP",
                "device_ip_type": "STATIC",
                "device_static_ip": "10.0.0.5",
                "device_netmask": "24",
            },
        ]
    )
    assert "; " in details  # WHY: separator inserted between entries.
    assert details.count("gw-") == 2  # WHY: both devices present.


def test_classify_manual_review_covers_all_levels() -> None:
    """classify_manual_review returns CRITICAL/WARNING/INFO/No based on counts."""
    assert WAN2MigrationManager._classify_manual_review({"critical_override_count": 1}) == "CRITICAL"
    assert WAN2MigrationManager._classify_manual_review({"warning_override_count": 1}) == "WARNING"
    assert WAN2MigrationManager._classify_manual_review({"info_override_count": 1}) == "INFO"
    assert WAN2MigrationManager._classify_manual_review({}) == "No"


def test_is_info_only_override_covers_all_branches() -> None:
    """is_info_only_override: no overrides -> False; critical -> False; warning -> False; only info -> True."""
    assert WAN2MigrationManager._is_info_only_override({"has_overrides": False}) is False
    assert WAN2MigrationManager._is_info_only_override({"has_overrides": True, "critical_override_count": 1}) is False
    assert WAN2MigrationManager._is_info_only_override({"has_overrides": True, "warning_override_count": 1}) is False
    assert (
        WAN2MigrationManager._is_info_only_override(
            {"has_overrides": True, "critical_override_count": 0, "warning_override_count": 0}
        )
        is True
    )


def test_count_override_severities_tallies_all_buckets() -> None:
    """count_override_severities tallies override/critical/warning/info correctly."""
    counters = WAN2MigrationManager._count_override_severities(
        [
            {"has_overrides": True, "critical_override_count": 1},
            {"has_overrides": True, "warning_override_count": 1},
            {"has_overrides": True, "info_override_count": 1},
            {"has_overrides": False},
        ]
    )
    assert counters["override"] == 3  # WHY: three records had overrides.
    assert counters["critical"] == 1
    assert counters["warning"] == 1
    assert counters["info"] == 1  # WHY: info-only record identified.


def test_accumulate_severity_increments_flags() -> None:
    """accumulate_severity increments counters for a single record."""
    counters = {"override": 0, "critical": 0, "warning": 0, "info": 0}
    WAN2MigrationManager._accumulate_severity({"has_overrides": True, "warning_override_count": 2}, counters)
    assert counters["override"] == 1
    assert counters["warning"] == 1


def test_parse_template_ip_config_extracts_fields() -> None:
    """parse_template_ip_config extracts fields from the template port_config JSON."""
    port_config_json = '{"type": "static", "ip": "10.1.0.1", "netmask": "24", "gateway": "10.1.0.254"}'
    parsed = WAN2MigrationManager._parse_template_ip_config({"port_config_ge-0/0/1_ip_config": port_config_json})
    assert parsed["ip_type"] == "static"
    assert parsed["ip"] == "10.1.0.1"

    empty = WAN2MigrationManager._parse_template_ip_config({})  # WHY: missing key -> not_configured.
    assert empty["ip_type"] == "not_configured"


def test_extract_base_port_ip_config_uses_shared_parser() -> None:
    """extract_base_port_ip_config wraps _parse_json_ip_payload with port identifier."""
    result = WAN2MigrationManager._extract_base_port_ip_config({"port_config_ge-0/0/1_ip_config": '{"type": "dhcp"}'})
    assert result["port_identifier"] == "ge-0/0/1"
    assert result["ip_type"] == "dhcp"


def test_build_subif_config_returns_normalised_shape() -> None:
    """build_subif_config recovers subif identifier and IP metadata from column names."""
    row = {
        "port_config_ge-0/0/1.100_ip_config_type": "STATIC",
        "port_config_ge-0/0/1.100_ip_config_ip": "10.2.0.1",
        "port_config_ge-0/0/1.100_ip_config_netmask": "24",
        "port_config_ge-0/0/1.100_ip_config_gateway": "10.2.0.254",
    }
    parsed = WAN2MigrationManager._build_subif_config(row, "port_config_ge-0/0/1.100_ip_config_type")
    assert parsed["port_identifier"] == "ge-0/0/1.100"
    assert parsed["ip_type"] == "static"  # WHY: normalised to lowercase.
    assert parsed["ip"] == "10.2.0.1"
    assert parsed["gateway"] == "10.2.0.254"


def test_get_wan2_override_fields_filters_columns() -> None:
    """get_wan2_override_fields returns only columns matching WAN2 prefixes."""
    row = {
        "port_config_ge-0/0/1_ip_config": "{}",
        "port_config_ge-0/0/0_ip_config": "{}",
        "unrelated": "x",
    }
    fields = WAN2MigrationManager._get_wan2_override_fields(row)
    assert "port_config_ge-0/0/1_ip_config" in fields
    assert "port_config_ge-0/0/0_ip_config" not in fields
    assert "unrelated" not in fields


def test_check_has_meaningful_override_skips_vpn_marker() -> None:
    """check_has_meaningful_override ignores fields containing VPN marker."""
    row = {"port_config_ge-0/0/1_vpn_paths_x": "static"}  # WHY: VPN marker column ignored.
    assert WAN2MigrationManager._check_has_meaningful_override(row, list(row.keys())) is False

    row2 = {"port_config_ge-0/0/1_ip_config": "static"}
    assert WAN2MigrationManager._check_has_meaningful_override(row2, list(row2.keys())) is True


def test_build_override_record_shapes_all_fields() -> None:
    """build_override_record produces a dict with all expected keys and uppercased tokens."""
    context = OverrideAnalysisContext(
        site_id="site-1",
        device_name="gw-1",
        device_ip={
            "port_identifier": "ge-0/0/1",
            "ip_type": "static",
            "ip": "10.0.0.1",
            "netmask": "24",
            "gateway": "10.0.0.254",
        },
        template_ip_type="dhcp",
    )
    record = WAN2MigrationManager._build_override_record(context)
    assert record["template_ip_type"] == "DHCP"  # WHY: uppercased.
    assert record["device_ip_type"] == "STATIC"
    assert record["ip_type_conflict"] is True  # WHY: dhcp->static -> CRITICAL.
    assert record["override_severity"] == "CRITICAL"


def test_extract_device_ip_config_prefers_subinterface_when_present() -> None:
    """extract_device_ip_config returns subif dict when available, base otherwise."""
    manager, _ = _wire()
    row = {
        "port_config_ge-0/0/1.100_ip_config_type": "DHCP",
        "port_config_ge-0/0/1.100_ip_config_ip": "",
        "port_config_ge-0/0/1.100_ip_config_netmask": "",
        "port_config_ge-0/0/1.100_ip_config_gateway": "",
    }
    assert manager._extract_device_ip_config(row)["port_identifier"] == "ge-0/0/1.100"

    base_only = {"port_config_ge-0/0/1_ip_config": '{"type": "dhcp"}'}
    assert manager._extract_device_ip_config(base_only)["port_identifier"] == "ge-0/0/1"


def test_get_template_ip_type_for_site_uses_base_when_no_subif() -> None:
    """get_template_ip_type_for_site returns base ip_type when no subif in port identifier."""
    manager, _ = _wire()
    manager.site_to_template_id = {"site-a": "tpl-1"}
    manager.template_port_configs = {"tpl-1": {"ip_type": "dhcp"}}

    assert manager._get_template_ip_type_for_site("site-a", "ge-0/0/1") == "dhcp"


def test_get_template_ip_type_for_site_falls_back_when_template_missing() -> None:
    """get_template_ip_type_for_site defaults to 'unknown' when template not found."""
    manager, _ = _wire()
    manager.site_to_template_id = {}
    manager.template_port_configs = {}

    assert manager._get_template_ip_type_for_site("orphan", "ge-0/0/1") == "unknown"


def test_lookup_subif_template_ip_type_reads_column_when_present() -> None:
    """lookup_subif_template_ip_type reads column value when template row matches."""
    manager, _ = _wire()
    manager.template_data = [
        {"id": "tpl-1", "port_config_ge-0/0/1.100_ip_config_type": "STATIC"},
    ]
    assert manager._lookup_subif_template_ip_type("tpl-1", "ge-0/0/1.100", "unknown") == "static"
    assert manager._lookup_subif_template_ip_type("missing", "ge-0/0/1.100", "unknown") == "unknown"


def test_get_template_ip_type_for_site_calls_subif_lookup_when_port_has_dot() -> None:
    """When port identifier contains '.', get_template_ip_type routes to subif lookup."""
    manager, _ = _wire()
    manager.site_to_template_id = {"site-a": "tpl-1"}
    manager.template_port_configs = {"tpl-1": {"ip_type": "dhcp"}}
    manager.template_data = [{"id": "tpl-1", "port_config_ge-0/0/1.100_ip_config_type": "STATIC"}]
    assert manager._get_template_ip_type_for_site("site-a", "ge-0/0/1.100") == "static"


def test_parse_site_indices_valid_and_invalid_inputs() -> None:
    """parse_site_indices returns matching sites and empty list on invalid input."""
    manager, _ = _wire()
    manager.sites = [{"id": "a"}, {"id": "b"}, {"id": "c"}]

    assert [s["id"] for s in manager._parse_site_indices("1,3")] == ["a", "c"]
    assert manager._parse_site_indices("abc") == []  # WHY: ValueError branch.


def test_dispatch_selection_choice_all_paths() -> None:
    """dispatch_selection_choice returns copy of sites for '2', empty for other, calls individual for '1'."""
    manager, _ = _wire()
    manager.sites = [{"id": "a"}]

    all_result = manager._dispatch_selection_choice("2")
    assert all_result == manager.sites
    assert all_result is not manager.sites  # WHY: defensive copy.

    assert manager._dispatch_selection_choice("9") == []  # WHY: cancel branch.


def test_dispatch_selection_choice_individual(monkeypatch: pytest.MonkeyPatch) -> None:
    """dispatch_selection_choice with '1' invokes _select_individual_sites."""
    manager, _ = _wire(safe_input=MagicMock(return_value="1,2"))
    manager.sites = [{"id": "a"}, {"id": "b"}]
    selected = manager._dispatch_selection_choice("1")
    assert [s["id"] for s in selected] == ["a", "b"]


def test_prompt_operator_confirmation_normalises_input() -> None:
    """prompt_operator_confirmation normalises text via strip+lower."""
    _wire(safe_input=MagicMock(return_value="  YES  "))  # WHY: verify normalisation path.
    assert WAN2MigrationManager._prompt_operator_confirmation() == "yes"


def test_log_confirmation_result_confirmed_and_cancelled(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """log_confirmation_result: confirmed branch is quiet, cancel branch prints cancel banner."""
    WAN2MigrationManager._log_confirmation_result(True, 3)
    assert "Operation cancelled" not in capsys.readouterr().out

    WAN2MigrationManager._log_confirmation_result(False, 3)
    assert "Operation cancelled" in capsys.readouterr().out


def test_display_site_variable_header_prints_banner(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """display_site_variable_header prints banner lines to stdout."""
    manager, _ = _wire()
    manager._display_site_variable_header()
    out = capsys.readouterr().out
    assert "Set WAN2 Interface Site Variable" in out
    assert "wan2_interface" in out


def test_print_selection_menu_and_index_menu(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """print_selection_menu and print_site_index_menu output expected labels."""
    manager, _ = _wire()
    manager.sites = [{"id": "s1", "name": "Site One"}]

    manager._print_selection_menu()
    out = capsys.readouterr().out
    assert "1. Select individual sites" in out

    manager._print_site_index_menu()
    out = capsys.readouterr().out
    assert "[1] Site One" in out


def test_initialize_and_add_override_details_end_to_end() -> None:
    """Combined initialize_site_result + add_override_info produces expected values with warning severity."""
    manager, _ = _wire()
    manager.site_overrides_map = {
        "s1": [
            {
                "device_name": "g1",
                "port_identifier": "ge-0/0/1",
                "template_ip_type": "STATIC",
                "device_ip_type": "DHCP",
                "device_static_ip": "",
                "device_netmask": "",
                "override_severity": "WARNING",
                "ip_type_conflict": True,
            }
        ]
    }
    result = manager._initialize_site_result("s1", "S1")
    manager._add_override_info_to_result(result, "s1")
    assert result["warning_override_count"] == 1


def test_apply_site_settings_success_marks_variable_set() -> None:
    """apply_site_settings updates result to SUCCESS on HTTP 200."""
    _wire()  # WHY: ensure module apisession + mistapi wired.
    result: dict[str, Any] = {"variable_set": False, "status": "", "error": ""}
    settings: dict[str, Any] = {"vars": {"wan2_interface": "ge-0/0/1"}}
    WAN2MigrationManager._apply_site_settings("s1", "S1", settings, result)
    assert result["variable_set"] is True
    assert result["status"] == "SUCCESS"


def test_apply_site_settings_failed_marks_error() -> None:
    """apply_site_settings records FAILED status when API returns non-200."""
    _, mocks = _wire(update_status_code=500)
    result: dict[str, Any] = {"variable_set": False, "status": "", "error": ""}
    WAN2MigrationManager._apply_site_settings("s1", "S1", {"vars": {}}, result)
    assert result["status"] == "FAILED"
    assert "500" in result["error"]
    assert mocks["mistapi"].api.v1.sites.setting.updateSiteSettings.called


def test_fetch_current_site_settings_normalises_non_dict() -> None:
    """fetch_current_site_settings returns {} when data attribute is missing or non-dict."""
    _, mocks = _wire()

    mocks["mistapi"].api.v1.sites.setting.getSiteSetting.return_value = SimpleNamespace(
        data="not a dict"
    )  # WHY: non-dict data.
    assert WAN2MigrationManager._fetch_current_site_settings("s1", "S1") == {}

    mocks["mistapi"].api.v1.sites.setting.getSiteSetting.return_value = object()  # WHY: no data attribute.
    assert WAN2MigrationManager._fetch_current_site_settings("s1", "S1") == {}


def test_inject_wan2_variable_creates_vars_when_missing() -> None:
    """inject_wan2_variable populates vars dict when missing or malformed."""
    settings: dict[str, Any] = {}
    WAN2MigrationManager._inject_wan2_variable(settings)
    assert settings["vars"]["wan2_interface"] == "ge-0/0/1"

    settings2: dict[str, Any] = {"vars": "not a dict"}  # WHY: malformed vars.
    WAN2MigrationManager._inject_wan2_variable(settings2)
    assert settings2["vars"]["wan2_interface"] == "ge-0/0/1"


def test_update_site_settings_delegates_to_fetch_inject_apply() -> None:
    """update_site_settings orchestrates fetch, inject, apply and marks success."""
    _wire(site_settings_data={})
    result: dict[str, Any] = {"variable_set": False, "status": "", "error": ""}
    manager = WAN2MigrationManager()
    manager._update_site_settings("s1", "S1", result)
    assert result["variable_set"] is True


def test_set_variable_for_site_captures_exception_as_error() -> None:
    """set_variable_for_site sets ERROR status when API raises."""
    _, mocks = _wire()
    mocks["mistapi"].api.v1.sites.setting.getSiteSetting.side_effect = RuntimeError("boom")

    manager = WAN2MigrationManager()
    result = manager._set_variable_for_site({"id": "s1", "name": "S1"})
    assert result["status"] == "ERROR"
    assert "boom" in result["error"]


def test_set_variable_for_site_success_path() -> None:
    """set_variable_for_site returns SUCCESS with variable set flag on happy path."""
    _wire(site_settings_data={"vars": {}})
    manager = WAN2MigrationManager()
    result = manager._set_variable_for_site({"id": "s1", "name": "S1"})
    assert result["variable_set"] is True
    assert result["status"] == "SUCCESS"


def test_process_sites_for_variable_respects_stop_signal() -> None:
    """process_sites_for_variable exits the loop when stop signal is asserted."""
    manager, mocks = _wire(stop_signal=True)  # WHY: stop signal fires on first call.
    results = manager._process_sites_for_variable([{"id": "s1", "name": "S1"}, {"id": "s2", "name": "S2"}])
    assert results == []  # WHY: no site processed before stop signal check.
    assert mocks["check_stop"].called


def test_process_sites_for_variable_processes_all_sites_when_no_stop() -> None:
    """process_sites_for_variable iterates every site when no stop signal."""
    manager, _ = _wire(stop_signal=False, site_settings_data={})
    results = manager._process_sites_for_variable([{"id": "s1", "name": "S1"}, {"id": "s2", "name": "S2"}])
    assert len(results) == 2
    assert all(r["variable_set"] for r in results)


def test_generate_site_variable_report_writes_and_prints_summary(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """generate_site_variable_report writes CSV report and prints summary block."""
    manager, mocks = _wire()
    manager._generate_site_variable_report(
        [
            {
                "site_id": "s1",
                "site_name": "S1",
                "variable_set": True,
                "has_overrides": True,
                "override_devices": ["gw"],
                "critical_override_count": 1,
                "warning_override_count": 0,
                "info_override_count": 0,
                "total_override_count": 1,
                "status": "SUCCESS",
                "error": "",
                "override_details": "gw@ge-0/0/1(CRITICAL:DHCP->STATIC)",
            }
        ]
    )
    assert mocks["write"].called  # WHY: DataExporter invoked.
    out = capsys.readouterr().out
    assert "Configuration Complete" in out
    assert "CRITICAL ATTENTION" in out


def test_print_severity_warnings_all_branches(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """print_severity_warnings emits critical/warning/info blocks conditionally."""
    WAN2MigrationManager._print_severity_warnings(2, 1, 3)
    out = capsys.readouterr().out
    assert "CRITICAL ATTENTION" in out
    assert "WARNING" in out
    assert "INFO" in out

    WAN2MigrationManager._print_severity_warnings(0, 0, 0)
    assert capsys.readouterr().out == ""  # WHY: no counters -> no output.


def test_compute_severity_counts_merges_success_with_severity_buckets() -> None:
    """compute_severity_counts merges success total with per-bucket counts."""
    manager, _ = _wire()
    counters = manager._compute_severity_counts(
        [
            {"variable_set": True, "has_overrides": True, "critical_override_count": 1},
            {"variable_set": False, "has_overrides": False},
        ]
    )
    assert counters["success"] == 1
    assert counters["critical"] == 1
    assert counters["override"] == 1


def test_load_gateway_configs_hydrates_from_csv(monkeypatch: pytest.MonkeyPatch) -> None:
    """load_gateway_configs reads CSV via open+DictReader and populates gateway_configs."""
    manager, _ = _wire()

    payload = "name,site_id\nGW1,site-a\nGW2,site-b\n"

    def _fake_open(*args: Any, **kwargs: Any) -> io.StringIO:  # WHY: minimal stub for open().
        return io.StringIO(payload)

    monkeypatch.setattr(builtins, "open", _fake_open)
    manager._load_gateway_configs()
    assert [row["name"] for row in manager.gateway_configs] == ["GW1", "GW2"]


def test_load_template_configs_hydrates_from_csv(monkeypatch: pytest.MonkeyPatch) -> None:
    """load_template_configs reads CSV via open+DictReader and populates template_data."""
    manager, _ = _wire()

    payload = "id,name\nt1,Template One\n"

    monkeypatch.setattr(builtins, "open", lambda *args, **kwargs: io.StringIO(payload))
    manager._load_template_configs()
    assert manager.template_data[0]["id"] == "t1"


def test_build_site_to_template_mapping_skips_missing_ids() -> None:
    """build_site_to_template_mapping ignores rows without both ids."""
    manager, _ = _wire()
    manager.sites = [
        {"id": "s1", "gatewaytemplate_id": "t1"},
        {"id": "s2", "gatewaytemplate_id": ""},  # WHY: missing template id.
        {"id": "", "gatewaytemplate_id": "t3"},  # WHY: missing site id.
    ]
    manager._build_site_to_template_mapping()
    assert manager.site_to_template_id == {"s1": "t1"}


def test_extract_template_port_configs_populates_cache() -> None:
    """extract_template_port_configs skips rows without id and populates config cache."""
    manager, _ = _wire()
    manager.template_data = [
        {"id": "t1", "port_config_ge-0/0/1_ip_config": '{"type": "dhcp"}'},
        {"id": "", "port_config_ge-0/0/1_ip_config": '{"type": "static"}'},  # WHY: no id -> skip.
    ]
    manager._extract_template_port_configs()
    assert "t1" in manager.template_port_configs
    assert "" not in manager.template_port_configs


def test_detect_device_overrides_populates_site_map() -> None:
    """detect_device_overrides builds site_overrides_map from gateway_configs."""
    manager, _ = _wire()
    manager.gateway_configs = [
        {
            "site_id": "s1",
            "name": "gw-1",
            "port_config_ge-0/0/1_ip_config": '{"type": "static", "ip": "10.0.0.1"}',
        }
    ]
    manager.site_to_template_id = {"s1": "t1"}
    manager.template_port_configs = {"t1": {"ip_type": "dhcp"}}
    manager.template_data = []

    manager._detect_device_overrides()
    assert "s1" in manager.site_overrides_map
    assert manager.site_overrides_map["s1"][0]["override_severity"] == "CRITICAL"


def test_detect_device_overrides_skips_when_no_meaningful_override() -> None:
    """detect_device_overrides skips rows lacking WAN2 fields entirely."""
    manager, _ = _wire()
    manager.gateway_configs = [{"site_id": "s1", "name": "gw-1"}]  # WHY: no WAN2 columns.
    manager._detect_device_overrides()
    assert manager.site_overrides_map == {}


def test_analyze_device_override_returns_none_when_no_meaningful_override() -> None:
    """analyze_device_override returns None when no meaningful WAN2 fields present."""
    manager, _ = _wire()
    row = {"unrelated": "x"}
    assert manager._analyze_device_override(row, "s1") is None


def test_analyze_device_override_returns_record_when_meaningful() -> None:
    """analyze_device_override produces override record when WAN2 fields have content."""
    manager, _ = _wire()
    manager.site_to_template_id = {"s1": "t1"}
    manager.template_port_configs = {"t1": {"ip_type": "dhcp"}}
    manager.template_data = []
    row = {"port_config_ge-0/0/1_ip_config": '{"type": "static", "ip": "10.0.0.1"}'}
    record = manager._analyze_device_override(row, "s1")
    assert record is not None
    assert record["override_severity"] == "CRITICAL"


def test_load_required_data_returns_true_when_sites_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """load_required_data returns True after successfully loading site cache."""
    manager, _ = _wire()

    payload = "id,name\ns1,Site One\ns2,Site Two\n"
    monkeypatch.setattr(builtins, "open", lambda *args, **kwargs: io.StringIO(payload))
    assert manager._load_required_data() is True
    assert len(manager.sites) == 2


def test_load_required_data_returns_false_when_no_sites(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """load_required_data prints warning and returns False on empty cache."""
    manager, _ = _wire()

    monkeypatch.setattr(builtins, "open", lambda *args, **kwargs: io.StringIO("id,name\n"))
    assert manager._load_required_data() is False
    assert "No sites found" in capsys.readouterr().out


def test_get_site_selection_returns_selected_sites(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """get_site_selection routes user input through selection helpers."""
    manager, _ = _wire(safe_input=MagicMock(side_effect=["2"]))  # WHY: pick 'all sites' option.
    manager.sites = [{"id": "s1", "name": "S1"}]
    result = manager._get_site_selection()
    assert result == manager.sites


def test_resolve_sites_to_configure_returns_empty_when_no_selection() -> None:
    """resolve_sites_to_configure returns empty list when nothing selected."""
    manager, _ = _wire(safe_input=MagicMock(return_value="3"))
    manager.sites = [{"id": "s1", "name": "S1"}]
    assert manager._resolve_sites_to_configure() == []


def test_resolve_sites_to_configure_applies_exclude_prefix() -> None:
    """resolve_sites_to_configure filters excluded sites after selection."""
    manager, _ = _wire(
        site_exclude_prefix="LAB-",
        safe_input=MagicMock(return_value="2"),  # WHY: 'all sites'.
    )
    manager.sites = [
        {"id": "s1", "name": "LAB-One"},
        {"id": "s2", "name": "Prod-Two"},
    ]
    result = manager._resolve_sites_to_configure()
    assert len(result) == 1
    assert result[0]["id"] == "s2"


def test_build_override_detection_map_orchestrates_all_helpers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """build_override_detection_map hydrates gateway/template caches and site override map."""
    manager, _ = _wire()

    gateway_csv = (
        "site_id,name,port_config_ge-0/0/1_ip_config\n" 's1,gw-1,"{""type"": ""static"", ""ip"": ""10.0.0.1""}"\n'
    )
    template_csv = "id,port_config_ge-0/0/1_ip_config\n" 't1,"{""type"": ""dhcp""}"\n'

    payloads = [gateway_csv, template_csv]  # WHY: order matches load_gateway_configs then load_template_configs.

    def _fake_open(*args: Any, **kwargs: Any) -> io.StringIO:
        return io.StringIO(payloads.pop(0))

    monkeypatch.setattr(builtins, "open", _fake_open)
    manager.sites = [{"id": "s1", "gatewaytemplate_id": "t1"}]

    manager._build_override_detection_map()
    assert "s1" in manager.site_overrides_map
    assert manager.site_to_template_id["s1"] == "t1"
    assert "t1" in manager.template_port_configs


def test_build_report_row_produces_all_expected_columns() -> None:
    """build_report_row emits legacy column names and friendly text tokens."""
    row = WAN2MigrationManager._build_report_row(
        {
            "site_name": "S1",
            "site_id": "s1",
            "variable_set": True,
            "status": "SUCCESS",
            "has_overrides": True,
            "total_override_count": 1,
            "critical_override_count": 1,
            "warning_override_count": 0,
            "info_override_count": 0,
            "override_devices": ["gw"],
            "override_details": "gw@ge-0/0/1(CRITICAL:DHCP->STATIC)",
            "error": "",
        }
    )
    assert row["wan2_variable_set"] == "Yes"
    assert row["has_wan2_overrides"] == "Yes"
    assert row["override_devices"] == "gw"
    assert row["requires_manual_review"] == "CRITICAL"


def test_build_report_row_omits_devices_when_empty() -> None:
    """build_report_row returns empty string for override_devices when list empty."""
    row = WAN2MigrationManager._build_report_row(
        {
            "site_name": "S2",
            "site_id": "s2",
            "variable_set": False,
            "status": "FAILED",
            "has_overrides": False,
            "total_override_count": 0,
            "critical_override_count": 0,
            "warning_override_count": 0,
            "info_override_count": 0,
            "override_devices": [],
            "override_details": "",
            "error": "some error",
        }
    )
    assert row["override_devices"] == ""
    assert row["wan2_variable_set"] == "No"
    assert row["error"] == "some error"


def test_prompt_selection_method_returns_stripped_input() -> None:
    """prompt_selection_method returns input stripped of whitespace."""
    manager, _ = _wire(safe_input=MagicMock(return_value="  2  "))
    assert manager._prompt_selection_method() == "2"


def test_select_individual_sites_returns_parsed_choices() -> None:
    """select_individual_sites parses index input and returns site rows."""
    manager, _ = _wire(safe_input=MagicMock(return_value="1"))
    manager.sites = [{"id": "s1"}, {"id": "s2"}]
    result = manager._select_individual_sites()
    assert result == [{"id": "s1"}]


def test_find_subinterface_ip_configs_returns_empty_when_no_type_columns() -> None:
    """find_subinterface_ip_configs returns empty when no subif type columns present."""
    manager, _ = _wire()
    assert manager._find_subinterface_ip_configs({"unrelated": "x"}) == []


def test_find_subinterface_ip_configs_yields_records_when_present() -> None:
    """find_subinterface_ip_configs yields records for each configured subif."""
    manager, _ = _wire()
    row = {
        "port_config_ge-0/0/1.100_ip_config_type": "STATIC",
        "port_config_ge-0/0/1.100_ip_config_ip": "10.1.1.1",
        "port_config_ge-0/0/1.100_ip_config_netmask": "24",
        "port_config_ge-0/0/1.100_ip_config_gateway": "10.1.1.254",
    }
    records = manager._find_subinterface_ip_configs(row)
    assert len(records) == 1
    assert records[0]["port_identifier"] == "ge-0/0/1.100"
