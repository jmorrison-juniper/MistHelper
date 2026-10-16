"""Prove that the E2E shards run each browser test file exactly one time (issue #4250).

The full browser suite ran in one job and reached the 20-minute job limit. The
workflow now runs one matrix row for each directory of ``tests/e2e``, and the
job ``playwright`` keeps the required check name "E2E smoke tests". This guard
reads the live workflow and the live test tree. It fails when a test file has
no shard, when a test file has two shards, when a shard narrows the selection,
or when the required gate stops failing on a shard result other than success.
"""

import copy
import logging
from pathlib import Path
from typing import Any

import pytest
import yaml

logger = logging.getLogger(__name__)  # WHY: keep the guard records on the module logger.

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]  # Resolve paths from the test, not the working directory.
WORKFLOW_PATH = REPOSITORY_ROOT / ".github" / "workflows" / "ci.yml"  # The workflow that runs the browser gate.
E2E_ROOT = REPOSITORY_ROOT / "tests" / "e2e"  # The tree that the old single job collected.
REQUIRED_ARGUMENTS = (  # The options of the old single job that each shard must keep.
    "-v",
    "--base-url=http://127.0.0.1:${CAPTURE_PORT}",
    "--timeout=180",
    "--screenshot only-on-failure",
    "--tracing retain-on-failure",
    "--output=${{ github.workspace }}/test-artifacts/issue-4229-browser",
)
NARROWING_ARGUMENTS = ("--ignore", "--deselect", " -k ", " -m ", "--lf", "--last-failed", "-x ", "--exitfirst")


class ShardPartitionAudit:
    """Read the shard rows and the aggregator, and report each defect as an assertion."""

    @staticmethod
    def workflow() -> dict[str, Any]:
        """Parse the live workflow, so an absent or malformed file fails the guard."""
        return yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))  # Read the shipped workflow as data.

    @staticmethod
    def test_files() -> list[Path]:
        """Return each file under tests/e2e that the pytest file patterns collect."""
        names = set(E2E_ROOT.rglob("test_*.py")) | set(E2E_ROOT.rglob("*_test.py"))  # Use the pyproject patterns.
        files = sorted(path for path in names if "__pycache__" not in path.parts)  # Skip compiled caches.
        assert len(files) > 0, f"No E2E test file under {E2E_ROOT}"  # An empty input must fail, not pass.
        return files

    @staticmethod
    def shard_paths(workflow: dict[str, Any]) -> dict[str, list[Path]]:
        """Map each shard name to the absolute paths that its row runs."""
        rows = workflow["jobs"]["playwright_shards"]["strategy"]["matrix"]["include"]  # Read each explicit row.
        return {row["shard"]: [REPOSITORY_ROOT / part for part in row["test_paths"].split()] for row in rows}

    @classmethod
    def check_partition(cls, workflow: dict[str, Any]) -> int:
        """Require that each test file belongs to exactly one shard, and return the file count."""
        shards = cls.shard_paths(workflow)  # Read the declared rows.
        files = cls.test_files()  # Read the live tree.
        for name, paths in shards.items():  # Each declared path must exist inside tests/e2e.
            for path in paths:
                assert path.is_dir() and E2E_ROOT in path.parents, f"Shard {name} names a bad path: {path}"
        for test_file in files:  # Each file must have one owner.
            owners = [name for name, paths in shards.items() if any(path in test_file.parents for path in paths)]
            assert len(owners) == 1, f"{test_file.relative_to(REPOSITORY_ROOT)} runs in shards {owners}"
        print(f"e2e_shard_partition: checked {len(files)} test files in {len(shards)} shards")
        return len(files)

    @staticmethod
    def check_command(workflow: dict[str, Any]) -> int:
        """Require the unchanged options, refuse a narrowing option, and return the rule count."""
        steps = workflow["jobs"]["playwright_shards"]["steps"]  # Read the shard steps.
        runs = [step["run"] for step in steps if "pytest ${E2E_TEST_PATHS}" in step.get("run", "")]
        assert len(runs) == 1, "Each shard must run exactly one pytest command"
        for argument in REQUIRED_ARGUMENTS:  # Keep each option of the old single job.
            assert argument in runs[0], f"The shard command lost {argument}"
        for argument in NARROWING_ARGUMENTS:  # A narrowing option changes the collection.
            assert argument not in runs[0], f"The shard command narrows the selection with {argument.strip()}"
        assert "set -o pipefail" in runs[0], "The tee pipe must keep the pytest exit status"
        return len(REQUIRED_ARGUMENTS) + len(NARROWING_ARGUMENTS) + 1  # Count each rule that the audit applied.

    @staticmethod
    def check_gate(workflow: dict[str, Any]) -> str:
        """Require that the required check fails on a bad shard result, and return its name."""
        gate = workflow["jobs"]["playwright"]  # The job that branch protection reads by name.
        assert gate["name"] == "E2E smoke tests", "The required check name changed"
        assert gate["needs"] == ["playwright_shards"], "The gate must wait for the shard matrix"
        assert gate["if"] == "${{ !cancelled() }}", "The gate must run after a failed shard"
        script = "\n".join(step.get("run", "") for step in gate["steps"])  # Join each shell line of the gate.
        assert '"${{ needs.playwright_shards.result }}" != "success"' in script, "The gate must compare the result"
        assert "exit 1" in script, "The gate must fail on a result other than success"
        return gate["name"]  # Give the checked name to the caller.


@pytest.fixture
def workflow() -> dict[str, Any]:
    """Give each test its own copy of the live workflow."""
    return ShardPartitionAudit.workflow()


def test_each_e2e_test_file_runs_in_exactly_one_shard(workflow: dict[str, Any]) -> None:
    """The union of the shards is the full tree, and no two shards overlap."""
    assert ShardPartitionAudit.check_partition(workflow) > 0  # The count proves that the guard read files.


def test_each_shard_keeps_the_options_of_the_single_job(workflow: dict[str, Any]) -> None:
    """Each shard keeps the timeout, the trace, the screenshot, and the output options."""
    expected = len(REQUIRED_ARGUMENTS) + len(NARROWING_ARGUMENTS) + 1  # Each option, each refusal, and pipefail.
    assert ShardPartitionAudit.check_command(workflow) == expected


def test_the_required_gate_reads_the_shard_result(workflow: dict[str, Any]) -> None:
    """The "E2E smoke tests" check fails when a shard is not a success."""
    assert ShardPartitionAudit.check_gate(workflow) == "E2E smoke tests"


@pytest.mark.parametrize("mutation", ["gap", "overlap", "outside"])
def test_a_bad_partition_fails(workflow: dict[str, Any], mutation: str) -> None:
    """Prove that the partition audit can fail for a gap, an overlap, and a path outside the tree."""
    rows = workflow["jobs"]["playwright_shards"]["strategy"]["matrix"]["include"]  # Edit the parsed rows.
    if mutation == "gap":
        rows.pop()  # Drop one directory, so its files have no shard.
    elif mutation == "overlap":
        rows.append({"shard": "everything", "test_paths": "tests/e2e"})  # Run each file a second time.
    else:
        rows[0]["test_paths"] = "tests/unit"  # Point a shard at a tree that is not E2E.
    with pytest.raises(AssertionError):
        ShardPartitionAudit.check_partition(workflow)


@pytest.mark.parametrize("mutation", ["-k smoke", "--ignore=tests/e2e/web_portal", "--timeout=600", "pipefail"])
def test_a_changed_command_fails(workflow: dict[str, Any], mutation: str) -> None:
    """Prove that the command audit refuses a narrowed selection, a changed timeout, and a lost exit status."""
    steps = copy.deepcopy(workflow["jobs"]["playwright_shards"]["steps"])  # Edit a copy of the steps.
    step = next(step for step in steps if "pytest ${E2E_TEST_PATHS}" in step.get("run", ""))
    if mutation == "--timeout=600":
        step["run"] = step["run"].replace("--timeout=180", mutation)  # Weaken the per-test timeout.
    elif mutation == "pipefail":
        step["run"] = step["run"].replace("set -o pipefail", "")  # Let tee hide the pytest status.
    else:
        step["run"] = step["run"].replace("pytest ${E2E_TEST_PATHS}", f"pytest ${{E2E_TEST_PATHS}} {mutation}")
    workflow["jobs"]["playwright_shards"]["steps"] = steps
    with pytest.raises(AssertionError):
        ShardPartitionAudit.check_command(workflow)


@pytest.mark.parametrize("mutation", ["name", "needs", "if", "compare", "exit"])
def test_a_weak_gate_fails(workflow: dict[str, Any], mutation: str) -> None:
    """Prove that the gate audit refuses each change that lets a bad shard pass."""
    gate = workflow["jobs"]["playwright"]  # Edit the parsed gate.
    if mutation == "name":
        gate["name"] = "E2E shards"
    elif mutation == "needs":
        gate["needs"] = ["pip_audit"]
    elif mutation == "if":
        gate["if"] = "${{ success() }}"
    else:
        old = '!= "success"' if mutation == "compare" else "exit 1"
        gate["steps"] = [{**step, "run": step.get("run", "").replace(old, "")} for step in gate["steps"]]
    with pytest.raises(AssertionError):
        ShardPartitionAudit.check_gate(workflow)
    logger.debug("The gate audit refused the %s mutation", mutation)  # Record the proof for a failure read.
