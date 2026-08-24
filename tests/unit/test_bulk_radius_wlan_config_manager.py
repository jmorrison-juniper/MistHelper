"""Comprehensive unit tests for BulkRadiusWLANConfigManager (Menu 122).

Complements test_bulk_radius_wlan_snapshot.py by covering the remaining
lifecycle: env loading, org resolution, WLAN scan, filtering, classification,
selection parsing, preview, apply, audit CSV export, and the manage()
orchestration end-to-end.

Why:
    The `bulk_radius_wlan_config_manager` module was previously excluded from
    coverage. Un-omitting it under initiative #878 requires 100% line + branch
    coverage without hitting the network. This file exercises every branch of
    the manager, patching `mistapi`, `MistHelper.apisession`,
    `MistHelper.IsDebugMode`, `MistHelper.ConfigUtils`, `MistHelper.InputUtils`,
    and `MistHelper.DataExporter` so all paths are deterministic.
"""

from __future__ import annotations

import os
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

import MistHelper  # Preloaded by conftest.py — provides live class references.
from src.site import bulk_radius_wlan_config_manager as brwcm


def _make_manager() -> brwcm.BulkRadiusWLANConfigManager:
    """Build a manager with deterministic target settings (timeout=3, retries=2, fast=True)."""
    manager = brwcm.BulkRadiusWLANConfigManager()
    manager.org_id = "org-123"
    manager.target_timeout = 3
    manager.target_retries = 2
    manager.target_fast_dot1x = True
    return manager


def _make_mh(debug: bool = False) -> SimpleNamespace:
    """Return a fake MistHelper module namespace for patching importlib.import_module."""
    return SimpleNamespace(
        apisession=MagicMock(),
        IsDebugMode=SimpleNamespace(check=MagicMock(return_value=debug)),
        ConfigUtils=SimpleNamespace(get_cached_or_prompted_org_id=MagicMock(return_value="org-123")),
        InputUtils=SimpleNamespace(safe_input=MagicMock(return_value="")),
        DataExporter=SimpleNamespace(write_with_format_selection=MagicMock(return_value=True)),
    )


# ---------------------------------------------------------------------------
# _load_env_config
# ---------------------------------------------------------------------------


def test_load_env_config_uses_env_values(monkeypatch: pytest.MonkeyPatch) -> None:
    """Env variables override defaults for timeout, retries, and fast_dot1x flag."""
    monkeypatch.setenv("RADIUS_AUTH_TIMEOUT", "7")
    monkeypatch.setenv("RADIUS_AUTH_RETRIES", "5")
    monkeypatch.setenv("RADIUS_FAST_DOT1X", "false")
    manager = brwcm.BulkRadiusWLANConfigManager()
    assert manager.target_timeout == 7
    assert manager.target_retries == 5
    assert manager.target_fast_dot1x is False


def test_load_env_config_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """Missing env variables yield the documented defaults (3/2/True)."""
    monkeypatch.delenv("RADIUS_AUTH_TIMEOUT", raising=False)
    monkeypatch.delenv("RADIUS_AUTH_RETRIES", raising=False)
    monkeypatch.delenv("RADIUS_FAST_DOT1X", raising=False)
    manager = brwcm.BulkRadiusWLANConfigManager()
    assert manager.target_timeout == 3
    assert manager.target_retries == 2
    assert manager.target_fast_dot1x is True


# ---------------------------------------------------------------------------
# _display_config
# ---------------------------------------------------------------------------


def test_display_config_prints_dry_run_and_debug_banners(capsys: pytest.CaptureFixture[str]) -> None:
    """Both dry-run and debug banners appear when both are active."""
    manager = _make_manager()
    manager.dry_run = True
    fake = _make_mh(debug=True)
    with patch.object(brwcm.importlib, "import_module", return_value=fake):
        manager._display_config()
    out = capsys.readouterr().out
    assert "DRY-RUN MODE" in out
    assert "DEBUG MODE" in out
    assert "auth_servers_timeout: 3" in out


def test_display_config_no_banners_when_disabled(capsys: pytest.CaptureFixture[str]) -> None:
    """Neither banner appears when dry-run and debug are off."""
    manager = _make_manager()
    manager.dry_run = False
    fake = _make_mh(debug=False)
    with patch.object(brwcm.importlib, "import_module", return_value=fake):
        manager._display_config()
    out = capsys.readouterr().out
    assert "DRY-RUN MODE" not in out
    assert "DEBUG MODE" not in out


# ---------------------------------------------------------------------------
# _get_org_id
# ---------------------------------------------------------------------------


def test_get_org_id_success() -> None:
    """Cached org id is stored and True is returned."""
    manager = _make_manager()
    manager.org_id = ""
    fake = _make_mh()
    fake.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-abc"
    with patch.object(brwcm.importlib, "import_module", return_value=fake):
        assert manager._get_org_id() is True
    assert manager.org_id == "org-abc"


def test_get_org_id_failure(capsys: pytest.CaptureFixture[str]) -> None:
    """Empty org id yields False plus an operator-facing error message."""
    manager = _make_manager()
    fake = _make_mh()
    fake.ConfigUtils.get_cached_or_prompted_org_id.return_value = ""
    with patch.object(brwcm.importlib, "import_module", return_value=fake):
        assert manager._get_org_id() is False
    assert "Unable to determine organization ID" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# _scan_org_wlans
# ---------------------------------------------------------------------------


def test_scan_org_wlans_success(capsys: pytest.CaptureFixture[str]) -> None:
    """Successful HTTP 200 loads WLAN list and returns True."""
    manager = _make_manager()
    fake = _make_mh(debug=True)  # Also exercise the debug-dump path
    response = SimpleNamespace(status_code=200, data=[{"id": "w1"}, {"id": "w2"}])
    with (
        patch.object(brwcm.importlib, "import_module", return_value=fake),
        patch.object(brwcm.mistapi.api.v1.orgs.wlans, "listOrgWlans", return_value=response),
    ):
        assert manager._scan_org_wlans() is True
    assert len(manager.all_wlans) == 2
    assert "Found 2 total WLANs" in capsys.readouterr().out


def test_scan_org_wlans_http_error(capsys: pytest.CaptureFixture[str]) -> None:
    """Non-200 HTTP status returns False and prints an error."""
    manager = _make_manager()
    fake = _make_mh()
    response = SimpleNamespace(status_code=403, data=None)
    with (
        patch.object(brwcm.importlib, "import_module", return_value=fake),
        patch.object(brwcm.mistapi.api.v1.orgs.wlans, "listOrgWlans", return_value=response),
    ):
        assert manager._scan_org_wlans() is False
    assert "HTTP 403" in capsys.readouterr().out


def test_scan_org_wlans_exception(capsys: pytest.CaptureFixture[str]) -> None:
    """API exception returns False and surfaces the error to the user."""
    manager = _make_manager()
    fake = _make_mh()
    with (
        patch.object(brwcm.importlib, "import_module", return_value=fake),
        patch.object(brwcm.mistapi.api.v1.orgs.wlans, "listOrgWlans", side_effect=RuntimeError("boom")),
    ):
        assert manager._scan_org_wlans() is False
    assert "Error fetching WLANs: boom" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# _uses_radius_auth
# ---------------------------------------------------------------------------


def test_uses_radius_auth_via_auth_servers() -> None:
    """Presence of auth_servers alone flags the WLAN as RADIUS."""
    manager = _make_manager()
    assert manager._uses_radius_auth({"auth_servers": [{"host": "a"}]}) is True


def test_uses_radius_auth_via_radsec() -> None:
    """Enabled radsec dict flags the WLAN as RADIUS."""
    manager = _make_manager()
    assert manager._uses_radius_auth({"radsec": {"enabled": True}}) is True


def test_uses_radius_auth_via_eap() -> None:
    """auth.type == 'eap' flags the WLAN as RADIUS."""
    manager = _make_manager()
    assert manager._uses_radius_auth({"auth": {"type": "eap"}}) is True


def test_uses_radius_auth_via_eap192() -> None:
    """auth.type == 'eap192' flags the WLAN as RADIUS."""
    manager = _make_manager()
    assert manager._uses_radius_auth({"auth": {"type": "eap192"}}) is True


def test_uses_radius_auth_none_of_the_above() -> None:
    """A WLAN with no RADIUS signals returns False."""
    manager = _make_manager()
    assert manager._uses_radius_auth({"auth": {"type": "psk"}}) is False


def test_uses_radius_auth_tolerates_non_dict_subconfigs() -> None:
    """Non-dict auth/radsec sub-configs degrade to False without raising."""
    manager = _make_manager()
    wlan: dict[str, Any] = {"auth": "bogus", "radsec": "nope"}
    assert manager._uses_radius_auth(wlan) is False


# ---------------------------------------------------------------------------
# _already_configured
# ---------------------------------------------------------------------------


def test_already_configured_true() -> None:
    """All three timer fields at target values -> compliant."""
    manager = _make_manager()
    wlan = {"auth_servers_timeout": 3, "auth_servers_retries": 2, "fast_dot1x_timers": True}
    assert manager._already_configured(wlan) is True


def test_already_configured_false() -> None:
    """Any mismatched timer field -> non-compliant."""
    manager = _make_manager()
    wlan = {"auth_servers_timeout": 5, "auth_servers_retries": 2, "fast_dot1x_timers": True}
    assert manager._already_configured(wlan) is False


# ---------------------------------------------------------------------------
# _log_radius_wlan_classification
# ---------------------------------------------------------------------------


def test_log_classification_no_op_when_debug_off() -> None:
    """Debug-off path returns without logging (branch coverage)."""
    manager = _make_manager()
    fake = _make_mh(debug=False)
    with patch.object(brwcm.importlib, "import_module", return_value=fake):
        manager._log_radius_wlan_classification("COMPLIANT", {"ssid": "X"})


def test_log_classification_emits_when_debug_on() -> None:
    """Debug-on path calls the logger (function reaches the debug call)."""
    manager = _make_manager()
    fake = _make_mh(debug=True)
    with (
        patch.object(brwcm.importlib, "import_module", return_value=fake),
        patch.object(brwcm.logging, "debug") as mock_debug,
    ):
        manager._log_radius_wlan_classification("NEEDS_UPDATE", {"ssid": "Y"})
    mock_debug.assert_called_once()


# ---------------------------------------------------------------------------
# _classify_radius_wlan + _filter_radius_wlans
# ---------------------------------------------------------------------------


def test_classify_and_filter_split_buckets() -> None:
    """Mixed WLAN list splits into compliant + needs-update buckets by settings."""
    manager = _make_manager()
    compliant = {
        "id": "c1",
        "ssid": "OK",
        "auth_servers": [{"host": "a"}],
        "auth_servers_timeout": 3,
        "auth_servers_retries": 2,
        "fast_dot1x_timers": True,
    }
    needs_update = {
        "id": "n1",
        "ssid": "UPD",
        "auth_servers": [{"host": "b"}],
        "auth_servers_timeout": 5,
    }
    non_radius = {"id": "x1", "ssid": "PSK", "auth": {"type": "psk"}}
    manager.all_wlans = [compliant, needs_update, non_radius]
    fake = _make_mh(debug=False)
    with patch.object(brwcm.importlib, "import_module", return_value=fake):
        manager._filter_radius_wlans()
    assert [w["id"] for w in manager.compliant_wlans] == ["c1"]
    assert [w["id"] for w in manager.radius_wlans] == ["n1"]
    assert manager.compliant_wlans[0]["_compliance_status"] == "COMPLIANT"
    assert manager.radius_wlans[0]["_compliance_status"] == "NEEDS_UPDATE"


# ---------------------------------------------------------------------------
# _add_inheritance_metadata
# ---------------------------------------------------------------------------


def test_add_inheritance_metadata_template() -> None:
    """Template-scoped WLAN gets 'template' level and truncated template id source."""
    manager = _make_manager()
    wlan = {"template_id": "abcdef01234567890"}
    manager._add_inheritance_metadata(wlan)
    assert wlan["_inheritance_level"] == "template"
    assert wlan["_inheritance_source"].startswith("Template ID: abcdef01")


def test_add_inheritance_metadata_org() -> None:
    """Org-scoped WLAN (no template_id) gets 'org' level."""
    manager = _make_manager()
    wlan: dict[str, Any] = {}
    manager._add_inheritance_metadata(wlan)
    assert wlan["_inheritance_level"] == "org"
    assert wlan["_inheritance_source"] == "Org-Level WLAN"


# ---------------------------------------------------------------------------
# _build_combined_wlan_rows / _print_wlan_row / _display_wlans
# ---------------------------------------------------------------------------


def test_build_combined_rows_and_print(capsys: pytest.CaptureFixture[str]) -> None:
    """Selectable WLANs get numeric indices; compliant WLANs get '--'; rows sorted by SSID."""
    manager = _make_manager()
    manager.radius_wlans = [
        {"ssid": "Bravo", "_inheritance_level": "template", "_compliance_status": "NEEDS_UPDATE"},
        {"ssid": "Alpha", "_inheritance_level": "org", "_compliance_status": "NEEDS_UPDATE"},
    ]
    manager.compliant_wlans = [
        {"ssid": "Zulu", "_inheritance_level": "template", "_compliance_status": "COMPLIANT"},
    ]
    manager._display_wlans()
    out = capsys.readouterr().out
    assert "Alpha" in out
    assert "Bravo" in out
    assert "Zulu" in out
    assert "COMPLIANT" in out
    assert "Total: 3 RADIUS WLANs" in out


def test_print_wlan_row_defaults_when_missing_keys(capsys: pytest.CaptureFixture[str]) -> None:
    """Missing SSID/level fields fall back to safe defaults in the row output."""
    manager = _make_manager()
    manager._print_wlan_row({}, None)
    out = capsys.readouterr().out
    assert "Unknown" in out
    assert "unknown" in out  # missing _inheritance_level
    assert "--" in out  # non-selectable row


# ---------------------------------------------------------------------------
# Selection parsing helpers
# ---------------------------------------------------------------------------


def test_is_range_part_true_and_false() -> None:
    """Range detection tolerates leading minus (single index) vs '3-7' (range)."""
    assert brwcm.BulkRadiusWLANConfigManager._is_range_part("3-7") is True
    assert brwcm.BulkRadiusWLANConfigManager._is_range_part("-3") is False
    assert brwcm.BulkRadiusWLANConfigManager._is_range_part("5") is False


def test_parse_range_part_valid_and_reversed() -> None:
    """Ranges parse to (0-based start, end) and reverse-order inputs are swapped."""
    assert brwcm.BulkRadiusWLANConfigManager._parse_range_part("3-7") == (2, 6)
    assert brwcm.BulkRadiusWLANConfigManager._parse_range_part("7-3") == (2, 6)


def test_parse_range_part_invalid_shape() -> None:
    """A range with more than two ends returns None."""
    assert brwcm.BulkRadiusWLANConfigManager._parse_range_part("1-2-3") is None


def test_parse_range_part_non_numeric() -> None:
    """A non-numeric range returns None (ValueError branch)."""
    assert brwcm.BulkRadiusWLANConfigManager._parse_range_part("a-b") is None


def test_parse_single_index_valid_and_invalid() -> None:
    """Valid strings return 0-based indices; non-numeric strings return None."""
    assert brwcm.BulkRadiusWLANConfigManager._parse_single_index("4") == 3
    assert brwcm.BulkRadiusWLANConfigManager._parse_single_index("foo") is None


def test_add_index_valid_and_duplicate() -> None:
    """Valid new indices are appended; duplicates are skipped silently."""
    indices: list[int] = []
    brwcm.BulkRadiusWLANConfigManager._add_index(2, 5, indices)
    brwcm.BulkRadiusWLANConfigManager._add_index(2, 5, indices)  # duplicate
    assert indices == [2]


def test_add_index_out_of_range(capsys: pytest.CaptureFixture[str]) -> None:
    """Indices past max_count trigger an operator-facing warning."""
    indices: list[int] = []
    brwcm.BulkRadiusWLANConfigManager._add_index(10, 5, indices)
    assert indices == []
    assert "out of range" in capsys.readouterr().out


def test_add_index_negative_is_silently_dropped() -> None:
    """Negative indices are neither added nor warned about (they're just ignored)."""
    indices: list[int] = []
    brwcm.BulkRadiusWLANConfigManager._add_index(-3, 5, indices)
    assert indices == []


def test_parse_one_part_range_and_single() -> None:
    """_parse_one_part expands ranges and appends single indices via _add_index."""
    indices: list[int] = []
    brwcm.BulkRadiusWLANConfigManager._parse_one_part("2-4", 10, indices)
    brwcm.BulkRadiusWLANConfigManager._parse_one_part("7", 10, indices)
    assert indices == [1, 2, 3, 6]


def test_parse_one_part_malformed_range_ignored() -> None:
    """A malformed range piece contributes nothing to indices."""
    indices: list[int] = []
    brwcm.BulkRadiusWLANConfigManager._parse_one_part("a-b", 10, indices)
    assert indices == []


def test_parse_one_part_malformed_single_ignored() -> None:
    """A malformed single-index piece contributes nothing to indices."""
    indices: list[int] = []
    brwcm.BulkRadiusWLANConfigManager._parse_one_part("nope", 10, indices)
    assert indices == []


def test_parse_selection_cancel_keyword() -> None:
    """Any cancel keyword returns None to signal user cancellation."""
    manager = _make_manager()
    for keyword in ["q", "Quit", "cancel", "back"]:
        assert manager._parse_selection(keyword) is None


def test_parse_selection_all() -> None:
    """'all' returns the full 0-based index range for radius_wlans."""
    manager = _make_manager()
    manager.radius_wlans = [{"id": str(i)} for i in range(4)]
    assert manager._parse_selection("all") == [0, 1, 2, 3]


def test_parse_selection_mixed_and_through() -> None:
    """Comma-separated indices with 'through' produce a sorted deduplicated list."""
    manager = _make_manager()
    manager.radius_wlans = [{"id": str(i)} for i in range(10)]
    result = manager._parse_selection("1, 3 through 5, 2")
    assert result == [0, 1, 2, 3, 4]


def test_parse_selection_through_word() -> None:
    """The literal word 'through' (no spaces) is also treated as a dash."""
    manager = _make_manager()
    manager.radius_wlans = [{"id": str(i)} for i in range(5)]
    result = manager._parse_selection("1through3")
    assert result == [0, 1, 2]


def test_parse_selection_empty_and_invalid() -> None:
    """Invalid input yields an empty list of indices (not None)."""
    manager = _make_manager()
    manager.radius_wlans = [{"id": "a"}]
    assert manager._parse_selection("nope") == []


# ---------------------------------------------------------------------------
# _display_preview
# ---------------------------------------------------------------------------


def test_display_preview_prints_diffs(capsys: pytest.CaptureFixture[str]) -> None:
    """Preview lists each selected WLAN with an SSID + old->new diff block."""
    manager = _make_manager()
    manager.selected_wlans = [{"ssid": "S1", "auth_servers_timeout": 5, "auth_servers_retries": 3}]
    manager._display_preview()
    out = capsys.readouterr().out
    assert "SSID: S1" in out
    assert "timeout: 5 -> 3" in out
    assert "retries: 3 -> 2" in out
    assert "fast_dot1x: False -> True" in out


# ---------------------------------------------------------------------------
# _build_radius_payload
# ---------------------------------------------------------------------------


def test_build_radius_payload_shape() -> None:
    """Payload contains exactly the three timer fields at target values."""
    manager = _make_manager()
    payload = manager._build_radius_payload()
    assert payload == {"auth_servers_timeout": 3, "auth_servers_retries": 2, "fast_dot1x_timers": True}


# ---------------------------------------------------------------------------
# _record_change
# ---------------------------------------------------------------------------


def test_record_change_captures_before_and_after() -> None:
    """Change record captures identifiers and before/after values."""
    manager = _make_manager()
    wlan = {
        "id": "w-1",
        "ssid": "SSID-1",
        "auth_servers_timeout": 5,
        "auth_servers_retries": 4,
        "fast_dot1x_timers": False,
        "_inheritance_source": "Org-Level WLAN",
        "_inheritance_level": "org",
    }
    manager._record_change(wlan, "success", "")
    assert len(manager.change_records) == 1
    rec = manager.change_records[0]
    assert rec["wlan_id"] == "w-1"
    assert rec["before_timeout"] == 5 and rec["after_timeout"] == 3
    assert rec["before_retries"] == 4 and rec["after_retries"] == 2
    assert rec["before_fast_dot1x"] is False and rec["after_fast_dot1x"] is True
    assert rec["status"] == "success"


# ---------------------------------------------------------------------------
# _simulate_wlan_update
# ---------------------------------------------------------------------------


def test_simulate_wlan_update_success_debug_off(capsys: pytest.CaptureFixture[str]) -> None:
    """Simulated update prints DRY-RUN, records a change, returns True."""
    manager = _make_manager()
    fake = _make_mh(debug=False)
    with patch.object(brwcm.importlib, "import_module", return_value=fake):
        assert manager._simulate_wlan_update({"id": "w", "ssid": "SS"}, {"k": "v"}) is True
    assert "DRY-RUN" in capsys.readouterr().out
    assert manager.change_records[0]["status"] == "DRY-RUN"


def test_simulate_wlan_update_debug_on_logs_payload() -> None:
    """Debug-on path emits a payload debug log line."""
    manager = _make_manager()
    fake = _make_mh(debug=True)
    with (
        patch.object(brwcm.importlib, "import_module", return_value=fake),
        patch.object(brwcm.logging, "debug") as mock_debug,
    ):
        manager._simulate_wlan_update({"id": "w", "ssid": "SS"}, {"k": "v"})
    mock_debug.assert_called()


# ---------------------------------------------------------------------------
# _call_wlan_update_api
# ---------------------------------------------------------------------------


def test_call_wlan_update_api_success(capsys: pytest.CaptureFixture[str]) -> None:
    """HTTP 200 records success and returns True."""
    manager = _make_manager()
    fake = _make_mh(debug=True)  # exercise debug-dump branch
    response = SimpleNamespace(status_code=200, data={"ok": True})
    with (
        patch.object(brwcm.importlib, "import_module", return_value=fake),
        patch.object(brwcm.mistapi.api.v1.orgs.wlans, "updateOrgWlan", return_value=response),
    ):
        assert manager._call_wlan_update_api({"id": "w", "ssid": "SS"}, {"k": "v"}) is True
    assert "OK" in capsys.readouterr().out
    assert manager.change_records[0]["status"] == "success"


def test_call_wlan_update_api_http_error(capsys: pytest.CaptureFixture[str]) -> None:
    """HTTP non-200 records failure with the status code in the error message."""
    manager = _make_manager()
    fake = _make_mh()
    response = SimpleNamespace(status_code=500, data=None)
    with (
        patch.object(brwcm.importlib, "import_module", return_value=fake),
        patch.object(brwcm.mistapi.api.v1.orgs.wlans, "updateOrgWlan", return_value=response),
    ):
        assert manager._call_wlan_update_api({"id": "w", "ssid": "SS"}, {"k": "v"}) is False
    assert "FAILED (HTTP 500)" in capsys.readouterr().out
    assert manager.change_records[0]["status"] == "failed"


def test_call_wlan_update_api_exception(capsys: pytest.CaptureFixture[str]) -> None:
    """Exceptions record failure with the exception text in the error message."""
    manager = _make_manager()
    fake = _make_mh()
    with (
        patch.object(brwcm.importlib, "import_module", return_value=fake),
        patch.object(brwcm.mistapi.api.v1.orgs.wlans, "updateOrgWlan", side_effect=RuntimeError("kaboom")),
    ):
        assert manager._call_wlan_update_api({"id": "w", "ssid": "SS"}, {"k": "v"}) is False
    assert "ERROR (kaboom)" in capsys.readouterr().out
    assert manager.change_records[0]["error_message"] == "kaboom"


# ---------------------------------------------------------------------------
# _update_one_wlan
# ---------------------------------------------------------------------------


def test_update_one_wlan_missing_id_records_failure() -> None:
    """WLAN with no id records a failure and returns False."""
    manager = _make_manager()
    manager.selected_wlans = [{}]
    assert manager._update_one_wlan(1, {}) is False
    assert manager.change_records[0]["error_message"] == "Missing WLAN ID"


def test_update_one_wlan_dry_run_path() -> None:
    """dry_run=True dispatches to the simulated path."""
    manager = _make_manager()
    manager.selected_wlans = [{"id": "w", "ssid": "SS"}]
    manager.dry_run = True
    fake = _make_mh(debug=False)
    with patch.object(brwcm.importlib, "import_module", return_value=fake):
        assert manager._update_one_wlan(1, {"id": "w", "ssid": "SS"}) is True
    assert manager.change_records[0]["status"] == "DRY-RUN"


def test_update_one_wlan_real_path() -> None:
    """dry_run=False dispatches to the real API call path."""
    manager = _make_manager()
    manager.selected_wlans = [{"id": "w", "ssid": "SS"}]
    manager.dry_run = False
    fake = _make_mh(debug=False)
    response = SimpleNamespace(status_code=200, data={"ok": True})
    with (
        patch.object(brwcm.importlib, "import_module", return_value=fake),
        patch.object(brwcm.mistapi.api.v1.orgs.wlans, "updateOrgWlan", return_value=response),
    ):
        assert manager._update_one_wlan(1, {"id": "w", "ssid": "SS"}) is True


# ---------------------------------------------------------------------------
# _apply_changes
# ---------------------------------------------------------------------------


def test_apply_changes_counts_success_and_failure(capsys: pytest.CaptureFixture[str]) -> None:
    """_apply_changes tallies success and failure counts based on per-WLAN outcome."""
    manager = _make_manager()
    manager.selected_wlans = [{"id": "w1", "ssid": "A"}, {"id": "w2", "ssid": "B"}]
    manager.dry_run = False
    fake = _make_mh()
    responses = iter(
        [
            SimpleNamespace(status_code=200, data={}),
            SimpleNamespace(status_code=500, data={}),
        ]
    )
    with (
        patch.object(brwcm.importlib, "import_module", return_value=fake),
        patch.object(brwcm.mistapi.api.v1.orgs.wlans, "updateOrgWlan", side_effect=lambda *a, **k: next(responses)),
        patch.object(brwcm.AdaptivePacer, "pace", return_value=0.0),
    ):
        manager._apply_changes()
    out = capsys.readouterr().out
    assert "1 successful, 1 failed" in out


def test_apply_changes_dry_run_label(capsys: pytest.CaptureFixture[str]) -> None:
    """dry_run flips the label from 'Applying' -> 'DRY-RUN: Simulating'."""
    manager = _make_manager()
    manager.selected_wlans = [{"id": "w1", "ssid": "A"}]
    manager.dry_run = True
    fake = _make_mh()
    with (
        patch.object(brwcm.importlib, "import_module", return_value=fake),
        patch.object(brwcm.AdaptivePacer, "pace", return_value=0.0),
    ):
        manager._apply_changes()
    out = capsys.readouterr().out
    assert "DRY-RUN: Simulating" in out
    assert "DRY-RUN complete" in out


# ---------------------------------------------------------------------------
# _write_audit_csv + _export_audit_trail
# ---------------------------------------------------------------------------


def test_export_audit_trail_no_records(capsys: pytest.CaptureFixture[str]) -> None:
    """Empty change_records short-circuits with a 'No changes' message."""
    manager = _make_manager()
    manager.change_records = []
    manager._export_audit_trail()
    assert "No changes to export" in capsys.readouterr().out


def test_export_audit_trail_writes_csv(tmp_path: Any, capsys: pytest.CaptureFixture[str]) -> None:
    """A non-empty change list writes a CSV under data/ and prints the path."""
    manager = _make_manager()
    manager.change_records = [
        {
            "timestamp": "2026-06-25T00:00:00",
            "wlan_id": "w1",
            "ssid": "S1",
            "site_name": "Org-Level",
            "inheritance_level": "org",
            "before_timeout": 5,
            "after_timeout": 3,
            "before_retries": 3,
            "after_retries": 2,
            "before_fast_dot1x": False,
            "after_fast_dot1x": True,
            "status": "success",
            "error_message": "",
        }
    ]
    manager._export_audit_trail()
    out = capsys.readouterr().out
    assert "Audit trail exported" in out
    # File should exist under the tmp cwd's data/ directory
    data_dir = os.path.join(os.getcwd(), "data")
    files = [f for f in os.listdir(data_dir) if f.endswith(".csv")]
    assert files, "expected an audit CSV in data/"


def test_export_audit_trail_dry_run_prefix() -> None:
    """dry_run=True prefixes the audit CSV filename with DRYRUN_."""
    manager = _make_manager()
    manager.dry_run = True
    manager.change_records = [{"status": "DRY-RUN"}]
    manager._export_audit_trail()
    data_dir = os.path.join(os.getcwd(), "data")
    files = os.listdir(data_dir)
    assert any(f.startswith("DRYRUN_RadiusWLANBulkConfig_") for f in files)


def test_write_audit_csv_handles_exception(capsys: pytest.CaptureFixture[str]) -> None:
    """A raise inside the CSV writer prints a user-facing failure message."""
    manager = _make_manager()
    manager.change_records = [{"status": "success"}]
    with patch("builtins.open", side_effect=PermissionError("denied")):
        manager._write_audit_csv("nowhere/data.csv")
    assert "Failed to export audit trail: denied" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# _export_scan_snapshot failure branch (line 482-483)
# ---------------------------------------------------------------------------


def test_export_scan_snapshot_reports_failure(capsys: pytest.CaptureFixture[str]) -> None:
    """DataExporter returning False triggers the failure-message branch."""
    manager = _make_manager()
    manager.radius_wlans = [{"id": "n1", "ssid": "N", "_compliance_status": "NEEDS_UPDATE"}]
    with patch.object(MistHelper.DataExporter, "write_with_format_selection", return_value=False):
        manager._export_scan_snapshot()
    assert "Failed to save scan snapshot" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# _scan_and_prepare
# ---------------------------------------------------------------------------


def test_scan_and_prepare_aborts_on_missing_org(capsys: pytest.CaptureFixture[str]) -> None:
    """_scan_and_prepare returns False when org id resolution fails."""
    manager = _make_manager()
    fake = _make_mh()
    fake.ConfigUtils.get_cached_or_prompted_org_id.return_value = ""
    with patch.object(brwcm.importlib, "import_module", return_value=fake):
        assert manager._scan_and_prepare() is False
    assert "Unable to determine organization ID" in capsys.readouterr().out


def test_scan_and_prepare_aborts_on_scan_failure() -> None:
    """_scan_and_prepare returns False when the WLAN scan fails."""
    manager = _make_manager()
    fake = _make_mh()
    response = SimpleNamespace(status_code=500, data=None)
    with (
        patch.object(brwcm.importlib, "import_module", return_value=fake),
        patch.object(brwcm.mistapi.api.v1.orgs.wlans, "listOrgWlans", return_value=response),
    ):
        assert manager._scan_and_prepare() is False


def test_scan_and_prepare_empty_returns_false(capsys: pytest.CaptureFixture[str]) -> None:
    """No RADIUS WLANs in the org yields False and a 'No RADIUS-enabled WLANs' message."""
    manager = _make_manager()
    fake = _make_mh()
    response = SimpleNamespace(status_code=200, data=[{"id": "x", "ssid": "PSK", "auth": {"type": "psk"}}])
    with (
        patch.object(brwcm.importlib, "import_module", return_value=fake),
        patch.object(brwcm.mistapi.api.v1.orgs.wlans, "listOrgWlans", return_value=response),
    ):
        assert manager._scan_and_prepare() is False
    assert "No RADIUS-enabled WLANs" in capsys.readouterr().out


def test_scan_and_prepare_success_returns_true() -> None:
    """Non-empty RADIUS WLAN list returns True to indicate readiness to apply."""
    manager = _make_manager()
    fake = _make_mh()
    wlan = {
        "id": "n1",
        "ssid": "NeedsUpdate",
        "auth_servers": [{"host": "a"}],
        "auth_servers_timeout": 5,
    }
    response = SimpleNamespace(status_code=200, data=[wlan])
    with (
        patch.object(brwcm.importlib, "import_module", return_value=fake),
        patch.object(brwcm.mistapi.api.v1.orgs.wlans, "listOrgWlans", return_value=response),
    ):
        assert manager._scan_and_prepare() is True
    assert manager.radius_wlans and manager.radius_wlans[0]["id"] == "n1"


# ---------------------------------------------------------------------------
# _handle_all_compliant
# ---------------------------------------------------------------------------


def test_handle_all_compliant_true_short_circuits(capsys: pytest.CaptureFixture[str]) -> None:
    """All-compliant state prints the informational message and returns True."""
    manager = _make_manager()
    manager.radius_wlans = []
    manager.compliant_wlans = [{"ssid": "OK", "_inheritance_level": "org", "_compliance_status": "COMPLIANT"}]
    assert manager._handle_all_compliant() is True
    assert "already at target settings" in capsys.readouterr().out


def test_handle_all_compliant_false_when_updates_pending() -> None:
    """Any non-empty radius_wlans list returns False (updates pending)."""
    manager = _make_manager()
    manager.radius_wlans = [{"id": "n"}]
    manager.compliant_wlans = []
    assert manager._handle_all_compliant() is False


# ---------------------------------------------------------------------------
# _prompt_and_parse_selection
# ---------------------------------------------------------------------------


def test_prompt_and_parse_empty_input(capsys: pytest.CaptureFixture[str]) -> None:
    """Empty input returns None and prints an 'exiting' message."""
    manager = _make_manager()
    manager.radius_wlans = [{"id": "n"}]
    fake = _make_mh()
    fake.InputUtils.safe_input.return_value = "   "
    with patch.object(brwcm.importlib, "import_module", return_value=fake):
        assert manager._prompt_and_parse_selection() is None
    assert "No selection made" in capsys.readouterr().out


def test_prompt_and_parse_cancel_keyword(capsys: pytest.CaptureFixture[str]) -> None:
    """Cancel keyword returns None and prints a cancellation message."""
    manager = _make_manager()
    manager.radius_wlans = [{"id": "n"}]
    fake = _make_mh()
    fake.InputUtils.safe_input.return_value = "q"
    with patch.object(brwcm.importlib, "import_module", return_value=fake):
        assert manager._prompt_and_parse_selection() is None
    assert "cancelled by user" in capsys.readouterr().out


def test_prompt_and_parse_invalid_selection(capsys: pytest.CaptureFixture[str]) -> None:
    """Selection that parses to no valid indices returns None with 'Invalid selection'."""
    manager = _make_manager()
    manager.radius_wlans = [{"id": "n"}]
    fake = _make_mh()
    fake.InputUtils.safe_input.return_value = "nonsense"
    with patch.object(brwcm.importlib, "import_module", return_value=fake):
        assert manager._prompt_and_parse_selection() is None
    assert "Invalid selection" in capsys.readouterr().out


def test_prompt_and_parse_success() -> None:
    """Valid '1,2' input resolves to [0, 1]."""
    manager = _make_manager()
    manager.radius_wlans = [{"id": "a"}, {"id": "b"}]
    fake = _make_mh()
    fake.InputUtils.safe_input.return_value = "1,2"
    with patch.object(brwcm.importlib, "import_module", return_value=fake):
        assert manager._prompt_and_parse_selection() == [0, 1]


# ---------------------------------------------------------------------------
# _confirm_and_apply
# ---------------------------------------------------------------------------


def test_confirm_and_apply_cancelled(capsys: pytest.CaptureFixture[str]) -> None:
    """Anything other than exact 'APPLY' cancels without applying changes."""
    manager = _make_manager()
    manager.selected_wlans = [{"id": "w", "ssid": "S"}]
    fake = _make_mh()
    fake.InputUtils.safe_input.return_value = "no"
    with patch.object(brwcm.importlib, "import_module", return_value=fake):
        manager._confirm_and_apply()
    out = capsys.readouterr().out
    assert "cancelled by user" in out
    assert manager.change_records == []


def test_confirm_and_apply_proceeds_on_apply(capsys: pytest.CaptureFixture[str]) -> None:
    """Exact 'APPLY' input calls _apply_changes + _export_audit_trail."""
    manager = _make_manager()
    manager.dry_run = True
    manager.selected_wlans = [{"id": "w", "ssid": "S"}]
    fake = _make_mh()
    fake.InputUtils.safe_input.return_value = "APPLY"
    with (
        patch.object(brwcm.importlib, "import_module", return_value=fake),
        patch.object(brwcm.AdaptivePacer, "pace", return_value=0.0),
    ):
        manager._confirm_and_apply()
    out = capsys.readouterr().out
    assert "Bulk RADIUS WLAN configuration completed" in out
    # dry-run recorded exactly one change
    assert manager.change_records[0]["status"] == "DRY-RUN"


# ---------------------------------------------------------------------------
# manage() end-to-end
# ---------------------------------------------------------------------------


def _run_manage(
    manager: brwcm.BulkRadiusWLANConfigManager,
    wlans: list[dict[str, Any]],
    selection: str,
    confirm: str,
    dry_run: bool = True,
) -> None:
    """Drive manage() end-to-end against a stub MistHelper namespace + mistapi patches."""
    fake = _make_mh()
    # Chain safe_input to return selection first, then the APPLY confirmation.
    fake.InputUtils.safe_input = MagicMock(side_effect=[selection, confirm])
    response = SimpleNamespace(status_code=200, data=wlans)
    with (
        patch.object(brwcm.importlib, "import_module", return_value=fake),
        patch.object(brwcm.mistapi.api.v1.orgs.wlans, "listOrgWlans", return_value=response),
        patch.object(
            brwcm.mistapi.api.v1.orgs.wlans,
            "updateOrgWlan",
            return_value=SimpleNamespace(status_code=200, data={}),
        ),
        patch.object(brwcm.AdaptivePacer, "pace", return_value=0.0),
    ):
        manager.manage(dry_run=dry_run)


def test_manage_scan_prepare_failure_short_circuits() -> None:
    """manage() returns early when _scan_and_prepare returns False."""
    manager = _make_manager()
    fake = _make_mh()
    fake.ConfigUtils.get_cached_or_prompted_org_id.return_value = ""
    with patch.object(brwcm.importlib, "import_module", return_value=fake):
        manager.manage(dry_run=False)
    # No selection was made -> no changes recorded
    assert manager.change_records == []


def test_manage_all_compliant_short_circuits(capsys: pytest.CaptureFixture[str]) -> None:
    """manage() short-circuits when every RADIUS WLAN is already compliant."""
    manager = _make_manager()
    wlan = {
        "id": "c1",
        "ssid": "OK",
        "auth_servers": [{"host": "a"}],
        "auth_servers_timeout": 3,
        "auth_servers_retries": 2,
        "fast_dot1x_timers": True,
    }
    _run_manage(manager, [wlan], selection="all", confirm="APPLY")
    assert "already at target settings" in capsys.readouterr().out
    assert manager.change_records == []


def test_manage_cancelled_at_selection(capsys: pytest.CaptureFixture[str]) -> None:
    """manage() aborts (no changes) when the user cancels at the selection prompt."""
    manager = _make_manager()
    wlan = {
        "id": "n1",
        "ssid": "NeedsUpdate",
        "auth_servers": [{"host": "a"}],
    }
    _run_manage(manager, [wlan], selection="q", confirm="APPLY")
    assert "cancelled by user" in capsys.readouterr().out
    assert manager.change_records == []


def test_manage_full_apply_dry_run(capsys: pytest.CaptureFixture[str]) -> None:
    """manage() dry-run path selects, previews, confirms, applies, and exports audit."""
    manager = _make_manager()
    wlan = {
        "id": "n1",
        "ssid": "NeedsUpdate",
        "auth_servers": [{"host": "a"}],
        "auth_servers_timeout": 5,
    }
    _run_manage(manager, [wlan], selection="1", confirm="APPLY", dry_run=True)
    out = capsys.readouterr().out
    assert "Bulk RADIUS WLAN configuration completed" in out
    assert manager.change_records and manager.change_records[0]["status"] == "DRY-RUN"


def test_manage_real_apply(capsys: pytest.CaptureFixture[str]) -> None:
    """manage() real-apply path calls updateOrgWlan and records success."""
    manager = _make_manager()
    wlan = {
        "id": "n1",
        "ssid": "NeedsUpdate",
        "auth_servers": [{"host": "a"}],
        "auth_servers_timeout": 5,
    }
    _run_manage(manager, [wlan], selection="1", confirm="APPLY", dry_run=False)
    out = capsys.readouterr().out
    assert "1 successful, 0 failed" in out
    assert manager.change_records[0]["status"] == "success"
