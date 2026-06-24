"""Tests for src.firmware.site_auto_upgrade -- SiteAutoUpgradeConfigurator.

Covers: parse_time_input, _parse_hour_minute, _apply_ampm,
_parse_index_selection, _build_auto_upgrade_payload,
_group_models_by_family, _get_family_versions,
_get_current_family_version, _extract_version_strings,
_compute_msp_totals, _print_msp_failed_orgs,
_collect_family_versions, _group_models_for_msp,
_build_version_map_from_list, _apply_version_to_models,
_apply_family_selection, _display_family_versions,
_display_step6_summary, _print_final_summary,
SiteAutoUpgradeConfigurator.__init__, execute, run, run_msp_mode,
and MSP workflow helpers.
"""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest

# Mock mistapi before importing the module under test
_mock_mistapi = MagicMock()
with patch.dict(
    sys.modules,
    {
        "mistapi": _mock_mistapi,
        "mistapi.api": MagicMock(),
        "mistapi.api.v1": MagicMock(),
        "mistapi.api.v1.orgs": MagicMock(),
        "mistapi.api.v1.orgs.devices": MagicMock(),
        "mistapi.api.v1.orgs.sites": MagicMock(),
        "mistapi.api.v1.sites": MagicMock(),
        "mistapi.api.v1.sites.setting": MagicMock(),
    },
):
    import src.firmware.site_auto_upgrade as _sau_mod
    from src.firmware.site_auto_upgrade import (
        SiteAutoUpgradeConfigurator,
        _apply_ampm,
        _apply_family_selection,
        _apply_version_to_models,
        _build_auto_upgrade_payload,
        _build_version_map_from_list,
        _collect_family_versions,
        _compute_msp_totals,
        _display_family_versions,
        _display_msp_family_versions,
        _display_step6_summary,
        _extract_version_strings,
        _get_current_family_version,
        _get_family_versions,
        _group_models_by_family,
        _group_models_for_msp,
        _parse_hour_minute,
        _parse_index_selection,
        _print_final_summary,
        _print_msp_failed_orgs,
        _print_msp_summary,
        parse_time_input,
    )

# Issue #433 Phase B introduced SiteAutoUpgradeCoreDeps / SiteAutoUpgradeMspDeps
# to keep helper signatures under the 5-Item Rule. Tests build them via the
# two helpers below so the existing per-kwarg test style stays readable.
from dataclasses import replace

from src.dataclasses.family_selection_context import FamilySelectionContext  # Phase B refactor.
from src.dataclasses.site_auto_upgrade_deps import SiteAutoUpgradeCoreDeps, SiteAutoUpgradeMspDeps


def _make_core(
    *,
    apisession=None,
    safe_input_fn=None,
    fetch_sites_fn=None,
    check_stop_fn=None,
    dry_run=False,
    **_ignored,
):
    """Build a SiteAutoUpgradeCoreDeps from per-kwarg test inputs."""
    return SiteAutoUpgradeCoreDeps(
        apisession=apisession if apisession is not None else MagicMock(),
        safe_input_fn=safe_input_fn if safe_input_fn is not None else MagicMock(),
        fetch_sites_fn=fetch_sites_fn if fetch_sites_fn is not None else MagicMock(),
        check_stop_fn=check_stop_fn if check_stop_fn is not None else MagicMock(),
        dry_run=dry_run,
    )


def _make_msp(*, select_msps_fn=None, select_orgs_fn=None, **_ignored):
    """Build a SiteAutoUpgradeMspDeps from per-kwarg test inputs."""
    return SiteAutoUpgradeMspDeps(
        select_msps_fn=select_msps_fn,
        select_orgs_fn=select_orgs_fn,
    )


# ===================================================================
# Helpers
# ===================================================================


def _mist_modules(**overrides):
    """Build full mistapi sys.modules dict with optional overrides.

    Builds a connected hierarchy so that attribute access matches
    sys.modules entries (required by Python's import system).
    """
    mock_devices = overrides.pop("mistapi.api.v1.orgs.devices", MagicMock())
    mock_orgs_sites = overrides.pop("mistapi.api.v1.orgs.sites", MagicMock())
    mock_site_setting = overrides.pop("mistapi.api.v1.sites.setting", MagicMock())

    mock_v1_orgs = MagicMock()
    mock_v1_orgs.devices = mock_devices
    mock_v1_orgs.sites = mock_orgs_sites

    mock_v1_sites = MagicMock()
    mock_v1_sites.setting = mock_site_setting

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
        "mistapi.api.v1.orgs.devices": mock_devices,
        "mistapi.api.v1.orgs.sites": mock_orgs_sites,
        "mistapi.api.v1.sites": mock_v1_sites,
        "mistapi.api.v1.sites.setting": mock_site_setting,
    }


# ===================================================================
# Fixtures
# ===================================================================


@pytest.fixture()
def mock_deps():
    """Return a dict whose ``deps`` value is the new SiteAutoUpgradeCoreDeps bundle.

    Tests using ``**mock_deps`` keep working unchanged because the
    SiteAutoUpgradeConfigurator now expects exactly one DI kwarg: ``deps``.
    Tests that previously read individual mocks (e.g. ``mock_deps["apisession"]``)
    keep working because the per-component mocks are also returned alongside
    for backwards compatibility.
    """
    apisession = MagicMock()  # Authenticated mistapi session for API calls.
    safe_input_fn = MagicMock(return_value="")  # Default prompt response is "" (empty/Enter).
    fetch_sites_fn = MagicMock(return_value=[])  # Default to an empty site list.
    check_stop_fn = MagicMock(return_value=False)  # Default to "no stop signal".
    deps = SiteAutoUpgradeCoreDeps(  # Build the new DI dataclass once per test.
        apisession=apisession,
        safe_input_fn=safe_input_fn,
        fetch_sites_fn=fetch_sites_fn,
        check_stop_fn=check_stop_fn,
        dry_run=False,
    )
    return {
        "deps": deps,  # Primary key consumed by `**mock_deps` splats in test ctors.
        "apisession": apisession,  # Kept for tests that still inspect the per-component mock.
        "safe_input_fn": safe_input_fn,  # Same: backwards-compat for older tests.
        "fetch_sites_fn": fetch_sites_fn,  # Same: backwards-compat for older tests.
        "check_stop_fn": check_stop_fn,  # Same: backwards-compat for older tests.
    }


@pytest.fixture()
def configurator(mock_deps):
    """Create a SiteAutoUpgradeConfigurator with mock deps."""
    return SiteAutoUpgradeConfigurator(
        org_id="org-123",
        deps=mock_deps["deps"],  # Issue #433 Phase B: new single-deps DI signature.
    )


# ===================================================================
# parse_time_input
# ===================================================================


class TestParseTimeInput:
    """Tests for the public parse_time_input function."""

    def test_empty_string(self):
        assert parse_time_input("") == "any"

    def test_standard_24h(self):
        assert parse_time_input("02:00") == "02:00"

    def test_24h_no_leading_zero(self):
        assert parse_time_input("2:00") == "02:00"

    def test_14_hours(self):
        assert parse_time_input("14:00") == "14:00"

    def test_2am(self):
        assert parse_time_input("2AM") == "02:00"

    def test_2pm(self):
        assert parse_time_input("2PM") == "14:00"

    def test_12am_is_midnight(self):
        assert parse_time_input("12AM") == "00:00"

    def test_12pm_is_noon(self):
        assert parse_time_input("12PM") == "12:00"

    def test_with_minutes_am(self):
        assert parse_time_input("02:30AM") == "02:30"

    def test_with_minutes_pm(self):
        assert parse_time_input("02:30PM") == "14:30"

    def test_invalid_returns_any(self):
        assert parse_time_input("abc") == "any"

    def test_out_of_range_hour(self):
        assert parse_time_input("25:00") == "any"

    def test_out_of_range_minute(self):
        assert parse_time_input("12:60") == "any"

    def test_lowercase_am(self):
        assert parse_time_input("3am") == "03:00"

    def test_midnight_24h(self):
        assert parse_time_input("0:00") == "00:00"

    def test_23_59(self):
        assert parse_time_input("23:59") == "23:59"


# ===================================================================
# _parse_hour_minute
# ===================================================================


class TestParseHourMinute:
    """Tests for _parse_hour_minute helper."""

    def test_colon_format(self):
        assert _parse_hour_minute("02:30") == (2, 30)

    def test_hour_only(self):
        assert _parse_hour_minute("14") == (14, 0)

    def test_invalid_returns_negative(self):
        assert _parse_hour_minute("abc") == (-1, 0)

    def test_colon_invalid_parts(self):
        assert _parse_hour_minute("ab:cd") == (-1, 0)

    def test_colon_hour_only(self):
        # "5:" splits to ["5", ""], int("") raises ValueError
        assert _parse_hour_minute("5:") == (-1, 0)


# ===================================================================
# _apply_ampm
# ===================================================================


class TestApplyAmpm:
    """Tests for _apply_ampm helper."""

    def test_pm_adds_12(self):
        assert _apply_ampm(2, is_am=False, is_pm=True) == 14

    def test_pm_noon_stays(self):
        assert _apply_ampm(12, is_am=False, is_pm=True) == 12

    def test_am_midnight(self):
        assert _apply_ampm(12, is_am=True, is_pm=False) == 0

    def test_am_normal(self):
        assert _apply_ampm(3, is_am=True, is_pm=False) == 3

    def test_no_ampm(self):
        assert _apply_ampm(15, is_am=False, is_pm=False) == 15


# ===================================================================
# _parse_index_selection
# ===================================================================


class TestParseIndexSelection:
    """Tests for _parse_index_selection."""

    def test_single_index(self):
        assert _parse_index_selection("3") == [3]

    def test_comma_separated(self):
        assert _parse_index_selection("1,3,5") == [1, 3, 5]

    def test_range(self):
        assert _parse_index_selection("1-3") == [1, 2, 3]

    def test_mixed(self):
        assert _parse_index_selection("1,3-5,7") == [1, 3, 4, 5, 7]

    def test_spaces(self):
        assert _parse_index_selection("1, 3, 5") == [1, 3, 5]

    def test_invalid_ignored(self):
        assert _parse_index_selection("1,abc,3") == [1, 3]

    def test_empty(self):
        assert _parse_index_selection("") == []

    def test_duplicates_removed(self):
        assert _parse_index_selection("1,1,2,2") == [1, 2]


# ===================================================================
# _build_auto_upgrade_payload
# ===================================================================


class TestBuildAutoUpgradePayload:
    """Tests for _build_auto_upgrade_payload."""

    def test_basic_payload(self):
        result = _build_auto_upgrade_payload(
            custom_versions={"AP41": "0.14.123"},
            schedule={"day_of_week": "mon", "time_of_day": "02:00"},
        )
        assert result["enabled"] is True
        assert result["version"] == "custom"
        assert result["custom_versions"] == {"AP41": "0.14.123"}
        assert result["day_of_week"] == "mon"
        assert result["time_of_day"] == "02:00"

    def test_defaults_any(self):
        result = _build_auto_upgrade_payload(
            custom_versions={},
            schedule={},
        )
        assert result["day_of_week"] == "any"
        assert result["time_of_day"] == "any"


# ===================================================================
# _group_models_by_family
# ===================================================================


class TestGroupModelsByFamily:
    """Tests for _group_models_by_family."""

    def test_groups_by_prefix(self):
        version_map = {
            "AP41": [{"version": "1.0"}],
            "AP41E": [{"version": "1.0"}],
            "AP43": [{"version": "2.0"}],
        }
        result = _group_models_by_family(version_map)
        assert "AP41" in result
        assert set(result["AP41"]) == {"AP41", "AP41E"}
        assert result["AP43"] == ["AP43"]

    def test_empty(self):
        assert _group_models_by_family({}) == {}


# ===================================================================
# _get_family_versions
# ===================================================================


class TestGetFamilyVersions:
    """Tests for _get_family_versions."""

    def test_collects_unique_sorted(self):
        version_map = {
            "AP41": [{"version": "1.0"}, {"version": "2.0"}],
            "AP41E": [{"version": "1.0"}, {"version": "3.0"}],
        }
        result = _get_family_versions(version_map, ["AP41", "AP41E"])
        assert result == ["3.0", "2.0", "1.0"]

    def test_string_entries(self):
        version_map = {"AP41": ["1.0", "2.0"]}
        result = _get_family_versions(version_map, ["AP41"])
        assert result == ["2.0", "1.0"]

    def test_missing_model(self):
        result = _get_family_versions({}, ["AP99"])
        assert result == []


# ===================================================================
# _get_current_family_version
# ===================================================================


class TestGetCurrentFamilyVersion:
    """Tests for _get_current_family_version."""

    def test_single_site_found(self):
        result = _get_current_family_version(
            True,
            {"AP41": "1.0", "AP43": "2.0"},
            ["AP41"],
        )
        assert result == "1.0"

    def test_not_single_site(self):
        result = _get_current_family_version(
            False,
            {"AP41": "1.0"},
            ["AP41"],
        )
        assert result is None

    def test_model_not_found(self):
        result = _get_current_family_version(
            True,
            {"AP43": "2.0"},
            ["AP41"],
        )
        assert result is None


# ===================================================================
# _extract_version_strings
# ===================================================================


class TestExtractVersionStrings:
    """Tests for _extract_version_strings."""

    def test_dict_entries(self):
        entries = [{"version": "1.0"}, {"version": "2.0"}]
        assert _extract_version_strings(entries) == ["1.0", "2.0"]

    def test_string_entries(self):
        assert _extract_version_strings(["1.0", "2.0"]) == ["1.0", "2.0"]

    def test_none_version_skipped(self):
        entries = [{"version": None}, {"version": "1.0"}]
        assert _extract_version_strings(entries) == ["1.0"]

    def test_empty(self):
        assert _extract_version_strings([]) == []


# ===================================================================
# _compute_msp_totals
# ===================================================================


class TestComputeMspTotals:
    """Tests for _compute_msp_totals."""

    def test_all_success(self):
        results = [
            {"success": True, "sites_configured": 5},
            {"success": True, "sites_configured": 3},
        ]
        total, success, sites = _compute_msp_totals(results)
        assert total == 2
        assert success == 2
        assert sites == 8

    def test_partial_failure(self):
        results = [
            {"success": True, "sites_configured": 5},
            {"success": False, "sites_configured": 0},
        ]
        total, success, sites = _compute_msp_totals(results)
        assert total == 2
        assert success == 1
        assert sites == 5

    def test_empty(self):
        total, success, sites = _compute_msp_totals([])
        assert total == 0
        assert success == 0
        assert sites == 0


# ===================================================================
# _print_msp_failed_orgs
# ===================================================================


class TestPrintMspFailedOrgs:
    """Tests for _print_msp_failed_orgs."""

    def test_prints_failed(self, capsys):
        results = [
            {"success": True, "org_name": "Org A"},
            {"success": False, "org_name": "Org B"},
            {"success": False, "org_name": "Org C"},
        ]
        _print_msp_failed_orgs(results)
        captured = capsys.readouterr()
        assert "Org B" in captured.out
        assert "Org C" in captured.out
        assert "Org A" not in captured.out


# ===================================================================
# _print_msp_summary
# ===================================================================


class TestPrintMspSummary:
    """Tests for _print_msp_summary."""

    def test_dry_run_summary(self, capsys):
        results = [
            {"success": True, "sites_configured": 5, "org_name": "Org A"},
        ]
        _print_msp_summary(results, dry_run=True)
        captured = capsys.readouterr()
        assert "DRY-RUN" in captured.out
        assert "Would configure" in captured.out

    def test_live_summary(self, capsys):
        results = [
            {"success": True, "sites_configured": 3, "org_name": "Org A"},
        ]
        _print_msp_summary(results, dry_run=False)
        captured = capsys.readouterr()
        assert "Configuration complete" in captured.out
        assert "Successful: 1" in captured.out

    def test_failed_orgs_shown(self, capsys):
        results = [
            {"success": True, "sites_configured": 3, "org_name": "Good"},
            {"success": False, "sites_configured": 0, "org_name": "Bad"},
        ]
        _print_msp_summary(results, dry_run=False)
        captured = capsys.readouterr()
        assert "Bad" in captured.out
        assert "Failed organizations" in captured.out


# ===================================================================
# _collect_family_versions
# ===================================================================


class TestCollectFamilyVersions:
    """Tests for _collect_family_versions."""

    def test_collects_and_sorts(self):
        version_map = {
            "AP41": [
                {"version": "1.0", "tag": "stable"},
                {"version": "2.0", "tag": "beta"},
            ],
        }
        result = _collect_family_versions(["AP41"], version_map)
        assert len(result) == 2
        assert result[0][0] == "2.0"
        assert result[1][0] == "1.0"

    def test_empty_models(self):
        assert _collect_family_versions([], {}) == []


# ===================================================================
# _group_models_for_msp
# ===================================================================


class TestGroupModelsForMsp:
    """Tests for _group_models_for_msp."""

    def test_groups_correctly(self):
        version_map = {
            "AP41": [{"version": "1.0"}],
            "AP41E": [{"version": "1.0"}],
            "AP41P": [{"version": "1.0"}],
        }
        result = _group_models_for_msp(version_map)
        assert "AP41" in result
        assert set(result["AP41"]) == {"AP41", "AP41E", "AP41P"}


# ===================================================================
# _build_version_map_from_list
# ===================================================================


class TestBuildVersionMapFromList:
    """Tests for _build_version_map_from_list."""

    def test_builds_map(self):
        versions = [
            {"model": "AP41", "version": "1.0", "tag": "stable"},
            {"model": "AP41", "version": "2.0", "tag": "beta"},
            {"model": "AP43", "version": "3.0"},
        ]
        result = _build_version_map_from_list(versions)
        assert len(result["AP41"]) == 2
        assert len(result["AP43"]) == 1

    def test_skips_non_dict(self):
        result = _build_version_map_from_list(["not-a-dict"])
        assert result == {}

    def test_skips_missing_fields(self):
        result = _build_version_map_from_list(
            [{"model": "AP41"}, {"version": "1.0"}],
        )
        assert result == {}


# ===================================================================
# _apply_version_to_models
# ===================================================================


class TestApplyVersionToModels:
    """Tests for _apply_version_to_models."""

    def test_applies_to_compatible(self, capsys):
        version_map = {
            "AP41": [{"version": "1.0"}, {"version": "2.0"}],
            "AP41E": [{"version": "1.0"}],
        }
        custom: dict[str, str] = {}
        _apply_version_to_models(
            "1.0",
            "AP41",
            ["AP41", "AP41E"],
            version_map,
            custom,
        )
        assert custom["AP41"] == "1.0"
        assert custom["AP41E"] == "1.0"
        captured = capsys.readouterr()
        assert "Set AP41 family" in captured.out

    def test_incompatible_skipped(self, capsys):
        version_map = {"AP41": [{"version": "2.0"}]}
        custom: dict[str, str] = {}
        _apply_version_to_models(
            "1.0",
            "AP41",
            ["AP41"],
            version_map,
            custom,
        )
        assert "AP41" not in custom


# ===================================================================
# _apply_family_selection
# ===================================================================


class TestApplyFamilySelection:
    """Tests for _apply_family_selection."""

    def test_valid_digit_selection(self, capsys):
        version_map = {"AP41": [{"version": "2.0"}, {"version": "1.0"}]}
        custom: dict[str, str] = {}
        _apply_family_selection(
            "1",  # Operator's choice -> picks index 1 in the sorted_versions list.
            custom,  # Mutable out dict the function writes the chosen version into.
            FamilySelectionContext(  # Issue #433 Phase B: 5 fields bundled into one ctx param.
                family="AP41",
                models=["AP41"],
                sorted_versions=["2.0", "1.0"],
                current_version=None,
                model_version_map=version_map,
            ),
        )
        assert custom["AP41"] == "2.0"

    def test_empty_keeps_current(self, capsys):
        _apply_family_selection(
            "",  # Empty choice falls through to the "keep current" path.
            {},  # No mutation expected when current version is preserved.
            FamilySelectionContext(  # Issue #433 Phase B: 5 fields bundled into one ctx param.
                family="AP41",
                models=["AP41"],
                sorted_versions=["2.0"],
                current_version="1.0",  # Current version exists -> "Keeping" message printed.
                model_version_map={},
            ),
        )
        captured = capsys.readouterr()
        assert "Keeping" in captured.out

    def test_empty_no_current_skips(self, capsys):
        _apply_family_selection(
            "",  # Empty choice + no current version triggers the "Skipped" path.
            {},  # No mutation expected on the skip path.
            FamilySelectionContext(  # Issue #433 Phase B: 5 fields bundled into one ctx param.
                family="AP41",
                models=["AP41"],
                sorted_versions=["2.0"],
                current_version=None,  # No current version -> "Skipped" message printed.
                model_version_map={},
            ),
        )
        captured = capsys.readouterr()
        assert "Skipped" in captured.out


# ===================================================================
# _display_family_versions (output verification)
# ===================================================================


class TestDisplayFamilyVersions:
    """Tests for _display_family_versions display function (non-MSP)."""

    def test_shows_current_marker(self, capsys):
        _display_family_versions(
            "AP41",
            ["AP41", "AP41E"],
            ["2.0", "1.0"],
            "1.0",
        )
        captured = capsys.readouterr()
        assert "<-- current" in captured.out
        assert "AP41 family" in captured.out

    def test_no_current(self, capsys):
        _display_family_versions(
            "AP43",
            ["AP43"],
            ["3.0", "2.0"],
            None,
        )
        captured = capsys.readouterr()
        assert "Skip" in captured.out
        assert "<-- current" not in captured.out


# ===================================================================
# _display_step6_summary
# ===================================================================


class TestDisplayStep6Summary:
    """Tests for _display_step6_summary."""

    def test_displays_info(self, capsys):
        _display_step6_summary(
            selected_sites=[{"id": "s1"}, {"id": "s2"}],
            custom_versions={"AP41": "1.0"},
            schedule={"day_of_week": "mon", "time_of_day": "02:00"},
        )
        captured = capsys.readouterr()
        assert "Sites: 2" in captured.out
        assert "AP41: 1.0" in captured.out
        assert "mon at 02:00" in captured.out


# ===================================================================
# _print_final_summary
# ===================================================================


class TestPrintFinalSummary:
    """Tests for _print_final_summary."""

    def test_dry_run(self, capsys):
        _print_final_summary(
            successful=3,
            failed=1,
            dry_run=True,
        )
        captured = capsys.readouterr()
        assert "DRY-RUN" in captured.out

    def test_live_run(self, capsys):
        _print_final_summary(
            successful=5,
            failed=0,
            dry_run=False,
        )
        captured = capsys.readouterr()
        assert "Successful: 5" in captured.out

    def test_failed_shown(self, capsys):
        _print_final_summary(
            successful=3,
            failed=2,
            dry_run=False,
        )
        captured = capsys.readouterr()
        assert "Failed: 2" in captured.out


# ===================================================================
# SiteAutoUpgradeConfigurator.__init__
# ===================================================================


class TestConfiguratorInit:
    """Tests for SiteAutoUpgradeConfigurator initialization."""

    def test_attributes_set(self, configurator):
        assert configurator.org_id == "org-123"
        assert configurator.dry_run is False
        assert configurator.all_sites == []
        assert configurator.selected_sites == []
        assert configurator.custom_versions == {}
        assert configurator.schedule == {}

    def test_dry_run_flag(self, mock_deps):
        cfg = SiteAutoUpgradeConfigurator(org_id="org-456", deps=replace(mock_deps["deps"], dry_run=True))
        assert cfg.dry_run is True


# ===================================================================
# SiteAutoUpgradeConfigurator.execute (static entry point)
# ===================================================================


class TestConfiguratorExecute:
    """Tests for the static execute entry point."""

    def test_no_msp_calls_single_org(self):
        with (
            patch.object(
                _sau_mod,
                "_run_single_org",
            ) as mock_single,
            patch.object(
                _sau_mod,
                "_handle_msp_mode",
            ) as mock_msp,
        ):
            SiteAutoUpgradeConfigurator.execute(
                apisession=MagicMock(),
                msp_privileges=[],
                safe_input_fn=MagicMock(return_value=""),
                get_org_id_fn=MagicMock(return_value="org-1"),
                fetch_sites_fn=MagicMock(return_value=[]),
                check_stop_fn=MagicMock(return_value=False),
                dry_run=False,
            )
            mock_single.assert_called_once()
            mock_msp.assert_not_called()

    def test_msp_prompts_mode(self):
        with (
            patch.object(
                _sau_mod,
                "_handle_msp_mode",
            ) as mock_msp,
            patch.object(
                _sau_mod,
                "_run_single_org",
            ) as mock_single,
        ):
            SiteAutoUpgradeConfigurator.execute(
                apisession=MagicMock(),
                msp_privileges=[{"scope": "msp"}],
                safe_input_fn=MagicMock(return_value="2"),
                get_org_id_fn=MagicMock(return_value="org-1"),
                fetch_sites_fn=MagicMock(return_value=[]),
                check_stop_fn=MagicMock(return_value=False),
                dry_run=False,
                select_msps_fn=MagicMock(),
                select_orgs_fn=MagicMock(),
            )
            mock_msp.assert_called_once()
            mock_single.assert_not_called()


# ===================================================================
# SiteAutoUpgradeConfigurator.run (orchestration)
# ===================================================================


class TestConfiguratorRun:
    """Tests for the run orchestration method."""

    def test_stop_signal_aborts(self, mock_deps):
        mock_deps["check_stop_fn"].return_value = True
        cfg = SiteAutoUpgradeConfigurator(
            org_id="org-1",
            deps=mock_deps["deps"],
        )
        cfg.run()
        assert cfg.all_sites == []

    def test_no_sites_aborts(self, mock_deps):
        mock_deps["check_stop_fn"].return_value = False
        mock_deps["fetch_sites_fn"].return_value = []
        cfg = SiteAutoUpgradeConfigurator(
            org_id="org-1",
            deps=mock_deps["deps"],
        )
        cfg.run()
        assert cfg.selected_sites == []

    def test_full_run_happy_path(self, mock_deps):
        sites = [{"id": "s1", "name": "Site1"}]
        mock_deps["fetch_sites_fn"].return_value = sites
        mock_deps["safe_input_fn"].side_effect = [
            "A",  # step2 - select all
            "1",  # step4 - version selection
            "1",  # step5 - day of week
            "02:00",  # step5 - time of day
            "y",  # step6 - confirm
        ]
        cfg = SiteAutoUpgradeConfigurator(
            org_id="org-1",
            deps=mock_deps["deps"],
        )
        # Mock step3 API call
        mock_response = MagicMock()
        mock_response.data = [
            {"model": "AP41", "version": "1.0", "tag": "stable"},
        ]
        with patch.dict(
            sys.modules,
            _mist_modules(
                **{
                    "mistapi.api.v1.orgs.devices": MagicMock(
                        listOrgAvailableDeviceVersions=MagicMock(return_value=mock_response),
                    ),
                    "mistapi.api.v1.sites.setting": MagicMock(
                        updateSiteSettings=MagicMock(),
                    ),
                }
            ),
        ):
            cfg.run()
        assert cfg.selected_sites == sites


# ===================================================================
# Step 1: _step1_fetch_sites
# ===================================================================


class TestStep1FetchSites:
    """Tests for _step1_fetch_sites."""

    def test_success(self, mock_deps, capsys):
        mock_deps["fetch_sites_fn"].return_value = [
            {"id": "s1", "name": "Bravo"},
            {"id": "s2", "name": "Alpha"},
        ]
        cfg = SiteAutoUpgradeConfigurator(org_id="org-1", deps=mock_deps["deps"])
        assert cfg._step1_fetch_sites() is True
        assert cfg.all_sites[0]["name"] == "Alpha"
        captured = capsys.readouterr()
        assert "Found 2 site(s)" in captured.out

    def test_empty_sites(self, mock_deps, capsys):
        mock_deps["fetch_sites_fn"].return_value = []
        cfg = SiteAutoUpgradeConfigurator(org_id="org-1", deps=mock_deps["deps"])
        assert cfg._step1_fetch_sites() is False
        captured = capsys.readouterr()
        assert "No sites found" in captured.out

    def test_exception(self, mock_deps, capsys):
        mock_deps["fetch_sites_fn"].side_effect = RuntimeError("network")
        cfg = SiteAutoUpgradeConfigurator(org_id="org-1", deps=mock_deps["deps"])
        assert cfg._step1_fetch_sites() is False
        captured = capsys.readouterr()
        assert "Error fetching sites" in captured.out


# ===================================================================
# Step 2: _step2_select_sites
# ===================================================================


class TestStep2SelectSites:
    """Tests for _step2_select_sites."""

    def test_select_all(self, mock_deps):
        cfg = SiteAutoUpgradeConfigurator(org_id="org-1", deps=mock_deps["deps"])
        cfg.all_sites = [{"id": "s1", "name": "A"}]
        mock_deps["safe_input_fn"].return_value = "A"
        assert cfg._step2_select_sites() is True
        assert len(cfg.selected_sites) == 1

    def test_select_single(self, mock_deps):
        cfg = SiteAutoUpgradeConfigurator(org_id="org-1", deps=mock_deps["deps"])
        cfg.all_sites = [
            {"id": "s1", "name": "Alpha"},
            {"id": "s2", "name": "Bravo"},
        ]
        mock_deps["safe_input_fn"].side_effect = ["S", "1"]
        with patch.dict(
            sys.modules,
            _mist_modules(
                **{
                    "mistapi.api.v1.sites.setting": MagicMock(
                        getSiteSettings=MagicMock(return_value=MagicMock(data={})),
                    ),
                }
            ),
        ):
            assert cfg._step2_select_sites() is True
        assert cfg.is_single_site is True

    def test_select_list(self, mock_deps):
        cfg = SiteAutoUpgradeConfigurator(org_id="org-1", deps=mock_deps["deps"])
        cfg.all_sites = [
            {"id": "s1", "name": "A"},
            {"id": "s2", "name": "B"},
            {"id": "s3", "name": "C"},
        ]
        mock_deps["safe_input_fn"].side_effect = ["L", "1,3"]
        assert cfg._step2_select_sites() is True
        assert len(cfg.selected_sites) == 2

    def test_system_exit(self, mock_deps):
        cfg = SiteAutoUpgradeConfigurator(org_id="org-1", deps=mock_deps["deps"])
        mock_deps["safe_input_fn"].side_effect = SystemExit
        assert cfg._step2_select_sites() is False


# ===================================================================
# _select_all_sites
# ===================================================================


class TestSelectAllSites:
    """Tests for _select_all_sites."""

    def test_copies_all(self, mock_deps, capsys):
        cfg = SiteAutoUpgradeConfigurator(org_id="org-1", deps=mock_deps["deps"])
        cfg.all_sites = [{"id": "s1"}, {"id": "s2"}]
        assert cfg._select_all_sites() is True
        assert len(cfg.selected_sites) == 2
        captured = capsys.readouterr()
        assert "Selected ALL 2" in captured.out


# ===================================================================
# _select_single_site
# ===================================================================


class TestSelectSingleSite:
    """Tests for _select_single_site."""

    def test_valid_selection(self, mock_deps):
        cfg = SiteAutoUpgradeConfigurator(org_id="org-1", deps=mock_deps["deps"])
        cfg.all_sites = [{"id": "s1", "name": "Site1"}]
        mock_deps["safe_input_fn"].return_value = "1"
        with patch.dict(
            sys.modules,
            _mist_modules(
                **{
                    "mistapi.api.v1.sites.setting": MagicMock(
                        getSiteSettings=MagicMock(return_value=MagicMock(data={})),
                    ),
                }
            ),
        ):
            assert cfg._select_single_site() is True
        assert cfg.is_single_site is True
        assert len(cfg.selected_sites) == 1

    def test_cancel(self, mock_deps):
        cfg = SiteAutoUpgradeConfigurator(org_id="org-1", deps=mock_deps["deps"])
        cfg.all_sites = [{"id": "s1", "name": "Site1"}]
        mock_deps["safe_input_fn"].return_value = "q"
        assert cfg._select_single_site() is False

    def test_invalid_input(self, mock_deps):
        cfg = SiteAutoUpgradeConfigurator(org_id="org-1", deps=mock_deps["deps"])
        cfg.all_sites = [{"id": "s1", "name": "Site1"}]
        mock_deps["safe_input_fn"].return_value = "abc"
        assert cfg._select_single_site() is False

    def test_out_of_range(self, mock_deps):
        cfg = SiteAutoUpgradeConfigurator(org_id="org-1", deps=mock_deps["deps"])
        cfg.all_sites = [{"id": "s1", "name": "Site1"}]
        mock_deps["safe_input_fn"].return_value = "5"
        assert cfg._select_single_site() is False

    def test_system_exit(self, mock_deps):
        cfg = SiteAutoUpgradeConfigurator(org_id="org-1", deps=mock_deps["deps"])
        cfg.all_sites = [{"id": "s1", "name": "Site1"}]
        mock_deps["safe_input_fn"].side_effect = SystemExit
        assert cfg._select_single_site() is False


# ===================================================================
# _fetch_current_site_settings
# ===================================================================


class TestFetchCurrentSiteSettings:
    """Tests for _fetch_current_site_settings."""

    def test_loads_settings(self, mock_deps, capsys):
        cfg = SiteAutoUpgradeConfigurator(org_id="org-1", deps=mock_deps["deps"])
        mock_response = MagicMock()
        mock_response.data = {
            "auto_upgrade": {
                "custom_versions": {"AP41": "1.0"},
                "day_of_week": "mon",
                "time_of_day": "03:00",
            },
        }
        with patch.dict(
            sys.modules,
            _mist_modules(
                **{
                    "mistapi.api.v1.sites.setting": MagicMock(
                        getSiteSettings=MagicMock(return_value=mock_response),
                    ),
                }
            ),
        ):
            cfg._fetch_current_site_settings("site-1")
        assert cfg.current_site_versions == {"AP41": "1.0"}
        assert cfg.schedule["day_of_week"] == "mon"
        captured = capsys.readouterr()
        assert "1 model(s) configured" in captured.out

    def test_no_auto_upgrade(self, mock_deps):
        cfg = SiteAutoUpgradeConfigurator(org_id="org-1", deps=mock_deps["deps"])
        mock_response = MagicMock()
        mock_response.data = {}
        with patch.dict(
            sys.modules,
            _mist_modules(
                **{
                    "mistapi.api.v1.sites.setting": MagicMock(
                        getSiteSettings=MagicMock(return_value=mock_response),
                    ),
                }
            ),
        ):
            cfg._fetch_current_site_settings("site-1")
        assert cfg.current_site_versions == {}

    def test_exception_handled(self, mock_deps):
        cfg = SiteAutoUpgradeConfigurator(org_id="org-1", deps=mock_deps["deps"])
        with patch.dict(
            sys.modules,
            _mist_modules(
                **{
                    "mistapi.api.v1.sites.setting": MagicMock(
                        getSiteSettings=MagicMock(side_effect=RuntimeError("err")),
                    ),
                }
            ),
        ):
            cfg._fetch_current_site_settings("site-1")
        assert cfg.current_site_versions == {}


# ===================================================================
# _select_from_list
# ===================================================================


class TestSelectFromList:
    """Tests for _select_from_list."""

    def test_valid_selection(self, mock_deps, capsys):
        cfg = SiteAutoUpgradeConfigurator(org_id="org-1", deps=mock_deps["deps"])
        cfg.all_sites = [
            {"id": "s1", "name": "A"},
            {"id": "s2", "name": "B"},
        ]
        mock_deps["safe_input_fn"].return_value = "1,2"
        assert cfg._select_from_list() is True
        assert len(cfg.selected_sites) == 2

    def test_empty_selection(self, mock_deps, capsys):
        cfg = SiteAutoUpgradeConfigurator(org_id="org-1", deps=mock_deps["deps"])
        cfg.all_sites = [{"id": "s1", "name": "A"}]
        mock_deps["safe_input_fn"].return_value = ""
        assert cfg._select_from_list() is False

    def test_system_exit(self, mock_deps):
        cfg = SiteAutoUpgradeConfigurator(org_id="org-1", deps=mock_deps["deps"])
        cfg.all_sites = [{"id": "s1", "name": "A"}]
        mock_deps["safe_input_fn"].side_effect = SystemExit
        assert cfg._select_from_list() is False


# ===================================================================
# _apply_site_indices
# ===================================================================


class TestApplySiteIndices:
    """Tests for _apply_site_indices."""

    def test_valid_indices(self, mock_deps, capsys):
        cfg = SiteAutoUpgradeConfigurator(org_id="org-1", deps=mock_deps["deps"])
        cfg.all_sites = [
            {"id": "s1", "name": "A"},
            {"id": "s2", "name": "B"},
            {"id": "s3", "name": "C"},
        ]
        assert cfg._apply_site_indices([1, 3]) is True
        assert len(cfg.selected_sites) == 2
        captured = capsys.readouterr()
        assert "Selected 2 site(s)" in captured.out

    def test_out_of_range_ignored(self, mock_deps):
        cfg = SiteAutoUpgradeConfigurator(org_id="org-1", deps=mock_deps["deps"])
        cfg.all_sites = [{"id": "s1", "name": "A"}]
        assert cfg._apply_site_indices([99]) is False

    def test_truncates_display(self, mock_deps, capsys):
        cfg = SiteAutoUpgradeConfigurator(org_id="org-1", deps=mock_deps["deps"])
        cfg.all_sites = [{"id": f"s{i}", "name": f"Site{i}"} for i in range(10)]
        assert cfg._apply_site_indices(list(range(1, 11))) is True
        captured = capsys.readouterr()
        assert "... and 5 more" in captured.out


# ===================================================================
# Step 3: _step3_fetch_available_versions
# ===================================================================


class TestStep3FetchVersions:
    """Tests for _step3_fetch_available_versions."""

    def test_success(self, mock_deps, capsys):
        cfg = SiteAutoUpgradeConfigurator(org_id="org-1", deps=mock_deps["deps"])
        mock_response = MagicMock()
        mock_response.data = [
            {"model": "AP41", "version": "1.0"},
        ]
        with patch.dict(
            sys.modules,
            _mist_modules(
                **{
                    "mistapi.api.v1.orgs.devices": MagicMock(
                        listOrgAvailableDeviceVersions=MagicMock(return_value=mock_response),
                    ),
                }
            ),
        ):
            assert cfg._step3_fetch_available_versions() is True
        assert "AP41" in cfg.model_version_map
        captured = capsys.readouterr()
        assert "Found firmware for 1 AP model(s)" in captured.out

    def test_no_session(self, mock_deps, capsys):
        cfg = SiteAutoUpgradeConfigurator(org_id="org-1", deps=mock_deps["deps"])
        cfg.apisession = None
        assert cfg._step3_fetch_available_versions() is False

    def test_no_data(self, mock_deps, capsys):
        cfg = SiteAutoUpgradeConfigurator(org_id="org-1", deps=mock_deps["deps"])
        mock_response = MagicMock(spec=[])
        del mock_response.data
        with patch.dict(
            sys.modules,
            _mist_modules(
                **{
                    "mistapi.api.v1.orgs.devices": MagicMock(
                        listOrgAvailableDeviceVersions=MagicMock(return_value=mock_response),
                    ),
                }
            ),
        ):
            assert cfg._step3_fetch_available_versions() is False

    def test_exception(self, mock_deps, capsys):
        cfg = SiteAutoUpgradeConfigurator(org_id="org-1", deps=mock_deps["deps"])
        with patch.dict(
            sys.modules,
            _mist_modules(
                **{
                    "mistapi.api.v1.orgs.devices": MagicMock(
                        listOrgAvailableDeviceVersions=MagicMock(side_effect=RuntimeError("err")),
                    ),
                }
            ),
        ):
            assert cfg._step3_fetch_available_versions() is False
        captured = capsys.readouterr()
        assert "Error fetching firmware" in captured.out


# ===================================================================
# _build_model_version_map
# ===================================================================


class TestBuildModelVersionMap:
    """Tests for _build_model_version_map."""

    def test_builds_map(self, mock_deps):
        cfg = SiteAutoUpgradeConfigurator(org_id="org-1", deps=mock_deps["deps"])
        cfg.available_versions = [
            {"model": "AP41", "version": "1.0"},
            {"model": "AP41", "version": "2.0"},
            {"model": "AP43", "version": "3.0"},
        ]
        cfg._build_model_version_map()
        assert len(cfg.model_version_map["AP41"]) == 2
        assert len(cfg.model_version_map["AP43"]) == 1

    def test_skips_invalid(self, mock_deps):
        cfg = SiteAutoUpgradeConfigurator(org_id="org-1", deps=mock_deps["deps"])
        cfg.available_versions = ["not-a-dict", {"model": "AP41"}]
        cfg._build_model_version_map()
        assert cfg.model_version_map == {}


# ===================================================================
# Step 4: _step4_select_versions
# ===================================================================


class TestStep4SelectVersions:
    """Tests for _step4_select_versions."""

    def test_select_version(self, mock_deps, capsys):
        cfg = SiteAutoUpgradeConfigurator(org_id="org-1", deps=mock_deps["deps"])
        cfg.model_version_map = {
            "AP41": [{"version": "2.0"}, {"version": "1.0"}],
        }
        mock_deps["safe_input_fn"].return_value = "1"
        assert cfg._step4_select_versions() is True
        assert "AP41" in cfg.custom_versions

    def test_skip_all(self, mock_deps, capsys):
        cfg = SiteAutoUpgradeConfigurator(org_id="org-1", deps=mock_deps["deps"])
        cfg.model_version_map = {
            "AP41": [{"version": "1.0"}],
        }
        mock_deps["safe_input_fn"].return_value = ""
        assert cfg._step4_select_versions() is False
        captured = capsys.readouterr()
        assert "No versions selected" in captured.out

    def test_system_exit(self, mock_deps):
        cfg = SiteAutoUpgradeConfigurator(org_id="org-1", deps=mock_deps["deps"])
        cfg.model_version_map = {
            "AP41": [{"version": "1.0"}],
        }
        mock_deps["safe_input_fn"].side_effect = SystemExit
        assert cfg._step4_select_versions() is False


# ===================================================================
# Step 5: _step5_configure_schedule
# ===================================================================


class TestStep5ConfigureSchedule:
    """Tests for _step5_configure_schedule."""

    def test_defaults(self, mock_deps, capsys):
        mock_deps["safe_input_fn"].side_effect = ["1", "02:00"]
        cfg = SiteAutoUpgradeConfigurator(org_id="org-1", deps=mock_deps["deps"])
        cfg._step5_configure_schedule()
        assert cfg.schedule["day_of_week"] == "any"
        assert cfg.schedule["time_of_day"] == "02:00"
        captured = capsys.readouterr()
        assert "daily at 02:00" in captured.out

    def test_specific_day(self, mock_deps, capsys):
        mock_deps["safe_input_fn"].side_effect = ["3", "14:00"]
        cfg = SiteAutoUpgradeConfigurator(org_id="org-1", deps=mock_deps["deps"])
        cfg._step5_configure_schedule()
        assert cfg.schedule["day_of_week"] == "mon"


# ===================================================================
# Step 6: _step6_confirm_and_apply
# ===================================================================


class TestStep6ConfirmAndApply:
    """Tests for _step6_confirm_and_apply."""

    def test_confirm_yes(self, mock_deps, capsys):
        cfg = SiteAutoUpgradeConfigurator(org_id="org-1", deps=mock_deps["deps"])
        cfg.selected_sites = [{"id": "s1", "name": "Site1"}]
        cfg.custom_versions = {"AP41": "1.0"}
        cfg.schedule = {"day_of_week": "any", "time_of_day": "02:00"}
        mock_deps["safe_input_fn"].return_value = "y"
        with patch.dict(
            sys.modules,
            _mist_modules(
                **{
                    "mistapi.api.v1.sites.setting": MagicMock(
                        updateSiteSettings=MagicMock(),
                    ),
                }
            ),
        ):
            cfg._step6_confirm_and_apply()
        captured = capsys.readouterr()
        assert "CONFIGURATION COMPLETE" in captured.out

    def test_confirm_no(self, mock_deps, capsys):
        cfg = SiteAutoUpgradeConfigurator(org_id="org-1", deps=mock_deps["deps"])
        cfg.selected_sites = [{"id": "s1", "name": "Site1"}]
        cfg.custom_versions = {"AP41": "1.0"}
        cfg.schedule = {}
        mock_deps["safe_input_fn"].return_value = "n"
        cfg._step6_confirm_and_apply()
        captured = capsys.readouterr()
        assert "Cancelled" in captured.out

    def test_dry_run_skips_confirm(self, mock_deps, capsys):
        cfg = SiteAutoUpgradeConfigurator(org_id="org-1", deps=replace(mock_deps["deps"], dry_run=True))
        cfg.selected_sites = [{"id": "s1", "name": "Site1"}]
        cfg.custom_versions = {"AP41": "1.0"}
        cfg.schedule = {}
        cfg._step6_confirm_and_apply()
        captured = capsys.readouterr()
        assert "DRY-RUN" in captured.out

    def test_system_exit(self, mock_deps):
        cfg = SiteAutoUpgradeConfigurator(org_id="org-1", deps=mock_deps["deps"])
        cfg.selected_sites = [{"id": "s1", "name": "Site1"}]
        cfg.custom_versions = {"AP41": "1.0"}
        cfg.schedule = {}
        mock_deps["safe_input_fn"].side_effect = SystemExit
        cfg._step6_confirm_and_apply()


# ===================================================================
# _print_intro_header
# ===================================================================


class TestPrintIntroHeader:
    """Tests for _print_intro_header."""

    def test_normal(self, capsys):
        _sau_mod._print_intro_header(False)
        captured = capsys.readouterr()
        assert "SITE AUTO-UPGRADE" in captured.out
        assert "DRY-RUN" not in captured.out

    def test_dry_run(self, capsys):
        _sau_mod._print_intro_header(True)
        captured = capsys.readouterr()
        assert "DRY-RUN" in captured.out


# ===================================================================
# _display_site_list
# ===================================================================


class TestDisplaySiteList:
    """Tests for _display_site_list."""

    def test_shows_sites(self, capsys):
        sites = [{"name": "Alpha"}, {"name": "Bravo"}]
        _sau_mod._display_site_list(sites)
        captured = capsys.readouterr()
        assert "Alpha" in captured.out
        assert "Bravo" in captured.out
        assert "2 total" in captured.out


# ===================================================================
# _display_selection_instructions
# ===================================================================


class TestDisplaySelectionInstructions:
    """Tests for _display_selection_instructions."""

    def test_shows_instructions(self, capsys):
        _sau_mod._display_selection_instructions()
        captured = capsys.readouterr()
        assert "Range: 1-10" in captured.out
        assert "Combined:" in captured.out


# ===================================================================
# _print_step4_header
# ===================================================================


class TestPrintStep4Header:
    """Tests for _print_step4_header."""

    def test_single_site(self, capsys):
        _sau_mod._print_step4_header(True, {"AP41": "1.0"})
        captured = capsys.readouterr()
        assert "Pre-loaded 1 existing" in captured.out

    def test_multi_site(self, capsys):
        _sau_mod._print_step4_header(False, {})
        captured = capsys.readouterr()
        assert "Press Enter to skip" in captured.out


# ===================================================================
# _pick_stable_version
# ===================================================================


class TestPickStableVersion:
    """Tests for _pick_stable_version."""

    def test_picks_stable(self):
        versions = [
            {"version": "2.0", "tag": "beta"},
            {"version": "1.0", "tag": "stable"},
        ]
        assert _sau_mod._pick_stable_version(versions) == "1.0"

    def test_falls_back_to_first_dict(self):
        versions = [{"version": "3.0", "tag": "beta"}]
        assert _sau_mod._pick_stable_version(versions) == "3.0"

    def test_falls_back_to_first_string(self):
        assert _sau_mod._pick_stable_version(["4.0"]) == "4.0"

    def test_empty_returns_empty(self):
        assert _sau_mod._pick_stable_version([]) == ""


# ===================================================================
# _prompt_day_of_week
# ===================================================================


class TestPromptDayOfWeek:
    """Tests for _prompt_day_of_week."""

    def test_daily(self):
        fn = MagicMock(return_value="1")
        assert _sau_mod._prompt_day_of_week(fn) == "any"

    def test_sunday(self):
        fn = MagicMock(return_value="2")
        assert _sau_mod._prompt_day_of_week(fn) == "sun"

    def test_invalid_defaults_any(self):
        fn = MagicMock(return_value="xyz")
        assert _sau_mod._prompt_day_of_week(fn) == "any"

    def test_system_exit(self):
        fn = MagicMock(side_effect=SystemExit)
        assert _sau_mod._prompt_day_of_week(fn) == "any"


# ===================================================================
# _prompt_time_of_day
# ===================================================================


class TestPromptTimeOfDay:
    """Tests for _prompt_time_of_day."""

    def test_valid_time(self):
        fn = MagicMock(return_value="14:00")
        parse_fn = MagicMock(return_value="14:00")
        assert _sau_mod._prompt_time_of_day(fn, parse_fn) == "14:00"

    def test_system_exit_returns_any(self):
        fn = MagicMock(side_effect=SystemExit)
        parse_fn = MagicMock(return_value="any")
        result = _sau_mod._prompt_time_of_day(fn, parse_fn)
        parse_fn.assert_called_with("")
        assert result == "any"


# ===================================================================
# _apply_settings_to_sites
# ===================================================================


class TestApplySettingsToSites:
    """Tests for _apply_settings_to_sites."""

    def test_dry_run(self, capsys):
        sites = [{"id": "s1", "name": "Site1"}]
        ok, fail = _sau_mod._apply_settings_to_sites(
            sites=sites,
            settings={"auto_upgrade": {}},
            apisession=MagicMock(),
            check_stop_fn=MagicMock(return_value=False),
            dry_run=True,
        )
        assert ok == 1
        assert fail == 0
        captured = capsys.readouterr()
        assert "[DRY-RUN]" in captured.out

    def test_live_success(self, capsys):
        sites = [{"id": "s1", "name": "Site1"}]
        with patch.dict(
            sys.modules,
            _mist_modules(
                **{
                    "mistapi.api.v1.sites.setting": MagicMock(
                        updateSiteSettings=MagicMock(),
                    ),
                }
            ),
        ):
            ok, fail = _sau_mod._apply_settings_to_sites(
                sites=sites,
                settings={"auto_upgrade": {}},
                apisession=MagicMock(),
                check_stop_fn=MagicMock(return_value=False),
                dry_run=False,
            )
        assert ok == 1
        assert fail == 0

    def test_api_error(self, capsys):
        sites = [{"id": "s1", "name": "Site1"}]
        with patch.dict(
            sys.modules,
            _mist_modules(
                **{
                    "mistapi.api.v1.sites.setting": MagicMock(
                        updateSiteSettings=MagicMock(side_effect=RuntimeError("fail")),
                    ),
                }
            ),
        ):
            ok, fail = _sau_mod._apply_settings_to_sites(
                sites=sites,
                settings={},
                apisession=MagicMock(),
                check_stop_fn=MagicMock(return_value=False),
                dry_run=False,
            )
        assert ok == 0
        assert fail == 1

    def test_missing_site_id(self):
        sites = [{"name": "NoID"}]
        ok, fail = _sau_mod._apply_settings_to_sites(
            sites=sites,
            settings={},
            apisession=MagicMock(),
            check_stop_fn=MagicMock(return_value=False),
            dry_run=False,
        )
        assert ok == 0
        assert fail == 1

    def test_stop_signal(self):
        sites = [{"id": "s1", "name": "A"}, {"id": "s2", "name": "B"}]
        ok, fail = _sau_mod._apply_settings_to_sites(
            sites=sites,
            settings={},
            apisession=MagicMock(),
            check_stop_fn=MagicMock(return_value=True),
            dry_run=True,
        )
        assert ok == 0
        assert fail == 0


# ===================================================================
# _handle_msp_mode
# ===================================================================


class TestHandleMspMode:
    """Tests for _handle_msp_mode."""

    def test_mode_1_calls_single_org(self):
        with patch.object(_sau_mod, "_run_single_org") as mock_single:
            _sau_mod._handle_msp_mode(
                _make_core(
                    apisession=MagicMock(),
                    safe_input_fn=MagicMock(return_value="1"),
                    fetch_sites_fn=MagicMock(),
                    check_stop_fn=MagicMock(),
                    dry_run=False,
                ),
                _make_msp(select_msps_fn=MagicMock(), select_orgs_fn=MagicMock()),
                MagicMock(return_value="org-1"),
            )
            mock_single.assert_called_once()

    def test_mode_2_calls_msp(self):
        with patch.object(_sau_mod, "_execute_msp_mode") as mock_msp:
            _sau_mod._handle_msp_mode(
                _make_core(
                    apisession=MagicMock(),
                    safe_input_fn=MagicMock(return_value="2"),
                    fetch_sites_fn=MagicMock(),
                    check_stop_fn=MagicMock(),
                    dry_run=False,
                ),
                _make_msp(select_msps_fn=MagicMock(), select_orgs_fn=MagicMock()),
                MagicMock(return_value="org-1"),
            )
            mock_msp.assert_called_once()

    def test_system_exit(self):
        _sau_mod._handle_msp_mode(
            _make_core(
                apisession=MagicMock(),
                safe_input_fn=MagicMock(side_effect=SystemExit),
                fetch_sites_fn=MagicMock(),
                check_stop_fn=MagicMock(),
                dry_run=False,
            ),
            _make_msp(select_msps_fn=None, select_orgs_fn=None),
            MagicMock(),
        )

    def test_dry_run_banner(self, capsys):
        with patch.object(_sau_mod, "_run_single_org"):
            _sau_mod._handle_msp_mode(
                _make_core(
                    apisession=MagicMock(),
                    safe_input_fn=MagicMock(return_value="1"),
                    fetch_sites_fn=MagicMock(),
                    check_stop_fn=MagicMock(),
                    dry_run=True,
                ),
                _make_msp(select_msps_fn=None, select_orgs_fn=None),
                MagicMock(return_value="org-1"),
            )
        captured = capsys.readouterr()
        assert "DRY-RUN MODE" in captured.out


# ===================================================================
# _run_single_org
# ===================================================================


class TestRunSingleOrg:
    """Tests for _run_single_org."""

    def test_no_org_id(self, capsys):
        _sau_mod._run_single_org(
            _make_core(
                apisession=MagicMock(),
                safe_input_fn=MagicMock(),
                fetch_sites_fn=MagicMock(),
                check_stop_fn=MagicMock(),
                dry_run=False,
            ),
            MagicMock(return_value=""),
        )
        captured = capsys.readouterr()
        assert "No organization selected" in captured.out

    def test_valid_org(self):
        with patch.object(
            SiteAutoUpgradeConfigurator,
            "run",
        ) as mock_run:
            _sau_mod._run_single_org(
                _make_core(
                    apisession=MagicMock(),
                    safe_input_fn=MagicMock(),
                    fetch_sites_fn=MagicMock(),
                    check_stop_fn=MagicMock(),
                    dry_run=False,
                ),
                MagicMock(return_value="org-1"),
            )
            mock_run.assert_called_once()


# ===================================================================
# _msp_select_entities
# ===================================================================


class TestMspSelectEntities:
    """Tests for _msp_select_entities."""

    def test_success(self, capsys):
        orgs = [{"id": "o1", "name": "Org1"}]
        result = _sau_mod._msp_select_entities(
            select_msps_fn=MagicMock(return_value=[{"id": "m1"}]),
            select_orgs_fn=MagicMock(return_value=orgs),
        )
        assert result == orgs

    def test_no_msps(self, capsys):
        result = _sau_mod._msp_select_entities(
            select_msps_fn=MagicMock(return_value=[]),
            select_orgs_fn=MagicMock(),
        )
        assert result is None

    def test_no_orgs(self, capsys):
        result = _sau_mod._msp_select_entities(
            select_msps_fn=MagicMock(return_value=[{"id": "m1"}]),
            select_orgs_fn=MagicMock(return_value=[]),
        )
        assert result is None


# ===================================================================
# _msp_get_firmware_config
# ===================================================================


class TestMspGetFirmwareConfig:
    """Tests for _msp_get_firmware_config."""

    def test_auto_detect(self, capsys):
        result = _sau_mod._msp_get_firmware_config(
            apisession=MagicMock(),
            selected_orgs=[{"id": "o1", "name": "Org1"}],
            safe_input_fn=MagicMock(return_value="1"),
        )
        assert result == {}

    def test_manual_select(self):
        with patch.object(
            _sau_mod,
            "_get_shared_firmware_versions",
            return_value={"AP41": "1.0"},
        ):
            result = _sau_mod._msp_get_firmware_config(
                apisession=MagicMock(),
                selected_orgs=[{"id": "o1", "name": "Org1"}],
                safe_input_fn=MagicMock(return_value="2"),
            )
        assert result == {"AP41": "1.0"}

    def test_system_exit(self):
        result = _sau_mod._msp_get_firmware_config(
            apisession=MagicMock(),
            selected_orgs=[{"id": "o1", "name": "Org1"}],
            safe_input_fn=MagicMock(side_effect=SystemExit),
        )
        assert result is None


# ===================================================================
# _msp_confirm_and_apply
# ===================================================================


class TestMspConfirmAndApply:
    """Tests for _msp_confirm_and_apply."""

    def test_cancel(self, capsys):
        _sau_mod._msp_confirm_and_apply(
            _make_core(
                apisession=MagicMock(),
                safe_input_fn=MagicMock(return_value="n"),
                fetch_sites_fn=MagicMock(),
                check_stop_fn=MagicMock(),
                dry_run=False,
            ),
            [{"id": "o1", "name": "Org1"}],
            {"day_of_week": "any", "time_of_day": "02:00"},
            None,
        )
        captured = capsys.readouterr()
        assert "Cancelled" in captured.out

    def test_confirm(self):
        with patch.object(
            _sau_mod,
            "_apply_to_all_orgs",
            return_value=[],
        ):
            _sau_mod._msp_confirm_and_apply(
                _make_core(
                    apisession=MagicMock(),
                    safe_input_fn=MagicMock(return_value="y"),
                    fetch_sites_fn=MagicMock(),
                    check_stop_fn=MagicMock(),
                    dry_run=False,
                ),
                [{"id": "o1", "name": "Org1"}],
                {"day_of_week": "any", "time_of_day": "02:00"},
                {"AP41": "1.0"},
            )

    def test_system_exit(self):
        _sau_mod._msp_confirm_and_apply(
            _make_core(
                apisession=MagicMock(),
                safe_input_fn=MagicMock(side_effect=SystemExit),
                fetch_sites_fn=MagicMock(),
                check_stop_fn=MagicMock(),
                dry_run=False,
            ),
            [{"id": "o1", "name": "Org1"}],
            {"day_of_week": "any", "time_of_day": "02:00"},
            None,
        )


# ===================================================================
# _execute_msp_mode
# ===================================================================


class TestExecuteMspMode:
    """Tests for _execute_msp_mode."""

    def test_no_msps_fn(self, capsys):
        _sau_mod._execute_msp_mode(
            _make_core(
                apisession=MagicMock(),
                safe_input_fn=MagicMock(),
                fetch_sites_fn=MagicMock(),
                check_stop_fn=MagicMock(),
                dry_run=False,
            ),
            _make_msp(select_msps_fn=None, select_orgs_fn=None),
        )
        captured = capsys.readouterr()
        assert "MSP functions not available" in captured.out

    def test_no_orgs_selected(self):
        with patch.object(
            _sau_mod,
            "_msp_select_entities",
            return_value=None,
        ):
            _sau_mod._execute_msp_mode(
                _make_core(
                    apisession=MagicMock(),
                    safe_input_fn=MagicMock(),
                    fetch_sites_fn=MagicMock(),
                    check_stop_fn=MagicMock(),
                    dry_run=False,
                ),
                _make_msp(select_msps_fn=MagicMock(), select_orgs_fn=MagicMock()),
            )

    def test_firmware_none_cancels(self):
        with (
            patch.object(
                _sau_mod,
                "_msp_select_entities",
                return_value=[{"id": "o1", "name": "Org1"}],
            ),
            patch.object(
                _sau_mod,
                "_msp_get_firmware_config",
                return_value=None,
            ),
        ):
            _sau_mod._execute_msp_mode(
                _make_core(
                    apisession=MagicMock(),
                    safe_input_fn=MagicMock(),
                    fetch_sites_fn=MagicMock(),
                    check_stop_fn=MagicMock(),
                    dry_run=False,
                ),
                _make_msp(select_msps_fn=MagicMock(), select_orgs_fn=MagicMock()),
            )

    def test_full_flow(self):
        with (
            patch.object(
                _sau_mod,
                "_msp_select_entities",
                return_value=[{"id": "o1", "name": "Org1"}],
            ),
            patch.object(
                _sau_mod,
                "_msp_get_firmware_config",
                return_value={},
            ),
            patch.object(
                _sau_mod,
                "_get_shared_schedule",
                return_value={"day_of_week": "any", "time_of_day": "02:00"},
            ),
            patch.object(
                _sau_mod,
                "_msp_confirm_and_apply",
            ) as mock_confirm,
        ):
            _sau_mod._execute_msp_mode(
                _make_core(
                    apisession=MagicMock(),
                    safe_input_fn=MagicMock(),
                    fetch_sites_fn=MagicMock(),
                    check_stop_fn=MagicMock(),
                    dry_run=False,
                ),
                _make_msp(select_msps_fn=MagicMock(), select_orgs_fn=MagicMock()),
            )
            mock_confirm.assert_called_once()

    def test_schedule_none_cancels(self):
        with (
            patch.object(
                _sau_mod,
                "_msp_select_entities",
                return_value=[{"id": "o1", "name": "Org1"}],
            ),
            patch.object(
                _sau_mod,
                "_msp_get_firmware_config",
                return_value={},
            ),
            patch.object(
                _sau_mod,
                "_get_shared_schedule",
                return_value=None,
            ),
        ):
            _sau_mod._execute_msp_mode(
                _make_core(
                    apisession=MagicMock(),
                    safe_input_fn=MagicMock(),
                    fetch_sites_fn=MagicMock(),
                    check_stop_fn=MagicMock(),
                    dry_run=False,
                ),
                _make_msp(select_msps_fn=MagicMock(), select_orgs_fn=MagicMock()),
            )


# ===================================================================
# _apply_to_all_orgs
# ===================================================================


class TestApplyToAllOrgs:
    """Tests for _apply_to_all_orgs."""

    def test_applies_to_orgs(self, mock_deps):
        orgs = [
            {"id": "o1", "name": "Org1"},
            {"id": "o2", "name": "Org2"},
        ]
        mock_deps["fetch_sites_fn"].return_value = [
            {"id": "s1", "name": "Site1"},
        ]
        with patch.object(
            SiteAutoUpgradeConfigurator,
            "run_msp_mode",
            return_value=(True, 1),
        ):
            results = _sau_mod._apply_to_all_orgs(
                _make_core(
                    apisession=mock_deps["apisession"],
                    safe_input_fn=mock_deps["safe_input_fn"],
                    fetch_sites_fn=mock_deps["fetch_sites_fn"],
                    check_stop_fn=mock_deps["check_stop_fn"],
                    dry_run=False,
                ),
                orgs,
                {"day_of_week": "any", "time_of_day": "02:00"},
                None,
            )
        assert len(results) == 2
        assert results[0]["success"] is True


# ===================================================================
# run_msp_mode
# ===================================================================


class TestRunMspMode:
    """Tests for SiteAutoUpgradeConfigurator.run_msp_mode."""

    def test_no_sites(self, mock_deps):
        mock_deps["fetch_sites_fn"].return_value = []
        cfg = SiteAutoUpgradeConfigurator(org_id="org-1", deps=mock_deps["deps"])
        success, count = cfg.run_msp_mode()
        assert success is False
        assert count == 0

    def test_shared_versions(self, mock_deps, capsys):
        mock_deps["fetch_sites_fn"].return_value = [
            {"id": "s1", "name": "Site1"},
        ]
        cfg = SiteAutoUpgradeConfigurator(org_id="org-1", deps=replace(mock_deps["deps"], dry_run=True))
        cfg.shared_versions = {"AP41": "1.0"}
        cfg.schedule = {"day_of_week": "any", "time_of_day": "02:00"}
        success, count = cfg.run_msp_mode()
        assert success is True
        assert count == 1
        captured = capsys.readouterr()
        assert "pre-selected firmware" in captured.out.lower() or "Pre-selected" in captured.out

    def test_auto_select_versions(self, mock_deps, capsys):
        mock_deps["fetch_sites_fn"].return_value = [
            {"id": "s1", "name": "Site1"},
        ]
        cfg = SiteAutoUpgradeConfigurator(org_id="org-1", deps=replace(mock_deps["deps"], dry_run=True))
        cfg.schedule = {"day_of_week": "any", "time_of_day": "02:00"}
        mock_response = MagicMock()
        mock_response.data = [
            {"model": "AP41", "version": "1.0", "tag": "stable"},
        ]
        with patch.dict(
            sys.modules,
            _mist_modules(
                **{
                    "mistapi.api.v1.orgs.devices": MagicMock(
                        listOrgAvailableDeviceVersions=MagicMock(return_value=mock_response),
                    ),
                }
            ),
        ):
            success, count = cfg.run_msp_mode()
        assert success is True


# ===================================================================
# _auto_select_versions
# ===================================================================


class TestAutoSelectVersions:
    """Tests for _auto_select_versions."""

    def test_empty_map(self, mock_deps, capsys):
        cfg = SiteAutoUpgradeConfigurator(org_id="org-1", deps=mock_deps["deps"])
        cfg.model_version_map = {}
        assert cfg._auto_select_versions() is False
        captured = capsys.readouterr()
        assert "No firmware versions" in captured.out

    def test_selects_versions(self, mock_deps, capsys):
        cfg = SiteAutoUpgradeConfigurator(org_id="org-1", deps=mock_deps["deps"])
        cfg.model_version_map = {
            "AP41": [{"version": "1.0", "tag": "stable"}],
            "AP43": [],
        }
        assert cfg._auto_select_versions() is True
        assert "AP41" in cfg.custom_versions


# ===================================================================
# _apply_auto_upgrade_config
# ===================================================================


class TestApplyAutoUpgradeConfig:
    """Tests for _apply_auto_upgrade_config."""

    def test_no_sites(self, mock_deps):
        cfg = SiteAutoUpgradeConfigurator(org_id="org-1", deps=mock_deps["deps"])
        cfg.selected_sites = []
        success, count = cfg._apply_auto_upgrade_config()
        assert success is False
        assert count == 0

    def test_dry_run(self, mock_deps, capsys):
        cfg = SiteAutoUpgradeConfigurator(org_id="org-1", deps=replace(mock_deps["deps"], dry_run=True))
        cfg.selected_sites = [{"id": "s1", "name": "Site1"}]
        cfg.custom_versions = {"AP41": "1.0"}
        cfg.schedule = {"day_of_week": "any", "time_of_day": "02:00"}
        success, count = cfg._apply_auto_upgrade_config()
        assert success is True
        assert count == 1
        captured = capsys.readouterr()
        assert "Would configure" in captured.out


# ===================================================================
# _get_shared_schedule
# ===================================================================


class TestGetSharedSchedule:
    """Tests for _get_shared_schedule."""

    def test_defaults(self, capsys):
        fn = MagicMock(side_effect=["any", "02:00"])
        result = _sau_mod._get_shared_schedule(fn)
        assert result == {"day_of_week": "any", "time_of_day": "02:00"}

    def test_named_day(self, capsys):
        fn = MagicMock(side_effect=["mon", "03:00"])
        result = _sau_mod._get_shared_schedule(fn)
        assert result["day_of_week"] == "mon"

    def test_numeric_day(self, capsys):
        fn = MagicMock(side_effect=["3", "02:00"])
        result = _sau_mod._get_shared_schedule(fn)
        assert result["day_of_week"] == "tue"

    def test_day_exit_returns_none(self):
        fn = MagicMock(side_effect=SystemExit)
        result = _sau_mod._get_shared_schedule(fn)
        assert result is None

    def test_time_exit_returns_none(self):
        fn = MagicMock(side_effect=["any", SystemExit])
        result = _sau_mod._get_shared_schedule(fn)
        assert result is None

    def test_any_time(self, capsys):
        fn = MagicMock(side_effect=["1", "any"])
        result = _sau_mod._get_shared_schedule(fn)
        assert result["time_of_day"] == "any"


# ===================================================================
# _get_shared_firmware_versions
# ===================================================================


class TestGetSharedFirmwareVersions:
    """Tests for _get_shared_firmware_versions."""

    def test_no_org_id(self, capsys):
        result = _sau_mod._get_shared_firmware_versions(
            apisession=MagicMock(),
            reference_org={"name": "Org1"},
            safe_input_fn=MagicMock(),
        )
        assert result == {}

    def test_no_session(self, capsys):
        result = _sau_mod._get_shared_firmware_versions(
            apisession=None,
            reference_org={"id": "o1", "name": "Org1"},
            safe_input_fn=MagicMock(),
        )
        assert result == {}

    def test_api_error(self, capsys):
        with patch.dict(
            sys.modules,
            _mist_modules(
                **{
                    "mistapi.api.v1.orgs.devices": MagicMock(
                        listOrgAvailableDeviceVersions=MagicMock(side_effect=RuntimeError("err")),
                    ),
                }
            ),
        ):
            result = _sau_mod._get_shared_firmware_versions(
                apisession=MagicMock(),
                reference_org={"id": "o1", "name": "Org1"},
                safe_input_fn=MagicMock(),
            )
        assert result == {}

    def test_success(self):
        mock_response = MagicMock()
        mock_response.data = [
            {"model": "AP41", "version": "1.0", "tag": "stable"},
        ]
        with (
            patch.dict(
                sys.modules,
                _mist_modules(
                    **{
                        "mistapi.api.v1.orgs.devices": MagicMock(
                            listOrgAvailableDeviceVersions=MagicMock(return_value=mock_response),
                        ),
                    }
                ),
            ),
            patch.object(
                _sau_mod,
                "_select_versions_interactively",
                return_value={"AP41": "1.0"},
            ),
        ):
            result = _sau_mod._get_shared_firmware_versions(
                apisession=MagicMock(),
                reference_org={"id": "o1", "name": "Org1"},
                safe_input_fn=MagicMock(),
            )
        assert result == {"AP41": "1.0"}

    def test_empty_versions(self, capsys):
        mock_response = MagicMock()
        mock_response.data = []
        with patch.dict(
            sys.modules,
            _mist_modules(
                **{
                    "mistapi.api.v1.orgs.devices": MagicMock(
                        listOrgAvailableDeviceVersions=MagicMock(return_value=mock_response),
                    ),
                }
            ),
        ):
            result = _sau_mod._get_shared_firmware_versions(
                apisession=MagicMock(),
                reference_org={"id": "o1", "name": "Org1"},
                safe_input_fn=MagicMock(),
            )
        assert result == {}


# ===================================================================
# _select_versions_interactively
# ===================================================================


class TestSelectVersionsInteractively:
    """Tests for _select_versions_interactively."""

    def test_select_one(self, capsys):
        families = {"AP41": ["AP41"]}
        version_map = {
            "AP41": [{"version": "1.0", "tag": "stable"}],
        }
        result = _sau_mod._select_versions_interactively(
            families,
            version_map,
            safe_input_fn=MagicMock(return_value="1"),
        )
        assert result == {"AP41": "1.0"}

    def test_quit(self):
        families = {"AP41": ["AP41"]}
        version_map = {
            "AP41": [{"version": "1.0", "tag": "stable"}],
        }
        result = _sau_mod._select_versions_interactively(
            families,
            version_map,
            safe_input_fn=MagicMock(return_value="q"),
        )
        assert result is None

    def test_skip(self, capsys):
        families = {"AP41": ["AP41"]}
        version_map = {
            "AP41": [{"version": "1.0", "tag": "stable"}],
        }
        result = _sau_mod._select_versions_interactively(
            families,
            version_map,
            safe_input_fn=MagicMock(return_value=""),
        )
        assert result == {}

    def test_system_exit(self):
        families = {"AP41": ["AP41"]}
        version_map = {
            "AP41": [{"version": "1.0", "tag": "stable"}],
        }
        result = _sau_mod._select_versions_interactively(
            families,
            version_map,
            safe_input_fn=MagicMock(side_effect=SystemExit),
        )
        assert result is None

    def test_invalid_index(self, capsys):
        families = {"AP41": ["AP41"]}
        version_map = {
            "AP41": [{"version": "1.0", "tag": "stable"}],
        }
        result = _sau_mod._select_versions_interactively(
            families,
            version_map,
            safe_input_fn=MagicMock(return_value="99"),
        )
        assert result == {}
        captured = capsys.readouterr()
        assert "Invalid selection" in captured.out


# ===================================================================
# _display_msp_family_versions
# ===================================================================


class TestDisplayMspFamilyVersions2:
    """Additional tests for _display_msp_family_versions."""

    def test_shows_tag(self, capsys):
        _display_msp_family_versions(
            "AP41",
            ["AP41"],
            [("1.0", "stable"), ("2.0", "beta")],
        )
        captured = capsys.readouterr()
        assert "[stable]" in captured.out
        assert "[beta]" in captured.out
        assert "Skip this family" in captured.out


# ===================================================================
# _display_msp_pre_apply_summary
# ===================================================================


class TestDisplayMspPreApplySummary:
    """Tests for _display_msp_pre_apply_summary."""

    def test_with_versions(self, capsys):
        _sau_mod._display_msp_pre_apply_summary(
            shared_schedule={"day_of_week": "mon", "time_of_day": "03:00"},
            shared_versions={"AP41": "1.0"},
            selected_orgs=[{"id": "o1"}, {"id": "o2"}],
        )
        captured = capsys.readouterr()
        assert "mon" in captured.out
        assert "03:00" in captured.out
        assert "AP41: 1.0" in captured.out
        assert "Organizations: 2" in captured.out

    def test_auto_detect(self, capsys):
        _sau_mod._display_msp_pre_apply_summary(
            shared_schedule={"day_of_week": "any", "time_of_day": "02:00"},
            shared_versions=None,
            selected_orgs=[{"id": "o1"}],
        )
        captured = capsys.readouterr()
        assert "auto-detected" in captured.out.lower() or "Latest stable" in captured.out
