"""Unit tests for E911BSSIDReportGenerator in src/reports/e911_bssid.py."""

import os
import sys
import time
from unittest.mock import MagicMock, patch

import pytest

from src.reports.e911_bssid import E911BSSIDReportGenerator, SiteBatchContext


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _clean_files(tmp_path, monkeypatch):
    """Run each test in a temp directory to avoid file side effects."""
    monkeypatch.chdir(tmp_path)
    os.makedirs("data", exist_ok=True)
    yield


@pytest.fixture()
def sample_sites():
    """Minimal site list from API."""
    return [
        {
            "id": "site-aaa",
            "name": "HQ",
            "address": "123 Main St",
            "sitegroup_ids": ["sg-1"],
            "sitetemplate_id": "st-1",
        },
        {
            "id": "site-bbb",
            "name": "Branch",
            "address": "456 Oak Ave",
            "sitegroup_ids": [],
            "sitetemplate_id": "",
        },
    ]


@pytest.fixture()
def site_lookup(sample_sites):
    """Pre-built site lookup dict."""
    return E911BSSIDReportGenerator._build_site_lookup(sample_sites)


@pytest.fixture()
def ap_lookup():
    """AP stats lookup dict."""
    return {
        "aa:bb:cc:dd:ee:ff": {
            "name": "AP-Lobby",
            "site_id": "site-aaa",
            "map_id": "map-1",
        },
        "11:22:33:44:55:66": {
            "name": "AP-Conf",
            "site_id": "site-bbb",
            "map_id": "",
        },
    }


@pytest.fixture()
def radio_macs_data():
    """Radio MAC data with 3-radio AP (last is scanning)."""
    return [
        {
            "mac": "aa:bb:cc:dd:ee:ff",
            "radio_mac": ["d4:20:b0:00:10:00", "d4:20:b0:00:20:00", "d4:20:b0:00:30:00"],
        },
    ]


@pytest.fixture()
def lookups(site_lookup, ap_lookup):
    """Full lookups dict for row building."""
    return {
        "sites": site_lookup,
        "aps": ap_lookup,
        "maps": {"map-1": "Lobby Floor"},
        "radio_bands": {
            "d4:20:b0:00:10:00": {"band": "6 GHz", "band_key": "band_6"},
            "d4:20:b0:00:20:00": {"band": "5 GHz", "band_key": "band_5"},
        },
        "wlan_bands": {
            "site-aaa::band_6": ["Corp-WiFi6E"],
            "site-aaa::band_5": ["Corp-WiFi", "Guest"],
        },
        "radio_macs": [],
    }


# ---------------------------------------------------------------------------
# _format_bssid
# ---------------------------------------------------------------------------
class TestFormatBssid:
    """Tests for BSSID derivation from radio base MAC."""

    def test_returns_16_bssids(self):
        """Always returns exactly 16 BSSIDs."""
        result = E911BSSIDReportGenerator._format_bssid("d4:20:b0:aa:bb:c0")
        assert len(result) == 16

    def test_colon_format(self):
        """Each BSSID is colon-separated."""
        result = E911BSSIDReportGenerator._format_bssid("d4:20:b0:aa:bb:c0")
        for bssid in result:
            assert bssid.count(":") == 5
            assert len(bssid) == 17

    def test_sequential_last_nibble(self):
        """BSSIDs increment the last nibble from 0 to f."""
        result = E911BSSIDReportGenerator._format_bssid("d4:20:b0:aa:bb:c5")
        last_nibbles = [bssid[-1] for bssid in result]
        assert last_nibbles == [format(i, "x") for i in range(16)]

    def test_clears_original_nibble(self):
        """Base MAC nibble is cleared before offset, regardless of input."""
        result_a = E911BSSIDReportGenerator._format_bssid("d4:20:b0:aa:bb:c0")
        result_b = E911BSSIDReportGenerator._format_bssid("d4:20:b0:aa:bb:cf")
        assert result_a == result_b

    def test_dash_separated_input(self):
        """Handles dash-separated MAC input."""
        result = E911BSSIDReportGenerator._format_bssid("d4-20-b0-aa-bb-c0")
        assert len(result) == 16

    def test_no_separator_input(self):
        """Handles raw hex MAC input."""
        result = E911BSSIDReportGenerator._format_bssid("d420b0aabbc0")
        assert len(result) == 16


# ---------------------------------------------------------------------------
# _build_site_lookup
# ---------------------------------------------------------------------------
class TestBuildSiteLookup:
    """Tests for site lookup dictionary construction."""

    def test_builds_correct_keys(self, sample_sites):
        """Lookup is keyed by site ID."""
        result = E911BSSIDReportGenerator._build_site_lookup(sample_sites)
        assert set(result.keys()) == {"site-aaa", "site-bbb"}

    def test_preserves_fields(self, sample_sites):
        """Lookup retains name, address, sitegroup_ids, sitetemplate_id."""
        result = E911BSSIDReportGenerator._build_site_lookup(sample_sites)
        assert result["site-aaa"]["name"] == "HQ"
        assert result["site-aaa"]["address"] == "123 Main St"
        assert result["site-aaa"]["sitegroup_ids"] == ["sg-1"]
        assert result["site-aaa"]["sitetemplate_id"] == "st-1"

    def test_empty_list(self):
        """Empty input returns empty dict."""
        assert E911BSSIDReportGenerator._build_site_lookup([]) == {}

    def test_skips_missing_id(self):
        """Sites without id are skipped."""
        result = E911BSSIDReportGenerator._build_site_lookup([{"name": "NoID"}])
        assert result == {}

    def test_defaults_for_missing_fields(self):
        """Missing optional fields default to empty."""
        result = E911BSSIDReportGenerator._build_site_lookup([{"id": "s1"}])
        assert result["s1"]["name"] == ""
        assert result["s1"]["address"] == ""
        assert result["s1"]["sitegroup_ids"] == []
        assert result["s1"]["sitetemplate_id"] == ""


# ---------------------------------------------------------------------------
# _infer_radio_bands
# ---------------------------------------------------------------------------
class TestInferRadioBands:
    """Tests for radio band inference from MAC positions."""

    def test_three_radio_ap(self):
        """3-radio AP: 2 broadcast (5, 2.4), last=scanning (excluded)."""
        data = [{"radio_mac": ["r1", "r2", "r3"]}]
        result = E911BSSIDReportGenerator._infer_radio_bands(data)
        assert result["r1"]["band"] == "5 GHz"
        assert result["r2"]["band"] == "2.4 GHz"
        assert "r3" not in result

    def test_two_radio_ap(self):
        """2-radio AP: first=2.4GHz (broadcast), second=scanning (excluded)."""
        data = [{"radio_mac": ["r1", "r2"]}]
        result = E911BSSIDReportGenerator._infer_radio_bands(data)
        assert result["r1"]["band"] == "2.4 GHz"
        assert "r2" not in result

    def test_single_radio_skipped(self):
        """Single radio (< 2) is skipped entirely."""
        data = [{"radio_mac": ["r1"]}]
        result = E911BSSIDReportGenerator._infer_radio_bands(data)
        assert result == {}

    def test_empty_data(self):
        """Empty input returns empty dict."""
        assert E911BSSIDReportGenerator._infer_radio_bands([]) == {}

    def test_four_radio_ap(self):
        """4-radio AP: 3 broadcast (6, 5, 2.4), last=scanning."""
        data = [{"radio_mac": ["r1", "r2", "r3", "r4"]}]
        result = E911BSSIDReportGenerator._infer_radio_bands(data)
        assert result["r1"]["band"] == "6 GHz"
        assert result["r2"]["band"] == "5 GHz"
        assert result["r3"]["band"] == "2.4 GHz"
        assert "r4" not in result


# ---------------------------------------------------------------------------
# _resolve_wlan_bands
# ---------------------------------------------------------------------------
class TestResolveWlanBands:
    """Tests for WLAN band string resolution."""

    def test_empty_string_all_bands(self):
        """Empty band string means all three bands."""
        result = E911BSSIDReportGenerator._resolve_wlan_bands("", E911BSSIDReportGenerator.BAND_MAP)
        assert set(result) == {"band_24", "band_5", "band_6"}

    def test_both_means_24_and_5(self):
        """'both' resolves to 2.4 and 5 GHz."""
        result = E911BSSIDReportGenerator._resolve_wlan_bands("both", E911BSSIDReportGenerator.BAND_MAP)
        assert result == ["band_24", "band_5"]

    def test_specific_band(self):
        """Numeric band string resolves via BAND_MAP."""
        result = E911BSSIDReportGenerator._resolve_wlan_bands("5", E911BSSIDReportGenerator.BAND_MAP)
        assert result == ["band_5"]

    def test_comma_separated(self):
        """Comma-separated band string splits correctly."""
        result = E911BSSIDReportGenerator._resolve_wlan_bands("24,5", E911BSSIDReportGenerator.BAND_MAP)
        assert result == ["band_24", "band_5"]


# ---------------------------------------------------------------------------
# _detect_gap
# ---------------------------------------------------------------------------
class TestDetectGap:
    """Tests for compliance gap detection."""

    def test_no_ap_info(self, lookups):
        """Missing AP info returns gap reason."""
        assert E911BSSIDReportGenerator._detect_gap({}, lookups) == "Not in device stats"

    def test_no_site(self, lookups):
        """AP without site_id returns gap."""
        result = E911BSSIDReportGenerator._detect_gap({"site_id": ""}, lookups)
        assert result == "No site assignment"

    def test_no_map(self, lookups):
        """AP without map_id returns gap."""
        result = E911BSSIDReportGenerator._detect_gap(
            {"site_id": "site-aaa", "map_id": ""},
            lookups,
        )
        assert result == "No map assignment"

    def test_unknown_map(self, lookups):
        """AP with map_id not in lookups returns gap."""
        result = E911BSSIDReportGenerator._detect_gap(
            {"site_id": "site-aaa", "map_id": "map-unknown"},
            lookups,
        )
        assert result == "Map ID not found"

    def test_no_gap(self, lookups):
        """AP with site and valid map returns empty string."""
        result = E911BSSIDReportGenerator._detect_gap(
            {"site_id": "site-aaa", "map_id": "map-1"},
            lookups,
        )
        assert result == ""


# ---------------------------------------------------------------------------
# _resolve_location
# ---------------------------------------------------------------------------
class TestResolveLocation:
    """Tests for site/map name resolution."""

    def test_no_site_id(self, lookups):
        """Empty site_id returns Unassigned."""
        name, addr, map_name = E911BSSIDReportGenerator._resolve_location("", "", lookups)
        assert name == "Unassigned"
        assert map_name == "Unassigned"

    def test_no_map_id(self, lookups):
        """Valid site but no map returns Unassigned map."""
        name, addr, map_name = E911BSSIDReportGenerator._resolve_location("site-aaa", "", lookups)
        assert name == "HQ"
        assert map_name == "Unassigned"

    def test_unknown_map_id(self, lookups):
        """Map ID not in lookup returns Unknown Map."""
        _, _, map_name = E911BSSIDReportGenerator._resolve_location("site-aaa", "map-bad", lookups)
        assert map_name == "Unknown Map"

    def test_valid_location(self, lookups):
        """Full resolution with known site and map."""
        name, addr, map_name = E911BSSIDReportGenerator._resolve_location("site-aaa", "map-1", lookups)
        assert name == "HQ"
        assert addr == "123 Main St"
        assert map_name == "Lobby Floor"


# ---------------------------------------------------------------------------
# _get_assigned_template_ids
# ---------------------------------------------------------------------------
class TestGetAssignedTemplateIds:
    """Tests for WLAN template assignment logic."""

    def test_org_wide_template(self):
        """Template with org_id applies to all sites."""
        templates = [{"id": "t1", "applies": {"org_id": "org-1"}}]
        result = E911BSSIDReportGenerator._get_assigned_template_ids("site-aaa", {}, templates)
        assert result == {"t1"}

    def test_site_specific_template(self):
        """Template assigned to specific site_ids."""
        templates = [{"id": "t1", "applies": {"site_ids": ["site-aaa", "site-bbb"]}}]
        result = E911BSSIDReportGenerator._get_assigned_template_ids("site-aaa", {}, templates)
        assert result == {"t1"}

    def test_sitegroup_template(self):
        """Template assigned via sitegroup membership."""
        templates = [{"id": "t1", "applies": {"sitegroup_ids": ["sg-1"]}}]
        site_info = {"sitegroup_ids": ["sg-1"]}
        result = E911BSSIDReportGenerator._get_assigned_template_ids("site-aaa", site_info, templates)
        assert result == {"t1"}

    def test_no_match(self):
        """Template not matching site returns empty."""
        templates = [{"id": "t1", "applies": {"site_ids": ["site-other"]}}]
        result = E911BSSIDReportGenerator._get_assigned_template_ids("site-aaa", {}, templates)
        assert result == set()

    def test_non_dict_applies(self):
        """Non-dict applies field is safely ignored."""
        templates = [{"id": "t1", "applies": "invalid"}]
        result = E911BSSIDReportGenerator._get_assigned_template_ids("site-aaa", {}, templates)
        assert result == set()


# ---------------------------------------------------------------------------
# _add_wlans_to_band_lookup
# ---------------------------------------------------------------------------
class TestAddWlansToBandLookup:
    """Tests for WLAN band population."""

    def test_adds_enabled_wlan(self):
        """Enabled WLAN with band is added to lookup."""
        lookup: dict[str, list[str]] = {}
        wlans = [{"enabled": True, "ssid": "Corp", "band": "5"}]
        E911BSSIDReportGenerator._add_wlans_to_band_lookup("s1", wlans, lookup)
        assert lookup["s1::band_5"] == ["Corp"]

    def test_skips_disabled_wlan(self):
        """Disabled WLANs are not added."""
        lookup: dict[str, list[str]] = {}
        wlans = [{"enabled": False, "ssid": "Hidden", "band": "5"}]
        E911BSSIDReportGenerator._add_wlans_to_band_lookup("s1", wlans, lookup)
        assert lookup == {}

    def test_skips_empty_ssid(self):
        """WLANs without SSID name are skipped."""
        lookup: dict[str, list[str]] = {}
        wlans = [{"enabled": True, "ssid": "", "band": "5"}]
        E911BSSIDReportGenerator._add_wlans_to_band_lookup("s1", wlans, lookup)
        assert lookup == {}

    def test_no_duplicates(self):
        """Same SSID is not added twice to the same band."""
        lookup: dict[str, list[str]] = {}
        wlans = [
            {"enabled": True, "ssid": "Corp", "band": "5"},
            {"enabled": True, "ssid": "Corp", "band": "5"},
        ]
        E911BSSIDReportGenerator._add_wlans_to_band_lookup("s1", wlans, lookup)
        assert lookup["s1::band_5"] == ["Corp"]

    def test_empty_band_goes_to_all(self):
        """WLAN with no band applies to all three bands."""
        lookup: dict[str, list[str]] = {}
        wlans = [{"enabled": True, "ssid": "Open", "band": ""}]
        E911BSSIDReportGenerator._add_wlans_to_band_lookup("s1", wlans, lookup)
        assert "s1::band_24" in lookup
        assert "s1::band_5" in lookup
        assert "s1::band_6" in lookup


# ---------------------------------------------------------------------------
# _build_bssid_rows
# ---------------------------------------------------------------------------
class TestBuildBssidRows:
    """Tests for full BSSID row construction."""

    def test_generates_rows_for_broadcast_radios(self, radio_macs_data, lookups):
        """Only broadcast radios produce rows; scanning radio excluded."""
        rows, gaps = E911BSSIDReportGenerator._build_bssid_rows(radio_macs_data, lookups)
        assert len(rows) == 32  # 2 broadcast radios x 16 BSSIDs

    def test_rows_are_sorted(self, radio_macs_data, lookups):
        """Output rows are sorted by Site, Map, AP, Band, BSSID."""
        rows, _ = E911BSSIDReportGenerator._build_bssid_rows(radio_macs_data, lookups)
        sort_keys = [(r["Site Name"], r["Map Name"], r["AP Name"], r["Band"], r["BSSID"]) for r in rows]
        assert sort_keys == sorted(sort_keys)

    def test_detects_compliance_gaps(self, lookups):
        """APs without maps produce compliance gaps."""
        data = [{"mac": "11:22:33:44:55:66", "radio_mac": []}]
        _, gaps = E911BSSIDReportGenerator._build_bssid_rows(data, lookups)
        assert len(gaps) == 1
        assert gaps[0]["reason"] == "No map assignment"

    def test_row_fields(self, radio_macs_data, lookups):
        """Each row has all required E911 columns."""
        rows, _ = E911BSSIDReportGenerator._build_bssid_rows(radio_macs_data, lookups)
        expected_keys = {
            "Site Name",
            "Site Address",
            "Map Name",
            "AP Name",
            "AP MAC",
            "Band",
            "Radio MAC",
            "BSSID",
            "SSIDs on Band",
        }
        assert set(rows[0].keys()) == expected_keys

    def test_ssids_populated(self, radio_macs_data, lookups):
        """SSIDs from wlan_bands lookup appear in rows."""
        rows, _ = E911BSSIDReportGenerator._build_bssid_rows(radio_macs_data, lookups)
        band_5_rows = [r for r in rows if r["Band"] == "5 GHz"]
        assert all("Corp-WiFi" in r["SSIDs on Band"] for r in band_5_rows)


# ---------------------------------------------------------------------------
# _display_summary
# ---------------------------------------------------------------------------
class TestDisplaySummary:
    """Tests for report summary output."""

    def test_no_gaps(self, capsys):
        """Summary without gaps shows clean message."""
        E911BSSIDReportGenerator._display_summary(5, 20, 320, [])
        output = capsys.readouterr().out
        assert "Sites processed: 5" in output
        assert "No compliance gaps" in output

    def test_with_gaps(self, capsys):
        """Summary with gaps lists each one."""
        gaps = [{"ap_name": "AP-1", "ap_mac": "aa:bb", "reason": "No map"}]
        E911BSSIDReportGenerator._display_summary(5, 20, 320, gaps)
        output = capsys.readouterr().out
        assert "Compliance Gaps: 1" in output
        assert "AP-1" in output


# ---------------------------------------------------------------------------
# Checkpoint save/load/clear
# ---------------------------------------------------------------------------
class TestCheckpoint:
    """Tests for checkpoint file operations."""

    def test_save_and_load(self):
        """Saved checkpoint can be loaded back."""
        org_data = {"sites": {}, "aps": {}}
        E911BSSIDReportGenerator._save_checkpoint(
            "org-1",
            org_data,
            {"site-a", "site-b"},
            {"map-1": "Floor 1"},
            {"s::band_5": ["Corp"]},
        )
        result = E911BSSIDReportGenerator._load_checkpoint("org-1")
        assert result is not None
        assert set(result["completed_sites"]) == {"site-a", "site-b"}
        assert result["map_lookup"] == {"map-1": "Floor 1"}

    def test_load_wrong_org(self):
        """Checkpoint for different org returns None."""
        E911BSSIDReportGenerator._save_checkpoint("org-1", {}, set(), {}, {})
        assert E911BSSIDReportGenerator._load_checkpoint("org-2") is None

    def test_load_nonexistent(self):
        """Missing checkpoint file returns None."""
        assert E911BSSIDReportGenerator._load_checkpoint("org-1") is None

    def test_clear(self):
        """Clear removes the checkpoint file."""
        E911BSSIDReportGenerator._save_checkpoint("org-1", {}, set(), {}, {})
        E911BSSIDReportGenerator._clear_checkpoint()
        assert not os.path.exists(E911BSSIDReportGenerator.CHECKPOINT_FILE)

    def test_clear_nonexistent(self):
        """Clearing when no file exists does not raise."""
        E911BSSIDReportGenerator._clear_checkpoint()

    def test_load_corrupt_json(self):
        """Corrupt JSON returns None."""
        with open(E911BSSIDReportGenerator.CHECKPOINT_FILE, "w") as handle:
            handle.write("not json{{{")
        assert E911BSSIDReportGenerator._load_checkpoint("org-1") is None


# ---------------------------------------------------------------------------
# _restore_or_init
# ---------------------------------------------------------------------------
class TestRestoreOrInit:
    """Tests for checkpoint restoration logic."""

    def test_no_checkpoint_returns_empty(self):
        """Without checkpoint, returns fresh state."""
        result = E911BSSIDReportGenerator._restore_or_init("org-1", lambda *a, **kw: "n")
        assert result["org_data"] is None
        assert result["completed"] == set()

    def test_resume_from_checkpoint(self):
        """User answering 'y' restores checkpoint data."""
        org_data = {"sites": {"s1": {}}}
        E911BSSIDReportGenerator._save_checkpoint(
            "org-1",
            org_data,
            {"site-done"},
            {"m1": "Floor"},
            {"s::b": ["W"]},
        )
        result = E911BSSIDReportGenerator._restore_or_init("org-1", lambda *a, **kw: "y")
        assert result["org_data"] is not None
        assert "site-done" in result["completed"]

    def test_decline_checkpoint(self):
        """User answering 'n' clears checkpoint and starts fresh."""
        E911BSSIDReportGenerator._save_checkpoint("org-1", {}, set(), {}, {})
        result = E911BSSIDReportGenerator._restore_or_init("org-1", lambda *a, **kw: "n")
        assert result["org_data"] is None
        assert not os.path.exists(E911BSSIDReportGenerator.CHECKPOINT_FILE)


# ---------------------------------------------------------------------------
# _handle_rate_limit
# ---------------------------------------------------------------------------
class TestHandleRateLimit:
    """Tests for rate limit handling."""

    def test_saves_checkpoint_and_returns_false(self, capsys):
        """Rate limit handler saves state and returns False."""
        org_data = {"sites": {}}
        batch = SiteBatchContext(
            org_id="org-1",
            org_data=org_data,
            total_sites=10,
            completed_sites={"site-a"},
            map_lookup={"m1": "F1"},
            wlan_band_lookup={"k": ["v"]},
            wlan_context={},
        )
        result = E911BSSIDReportGenerator._handle_rate_limit(batch, 5)
        assert result is False
        assert os.path.exists(E911BSSIDReportGenerator.CHECKPOINT_FILE)
        output = capsys.readouterr().out
        assert "Rate limited" in output


# ---------------------------------------------------------------------------
# _write_report
# ---------------------------------------------------------------------------
class TestWriteReport:
    """Tests for report writing and cleanup."""

    def test_calls_write_fn(self, lookups, capsys):
        """Write function is called with rows and filename."""
        write_fn = MagicMock()
        radio_data = [
            {
                "mac": "aa:bb:cc:dd:ee:ff",
                "radio_mac": ["d4:20:b0:00:10:00", "d4:20:b0:00:20:00"],
            },
        ]
        site_state = {
            "maps": lookups["maps"],
            "wlan_bands": lookups["wlan_bands"],
        }
        org_data = {
            "sites": lookups["sites"],
            "aps": lookups["aps"],
            "radio_bands": lookups["radio_bands"],
        }
        E911BSSIDReportGenerator._write_report(
            org_data,
            radio_data,
            site_state,
            write_fn,
            time.time(),
        )
        write_fn.assert_called_once()
        call_kwargs = write_fn.call_args
        assert "E911_BSSID_Report_" in call_kwargs.kwargs.get(
            "filename_or_table",
            call_kwargs[1].get("filename_or_table", ""),
        )

    def test_clears_checkpoint_after_write(self, lookups):
        """Checkpoint file is removed after successful report."""
        E911BSSIDReportGenerator._save_checkpoint("org-1", {}, set(), {}, {})
        write_fn = MagicMock()
        org_data = {
            "sites": lookups["sites"],
            "aps": lookups["aps"],
            "radio_bands": lookups["radio_bands"],
        }
        site_state = {
            "maps": lookups["maps"],
            "wlan_bands": lookups["wlan_bands"],
        }
        E911BSSIDReportGenerator._write_report(
            org_data,
            [{"mac": "x", "radio_mac": []}],
            site_state,
            write_fn,
            time.time(),
        )
        assert not os.path.exists(E911BSSIDReportGenerator.CHECKPOINT_FILE)


# ---------------------------------------------------------------------------
# _append_ap_rows
# ---------------------------------------------------------------------------
class TestAppendApRows:
    """Tests for per-AP row construction."""

    def test_appends_rows(self, lookups):
        """Rows are appended for each broadcast radio."""
        rows: list[dict[str, str]] = []
        ap_entry = {
            "mac": "aa:bb:cc:dd:ee:ff",
            "radio_mac": ["d4:20:b0:00:10:00", "d4:20:b0:00:20:00"],
        }
        ap_info = lookups["aps"]["aa:bb:cc:dd:ee:ff"]
        E911BSSIDReportGenerator._append_ap_rows(ap_entry, ap_info, lookups, rows)
        assert len(rows) == 32  # 2 radios x 16 BSSIDs

    def test_skips_scanning_radio(self, lookups):
        """Radio without band mapping is skipped."""
        rows: list[dict[str, str]] = []
        ap_entry = {"mac": "aa:bb:cc:dd:ee:ff", "radio_mac": ["unknown-mac"]}
        ap_info = lookups["aps"]["aa:bb:cc:dd:ee:ff"]
        E911BSSIDReportGenerator._append_ap_rows(ap_entry, ap_info, lookups, rows)
        assert len(rows) == 0


# ---------------------------------------------------------------------------
# execute (integration-level with mocks)
# ---------------------------------------------------------------------------
class TestExecute:
    """Integration tests for the top-level execute method."""

    def test_no_aps_exits_early(self, capsys):
        """If no APs found, report exits with message."""
        mock_api = MagicMock()

        def fake_fetch_bulk(*args, **kwargs):
            return {
                "sites": {},
                "aps": {},
                "wlan_templates": [],
                "org_wlans": [],
                "site_template_cache": {},
                "radio_macs": [],
                "radio_bands": {},
            }

        with patch.object(
            E911BSSIDReportGenerator,
            "_fetch_org_bulk_data",
            side_effect=fake_fetch_bulk,
        ):
            E911BSSIDReportGenerator.execute(
                apisession=mock_api,
                page_limit=100,
                org_id="org-1",
                safe_input_fn=lambda *a, **kw: "n",
                write_data_fn=MagicMock(),
            )
        output = capsys.readouterr().out
        assert "No APs found" in output

    def test_full_run_writes_report(self, lookups):
        """Full execution with mocked data produces a report."""
        mock_api = MagicMock()
        write_fn = MagicMock()
        radio_data = [
            {
                "mac": "aa:bb:cc:dd:ee:ff",
                "radio_mac": ["d4:20:b0:00:10:00", "d4:20:b0:00:20:00"],
            },
        ]

        def fake_fetch_bulk(*args, **kwargs):
            return {
                "sites": lookups["sites"],
                "aps": lookups["aps"],
                "wlan_templates": [],
                "org_wlans": [],
                "site_template_cache": {},
                "radio_macs": radio_data,
                "radio_bands": lookups["radio_bands"],
            }

        def fake_process_sites(api, org_id, pl, org_data, state):
            state["maps"] = lookups["maps"]
            state["wlan_bands"] = lookups["wlan_bands"]
            return True

        with (
            patch.object(
                E911BSSIDReportGenerator,
                "_fetch_org_bulk_data",
                side_effect=fake_fetch_bulk,
            ),
            patch.object(
                E911BSSIDReportGenerator,
                "_process_sites",
                side_effect=fake_process_sites,
            ),
        ):
            E911BSSIDReportGenerator.execute(
                apisession=mock_api,
                page_limit=100,
                org_id="org-1",
                safe_input_fn=lambda *a, **kw: "n",
                write_data_fn=write_fn,
            )
        write_fn.assert_called_once()

    def test_rate_limited_run_stops_early(self, lookups, capsys):
        """Execution stops when rate-limited, doesn't call write."""
        mock_api = MagicMock()
        write_fn = MagicMock()

        def fake_fetch_bulk(*args, **kwargs):
            return {
                "sites": lookups["sites"],
                "aps": lookups["aps"],
                "wlan_templates": [],
                "org_wlans": [],
                "site_template_cache": {},
                "radio_macs": [{"mac": "aa:bb:cc:dd:ee:ff", "radio_mac": ["r1"]}],
                "radio_bands": {},
            }

        with (
            patch.object(
                E911BSSIDReportGenerator,
                "_fetch_org_bulk_data",
                side_effect=fake_fetch_bulk,
            ),
            patch.object(
                E911BSSIDReportGenerator,
                "_process_sites",
                return_value=False,
            ),
        ):
            E911BSSIDReportGenerator.execute(
                apisession=mock_api,
                page_limit=100,
                org_id="org-1",
                safe_input_fn=lambda *a, **kw: "n",
                write_data_fn=write_fn,
            )
        write_fn.assert_not_called()


# ---------------------------------------------------------------------------
# API-calling methods (mocked mistapi)
# ---------------------------------------------------------------------------
def _mock_mistapi():
    """Create a mock mistapi module with typical API response patterns."""
    mock_mod = MagicMock()
    mock_mod.get_all.return_value = []
    return mock_mod


class TestFetchAllSites:
    """Tests for _fetch_all_sites with mocked mistapi."""

    def test_returns_site_list(self):
        """Fetches and returns all sites via mistapi.get_all."""
        mock_api = MagicMock()
        mock_mistapi = _mock_mistapi()
        mock_mistapi.get_all.return_value = [{"id": "s1", "name": "HQ"}]
        with patch.dict(sys.modules, {"mistapi": mock_mistapi}):
            result = E911BSSIDReportGenerator._fetch_all_sites(mock_api, "org-1", 100)
        assert result == [{"id": "s1", "name": "HQ"}]


class TestFetchOrgBulkData:
    """Tests for _fetch_org_bulk_data with mocked mistapi."""

    def test_returns_all_bulk_data_keys(self):
        """Bulk data dict contains all expected keys."""
        mock_api = MagicMock()
        mock_mistapi = _mock_mistapi()

        # Mock response objects
        response = MagicMock()
        response.status_code = 200
        response.data = []
        mock_mistapi.api.v1.orgs.sites.listOrgSites.return_value = response
        mock_mistapi.api.v1.orgs.stats.listOrgDevicesStats.return_value = response
        mock_mistapi.api.v1.orgs.templates.listOrgTemplates.return_value = response
        mock_mistapi.api.v1.orgs.wlans.listOrgWlans.return_value = response
        mock_mistapi.api.v1.orgs.devices.listOrgApsMacs.return_value = response
        mock_mistapi.get_all.return_value = []

        with patch.dict(sys.modules, {"mistapi": mock_mistapi}):
            result = E911BSSIDReportGenerator._fetch_org_bulk_data(mock_api, "org-1", 100)

        expected_keys = {
            "sites",
            "aps",
            "wlan_templates",
            "org_wlans",
            "site_template_cache",
            "radio_macs",
            "radio_bands",
        }
        assert set(result.keys()) == expected_keys


class TestFetchApStats:
    """Tests for _fetch_ap_stats with mocked mistapi."""

    def test_builds_ap_lookup(self):
        """AP stats are indexed by MAC address."""
        mock_api = MagicMock()
        mock_mistapi = _mock_mistapi()
        mock_mistapi.get_all.return_value = [
            {"mac": "aa:bb", "name": "AP1", "site_id": "s1", "map_id": "m1"},
        ]

        with patch.dict(sys.modules, {"mistapi": mock_mistapi}):
            result = E911BSSIDReportGenerator._fetch_ap_stats(mock_api, "org-1", 100)

        assert "aa:bb" in result
        assert result["aa:bb"]["name"] == "AP1"


class TestPrefetchSiteTemplates:
    """Tests for _prefetch_site_templates with mocked mistapi."""

    def test_caches_unique_templates(self):
        """Unique site template IDs are fetched and cached."""
        mock_api = MagicMock()
        mock_mistapi = _mock_mistapi()
        response = MagicMock()
        response.status_code = 200
        response.data = {"wlans": {"w1": {"ssid": "Corp"}}}
        mock_mistapi.api.v1.orgs.sitetemplates.getOrgSiteTemplate.return_value = response

        site_lookup = {"s1": {"sitetemplate_id": "st-1"}, "s2": {"sitetemplate_id": "st-1"}}
        with patch.dict(sys.modules, {"mistapi": mock_mistapi}):
            result = E911BSSIDReportGenerator._prefetch_site_templates(mock_api, "org-1", site_lookup)

        assert "st-1" in result
        assert len(result["st-1"]) == 1  # one WLAN from dict values

    def test_handles_fetch_failure(self):
        """Failed template fetch returns empty list for that template."""
        mock_api = MagicMock()
        mock_mistapi = _mock_mistapi()
        mock_mistapi.api.v1.orgs.sitetemplates.getOrgSiteTemplate.side_effect = Exception("fail")

        site_lookup = {"s1": {"sitetemplate_id": "st-1"}}
        with patch.dict(sys.modules, {"mistapi": mock_mistapi}):
            result = E911BSSIDReportGenerator._prefetch_site_templates(mock_api, "org-1", site_lookup)

        assert result["st-1"] == []

    def test_non_200_returns_empty(self):
        """Non-200 response returns empty list."""
        mock_api = MagicMock()
        mock_mistapi = _mock_mistapi()
        response = MagicMock()
        response.status_code = 404
        mock_mistapi.api.v1.orgs.sitetemplates.getOrgSiteTemplate.return_value = response

        site_lookup = {"s1": {"sitetemplate_id": "st-1"}}
        with patch.dict(sys.modules, {"mistapi": mock_mistapi}):
            result = E911BSSIDReportGenerator._prefetch_site_templates(mock_api, "org-1", site_lookup)

        assert result["st-1"] == []


class TestFetchOrgWlanTemplates:
    """Tests for _fetch_org_wlan_templates with mocked mistapi."""

    def test_returns_template_list(self):
        """Returns list of WLAN templates on 200."""
        mock_api = MagicMock()
        mock_mistapi = _mock_mistapi()
        response = MagicMock()
        response.status_code = 200
        response.data = [{"id": "t1"}]
        mock_mistapi.api.v1.orgs.templates.listOrgTemplates.return_value = response

        with patch.dict(sys.modules, {"mistapi": mock_mistapi}):
            result = E911BSSIDReportGenerator._fetch_org_wlan_templates(mock_api, "org-1")

        assert result == [{"id": "t1"}]

    def test_non_200_returns_empty(self):
        """Non-200 response returns empty list."""
        mock_api = MagicMock()
        mock_mistapi = _mock_mistapi()
        response = MagicMock()
        response.status_code = 500
        mock_mistapi.api.v1.orgs.templates.listOrgTemplates.return_value = response

        with patch.dict(sys.modules, {"mistapi": mock_mistapi}):
            result = E911BSSIDReportGenerator._fetch_org_wlan_templates(mock_api, "org-1")

        assert result == []


class TestFetchOrgWlans:
    """Tests for _fetch_org_wlans with mocked mistapi."""

    def test_returns_wlan_list(self):
        """Returns list of org WLANs via get_all."""
        mock_api = MagicMock()
        mock_mistapi = _mock_mistapi()
        mock_mistapi.get_all.return_value = [{"id": "w1", "ssid": "Corp"}]

        with patch.dict(sys.modules, {"mistapi": mock_mistapi}):
            result = E911BSSIDReportGenerator._fetch_org_wlans(mock_api, "org-1", 100)

        assert result == [{"id": "w1", "ssid": "Corp"}]


class TestFetchSiteMaps:
    """Tests for _fetch_site_maps with mocked mistapi."""

    def test_populates_map_lookup(self):
        """Maps are added to the lookup dict."""
        mock_api = MagicMock()
        mock_mistapi = _mock_mistapi()
        response = MagicMock()
        response.status_code = 200
        mock_mistapi.api.v1.sites.maps.listSiteMaps.return_value = response
        mock_mistapi.get_all.return_value = [{"id": "m1", "name": "Floor 1"}]
        map_lookup: dict[str, str] = {}

        with patch.dict(sys.modules, {"mistapi": mock_mistapi}):
            E911BSSIDReportGenerator._fetch_site_maps(mock_api, "s1", 100, map_lookup)

        assert map_lookup["m1"] == "Floor 1"

    def test_raises_on_429(self):
        """HTTP 429 raises RuntimeError."""
        mock_api = MagicMock()
        mock_mistapi = _mock_mistapi()
        response = MagicMock()
        response.status_code = 429
        mock_mistapi.api.v1.sites.maps.listSiteMaps.return_value = response

        with patch.dict(sys.modules, {"mistapi": mock_mistapi}):
            with pytest.raises(RuntimeError, match="E911_RATE_LIMIT"):
                E911BSSIDReportGenerator._fetch_site_maps(mock_api, "s1", 100, {})


class TestResolveSiteSsids:
    """Tests for _resolve_site_ssids with mocked mistapi."""

    def test_adds_site_wlans(self):
        """Site-level WLANs are resolved and added to band lookup."""
        mock_api = MagicMock()
        mock_mistapi = _mock_mistapi()
        response = MagicMock()
        response.status_code = 200
        mock_mistapi.api.v1.sites.wlans.listSiteWlans.return_value = response
        mock_mistapi.get_all.return_value = [
            {"enabled": True, "ssid": "Local", "band": "5"},
        ]
        wlan_context = {
            "wlan_templates": [],
            "org_wlans": [],
            "wlan_band_lookup": {},
            "site_template_cache": {},
        }
        site_info = {"sitetemplate_id": "", "sitegroup_ids": []}

        with patch.dict(sys.modules, {"mistapi": mock_mistapi}):
            E911BSSIDReportGenerator._resolve_site_ssids(
                mock_api,
                "s1",
                100,
                site_info,
                wlan_context,
            )

        assert "s1::band_5" in wlan_context["wlan_band_lookup"]
        assert "Local" in wlan_context["wlan_band_lookup"]["s1::band_5"]

    def test_raises_on_429(self):
        """HTTP 429 raises RuntimeError."""
        mock_api = MagicMock()
        mock_mistapi = _mock_mistapi()
        response = MagicMock()
        response.status_code = 429
        mock_mistapi.api.v1.sites.wlans.listSiteWlans.return_value = response
        wlan_context = {
            "wlan_templates": [],
            "org_wlans": [],
            "wlan_band_lookup": {},
            "site_template_cache": {},
        }

        with patch.dict(sys.modules, {"mistapi": mock_mistapi}):
            with pytest.raises(RuntimeError, match="E911_RATE_LIMIT"):
                E911BSSIDReportGenerator._resolve_site_ssids(
                    mock_api,
                    "s1",
                    100,
                    {},
                    wlan_context,
                )

    def test_includes_cached_template_wlans(self):
        """Site template WLANs from cache are added to band lookup."""
        mock_api = MagicMock()
        mock_mistapi = _mock_mistapi()
        response = MagicMock()
        response.status_code = 200
        mock_mistapi.api.v1.sites.wlans.listSiteWlans.return_value = response
        mock_mistapi.get_all.return_value = []
        wlan_context = {
            "wlan_templates": [],
            "org_wlans": [],
            "wlan_band_lookup": {},
            "site_template_cache": {
                "st-1": [{"enabled": True, "ssid": "Template-SSID", "band": "24"}],
            },
        }
        site_info = {"sitetemplate_id": "st-1", "sitegroup_ids": []}

        with patch.dict(sys.modules, {"mistapi": mock_mistapi}):
            E911BSSIDReportGenerator._resolve_site_ssids(
                mock_api,
                "s1",
                100,
                site_info,
                wlan_context,
            )

        assert "Template-SSID" in wlan_context["wlan_band_lookup"].get("s1::band_24", [])


class TestProcessSites:
    """Tests for _process_sites with mocked API methods."""

    def test_all_cached_returns_true(self, capsys):
        """When all sites are already cached, returns True immediately."""
        org_data = {
            "aps": {"aa": {"site_id": "s1"}},
            "sites": {"s1": {}},
            "wlan_templates": [],
            "org_wlans": [],
            "site_template_cache": {},
        }
        site_state = {
            "completed": {"s1"},
            "maps": {},
            "wlan_bands": {},
        }
        result = E911BSSIDReportGenerator._process_sites(
            MagicMock(),
            "org-1",
            100,
            org_data,
            site_state,
        )
        assert result is True
        assert "already cached" in capsys.readouterr().out

    def test_processes_remaining_sites(self):
        """Processes remaining sites and returns True when complete."""
        org_data = {
            "aps": {"aa": {"site_id": "s1"}},
            "sites": {"s1": {}},
            "wlan_templates": [],
            "org_wlans": [],
            "site_template_cache": {},
        }
        site_state = {
            "completed": set(),
            "maps": {},
            "wlan_bands": {},
        }
        with patch.object(
            E911BSSIDReportGenerator,
            "_process_site_batch",
            return_value=True,
        ):
            result = E911BSSIDReportGenerator._process_sites(
                MagicMock(),
                "org-1",
                100,
                org_data,
                site_state,
            )
        assert result is True


class TestProcessSiteBatch:
    """Tests for _process_site_batch with mocked API methods."""

    def test_processes_all_sites(self):
        """All sites processed returns True."""
        org_data = {"sites": {"s1": {}}}  # WHY: minimal org_data with one site
        wctx = {  # WHY: wlan_context bundle used by SiteBatchContext
            "wlan_templates": [],
            "org_wlans": [],
            "wlan_band_lookup": {},
            "site_template_cache": {},
        }
        batch = SiteBatchContext(  # WHY: bundle 7 per-batch fields into the new 4-arg signature
            org_id="org-1",
            org_data=org_data,
            total_sites=1,
            completed_sites=set(),
            map_lookup={},
            wlan_band_lookup={},
            wlan_context=wctx,
        )
        with (
            patch.object(E911BSSIDReportGenerator, "_fetch_site_maps"),
            patch.object(E911BSSIDReportGenerator, "_resolve_site_ssids"),
        ):
            result = E911BSSIDReportGenerator._process_site_batch(
                MagicMock(),  # apisession
                100,  # page_limit
                ["s1"],  # remaining sites
                batch,  # SiteBatchContext bundling org state
            )
        assert result is True

    def test_rate_limit_returns_false(self):
        """Rate-limited site batch saves checkpoint and returns False."""
        org_data = {"sites": {"s1": {}}}  # WHY: minimal org_data with one site
        wctx = {  # WHY: wlan_context bundle used by SiteBatchContext
            "wlan_templates": [],
            "org_wlans": [],
            "wlan_band_lookup": {},
            "site_template_cache": {},
        }
        batch = SiteBatchContext(  # WHY: bundle 7 per-batch fields into the new 4-arg signature
            org_id="org-1",
            org_data=org_data,
            total_sites=1,
            completed_sites=set(),
            map_lookup={},
            wlan_band_lookup={},
            wlan_context=wctx,
        )
        with (
            patch.object(
                E911BSSIDReportGenerator,
                "_fetch_site_maps",
                side_effect=RuntimeError("E911_RATE_LIMIT"),
            ),
            patch.object(E911BSSIDReportGenerator, "_handle_rate_limit", return_value=False),
        ):
            result = E911BSSIDReportGenerator._process_site_batch(
                MagicMock(),  # apisession
                100,  # page_limit
                ["s1"],  # remaining sites
                batch,  # SiteBatchContext bundling org state
            )
        assert result is False

    def test_generic_error_continues(self):
        """Non-rate-limit errors are logged and site is marked done."""
        org_data = {"sites": {"s1": {}}}  # WHY: minimal org_data with one site
        completed: set[str] = set()  # WHY: track sites marked done via shared set
        wctx = {  # WHY: wlan_context bundle used by SiteBatchContext
            "wlan_templates": [],
            "org_wlans": [],
            "wlan_band_lookup": {},
            "site_template_cache": {},
        }
        batch = SiteBatchContext(  # WHY: bundle 7 per-batch fields into the new 4-arg signature
            org_id="org-1",
            org_data=org_data,
            total_sites=1,
            completed_sites=completed,
            map_lookup={},
            wlan_band_lookup={},
            wlan_context=wctx,
        )
        with (
            patch.object(
                E911BSSIDReportGenerator,
                "_fetch_site_maps",
                side_effect=ValueError("oops"),
            ),
        ):
            result = E911BSSIDReportGenerator._process_site_batch(
                MagicMock(),  # apisession
                100,  # page_limit
                ["s1"],  # remaining sites
                batch,  # SiteBatchContext bundling org state
            )
        assert result is True
        assert "s1" in completed

    def test_checkpoint_at_interval(self):
        """Checkpoint saved at CHECKPOINT_INTERVAL."""
        org_data = {"sites": {f"s{i}": {} for i in range(55)}}  # WHY: 55 sites > CHECKPOINT_INTERVAL (50)
        remaining = [f"s{i}" for i in range(55)]  # WHY: all 55 sites to process this run
        wctx = {  # WHY: wlan_context bundle used by SiteBatchContext
            "wlan_templates": [],
            "org_wlans": [],
            "wlan_band_lookup": {},
            "site_template_cache": {},
        }
        batch = SiteBatchContext(  # WHY: bundle 7 per-batch fields into the new 4-arg signature
            org_id="org-1",
            org_data=org_data,
            total_sites=55,
            completed_sites=set(),
            map_lookup={},
            wlan_band_lookup={},
            wlan_context=wctx,
        )
        with (
            patch.object(E911BSSIDReportGenerator, "_fetch_site_maps"),
            patch.object(E911BSSIDReportGenerator, "_resolve_site_ssids"),
            patch.object(E911BSSIDReportGenerator, "_save_checkpoint") as mock_save,
        ):
            E911BSSIDReportGenerator._process_site_batch(
                MagicMock(),  # apisession
                100,  # page_limit
                remaining,  # remaining sites
                batch,  # SiteBatchContext bundling org state
            )
        assert mock_save.call_count == 1  # At index 50


class TestSaveCheckpointOsError:
    """Edge case: OSError during checkpoint save."""

    def test_oserror_is_logged(self, tmp_path):
        """OSError during save is logged, not raised."""
        with patch(
            "builtins.open",
            side_effect=OSError("disk full"),
        ):
            E911BSSIDReportGenerator._save_checkpoint("org-1", {}, set(), {}, {})


# ===========================================================================
# Coverage gaps: lines 189, 359-361, 640
# ===========================================================================


class TestPreFetchSiteTemplatesNonDictWlans:
    """Line 189: wlans in response is a list (not dict) → cache entry set to []."""

    def test_template_wlans_list_sets_empty_cache(self):
        """Line 189: response.data['wlans'] is a list → else branch → cache[id]=[]."""
        mock_mistapi = MagicMock()  # mock the mistapi module for lazy import
        mock_resp = MagicMock()  # mock API response object
        mock_resp.status_code = 200  # simulate HTTP 200 OK
        mock_resp.data = {"wlans": [{"id": "w1", "ssid": "TestSSID"}]}  # list, not dict
        mock_mistapi.api.v1.orgs.sitetemplates.getOrgSiteTemplate.return_value = mock_resp  # set mock

        site_lookup = {"s1": {"sitetemplate_id": "tmpl-1", "name": "SiteA"}}  # one site with template
        with patch.dict("sys.modules", {"mistapi": mock_mistapi}):  # inject mock mistapi
            cache = E911BSSIDReportGenerator._prefetch_site_templates(
                apisession=MagicMock(),  # apisession not used directly with mocked mistapi
                org_id="org-1",
                site_lookup=site_lookup,
            )
        assert cache["tmpl-1"] == []  # list wlans → else branch → empty list cached


class TestResolveSiteSSIDsWithAssignedTemplates:
    """Lines 359-361: org WLANs from WLAN templates added when assigned_template_ids non-empty."""

    def test_org_wlans_via_templates_added_to_band_lookup(self):
        """Lines 359-361: site has wlan_templates assigned → org wlans added to lookup."""
        mock_mistapi = MagicMock()  # mock the mistapi module for lazy import
        mock_resp = MagicMock()  # mock site WLANs API response
        mock_resp.status_code = 200  # simulate HTTP 200 OK
        mock_mistapi.api.v1.sites.wlans.listSiteWlans.return_value = mock_resp  # set mock
        mock_mistapi.get_all.return_value = []  # no site-level WLANs to simplify test

        wlan_band_lookup: dict = {}  # lookup dict to populate
        site_info = {  # site info with no sitetemplate_id to skip that path
            "sitetemplate_id": None,
            "sitegroup_ids": [],
        }
        wlan_templates = [{"id": "tmpl-1", "applies": {"org_id": "org-1"}}]  # one template that applies to this org
        org_wlans = [  # one org WLAN assigned via template
            {"template_id": "tmpl-1", "enabled": True, "ssid": "OrgSSID", "band": ""}
        ]
        wlan_context = {  # full wlan context dict required by _resolve_site_ssids
            "wlan_templates": wlan_templates,
            "org_wlans": org_wlans,
            "wlan_band_lookup": wlan_band_lookup,
            "site_template_cache": {},
        }
        with patch.dict("sys.modules", {"mistapi": mock_mistapi}):  # inject mock mistapi
            E911BSSIDReportGenerator._resolve_site_ssids(
                apisession=MagicMock(),
                site_id="site-1",
                page_limit=1000,
                site_info=site_info,
                wlan_context=wlan_context,
            )
        # Lines 359-361: _add_wlans_to_band_lookup called + logging.debug → OrgSSID in lookup
        assert any("OrgSSID" in v for v in wlan_band_lookup.values())  # org WLAN was added


class TestProcessSiteBatchRateLimit:
    """Line 640: _process_site_batch returns from _handle_rate_limit on E911_RATE_LIMIT error."""

    def test_rate_limit_error_returns_false(self, tmp_path):
        """Line 640: _fetch_site_maps raises RuntimeError(E911_RATE_LIMIT) → False returned."""
        mock_apisession = MagicMock()  # mock apisession; not used directly
        org_data = {  # minimal org_data structure required by _process_site_batch
            "aps": {"aa:bb:cc:dd:ee:ff": {"site_id": "site-1"}},
            "sites": {"site-1": {"name": "SiteA"}},
            "wlan_templates": [],
            "org_wlans": [],
            "site_template_cache": {},
        }
        completed_sites: set = set()  # no sites completed yet
        batch = SiteBatchContext(  # WHY: bundle 7 per-batch fields into the new 4-arg signature
            org_id="org-1",
            org_data=org_data,
            total_sites=1,
            completed_sites=completed_sites,
            map_lookup={},
            wlan_band_lookup={},
            wlan_context={
                "wlan_templates": [],
                "org_wlans": [],
                "wlan_band_lookup": {},
                "site_template_cache": {},
            },
        )
        with patch.object(  # _fetch_site_maps raises E911_RATE_LIMIT on first site
            E911BSSIDReportGenerator,
            "_fetch_site_maps",
            side_effect=RuntimeError("E911_RATE_LIMIT"),
        ):
            with patch.object(  # _handle_rate_limit returns False and saves checkpoint
                E911BSSIDReportGenerator,
                "_handle_rate_limit",
                return_value=False,
            ) as mock_handle:
                result = E911BSSIDReportGenerator._process_site_batch(
                    apisession=mock_apisession,
                    page_limit=1000,
                    remaining=["site-1"],
                    batch=batch,
                )
        assert result is False  # line 640: returned from _handle_rate_limit call
        mock_handle.assert_called_once()  # _handle_rate_limit was invoked at line 640

    def test_non_rate_limit_runtime_error_reraises_line_640(self):
        """Line 640: RuntimeError without E911_RATE_LIMIT in message → raise re-raises."""
        import pytest  # imported inline for clarity in this test method

        mock_apisession = MagicMock()  # mock apisession; not used directly
        org_data = {  # minimal org_data structure required by _process_site_batch
            "aps": {"aa:bb:cc:dd:ee:ff": {"site_id": "site-1"}},
            "sites": {"site-1": {"name": "SiteA"}},
            "wlan_templates": [],
            "org_wlans": [],
            "site_template_cache": {},
        }
        completed_sites: set = set()  # no sites completed yet
        batch = SiteBatchContext(  # WHY: bundle 7 per-batch fields into the new 4-arg signature
            org_id="org-1",
            org_data=org_data,
            total_sites=1,
            completed_sites=completed_sites,
            map_lookup={},
            wlan_band_lookup={},
            wlan_context={
                "wlan_templates": [],
                "org_wlans": [],
                "wlan_band_lookup": {},
                "site_template_cache": {},
            },
        )
        with patch.object(  # _fetch_site_maps raises non-RATE-LIMIT RuntimeError
            E911BSSIDReportGenerator,
            "_fetch_site_maps",
            side_effect=RuntimeError("unexpected_api_error"),  # no E911_RATE_LIMIT in msg
        ):
            with pytest.raises(RuntimeError, match="unexpected_api_error"):  # expect re-raise
                E911BSSIDReportGenerator._process_site_batch(  # call; should re-raise
                    apisession=mock_apisession,
                    page_limit=1000,
                    remaining=["site-1"],
                    batch=batch,
                )
        # Line 640 (raise) was executed: RuntimeError re-raised and caught by pytest.raises
