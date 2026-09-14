"""Guardrails for the auto-merge workflow that closes a linked issue.

Issue #1926 recorded that a closing keyword never closed its issue. Twelve
merged pull requests in a row left their issue open. A person closed each one
by hand.

The repair adds a `close-linked-issues` job to `.github/workflows/auto-merge.yml`.
The job runs after a merge and on a schedule. It closes each linked issue.

These tests hold the repair in place. A change that drops the job, drops the
`closed` trigger, drops the schedule path, or drops the issue scope fails.
"""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
import yaml

# The workflow sits three directories above this test file.
REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Name the workflow once, because both test classes read the same file.
AUTO_MERGE_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "auto-merge.yml"

# PyYAML turns the bare `on` key into the boolean True, so name that key once.
TRIGGER_KEY = True

# Name the job once, because a rename must fail one test and not many.
CLOSE_JOB_NAME = "close-linked-issues"


def should_close_linked_issue(issue_state: str, merged_at: datetime, reopened_events: tuple[datetime, ...]) -> bool:
    """Return whether the schedule may close the linked issue."""
    # A closed issue needs no action, and a second close call reports an error.
    if issue_state == "CLOSED":
        return False

    # A person can reopen the issue after the merge when the repair was incomplete.
    reopened_after_merge = any(reopened_at > merged_at for reopened_at in reopened_events)

    # The schedule must not reverse a reopen that happened after the merge.
    return not reopened_after_merge


@pytest.fixture(scope="module")
def workflow() -> dict[str, Any]:
    """Parse the auto-merge workflow and return the mapping."""
    # Read the file with an explicit encoding, because Windows defaults differ.
    text = AUTO_MERGE_WORKFLOW.read_text(encoding="utf-8")

    # Parse with the safe loader, because the file is untrusted configuration.
    parsed = yaml.safe_load(text)

    # Fail early with a clear message, because a list or a string breaks each test.
    assert isinstance(parsed, dict), "The auto-merge workflow must parse to a mapping."

    return parsed


class TestAutoMergeWorkflowTriggers:
    """Check the events that start the auto-merge workflow."""

    def test_workflow_file_exists(self) -> None:
        """The workflow file must exist, because every other test reads it."""
        # A missing file means the repair was reverted, so state that plainly.
        assert AUTO_MERGE_WORKFLOW.is_file(), f"Missing workflow: {AUTO_MERGE_WORKFLOW}"

    def test_closed_event_starts_the_workflow(self, workflow: dict[str, Any]) -> None:
        """The workflow must react to the `closed` event."""
        # Read the pull_request trigger, because the close job depends on it.
        types = workflow[TRIGGER_KEY]["pull_request"]["types"]

        # Without this event the close job never runs and issue #1926 returns.
        assert "closed" in types, "The pull_request trigger must include 'closed'."

    def test_existing_merge_events_survive(self, workflow: dict[str, Any]) -> None:
        """The repair must not remove an event that auto-merge already needed."""
        # Read the trigger list once, because the loop below checks each entry.
        types = workflow[TRIGGER_KEY]["pull_request"]["types"]

        # These four events drove auto-merge before the repair, so keep them.
        for event in ("labeled", "synchronize", "opened", "reopened"):
            assert event in types, f"The pull_request trigger lost the '{event}' event."

    def test_workflow_can_close_an_issue(self, workflow: dict[str, Any]) -> None:
        """The close job needs the `issues: write` scope to close an issue."""
        # Read the job permissions, because the workflow grants no scope by default.
        permissions = workflow["jobs"][CLOSE_JOB_NAME]["permissions"]

        # The gh CLI cannot close an issue with a read-only token.
        assert permissions.get("issues") == "write", "The close job needs issues: write."

    def test_workflow_grants_no_blanket_permission(self, workflow: dict[str, Any]) -> None:
        """Each job must state its own scope, so no job holds a spare permission."""
        # An empty map at the top removes every default scope from every job.
        assert workflow["permissions"] == {}, "The workflow must grant no blanket scope."


class TestCloseLinkedIssuesJob:
    """Check the job that closes an issue after a merge."""

    def test_close_job_exists(self, workflow: dict[str, Any]) -> None:
        """The workflow must define the close job."""
        # A missing job is the exact regression that issue #1926 describes.
        assert CLOSE_JOB_NAME in workflow["jobs"], f"Missing job: {CLOSE_JOB_NAME}"

    def test_close_job_accepts_only_a_real_pull_request_merge(self, workflow: dict[str, Any]) -> None:
        """The close job must ignore a pull request that a person rejected."""
        # Read the condition, because it is the only guard against a wrong close.
        condition = workflow["jobs"][CLOSE_JOB_NAME]["if"]

        # A closed pull request that never merged must close no issue.
        assert "merged == true" in condition, "The close job must require a merge."

        # The condition must also pin the event, because other events carry no merge.
        assert "'closed'" in condition, "The close job must require the closed event."

    def test_close_job_allows_the_schedule_backstop(self, workflow: dict[str, Any]) -> None:
        """The close job must let a schedule repair a missed close."""
        # Read the condition, because the schedule path lives only in this text.
        condition = workflow["jobs"][CLOSE_JOB_NAME]["if"]

        # A push event carries no pull request, so it must not reach the close job.
        assert "github.event_name != 'push'" in condition, "The close job must reject a push."

        # The backstop cannot work if the condition requires a pull request event.
        assert (
            "github.event_name == 'pull_request'" not in condition
        ), "The close job must not reject the schedule before the script runs."

    def test_auto_merge_job_skips_the_closed_event(self, workflow: dict[str, Any]) -> None:
        """The auto-merge job must not run on the `closed` event."""
        # Read the condition, because the new event would otherwise reach this job.
        condition = workflow["jobs"]["auto-merge"]["if"]

        # A closed pull request cannot auto-merge, so the job would fail every time.
        assert "!= 'closed'" in condition, "The auto-merge job must skip a close event."

    def test_close_job_reads_the_linked_issues(self, workflow: dict[str, Any]) -> None:
        """The close job must read the issues that GitHub parsed from the body."""
        # Join the step scripts, because the check reads the shell body as text.
        script = self._job_script(workflow)

        # This field holds the issues that the closing keyword named.
        assert "closingIssuesReferences" in script, "The job must read the linked issues."

        # The schedule path reads merged pull requests, because no event carries one.
        assert "gh pr list" in script, "The schedule path must read merged pull requests."

        # The query must allow no linked issue, because that state is normal.
        assert "[]?" in script, "The linked issue query must allow an empty list."

    def test_close_job_reads_the_issue_timeline(self, workflow: dict[str, Any]) -> None:
        """The close job must read the issue timeline before it closes an issue."""
        # Join the step scripts, because the check reads the shell body as text.
        script = self._job_script(workflow)

        # The timeline has the reopen event that protects a maintainer decision.
        assert "timeline?per_page=100" in script, "The job must read the issue timeline."

        # Busy issues can put a recent reopen on a later page.
        assert "--paginate" in script, "The timeline call must read every page."

        # The event type names the exact decision that the schedule must honor.
        assert '.event == "reopened"' in script, "The job must read a reopen event."

        # The actor filter keeps the automation from reversing a human decision.
        assert '.actor.type == "User"' in script, "The job must honor a human reopen."

        # The time comparison lets an old reopen still receive the merged fix.
        assert ".created_at >" in script, "The job must compare the reopen time."

    def test_close_job_skips_an_already_closed_issue(self, workflow: dict[str, Any]) -> None:
        """The close job must not call close twice on one issue."""
        # Read the shell body, because the guard lives in the script.
        script = self._job_script(workflow)

        # A second close call reports an error and would fail the whole job.
        assert "CLOSED" in script, "The job must check the issue state before a close."

    def test_close_job_reports_a_failed_close(self, workflow: dict[str, Any]) -> None:
        """A failed close must stay visible instead of passing quietly."""
        # Read the shell body, because the error report lives in the script.
        script = self._job_script(workflow)

        # Issue #1926 stayed hidden because nothing reported the missed close.
        assert "::error::" in script, "The job must report a failed close."

    def test_close_job_stops_on_a_shell_error(self, workflow: dict[str, Any]) -> None:
        """The shell must stop on an error instead of running the next line."""
        # Read the shell body, because the option appears on the first line.
        script = self._job_script(workflow)

        # Without this option a failed gh call would leave the job green.
        assert "set -euo pipefail" in script, "The job script must use a strict shell."

    @staticmethod
    def _job_script(workflow: dict[str, Any]) -> str:
        """Return every `run` script in the close job as one string."""
        # Read the step list, because the script may span more than one step.
        steps = workflow["jobs"][CLOSE_JOB_NAME]["steps"]

        # Keep only a step that runs a shell command, because a step may use an action.
        scripts = [step.get("run", "") for step in steps]

        # Join the scripts, so a caller can search the whole job body at once.
        return "\n".join(scripts)


class TestCloseLinkedIssuesDecisionRule:
    """Check the rule that protects a reopened issue."""

    def test_open_issue_closes_when_no_reopen_exists(self) -> None:
        """An open issue can close when no person reopened it after the merge."""
        # Set the merge time, because the decision compares all reopen times to it.
        merged_at = datetime(2026, 9, 13, 22, 41, 17, tzinfo=UTC)

        # No reopen event exists, so the schedule can close the issue.
        assert should_close_linked_issue("OPEN", merged_at, ())

    def test_closed_issue_stays_unchanged(self) -> None:
        """A closed issue must stay unchanged, because a second close can fail."""
        # Set the merge time, because the helper needs a complete input.
        merged_at = datetime(2026, 9, 13, 22, 41, 17, tzinfo=UTC)

        # The issue is already closed, so no further action is correct.
        assert not should_close_linked_issue("CLOSED", merged_at, ())

    def test_reopen_after_merge_keeps_issue_open(self) -> None:
        """A person can reopen an issue after the merge and keep it open."""
        # Set the merge time, because the next reopen must be later.
        merged_at = datetime(2026, 9, 13, 22, 41, 17, tzinfo=UTC)

        # The reopen happened after the merge, so the schedule must skip it.
        reopened_at = datetime(2026, 9, 13, 22, 50, 0, tzinfo=UTC)

        # The rule protects the maintainer decision from the schedule.
        assert not should_close_linked_issue("OPEN", merged_at, (reopened_at,))

    def test_reopen_before_merge_still_allows_close(self) -> None:
        """An old reopen does not stop the close for the later merge."""
        # Set the merge time, because an earlier reopen belongs to old work.
        merged_at = datetime(2026, 9, 13, 22, 41, 17, tzinfo=UTC)

        # The reopen happened before the merge, so the merge can still close the issue.
        reopened_at = datetime(2026, 9, 13, 22, 30, 0, tzinfo=UTC)

        # The rule lets the schedule close the issue for the later merge.
        assert should_close_linked_issue("OPEN", merged_at, (reopened_at,))
