"""Tests for src.device.virtual_chassis -- VirtualChassisManager.

Covers all static methods: public entry-points (convert_single,
convert_by_site_list, check_status) and private helpers.
"""

from __future__ import annotations

import csv
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# We need to mock mistapi before importing the module under test because
# the module uses lazy ``import mistapi`` inside certain methods.
# ---------------------------------------------------------------------------
_mock_mistapi = MagicMock()
with patch.dict(sys.modules, {"mistapi": _mock_mistapi}):
    from src.device.virtual_chassis import VirtualChassisManager


# ===================================================================
# Fixtures
# ===================================================================


@pytest.fixture(autouse=True)
def _clean(tmp_path, monkeypatch):
    """Run every test in a temp dir with a data/ subdirectory."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir()


@pytest.fixture()
def deps():
    """Return a dict of common mock dependencies."""
    return {
        "apisession": MagicMock(),
        "safe_input_fn": MagicMock(return_value=""),
        "select_site_fn": MagicMock(return_value="site-1"),
        "get_csv_path_fn": MagicMock(side_effect=lambda f: os.path.join("data", f)),
        "create_csv_template_fn": MagicMock(return_value="data/VCConvert.CSV"),
        "check_and_generate_csv_fn": MagicMock(),
        "inventory_generator": MagicMock(),
        "sites_generator": MagicMock(),
        "flatten_fields_fn": MagicMock(side_effect=lambda x: x),
        "escape_multiline_fn": MagicMock(side_effect=lambda x: x),
        "save_data_fn": MagicMock(),
    }


def _write_inventory_csv(path, rows):
    """Helper: write an OrgInventory.csv at *path*."""
    fieldnames = ["type", "id", "site_id", "name", "mac", "model", "serial", "vc_mac"]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            full = {k: "" for k in fieldnames}
            full.update(row)
            writer.writerow(full)


def _write_site_list_csv(path, rows):
    """Helper: write a SiteList.csv at *path*."""
    fieldnames = ["id", "name"]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _write_vc_csv(path, site_names):
    """Helper: write a VCConvert.CSV."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        for name in site_names:
            fh.write(name + "\n")


# ===================================================================
# _resolve_site_ids
# ===================================================================


class TestResolveSiteIds:
    """Tests for _resolve_site_ids."""

    def test_all_found(self):
        mapping = {"SiteA": "id-a", "SiteB": "id-b"}
        ids, missing = VirtualChassisManager._resolve_site_ids(["SiteA", "SiteB"], mapping)
        assert ids == ["id-a", "id-b"]
        assert missing == []

    def test_some_missing(self):
        mapping = {"SiteA": "id-a"}
        ids, missing = VirtualChassisManager._resolve_site_ids(["SiteA", "SiteX"], mapping)
        assert ids == ["id-a"]
        assert missing == ["SiteX"]

    def test_empty_input(self):
        ids, missing = VirtualChassisManager._resolve_site_ids([], {"A": "1"})
        assert ids == []
        assert missing == []


# ===================================================================
# _analyze_conversion_status
# ===================================================================


class TestAnalyzeConversionStatus:
    """Tests for _analyze_conversion_status."""

    def test_converted(self):
        switches = [{"vc_mac": "020003aabbcc", "site_id": "s1", "name": "sw1"}]
        site_map = {"s1": "Site One"}
        conv, not_conv = VirtualChassisManager._analyze_conversion_status(switches, site_map)
        assert len(conv) == 1
        assert conv[0]["conversion_status"] == "CONVERTED"
        assert conv[0]["site_name"] == "Site One"
        assert not_conv == []

    def test_not_converted(self):
        switches = [{"vc_mac": "aabbccddeeff", "site_id": "s2", "name": "sw2"}]
        site_map = {"s2": "Site Two"}
        conv, not_conv = VirtualChassisManager._analyze_conversion_status(switches, site_map)
        assert conv == []
        assert len(not_conv) == 1
        assert not_conv[0]["conversion_status"] == "NOT_CONVERTED"

    def test_unknown_site(self):
        switches = [{"vc_mac": "020003112233", "site_id": "s-unknown"}]
        conv, _ = VirtualChassisManager._analyze_conversion_status(switches, {})
        assert conv[0]["site_name"] == "Unknown Site"

    def test_empty(self):
        conv, not_conv = VirtualChassisManager._analyze_conversion_status([], {})
        assert conv == []
        assert not_conv == []

    def test_mixed(self):
        switches = [
            {"vc_mac": "020003aabb", "site_id": "s1"},
            {"vc_mac": "ffeedd112233", "site_id": "s1"},
        ]
        conv, not_conv = VirtualChassisManager._analyze_conversion_status(switches, {"s1": "S"})
        assert len(conv) == 1
        assert len(not_conv) == 1


# ===================================================================
# _is_target_switch
# ===================================================================


class TestIsTargetSwitch:
    """Tests for _is_target_switch."""

    def test_valid_target(self):
        row = {"type": "switch", "site_id": "s1", "id": "dev-1"}
        assert VirtualChassisManager._is_target_switch(row, ["s1"]) is True

    def test_wrong_type(self):
        row = {"type": "ap", "site_id": "s1", "id": "dev-1"}
        assert VirtualChassisManager._is_target_switch(row, ["s1"]) is False

    def test_wrong_site(self):
        row = {"type": "switch", "site_id": "s2", "id": "dev-1"}
        assert VirtualChassisManager._is_target_switch(row, ["s1"]) is False

    def test_empty_id(self):
        row = {"type": "switch", "site_id": "s1", "id": "  "}
        assert VirtualChassisManager._is_target_switch(row, ["s1"]) is False

    def test_missing_id(self):
        row = {"type": "switch", "site_id": "s1"}
        assert VirtualChassisManager._is_target_switch(row, ["s1"]) is False


# ===================================================================
# _reverse_lookup
# ===================================================================


class TestReverseLookup:
    """Tests for _reverse_lookup."""

    def test_found(self):
        name_to_id = {"SiteA": "id-a", "SiteB": "id-b"}
        assert VirtualChassisManager._reverse_lookup("id-b", name_to_id) == "SiteB"

    def test_not_found(self):
        assert VirtualChassisManager._reverse_lookup("x", {}) == "Unknown Site"


# ===================================================================
# _is_conversion_error
# ===================================================================


class TestIsConversionError:
    """Tests for _is_conversion_error."""

    def test_http_error(self, capsys):
        resp = MagicMock()
        resp.status_code = 500
        resp.data = "server error"
        assert VirtualChassisManager._is_conversion_error(resp) is True
        assert "500" in capsys.readouterr().out

    def test_detail_error(self, capsys):
        resp = MagicMock(spec=[])
        resp.data = {"detail": "device not found"}
        assert VirtualChassisManager._is_conversion_error(resp) is True
        assert "device not found" in capsys.readouterr().out

    def test_success(self):
        resp = MagicMock(spec=[])
        resp.data = {"id": "ok"}
        assert VirtualChassisManager._is_conversion_error(resp) is False


# ===================================================================
# _preflight_check
# ===================================================================


class TestPreflightCheck:
    """Tests for _preflight_check."""

    def test_valid_switch(self):
        switch = {"type": "switch", "id": "dev-1", "name": "sw1"}
        assert VirtualChassisManager._preflight_check(switch, MagicMock()) is True

    def test_wrong_type(self, capsys):
        switch = {"type": "ap", "id": "dev-1"}
        assert VirtualChassisManager._preflight_check(switch, MagicMock()) is False
        assert "Preflight FAILED" in capsys.readouterr().out

    def test_missing_device_id(self, capsys):
        switch = {"type": "switch", "id": ""}
        assert VirtualChassisManager._preflight_check(switch, MagicMock()) is False
        assert "Preflight FAILED" in capsys.readouterr().out

    def test_already_converted_user_cancels(self):
        switch = {"type": "switch", "id": "dev-1", "vc_mac": "020003aabb", "name": "s"}
        safe_fn = MagicMock(return_value="n")
        assert VirtualChassisManager._preflight_check(switch, safe_fn) is False

    def test_already_converted_user_continues(self):
        switch = {"type": "switch", "id": "dev-1", "vc_mac": "020003aabb", "name": "s"}
        safe_fn = MagicMock(return_value="y")
        assert VirtualChassisManager._preflight_check(switch, safe_fn) is True


# ===================================================================
# _confirm_conversion
# ===================================================================


class TestConfirmConversion:
    """Tests for _confirm_conversion."""

    def test_confirmed(self):
        safe_fn = MagicMock(return_value="CONVERT")
        result = VirtualChassisManager._confirm_conversion({"name": "sw1", "mac": "aa:bb"}, "Site1", "dev-1", safe_fn)
        assert result is True

    def test_cancelled(self):
        safe_fn = MagicMock(return_value="no")
        result = VirtualChassisManager._confirm_conversion({"name": "sw1"}, "Site1", "dev-1", safe_fn)
        assert result is False


# ===================================================================
# _prompt_switch_selection
# ===================================================================


class TestPromptSwitchSelection:
    """Tests for _prompt_switch_selection."""

    def test_select_by_index(self):
        switches = [
            {"name": "sw-a", "mac": "aa", "model": "EX", "serial": "S1", "id": "d1"},
            {"name": "sw-b", "mac": "bb", "model": "EX", "serial": "S2", "id": "d2"},
        ]
        safe_fn = MagicMock(return_value="1")
        result = VirtualChassisManager._prompt_switch_selection(switches, "TestSite", safe_fn)
        assert result is not None
        assert result["name"] == "sw-b"

    def test_select_by_name(self):
        switches = [
            {"name": "sw-a", "mac": "aa", "model": "EX", "serial": "S1", "id": "d1"},
        ]
        safe_fn = MagicMock(return_value="sw-a")
        result = VirtualChassisManager._prompt_switch_selection(switches, "TestSite", safe_fn)
        assert result is not None
        assert result["id"] == "d1"

    def test_invalid_selection(self):
        switches = [
            {"name": "sw-a", "mac": "aa", "model": "EX", "serial": "S1", "id": "d1"},
        ]
        safe_fn = MagicMock(return_value="nonexistent")
        result = VirtualChassisManager._prompt_switch_selection(switches, "TestSite", safe_fn)
        assert result is None


# ===================================================================
# _get_site_name
# ===================================================================


class TestGetSiteName:
    """Tests for _get_site_name."""

    def test_success(self):
        with patch.dict(sys.modules, {"mistapi": _mock_mistapi}):
            session = MagicMock()
            resp = MagicMock()
            resp.data = {"name": "MySite"}
            _mock_mistapi.api.v1.sites.getSite.return_value = resp
            name = VirtualChassisManager._get_site_name(session, "s1")
            assert name == "MySite"

    def test_exception(self):
        with patch.dict(sys.modules, {"mistapi": _mock_mistapi}):
            _mock_mistapi.api.v1.sites.getSite.side_effect = RuntimeError("err")
            name = VirtualChassisManager._get_site_name(MagicMock(), "s1")
            assert name == "Unknown Site"
            _mock_mistapi.api.v1.sites.getSite.side_effect = None

    def test_no_data(self):
        with patch.dict(sys.modules, {"mistapi": _mock_mistapi}):
            resp = MagicMock()
            resp.data = None
            _mock_mistapi.api.v1.sites.getSite.return_value = resp
            name = VirtualChassisManager._get_site_name(MagicMock(), "s1")
            assert name == "Unknown Site"


# ===================================================================
# _load_site_switches
# ===================================================================


class TestLoadSiteSwitches:
    """Tests for _load_site_switches."""

    def test_filters_by_site_and_type(self, tmp_path):
        inv_path = str(tmp_path / "data" / "OrgInventory.csv")
        _write_inventory_csv(
            inv_path,
            [
                {"type": "switch", "id": "d1", "site_id": "s1", "name": "sw1"},
                {"type": "ap", "id": "d2", "site_id": "s1", "name": "ap1"},
                {"type": "switch", "id": "d3", "site_id": "s2", "name": "sw2"},
                {"type": "switch", "id": "", "site_id": "s1", "name": "sw3"},
            ],
        )
        get_fn = MagicMock(return_value=inv_path)
        check_fn = MagicMock()
        result = VirtualChassisManager._load_site_switches("s1", get_fn, check_fn, MagicMock())
        assert len(result) == 1
        assert result[0]["name"] == "sw1"


# ===================================================================
# _load_site_names_from_csv
# ===================================================================


class TestLoadSiteNamesFromCsv:
    """Tests for _load_site_names_from_csv."""

    def test_reads_names(self, tmp_path):
        csv_path = str(tmp_path / "data" / "VCConvert.CSV")
        _write_vc_csv(csv_path, ["SiteA", "SiteB"])
        get_fn = MagicMock(return_value=csv_path)
        result = VirtualChassisManager._load_site_names_from_csv(get_fn, MagicMock(), MagicMock())
        assert result == ["SiteA", "SiteB"]

    def test_missing_file(self, tmp_path):
        csv_path = str(tmp_path / "data" / "VCConvert.CSV")
        get_fn = MagicMock(return_value=csv_path)
        safe_fn = MagicMock(return_value="n")
        result = VirtualChassisManager._load_site_names_from_csv(get_fn, MagicMock(), safe_fn)
        assert result == []

    def test_missing_file_creates_template(self, tmp_path):
        csv_path = str(tmp_path / "data" / "VCConvert.CSV")
        get_fn = MagicMock(return_value=csv_path)
        safe_fn = MagicMock(return_value="y")
        create_fn = MagicMock(return_value=csv_path)
        result = VirtualChassisManager._load_site_names_from_csv(get_fn, create_fn, safe_fn)
        assert result == []
        create_fn.assert_called_once_with("VCConvert.CSV")

    def test_empty_lines_skipped(self, tmp_path):
        csv_path = str(tmp_path / "data" / "VCConvert.CSV")
        _write_vc_csv(csv_path, ["SiteA", "", "  ", "SiteB"])
        get_fn = MagicMock(return_value=csv_path)
        result = VirtualChassisManager._load_site_names_from_csv(get_fn, MagicMock(), MagicMock())
        assert result == ["SiteA", "SiteB"]


# ===================================================================
# _load_site_name_mapping
# ===================================================================


class TestLoadSiteNameMapping:
    """Tests for _load_site_name_mapping."""

    def test_reads_mapping(self, tmp_path):
        csv_path = str(tmp_path / "data" / "SiteList.csv")
        _write_site_list_csv(csv_path, [{"id": "id-a", "name": "SiteA"}])
        get_fn = MagicMock(return_value=csv_path)
        result = VirtualChassisManager._load_site_name_mapping(get_fn)
        assert result == {"SiteA": "id-a"}

    def test_file_error(self, tmp_path):
        get_fn = MagicMock(return_value=str(tmp_path / "nope.csv"))
        result = VirtualChassisManager._load_site_name_mapping(get_fn)
        assert result == {}


# ===================================================================
# _load_switches_for_sites
# ===================================================================


class TestLoadSwitchesForSites:
    """Tests for _load_switches_for_sites."""

    def test_loads_target_switches(self, tmp_path):
        inv_path = str(tmp_path / "data" / "OrgInventory.csv")
        _write_inventory_csv(
            inv_path,
            [
                {"type": "switch", "id": "d1", "site_id": "s1", "name": "sw1"},
                {"type": "switch", "id": "d2", "site_id": "s2", "name": "sw2"},
            ],
        )
        get_fn = MagicMock(return_value=inv_path)
        name_map = {"SiteA": "s1", "SiteB": "s2"}
        result = VirtualChassisManager._load_switches_for_sites(["s1"], name_map, get_fn)
        assert len(result) == 1
        assert result[0]["site_name"] == "SiteA"

    def test_file_error(self, tmp_path):
        get_fn = MagicMock(return_value=str(tmp_path / "nope.csv"))
        result = VirtualChassisManager._load_switches_for_sites(["s1"], {}, get_fn)
        assert result == []


# ===================================================================
# _load_vc_switches
# ===================================================================


class TestLoadVcSwitches:
    """Tests for _load_vc_switches."""

    def test_filters_by_vc_mac(self, tmp_path):
        inv_path = str(tmp_path / "data" / "OrgInventory.csv")
        _write_inventory_csv(
            inv_path,
            [
                {"type": "switch", "vc_mac": "020003aa", "name": "sw1"},
                {"type": "switch", "vc_mac": "", "name": "sw2"},
                {"type": "ap", "vc_mac": "020003bb", "name": "ap1"},
            ],
        )
        get_fn = MagicMock(return_value=inv_path)
        result = VirtualChassisManager._load_vc_switches(get_fn)
        assert len(result) == 1
        assert result[0]["name"] == "sw1"

    def test_file_error(self, tmp_path):
        get_fn = MagicMock(return_value=str(tmp_path / "nope.csv"))
        result = VirtualChassisManager._load_vc_switches(get_fn)
        assert result == []


# ===================================================================
# _load_site_id_mapping
# ===================================================================


class TestLoadSiteIdMapping:
    """Tests for _load_site_id_mapping."""

    def test_reads_mapping(self, tmp_path):
        csv_path = str(tmp_path / "data" / "SiteList.csv")
        _write_site_list_csv(csv_path, [{"id": "id-a", "name": "SiteA"}])
        get_fn = MagicMock(return_value=csv_path)
        check_fn = MagicMock()
        result = VirtualChassisManager._load_site_id_mapping(get_fn, check_fn, MagicMock())
        assert result == {"id-a": "SiteA"}

    def test_exception(self, tmp_path):
        get_fn = MagicMock(return_value=str(tmp_path / "nope.csv"))
        result = VirtualChassisManager._load_site_id_mapping(get_fn, MagicMock(), MagicMock())
        assert result == {}


# ===================================================================
# Display helpers (smoke tests -- verify no exceptions)
# ===================================================================


class TestDisplayHelpers:
    """Smoke tests for display/print helpers."""

    def test_print_dry_run(self, capsys):
        VirtualChassisManager._print_dry_run({"name": "sw1", "mac": "aa:bb"}, "Site1", "dev-1", "s1")
        out = capsys.readouterr().out
        assert "DRY RUN" in out
        assert "sw1" in out

    def test_display_switches_for_conversion(self, capsys):
        switches = [
            {
                "site_name": "S",
                "name": "sw",
                "mac": "aa",
                "model": "EX",
                "serial": "123",
            }
        ]
        VirtualChassisManager._display_switches_for_conversion(switches)
        out = capsys.readouterr().out
        assert "1" in out

    def test_display_status_summary_empty(self, capsys):
        VirtualChassisManager._display_status_summary([], [])
        out = capsys.readouterr().out
        assert "Total virtual chassis switches: 0" in out

    def test_display_status_summary_with_data(self, capsys):
        conv = [{"name": "sw1", "site_name": "S1", "vc_mac": "020003aabb"}]
        not_conv = [{"name": "sw2", "site_name": "S2", "vc_mac": "ffeeddccbb"}]
        VirtualChassisManager._display_status_summary(conv, not_conv)
        out = capsys.readouterr().out
        assert "Converted to virtual MAC: 1" in out
        assert "Not converted: 1" in out

    def test_print_bulk_summary(self, capsys):
        VirtualChassisManager._print_bulk_summary(3, 1, 4)
        out = capsys.readouterr().out
        assert "Successful conversions: 3" in out
        assert "Failed conversions: 1" in out

    def test_print_status_list_truncates(self, capsys):
        switches = [{"name": f"sw{i}", "site_name": "S", "vc_mac": "aabb"} for i in range(15)]
        VirtualChassisManager._print_status_list(switches, "Test", "desc")
        out = capsys.readouterr().out
        assert "... and 5 more" in out

    def test_print_status_list_empty(self, capsys):
        VirtualChassisManager._print_status_list([], "Test", "desc")
        assert capsys.readouterr().out == ""


# ===================================================================
# _export_status_results
# ===================================================================


class TestExportStatusResults:
    """Tests for _export_status_results."""

    def test_success(self):
        flatten_fn = MagicMock(side_effect=lambda x: x)
        escape_fn = MagicMock(side_effect=lambda x: x)
        save_fn = MagicMock()
        get_fn = MagicMock(return_value="data/out.csv")
        data = [{"name": "sw1"}]
        VirtualChassisManager._export_status_results(data, flatten_fn, escape_fn, save_fn, get_fn)
        save_fn.assert_called_once()

    def test_exception(self, capsys):
        flatten_fn = MagicMock(side_effect=RuntimeError("boom"))
        VirtualChassisManager._export_status_results([], flatten_fn, MagicMock(), MagicMock(), MagicMock())
        assert "Error exporting" in capsys.readouterr().out


# ===================================================================
# _handle_conversion_response
# ===================================================================


class TestHandleConversionResponse:
    """Tests for _handle_conversion_response."""

    def test_http_error(self, capsys):
        resp = MagicMock()
        resp.status_code = 403
        resp.data = "forbidden"
        VirtualChassisManager._handle_conversion_response(resp, "d1", "s1", "Site1", "sw1")
        assert "403" in capsys.readouterr().out

    def test_detail_error(self, capsys):
        resp = MagicMock(spec=[])
        resp.data = {"detail": "bad device"}
        VirtualChassisManager._handle_conversion_response(resp, "d1", "s1", "Site1", "sw1")
        assert "bad device" in capsys.readouterr().out

    def test_success(self, capsys):
        resp = MagicMock(spec=[])
        resp.data = {"ok": True}
        VirtualChassisManager._handle_conversion_response(resp, "d1", "s1", "Site1", "sw1")
        out = capsys.readouterr().out
        assert "successfully" in out


# ===================================================================
# _execute_conversion
# ===================================================================


class TestExecuteConversion:
    """Tests for _execute_conversion."""

    def test_calls_api(self):
        with patch.dict(sys.modules, {"mistapi": _mock_mistapi}):
            session = MagicMock()
            resp = MagicMock(spec=[])
            resp.data = {"ok": True}
            _mock_mistapi.api.v1.sites.devices.convertSiteVirtualChassisToVirtualMac.return_value = resp
            VirtualChassisManager._execute_conversion(session, "s1", "d1", "sw1", "Site1")
            _mock_mistapi.api.v1.sites.devices.convertSiteVirtualChassisToVirtualMac.assert_called_once()

    def test_exception(self, capsys):
        with patch.dict(sys.modules, {"mistapi": _mock_mistapi}):
            _mock_mistapi.api.v1.sites.devices.convertSiteVirtualChassisToVirtualMac.side_effect = RuntimeError("fail")
            VirtualChassisManager._execute_conversion(MagicMock(), "s1", "d1", "sw1", "Site1")
            assert "Failed" in capsys.readouterr().out
            _mock_mistapi.api.v1.sites.devices.convertSiteVirtualChassisToVirtualMac.side_effect = None


# ===================================================================
# _execute_bulk_conversion
# ===================================================================


class TestExecuteBulkConversion:
    """Tests for _execute_bulk_conversion."""

    def test_mixed_results(self, capsys):
        with patch.dict(sys.modules, {"mistapi": _mock_mistapi}):
            ok_resp = MagicMock(spec=[])
            ok_resp.data = {"ok": True}
            fail_resp = MagicMock()
            fail_resp.status_code = 500
            fail_resp.data = "err"
            _mock_mistapi.api.v1.sites.devices.convertSiteVirtualChassisToVirtualMac.side_effect = [
                ok_resp,
                fail_resp,
            ]
            switches = [
                {"site_id": "s1", "id": "d1", "name": "sw1", "site_name": "S1"},
                {"site_id": "s2", "id": "d2", "name": "sw2", "site_name": "S2"},
            ]
            VirtualChassisManager._execute_bulk_conversion(MagicMock(), switches)
            out = capsys.readouterr().out
            assert "Successful conversions: 1" in out
            assert "Failed conversions: 1" in out
            _mock_mistapi.api.v1.sites.devices.convertSiteVirtualChassisToVirtualMac.side_effect = None

    def test_exception_during_conversion(self, capsys):
        with patch.dict(sys.modules, {"mistapi": _mock_mistapi}):
            _mock_mistapi.api.v1.sites.devices.convertSiteVirtualChassisToVirtualMac.side_effect = RuntimeError("boom")
            switches = [
                {"site_id": "s1", "id": "d1", "name": "sw1", "site_name": "S1"},
            ]
            VirtualChassisManager._execute_bulk_conversion(MagicMock(), switches)
            out = capsys.readouterr().out
            assert "Exception" in out
            _mock_mistapi.api.v1.sites.devices.convertSiteVirtualChassisToVirtualMac.side_effect = None


# ===================================================================
# convert_single (integration-style)
# ===================================================================


class TestConvertSingle:
    """Tests for the convert_single public entry-point."""

    def test_no_site_selected(self, deps, capsys):
        deps["select_site_fn"].return_value = None
        VirtualChassisManager.convert_single(
            apisession=deps["apisession"],
            select_site_fn=deps["select_site_fn"],
            safe_input_fn=deps["safe_input_fn"],
            get_csv_path_fn=deps["get_csv_path_fn"],
            check_and_generate_csv_fn=deps["check_and_generate_csv_fn"],
            inventory_generator=deps["inventory_generator"],
        )
        assert "No site selected" in capsys.readouterr().out

    def test_no_switches_found(self, deps, tmp_path, capsys):
        inv_path = str(tmp_path / "data" / "OrgInventory.csv")
        _write_inventory_csv(inv_path, [])
        deps["get_csv_path_fn"].side_effect = lambda f: inv_path
        with patch.dict(sys.modules, {"mistapi": _mock_mistapi}):
            resp = MagicMock()
            resp.data = {"name": "TestSite"}
            _mock_mistapi.api.v1.sites.getSite.return_value = resp
            VirtualChassisManager.convert_single(
                apisession=deps["apisession"],
                select_site_fn=deps["select_site_fn"],
                safe_input_fn=deps["safe_input_fn"],
                get_csv_path_fn=deps["get_csv_path_fn"],
                check_and_generate_csv_fn=deps["check_and_generate_csv_fn"],
                inventory_generator=deps["inventory_generator"],
            )
        assert "No virtual chassis switches" in capsys.readouterr().out

    def test_dry_run(self, deps, tmp_path, capsys):
        inv_path = str(tmp_path / "data" / "OrgInventory.csv")
        _write_inventory_csv(
            inv_path,
            [{"type": "switch", "id": "d1", "site_id": "site-1", "name": "sw1"}],
        )
        deps["get_csv_path_fn"].side_effect = lambda f: inv_path
        deps["safe_input_fn"].return_value = "0"
        with patch.dict(sys.modules, {"mistapi": _mock_mistapi}):
            resp = MagicMock()
            resp.data = {"name": "TestSite"}
            _mock_mistapi.api.v1.sites.getSite.return_value = resp
            VirtualChassisManager.convert_single(
                apisession=deps["apisession"],
                select_site_fn=deps["select_site_fn"],
                safe_input_fn=deps["safe_input_fn"],
                get_csv_path_fn=deps["get_csv_path_fn"],
                check_and_generate_csv_fn=deps["check_and_generate_csv_fn"],
                inventory_generator=deps["inventory_generator"],
                dry_run=True,
            )
        assert "DRY RUN" in capsys.readouterr().out

    def test_user_cancels_conversion(self, deps, tmp_path, capsys):
        inv_path = str(tmp_path / "data" / "OrgInventory.csv")
        _write_inventory_csv(
            inv_path,
            [{"type": "switch", "id": "d1", "site_id": "site-1", "name": "sw1"}],
        )
        deps["get_csv_path_fn"].side_effect = lambda f: inv_path
        # First call selects switch "0", second call cancels "NOPE"
        deps["safe_input_fn"].side_effect = ["0", "NOPE"]
        with patch.dict(sys.modules, {"mistapi": _mock_mistapi}):
            resp = MagicMock()
            resp.data = {"name": "TestSite"}
            _mock_mistapi.api.v1.sites.getSite.return_value = resp
            VirtualChassisManager.convert_single(
                apisession=deps["apisession"],
                select_site_fn=deps["select_site_fn"],
                safe_input_fn=deps["safe_input_fn"],
                get_csv_path_fn=deps["get_csv_path_fn"],
                check_and_generate_csv_fn=deps["check_and_generate_csv_fn"],
                inventory_generator=deps["inventory_generator"],
            )
        assert "cancelled" in capsys.readouterr().out

    def test_no_switch_selected(self, deps, tmp_path, capsys):
        inv_path = str(tmp_path / "data" / "OrgInventory.csv")
        _write_inventory_csv(
            inv_path,
            [{"type": "switch", "id": "d1", "site_id": "site-1", "name": "sw1"}],
        )
        deps["get_csv_path_fn"].side_effect = lambda f: inv_path
        deps["safe_input_fn"].return_value = "nonexistent"
        with patch.dict(sys.modules, {"mistapi": _mock_mistapi}):
            resp = MagicMock()
            resp.data = {"name": "TestSite"}
            _mock_mistapi.api.v1.sites.getSite.return_value = resp
            VirtualChassisManager.convert_single(
                apisession=deps["apisession"],
                select_site_fn=deps["select_site_fn"],
                safe_input_fn=deps["safe_input_fn"],
                get_csv_path_fn=deps["get_csv_path_fn"],
                check_and_generate_csv_fn=deps["check_and_generate_csv_fn"],
                inventory_generator=deps["inventory_generator"],
            )
        # Should return silently with no crash
        out = capsys.readouterr().out
        assert "DESTRUCTIVE" in out

    def test_missing_device_id(self, deps, tmp_path, capsys):
        inv_path = str(tmp_path / "data" / "OrgInventory.csv")
        # Write a switch with a non-empty id so it passes the filter,
        # but we'll mock the selection to return one without id
        _write_inventory_csv(
            inv_path,
            [{"type": "switch", "id": "d1", "site_id": "site-1", "name": "sw1"}],
        )
        deps["get_csv_path_fn"].side_effect = lambda f: inv_path
        deps["safe_input_fn"].return_value = "0"
        with patch.dict(sys.modules, {"mistapi": _mock_mistapi}):
            resp = MagicMock()
            resp.data = {"name": "TestSite"}
            _mock_mistapi.api.v1.sites.getSite.return_value = resp
            # Patch _prompt_switch_selection to return a switch with empty id
            with patch.object(
                VirtualChassisManager,
                "_prompt_switch_selection",
                return_value={"name": "sw1", "id": ""},
            ):
                VirtualChassisManager.convert_single(
                    apisession=deps["apisession"],
                    select_site_fn=deps["select_site_fn"],
                    safe_input_fn=deps["safe_input_fn"],
                    get_csv_path_fn=deps["get_csv_path_fn"],
                    check_and_generate_csv_fn=deps["check_and_generate_csv_fn"],
                    inventory_generator=deps["inventory_generator"],
                )
        assert "Missing device_id" in capsys.readouterr().out


# ===================================================================
# convert_by_site_list (integration-style)
# ===================================================================


class TestConvertBySiteList:
    """Tests for the convert_by_site_list public entry-point."""

    def test_no_sites_in_csv(self, deps, tmp_path):
        csv_path = str(tmp_path / "data" / "VCConvert.CSV")
        _write_vc_csv(csv_path, [])
        deps["get_csv_path_fn"].side_effect = lambda f: str(tmp_path / "data" / f)
        VirtualChassisManager.convert_by_site_list(
            apisession=deps["apisession"],
            safe_input_fn=deps["safe_input_fn"],
            get_csv_path_fn=deps["get_csv_path_fn"],
            create_csv_template_fn=deps["create_csv_template_fn"],
            check_and_generate_csv_fn=deps["check_and_generate_csv_fn"],
            inventory_generator=deps["inventory_generator"],
            sites_generator=deps["sites_generator"],
        )
        # Empty CSV returns empty list, function returns early before printing
        deps["check_and_generate_csv_fn"].assert_not_called()

    def test_no_valid_sites(self, deps, tmp_path, capsys):
        csv_path = str(tmp_path / "data" / "VCConvert.CSV")
        _write_vc_csv(csv_path, ["NonexistentSite"])
        site_list_path = str(tmp_path / "data" / "SiteList.csv")
        _write_site_list_csv(site_list_path, [{"id": "s1", "name": "RealSite"}])

        def path_fn(f):
            return str(tmp_path / "data" / f)

        deps["get_csv_path_fn"].side_effect = path_fn
        VirtualChassisManager.convert_by_site_list(
            apisession=deps["apisession"],
            safe_input_fn=deps["safe_input_fn"],
            get_csv_path_fn=deps["get_csv_path_fn"],
            create_csv_template_fn=deps["create_csv_template_fn"],
            check_and_generate_csv_fn=deps["check_and_generate_csv_fn"],
            inventory_generator=deps["inventory_generator"],
            sites_generator=deps["sites_generator"],
        )
        out = capsys.readouterr().out
        assert "No valid sites found" in out

    def test_user_cancels(self, deps, tmp_path, capsys):
        csv_path = str(tmp_path / "data" / "VCConvert.CSV")
        _write_vc_csv(csv_path, ["SiteA"])
        site_list_path = str(tmp_path / "data" / "SiteList.csv")
        _write_site_list_csv(site_list_path, [{"id": "s1", "name": "SiteA"}])
        inv_path = str(tmp_path / "data" / "OrgInventory.csv")
        _write_inventory_csv(
            inv_path,
            [{"type": "switch", "id": "d1", "site_id": "s1", "name": "sw1"}],
        )

        def path_fn(f):
            return str(tmp_path / "data" / f)

        deps["get_csv_path_fn"].side_effect = path_fn
        deps["safe_input_fn"].return_value = "no"
        VirtualChassisManager.convert_by_site_list(
            apisession=deps["apisession"],
            safe_input_fn=deps["safe_input_fn"],
            get_csv_path_fn=deps["get_csv_path_fn"],
            create_csv_template_fn=deps["create_csv_template_fn"],
            check_and_generate_csv_fn=deps["check_and_generate_csv_fn"],
            inventory_generator=deps["inventory_generator"],
            sites_generator=deps["sites_generator"],
        )
        out = capsys.readouterr().out
        assert "cancelled" in out


# ===================================================================
# check_status (integration-style)
# ===================================================================


class TestCheckStatus:
    """Tests for the check_status public entry-point."""

    def test_no_vc_switches(self, deps, tmp_path, capsys):
        inv_path = str(tmp_path / "data" / "OrgInventory.csv")
        _write_inventory_csv(inv_path, [{"type": "ap", "vc_mac": ""}])

        def path_fn(f):
            return str(tmp_path / "data" / f)

        deps["get_csv_path_fn"].side_effect = path_fn
        VirtualChassisManager.check_status(
            get_csv_path_fn=deps["get_csv_path_fn"],
            check_and_generate_csv_fn=deps["check_and_generate_csv_fn"],
            inventory_generator=deps["inventory_generator"],
            sites_generator=deps["sites_generator"],
            flatten_fields_fn=deps["flatten_fields_fn"],
            escape_multiline_fn=deps["escape_multiline_fn"],
            save_data_fn=deps["save_data_fn"],
        )
        out = capsys.readouterr().out
        assert "No switches with vc_mac" in out

    def test_with_vc_switches(self, deps, tmp_path, capsys):
        inv_path = str(tmp_path / "data" / "OrgInventory.csv")
        _write_inventory_csv(
            inv_path,
            [
                {
                    "type": "switch",
                    "vc_mac": "020003aabbcc",
                    "site_id": "s1",
                    "name": "sw1",
                },
                {
                    "type": "switch",
                    "vc_mac": "ffeeddaabbcc",
                    "site_id": "s1",
                    "name": "sw2",
                },
            ],
        )
        site_path = str(tmp_path / "data" / "SiteList.csv")
        _write_site_list_csv(site_path, [{"id": "s1", "name": "SiteA"}])

        def path_fn(f):
            return str(tmp_path / "data" / f)

        deps["get_csv_path_fn"].side_effect = path_fn
        VirtualChassisManager.check_status(
            get_csv_path_fn=deps["get_csv_path_fn"],
            check_and_generate_csv_fn=deps["check_and_generate_csv_fn"],
            inventory_generator=deps["inventory_generator"],
            sites_generator=deps["sites_generator"],
            flatten_fields_fn=deps["flatten_fields_fn"],
            escape_multiline_fn=deps["escape_multiline_fn"],
            save_data_fn=deps["save_data_fn"],
        )
        out = capsys.readouterr().out
        assert "Converted to virtual MAC: 1" in out
        assert "Not converted: 1" in out
        deps["save_data_fn"].assert_called_once()


# ===================================================================
# _handle_missing_csv
# ===================================================================


class TestHandleMissingCsv:
    """Tests for _handle_missing_csv."""

    def test_user_declines(self, capsys):
        safe_fn = MagicMock(return_value="n")
        create_fn = MagicMock()
        VirtualChassisManager._handle_missing_csv("path.csv", create_fn, safe_fn)
        create_fn.assert_not_called()
        assert "not found" in capsys.readouterr().out

    def test_user_accepts(self, capsys):
        safe_fn = MagicMock(return_value="y")
        create_fn = MagicMock(return_value="/data/VCConvert.CSV")
        VirtualChassisManager._handle_missing_csv("path.csv", create_fn, safe_fn)
        create_fn.assert_called_once_with("VCConvert.CSV")

    def test_create_fails(self, capsys):
        safe_fn = MagicMock(return_value="yes")
        create_fn = MagicMock(side_effect=OSError("denied"))
        VirtualChassisManager._handle_missing_csv("path.csv", create_fn, safe_fn)
        assert "Failed to create" in capsys.readouterr().out


# ===========================================================================
# Coverage gaps: lines 102, 112 in convert_single
# ===========================================================================


class TestConvertSingleCoverageGaps:
    """Tests targeting uncovered lines 102 and 112 in convert_single."""

    def test_preflight_fails_returns_at_line_102(self, deps, tmp_path) -> None:
        """Line 102: _preflight_check returns False → early return, no conversion."""
        inv_path = str(tmp_path / "data" / "OrgInventory.csv")  # path for inventory csv
        _write_inventory_csv(  # create inventory with one switch so selection works
            inv_path,
            [{"type": "switch", "id": "d1", "site_id": "site-1", "name": "sw1"}],
        )
        deps["get_csv_path_fn"].side_effect = lambda f: (  # return inventory path for Inventory requests
            inv_path if "Inventory" in f else str(tmp_path / "data" / f)
        )
        deps["safe_input_fn"].return_value = "0"  # select first switch in menu
        with patch.dict(sys.modules, {"mistapi": _mock_mistapi}):  # inject mock mistapi
            resp = MagicMock()  # mock site API response
            resp.data = {"name": "TestSite"}  # set expected site name field
            _mock_mistapi.api.v1.sites.getSite.return_value = resp  # return mock site
            with patch.object(VirtualChassisManager, "_preflight_check", return_value=False):  # force fail
                with patch.object(VirtualChassisManager, "_execute_conversion") as mock_exec:  # spy
                    VirtualChassisManager.convert_single(  # call with preflight failing
                        apisession=deps["apisession"],
                        select_site_fn=deps["select_site_fn"],
                        safe_input_fn=deps["safe_input_fn"],
                        get_csv_path_fn=deps["get_csv_path_fn"],
                        check_and_generate_csv_fn=deps["check_and_generate_csv_fn"],
                        inventory_generator=deps["inventory_generator"],
                    )
                    mock_exec.assert_not_called()  # line 102 hit: returned before _execute_conversion

    def test_execute_conversion_called_at_line_112(self, deps, tmp_path) -> None:
        """Line 112: all guards pass + user confirms CONVERT → _execute_conversion called."""
        inv_path = str(tmp_path / "data" / "OrgInventory.csv")  # path for inventory csv
        _write_inventory_csv(  # create inventory with one switch for selection
            inv_path,
            [{"type": "switch", "id": "d1", "site_id": "site-1", "name": "sw1"}],
        )
        deps["get_csv_path_fn"].side_effect = lambda f: (  # return inventory path for Inventory requests
            inv_path if "Inventory" in f else str(tmp_path / "data" / f)
        )
        deps["safe_input_fn"].side_effect = ["0", "CONVERT"]  # select switch then confirm
        with patch.dict(sys.modules, {"mistapi": _mock_mistapi}):  # inject mock mistapi
            resp = MagicMock()  # mock site API response
            resp.data = {"name": "TestSite"}  # expected site name field
            _mock_mistapi.api.v1.sites.getSite.return_value = resp  # return mock site
            with patch.object(VirtualChassisManager, "_preflight_check", return_value=True):  # pass check
                with patch.object(VirtualChassisManager, "_execute_conversion") as mock_exec:  # spy
                    VirtualChassisManager.convert_single(  # call with all guards passing
                        apisession=deps["apisession"],
                        select_site_fn=deps["select_site_fn"],
                        safe_input_fn=deps["safe_input_fn"],
                        get_csv_path_fn=deps["get_csv_path_fn"],
                        check_and_generate_csv_fn=deps["check_and_generate_csv_fn"],
                        inventory_generator=deps["inventory_generator"],
                    )
                    mock_exec.assert_called_once()  # line 112: _execute_conversion reached


# ===========================================================================
# Coverage gaps: lines 153, 169-171, 184 in convert_by_site_list
# ===========================================================================


class TestConvertBySiteListCoverageGaps:
    """Tests targeting uncovered lines 153, 169-171, and 184 in convert_by_site_list."""

    def test_empty_site_mapping_returns_at_line_153(self, deps, tmp_path, capsys) -> None:
        """Line 153: SiteList.csv header-only → site_name_to_id empty → early return."""
        vc_path = str(tmp_path / "data" / "VCConvert.CSV")  # path for VCConvert.CSV
        _write_vc_csv(vc_path, ["SiteA"])  # write one site name to trigger non-empty path
        site_list_path = str(tmp_path / "data" / "SiteList.csv")  # path for SiteList.csv
        _write_site_list_csv(site_list_path, [])  # write header-only → empty mapping dict

        def path_fn(f: str) -> str:
            return str(tmp_path / "data" / f)  # return path for any filename in data dir

        deps["get_csv_path_fn"].side_effect = path_fn  # return correct paths per filename
        VirtualChassisManager.convert_by_site_list(  # call; should return early at line 153
            apisession=deps["apisession"],
            safe_input_fn=deps["safe_input_fn"],
            get_csv_path_fn=deps["get_csv_path_fn"],
            create_csv_template_fn=deps["create_csv_template_fn"],
            check_and_generate_csv_fn=deps["check_and_generate_csv_fn"],
            inventory_generator=deps["inventory_generator"],
            sites_generator=deps["sites_generator"],
        )
        assert "SiteA" in capsys.readouterr().out  # site names printed before early return

    def test_no_switches_in_target_sites_lines_169_171(self, deps, tmp_path, capsys) -> None:
        """Lines 169-171: target sites found but no VC switches exist → early return."""
        vc_path = str(tmp_path / "data" / "VCConvert.CSV")  # path for VCConvert.CSV
        _write_vc_csv(vc_path, ["SiteA"])  # site name that maps to a valid site id
        site_list_path = str(tmp_path / "data" / "SiteList.csv")  # path for SiteList.csv
        _write_site_list_csv(site_list_path, [{"id": "s1", "name": "SiteA"}])  # SiteA → s1
        inv_path = str(tmp_path / "data" / "OrgInventory.csv")  # path for OrgInventory.csv
        _write_inventory_csv(inv_path, [])  # empty inventory → no switches for site s1

        def path_fn(f: str) -> str:
            return str(tmp_path / "data" / f)  # return path for any filename in data dir

        deps["get_csv_path_fn"].side_effect = path_fn  # return correct paths per filename
        VirtualChassisManager.convert_by_site_list(  # call; should hit lines 169-171
            apisession=deps["apisession"],
            safe_input_fn=deps["safe_input_fn"],
            get_csv_path_fn=deps["get_csv_path_fn"],
            create_csv_template_fn=deps["create_csv_template_fn"],
            check_and_generate_csv_fn=deps["check_and_generate_csv_fn"],
            inventory_generator=deps["inventory_generator"],
            sites_generator=deps["sites_generator"],
        )
        out = capsys.readouterr().out  # capture printed output
        assert "No virtual chassis switches" in out  # lines 169-171: message printed

    def test_user_confirms_executes_bulk_conversion_line_184(self, deps, tmp_path) -> None:
        """Line 184: switches found + user confirms CONVERT → _execute_bulk_conversion called."""
        vc_path = str(tmp_path / "data" / "VCConvert.CSV")  # path for VCConvert.CSV
        _write_vc_csv(vc_path, ["SiteA"])  # site name that maps to valid site
        site_list_path = str(tmp_path / "data" / "SiteList.csv")  # path for SiteList.csv
        _write_site_list_csv(site_list_path, [{"id": "s1", "name": "SiteA"}])  # SiteA → s1
        inv_path = str(tmp_path / "data" / "OrgInventory.csv")  # path for OrgInventory.csv
        _write_inventory_csv(  # create one switch for site s1 so target_ids resolves
            inv_path,
            [{"type": "switch", "id": "d1", "site_id": "s1", "name": "sw1"}],
        )

        def path_fn(f: str) -> str:
            return str(tmp_path / "data" / f)  # return path for any filename in data dir

        deps["get_csv_path_fn"].side_effect = path_fn  # return correct paths per filename
        deps["safe_input_fn"].return_value = "CONVERT"  # user confirms bulk conversion
        with patch.object(VirtualChassisManager, "_execute_bulk_conversion") as mock_exec:  # spy
            VirtualChassisManager.convert_by_site_list(  # call; should reach line 184
                apisession=deps["apisession"],
                safe_input_fn=deps["safe_input_fn"],
                get_csv_path_fn=deps["get_csv_path_fn"],
                create_csv_template_fn=deps["create_csv_template_fn"],
                check_and_generate_csv_fn=deps["check_and_generate_csv_fn"],
                inventory_generator=deps["inventory_generator"],
                sites_generator=deps["sites_generator"],
            )
        mock_exec.assert_called_once()  # line 184: _execute_bulk_conversion reached


# ===========================================================================
# Coverage gap: lines 408-411 in _load_site_names_from_csv
# ===========================================================================


class TestLoadSiteNamesFromCsvExceptBlock:
    """Tests targeting uncovered lines 408-411 in _load_site_names_from_csv."""

    def test_open_raises_when_path_is_directory(self, deps, tmp_path) -> None:
        """Lines 408-411: open() raises PermissionError on directory → except → returns []."""
        data_dir = str(tmp_path / "data")  # base directory for CSV files
        csv_path = os.path.join(data_dir, "VCConvert.CSV")  # path that will be a directory
        os.makedirs(csv_path, exist_ok=True)  # create DIRECTORY at csv_path (not a file)
        deps["get_csv_path_fn"].side_effect = lambda f: os.path.join(data_dir, f)  # return paths
        result = VirtualChassisManager._load_site_names_from_csv(  # call the method
            deps["get_csv_path_fn"],
            deps["create_csv_template_fn"],
            deps["safe_input_fn"],
        )
        assert result == []  # except block catches PermissionError/IsADirectoryError → []
