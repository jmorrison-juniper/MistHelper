"""Tests for AP scorecard support files."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]


def test_ap_scorecard_wiring_manifest_has_required_sections() -> None:
    """The wiring manifest contains every fleet contract section."""
    text = (REPO_ROOT / "specs/3559-ap-scorecard/wiring.md").read_text(encoding="utf-8")
    assert "## Menu entries" in text
    assert "## OperationRegistry comment" in text
    assert "## Primary key strategies" in text
    assert "## copilot-instructions category table" in text
    assert "## Import line for MistHelper.py" in text


def test_ap_scorecard_release_note_fragment_names_issue() -> None:
    """The release note fragment has one Added heading and one issue bullet."""
    text = (REPO_ROOT / "changelog.d/issue-3559-ap-scorecard.md").read_text(encoding="utf-8")
    assert text.count("### Added") == 1
    assert "- #3559" in text
