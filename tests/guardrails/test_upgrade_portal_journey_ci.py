"""Guard the bounded CI job for the issue #3200 journey harness."""

from copy import deepcopy  # The mutation test needs an isolated workflow copy.
from pathlib import Path  # Resolve the workflow without a fixed checkout path.
from typing import Any  # PyYAML returns general mapping values.

import pytest  # Prove that weakened job contracts fail.
import yaml  # Parse the workflow as structured data.


class JourneyJobConstants:
    """Keep the live workflow path and expected contract values together."""

    ROOT = Path(__file__).resolve().parents[2]  # The test path identifies this checkout.
    PATH = ROOT / ".github" / "workflows" / "ci.yml"  # Read the live CI contract.
    JOB = "upgrade_portal_journeys"  # Keep the new gate's workflow key stable.
    COMMAND = "python -m tests.e2e.upgrade_portal.journeys.run_journeys --parallel 1"  # Bound workers.


class JourneyJobContract:
    """Check that CI runs the isolated journeys and keeps their reports."""

    @staticmethod
    def check_identity(workflow: dict[str, Any]) -> int:
        """Keep the job name and its ordering stable."""
        job = workflow["jobs"][JourneyJobConstants.JOB]  # Select the new journey job.
        assert job["name"] == "Upgrade portal journeys"  # Keep the reported status clear.
        assert job["needs"] == ["playwright"]  # Wait for the shared browser suite.
        return 2  # Count the checked identity rules.

    @staticmethod
    def check_bounds(workflow: dict[str, Any]) -> int:
        """Bound runtime and prevent external service use."""
        job = workflow["jobs"][JourneyJobConstants.JOB]  # Read the job that owns the worker.
        assert job["if"] == "${{ !cancelled() }}"  # Run after failure but stop on cancellation.
        assert job["timeout-minutes"] == 30  # Cap the total worker time.
        assert "services" not in job  # Keep the harness on its simulated cloud boundary.
        return 3  # Count the checked safety rules.

    @staticmethod
    def check_command(workflow: dict[str, Any]) -> int:
        """Require dependencies, Chromium, and the complete journey command."""
        steps = workflow["jobs"][JourneyJobConstants.JOB]["steps"]  # Read the executable job steps.
        commands = "\n".join(step["run"] for step in steps if "run" in step)  # Join multiline commands.
        required_commands = (  # Require both installs and the complete browser journey.
            "python -m pip install -r requirements.txt",
            "python -m pip install -r requirements-dev.txt",
            "python -m playwright install --with-deps chromium",
            JourneyJobConstants.COMMAND,
        )
        assert all(command in commands for command in required_commands)  # Require the full browser setup.
        return 3  # Count the checked execution rules.

    @staticmethod
    def check_artifact(workflow: dict[str, Any]) -> int:
        """Require one upload with the complete journey report directory."""
        steps = workflow["jobs"][JourneyJobConstants.JOB]["steps"]  # Read the job that writes the reports.
        uploads = [
            step for step in steps if step.get("uses", "").startswith("actions/upload-artifact@")
        ]  # Match upload actions.
        assert len(uploads) == 1  # Reject missing or duplicate report uploads.
        upload = uploads[0]  # Select the only upload action.
        assert (upload["uses"], upload["if"], upload["with"]) == (  # Pin each artifact property.
            "actions/upload-artifact@v7",
            "${{ !cancelled() }}",
            {
                "name": "upgrade-portal-journeys",
                "path": "test-artifacts/upgrade-portal-journeys/",
                "if-no-files-found": "error",
            },
        )  # Fail on a missing or weakened artifact value.
        return 6  # Count the upload, action, condition, name, path, and missing-file rule.

    @staticmethod
    def check_issue_sync(workflow: dict[str, Any]) -> int:
        """Check that the failure reporter receives the journey job result."""
        needs = workflow["jobs"]["quality_gate_issues"]["needs"]  # Read the issue reporter dependencies.
        assert JourneyJobConstants.JOB in needs  # Keep journey failures visible to the shared reporter.
        return 1  # Count the checked reporting rule.


class TestUpgradePortalJourneyCi:
    """Run the workflow contract and prove that weakened values fail."""

    @staticmethod
    def load_workflow() -> dict[str, Any]:
        """Read the CI workflow and fail when the file is absent or invalid."""
        workflow = yaml.safe_load(JourneyJobConstants.PATH.read_text(encoding="utf-8"))  # Read live YAML.
        assert isinstance(workflow, dict), f"The workflow must be a mapping: {JourneyJobConstants.PATH}"
        return workflow

    def test_ci_runs_bounded_journeys_and_uploads_evidence(self) -> None:
        """Require the full isolated run, its artifact, and issue reporting."""
        workflow = self.load_workflow()  # Read the workflow before each contract pass.
        checked = sum(  # Count every live rule that the contract applies.
            (
                JourneyJobContract.check_identity(workflow),
                JourneyJobContract.check_bounds(workflow),
                JourneyJobContract.check_command(workflow),
                JourneyJobContract.check_artifact(workflow),
                JourneyJobContract.check_issue_sync(workflow),
            )
        )
        print(f"upgrade_portal_journey_ci: checked {checked} workflow rules")  # Report the measured scope.
        assert checked == 15  # Fail if the guard stops checking one of its declared rules.

    @pytest.mark.parametrize("mutation", ["command", "timeout", "artifact", "issue-sync"])
    def test_contract_rejects_a_missing_journey_requirement(self, mutation: str) -> None:
        """Prove that the guard fails when the job, report, or issue sync weakens."""
        candidate = deepcopy(self.load_workflow())  # Preserve the live workflow for the other scenarios.
        job = candidate["jobs"][JourneyJobConstants.JOB]  # Select the mutable job copy.
        if mutation == "command":  # Remove the required full-run command.
            command = next(  # Select the command that must remain in the job.
                step for step in job["steps"] if step.get("run") == JourneyJobConstants.COMMAND
            )
            command["run"] = "pytest"  # Replace it with an incomplete test command.
        elif mutation == "timeout":  # Widen the declared runtime bound.
            job["timeout-minutes"] = 60  # Make the time limit violate the contract.
        elif mutation == "artifact":  # Point the upload at a missing location.
            upload = next(  # Select the only report upload action.
                step for step in job["steps"] if step.get("uses", "").startswith("actions/upload-artifact@")
            )
            upload["with"]["path"] = "missing/"  # Remove the required report directory.
        elif mutation == "issue-sync":  # Hide the job from failure reporting.
            candidate["jobs"]["quality_gate_issues"]["needs"].remove(JourneyJobConstants.JOB)  # Drop its result.
        else:
            pytest.fail(f"Unknown mutation: {mutation}")  # Reject an untested scenario.
        with pytest.raises(AssertionError):  # Require each weakened workflow to fail.
            if mutation == "artifact":  # Check the altered artifact rule.
                JourneyJobContract.check_artifact(candidate)
            elif mutation == "issue-sync":  # Check the altered failure report.
                JourneyJobContract.check_issue_sync(candidate)
            else:
                (
                    JourneyJobContract.check_bounds(candidate)
                    if mutation == "timeout"
                    else JourneyJobContract.check_command(candidate)
                )
