"""Contract tests for the advisory quality-gate exclusion report."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import yaml

from scripts.check_exclusion_drift import Exclusion, ExclusionDriftReporter

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "quality_gate_exclusions.json"
CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"


class TestExclusionManifest:
    """Check that the manifest stays complete and machine-readable."""

    def test_manifest_has_required_fields(self) -> None:
        """Each entry must identify a gate, path, scan target, and count."""
        payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
        assert payload["version"] == 1
        assert payload["recorded_at"]
        assert payload["entries"]
        for entry in payload["entries"]:
            assert set(entry) == {"gate", "path", "scan_path", "recorded_count"}
            assert entry["recorded_count"] >= 0

    def test_manifest_covers_documented_gate_groups(self) -> None:
        """The manifest must cover each gate with documented exclusions."""
        payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
        gates = {entry["gate"] for entry in payload["entries"]}
        assert gates == {"ruff", "mypy", "bandit", "pylint"}

    def test_ci_job_is_advisory_and_uploads_json(self) -> None:
        """CI must surface drift without making it a blocking gate."""
        workflow = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
        job = workflow["jobs"]["exclusion_drift"]
        script = "\n".join(step.get("run", "") for step in job["steps"])
        assert job["continue-on-error"] is True
        assert "--format github" in script
        assert "--output exclusion-drift.json" in script
        assert "quality-exclusion-drift" in str(job["steps"])


class TestExclusionDriftReporter:
    """Check count parsing and the non-blocking drift contract."""

    def test_ruff_json_count(self) -> None:
        """Ruff JSON findings must count as one result each."""
        output = '[{"code":"E501"},{"code":"F401"}]'
        assert ExclusionDriftReporter._count_findings("ruff", output) == 2

    def test_mypy_error_count(self) -> None:
        """Mypy error lines must count while notes stay excluded."""
        output = "file.py:1: error: Bad type\nfile.py:1: note: Detail"
        assert ExclusionDriftReporter._count_findings("mypy", output) == 1

    def test_bandit_json_count(self) -> None:
        """Bandit results must count from JSON after log lines."""
        output = 'INFO scan\n{"results":[{"issue_text":"one"}]}'
        assert ExclusionDriftReporter._count_findings("bandit", output) == 1

    def test_drift_does_not_fail_the_report(self) -> None:
        """A changed count must remain an advisory result."""
        exclusion = Exclusion("ruff", "scripts", "scripts", 1)
        reporter = ExclusionDriftReporter()
        with patch.object(reporter, "_commands_for", return_value=[["tool"]]):
            with patch("scripts.check_exclusion_drift.subprocess.run") as run:
                run.return_value.stdout = '[{"code":"E501"},{"code":"F401"}]'
                run.return_value.stderr = ""
                run.return_value.returncode = 1
                result = reporter.measure(exclusion)
        assert result["delta"] == 1
        assert result["status"] == "measured"

    def test_missing_path_reports_zero_without_running_a_tool(self) -> None:
        """A missing optional path must report zero without a tool error."""
        exclusion = Exclusion("bandit", "missing", "missing", 3)
        reporter = ExclusionDriftReporter()
        with patch("scripts.check_exclusion_drift.subprocess.run") as run:
            result = reporter.measure(exclusion)
        run.assert_not_called()
        assert result["status"] == "missing"
        assert result["current_count"] == 0
        assert result["delta"] == -3
