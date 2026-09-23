"""Unit tests for the pure portal harness logic."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from portal_harness import (
    classify_select_state,
    classify_terminal_defects,
    parse_log_phase_timing,
    reconcile_verdict,
)


def test_log_phase_parser_matches_interleaved_lines() -> None:
    """The parser uses content markers, not adjacent line positions."""
    lines = [
        "2026-09-23 08:00:00,000 INFO Output scan marks the run start for /app/data",
        "2026-09-23 08:00:00,100 INFO another thread starts work",
        "2026-09-23 08:00:02,000 INFO Output scan reads /app/data for files the run wrote",
        "2026-09-23 08:00:02,500 ERROR Operation 69 hit a sample error",
        "2026-09-23 08:00:03,500 INFO Assessing operation 69 result evidence",
        "2026-09-23 08:00:04,000 INFO Assessing operation 70 result evidence",
    ]

    timing = parse_log_phase_timing(lines, "69")

    assert timing.handler_seconds == 2.0
    assert timing.walk_seconds == 1.5
    assert timing.error_lines == ["2026-09-23 08:00:02,500 ERROR Operation 69 hit a sample error"]


def test_log_phase_parser_uses_utc_start_window() -> None:
    """The parser ignores matching markers that are older than the run window."""
    lines = [
        "2026-09-23 07:00:00,000 INFO Output scan marks the run start for /app/data",
        "2026-09-23 07:00:05,000 INFO Output scan reads /app/data for files the run wrote",
        "2026-09-23 07:00:06,000 INFO Assessing operation 69 result evidence",
        "2026-09-23 08:00:00,000 INFO Output scan marks the run start for /app/data",
        "2026-09-23 08:00:02,000 INFO Output scan reads /app/data for files the run wrote",
        "2026-09-23 08:00:04,000 INFO Assessing operation 69 result evidence",
    ]

    timing = parse_log_phase_timing(lines, "69", datetime(2026, 9, 23, 8, 0, 0))

    assert timing.handler_seconds == 2.0
    assert timing.walk_seconds == 2.0


def test_verdict_reconciliation_detects_status_mismatch() -> None:
    """A stale badge cannot override the server run state."""
    verdict = reconcile_verdict("failed", "Complete", run_started=True)

    assert verdict.verdict == "status-mismatch"
    assert verdict.server_state == "failed"
    assert verdict.badge_state == "completed"
    assert verdict.kind == "status-mismatch"


def test_verdict_reconciliation_reports_did_not_start() -> None:
    """A missing run identifier never reuses the old badge value."""
    verdict = reconcile_verdict("none", "Complete", run_started=False)

    assert verdict.verdict == "did-not-start"
    assert verdict.server_state == "none"
    assert verdict.badge_state == "completed"


def test_defect_classification_distinguishes_row_states() -> None:
    """Row reachability separates absent, opening, hidden, and ready states."""
    assert classify_select_state(False, False, False) == "absent"
    assert classify_select_state(True, False, False) == "opening"
    assert classify_select_state(True, True, False) == "hidden"
    assert classify_select_state(True, True, True) == "ready"


def test_terminal_defect_classification_marks_failed_and_slow() -> None:
    """Terminal classifications expose runtime and performance defects."""
    defects = classify_terminal_defects("69", "Example operation", "failed", 50.0, "terminal.png")

    assert [defect["kind"] for defect in defects] == ["runtime", "performance"]
    assert defects[0]["severity"] == "high"
    assert defects[1]["severity"] == "medium"
