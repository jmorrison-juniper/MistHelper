"""Unit tests for SFPTransceiverDataProcessor (issue #878 tranche 5 -- un-omit).

Covers all eight static methods on ``src.reports.sfp_transceiver_data_processor``:
``_ensure_prerequisite_csvs`` (four file-existence combinations),
``_load_device_site_context`` (happy path builds MAC->site map),
``_extract_transceiver_row`` (no-optic, unknown-mac, matched branches),
``_scan_port_stats`` (mixed rows produce correct counters + unique MACs),
``_log_merge_summary`` (matched==0 vs matched>0 log paths),
``_finalize_merge_output`` (write + user notice + logging),
``_run_merge_pipeline`` (happy path + FileNotFoundError / csv.Error /
Exception re-raises), and ``merge_transceiver_data`` (public entry point
resolves paths and delegates to helpers).
"""

from __future__ import annotations

import csv
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from src.reports.sfp_transceiver_data_processor import (
    SFPTransceiverDataProcessor as P,
)


def _make_mh(**extra):
    """Assemble a stub MistHelper module with the attributes each method touches."""
    defaults = {
        "OrgDeviceStatsExporter": MagicMock(name="OrgDeviceStatsExporter"),
        "DataExporter": MagicMock(name="DataExporter"),
        "FilePathUtils": MagicMock(name="FilePathUtils"),
    }
    defaults.update(extra)
    return SimpleNamespace(**defaults)


# ---------- _ensure_prerequisite_csvs ----------


def test_ensure_prereq_csvs_does_nothing_when_both_exist() -> None:
    """When both CSVs exist neither exporter is invoked."""
    fake_mh = _make_mh()
    with (
        patch("src.reports.sfp_transceiver_data_processor.OrgInventoryExporter") as inv_exporter,
        patch("src.reports.sfp_transceiver_data_processor.os.path.exists", return_value=True),
        patch("src.reports.sfp_transceiver_data_processor.importlib.import_module", return_value=fake_mh),
    ):
        P._ensure_prerequisite_csvs("port.csv", "devices.csv")
    fake_mh.OrgDeviceStatsExporter.device_port_stats.assert_not_called()
    inv_exporter.devices_with_site_info.assert_not_called()


def test_ensure_prereq_csvs_generates_port_stats_when_missing(capsys: pytest.CaptureFixture[str]) -> None:
    """When only the port-stats CSV is missing OrgDeviceStatsExporter is invoked."""
    fake_mh = _make_mh()

    def exists(path: str) -> bool:
        return path != "port.csv"

    with (
        patch("src.reports.sfp_transceiver_data_processor.OrgInventoryExporter") as inv_exporter,
        patch("src.reports.sfp_transceiver_data_processor.os.path.exists", side_effect=exists),
        patch("src.reports.sfp_transceiver_data_processor.importlib.import_module", return_value=fake_mh),
    ):
        P._ensure_prerequisite_csvs("port.csv", "devices.csv")
    fake_mh.OrgDeviceStatsExporter.device_port_stats.assert_called_once_with()
    inv_exporter.devices_with_site_info.assert_not_called()
    assert "OrgDevicePortStats.csv not found" in capsys.readouterr().out


def test_ensure_prereq_csvs_generates_devices_when_missing(capsys: pytest.CaptureFixture[str]) -> None:
    """When only the devices CSV is missing OrgInventoryExporter is invoked."""
    fake_mh = _make_mh()

    def exists(path: str) -> bool:
        return path != "devices.csv"

    with (
        patch("src.reports.sfp_transceiver_data_processor.OrgInventoryExporter") as inv_exporter,
        patch("src.reports.sfp_transceiver_data_processor.os.path.exists", side_effect=exists),
        patch("src.reports.sfp_transceiver_data_processor.importlib.import_module", return_value=fake_mh),
    ):
        P._ensure_prerequisite_csvs("port.csv", "devices.csv")
    fake_mh.OrgDeviceStatsExporter.device_port_stats.assert_not_called()
    inv_exporter.devices_with_site_info.assert_called_once_with()
    assert "AllDevicesWithSiteInfo.csv not found" in capsys.readouterr().out


def test_ensure_prereq_csvs_generates_both_when_missing() -> None:
    """When both CSVs are missing both exporters run."""
    fake_mh = _make_mh()
    with (
        patch("src.reports.sfp_transceiver_data_processor.OrgInventoryExporter") as inv_exporter,
        patch("src.reports.sfp_transceiver_data_processor.os.path.exists", return_value=False),
        patch("src.reports.sfp_transceiver_data_processor.importlib.import_module", return_value=fake_mh),
    ):
        P._ensure_prerequisite_csvs("port.csv", "devices.csv")
    fake_mh.OrgDeviceStatsExporter.device_port_stats.assert_called_once_with()
    inv_exporter.devices_with_site_info.assert_called_once_with()


# ---------- _load_device_site_context ----------


def test_load_device_site_context_builds_mac_keyed_map(tmp_path) -> None:
    """CSV rows become a MAC-keyed dict of site_name/site_address/device_name."""
    csv_path = tmp_path / "devices.csv"
    csv_path.write_text(
        "mac,site_name,site_address,name\n" "aa,HQ,1 Main St,ap-1\n" "bb,Branch,2 Elm St,ap-2\n",
        encoding="utf-8",
    )
    result = P._load_device_site_context(str(csv_path))
    assert result == {
        "aa": {"site_name": "HQ", "site_address": "1 Main St", "device_name": "ap-1"},
        "bb": {"site_name": "Branch", "site_address": "2 Elm St", "device_name": "ap-2"},
    }


def test_load_device_site_context_defaults_missing_columns_to_empty(tmp_path) -> None:
    """Missing optional columns default to empty strings for each row."""
    csv_path = tmp_path / "devices.csv"
    csv_path.write_text("mac\naa\n", encoding="utf-8")
    result = P._load_device_site_context(str(csv_path))
    assert result == {"aa": {"site_name": "", "site_address": "", "device_name": ""}}


# ---------- _extract_transceiver_row ----------


def test_extract_transceiver_row_returns_none_when_no_optic() -> None:
    """Empty xcvr_model is not a candidate row."""
    result = P._extract_transceiver_row({"mac": "aa", "xcvr_model": ""}, {"aa": {}})
    assert result == (None, False, None)


def test_extract_transceiver_row_flags_candidate_when_mac_unknown() -> None:
    """Optic present but MAC absent from site_info -> candidate, no merged row."""
    result = P._extract_transceiver_row({"mac": "unknown", "xcvr_model": "SFP-1G"}, {"aa": {}})
    assert result == (None, True, None)


def test_extract_transceiver_row_builds_merged_row_when_matched() -> None:
    """Optic present and MAC known -> merged row + candidate + mac."""
    site_info = {"aa": {"site_name": "HQ", "site_address": "1 Main St", "device_name": "ap-1"}}
    row = {
        "mac": "aa",
        "xcvr_model": "SFP-1G",
        "port_id": "ge-0/0/0",
        "xcvr_part_number": "PN-1",
        "xcvr_serial": "SN-1",
    }
    merged, has_transceiver, mac_match = P._extract_transceiver_row(row, site_info)
    assert has_transceiver is True
    assert mac_match == "aa"
    assert merged == {
        "site_name": "HQ",
        "site_address": "1 Main St",
        "device_name": "ap-1",
        "port_id": "ge-0/0/0",
        "transceiver_part_number": "PN-1",
        "transceiver_model": "SFP-1G",
        "transceiver_serial_number": "SN-1",
    }


# ---------- _scan_port_stats ----------


def test_scan_port_stats_counts_and_returns_merged_rows(tmp_path) -> None:
    """Mixed rows produce correct counters, merged rows, and unique-MAC set."""
    csv_path = tmp_path / "ports.csv"
    csv_path.write_text(
        "mac,xcvr_model,port_id,xcvr_part_number,xcvr_serial\n"
        "aa,SFP-1G,ge-0/0/0,PN-1,SN-1\n"
        "aa,SFP-10G,ge-0/0/1,PN-2,SN-2\n"
        "unknown,SFP-1G,ge-0/0/2,PN-3,SN-3\n"
        "aa,,ge-0/0/3,,\n",
        encoding="utf-8",
    )
    site_info = {"aa": {"site_name": "HQ", "site_address": "1 Main St", "device_name": "ap-1"}}
    merged, total, candidates, matched, macs = P._scan_port_stats(str(csv_path), site_info)
    assert total == 4
    assert candidates == 3  # three rows with a non-empty xcvr_model
    assert matched == 2  # two merged output rows (both for MAC aa)
    assert len(merged) == 2
    assert macs == {"aa"}


# ---------- _log_merge_summary ----------


def test_log_merge_summary_emits_no_match_message(caplog: pytest.LogCaptureFixture) -> None:
    """matched_rows==0 goes down the informational no-optics-populated branch."""
    with caplog.at_level("INFO"):
        P._log_merge_summary(0, 10, 3, 5, 0)
    assert any("no matching transceivers found" in r.message for r in caplog.records)


def test_log_merge_summary_emits_success_message(caplog: pytest.LogCaptureFixture) -> None:
    """matched_rows>0 emits the success-path counters message."""
    with caplog.at_level("INFO"):
        P._log_merge_summary(4, 10, 5, 5, 2)
    assert any("ports with transceivers found" in r.message for r in caplog.records)


# ---------- _finalize_merge_output ----------


def test_finalize_merge_output_writes_via_backend_and_notifies_user(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Writes via DataExporter and prints the user-facing filename notice."""
    fake_mh = _make_mh()
    rows = [{"site_name": "HQ"}]
    with patch("src.reports.sfp_transceiver_data_processor.importlib.import_module", return_value=fake_mh):
        P._finalize_merge_output(rows)
    fake_mh.DataExporter.write_with_format_selection.assert_called_once_with(rows, "MergedTransceiverData.csv")
    assert "Merged data written to MergedTransceiverData.csv" in capsys.readouterr().out


# ---------- _run_merge_pipeline ----------


def test_run_merge_pipeline_happy_path_invokes_helpers_in_order() -> None:
    """Happy path: load -> scan -> summary -> finalize, each called with the right args."""
    site_info = {"aa": {"site_name": "HQ", "site_address": "1 Main St", "device_name": "ap-1"}}
    merged_data = [{"site_name": "HQ"}]
    with (
        patch.object(P, "_load_device_site_context", return_value=site_info) as load,
        patch.object(
            P,
            "_scan_port_stats",
            return_value=(merged_data, 5, 3, 1, {"aa"}),
        ) as scan,
        patch.object(P, "_log_merge_summary") as log_summary,
        patch.object(P, "_finalize_merge_output") as finalize,
    ):
        P._run_merge_pipeline("port.csv", "devices.csv")
    load.assert_called_once_with("devices.csv")
    scan.assert_called_once_with("port.csv", site_info)
    log_summary.assert_called_once_with(1, 5, 3, 1, 1)
    finalize.assert_called_once_with(merged_data)


def test_run_merge_pipeline_reraises_file_not_found() -> None:
    """FileNotFoundError from the helpers propagates to the caller."""
    with patch.object(P, "_load_device_site_context", side_effect=FileNotFoundError("missing")):
        with pytest.raises(FileNotFoundError):
            P._run_merge_pipeline("port.csv", "devices.csv")


def test_run_merge_pipeline_reraises_csv_error() -> None:
    """csv.Error from the helpers propagates to the caller."""
    with patch.object(P, "_load_device_site_context", side_effect=csv.Error("bad csv")):
        with pytest.raises(csv.Error):
            P._run_merge_pipeline("port.csv", "devices.csv")


def test_run_merge_pipeline_reraises_generic_exception() -> None:
    """Unexpected errors propagate to the caller."""
    with patch.object(P, "_load_device_site_context", side_effect=RuntimeError("boom")):
        with pytest.raises(RuntimeError, match="boom"):
            P._run_merge_pipeline("port.csv", "devices.csv")


# ---------- merge_transceiver_data ----------


def test_merge_transceiver_data_resolves_paths_and_delegates() -> None:
    """Public entry resolves both CSV paths and delegates to prereq + pipeline helpers."""
    fake_mh = _make_mh()
    fake_mh.FilePathUtils.get_csv_path.side_effect = lambda name: f"/data/{name}"
    with (
        patch("src.reports.sfp_transceiver_data_processor.importlib.import_module", return_value=fake_mh),
        patch.object(P, "_ensure_prerequisite_csvs") as ensure,
        patch.object(P, "_run_merge_pipeline") as pipeline,
    ):
        P.merge_transceiver_data()
    ensure.assert_called_once_with("/data/OrgDevicePortStats.csv", "/data/AllDevicesWithSiteInfo.csv")
    pipeline.assert_called_once_with("/data/OrgDevicePortStats.csv", "/data/AllDevicesWithSiteInfo.csv")
