"""Tests for src.ssid_consolidation.ssid_template_consolidation.

Covers all pure helper functions, class __init__, execute entry point,
phase menu dispatch, cache/resume logic, matrix building, deviation
analysis, variable plan, group plan, template configs, disable plan,
and display/summary functions.
"""

# pylint: disable=too-many-lines,logging-fstring-interpolation

from __future__ import annotations

import json
import logging
import os
import re
import sys
from datetime import UTC, datetime
from unittest.mock import MagicMock, mock_open, patch

import pytest

# ---------------------------------------------------------------------------
# Mock mistapi before importing the module under test
# ---------------------------------------------------------------------------
_mock_mistapi = MagicMock()
# WHY: the cluster methods do lazy re-imports (for example `from
# .ssid_template_consolidation import _disable_single_ssid` inside
# _SsidTemplatePhase45Cluster). Those must resolve the same mocked mistapi, so the
# stubs stay installed for the whole time this module's tests run. setup_module
# re-installs them and teardown_module removes them again.
_MISTAPI_STUBS: dict[str, MagicMock] = {
    "mistapi": _mock_mistapi,
    "mistapi.api": MagicMock(),
    "mistapi.api.v1": MagicMock(),
    "mistapi.api.v1.orgs": MagicMock(),
    "mistapi.api.v1.orgs.templates": MagicMock(),
    "mistapi.api.v1.orgs.wlans": MagicMock(),
    "mistapi.api.v1.orgs.sites": MagicMock(),
    "mistapi.api.v1.orgs.mxtunnels": MagicMock(),
    "mistapi.api.v1.orgs.sitegroups": MagicMock(),
    "mistapi.api.v1.sites": MagicMock(),
    "mistapi.api.v1.sites.sites": MagicMock(),
    "mistapi.get_all": MagicMock(),
}
_saved_mistapi_modules = {name: sys.modules.get(name) for name in _MISTAPI_STUBS}


def _install_mistapi_stubs() -> None:
    """Put every mistapi stub into sys.modules."""
    sys.modules.update(_MISTAPI_STUBS)


def _restore_mistapi_modules() -> None:
    """Undo _install_mistapi_stubs for each entry we still own."""
    for name, saved in _saved_mistapi_modules.items():
        if sys.modules.get(name) is not _MISTAPI_STUBS[name]:
            continue  # Another module replaced our stub; leave it alone.
        if saved is not None:
            sys.modules[name] = saved
        else:
            sys.modules.pop(name, None)


# Restore the moment the import finishes. pytest imports every test module during
# collection but runs teardown_module only for a module that has a selected test, so a
# stub left here leaks for the whole session and breaks mistapi's lazy subpackage
# import. See issue #1739.
_install_mistapi_stubs()
try:
    import src.ssid_consolidation.ssid_template_consolidation as _mod  # noqa: E402
    from src.ssid_consolidation.ssid_template_consolidation import (  # noqa: E402
        SSIDTemplateConsolidationManager,
        SsidTemplateDeps,
        TemplateOpParams,
        TemplateOutcome,
        _add_pilot_group,
        _append_drift_record,
        _append_ssid_to_template,
        _assign_matrix_sites,
        _build_all_template_configs,
        _build_cluster_groups,
        _build_deviation_record,
        _build_disable_base,
        _build_disable_plan,
        _build_mxtunnel_lookup,
        _build_site_row,
        _build_sitegroup_lookup,
        _build_skip_entry,
        _build_template_config,
        _build_template_lookup,
        _build_variable_entry,
        _cache_age_minutes,
        _check_cache_exists,
        _check_prerequisite_for_all,
        _classify_disable_entry,
        _classify_site,
        _collect_comparison_keys,
        _collect_group_wlan_configs,
        _collect_key_values,
        _compute_group_plan,
        _compute_variable_plan,
        _create_new_template,
        _create_site_group,
        _detect_cross_cluster_drift,
        _determine_target_group,
        _display_disable_plan,
        _display_group_plan,
        _display_template_plan,
        _display_variable_summary,
        _extract_deviation_params,
        _find_representative,
        _find_target_wlan,
        _get_cached_site_vars,
        _get_existing_group_site_ids,
        _get_template_wlans,
        _group_by_target,
        _group_entries_by_site,
        _handle_completed_resume,
        _handle_existing_non_misthelper,
        _handle_partial_resume,
        _load_group_plan_from_results,
        _populate_from_representative,
        _print_conflicts,
        _print_phase1_summary,
        _print_phase_summary,
        _resolve_template,
        _set_ssid_disabled,
        _SiteLookups,
        _template_result,
    )
finally:
    _restore_mistapi_modules()


def setup_module() -> None:
    """Re-install the stubs for the duration of this module's tests."""
    _install_mistapi_stubs()


def teardown_module() -> None:
    """Remove the stubs again after this module's tests finish."""
    _restore_mistapi_modules()


# ===================================================================
# Helpers
# ===================================================================


def _mist_modules(**overrides: MagicMock) -> dict[str, MagicMock]:
    """Build connected mistapi sys.modules hierarchy."""
    mock_templates = overrides.pop("mistapi.api.v1.orgs.templates", MagicMock())
    mock_wlans = overrides.pop("mistapi.api.v1.orgs.wlans", MagicMock())
    mock_orgs_sites = overrides.pop("mistapi.api.v1.orgs.sites", MagicMock())
    mock_mxtunnels = overrides.pop("mistapi.api.v1.orgs.mxtunnels", MagicMock())
    mock_sitegroups = overrides.pop("mistapi.api.v1.orgs.sitegroups", MagicMock())
    mock_sites_sites = overrides.pop("mistapi.api.v1.sites.sites", MagicMock())

    mock_v1_orgs = MagicMock()
    mock_v1_orgs.templates = mock_templates
    mock_v1_orgs.wlans = mock_wlans
    mock_v1_orgs.sites = mock_orgs_sites
    mock_v1_orgs.mxtunnels = mock_mxtunnels
    mock_v1_orgs.sitegroups = mock_sitegroups

    mock_v1_sites = MagicMock()
    mock_v1_sites.sites = mock_sites_sites

    mock_v1 = MagicMock()
    mock_v1.orgs = mock_v1_orgs
    mock_v1.sites = mock_v1_sites

    mock_api = MagicMock()
    mock_api.v1 = mock_v1

    mock_mistapi = MagicMock()
    mock_mistapi.api = mock_api

    return {
        "mistapi": mock_mistapi,
        "mistapi.api": mock_api,
        "mistapi.api.v1": mock_v1,
        "mistapi.api.v1.orgs": mock_v1_orgs,
        "mistapi.api.v1.orgs.templates": mock_templates,
        "mistapi.api.v1.orgs.wlans": mock_wlans,
        "mistapi.api.v1.orgs.sites": mock_orgs_sites,
        "mistapi.api.v1.orgs.mxtunnels": mock_mxtunnels,
        "mistapi.api.v1.orgs.sitegroups": mock_sitegroups,
        "mistapi.api.v1.sites": mock_v1_sites,
        "mistapi.api.v1.sites.sites": mock_sites_sites,
    }


def _make_manager(**kwargs: object) -> SSIDTemplateConsolidationManager:
    """Create a manager instance with sensible defaults."""
    defaults: dict[str, object] = {
        "org_id": "org-001",
        "target_ssid": "Corp-WiFi",
        "apisession": MagicMock(),
        "page_limit": 100,
        "safe_input_fn": MagicMock(return_value=""),
        "write_data_fn": MagicMock(),
    }
    defaults.update(kwargs)
    return SSIDTemplateConsolidationManager(SsidTemplateDeps(**defaults))  # type: ignore[arg-type]


# ===================================================================
# Class __init__
# ===================================================================


class TestInit:
    """SSIDTemplateConsolidationManager.__init__ tests."""

    def test_stores_all_params(self) -> None:
        session = MagicMock()
        safe_fn = MagicMock()
        write_fn = MagicMock()
        manager = SSIDTemplateConsolidationManager(
            SsidTemplateDeps(
                org_id="org-1",
                target_ssid="TestSSID",
                apisession=session,
                page_limit=500,
                safe_input_fn=safe_fn,
                write_data_fn=write_fn,
            )
        )
        assert manager.org_id == "org-1"
        assert manager.target_ssid == "TestSSID"
        assert manager.apisession is session
        assert manager.page_limit == 500
        assert manager.safe_input_fn is safe_fn
        assert manager.write_data_fn is write_fn
        assert manager.cache == {}


# ===================================================================
# execute() entry point
# ===================================================================


class TestExecute:
    """SSIDTemplateConsolidationManager.execute tests."""

    def test_exits_when_no_org_id(self, caplog: pytest.LogCaptureFixture) -> None:
        get_org = MagicMock(return_value=None)
        with caplog.at_level(logging.WARNING):
            SSIDTemplateConsolidationManager.execute(
                apisession=MagicMock(),
                page_limit=100,
                safe_input_fn=MagicMock(),
                write_data_fn=MagicMock(),
                get_org_id_fn=get_org,
            )
        assert "No organization selected" in caplog.text

    def test_exits_when_no_ssid(self, caplog: pytest.LogCaptureFixture) -> None:
        get_org = MagicMock(return_value="org-1")
        safe_fn = MagicMock(return_value="")
        with caplog.at_level(logging.WARNING):
            SSIDTemplateConsolidationManager.execute(
                apisession=MagicMock(),
                page_limit=100,
                safe_input_fn=safe_fn,
                write_data_fn=MagicMock(),
                get_org_id_fn=get_org,
            )
        assert "No target SSID specified" in caplog.text

    @patch.object(SSIDTemplateConsolidationManager, "run_phase_menu")
    def test_launches_phase_menu(self, mock_menu: MagicMock) -> None:
        get_org = MagicMock(return_value="org-1")
        safe_fn = MagicMock(return_value="Corp-WiFi")
        SSIDTemplateConsolidationManager.execute(
            apisession=MagicMock(),
            page_limit=100,
            safe_input_fn=safe_fn,
            write_data_fn=MagicMock(),
            get_org_id_fn=get_org,
        )
        mock_menu.assert_called_once()


# ===================================================================
# Phase menu
# ===================================================================


class TestPhaseMenu:
    """Phase menu dispatch and navigation tests."""

    def test_quit_returns(self) -> None:
        manager = _make_manager(safe_input_fn=MagicMock(return_value="q"))
        manager.run_phase_menu()

    def test_invalid_selection_loops(self) -> None:
        safe_fn = MagicMock(side_effect=["invalid", "q"])
        manager = _make_manager(safe_input_fn=safe_fn)
        manager.run_phase_menu()
        assert safe_fn.call_count == 2

    def test_build_phase_dispatch_keys(self) -> None:
        manager = _make_manager()
        dispatch = manager._build_phase_dispatch()
        assert set(dispatch.keys()) == {"1", "2", "3", "4", "5"}

    def test_display_phase_menu(self, caplog: pytest.LogCaptureFixture) -> None:
        manager = _make_manager()
        labels = {"1": "Phase 1: Audit"}
        with caplog.at_level(logging.WARNING):
            manager._display_phase_menu(labels)
        assert "Phase 1: Audit" in caplog.text
        assert "q." in caplog.text


# ===================================================================
# Prerequisite checking
# ===================================================================


class TestPrerequisites:
    """Prerequisite checking tests."""

    def test_phase_1_no_cache_needed(self) -> None:
        manager = _make_manager()
        manager.cache = {}
        with patch.object(manager, "_load_cache", return_value=None):
            result = manager._check_prerequisite(1)
        assert result is True

    def test_phase_2_needs_cache(self) -> None:
        manager = _make_manager()
        manager.cache = {}
        with patch.object(manager, "_load_cache", return_value=None):
            result = manager._check_prerequisite(2)
        assert result is False

    def test_check_prerequisite_for_all_phase_1(self) -> None:
        assert _check_prerequisite_for_all(1) is True

    def test_check_prerequisite_for_all_phase_2(self) -> None:
        assert _check_prerequisite_for_all(2) is False


# ===================================================================
# Confirm or cancel
# ===================================================================


class TestConfirmOrCancel:
    """Confirm/cancel prompt tests."""

    def test_confirm_accepted(self) -> None:
        manager = _make_manager(safe_input_fn=MagicMock(return_value="CONFIRM"))
        assert manager._confirm_or_cancel("Proceed?") is True

    def test_confirm_rejected(self, caplog: pytest.LogCaptureFixture) -> None:
        manager = _make_manager(safe_input_fn=MagicMock(return_value="no"))
        with caplog.at_level(logging.WARNING):
            assert manager._confirm_or_cancel("Proceed?") is False
        assert "cancelled" in caplog.text.lower()


# ===================================================================
# Cache age
# ===================================================================


class TestCacheAge:
    """_cache_age_minutes tests."""

    def test_recent_cache(self) -> None:
        now = datetime.now(tz=UTC).isoformat()
        age = _cache_age_minutes(now)
        assert age < 1.0

    def test_old_cache(self) -> None:
        from datetime import timedelta

        old = (datetime.now(tz=UTC) - timedelta(hours=2)).isoformat()
        age = _cache_age_minutes(old)
        assert age > 100.0


# ===================================================================
# Check cache exists
# ===================================================================


class TestCheckCacheExists:
    """_check_cache_exists tests."""

    @patch("os.path.exists", return_value=True)
    def test_cache_found(self, _mock: MagicMock) -> None:
        assert _check_cache_exists("data/cache.json") is True

    @patch("os.path.exists", return_value=False)
    def test_cache_not_found(self, _mock: MagicMock, caplog: pytest.LogCaptureFixture) -> None:
        with caplog.at_level(logging.WARNING):
            assert _check_cache_exists("data/cache.json") is False
        assert "Phase 1 cache not found" in caplog.text


# ===================================================================
# Lookup builders
# ===================================================================


class TestLookupBuilders:
    """_build_mxtunnel_lookup, _build_template_lookup, _build_sitegroup_lookup."""

    def test_mxtunnel_lookup(self) -> None:
        tunnels = [
            {"id": "t1", "name": "Edge-East"},
            {"id": "t2", "name": "Edge-West"},
            {"name": "no-id"},
        ]
        result = _build_mxtunnel_lookup(tunnels)
        assert result == {"t1": "Edge-East", "t2": "Edge-West"}

    def test_template_lookup(self) -> None:
        templates = [
            {"id": "tmpl-1", "name": "Tmpl-A"},
            {"id": "tmpl-2", "name": "Tmpl-B"},
            {},
        ]
        result = _build_template_lookup(templates)
        assert "tmpl-1" in result
        assert "tmpl-2" in result
        assert len(result) == 2

    def test_sitegroup_lookup(self) -> None:
        groups = [
            {"id": "g1", "name": "Group-1"},
            {},
        ]
        result = _build_sitegroup_lookup(groups)
        assert "g1" in result
        assert len(result) == 1


# ===================================================================
# _resolve_template
# ===================================================================


class TestResolveTemplate:
    """_resolve_template tests."""

    def test_direct_site_match(self) -> None:
        site = {"id": "site-1", "sitegroup_ids": []}
        lookup = {
            "tmpl-1": {
                "name": "T1",
                "applies": {"site_ids": ["site-1"], "sitegroup_ids": []},
            }
        }
        tmpl, tid = _resolve_template(site, lookup)  # WHY: sitegroup_lookup left the signature in issue #887.
        assert tid == "tmpl-1"

    def test_sitegroup_match(self) -> None:
        site = {"id": "site-1", "sitegroup_ids": ["g1"]}
        lookup = {
            "tmpl-1": {
                "name": "T1",
                "applies": {"site_ids": [], "sitegroup_ids": ["g1"]},
            }
        }
        tmpl, tid = _resolve_template(site, lookup)  # WHY: sitegroup_lookup left the signature in issue #887.
        assert tid == "tmpl-1"

    def test_no_match(self) -> None:
        site = {"id": "site-1", "sitegroup_ids": []}
        lookup = {
            "tmpl-1": {
                "name": "T1",
                "applies": {"site_ids": ["site-2"], "sitegroup_ids": []},
            }
        }
        tmpl, tid = _resolve_template(site, lookup)  # WHY: sitegroup_lookup left the signature in issue #887.
        assert tmpl is None
        assert tid == ""


# ===================================================================
# _get_template_wlans, _find_target_wlan
# ===================================================================


class TestWlanHelpers:
    """Template WLAN helper tests."""

    def test_get_template_wlans(self) -> None:
        template = {"wlans": [{"ssid": "A"}, {"ssid": "B"}]}
        assert len(_get_template_wlans(template)) == 2

    def test_get_template_wlans_none(self) -> None:
        template = {"wlans": None}
        assert _get_template_wlans(template) == []

    def test_find_target_wlan_match(self) -> None:
        wlans = [{"ssid": "Corp-WiFi"}, {"ssid": "Guest"}]
        result = _find_target_wlan(wlans, "corp-wifi")
        assert result is not None
        assert result["ssid"] == "Corp-WiFi"

    def test_find_target_wlan_no_match(self) -> None:
        wlans = [{"ssid": "Guest"}]
        assert _find_target_wlan(wlans, "Corp-WiFi") is None


# ===================================================================
# _classify_site
# ===================================================================


class TestClassifySite:
    """_classify_site tests."""

    def test_no_template(self) -> None:
        psk, anomaly, reason = _classify_site(None, [], None, {}, ("psk",))
        assert anomaly is True
        assert reason == "no template assigned"

    def test_no_matched_wlan(self) -> None:
        tmpl = {"name": "T"}
        psk, anomaly, reason = _classify_site(tmpl, [{"ssid": "X"}], None, {}, ("psk",))
        assert anomaly is True
        assert reason == "target SSID not found"

    def test_zero_ssids(self) -> None:
        tmpl = {"name": "T"}
        wlan = {"ssid": "Corp"}
        psk, anomaly, reason = _classify_site(tmpl, [], wlan, {}, ("psk",))
        assert anomaly is True
        assert reason == "0 SSIDs"

    def test_one_ssid(self) -> None:
        tmpl = {"name": "T"}
        wlan = {"ssid": "Corp", "auth": {"type": "open"}, "mxtunnel_ids": ["c1"]}
        psk, anomaly, reason = _classify_site(tmpl, [wlan], wlan, {"c1": "Edge"}, ("psk",))
        assert anomaly is True
        assert reason == "1 SSID"

    def test_three_plus_ssids(self) -> None:
        tmpl = {"name": "T"}
        wlans = [{"ssid": "A"}, {"ssid": "B"}, {"ssid": "C"}]
        psk, anomaly, reason = _classify_site(tmpl, wlans, wlans[0], {}, ("psk",))
        assert anomaly is True
        assert reason == "3+ SSIDs"

    def test_two_ssids_psk_detected(self) -> None:
        tmpl = {"name": "T"}
        wlan = {"ssid": "Corp", "auth": {"type": "psk"}, "mxtunnel_ids": ["c1"]}
        wlans = [wlan, {"ssid": "Guest"}]
        psk, anomaly, reason = _classify_site(tmpl, wlans, wlan, {"c1": "Edge"}, ("psk",))
        assert psk is True
        assert anomaly is False

    def test_two_ssids_no_edge(self) -> None:
        tmpl = {"name": "T"}
        wlan = {"ssid": "Corp", "auth": {"type": "open"}, "mxtunnel_ids": []}
        wlans = [wlan, {"ssid": "Guest"}]
        psk, anomaly, reason = _classify_site(tmpl, wlans, wlan, {}, ("psk",))
        assert anomaly is True
        assert reason == "no Edge cluster mapping"

    def test_two_ssids_eligible(self) -> None:
        tmpl = {"name": "T"}
        wlan = {"ssid": "Corp", "auth": {"type": "open"}, "mxtunnel_ids": ["c1"]}
        wlans = [wlan, {"ssid": "Guest"}]
        psk, anomaly, reason = _classify_site(tmpl, wlans, wlan, {"c1": "Edge-East"}, ("psk",))
        assert psk is False
        assert anomaly is False
        assert reason == ""


# ===================================================================
# _determine_target_group
# ===================================================================


class TestDetermineTargetGroup:
    """_determine_target_group tests."""

    def test_pilot_site(self) -> None:
        pattern = re.compile(r"(?i)\b(pilot|test|lab)\b")
        assert _determine_target_group("HQ-Pilot-01", "East", pattern) == "pilot"

    def test_normal_site(self) -> None:
        pattern = re.compile(r"(?i)\b(pilot|test|lab)\b")
        assert _determine_target_group("HQ-Main-01", "East", pattern) == "East"

    def test_empty_cluster(self) -> None:
        pattern = re.compile(r"(?i)\b(pilot|test|lab)\b")
        assert _determine_target_group("HQ-Main-01", "", pattern) == "unknown"


# ===================================================================
# _group_by_target
# ===================================================================


class TestGroupByTarget:
    """_group_by_target tests."""

    def test_groups_correctly(self) -> None:
        rows = [
            {"target_group": "East", "site": "A"},
            {"target_group": "West", "site": "B"},
            {"target_group": "East", "site": "C"},
        ]
        result = _group_by_target(rows)
        assert len(result["East"]) == 2
        assert len(result["West"]) == 1

    def test_missing_target_group(self) -> None:
        rows = [{"site": "A"}]
        result = _group_by_target(rows)
        assert "unknown" in result


# ===================================================================
# Deviation analysis helpers
# ===================================================================


class TestDeviationHelpers:
    """Deviation analysis helper tests."""

    def test_collect_comparison_keys(self) -> None:
        configs = [
            {"ssid": "A", "vlan_id": 10, "auth": {"type": "psk"}},
            {"ssid": "A", "band": "5"},
        ]
        metadata = {"id", "org_id"}
        keys = _collect_comparison_keys(configs, metadata)
        assert "vlan_id" in keys
        assert "band" in keys
        assert "id" not in keys

    def test_collect_key_values_single_value(self) -> None:
        configs = [{"vlan_id": 10}, {"vlan_id": 10}]
        rows = [{"site_name": "A"}, {"site_name": "B"}]
        result = _collect_key_values("vlan_id", configs, rows)
        # Returns dict[str, list[str]] keyed by json-serialized value
        assert len(result) == 1

    def test_collect_key_values_multiple_values(self) -> None:
        configs = [{"vlan_id": 10}, {"vlan_id": 20}]
        rows = [{"site_name": "A"}, {"site_name": "B"}]
        result = _collect_key_values("vlan_id", configs, rows)
        assert len(result) == 2

    def test_build_deviation_record(self) -> None:
        values_map = {
            json.dumps(10): ["A", "B"],
            json.dumps(20): ["C"],
        }
        record = _build_deviation_record("East", [], "vlan_id", values_map)
        assert record["cluster_name"] == "East"
        assert record["parameter"] == "vlan_id"


# ===================================================================
# Cross-cluster drift detection
# ===================================================================


class TestCrossClusterDrift:
    """_detect_cross_cluster_drift tests."""

    def test_no_drift(self) -> None:
        cluster_canonicals = {
            "East": {"auth": "open"},
            "West": {"auth": "open"},
        }
        result = _detect_cross_cluster_drift(cluster_canonicals)
        assert result == []

    def test_drift_detected(self) -> None:
        cluster_canonicals = {
            "East": {"vlan_id": 10},
            "West": {"vlan_id": 20},
        }
        result = _detect_cross_cluster_drift(cluster_canonicals)
        assert len(result) >= 1
        assert result[0]["cluster_name"] == "cross_cluster"


# ===================================================================
# Variable plan helpers
# ===================================================================


class TestVariablePlanHelpers:
    """_compute_variable_plan, _extract_deviation_params, etc."""

    def test_extract_deviation_params(self) -> None:
        deviations = [
            {"cluster_name": "East", "parameter": "vlan_id"},
            {"cluster_name": "cross_cluster", "parameter": "auth"},
            {"cluster_name": "West", "parameter": "band"},
            {"cluster_name": "East", "parameter": ""},
        ]
        result = _extract_deviation_params(deviations)
        assert result == ["band", "vlan_id"]

    def test_build_skip_entry_psk(self) -> None:
        row = {"site_name": "A", "site_id": "s1", "psk_detected": True}
        entry = _build_skip_entry(row, "vlan_id")
        assert entry["status"] == "skipped"
        assert "PSK" in entry["reason"]

    def test_build_skip_entry_anomaly(self) -> None:
        row = {
            "site_name": "A",
            "site_id": "s1",
            "psk_detected": False,
            "anomaly_reason": "bad",
        }
        entry = _build_skip_entry(row, "vlan_id")
        assert entry["status"] == "skipped"
        assert "Anomaly" in entry["reason"]

    def test_get_cached_site_vars_found(self) -> None:
        cache = {
            "data": {
                "sites": [
                    {"id": "s1", "vars": {"MISTHELPER_VLAN_ID": "100"}},
                ]
            }
        }
        result = _get_cached_site_vars(cache, "s1")
        assert result == {"MISTHELPER_VLAN_ID": "100"}

    def test_get_cached_site_vars_not_found(self) -> None:
        cache = {"data": {"sites": []}}
        result = _get_cached_site_vars(cache, "s1")
        assert result == {}

    def test_build_variable_entry_pending(self) -> None:
        row = {"site_name": "A", "site_id": "s1", "vlan_id": "100"}
        entry = _build_variable_entry(row, "vlan_id", {})
        assert entry["status"] == "pending"
        assert entry["proposed_value"] == "100"

    def test_build_variable_entry_already_configured(self) -> None:
        row = {"site_name": "A", "site_id": "s1", "vlan_id": "100"}
        site_vars = {"MISTHELPER_VLAN_ID": "100"}
        entry = _build_variable_entry(row, "vlan_id", site_vars)
        assert entry["status"] == "already_configured"

    def test_build_variable_entry_conflict(self) -> None:
        row = {"site_name": "A", "site_id": "s1", "vlan_id": "100"}
        site_vars = {"MISTHELPER_VLAN_ID": "200"}
        entry = _build_variable_entry(row, "vlan_id", site_vars)
        assert entry["status"] == "conflict"
        assert "200" in entry["reason"]

    def test_compute_variable_plan_skips_psk(self) -> None:
        cache = {
            "deviations": [{"cluster_name": "East", "parameter": "vlan_id"}],
            "matrix": [
                {"site_name": "A", "site_id": "s1", "psk_detected": True, "anomaly": False},
            ],
            "data": {"sites": []},
        }
        plan = _compute_variable_plan(cache)
        assert len(plan) == 1
        assert plan[0]["status"] == "skipped"

    def test_compute_variable_plan_pending(self) -> None:
        cache = {
            "deviations": [{"cluster_name": "East", "parameter": "vlan_id"}],
            "matrix": [
                {
                    "site_name": "A",
                    "site_id": "s1",
                    "psk_detected": False,
                    "anomaly": False,
                    "vlan_id": "100",
                },
            ],
            "data": {"sites": [{"id": "s1", "vars": {}}]},
        }
        plan = _compute_variable_plan(cache)
        assert len(plan) == 1
        assert plan[0]["status"] == "pending"


# ===================================================================
# Group plan helpers
# ===================================================================


class TestGroupPlanHelpers:
    """_compute_group_plan, _build_cluster_groups, _add_pilot_group, etc."""

    def test_compute_group_plan_empty(self) -> None:
        cache = {"matrix": []}
        plan = _compute_group_plan(cache)
        assert "groups" in plan

    def test_build_cluster_groups(self) -> None:
        cluster_names = ["East", "West"]
        existing_lookup: dict[str, dict[str, object]] = {}
        groups = _build_cluster_groups(cluster_names, existing_lookup)
        names = {g["group_name"] for g in groups}
        assert any("East" in str(n) for n in names)
        assert any("West" in str(n) for n in names)

    def test_add_pilot_group(self) -> None:
        existing_lookup: dict[str, dict[str, object]] = {}
        groups: list[dict[str, object]] = []
        _add_pilot_group(groups, existing_lookup)
        assert len(groups) == 1

    def test_add_pilot_group_already_exists(self) -> None:
        existing_lookup = {"misthelper_pilot": {"id": "g1"}}
        groups: list[dict[str, object]] = []
        _add_pilot_group(groups, existing_lookup)
        assert len(groups) == 1

    def test_assign_matrix_sites(self) -> None:
        group_name_map = {
            "East": {
                "group_name": "misthelper_prod_East",
                "cluster_name": "East",
                "sites": [],
            }
        }
        matrix = [
            {
                "target_group": "East",
                "site_id": "s1",
                "site_name": "Site-A",
                "anomaly": False,
                "psk_detected": False,
            },
            {
                "target_group": "East",
                "site_id": "s2",
                "site_name": "Site-B",
                "anomaly": True,
                "psk_detected": False,
            },
        ]
        _assign_matrix_sites(matrix, group_name_map)


# ===================================================================
# Resume helpers
# ===================================================================


class TestResumeHelpers:
    """_handle_completed_resume, _handle_partial_resume tests."""

    def test_handle_completed_resume(self) -> None:
        result = _handle_completed_resume(2, 10, 10, MagicMock(return_value="y"))
        assert isinstance(result, tuple)

    def test_handle_partial_resume_yes(self) -> None:
        safe_fn = MagicMock(return_value="y")
        result = _handle_partial_resume(2, 5, 10, [{"status": "done"}], safe_fn)
        assert isinstance(result, tuple)

    def test_handle_partial_resume_no(self) -> None:
        safe_fn = MagicMock(return_value="n")
        result = _handle_partial_resume(2, 5, 10, [], safe_fn)
        assert isinstance(result, tuple)


# ===================================================================
# Display helpers
# ===================================================================


class TestDisplayHelpers:
    """Display/print helper tests."""

    def test_display_variable_summary(self, caplog: pytest.LogCaptureFixture) -> None:
        plan = [
            {"status": "pending", "variable_name": "V"},
            {"status": "skipped", "variable_name": "V"},
            {"status": "already_configured", "variable_name": "V"},
            {
                "status": "conflict",
                "variable_name": "V",
                "site_name": "S",
                "reason": "X",
                "current_value": "200",
                "proposed_value": "100",
            },
        ]
        with caplog.at_level(logging.WARNING):
            _display_variable_summary(plan)
        assert len(caplog.text) > 0

    def test_print_conflicts(self, caplog: pytest.LogCaptureFixture) -> None:
        conflicts = [
            {
                "site_name": "Site-A",
                "variable_name": "V",
                "reason": "Existing: 200",
                "current_value": "200",
                "proposed_value": "100",
            },
        ]
        with caplog.at_level(logging.WARNING):
            _print_conflicts(conflicts)
        assert "Site-A" in caplog.text

    def test_display_group_plan(self, caplog: pytest.LogCaptureFixture) -> None:
        plan = {
            "groups": [
                {
                    "group_name": "G1",
                    "cluster_name": "East",
                    "exists": False,
                    "sites": [{"site_name": "S1"}],
                }
            ]
        }
        with caplog.at_level(logging.WARNING):
            _display_group_plan(plan)
        assert "G1" in caplog.text

    def test_display_template_plan(self, caplog: pytest.LogCaptureFixture) -> None:
        configs = {
            "G1": {"ssid": "Corp", "enabled": True},
        }
        group_plan = {"G1": {"cluster_name": "East"}}
        with caplog.at_level(logging.WARNING):
            _display_template_plan(configs, group_plan)
        assert "G1" in caplog.text

    def test_display_disable_plan(self, caplog: pytest.LogCaptureFixture) -> None:
        plan = [
            {"site_name": "A", "ssid_name": "Corp", "action": "to_disable", "status": "pending"},
        ]
        with caplog.at_level(logging.WARNING):
            _display_disable_plan(plan)
        assert len(caplog.text) > 0

    def test_print_phase1_summary(self, caplog: pytest.LogCaptureFixture) -> None:
        matrix = [
            {"anomaly": False, "psk_detected": False, "target_group": "East"},
            {"anomaly": True, "psk_detected": False, "target_group": "East"},
        ]
        deviations = [{"parameter": "vlan_id"}]
        with caplog.at_level(logging.WARNING):
            _print_phase1_summary(matrix, deviations)
        assert "eligible" in caplog.text.lower() or "Eligible" in caplog.text

    def test_print_phase_summary(self, caplog: pytest.LogCaptureFixture) -> None:
        results = [
            {"status": "success"},
            {"status": "failed"},
            {"status": "skipped"},
        ]
        with caplog.at_level(logging.WARNING):
            _print_phase_summary("Test Phase", results)
        assert "success" in caplog.text.lower() or "Success" in caplog.text


# ===================================================================
# Group entry helpers
# ===================================================================


class TestGroupEntryHelpers:
    """_group_entries_by_site, _get_existing_group_site_ids tests."""

    def test_group_entries_by_site(self) -> None:
        entries = [
            {"site_id": "s1", "var": "V1"},
            {"site_id": "s1", "var": "V2"},
            {"site_id": "s2", "var": "V3"},
        ]
        result = _group_entries_by_site(entries)
        assert len(result["s1"]) == 2
        assert len(result["s2"]) == 1

    def test_get_existing_group_site_ids(self) -> None:
        cache = {
            "data": {
                "sitegroups": [
                    {"id": "g1", "site_ids": ["s1", "s2"]},
                    {"id": "g2", "site_ids": ["s3"]},
                ]
            }
        }
        result = _get_existing_group_site_ids(cache, "g1")
        assert result == ["s1", "s2"]

    def test_get_existing_group_site_ids_not_found(self) -> None:
        cache = {"data": {"sitegroups": []}}
        result = _get_existing_group_site_ids(cache, "g1")
        assert result == []


# ===================================================================
# Template config builders
# ===================================================================


class TestTemplateConfigBuilders:
    """_build_template_config, _build_all_template_configs, etc."""

    def test_build_template_config_no_representative(self) -> None:
        cache = {"deviations": [], "matrix": []}
        config = _build_template_config("East", {}, cache, "Corp-WiFi")
        assert config["ssid"] == "Corp-WiFi"
        assert config["enabled"] is True

    def test_build_template_config_with_deviation(self) -> None:
        cache = {
            "deviations": [
                {"cluster_name": "East", "parameter": "band"},
            ],
            "matrix": [
                {
                    "target_group": "East",
                    "anomaly": False,
                    "psk_detected": False,
                    "wlan_config": {"band": "5"},
                }
            ],
        }
        config = _build_template_config("East", {}, cache, "Corp-WiFi")
        assert "MISTHELPER" in str(config.get("band", ""))

    def test_build_all_template_configs(self) -> None:
        group_plan = {
            "G1": {"cluster_name": "East"},
            "G2": {"cluster_name": "West"},
        }
        cache = {"deviations": [], "matrix": []}
        configs = _build_all_template_configs(group_plan, {}, cache, "Corp")
        assert "G1" in configs
        assert "G2" in configs

    def test_find_representative_found(self) -> None:
        cache = {
            "matrix": [
                {
                    "target_group": "East",
                    "anomaly": False,
                    "psk_detected": False,
                    "site_name": "A",
                },
            ]
        }
        result = _find_representative(cache, "East")
        assert result is not None
        assert result["site_name"] == "A"

    def test_find_representative_fallback_to_pilot(self) -> None:
        cache = {
            "matrix": [
                {
                    "target_group": "pilot",
                    "anomaly": False,
                    "psk_detected": False,
                    "site_name": "P1",
                },
            ]
        }
        result = _find_representative(cache, "NonExistent")
        assert result is not None
        assert result["site_name"] == "P1"

    def test_find_representative_none(self) -> None:
        cache = {"matrix": []}
        assert _find_representative(cache, "East") is None

    def test_populate_from_representative(self) -> None:
        config: dict[str, object] = {"ssid": "Corp"}
        rep = {"vlan_id": 100, "band": "5", "wlan_config": {"auth": "open"}}
        deviation_params: set[str | None] = {"band"}
        _populate_from_representative(config, rep, deviation_params)
        # band is a deviation param, so check it's handled


# ===================================================================
# _load_group_plan_from_results
# ===================================================================


class TestLoadGroupPlanFromResults:
    """_load_group_plan_from_results tests."""

    def test_basic_loading(self) -> None:
        phase3_results = {
            "results": [
                {
                    "group_name": "G1",
                    "cluster_name": "East",
                    "group_id": "gid1",
                    "status": "assigned",
                },
            ]
        }
        plan = _load_group_plan_from_results(phase3_results)
        assert "G1" in plan
        assert plan["G1"]["group_id"] == "gid1"


# ===================================================================
# Disable plan helpers
# ===================================================================


class TestDisablePlanHelpers:
    """_build_disable_plan, _classify_disable_entry, _build_disable_base, etc."""

    def test_build_disable_base(self) -> None:
        row = {
            "site_name": "A",
            "site_id": "s1",
            "template_id": "t1",
            "template_name": "T1",
        }
        base = _build_disable_base(row)
        assert base["site_name"] == "A"
        assert base["site_id"] == "s1"

    def test_set_ssid_disabled_found(self) -> None:
        wlans = [
            {"id": "w1", "enabled": True},
            {"id": "w2", "enabled": True},
        ]
        assert _set_ssid_disabled(wlans, "w1") is True
        assert wlans[0]["enabled"] is False

    def test_set_ssid_disabled_not_found(self) -> None:
        wlans = [{"id": "w1", "enabled": True}]
        assert _set_ssid_disabled(wlans, "w999") is False

    def test_template_result(self) -> None:
        params = TemplateOpParams(
            template_name="T1",
            wlan_config={},
            group_info={"group_name": "G1", "cluster_name": "East"},
            timestamp="2025-01-01T00:00:00",
            target_ssid="",
            org_id="",
            apisession=MagicMock(),
            safe_input_fn=MagicMock(),
        )
        outcome = TemplateOutcome(template_id="t1", action="created")
        result = _template_result(params, outcome)
        assert result["action"] == "created"


# ===================================================================
# _create_site_group
# ===================================================================


class TestCreateSiteGroup:
    """_create_site_group tests."""

    def test_creates_when_no_id(self) -> None:
        group: dict[str, object] = {"group_name": "G1", "sites": []}
        session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.data = {"id": "new-id"}
        with patch.object(
            _mod.mistapi.api.v1.orgs.sitegroups,
            "createOrgSiteGroup",
            return_value=mock_resp,
        ):
            _create_site_group(group, "org-1", session)
        assert group.get("group_id") == "new-id"

    def test_skips_when_has_id(self) -> None:
        group: dict[str, object] = {
            "group_name": "G1",
            "group_id": "existing",
            "sites": [],
        }
        session = MagicMock()
        with patch.dict(sys.modules, _mist_modules()):
            import mistapi.api.v1.orgs.sitegroups as sg_mod

            _create_site_group(group, "org-1", session)
            sg_mod.createOrgSiteGroup.assert_not_called()


# ===================================================================
# _append_ssid_to_template, _create_new_template
# ===================================================================


class TestTemplateCreation:
    """_append_ssid_to_template and _create_new_template tests."""

    def test_append_ssid_to_template(self) -> None:
        session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.data = {"id": "t1", "name": "T1"}
        existing = {"id": "t1", "name": "T1"}
        group_info = {"group_id": "g1", "cluster_name": "East"}
        with (
            patch.object(
                _mod.mistapi.api.v1.orgs.templates,
                "getOrgTemplate",
                return_value=MagicMock(
                    status_code=200,
                    data={"id": "t1", "wlans": [{"ssid": "Guest"}]},
                ),
            ),
            patch.object(
                _mod.mistapi.api.v1.orgs.templates,
                "updateOrgTemplate",
                return_value=mock_resp,
            ),
        ):
            params = TemplateOpParams(
                template_name="T1",
                wlan_config={"ssid": "Corp", "enabled": True},
                group_info=group_info,
                timestamp="2025-01-01T00:00:00",
                target_ssid="Corp",
                org_id="org-1",
                apisession=session,
                safe_input_fn=MagicMock(),
            )
            result = _append_ssid_to_template(params, existing)
        assert result is not None
        assert result["action"] == "updated_append"

    def test_create_new_template(self) -> None:
        session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.data = {"id": "new-t", "name": "T-New"}
        group_info = {"group_id": "g1", "cluster_name": "East"}
        with patch.object(
            _mod.mistapi.api.v1.orgs.templates,
            "createOrgTemplate",
            return_value=mock_resp,
        ):
            params = TemplateOpParams(
                template_name="T-New",
                wlan_config={"ssid": "Corp", "enabled": True},
                group_info=group_info,
                timestamp="2025-01-01T00:00:00",
                target_ssid="Corp",
                org_id="org-1",
                apisession=session,
                safe_input_fn=MagicMock(),
            )
            result = _create_new_template(params)
        assert result is not None
        assert result["action"] == "created"


# ===================================================================
# Coverage boost: module-private helpers & phase orchestrators
# ===================================================================


class TestAssembleSiteRow:
    """_assemble_site_row tests."""

    def test_basic_row(self) -> None:
        from src.ssid_consolidation.ssid_template_consolidation import (
            _assemble_site_row,
        )

        row = _assemble_site_row(
            site_name="HQ",
            site_id="s1",
            template_name="T1",
            template_id="t1",
            matched_wlan={
                "ssid": "Corp",
                "id": "w1",
                "auth": {"type": "psk"},
                "vlan_id": 100,
                "enabled": True,
            },
            first_tunnel_id="mx1",
            cluster_name="East",
            psk_detected=False,
            anomaly=False,
            anomaly_reason="",
            wlans=[{"ssid": "Corp"}, {"ssid": "Guest"}],
            site={"sitegroup_ids": ["sg1"]},
            target_group="East",
        )
        assert row["site_name"] == "HQ"
        assert row["ssid_name"] == "Corp"
        assert row["ssid_id"] == "w1"
        assert row["target_group"] == "East"
        assert row["ssid_count_in_template"] == 2

    def test_no_matched_wlan(self) -> None:
        from src.ssid_consolidation.ssid_template_consolidation import (
            _assemble_site_row,
        )

        row = _assemble_site_row(
            site_name="Branch",
            site_id="s2",
            template_name="",
            template_id="",
            matched_wlan=None,
            first_tunnel_id="",
            cluster_name="",
            psk_detected=False,
            anomaly=True,
            anomaly_reason="No template",
            wlans=[],
            site={},
            target_group="",
        )
        assert row["ssid_name"] == ""
        assert row["ssid_enabled"] is False
        assert row["anomaly"] is True


class TestFetchAndLog:
    """_fetch_and_log tests."""

    def test_fetches_data(self) -> None:
        mock_fn = MagicMock(return_value=MagicMock())
        session = MagicMock()
        with patch.object(_mod, "mistapi") as mock_api:
            mock_api.get_all.return_value = [{"id": "1"}, {"id": "2"}]
            data = _mod._fetch_and_log(
                "test items",
                mock_fn,
                session,
                "org-1",
            )
        assert len(data) == 2

    def test_fetches_with_kwargs(self) -> None:
        mock_fn = MagicMock(return_value=MagicMock())
        session = MagicMock()
        with patch.object(_mod, "mistapi") as mock_api:
            mock_api.get_all.return_value = []
            data = _mod._fetch_and_log(
                "test",
                mock_fn,
                session,
                "org-1",
                limit=100,
            )
        assert data == []


class TestAnalyzeGroupDeviations:
    """_analyze_group_deviations tests."""

    def test_no_wlan_configs(self) -> None:
        from src.ssid_consolidation.ssid_template_consolidation import (
            _analyze_group_deviations,
        )

        rows = [{"template_id": "t1"}]
        template_lookup: dict[str, dict[str, object]] = {
            "t1": {"wlans": [{"ssid": "Other"}]},
        }
        devs, canonicals = _analyze_group_deviations(
            "East",
            rows,
            template_lookup,
            "Corp",
            {"id", "created_time"},
        )
        assert devs == []
        assert canonicals == {}

    def test_with_matching_configs(self) -> None:
        from src.ssid_consolidation.ssid_template_consolidation import (
            _analyze_group_deviations,
        )

        rows = [
            {"template_id": "t1", "site_name": "A"},
            {"template_id": "t2", "site_name": "B"},
        ]
        template_lookup: dict[str, dict[str, object]] = {
            "t1": {
                "wlans": [
                    {"ssid": "Corp", "vlan_id": 100, "auth": {"type": "psk"}},
                ]
            },
            "t2": {
                "wlans": [
                    {"ssid": "Corp", "vlan_id": 200, "auth": {"type": "psk"}},
                ]
            },
        }
        devs, canonicals = _analyze_group_deviations(
            "East",
            rows,
            template_lookup,
            "Corp",
            {"id", "created_time"},
        )
        assert len(devs) >= 1
        assert "vlan_id" in canonicals


class TestWriteSingleSiteVars:
    """_write_single_site_vars tests."""

    def test_writes_successfully(self) -> None:
        from src.ssid_consolidation.ssid_template_consolidation import (
            _write_single_site_vars,
        )

        entries = [
            {
                "site_id": "s1",
                "variable_name": "vlan_id",
                "proposed_value": "100",
                "status": "pending",
            },
        ]
        cache: dict[str, object] = {
            "data": {"sites": [{"id": "s1", "vars": {}}]},
        }
        session = MagicMock()
        with patch.object(
            _mod.mistapi.api.v1.sites.sites,
            "updateSiteInfo",
        ):
            results = _write_single_site_vars("s1", entries, cache, session)
        assert len(results) == 1
        assert results[0]["status"] == "written"

    def test_write_failure(self) -> None:
        entries = [
            {
                "site_id": "s1",
                "variable_name": "vlan_id",
                "proposed_value": "100",
                "status": "pending",
            },
        ]
        cache: dict[str, object] = {
            "data": {"sites": [{"id": "s1", "vars": {}}]},
        }
        session = MagicMock()
        with patch.object(_mod, "mistapi") as mock_api:
            mock_api.api.v1.sites.sites.updateSiteInfo.side_effect = RuntimeError("API error")
            results = _mod._write_single_site_vars(
                "s1",
                entries,
                cache,
                session,
            )
        assert len(results) == 1
        assert results[0]["status"] == "failed"


class TestBuildAssignResults:
    """_build_assign_results and _build_failed_assign_results tests."""

    def test_build_assign_results(self) -> None:
        from src.ssid_consolidation.ssid_template_consolidation import (
            _build_assign_results,
        )

        sites = [
            {"site_id": "s1", "site_name": "A"},
            {"site_id": "s2", "site_name": "B"},
        ]
        existing_ids = ["s1"]
        group = {"group_name": "G1", "cluster_name": "East"}
        results = _build_assign_results(sites, existing_ids, group, "g1")
        assert len(results) == 2
        assert results[0]["status"] == "already_assigned"
        assert results[1]["status"] == "assigned"

    def test_build_failed_assign_results(self) -> None:
        from src.ssid_consolidation.ssid_template_consolidation import (
            _build_failed_assign_results,
        )

        sites = [{"site_id": "s1", "site_name": "A"}]
        group = {"group_name": "G1", "cluster_name": "East"}
        error = RuntimeError("network error")
        results = _build_failed_assign_results(sites, group, "g1", error)
        assert len(results) == 1
        assert results[0]["status"] == "failed"
        assert "network error" in results[0]["reason"]


class TestAssignGroupSites:
    """_assign_group_sites tests."""

    def test_assigns_new_sites(self) -> None:
        from src.ssid_consolidation.ssid_template_consolidation import (
            _assign_group_sites,
        )

        group = {
            "group_id": "g1",
            "group_name": "G1",
            "cluster_name": "East",
            "sites": [
                {"site_id": "s1", "site_name": "A"},
                {"site_id": "s2", "site_name": "B"},
            ],
        }
        completed: set[tuple[str, str]] = set()
        cache: dict[str, object] = {
            "data": {"sitegroups": [{"id": "g1", "site_ids": ["s1"]}]},
        }
        with patch.object(
            _mod.mistapi.api.v1.orgs.sitegroups,
            "updateOrgSiteGroup",
        ):
            results = _assign_group_sites(
                group,
                completed,
                cache,
                "org-1",
                MagicMock(),
            )
        assert len(results) == 2

    def test_skips_completed(self) -> None:
        from src.ssid_consolidation.ssid_template_consolidation import (
            _assign_group_sites,
        )

        group = {
            "group_id": "g1",
            "group_name": "G1",
            "cluster_name": "East",
            "sites": [{"site_id": "s1", "site_name": "A"}],
        }
        completed: set[tuple[str, str]] = {("s1", "g1")}
        cache: dict[str, object] = {"data": {"sitegroups": []}}
        results = _assign_group_sites(
            group,
            completed,
            cache,
            "org-1",
            MagicMock(),
        )
        assert results == []

    def test_handles_api_error(self) -> None:
        group = {
            "group_id": "g1",
            "group_name": "G1",
            "cluster_name": "East",
            "sites": [{"site_id": "s1", "site_name": "A"}],
        }
        completed: set[tuple[str, str]] = set()
        cache: dict[str, object] = {"data": {"sitegroups": []}}
        with patch.object(_mod, "mistapi") as mock_api:
            mock_api.api.v1.orgs.sitegroups.updateOrgSiteGroup.side_effect = RuntimeError("API error")
            results = _mod._assign_group_sites(
                group,
                completed,
                cache,
                "org-1",
                MagicMock(),
            )
        assert len(results) == 1
        assert results[0]["status"] == "failed"


class TestResolveSingleDeviation:
    """_resolve_single_deviation tests."""

    def test_resolves_with_valid_choice(self) -> None:
        from src.ssid_consolidation.ssid_template_consolidation import (
            _resolve_single_deviation,
        )

        deviation = {
            "cluster_name": "East",
            "parameter": "vlan_id",
            "unique_values": json.dumps(
                [
                    {"value": 100, "sites": ["A", "B"], "count": 2},
                    {"value": 200, "sites": ["C"], "count": 1},
                ]
            ),
        }
        resolutions: dict[tuple[str, str], object] = {}
        mock_input = MagicMock(return_value="1")
        _resolve_single_deviation(deviation, resolutions, mock_input)
        assert resolutions[("East", "vlan_id")] == 100

    def test_invalid_choice_skips(self) -> None:
        from src.ssid_consolidation.ssid_template_consolidation import (
            _resolve_single_deviation,
        )

        deviation = {
            "cluster_name": "East",
            "parameter": "vlan_id",
            "unique_values": json.dumps(
                [
                    {"value": 100, "sites": ["A"], "count": 1},
                ]
            ),
        }
        resolutions: dict[tuple[str, str], object] = {}
        mock_input = MagicMock(return_value="abc")
        _resolve_single_deviation(deviation, resolutions, mock_input)
        assert ("East", "vlan_id") not in resolutions

    def test_out_of_range_skips(self) -> None:
        from src.ssid_consolidation.ssid_template_consolidation import (
            _resolve_single_deviation,
        )

        deviation = {
            "cluster_name": "East",
            "parameter": "vlan_id",
            "unique_values": json.dumps(
                [
                    {"value": 100, "sites": ["A"], "count": 1},
                ]
            ),
        }
        resolutions: dict[tuple[str, str], object] = {}
        mock_input = MagicMock(return_value="5")
        _resolve_single_deviation(deviation, resolutions, mock_input)
        assert ("East", "vlan_id") not in resolutions


class TestResolveDeviations:
    """_resolve_deviations tests."""

    def test_resolves_non_cross_cluster(self) -> None:
        cache = {
            "deviations": [
                {
                    "cluster_name": "East",
                    "parameter": "vlan_id",
                    "unique_values": json.dumps(
                        [
                            {"value": 100, "sites": ["A"], "count": 1},
                            {"value": 200, "sites": ["B"], "count": 1},
                        ]
                    ),
                },
                {
                    "cluster_name": "cross_cluster",
                    "parameter": "auth_type",
                    "unique_values": json.dumps([]),
                },
            ],
        }
        mock_input = MagicMock(return_value="1")
        result = _mod._resolve_deviations(cache, mock_input)
        assert ("East", "vlan_id") in result
        assert ("cross_cluster", "auth_type") not in result

    def test_empty_deviations(self) -> None:
        cache: dict[str, object] = {"deviations": []}
        result = _mod._resolve_deviations(cache, MagicMock())
        assert result == {}


class TestDisableSingleSsid:
    """_disable_single_ssid tests."""

    def test_disables_ssid(self) -> None:
        entry = {
            "old_template_id": "t1",
            "ssid_id": "w1",
            "site_id": "s1",
            "status": "to_disable",
        }
        mock_get = MagicMock()
        mock_get.data = {"wlans": [{"id": "w1", "enabled": True}]}
        with patch.object(_mod, "mistapi") as mock_api:
            mock_api.api.v1.orgs.templates.getOrgTemplate.return_value = mock_get
            result = _mod._disable_single_ssid(
                entry,
                "org-1",
                MagicMock(),
            )
        assert result["status"] == "disabled"

    def test_ssid_not_found(self) -> None:
        from src.ssid_consolidation.ssid_template_consolidation import (
            _disable_single_ssid,
        )

        entry = {
            "old_template_id": "t1",
            "ssid_id": "w999",
            "site_id": "s1",
            "status": "to_disable",
        }
        mock_get = MagicMock()
        mock_get.data = {"wlans": [{"id": "w1", "enabled": True}]}
        with patch.object(
            _mod.mistapi.api.v1.orgs.templates,
            "getOrgTemplate",
            return_value=mock_get,
        ):
            result = _disable_single_ssid(entry, "org-1", MagicMock())
        assert result["status"] == "skipped"

    def test_api_error(self) -> None:
        entry = {
            "old_template_id": "t1",
            "ssid_id": "w1",
            "site_id": "s1",
            "status": "to_disable",
        }
        with patch.object(_mod, "mistapi") as mock_api:
            mock_api.api.v1.orgs.templates.getOrgTemplate.side_effect = RuntimeError("API failure")
            result = _mod._disable_single_ssid(
                entry,
                "org-1",
                MagicMock(),
            )
        assert result["status"] == "failed"


class TestCreateOrUpdateSingleTemplate:
    """_create_or_update_single_template tests."""

    def test_creates_new_template(self) -> None:
        from src.ssid_consolidation.ssid_template_consolidation import (
            _create_or_update_single_template,
        )

        mock_resp = MagicMock()
        mock_resp.data = {"id": "new-t", "name": "T-New"}
        with patch.object(
            _mod.mistapi.api.v1.orgs.templates,
            "createOrgTemplate",
            return_value=mock_resp,
        ):
            params = TemplateOpParams(
                template_name="misthelper_East_Corp",
                wlan_config={"ssid": "Corp", "enabled": True},
                group_info={"group_id": "g1", "cluster_name": "East"},
                timestamp="2025-01-01T00:00:00",
                target_ssid="Corp",
                org_id="org-1",
                apisession=MagicMock(),
                safe_input_fn=MagicMock(),
            )
            result = _create_or_update_single_template(params, {})
        assert result["action"] == "created"

    def test_updates_existing_misthelper(self) -> None:
        from src.ssid_consolidation.ssid_template_consolidation import (
            _create_or_update_single_template,
        )

        existing = {"id": "t1", "name": "misthelper_East_Corp"}
        mock_get = MagicMock()
        mock_get.data = {"id": "t1", "wlans": []}
        mock_update = MagicMock()
        mock_update.data = {"id": "t1"}
        with (
            patch.object(
                _mod.mistapi.api.v1.orgs.templates,
                "getOrgTemplate",
                return_value=mock_get,
            ),
            patch.object(
                _mod.mistapi.api.v1.orgs.templates,
                "updateOrgTemplate",
                return_value=mock_update,
            ),
        ):
            params = TemplateOpParams(
                template_name="misthelper_East_Corp",
                wlan_config={"ssid": "Corp", "enabled": True},
                group_info={"group_id": "g1", "cluster_name": "East"},
                timestamp="2025-01-01T00:00:00",
                target_ssid="Corp",
                org_id="org-1",
                apisession=MagicMock(),
                safe_input_fn=MagicMock(),
            )
            result = _create_or_update_single_template(
                params,
                {"misthelper_East_Corp": existing},
            )
        assert result["action"] == "updated_append"

    def test_existing_non_misthelper_skip(self) -> None:
        mock_input = MagicMock(return_value="n")
        params = TemplateOpParams(
            template_name="manual_template",
            wlan_config={"ssid": "Corp"},
            group_info={"group_id": "g1", "cluster_name": "East"},
            timestamp="2025-01-01T00:00:00",
            target_ssid="Corp",
            org_id="org-1",
            apisession=MagicMock(),
            safe_input_fn=mock_input,
        )
        result = _handle_existing_non_misthelper(params)
        assert result["action"] == "skipped"

    def test_handles_exception(self) -> None:
        with patch.object(_mod, "mistapi") as mock_api:
            mock_api.api.v1.orgs.templates.createOrgTemplate.side_effect = RuntimeError("API boom")
            params = TemplateOpParams(
                template_name="misthelper_East_Corp",
                wlan_config={"ssid": "Corp"},
                group_info={"group_id": "g1", "cluster_name": "East"},
                timestamp="2025-01-01T00:00:00",
                target_ssid="Corp",
                org_id="org-1",
                apisession=MagicMock(),
                safe_input_fn=MagicMock(),
            )
            result = _mod._create_or_update_single_template(params, {})
        assert result["action"] == "failed"


class TestHandleExistingNonMisthelper:
    """_handle_existing_non_misthelper tests."""

    def test_user_declines(self) -> None:
        mock_input = MagicMock(return_value="n")
        params = TemplateOpParams(
            template_name="OldTemplate",
            wlan_config={"ssid": "Corp"},
            group_info={"group_id": "g1", "cluster_name": "East"},
            timestamp="2025-01-01T00:00:00",
            target_ssid="Corp",
            org_id="org-1",
            apisession=MagicMock(),
            safe_input_fn=mock_input,
        )
        result = _handle_existing_non_misthelper(params)
        assert result["action"] == "skipped"

    def test_user_accepts(self) -> None:
        mock_input = MagicMock(return_value="y")
        mock_resp = MagicMock()
        mock_resp.data = {"id": "new-t"}
        with patch.object(
            _mod.mistapi.api.v1.orgs.templates,
            "createOrgTemplate",
            return_value=mock_resp,
        ):
            params = TemplateOpParams(
                template_name="OldTemplate",
                wlan_config={"ssid": "Corp"},
                group_info={"group_id": "g1", "cluster_name": "East"},
                timestamp="2025-01-01T00:00:00",
                target_ssid="Corp",
                org_id="org-1",
                apisession=MagicMock(),
                safe_input_fn=mock_input,
            )
            result = _handle_existing_non_misthelper(params)
        assert result["action"] == "created"


class TestPhaseOrchestrators:
    """Tests for phase orchestrator methods."""

    @staticmethod
    def _make_manager() -> SSIDTemplateConsolidationManager:
        return SSIDTemplateConsolidationManager(
            SsidTemplateDeps(
                org_id="org-1",
                target_ssid="Corp",
                apisession=MagicMock(),
                page_limit=100,
                safe_input_fn=MagicMock(return_value="CONFIRM"),
                write_data_fn=MagicMock(),
            )
        )

    def test_check_prerequisite_phase1(self) -> None:
        mgr = self._make_manager()
        assert mgr._check_prerequisite(1) is True

    def test_check_prerequisite_phase2_no_cache(self) -> None:
        mgr = self._make_manager()
        with patch("os.path.exists", return_value=False):
            assert mgr._check_prerequisite(2) is False

    def test_build_phase_dispatch(self) -> None:
        mgr = self._make_manager()
        dispatch = mgr._build_phase_dispatch()
        assert "1" in dispatch
        assert "5" in dispatch

    def test_display_phase_menu(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        mgr = self._make_manager()
        labels = {"1": "Audit", "2": "Variables"}
        with caplog.at_level(logging.WARNING):
            mgr._display_phase_menu(labels)
        assert "Audit" in caplog.text

    def test_phase1_audit_no_data(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        mgr = self._make_manager()
        mgr._phase1_load_or_fetch = MagicMock(return_value=None)  # type: ignore[method-assign]
        with caplog.at_level(logging.WARNING):
            mgr.phase1_audit()
        assert "Failed" in caplog.text or "failed" in caplog.text.lower()

    def test_phase1_load_or_fetch_uses_cache(self) -> None:
        mgr = self._make_manager()
        cache_data = {
            "data": {"sites": []},
            "collected_at": datetime.now(tz=UTC).isoformat(),
        }
        mgr._load_cache = MagicMock(return_value=cache_data)  # type: ignore[method-assign]
        mgr.safe_input_fn = MagicMock(return_value="Y")
        result = mgr._phase1_load_or_fetch()
        assert result == {"sites": []}

    def test_phase2_no_cache(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        mgr = self._make_manager()
        mgr._load_cache = MagicMock(return_value=None)  # type: ignore[method-assign]
        with caplog.at_level(logging.WARNING):
            mgr.phase2_site_variables()
        assert "not found" in caplog.text.lower() or "no cache" in caplog.text.lower()

    def test_phase3_no_cache(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        mgr = self._make_manager()
        mgr._load_cache = MagicMock(return_value=None)  # type: ignore[method-assign]
        with caplog.at_level(logging.WARNING):
            mgr.phase3_site_groups()
        assert "not found" in caplog.text.lower() or "no cache" in caplog.text.lower()

    def test_phase4_no_cache(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        mgr = self._make_manager()
        mgr._load_cache = MagicMock(return_value=None)  # type: ignore[method-assign]
        with caplog.at_level(logging.WARNING):
            mgr.phase4_templates()
        assert "not found" in caplog.text.lower() or "no cache" in caplog.text.lower()

    def test_phase5_no_cache(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        mgr = self._make_manager()
        mgr._load_cache = MagicMock(return_value=None)  # type: ignore[method-assign]
        with caplog.at_level(logging.WARNING):
            mgr.phase5_disable_old()
        assert "not found" in caplog.text.lower() or "no cache" in caplog.text.lower()


class TestFetchAllOrgData:
    """_fetch_all_org_data tests."""

    def test_fetches_five_endpoints(self) -> None:
        mgr = SSIDTemplateConsolidationManager(
            SsidTemplateDeps(
                org_id="org-1",
                target_ssid="Corp",
                apisession=MagicMock(),
                page_limit=100,
                safe_input_fn=MagicMock(),
                write_data_fn=MagicMock(),
            )
        )
        with patch.object(
            _mod.mistapi,
            "get_all",
            return_value=[{"id": "1"}],
        ):
            result = mgr._fetch_all_org_data()
        assert "wlan_templates" in result
        assert "org_wlans" in result
        assert "sites" in result
        assert "mxtunnels" in result
        assert "sitegroups" in result


class TestBuildMatrix:
    """_build_matrix tests."""

    def test_builds_from_org_data(self) -> None:
        mgr = SSIDTemplateConsolidationManager(
            SsidTemplateDeps(
                org_id="org-1",
                target_ssid="Corp",
                apisession=MagicMock(),
                page_limit=100,
                safe_input_fn=MagicMock(),
                write_data_fn=MagicMock(),
            )
        )
        org_data: dict[str, object] = {
            "sites": [{"id": "s1", "name": "HQ"}],
            "wlan_templates": [],
            "sitegroups": [],
            "mxtunnels": [],
        }
        matrix = mgr._build_matrix(org_data)
        assert isinstance(matrix, list)


class TestAnalyzeDeviations:
    """_analyze_deviations tests."""

    def test_no_eligible_sites(self) -> None:
        mgr = SSIDTemplateConsolidationManager(
            SsidTemplateDeps(
                org_id="org-1",
                target_ssid="Corp",
                apisession=MagicMock(),
                page_limit=100,
                safe_input_fn=MagicMock(),
                write_data_fn=MagicMock(),
            )
        )
        matrix = [
            {"anomaly": True, "psk_detected": False, "target_group": "East"},
        ]
        org_data: dict[str, object] = {"wlan_templates": []}
        devs = mgr._analyze_deviations(matrix, org_data)
        assert devs == []


class TestOfferResume:
    """_offer_resume tests."""

    def test_no_prior_results(self) -> None:
        mgr = SSIDTemplateConsolidationManager(
            SsidTemplateDeps(
                org_id="org-1",
                target_ssid="Corp",
                apisession=MagicMock(),
                page_limit=100,
                safe_input_fn=MagicMock(),
                write_data_fn=MagicMock(),
            )
        )
        mgr._load_phase_results = MagicMock(return_value=None)  # type: ignore[method-assign]
        resuming, results = mgr._offer_resume(2)  # WHY: the results parameter left the signature in issue #887.
        assert resuming is False
        assert results == []


class TestEnsureGroupsExist:
    """_ensure_groups_exist tests."""

    def test_creates_missing_groups(self) -> None:
        mgr = SSIDTemplateConsolidationManager(
            SsidTemplateDeps(
                org_id="org-1",
                target_ssid="Corp",
                apisession=MagicMock(),
                page_limit=100,
                safe_input_fn=MagicMock(),
                write_data_fn=MagicMock(),
            )
        )
        plan = {
            "groups": [
                {
                    "group_name": "G1",
                    "exists": True,
                    "group_id": "g1",
                    "sites": [],
                },
                {
                    "group_name": "G2",
                    "exists": False,
                    "group_id": "",
                    "sites": [],
                },
            ],
        }
        mock_resp = MagicMock()
        mock_resp.data = {"id": "new-g"}
        with patch.object(
            _mod.mistapi.api.v1.orgs.sitegroups,
            "createOrgSiteGroup",
            return_value=mock_resp,
        ):
            result = mgr._ensure_groups_exist(plan)
        assert result is plan


class TestDisableSsids:
    """_disable_ssids tests."""

    def test_skips_non_disable_entries(self) -> None:
        mgr = SSIDTemplateConsolidationManager(
            SsidTemplateDeps(
                org_id="org-1",
                target_ssid="Corp",
                apisession=MagicMock(),
                page_limit=100,
                safe_input_fn=MagicMock(),
                write_data_fn=MagicMock(),
            )
        )
        mgr._save_phase_results = MagicMock()  # type: ignore[method-assign]
        plan = [{"status": "skipped", "site_id": "s1", "ssid_id": "w1"}]
        results = mgr._disable_ssids(plan, [])
        assert len(results) == 1
        assert results[0]["status"] == "skipped"

    def test_disables_entries(self) -> None:
        mgr = SSIDTemplateConsolidationManager(
            SsidTemplateDeps(
                org_id="org-1",
                target_ssid="Corp",
                apisession=MagicMock(),
                page_limit=100,
                safe_input_fn=MagicMock(),
                write_data_fn=MagicMock(),
            )
        )
        mgr._save_phase_results = MagicMock()  # type: ignore[method-assign]
        plan = [
            {
                "status": "to_disable",
                "site_id": "s1",
                "ssid_id": "w1",
                "old_template_id": "t1",
            }
        ]
        mock_get = MagicMock()
        mock_get.data = {"wlans": [{"id": "w1", "enabled": True}]}
        with patch.object(_mod, "mistapi") as mock_api:
            mock_api.api.v1.orgs.templates.getOrgTemplate.return_value = mock_get
            results = mgr._disable_ssids(plan, [])
        assert len(results) == 1
        assert results[0]["status"] == "disabled"


class TestWriteSiteVariables:
    """_write_site_variables tests."""

    def test_writes_pending_entries(self) -> None:
        mgr = SSIDTemplateConsolidationManager(
            SsidTemplateDeps(
                org_id="org-1",
                target_ssid="Corp",
                apisession=MagicMock(),
                page_limit=100,
                safe_input_fn=MagicMock(),
                write_data_fn=MagicMock(),
            )
        )
        mgr.cache = {
            "data": {"sites": [{"id": "s1", "vars": {}}]},
        }
        mgr._save_phase_results = MagicMock()  # type: ignore[method-assign]
        plan = [
            {
                "site_id": "s1",
                "variable_name": "vlan",
                "proposed_value": "100",
                "status": "pending",
            }
        ]
        with patch.object(
            _mod.mistapi.api.v1.sites.sites,
            "updateSiteInfo",
        ):
            results = mgr._write_site_variables(plan, [])
        assert len(results) == 1


class TestCreateOrUpdateTemplates:
    """_create_or_update_templates tests."""

    def test_creates_templates(self) -> None:
        mgr = SSIDTemplateConsolidationManager(
            SsidTemplateDeps(
                org_id="org-1",
                target_ssid="Corp",
                apisession=MagicMock(),
                page_limit=100,
                safe_input_fn=MagicMock(),
                write_data_fn=MagicMock(),
            )
        )
        mgr.cache = {"data": {"wlan_templates": []}}
        configs = {"G1": {"ssid": "Corp", "enabled": True}}
        group_plan = {"G1": {"group_id": "g1", "cluster_name": "East"}}
        mock_resp = MagicMock()
        mock_resp.data = {"id": "new-t"}
        with patch.object(
            _mod.mistapi.api.v1.orgs.templates,
            "createOrgTemplate",
            return_value=mock_resp,
        ):
            results = mgr._create_or_update_templates(configs, group_plan)
        assert len(results) == 1


class TestLoadCache:
    """_load_cache with stale/fresh logic tests."""

    def test_returns_none_when_no_file(self) -> None:
        mgr = SSIDTemplateConsolidationManager(
            SsidTemplateDeps(
                org_id="org-1",
                target_ssid="Corp",
                apisession=MagicMock(),
                page_limit=100,
                safe_input_fn=MagicMock(),
                write_data_fn=MagicMock(),
            )
        )
        with patch("os.path.exists", return_value=False):
            assert mgr._load_cache() is None

    def test_returns_fresh_cache(self, tmp_path: os.PathLike[str]) -> None:
        mgr = SSIDTemplateConsolidationManager(
            SsidTemplateDeps(
                org_id="org-1",
                target_ssid="Corp",
                apisession=MagicMock(),
                page_limit=100,
                safe_input_fn=MagicMock(),
                write_data_fn=MagicMock(),
            )
        )
        from pathlib import Path

        cache_file = Path(tmp_path) / "cache.json"
        cache_data = {
            "collected_at": datetime.now(tz=UTC).isoformat(),
            "data": {"sites": []},
        }
        cache_file.write_text(json.dumps(cache_data))
        mgr.CACHE_FILE = str(cache_file)
        result = mgr._load_cache()
        assert result is not None
        assert result["data"] == {"sites": []}

    def test_returns_none_on_invalid_json(
        self,
        tmp_path: os.PathLike[str],
    ) -> None:
        mgr = SSIDTemplateConsolidationManager(
            SsidTemplateDeps(
                org_id="org-1",
                target_ssid="Corp",
                apisession=MagicMock(),
                page_limit=100,
                safe_input_fn=MagicMock(),
                write_data_fn=MagicMock(),
            )
        )
        from pathlib import Path

        cache_file = Path(tmp_path) / "cache.json"
        cache_file.write_text("not json")
        mgr.CACHE_FILE = str(cache_file)
        result = mgr._load_cache()
        assert result is None


class TestTemplateCreationExtra:
    """Template create/update helper tests."""

    def test_append_ssid_to_template(self) -> None:
        session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.data = {"id": "t1", "name": "T1"}
        config = {"ssid": "Corp", "enabled": True}
        existing = {"id": "t1", "name": "T1"}
        group_info = {"group_id": "g1", "cluster_name": "East"}
        with patch.dict(sys.modules, _mist_modules()):
            import mistapi.api.v1.orgs.templates as tmpl_mod

            tmpl_mod.getOrgTemplate.return_value = MagicMock(
                status_code=200,
                data={"id": "t1", "wlans": [{"ssid": "Guest"}]},
            )
            tmpl_mod.updateOrgTemplate.return_value = mock_resp
            params = TemplateOpParams(
                template_name="T1",
                wlan_config=config,
                group_info=group_info,
                timestamp="2025-01-01T00:00:00",
                target_ssid="Corp",
                org_id="org-1",
                apisession=session,
                safe_input_fn=MagicMock(),
            )
            result = _append_ssid_to_template(params, existing)
        assert result is not None
        assert result["action"] == "updated_append"

    def test_create_new_template(self) -> None:
        session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.data = {"id": "new-t", "name": "T-New"}
        config = {"ssid": "Corp", "enabled": True}
        group_info = {"group_id": "g1", "cluster_name": "East"}
        with patch.dict(sys.modules, _mist_modules()):
            import mistapi.api.v1.orgs.templates as tmpl_mod

            tmpl_mod.createOrgTemplate.return_value = mock_resp
            params = TemplateOpParams(
                template_name="T-New",
                wlan_config=config,
                group_info=group_info,
                timestamp="2025-01-01T00:00:00",
                target_ssid="Corp",
                org_id="org-1",
                apisession=session,
                safe_input_fn=MagicMock(),
            )
            result = _create_new_template(params)
        assert result is not None
        assert result["action"] == "created"


# ===================================================================
# _classify_disable_entry
# ===================================================================


class TestClassifyDisableEntry:
    """_classify_disable_entry tests."""

    def test_anomaly_skipped(self) -> None:
        row = {
            "anomaly": True,
            "psk_detected": False,
            "site_name": "A",
            "site_id": "s1",
            "template_id": "t1",
            "template_name": "T1",
        }
        entry = _classify_disable_entry(row)
        assert entry["status"] == "skipped"

    def test_no_ssid_id_skipped(self) -> None:
        row = {
            "anomaly": False,
            "psk_detected": False,
            "site_name": "A",
            "site_id": "s1",
            "template_id": "t1",
            "template_name": "T1",
        }
        entry = _classify_disable_entry(row)
        assert entry["status"] == "skipped"

    def test_has_ssid_id(self) -> None:
        row = {
            "anomaly": False,
            "psk_detected": False,
            "site_name": "A",
            "site_id": "s1",
            "template_id": "t1",
            "template_name": "T1",
            "ssid_id": "wlan-1",
        }
        entry = _classify_disable_entry(row)
        assert entry["status"] == "to_disable"


# ===================================================================
# _build_disable_plan
# ===================================================================


class TestBuildDisablePlan:
    """_build_disable_plan tests."""

    def test_builds_plan_from_matrix(self) -> None:
        cache = {
            "matrix": [
                {
                    "anomaly": False,
                    "psk_detected": False,
                    "site_name": "A",
                    "site_id": "s1",
                    "template_id": "t1",
                    "template_name": "T1",
                    "wlan_config": {"id": "w1"},
                },
            ]
        }
        plan = _build_disable_plan(cache)
        assert isinstance(plan, list)


# ===================================================================
# Cache and phase result persistence
# ===================================================================


class TestCachePersistence:
    """Cache load/save and phase result persistence tests."""

    def test_save_cache(self, tmp_path: object) -> None:
        manager = _make_manager()
        cache_file = os.path.join(str(tmp_path), "cache.json")
        manager.CACHE_FILE = cache_file
        data = {"collected_at": "2025-01-01T00:00:00+00:00", "matrix": []}
        manager._save_cache(data)
        assert os.path.exists(cache_file)
        with open(cache_file) as fh:
            loaded = json.load(fh)
        assert loaded["matrix"] == []

    def test_load_cache_missing(self) -> None:
        manager = _make_manager()
        manager.CACHE_FILE = "nonexistent.json"
        result = manager._load_cache()
        assert result is None

    def test_load_cache_valid(self, tmp_path: object) -> None:
        manager = _make_manager()
        cache_file = os.path.join(str(tmp_path), "cache.json")
        manager.CACHE_FILE = cache_file
        data = {"collected_at": "2025-01-01T00:00:00+00:00", "matrix": []}
        with open(cache_file, "w") as fh:
            json.dump(data, fh)
        result = manager._load_cache()
        assert result is not None

    def test_save_phase_results(self, tmp_path: object) -> None:
        manager = _make_manager()
        result_file = os.path.join(str(tmp_path), "phase2.json")
        manager.PHASE_RESULT_FILES = {2: result_file}
        results = [{"status": "success"}]
        manager._save_phase_results(2, results)
        assert os.path.exists(result_file)

    def test_load_phase_results_missing(self) -> None:
        manager = _make_manager()
        manager.PHASE_RESULT_FILES = {2: "nonexistent.json"}
        result = manager._load_phase_results(2)
        assert result is None


# ===================================================================
# _collect_group_wlan_configs
# ===================================================================


class TestCollectGroupWlanConfigs:
    """_collect_group_wlan_configs tests."""

    def test_collects_non_anomaly(self) -> None:
        rows = [
            {"template_id": "t1"},
            {"template_id": "t2"},
        ]
        template_lookup = {
            "t1": {"wlans": [{"ssid": "Corp"}]},
            "t2": {"wlans": [{"ssid": "Other"}]},
        }
        configs = _collect_group_wlan_configs(rows, template_lookup, "Corp")
        assert len(configs) == 1
        assert configs[0]["ssid"] == "Corp"


# ===================================================================
# _append_drift_record
# ===================================================================


class TestAppendDriftRecord:
    """_append_drift_record tests."""

    def test_appends_when_multiple_values(self) -> None:
        deviations: list[dict[str, object]] = []
        cluster_values = {"East": 10, "West": 20}
        _append_drift_record(deviations, "vlan_id", cluster_values)
        assert len(deviations) == 1
        assert deviations[0]["cluster_name"] == "cross_cluster"

    def test_records_when_same_value(self) -> None:
        deviations: list[dict[str, object]] = []
        cluster_values = {"East": 10, "West": 10}
        _append_drift_record(deviations, "vlan_id", cluster_values)
        assert len(deviations) == 1


# ===================================================================
# Edge cases and integration
# ===================================================================


class TestEdgeCases:
    """Edge case and integration tests."""

    def test_empty_matrix_build_disable_plan(self) -> None:
        cache = {"matrix": []}
        plan = _build_disable_plan(cache)
        assert plan == []

    def test_empty_deviations_resolve(self) -> None:
        cache = {"deviations": []}
        result = _mod._resolve_deviations(cache, MagicMock())
        assert result == {}

    def test_resolve_deviations_skips_cross_cluster(self) -> None:
        cache = {
            "deviations": [
                {"cluster_name": "cross_cluster", "parameter": "auth"},
            ]
        }
        result = _mod._resolve_deviations(cache, MagicMock())
        assert result == {}

    def test_class_constants(self) -> None:
        assert SSIDTemplateConsolidationManager.CONFIRM_KEYWORD == "CONFIRM"
        assert SSIDTemplateConsolidationManager.CACHE_FRESHNESS_MINUTES == 60
        assert "psk" in SSIDTemplateConsolidationManager.PSK_AUTH_TYPES

    def test_metadata_fields_constant(self) -> None:
        fields = SSIDTemplateConsolidationManager.METADATA_FIELDS
        assert "id" in fields
        assert "org_id" in fields
        assert "site_id" in fields

    def test_pilot_pattern_matches(self) -> None:
        pattern = SSIDTemplateConsolidationManager.PILOT_PATTERN
        assert pattern.search("HQ-Pilot-01")
        assert pattern.search("Test-Site")
        assert pattern.search("LAB-123")
        assert not pattern.search("Production-East")


# ===================================================================
# Coverage boost: standalone helpers & instance methods
# ===================================================================


class TestComputeVariablePlan:
    """_compute_variable_plan with various cache shapes."""

    def test_no_deviations_returns_empty(self) -> None:
        cache: dict[str, object] = {"deviations": [], "matrix": []}
        assert _compute_variable_plan(cache) == []

    def test_skips_psk_and_anomaly_rows(self) -> None:
        cache: dict[str, object] = {
            "deviations": [
                {"cluster_name": "East", "parameter": "vlan_id"},
            ],
            "matrix": [
                {"site_name": "S1", "site_id": "s1", "psk_detected": True},
                {"site_name": "S2", "site_id": "s2", "anomaly": True, "anomaly_reason": "no template"},
            ],
            "data": {"sites": []},
        }
        plan = _compute_variable_plan(cache)
        assert len(plan) == 2
        assert all(e["status"] == "skipped" for e in plan)

    def test_pending_entry_for_normal_row(self) -> None:
        cache: dict[str, object] = {
            "deviations": [
                {"cluster_name": "East", "parameter": "vlan_id"},
            ],
            "matrix": [
                {"site_name": "S1", "site_id": "s1"},
            ],
            "data": {"sites": [{"id": "s1", "vars": {}}]},
        }
        plan = _compute_variable_plan(cache)
        assert len(plan) == 1
        assert plan[0]["status"] == "pending"
        assert "VLAN_ID" in plan[0]["variable_name"]


class TestExtractDeviationParams:
    """_extract_deviation_params edge cases."""

    def test_excludes_cross_cluster(self) -> None:
        devs = [
            {"cluster_name": "East", "parameter": "vlan_id"},
            {"cluster_name": "cross_cluster", "parameter": "auth"},
        ]
        result = _extract_deviation_params(devs)
        assert result == ["vlan_id"]

    def test_empty_params_filtered(self) -> None:
        devs = [{"cluster_name": "East", "parameter": ""}]
        assert _extract_deviation_params(devs) == []


class TestBuildSkipEntry:
    """_build_skip_entry coverage."""

    def test_psk_reason(self) -> None:
        row = {"site_name": "S1", "site_id": "s1", "psk_detected": True}
        entry = _build_skip_entry(row, "vlan_id")
        assert entry["status"] == "skipped"
        assert "PSK" in entry["reason"]

    def test_anomaly_reason(self) -> None:
        row = {"site_name": "S1", "site_id": "s1", "anomaly_reason": "no template"}
        entry = _build_skip_entry(row, "vlan_id")
        assert "Anomaly" in entry["reason"]


class TestGetCachedSiteVars:
    """_get_cached_site_vars coverage."""

    def test_returns_vars(self) -> None:
        cache: dict[str, object] = {
            "data": {"sites": [{"id": "s1", "vars": {"FOO": "bar"}}]},
        }
        result = _get_cached_site_vars(cache, "s1")
        assert result == {"FOO": "bar"}

    def test_returns_empty_on_miss(self) -> None:
        cache: dict[str, object] = {"data": {"sites": []}}
        assert _get_cached_site_vars(cache, "s1") == {}


class TestBuildVariableEntry:
    """_build_variable_entry coverage."""

    def test_already_configured(self) -> None:
        row = {"site_name": "S1", "site_id": "s1", "vlan_id": "100"}
        entry = _build_variable_entry(
            row,
            "vlan_id",
            {"MISTHELPER_VLAN_ID": "100"},
        )
        assert entry["status"] == "already_configured"

    def test_conflict(self) -> None:
        row = {"site_name": "S1", "site_id": "s1", "vlan_id": "100"}
        entry = _build_variable_entry(
            row,
            "vlan_id",
            {"MISTHELPER_VLAN_ID": "200"},
        )
        assert entry["status"] == "conflict"

    def test_pending(self) -> None:
        row = {"site_name": "S1", "site_id": "s1", "vlan_id": "100"}
        entry = _build_variable_entry(row, "vlan_id", {})
        assert entry["status"] == "pending"


class TestComputeGroupPlan:
    """_compute_group_plan coverage."""

    def test_creates_cluster_groups(self) -> None:
        cache: dict[str, object] = {
            "data": {
                "mxtunnels": [{"id": "t1", "name": "East"}],
                "sitegroups": [],
            },
            "matrix": [
                {"target_group": "East", "site_id": "s1", "site_name": "S1"},
            ],
        }
        plan = _compute_group_plan(cache)
        names = [g["group_name"] for g in plan["groups"]]
        assert "misthelper_prod_East" in names
        assert "misthelper_pilot" in names


class TestAssignMatrixSites:
    """_assign_matrix_sites coverage."""

    def test_assigns_production_sites(self) -> None:
        matrix = [
            {"target_group": "East", "site_id": "s1", "site_name": "S1"},
        ]
        group_map: dict[str, dict[str, object]] = {
            "misthelper_prod_East": {
                "group_name": "misthelper_prod_East",
                "sites": [],
            },
        }
        _assign_matrix_sites(matrix, group_map)
        assert len(group_map["misthelper_prod_East"]["sites"]) == 1

    def test_assigns_pilot_sites(self) -> None:
        matrix = [
            {"target_group": "pilot", "site_id": "s1", "site_name": "P1"},
        ]
        group_map: dict[str, dict[str, object]] = {
            "misthelper_pilot": {
                "group_name": "misthelper_pilot",
                "sites": [],
            },
        }
        _assign_matrix_sites(matrix, group_map)
        assert len(group_map["misthelper_pilot"]["sites"]) == 1

    def test_skips_psk_and_anomaly(self) -> None:
        matrix = [
            {"target_group": "East", "psk_detected": True},
            {"target_group": "East", "anomaly": True},
        ]
        group_map: dict[str, dict[str, object]] = {
            "misthelper_prod_East": {"sites": []},
        }
        _assign_matrix_sites(matrix, group_map)
        assert group_map["misthelper_prod_East"]["sites"] == []


class TestPopulateFromRepresentative:
    """_populate_from_representative coverage."""

    def test_with_vlan_deviation(self) -> None:
        config: dict[str, object] = {}
        rep = {"vlan_id": "100", "auth_type": "psk", "mxtunnel_id": "t1"}
        _populate_from_representative(config, rep, {"vlan_id"})
        assert config["vlan_id"] == "{{MISTHELPER_VLAN_ID}}"
        assert config["mxtunnel_ids"] == ["t1"]

    def test_without_deviation(self) -> None:
        config: dict[str, object] = {}
        rep = {"vlan_id": "100", "auth_type": "psk", "mxtunnel_id": ""}
        _populate_from_representative(config, rep, set())
        assert config["vlan_id"] == "100"
        assert "mxtunnel_ids" not in config


class TestLoadGroupPlanFromResultsExtra:
    """_load_group_plan_from_results coverage."""

    def test_extracts_group_map(self) -> None:
        phase3 = {
            "results": [
                {"group_name": "G1", "group_id": "g1", "cluster_name": "East"},
                {"group_name": "G1", "group_id": "g1", "cluster_name": "East"},
                {"group_name": "G2", "group_id": "g2", "cluster_name": "West"},
            ],
        }
        result = _load_group_plan_from_results(phase3)
        assert len(result) == 2
        assert result["G1"]["group_id"] == "g1"


class TestBuildAllTemplateConfigs:
    """_build_all_template_configs coverage."""

    def test_builds_config_per_group(self) -> None:
        group_plan = {
            "East": {"group_id": "g1", "cluster_name": "East"},
        }
        cache: dict[str, object] = {
            "deviations": [],
            "matrix": [
                {"target_group": "East", "site_id": "s1", "vlan_id": "100", "auth_type": "psk"},
            ],
        }
        configs = _build_all_template_configs(
            group_plan,
            {},
            cache,
            "Corp",
        )
        assert "East" in configs
        assert configs["East"]["ssid"] == "Corp"


class TestFindRepresentative:
    """_find_representative coverage."""

    def test_finds_matching_cluster(self) -> None:
        cache: dict[str, object] = {
            "matrix": [
                {"target_group": "East", "site_id": "s1"},
            ],
        }
        result = _find_representative(cache, "East")
        assert result is not None
        assert result["site_id"] == "s1"

    def test_falls_back_to_pilot(self) -> None:
        cache: dict[str, object] = {
            "matrix": [
                {"target_group": "pilot", "site_id": "p1"},
            ],
        }
        result = _find_representative(cache, "West")
        assert result is not None
        assert result["site_id"] == "p1"

    def test_returns_none_when_empty(self) -> None:
        cache: dict[str, object] = {"matrix": []}
        assert _find_representative(cache, "East") is None


class TestCreateSiteGroupExtra:
    """_create_site_group with API mock."""

    def test_creates_group_successfully(self) -> None:
        group: dict[str, object] = {
            "group_name": "G1",
            "group_id": "",
            "exists": False,
        }
        mock_resp = MagicMock()
        mock_resp.data = {"id": "new-g1"}
        with patch.object(
            _mod.mistapi.api.v1.orgs.sitegroups,
            "createOrgSiteGroup",
            return_value=mock_resp,
        ):
            _mod._create_site_group(group, "org-1", MagicMock())
        assert group["group_id"] == "new-g1"
        assert group["exists"] is True

    def test_handles_api_error(self) -> None:
        group: dict[str, object] = {
            "group_name": "G1",
            "group_id": "",
            "exists": False,
        }
        with patch.object(_mod, "mistapi") as mock_api:
            mock_api.api.v1.orgs.sitegroups.createOrgSiteGroup.side_effect = RuntimeError("fail")
            _mod._create_site_group(group, "org-1", MagicMock())
        assert group["exists"] is False


class TestDisplayFunctions:
    """Cover display/print functions for coverage (output-only)."""

    def test_display_variable_summary(self) -> None:
        plan = [
            {"status": "pending", "site_name": "S1"},
            {"status": "skipped", "site_name": "S2"},
            {"status": "already_configured", "site_name": "S3"},
            {
                "status": "conflict",
                "site_name": "S4",
                "variable_name": "V",
                "current_value": "1",
                "proposed_value": "2",
            },
        ]
        _display_variable_summary(plan)

    def test_print_conflicts_truncates(self) -> None:
        conflicts = [
            {"site_name": f"S{i}", "variable_name": "V", "current_value": "1", "proposed_value": "2"} for i in range(15)
        ]
        _print_conflicts(conflicts)

    def test_display_group_plan(self) -> None:
        plan = {
            "groups": [
                {"group_name": "G1", "exists": True, "sites": [{"site_name": f"S{i}"} for i in range(7)]},
            ],
        }
        _display_group_plan(plan)

    def test_display_template_plan(self) -> None:
        configs = {"East": {"ssid": "Corp", "vlan_id": "100"}}
        group_plan = {"East": {"group_id": "g1"}}
        _display_template_plan(configs, group_plan)

    def test_display_disable_plan(self) -> None:
        plan = [
            {"status": "to_disable", "site_name": "S1", "ssid_name": "Corp"},
            {"status": "skipped", "site_name": "S2", "ssid_name": "Corp", "reason": "PSK"},
        ]
        _display_disable_plan(plan)

    def test_print_phase_summary(self) -> None:
        results = [
            {"status": "written"},
            {"status": "failed"},
            {"status": "skipped"},
        ]
        _print_phase_summary("Phase 2", results)


class TestGroupEntriesBySite:
    """_group_entries_by_site coverage."""

    def test_groups_correctly(self) -> None:
        entries = [
            {"site_id": "s1", "var": "a"},
            {"site_id": "s1", "var": "b"},
            {"site_id": "s2", "var": "c"},
        ]
        groups = _group_entries_by_site(entries)
        assert len(groups["s1"]) == 2
        assert len(groups["s2"]) == 1


class TestInstanceMethods:
    """Cover instance methods of SSIDTemplateConsolidationManager."""

    def _make_manager(self, **kwargs: object) -> SSIDTemplateConsolidationManager:
        defaults = {
            "org_id": "org-1",
            "target_ssid": "Corp",
            "apisession": MagicMock(),
            "page_limit": 100,
            "safe_input_fn": MagicMock(return_value=""),
            "write_data_fn": MagicMock(),
        }
        defaults.update(kwargs)
        return SSIDTemplateConsolidationManager(SsidTemplateDeps(**defaults))  # type: ignore[arg-type]

    def test_check_prerequisite_phase1(self) -> None:
        mgr = self._make_manager()
        assert mgr._check_prerequisite(1) is True

    def test_check_prerequisite_phase2_no_cache(self) -> None:
        mgr = self._make_manager()
        with patch.object(
            _mod,
            "_check_cache_exists",
            return_value=False,
        ):
            assert mgr._check_prerequisite(2) is False

    def test_check_prerequisite_phase3_missing_file(self) -> None:
        mgr = self._make_manager()
        with patch("os.path.exists", return_value=False):
            assert mgr._check_prerequisite(3) is False

    def test_confirm_or_cancel_confirmed(self) -> None:
        mgr = self._make_manager(
            safe_input_fn=MagicMock(return_value="CONFIRM"),
        )
        assert mgr._confirm_or_cancel("Test?") is True

    def test_confirm_or_cancel_declined(self) -> None:
        mgr = self._make_manager(
            safe_input_fn=MagicMock(return_value="no"),
        )
        assert mgr._confirm_or_cancel("Test?") is False

    def test_save_cache_writes_json(self) -> None:
        mgr = self._make_manager()
        m = mock_open()
        with patch("builtins.open", m):
            mgr._save_cache({"data": {}})
        m.assert_called_once()

    def test_save_cache_handles_oserror(self) -> None:
        mgr = self._make_manager()
        with patch("builtins.open", side_effect=OSError("disk full")):
            mgr._save_cache({"data": {}})

    def test_save_phase_results_no_file(self) -> None:
        mgr = self._make_manager()
        mgr._save_phase_results(99, [])

    def test_save_phase_results_writes(self) -> None:
        mgr = self._make_manager()
        m = mock_open()
        with patch("builtins.open", m):
            mgr._save_phase_results(2, [{"status": "written"}])
        m.assert_called_once()

    def test_save_phase_results_oserror(self) -> None:
        mgr = self._make_manager()
        with patch("builtins.open", side_effect=OSError("fail")):
            mgr._save_phase_results(2, [])

    def test_load_cache_missing_file(self) -> None:
        mgr = self._make_manager()
        with patch("os.path.exists", return_value=False):
            assert mgr._load_cache() is None

    def test_load_cache_valid_fresh(self) -> None:
        mgr = self._make_manager()
        cache_data = {
            "collected_at": datetime.now().isoformat(),
            "data": {"sites": []},
        }
        with (
            patch("os.path.exists", return_value=True),
            patch(
                "builtins.open",
                mock_open(
                    read_data=json.dumps(cache_data),
                ),
            ),
        ):
            result = mgr._load_cache()
        assert result is not None

    def test_load_cache_corrupt(self) -> None:
        mgr = self._make_manager()
        with patch("os.path.exists", return_value=True), patch("builtins.open", mock_open(read_data="not json")):
            assert mgr._load_cache() is None

    def test_run_all_phases_stops_on_prereq(self) -> None:
        mgr = self._make_manager()
        dispatch = {"1": MagicMock(), "2": MagicMock()}
        with patch.object(
            _mod,
            "_check_prerequisite_for_all",
            return_value=False,
        ):
            mgr._run_all_phases(dispatch)
        dispatch["1"].assert_not_called()

    def test_run_all_phases_stops_on_error(self) -> None:
        mgr = self._make_manager()
        phase1 = MagicMock(side_effect=RuntimeError("boom"))
        dispatch = {
            "1": phase1,
            "2": MagicMock(),
            "3": MagicMock(),
            "4": MagicMock(),
            "5": MagicMock(),
        }
        with patch.object(
            _mod,
            "_check_prerequisite_for_all",
            return_value=True,
        ):
            mgr._run_all_phases(dispatch)
        dispatch["2"].assert_not_called()

    def test_run_all_phases_completes(self) -> None:
        mgr = self._make_manager()
        dispatch = {str(i): MagicMock() for i in range(1, 6)}
        with patch.object(
            _mod,
            "_check_prerequisite_for_all",
            return_value=True,
        ):
            mgr._run_all_phases(dispatch)
        for fn in dispatch.values():
            fn.assert_called_once()

    def test_execute_no_org_id(self) -> None:
        SSIDTemplateConsolidationManager.execute(
            apisession=MagicMock(),
            page_limit=100,
            safe_input_fn=MagicMock(),
            write_data_fn=MagicMock(),
            get_org_id_fn=MagicMock(return_value=None),
        )

    def test_execute_no_ssid(self) -> None:
        SSIDTemplateConsolidationManager.execute(
            apisession=MagicMock(),
            page_limit=100,
            safe_input_fn=MagicMock(return_value=""),
            write_data_fn=MagicMock(),
            get_org_id_fn=MagicMock(return_value="org-1"),
        )

    def test_run_phase_menu_quit(self) -> None:
        mgr = self._make_manager(
            safe_input_fn=MagicMock(return_value="q"),
        )
        mgr.run_phase_menu()

    def test_run_phase_menu_invalid_then_quit(self) -> None:
        mock_input = MagicMock(side_effect=["99", "q"])
        mgr = self._make_manager(safe_input_fn=mock_input)
        mgr.run_phase_menu()

    def test_run_phase_menu_select_phase(self) -> None:
        mock_input = MagicMock(side_effect=["1", "q"])
        mgr = self._make_manager(safe_input_fn=mock_input)
        with patch.object(mgr, "phase1_audit"):
            mgr.run_phase_menu()

    def test_run_phase_menu_run_all(self) -> None:
        mock_input = MagicMock(return_value="6")
        mgr = self._make_manager(safe_input_fn=mock_input)
        with patch.object(mgr, "_run_all_phases"):
            mgr.run_phase_menu()


class TestHandleResumeHelpers:
    """_handle_completed_resume and _handle_partial_resume."""

    def test_completed_rerun(self) -> None:
        mock_input = MagicMock(return_value="y")
        resuming, results = _handle_completed_resume(
            2,
            5,
            5,
            mock_input,
        )
        assert resuming is False
        assert results == []

    def test_completed_skip(self) -> None:
        mock_input = MagicMock(return_value="n")
        resuming, results = _handle_completed_resume(
            2,
            5,
            5,
            mock_input,
        )
        assert resuming is True

    def test_partial_resume(self) -> None:
        mock_input = MagicMock(return_value="Y")
        prior = [{"status": "written"}]
        resuming, results = _handle_partial_resume(
            2,
            1,
            5,
            prior,
            mock_input,
        )
        assert resuming is True
        assert results == prior

    def test_partial_restart(self) -> None:
        mock_input = MagicMock(return_value="n")
        resuming, results = _handle_partial_resume(
            2,
            1,
            5,
            [{"status": "written"}],
            mock_input,
        )
        assert resuming is False
        assert results == []


class TestBuildTemplateConfig:
    """_build_template_config coverage."""

    def test_with_deviations_and_representative(self) -> None:
        cache: dict[str, object] = {
            "deviations": [
                {"cluster_name": "East", "parameter": "vlan_id"},
                {"cluster_name": "East", "parameter": "auth_type"},
            ],
            "matrix": [
                {"target_group": "East", "site_id": "s1", "vlan_id": "100", "auth_type": "psk", "mxtunnel_id": ""},
            ],
        }
        config = _build_template_config("East", {}, cache, "Corp")
        assert config["ssid"] == "Corp"
        assert config["vlan_id"] == "{{MISTHELPER_VLAN_ID}}"

    def test_no_representative(self) -> None:
        cache: dict[str, object] = {
            "deviations": [],
            "matrix": [],
        }
        config = _build_template_config("East", {}, cache, "Corp")
        assert config["ssid"] == "Corp"
        assert "vlan_id" not in config


# ===================================================================
# Final coverage boost: uncovered paths
# ===================================================================


class TestClassifyDisableEntryExtra:
    """Extra _classify_disable_entry coverage for uncovered branches."""

    def test_already_disabled(self) -> None:
        row: dict[str, object] = {
            "ssid_enabled": False,
            "site_name": "S1",
            "site_id": "s1",
            "ssid_name": "Corp",
            "ssid_id": "w1",
            "old_template_id": "t1",
        }
        result = _classify_disable_entry(row)
        assert result["status"] == "already_disabled"

    def test_no_ssid_id(self) -> None:
        row: dict[str, object] = {
            "site_name": "S1",
            "site_id": "s1",
            "ssid_name": "Corp",
            "ssid_id": "",
            "old_template_id": "t1",
            "ssid_enabled": True,
        }
        result = _classify_disable_entry(row)
        assert result["status"] == "skipped"
        assert "No SSID ID" in result["reason"]


class TestBuildSiteRowEmpty:
    """_build_site_row with empty site_id returns None."""

    def test_returns_none_for_empty_id(self) -> None:
        site: dict[str, object] = {"id": "", "name": "S1"}
        result = _build_site_row(
            site,
            "Corp",
            ("psk",),
            re.compile(r"pilot|test|lab", re.IGNORECASE),
            _SiteLookups(template_lookup={}, sitegroup_lookup={}, mxtunnel_lookup={}),
        )
        assert result is None


class TestResolveSingleDeviationManySites:
    """_resolve_single_deviation with >3 sites display."""

    def test_many_sites_truncated(self) -> None:
        deviation: dict[str, object] = {
            "cluster_name": "East",
            "parameter": "vlan_id",
            "unique_values": json.dumps(
                [
                    {
                        "value": 100,
                        "sites": ["A", "B", "C", "D", "E"],
                        "count": 5,
                    },
                ]
            ),
        }
        resolutions: dict[tuple[str, str], object] = {}
        mock_input = MagicMock(return_value="1")
        _mod._resolve_single_deviation(
            deviation,
            resolutions,
            mock_input,
        )
        assert resolutions[("East", "vlan_id")] == 100


class TestPhaseOrchestratorsCoverage:
    """Cover phase orchestrator instance methods."""

    def _make_manager(
        self,
        **kwargs: object,
    ) -> SSIDTemplateConsolidationManager:
        defaults: dict[str, object] = {
            "org_id": "org-1",
            "target_ssid": "Corp",
            "apisession": MagicMock(),
            "page_limit": 100,
            "safe_input_fn": MagicMock(return_value=""),
            "write_data_fn": MagicMock(),
        }
        defaults.update(kwargs)
        return SSIDTemplateConsolidationManager(SsidTemplateDeps(**defaults))  # type: ignore[arg-type]

    def test_phase1_no_data(self) -> None:
        mgr = self._make_manager()
        with patch.object(
            mgr,
            "_phase1_load_or_fetch",
            return_value=None,
        ):
            mgr.phase1_audit()

    def test_phase1_success(self) -> None:
        mgr = self._make_manager()
        org_data: dict[str, object] = {
            "wlan_templates": [],
            "sites": [],
            "mxtunnels": [],
            "sitegroups": [],
            "wlans": [],
        }
        with (
            patch.object(
                mgr,
                "_phase1_load_or_fetch",
                return_value=org_data,
            ),
            patch.object(mgr, "_build_matrix", return_value=[]),
            patch.object(
                mgr,
                "_analyze_deviations",
                return_value=[],
            ),
            patch.object(mgr, "_phase1_save_and_report"),
        ):
            mgr.phase1_audit()

    def test_phase2_no_cache(self) -> None:
        mgr = self._make_manager()
        with patch.object(mgr, "_load_cache", return_value=None):
            mgr.phase2_site_variables()

    def test_phase2_no_plan(self) -> None:
        mgr = self._make_manager()
        cache: dict[str, object] = {
            "deviations": [],
            "matrix": [],
        }
        with (
            patch.object(mgr, "_load_cache", return_value=cache),
            patch.object(
                mgr,
                "_offer_resume",
                return_value=(False, []),
            ),
        ):
            mgr.phase2_site_variables()

    def test_phase3_no_cache(self) -> None:
        mgr = self._make_manager()
        with patch.object(mgr, "_load_cache", return_value=None):
            mgr.phase3_site_groups()

    def test_phase4_no_cache(self) -> None:
        mgr = self._make_manager()
        with patch.object(mgr, "_load_cache", return_value=None):
            mgr.phase4_templates()

    def test_phase4_no_phase3(self) -> None:
        mgr = self._make_manager()
        cache: dict[str, object] = {
            "data": {},
            "deviations": [],
            "matrix": [],
        }
        with (
            patch.object(mgr, "_load_cache", return_value=cache),
            patch.object(
                mgr,
                "_load_phase_results",
                return_value=None,
            ),
        ):
            mgr.phase4_templates()

    def test_phase5_no_cache(self) -> None:
        mgr = self._make_manager()
        with patch.object(mgr, "_load_cache", return_value=None):
            mgr.phase5_disable_old()

    def test_phase5_nothing_to_disable(self) -> None:
        mgr = self._make_manager()
        cache: dict[str, object] = {
            "matrix": [
                {
                    "psk_detected": True,
                    "site_name": "S1",
                    "site_id": "s1",
                    "ssid_name": "Corp",
                    "ssid_id": "",
                    "old_template_id": "t1",
                },
            ],
        }
        with (
            patch.object(mgr, "_load_cache", return_value=cache),
            patch.object(
                mgr,
                "_offer_resume",
                return_value=(False, []),
            ),
        ):
            mgr.phase5_disable_old()

    def test_phase1_save_and_report(self) -> None:
        mgr = self._make_manager()
        with patch.object(mgr, "_save_cache"):
            mgr._phase1_save_and_report(
                {"wlan_templates": []},
                [{"site": "A"}],
                [{"dev": "B"}],
            )
        assert mgr.write_data_fn.call_count == 2

    def test_phase1_load_cached(self) -> None:
        mgr = self._make_manager(
            safe_input_fn=MagicMock(return_value="Y"),
        )
        cached: dict[str, object] = {
            "collected_at": datetime.now(
                tz=UTC,
            ).isoformat(),
            "data": {"sites": []},
        }
        with patch.object(mgr, "_load_cache", return_value=cached):
            result = mgr._phase1_load_or_fetch()
        assert result == {"sites": []}

    def test_phase1_load_no_cache(self) -> None:
        mgr = self._make_manager()
        with (
            patch.object(mgr, "_load_cache", return_value=None),
            patch.object(
                mgr,
                "_fetch_all_org_data",
                return_value={"sites": []},
            ),
        ):
            result = mgr._phase1_load_or_fetch()
        assert result == {"sites": []}

    def test_analyze_deviations(self) -> None:
        mgr = self._make_manager()
        matrix = [
            {"target_group": "East", "site_id": "s1"},
        ]
        org_data: dict[str, object] = {"wlan_templates": []}
        result = mgr._analyze_deviations(matrix, org_data)
        assert isinstance(result, list)

    def test_ensure_groups_exist_skips_existing(self) -> None:
        mgr = self._make_manager()
        plan: dict[str, object] = {
            "groups": [
                {
                    "group_name": "G1",
                    "group_id": "g1",
                    "exists": True,
                },
            ],
        }
        result = mgr._ensure_groups_exist(plan)
        assert result is plan

    def test_assign_sites_to_groups(self) -> None:
        mgr = self._make_manager()
        mgr.cache = {"data": {"sitegroups": []}}
        plan: dict[str, object] = {
            "groups": [
                {
                    "group_name": "G1",
                    "group_id": "g1",
                    "cluster_name": "East",
                    "sites": [
                        {"site_id": "s1", "site_name": "A"},
                    ],
                },
            ],
        }
        with patch.object(_mod, "mistapi") as mock_api:
            mock_api.api.v1.orgs.sitegroups.updateOrgSiteGroup.return_value = MagicMock()
            results = mgr._assign_sites_to_groups(plan, [])
        assert len(results) >= 1

    def test_write_site_variables_empty_plan(self) -> None:
        mgr = self._make_manager()
        mgr.cache = {"data": {"sites": []}}
        results = mgr._write_site_variables([], [])
        assert results == []

    def test_disable_ssids_skips_non_disable(self) -> None:
        mgr = self._make_manager()
        plan = [
            {
                "status": "skipped",
                "site_name": "S1",
                "site_id": "s1",
                "ssid_id": "",
                "old_template_id": "t1",
            },
        ]
        results = mgr._disable_ssids(plan, [])
        assert len(results) == 1
        assert results[0]["status"] == "skipped"
