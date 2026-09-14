"""Guardrail: the main sweep never closes the issue of an open pull request (issue #2623).

Why:
    The job `close_resolved_issues` closes a quality-gate issue when the gate
    passes. A run on a pull request closes the one issue of that pull request.
    A run on main closed every open issue that named the gate, because main is
    authoritative for main.

    That second rule reached too far. An issue with the title
    "CI: quality-gate `black` failed (PR #2622)" belongs to pull request #2622.
    A `black` pass on main closed it, although pull request #2622 stayed open
    and its own `black` job still failed. Issue #2623 closed that way twice,
    and the second close came 13 seconds after an operator reopened it.

    Only the run of a pull request may report the gate state of that pull
    request. These tests read both workflow files and the decision model. They
    fail when a later change lets the main sweep speak for an open pull request.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]

# Both files carry the same job. The first one runs here. The second one ships
# to another repository, so it must hold the same guard.
WORKFLOW_FILES = (
    Path(".github/workflows/ci.yml"),
    Path(".github/quality-gates-portable.yml"),
)

JOB_NAME = "close_resolved_issues"
STEP_NAME = "Close issues for passing gates"

# The title form that the failure job writes for a pull request.
SCOPED_TITLE = re.compile(r"\(PR #(\d+)\)")

OPEN_STATE = "OPEN"  # The one state that keeps a pull request in charge of its gate.


def scoped_pull_request(issue_title: str) -> int | None:
    """Return the pull request number that an issue title names.

    Why:
        The sweep must tell a main-scoped issue from an issue that belongs to
        one pull request. The title carries that difference and nothing else
        does.

    Args:
        issue_title: The full title of the quality-gate issue.

    Returns:
        The pull request number, or None when the title names no pull request.
    """
    found = SCOPED_TITLE.search(issue_title)  # The suffix is the only scope marker.
    return int(found.group(1)) if found else None


def close_is_allowed(issue_title: str, is_main_run: bool, pull_request_state: str | None) -> bool:
    """Return whether the sweep may close one quality-gate issue.

    Why:
        A run on a pull request already searches for the one title of that pull
        request, so it may always close what it finds. A run on main must first
        prove that no open pull request owns the issue.

    Args:
        issue_title: The full title of the quality-gate issue.
        is_main_run: True when the run belongs to main.
        pull_request_state: The state of the named pull request, or None when
            the title names no pull request.

    Returns:
        True when the sweep may close the issue.
    """
    if not is_main_run:  # The pull request run owns the one issue it searched for.
        return True
    if scoped_pull_request(issue_title) is None:  # A main-scoped issue has no other owner.
        return True
    return pull_request_state != OPEN_STATE  # An open pull request keeps its own issue.


def close_step_script(relative_path: Path) -> str:
    """Return the shell script of the close step in one workflow file.

    Args:
        relative_path: The workflow path, relative to the repository root.

    Returns:
        The script text of the close step.
    """
    document = yaml.safe_load((REPOSITORY_ROOT / relative_path).read_text(encoding="utf-8"))
    steps = document["jobs"][JOB_NAME]["steps"]  # A missing job raises here, which is the correct report.
    for step in steps:
        if step.get("name") == STEP_NAME:
            return str(step["run"])
    raise AssertionError(f"{relative_path} holds no step named {STEP_NAME!r}")


class TestTheDecisionModel:
    """The rule keeps an open pull request in charge of its own gate."""

    def test_a_main_run_keeps_the_issue_of_an_open_pull_request(self) -> None:
        """This is the exact fault of issue #2623, so it must never pass again."""
        assert not close_is_allowed("CI: quality-gate `black` failed (PR #2622)", True, OPEN_STATE)

    def test_a_main_run_closes_the_issue_of_a_merged_pull_request(self) -> None:
        """A merged pull request puts its code on main, so the main gate speaks for it."""
        assert close_is_allowed("CI: quality-gate `black` failed (PR #2600)", True, "MERGED")

    def test_a_main_run_closes_the_issue_of_a_closed_pull_request(self) -> None:
        """A pull request that never merged leaves no failure to repair."""
        assert close_is_allowed("CI: quality-gate `radon` failed (PR #2468)", True, "CLOSED")

    def test_a_main_run_closes_an_issue_that_names_no_pull_request(self) -> None:
        """A main-scoped issue belongs to main, so the main gate decides it."""
        assert close_is_allowed("CI: quality-gate `pytest` failed", True, None)

    def test_a_pull_request_run_closes_its_own_issue(self) -> None:
        """The pull request run searched for this one title, so it may close it."""
        assert close_is_allowed("CI: quality-gate `black` failed (PR #2622)", False, OPEN_STATE)


class TestTheTitleScope:
    """The title is the only marker that names the owner of an issue."""

    def test_a_scoped_title_gives_the_pull_request_number(self) -> None:
        """The sweep reads this number to ask for the state of the pull request."""
        assert scoped_pull_request("CI: quality-gate `mypy` failed (PR #2534)") == 2534

    def test_a_main_title_gives_no_number(self) -> None:
        """A title without the suffix belongs to main."""
        assert scoped_pull_request("CI: quality-gate `mypy` failed") is None


class TestTheWorkflowHoldsTheGuard:
    """Both workflow files must ask for the state before they close."""

    @pytest.mark.parametrize("relative_path", WORKFLOW_FILES, ids=lambda path: path.name)
    def test_the_step_reads_the_pull_request_state(self, relative_path: Path) -> None:
        """A sweep that never reads the state cannot keep an open pull request."""
        script = close_step_script(relative_path)
        assert "gh pr view" in script, f"{relative_path} never reads the state of the named pull request"
        assert "--json state" in script, f"{relative_path} never asks for the state field"

    @pytest.mark.parametrize("relative_path", WORKFLOW_FILES, ids=lambda path: path.name)
    def test_the_step_reads_the_issue_title(self, relative_path: Path) -> None:
        """The title carries the pull request number, so the sweep must read it."""
        script = close_step_script(relative_path)
        assert "gh issue view" in script, f"{relative_path} never reads the title of the issue"

    @pytest.mark.parametrize("relative_path", WORKFLOW_FILES, ids=lambda path: path.name)
    def test_the_step_skips_an_open_pull_request(self, relative_path: Path) -> None:
        """The skip is the action that repairs issue #2623."""
        script = close_step_script(relative_path)
        assert OPEN_STATE in script, f"{relative_path} never compares the state against {OPEN_STATE}"
        assert "continue" in script, f"{relative_path} never skips an issue"

    @pytest.mark.parametrize("relative_path", WORKFLOW_FILES, ids=lambda path: path.name)
    def test_the_step_still_closes_an_issue(self, relative_path: Path) -> None:
        """A guard that closes nothing would leave every repaired gate issue open."""
        script = close_step_script(relative_path)
        assert "gh issue close" in script, f"{relative_path} closes no issue at all"
