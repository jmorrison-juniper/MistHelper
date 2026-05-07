"""Tests for src.firmware.org_ap_upgrader -- OrgLevelAPFirmwareUpgrader.

Covers: initialization, MSP mode selection, MSP/org selection, site scope,
AP discovery, firmware stats, version selection, upgrade configuration,
scheduling/time parsing, confirmation, execution (dry-run and live),
results writing, and selection parsing utilities.
"""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

_mock_mistapi = MagicMock()
with patch.dict(
    sys.modules,
    {
        "mistapi": _mock_mistapi,
        "mistapi.api": MagicMock(),
        "mistapi.api.v1": MagicMock(),
        "mistapi.api.v1.orgs": MagicMock(),
        "mistapi.api.v1.orgs.devices": MagicMock(),
        "mistapi.api.v1.orgs.inventory": MagicMock(),
        "mistapi.api.v1.orgs.stats": MagicMock(),
        "mistapi.api.v1.msps": MagicMock(),
        "mistapi.api.v1.msps.orgs": MagicMock(),
        "mistapi.api.v1.sites": MagicMock(),
        "mistapi.api.v1.sites.devices": MagicMock(),
    },
):
    from src.firmware.org_ap_upgrader import OrgLevelAPFirmwareUpgrader


# ===================================================================
# Helpers
# ===================================================================

SAMPLE_SITE = {"id": "site-001", "name": "HQ"}
SAMPLE_SITE_2 = {"id": "site-002", "name": "Branch-1"}
SAMPLE_AP = {
    "id": "ap-001",
    "name": "AP-Lobby",
    "mac": "aa:bb:cc:dd:ee:01",
    "model": "AP45",
    "type": "ap",
    "_site_id": "site-001",
    "_site_name": "HQ",
}
SAMPLE_AP_2 = {
    "id": "ap-002",
    "name": "AP-Conf",
    "mac": "aa:bb:cc:dd:ee:02",
    "model": "AP45",
    "type": "ap",
    "_site_id": "site-001",
    "_site_name": "HQ",
}
SAMPLE_AP_3 = {
    "id": "ap-003",
    "name": "AP-Floor2",
    "mac": "aa:bb:cc:dd:ee:03",
    "model": "AP34",
    "type": "ap",
    "_site_id": "site-002",
    "_site_name": "Branch-1",
}
SAMPLE_MSP = {"msp_id": "msp-001", "msp_name": "Test MSP", "role": "admin"}
SAMPLE_MSP_2 = {"msp_id": "msp-002", "msp_name": "Test MSP 2", "role": "admin"}
SAMPLE_ORG = {"id": "org-456", "name": "Test Org"}
SAMPLE_ORG_2 = {"id": "org-789", "name": "Other Org"}

SAMPLE_VERSION_INFO = {
    "version": "0.14.29411",
    "model": "AP45",
    "models": ["AP45"],
    "recommended": True,
}
SAMPLE_VERSION_INFO_2 = {
    "version": "0.14.29000",
    "model": "AP45",
    "models": ["AP45"],
}
SAMPLE_VERSION_AP34 = {
    "version": "0.14.29411",
    "model": "AP34",
    "models": ["AP34"],
    "recommended": True,
}


def _make_upgrader(**kwargs):
    """Create an OrgLevelAPFirmwareUpgrader with sensible defaults."""
    defaults = {
        "org_id": "org-123",
        "apisession": MagicMock(),
        "dry_run": True,
        "safe_input_fn": MagicMock(return_value=""),
        "check_stop_fn": MagicMock(return_value=False),
        "fetch_sites_fn": MagicMock(return_value=[SAMPLE_SITE]),
        "get_org_id_fn": MagicMock(return_value="org-123"),
        "write_results_fn": MagicMock(),
        "is_debug_fn": MagicMock(return_value=False),
        "msp_privileges": [],
        "selected_msp": None,
    }
    defaults.update(kwargs)
    return OrgLevelAPFirmwareUpgrader(**defaults)


def _make_api_response(data):
    """Create a mock API response with .data attribute."""
    resp = MagicMock()
    resp.data = data
    return resp


# ===================================================================
# Initialization
# ===================================================================


class TestInit:
    """Constructor and initialization tests."""

    def test_defaults(self):
        u = _make_upgrader()
        assert u.org_id == "org-123"
        assert u.dry_run is True
        assert u.target_all_sites is True
        assert u.all_aps == []
        assert u.aps_by_model == {}
        assert u.upgrade_plan == {}
        assert u.results == []
        assert u.successful_api_calls == 0

    def test_msp_privileges(self):
        u = _make_upgrader(msp_privileges=[SAMPLE_MSP])
        assert len(u._msp_privileges) == 1

    def test_selected_msp(self):
        u = _make_upgrader(selected_msp=SAMPLE_MSP)
        assert u._selected_msp == SAMPLE_MSP

    def test_dry_run_false(self):
        u = _make_upgrader(dry_run=False)
        assert u.dry_run is False


# ===================================================================
# Selection Parsing
# ===================================================================


class TestParseSelection:
    """Tests for _parse_selection instance method."""

    def test_single_number(self):
        u = _make_upgrader()
        assert u._parse_selection("1", 5) == [0]

    def test_multiple_comma(self):
        u = _make_upgrader()
        assert u._parse_selection("1,3,5", 5) == [0, 2, 4]

    def test_range_dash(self):
        u = _make_upgrader()
        assert u._parse_selection("1-3", 5) == [0, 1, 2]

    def test_through_keyword(self):
        u = _make_upgrader()
        assert u._parse_selection("1 through 3", 5) == [0, 1, 2]

    def test_out_of_range(self):
        u = _make_upgrader()
        assert u._parse_selection("10", 5) == []

    def test_invalid_text(self):
        u = _make_upgrader()
        assert u._parse_selection("abc", 5) == []

    def test_mixed_input(self):
        u = _make_upgrader()
        result = u._parse_selection("1,3", 5)
        assert result == [0, 2]

    def test_dedup(self):
        u = _make_upgrader()
        result = u._parse_selection("1,1,1", 5)
        assert result == [0]

    def test_empty_string(self):
        u = _make_upgrader()
        assert u._parse_selection("", 5) == []


# ===================================================================
# Site Scope Selection (Step 1)
# ===================================================================


class TestSiteScope:
    """Tests for _step1_select_site_scope."""

    def test_all_sites(self):
        u = _make_upgrader(safe_input_fn=MagicMock(return_value="1"))
        result = u._step1_select_site_scope()
        assert result is True
        assert u.target_all_sites is True

    def test_specific_sites(self):
        u = _make_upgrader(
            safe_input_fn=MagicMock(side_effect=["2", "1"]),
            fetch_sites_fn=MagicMock(return_value=[SAMPLE_SITE, SAMPLE_SITE_2]),
        )
        result = u._step1_select_site_scope()
        assert result is True
        assert u.target_all_sites is False
        assert len(u.selected_site_ids) == 1

    def test_invalid_choice(self):
        u = _make_upgrader(safe_input_fn=MagicMock(return_value="9"))
        result = u._step1_select_site_scope()
        assert result is False

    def test_eof_exit(self):
        u = _make_upgrader(safe_input_fn=MagicMock(side_effect=SystemExit))
        result = u._step1_select_site_scope()
        assert result is False

    def test_select_all_from_specific(self):
        u = _make_upgrader(
            safe_input_fn=MagicMock(side_effect=["2", "all"]),
            fetch_sites_fn=MagicMock(return_value=[SAMPLE_SITE]),
        )
        result = u._step1_select_site_scope()
        assert result is True
        assert u.target_all_sites is True

    def test_cancel_site_selection(self):
        u = _make_upgrader(
            safe_input_fn=MagicMock(side_effect=["2", "q"]),
            fetch_sites_fn=MagicMock(return_value=[SAMPLE_SITE]),
        )
        result = u._step1_select_site_scope()
        assert result is False

    def test_no_sites_found(self):
        u = _make_upgrader(
            safe_input_fn=MagicMock(side_effect=["2"]),
            fetch_sites_fn=MagicMock(return_value=[]),
        )
        result = u._step1_select_site_scope()
        assert result is False


# ===================================================================
# AP Discovery (Step 2)
# ===================================================================


class TestAPDiscovery:
    """Tests for _step2_discover_aps."""

    def test_org_aps_found(self):
        u = _make_upgrader()
        u.target_all_sites = True
        mock_resp = _make_api_response([SAMPLE_AP, SAMPLE_AP_2])

        with (
            patch.dict(sys.modules, {"mistapi": _mock_mistapi}),
            patch("importlib.import_module") as mock_import,
            patch.object(_mock_mistapi, "get_all", return_value=[SAMPLE_AP, SAMPLE_AP_2]),
        ):
            mock_inv = MagicMock()
            mock_inv.getOrgInventory.return_value = mock_resp
            mock_import.return_value = mock_inv
            result = u._step2_discover_aps()

        assert result is True
        assert len(u.all_aps) == 2
        assert "AP45" in u.aps_by_model

    def test_no_aps_found(self):
        u = _make_upgrader()
        u.target_all_sites = True

        with (
            patch.dict(sys.modules, {"mistapi": _mock_mistapi}),
            patch("importlib.import_module") as mock_import,
            patch.object(_mock_mistapi, "get_all", return_value=[]),
        ):
            mock_inv = MagicMock()
            mock_inv.getOrgInventory.return_value = _make_api_response([])
            mock_import.return_value = mock_inv
            result = u._step2_discover_aps()

        assert result is False

    def test_selected_sites_aps(self):
        u = _make_upgrader()
        u.target_all_sites = False
        u.selected_sites = [SAMPLE_SITE]
        u.selected_site_ids = ["site-001"]

        import mistapi.api.v1.sites.devices as mock_site_devices

        mock_site_devices.listSiteDevices.return_value = _make_api_response([SAMPLE_AP])

        result = u._step2_discover_aps()
        assert result is True
        assert len(u.all_aps) == 1

    def test_api_session_none(self):
        u = _make_upgrader(apisession=None)
        u.target_all_sites = True
        result = u._fetch_org_aps()
        assert result is False


class TestFilterAPs:
    """Tests for _filter_ap_devices."""

    def test_filters_by_type(self):
        devices = [
            {"type": "ap", "model": "AP45"},
            {"type": "switch", "model": "EX4300"},
        ]
        result = OrgLevelAPFirmwareUpgrader._filter_ap_devices(devices)
        assert len(result) == 1
        assert result[0]["model"] == "AP45"

    def test_filters_by_model_prefix(self):
        devices = [{"model": "AP34", "type": "unknown"}]
        result = OrgLevelAPFirmwareUpgrader._filter_ap_devices(devices)
        assert len(result) == 1

    def test_empty_list(self):
        assert OrgLevelAPFirmwareUpgrader._filter_ap_devices([]) == []


# ===================================================================
# Firmware Stats (Step 3)
# ===================================================================


class TestFirmwareStats:
    """Tests for _step3_fetch_firmware_stats."""

    def test_populates_versions(self):
        u = _make_upgrader()
        u.all_aps = [SAMPLE_AP, SAMPLE_AP_2]

        stats = [
            {"mac": "aa:bb:cc:dd:ee:01", "version": "0.14.29000"},
            {"mac": "aa:bb:cc:dd:ee:02", "version": "0.14.29411"},
        ]

        with (
            patch.dict(sys.modules, {"mistapi": _mock_mistapi}),
            patch("importlib.import_module") as mock_import,
            patch.object(_mock_mistapi, "get_all", return_value=stats),
        ):
            mock_stats = MagicMock()
            mock_stats.listOrgDevicesStats.return_value = _make_api_response(stats)
            mock_import.return_value = mock_stats
            result = u._step3_fetch_firmware_stats()

        assert result is True
        assert u.ap_versions["aa:bb:cc:dd:ee:01"] == "0.14.29000"
        assert u.ap_versions["aa:bb:cc:dd:ee:02"] == "0.14.29411"

    def test_api_session_none(self):
        u = _make_upgrader(apisession=None)
        result = u._step3_fetch_firmware_stats()
        assert result is False

    def test_unknown_firmware(self):
        u = _make_upgrader()
        u.all_aps = [SAMPLE_AP]
        unknown = u._get_unknown_firmware_devices()
        assert len(unknown) == 1


class TestVersionCounting:
    """Tests for _count_versions_by_mac."""

    def test_counts_versions(self):
        u = _make_upgrader()
        u.all_aps = [SAMPLE_AP, SAMPLE_AP_2]
        u.ap_versions = {
            "aa:bb:cc:dd:ee:01": "0.14.29000",
            "aa:bb:cc:dd:ee:02": "0.14.29000",
        }
        counts = u._count_versions_by_mac()
        assert counts["0.14.29000"] == 2

    def test_unknown_counted(self):
        u = _make_upgrader()
        u.all_aps = [SAMPLE_AP]
        u.ap_versions = {}
        counts = u._count_versions_by_mac()
        assert counts["Unknown"] == 1


# ===================================================================
# Available Firmware (Step 4)
# ===================================================================


class TestAvailableFirmware:
    """Tests for _step4_fetch_available_firmware."""

    def test_loads_versions(self):
        u = _make_upgrader()
        u.aps_by_model = {"AP45": [SAMPLE_AP]}

        with patch("importlib.import_module") as mock_import:
            mock_dev = MagicMock()
            mock_dev.listOrgAvailableDeviceVersions.return_value = _make_api_response([SAMPLE_VERSION_INFO])
            mock_import.return_value = mock_dev
            result = u._step4_fetch_available_firmware()

        assert result is True
        assert "AP45" in u.model_version_ranges

    def test_no_versions(self):
        u = _make_upgrader()
        u.aps_by_model = {"AP45": [SAMPLE_AP]}

        with patch("importlib.import_module") as mock_import:
            mock_dev = MagicMock()
            mock_dev.listOrgAvailableDeviceVersions.return_value = _make_api_response([])
            mock_import.return_value = mock_dev
            result = u._step4_fetch_available_firmware()

        assert result is False

    def test_api_session_none(self):
        u = _make_upgrader(apisession=None)
        result = u._step4_fetch_available_firmware()
        assert result is False


# ===================================================================
# Version Selection (Step 5)
# ===================================================================


class TestVersionSelection:
    """Tests for _step5_select_firmware_versions."""

    def test_selects_version(self):
        u = _make_upgrader(safe_input_fn=MagicMock(return_value="0"))
        u.aps_by_model = {"AP45": [SAMPLE_AP, SAMPLE_AP_2]}
        u.available_versions = [SAMPLE_VERSION_INFO, SAMPLE_VERSION_INFO_2]
        u.ap_versions = {"aa:bb:cc:dd:ee:01": "0.14.29000", "aa:bb:cc:dd:ee:02": "0.14.29000"}

        result = u._step5_select_firmware_versions()
        assert result is True
        assert "0.14.29411" in u.upgrade_plan

    def test_skip_model(self):
        u = _make_upgrader(safe_input_fn=MagicMock(return_value="s"))
        u.aps_by_model = {"AP45": [SAMPLE_AP]}
        u.available_versions = [SAMPLE_VERSION_INFO]
        u.ap_versions = {"aa:bb:cc:dd:ee:01": "0.14.29000"}

        result = u._step5_select_firmware_versions()
        assert result is False

    def test_all_at_target(self):
        u = _make_upgrader(safe_input_fn=MagicMock(return_value="0"))
        u.aps_by_model = {"AP45": [SAMPLE_AP]}
        u.available_versions = [SAMPLE_VERSION_INFO]
        u.ap_versions = {"aa:bb:cc:dd:ee:01": "0.14.29411"}

        result = u._step5_select_firmware_versions()
        assert result is False

    def test_eof_during_selection(self):
        u = _make_upgrader(safe_input_fn=MagicMock(side_effect=SystemExit))
        u.aps_by_model = {"AP45": [SAMPLE_AP]}
        u.available_versions = [SAMPLE_VERSION_INFO]
        u.ap_versions = {"aa:bb:cc:dd:ee:01": "0.14.29000"}

        result = u._step5_select_firmware_versions()
        assert result is False


class TestGetVersionsForModel:
    """Tests for _get_versions_for_model."""

    def test_returns_sorted(self):
        u = _make_upgrader()
        u.available_versions = [SAMPLE_VERSION_INFO_2, SAMPLE_VERSION_INFO]
        versions = u._get_versions_for_model("AP45")
        assert versions[0]["version"] == "0.14.29411"
        assert versions[1]["version"] == "0.14.29000"

    def test_no_match(self):
        u = _make_upgrader()
        u.available_versions = [SAMPLE_VERSION_INFO]
        versions = u._get_versions_for_model("EX4300")
        assert versions == []

    def test_dedup(self):
        u = _make_upgrader()
        u.available_versions = [SAMPLE_VERSION_INFO, SAMPLE_VERSION_INFO]
        versions = u._get_versions_for_model("AP45")
        assert len(versions) == 1


# ===================================================================
# Upgrade Configuration (Step 6)
# ===================================================================


class TestUpgradeConfig:
    """Tests for _step6_configure_upgrade."""

    def test_basic_config(self):
        # Order: dl_strategy, rb_strategy, time_mode, dl_time, rb_time,
        #        p2p_enable, cluster, parallelism, failure_threshold
        inputs = iter(["1", "1", "1", "", "", "Y", "", "", ""])
        u = _make_upgrader(safe_input_fn=MagicMock(side_effect=inputs))
        result = u._step6_configure_upgrade()
        assert result is True
        assert u.upgrade_config["download_strategy"] == "big_bang"
        assert u.upgrade_config["reboot_strategy"] == "big_bang"

    def test_serial_strategies(self):
        # Order: dl_strategy, rb_strategy, time_mode, dl_time, rb_time, p2p_enable, failure_threshold
        inputs = iter(["2", "2", "1", "", "", "n", ""])
        u = _make_upgrader(safe_input_fn=MagicMock(side_effect=inputs))
        result = u._step6_configure_upgrade()
        assert result is True
        assert u.upgrade_config["download_strategy"] == "serial"
        assert u.upgrade_config["reboot_strategy"] == "serial"

    def test_canary_config(self):
        # Order: dl_strategy, rb_strategy, time_mode, dl_time, rb_time,
        #        p2p_enable, cluster, parallelism, canary_phases, failure_threshold
        inputs = iter(["3", "4", "1", "", "", "Y", "", "", "1,5,25,50,100", ""])
        u = _make_upgrader(safe_input_fn=MagicMock(side_effect=inputs))
        result = u._step6_configure_upgrade()
        assert result is True
        assert u.upgrade_config["download_strategy"] == "canary"
        assert u.upgrade_config["reboot_strategy"] == "canary"
        assert u.upgrade_config["canary_phases"] == [1, 5, 25, 50, 100]

    def test_eof_download(self):
        u = _make_upgrader(safe_input_fn=MagicMock(side_effect=SystemExit))
        result = u._step6_configure_upgrade()
        assert result is False


class TestTimeParsingRelative:
    """Tests for _parse_relative_offset."""

    def test_minutes(self):
        u = _make_upgrader()
        td = u._parse_relative_offset("15 minutes")
        assert td is not None
        assert td.total_seconds() == 900

    def test_hours(self):
        u = _make_upgrader()
        td = u._parse_relative_offset("+3h")
        assert td is not None
        assert td.total_seconds() == 10800

    def test_days(self):
        u = _make_upgrader()
        td = u._parse_relative_offset("2 days")
        assert td is not None
        assert td.total_seconds() == 172800

    def test_in_prefix(self):
        u = _make_upgrader()
        td = u._parse_relative_offset("in 30 min")
        assert td is not None
        assert td.total_seconds() == 1800

    def test_invalid(self):
        u = _make_upgrader()
        assert u._parse_relative_offset("abc") is None


class TestTimeParsingAbsolute:
    """Tests for _parse_time_input."""

    def test_now(self):
        u = _make_upgrader()
        u.upgrade_config = {"use_site_local_time": False}
        assert u._parse_time_input("now") is None

    def test_empty(self):
        u = _make_upgrader()
        u.upgrade_config = {"use_site_local_time": False}
        assert u._parse_time_input("") is None

    def test_relative_input(self):
        u = _make_upgrader()
        u.upgrade_config = {"use_site_local_time": False}
        result = u._parse_time_input("+3h")
        assert result is not None
        assert result.endswith("Z")

    def test_absolute_hhmm(self):
        u = _make_upgrader()
        u.upgrade_config = {"use_site_local_time": False}
        result = u._parse_time_input("21:30")
        assert result is not None

    def test_utc_suffix(self):
        u = _make_upgrader()
        u.upgrade_config = {"use_site_local_time": False}
        result = u._parse_time_input("19:45 UTC")
        assert result is not None
        assert result.endswith("Z")

    def test_invalid_time(self):
        u = _make_upgrader()
        u.upgrade_config = {"use_site_local_time": False}
        assert u._parse_time_input("25:99") is None

    def test_site_local_mode(self):
        u = _make_upgrader()
        u.upgrade_config = {"use_site_local_time": True}
        result = u._parse_time_input("21:00")
        assert result is not None
        assert not result.endswith("Z")


class TestP2PConfig:
    """Tests for P2P configuration."""

    def test_p2p_enabled(self):
        u = _make_upgrader(safe_input_fn=MagicMock(side_effect=["y", "10", "50"]))
        result = u._configure_p2p()
        assert result is True
        assert u.upgrade_config["enable_p2p"] is True
        assert u.upgrade_config["p2p_cluster_size"] == 10
        assert u.upgrade_config["p2p_parallelism"] == 50

    def test_p2p_disabled(self):
        u = _make_upgrader(safe_input_fn=MagicMock(return_value="n"))
        result = u._configure_p2p()
        assert result is True
        assert u.upgrade_config["enable_p2p"] is False

    def test_p2p_defaults(self):
        u = _make_upgrader(safe_input_fn=MagicMock(side_effect=["y", "", ""]))
        result = u._configure_p2p()
        assert result is True
        assert u.upgrade_config["p2p_cluster_size"] == 5
        assert u.upgrade_config["p2p_parallelism"] == 100

    def test_p2p_invalid_values(self):
        u = _make_upgrader(safe_input_fn=MagicMock(side_effect=["y", "abc", "abc"]))
        result = u._configure_p2p()
        assert result is True
        assert u.upgrade_config["p2p_cluster_size"] == 5
        assert u.upgrade_config["p2p_parallelism"] == 100


# ===================================================================
# Confirm and Execute (Step 7)
# ===================================================================


class TestDryRun:
    """Tests for dry-run execution."""

    def test_dry_run_succeeds(self):
        u = _make_upgrader(dry_run=True)
        u.upgrade_plan = {
            "0.14.29411": {
                "models": ["AP45"],
                "device_ids": ["ap-001", "ap-002"],
            }
        }
        u.upgrade_config = {
            "start_datetime": None,
            "reboot_datetime": None,
            "use_site_local_time": False,
        }
        result = u._step7_confirm_and_execute()
        assert result is True
        assert u.successful_api_calls == 1
        assert u.total_devices_upgraded == 2
        assert len(u.results) == 2

    def test_dry_run_records_status(self):
        u = _make_upgrader(dry_run=True)
        u.upgrade_plan = {"0.14.29411": {"models": ["AP45"], "device_ids": ["ap-001"]}}
        u.upgrade_config = {"start_datetime": None, "reboot_datetime": None, "use_site_local_time": False}
        u._step7_confirm_and_execute()
        assert u.results[0]["status"] == "DRY-RUN: Would upgrade"


class TestLiveExecution:
    """Tests for live execution path."""

    def test_cancel_upgrade(self):
        u = _make_upgrader(dry_run=False, safe_input_fn=MagicMock(return_value="no"))
        u.upgrade_plan = {"0.14.29411": {"models": ["AP45"], "device_ids": ["ap-001"]}}
        u.upgrade_config = {}
        result = u._confirm_and_execute_live()
        assert result is False

    def test_upgrade_confirmed(self):
        u = _make_upgrader(dry_run=False, safe_input_fn=MagicMock(return_value="UPGRADE"))
        u.upgrade_plan = {"0.14.29411": {"models": ["AP45"], "device_ids": ["ap-001"]}}
        u.upgrade_config = {
            "download_strategy": "big_bang",
            "reboot_strategy": "big_bang",
            "max_failure_percentage": 7,
            "start_datetime": None,
            "reboot_datetime": None,
        }
        u.target_all_sites = True

        with patch("importlib.import_module") as mock_import:
            mock_dev = MagicMock()
            mock_dev.upgradeOrgDevices.return_value = _make_api_response({"id": "upgrade-123"})
            mock_import.return_value = mock_dev
            result = u._confirm_and_execute_live()

        assert result is True
        assert u.successful_api_calls == 1

    def test_upgrade_api_failure(self):
        u = _make_upgrader(dry_run=False, safe_input_fn=MagicMock(return_value="UPGRADE"))
        u.upgrade_plan = {"0.14.29411": {"models": ["AP45"], "device_ids": ["ap-001"]}}
        u.upgrade_config = {
            "download_strategy": "big_bang",
            "reboot_strategy": "big_bang",
            "max_failure_percentage": 7,
            "start_datetime": None,
            "reboot_datetime": None,
        }
        u.target_all_sites = True

        with patch("importlib.import_module") as mock_import:
            mock_dev = MagicMock()
            mock_dev.upgradeOrgDevices.side_effect = Exception("API error")
            mock_import.return_value = mock_dev
            result = u._confirm_and_execute_live()

        assert result is True
        assert u.failed_api_calls == 1

    def test_eof_during_confirm(self):
        u = _make_upgrader(dry_run=False, safe_input_fn=MagicMock(side_effect=SystemExit))
        u.upgrade_plan = {"0.14.29411": {"models": ["AP45"], "device_ids": ["ap-001"]}}
        u.upgrade_config = {}
        result = u._confirm_and_execute_live()
        assert result is False


class TestBuildUpgradeBody:
    """Tests for _build_upgrade_body."""

    def test_all_sites(self):
        u = _make_upgrader()
        u.target_all_sites = True
        u.upgrade_config = {
            "reboot_strategy": "big_bang",
            "download_strategy": "big_bang",
            "max_failure_percentage": 7,
        }
        body = u._build_upgrade_body("0.14.29411", {"models": ["AP45"], "device_ids": ["ap-001"]})
        assert body["all_sites"] is True
        assert "site_ids" not in body

    def test_selected_sites(self):
        u = _make_upgrader()
        u.target_all_sites = False
        u.selected_site_ids = ["site-001", "site-002"]
        u.upgrade_config = {
            "reboot_strategy": "serial",
            "download_strategy": "serial",
            "max_failure_percentage": 7,
        }
        body = u._build_upgrade_body("0.14.29411", {"models": ["AP45"], "device_ids": ["ap-001"]})
        assert "all_sites" not in body
        assert body["site_ids"] == ["site-001", "site-002"]

    def test_canary_phases(self):
        u = _make_upgrader()
        u.target_all_sites = True
        u.upgrade_config = {
            "reboot_strategy": "canary",
            "download_strategy": "canary",
            "max_failure_percentage": 7,
            "canary_phases": [1, 5, 25, 100],
        }
        body = u._build_upgrade_body("0.14.29411", {"models": ["AP45"], "device_ids": ["ap-001"]})
        assert body["canary_phases"] == [1, 5, 25, 100]

    def test_p2p_enabled(self):
        u = _make_upgrader()
        u.target_all_sites = True
        u.upgrade_config = {
            "reboot_strategy": "big_bang",
            "download_strategy": "big_bang",
            "max_failure_percentage": 7,
            "enable_p2p": True,
            "p2p_cluster_size": 10,
            "p2p_parallelism": 50,
        }
        body = u._build_upgrade_body("0.14.29411", {"models": ["AP45"], "device_ids": ["ap-001"]})
        assert body["enable_p2p"] is True
        assert body["p2p_cluster_size"] == 10
        assert body["p2p_parallelism"] == 50

    def test_scheduling(self):
        u = _make_upgrader()
        u.target_all_sites = True
        u.upgrade_config = {
            "reboot_strategy": "big_bang",
            "download_strategy": "big_bang",
            "max_failure_percentage": 7,
            "start_datetime": "2025-01-01T21:00:00Z",
            "reboot_datetime": "2025-01-02T02:00:00Z",
        }
        body = u._build_upgrade_body("0.14.29411", {"models": ["AP45"], "device_ids": ["ap-001"]})
        assert body["start_datetime"] == "2025-01-01T21:00:00Z"
        assert body["reboot_datetime"] == "2025-01-02T02:00:00Z"


# ===================================================================
# Results Writing (Step 8)
# ===================================================================


class TestResultsWriting:
    """Tests for _step8_write_results."""

    def test_writes_results(self):
        mock_write = MagicMock()
        u = _make_upgrader(write_results_fn=mock_write)
        u.results = [{"org_id": "org-123", "version": "0.14.29411", "status": "ok"}]
        u._step8_write_results()
        mock_write.assert_called_once()

    def test_no_results(self):
        mock_write = MagicMock()
        u = _make_upgrader(write_results_fn=mock_write)
        u.results = []
        u._step8_write_results()
        mock_write.assert_not_called()

    def test_write_error(self):
        mock_write = MagicMock(side_effect=Exception("write failed"))
        u = _make_upgrader(write_results_fn=mock_write)
        u.results = [{"org_id": "org-123"}]
        u._step8_write_results()  # Should not raise


# ===================================================================
# MSP Mode
# ===================================================================


class TestMSPMode:
    """Tests for MSP multi-org mode."""

    def test_run_single_org_mode(self):
        u = _make_upgrader(
            msp_privileges=[],
            safe_input_fn=MagicMock(side_effect=SystemExit),
        )
        u.run()  # Should enter single-org mode, get org_id, then fail gracefully

    def test_run_msp_mode_selected(self):
        u = _make_upgrader(
            msp_privileges=[SAMPLE_MSP],
            safe_input_fn=MagicMock(side_effect=["2", SystemExit]),
        )
        u.run()  # Should enter MSP mode

    def test_prompt_msp_mode_single(self):
        u = _make_upgrader(safe_input_fn=MagicMock(return_value="1"))
        result = u._prompt_msp_mode()
        assert result == "1"

    def test_prompt_msp_mode_multi(self):
        u = _make_upgrader(safe_input_fn=MagicMock(return_value="2"))
        result = u._prompt_msp_mode()
        assert result == "2"

    def test_prompt_msp_mode_default(self):
        u = _make_upgrader(safe_input_fn=MagicMock(return_value=""))
        result = u._prompt_msp_mode()
        assert result == "1"

    def test_prompt_msp_mode_eof(self):
        u = _make_upgrader(safe_input_fn=MagicMock(side_effect=SystemExit))
        result = u._prompt_msp_mode()
        assert result is None


class TestMSPSelection:
    """Tests for _select_msps."""

    def test_single_msp_auto(self):
        u = _make_upgrader(msp_privileges=[SAMPLE_MSP])
        result = u._select_msps()
        assert len(result) == 1

    def test_multi_msp_select_all(self):
        u = _make_upgrader(
            msp_privileges=[SAMPLE_MSP, SAMPLE_MSP_2],
            safe_input_fn=MagicMock(return_value="all"),
        )
        result = u._select_msps()
        assert len(result) == 2

    def test_multi_msp_cancel(self):
        u = _make_upgrader(
            msp_privileges=[SAMPLE_MSP, SAMPLE_MSP_2],
            safe_input_fn=MagicMock(return_value="q"),
        )
        result = u._select_msps()
        assert result == []

    def test_multi_msp_select_one(self):
        u = _make_upgrader(
            msp_privileges=[SAMPLE_MSP, SAMPLE_MSP_2],
            safe_input_fn=MagicMock(return_value="1"),
        )
        result = u._select_msps()
        assert len(result) == 1

    def test_default_msp(self):
        u = _make_upgrader(
            msp_privileges=[SAMPLE_MSP, SAMPLE_MSP_2],
            selected_msp=SAMPLE_MSP,
            safe_input_fn=MagicMock(return_value=""),
        )
        result = u._select_msps()
        assert len(result) == 1
        assert result[0]["msp_id"] == "msp-001"


class TestOrgSelection:
    """Tests for _select_orgs_from_msp."""

    def test_selects_orgs(self):
        u = _make_upgrader(safe_input_fn=MagicMock(return_value="1"))

        with patch("importlib.import_module") as mock_import:
            mock_msp_api = MagicMock()
            mock_msp_api.listMspOrgs.return_value = _make_api_response([SAMPLE_ORG, SAMPLE_ORG_2])
            mock_import.return_value = mock_msp_api
            result = u._select_orgs_from_msp(SAMPLE_MSP)

        assert len(result) == 1

    def test_select_all_orgs(self):
        u = _make_upgrader(safe_input_fn=MagicMock(return_value="all"))

        with patch("importlib.import_module") as mock_import:
            mock_msp_api = MagicMock()
            mock_msp_api.listMspOrgs.return_value = _make_api_response([SAMPLE_ORG, SAMPLE_ORG_2])
            mock_import.return_value = mock_msp_api
            result = u._select_orgs_from_msp(SAMPLE_MSP)

        assert len(result) == 2

    def test_skip_msp(self):
        u = _make_upgrader(safe_input_fn=MagicMock(return_value="q"))

        with patch("importlib.import_module") as mock_import:
            mock_msp_api = MagicMock()
            mock_msp_api.listMspOrgs.return_value = _make_api_response([SAMPLE_ORG])
            mock_import.return_value = mock_msp_api
            result = u._select_orgs_from_msp(SAMPLE_MSP)

        assert result == []

    def test_no_orgs(self):
        u = _make_upgrader(safe_input_fn=MagicMock(return_value="all"))

        with patch("importlib.import_module") as mock_import:
            mock_msp_api = MagicMock()
            mock_msp_api.listMspOrgs.return_value = _make_api_response([])
            mock_import.return_value = mock_msp_api
            result = u._select_orgs_from_msp(SAMPLE_MSP)

        assert result == []

    def test_api_error(self):
        u = _make_upgrader(safe_input_fn=MagicMock(return_value="1"))

        with patch("importlib.import_module") as mock_import:
            mock_msp_api = MagicMock()
            mock_msp_api.listMspOrgs.side_effect = Exception("API error")
            mock_import.return_value = mock_msp_api
            result = u._select_orgs_from_msp(SAMPLE_MSP)

        assert result == []

    def test_api_session_none(self):
        u = _make_upgrader(apisession=None)
        result = u._select_orgs_from_msp(SAMPLE_MSP)
        assert result == []


# ===================================================================
# MSP Summary
# ===================================================================


class TestMSPSummary:
    """Tests for _print_msp_summary."""

    def test_summary_output(self, capsys):
        results = [
            {"org_id": "org-1", "org_name": "Org A", "success": 3, "failed": 0, "devices": 50},
            {"org_id": "org-2", "org_name": "Org B", "success": 2, "failed": 1, "devices": 30},
        ]
        OrgLevelAPFirmwareUpgrader._print_msp_summary(results, dry_run=False)
        captured = capsys.readouterr()
        assert "Org A" in captured.out
        assert "Org B" in captured.out
        assert "80" in captured.out  # total devices

    def test_summary_dry_run(self, capsys):
        results = [{"org_id": "org-1", "org_name": "Org A", "success": 1, "failed": 0, "devices": 10}]
        OrgLevelAPFirmwareUpgrader._print_msp_summary(results, dry_run=True)
        captured = capsys.readouterr()
        assert "DRY-RUN" in captured.out


# ===================================================================
# Selection Input Parsing
# ===================================================================


class TestParseSelectionInput:
    """Tests for _parse_selection_input."""

    def test_single(self):
        u = _make_upgrader()
        assert u._parse_selection_input("2", 5) == [1]

    def test_range(self):
        u = _make_upgrader()
        assert u._parse_selection_input("1-3", 5) == [0, 1, 2]

    def test_through(self):
        u = _make_upgrader()
        assert u._parse_selection_input("2 through 4", 5) == [1, 2, 3]

    def test_comma_separated(self):
        u = _make_upgrader()
        assert u._parse_selection_input("1,3,5", 5) == [0, 2, 4]

    def test_out_of_range(self):
        u = _make_upgrader()
        assert u._parse_selection_input("99", 5) == []


# ===================================================================
# Execute Workflow
# ===================================================================


class TestExecuteWorkflow:
    """Tests for the execute method."""

    def test_keyboard_interrupt(self):
        u = _make_upgrader(safe_input_fn=MagicMock(side_effect=KeyboardInterrupt))
        u.execute()  # Should catch KeyboardInterrupt gracefully

    def test_step1_fails(self):
        u = _make_upgrader(safe_input_fn=MagicMock(return_value="9"))
        u.execute()  # Step 1 fails, should return without error


# ===================================================================
# Organize by Version
# ===================================================================


class TestOrganizeByVersion:
    """Tests for _organize_by_version."""

    def test_groups_by_version(self):
        u = _make_upgrader()
        u.target_all_sites = True
        selections = {
            "AP45": {"version": "0.14.29411", "devices": [SAMPLE_AP, SAMPLE_AP_2]},
            "AP34": {"version": "0.14.29411", "devices": [SAMPLE_AP_3]},
        }
        u._organize_by_version(selections)
        assert "0.14.29411" in u.upgrade_plan
        assert len(u.upgrade_plan["0.14.29411"]["device_ids"]) == 3
        assert "AP45" in u.upgrade_plan["0.14.29411"]["models"]
        assert "AP34" in u.upgrade_plan["0.14.29411"]["models"]

    def test_separate_versions(self):
        u = _make_upgrader()
        u.target_all_sites = True
        selections = {
            "AP45": {"version": "0.14.29411", "devices": [SAMPLE_AP]},
            "AP34": {"version": "0.14.29000", "devices": [SAMPLE_AP_3]},
        }
        u._organize_by_version(selections)
        assert len(u.upgrade_plan) == 2


# ===================================================================
# Display Configuration
# ===================================================================


class TestDisplayConfig:
    """Tests for _display_configuration."""

    def test_basic_display(self, capsys):
        u = _make_upgrader()
        u.upgrade_config = {
            "download_strategy": "big_bang",
            "reboot_strategy": "serial",
            "use_site_local_time": False,
            "start_datetime": None,
            "reboot_datetime": None,
            "max_failure_percentage": 7,
            "enable_p2p": False,
        }
        u._display_configuration()
        captured = capsys.readouterr()
        assert "big_bang" in captured.out
        assert "serial" in captured.out

    def test_scheduled_display(self, capsys):
        u = _make_upgrader()
        u.upgrade_config = {
            "download_strategy": "canary",
            "reboot_strategy": "canary",
            "use_site_local_time": True,
            "start_datetime": "2025-01-01T21:00:00",
            "reboot_datetime": "2025-01-02T02:00:00",
            "max_failure_percentage": 5,
            "canary_phases": [1, 5, 25, 100],
            "enable_p2p": True,
            "p2p_cluster_size": 10,
            "p2p_parallelism": 50,
        }
        u._display_configuration()
        captured = capsys.readouterr()
        assert "Site-Local" in captured.out
        assert "canary" in captured.out
        assert "1, 5, 25, 100" in captured.out
        assert "P2P Enabled: Yes" in captured.out


# ===================================================================
# Failure Threshold
# ===================================================================


class TestFailureThreshold:
    """Tests for _configure_failure_threshold."""

    def test_custom_threshold(self):
        u = _make_upgrader(safe_input_fn=MagicMock(return_value="15"))
        result = u._configure_failure_threshold()
        assert result is True
        assert u.upgrade_config["max_failure_percentage"] == 15

    def test_default_threshold(self):
        u = _make_upgrader(safe_input_fn=MagicMock(return_value=""))
        result = u._configure_failure_threshold()
        assert result is True
        assert u.upgrade_config["max_failure_percentage"] == 7

    def test_invalid_threshold(self):
        u = _make_upgrader(safe_input_fn=MagicMock(return_value="abc"))
        result = u._configure_failure_threshold()
        assert result is True
        assert u.upgrade_config["max_failure_percentage"] == 7

    def test_out_of_range_threshold(self):
        u = _make_upgrader(safe_input_fn=MagicMock(return_value="150"))
        result = u._configure_failure_threshold()
        assert result is True
        assert u.upgrade_config["max_failure_percentage"] == 7
