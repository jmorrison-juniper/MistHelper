"""Unit tests for extracted GatewayStatsExporter module."""

from __future__ import annotations  # WHY: forward refs for method signatures.

import csv  # WHY: build in-memory CSVs for the file-read helper tests.
import logging  # WHY: assert log-record emission for retry/failure/success helpers.
import time  # WHY: patch time.sleep directly (avoids mypy strict re-export on time).
from pathlib import Path  # WHY: typed tmp_path parameter without # type: ignore.
from types import SimpleNamespace  # WHY: lightweight dep stubs for DI wiring.
from unittest.mock import MagicMock, patch  # WHY: side-effect stubs + attribute patching for statics.

import pytest  # WHY: fixtures + tmp_path for file helper tests.

from src.gateway import gateway_stats_exporter as module  # WHY: module handle for slot replacement + patching.
from src.gateway.gateway_stats_exporter import (  # WHY: direct symbols under test.
    EMPTY_IP_TOKENS,
    SAMPLE_CONFLICT_LIMIT,
    STATS_CSV_FILENAME,
    STATUS_FAILED,
    GatewayStatsExporter,
    _build_failure_record,
    _compute_backoff,
    _enrich_stats_record,
    _log_attempt_success,
    _log_retry_failure,
    _log_terminal_failure,
    configure_gateway_stats_exporter_dependencies,
)


def _configure_dependencies() -> None:
    """Configure minimal dependency graph for gateway stats exporter tests."""
    configure_gateway_stats_exporter_dependencies(
        apisession_dependency=object(),
        mistapi_dependency=SimpleNamespace(),
        config_utils=SimpleNamespace(get_cached_or_prompted_org_id=MagicMock(return_value="org-1")),
        validation_utils=SimpleNamespace(validate_site_id=MagicMock(), validate_device_id=MagicMock()),
        data_processing_utils=SimpleNamespace(flatten_dict=MagicMock(side_effect=lambda row: row)),
        data_exporter=SimpleNamespace(write_with_format_selection=MagicMock()),
        rate_limiting_utils=SimpleNamespace(get_rate_limited_delay=MagicMock(return_value=(None, 0))),
        cache_utils=SimpleNamespace(check_and_generate_csv=MagicMock(return_value=True)),
        file_path_utils=SimpleNamespace(get_csv_path=MagicMock(return_value="test.csv")),
        execute_fn=MagicMock(return_value=([], [])),
        fast_mode_max_retries=2,
        fast_mode_retry_delay=0.1,
        api_usage_cache={},
        tqdm_module=MagicMock(side_effect=lambda rows, **kwargs: rows),
        gateway_export_utils_ref=SimpleNamespace(_get_devices_with_sites=MagicMock(return_value=[])),
    )


# -------------------------- Existing coverage (preserved) --------------------------


def test_collect_device_wan_ips_ignores_empty_and_invalid_values() -> None:
    """WAN IP collection should keep only non-empty, non-null values mapped by port."""
    _configure_dependencies()

    row = {
        "if_stat_ge-0/0/0_ips": "10.0.0.1",
        "if_stat_ge-0/0/1_ips": "",
        "if_stat_ge-0/0/2_ips": "null",
    }

    device_ips = GatewayStatsExporter._collect_device_wan_ips(row)

    assert device_ips == {"10.0.0.1": ["0/0/0"]}


def test_find_ip_conflicts_returns_only_multi_port_ips() -> None:
    """Conflict finder should return only entries whose IP appears on multiple ports."""
    _configure_dependencies()

    conflicts = GatewayStatsExporter._find_ip_conflicts(
        {
            "10.0.0.1": ["0/0/0", "0/0/1"],
            "10.0.0.2": ["0/0/2"],
        },
        "gw-1",
    )

    assert conflicts == [{"value": "10.0.0.1", "ports": ["0/0/0", "0/0/1"]}]


def test_build_conflict_records_creates_port_level_rows() -> None:
    """Conflict record builder should generate one row per conflicting port."""
    _configure_dependencies()

    records = GatewayStatsExporter._build_conflict_records(
        [{"value": "10.0.0.1", "ports": ["0/0/0", "0/0/1"]}],
        "gw-1",
        "site-a",
    )

    assert len(records) == 2
    assert {record["port_name"] for record in records} == {"ge-0/0/0", "ge-0/0/1"}
    assert all(record["port_ip"] == "10.0.0.1" for record in records)


# -------------------------- Module helper coverage --------------------------


def test_enrich_stats_record_attaches_all_identifiers() -> None:
    """Enrichment should stamp site_id/site_name/device_id/device_name into the stats dict."""
    _configure_dependencies()

    stats = {"cpu": 0.5}  # WHY: baseline stats record before enrichment.
    device_info = ("site-1", "dev-1", "gw-name", "Site A")

    enriched = _enrich_stats_record(stats, device_info)

    assert enriched["site_id"] == "site-1"
    assert enriched["site_name"] == "Site A"
    assert enriched["device_id"] == "dev-1"
    assert enriched["device_name"] == "gw-name"
    assert enriched["cpu"] == 0.5  # WHY: preserves original payload keys.


def test_build_failure_record_preserves_legacy_shape() -> None:
    """Failure record builder should return the legacy dict with error text and failed status."""
    _configure_dependencies()

    device_info = ("site-1", "dev-1", "gw-name", "Site A")
    record = _build_failure_record(device_info, RuntimeError("boom"))

    assert record["site_id"] == "site-1"
    assert record["device_id"] == "dev-1"
    assert record["device_name"] == "gw-name"
    assert record["site_name"] == "Site A"
    assert record["error"] == "boom"
    assert record["status"] == STATUS_FAILED


def test_compute_backoff_fast_returns_flat_delay() -> None:
    """Fast-mode backoff should return the base delay regardless of attempt count."""
    _configure_dependencies()

    assert _compute_backoff(attempt=0, retry_delay=0.5, fast=True) == 0.5
    assert _compute_backoff(attempt=3, retry_delay=0.5, fast=True) == 0.5


def test_compute_backoff_slow_uses_exponential_growth() -> None:
    """Non-fast backoff should grow as retry_delay * 2**attempt."""
    _configure_dependencies()

    assert _compute_backoff(attempt=0, retry_delay=1.0, fast=False) == 1.0  # WHY: 1 * 2^0.
    assert _compute_backoff(attempt=1, retry_delay=1.0, fast=False) == 2.0  # WHY: 1 * 2^1.
    assert _compute_backoff(attempt=3, retry_delay=1.0, fast=False) == 8.0  # WHY: 1 * 2^3.


def test_log_retry_failure_emits_warning(caplog: pytest.LogCaptureFixture) -> None:
    """Retry-failure helper should emit a WARNING record with legacy phrasing."""
    _configure_dependencies()

    with caplog.at_level(logging.WARNING):
        _log_retry_failure(0, ("site-1", "dev-1", "gw", "Site A"), RuntimeError("nope"))

    assert any("Attempt 1 failed" in record.getMessage() for record in caplog.records)


def test_log_terminal_failure_emits_error(caplog: pytest.LogCaptureFixture) -> None:
    """Terminal-failure helper should emit an ERROR record with retry count in phrasing."""
    _configure_dependencies()

    with caplog.at_level(logging.ERROR):
        _log_terminal_failure(("site-1", "dev-1", "gw", "Site A"), 3, RuntimeError("nope"))

    assert any(
        "Failed to fetch device stats" in record.getMessage() and "3 attempts" in record.getMessage()
        for record in caplog.records
    )


def test_log_attempt_success_first_try_uses_debug(caplog: pytest.LogCaptureFixture) -> None:
    """First-try success should emit at DEBUG, not INFO."""
    _configure_dependencies()

    with caplog.at_level(logging.DEBUG):
        _log_attempt_success(0, ("site-1", "dev-1", "gw", "Site A"))

    debug_records = [record for record in caplog.records if record.levelno == logging.DEBUG]
    assert any("Collected device stats" in record.getMessage() for record in debug_records)


def test_log_attempt_success_retry_uses_info(caplog: pytest.LogCaptureFixture) -> None:
    """Retry success should emit at INFO with retry index in phrasing."""
    _configure_dependencies()

    with caplog.at_level(logging.INFO):
        _log_attempt_success(2, ("site-1", "dev-1", "gw", "Site A"))

    info_records = [record for record in caplog.records if record.levelno == logging.INFO]
    assert any("Retry 2 successful" in record.getMessage() for record in info_records)


# -------------------------- _extract_wan_ip_cell edge cases --------------------------


def test_extract_wan_ip_cell_returns_none_for_missing_key() -> None:
    """Missing key should short-circuit to None."""
    _configure_dependencies()

    assert GatewayStatsExporter._extract_wan_ip_cell({}, "if_stat_ge-0/0/0_ips") is None


def test_extract_wan_ip_cell_returns_none_for_sentinel_tokens() -> None:
    """Sentinel tokens like 'nan'/'None'/'null' should map to None."""
    _configure_dependencies()

    for sentinel in EMPTY_IP_TOKENS:  # WHY: exercise each legacy sentinel value.
        row = {"if_stat_ge-0/0/0_ips": sentinel}
        # WHY: empty strings are falsy so short-circuit path returns None too.
        assert GatewayStatsExporter._extract_wan_ip_cell(row, "if_stat_ge-0/0/0_ips") is None


def test_extract_wan_ip_cell_strips_whitespace_around_valid_ip() -> None:
    """Valid IPs should be returned stripped of surrounding whitespace."""
    _configure_dependencies()

    row = {"if_stat_ge-0/0/0_ips": "  10.0.0.1  "}
    assert GatewayStatsExporter._extract_wan_ip_cell(row, "if_stat_ge-0/0/0_ips") == "10.0.0.1"


# -------------------------- _flatten_stats + _log_export_summary --------------------------


def test_flatten_stats_delegates_to_data_processing_utils() -> None:
    """Flatten helper should call DataProcessingUtils.flatten_dict once per row."""
    _configure_dependencies()

    all_stats = [{"a": 1}, {"b": 2}]
    result = GatewayStatsExporter._flatten_stats(all_stats)

    assert result == all_stats  # WHY: default stub is identity so rows pass through.
    assert module.DataProcessingUtils.flatten_dict.call_count == 2


def test_log_export_summary_success_only(caplog: pytest.LogCaptureFixture) -> None:
    """When all rows are successful, INFO 'all completed successfully' banner should emit."""
    _configure_dependencies()

    with caplog.at_level(logging.INFO):
        GatewayStatsExporter._log_export_summary(
            [{"status": "ok"}, {"status": "ok"}],
            [("site-1", "dev-1", "gw", "Site A")],
        )

    assert any("All 2 requests completed successfully" in record.getMessage() for record in caplog.records)


def test_log_export_summary_partial_failure_emits_warning(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Partial-failure branch should emit a WARNING with failed count."""
    _configure_dependencies()

    with caplog.at_level(logging.WARNING):
        GatewayStatsExporter._log_export_summary(
            [{"status": "ok"}, {"status": STATUS_FAILED}],
            [("site-1", "dev-1", "gw", "Site A")],
        )

    warns = [record for record in caplog.records if record.levelno == logging.WARNING]
    assert any("1 requests failed out of 2" in record.getMessage() for record in warns)


# -------------------------- _export_stats + _export_conflict_results --------------------------


def test_export_stats_empty_short_circuits(caplog: pytest.LogCaptureFixture) -> None:
    """Empty stats list should warn and skip persistence."""
    _configure_dependencies()

    module.DataExporter.write_with_format_selection = MagicMock()
    with caplog.at_level(logging.WARNING):
        GatewayStatsExporter._export_stats([], [])

    module.DataExporter.write_with_format_selection.assert_not_called()
    assert any("No gateway device statistics found" in record.getMessage() for record in caplog.records)


def test_export_stats_populated_writes_csv() -> None:
    """Populated stats list should be flattened and written via DataExporter."""
    _configure_dependencies()

    module.DataExporter.write_with_format_selection = MagicMock()
    stats = [{"status": "ok", "cpu": 0.1}]
    devices = [("site-1", "dev-1", "gw", "Site A")]

    GatewayStatsExporter._export_stats(stats, devices)

    module.DataExporter.write_with_format_selection.assert_called_once_with(stats, STATS_CSV_FILENAME)


def test_export_conflict_results_empty_short_circuits(caplog: pytest.LogCaptureFixture) -> None:
    """Empty conflict list should log healthy banner and skip persistence."""
    _configure_dependencies()

    module.DataExporter.write_with_format_selection = MagicMock()

    with caplog.at_level(logging.INFO):
        GatewayStatsExporter._export_conflict_results([])

    module.DataExporter.write_with_format_selection.assert_not_called()
    messages = [record.getMessage() for record in caplog.records]
    assert any("healthy WAN port configurations" in message for message in messages)


def test_export_conflict_results_populated_writes_and_prints(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Populated conflicts should sort, write CSV, log summary + sample."""
    _configure_dependencies()

    module.DataExporter.write_with_format_selection = MagicMock()

    conflicts = [
        {
            "device_name": "gw-1",
            "site_name": "Site A",
            "port_name": "ge-0/0/0",
            "port_ip": "10.0.0.1",
            "conflict_with_ports": "0/0/1",
        },
        {
            "device_name": "gw-1",
            "site_name": "Site A",
            "port_name": "ge-0/0/1",
            "port_ip": "10.0.0.1",
            "conflict_with_ports": "0/0/0",
        },
    ]

    with caplog.at_level(logging.INFO):
        GatewayStatsExporter._export_conflict_results(conflicts)

    module.DataExporter.write_with_format_selection.assert_called_once()
    messages = [record.getMessage() for record in caplog.records]
    assert any("1 gateways with IP conflicts" in message for message in messages)
    assert any("Sample WAN Port IP Conflicts" in message for message in messages)


# -------------------------- _display_conflict_samples truncation --------------------------


def test_display_conflict_samples_short_list_no_trailer(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Fewer than SAMPLE_CONFLICT_LIMIT items should not log trailing 'and N more'."""
    _configure_dependencies()

    conflicts = [
        {"device_name": f"gw-{idx}", "site_name": "S", "port_name": "ge-0/0/0", "port_ip": "1.1.1.1"}
        for idx in range(3)
    ]

    with caplog.at_level(logging.INFO):
        GatewayStatsExporter._display_conflict_samples(conflicts)

    messages = [record.getMessage() for record in caplog.records]
    assert not any("more conflicted ports" in message for message in messages)


def test_display_conflict_samples_long_list_emits_trailer(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Lists exceeding SAMPLE_CONFLICT_LIMIT should emit trailer with remaining count."""
    _configure_dependencies()

    total = SAMPLE_CONFLICT_LIMIT + 3
    conflicts = [
        {"device_name": f"gw-{idx}", "site_name": "S", "port_name": "ge-0/0/0", "port_ip": "1.1.1.1"}
        for idx in range(total)
    ]

    with caplog.at_level(logging.INFO):
        GatewayStatsExporter._display_conflict_samples(conflicts)

    messages = [record.getMessage() for record in caplog.records]
    assert any(f"and {total - SAMPLE_CONFLICT_LIMIT} more conflicted ports" in message for message in messages)


# -------------------------- _analyze_device_ip_conflicts + _analyze_all_gateway_conflicts --------------------------


def test_analyze_device_ip_conflicts_returns_records_for_duplicates() -> None:
    """Row with same IP on two ports should produce two conflict records."""
    _configure_dependencies()

    row = {
        "device_name": "gw-1",
        "site_name": "Site A",
        "if_stat_ge-0/0/0_ips": "10.0.0.1",
        "if_stat_ge-0/0/1_ips": "10.0.0.1",
        "if_stat_ge-0/0/2_ips": "10.0.0.2",
    }

    records = GatewayStatsExporter._analyze_device_ip_conflicts(row, index=0)

    assert len(records) == 2
    assert {record["port_name"] for record in records} == {"ge-0/0/0", "ge-0/0/1"}
    assert all(record["port_ip"] == "10.0.0.1" for record in records)


def test_analyze_device_ip_conflicts_uses_fallback_name_when_missing() -> None:
    """Missing device_name/name should fall back to 'Device_<index>'."""
    _configure_dependencies()

    row = {
        "if_stat_ge-0/0/0_ips": "10.0.0.1",
        "if_stat_ge-0/0/1_ips": "10.0.0.1",
    }

    records = GatewayStatsExporter._analyze_device_ip_conflicts(row, index=7)

    assert all(record["device_name"] == "Device_7" for record in records)


def test_analyze_all_gateway_conflicts_aggregates_per_row() -> None:
    """Multi-row scanner should return the union of per-row conflict records."""
    _configure_dependencies()

    rows = [
        {
            "device_name": "gw-1",
            "if_stat_ge-0/0/0_ips": "10.0.0.1",
            "if_stat_ge-0/0/1_ips": "10.0.0.1",
        },
        {
            "device_name": "gw-2",
            "if_stat_ge-0/0/0_ips": "10.0.0.2",
        },
    ]

    conflicts = GatewayStatsExporter._analyze_all_gateway_conflicts(rows)

    assert len(conflicts) == 2
    assert {record["device_name"] for record in conflicts} == {"gw-1"}  # only gw-1 has duplicate ports


# -------------------------- _load_gateway_stats_for_conflicts --------------------------


def test_load_gateway_stats_reads_csv_rows(tmp_path: Path) -> None:
    """CSV reader should return list of dict rows on success."""
    _configure_dependencies()

    csv_file = tmp_path / "stats.csv"
    with open(csv_file, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["device_name", "if_stat_ge-0/0/0_ips"])
        writer.writeheader()
        writer.writerow({"device_name": "gw-1", "if_stat_ge-0/0/0_ips": "10.0.0.1"})

    module.FilePathUtils = SimpleNamespace(get_csv_path=MagicMock(return_value=str(csv_file)))
    module.CacheUtils = SimpleNamespace(check_and_generate_csv=MagicMock(return_value=True))

    rows = GatewayStatsExporter._load_gateway_stats_for_conflicts()

    assert rows == [{"device_name": "gw-1", "if_stat_ge-0/0/0_ips": "10.0.0.1"}]


def test_load_gateway_stats_returns_none_on_failure(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Missing/unreadable file should return None and log an error banner."""
    _configure_dependencies()

    module.FilePathUtils = SimpleNamespace(get_csv_path=MagicMock(return_value="/no/such/path/nowhere.csv"))
    module.CacheUtils = SimpleNamespace(check_and_generate_csv=MagicMock(return_value=False))

    with caplog.at_level(logging.INFO):
        result = GatewayStatsExporter._load_gateway_stats_for_conflicts()

    assert result is None
    messages = [record.getMessage() for record in caplog.records]
    assert any("Failed to load" in message for message in messages)


# -------------------------- _fetch_one_device_stats retry loop --------------------------


def test_fetch_one_device_stats_success_first_try() -> None:
    """First attempt success should return enriched stats without sleeping."""
    _configure_dependencies()

    with (
        patch.object(module, "_attempt_fetch_stats", return_value={"cpu": 0.1}),
        patch.object(time, "sleep") as sleep_mock,
    ):
        result = GatewayStatsExporter._fetch_one_device_stats(("site-1", "dev-1", "gw", "Site A"), fast=True)

    assert result == {"cpu": 0.1}
    sleep_mock.assert_not_called()


def test_fetch_one_device_stats_retry_then_success() -> None:
    """Transient error should trigger retry then return success on second attempt."""
    _configure_dependencies()

    attempts = MagicMock(side_effect=[RuntimeError("boom"), {"cpu": 0.2}])
    with patch.object(module, "_attempt_fetch_stats", attempts), patch.object(time, "sleep") as sleep_mock:
        result = GatewayStatsExporter._fetch_one_device_stats(("site-1", "dev-1", "gw", "Site A"), fast=True)

    assert result == {"cpu": 0.2}
    sleep_mock.assert_called_once()  # WHY: exactly one backoff between attempts.


def test_fetch_one_device_stats_terminal_failure_returns_failure_record() -> None:
    """Exhausted retries should return legacy failure record with status='failed'."""
    _configure_dependencies()

    with (
        patch.object(module, "_attempt_fetch_stats", side_effect=RuntimeError("boom")),
        patch.object(time, "sleep"),
    ):
        result = GatewayStatsExporter._fetch_one_device_stats(("site-1", "dev-1", "gw", "Site A"), fast=True)

    assert result["status"] == STATUS_FAILED
    assert result["error"] == "boom"


# -------------------------- _process_devices_sequential --------------------------


def test_process_devices_sequential_collects_successful_rows() -> None:
    """Sequential loop should call fetch once per device and skip empty results."""
    _configure_dependencies()

    devices = [
        ("site-1", "dev-1", "gw-1", "Site A"),
        ("site-2", "dev-2", "gw-2", "Site B"),
    ]

    fetch_mock = MagicMock(side_effect=[{"cpu": 0.1}, None])  # WHY: second call returns falsy.
    with patch.object(GatewayStatsExporter, "_fetch_one_device_stats", fetch_mock):
        result = GatewayStatsExporter._process_devices_sequential(devices, fast=False)

    assert result == [{"cpu": 0.1}]  # WHY: None result is filtered.
    assert fetch_mock.call_count == 2
