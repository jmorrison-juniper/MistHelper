"""Verify that CI checks the dependency lock and its exports."""

import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
import yaml

WORKFLOW = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "ci.yml"
RESULT_CHECK = """\
if [ "$LOCK_RESULT" != "success" ]; then
  echo "::error::The dependency lock job finished with $LOCK_RESULT."
  exit 1
fi
"""


class DependencyLockWorkflow:
    """Identify missing or optional checks in the dependency lock job."""

    @staticmethod
    def defects(workflow: dict[str, Any]) -> list[str]:
        """Report changes that prevent the lock and export checks from blocking."""
        job = workflow.get("jobs", {}).get("dependency_lock")
        if not isinstance(job, dict):
            return ["dependency_lock job is missing"]
        defects = []
        if "if" in job or "needs" in job or job.get("continue-on-error"):
            defects.append("dependency_lock job must always block")
        steps = job.get("steps", [])
        for command in ("uv lock --check", "python -m pytest -s -q tests/guardrails/test_dependency_export.py"):
            if not any(
                isinstance(step, dict)
                and step.get("run") == command
                and "if" not in step
                and not step.get("continue-on-error")
                for step in steps
            ):
                defects.append(f"missing blocking command: {command}")
        if "dependency_lock" not in workflow["jobs"]["quality_gate_issues"]["needs"]:
            defects.append("quality_gate_issues must report dependency_lock")
        return defects

    @staticmethod
    def aggregation_defects(workflow: dict[str, Any]) -> list[str]:
        """Report changes that let the required pytest gate ignore the lock result."""
        job = workflow["jobs"]["pytest"]
        defects = []
        if job.get("name") != "pytest (coverage gate)" or job.get("if") != "${{ !cancelled() }}":
            defects.append("required pytest gate must run after unsuccessful dependencies")
        if not {"pytest_coverage_shards", "dependency_lock"}.issubset(job.get("needs", [])):
            defects.append("required pytest gate must depend on coverage and dependency_lock")
        step = job.get("steps", [{}])[0]
        if step.get("run") != RESULT_CHECK or step.get("env") != {"LOCK_RESULT": "${{ needs.dependency_lock.result }}"}:
            defects.append("required pytest gate must check the dependency_lock result first")
        if "if" in step or step.get("continue-on-error") or job.get("continue-on-error"):
            defects.append("dependency_lock result check must block")
        return defects


class TestDependencyLockWorkflow:
    """Check the live workflow and prove that missing checks fail."""

    @pytest.fixture
    def workflow(self) -> dict[str, Any]:
        """Read the actual workflow so missing input cannot pass."""
        workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
        assert isinstance(workflow, dict)
        return workflow

    def test_live_job_blocks_on_lock_and_export_drift(self, workflow: dict[str, Any]) -> None:
        """Require both checks and their issue reporting."""
        defects = DependencyLockWorkflow.defects(workflow)
        print(f"Examined 1 dependency lock job, {len(defects)} defects")
        assert defects == []

    @pytest.mark.parametrize(
        "mutation",
        ["missing_job", "skip_job", "dependent_job", "optional_job", "skip_lock", "skip_export", "missing_report"],
    )
    def test_contract_rejects_missing_or_optional_checks(self, workflow: dict[str, Any], mutation: str) -> None:
        """Prove that each omitted or optional check is detected."""
        candidate = deepcopy(workflow)
        job = candidate["jobs"]["dependency_lock"]
        if mutation == "missing_job":
            del candidate["jobs"]["dependency_lock"]
        elif mutation == "skip_job":
            job["if"] = "${{ false }}"
        elif mutation == "dependent_job":
            job["needs"] = ["ruff"]
        elif mutation == "optional_job":
            job["continue-on-error"] = True
        elif mutation == "skip_lock":
            next(step for step in job["steps"] if step.get("run") == "uv lock --check")["continue-on-error"] = True
        elif mutation == "skip_export":
            next(step for step in job["steps"] if "test_dependency_export.py" in step.get("run", ""))["if"] = "false"
        else:
            candidate["jobs"]["quality_gate_issues"]["needs"].remove("dependency_lock")
        assert DependencyLockWorkflow.defects(candidate) != []

    def test_required_pytest_gate_checks_lock_result(self, workflow: dict[str, Any]) -> None:
        """Require the coverage gate to include the lock job result."""
        defects = DependencyLockWorkflow.aggregation_defects(workflow)
        print(f"Examined 1 required pytest gate, {len(defects)} defects")
        assert defects == []

    @pytest.mark.skipif(sys.platform == "win32", reason="The workflow runs this Bash step on Ubuntu.")
    @pytest.mark.parametrize("status", ["success", "failure", "skipped", "cancelled", ""])
    def test_lock_result_step_accepts_only_success(self, workflow: dict[str, Any], status: str) -> None:
        """Prove that a non-success result cannot pass the required gate."""
        step = workflow["jobs"]["pytest"]["steps"][0]
        assert step["run"] == RESULT_CHECK
        result = subprocess.run(
            ["bash", "-e", "-c", step["run"]], env={"LOCK_RESULT": status}, capture_output=True, text=True, check=False
        )
        assert result.returncode == (0 if status == "success" else 1)

    @pytest.mark.parametrize("mutation", ["missing_need", "skip_gate", "missing_check", "optional_check", "bypass"])
    def test_aggregation_contract_rejects_mutations(self, workflow: dict[str, Any], mutation: str) -> None:
        """Prove that a removed or bypassed aggregation cannot pass."""
        candidate = deepcopy(workflow)
        job = candidate["jobs"]["pytest"]
        if mutation == "missing_need":
            job["needs"].remove("dependency_lock")
        elif mutation == "skip_gate":
            job.pop("if")
        elif mutation == "missing_check":
            job["steps"].pop(0)
        elif mutation == "optional_check":
            job["steps"][0]["continue-on-error"] = True
        else:
            job["steps"][0]["run"] = "echo accepted"
        assert DependencyLockWorkflow.aggregation_defects(candidate) != []
