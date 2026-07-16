"""Unit tests for src.export.wifi_clients_exporter.

Wave 13 P2 coverage lift — extends coverage to include exception guards
(execute + resolve_site_name), placeholder + empty-merge branches, the
prompt-hit path in _ensure_site_selected, orphan session row synthesis,
and the pure helpers (_index_sessions_by_mac, _scan_site_list_for_name,
_attach_latest_session zero-session path).
"""

from __future__ import annotations  # WHY: postponed annotations keep forward refs cheap under strict typing.

import csv  # WHY: build CSV placeholders inline to verify _write_no_data_placeholder output shape.
import os  # WHY: mkdir/write temporary fixture files under tests/fixtures for CSV-backed helpers.
from pathlib import Path  # WHY: build platform-neutral tmp_path strings for CSV fixtures under pytest tmp_path.
from typing import Any  # WHY: annotate mixed-value dict literals so mypy --strict accepts str/int co-occurrence.
from unittest.mock import MagicMock  # WHY: MagicMock stubs give per-test isolation without ceremony.

from src.export.wifi_clients_exporter import (
    WifiClientsExporter,  # WHY: subject under test — orchestrator dataclass.
    _SiteStamp,  # WHY: dataclass used by helpers below to construct stamp arguments.
)


def _build_exporter() -> tuple[WifiClientsExporter, MagicMock, MagicMock, MagicMock]:
    """Create exporter with mocked dependencies."""
    cache_utils = MagicMock()
    org_site_exporter = MagicMock()
    prompt_utils = MagicMock()
    file_path_utils = MagicMock()
    data_processing_utils = MagicMock()
    data_exporter = MagicMock()
    mistapi_module = MagicMock()
    apisession = MagicMock()
    exporter = WifiClientsExporter(
        cache_utils=cache_utils,
        org_site_exporter=org_site_exporter,
        prompt_utils=prompt_utils,
        file_path_utils=file_path_utils,
        data_processing_utils=data_processing_utils,
        data_exporter=data_exporter,
        mistapi_module=mistapi_module,
        apisession=apisession,
    )
    return exporter, prompt_utils, mistapi_module, data_exporter


def test_execute_aborts_when_no_site_selected() -> None:
    """Exporter should return early when site selection is cancelled."""
    exporter, prompt_utils, _mistapi, data_exporter = _build_exporter()
    prompt_utils.select_site_id_from_csv.return_value = None

    exporter.execute(site_id=None)

    data_exporter.write_with_format_selection.assert_not_called()


def test_execute_exports_merged_records() -> None:
    """Exporter should merge client/session data and write output."""
    exporter, _prompt_utils, mistapi_module, data_exporter = _build_exporter()
    exporter.file_path_utils.get_csv_path.return_value = "tests/fixtures/site_list.csv"
    exporter.data_processing_utils.flatten_nested_fields.side_effect = lambda value: value
    exporter.data_processing_utils.escape_multiline.side_effect = lambda value: value

    client_response = MagicMock()
    session_response = MagicMock()
    mistapi_module.api.v1.sites.clients.searchSiteWirelessClients.return_value = client_response
    mistapi_module.api.v1.sites.clients.searchSiteWirelessClientSessions.return_value = session_response
    mistapi_module.get_all.side_effect = [
        [{"mac": "aa:bb:cc:dd:ee:ff", "hostname": "client-1"}],
        [{"mac": "aa:bb:cc:dd:ee:ff", "start_time": 10}],
    ]

    os.makedirs("tests/fixtures", exist_ok=True)
    with open("tests/fixtures/site_list.csv", "w", encoding="utf-8") as file_handle:
        file_handle.write("id,name\nsite-1,Site One\n")

    exporter.execute(site_id="site-1")

    data_exporter.write_with_format_selection.assert_called_once()


def test_execute_logs_failure_when_pipeline_raises(capsys, caplog) -> None:
    """execute() should log + print the operator-facing failure line when the pipeline raises."""
    exporter, _prompt_utils, mistapi_module, data_exporter = _build_exporter()
    exporter.file_path_utils.get_csv_path.return_value = "tests/fixtures/site_list.csv"  # WHY: prevent lookup crash
    mistapi_module.api.v1.sites.clients.searchSiteWirelessClients.side_effect = RuntimeError("api boom")
    os.makedirs("tests/fixtures", exist_ok=True)  # WHY: ensure fixture dir exists for the CSV read
    with open("tests/fixtures/site_list.csv", "w", encoding="utf-8") as file_handle:  # WHY: minimal SiteList
        file_handle.write("id,name\nsite-1,Site One\n")

    with caplog.at_level("ERROR"):
        exporter.execute(site_id="site-1")

    data_exporter.write_with_format_selection.assert_not_called()  # WHY: pipeline aborted before final write
    assert "Failed to fetch WiFi data" in capsys.readouterr().out  # WHY: legacy operator-facing failure text
    assert any("Failed to fetch WiFi data" in rec.message for rec in caplog.records)  # WHY: log captured


def test_execute_writes_placeholder_when_no_data(tmp_path: Path) -> None:
    """execute() should write the no-data placeholder CSV when both datasets are empty."""
    exporter, _prompt_utils, mistapi_module, data_exporter = _build_exporter()
    placeholder_path = tmp_path / "SiteWiFiClients.CSV"  # WHY: placeholder written via file_path_utils.get_csv_path
    exporter.file_path_utils.get_csv_path.return_value = str(placeholder_path)  # WHY: route path for both lookups
    mistapi_module.get_all.return_value = []  # WHY: empty datasets trigger the placeholder branch

    exporter.execute(site_id="site-1")

    data_exporter.write_with_format_selection.assert_not_called()  # WHY: no final write when placeholder path taken
    assert placeholder_path.exists()  # WHY: placeholder artifact must be written to disk
    contents = placeholder_path.read_text(encoding="utf-8")
    assert "No WiFi clients or sessions found" in contents  # WHY: placeholder message body
    assert "site-1" in contents  # WHY: site id stamped in placeholder body row


def test_execute_logs_empty_merge_when_no_enriched_rows(tmp_path: Path, capsys) -> None:
    """execute() should log + print the empty-merge banner when merge produces zero rows."""
    exporter, _prompt_utils, mistapi_module, data_exporter = _build_exporter()
    exporter.file_path_utils.get_csv_path.return_value = str(tmp_path / "site_list.csv")  # WHY: unused; safe path
    exporter.data_processing_utils.flatten_nested_fields.side_effect = lambda value: value
    exporter.data_processing_utils.escape_multiline.side_effect = lambda value: value
    # WHY: return sessions with no MAC (skipped) and no clients — merge produces zero rows.
    mistapi_module.get_all.side_effect = [
        [],  # WHY: zero clients so client_pass produces empty enriched list
        [{"start_time": 1}],  # WHY: session without MAC — orphan pass skips it
    ]

    exporter.execute(site_id="site-1")

    data_exporter.write_with_format_selection.assert_not_called()  # WHY: empty-merge aborts before final write
    assert "No data to export after processing" in capsys.readouterr().out  # WHY: legacy empty-merge banner


def test_ensure_site_selected_returns_prompt_choice() -> None:
    """_ensure_site_selected should return operator-chosen site id when prompt succeeds."""
    exporter, prompt_utils, _mistapi, _data_exporter = _build_exporter()
    prompt_utils.select_site_id_from_csv.return_value = "picked-site"  # WHY: exercise the returned-chosen branch

    resolved = exporter._ensure_site_selected(None)  # WHY: no supplied id -> prompt path

    assert resolved == "picked-site"  # WHY: return the operator's prompt choice verbatim


def test_resolve_site_name_handles_exception(caplog) -> None:
    """_resolve_site_name should fall back to Unknown Site and log a warning when lookup fails."""
    exporter, _prompt_utils, _mistapi, _data_exporter = _build_exporter()
    exporter.file_path_utils.get_csv_path.side_effect = RuntimeError("path boom")  # WHY: force the except branch

    with caplog.at_level("WARNING"):
        resolved = exporter._resolve_site_name("site-x")

    assert resolved == "Unknown Site"  # WHY: fallback preserved when lookup fails
    assert any("Failed to load site name" in rec.message for rec in caplog.records)  # WHY: warning log captured


def test_scan_site_list_for_name_returns_unknown_when_no_match(tmp_path: Path) -> None:
    """_scan_site_list_for_name should return 'Unknown Site' when no row matches the site_id."""
    csv_path = tmp_path / "SiteList.csv"  # WHY: build a fixture CSV with a non-matching row
    csv_path.write_text("id,name\nother-site,Other\n", encoding="utf-8")

    resolved = WifiClientsExporter._scan_site_list_for_name(str(csv_path), "missing-site")

    assert resolved == "Unknown Site"  # WHY: fallback when scan finds no matching row


def test_index_sessions_by_mac_returns_empty_for_no_sessions() -> None:
    """_index_sessions_by_mac should return an empty map when the sessions list is empty."""
    assert WifiClientsExporter._index_sessions_by_mac([]) == {}  # WHY: fast-path branch for empty input


def test_index_sessions_by_mac_buckets_by_mac() -> None:
    """_index_sessions_by_mac should bucket sessions into MAC-keyed lists."""
    sessions: list[dict[str, Any]] = [
        {"mac": "aa:bb", "start_time": 1},  # WHY: two sessions for same MAC exercise bucket-append
        {"mac": "aa:bb", "start_time": 2},
        {"mac": "cc:dd", "start_time": 3},  # WHY: distinct MAC produces separate bucket
        {"start_time": 4},  # WHY: missing MAC — must be skipped to hit the guard branch
    ]

    indexed = WifiClientsExporter._index_sessions_by_mac(sessions)

    assert set(indexed.keys()) == {"aa:bb", "cc:dd"}  # WHY: only entries with MAC produce buckets
    assert len(indexed["aa:bb"]) == 2  # WHY: two sessions grouped into one bucket


def test_merge_client_pass_returns_empty_for_no_clients() -> None:
    """_merge_client_pass should return an empty list without logging when clients is empty."""
    result = WifiClientsExporter._merge_client_pass(
        clients=[],
        sessions_by_mac={},
        processed_macs=set(),
        stamp=_SiteStamp("site-1", "Site One"),
    )

    assert result == []  # WHY: fast-path branch returns empty accumulator


def test_merge_session_only_pass_returns_when_no_sessions() -> None:
    """_merge_session_only_pass should return early when sessions is empty."""
    enriched: list[dict[str, Any]] = []
    WifiClientsExporter._merge_session_only_pass(
        sessions=[],
        processed_macs=set(),
        enriched=enriched,
        stamp=_SiteStamp("site-1", "Site One"),
    )

    assert enriched == []  # WHY: no sessions -> no rows appended


def test_merge_session_only_pass_appends_orphan_rows() -> None:
    """_merge_session_only_pass should append synthetic rows for orphan MACs not in processed set."""
    enriched: list[dict[str, Any]] = []
    sessions: list[dict[str, Any]] = [
        {"mac": "aa:bb", "start_time": 1, "duration": 10},  # WHY: unprocessed MAC -> synthesized row
        {"mac": "cc:dd", "start_time": 2},  # WHY: already processed MAC -> skipped
        {"start_time": 5},  # WHY: no MAC -> guard branch skips
    ]

    WifiClientsExporter._merge_session_only_pass(
        sessions=sessions,
        processed_macs={"cc:dd"},  # WHY: seed a processed MAC to exercise the skip guard
        enriched=enriched,
        stamp=_SiteStamp("site-1", "Site One"),
    )

    assert len(enriched) == 1  # WHY: only the unprocessed MAC produced an orphan row
    row = enriched[0]
    assert row["site_id"] == "site-1"  # WHY: meta key preserved (not prefixed)
    assert row["site_name"] == "Site One"  # WHY: meta key preserved
    assert row["data_source"] == "session_only"  # WHY: provenance marker for orphan rows
    assert row["session_count"] == 1  # WHY: orphan rows always report exactly one session
    assert row["session_start_time"] == 1  # WHY: non-meta keys prefixed with session_
    assert row["session_duration"] == 10  # WHY: non-meta keys prefixed with session_


def test_attach_latest_session_records_zero_when_no_sessions() -> None:
    """_attach_latest_session should record session_count=0 when no matching sessions exist."""
    client: dict[str, Any] = {"mac": "aa:bb", "hostname": "client-1"}  # WHY: mac has no bucket in sessions_by_mac

    WifiClientsExporter._attach_latest_session(
        client=client,
        sessions_by_mac={},
        processed_macs=set(),
    )

    assert client["session_count"] == 0  # WHY: explicit zero preserved when no session data exists


def test_write_no_data_placeholder_writes_header_and_row(tmp_path: Path) -> None:
    """_write_no_data_placeholder should write a two-row CSV with header + sentinel body row."""
    exporter, _prompt_utils, _mistapi, _data_exporter = _build_exporter()
    placeholder = tmp_path / "SiteWiFiClients.CSV"
    exporter.file_path_utils.get_csv_path.return_value = str(placeholder)

    exporter._write_no_data_placeholder(_SiteStamp("site-1", "Site One"))

    with open(placeholder, encoding="utf-8") as file_handle:
        rows = list(csv.reader(file_handle))
    assert rows[0] == ["site_id", "site_name", "message"]  # WHY: fixed schema header expected downstream
    assert rows[1] == ["site-1", "Site One", "No WiFi clients or sessions found"]  # WHY: sentinel body row
