"""Extended unit tests for DeviceEvents52wExporter internals.

The pre-existing suite only exercises the empty-result branch. This file
targets the missing coverage on private helpers: paths, checkpoint I/O,
pagination, retry backoff, initial + append writes (CSV and SQLite branches),
and completion logging.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.dataclasses.export_backend_options import ExportBackendOptions
from src.export.device_events_52w_exporter import (
    DeviceEvents52wExporter,
    _first_present,
    _StreamRequest,
    _write_rows,
)


def _build_exporter(**overrides: Any) -> DeviceEvents52wExporter:
    """Construct an exporter with sensible defaults; individual fields can be overridden."""
    defaults: dict[str, Any] = {  # Default mock dependency set matching the frozen exporter fields
        "apisession": MagicMock(name="apisession"),  # Mock authenticated session
        "mistapi": MagicMock(name="mistapi"),  # Mock mistapi module reference
        "org_id": "org-1",  # Non-empty org so guard doesn't fire
        "data_processing_utils": MagicMock(name="data_processing_utils"),  # Flatten/escape helpers
        "data_exporter": MagicMock(name="data_exporter"),  # Backend writer stub
        "output_format": "csv",  # Default CSV branch
        "database_path": "data/mist_data.db",  # SQLite path for completion log
        "logger": MagicMock(name="logger"),  # Structured logger stub
    }
    defaults.update(overrides)  # Allow individual tests to override specific fields
    return DeviceEvents52wExporter(**defaults)  # Build immutable exporter


def test_export_early_exits_when_org_id_missing() -> None:
    """export() must log error and return immediately when org_id is empty."""
    logger = MagicMock()  # Track error log call
    data_exporter = MagicMock()  # Must NOT be invoked when org is missing
    exporter = _build_exporter(org_id="", logger=logger, data_exporter=data_exporter)
    exporter.export()  # Trigger the guarded path
    logger.error.assert_called_once()  # Operator-visible error emitted
    data_exporter.write_with_format_selection.assert_not_called()  # No output emitted


def test_paths_returns_data_dir_paths_and_creates_dir(tmp_path: Path, monkeypatch) -> None:
    """_paths must build data/CSV + per-org checkpoint paths and ensure the data dir exists."""
    monkeypatch.chdir(tmp_path)  # Sandbox the working directory
    exporter = _build_exporter(org_id="org-abc")  # Non-empty org id
    csv_file, checkpoint_file = exporter._paths()  # Trigger the path helper
    assert csv_file.endswith("OrgDeviceEvents_52w.csv")  # CSV filename preserved
    assert checkpoint_file.endswith("OrgDeviceEvents_52w.org-abc.checkpoint")  # Per-org token
    assert (tmp_path / "data").exists()  # Data dir must be created if missing


def test_read_checkpoint_returns_none_when_file_absent(tmp_path: Path) -> None:
    """_read_checkpoint must return None when checkpoint file does not exist."""
    exporter = _build_exporter()  # Default exporter
    missing_path = str(tmp_path / "no_such_checkpoint")  # File deliberately absent
    assert exporter._read_checkpoint(missing_path) is None  # Absent file yields None


def test_read_checkpoint_returns_token_when_file_present(tmp_path: Path) -> None:
    """_read_checkpoint must strip and return the token, logging a resume trace."""
    checkpoint_file = tmp_path / "resume.checkpoint"  # Fixture path
    checkpoint_file.write_text("token-123\n", encoding="utf-8")  # Trailing newline stripped
    logger = MagicMock()  # Capture resume log
    exporter = _build_exporter(logger=logger)
    assert exporter._read_checkpoint(str(checkpoint_file)) == "token-123"  # Stripped
    logger.info.assert_called()  # Resume trace logged


def test_read_checkpoint_returns_none_for_empty_file(tmp_path: Path) -> None:
    """_read_checkpoint must treat an empty file as no checkpoint token."""
    checkpoint_file = tmp_path / "empty.checkpoint"  # Empty file
    checkpoint_file.write_text("", encoding="utf-8")  # Explicit empty content
    exporter = _build_exporter()
    assert exporter._read_checkpoint(str(checkpoint_file)) is None  # Empty yields None


def test_read_checkpoint_handles_read_failure_and_warns(tmp_path: Path) -> None:
    """_read_checkpoint must warn and return None if the file open fails."""
    checkpoint_file = tmp_path / "will_fail.checkpoint"  # Path will exist to bypass guard
    checkpoint_file.write_text("ignored", encoding="utf-8")  # Force existence
    logger = MagicMock()  # Capture warning
    exporter = _build_exporter(logger=logger)
    with patch("builtins.open", side_effect=OSError("boom")):  # Force read to fail
        assert exporter._read_checkpoint(str(checkpoint_file)) is None
    logger.warning.assert_called()  # Non-fatal warn emitted


def test_write_checkpoint_writes_token_to_file(tmp_path: Path) -> None:
    """_write_checkpoint must persist the token verbatim when non-empty."""
    checkpoint_file = tmp_path / "wc.checkpoint"  # Destination
    exporter = _build_exporter()
    exporter._write_checkpoint(str(checkpoint_file), "next-token")  # Persist token
    assert checkpoint_file.read_text(encoding="utf-8") == "next-token"  # Round-trip


def test_write_checkpoint_skips_when_token_is_none(tmp_path: Path) -> None:
    """_write_checkpoint must skip persistence when token is None."""
    checkpoint_file = tmp_path / "skip.checkpoint"  # File must NOT be created
    exporter = _build_exporter()
    exporter._write_checkpoint(str(checkpoint_file), None)  # Guard exercised
    assert not checkpoint_file.exists()  # Nothing written


def test_write_checkpoint_warns_on_write_failure(tmp_path: Path) -> None:
    """_write_checkpoint must warn (non-fatal) when the write itself fails."""
    logger = MagicMock()  # Capture warning
    exporter = _build_exporter(logger=logger)
    with patch("builtins.open", side_effect=OSError("disk full")):  # Force write to fail
        exporter._write_checkpoint(str(tmp_path / "cp"), "tok")  # Should not raise
    logger.warning.assert_called()  # Non-fatal warn emitted


def test_remove_checkpoint_removes_file_when_present(tmp_path: Path) -> None:
    """_remove_checkpoint must delete the checkpoint when present."""
    checkpoint_file = tmp_path / "remove.checkpoint"  # File to be deleted
    checkpoint_file.write_text("token", encoding="utf-8")  # Ensure it exists first
    exporter = _build_exporter()
    exporter._remove_checkpoint(str(checkpoint_file))  # Trigger cleanup
    assert not checkpoint_file.exists()  # File must be removed


def test_remove_checkpoint_skips_when_file_absent(tmp_path: Path) -> None:
    """_remove_checkpoint must be a no-op when file does not exist."""
    exporter = _build_exporter()  # Default exporter
    # Should not raise even though file is absent
    exporter._remove_checkpoint(str(tmp_path / "absent"))  # Guard exercised


def test_remove_checkpoint_logs_debug_on_failure(tmp_path: Path) -> None:
    """_remove_checkpoint must emit a debug breadcrumb on OS-level failure."""
    checkpoint_file = tmp_path / "err.checkpoint"  # Existing file
    checkpoint_file.write_text("token", encoding="utf-8")  # Force existence
    logger = MagicMock()  # Capture debug log
    exporter = _build_exporter(logger=logger)
    with patch("os.remove", side_effect=OSError("locked")):  # Force removal to fail
        exporter._remove_checkpoint(str(checkpoint_file))  # Should not raise
    logger.debug.assert_called()  # Debug breadcrumb emitted


def test_fetch_kwargs_omits_search_after_when_no_token() -> None:
    """_fetch_kwargs must not include search_after when token is None."""
    kwargs = DeviceEvents52wExporter._fetch_kwargs(None, "52w", 1000)  # No token
    assert kwargs == {"device_type": "all", "limit": 1000, "duration": "52w"}  # Exact base kwargs


def test_fetch_kwargs_includes_search_after_when_token_present() -> None:
    """_fetch_kwargs must add search_after key when token is provided."""
    kwargs = DeviceEvents52wExporter._fetch_kwargs("tok", "52w", 500)  # Non-None token
    assert kwargs["search_after"] == "tok"  # Resume token attached


def test_normalize_page_returns_empty_when_no_data() -> None:
    """_normalize_page must return ([], None) when response.data is empty."""
    exporter = _build_exporter()
    empty_response = SimpleNamespace(data=None)  # No payload
    assert exporter._normalize_page(empty_response) == ([], None)  # Guard branch


def test_normalize_page_returns_list_directly() -> None:
    """_normalize_page must return list payload verbatim with no token."""
    exporter = _build_exporter()
    rows = [{"a": 1}]  # List payload skips dict probing
    response = SimpleNamespace(data=rows)
    assert exporter._normalize_page(response) == (rows, None)  # No token on list


def test_normalize_page_extracts_results_and_next_token_from_dict() -> None:
    """_normalize_page must probe results/next keys when payload is a dict."""
    exporter = _build_exporter()
    dict_payload = {"results": [{"row": 1}], "next": "tok"}  # Both keys populated
    response = SimpleNamespace(data=dict_payload)
    assert exporter._normalize_page(response) == ([{"row": 1}], "tok")  # Both extracted


def test_normalize_page_unknown_payload_shape_returns_empty() -> None:
    """_normalize_page must default to empty tuple when payload is an unexpected type."""
    exporter = _build_exporter()
    response = SimpleNamespace(data="unexpected-scalar")  # Not list/dict
    assert exporter._normalize_page(response) == ([], None)


def test_first_present_returns_first_truthy_match() -> None:
    """_first_present must return the first key with a truthy value."""
    payload = {"a": [], "b": "value", "c": "other"}  # 'a' is falsy, 'b' is first truthy
    assert _first_present(payload, ("a", "b", "c"), default="default") == "value"


def test_first_present_returns_default_when_all_missing() -> None:
    """_first_present must return default when no key has a truthy value."""
    assert _first_present({}, ("a", "b"), default=[]) == []  # Empty payload -> default


def test_process_rows_flattens_and_escapes() -> None:
    """_process_rows must call flatten_nested_fields then escape_multiline in order."""
    utils = MagicMock()  # Track call order
    utils.flatten_nested_fields.side_effect = lambda rows: [{"flat": True}]
    utils.escape_multiline.side_effect = lambda rows: [{"escaped": True}]
    exporter = _build_exporter(data_processing_utils=utils)
    result = exporter._process_rows([{"raw": True}])  # Input rows
    utils.flatten_nested_fields.assert_called_once_with([{"raw": True}])  # Flatten first
    utils.escape_multiline.assert_called_once_with([{"flat": True}])  # Escape second
    assert result == [{"escaped": True}]  # Final normalized rows


def test_build_header_returns_unique_keys_and_logs_header_size() -> None:
    """_build_header must return the unique-keys list and log the header size."""
    utils = MagicMock()  # Track get_unique_keys call
    utils.get_unique_keys.return_value = ["timestamp", "type"]  # Frozen header
    logger = MagicMock()  # Capture header log
    exporter = _build_exporter(data_processing_utils=utils, logger=logger)
    header = exporter._build_header([{"timestamp": 1, "type": "x"}])  # Trigger
    assert header == ["timestamp", "type"]  # Verbatim pass-through
    logger.info.assert_called()  # Header size log emitted


def test_write_initial_batch_csv_branch_writes_header_and_rows(tmp_path: Path) -> None:
    """_write_initial_batch (CSV) must truncate file, write header, and emit rows."""
    csv_file = tmp_path / "out.csv"  # Destination CSV path
    exporter = _build_exporter(output_format="csv")  # CSV branch
    header_fields = ["a", "b"]  # Frozen schema
    exporter._write_initial_batch(  # Trigger CSV path
        str(csv_file),
        [{"a": "1", "b": "2"}],
        header_fields,
    )
    contents = csv_file.read_text(encoding="utf-8")  # Verify written CSV
    assert "a,b" in contents  # Header row
    assert "1,2" in contents  # Data row


def test_write_initial_batch_sqlite_branch_dispatches_to_backend() -> None:
    """_write_initial_batch (SQLite) must call data_exporter with backend_options.format_override='sqlite'."""
    data_exporter = MagicMock()  # Track backend call
    exporter = _build_exporter(output_format="sqlite", data_exporter=data_exporter)
    exporter._write_initial_batch("ignored.csv", [{"a": 1}], ["a"])  # Trigger SQLite path
    data_exporter.write_with_format_selection.assert_called_once()  # Backend invoked
    _, kwargs = data_exporter.write_with_format_selection.call_args  # Inspect kwargs
    assert kwargs["api_function_name"] == "searchOrgDeviceEvents"  # PK strategy key
    assert isinstance(kwargs["backend_options"], ExportBackendOptions)  # Options attached
    assert kwargs["backend_options"].format_override == "sqlite"  # Format sentinel set


def test_append_rows_csv_branch_appends_without_header(tmp_path: Path) -> None:
    """_append_rows (CSV) must append rows to an existing CSV without re-writing the header."""
    csv_file = tmp_path / "append.csv"  # Prepopulated with header + first row
    csv_file.write_text("a,b\n1,2\n", encoding="utf-8")  # Pre-existing content
    exporter = _build_exporter(output_format="csv")  # CSV branch
    exporter._append_rows(str(csv_file), [{"a": "3", "b": "4"}], ["a", "b"])  # Append batch
    contents = csv_file.read_text(encoding="utf-8")  # Verify accumulated output
    assert contents.count("a,b\n") == 1  # Only original header remains
    assert "3,4" in contents  # New row appended


def test_append_rows_sqlite_branch_dispatches_to_backend() -> None:
    """_append_rows (SQLite) must call data_exporter with sqlite override."""
    data_exporter = MagicMock()  # Track backend call
    exporter = _build_exporter(output_format="sqlite", data_exporter=data_exporter)
    exporter._append_rows("ignored.csv", [{"a": 1}], ["a"])  # Trigger SQLite path
    data_exporter.write_with_format_selection.assert_called_once()  # Backend invoked


def test_write_rows_restricts_to_header_fields(tmp_path: Path) -> None:
    """_write_rows must write each row limited to header_fields, blanks for missing keys."""
    import csv as _csv  # Standard library csv (aliased to avoid shadowing test-scope names)

    output = tmp_path / "restrict.csv"  # Destination file
    header = ["a", "b", "c"]  # Frozen schema
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = _csv.DictWriter(handle, fieldnames=header)
        writer.writeheader()  # Emit header first
        _write_rows(writer, [{"a": "1", "extra": "ignored"}, {"b": "2"}], header)
    lines = output.read_text(encoding="utf-8").strip().splitlines()
    assert lines[0] == "a,b,c"  # Header row
    assert lines[1] == "1,,"  # Only 'a' populated; 'extra' dropped
    assert lines[2] == ",2,"  # Only 'b' populated


def test_log_completion_csv_branch_logs_csv_file_path() -> None:
    """_log_completion (CSV) must log the CSV completion message with the file path."""
    logger = MagicMock()  # Capture completion log
    exporter = _build_exporter(output_format="csv", logger=logger)
    exporter._log_completion("path/to/output.csv")  # Trigger CSV branch
    logger.info.assert_called()  # Completion line emitted
    args = logger.info.call_args[0]  # Format args
    assert "path/to/output.csv" in args  # File path passed through


def test_log_completion_sqlite_branch_logs_database_path() -> None:
    """_log_completion (SQLite) must log DB path and skip the CSV line."""
    logger = MagicMock()  # Capture completion log
    exporter = _build_exporter(output_format="sqlite", database_path="db/mist.db", logger=logger)
    exporter._log_completion("ignored.csv")  # Trigger SQLite branch
    logger.info.assert_called()  # Completion line emitted
    args = logger.info.call_args[0]  # Format args
    assert "db/mist.db" in args  # DB path passed through


def test_sleep_before_retry_skips_on_final_attempt() -> None:
    """_sleep_before_retry must not sleep when attempt is the last one."""
    exporter = _build_exporter()
    with patch("time.sleep") as sleep_mock:  # Track sleep calls
        exporter._sleep_before_retry(attempt=2, retries=3, backoff=1.0)  # Last attempt
    sleep_mock.assert_not_called()  # Final attempt short-circuits


def test_sleep_before_retry_sleeps_exponentially() -> None:
    """_sleep_before_retry must sleep backoff*2^attempt on non-final attempts."""
    exporter = _build_exporter()
    with patch("time.sleep") as sleep_mock:  # Track sleep calls
        exporter._sleep_before_retry(attempt=0, retries=3, backoff=1.0)  # First attempt
    sleep_mock.assert_called_once_with(1.0)  # 1.0 * 2^0 = 1.0
    with patch("time.sleep") as sleep_mock:  # Second call, reset mock
        exporter._sleep_before_retry(attempt=1, retries=3, backoff=1.0)  # Second attempt
    sleep_mock.assert_called_once_with(2.0)  # 1.0 * 2^1 = 2.0


def test_fetch_with_retries_returns_immediately_on_success() -> None:
    """_fetch_with_retries must return the first-attempt payload with no retries."""
    exporter = _build_exporter()
    with (
        patch.object(DeviceEvents52wExporter, "_fetch_page", return_value="response") as fetch_mock,
        patch.object(DeviceEvents52wExporter, "_sleep_before_retry") as sleep_mock,
    ):
        result = exporter._fetch_with_retries("tok", "52w", 1000)
    assert result == "response"  # First-attempt success
    fetch_mock.assert_called_once()  # No retries needed
    sleep_mock.assert_not_called()  # No backoff needed


def test_fetch_with_retries_reraises_after_all_attempts_fail() -> None:
    """_fetch_with_retries must re-raise the last exception after all retries fail."""
    exporter = _build_exporter()
    boom = RuntimeError("transient")  # Simulated transient error
    with (
        patch.object(DeviceEvents52wExporter, "_fetch_page", side_effect=boom),
        patch.object(DeviceEvents52wExporter, "_sleep_before_retry"),
    ):
        with pytest.raises(RuntimeError, match="transient"):
            exporter._fetch_with_retries("tok", "52w", 1000, retries=2, backoff=0.0)


def test_fetch_with_retries_succeeds_on_second_attempt() -> None:
    """_fetch_with_retries must succeed after a transient first-attempt failure."""
    exporter = _build_exporter()
    side_effects = [RuntimeError("transient"), "ok"]  # Fail then succeed
    with (
        patch.object(DeviceEvents52wExporter, "_fetch_page", side_effect=side_effects),
        patch.object(DeviceEvents52wExporter, "_sleep_before_retry") as sleep_mock,
    ):
        result = exporter._fetch_with_retries("tok", "52w", 1000, retries=3, backoff=0.0)
    assert result == "ok"  # Second attempt returned successfully
    sleep_mock.assert_called_once()  # Sleep between attempts occurred


def test_preload_rows_stops_when_no_results_returned() -> None:
    """_preload_rows must break early when the first page returns no results."""
    exporter = _build_exporter()
    with patch.object(
        DeviceEvents52wExporter,
        "_fetch_page",
        return_value=SimpleNamespace(data={"results": [], "next": "ignored"}),
    ) as fetch_mock:
        rows, token = exporter._preload_rows(1000, "52w", 3, None)  # Trigger preload
    assert rows == []  # No rows accumulated
    # WHY: _preload_rows assigns next_token BEFORE the empty-results break, so the
    # last-seen continuation token propagates even when the page yielded no rows.
    assert token == "ignored"  # Preserved token from the normalized-page tuple
    assert fetch_mock.call_count == 1  # Broke after first empty page


def test_preload_rows_stops_when_next_token_absent() -> None:
    """_preload_rows must break after processing a page with no continuation token."""
    exporter = _build_exporter()
    exporter.data_processing_utils.flatten_nested_fields.side_effect = lambda rows: rows
    exporter.data_processing_utils.escape_multiline.side_effect = lambda rows: rows
    response = SimpleNamespace(data={"results": [{"row": 1}]})  # No 'next' key
    with patch.object(DeviceEvents52wExporter, "_fetch_page", return_value=response) as fetch_mock:
        rows, token = exporter._preload_rows(1000, "52w", 3, None)  # Trigger
    assert rows == [{"row": 1}]  # Page rows buffered
    assert token is None  # No continuation
    assert fetch_mock.call_count == 1  # Broke after processing this page


def test_preload_rows_advances_search_after_across_pages() -> None:
    """_preload_rows must advance search_after between pages until preload_pages exhausted."""
    exporter = _build_exporter()
    exporter.data_processing_utils.flatten_nested_fields.side_effect = lambda rows: rows
    exporter.data_processing_utils.escape_multiline.side_effect = lambda rows: rows
    responses = [  # Two pages then break (no next token on final page)
        SimpleNamespace(data={"results": [{"row": 1}], "next": "tok-a"}),
        SimpleNamespace(data={"results": [{"row": 2}], "next": "tok-b"}),
    ]
    with patch.object(DeviceEvents52wExporter, "_fetch_page", side_effect=responses) as fetch_mock:
        rows, token = exporter._preload_rows(1000, "52w", 2, None)  # Preload 2 pages
    assert rows == [{"row": 1}, {"row": 2}]  # Both pages buffered
    assert token == "tok-b"  # Last-seen continuation token returned
    assert fetch_mock.call_count == 2  # Fetched exactly preload_pages times


def test_stream_remaining_pages_writes_appends_and_checkpoints() -> None:
    """_stream_remaining_pages must append rows and persist checkpoint until token is exhausted."""
    exporter = _build_exporter(output_format="csv")
    exporter.data_processing_utils.flatten_nested_fields.side_effect = lambda rows: rows
    exporter.data_processing_utils.escape_multiline.side_effect = lambda rows: rows
    responses = [  # Two pages then empty page to break
        SimpleNamespace(data={"results": [{"row": 2}], "next": "tok-b"}),
        SimpleNamespace(data={"results": [{"row": 3}]}),  # No next token
    ]
    with (
        patch.object(DeviceEvents52wExporter, "_fetch_with_retries", side_effect=responses),
        patch.object(DeviceEvents52wExporter, "_append_rows") as append_mock,
        patch.object(DeviceEvents52wExporter, "_write_checkpoint") as ckpt_mock,
    ):
        exporter._stream_remaining_pages(
            _StreamRequest(
                next_token="tok-a",  # Seed continuation token
                duration="52w",
                limit=1000,
                csv_file="out.csv",
                header_fields=["row"],
                checkpoint_file="cp.txt",
            )
        )
    assert append_mock.call_count == 2  # Two pages appended
    assert ckpt_mock.call_count == 2  # Checkpoint written after each page


def test_stream_remaining_pages_breaks_on_empty_results() -> None:
    """_stream_remaining_pages must break out of the loop when a page yields no results."""
    exporter = _build_exporter(output_format="csv")
    exporter.data_processing_utils.flatten_nested_fields.side_effect = lambda rows: rows
    exporter.data_processing_utils.escape_multiline.side_effect = lambda rows: rows
    empty_response = SimpleNamespace(data={"results": [], "next": "should-be-ignored"})
    with (
        patch.object(DeviceEvents52wExporter, "_fetch_with_retries", return_value=empty_response),
        patch.object(DeviceEvents52wExporter, "_append_rows") as append_mock,
    ):
        exporter._stream_remaining_pages(
            _StreamRequest(
                next_token="tok-a",
                duration="52w",
                limit=1000,
                csv_file="out.csv",
                header_fields=["row"],
                checkpoint_file="cp.txt",
            )
        )
    append_mock.assert_not_called()  # Empty page short-circuits before append


def test_export_full_happy_path_calls_streaming_pipeline(tmp_path: Path, monkeypatch) -> None:
    """export() must invoke preload -> initial batch -> streaming -> completion when rows exist."""
    monkeypatch.chdir(tmp_path)  # Sandbox CWD so 'data/' is created here
    utils = MagicMock()  # data_processing_utils stub
    utils.flatten_nested_fields.side_effect = lambda rows: rows
    utils.escape_multiline.side_effect = lambda rows: rows
    utils.get_unique_keys.return_value = ["timestamp", "type"]  # Header fields
    mistapi = MagicMock()
    mistapi.api.v1.orgs.devices.searchOrgDeviceEvents.side_effect = [  # Two pages of results
        SimpleNamespace(data={"results": [{"timestamp": 1, "type": "e1"}], "next": "tok-a"}),
        SimpleNamespace(data={"results": [{"timestamp": 2, "type": "e2"}]}),  # No next token
    ]
    logger = MagicMock()  # Capture completion log
    exporter = _build_exporter(
        mistapi=mistapi,
        data_processing_utils=utils,
        output_format="csv",
        logger=logger,
    )
    exporter.export()  # Trigger full export
    logger.info.assert_called()  # Completion log emitted
    assert (tmp_path / "data" / "OrgDeviceEvents_52w.csv").exists()  # CSV output produced


def test_export_empty_result_branch_writes_zero_rows_and_returns(tmp_path: Path, monkeypatch) -> None:
    """export() must short-circuit via _handle_empty_result when no rows found."""
    monkeypatch.chdir(tmp_path)
    utils = MagicMock()
    utils.flatten_nested_fields.side_effect = lambda rows: rows
    utils.escape_multiline.side_effect = lambda rows: rows
    mistapi = MagicMock()
    mistapi.api.v1.orgs.devices.searchOrgDeviceEvents.return_value = SimpleNamespace(data={"results": []})
    data_exporter = MagicMock()
    exporter = _build_exporter(mistapi=mistapi, data_processing_utils=utils, data_exporter=data_exporter)
    exporter.export()  # Trigger empty-result branch
    data_exporter.write_with_format_selection.assert_called_once_with([], "OrgDeviceEvents_52w.csv")
