"""Prove that the SSH menu console shows every operator line of menu 270.

Why:
    The container .env sets ``CONSOLE_LOG_LEVEL=30``, so the console handler
    hides every INFO line (#886 Phase 2). A table or a preview at INFO would
    leave the SSH operator with bare prompts and no numbers to choose from.

    These tests keep only the records that a WARNING console shows. Each table,
    the preview, the progress, the summaries, and the completion line must be
    among them. The action log lines must stay at INFO, so the console stays
    short.

Privacy:
    Every identifier comes from the synthetic row factory in ``conftest``.
"""

from __future__ import annotations

import logging
from typing import Any

import pytest

from src.marvis.actions.operation import MarvisActionsOperation, MarvisBulkResolver
from src.marvis.actions.selection import DISPLAY_LEVEL
from tests.unit.marvis.actions.conftest import make_raw

CONSOLE_LEVEL = 30  # The CONSOLE_LOG_LEVEL value of the container .env.


def console_lines(caplog: pytest.LogCaptureFixture) -> list[str]:
    """Return the messages that a console at CONSOLE_LOG_LEVEL=30 shows."""
    return [record.getMessage() for record in caplog.records if record.levelno >= CONSOLE_LEVEL]


def run_menu(caplog: pytest.LogCaptureFixture) -> list[str]:
    """Run the menu with every record captured, and return the console lines."""
    caplog.set_level(logging.DEBUG)  # Capture every level, then keep the console levels only.
    MarvisActionsOperation.run()
    return console_lines(caplog)


def has_line(lines: list[str], start: str) -> bool:
    """Return True when one console line starts with the text."""
    return any(line.startswith(start) for line in lines)


class TestTheDisplayLevel:
    """The display level is the lowest level that the SSH menu console shows."""

    def test_the_display_level_reaches_the_container_console(self) -> None:
        """A display level below 30 would hide the tables again."""
        assert DISPLAY_LEVEL >= CONSOLE_LEVEL

    def test_the_display_level_is_not_an_error(self) -> None:
        """The web dashboard reads an ERROR line as a failed run, so a table must stay below ERROR."""
        assert DISPLAY_LEVEL < logging.ERROR


class TestTheExportConsole:
    """Modes 1, 2, and 4 show the tables, the status mix, and the completion line."""

    def test_the_report_run_shows_each_table_and_the_completion(
        self, harness: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        """The operator needs the numbers of each table to answer the prompts."""
        harness([make_raw(1), make_raw(2, category="ap", symptom="ap_disconnect")], "", "", "")
        lines = run_menu(caplog)
        for start in (
            "Marvis Actions modes:",
            "  1. Export every Marvis Action",
            "  3. Mark the open Marvis Actions of the chosen topics as resolved",
            "Marvis Action categories:",
            "  No.  Key",
            "  1    ap ",
            "  2    switch ",
            "Marvis Action subcategories:",
            "  2    switch/sw_offline ",
            "Selected Marvis Actions by status: Open=2",
            "Completed the Marvis Actions export and wrote results to OrgMarvisActions.csv",
        ):
            assert has_line(lines, start), start

    def test_the_action_log_lines_stay_off_the_console(self, harness: Any, caplog: pytest.LogCaptureFixture) -> None:
        """The read and write action lines are for script.log, not for the operator console."""
        harness([make_raw(1)], "", "", "")
        lines = run_menu(caplog)
        for start in ("Menu #270: Starting", "Reading the Marvis Actions list", "Writing 1 Marvis Actions to"):
            assert not has_line(lines, start), start

    def test_an_organization_without_open_actions_says_so(self, harness: Any, caplog: pytest.LogCaptureFixture) -> None:
        """A run that stops early must still tell the SSH operator why."""
        harness([make_raw(1, status="validated")], "2")
        lines = run_menu(caplog)
        assert "No open Marvis Actions exist in this organization. No file was written." in lines

    def test_an_organization_without_actions_says_so(self, harness: Any, caplog: pytest.LogCaptureFixture) -> None:
        """An empty list must still tell the SSH operator why no file exists."""
        harness([], "1")
        lines = run_menu(caplog)
        assert "No Marvis Actions exist in this organization. No file was written." in lines

    def test_a_filter_without_matches_says_so(self, harness: Any, caplog: pytest.LogCaptureFixture) -> None:
        """The category exists, but it holds no open action in mode 3."""
        raws = [make_raw(1), make_raw(2, category="ap", symptom="ap_disconnect", status="validated")]
        harness(raws, "3", "switch", "ap")
        lines = run_menu(caplog)
        assert "No open Marvis Actions match the filter. No action was changed." in lines

    def test_the_closed_report_shows_its_mode_line_and_the_closed_column(
        self, harness: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Issue #3342: the SSH operator sees mode 4, the Closed column, and the status mix of the closed actions."""
        harness([make_raw(1), make_raw(2, status="validated")], "4", "", "")
        lines = run_menu(caplog)
        for start in (
            "  4. Export the closed Marvis Actions only",
            "Selected Marvis Actions by status: AI Validated=1",
            "Completed the Marvis Actions export and wrote results to OrgMarvisActions.csv",
        ):
            assert has_line(lines, start), start
        headers = [line for line in lines if line.startswith("  No.  Key")]
        assert len(headers) == 2
        assert all(line.split()[-3:] == ["Actions", "Open", "Closed"] for line in headers)

    def test_an_organization_without_closed_actions_says_so(
        self, harness: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A mode 4 run that stops early must still tell the SSH operator why."""
        harness([make_raw(1), make_raw(2, status="inprogress")], "4")
        lines = run_menu(caplog)
        assert "No closed Marvis Actions exist in this organization. No file was written." in lines

    def test_the_unknown_status_caution_reaches_the_console(
        self, harness: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        """The SSH operator must see the caution, because the report counts an unknown key as closed."""
        harness([make_raw(1, status="snoozed")], "4", "", "")
        lines = run_menu(caplog)
        assert has_line(lines, "Caution: MistHelper does not know these status keys")


class TestTheResolveConsole:
    """Mode 3 shows the codes, the preview, the progress, the summary, and the completion line."""

    def test_the_resolve_run_shows_each_step(self, harness: Any, caplog: pytest.LogCaptureFixture) -> None:
        """The operator must see each action before the confirmation, and the result after it."""
        harness([make_raw(1), make_raw(2)], "3", "", "", "", "", "RESOLVE 2")
        lines = run_menu(caplog)
        for start in (
            "Resolution codes:",
            "  1. suggested",
            "  2. nonsuggested",
            "Preview of the 2 open Marvis Actions that this run resolves:",
            "     1. Lab Site One | Wired / Switch Offline | SW-LAB-01 | Open | started ",
            "     2. Lab Site One | Wired / Switch Offline | SW-LAB-02 | Open | started ",
            "Caution: Mist stores the resolution code",
            "Sending 2 resolve requests, one at a time",
            "Resolve progress: 2 of 2 actions",
            "Marvis Actions resolve summary: resolved=2 ",
            "Completed the Marvis Actions resolve and wrote results to OrgMarvisActionsResolveResults.csv",
        ):
            assert has_line(lines, start), start

    def test_the_request_lines_stay_off_the_console(self, harness: Any, caplog: pytest.LogCaptureFixture) -> None:
        """One line for each request would flood the console of a 500 action run."""
        harness([make_raw(1), make_raw(2)], "3", "", "", "", "", "RESOLVE 2")
        lines = run_menu(caplog)
        assert not has_line(lines, "Sending the resolve request")


class TestTheProgressLines:
    """A long run shows one line for each group of 25 requests, and one line for the last request."""

    @pytest.mark.parametrize(
        ("total", "expected"),
        [
            (1, [1]),
            (25, [25]),
            (26, [25, 26]),
            (60, [25, 50, 60]),
        ],
    )
    def test_the_progress_numbers(self, total: int, expected: list[int], caplog: pytest.LogCaptureFixture) -> None:
        """The last request always shows, so the operator sees the loop end."""
        caplog.set_level(logging.DEBUG)
        for number in range(1, total + 1):
            MarvisBulkResolver._log_progress(number, total)
        assert console_lines(caplog) == [f"Resolve progress: {number} of {total} actions" for number in expected]
