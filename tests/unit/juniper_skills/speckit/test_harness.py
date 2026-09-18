"""Tests for the SpecKit skill factory harness."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from src.juniper_skills.speckit import SkillDocument, SpecKitAnalyzer, SpecKitHarness, SpecKitPaths


class TestSpecKitHarness:
    """Verify programmatic SpecKit artifact generation."""

    def test_emits_complete_artifact_set(self) -> None:
        """Confirm the harness writes every required artifact."""
        workspace = self._workspace("complete")  # Use a repository-local test workspace.
        document = self._document(workspace)  # Create one source document fixture.
        harness = self._harness(workspace)  # Build the harness with isolated output.
        feature_dir = harness.emit_for_document(document)  # Generate the full artifact set.
        required = self._required(feature_dir)  # Build the exact required artifact list.
        assert all(path.exists() for path in required)  # Prove every required artifact exists.
        assert harness.validate(feature_dir) == []  # Prove the generated set has no critical gaps.

    def test_context_matches_companion_schema(self) -> None:
        """Confirm the context file has the Companion keys."""
        workspace = self._workspace("context")  # Use a repository-local test workspace.
        document = self._document(workspace)  # Create one source document fixture.
        harness = self._harness(workspace)  # Build the harness with isolated output.
        feature_dir = harness.emit_for_document(document)  # Generate the Companion context.
        data = json.loads((feature_dir / ".spec-context.json").read_text(encoding="utf-8"))  # Read context JSON.
        for key in ("currentStep", "status", "phase", "phaseStatus", "completionPercentage"):
            assert key in data  # Prove the root Companion schema keys exist.
        assert data["livingSpec"]["enabled"] is True  # Prove living-spec metadata is active.
        assert data["livingSpec"]["sourceHash"] == document.content_hash  # Prove drift tracking uses source bytes.

    def test_analyzer_catches_missing_requirement_task(self) -> None:
        """Confirm the analyzer catches a real coverage inconsistency."""
        workspace = self._workspace("inconsistent")  # Use a repository-local test workspace.
        feature_dir = workspace / "specs" / "skills" / "junos" / "bad-doc"  # Create an isolated feature path.
        feature_dir.mkdir(parents=True, exist_ok=True)  # Ensure the analysis directory exists.
        (feature_dir / "spec.md").write_text(
            "- **FR-001**: The harness MUST write files.\n", encoding="utf-8"
        )  # Write one requirement.
        (feature_dir / "plan.md").write_text(
            "# Plan\n\nNo placeholders remain.\n", encoding="utf-8"
        )  # Write a valid minimal plan.
        (feature_dir / "tasks.md").write_text(
            "- [x] T001 Create files without an id.\n", encoding="utf-8"
        )  # Omit FR-001.
        findings = SpecKitAnalyzer().analyze(feature_dir)  # Run the real coverage check.
        assert any(finding.severity == "CRITICAL" for finding in findings)  # Prove the inconsistency fails.
        assert any("FR-001" in finding.summary for finding in findings)  # Prove the missing id is named.

    def _workspace(self, name: str) -> Path:
        """Return a clean repository-local test workspace."""
        root = self._repo_root() / "data" / "juniper_skills" / "test_speckit" / name  # Avoid system temporary paths.
        if root.exists():
            shutil.rmtree(root)  # Remove only this test-owned workspace for repeatability.
        root.mkdir(parents=True)  # Create the clean workspace before test writes.
        return root

    def _document(self, workspace: Path) -> SkillDocument:
        """Create one source Markdown fixture."""
        source = workspace / "source" / "guides" / "junos-beginners-guide.md"  # Mirror the real source path shape.
        source.parent.mkdir(parents=True, exist_ok=True)  # Create the fixture directory.
        source.write_text(self._source_text(), encoding="utf-8")  # Write front matter needed by the parser.
        return SkillDocument.from_markdown(source, "junos")  # Build the document model from real Markdown shape.

    def _harness(self, workspace: Path) -> SpecKitHarness:
        """Return a harness with isolated output."""
        paths = SpecKitPaths(self._repo_root(), workspace / "specs" / "skills")  # Use the real SpecKit install.
        return SpecKitHarness(paths)  # Return the class under test.

    def _required(self, feature_dir: Path) -> list[Path]:
        """Return required artifact paths."""
        names = [
            "spec.md",
            "plan.md",
            "tasks.md",
            Path("checklists") / "requirements.md",
            "analysis.md",
            ".spec-context.json",
        ]  # Lock required files.
        return [feature_dir / name for name in names]  # Convert names to paths for assertions.

    def _repo_root(self) -> Path:
        """Return the repository root from this test file."""
        return Path(__file__).resolve().parents[4]  # Avoid pytest working directory changes.

    def _source_text(self) -> str:
        """Return a minimal source document with real front matter keys."""
        return """---
source_file: "guides/junos-beginners-guide.pdf"
title: "Day One: Beginner's Guide to Learning Junos"
pages: 356
---

## Chapter 1

Junos Fundamentals
"""  # Keep source text short and copyright-safe.
