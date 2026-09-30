"""Traceability tests for the PSK hygiene report."""

from __future__ import annotations

from pathlib import Path


def test_wiring_manifest_has_issue_3555_sections() -> None:
    """The wiring manifest carries the required issue evidence."""
    root = Path(__file__).resolve().parents[4]  # Resolve the repository root from the test file.
    wiring = root / "specs" / "3555-psk-hygiene-report" / "wiring.md"  # Build the feature wiring path.
    text = wiring.read_text(encoding="utf-8")  # Read the traceability artifact.
    assert "Issue**: #3555" in text  # The manifest must name the owning issue.
    assert "Branch Contract" in text  # The manifest must include branch evidence.
    assert "Scope Boundary" in text  # The manifest must include scope evidence.
    assert "Release Note Contract" in text  # The manifest must include release evidence.


def test_release_fragment_exists_for_issue_3555() -> None:
    """The release fragment exists for issue 3555."""
    root = Path(__file__).resolve().parents[4]  # Resolve the repository root from the test file.
    fragment = root / "changelog.d" / "issue-3555-psk-hygiene-report.md"  # Build the release fragment path.
    text = fragment.read_text(encoding="utf-8")  # Read the release note fragment.
    assert "### Added" in text  # The fragment must use a valid release-note section.
    assert "#3555" in text  # The fragment must name the owning issue.
