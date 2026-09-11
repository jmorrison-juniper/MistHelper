"""Unit tests for WANProbeConfigManager (Menu #166 WAN probe overrides).

Wave 10 P2 coverage lift (initiative 1018). Tests patch the module-level
``_MH`` proxy singleton via ``monkeypatch.setattr(module, "_MH", ...)`` so
call-time attribute access resolves to a controlled fake, without importing
the real MistHelper module.
"""

from __future__ import annotations  # WHY: PEP 604 unions on Python 3.9+.

import csv  # WHY: build CSV fixtures for _load_data tests.
import logging  # WHY: assert on log-record output.
from types import SimpleNamespace  # WHY: build stand-in namespaces for injected deps.
from typing import Any  # WHY: loose typing for dict fixtures.
from unittest.mock import MagicMock  # WHY: stub callables that record invocation.

import mistapi.api.v1.orgs.gatewaytemplates as gwt_api  # WHY: patch API endpoint directly (mypy strict re-export).
import pytest  # WHY: fixtures, monkeypatch, capsys, caplog.

from src.refactors import wanprobe_config_manager as module  # WHY: SUT module handle.
from src.refactors.wanprobe_config_manager import WANProbeConfigManager  # WHY: class under test.


def _install_fake_mh(
    monkeypatch: pytest.MonkeyPatch,
    *,
    org_id: str | None = "org-1",
    templates_csv_path: str = "OrgGatewayTemplates.csv",
    sites_csv_path: str = "SiteList.csv",
    safe_input_value: str = "1",
    apisession: Any | None = None,
) -> SimpleNamespace:
    """Install a fake ``_MH`` proxy on the module under test and return it for further tweaking."""
    fake_mh = SimpleNamespace(  # WHY: build all attributes accessed via _MH.<name>.
        ConfigUtils=SimpleNamespace(get_cached_or_prompted_org_id=MagicMock(return_value=org_id)),
        CacheUtils=SimpleNamespace(check_and_generate_csv=MagicMock()),
        GatewayExportUtils=SimpleNamespace(templates=MagicMock()),
        OrgSiteExporter=SimpleNamespace(sites=MagicMock()),
        FilePathUtils=SimpleNamespace(
            get_csv_path=MagicMock(side_effect=[templates_csv_path, sites_csv_path]),
        ),
        InputUtils=SimpleNamespace(safe_input=MagicMock(return_value=safe_input_value)),
        DataExporter=SimpleNamespace(write_with_format_selection=MagicMock()),
        apisession=apisession if apisession is not None else object(),  # WHY: mistapi calls receive this.
    )
    monkeypatch.setattr(module, "_MH", fake_mh)  # WHY: swap proxy singleton in place.
    return fake_mh  # WHY: return for per-test tweaks.


# ---------------------------------------------------------------------------
# __init__ and DEFAULT_* class attributes
# ---------------------------------------------------------------------------


def test_init_state_defaults() -> None:
    """Constructor should copy class-level default IPs/profile onto instance."""
    manager = WANProbeConfigManager()  # WHY: fresh instance.
    assert manager.org_id is None  # WHY: unresolved.
    assert manager.templates == []  # WHY: empty list.
    assert manager.sites == []  # WHY: empty list.
    assert manager.template_site_counts == {}  # WHY: empty dict.
    assert manager.probe_ips == WANProbeConfigManager.DEFAULT_PROBE_IPS  # WHY: copy.
    assert manager.probe_ips is not WANProbeConfigManager.DEFAULT_PROBE_IPS  # WHY: not shared alias.
    assert manager.probe_profile == WANProbeConfigManager.DEFAULT_PROBE_PROFILE  # WHY: default.


# ---------------------------------------------------------------------------
# _initialize / _load_data / _build_template_site_counts
# ---------------------------------------------------------------------------


def test_initialize_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """_initialize returns True and stores org_id when ConfigUtils resolves one."""
    _install_fake_mh(monkeypatch, org_id="org-abc")
    manager = WANProbeConfigManager()  # WHY: instance under test.
    assert manager._initialize() is True  # WHY: resolution succeeded.
    assert manager.org_id == "org-abc"  # WHY: stored on instance.


def test_initialize_failure(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """_initialize returns False when the org lookup returns falsy."""
    _install_fake_mh(monkeypatch, org_id=None)
    manager = WANProbeConfigManager()
    assert manager._initialize() is False  # WHY: no org -> abort.
    assert "Failed to get organization ID" in capsys.readouterr().out  # WHY: user notice.


def test_build_template_site_counts_tallies_and_skips_prefix(monkeypatch: pytest.MonkeyPatch) -> None:
    """Site tally skips names starting with MIST_SITE_EXCLUDE_PREFIX and skips blank template ids."""
    # WHY: patch the imported symbol on the module the SUT reads it from.
    monkeypatch.setattr(
        "src.refactors.mist_site_exclude_prefix.MIST_SITE_EXCLUDE_PREFIX",
        "SKIP-",
    )
    manager = WANProbeConfigManager()
    manager.sites = [
        {"name": "Alpha", "gatewaytemplate_id": "tpl-1"},  # WHY: count.
        {"name": "Beta", "gatewaytemplate_id": "tpl-1"},  # WHY: count again.
        {"name": "SKIP-Excluded", "gatewaytemplate_id": "tpl-2"},  # WHY: excluded.
        {"name": "Gamma", "gatewaytemplate_id": ""},  # WHY: blank id skipped.
        {"name": "Delta", "gatewaytemplate_id": "tpl-3"},  # WHY: unique.
    ]
    manager._build_template_site_counts()
    assert manager.template_site_counts == {"tpl-1": 2, "tpl-3": 1}  # WHY: excluded/blank filtered out.


def test_load_data_success(monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> None:
    """_load_data reads both CSVs and populates templates + sites + counts."""
    templates_csv = tmp_path / "OrgGatewayTemplates.csv"
    sites_csv = tmp_path / "SiteList.csv"
    with open(templates_csv, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["id", "name"])
        writer.writeheader()
        writer.writerow({"id": "tpl-1", "name": "T1"})
    with open(sites_csv, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["name", "gatewaytemplate_id"])
        writer.writeheader()
        writer.writerow({"name": "Site1", "gatewaytemplate_id": "tpl-1"})

    _install_fake_mh(
        monkeypatch,
        templates_csv_path=str(templates_csv),
        sites_csv_path=str(sites_csv),
    )
    manager = WANProbeConfigManager()
    assert manager._load_data() is True  # WHY: both CSVs read.
    assert manager.templates == [{"id": "tpl-1", "name": "T1"}]  # WHY: templates loaded.
    assert manager.sites == [{"name": "Site1", "gatewaytemplate_id": "tpl-1"}]  # WHY: sites loaded.
    assert manager.template_site_counts == {"tpl-1": 1}  # WHY: site tally built.


def test_load_data_no_templates(monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> None:
    """_load_data returns False and warns when the templates CSV is empty."""
    templates_csv = tmp_path / "OrgGatewayTemplates.csv"
    templates_csv.write_text("id,name\n", encoding="utf-8")
    sites_csv = tmp_path / "SiteList.csv"
    sites_csv.write_text("name,gatewaytemplate_id\n", encoding="utf-8")

    _install_fake_mh(
        monkeypatch,
        templates_csv_path=str(templates_csv),
        sites_csv_path=str(sites_csv),
    )
    manager = WANProbeConfigManager()
    assert manager._load_data() is False  # WHY: no templates -> abort.


# ---------------------------------------------------------------------------
# _resolve_template_indices / _parse_template_selection
# ---------------------------------------------------------------------------


def test_resolve_template_indices_valid() -> None:
    """Static helper maps 1-based comma-separated indices to matching rows."""
    template_list = [{"id": "a"}, {"id": "b"}, {"id": "c"}]
    result = WANProbeConfigManager._resolve_template_indices("1,3", template_list)
    assert result == [{"id": "a"}, {"id": "c"}]  # WHY: 1-based -> 0-based index.


def test_resolve_template_indices_drops_out_of_range() -> None:
    """Static helper silently drops indices outside the template range."""
    template_list = [{"id": "a"}, {"id": "b"}]
    result = WANProbeConfigManager._resolve_template_indices("1,99", template_list)
    assert result == [{"id": "a"}]  # WHY: out-of-range 99 dropped.


def test_resolve_template_indices_bad_input_raises() -> None:
    """Static helper propagates ValueError on non-numeric input."""
    with pytest.raises(ValueError):
        WANProbeConfigManager._resolve_template_indices("foo", [{"id": "a"}])  # WHY: int() barfs.


def test_parse_template_selection_cancel() -> None:
    """'cancel' selection returns an empty list."""
    manager = WANProbeConfigManager()
    assert manager._parse_template_selection("cancel", [{"id": "a"}]) == []


def test_parse_template_selection_all() -> None:
    """'all' selection returns the full template list as-is."""
    manager = WANProbeConfigManager()
    template_list = [{"id": "a"}, {"id": "b"}]
    assert manager._parse_template_selection("all", template_list) == template_list


def test_parse_template_selection_invalid_input_caught() -> None:
    """Malformed numeric input returns empty list without raising."""
    manager = WANProbeConfigManager()
    assert manager._parse_template_selection("foo", [{"id": "a"}]) == []


def test_parse_template_selection_out_of_range_only() -> None:
    """When all indices are out-of-range the helper returns empty."""
    manager = WANProbeConfigManager()
    assert manager._parse_template_selection("99", [{"id": "a"}]) == []


def test_parse_template_selection_delegates_to_resolver() -> None:
    """Valid numeric selection routes through _resolve_template_indices."""
    manager = WANProbeConfigManager()
    template_list = [{"id": "a"}, {"id": "b"}, {"id": "c"}]
    result = manager._parse_template_selection("2", template_list)
    assert result == [{"id": "b"}]  # WHY: 1-based index 2 -> row index 1.


# ---------------------------------------------------------------------------
# _extract_wan_interfaces / _build_wan_interface
# ---------------------------------------------------------------------------


def test_extract_wan_interfaces_non_dict_returns_empty() -> None:
    """Non-dict port_config returns an empty list."""
    manager = WANProbeConfigManager()
    assert manager._extract_wan_interfaces(None) == []
    assert manager._extract_wan_interfaces("not-a-dict") == []
    assert manager._extract_wan_interfaces(["also", "wrong"]) == []


def test_extract_wan_interfaces_filters_non_wan() -> None:
    """Only ports with usage == 'wan' are collected."""
    manager = WANProbeConfigManager()
    port_config = {
        "ge-0/0/0": {"usage": "wan", "wan_probe_override": {"ips": ["1.1.1.1"], "probe_profile": "lte"}},
        "ge-0/0/1": {"usage": "lan"},
        "ge-0/0/2": {"usage": "wan"},  # WHY: no override present.
        "ge-0/0/3": "not-a-dict",  # WHY: non-dict skipped.
    }
    result = manager._extract_wan_interfaces(port_config)
    port_names = sorted(r["port_name"] for r in result)
    assert port_names == ["ge-0/0/0", "ge-0/0/2"]  # WHY: only WAN entries.


def test_build_wan_interface_with_override() -> None:
    """Existing override values populate current_ips / current_profile."""
    manager = WANProbeConfigManager()
    result = manager._build_wan_interface(
        "ge-0/0/0",
        {"usage": "wan", "wan_probe_override": {"ips": ["1.1.1.1"], "probe_profile": "lte"}},
    )
    assert result == {
        "port_name": "ge-0/0/0",
        "current_ips": ["1.1.1.1"],
        "current_profile": "lte",
    }


def test_build_wan_interface_without_override() -> None:
    """Missing override yields empty ips/profile defaults."""
    manager = WANProbeConfigManager()
    result = manager._build_wan_interface("ge-0/0/1", {"usage": "wan"})
    assert result == {"port_name": "ge-0/0/1", "current_ips": [], "current_profile": ""}


def test_build_wan_interface_non_dict_override() -> None:
    """Non-dict override falls back to empty values via isinstance guard."""
    manager = WANProbeConfigManager()
    result = manager._build_wan_interface("ge-0/0/2", {"usage": "wan", "wan_probe_override": "bad"})
    assert result == {"port_name": "ge-0/0/2", "current_ips": [], "current_profile": ""}


# ---------------------------------------------------------------------------
# _blank_template_result / _build_report_row / _compute_report_totals
# ---------------------------------------------------------------------------


def test_blank_template_result_skeleton() -> None:
    """Skeleton fills identity fields and leaves status/error/updates empty."""
    template = {"id": "tpl-1", "name": "T1", "site_count": 5}
    result = WANProbeConfigManager._blank_template_result(template)
    assert result == {
        "template_name": "T1",
        "template_id": "tpl-1",
        "site_count": 5,
        "interfaces_updated": [],
        "status": "",
        "error": "",
    }


def test_build_report_row_populated() -> None:
    """Report row joins interface names and stamps current probe config."""
    manager = WANProbeConfigManager()
    manager.probe_ips = ["1.1.1.1", "2.2.2.2"]
    manager.probe_profile = "lte"
    row = manager._build_report_row(
        {
            "template_name": "T1",
            "template_id": "tpl-1",
            "site_count": 3,
            "interfaces_updated": ["ge-0/0/0", "ge-0/0/1"],
            "status": "SUCCESS",
            "error": "",
        }
    )
    assert row["interfaces_updated"] == "ge-0/0/0, ge-0/0/1"  # WHY: joined name string.
    assert row["interface_count"] == 2  # WHY: count of updates.
    assert row["new_probe_ips"] == "1.1.1.1, 2.2.2.2"  # WHY: joined ip string.
    assert row["new_probe_profile"] == "lte"  # WHY: current profile stamp.


def test_build_report_row_empty_updates() -> None:
    """Empty interface list renders as empty string, not literal 'None'."""
    manager = WANProbeConfigManager()
    row = manager._build_report_row(
        {
            "template_name": "T",
            "template_id": "i",
            "site_count": 0,
            "interfaces_updated": [],
            "status": "SKIPPED",
            "error": "no wan",
        }
    )
    assert row["interfaces_updated"] == ""  # WHY: empty list -> empty string.
    assert row["interface_count"] == 0  # WHY: no updates.


def test_compute_report_totals_sums_by_status() -> None:
    """Total sites only counts SUCCESS + DRY-RUN rows; interfaces sums all."""
    manager = WANProbeConfigManager()
    results = [
        {"interfaces_updated": ["a"], "site_count": 5, "status": "SUCCESS"},
        {"interfaces_updated": ["b", "c"], "site_count": 10, "status": "FAILED"},
        {"interfaces_updated": [], "site_count": 7, "status": "DRY-RUN"},
    ]
    total_interfaces, total_sites = manager._compute_report_totals(results)
    assert total_interfaces == 3  # WHY: 1 + 2 + 0.
    assert total_sites == 12  # WHY: SUCCESS(5) + DRY-RUN(7); FAILED skipped.


# ---------------------------------------------------------------------------
# _apply_wan_probe_overrides
# ---------------------------------------------------------------------------


def test_apply_wan_probe_overrides_sets_config_on_matching_ports() -> None:
    """Ports in wan_interfaces AND port_config get probe overrides applied."""
    manager = WANProbeConfigManager()
    manager.probe_ips = ["1.1.1.1"]
    manager.probe_profile = "lte"
    port_config: dict[str, dict[str, Any]] = {  # WHY: values are Any-valued dicts (usage str + override dict).
        "ge-0/0/0": {"usage": "wan"},
        "ge-0/0/1": {"usage": "wan"},
    }
    template = {
        "name": "T1",
        "wan_interfaces": [
            {"port_name": "ge-0/0/0", "current_ips": [], "current_profile": ""},
            {"port_name": "ge-0/0/1", "current_ips": [], "current_profile": ""},
        ],
    }
    modified = manager._apply_wan_probe_overrides(template, port_config)
    assert sorted(modified) == ["ge-0/0/0", "ge-0/0/1"]
    assert port_config["ge-0/0/0"]["wan_probe_override"] == {"ips": ["1.1.1.1"], "probe_profile": "lte"}
    assert port_config["ge-0/0/1"]["wan_probe_override"] == {"ips": ["1.1.1.1"], "probe_profile": "lte"}


def test_apply_wan_probe_overrides_skips_missing_ports() -> None:
    """Ports absent from port_config are skipped without KeyError."""
    manager = WANProbeConfigManager()
    port_config = {"ge-0/0/0": {"usage": "wan"}}
    template = {
        "name": "T1",
        "wan_interfaces": [
            {"port_name": "ge-0/0/0"},
            {"port_name": "ge-0/0/missing"},  # WHY: not in port_config.
        ],
    }
    modified = manager._apply_wan_probe_overrides(template, port_config)
    assert modified == ["ge-0/0/0"]


# ---------------------------------------------------------------------------
# _persist_template_update
# ---------------------------------------------------------------------------


def test_persist_template_update_dry_run() -> None:
    """Dry-run path returns ('DRY-RUN', '') and does not call the API."""
    manager = WANProbeConfigManager()
    status, error = manager._persist_template_update(
        {"id": "tpl-1", "name": "T"}, {"config": True}, dry_run=True, interfaces_modified=["ge-0/0/0"]
    )
    assert status == "DRY-RUN"
    assert error == ""


def test_persist_template_update_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Successful API response returns ('SUCCESS', '')."""
    _install_fake_mh(monkeypatch)
    update_resp = SimpleNamespace(status_code=200)  # WHY: emulate mistapi response.
    update_mock = MagicMock(return_value=update_resp)
    monkeypatch.setattr(
        gwt_api,
        "updateOrgGatewayTemplate",
        update_mock,
    )
    manager = WANProbeConfigManager()
    manager.org_id = "org-1"
    status, error = manager._persist_template_update(
        {"id": "tpl-1", "name": "T"}, {"cfg": True}, dry_run=False, interfaces_modified=["ge-0/0/0"]
    )
    assert status == "SUCCESS"
    assert error == ""
    update_mock.assert_called_once()


def test_persist_template_update_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """Non-200 API response returns ('FAILED', 'API returned status ...')."""
    _install_fake_mh(monkeypatch)
    update_resp = SimpleNamespace(status_code=500)
    update_mock = MagicMock(return_value=update_resp)
    monkeypatch.setattr(
        gwt_api,
        "updateOrgGatewayTemplate",
        update_mock,
    )
    manager = WANProbeConfigManager()
    manager.org_id = "org-1"
    status, error = manager._persist_template_update(
        {"id": "tpl-1", "name": "T"}, {"cfg": True}, dry_run=False, interfaces_modified=["ge-0/0/0"]
    )
    assert status == "FAILED"
    assert "500" in error


# ---------------------------------------------------------------------------
# print / preview helpers (capsys)
# ---------------------------------------------------------------------------


def test_print_wan_interface_change_populated(capsys: pytest.CaptureFixture[str]) -> None:
    """Populated port renders current and new lines with actual values."""
    manager = WANProbeConfigManager()
    manager.probe_ips = ["9.9.9.9"]
    manager.probe_profile = "starlink"
    manager._print_wan_interface_change({"port_name": "ge-0/0/0", "current_ips": ["1.1.1.1"], "current_profile": "lte"})
    output = capsys.readouterr().out
    assert "ge-0/0/0" in output
    assert "1.1.1.1" in output
    assert "9.9.9.9" in output
    assert "starlink" in output


def test_print_wan_interface_change_empty(capsys: pytest.CaptureFixture[str]) -> None:
    """Empty current values render '(none)' literals."""
    manager = WANProbeConfigManager()
    manager._print_wan_interface_change({"port_name": "ge-0/0/0", "current_ips": [], "current_profile": ""})
    output = capsys.readouterr().out
    assert "(none)" in output  # WHY: substitution for empty values.


def test_show_preview_prints_totals_and_ports(capsys: pytest.CaptureFixture[str]) -> None:
    """Preview prints template count, interface count, site count, and per-port block."""
    manager = WANProbeConfigManager()
    templates = [
        {
            "name": "T1",
            "site_count": 3,
            "wan_interfaces": [
                {"port_name": "ge-0/0/0", "current_ips": [], "current_profile": ""},
                {"port_name": "ge-0/0/1", "current_ips": ["1.1.1.1"], "current_profile": "lte"},
            ],
        },
        {
            "name": "T2",
            "site_count": 2,
            "wan_interfaces": [
                {"port_name": "ge-0/0/0", "current_ips": [], "current_profile": ""},
            ],
        },
    ]
    manager._show_preview(templates, dry_run=False)
    output = capsys.readouterr().out
    assert "2 templates with 3 WAN interfaces" in output  # WHY: totals line.
    assert "Affecting 5 sites" in output  # WHY: sum site_count.
    assert "T1" in output  # WHY: template subheader.
    assert "T2" in output


def test_display_header_dry_run(capsys: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture) -> None:
    """Dry-run header prints DRY-RUN MODE banner and logs a warning."""
    manager = WANProbeConfigManager()
    with caplog.at_level(logging.WARNING):
        manager._display_header(dry_run=True)
    output = capsys.readouterr().out
    assert "DRY-RUN MODE" in output
    assert "Menu #166 DESTRUCTIVE" in caplog.text  # WHY: warning-level log emitted.


def test_display_header_live_run(capsys: pytest.CaptureFixture[str]) -> None:
    """Live-run header prints destructive warning."""
    manager = WANProbeConfigManager()
    manager._display_header(dry_run=False)
    output = capsys.readouterr().out
    assert "WARNING" in output
    assert "modifies gateway templates" in output


def test_announce_no_wan_interfaces(capsys: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture) -> None:
    """No-interfaces announcement prints message and logs info line."""
    manager = WANProbeConfigManager()
    with caplog.at_level(logging.INFO):
        manager._announce_no_wan_interfaces()
    output = capsys.readouterr().out
    assert "No WAN interfaces" in output
    assert "No WAN interfaces" in caplog.text  # WHY: same message logged.


# ---------------------------------------------------------------------------
# _emit_dry_run_summary / _emit_live_run_summary / _log_destructive_completion
# ---------------------------------------------------------------------------


def test_emit_dry_run_summary_prints_counts(capsys: pytest.CaptureFixture[str]) -> None:
    """Dry-run summary reports templates analyzed and would-update counts."""
    manager = WANProbeConfigManager()
    results = [
        {"status": "DRY-RUN"},
        {"status": "DRY-RUN"},
        {"status": "SKIPPED"},
    ]
    manager._emit_dry_run_summary(results, total_interfaces=5, total_sites=10)
    output = capsys.readouterr().out
    assert "Templates Analyzed: 3" in output
    assert "Would Update: 2" in output
    assert "WAN Interfaces: 5" in output
    assert "Sites Affected: 10" in output


def test_emit_live_run_summary_success_only(capsys: pytest.CaptureFixture[str]) -> None:
    """Live-run summary lists success + failure counts and skips failure line when none."""
    manager = WANProbeConfigManager()
    manager.probe_ips = ["1.1.1.1"]
    manager.probe_profile = "lte"
    results = [{"status": "SUCCESS"}, {"status": "SUCCESS"}]
    manager._emit_live_run_summary(results, total_interfaces=4, total_sites=8)
    output = capsys.readouterr().out
    assert "Templates Updated: 2" in output
    assert "Templates Failed: 0" in output
    assert "Configuration Applied" in output  # WHY: success block present.
    assert "templates failed - check audit report" not in output  # WHY: no failure line.


def test_emit_live_run_summary_with_failures(capsys: pytest.CaptureFixture[str]) -> None:
    """Live-run summary prints failure count and audit-report line when there are failures."""
    manager = WANProbeConfigManager()
    results = [{"status": "SUCCESS"}, {"status": "FAILED"}]
    manager._emit_live_run_summary(results, total_interfaces=3, total_sites=6)
    output = capsys.readouterr().out
    assert "Templates Updated: 1" in output
    assert "Templates Failed: 1" in output
    assert "1 templates failed - check audit report" in output


def test_log_destructive_completion(caplog: pytest.LogCaptureFixture) -> None:
    """Completion logger emits a warning-level record counting successes."""
    manager = WANProbeConfigManager()
    results = [{"status": "SUCCESS"}, {"status": "SUCCESS"}, {"status": "FAILED"}]
    with caplog.at_level(logging.WARNING):
        manager._log_destructive_completion(results)
    assert "2 templates updated" in caplog.text  # WHY: success count only.


# ---------------------------------------------------------------------------
# _confirm_operation
# ---------------------------------------------------------------------------


def test_confirm_operation_apply(monkeypatch: pytest.MonkeyPatch) -> None:
    """Typing 'APPLY' returns True."""
    _install_fake_mh(monkeypatch, safe_input_value="APPLY")
    manager = WANProbeConfigManager()
    assert manager._confirm_operation(3) is True


def test_confirm_operation_cancelled(monkeypatch: pytest.MonkeyPatch) -> None:
    """Any other input cancels the operation."""
    _install_fake_mh(monkeypatch, safe_input_value="no")
    manager = WANProbeConfigManager()
    assert manager._confirm_operation(3) is False


# ---------------------------------------------------------------------------
# _render_template_list / _select_templates
# ---------------------------------------------------------------------------


def test_render_template_list_returns_rows_and_prints(capsys: pytest.CaptureFixture[str]) -> None:
    """Template list renders rows with site counts populated from template_site_counts."""
    manager = WANProbeConfigManager()
    manager.template_site_counts = {"tpl-1": 4, "tpl-2": 0}
    rows = manager._render_template_list(
        [
            {"id": "tpl-1", "name": "T1"},
            {"id": "tpl-2", "name": "T2"},
        ]
    )
    assert rows == [
        {"id": "tpl-1", "name": "T1", "site_count": 4},
        {"id": "tpl-2", "name": "T2", "site_count": 0},
    ]
    output = capsys.readouterr().out
    assert "T1" in output
    assert "T2" in output


def test_select_templates_all(monkeypatch: pytest.MonkeyPatch) -> None:
    """When user types 'all', _select_templates returns every rendered row."""
    _install_fake_mh(monkeypatch, safe_input_value="all")
    manager = WANProbeConfigManager()
    manager.templates = [
        {"id": "tpl-1", "name": "T1"},
        {"id": "tpl-2", "name": "T2"},
    ]
    manager.template_site_counts = {"tpl-1": 1, "tpl-2": 2}
    result = manager._select_templates()
    assert len(result) == 2  # WHY: both templates.
    assert {row["id"] for row in result} == {"tpl-1", "tpl-2"}


def test_select_templates_numeric(monkeypatch: pytest.MonkeyPatch) -> None:
    """Numeric selection returns just the matching rendered rows."""
    _install_fake_mh(monkeypatch, safe_input_value="2")
    manager = WANProbeConfigManager()
    manager.templates = [
        {"id": "tpl-1", "name": "T1"},
        {"id": "tpl-2", "name": "T2"},
    ]
    manager.template_site_counts = {"tpl-1": 0, "tpl-2": 0}
    result = manager._select_templates()
    assert len(result) == 1
    assert result[0]["id"] == "tpl-2"


# ---------------------------------------------------------------------------
# _fetch_template_config / _analyze_template
# ---------------------------------------------------------------------------


def test_fetch_template_config_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Successful fetch returns the config dict from response.data."""
    _install_fake_mh(monkeypatch)
    fetch_mock = MagicMock(return_value=SimpleNamespace(data={"port_config": {"ge-0/0/0": {"usage": "wan"}}}))
    monkeypatch.setattr(
        gwt_api,
        "getOrgGatewayTemplate",
        fetch_mock,
    )
    manager = WANProbeConfigManager()
    manager.org_id = "org-1"
    config = manager._fetch_template_config({"id": "tpl-1", "name": "T1"})
    assert config == {"port_config": {"ge-0/0/0": {"usage": "wan"}}}


def test_fetch_template_config_invalid_structure(monkeypatch: pytest.MonkeyPatch) -> None:
    """Non-dict data returns None."""
    _install_fake_mh(monkeypatch)
    fetch_mock = MagicMock(return_value=SimpleNamespace(data="bad"))
    monkeypatch.setattr(
        gwt_api,
        "getOrgGatewayTemplate",
        fetch_mock,
    )
    manager = WANProbeConfigManager()
    manager.org_id = "org-1"
    assert manager._fetch_template_config({"id": "tpl-1", "name": "T1"}) is None


def test_fetch_template_config_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    """Exception during fetch is caught; helper returns None."""
    _install_fake_mh(monkeypatch)
    fetch_mock = MagicMock(side_effect=RuntimeError("boom"))
    monkeypatch.setattr(
        gwt_api,
        "getOrgGatewayTemplate",
        fetch_mock,
    )
    manager = WANProbeConfigManager()
    manager.org_id = "org-1"
    assert manager._fetch_template_config({"id": "tpl-1", "name": "T1"}) is None


def test_analyze_template_no_wan(monkeypatch: pytest.MonkeyPatch) -> None:
    """_analyze_template returns None when a template has no WAN interfaces."""
    _install_fake_mh(monkeypatch)
    monkeypatch.setattr(
        WANProbeConfigManager,
        "_fetch_template_config",
        lambda self, tinfo: {"port_config": {"ge-0/0/0": {"usage": "lan"}}},
    )
    manager = WANProbeConfigManager()
    assert manager._analyze_template({"id": "tpl-1", "name": "T1", "site_count": 1}) is None


def test_analyze_template_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """_analyze_template returns a change record when WAN interfaces are present."""
    _install_fake_mh(monkeypatch)
    monkeypatch.setattr(
        WANProbeConfigManager,
        "_fetch_template_config",
        lambda self, tinfo: {"port_config": {"ge-0/0/0": {"usage": "wan"}}},
    )
    manager = WANProbeConfigManager()
    result = manager._analyze_template({"id": "tpl-1", "name": "T1", "site_count": 3})
    assert result is not None
    assert result["id"] == "tpl-1"
    assert len(result["wan_interfaces"]) == 1
    assert result["wan_interfaces"][0]["port_name"] == "ge-0/0/0"


def test_analyze_template_fetch_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """When _fetch_template_config returns None, _analyze_template returns None."""
    _install_fake_mh(monkeypatch)
    monkeypatch.setattr(
        WANProbeConfigManager,
        "_fetch_template_config",
        lambda self, tinfo: None,
    )
    manager = WANProbeConfigManager()
    assert manager._analyze_template({"id": "tpl-1", "name": "T1", "site_count": 1}) is None


# ---------------------------------------------------------------------------
# _update_single_template
# ---------------------------------------------------------------------------


def test_update_single_template_dry_run(monkeypatch: pytest.MonkeyPatch) -> None:
    """Dry-run path records DRY-RUN status and updated interfaces."""
    _install_fake_mh(monkeypatch)
    manager = WANProbeConfigManager()
    template = {
        "id": "tpl-1",
        "name": "T1",
        "site_count": 3,
        "config": {"port_config": {"ge-0/0/0": {"usage": "wan"}}},
        "wan_interfaces": [{"port_name": "ge-0/0/0"}],
    }
    result = manager._update_single_template(template, dry_run=True)
    assert result["status"] == "DRY-RUN"
    assert result["interfaces_updated"] == ["ge-0/0/0"]


def test_update_single_template_no_interfaces(monkeypatch: pytest.MonkeyPatch) -> None:
    """When no interfaces match port_config the result is SKIPPED."""
    _install_fake_mh(monkeypatch)
    manager = WANProbeConfigManager()
    template = {
        "id": "tpl-1",
        "name": "T1",
        "site_count": 2,
        "config": {"port_config": {}},
        "wan_interfaces": [{"port_name": "ge-0/0/missing"}],
    }
    result = manager._update_single_template(template, dry_run=True)
    assert result["status"] == "SKIPPED"
    assert result["interfaces_updated"] == []


def test_update_single_template_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    """Exception during update is caught and reported as ERROR status."""
    _install_fake_mh(monkeypatch)
    manager = WANProbeConfigManager()
    template = {
        "id": "tpl-1",
        "name": "T1",
        "site_count": 1,
        "config": None,  # WHY: .get('port_config') will fail on None.
        "wan_interfaces": [{"port_name": "ge-0/0/0"}],
    }
    result = manager._update_single_template(template, dry_run=True)
    assert result["status"] == "ERROR"
    assert result["error"]  # WHY: some error string recorded.


# ---------------------------------------------------------------------------
# _apply_changes / _generate_report
# ---------------------------------------------------------------------------


def test_apply_changes_delegates_per_template(monkeypatch: pytest.MonkeyPatch) -> None:
    """_apply_changes iterates through templates and returns all update results."""
    _install_fake_mh(monkeypatch)
    manager = WANProbeConfigManager()
    call_count = {"n": 0}

    def _fake_update(
        self: WANProbeConfigManager, template: dict[str, Any], dry_run: bool
    ) -> dict[str, Any]:  # WHY: replace real update.
        call_count["n"] += 1
        return {"status": "DRY-RUN", "template_name": template["name"]}

    monkeypatch.setattr(WANProbeConfigManager, "_update_single_template", _fake_update)
    templates = [
        {"name": "T1", "id": "1", "site_count": 0, "config": {}, "wan_interfaces": []},
        {"name": "T2", "id": "2", "site_count": 0, "config": {}, "wan_interfaces": []},
    ]
    results = manager._apply_changes(templates, dry_run=True)
    assert call_count["n"] == 2  # WHY: dispatched twice.
    assert [r["template_name"] for r in results] == ["T1", "T2"]  # WHY: preserves order.


def test_generate_report_dry_run(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """Dry-run report writes CSV via DataExporter and prints the dry-run summary."""
    fake_mh = _install_fake_mh(monkeypatch)
    manager = WANProbeConfigManager()
    results = [
        {
            "template_name": "T1",
            "template_id": "tpl-1",
            "site_count": 3,
            "interfaces_updated": ["ge-0/0/0"],
            "status": "DRY-RUN",
            "error": "",
        }
    ]
    manager._generate_report(results, dry_run=True)
    fake_mh.DataExporter.write_with_format_selection.assert_called_once()  # WHY: CSV written.
    output = capsys.readouterr().out
    assert "DRY-RUN Complete" in output
    assert "Would Update: 1" in output


def test_generate_report_live_run(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """Live-run report writes CSV and prints the live summary."""
    fake_mh = _install_fake_mh(monkeypatch)
    manager = WANProbeConfigManager()
    results = [
        {
            "template_name": "T1",
            "template_id": "tpl-1",
            "site_count": 3,
            "interfaces_updated": ["ge-0/0/0"],
            "status": "SUCCESS",
            "error": "",
        }
    ]
    manager._generate_report(results, dry_run=False)
    fake_mh.DataExporter.write_with_format_selection.assert_called_once()
    output = capsys.readouterr().out
    assert "WAN Probe Configuration Complete" in output
    assert "Templates Updated: 1" in output


# ---------------------------------------------------------------------------
# _prepare_templates_with_changes / _execute / configure classmethod
# ---------------------------------------------------------------------------


def test_prepare_templates_with_changes_init_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prep helper returns None when _initialize fails."""
    _install_fake_mh(monkeypatch)
    monkeypatch.setattr(WANProbeConfigManager, "_initialize", lambda self: False)
    manager = WANProbeConfigManager()
    assert manager._prepare_templates_with_changes() is None


def test_prepare_templates_with_changes_load_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prep helper returns None when _load_data fails after successful init."""
    _install_fake_mh(monkeypatch)
    monkeypatch.setattr(WANProbeConfigManager, "_initialize", lambda self: True)
    monkeypatch.setattr(WANProbeConfigManager, "_load_data", lambda self: False)
    manager = WANProbeConfigManager()
    assert manager._prepare_templates_with_changes() is None


def test_prepare_templates_with_changes_no_selection(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prep helper returns None when the operator picks no templates."""
    _install_fake_mh(monkeypatch)
    monkeypatch.setattr(WANProbeConfigManager, "_initialize", lambda self: True)
    monkeypatch.setattr(WANProbeConfigManager, "_load_data", lambda self: True)
    monkeypatch.setattr(WANProbeConfigManager, "_select_templates", lambda self: [])
    manager = WANProbeConfigManager()
    assert manager._prepare_templates_with_changes() is None


def test_prepare_templates_with_changes_no_wan(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Prep helper returns None and announces when analysis yields no changes."""
    _install_fake_mh(monkeypatch)
    monkeypatch.setattr(WANProbeConfigManager, "_initialize", lambda self: True)
    monkeypatch.setattr(WANProbeConfigManager, "_load_data", lambda self: True)
    monkeypatch.setattr(WANProbeConfigManager, "_select_templates", lambda self: [{"id": "tpl-1"}])
    monkeypatch.setattr(WANProbeConfigManager, "_analyze_templates", lambda self, x: [])
    manager = WANProbeConfigManager()
    assert manager._prepare_templates_with_changes() is None
    assert "No WAN interfaces" in capsys.readouterr().out


def test_prepare_templates_with_changes_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prep helper returns the analyzed list when every step succeeds."""
    _install_fake_mh(monkeypatch)
    monkeypatch.setattr(WANProbeConfigManager, "_initialize", lambda self: True)
    monkeypatch.setattr(WANProbeConfigManager, "_load_data", lambda self: True)
    monkeypatch.setattr(WANProbeConfigManager, "_select_templates", lambda self: [{"id": "tpl-1"}])
    expected = [{"id": "tpl-1", "wan_interfaces": [{"port_name": "ge-0/0/0"}]}]
    monkeypatch.setattr(WANProbeConfigManager, "_analyze_templates", lambda self, x: expected)
    manager = WANProbeConfigManager()
    assert manager._prepare_templates_with_changes() == expected


def test_execute_short_circuits_on_prep_none(monkeypatch: pytest.MonkeyPatch) -> None:
    """_execute returns early when _prepare_templates_with_changes yields None."""
    _install_fake_mh(monkeypatch)
    monkeypatch.setattr(WANProbeConfigManager, "_display_header", lambda self, dr: None)
    monkeypatch.setattr(WANProbeConfigManager, "_prepare_templates_with_changes", lambda self: None)
    apply_mock = MagicMock()
    monkeypatch.setattr(WANProbeConfigManager, "_apply_changes", apply_mock)
    manager = WANProbeConfigManager()
    manager._execute(dry_run=False)
    apply_mock.assert_not_called()  # WHY: prep aborted; apply must be skipped.


def test_execute_full_dry_run(monkeypatch: pytest.MonkeyPatch) -> None:
    """_execute in dry-run mode calls preview, apply, and report (skips confirmation)."""
    _install_fake_mh(monkeypatch)
    monkeypatch.setattr(WANProbeConfigManager, "_display_header", lambda self, dr: None)
    monkeypatch.setattr(
        WANProbeConfigManager,
        "_prepare_templates_with_changes",
        lambda self: [{"id": "tpl-1", "name": "T", "site_count": 1, "wan_interfaces": []}],
    )
    preview_mock = MagicMock()
    apply_mock = MagicMock(return_value=[{"status": "DRY-RUN"}])
    report_mock = MagicMock()
    monkeypatch.setattr(WANProbeConfigManager, "_show_preview", preview_mock)
    monkeypatch.setattr(WANProbeConfigManager, "_apply_changes", apply_mock)
    monkeypatch.setattr(WANProbeConfigManager, "_generate_report", report_mock)
    manager = WANProbeConfigManager()
    manager._execute(dry_run=True)
    preview_mock.assert_called_once()
    apply_mock.assert_called_once()
    report_mock.assert_called_once()


def test_execute_live_run_cancelled(monkeypatch: pytest.MonkeyPatch) -> None:
    """Live-run _execute returns early when confirmation fails."""
    _install_fake_mh(monkeypatch)
    monkeypatch.setattr(WANProbeConfigManager, "_display_header", lambda self, dr: None)
    monkeypatch.setattr(
        WANProbeConfigManager,
        "_prepare_templates_with_changes",
        lambda self: [{"id": "tpl-1", "name": "T", "site_count": 1, "wan_interfaces": []}],
    )
    monkeypatch.setattr(WANProbeConfigManager, "_show_preview", lambda self, t, dr: None)
    monkeypatch.setattr(WANProbeConfigManager, "_confirm_operation", lambda self, n: False)
    apply_mock = MagicMock()
    monkeypatch.setattr(WANProbeConfigManager, "_apply_changes", apply_mock)
    manager = WANProbeConfigManager()
    manager._execute(dry_run=False)
    apply_mock.assert_not_called()  # WHY: cancelled; no writes.


def test_configure_classmethod_dispatches(monkeypatch: pytest.MonkeyPatch) -> None:
    """configure() builds an instance and dispatches to _execute with the dry_run flag."""
    execute_mock = MagicMock()
    monkeypatch.setattr(WANProbeConfigManager, "_execute", execute_mock)
    WANProbeConfigManager.configure(dry_run=True)
    execute_mock.assert_called_once_with(True)
