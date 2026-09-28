"""Guardrail: the main sweep never closes the issue of an open pull request (issue #2623).

Why:
    The quality-gate issue job closes a quality-gate issue when the gate
    passes. A run on a pull request closes the one issue of that pull request.
    A run on main closed every open issue that named the gate, because main is
    authoritative for main.

    That second rule reached too far. An issue with the title
    "CI: quality-gate `black` failed (PR #2622)" belongs to pull request #2622.
    A `black` pass on main closed it, although pull request #2622 stayed open
    and its own `black` job still failed. Issue #2623 closed that way twice,
    and the second close came 13 seconds after an operator reopened it.

    Issue #3487 moved the job body to `reusable-quality-gate-issues.yml` in
    misthelper-devtools. That shared script keeps the issue of an open pull
    request, and the shared repository tests it. These tests hold the wiring in
    the CI workflow of this repository. The workflow must call the pinned
    shared workflow, pass the result of each gate, and keep its scope. A
    workflow that brings back an inline copy of the job fails.

    Issue #3515 deleted the portable template .github/quality-gates-portable.yml.
    Another repository calls the shared quality gate workflow instead.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]

CI_WORKFLOW = Path(".github/workflows/ci.yml")
WORKFLOW_FILES = (CI_WORKFLOW,)

JOB_NAME = "quality_gate_issues"

# The shared workflow and the full-commit form of its reference.
SHARED_CALL = re.compile(
    r"^jmorrison-juniper/misthelper-devtools/\.github/workflows/reusable-quality-gate-issues\.yml@[0-9a-f]{40}$"
)

# The scope of each file. A pull request run in this repository opens an issue
# whose title names the pull request.
EXPECTED_SCOPE: dict[Path, str | None] = {CI_WORKFLOW: "all"}

# The gates of each file. A gate that leaves this list opens no issue when it fails.
QUALITY_GATES = {
    "ruff",
    "black",
    "mypy",
    "pytest",
    "bandit",
    "pip_audit",
    "pylint",
    "radon",
    "vulture",
    "pydocstyle",
    "interrogate",
}
EXPECTED_GATES: dict[Path, set[str]] = {
    CI_WORKFLOW: QUALITY_GATES | {"codeql_register_check", "ops_portal", "ops_platform_pytest"},
}

# The job names that the inline copies used before issue #3487.
RETIRED_JOBS = ("create_failure_issues", "close_resolved_issues")


def issue_job(relative_path: Path) -> dict[str, Any]:
    """Return the quality-gate issue job of one workflow file.

    Args:
        relative_path: The workflow path, relative to the repository root.

    Returns:
        The job mapping.
    """
    document = yaml.safe_load((REPOSITORY_ROOT / relative_path).read_text(encoding="utf-8"))
    job = document["jobs"][JOB_NAME]  # A missing job raises here, which is the correct report.
    assert isinstance(job, dict), f"{relative_path} holds no job mapping named {JOB_NAME!r}"
    return job


class TestTheWorkflowCallsTheSharedJob:
    """The CI workflow must hand the gate results to the shared job."""

    @pytest.mark.parametrize("relative_path", WORKFLOW_FILES, ids=lambda path: path.name)
    def test_the_job_calls_the_pinned_shared_workflow(self, relative_path: Path) -> None:
        """The shared script holds the open pull request skip that repairs issue #2623."""
        uses = str(issue_job(relative_path).get("uses", ""))
        assert SHARED_CALL.match(uses), f"{relative_path} must call the shared workflow at a full commit: {uses!r}"

    @pytest.mark.parametrize("relative_path", WORKFLOW_FILES, ids=lambda path: path.name)
    def test_the_job_passes_each_gate_result(self, relative_path: Path) -> None:
        """The shared job reads each gate result from the needs context."""
        results = issue_job(relative_path)["with"]["results"]
        assert results == "${{ toJSON(needs) }}", f"{relative_path} must pass the whole needs context"

    @pytest.mark.parametrize("relative_path", WORKFLOW_FILES, ids=lambda path: path.name)
    def test_the_job_reads_each_gate(self, relative_path: Path) -> None:
        """The needs list is the gate list, so a dropped gate opens no issue."""
        needs = issue_job(relative_path)["needs"]
        assert len(needs) == len(set(needs)), f"{relative_path} names a gate twice"
        assert set(needs) == EXPECTED_GATES[relative_path], f"{relative_path} changed its gate list"

    @pytest.mark.parametrize("relative_path", WORKFLOW_FILES, ids=lambda path: path.name)
    def test_the_job_runs_after_a_failed_gate(self, relative_path: Path) -> None:
        """Without always(), a failed gate skips the job that must open its issue."""
        condition = issue_job(relative_path)["if"]
        assert "always()" in condition, f"{relative_path} must run the job after a failed gate"

    @pytest.mark.parametrize("relative_path", WORKFLOW_FILES, ids=lambda path: path.name)
    def test_the_job_can_read_the_pull_request_state(self, relative_path: Path) -> None:
        """The skip reads the state of the named pull request, so the job needs that scope."""
        permissions = issue_job(relative_path)["permissions"]
        assert permissions == {"issues": "write", "pull-requests": "read"}, f"{relative_path} changed the scopes"

    @pytest.mark.parametrize("relative_path", WORKFLOW_FILES, ids=lambda path: path.name)
    def test_the_scope_is_unchanged(self, relative_path: Path) -> None:
        """A scope change moves the runs that may open or close an issue."""
        scope = issue_job(relative_path)["with"].get("scope")
        assert scope == EXPECTED_SCOPE[relative_path], f"{relative_path} changed its scope to {scope!r}"

    @pytest.mark.parametrize("relative_path", WORKFLOW_FILES, ids=lambda path: path.name)
    def test_no_inline_copy_remains(self, relative_path: Path) -> None:
        """An inline copy would run beside the shared job and could close the issue of an open pull request."""
        document = yaml.safe_load((REPOSITORY_ROOT / relative_path).read_text(encoding="utf-8"))
        for name in RETIRED_JOBS:
            assert name not in document["jobs"], f"{relative_path} brings back the inline job {name!r}"
