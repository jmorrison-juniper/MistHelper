"""Unit tests for RF diagnostics audit rows."""

from __future__ import annotations  # WHY: keep annotations import-safe.

import csv  # WHY: read back written audit rows.

from src.troubleshooting.rf_diagnostics.audit import RfDiagnosticsAuditWriter  # WHY: test target.
from src.troubleshooting.rf_diagnostics.models import RfDiagnosticRun  # WHY: build audit rows.


def test_audit_writer_appends_one_row_per_run(tmp_path) -> None:
    """The audit writer appends rows without replacing prior runs."""
    writer = RfDiagnosticsAuditWriter(tmp_path / "RfDiagnostics.csv")  # WHY: isolate the audit file.
    first = RfDiagnosticRun("spectrum", "site1", "ap1", "t1", "success", "ok")  # WHY: first audit row.
    second = RfDiagnosticRun("recording", "site1", "mac1", "t2", "failed", "bad")  # WHY: second audit row.
    assert writer.append(first) is True  # WHY: first write should create the file.
    assert writer.append(second) is True  # WHY: second write should append to it.
    with (tmp_path / "RfDiagnostics.csv").open(encoding="utf-8", newline="") as file_handle:  # WHY: read output.
        rows = list(csv.DictReader(file_handle))  # WHY: compare logical rows instead of raw text.
    assert [row["mode"] for row in rows] == ["spectrum", "recording"]  # WHY: one row per run remains.
    assert rows[1]["result_reference"] == "bad"  # WHY: failure detail is preserved.
