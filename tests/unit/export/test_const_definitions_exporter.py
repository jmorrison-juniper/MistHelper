"""Unit tests for src.export.const_definitions_exporter."""

from __future__ import annotations

import os
import time
from unittest.mock import MagicMock

from src.export.const_definitions_exporter import ConstDefinitionsExporter


def _build_exporter() -> ConstDefinitionsExporter:
    """Create exporter with mocked dependencies for isolated tests."""
    return ConstDefinitionsExporter(
        apisession=MagicMock(),
        data_exporter=MagicMock(),
        escape_multiline_strings_for_csv=lambda rows: rows,
    )


def test_payload_to_rows_flattens_insight_metrics() -> None:
    """Insight metrics payload should flatten interval/report fields into strings."""
    exporter = _build_exporter()
    payload = {
        "metric_one": {
            "description": "desc",
            "type": "number",
            "unit": "ms",
            "scopes": ["site", "client"],
            "report_scopes": ["org"],
            "intervals": {"last_minute": {"interval": 60, "max_age": 600}},
            "report_intervals": {"daily": {"interval": 86400}},
        }
    }

    rows = exporter._payload_to_rows("insight_metrics", payload)

    assert len(rows) == 1
    assert rows[0]["metric_name"] == "metric_one"
    assert "last_minute(60s, max_age:600s)" in rows[0]["intervals"]
    assert "daily(86400s)" in rows[0]["report_intervals"]


def test_is_output_fresh_returns_true_for_recent_file(tmp_path, monkeypatch) -> None:
    """Fresh file should skip API work when age is below threshold."""
    exporter = _build_exporter()
    exporter.cache_max_age_hours = 24
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    file_path = data_dir / "ConstTest.csv"
    file_path.write_text("header\n", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    is_fresh = exporter._is_output_fresh("ConstTest.csv", "test")

    assert is_fresh is True


def test_is_output_fresh_returns_false_for_stale_file(tmp_path, monkeypatch) -> None:
    """Stale file should force API fetch when age exceeds threshold."""
    exporter = _build_exporter()
    exporter.cache_max_age_hours = 24
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    file_path = data_dir / "ConstTest.csv"
    file_path.write_text("header\n", encoding="utf-8")
    stale_timestamp = time.time() - (25 * 3600)
    os.utime(file_path, (stale_timestamp, stale_timestamp))

    monkeypatch.chdir(tmp_path)
    is_fresh = exporter._is_output_fresh("ConstTest.csv", "test")

    assert is_fresh is False


def test_process_endpoint_writes_rows_when_not_fresh() -> None:
    """Endpoint processing should save transformed rows when fetch succeeds."""
    exporter = _build_exporter()
    exporter._is_output_fresh = MagicMock(return_value=False)
    exporter._fetch_rows_for_endpoint = MagicMock(return_value=[{"name": "abc"}])

    counters = {"processed": 0, "skipped_fresh": 0, "updated": 0, "failed": 0}
    exporter._process_endpoint(
        "test_endpoint",
        {
            "filename": "ConstTest.csv",
            "description": "Test Definitions",
            "module": MagicMock(),
            "function": "listTest",
            "special_handling": None,
        },
        counters,
    )

    exporter.data_exporter.save_data_to_output.assert_called_once_with([{"name": "abc"}], "ConstTest.csv")
    assert counters["processed"] == 1
    assert counters["updated"] == 1
