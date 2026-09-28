"""Contract tests for the Mermaid syntax gate.

Issue #3515 moved the parser to the `mermaid-lint` action of misthelper-devtools.
The devtools tests prove that the parser rejects a broken block. These tests
hold the wiring in this repository: the gate keeps its job, calls the shared
action at a full commit, and scans the same files as before.
"""

import re  # Match the full commit at the end of the action reference.
from pathlib import Path  # Build paths without platform-specific separators.
from typing import Any  # Type the parsed workflow mapping.

import pytest  # Share one parsed workflow across the tests.
import yaml  # Read the workflow as data, not as text.

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]  # Locate the repository from this test file.
WORKFLOW_PATH = REPOSITORY_ROOT / ".github" / "workflows" / "ci.yml"  # Identify the CI workflow contract.
GATE_JOB = "mermaid_lint"  # The job that owns the required check name.
ACTION_PREFIX = "jmorrison-juniper/misthelper-devtools/.github/actions/mermaid-lint@"  # The shared action.
FULL_COMMIT = re.compile(r"@[0-9a-f]{40}$")  # A tag or a branch can move without a change here.


@pytest.fixture(scope="module")
def gate_job() -> dict[str, Any]:
    """Return the Mermaid gate job from the real workflow."""
    workflow = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))  # Read the workflow contract.
    assert isinstance(workflow, dict), "The workflow must parse to a mapping."
    assert GATE_JOB in workflow["jobs"], "The workflow must keep a dedicated Mermaid syntax gate."
    return workflow["jobs"][GATE_JOB]


def test_the_gate_keeps_its_check_name(gate_job: dict[str, Any]) -> None:
    """Keep the check name that branch protection requires."""
    assert gate_job["name"] == "Mermaid syntax lint"


def test_the_gate_calls_the_shared_action_at_a_full_commit(gate_job: dict[str, Any]) -> None:
    """Require one call to the shared action, pinned so it cannot move."""
    calls = [step["uses"] for step in gate_job["steps"] if str(step.get("uses", "")).startswith(ACTION_PREFIX)]
    assert len(calls) == 1, "The gate must call the shared mermaid-lint action once."
    assert FULL_COMMIT.search(calls[0]), f"The action call must pin a full commit: {calls[0]!r}"


def test_the_gate_scans_the_documentation_and_the_readme(gate_job: dict[str, Any]) -> None:
    """Scan the same Markdown files that the local parser scanned."""
    step = next(step for step in gate_job["steps"] if str(step.get("uses", "")).startswith(ACTION_PREFIX))
    assert step["with"]["docs-dir"] == "documentation"
    assert step["with"]["extra-files"] == "README.md"


def test_the_gate_runs_no_local_parser(gate_job: dict[str, Any]) -> None:
    """Keep a second copy of the parser out of this repository."""
    commands = "\n".join(str(step.get("run", "")) for step in gate_job["steps"])
    assert "lint_mermaid.mjs" not in commands
    assert not (REPOSITORY_ROOT / "scripts" / "mermaid").exists()
