"""Contract tests for the root pytest coverage gate."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pytest
import yaml

_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]  # Locate the repository from the contract test package.
_WORKFLOW_PATH = _REPOSITORY_ROOT / ".github" / "workflows" / "ci.yml"  # Read the required quality gate workflow.


class CoverageGateWorkflow:
    """Read coverage gate settings from the workflow file."""

    def __init__(self, workflow_path: Path) -> None:
        """Store the workflow path for all contract checks."""
        logging.info("Storing the workflow path %s", workflow_path)  # Record the workflow path before use.
        self.workflow_path = workflow_path  # Keep the path as state for repeated reads.
        logging.debug("Stored workflow path %s", self.workflow_path)  # Confirm the path that later checks read.

    def load(self) -> dict[str, Any]:
        """Return the parsed workflow mapping."""
        logging.info("Reading workflow file %s", self.workflow_path)  # Record the file read before it starts.
        document = yaml.safe_load(self.workflow_path.read_text(encoding="utf-8"))  # Parse the workflow safely.
        logging.debug("Parsed workflow with %d top-level keys", len(document))  # Record the parsed shape.
        assert isinstance(document, dict), "The workflow must parse as a mapping."  # Fail early on invalid YAML.
        return document  # Return the parsed workflow for the tests.

    def job(self, job_name: str) -> dict[str, Any]:
        """Return one workflow job by identifier."""
        logging.info("Reading the workflow job %s", job_name)  # Record the job lookup before it starts.
        jobs = self.load()["jobs"]  # Read all jobs from the parsed workflow.
        job = jobs[job_name]  # Select the expected job by stable identifier.
        logging.debug("The workflow job %s has %d keys", job_name, len(job))  # Record the selected job shape.
        return dict(job)  # Return a copy so tests cannot mutate shared data.


@pytest.fixture(name="coverage_workflow", scope="module")
def fixture_coverage_workflow() -> CoverageGateWorkflow:
    """Return the coverage gate workflow reader."""
    logging.info("Creating the coverage workflow reader")  # Record fixture construction.
    reader = CoverageGateWorkflow(_WORKFLOW_PATH)  # Create the reader around the workflow path.
    logging.debug("Created the coverage workflow reader")  # Confirm fixture construction.
    return reader  # Provide the reader to each contract test.


class TestCoverageGateShards:
    """Verify that the coverage gate stays split and complete."""

    def test_shards_run_in_parallel(self, coverage_workflow: CoverageGateWorkflow) -> None:
        """The coverage suite MUST run in matrix shards."""
        logging.info("Checking that the shard job uses a matrix")  # Record the workflow assertion.
        shard_job = coverage_workflow.job("pytest_coverage_shards")  # Read the shard job from the workflow.
        matrix = shard_job["strategy"]["matrix"]["include"]  # Read the explicit shard list.
        logging.debug("The shard matrix contains %d entries", len(matrix))  # Record the shard count.
        assert len(matrix) >= 4, "The root coverage suite must run in at least four shards."  # Keep headroom.

    def test_each_shard_uploads_hidden_coverage_data(self, coverage_workflow: CoverageGateWorkflow) -> None:
        """Each shard MUST upload its coverage data file."""
        logging.info("Checking the shard artifact upload")  # Record the artifact assertion.
        shard_job = coverage_workflow.job("pytest_coverage_shards")  # Read the shard job from the workflow.
        upload_step = next(
            step for step in shard_job["steps"] if step.get("name") == "Upload coverage data"
        )  # Find upload.
        logging.debug("The upload step uses %s", upload_step["uses"])  # Record the action version.
        assert upload_step["with"]["include-hidden-files"] is True  # Keep hidden .coverage files in artifacts.

    def test_shards_do_not_apply_the_final_threshold(self, coverage_workflow: CoverageGateWorkflow) -> None:
        """Each shard MUST leave the threshold to the final gate."""
        logging.info("Checking that shards disable per-shard coverage failure")  # Record the threshold assertion.
        shard_job = coverage_workflow.job("pytest_coverage_shards")  # Read the shard job from the workflow.
        test_step = next(
            step for step in shard_job["steps"] if step.get("name") == "Run tests with coverage"
        )  # Find run.
        command = str(test_step["run"])  # Normalize the shell block for substring checks.
        logging.debug("The shard test step contains %d characters", len(command))  # Record command size, not content.
        assert "--cov-fail-under=0" in command  # Prevent partial shards from enforcing the global threshold.

    def test_final_gate_keeps_required_check_name(self, coverage_workflow: CoverageGateWorkflow) -> None:
        """The final job MUST keep the required coverage check name."""
        logging.info("Checking the final coverage gate name")  # Record the required-check assertion.
        final_job = coverage_workflow.job("pytest")  # Read the final job that branch protection sees.
        logging.debug("The final coverage job name is %s", final_job["name"])  # Record the check name.
        assert final_job["name"] == "pytest (coverage gate)"  # Preserve the required check name.

    def test_final_gate_combines_reports_once(self, coverage_workflow: CoverageGateWorkflow) -> None:
        """The final job MUST combine shard data before enforcing coverage."""
        logging.info("Checking the coverage combine command")  # Record the final command assertion.
        final_job = coverage_workflow.job("pytest")  # Read the final job from the workflow.
        combine_step = next(
            step for step in final_job["steps"] if step.get("name") == "Combine coverage and enforce threshold"
        )  # Find combine.
        command = str(combine_step["run"])  # Normalize the shell block for substring checks.
        logging.debug("The combine step contains %d characters", len(command))  # Record command size, not content.
        assert "coverage combine --keep coverage-data" in command  # Require a combined report.
        assert "--fail-under=${{ env.COVERAGE_THRESHOLD }}" in command  # Keep the unchanged threshold variable.
