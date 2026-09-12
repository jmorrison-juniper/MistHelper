"""Test the CodeQL verdict register tool.

The tests cover the row builder and the reconciler. No test calls the network,
because the tests must run inside the CI gates.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

# Find the tool by path, because the scripts folder is not an importable package.
_TOOL_PATH = Path(__file__).resolve().parents[2] / "scripts" / "codeql_verdict_register.py"
_SPEC = importlib.util.spec_from_file_location("codeql_verdict_register", _TOOL_PATH)
assert _SPEC is not None and _SPEC.loader is not None
register = importlib.util.module_from_spec(_SPEC)
# Register the module before the loader runs it, because a dataclass reads
# sys.modules to resolve its own annotations.
sys.modules["codeql_verdict_register"] = register
_SPEC.loader.exec_module(register)


def _alert(number: int, reason: str, comment: str | None) -> dict:
    """Return one API alert record for a test."""
    # Build the smallest record shape that the row builder reads.
    return {
        "number": number,
        "dismissed_reason": reason,
        "dismissed_comment": comment,
        "dismissed_by": {"login": "tester"},
        "dismissed_at": "2026-01-01T00:00:00Z",
        "most_recent_instance": {"location": {"path": "src/demo.py", "start_line": 12}},
    }


class TestRowBuilder:
    """Check that an API alert becomes a correct register row."""

    def test_used_in_tests_maps_to_a_verdict(self) -> None:
        """The reason `used in tests` must map to a permitted verdict."""
        # Build the row for an alert that the team dismissed as a test fixture.
        row = register.RowBuilder().build(_alert(7, "used in tests", "A test fixture holds it."))
        # Confirm the mapping, because clause C-7 had no value for this reason.
        assert row.verdict == "test_fixture"

    def test_a_blank_comment_never_yields_a_blank_reason(self) -> None:
        """A dismissal with no comment must still carry a written reason."""
        # Build the row for an alert that carries no dismissal comment.
        row = register.RowBuilder().build(_alert(8, "false positive", None))
        # Confirm the warning text, because clause C-4 forbids a blank cell.
        assert row.reason == register.MISSING_REASON_TEXT
        # Confirm the trigger names the missing reason as the review event.
        assert row.trigger == register.MISSING_REASON_TRIGGER

    def test_the_row_records_a_review_date(self) -> None:
        """A non-fixed row must carry a review date, as clause C-5 requires."""
        # Build the row for a dismissal that carries a decision date.
        row = register.RowBuilder().build(_alert(9, "false positive", "The value is a label."))
        # Confirm the decision date comes from the API timestamp.
        assert row.decided == "2026-01-01"
        # Confirm the review date sits the full interval after the decision.
        assert row.review == "2026-06-30"

    def test_the_row_reads_the_issue_reference(self) -> None:
        """The builder must copy an issue reference out of the comment."""
        # Build the row for a comment that names its tracking issue.
        row = register.RowBuilder().build(_alert(10, "won't fix", "Refs #1735 and accepted."))
        # Confirm the issue cell carries the reference for the audit trail.
        assert row.issue == "#1735"

    def test_a_pipe_in_the_comment_cannot_break_the_table(self, tmp_path: Path) -> None:
        """A pipe inside a comment must not end the markdown cell early."""
        # Build the row for a comment that holds a raw pipe character.
        row = register.RowBuilder().build(_alert(11, "false positive", "a | b"))
        # Confirm the writer escapes the pipe so the cell survives the table.
        assert "\\|" in row.to_markdown()
        # Write the register and read it back, because the round trip proves the format.
        path = tmp_path / "register.md"
        register.RegisterWriter(path).write([row])
        # Confirm the reconciler still reads the alert number and the verdict.
        assert register.RegisterReconciler(path).parse() == {11: "false_positive"}


class TestRegisterReconciler:
    """Check that the reconciliation reports every difference."""

    def _write(self, tmp_path: Path, rows: list) -> Path:
        """Write a register file for a test and return its path."""
        # Build the target path inside the temporary directory.
        path = tmp_path / "register.md"
        # Write the rows with the real writer, so the test reads the real format.
        register.RegisterWriter(path).write(rows)
        return path

    def test_a_matching_register_reports_no_difference(self, tmp_path: Path) -> None:
        """A register that matches the API must report no difference."""
        # Build one row and write it to the register.
        rows = [register.RowBuilder().build(_alert(3, "false positive", "The value is a label."))]
        path = self._write(tmp_path, rows)
        # Compare the register against the same rows.
        assert register.RegisterReconciler(path).compare(rows) == []

    def test_a_missing_row_fails_the_review(self, tmp_path: Path) -> None:
        """A dismissed alert with no register row must fail the review."""
        # Write a register that holds one row.
        first = register.RowBuilder().build(_alert(3, "false positive", "The value is a label."))
        path = self._write(tmp_path, [first])
        # Compare against two alerts, so the second one has no row.
        second = register.RowBuilder().build(_alert(4, "won't fix", "The team accepts the risk."))
        problems = register.RegisterReconciler(path).compare([first, second])
        # Confirm the reconciliation names the alert that the register misses.
        assert len(problems) == 1
        assert "Alert 4" in problems[0]

    def test_an_absent_register_reports_every_alert(self, tmp_path: Path) -> None:
        """An absent register must report every dismissed alert as missing."""
        # Point the reconciler at a path that holds no file.
        path = tmp_path / "absent.md"
        rows = [register.RowBuilder().build(_alert(5, "false positive", "The value is a label."))]
        # Confirm the reconciliation reports the gap instead of passing silently.
        assert len(register.RegisterReconciler(path).compare(rows)) == 1


@pytest.mark.parametrize("reason", ["false positive", "won't fix", "used in tests"])
def test_every_api_reason_maps_to_a_verdict(reason: str) -> None:
    """Each API dismissal reason must produce a permitted verdict."""
    # Build the row for the reason under test.
    row = register.RowBuilder().build(_alert(1, reason, "A written reason."))
    # Confirm the verdict belongs to the permitted set.
    assert row.verdict in {"false_positive", "accepted_with_rationale", "test_fixture", "fixed"}
