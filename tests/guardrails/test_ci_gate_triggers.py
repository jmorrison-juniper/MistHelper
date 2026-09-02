"""Guardrails for the events that start the quality gate workflow.

Issue #1952 recorded that `.github/workflows/ci.yml` started on a pull request
that targeted `main` only. A pull request against any other base ran no gate at
all. It reported zero checks and a `CLEAN` merge state, which a reviewer reads
as safe rather than unmeasured.

Pull request #1890 showed the behavior. It reported 0 successful checks and 0
failed checks, while every pull request against `main` reported 17 to 19.

The repair removes the branch filter from the `pull_request` trigger. These
tests hold the repair in place. A change that restores the filter fails a test.

Issue #2204 recorded a second defect in the same file. The workflow declared no
concurrency group, so a second push to a pull request left the older run alive.
Both runs then spent minutes on the same branch, and the older run measured a
tree that no reviewer would read.

Issue #2205 recorded the same branch filter defect in
`.github/workflows/codeql.yml`. CodeQL reports a required check, so a filter
that named `main` alone stopped that check from ever reporting on a stacked
pull request.
"""

from pathlib import Path
from typing import Any

import pytest
import yaml

# The workflow sits three directories above this test file.
REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Name the workflow once, because every test below reads the same file.
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"

# Name the CodeQL workflow once, because it reports a required check too.
CODEQL_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "codeql.yml"

# PyYAML turns the bare `on` key into the boolean True, so name that key once.
TRIGGER_KEY = True


def _parse(path: Path) -> dict[str, Any]:
    """Parse one workflow file and return the mapping."""
    # Read with an explicit encoding, because the Windows default differs.
    text = path.read_text(encoding="utf-8")

    # Parse with the safe loader, because the file is untrusted configuration.
    parsed = yaml.safe_load(text)

    # Fail early with a clear message, because a non-mapping breaks each test.
    assert isinstance(parsed, dict), f"The workflow must be a mapping: {path}"

    return parsed


@pytest.fixture(scope="module")
def workflow() -> dict[str, Any]:
    """Parse the quality gate workflow and return the mapping."""
    # Read the quality gate workflow, because most tests below inspect it.
    return _parse(CI_WORKFLOW)


@pytest.fixture(scope="module")
def codeql() -> dict[str, Any]:
    """Parse the CodeQL workflow and return the mapping."""
    # Read the CodeQL workflow, because it reports a required check.
    return _parse(CODEQL_WORKFLOW)


class TestPullRequestTrigger:
    """Check the pull request event that starts the quality gates."""

    def test_workflow_file_exists(self) -> None:
        """The workflow file must exist, because every other test reads it."""
        # A missing file means the gates are gone, so state that plainly.
        assert CI_WORKFLOW.is_file(), f"Missing workflow: {CI_WORKFLOW}"

    def test_pull_request_trigger_is_present(self, workflow: dict[str, Any]) -> None:
        """A pull request must start the quality gates."""
        # Without this trigger no pull request is measured at all.
        assert "pull_request" in workflow[TRIGGER_KEY], "A pull request must run CI."

    def test_pull_request_has_no_branch_filter(self, workflow: dict[str, Any]) -> None:
        """Every pull request must run the gates, whatever its base branch."""
        # Read the trigger. A bare key parses to None, which means every branch.
        trigger = workflow[TRIGGER_KEY]["pull_request"]

        # A None trigger is the repaired shape, so accept it and stop here.
        if trigger is None:
            return

        # A mapping with a branch filter is the exact defect that #1952 records.
        assert "branches" not in trigger, (
            "The pull_request trigger must carry no branch filter. "
            "A filter lets a stacked pull request merge with zero checks."
        )

    def test_stacked_base_branch_is_not_excluded(self, workflow: dict[str, Any]) -> None:
        """A pull request against a feature branch must not be filtered out."""
        # Read the trigger, because the check below inspects any surviving filter.
        trigger = workflow[TRIGGER_KEY]["pull_request"]

        # The repaired shape parses to None, so no branch can be excluded.
        if trigger is None:
            return

        # If a filter survives, it must at least admit a feature branch pattern.
        branches = trigger.get("branches", [])

        # A filter of main alone reproduces the defect, so reject that exact case.
        assert branches != ["main"], "A filter of main alone reproduces issue #1952."


class TestPushTrigger:
    """Check the push event, which must stay narrow."""

    def test_push_stays_pinned_to_main(self, workflow: dict[str, Any]) -> None:
        """The push trigger must stay on main, so no branch runs twice."""
        # Read the push trigger, because a wide filter doubles every run.
        push = workflow[TRIGGER_KEY]["push"]

        # A push run on every branch repeats the pull request run and adds cost.
        assert push["branches"] == ["main"], "The push trigger must stay on main."


class TestConcurrency:
    """Check the group that cancels a stale quality gate run."""

    def test_workflow_declares_a_concurrency_group(self, workflow: dict[str, Any]) -> None:
        """The workflow must declare a group, so a stale run stops."""
        # Without a group both runs continue, and the older run wastes minutes.
        assert "concurrency" in workflow, "The workflow must declare a concurrency group."

    def test_group_separates_each_pull_request(self, workflow: dict[str, Any]) -> None:
        """The group must name the pull request, so one branch cancels itself."""
        # Read the group name, because the checks below inspect its parts.
        group = workflow["concurrency"]["group"]

        # A group that reads the pull request number keeps each branch separate.
        assert "github.event.pull_request.number" in group, (
            "The group must name the pull request, " "so a push to one branch cancels that branch alone."
        )

        # A fallback to the reference covers a push and a manual start.
        assert "github.ref" in group, "The group must fall back to the reference."

    def test_group_avoids_the_caller_workflow_name(self, workflow: dict[str, Any]) -> None:
        """The group must not read github.workflow, because a caller renames it."""
        # This workflow accepts workflow_call, and then github.workflow reports
        # the name of the caller. The group would then merge with the caller.
        assert "github.workflow" not in workflow["concurrency"]["group"], (
            "The group must use a literal name. " "github.workflow reports the name of the caller."
        )

    def test_a_main_run_is_never_cancelled(self, workflow: dict[str, Any]) -> None:
        """A push to main must finish, because Auto-merge reads its result."""
        # Read the setting, because a bare true would cancel a main run.
        cancel = workflow["concurrency"]["cancel-in-progress"]

        # The condition must limit the cancel to a pull request event.
        assert "pull_request" in str(cancel), (
            "cancel-in-progress must apply to a pull request alone. "
            "A cancelled main run leaves the merged tree unmeasured."
        )


class TestCodeqlTrigger:
    """Check the events that start the CodeQL scan, a required check."""

    def test_codeql_workflow_exists(self) -> None:
        """The CodeQL workflow must exist, because it reports a required check."""
        # A missing file means no scan reports, and every merge then blocks.
        assert CODEQL_WORKFLOW.is_file(), f"Missing workflow: {CODEQL_WORKFLOW}"

    def test_pull_request_has_no_branch_filter(self, codeql: dict[str, Any]) -> None:
        """Every pull request must run the scan, whatever its base branch."""
        # Read the trigger. A bare key parses to None, which means every branch.
        trigger = codeql[TRIGGER_KEY]["pull_request"]

        # A None trigger is the repaired shape, so accept it and stop here.
        if trigger is None:
            return

        # CodeQL reports a required check, so a filter blocks a stacked branch.
        assert "branches" not in trigger, (
            "The pull_request trigger must carry no branch filter. "
            "CodeQL is a required check, so a filtered branch never reports."
        )

    def test_push_stays_pinned_to_main(self, codeql: dict[str, Any]) -> None:
        """The push trigger must stay on main, so no branch scans twice."""
        # Read the push trigger, because a wide filter doubles every scan.
        push = codeql[TRIGGER_KEY]["push"]

        # A scan on every push repeats the pull request scan and adds cost.
        assert push["branches"] == ["main"], "The push trigger must stay on main."
