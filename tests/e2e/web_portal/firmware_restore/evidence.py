"""Resolve browser evidence from the repository rather than a temporary test directory."""

from pathlib import Path


class BrowserEvidence:
    """Keep synthetic browser screenshots in the declared CI artifact directory."""

    @staticmethod
    def path(name: str) -> Path:
        """Resolve a screenshot destination independently of the current working directory."""
        return Path(__file__).resolve().parents[4] / "test-artifacts" / name
