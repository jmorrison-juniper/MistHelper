"""Keep firmware comparison screenshots and failed browser flows in CI evidence."""

from pathlib import Path
from typing import Any

import pytest
import yaml


class TestBrowserEvidence:
    """Check the live evidence contract and prove that missing evidence fails."""

    @staticmethod
    def configuration() -> dict[str, Any]:
        """Read the live workflow so absent or malformed input fails the guard."""
        workflow = Path(__file__).resolve().parents[4] / ".github" / "workflows" / "ci.yml"
        return yaml.safe_load(workflow.read_text(encoding="utf-8"))

    @staticmethod
    def check(configuration: dict[str, Any]) -> int:
        """Require existing evidence, comparison screenshots, and failed-flow traces."""
        steps = configuration["jobs"]["playwright"]["steps"]
        upload = next(step for step in steps if step.get("with", {}).get("name") == "firmware-policy-browser-evidence")
        expected = {
            "test-artifacts/issue-4229-*.png",
            "test-artifacts/issue-4229-browser/",
        }
        assert expected.issubset(upload["with"]["path"].splitlines()), "Required browser evidence paths are missing"
        command = next(step["run"] for step in steps if step.get("run", "").startswith("pytest tests/e2e/"))
        for argument in (
            "--screenshot only-on-failure",
            "--tracing retain-on-failure",
            "--output=test-artifacts/issue-4229-browser",
        ):
            assert argument in command, "Required browser evidence capture is missing"
        print("browser_evidence: checked 2 artifact paths and 3 capture arguments")
        return len(set(upload["with"]["path"].splitlines()))

    def test_live_workflow_retains_comparison_evidence(self) -> None:
        """Require the declared main-flow screenshots and failed-flow evidence."""
        assert self.check(self.configuration()) == 2

    @pytest.mark.parametrize("mutation", ["paths", "screenshot", "tracing", "output"])
    def test_missing_evidence_fails(self, mutation: str) -> None:
        """Reject a workflow that loses either evidence paths or capture arguments."""
        configuration = self.configuration()
        steps = configuration["jobs"]["playwright"]["steps"]
        if mutation == "paths":
            upload = next(
                step for step in steps if step.get("with", {}).get("name") == "firmware-policy-browser-evidence"
            )
            upload["with"]["path"] = "test-artifacts/issue4218-*.png"
        else:
            execution = next(step for step in steps if step.get("run", "").startswith("pytest tests/e2e/"))
            execution["run"] = execution["run"].replace("--" + mutation, "--removed")
        with pytest.raises(AssertionError, match="browser evidence"):
            self.check(configuration)
