"""Prove the Maps contrast Playwright capability guard for issue #3728."""

from __future__ import annotations  # Keep annotations stable on every supported Python version.

import logging  # Record each child-process proof action for test diagnostics.
import os  # Build an isolated environment for each proof process.
import subprocess  # Run collection in a clean interpreter with a controlled import result.
import sys  # Use the active virtual environment for each child process.
from pathlib import Path  # Build repository paths without hardcoded separators.

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]  # Run each probe against this worktree.
TARGET = "tests/e2e/web_portal/test_map_title_contrast.py"  # Limit each probe to the repaired Maps module.
SKIP_REASON = (  # Keep the expected operator-facing reason exact.
    "The Playwright synchronous API is not installed, so the Maps contrast test cannot run."
)
CHILD_PROGRAM = r"""
import importlib.abc
import os
import sys


class PlaywrightImportProbe(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname != "playwright" and not fullname.startswith("playwright."):
            return None
        if os.environ["MAPS_PLAYWRIGHT_PROBE"] == "missing":
            raise ModuleNotFoundError("No module named 'playwright'", name="playwright")
        raise ImportError("The simulated Playwright loader failed.")


sys.meta_path.insert(0, PlaywrightImportProbe())
import pytest

arguments = [
    sys.argv[1],
    "--collect-only",
    "-q",
    "-rs",
    "-p",
    "no:cacheprovider",
]
raise SystemExit(pytest.main(arguments))
"""  # Keep the import probe independent from the parent process module cache.

logger = logging.getLogger(__name__)  # Keep proof details with the guardrail test output.


def run_collection_probe(mode: str) -> subprocess.CompletedProcess[str]:
    """Collect the Maps module with one controlled Playwright import result."""
    environment = os.environ.copy()  # Preserve required local interpreter settings.
    environment["MAPS_PLAYWRIGHT_PROBE"] = mode  # Select the missing or broken import result.
    environment["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"  # Keep unrelated local plugins out of the proof.
    environment["PYTHONDONTWRITEBYTECODE"] = "1"  # Keep the proof from changing the worktree.
    logger.info("Collecting one Maps contrast module with the %s Playwright probe", mode)  # Log the action.
    completed = subprocess.run(  # Run collection in a clean interpreter with the controlled importer.
        [sys.executable, "-B", "-c", CHILD_PROGRAM, TARGET],
        cwd=REPOSITORY_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    logger.debug("The %s probe completed with status %d", mode, completed.returncode)  # Log the result.
    return completed  # Return both streams so each proof can inspect the exact collection outcome.


def combined_output(completed: subprocess.CompletedProcess[str]) -> str:
    """Combine both child streams for stable pytest diagnostics."""
    return completed.stdout + completed.stderr  # Preserve every collection and import message.


def test_missing_playwright_capability_skips_with_an_explicit_reason() -> None:
    """A missing Playwright package must skip the one measured Maps module."""
    completed = run_collection_probe("missing")  # Exercise the intended environmental skip path.
    output = combined_output(completed)  # Read the complete child result before assertions.
    assert completed.returncode == 5, output  # An isolated skipped module collects no runnable tests.
    assert SKIP_REASON in output  # The skip must name the missing capability and affected test.
    assert "1 skipped" in output  # The proof must state that it measured one module skip.


def test_broken_playwright_import_still_fails_collection() -> None:
    """A real Playwright loader failure must remain a collection failure."""
    completed = run_collection_probe("broken")  # Exercise a failure that is not a missing capability.
    output = combined_output(completed)  # Read the complete child result before assertions.
    assert completed.returncode == 2, output  # A real import failure must keep pytest red.
    assert "The simulated Playwright loader failed." in output  # Preserve the root failure for diagnosis.
    assert "1 error" in output  # The proof must state that one module failed collection.
