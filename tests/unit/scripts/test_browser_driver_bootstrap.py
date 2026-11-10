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
from unittest.mock import Mock

import pytest

from scripts.bootstrap_worktree import (
    PLAYWRIGHT_BROWSER,
    PLAYWRIGHT_INSTALL_HINT,
    WorktreeBootstrapper,
    main,
    report_result,
)

logger = logging.getLogger(__name__)  # WHY: keep test log records on the module logger.

# The requirement file that must name both browser packages. Issue #2241 exists
# because neither requirement file named either package.
_REQUIREMENTS_DEV = Path(__file__).resolve().parents[3] / "requirements-dev.txt"

# UV omits source comments from generated exports, so keep this note in the declaration.
_PYPROJECT = Path(__file__).resolve().parents[3] / "pyproject.toml"

# The workflow that runs the browser gate. It must download the browser and it
# must run the suite in strict mode.
_CI_WORKFLOW = Path(__file__).resolve().parents[3] / ".github" / "workflows" / "ci.yml"

# The Windows entry point that must select the supported interpreter.
_WINDOWS_BOOTSTRAP = Path(__file__).resolve().parents[3] / "scripts" / "bootstrap_worktree.ps1"


# ---------------------------------------------------------------------------
# The pinned packages
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("package", ["playwright", "pytest-playwright"])
def test_the_requirement_file_pins_the_browser_package(package: str) -> None:
    """Both browser packages MUST carry a pin, so a fresh worktree can run the suite."""
    logger.info("Checking that %s carries a pin", package)  # Report the plan before the read.
    text = _REQUIREMENTS_DEV.read_text(encoding="utf-8")  # Read the pinned tool list.

    # WHY: an unpinned package lets a new release move a gate result with no code change.
    assert f"{package}==" in text, f"{package} must carry an exact pin in requirements-dev.txt"


def test_the_project_declaration_names_the_browser_download() -> None:
    """The declaration MUST name the browser download that the package needs."""
    logger.info("Checking the browser download warning")  # Report the plan before the read.
    text = _PYPROJECT.read_text(encoding="utf-8")  # Read the canonical comment that UV does not export.

    # WHY: a reader who installs the package alone still cannot open a page.
    assert "python -m playwright install chromium" in text, "the declaration must name the browser download command"


# ---------------------------------------------------------------------------
# The continuous integration gate
# ---------------------------------------------------------------------------


def test_the_gate_downloads_the_browser() -> None:
    """The browser gate MUST download a browser, because the package ships none."""
    logger.info("Checking that the gate downloads a browser")  # Report the plan before the read.
    text = _CI_WORKFLOW.read_text(encoding="utf-8")  # Read the workflow that runs the gate.

    assert "playwright install --with-deps chromium" in text, "the gate must download the browser"


def test_the_gate_runs_in_strict_mode() -> None:
    """The browser gate MUST refuse a run that would skip every browser test."""
    logger.info("Checking that the gate runs strict")  # Report the plan before the read.
    text = _CI_WORKFLOW.read_text(encoding="utf-8")  # Read the workflow that runs the gate.

    # WHY: without strict mode the gate reports green over an empty suite, which is issue #2241.
    assert "UPGRADE_PORTAL_E2E_STRICT" in text, "the gate must run the browser suite in strict mode"


# ---------------------------------------------------------------------------
# The bootstrap download
# ---------------------------------------------------------------------------


def test_the_bootstrap_runs_the_browser_download(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The bootstrap MUST call the browser download with the chosen browser."""
    logger.info("Checking the browser download command")  # Report the plan before the work.
    calls: list[list[str]] = []  # Record every command the bootstrap runs.
    monkeypatch.setattr(
        "scripts.bootstrap_worktree.subprocess.run",
        lambda command, **kwargs: calls.append(command) or _completed(0),
    )
    bootstrapper = WorktreeBootstrapper(tmp_path)  # Point the bootstrap at an empty directory.

    assert bootstrapper.install_browser_driver() is True, "a zero exit status means the browser is ready"
    logger.debug("The bootstrap ran %r", calls)  # Record the command for a failure read.

    assert len(calls) > 0, "the bootstrap must run one command"
    assert calls[0][1:] == ["-m", "playwright", "install", PLAYWRIGHT_BROWSER], "wrong download command"


def test_a_failed_download_never_stops_the_bootstrap(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A failed download MUST report false, not raise, so the rest of the setup survives."""
    logger.info("Checking the failed download path")  # Report the plan before the work.
    monkeypatch.setattr("scripts.bootstrap_worktree.subprocess.run", lambda command, **kwargs: _completed(1))
    bootstrapper = WorktreeBootstrapper(tmp_path)  # Point the bootstrap at an empty directory.

    # WHY: a worktree with no network still needs its virtual environment.
    assert bootstrapper.install_browser_driver() is False, "a failed download must report false"


def test_the_report_names_the_repair_when_the_download_failed(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """A failed download MUST print the command that repairs it."""
    logger.info("Checking the repair line of the report")  # Report the plan before the work.
    caplog.set_level(logging.WARNING, logger="bootstrap_worktree")  # Capture the warning lines.

    report_result(WorktreeBootstrapper(tmp_path), browser_ready=False)

    assert PLAYWRIGHT_INSTALL_HINT in caplog.text, "the report must name the download command"
    assert "skip reads as a pass" in caplog.text, "the report must state why a skip is dangerous"


def test_the_report_names_the_browser_suite_on_success(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """A ready browser MUST print the command that runs the browser suite."""
    logger.info("Checking the success line of the report")  # Report the plan before the work.
    caplog.set_level(logging.INFO, logger="bootstrap_worktree")  # Capture the information lines.

    report_result(WorktreeBootstrapper(tmp_path), browser_ready=True)

    assert "tests/e2e/upgrade_portal" in caplog.text, "the report must name the browser suite"
    assert PLAYWRIGHT_INSTALL_HINT not in caplog.text, "a ready browser needs no repair line"


def test_the_report_names_the_locked_sync_on_success(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """A successful bootstrap MUST report its locked dependency command."""
    logger.info("Checking the locked sync report")  # Report the plan before the work.
    caplog.set_level(logging.INFO, logger="bootstrap_worktree")  # Capture the information lines.

    report_result(WorktreeBootstrapper(tmp_path), browser_ready=True)

    assert "Installed dependencies with uv sync --locked --extra dev." in caplog.text


@pytest.mark.parametrize(
    ("version", "expected"),
    [
        ((3, 14), False),  # WHY: the old baseline must fail before setup changes files.
        ((3, 15), True),  # WHY: the new minimum must run the bootstrap.
        ((3, 16), True),  # WHY: newer interpreters must remain supported.
    ],
)
def test_python_version_guard_requires_315(version: tuple[int, int], expected: bool, tmp_path: Path) -> None:
    """The bootstrap accepts Python 3.15 and newer only."""
    logger.info("Checking Python %s.%s against the bootstrap minimum.", *version)  # Trace the decision input.
    supported = WorktreeBootstrapper(tmp_path).check_python_version(version)  # Ask the bootstrap to validate it.
    logger.debug("The bootstrap accepted the interpreter: %s.", supported)  # Report the decision without ambiguity.

    assert supported is expected  # Confirm the minimum-version contract.


def test_python_version_guard_uses_active_interpreter_when_no_version_is_supplied(tmp_path: Path) -> None:
    """The bootstrap checks the active interpreter when the caller supplies no version."""
    logger.info("Checking the active Python interpreter against the bootstrap minimum.")  # Trace the default path.
    supported = WorktreeBootstrapper(tmp_path).check_python_version(None)  # Exercise the default interpreter input.
    logger.debug("The active interpreter meets the minimum: %s.", supported)  # Report the measured decision.

    assert supported is True, "the current test interpreter must meet the project minimum"


def test_windows_entrypoint_selects_python_315() -> None:
    """The Windows entry point MUST select Python 3.15.2 through UV."""
    logger.info("Checking the Windows bootstrap interpreter.")  # Trace before reading the PowerShell entry point.
    text = _WINDOWS_BOOTSTRAP.read_text(encoding="utf-8")  # Read the command that prepares Windows worktrees.

    assert "Get-Command uv" in text  # Require UV to select the supported interpreter.
    assert '"--no-project"' in text  # Prevent project discovery from changing the selected interpreter.
    assert '"--python", "3.15.2"' in text  # Lock the bootstrap to the tested Python release.
    assert "& $uv.Source @arguments" in text  # Run the bootstrap through the selected UV command.


def test_main_stops_before_sweep_when_python_is_too_old(monkeypatch: pytest.MonkeyPatch) -> None:
    """The command rejects an old interpreter before it changes the worktree."""
    logger.info("Checking the early Python version gate.")  # Trace before replacing external work.
    version_check = Mock(return_value=False)  # Reject Python without starting a real setup process.
    sweep = Mock()  # Detect any cleanup that would change the worktree.
    monkeypatch.setattr("scripts.bootstrap_worktree.WorktreeBootstrapper.check_python_version", version_check)
    monkeypatch.setattr("scripts.bootstrap_worktree.StaleSourceSweeper.sweep", sweep)
    result = main([])  # Run the command with no optional arguments.
    logger.debug("The bootstrap returned code %s.", result)  # Report the command result.

    assert result == 1  # An unsupported interpreter must return failure.
    assert sweep.call_count == 0  # Reject before the bootstrap removes stale files.


def _completed(code: int) -> object:
    """Build a stand-in that answers one return code, like a finished subprocess."""
    logger.debug("Building a stand-in process result with code %d", code)  # Record the build.

    class _Result:  # A two-line stand-in needs no class docstring of its own.
        """One finished process with a return code and nothing else."""

        returncode = code  # The only attribute that the bootstrap reads.

    return _Result()
