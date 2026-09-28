"""Contract tests for the advisory quality-gate exclusion report.

Issue #3515 moved the report tool to the `exclusion-drift` command of
misthelper-devtools. The devtools tests cover the count parsing and the tool
cache. These tests hold the manifest content and the CI wiring of this
repository.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

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
        assert "exclusion-drift --format github" in script
        assert "--output exclusion-drift.json" in script
        assert "quality-exclusion-drift" in str(job["steps"])

    def test_ci_job_runs_no_local_copy_of_the_tool(self) -> None:
        """The report must come from the pinned devtools command."""
        workflow = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
        script = "\n".join(step.get("run", "") for step in workflow["jobs"]["exclusion_drift"]["steps"])
        assert "check_exclusion_drift.py" not in script
        assert not (ROOT / "scripts" / "check_exclusion_drift.py").exists()
