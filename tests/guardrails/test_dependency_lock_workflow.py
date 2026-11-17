"""Verify that CI checks the dependency lock and its exports."""

from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
import yaml

WORKFLOW = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "ci.yml"


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
