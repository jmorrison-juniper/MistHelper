"""Guardrails for the auto-merge workflow and the jobs that close a linked issue.

Issue #1926 recorded that a closing keyword never closed its issue. Twelve
merged pull requests in a row left their issue open. A person closed each one
by hand. The repair added a `close-linked-issues` job to
`.github/workflows/auto-merge.yml`. The job runs after a merge and on the
six-hour schedule, and `.github/workflows/close-linked-issues.yml` runs the
same work twice a day.

Issue #3487 moved the job bodies to the shared workflows in
misthelper-devtools. The shared repository tests the scripts. These tests hold
the wiring in this repository. A change that drops the close job, drops the
`closed` trigger, drops the schedule path, drops the issue scope, or calls a
reference that can move fails.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
import yaml

# The workflows sit three directories above this test file.
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
WORKFLOWS = REPO_ROOT / ".github" / "workflows"

# Name each workflow once, because more than one test class reads it.
AUTO_MERGE_WORKFLOW = WORKFLOWS / "auto-merge.yml"
CLOSE_WORKFLOW = WORKFLOWS / "close-linked-issues.yml"

# PyYAML turns the bare `on` key into the boolean True, so name that key once.
TRIGGER_KEY = True

# Name each job once, because a rename must fail one test and not many.
MERGE_JOB_NAME = "auto-merge"
CLOSE_JOB_NAME = "close-linked-issues"

# The shared workflows live in this folder of the devtools repository.
SHARED_PREFIX = "jmorrison-juniper/misthelper-devtools/.github/workflows/"

# A full commit cannot move. A branch or a tag can move without a change here.
FULL_COMMIT = re.compile(r"@[0-9a-f]{40}$")


def load_workflow(path: Path) -> dict[Any, Any]:
    """Parse one workflow file and return the mapping."""
    # Read the file with an explicit encoding, because Windows defaults differ.
    parsed = yaml.safe_load(path.read_text(encoding="utf-8"))

    # Fail early with a clear message, because a list or a string breaks each test.
    assert isinstance(parsed, dict), f"{path.name} must parse to a mapping."
    return parsed


def shared_call_problems(job: dict[str, Any], workflow_file: str) -> list[str]:
    """Return each reason that one job does not call one shared workflow at a full commit."""
    # Read the reference, because the job body now lives in the shared file.
    uses = str(job.get("uses", ""))
    problems = []

    # A local copy or a different file would bring back a second copy of the rules.
    if not uses.startswith(f"{SHARED_PREFIX}{workflow_file}@"):
        problems.append(f"The job must call {workflow_file}, not {uses!r}.")

    # A moving reference would change the job with no change in this repository.
    if not FULL_COMMIT.search(uses):
        problems.append(f"The call must pin a full commit: {uses!r}")
    return problems


@pytest.fixture(scope="module")
def auto_merge() -> dict[Any, Any]:
    """Parse the auto-merge workflow."""
    return load_workflow(AUTO_MERGE_WORKFLOW)


@pytest.fixture(scope="module")
def close_workflow() -> dict[Any, Any]:
    """Parse the close-linked-issues workflow."""
    return load_workflow(CLOSE_WORKFLOW)


class TestAutoMergeWorkflowTriggers:
    """Check the events that start the auto-merge workflow."""

    def test_closed_event_starts_the_workflow(self, auto_merge: dict[Any, Any]) -> None:
        """The workflow must react to the `closed` event."""
        # Read the pull_request trigger, because the close job depends on it.
        types = auto_merge[TRIGGER_KEY]["pull_request"]["types"]

        # Without this event the close job never runs and issue #1926 returns.
        assert "closed" in types, "The pull_request trigger must include 'closed'."

    def test_existing_merge_events_survive(self, auto_merge: dict[Any, Any]) -> None:
        """The repair must not remove an event that auto-merge already needed."""
        # Read the trigger list once, because the loop below checks each entry.
        types = auto_merge[TRIGGER_KEY]["pull_request"]["types"]

        # These four events drive auto-merge, so keep them.
        for event in ("labeled", "synchronize", "opened", "reopened"):
            assert event in types, f"The pull_request trigger lost the '{event}' event."

    def test_a_branch_push_starts_the_orphan_report(self, auto_merge: dict[Any, Any]) -> None:
        """A push to a feature branch must reach the orphan report of issue #1960."""
        # The shared orphan job reads only a push event, so the trigger must stay.
        assert auto_merge[TRIGGER_KEY]["push"]["branches-ignore"] == ["main"], "The push trigger must skip main only."

        # The shared job reports nothing unless the caller asks for the report.
        assert auto_merge["jobs"][MERGE_JOB_NAME]["with"]["report-orphaned-push"] is True, "Ask for the report."

    def test_the_schedule_backstop_survives(self, auto_merge: dict[Any, Any]) -> None:
        """A merge that GITHUB_TOKEN makes starts no closed event, so a schedule must repair it."""
        # Read the triggers once, because both paths live there.
        triggers = auto_merge[TRIGGER_KEY]

        # The schedule repairs main and the linked issues when no merge event arrives.
        assert triggers["schedule"], "The workflow must keep its schedule."

        # A maintainer starts the same repair by hand after an outage.
        assert "workflow_dispatch" in triggers, "The workflow must accept a manual start."

    def test_workflow_grants_no_blanket_permission(self, auto_merge: dict[Any, Any]) -> None:
        """Each job must state its own scope, so no job holds a spare permission."""
        # An empty map at the top removes every default scope from every job.
        assert auto_merge["permissions"] == {}, "The workflow must grant no blanket scope."


class TestAutoMergeJob:
    """Check the job that merges a labeled pull request and repairs main."""

    def test_the_job_calls_the_shared_workflow(self, auto_merge: dict[Any, Any]) -> None:
        """The merge, dispatch, and orphan rules must come from one pinned copy."""
        # A local copy would drift from the other Mist repositories.
        problems = shared_call_problems(auto_merge["jobs"][MERGE_JOB_NAME], "reusable-auto-merge.yml")
        assert not problems, "\n".join(problems)

    def test_the_job_grants_each_scope_of_the_shared_jobs(self, auto_merge: dict[Any, Any]) -> None:
        """A missing scope fails the whole run before any shared job starts."""
        # The dispatch needs actions, the merge needs contents, and the notices need pull requests.
        expected = {"actions": "write", "contents": "write", "pull-requests": "write"}
        assert auto_merge["jobs"][MERGE_JOB_NAME]["permissions"] == expected, "The job scopes changed."

    def test_each_main_workflow_accepts_a_dispatch(self, auto_merge: dict[Any, Any]) -> None:
        """The dispatch job can start only a workflow with a workflow_dispatch trigger."""
        # Read the list that the shared dispatch job starts after a merge (issue #1851).
        names = str(auto_merge["jobs"][MERGE_JOB_NAME]["with"]["main-workflows"]).split()

        # These three workflows report the state of main, so each must run after a merge.
        assert {"ci.yml", "codeql.yml", "container-build.yml"} <= set(names), f"A main workflow is missing: {names}"

        # A workflow without the trigger rejects the dispatch call, and main stays stale.
        for name in names:
            triggers = load_workflow(WORKFLOWS / name)[TRIGGER_KEY]
            assert "workflow_dispatch" in triggers, f"{name} must accept workflow_dispatch."


class TestCloseLinkedIssuesJob:
    """Check the job in auto-merge.yml that closes an issue after a merge."""

    def test_close_job_calls_the_shared_workflow(self, auto_merge: dict[Any, Any]) -> None:
        """The workflow must keep the close job, and the job must call the shared copy."""
        # A missing job is the exact regression that issue #1926 describes.
        assert CLOSE_JOB_NAME in auto_merge["jobs"], f"Missing job: {CLOSE_JOB_NAME}"
        problems = shared_call_problems(auto_merge["jobs"][CLOSE_JOB_NAME], "reusable-close-linked-issues.yml")
        assert not problems, "\n".join(problems)

    def test_workflow_can_close_an_issue(self, auto_merge: dict[Any, Any]) -> None:
        """The close job needs the `issues: write` scope to close an issue."""
        # Read the job permissions, because the workflow grants no scope by default.
        permissions = auto_merge["jobs"][CLOSE_JOB_NAME]["permissions"]

        # The gh CLI cannot close an issue with a read-only token.
        assert permissions == {"issues": "write", "pull-requests": "read"}, "The close job scopes changed."

    def test_close_job_accepts_only_a_real_pull_request_merge(self, auto_merge: dict[Any, Any]) -> None:
        """The close job must ignore a pull request that a person rejected."""
        # Read the condition, because it is the only guard against a wrong close.
        condition = auto_merge["jobs"][CLOSE_JOB_NAME]["if"]

        # A closed pull request that never merged must close no issue.
        assert "merged == true" in condition, "The close job must require a merge."

        # The condition must also pin the event, because other events carry no merge.
        assert "'closed'" in condition, "The close job must require the closed event."

    def test_close_job_allows_the_schedule_backstop(self, auto_merge: dict[Any, Any]) -> None:
        """The close job must let a schedule repair a missed close."""
        # Read the condition, because the schedule path lives only in this text.
        condition = auto_merge["jobs"][CLOSE_JOB_NAME]["if"]

        # A push event carries no pull request, so it must not reach the close job.
        assert "github.event_name != 'push'" in condition, "The close job must reject a push."

        # The backstop cannot work if the condition requires a pull request event.
        assert (
            "github.event_name == 'pull_request'" not in condition
        ), "The close job must not reject the schedule before the shared job runs."


class TestCloseLinkedIssuesWorkflow:
    """Check the workflow that closes a linked issue twice a day (issue #1742)."""

    def test_a_merge_and_a_schedule_start_the_workflow(self, close_workflow: dict[Any, Any]) -> None:
        """A human merge starts the closed event, and the schedule sweeps an auto-merge."""
        # Read the triggers once, because both paths live there.
        triggers = close_workflow[TRIGGER_KEY]
        assert triggers["pull_request"]["types"] == ["closed"], "The workflow must react to a closed pull request."
        assert triggers["schedule"], "The workflow must keep the sweep for an auto-merge."

    def test_the_job_calls_the_shared_workflow(self, close_workflow: dict[Any, Any]) -> None:
        """The sweep must come from the same pinned copy as the job in auto-merge.yml."""
        # A local copy would drift from the other Mist repositories.
        problems = shared_call_problems(close_workflow["jobs"][CLOSE_JOB_NAME], "reusable-close-linked-issues.yml")
        assert not problems, "\n".join(problems)

    def test_the_job_skips_a_pull_request_that_did_not_merge(self, close_workflow: dict[Any, Any]) -> None:
        """A closed pull request that never merged must close no issue."""
        # The condition must let the schedule through and stop an unmerged close.
        condition = close_workflow["jobs"][CLOSE_JOB_NAME]["if"]
        assert "merged == true" in condition, "The job must require a merge on the closed event."
        assert "github.event_name != 'pull_request'" in condition, "The job must let the schedule through."

    def test_the_job_can_close_an_issue(self, close_workflow: dict[Any, Any]) -> None:
        """The shared job closes an issue and reads the linked issues of a pull request."""
        # A missing scope fails the whole run before the shared job starts.
        permissions = close_workflow["jobs"][CLOSE_JOB_NAME]["permissions"]
        assert permissions == {"issues": "write", "pull-requests": "read"}, "The close job scopes changed."
