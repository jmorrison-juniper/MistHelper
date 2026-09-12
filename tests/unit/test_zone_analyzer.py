"""Tests for src.analytics.zone_analyzer module."""

from __future__ import annotations

import sys
from typing import Any
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Mock mistapi before importing the module under test.
# We save/restore previous sys.modules entries so we don't pollute other
# test files that expect ``import mistapi`` to raise ImportError.
# ---------------------------------------------------------------------------
_mock_mistapi = MagicMock()

# Mock tqdm too, to avoid import issues in CI.
_mock_tqdm_mod = MagicMock()
_mock_tqdm_mod.tqdm = lambda items, **_kw: items

_MOCKED_MODULES: dict[str, Any] = {
    "mistapi": _mock_mistapi,
    "mistapi.api": _mock_mistapi.api,
    "mistapi.api.v1": _mock_mistapi.api.v1,
    "mistapi.api.v1.sites": _mock_mistapi.api.v1.sites,
    "mistapi.api.v1.sites.setting": _mock_mistapi.api.v1.sites.setting,
    "mistapi.api.v1.sites.zones": _mock_mistapi.api.v1.sites.zones,
    "tqdm": _mock_tqdm_mod,
}

# Remember what was there before (if anything).
_saved: dict[str, Any] = {key: sys.modules.get(key) for key in _MOCKED_MODULES}


def _install_stub_modules() -> None:
    """Put every stub into sys.modules."""
    sys.modules.update(_MOCKED_MODULES)


def _restore_stub_modules() -> None:
    """Undo _install_stub_modules for each entry we still own."""
    for key, saved in _saved.items():
        if sys.modules.get(key) is not _MOCKED_MODULES[key]:
            continue  # Another module replaced our stub; leave it alone.
        if saved is not None:
            sys.modules[key] = saved
        else:
            sys.modules.pop(key, None)


# Restore the moment the import finishes. pytest imports every test module during
# collection but runs teardown_module only for a module that has a selected test, so a
# stub left here leaks for the whole session and breaks mistapi's lazy subpackage
# import. See issue #1739.
_install_stub_modules()
try:
    from src.analytics.zone_analyzer import (
        ZoneConfigurationAnalyzer,
        _build_one_summary_row,
        _build_summary_rows,
        _compute_zone_stats,
        _dwell_config_key,
        _empty_zone_entry,
        _find_dwell_deviations,
        _find_occupancy_deviations,
        _find_sites_missing_common,
        _find_sites_with_unique,
        _find_zone_count_deviations,
        _occupancy_config_key,
        _track_custom_names,
    )
finally:
    _restore_stub_modules()


# ---------------------------------------------------------------------------
# Module setup/teardown -- ensure mocks survive pytest collection ordering
# ---------------------------------------------------------------------------
def setup_module() -> None:
    """Re-install the stubs for the duration of this module's tests."""
    _install_stub_modules()


def teardown_module() -> None:
    """Remove the stubs again after this module's tests finish."""
    _restore_stub_modules()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture()
def mock_apisession() -> MagicMock:
    """Return a mock API session."""
    return MagicMock()


@pytest.fixture()
def mock_deps(mock_apisession: MagicMock) -> dict[str, Any]:
    """Return standard dependency mocks."""
    return {
        "apisession": mock_apisession,
        "get_org_id_fn": MagicMock(return_value="org-123"),
        "check_stop_fn": MagicMock(return_value=False),
        "all_sites_fn": MagicMock(return_value=[]),
        "save_data_fn": MagicMock(),
    }


# ======================================================================
# Helper function tests
# ======================================================================


class TestEmptyZoneEntry:
    """Tests for _empty_zone_entry."""

    def test_returns_correct_structure(self) -> None:
        result = _empty_zone_entry("TestSite")
        assert result["site_name"] == "TestSite"
        assert result["zones"] == []
        assert result["zone_names"] == set()
        assert result["zone_count"] == 0


class TestComputeZoneStats:
    """Tests for _compute_zone_stats."""

    def test_empty_list(self) -> None:
        stats = _compute_zone_stats([], 0, 0)
        assert stats["mean"] == 0.0
        assert stats["median"] == 0
        assert stats["std_dev"] == 0.0

    def test_single_value(self) -> None:
        stats = _compute_zone_stats([5], 1, 1)
        assert stats["mean"] == 5.0
        assert stats["median"] == 5
        assert stats["min"] == 5
        assert stats["max"] == 5
        assert stats["std_dev"] == 0.0

    def test_multiple_values(self) -> None:
        stats = _compute_zone_stats([2, 4, 6], 3, 3)
        assert stats["mean"] == 4.0
        assert stats["median"] == 4
        assert stats["min"] == 2
        assert stats["max"] == 6
        assert stats["std_dev"] > 0

    def test_all_zeros(self) -> None:
        stats = _compute_zone_stats([0, 0, 0], 3, 0)
        assert stats["mean"] == 0.0
        assert stats["sites_with_zones"] == 0


class TestFindSitesMissingCommon:
    """Tests for _find_sites_missing_common."""

    def test_no_missing(self) -> None:
        site_zones = {
            "s1": {
                "zone_count": 2,
                "zone_names": {"A", "B"},
                "site_name": "Site1",
            },
        }
        result = _find_sites_missing_common(site_zones, {"A", "B"})
        assert result == {}

    def test_site_missing_zones(self) -> None:
        site_zones = {
            "s1": {
                "zone_count": 1,
                "zone_names": {"A"},
                "site_name": "Site1",
            },
        }
        result = _find_sites_missing_common(site_zones, {"A", "B"})
        assert "s1" in result
        assert "B" in result["s1"]["missing_zones"]

    def test_empty_sites_skipped(self) -> None:
        site_zones = {
            "s1": {
                "zone_count": 0,
                "zone_names": set(),
                "site_name": "Site1",
            },
        }
        result = _find_sites_missing_common(site_zones, {"A"})
        assert result == {}


class TestFindSitesWithUnique:
    """Tests for _find_sites_with_unique."""

    def test_no_unique(self) -> None:
        site_zones = {
            "s1": {"zone_names": {"A"}, "zone_count": 1, "site_name": "S1"},
        }
        freq = {"A": 10}
        result = _find_sites_with_unique(site_zones, freq, 10)
        assert result == {}

    def test_unique_found(self) -> None:
        site_zones = {
            "s1": {"zone_names": {"Rare"}, "zone_count": 1, "site_name": "S1"},
        }
        freq = {"Rare": 1}
        result = _find_sites_with_unique(site_zones, freq, 10)
        assert "s1" in result
        assert "Rare" in result["s1"]["unique_zones"]


class TestFindZoneCountDeviations:
    """Tests for _find_zone_count_deviations."""

    def test_no_std_dev(self) -> None:
        site_zones = {
            "s1": {"zone_count": 5, "site_name": "S1"},
        }
        result = _find_zone_count_deviations(site_zones, 5.0, 0.0)
        assert result == {}

    def test_deviation_detected(self) -> None:
        site_zones = {
            "s1": {"zone_count": 20, "site_name": "S1"},
        }
        result = _find_zone_count_deviations(site_zones, 5.0, 2.0)
        assert "s1" in result
        assert result["s1"]["deviation_score"] > 1.5

    def test_zero_count_with_positive_mean(self) -> None:
        site_zones = {
            "s1": {"zone_count": 0, "site_name": "S1"},
        }
        result = _find_zone_count_deviations(site_zones, 5.0, 2.0)
        assert "s1" in result


class TestDwellConfigKey:
    """Tests for _dwell_config_key."""

    def test_creates_key(self) -> None:
        tags = {
            "passerby": "1-300",
            "bounce": "301-14400",
            "engaged": "14401-36000",
            "stationed": "36001-86400",
        }
        key = _dwell_config_key(tags)
        assert "passerby=1-300" in key
        assert "bounce=301-14400" in key

    def test_missing_tags(self) -> None:
        key = _dwell_config_key({})
        assert "passerby=N/A" in key


class TestOccupancyConfigKey:
    """Tests for _occupancy_config_key."""

    def test_creates_key(self) -> None:
        occ = {"min_duration": 180, "clients_enabled": True}
        key = _occupancy_config_key(occ)
        assert "min_duration=180" in key
        assert "clients_enabled=True" in key

    def test_empty_config(self) -> None:
        key = _occupancy_config_key({})
        assert "min_duration=N/A" in key


class TestTrackCustomNames:
    """Tests for _track_custom_names."""

    def test_no_custom_names(self) -> None:
        usage: dict[str, dict[str, list[dict[str, Any]]]] = {}
        custom: dict[str, dict[str, Any]] = {}
        _track_custom_names("s1", "Site1", {}, usage, custom)
        assert custom == {}

    def test_custom_name_tracked(self) -> None:
        usage: dict[str, dict[str, list[dict[str, Any]]]] = {}
        custom: dict[str, dict[str, Any]] = {}
        _track_custom_names("s1", "Site1", {"passerby": "Walk-by"}, usage, custom)
        assert "s1" in custom
        assert custom["s1"]["custom_names"]["passerby"] == "Walk-by"
        assert "passerby" in usage
        assert "Walk-by" in usage["passerby"]

    def test_empty_string_ignored(self) -> None:
        usage: dict[str, dict[str, list[dict[str, Any]]]] = {}
        custom: dict[str, dict[str, Any]] = {}
        _track_custom_names("s1", "Site1", {"passerby": ""}, usage, custom)
        assert custom == {}


class TestFindDwellDeviations:
    """Tests for _find_dwell_deviations."""

    def test_no_deviations(self) -> None:
        configs = {
            "key1": [
                {"site_id": "s1", "site_name": "S1", "dwell_tags": {}},
            ],
        }
        result = _find_dwell_deviations(configs, ("key1", configs["key1"]))
        assert result == {}

    def test_deviation_found(self) -> None:
        configs = {
            "key1": [
                {"site_id": "s1", "site_name": "S1", "dwell_tags": {"a": "1"}},
            ],
            "key2": [
                {"site_id": "s2", "site_name": "S2", "dwell_tags": {"a": "2"}},
            ],
        }
        result = _find_dwell_deviations(configs, ("key1", configs["key1"]))
        assert "s2" in result

    def test_empty_most_common(self) -> None:
        result = _find_dwell_deviations({}, (None, []))
        assert result == {}


class TestFindOccupancyDeviations:
    """Tests for _find_occupancy_deviations."""

    def test_no_deviations(self) -> None:
        configs = {
            "k1": [
                {"site_id": "s1", "site_name": "S1", "occupancy": {}},
            ],
        }
        result = _find_occupancy_deviations(configs, ("k1", configs["k1"]))
        assert result == {}

    def test_deviation_found(self) -> None:
        configs = {
            "k1": [{"site_id": "s1", "site_name": "S1", "occupancy": {}}],
            "k2": [
                {"site_id": "s2", "site_name": "S2", "occupancy": {"x": 1}},
            ],
        }
        result = _find_occupancy_deviations(configs, ("k1", configs["k1"]))
        assert "s2" in result


class TestBuildOneSummaryRow:
    """Tests for _build_one_summary_row."""

    def test_minimal_row(self) -> None:
        row = _build_one_summary_row(
            "s1",
            {"site_name": "Site1", "zone_count": 3, "zone_names": {"A", "B"}},
            {
                "site_name": "Site1",
                "engagement": {"dwell_tags": {}, "dwell_tag_names": {}},
                "occupancy": {},
                "analytic": {},
            },
            {},
            {},
            {},
        )
        assert row["site_id"] == "s1"
        assert row["site_name"] == "Site1"
        assert row["zone_count"] == 3
        assert row["zone_deviation"] == "No"
        assert row["dwell_deviation"] == "No"
        assert row["occupancy_deviation"] == "No"


class TestBuildSummaryRows:
    """Tests for _build_summary_rows."""

    def test_empty_inputs(self) -> None:
        rows = _build_summary_rows({}, {}, {}, {}, {})
        assert rows == []

    def test_sorts_by_deviation(self) -> None:
        site_zones = {
            "s1": {"site_name": "A", "zone_count": 5, "zone_names": set()},
            "s2": {"site_name": "B", "zone_count": 5, "zone_names": set()},
        }
        site_settings = {
            "s1": {
                "site_name": "A",
                "engagement": {"dwell_tags": {}, "dwell_tag_names": {}},
                "occupancy": {},
                "analytic": {},
            },
            "s2": {
                "site_name": "B",
                "engagement": {"dwell_tags": {}, "dwell_tag_names": {}},
                "occupancy": {},
                "analytic": {},
            },
        }
        zone_a = {"zone_count_deviations": {"s1": {"score": 2}}}
        rows = _build_summary_rows(site_zones, site_settings, zone_a, {}, {})
        assert len(rows) == 2
        assert rows[0]["site_name"] == "A"


# ======================================================================
# Class method tests
# ======================================================================


class TestAnalyzeZonePatterns:
    """Tests for ZoneConfigurationAnalyzer._analyze_zone_patterns."""

    def test_empty_input(self) -> None:
        result = ZoneConfigurationAnalyzer._analyze_zone_patterns({})
        assert result["zone_frequency"] == {}
        assert result["common_zones"] == set()

    def test_basic_patterns(self) -> None:
        site_zones = {
            "s1": {
                "zone_count": 2,
                "zone_names": {"A", "B"},
                "site_name": "S1",
            },
            "s2": {
                "zone_count": 2,
                "zone_names": {"A", "B"},
                "site_name": "S2",
            },
            "s3": {
                "zone_count": 1,
                "zone_names": {"A"},
                "site_name": "S3",
            },
        }
        result = ZoneConfigurationAnalyzer._analyze_zone_patterns(site_zones)
        assert result["zone_frequency"]["A"] == 3
        assert result["zone_frequency"]["B"] == 2
        assert "A" in result["common_zones"]


class TestAnalyzeEngagementPatterns:
    """Tests for ZoneConfigurationAnalyzer._analyze_engagement_patterns."""

    def test_empty_input(self) -> None:
        result = ZoneConfigurationAnalyzer._analyze_engagement_patterns({})
        assert result["dwell_tag_configs"] == {}
        assert result["total_sites"] == 0

    def test_basic_patterns(self) -> None:
        settings = {
            "s1": {
                "site_name": "S1",
                "engagement": {
                    "dwell_tags": {"passerby": "1-300"},
                    "dwell_tag_names": {},
                    "hours": {},
                },
            },
            "s2": {
                "site_name": "S2",
                "engagement": {
                    "dwell_tags": {"passerby": "1-300"},
                    "dwell_tag_names": {},
                    "hours": {},
                },
            },
        }
        result = ZoneConfigurationAnalyzer._analyze_engagement_patterns(settings)
        assert result["total_sites"] == 2
        assert len(result["dwell_tag_configs"]) == 1

    def test_custom_names_tracked(self) -> None:
        settings = {
            "s1": {
                "site_name": "S1",
                "engagement": {
                    "dwell_tags": {},
                    "dwell_tag_names": {"passerby": "Walk-by"},
                    "hours": {},
                },
            },
        }
        result = ZoneConfigurationAnalyzer._analyze_engagement_patterns(settings)
        assert "s1" in result["sites_with_custom_names"]

    def test_business_hours_tracked(self) -> None:
        settings = {
            "s1": {
                "site_name": "S1",
                "engagement": {
                    "dwell_tags": {},
                    "dwell_tag_names": {},
                    "hours": {"mon": "09:00-17:00"},
                },
            },
        }
        result = ZoneConfigurationAnalyzer._analyze_engagement_patterns(settings)
        assert "s1" in result["sites_with_business_hours"]


class TestAnalyzeOccupancyPatterns:
    """Tests for ZoneConfigurationAnalyzer._analyze_occupancy_patterns."""

    def test_empty_input(self) -> None:
        result = ZoneConfigurationAnalyzer._analyze_occupancy_patterns({})
        assert result["occupancy_configs"] == {}
        assert result["total_sites"] == 0

    def test_basic_patterns(self) -> None:
        settings = {
            "s1": {
                "site_name": "S1",
                "occupancy": {"min_duration": 180},
                "analytic": {"enabled": True},
            },
            "s2": {
                "site_name": "S2",
                "occupancy": {"min_duration": 180},
                "analytic": {"enabled": False},
            },
        }
        result = ZoneConfigurationAnalyzer._analyze_occupancy_patterns(settings)
        assert result["analytic_enabled_count"] == 1
        assert result["analytic_disabled_count"] == 1
        assert result["total_sites"] == 2


class TestDisplayResults:
    """Tests for display methods (smoke tests)."""

    def test_display_results_empty(self, capsys: pytest.CaptureFixture[str]) -> None:
        ZoneConfigurationAnalyzer._display_results({})
        out = capsys.readouterr().out
        assert "ZONE & ENGAGEMENT" in out

    def test_display_zone_section(self, capsys: pytest.CaptureFixture[str]) -> None:
        zone_analysis = {
            "zone_count_stats": {
                "total_sites": 10,
                "sites_with_zones": 8,
                "mean": 5.0,
                "median": 5,
                "min": 2,
                "max": 8,
                "std_dev": 1.5,
            },
            "common_zones": {"A", "B"},
            "zone_frequency": {"A": 8, "B": 7},
            "sites_missing_common_zones": {},
            "zone_count_deviations": {},
        }
        ZoneConfigurationAnalyzer._display_zone_section(zone_analysis)
        out = capsys.readouterr().out
        assert "ZONE ANALYSIS" in out
        assert "Total sites scanned: 10" in out

    def test_display_engagement_section(self, capsys: pytest.CaptureFixture[str]) -> None:
        engagement = {
            "dwell_tag_configs": {
                "k1": [{"dwell_tags": {"passerby": "1-300"}}],
            },
            "most_common_config": (
                "k1",
                [{"dwell_tags": {"passerby": "1-300"}}],
            ),
            "sites_with_dwell_deviations": {},
            "sites_with_custom_names": {},
            "sites_with_business_hours": {},
        }
        ZoneConfigurationAnalyzer._display_engagement_section(engagement)
        out = capsys.readouterr().out
        assert "ENGAGEMENT ANALYSIS" in out

    def test_display_occupancy_section(self, capsys: pytest.CaptureFixture[str]) -> None:
        occupancy = {
            "total_sites": 5,
            "analytic_enabled_count": 3,
            "analytic_disabled_count": 2,
            "occupancy_configs": {},
            "most_common_config": (None, []),
            "sites_with_occupancy_deviations": {},
            "min_duration_values": {},
        }
        ZoneConfigurationAnalyzer._display_occupancy_section(occupancy)
        out = capsys.readouterr().out
        assert "OCCUPANCY ANALYSIS" in out
        assert "Enabled: 3" in out


class TestDisplayHelpersBranches:
    """Cover display helper branches with data present."""

    def test_display_missing_zones_with_data(self, capsys: pytest.CaptureFixture[str]) -> None:
        from src.analytics.zone_analyzer import _display_missing_zones

        zone_analysis = {
            "sites_missing_common_zones": {
                "s1": {"site_name": "S1", "missing_zones": {"X", "Y"}},
            },
        }
        _display_missing_zones(zone_analysis)
        out = capsys.readouterr().out
        assert "S1" in out
        assert "Missing:" in out

    def test_display_zone_deviations_with_data(self, capsys: pytest.CaptureFixture[str]) -> None:
        from src.analytics.zone_analyzer import _display_zone_deviations

        zone_analysis = {
            "zone_count_deviations": {
                "s1": {
                    "site_name": "S1",
                    "zone_count": 20,
                    "expected_range": "3-7",
                    "deviation_score": 5.0,
                },
            },
        }
        _display_zone_deviations(zone_analysis)
        out = capsys.readouterr().out
        assert "S1" in out
        assert "20 zones" in out

    def test_display_custom_names_with_data(self, capsys: pytest.CaptureFixture[str]) -> None:
        from src.analytics.zone_analyzer import _display_custom_names

        engagement = {
            "sites_with_custom_names": {
                "s1": {
                    "site_name": "S1",
                    "custom_names": {"passerby": "Walk-by"},
                },
            },
        }
        _display_custom_names(engagement)
        out = capsys.readouterr().out
        assert "Walk-by" in out

    def test_display_business_hours_few_sites(self, capsys: pytest.CaptureFixture[str]) -> None:
        from src.analytics.zone_analyzer import _display_business_hours

        engagement = {
            "sites_with_business_hours": {
                "s1": {"site_name": "S1"},
                "s2": {"site_name": "S2"},
            },
        }
        _display_business_hours(engagement)
        out = capsys.readouterr().out
        assert "S1" in out
        assert "S2" in out

    def test_display_business_hours_many_sites(self, capsys: pytest.CaptureFixture[str]) -> None:
        from src.analytics.zone_analyzer import _display_business_hours

        many = {f"s{i}": {"site_name": f"S{i}"} for i in range(10)}
        engagement = {"sites_with_business_hours": many}
        _display_business_hours(engagement)
        out = capsys.readouterr().out
        assert "10 sites have business hours" in out

    def test_display_occupancy_configs_with_data(self, capsys: pytest.CaptureFixture[str]) -> None:
        from src.analytics.zone_analyzer import _display_occupancy_configs

        occupancy = {
            "most_common_config": (
                "k1",
                [{"occupancy": {"min_duration": 180, "clients_enabled": True}}],
            ),
            "occupancy_configs": {"k1": []},
            "min_duration_values": {180: 8, 300: 2},
        }
        _display_occupancy_configs(occupancy)
        out = capsys.readouterr().out
        assert "min_duration: 180" in out
        assert "Min Duration Distribution" in out

    def test_display_dwell_deviations_with_data(self, capsys: pytest.CaptureFixture[str]) -> None:
        from src.analytics.zone_analyzer import _display_dwell_deviations

        engagement = {
            "sites_with_dwell_deviations": {
                "s1": {
                    "site_name": "S1",
                    "current_config": {"passerby": "1-300", "bounce": "301-600"},
                },
            },
        }
        _display_dwell_deviations(engagement)
        out = capsys.readouterr().out
        assert "S1" in out
        assert "passerby=1-300" in out

    def test_display_occupancy_deviations_with_data(self, capsys: pytest.CaptureFixture[str]) -> None:
        from src.analytics.zone_analyzer import _display_occupancy_deviations

        occupancy = {
            "sites_with_occupancy_deviations": {
                "s1": {
                    "site_name": "S1",
                    "current_config": {"min_duration": 999, "clients_enabled": False},
                },
            },
        }
        _display_occupancy_deviations(occupancy)
        out = capsys.readouterr().out
        assert "S1" in out


class TestCollectSuccessPaths:
    """Test the HTTP 200 success paths in collect methods."""

    def test_collect_zones_success(self, mock_apisession: MagicMock) -> None:
        sites = [{"id": "s1", "name": "Site1"}]
        resp = MagicMock()
        resp.status_code = 200
        resp.data = [{"name": "ZoneA", "id": "z1"}, {"name": "ZoneB", "id": "z2"}]
        mock_fn = _mock_mistapi.api.v1.sites.zones.listSiteZones
        mock_fn.side_effect = None
        mock_fn.return_value = resp

        result = ZoneConfigurationAnalyzer._collect_all_site_zones(
            apisession=mock_apisession,
            org_id="org-1",
            all_sites_fn=lambda _: sites,
            check_stop_fn=lambda: False,
        )
        assert result["s1"]["zone_count"] == 2
        assert "ZoneA" in result["s1"]["zone_names"]
        assert "ZoneB" in result["s1"]["zone_names"]

    def test_collect_settings_success(self, mock_apisession: MagicMock) -> None:
        sites = [{"id": "s1", "name": "Site1"}]
        resp = MagicMock()
        resp.status_code = 200
        resp.data = {
            "engagement": {
                "dwell_tags": {"passerby": "1-300"},
                "dwell_tag_names": {"passerby": "Walk-by"},
                "hours": {"mon": "09:00-17:00"},
            },
            "occupancy": {"min_duration": 180},
            "analytic": {"enabled": True},
        }
        mock_fn = _mock_mistapi.api.v1.sites.setting.getSiteSetting
        mock_fn.side_effect = None
        mock_fn.return_value = resp

        result = ZoneConfigurationAnalyzer._collect_all_site_settings(
            apisession=mock_apisession,
            org_id="org-1",
            all_sites_fn=lambda _: sites,
            check_stop_fn=lambda: False,
        )
        assert result["s1"]["engagement"]["dwell_tags"]["passerby"] == "1-300"
        assert result["s1"]["occupancy"]["min_duration"] == 180
        assert result["s1"]["analytic"]["enabled"] is True


class TestExportHelpersBranches:
    """Test export helper functions with actual data."""

    def test_export_all_zones(self, capsys: pytest.CaptureFixture[str]) -> None:
        from src.analytics.zone_analyzer import _export_all_zones

        save_fn = MagicMock()
        site_zones = {
            "s1": {
                "site_name": "S1",
                "zones": [
                    {"id": "z1", "name": "Lobby", "map_id": "m1", "vertices": [1, 2]},
                ],
            },
        }
        _export_all_zones(site_zones, "20250101", save_fn)
        save_fn.assert_called_once()
        rows = save_fn.call_args[0][0]
        assert rows[0]["zone_name"] == "Lobby"
        assert rows[0]["vertex_count"] == 2

    def test_export_zone_frequency(self, capsys: pytest.CaptureFixture[str]) -> None:
        from src.analytics.zone_analyzer import _export_zone_frequency

        save_fn = MagicMock()
        zone_analysis = {
            "zone_frequency": {"A": 8, "B": 3},
            "zone_count_stats": {"sites_with_zones": 10},
            "common_zones": {"A"},
        }
        _export_zone_frequency(zone_analysis, "20250101", save_fn)
        save_fn.assert_called_once()
        rows = save_fn.call_args[0][0]
        assert rows[0]["zone_name"] == "A"
        assert rows[0]["is_common"] == "Yes"

    def test_export_dwell_configs(self) -> None:
        from src.analytics.zone_analyzer import _export_dwell_configs

        save_fn = MagicMock()
        engagement = {
            "dwell_tag_configs": {
                "k1": [
                    {
                        "site_id": "s1",
                        "site_name": "S1",
                        "dwell_tags": {"passerby": "1-300"},
                    },
                ],
            },
        }
        _export_dwell_configs(engagement, "20250101", save_fn)
        save_fn.assert_called_once()

    def test_export_occupancy_configs(self) -> None:
        from src.analytics.zone_analyzer import _export_occupancy_configs

        save_fn = MagicMock()
        occupancy = {
            "occupancy_configs": {
                "k1": [
                    {
                        "site_id": "s1",
                        "site_name": "S1",
                        "occupancy": {"min_duration": 180},
                    },
                ],
            },
        }
        _export_occupancy_configs(occupancy, "20250101", save_fn)
        save_fn.assert_called_once()


class TestExportResults:
    """Tests for export methods."""

    def test_export_calls_save_data(self) -> None:
        save_fn = MagicMock()
        combined = {
            "zones": {
                "zone_frequency": {"A": 5},
                "common_zones": {"A"},
                "zone_count_stats": {"sites_with_zones": 5},
            },
            "engagement": {
                "dwell_tag_configs": {
                    "k1": [
                        {
                            "site_id": "s1",
                            "site_name": "S1",
                            "dwell_tags": {},
                        }
                    ],
                },
            },
            "occupancy": {
                "occupancy_configs": {
                    "k1": [
                        {
                            "site_id": "s1",
                            "site_name": "S1",
                            "occupancy": {},
                        }
                    ],
                },
            },
        }
        site_zones = {
            "s1": {
                "site_name": "S1",
                "zones": [{"name": "A", "id": "z1"}],
                "zone_names": {"A"},
                "zone_count": 1,
            },
        }
        site_settings = {
            "s1": {
                "site_name": "S1",
                "engagement": {"dwell_tags": {}, "dwell_tag_names": {}},
                "occupancy": {},
                "analytic": {},
            },
        }
        ZoneConfigurationAnalyzer._export_results(combined, site_zones, site_settings, save_data_fn=save_fn)
        assert save_fn.call_count >= 4


class TestAnalyzeIntegration:
    """Integration tests for the analyze() entry point."""

    def test_no_org_id(
        self,
        mock_deps: dict[str, Any],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        mock_deps["get_org_id_fn"].return_value = None
        ZoneConfigurationAnalyzer.analyze(**mock_deps)
        out = capsys.readouterr().out
        assert "No organization selected" in out

    def test_no_sites(
        self,
        mock_deps: dict[str, Any],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        mock_deps["all_sites_fn"].return_value = []
        ZoneConfigurationAnalyzer.analyze(**mock_deps)
        out = capsys.readouterr().out
        assert "No data collected" in out

    def test_with_sites_and_zones(
        self,
        mock_deps: dict[str, Any],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        sites = [{"id": "s1", "name": "TestSite"}]
        mock_deps["all_sites_fn"].return_value = sites

        zone_resp = MagicMock()
        zone_resp.status_code = 200
        zone_resp.data = [{"name": "ZoneA", "id": "z1"}]

        setting_resp = MagicMock()
        setting_resp.status_code = 200
        setting_resp.data = {
            "engagement": {
                "dwell_tags": {"passerby": "1-300"},
                "dwell_tag_names": {},
                "hours": {},
            },
            "occupancy": {"min_duration": 180},
            "analytic": {"enabled": True},
        }

        _mock_mistapi.api.v1.sites.zones.listSiteZones.return_value = zone_resp
        _mock_mistapi.api.v1.sites.setting.getSiteSetting.return_value = setting_resp

        ZoneConfigurationAnalyzer.analyze(**mock_deps)
        out = capsys.readouterr().out
        assert "ZONE & ENGAGEMENT" in out
        mock_deps["save_data_fn"].assert_called()

    def test_api_error_handled(
        self,
        mock_deps: dict[str, Any],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        sites = [{"id": "s1", "name": "ErrSite"}]
        mock_deps["all_sites_fn"].return_value = sites

        _mock_mistapi.api.v1.sites.zones.listSiteZones.side_effect = RuntimeError("API timeout")
        _mock_mistapi.api.v1.sites.setting.getSiteSetting.side_effect = RuntimeError("API timeout")

        ZoneConfigurationAnalyzer.analyze(**mock_deps)
        out = capsys.readouterr().out
        assert "ZONE & ENGAGEMENT" in out

    def test_stop_signal_respected(
        self,
        mock_deps: dict[str, Any],
    ) -> None:
        sites = [
            {"id": "s1", "name": "S1"},
            {"id": "s2", "name": "S2"},
        ]
        mock_deps["all_sites_fn"].return_value = sites
        mock_deps["check_stop_fn"].return_value = True

        zone_resp = MagicMock()
        zone_resp.status_code = 200
        zone_resp.data = []
        zone_mock = _mock_mistapi.api.v1.sites.zones.listSiteZones
        zone_mock.side_effect = None
        zone_mock.return_value = zone_resp
        zone_mock.reset_mock()

        setting_resp = MagicMock()
        setting_resp.status_code = 200
        setting_resp.data = {}
        setting_mock = _mock_mistapi.api.v1.sites.setting.getSiteSetting
        setting_mock.side_effect = None
        setting_mock.return_value = setting_resp
        setting_mock.reset_mock()

        ZoneConfigurationAnalyzer.analyze(**mock_deps)
        # Should have stopped early without processing any sites
        zone_mock.assert_not_called()


class TestCollectAllSiteZones:
    """Tests for _collect_all_site_zones."""

    def test_non_200_response(
        self,
        mock_apisession: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        sites = [{"id": "s1", "name": "FailSite"}]
        resp = MagicMock()
        resp.status_code = 500
        _mock_mistapi.api.v1.sites.zones.listSiteZones.return_value = resp

        result = ZoneConfigurationAnalyzer._collect_all_site_zones(
            apisession=mock_apisession,
            org_id="org-1",
            all_sites_fn=lambda _: sites,
            check_stop_fn=lambda: False,
        )
        assert result["s1"]["zone_count"] == 0

    def test_exception_handled(
        self,
        mock_apisession: MagicMock,
    ) -> None:
        sites = [{"id": "s1", "name": "ExcSite"}]
        _mock_mistapi.api.v1.sites.zones.listSiteZones.side_effect = ValueError("boom")

        result = ZoneConfigurationAnalyzer._collect_all_site_zones(
            apisession=mock_apisession,
            org_id="org-1",
            all_sites_fn=lambda _: sites,
            check_stop_fn=lambda: False,
        )
        assert result["s1"]["zone_count"] == 0


class TestCollectAllSiteSettings:
    """Tests for _collect_all_site_settings."""

    def test_non_200_response(
        self,
        mock_apisession: MagicMock,
    ) -> None:
        sites = [{"id": "s1", "name": "FailSite"}]
        resp = MagicMock()
        resp.status_code = 403
        _mock_mistapi.api.v1.sites.setting.getSiteSetting.return_value = resp

        result = ZoneConfigurationAnalyzer._collect_all_site_settings(
            apisession=mock_apisession,
            org_id="org-1",
            all_sites_fn=lambda _: sites,
            check_stop_fn=lambda: False,
        )
        assert result["s1"]["engagement"]["dwell_tags"] == {}

    def test_exception_handled(
        self,
        mock_apisession: MagicMock,
    ) -> None:
        sites = [{"id": "s1", "name": "ExcSite"}]
        _mock_mistapi.api.v1.sites.setting.getSiteSetting.side_effect = ValueError("boom")

        result = ZoneConfigurationAnalyzer._collect_all_site_settings(
            apisession=mock_apisession,
            org_id="org-1",
            all_sites_fn=lambda _: sites,
            check_stop_fn=lambda: False,
        )
        assert result["s1"]["engagement"]["dwell_tags"] == {}


# ===========================================================================
# Display functions: >10 items paths (lines 760, 774, 809, 826, 888)
# ===========================================================================


class TestDisplayMoreThanTen:
    """Tests that cover the '... and X more sites' paths in display functions."""

    def test_display_missing_zones_more_than_ten(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Line 760: 11+ sites with missing zones → overflow count message printed."""
        from src.analytics.zone_analyzer import _display_missing_zones  # private fn under test

        missing = {  # build 11-item dict so len > 10 branch fires
            f"site-{i}": {"site_name": f"Site {i}", "missing_zones": ["ZoneA"]} for i in range(11)
        }
        _display_missing_zones({"sites_missing_common_zones": missing})  # call with 11 items
        assert "and 1 more" in capsys.readouterr().out  # overflow message expected

    def test_display_zone_deviations_more_than_ten(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Line 774: 11+ deviating sites → overflow count message printed."""
        from src.analytics.zone_analyzer import _display_zone_deviations  # private fn under test

        devs = {  # build 11-item dict so len > 10 branch fires
            f"site-{i}": {
                "site_name": f"Site {i}",
                "zone_count": 5,
                "expected_range": "3-7",
                "deviation_score": 1.2,
            }
            for i in range(11)
        }
        _display_zone_deviations({"zone_count_deviations": devs})  # call with 11 items
        assert "and 1 more" in capsys.readouterr().out  # overflow message expected

    def test_display_dwell_deviations_more_than_ten(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Line 809: 11+ dwell deviating sites → overflow count message printed."""
        from src.analytics.zone_analyzer import _display_dwell_deviations  # private fn

        devs = {  # build 11-item dict with required current_config fields
            f"site-{i}": {
                "site_name": f"Site {i}",
                "current_config": {
                    "passerby": "60",
                    "bounce": "360",
                    "engaged": "3600",
                    "stationed": "14400",
                },
            }
            for i in range(11)
        }
        _display_dwell_deviations({"sites_with_dwell_deviations": devs})  # call with 11 items
        assert "and 1 more" in capsys.readouterr().out  # overflow message expected

    def test_display_custom_names_more_than_ten(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Line 826: 11+ sites with custom names → overflow count message printed."""
        from src.analytics.zone_analyzer import _display_custom_names  # private fn under test

        custom = {  # build 11-item dict so len > 10 branch fires
            f"site-{i}": {
                "site_name": f"Site {i}",
                "custom_names": {"passerby": "Visitor"},
            }
            for i in range(11)
        }
        _display_custom_names({"sites_with_custom_names": custom})  # call with 11 items
        assert "and 1 more" in capsys.readouterr().out  # overflow message expected

    def test_display_occupancy_deviations_more_than_ten(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Line 888: 11+ occupancy deviating sites → overflow count message printed."""
        from src.analytics.zone_analyzer import _display_occupancy_deviations  # private fn

        devs = {  # build 11-item dict with required current_config fields
            f"site-{i}": {
                "site_name": f"Site {i}",
                "current_config": {
                    "min_duration": 180,
                    "clients_enabled": True,
                    "unconnected_clients_enabled": False,
                },
            }
            for i in range(11)
        }
        _display_occupancy_deviations({"sites_with_occupancy_deviations": devs})  # 11 items
        assert "and 1 more" in capsys.readouterr().out  # overflow message expected


# ===========================================================================
# Export functions: early-return paths (lines 916, 1026, 1086, 1116)
# ===========================================================================


class TestExportEarlyReturns:
    """Tests that cover early-return paths in export functions when inputs are empty."""

    def test_export_summary_empty_rows(self) -> None:
        """Line 916: _export_summary returns early when _build_summary_rows produces no rows."""
        from src.analytics.zone_analyzer import _export_summary  # private fn under test

        save_fn = MagicMock()  # spy on whether the save function is ever called
        _export_summary({}, {}, {}, {}, {}, "20250101", save_fn)  # all-empty inputs
        save_fn.assert_not_called()  # early return before save_data_fn reached

    def test_export_all_zones_empty_input(self) -> None:
        """Line 1026: _export_all_zones returns early when site_zones is empty."""
        from src.analytics.zone_analyzer import _export_all_zones  # private fn under test

        save_fn = MagicMock()  # spy on whether the save function is ever called
        _export_all_zones({}, "20250101", save_fn)  # empty site_zones dict
        save_fn.assert_not_called()  # early return before save reached

    def test_export_dwell_configs_empty_input(self) -> None:
        """Line 1086: _export_dwell_configs returns early when dwell_tag_configs absent."""
        from src.analytics.zone_analyzer import _export_dwell_configs  # private fn under test

        save_fn = MagicMock()  # spy on whether the save function is ever called
        _export_dwell_configs({}, "20250101", save_fn)  # no dwell_tag_configs key in dict
        save_fn.assert_not_called()  # early return before save reached

    def test_export_occupancy_configs_empty_input(self) -> None:
        """Line 1116: _export_occupancy_configs returns early when occupancy_configs absent."""
        from src.analytics.zone_analyzer import _export_occupancy_configs  # private fn

        save_fn = MagicMock()  # spy on whether the save function is ever called
        _export_occupancy_configs({}, "20250101", save_fn)  # no occupancy_configs key in dict
        save_fn.assert_not_called()  # early return before save reached
