"""Prove that a repository pytest run prints no pytest 10 removal warning (issue #4826)."""

import logging  # Record each child-process proof action for test diagnostics.
import os  # Build the child environment from the parent environment.
import subprocess  # Run collection in a clean interpreter that reads the repository configuration.
import sys  # Use the active virtual environment for the child process.
from pathlib import Path  # Build repository paths without hardcoded separators.

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]  # Read the pytest configuration of this worktree.
THIS_MODULE = Path(__file__).resolve()  # Collect this module, so the proof target always exists.
REMOVAL_WARNING_CLASS = "PytestRemovedIn10Warning"  # The class that pytest 9 prints for an old-style hook marker.

logger = logging.getLogger(__name__)  # Keep proof details with the guardrail test output.


def run_collection_child() -> subprocess.CompletedProcess[str]:
    """Collect this module in a child pytest run that reads the repository configuration."""
    environment = os.environ.copy()  # Start from the parent environment.
    environment.pop("PYTEST_DISABLE_PLUGIN_AUTOLOAD", None)  # A plugin override would hide the startup behavior.
    environment.pop("PYTEST_ADDOPTS", None)  # Read the addopts of the repository only.
    environment["PYTHONDONTWRITEBYTECODE"] = "1"  # Keep the proof from changing the worktree.
    logger.info("Collecting this module in a child pytest run")  # Log before the child starts.
    completed = subprocess.run(  # Run collection in a clean interpreter.
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider", str(THIS_MODULE)],
        cwd=REPOSITORY_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    logger.debug("The child pytest run completed with status %d", completed.returncode)  # Log the result.
    return completed


def test_pytest_startup_emits_no_pytest_10_removal_warning() -> None:
    """A pytest run in this repository must not print a pytest 10 removal warning."""
    completed = run_collection_child()  # Run the child with the repository configuration.
    output = completed.stdout + completed.stderr  # Read both streams, because pytest prints warnings to either.
    removal_count = output.count(REMOVAL_WARNING_CLASS)  # Count each removal warning that the child printed.
    assert completed.returncode == 0, output  # A failed collection would hide the warning check.
    assert "1 test collected" in output, output  # The child must collect this one test.
    assert removal_count == 0, (  # The Dash plugin must not register its old-style marker.
        f"The child run printed {removal_count} removal warning(s).\n{output}"
    )
