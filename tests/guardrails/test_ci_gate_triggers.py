"""Guardrails for the events that start the quality gate workflow.

Issue #1952 recorded that `.github/workflows/ci.yml` started on a pull request
that targeted `main` only. A pull request against any other base ran no gate at
all. It reported zero checks and a `CLEAN` merge state, which a reviewer reads
as safe rather than unmeasured.

Pull request #1890 showed the behavior. It reported 0 successful checks and 0
failed checks, while every pull request against `main` reported 17 to 19.

The repair removes the branch filter from the `pull_request` trigger. These
tests hold the repair in place. A change that restores the filter fails a test.
"""

from pathlib import Path
from typing import Any

import pytest
import yaml

# The workflow sits three directories above this test file.
REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Name the workflow once, because every test below reads the same file.
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"

# PyYAML turns the bare `on` key into the boolean True, so name that key once.
TRIGGER_KEY = True


@pytest.fixture(scope="module")
def workflow() -> dict[str, Any]:
    """Parse the quality gate workflow and return the mapping."""
    # Read with an explicit encoding, because the Windows default differs.
    text = CI_WORKFLOW.read_text(encoding="utf-8")

    # Parse with the safe loader, because the file is untrusted configuration.
    parsed = yaml.safe_load(text)

    # Fail early with a clear message, because a non-mapping breaks each test.
    assert isinstance(parsed, dict), "The quality gate workflow must be a mapping."

    return parsed


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
