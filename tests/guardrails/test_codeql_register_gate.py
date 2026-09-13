"""Protect the independent CodeQL register gate recovered for issue #2088.

The gate audits live metadata with a read-only job token. It must report a
failure, not a skipped or advisory result, when the audit cannot finish.
The parent makes the exact check name required before the recovery merges.
"""

from pathlib import Path
from typing import Any

import pytest
import yaml

CI_WORKFLOW = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "ci.yml"
GATE_JOB = "codeql_register_check"
Workflow = dict[str | bool, Any]  # Include the Boolean key that PyYAML creates for an unquoted "on" key.


@pytest.fixture(scope="module")
def workflow() -> Workflow:
    """Read the real workflow rather than a separate test configuration."""
    parsed = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    assert isinstance(parsed, dict), "The workflow must contain a mapping."
    assert GATE_JOB in parsed["jobs"], "The workflow must keep the CodeQL register gate."
    return parsed


class TestCodeqlRegisterGate:
    """Keep the live audit independently visible and read-only."""

    def test_the_name_and_independent_execution_are_stable(self, workflow: Workflow) -> None:
        """The required check name must not change or depend on another gate."""
        job = workflow["jobs"][GATE_JOB]
        assert job["name"] == "CodeQL verdict register check"
        assert job["runs-on"] == "ubuntu-latest"
        assert 0 < job["timeout-minutes"] <= 5
        assert "needs" not in job
        assert "if" not in job

    def test_the_gate_runs_exactly_the_shipped_check(self, workflow: Workflow) -> None:
        """No added shell command may hide a failed check or generate a repair."""
        job = workflow["jobs"][GATE_JOB]
        commands = [step["run"] for step in job["steps"] if "run" in step]
        assert commands == ["python scripts/codeql_verdict_register.py check"]
        assert not job.get("continue-on-error", False)
        assert "defaults" not in job
        for step in job["steps"]:
            assert "if" not in step
            assert not step.get("continue-on-error", False)
            assert "working-directory" not in step

    def test_the_api_permissions_are_minimal_and_job_local(self, workflow: Workflow) -> None:
        """The audit must not inherit issue-write access or need a personal token."""
        job = workflow["jobs"][GATE_JOB]
        assert job["permissions"] == {"contents": "read", "security-events": "read"}
        assert "security-events" not in workflow["permissions"]
        assert "GH_TOKEN" not in workflow.get("env", {})
        assert "GH_TOKEN" not in job.get("env", {})
        check = next(step for step in job["steps"] if "run" in step)
        assert check["env"] == {"GH_HOST": "github.com", "GH_TOKEN": "${{ secrets.GITHUB_TOKEN }}"}
        assert all("GH_TOKEN" not in step.get("env", {}) for step in job["steps"] if step is not check)

    def test_checkout_does_not_keep_credentials(self, workflow: Workflow) -> None:
        """The checked-out code must not retain an authenticated Git remote."""
        job = workflow["jobs"][GATE_JOB]
        checkout = next(step for step in job["steps"] if step.get("uses", "").startswith("actions/checkout@"))
        assert checkout["with"]["persist-credentials"] is False
        assert checkout["with"]["submodules"] is False
        assert "ref" not in checkout["with"]
        assert "repository" not in checkout["with"]

    def test_regular_pull_requests_keep_the_same_audit(self, workflow: Workflow) -> None:
        """A fork must not select a privileged trigger or bypass the audit."""
        triggers = workflow[True]  # PyYAML reads the unquoted YAML key "on" as True.
        assert triggers["pull_request"] is None
        assert "pull_request_target" not in triggers
        assert triggers["push"]["branches"] == ["main"]
        assert "workflow_dispatch" in triggers
        assert "workflow_call" in triggers


class TestRegisterReporting:
    """Connect the audit result to the existing issue lifecycle."""

    @pytest.mark.parametrize("job_name", ["create_failure_issues", "close_resolved_issues"])
    def test_the_reporting_job_reads_the_actual_gate_result(self, workflow: Workflow, job_name: str) -> None:
        """A needs entry alone is insufficient without the matching result entry."""
        job = workflow["jobs"][job_name]
        assert job["needs"].count(GATE_JOB) == 1
        assert "always()" in job["if"]
        commands = "\n".join(step.get("run", "") for step in job["steps"])
        expected = 'RESULTS[codeql_register_check]="${{ needs.codeql_register_check.result }}"'
        assert commands.count(expected) == 1
        expected_result = "failure" if job_name == "create_failure_issues" else "success"
        assert f'if [ "$result" = "{expected_result}" ]; then' in commands
