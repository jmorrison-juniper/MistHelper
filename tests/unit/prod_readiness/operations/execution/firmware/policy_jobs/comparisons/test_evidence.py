"""Keep firmware comparison screenshots and failed browser flows in CI evidence."""

from pathlib import Path
from typing import Any

import pytest
import yaml

from tests.e2e.web_portal.firmware_restore.evidence import BrowserEvidence


def _repository_root() -> Path:  # Find the root by its live workflow file.
    """Locate the repository root after test-package moves."""
    for parent in Path(__file__).resolve().parents:  # Check each parent path.
        workflow = parent / ".github" / "workflows" / "ci.yml"  # Use the required repository marker.
        if workflow.is_file():  # Stop at the live CI configuration.
            return parent  # Keep test evidence paths rooted in the repository.
    raise FileNotFoundError("Could not locate the repository root from this test module.")  # Fail without a fallback.


class TestBrowserEvidence:
    """Check the live evidence contract and prove that missing evidence fails."""

    @staticmethod
    def configuration() -> dict[str, Any]:
        """Read the live workflow so absent or malformed input fails the guard."""
        workflow = (
            _repository_root() / ".github" / "workflows" / "ci.yml"
        )  # Read the workflow from the discovered root.
        return yaml.safe_load(workflow.read_text(encoding="utf-8"))

    @staticmethod
    def check(configuration: dict[str, Any]) -> int:
        """Require existing evidence, comparison screenshots, and failed-flow traces."""
        steps = configuration["jobs"]["playwright_shards"]["steps"]
        upload = next(step for step in steps if step.get("with", {}).get("name") == "firmware-policy-browser-evidence")
        expected = {
            "test-artifacts/issue-4229-*.png",
            "test-artifacts/issue-4229-browser/",
        }
        assert expected.issubset(upload["with"]["path"].splitlines()), "Required browser evidence paths are missing"
        command = next(step["run"] for step in steps if "pytest ${E2E_TEST_PATHS}" in step.get("run", ""))
        for argument in (
            "--screenshot only-on-failure",
            "--tracing retain-on-failure",
            "--output=${{ github.workspace }}/test-artifacts/issue-4229-browser",
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
        steps = configuration["jobs"]["playwright_shards"]["steps"]
        if mutation == "paths":
            upload = next(
                step for step in steps if step.get("with", {}).get("name") == "firmware-policy-browser-evidence"
            )
            upload["with"]["path"] = "test-artifacts/issue4218-*.png"
        else:
            execution = next(step for step in steps if "pytest ${E2E_TEST_PATHS}" in step.get("run", ""))
            execution["run"] = execution["run"].replace("--" + mutation, "--removed")
        with pytest.raises(AssertionError, match="browser evidence"):
            self.check(configuration)

    @pytest.mark.parametrize("name", ["issue-4229-policy-comparison.png", "issue-4229-history-comparison.png"])
    def test_screenshot_paths_ignore_changed_working_directory(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str
    ) -> None:
        """Resolve real screenshot destinations under the repository after a directory change."""
        monkeypatch.chdir(tmp_path)
        destination = BrowserEvidence.path(name)
        expected = _repository_root() / "test-artifacts" / name  # Resolve expected output from the discovered root.
        assert destination == expected
        assert destination.is_absolute()
