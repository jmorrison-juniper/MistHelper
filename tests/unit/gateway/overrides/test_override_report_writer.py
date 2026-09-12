"""Wave 6 P2 coverage for ``src.gateway.overrides.override_report_writer.OverrideReportWriter``.

Covers ``write_empty``, ``write_full``, ``_log_summary``, ``_print_summary``,
and ``_print_summary_lines``. All ``_deps`` module-level slots are patched
directly with ``MagicMock(spec=…)`` per project mandatory mock policy;
no live network or MistHelper import is exercised.
"""

from __future__ import annotations  # WHY: PEP 604 unions in test annotations.

import csv  # WHY: verify header-only CSV round-trip in write_empty.
import logging  # WHY: caplog verification of the legacy info log lines.
from pathlib import Path  # WHY: type-safe tmp_path writes for the empty CSV.
from typing import Any  # WHY: dict typing mirroring SUT.
from unittest.mock import MagicMock, patch  # WHY: mandatory spec= mocks.

import pytest  # WHY: caplog fixture for legacy operator log verification.

from src.gateway.overrides import _deps  # WHY: patch module-level DI slots directly.
from src.gateway.overrides.override_report_writer import (  # WHY: SUT direct import.
    _EMPTY_FIELDNAMES,
    OUTPUT_FILENAME,
    OverrideReportWriter,
)


class TestWriteEmpty:
    """Cover the header-only fast path."""

    def test_writes_header_only_csv(self, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
        """Header row is written; no data rows; legacy operator lines routed via logger."""
        # WHY: exercises the file-open+DictWriter branch and both logging.info() operator calls.
        output_path = tmp_path / OUTPUT_FILENAME  # Route the writer to the tmp path.
        fake_file_path_utils = MagicMock(spec=["get_csv_path"])  # Minimal spec attr surface.
        fake_file_path_utils.get_csv_path.return_value = str(output_path)  # Redirect writes.
        with (
            patch.object(_deps, "FilePathUtils", fake_file_path_utils),  # Inject DI slot.
            caplog.at_level(logging.INFO, logger="root"),  # Capture operator log lines.
        ):
            OverrideReportWriter.write_empty()  # Trigger the empty write.
        fake_file_path_utils.get_csv_path.assert_called_once_with(OUTPUT_FILENAME)  # Verified path resolution.
        # Verify header-only content.
        with open(output_path, newline="", encoding="utf-8") as csvfile:  # Read the written CSV back.
            rows = list(csv.reader(csvfile))  # Load all rows.
        assert rows == [_EMPTY_FIELDNAMES]  # Only the header row is present.
        # Verify legacy operator output routed via logger.
        stdout = "\n".join(record.getMessage() for record in caplog.records)  # Aggregate log messages.
        assert f"! Gateway override report written to {OUTPUT_FILENAME}" in stdout  # Legacy line 1.
        assert "compliant with their assigned templates" in stdout  # Legacy line 2 substring.


class TestWriteFull:
    """Cover the multi-entry path that delegates to DataExporter and prints the summary block."""

    def test_delegates_to_data_exporter_and_prints_summary(self, caplog: pytest.LogCaptureFixture) -> None:
        """DataExporter is called with entries + filename; log + summary lines emitted."""
        # WHY: exercises DataExporter dispatch, _log_summary, and _print_summary_lines together.
        entries: list[dict[str, Any]] = [  # Two entries sharing one device_id -> distinct-device count = 1.
            {"device_id": "dev-1", "port_name": "ge-0/0/0"},
            {"device_id": "dev-1", "port_name": "ge-0/0/1"},
        ]
        fake_data_exporter = MagicMock(spec=["write_with_format_selection"])  # Minimal spec.
        with (
            patch.object(_deps, "DataExporter", fake_data_exporter),  # Redirect writer.
            caplog.at_level(logging.INFO, logger="root"),  # Capture info logs.
        ):
            OverrideReportWriter.write_full(
                entries=entries,
                total_gateways=10,
                devices_with_overrides_count=1,
                target_ports=["ge-0/0/0", "ge-0/0/1"],
            )
        fake_data_exporter.write_with_format_selection.assert_called_once_with(entries, OUTPUT_FILENAME)  # Deleg.
        stdout = "\n".join(record.getMessage() for record in caplog.records)  # Aggregate log output.
        assert f"! Gateway override report written to {OUTPUT_FILENAME}" in stdout  # Console line 1.
        assert "Found 2 overridden ports across 1 of 10" in stdout  # Console line 2 (distinct-device math).
        assert "Only fetched live data for 1 devices" in stdout  # Console line 3 (API optimization).
        assert "saved 9 unnecessary API calls" in stdout  # Saved-calls math (10-1).
        assert "Target ports analyzed: ge-0/0/0, ge-0/0/1" in stdout  # Console line 4.
        assert "outliers that may need correction" in stdout  # Console line 5.
        # Verify structured logs (both info lines).
        assert any("Writing 2 override entries" in rec.message for rec in caplog.records)  # Before-action log.
        assert any("with 2 overridden ports from 1 gateway" in rec.getMessage() for rec in caplog.records)  # Sum.
        assert any("API Optimization" in rec.getMessage() for rec in caplog.records)  # Optimization log.

    def test_empty_entries_zero_gateways_and_repeats_compliant_line(self, caplog: pytest.LogCaptureFixture) -> None:
        """Zero-entry write_full path exercises the `entries else 0` branch + compliant repeat."""
        # WHY: covers the False branch of `if entries` in _log_summary and _print_summary,
        # plus the `if total_overridden_ports == 0` repeat-compliant branch in _print_summary_lines.
        fake_data_exporter = MagicMock(spec=["write_with_format_selection"])  # Stub exporter.
        with (
            patch.object(_deps, "DataExporter", fake_data_exporter),
            caplog.at_level(logging.INFO, logger="root"),  # Capture info logs.
        ):
            OverrideReportWriter.write_full(
                entries=[],
                total_gateways=5,
                devices_with_overrides_count=0,
                target_ports=["ge-0/0/0"],
            )
        stdout = "\n".join(record.getMessage() for record in caplog.records)  # Aggregate log output.
        assert "Found 0 overridden ports across 0 of 5" in stdout  # Zero-entry summary line.
        assert "compliant with their assigned templates" in stdout  # Repeated compliant message.


class TestLogSummary:
    """Directly exercise ``_log_summary`` to nail down both branches of the `if entries` guard."""

    def test_empty_entries_logs_zero_gateways(self, caplog: pytest.LogCaptureFixture) -> None:
        """Empty entries -> gateways_with_overrides logged as 0."""
        # WHY: hits the False branch of `if entries` inside _log_summary.
        with caplog.at_level(logging.INFO, logger="root"):
            OverrideReportWriter._log_summary(entries=[], total_gateways=3, devices_with_overrides_count=0)
        assert any("0 gateway devices" in rec.getMessage() for rec in caplog.records)  # Zero-gateway line.


class TestPrintSummary:
    """Directly exercise ``_print_summary`` to verify the distinct-device math parity."""

    def test_distinct_devices_computed_from_entries(self, caplog: pytest.LogCaptureFixture) -> None:
        """Distinct device_id count drives the summary numerator."""
        # WHY: exercises the True branch of the `if entries else 0` guard in _print_summary.
        entries: list[dict[str, Any]] = [  # Three entries, two distinct device_ids.
            {"device_id": "a"},
            {"device_id": "a"},
            {"device_id": "b"},
        ]
        with caplog.at_level(logging.INFO, logger="root"):  # Capture info logs.
            OverrideReportWriter._print_summary(
                entries=entries,
                total_gateways=7,
                devices_with_overrides_count=2,
                target_ports=["ge-0/0/0"],
            )
        stdout = "\n".join(record.getMessage() for record in caplog.records)  # Aggregate log output.
        assert "Found 3 overridden ports across 2 of 7" in stdout  # Two distinct devices, three ports.
