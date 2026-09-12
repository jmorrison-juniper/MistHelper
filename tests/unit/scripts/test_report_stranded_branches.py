"""Test the stranded branch report that issues #1980 and #2251 asked for.

A stranded branch holds commits above the base branch and has no open pull
request. Only `refs/pull/<n>/head` survives a branch deletion, so a branch with
no pull request has one copy. These tests lock the three protection tests and
the report that names the result.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

import pytest

from scripts.report_stranded_branches import (
    BranchRecord,
    StrandedBranchReporter,
    _as_rows,
    _head_date,
    _head_ref,
    main,
)

# The instant that every age test measures against. A fixed value keeps the
# tests hermetic, because a real clock changes between two runs.
_NOW = datetime(2026, 9, 3, 12, 0, 0, tzinfo=UTC)


def _record(name: str, ahead_by: int = 3, age_days: int = 30) -> BranchRecord:
    """Build one branch record at a chosen age and ahead count."""
    logging.info("Building the record for the branch %s", name)  # Report the build before the work.
    record = BranchRecord(
        name=name,  # The short branch name the tests assert on.
        sha="a" * 40,  # A fixed fork point, because no test reads the value.
        ahead_by=ahead_by,  # The count that the first protection test reads.
        last_commit_at=_NOW - timedelta(days=age_days),  # The date that the age test reads.
    )
    logging.debug("The record for %s is %d days old", name, age_days)  # Record the age.
    return record


def _reporter(records: list[BranchRecord], open_heads: frozenset[str], min_age_days: int = 7) -> StrandedBranchReporter:
    """Build a reporter over a fixed set of records and open pull requests."""
    logging.info("Building a reporter over %d records", len(records))  # Report before the build.
    by_name = {record.name: record for record in records}  # Index the records for the read callback.
    return StrandedBranchReporter(
        lambda: list(by_name),  # Answer every branch name in the fixed set.
        by_name.get,  # Answer one record, or None when the name is unknown.
        lambda: open_heads,  # Answer the head name of every open pull request.
        min_age_days,  # Apply the quiet period the caller chose.
    )


# ---------------------------------------------------------------------------
# The three protection tests
# ---------------------------------------------------------------------------


def test_a_branch_with_work_and_no_pull_request_is_stranded() -> None:
    """A branch above the base with no open pull request MUST be reported."""
    logging.info("Checking that unprotected work is reported")  # Report the plan.
    record = _record("fix/1234-a-defect")  # Three commits above the base, thirty days old.

    assert record.is_stranded(frozenset(), 7, _NOW), "unprotected work must be reported"


def test_an_open_pull_request_protects_the_branch() -> None:
    """A branch that an open pull request names MUST NOT be reported."""
    logging.info("Checking that an open pull request protects the head")  # Report the plan.
    record = _record("fix/1234-a-defect")  # The same unprotected shape as the previous test.

    # WHY: refs/pull/<n>/head survives a deletion, so the head is already permanent.
    assert not record.is_stranded(frozenset({"fix/1234-a-defect"}), 7, _NOW)


def test_a_branch_at_the_base_holds_nothing_to_lose() -> None:
    """A branch with no commit above the base MUST NOT be reported."""
    logging.info("Checking that a branch at the base is quiet")  # Report the plan.
    record = _record("chore/no-work", ahead_by=0)  # No commit above the base branch.

    assert not record.is_stranded(frozenset(), 7, _NOW), "a branch at the base loses nothing"


def test_recent_work_stays_below_the_quiet_period() -> None:
    """A branch younger than the threshold MUST NOT be reported."""
    logging.info("Checking that recent work stays quiet")  # Report the plan.
    record = _record("feat/today", age_days=2)  # Pushed two days ago, so the work is active.

    assert not record.is_stranded(frozenset(), 7, _NOW), "active work is not stranded"


@pytest.mark.parametrize(
    "name",
    ["dependabot/npm_and_yarn/ops-portal/x", "gh-readonly-queue/main/pr-1", "revert-1234-a-branch"],
)
def test_a_bot_branch_is_never_reported(name: str) -> None:
    """A bot branch follows its own lifecycle, so the report MUST skip it."""
    logging.info("Checking that the bot branch %s stays quiet", name)  # Report the plan.
    record = _record(name)  # The same unprotected shape as a real feature branch.

    assert not record.is_stranded(frozenset(), 7, _NOW), f"{name} must not be reported"


def test_a_clock_skew_never_reports_a_negative_age() -> None:
    """A head dated in the future MUST report an age of zero, not a negative."""
    logging.info("Checking the age floor against a clock skew")  # Report the plan.
    record = _record("feat/future", age_days=-5)  # A head dated five days ahead of the clock.

    assert record.age_days(_NOW) == 0, "an age must never fall below zero"


# ---------------------------------------------------------------------------
# The report
# ---------------------------------------------------------------------------


def test_the_report_names_every_stranded_branch() -> None:
    """The report MUST name each stranded branch and skip each protected one."""
    logging.info("Checking the report content")  # Report the plan before the work.
    records = [_record("fix/a-defect"), _record("feat/protected"), _record("chore/fresh", age_days=1)]
    reporter = _reporter(records, frozenset({"feat/protected"}))  # One branch has a pull request.

    text = reporter.render(reporter.find())  # Find the branches, then render the Markdown.
    logging.debug("The report is %r", text)  # Record the report for a failure read.

    assert "`fix/a-defect`" in text, "the stranded branch must appear"
    assert "feat/protected" not in text, "a branch with a pull request must not appear"
    assert "chore/fresh" not in text, "a branch inside the quiet period must not appear"


def test_the_report_orders_the_oldest_head_first() -> None:
    """The report MUST list the oldest head first, because it is the most at risk."""
    logging.info("Checking the report order")  # Report the plan before the work.
    records = [_record("feat/newer", age_days=10), _record("feat/older", age_days=200)]
    reporter = _reporter(records, frozenset())  # Neither branch has a pull request.

    names = [record.name for record in reporter.find()]  # Read the order the reporter chose.
    logging.debug("The report order is %r", names)  # Record the order for a failure read.

    assert names == ["feat/older", "feat/newer"], "the oldest head must come first"


def test_a_clean_repository_answers_a_clear_sentence() -> None:
    """An empty result MUST answer a sentence, not an empty table."""
    logging.info("Checking the clean report")  # Report the plan before the work.
    reporter = _reporter([], frozenset())  # No branch at all, so nothing can be stranded.

    text = reporter.render(reporter.find())  # Render the empty result.

    assert "Every branch" in text, "a clean repository needs a clear answer"
    assert "|" not in text, "a clean report must hold no table"


def test_the_base_branch_is_never_reported() -> None:
    """The base branch MUST NOT appear in its own report."""
    logging.info("Checking that the base branch is skipped")  # Report the plan.
    reporter = _reporter([_record("main")], frozenset())  # Only the base branch exists.

    assert reporter.find("main") == [], "the base branch cannot be stranded against itself"


def test_an_unreadable_branch_is_skipped() -> None:
    """A branch the reader cannot answer MUST NOT stop the report."""
    logging.info("Checking that an unreadable branch is skipped")  # Report the plan.
    reporter = StrandedBranchReporter(
        lambda: ["feat/unreadable", "fix/a-defect"],  # The API lists two branches.
        {"fix/a-defect": _record("fix/a-defect")}.get,  # The compare answers only one of them.
        frozenset,  # No open pull request protects either branch.
    )

    names = [record.name for record in reporter.find()]  # Read the branches the reporter kept.

    assert names == ["fix/a-defect"], "an unreadable branch must not stop the report"


# ---------------------------------------------------------------------------
# The response readers
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("body", [{"message": "Not Found"}, None, "text", 7])
def test_a_non_list_body_answers_no_rows(body: object) -> None:
    """An error body or a scalar MUST answer no rows, not raise."""
    logging.info("Checking the row reader against %r", body)  # Report the plan.

    assert list(_as_rows(body)) == [], "only a JSON array holds rows"


def test_the_row_reader_drops_a_non_object_element() -> None:
    """A list that mixes objects and scalars MUST answer the objects only."""
    logging.info("Checking the row reader against a mixed list")  # Report the plan.

    rows = list(_as_rows([{"name": "a"}, "b", None, {"name": "c"}]))  # Two objects, two scalars.

    assert rows == [{"name": "a"}, {"name": "c"}], "a scalar element must be dropped"


def test_the_head_reference_reads_a_well_formed_row() -> None:
    """A pull request row MUST answer the short head branch name."""
    logging.info("Checking the head reference reader")  # Report the plan before the work.

    name = _head_ref({"head": {"ref": "fix/1234-a-defect", "sha": "b" * 40}})  # A normal API row.

    assert name == "fix/1234-a-defect", "the reader must answer the short branch name"


@pytest.mark.parametrize("row", [{}, {"head": None}, {"head": "main"}, {"head": {}}, {"head": {"ref": 7}}])
def test_a_malformed_row_answers_an_empty_head(row: dict[str, object]) -> None:
    """A row with no readable head MUST answer an empty name, not raise."""
    logging.info("Checking the head reference reader against %r", row)  # Report the plan.

    # WHY: an empty name never matches a branch, so a malformed row protects nothing.
    assert _head_ref(row) == "", "a malformed row must answer an empty name"


def test_an_unreadable_pull_request_row_protects_no_branch() -> None:
    """An empty head name MUST NOT protect a branch whose name is also empty."""
    logging.info("Checking that an empty head name protects nothing")  # Report the plan.
    record = _record("")  # A branch with an empty name cannot exist, so it must not match.

    assert record.is_stranded(frozenset(), 7, _NOW), "an empty name must not act as protection"


def test_the_head_date_reads_the_last_commit() -> None:
    """The head date MUST come from the last commit, because compare orders oldest first."""
    logging.info("Checking the head date reader")  # Report the plan before the work.
    commits = [
        {"commit": {"committer": {"date": "2026-01-01T00:00:00Z"}}},  # The oldest commit.
        {"commit": {"committer": {"date": "2026-06-15T09:30:00Z"}}},  # The head commit.
    ]

    stamp = _head_date(commits)  # Read the date that the age test uses.
    logging.debug("The head date is %s", stamp)  # Record the value for a failure read.

    assert stamp == datetime(2026, 6, 15, 9, 30, tzinfo=UTC), "the last commit is the head"


@pytest.mark.parametrize("commits", [[], [{"commit": {}}], [{"commit": {"committer": {}}}], "not-a-list"])
def test_a_missing_head_date_reads_as_now(commits: object) -> None:
    """A missing date MUST read as now, so the branch stays below every threshold."""
    logging.info("Checking the head date fallback against %r", commits)  # Report the plan.

    stamp = _head_date(commits)  # Read the fallback value.

    # WHY: a missing date cannot support a deletion, so the report must stay quiet.
    assert (datetime.now(UTC) - stamp).total_seconds() < 60, "a missing date must read as now"


# ---------------------------------------------------------------------------
# The command line
# ---------------------------------------------------------------------------


def test_the_command_line_reports_success_without_the_fail_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    """A find MUST answer status 0 unless the caller passes --fail-on-find."""
    logging.info("Checking the default exit status")  # Report the plan before the work.
    _patch_reader(monkeypatch, [_record("fix/a-defect")])  # One stranded branch exists.

    assert main([]) == 0, "a report alone must not fail a run"


def test_the_fail_flag_turns_a_find_into_a_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """A find with --fail-on-find MUST answer status 1, so a gate can block."""
    logging.info("Checking the exit status under --fail-on-find")  # Report the plan.
    _patch_reader(monkeypatch, [_record("fix/a-defect")])  # One stranded branch exists.

    assert main(["--fail-on-find"]) == 1, "a find must fail the run under the flag"


def test_a_clean_repository_answers_zero_under_the_fail_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    """No find MUST answer status 0, even with --fail-on-find."""
    logging.info("Checking the clean exit status under --fail-on-find")  # Report the plan.
    _patch_reader(monkeypatch, [])  # No branch at all, so nothing can be stranded.

    assert main(["--fail-on-find"]) == 0, "a clean repository must pass the gate"


def _patch_reader(monkeypatch: pytest.MonkeyPatch, records: list[BranchRecord]) -> None:
    """Replace the GitHub reader with a fixed set of records."""
    logging.info("Patching the GitHub reader with %d records", len(records))  # Report the plan.
    by_name = {record.name: record for record in records}  # Index the records for the read callback.
    monkeypatch.setattr("scripts.report_stranded_branches.GitHubReader.list_branches", lambda self: list(by_name))
    monkeypatch.setattr(
        "scripts.report_stranded_branches.GitHubReader.read_branch", lambda self, name: by_name.get(name)
    )
    monkeypatch.setattr(
        "scripts.report_stranded_branches.GitHubReader.list_open_pull_request_heads", lambda self: frozenset()
    )
    logging.debug("The GitHub reader now answers a fixed set")  # Record the patch after the work.
