"""Unit tests for OfflineDeviceReporter (issue #878 tranche 33 -- un-omit).

Covers every static method on
``src.reports.offline_device_reporter.OfflineDeviceReporter``:
``_parse_threshold_attempt`` (int/range/ValueError), ``_prompt_threshold``
(test-mode shortcut + retry-until-valid + max-retries fallback),
``_fetch_data`` (site lookup + device stats happy path with missing site_id),
``_format_offline_timing`` (never-connected sentinel + days+hours + hours-only),
``_compile_offline_record`` (type-map hit + capitalize fallback + site
lookup fallback + unnamed fallback), ``_parse_last_seen_epoch``
(missing/None/blank/numeric), ``_maybe_build_offline_record``
(connected-skip / inside-threshold-skip / never-connected keep / offline
keep), ``_process_devices`` (sort by sort_key desc),
``_render_offline_breakdowns`` (zero-suppress + top 5 leaderboard),
``_display_summary`` (aggregate + breakdown call),
``_save_offline_csv`` (strip helper keys + timestamped filename),
``_present_results`` (display cap + save call),
``_gather_offline_inputs`` (no-org early-abort + happy path),
``_finalize_offline_report`` (summary + present + elapsed log),
``execute`` (every branch: no-org, fetch-exception, no-devices,
no-offline, happy path).
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from src.reports.offline_device_reporter import OfflineDeviceReporter as R


def _make_mh(**extra):
    """Assemble a stub MistHelper module with the attributes each method touches."""
    defaults = {
        "IS_TEST_MODE": False,
        "InputUtils": MagicMock(name="InputUtils"),
        "APICoreFetchUtils": MagicMock(name="APICoreFetchUtils"),
        "mistapi": MagicMock(name="mistapi"),
        "apisession": MagicMock(name="apisession"),
        "DataExporter": MagicMock(name="DataExporter"),
        "ConfigUtils": MagicMock(name="ConfigUtils"),
    }
    defaults.update(extra)
    return SimpleNamespace(**defaults)


# ---------- _parse_threshold_attempt ----------


def test_parse_threshold_attempt_returns_int_when_in_range() -> None:
    """Numeric input within bounds returns the parsed int."""
    assert R._parse_threshold_attempt("48") == 48


def test_parse_threshold_attempt_returns_none_when_below_min(capsys: pytest.CaptureFixture[str]) -> None:
    """Zero is below MIN_THRESHOLD_HOURS: returns None with range message."""
    assert R._parse_threshold_attempt("0") is None
    assert "must be between" in capsys.readouterr().out


def test_parse_threshold_attempt_returns_none_when_above_max(capsys: pytest.CaptureFixture[str]) -> None:
    """Above MAX_THRESHOLD_HOURS: returns None with range message."""
    assert R._parse_threshold_attempt("99999") is None
    assert "must be between" in capsys.readouterr().out


def test_parse_threshold_attempt_returns_none_on_value_error(capsys: pytest.CaptureFixture[str]) -> None:
    """Non-numeric input triggers ValueError branch and prints invalid message."""
    assert R._parse_threshold_attempt("abc") is None
    assert "Invalid input" in capsys.readouterr().out


# ---------- _prompt_threshold ----------


def test_prompt_threshold_returns_default_in_test_mode() -> None:
    """IS_TEST_MODE short-circuits interactive prompting."""
    fake_mh = _make_mh(IS_TEST_MODE=True)
    with patch(
        "src.reports.offline_device_reporter.importlib.import_module",
        return_value=fake_mh,
    ):
        assert R._prompt_threshold() == R.DEFAULT_THRESHOLD_HOURS


def test_prompt_threshold_returns_first_valid_attempt() -> None:
    """First safe_input value parses cleanly -> returned immediately."""
    fake_mh = _make_mh()
    fake_mh.InputUtils.safe_input.return_value = "24"
    with patch(
        "src.reports.offline_device_reporter.importlib.import_module",
        return_value=fake_mh,
    ):
        assert R._prompt_threshold() == 24


def test_prompt_threshold_retries_then_succeeds(capsys: pytest.CaptureFixture[str]) -> None:
    """Bad input on first attempt: retry counter decrements and second attempt wins."""
    fake_mh = _make_mh()
    fake_mh.InputUtils.safe_input.side_effect = ["bad", "72"]
    with patch(
        "src.reports.offline_device_reporter.importlib.import_module",
        return_value=fake_mh,
    ):
        assert R._prompt_threshold() == 72
    assert "attempt(s) remaining" in capsys.readouterr().out


def test_prompt_threshold_falls_back_when_max_retries_exceeded(capsys: pytest.CaptureFixture[str]) -> None:
    """All MAX_INPUT_RETRIES attempts fail -> DEFAULT_THRESHOLD_HOURS."""
    fake_mh = _make_mh()
    fake_mh.InputUtils.safe_input.side_effect = ["bad"] * R.MAX_INPUT_RETRIES
    with patch(
        "src.reports.offline_device_reporter.importlib.import_module",
        return_value=fake_mh,
    ):
        assert R._prompt_threshold() == R.DEFAULT_THRESHOLD_HOURS
    assert "Using default threshold" in capsys.readouterr().out


# ---------- _fetch_data ----------


def test_fetch_data_builds_site_lookup_and_returns_devices() -> None:
    """Happy path: sites with id become lookup entries, id-less sites are skipped."""
    fake_mh = _make_mh()
    fake_mh.APICoreFetchUtils.all_sites_with_limit.return_value = [
        {"id": "site-a", "name": "Alpha"},
        {"id": "site-b"},  # No name -> "Unknown Site"
        {"name": "orphan"},  # No id -> skipped
    ]
    stats_resp = MagicMock(name="statsResp")
    fake_mh.mistapi.api.v1.orgs.stats.listOrgDevicesStats.return_value = stats_resp
    fake_mh.mistapi.get_all.return_value = [{"mac": "aa"}, {"mac": "bb"}]
    with patch(
        "src.reports.offline_device_reporter.importlib.import_module",
        return_value=fake_mh,
    ):
        site_lookup, devices = R._fetch_data("org-uuid")
    assert site_lookup == {"site-a": "Alpha", "site-b": "Unknown Site"}
    assert devices == [{"mac": "aa"}, {"mac": "bb"}]
    fake_mh.mistapi.api.v1.orgs.stats.listOrgDevicesStats.assert_called_once_with(
        fake_mh.apisession, "org-uuid", type="all", status="all", fields="*", limit=1000
    )


# ---------- _format_offline_timing ----------


def test_format_offline_timing_returns_never_connected_sentinel() -> None:
    """Epoch 0.0 signals never-connected -> sentinel strings + infinite sort key."""
    last_seen, duration, sort_key = R._format_offline_timing(0.0, 0.0)
    assert last_seen == "Never Connected"
    assert duration == "Never Connected"
    assert sort_key == float("inf")


def test_format_offline_timing_days_and_hours() -> None:
    """Offline > 24h produces "N days H hours"."""
    last_seen, duration, sort_key = R._format_offline_timing(1_700_000_000.0, 25 * 3600)
    assert "days" in duration and "hours" in duration
    assert sort_key == 25 * 3600
    assert last_seen != "Never Connected"


def test_format_offline_timing_hours_only() -> None:
    """Offline < 24h produces "H hours" (no days segment)."""
    _, duration, _ = R._format_offline_timing(1_700_000_000.0, 5 * 3600)
    assert duration == "5 hours"


# ---------- _compile_offline_record ----------


def test_compile_offline_record_maps_known_type_and_resolves_site() -> None:
    """Known type maps to friendly label; site_id resolves via lookup."""
    device = {"type": "ap", "site_id": "s1", "mac": "aa", "name": "AP-1"}
    site_lookup = {"s1": "HQ"}
    rec = R._compile_offline_record(device, site_lookup, "2026-01-01", "5 hours", 18000.0)
    assert rec["Device Type"] == "AP"
    assert rec["Site Name"] == "HQ"
    assert rec["Device Name"] == "AP-1"
    assert rec["_sort_key"] == "18000.0"


def test_compile_offline_record_capitalizes_unknown_type_and_defaults() -> None:
    """Unknown type is capitalized; missing name/site fall back to defaults."""
    device = {"type": "router"}
    rec = R._compile_offline_record(device, {}, "2026-01-01", "1 hours", 3600.0)
    assert rec["Device Type"] == "Router"
    assert rec["Site Name"] == "Unknown Site"
    assert rec["Device Name"] == "(unnamed)"


def test_compile_offline_record_uses_unknown_when_type_absent() -> None:
    """Missing type field defaults to 'unknown' and capitalizes to 'Unknown'."""
    rec = R._compile_offline_record({}, {}, "x", "y", 0.0)
    assert rec["Device Type"] == "Unknown"


# ---------- _parse_last_seen_epoch ----------


def test_parse_last_seen_epoch_returns_zero_when_missing() -> None:
    """Missing key -> 0.0."""
    assert R._parse_last_seen_epoch({}) == 0.0


def test_parse_last_seen_epoch_returns_zero_when_none() -> None:
    """None value -> 0.0."""
    assert R._parse_last_seen_epoch({"last_seen": None}) == 0.0


def test_parse_last_seen_epoch_returns_zero_when_falsy_zero() -> None:
    """Numeric 0 is falsy -> 0.0."""
    assert R._parse_last_seen_epoch({"last_seen": 0}) == 0.0


def test_parse_last_seen_epoch_coerces_numeric_string() -> None:
    """Non-zero numeric epoch cast via float()."""
    assert R._parse_last_seen_epoch({"last_seen": "1700000000"}) == 1_700_000_000.0


# ---------- _maybe_build_offline_record ----------


def test_maybe_build_offline_record_skips_connected_devices() -> None:
    """status == 'connected' short-circuits to None."""
    assert R._maybe_build_offline_record({"status": "connected"}, {}, 0.0, 3600) is None


def test_maybe_build_offline_record_skips_when_inside_threshold() -> None:
    """last_seen fresh (< threshold) with prior contact -> None."""
    now = 1_700_000_000.0
    device = {"status": "disconnected", "last_seen": now - 100}
    assert R._maybe_build_offline_record(device, {}, now, 3600) is None


def test_maybe_build_offline_record_keeps_never_connected_devices() -> None:
    """Never-connected (last_seen == 0) always qualifies."""
    device = {"status": "disconnected"}
    rec = R._maybe_build_offline_record(device, {}, 1_700_000_000.0, 3600)
    assert rec is not None
    assert rec["Last Seen"] == "Never Connected"


def test_maybe_build_offline_record_keeps_offline_beyond_threshold() -> None:
    """Offline longer than threshold builds a record."""
    now = 1_700_000_000.0
    device = {"status": "disconnected", "last_seen": now - 7200, "type": "switch"}
    rec = R._maybe_build_offline_record(device, {}, now, 3600)
    assert rec is not None
    assert rec["Device Type"] == "Switch"


# ---------- _process_devices ----------


def test_process_devices_sorts_offline_records_by_duration_desc() -> None:
    """Longest-offline devices appear first."""
    now = 2_000_000_000.0
    devices = [
        {"status": "disconnected", "last_seen": now - 3600, "name": "short"},
        {"status": "disconnected", "last_seen": now - 100_000, "name": "long"},
        {"status": "connected", "last_seen": now, "name": "skip"},
    ]
    with patch("src.reports.offline_device_reporter.time.time", return_value=now):
        results = R._process_devices(devices, {}, 1)
    assert [r["Device Name"] for r in results] == ["long", "short"]


# ---------- _render_offline_breakdowns ----------


def test_render_offline_breakdowns_hides_zero_type_and_lists_top_sites(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Zero counts are suppressed; sites render sorted descending, capped at 5."""
    type_counts = {"AP": 3, "Switch": 0, "Gateway": 1}
    site_counts = {f"site-{i}": i for i in range(1, 8)}
    R._render_offline_breakdowns(type_counts, site_counts)
    output = capsys.readouterr().out
    assert "APs: 3" in output
    assert "Switches:" not in output  # zero-suppressed
    assert "Gateways: 1" in output
    assert "1. site-7: 7 offline" in output  # highest count first
    assert "site-1" not in output  # trimmed by top-5 slice


def test_render_offline_breakdowns_skips_top_sites_when_empty(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Empty site_counts hides the Top 5 leaderboard entirely."""
    R._render_offline_breakdowns({"AP": 1}, {})
    output = capsys.readouterr().out
    assert "Top 5 Sites" not in output


# ---------- _display_summary ----------


def test_display_summary_prints_counts_and_calls_breakdown(capsys: pytest.CaptureFixture[str]) -> None:
    """Header + totals print; per-type/per-site counts render via helper."""
    offline_records = [
        {"Device Type": "AP", "Site Name": "HQ"},
        {"Device Type": "AP", "Site Name": "HQ"},
        {"Device Type": "Switch", "Site Name": "Branch"},
    ]
    R._display_summary(100, offline_records, 48)
    output = capsys.readouterr().out
    assert "Total devices in org: 100" in output
    assert "Devices offline > 48 hours: 3" in output
    assert "APs: 2" in output
    assert "Switchs: 1" in output  # naive pluralization in source: "Switch" + "s"


# ---------- _save_offline_csv ----------


def test_save_offline_csv_strips_helper_keys_and_writes(capsys: pytest.CaptureFixture[str]) -> None:
    """Helper keys (_sort_key) are stripped; DataExporter is called with expected filename."""
    fake_mh = _make_mh()
    records = [
        {
            "Device Name": "AP-1",
            "Device Type": "AP",
            "Site Name": "HQ",
            "MAC Address": "aa",
            "Serial Number": "s1",
            "Model": "m1",
            "Last Seen": "2026-01-01",
            "Offline Duration": "1 hours",
            "Status": "disconnected",
            "_sort_key": "3600.0",
        }
    ]
    with patch(
        "src.reports.offline_device_reporter.importlib.import_module",
        return_value=fake_mh,
    ):
        R._save_offline_csv(records, 1)
    written = fake_mh.DataExporter.write_with_format_selection.call_args
    csv_records = written.kwargs["data"]
    assert "_sort_key" not in csv_records[0]
    filename = written.kwargs["filename_or_table"]
    assert filename.startswith("OfflineDeviceReport_") and filename.endswith(".csv")
    assert "CSV saved" in capsys.readouterr().out


# ---------- _present_results ----------


def test_present_results_caps_display_rows_and_calls_save(capsys: pytest.CaptureFixture[str]) -> None:
    """Table display honors MAX_DISPLAY_ROWS; _save_offline_csv gets the full list."""
    records = [
        {
            "Device Name": f"d{i}",
            "Device Type": "AP",
            "Site Name": "HQ",
            "MAC Address": "",
            "Serial Number": "",
            "Model": "",
            "Last Seen": "",
            "Offline Duration": "",
            "Status": "",
        }
        for i in range(R.MAX_DISPLAY_ROWS + 5)
    ]
    with patch.object(R, "_save_offline_csv") as save:
        R._present_results(records)
    save.assert_called_once_with(records, R.MAX_DISPLAY_ROWS + 5)
    output = capsys.readouterr().out
    assert f"showing {R.MAX_DISPLAY_ROWS} of {R.MAX_DISPLAY_ROWS + 5}" in output


# ---------- _gather_offline_inputs ----------


def test_gather_offline_inputs_aborts_when_no_org(capsys: pytest.CaptureFixture[str]) -> None:
    """Missing org -> (None, 0)."""
    fake_mh = _make_mh()
    fake_mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = ""
    with patch(
        "src.reports.offline_device_reporter.importlib.import_module",
        return_value=fake_mh,
    ):
        assert R._gather_offline_inputs() == (None, 0)
    assert "No organization selected" in capsys.readouterr().out


def test_gather_offline_inputs_returns_org_and_threshold(capsys: pytest.CaptureFixture[str]) -> None:
    """Happy path resolves org + prompts threshold + echoes."""
    fake_mh = _make_mh()
    fake_mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-x"
    with (
        patch.object(R, "_prompt_threshold", return_value=24),
        patch(
            "src.reports.offline_device_reporter.importlib.import_module",
            return_value=fake_mh,
        ),
    ):
        assert R._gather_offline_inputs() == ("org-x", 24)
    assert "Threshold: 24 hours" in capsys.readouterr().out


# ---------- _finalize_offline_report ----------


def test_finalize_offline_report_runs_summary_present_and_elapsed(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Finalize walks summary -> present -> elapsed."""
    with (
        patch.object(R, "_display_summary") as summary,
        patch.object(R, "_present_results") as present,
        patch("src.reports.offline_device_reporter.time.time", return_value=1000.0),
    ):
        R._finalize_offline_report(10, [{"x": 1}], 48, 990.0)
    summary.assert_called_once_with(10, [{"x": 1}], 48)
    present.assert_called_once_with([{"x": 1}])
    assert "Report completed in 10.0 seconds" in capsys.readouterr().out


# ---------- execute ----------


def test_execute_returns_early_when_no_org() -> None:
    """No org resolved -> early return, no downstream calls."""
    with (
        patch.object(R, "_gather_offline_inputs", return_value=(None, 0)),
        patch.object(R, "_fetch_data") as fetch,
    ):
        R.execute()
    fetch.assert_not_called()


def test_execute_handles_fetch_exception(capsys: pytest.CaptureFixture[str]) -> None:
    """_fetch_data exception -> user-facing error + no processing."""
    with (
        patch.object(R, "_gather_offline_inputs", return_value=("org", 48)),
        patch.object(R, "_fetch_data", side_effect=RuntimeError("boom")),
        patch.object(R, "_process_devices") as proc,
    ):
        R.execute()
    proc.assert_not_called()
    assert "Failed to fetch data" in capsys.readouterr().out


def test_execute_prints_notice_when_no_devices(capsys: pytest.CaptureFixture[str]) -> None:
    """Empty device list -> "No devices found" notice + early return."""
    with (
        patch.object(R, "_gather_offline_inputs", return_value=("org", 48)),
        patch.object(R, "_fetch_data", return_value=({}, [])),
        patch.object(R, "_process_devices") as proc,
    ):
        R.execute()
    proc.assert_not_called()
    assert "No devices found in this organization" in capsys.readouterr().out


def test_execute_prints_all_clear_when_none_offline(capsys: pytest.CaptureFixture[str]) -> None:
    """Devices exist but none offline beyond threshold -> all-clear message."""
    with (
        patch.object(R, "_gather_offline_inputs", return_value=("org", 48)),
        patch.object(R, "_fetch_data", return_value=({}, [{"mac": "aa"}])),
        patch.object(R, "_process_devices", return_value=[]),
        patch.object(R, "_finalize_offline_report") as finalize,
    ):
        R.execute()
    finalize.assert_not_called()
    assert "All clear" in capsys.readouterr().out


def test_execute_finalizes_when_offline_records_present() -> None:
    """Happy path: devices offline -> _finalize_offline_report invoked."""
    with (
        patch.object(R, "_gather_offline_inputs", return_value=("org", 48)),
        patch.object(R, "_fetch_data", return_value=({}, [{"mac": "aa"}, {"mac": "bb"}])),
        patch.object(R, "_process_devices", return_value=[{"rec": 1}]),
        patch.object(R, "_finalize_offline_report") as finalize,
    ):
        R.execute()
    finalize.assert_called_once()
    args = finalize.call_args.args
    assert args[0] == 2  # total device count from all_devices
    assert args[1] == [{"rec": 1}]
    assert args[2] == 48
