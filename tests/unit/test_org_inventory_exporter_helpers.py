"""Focused unit tests for pure/near-pure static helpers on OrgInventoryExporter.

Purpose: lift coverage for src/export/org_inventory_exporter.py above the 42%
floor produced by the T-06 extraction. These tests target only helpers whose
behavior is fully specified by their inputs/outputs (or filesystem/log side
effects that fixtures like ``tmp_path``, ``capsys``, and ``caplog`` capture
directly), so no live API/session objects are required.

Issue: initiative 1015 T-06 (Cat E fresh extraction) coverage gate.
"""

from __future__ import annotations

import csv
import logging
import os
from collections import defaultdict

import pytest

import MistHelper
from src.export.org_inventory_exporter import OrgInventoryExporter

# ---------------------------------------------------------------------------
# _build_safe_org_name (pure)
# ---------------------------------------------------------------------------


def test_build_safe_org_name_preserves_allowed_chars() -> None:
    """Alphanumerics, dashes, and underscores must survive unchanged."""
    assert OrgInventoryExporter._build_safe_org_name("Acme-Corp_1") == "Acme-Corp_1"


def test_build_safe_org_name_replaces_forbidden_chars() -> None:
    """Any char outside [alnum-_] must become an underscore."""
    assert OrgInventoryExporter._build_safe_org_name("A / B: C.D") == "A___B__C_D"


# ---------------------------------------------------------------------------
# _split_full_address (pure with try/except fallback)
# ---------------------------------------------------------------------------


def test_split_full_address_valid_us_form() -> None:
    """Well-formed 'street, city, state zip, country' address splits into 5-tuple."""
    result = OrgInventoryExporter._split_full_address("123 Main St, Springfield, IL 62704, US")
    assert result == ("123 Main St", "Springfield", "IL", "62704", "US")


def test_split_full_address_falls_back_on_parse_error() -> None:
    """Malformed inputs must return (address, '', '', '', '') without raising."""
    result = OrgInventoryExporter._split_full_address("not-an-address")
    assert result == ("not-an-address", "", "", "", "")


# ---------------------------------------------------------------------------
# _build_master_csv_row / _build_combined_inventory_weekly_row (pure)
# ---------------------------------------------------------------------------


def test_build_master_csv_row_maps_all_expected_keys() -> None:
    device = {
        "serial": "SN1",
        "mac": "aabbccddeeff",
        "model": "AP41",
        "street": "1 Way",
        "city": "Town",
        "state": "CA",
        "zip_code": "94000",
    }
    row = OrgInventoryExporter._build_master_csv_row(device)
    assert row == {
        "serial": "SN1",
        "mac": "aabbccddeeff",
        "model": "AP41",
        "Street Address": "1 Way",
        "City": "Town",
        "State": "CA",
        "Zip": "94000",
    }


def test_build_master_csv_row_defaults_missing_keys_to_empty_string() -> None:
    row = OrgInventoryExporter._build_master_csv_row({})
    assert row == {
        "serial": "",
        "mac": "",
        "model": "",
        "Street Address": "",
        "City": "",
        "State": "",
        "Zip": "",
    }


def test_build_combined_inventory_weekly_row_defaults_country_to_us() -> None:
    """When device dict omits 'country', helper must default it to 'US'."""
    device = {
        "site_name": "S1",
        "serial": "SN1",
        "mac": "aabb",
        "model": "AP41",
        "street": "1 Way",
        "city": "Town",
        "state": "CA",
        "zip_code": "94000",
    }
    row = OrgInventoryExporter._build_combined_inventory_weekly_row(device, "Acme", "acct-1")
    assert row["End Customer Name"] == "Acme"
    assert row["End Customer Account ID"] == "acct-1"
    assert row["Country"] == "US"
    assert row["Address Line 2"] == ""
    assert row["Full Site"] == "S1"


def test_build_combined_inventory_weekly_row_uses_explicit_country() -> None:
    device = {"country": "GB"}
    row = OrgInventoryExporter._build_combined_inventory_weekly_row(device, None, None)
    assert row["Country"] == "GB"
    assert row["End Customer Name"] is None
    assert row["End Customer Account ID"] is None


# ---------------------------------------------------------------------------
# _split_physical_vs_virtual_inventory / _classify_empty_vc_shells /
# _partition_combined_inventory_rows (pure)
# ---------------------------------------------------------------------------


def _sample_devices() -> list[dict[str, str]]:
    return [
        {"mac": "aabbccddee01", "vc_mac": ""},  # Physical, standalone
        {"mac": "aabbccddee02", "vc_mac": "020003aabbcc"},  # Physical member of empty-shell VC
        {"mac": "aabbccddee03", "vc_mac": "aabbccddee01"},  # Physical member of a physical VC parent
        {"mac": "020003aabbcc", "vc_mac": ""},  # Virtual VC placeholder w/ no physical members = shell
        {"mac": "020003ffffff", "vc_mac": ""},  # Virtual VC placeholder duplicate (no member points to it)
    ]


def test_split_physical_vs_virtual_inventory_filters_020003_prefix() -> None:
    physical, virtual = OrgInventoryExporter._split_physical_vs_virtual_inventory(_sample_devices())
    assert len(physical) == 3
    assert all(not d["mac"].startswith("020003") for d in physical)
    assert len(virtual) == 2
    assert all(d["mac"].startswith("020003") for d in virtual)


def test_classify_empty_vc_shells_identifies_shells_and_duplicates() -> None:
    physical, virtual = OrgInventoryExporter._split_physical_vs_virtual_inventory(_sample_devices())
    empty_shells, duplicates = OrgInventoryExporter._classify_empty_vc_shells(virtual, physical)
    # Only the 020003aabbcc virtual entry has a physical member pointing at it via vc_mac.
    # The 020003ffffff entry has no physical member -> empty shell.
    shell_macs = {s["mac"] for s in empty_shells}
    assert shell_macs == {"020003ffffff"}
    assert duplicates == 1


def test_partition_combined_inventory_rows_composes_split_and_classify() -> None:
    physical, empty_shells, duplicates = OrgInventoryExporter._partition_combined_inventory_rows(_sample_devices())
    assert len(physical) == 3
    assert len(empty_shells) == 1
    assert duplicates == 1


# ---------------------------------------------------------------------------
# _emit_vc_shell_dashboard_diff / _log_combined_inventory_vc_summary
# (print + log side effects)
# ---------------------------------------------------------------------------


def test_emit_vc_shell_dashboard_diff_prints_three_lines(capsys: pytest.CaptureFixture[str]) -> None:
    physical = [{"mac": "aabbccddee01"}]
    shells = [{"mac": "020003ffffff"}]
    OrgInventoryExporter._emit_vc_shell_dashboard_diff(physical, shells)
    captured = capsys.readouterr().out
    assert "1 provisioned VC shells" in captured
    assert "Dashboard shows 2" in captured
    assert "Report correctly includes only 1" in captured


def test_log_combined_inventory_vc_summary_without_shells_stays_silent(
    caplog: pytest.LogCaptureFixture,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """No empty shells -> no dashboard-parity print."""
    with caplog.at_level(logging.INFO):
        OrgInventoryExporter._log_combined_inventory_vc_summary(
            all_devices=[{"mac": "aabb"}],
            site_configs=[{"mac": "aabb"}],
            empty_vc_shells=[],
            duplicate_vc_entries=0,
        )
    assert "Loaded 1 total devices" in caplog.text
    assert capsys.readouterr().out == ""


def test_log_combined_inventory_vc_summary_with_shells_emits_dashboard_note(
    caplog: pytest.LogCaptureFixture,
    capsys: pytest.CaptureFixture[str],
) -> None:
    with caplog.at_level(logging.INFO):
        OrgInventoryExporter._log_combined_inventory_vc_summary(
            all_devices=[{"mac": "aabb"}, {"mac": "020003ffffff"}],
            site_configs=[{"mac": "aabb"}],
            empty_vc_shells=[{"mac": "020003ffffff"}],
            duplicate_vc_entries=0,
        )
    assert "Virtual VC breakdown" in caplog.text
    assert "provisioned VC shells" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# _bucket_device_into_week / _build_combined_inventory_weekly_data
# (near-pure with defaultdict mutation)
# ---------------------------------------------------------------------------


def test_bucket_device_into_week_valid_row_populates_both_buckets() -> None:
    """A valid created_time must land in both weekly and summary buckets."""
    weekly: defaultdict = defaultdict(list)
    summary: defaultdict = defaultdict(int)
    # 2024-01-03 UTC is Wed ISO week 1 of 2024.
    device = {"created_time": "1704240000", "mac": "aabb", "serial": "SN1"}
    OrgInventoryExporter._bucket_device_into_week(device, weekly, summary, "Acme", "acct-1")
    assert len(weekly) == 1
    week_key = next(iter(weekly))
    assert week_key.startswith("2024_Week_")
    assert len(weekly[week_key]) == 1
    assert weekly[week_key][0]["End Customer Name"] == "Acme"
    assert sum(summary.values()) == 1


def test_bucket_device_into_week_bad_row_logs_warning_and_skips(caplog: pytest.LogCaptureFixture) -> None:
    weekly: defaultdict = defaultdict(list)
    summary: defaultdict = defaultdict(int)
    with caplog.at_level(logging.WARNING):
        OrgInventoryExporter._bucket_device_into_week({"created_time": "not-a-number"}, weekly, summary, None, None)
    assert weekly == {}
    assert summary == {}
    assert "Skipping device due to error" in caplog.text


def test_build_combined_inventory_weekly_data_aggregates_multiple_devices() -> None:
    devices = [
        {"created_time": "1704240000", "mac": "a1"},  # 2024 W1
        {"created_time": "1704240000", "mac": "a2"},  # Same week
        {"created_time": "1735689600", "mac": "b1"},  # 2025 W1
    ]
    weekly, summary = OrgInventoryExporter._build_combined_inventory_weekly_data(devices, "Acme", "acct-1")
    # Two ISO weeks distributed across two calendar years -> two buckets
    assert len(weekly) == 2
    assert sum(summary.values()) == 3


# ---------------------------------------------------------------------------
# CSV writers (tmp_path filesystem IO)
# ---------------------------------------------------------------------------


def test_write_combined_inventory_weekly_csvs_writes_one_file_per_bucket(tmp_path) -> None:
    weekly: defaultdict = defaultdict(list)
    weekly["2024_Week_01"].append(
        {
            "Full Site": "S",
            "System Serial Number": "SN1",
            "System MAC Address": "aabb",
            "System Model Number": "AP41",
            "End Customer Name": "Acme",
            "Address Line 1": "1 Way",
            "Address Line 2": "",
            "City": "Town",
            "State": "CA",
            "Country": "US",
            "Zip Code / Postal Code": "94000",
            "End Customer Account ID": "acct-1",
        }
    )
    fieldnames = OrgInventoryExporter._COMBINED_INVENTORY_FIELDNAMES
    OrgInventoryExporter._write_combined_inventory_weekly_csvs(str(tmp_path), fieldnames, weekly)
    written = tmp_path / "2024_Week_01.csv"
    assert written.exists()
    rows = list(csv.DictReader(written.open()))
    assert len(rows) == 1
    assert rows[0]["System Serial Number"] == "SN1"


def test_write_combined_inventory_summary_sorts_year_week(tmp_path) -> None:
    summary: defaultdict = defaultdict(int)
    summary[(2024, 2)] = 5
    summary[(2024, 1)] = 3
    summary[(2023, 52)] = 2
    OrgInventoryExporter._write_combined_inventory_summary(str(tmp_path), summary)
    summary_path = tmp_path / "CombinedInventory_Summary.csv"
    with summary_path.open() as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)
    assert header == ["Year", "Week", "Device Count"]
    assert rows == [["2023", "52", "2"], ["2024", "1", "3"], ["2024", "2", "5"]]


def test_persist_master_csv_writes_dict_rows(tmp_path) -> None:
    target = tmp_path / "master.csv"
    fieldnames = ["a", "b"]
    rows = [{"a": "1", "b": "2"}, {"a": "3", "b": "4"}]
    OrgInventoryExporter._persist_master_csv(str(target), fieldnames, rows)
    assert list(csv.DictReader(target.open())) == rows


def test_write_combined_inventory_master_csv_builds_filename_and_returns_row_count(tmp_path) -> None:
    site_configs = [
        {
            "serial": "S1",
            "mac": "aabb",
            "model": "AP41",
            "street": "1 Way",
            "city": "T",
            "state": "CA",
            "zip_code": "94000",
        },
        {
            "serial": "S2",
            "mac": "ccdd",
            "model": "SW",
            "street": "2 Way",
            "city": "U",
            "state": "NY",
            "zip_code": "10001",
        },
    ]
    filename, count = OrgInventoryExporter._write_combined_inventory_master_csv(str(tmp_path), "AcmeCorp", site_configs)
    assert filename == "AcmeCorp_CombinedInventory_Master.csv"
    assert count == 2
    written = tmp_path / filename
    rows = list(csv.DictReader(written.open()))
    assert rows[0]["serial"] == "S1"
    assert rows[1]["Zip"] == "10001"


# ---------------------------------------------------------------------------
# _print_combined_inventory_summary
# ---------------------------------------------------------------------------


def test_print_combined_inventory_summary_names_three_outputs(capsys: pytest.CaptureFixture[str]) -> None:
    weekly: defaultdict = defaultdict(list)
    weekly["2024_Week_01"] = [{}]
    weekly["2024_Week_02"] = [{}, {}]
    site_configs = [{}] * 3
    OrgInventoryExporter._print_combined_inventory_summary(weekly, site_configs, "acme.csv", 3)
    out = capsys.readouterr().out
    assert "2 weekly CSV files" in out
    assert "3 total devices processed" in out
    assert "CombinedInventory_Summary.csv" in out
    assert "acme.csv" in out
    assert "3 devices" in out


# ---------------------------------------------------------------------------
# _build_mac_to_site_id / _enrich_one_device (VC inheritance)
# ---------------------------------------------------------------------------


def test_build_mac_to_site_id_indexes_only_devices_with_site() -> None:
    inventory = [
        {"mac": "a1", "site_id": "S1"},
        {"mac": "a2", "site_id": ""},  # No site_id -> excluded
        {"mac": "", "site_id": "S3"},  # No mac -> excluded
        {"mac": "a4", "site_id": "S4"},
    ]
    result = OrgInventoryExporter._build_mac_to_site_id(inventory)
    assert result == {"a1": "S1", "a4": "S4"}


def test_enrich_one_device_uses_own_site_when_present() -> None:
    site_lookup = {"S1": {"name": "Site One", "address": "1 A, T, CA 94000, US"}}
    device = {"site_id": "S1"}
    inherited = OrgInventoryExporter._enrich_one_device(device, site_lookup, {})
    assert inherited is False
    assert device["site_name"] == "Site One"
    assert device["street"] == "1 A"
    assert device["country"] == "US"


def test_enrich_one_device_inherits_from_vc_mac_when_site_missing() -> None:
    site_lookup = {"S9": {"name": "VC Parent Site", "address": "9 W, C, TX 75000, US"}}
    mac_to_site_id = {"vc-parent-mac": "S9"}
    device = {"vc_mac": "vc-parent-mac"}
    inherited = OrgInventoryExporter._enrich_one_device(device, site_lookup, mac_to_site_id)
    assert inherited is True
    assert device["site_id"] == "S9"
    assert device["site_name"] == "VC Parent Site"
    assert device["state"] == "TX"


def test_enrich_one_device_falls_back_to_unknown_when_no_site() -> None:
    device: dict = {}
    inherited = OrgInventoryExporter._enrich_one_device(device, {}, {})
    assert inherited is False
    assert device["site_name"] == "Unknown"
    assert device["site_address"] == "Unknown"


# ---------------------------------------------------------------------------
# _enrich_gateways_with_site_info (filter + tqdm loop)
# ---------------------------------------------------------------------------


def test_enrich_gateways_with_site_info_filters_non_gateways() -> None:
    site_lookup = {"S1": {"name": "Site", "address": "1 W, T, CA 94000, US"}}
    inventory = [
        {"type": "ap", "site_id": "S1"},
        {"type": "gateway", "site_id": "S1", "mac": "gw1"},
        {"type": "switch", "site_id": "S1"},
    ]
    result = OrgInventoryExporter._enrich_gateways_with_site_info(inventory, site_lookup)
    assert len(result) == 1
    assert result[0]["mac"] == "gw1"
    assert result[0]["site_name"] == "Site"
    assert result[0]["state"] == "CA"


# ---------------------------------------------------------------------------
# _display_devices_summary_table / _display_gateways_summary_table
# ---------------------------------------------------------------------------


def test_display_devices_summary_table_emits_debug_log(caplog: pytest.LogCaptureFixture) -> None:
    devices = [{"name": "d1", "mac": "aabb", "model": "AP41", "site_name": "S", "city": "T"}]
    with caplog.at_level(logging.DEBUG):
        OrgInventoryExporter._display_devices_summary_table(devices)
    assert "d1" in caplog.text
    assert "aabb" in caplog.text


def test_display_gateways_summary_table_emits_debug_log(caplog: pytest.LogCaptureFixture) -> None:
    gateways = [{"name": "g1", "mac": "ccdd", "model": "SRX", "site_name": "S", "state": "CA"}]
    with caplog.at_level(logging.DEBUG):
        OrgInventoryExporter._display_gateways_summary_table(gateways)
    assert "g1" in caplog.text
    assert "SRX" in caplog.text


# ---------------------------------------------------------------------------
# _flatten_sort_export_devices / _flatten_sort_export_gateways
# (need DataExporter mock via monkeypatch on MistHelper module)
# ---------------------------------------------------------------------------


class _RecordingDataExporter:
    """Stand-in for MistHelper.DataExporter capturing write calls."""

    calls: list[tuple[list, str]] = []

    @classmethod
    def write_with_format_selection(cls, rows, filename) -> None:  # type: ignore[no-untyped-def]
        cls.calls.append((list(rows), filename))


def test_flatten_sort_export_devices_sorts_by_site_and_writes_csv(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _RecordingDataExporter.calls = []
    monkeypatch.setattr(MistHelper, "DataExporter", _RecordingDataExporter)
    devices = [
        {"name": "d2", "site_name": "Zeta"},
        {"name": "d1", "site_name": "Alpha"},
    ]
    result = OrgInventoryExporter._flatten_sort_export_devices(devices)
    assert [d["site_name"] for d in result] == ["Alpha", "Zeta"]
    assert _RecordingDataExporter.calls[-1][1] == "AllDevicesWithSiteInfo.csv"
    assert "2 devices exported" in capsys.readouterr().out


def test_flatten_sort_export_gateways_sorts_by_site_and_writes_csv(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _RecordingDataExporter.calls = []
    monkeypatch.setattr(MistHelper, "DataExporter", _RecordingDataExporter)
    gateways = [
        {"name": "g2", "site_name": "Zeta"},
        {"name": "g1", "site_name": "Alpha"},
    ]
    result = OrgInventoryExporter._flatten_sort_export_gateways(gateways)
    assert [g["site_name"] for g in result] == ["Alpha", "Zeta"]
    assert _RecordingDataExporter.calls[-1][1] == "GatewaysWithSiteInfo.csv"
    assert "2 gateways exported" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# _load_combined_inventory_rows (filesystem read via FilePathUtils)
# ---------------------------------------------------------------------------


def test_load_combined_inventory_rows_reads_all_devices_with_site_info_csv(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Redirect FilePathUtils to a tmp CSV and confirm rows are materialized."""
    from src.utils import file_path_utils

    csv_path = tmp_path / "AllDevicesWithSiteInfo.csv"
    csv_path.write_text("mac,site_name\naabb,Site1\nccdd,Site2\n", encoding="utf-8")

    def _fake_get_csv_path(filename: str) -> str:
        return str(tmp_path / filename)

    monkeypatch.setattr(file_path_utils.FilePathUtils, "get_csv_path", staticmethod(_fake_get_csv_path))
    # The exporter imports FilePathUtils at module load; patch that reference too.
    from src.export import org_inventory_exporter

    monkeypatch.setattr(org_inventory_exporter.FilePathUtils, "get_csv_path", staticmethod(_fake_get_csv_path))

    rows = OrgInventoryExporter._load_combined_inventory_rows()
    assert [r["site_name"] for r in rows] == ["Site1", "Site2"]


# ---------------------------------------------------------------------------
# _load_site_lookup_from_cache / _load_inventory_from_cache (cache success path)
# ---------------------------------------------------------------------------


def test_load_site_lookup_from_cache_reads_site_list_csv(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    csv_path = tmp_path / "SiteList.csv"
    csv_path.write_text("id,name,address\nS1,Site1,Addr1\nS2,Site2,Addr2\n", encoding="utf-8")
    from src.export import org_inventory_exporter

    monkeypatch.setattr(
        org_inventory_exporter.FilePathUtils, "get_csv_path", staticmethod(lambda fn: str(tmp_path / fn))
    )
    lookup = OrgInventoryExporter._load_site_lookup_from_cache("org-1")
    assert lookup == {
        "S1": {"name": "Site1", "address": "Addr1"},
        "S2": {"name": "Site2", "address": "Addr2"},
    }


def test_load_inventory_from_cache_reads_org_inventory_csv(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    csv_path = tmp_path / "OrgInventory.csv"
    csv_path.write_text("mac,model\naabb,AP41\nccdd,SW\n", encoding="utf-8")
    from src.export import org_inventory_exporter

    monkeypatch.setattr(
        org_inventory_exporter.FilePathUtils, "get_csv_path", staticmethod(lambda fn: str(tmp_path / fn))
    )
    inventory = OrgInventoryExporter._load_inventory_from_cache("org-1")
    assert [d["model"] for d in inventory] == ["AP41", "SW"]


# ---------------------------------------------------------------------------
# _enrich_devices_with_site_info (integration of _enrich_one_device + tqdm)
# ---------------------------------------------------------------------------


def test_enrich_devices_with_site_info_logs_vc_inheritance_count(caplog: pytest.LogCaptureFixture) -> None:
    site_lookup = {"S1": {"name": "Site One", "address": "1 A, T, CA 94000, US"}}
    inventory = [
        {"mac": "own-site", "site_id": "S1"},  # Owns its site.
        {"mac": "vc-member", "vc_mac": "vc-parent-mac"},  # Will inherit.
    ]
    mac_to_site_id = {"vc-parent-mac": "S1"}
    with caplog.at_level(logging.INFO):
        result = OrgInventoryExporter._enrich_devices_with_site_info(inventory, site_lookup, mac_to_site_id)
    assert len(result) == 2
    assert any("1 physical VC members inherited" in rec.message for rec in caplog.records)


# ---------------------------------------------------------------------------
# _prepare_combined_inventory_context (env + ConfigUtils)
# ---------------------------------------------------------------------------


def test_prepare_combined_inventory_context_returns_expected_tuple(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.export import org_inventory_exporter

    monkeypatch.setenv("END_CUSTOMER_NAME", "Acme")
    monkeypatch.setenv("END_CUSTOMER_ACCOUNT_ID", "acct-1")
    monkeypatch.setattr(
        org_inventory_exporter.ConfigUtils,
        "get_cached_or_prompted_org_id",
        staticmethod(lambda: "org-uuid"),
    )
    # Force the API-resolve branch to fail so it falls back to end_customer_name.
    monkeypatch.setattr(
        org_inventory_exporter,
        "mistapi",
        type("FakeMistapi", (), {"api": None})(),
        raising=False,
    )

    def _boom(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise RuntimeError("no api in test")

    # Patch the resolve helper directly so we don't have to stub the whole mistapi chain.
    monkeypatch.setattr(
        org_inventory_exporter.OrgInventoryExporter,
        "_resolve_combined_inventory_org_name",
        staticmethod(lambda org_id, fallback: fallback or "UnknownOrg"),
    )

    ctx = OrgInventoryExporter._prepare_combined_inventory_context()
    org_id, name, acct, safe, folder = ctx
    assert org_id == "org-uuid"
    assert name == "Acme"
    assert acct == "acct-1"
    assert safe == "Acme"  # Already safe.
    assert folder == os.path.join("data", "CombinedInventory_ByWeek")


# ---------------------------------------------------------------------------
# _emit_combined_inventory_outputs (composes weekly + summary + master writers)
# ---------------------------------------------------------------------------


def test_emit_combined_inventory_outputs_writes_all_three_artifacts(tmp_path) -> None:
    weekly: defaultdict = defaultdict(list)
    weekly["2024_Week_01"].append({k: "" for k in OrgInventoryExporter._COMBINED_INVENTORY_FIELDNAMES})
    summary: defaultdict = defaultdict(int)
    summary[(2024, 1)] = 1
    site_configs = [{"serial": "S1", "mac": "aabb", "model": "AP41"}]
    filename, count = OrgInventoryExporter._emit_combined_inventory_outputs(
        str(tmp_path), "Acme", site_configs, weekly, summary
    )
    assert filename == "Acme_CombinedInventory_Master.csv"
    assert count == 1
    assert (tmp_path / "2024_Week_01.csv").exists()
    assert (tmp_path / "CombinedInventory_Summary.csv").exists()
    assert (tmp_path / filename).exists()


# ---------------------------------------------------------------------------
# inventory() / devices() — public menu entrypoints (12, 17)
# ---------------------------------------------------------------------------


class _RecordingFetcher:
    """Test double for MistHelper.APIDataFetcher that records init args + execute()."""

    calls: list[dict] = []

    def __init__(self, **kwargs) -> None:
        _RecordingFetcher.calls.append(kwargs)

    def execute(self) -> None:
        _RecordingFetcher.calls[-1]["_executed"] = True


class _RecordingEmitter:
    """Test double for MistHelper.PROGRESS_EMITTER capturing start/complete calls."""

    def __init__(self) -> None:
        self.starts: list[tuple] = []
        self.completes: list[tuple] = []

    def emit_progress_start(self, menu, name, total) -> None:  # type: ignore[no-untyped-def]
        self.starts.append((menu, name, total))

    def emit_progress_complete(self, ctx, done, cancelled, elapsed) -> None:  # type: ignore[no-untyped-def]
        self.completes.append((ctx, done, cancelled, elapsed))


def _install_fetcher_and_emitter(monkeypatch) -> _RecordingEmitter:
    _RecordingFetcher.calls = []
    emitter = _RecordingEmitter()
    monkeypatch.setattr(MistHelper, "APIDataFetcher", _RecordingFetcher, raising=True)
    monkeypatch.setattr(MistHelper, "PROGRESS_EMITTER", emitter, raising=True)
    return emitter


def test_inventory_menu12_dispatches_via_apidatafetcher(monkeypatch) -> None:
    emitter = _install_fetcher_and_emitter(monkeypatch)
    OrgInventoryExporter.inventory()
    assert len(_RecordingFetcher.calls) == 1
    call = _RecordingFetcher.calls[0]
    assert call["filename"] == "OrgInventory.csv"
    assert call["sort_key"] == "model"
    assert call["vc"] is True
    assert call["limit"] == 1000
    assert call["_executed"] is True
    assert emitter.starts == [("12", "inventory", 1)]
    assert len(emitter.completes) == 1


def test_inventory_menu12_skips_emitter_when_absent(monkeypatch) -> None:
    _RecordingFetcher.calls = []
    monkeypatch.setattr(MistHelper, "APIDataFetcher", _RecordingFetcher, raising=True)
    monkeypatch.setattr(MistHelper, "PROGRESS_EMITTER", None, raising=True)
    OrgInventoryExporter.inventory()
    assert _RecordingFetcher.calls[0]["_executed"] is True


def test_devices_menu17_dispatches_via_apidatafetcher(monkeypatch) -> None:
    emitter = _install_fetcher_and_emitter(monkeypatch)
    OrgInventoryExporter.devices()
    call = _RecordingFetcher.calls[0]
    assert call["filename"] == "OrgDevices.csv"
    assert call["sort_key"] == "type"
    assert "vc" not in call  # devices() does not pass vc
    assert call["_executed"] is True
    assert emitter.starts == [("17", "devices", 1)]


def test_devices_menu17_skips_emitter_when_absent(monkeypatch) -> None:
    _RecordingFetcher.calls = []
    monkeypatch.setattr(MistHelper, "APIDataFetcher", _RecordingFetcher, raising=True)
    monkeypatch.setattr(MistHelper, "PROGRESS_EMITTER", None, raising=True)
    OrgInventoryExporter.devices()
    assert _RecordingFetcher.calls[0]["_executed"] is True


# ---------------------------------------------------------------------------
# _build_site_lookup_from_api + cached-CSV fallback paths
# ---------------------------------------------------------------------------


def test_build_site_lookup_from_api(monkeypatch) -> None:
    from src.export import org_inventory_exporter as mod

    monkeypatch.setattr(
        mod.APICoreFetchUtils,
        "all_sites_with_limit",
        lambda org_id: [
            {"id": "s1", "name": "HQ", "address": "1 Main"},
            {"id": "s2", "name": "Branch", "address": "2 Elm"},
        ],
    )
    lookup = OrgInventoryExporter._build_site_lookup_from_api("org-1")
    assert lookup == {
        "s1": {"name": "HQ", "address": "1 Main"},
        "s2": {"name": "Branch", "address": "2 Elm"},
    }


def test_load_site_lookup_from_cache_falls_back_on_read_error(monkeypatch) -> None:
    from src.export import org_inventory_exporter as mod

    monkeypatch.setattr(mod.FilePathUtils, "get_csv_path", lambda name: "/nonexistent/does_not_exist.csv")
    monkeypatch.setattr(
        mod.APICoreFetchUtils,
        "all_sites_with_limit",
        lambda org_id: [{"id": "s9", "name": "Fallback", "address": "x"}],
    )
    lookup = OrgInventoryExporter._load_site_lookup_from_cache("org-1")
    assert lookup == {"s9": {"name": "Fallback", "address": "x"}}


def test_load_site_lookup_from_cache_reads_csv(monkeypatch, tmp_path) -> None:
    from src.export import org_inventory_exporter as mod

    csv_path = tmp_path / "SiteList.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "name", "address"])
        w.writeheader()
        w.writerow({"id": "s1", "name": "HQ", "address": "1 Main"})
    monkeypatch.setattr(mod.FilePathUtils, "get_csv_path", lambda name: str(csv_path))
    lookup = OrgInventoryExporter._load_site_lookup_from_cache("org-1")
    assert lookup == {"s1": {"name": "HQ", "address": "1 Main"}}


def test_load_inventory_from_cache_falls_back_on_read_error(monkeypatch) -> None:
    from src.export import org_inventory_exporter as mod

    monkeypatch.setattr(mod.FilePathUtils, "get_csv_path", lambda name: "/nonexistent/does_not_exist.csv")
    monkeypatch.setattr(
        mod.APICoreFetchUtils,
        "all_inventory_with_limit",
        lambda org_id: [{"mac": "aa", "serial": "S1"}],
    )
    inv = OrgInventoryExporter._load_inventory_from_cache("org-1")
    assert inv == [{"mac": "aa", "serial": "S1"}]


def test_load_inventory_from_cache_reads_csv(monkeypatch, tmp_path) -> None:
    from src.export import org_inventory_exporter as mod

    csv_path = tmp_path / "OrgInventory.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["mac", "serial"])
        w.writeheader()
        w.writerow({"mac": "aa", "serial": "S1"})
    monkeypatch.setattr(mod.FilePathUtils, "get_csv_path", lambda name: str(csv_path))
    inv = OrgInventoryExporter._load_inventory_from_cache("org-1")
    assert inv == [{"mac": "aa", "serial": "S1"}]


def test_devices_load_data_non_fast_calls_api(monkeypatch) -> None:
    from src.export import org_inventory_exporter as mod

    monkeypatch.setattr(
        mod.APICoreFetchUtils,
        "all_sites_with_limit",
        lambda org_id: [{"id": "s1", "name": "HQ", "address": "a"}],
    )
    monkeypatch.setattr(
        mod.APICoreFetchUtils,
        "all_inventory_with_limit",
        lambda org_id: [{"mac": "aa", "site_id": "s1"}],
    )
    site_lookup, inventory = OrgInventoryExporter._devices_load_data("org-1", fast=False)
    assert site_lookup == {"s1": {"name": "HQ", "address": "a"}}
    assert inventory == [{"mac": "aa", "site_id": "s1"}]


def test_devices_load_data_fast_uses_cache(monkeypatch, tmp_path) -> None:
    from src.export import org_inventory_exporter as mod

    site_csv = tmp_path / "SiteList.csv"
    inv_csv = tmp_path / "OrgInventory.csv"
    with open(site_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "name", "address"])
        w.writeheader()
        w.writerow({"id": "s1", "name": "HQ", "address": "a"})
    with open(inv_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["mac", "serial"])
        w.writeheader()
        w.writerow({"mac": "aa", "serial": "S1"})

    def _fake_get_csv_path(name):
        if name == "SiteList.csv":
            return str(site_csv)
        return str(inv_csv)

    monkeypatch.setattr(mod.FilePathUtils, "get_csv_path", _fake_get_csv_path)
    monkeypatch.setattr(mod.CacheUtils, "check_and_generate_csv", lambda name, gen: None)
    site_lookup, inventory = OrgInventoryExporter._devices_load_data("org-1", fast=True)
    assert site_lookup == {"s1": {"name": "HQ", "address": "a"}}
    assert inventory == [{"mac": "aa", "serial": "S1"}]


# ---------------------------------------------------------------------------
# _resolve_combined_inventory_org_name — API-first, then fallbacks
# ---------------------------------------------------------------------------


class _StubOrgResponse:
    def __init__(self, name: str | None) -> None:
        self.data = {"name": name} if name is not None else {}


def test_resolve_combined_inventory_org_name_uses_api_name(monkeypatch) -> None:
    from src.export import org_inventory_exporter as mod

    monkeypatch.setattr(MistHelper, "apisession", object(), raising=False)
    monkeypatch.setattr(
        mod.mistapi.api.v1.orgs.orgs,
        "getOrg",
        lambda session, org_id: _StubOrgResponse("Real Org"),
    )
    name = OrgInventoryExporter._resolve_combined_inventory_org_name("org-1", "fallback")
    assert name == "Real Org"


def test_resolve_combined_inventory_org_name_falls_back_to_env(monkeypatch) -> None:
    from src.export import org_inventory_exporter as mod

    monkeypatch.setattr(MistHelper, "apisession", object(), raising=False)
    monkeypatch.setattr(
        mod.mistapi.api.v1.orgs.orgs,
        "getOrg",
        lambda session, org_id: _StubOrgResponse(None),
    )
    name = OrgInventoryExporter._resolve_combined_inventory_org_name("org-1", "EnvCustomer")
    assert name == "EnvCustomer"


def test_resolve_combined_inventory_org_name_final_fallback(monkeypatch) -> None:
    from src.export import org_inventory_exporter as mod

    monkeypatch.setattr(MistHelper, "apisession", object(), raising=False)
    monkeypatch.setattr(
        mod.mistapi.api.v1.orgs.orgs,
        "getOrg",
        lambda session, org_id: (_ for _ in ()).throw(RuntimeError("api down")),
    )
    name = OrgInventoryExporter._resolve_combined_inventory_org_name("org-1", None)
    assert name == "org-1"


def test_resolve_combined_inventory_org_name_unknown_org_sentinel(monkeypatch) -> None:
    from src.export import org_inventory_exporter as mod

    monkeypatch.setattr(MistHelper, "apisession", object(), raising=False)
    monkeypatch.setattr(
        mod.mistapi.api.v1.orgs.orgs,
        "getOrg",
        lambda session, org_id: (_ for _ in ()).throw(RuntimeError("api down")),
    )
    name = OrgInventoryExporter._resolve_combined_inventory_org_name(None, None)
    assert name == "UnknownOrg"


# ---------------------------------------------------------------------------
# devices_with_site_info / gateways_with_site_info — orchestrators
# ---------------------------------------------------------------------------


def test_devices_with_site_info_orchestrator(monkeypatch, tmp_path) -> None:
    """Cover the devices_with_site_info orchestrator path (fast=False)."""
    from src.export import org_inventory_exporter as mod

    monkeypatch.setattr(mod.ConfigUtils, "get_cached_or_prompted_org_id", lambda: "org-1")
    monkeypatch.setattr(
        mod.APICoreFetchUtils,
        "all_sites_with_limit",
        lambda org_id: [{"id": "s1", "name": "HQ", "address": "1 Main"}],
    )
    monkeypatch.setattr(
        mod.APICoreFetchUtils,
        "all_inventory_with_limit",
        lambda org_id: [
            {"mac": "aa", "site_id": "s1", "type": "ap", "model": "AP32"},
        ],
    )
    # DataExporter lives on MistHelper (T-08 pending); stub write
    monkeypatch.setattr(
        MistHelper.DataExporter,
        "export_to_csv",
        staticmethod(lambda data, filename: None),
        raising=False,
    )
    OrgInventoryExporter.devices_with_site_info(fast=False)


def test_gateways_with_site_info_orchestrator(monkeypatch) -> None:
    """Cover the gateways_with_site_info orchestrator path."""
    from src.export import org_inventory_exporter as mod

    monkeypatch.setattr(mod.ConfigUtils, "get_cached_or_prompted_org_id", lambda: "org-1")
    monkeypatch.setattr(
        mod.APICoreFetchUtils,
        "all_sites_with_limit",
        lambda org_id: [{"id": "s1", "name": "HQ", "address": "1 Main"}],
    )
    monkeypatch.setattr(
        mod.APICoreFetchUtils,
        "all_inventory_with_limit",
        lambda org_id: [
            {"mac": "aa", "site_id": "s1", "type": "gateway", "model": "SRX", "hostname": "gw1"},
        ],
    )
    monkeypatch.setattr(
        MistHelper.DataExporter,
        "export_to_csv",
        staticmethod(lambda data, filename: None),
        raising=False,
    )
    OrgInventoryExporter.gateways_with_site_info()


# ---------------------------------------------------------------------------
# _fetch_and_persist_raw_inventory_variant / _export_combined_inventory_raw_json
# ---------------------------------------------------------------------------


class _StubResponse:
    def __init__(self, data) -> None:
        self.data = data


def test_fetch_and_persist_raw_inventory_variant(monkeypatch, tmp_path) -> None:
    from src.export import org_inventory_exporter as mod

    monkeypatch.setattr(MistHelper, "apisession", object(), raising=False)
    monkeypatch.setattr(
        mod.mistapi.api.v1.orgs.inventory,
        "getOrgInventory",
        lambda session, org_id, **kwargs: _StubResponse([{"mac": "aa"}, {"mac": "bb"}]),
    )
    monkeypatch.setattr(
        mod.mistapi,
        "get_all",
        lambda response, mist_session: response.data,
    )
    count = OrgInventoryExporter._fetch_and_persist_raw_inventory_variant(
        "test_variant.json", {"vc": True}, "org-1", str(tmp_path)
    )
    assert count == 2
    assert (tmp_path / "test_variant.json").exists()


def test_export_combined_inventory_raw_json(monkeypatch, tmp_path) -> None:
    from src.export import org_inventory_exporter as mod

    monkeypatch.setattr(MistHelper, "apisession", object(), raising=False)
    monkeypatch.setattr(MistHelper, "DEFAULT_API_PAGE_LIMIT", 1000, raising=False)
    monkeypatch.setattr(
        mod.mistapi.api.v1.orgs.inventory,
        "getOrgInventory",
        lambda session, org_id, **kwargs: _StubResponse([{"mac": "aa"}]),
    )
    monkeypatch.setattr(
        mod.mistapi,
        "get_all",
        lambda response, mist_session: response.data,
    )
    OrgInventoryExporter._export_combined_inventory_raw_json(str(tmp_path), "org-1")
    # All three variants written
    assert (tmp_path / "raw_inventory_vc_true.json").exists()
    assert (tmp_path / "raw_inventory_vc_false.json").exists()
    assert (tmp_path / "raw_inventory_no_vc_param.json").exists()


def test_export_combined_inventory_raw_json_swallows_errors(monkeypatch, tmp_path, caplog) -> None:
    """Diagnostic export must be non-fatal: exceptions are logged as warnings, not raised."""
    from src.export import org_inventory_exporter as mod

    monkeypatch.setattr(MistHelper, "apisession", object(), raising=False)
    monkeypatch.setattr(MistHelper, "DEFAULT_API_PAGE_LIMIT", 1000, raising=False)
    monkeypatch.setattr(
        mod.mistapi.api.v1.orgs.inventory,
        "getOrgInventory",
        lambda session, org_id, **kwargs: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    with caplog.at_level(logging.WARNING):
        OrgInventoryExporter._export_combined_inventory_raw_json(str(tmp_path), "org-1")
    assert any("Failed to save raw inventory JSON" in rec.message for rec in caplog.records)
