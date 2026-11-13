"""Artifact tests for the admin token hygiene feature."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]


def test_wiring_manifest_exists() -> None:
    """The wiring manifest must exist for the integration pull request."""
    path = REPO_ROOT / "specs" / "3554-admin-token-hygiene" / "wiring.md"
    assert path.exists()


def test_release_note_fragment_exists() -> None:
    """The release note fragment must exist for issue 3554."""
    path = REPO_ROOT / "changelog.d" / "issue-3554-admin-token-hygiene.md"
    assert path.exists()
