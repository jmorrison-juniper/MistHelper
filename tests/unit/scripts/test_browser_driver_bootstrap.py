"""Test the browser guard and the browser download that issue #2241 asked for.

A missing Playwright package turned all 11 browser test modules into a skip, and
pytest reports a skip as a pass. The "E2E smoke tests" gate then reported green
while it opened no page.

These tests lock the two repairs. The strict guard fails a run that would skip
every browser test. The bootstrap downloads the browser that the package omits.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from scripts.bootstrap_worktree import (
    PLAYWRIGHT_BROWSER,
    PLAYWRIGHT_INSTALL_HINT,
    WorktreeBootstrapper,
    report_result,
)

# The requirement file that must name both browser packages. Issue #2241 exists
# because neither requirement file named either package.
_REQUIREMENTS_DEV = Path(__file__).resolve().parents[3] / "requirements-dev.txt"

# The workflow that runs the browser gate. It must download the browser and it
# must run the suite in strict mode.
_CI_WORKFLOW = Path(__file__).resolve().parents[3] / ".github" / "workflows" / "ci.yml"


# ---------------------------------------------------------------------------
# The pinned packages
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("package", ["playwright", "pytest-playwright"])
def test_the_requirement_file_pins_the_browser_package(package: str) -> None:
    """Both browser packages MUST carry a pin, so a fresh worktree can run the suite."""
    logging.info("Checking that %s carries a pin", package)  # Report the plan before the read.
    text = _REQUIREMENTS_DEV.read_text(encoding="utf-8")  # Read the pinned tool list.

    # WHY: an unpinned package lets a new release move a gate result with no code change.
    assert f"{package}==" in text, f"{package} must carry an exact pin in requirements-dev.txt"


def test_the_requirement_file_names_the_browser_download() -> None:
    """The pin MUST carry the warning that the package ships no browser."""
    logging.info("Checking the browser download warning")  # Report the plan before the read.
    text = _REQUIREMENTS_DEV.read_text(encoding="utf-8")  # Read the pinned tool list.

    # WHY: a reader who installs the package alone still cannot open a page.
    assert "playwright install chromium" in text, "the pin must name the browser download command"


# ---------------------------------------------------------------------------
# The continuous integration gate
# ---------------------------------------------------------------------------


def test_the_gate_downloads_the_browser() -> None:
    """The browser gate MUST download a browser, because the package ships none."""
    logging.info("Checking that the gate downloads a browser")  # Report the plan before the read.
    text = _CI_WORKFLOW.read_text(encoding="utf-8")  # Read the workflow that runs the gate.

    assert "playwright install --with-deps chromium" in text, "the gate must download the browser"


def test_the_gate_runs_in_strict_mode() -> None:
    """The browser gate MUST refuse a run that would skip every browser test."""
    logging.info("Checking that the gate runs strict")  # Report the plan before the read.
    text = _CI_WORKFLOW.read_text(encoding="utf-8")  # Read the workflow that runs the gate.

    # WHY: without strict mode the gate reports green over an empty suite, which is issue #2241.
    assert "UPGRADE_PORTAL_E2E_STRICT" in text, "the gate must run the browser suite in strict mode"


# ---------------------------------------------------------------------------
# The bootstrap download
# ---------------------------------------------------------------------------


def test_the_bootstrap_runs_the_browser_download(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The bootstrap MUST call the browser download with the chosen browser."""
    logging.info("Checking the browser download command")  # Report the plan before the work.
    calls: list[list[str]] = []  # Record every command the bootstrap runs.
    monkeypatch.setattr(
        "scripts.bootstrap_worktree.subprocess.run",
        lambda command, **kwargs: calls.append(command) or _completed(0),
    )
    bootstrapper = WorktreeBootstrapper(tmp_path)  # Point the bootstrap at an empty directory.

    assert bootstrapper.install_browser_driver() is True, "a zero exit status means the browser is ready"
    logging.debug("The bootstrap ran %r", calls)  # Record the command for a failure read.

    assert calls, "the bootstrap must run one command"
    assert calls[0][1:] == ["-m", "playwright", "install", PLAYWRIGHT_BROWSER], "wrong download command"


def test_a_failed_download_never_stops_the_bootstrap(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A failed download MUST report false, not raise, so the rest of the setup survives."""
    logging.info("Checking the failed download path")  # Report the plan before the work.
    monkeypatch.setattr("scripts.bootstrap_worktree.subprocess.run", lambda command, **kwargs: _completed(1))
    bootstrapper = WorktreeBootstrapper(tmp_path)  # Point the bootstrap at an empty directory.

    # WHY: a worktree with no network still needs its virtual environment.
    assert bootstrapper.install_browser_driver() is False, "a failed download must report false"


def test_the_report_names_the_repair_when_the_download_failed(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """A failed download MUST print the command that repairs it."""
    logging.info("Checking the repair line of the report")  # Report the plan before the work.
    caplog.set_level(logging.WARNING, logger="bootstrap_worktree")  # Capture the warning lines.

    report_result(WorktreeBootstrapper(tmp_path), ["requirements.txt"], browser_ready=False)

    assert PLAYWRIGHT_INSTALL_HINT in caplog.text, "the report must name the download command"
    assert "skip reads as a pass" in caplog.text, "the report must state why a skip is dangerous"


def test_the_report_names_the_browser_suite_on_success(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """A ready browser MUST print the command that runs the browser suite."""
    logging.info("Checking the success line of the report")  # Report the plan before the work.
    caplog.set_level(logging.INFO, logger="bootstrap_worktree")  # Capture the information lines.

    report_result(WorktreeBootstrapper(tmp_path), ["requirements.txt"], browser_ready=True)

    assert "tests/e2e/upgrade_portal" in caplog.text, "the report must name the browser suite"
    assert PLAYWRIGHT_INSTALL_HINT not in caplog.text, "a ready browser needs no repair line"


def _completed(code: int) -> object:
    """Build a stand-in that answers one return code, like a finished subprocess."""
    logging.debug("Building a stand-in process result with code %d", code)  # Record the build.

    class _Result:  # A two-line stand-in needs no class docstring of its own.
        """One finished process with a return code and nothing else."""

        returncode = code  # The only attribute that the bootstrap reads.

    return _Result()
