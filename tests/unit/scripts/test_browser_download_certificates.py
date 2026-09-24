"""Test the certificate option of the browser download that issue #3302 asked for.

Playwright downloads each browser with its own Node runtime. That runtime trusts
only its own certificate list. A proxy that inspects TLS, such as Zscaler, signs
each certificate with a root that only the system store holds, so the download
fails with UNABLE_TO_GET_ISSUER_CERT_LOCALLY. The Node option
``--use-system-ca`` makes Node trust the certificate store of the system too.

The tests use the literal option text, because the option is the interface that
Node reads. The tests start no process and send no request.
"""

from __future__ import annotations

import logging
import subprocess  # nosec B404 - the tests build a finished-process record only. They start no process.
from pathlib import Path

import pytest

from scripts.bootstrap_worktree import PLAYWRIGHT_INSTALL_HINT, WorktreeBootstrapper, report_result

logger = logging.getLogger(__name__)  # WHY: keep test log records on the module logger.

SYSTEM_CA_OPTION = "--use-system-ca"  # WHY: The Node option that reads the certificate store of the system.
# WHY: A caller value with a quoted path that holds a space. The bootstrap must keep this text as it is.
CALLER_OPTIONS = '--max-old-space-size=4096 --require "C:\\tools\\hook dir\\hook.js"'
CALLER_PROXY = "http://proxy.example.invalid:8080"  # WHY: A proxy value that the download must keep.


class _RecordedRun:
    """Record the command and the environment of each subprocess that the bootstrap starts."""

    def __init__(self, return_code: int) -> None:
        """Store the return code that each recorded run answers."""
        self.return_code = return_code  # WHY: The bootstrap reads only the return code of a run.
        self.commands: list[list[str]] = []  # WHY: Each command, in start order.
        self.environments: list[dict[str, str]] = []  # WHY: Each environment, in start order.

    def __call__(
        self, command: list[str], env: dict[str, str] | None = None, **kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        """Record one subprocess start and answer the stored return code."""
        logger.debug("Recording the command %r with the options %r", command, sorted(kwargs))  # WHY: Trace the run.
        self.commands.append(command)  # WHY: A test can check which subprocess got which environment.
        self.environments.append(dict(env or {}))  # WHY: Copy, so a later change cannot alter the record.
        return subprocess.CompletedProcess(command, self.return_code)  # WHY: Answer like a finished subprocess.


@pytest.fixture
def recorded_run(monkeypatch: pytest.MonkeyPatch) -> _RecordedRun:
    """Replace the subprocess start of the bootstrap with a recorder that answers 0."""
    recorder = _RecordedRun(0)  # WHY: A zero return code means that the download worked.
    monkeypatch.setattr("scripts.bootstrap_worktree.subprocess.run", recorder)  # WHY: Start no real process.
    return recorder  # WHY: The test reads the recorded environments.


def test_the_browser_download_trusts_the_system_certificate_store(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, recorded_run: _RecordedRun
) -> None:
    """FR-001: the download subprocess gets the option in NODE_OPTIONS."""
    logger.info("Checking the Node option of the browser download")  # WHY: Report the plan before the work.
    monkeypatch.delenv("NODE_OPTIONS", raising=False)  # WHY: Start from a caller that set no Node option.

    WorktreeBootstrapper(tmp_path).install_browser_driver()  # WHY: Run the download against the recorder.

    assert recorded_run.environments[0].get("NODE_OPTIONS") == SYSTEM_CA_OPTION  # WHY: The option alone.


def test_an_empty_caller_node_option_gives_the_option_alone(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, recorded_run: _RecordedRun
) -> None:
    """FR-002 edge case: an empty caller value gives the option with no extra space."""
    logger.info("Checking an empty caller Node option")  # WHY: Report the plan before the work.
    monkeypatch.setenv("NODE_OPTIONS", "   ")  # WHY: A shell can export the variable with blank text only.

    WorktreeBootstrapper(tmp_path).install_browser_driver()  # WHY: Run the download against the recorder.

    assert recorded_run.environments[0]["NODE_OPTIONS"] == SYSTEM_CA_OPTION  # WHY: No blank text stays.


def test_the_browser_download_keeps_each_caller_node_option(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, recorded_run: _RecordedRun
) -> None:
    """FR-002: the bootstrap adds the option after the caller options, and it keeps the caller text."""
    logger.info("Checking that the caller Node options stay")  # WHY: Report the plan before the work.
    monkeypatch.setenv("NODE_OPTIONS", CALLER_OPTIONS)  # WHY: A caller value with a quoted path.

    WorktreeBootstrapper(tmp_path).install_browser_driver()  # WHY: Run the download against the recorder.

    expected = f"{CALLER_OPTIONS} {SYSTEM_CA_OPTION}"  # WHY: The caller text first, then the new option.
    assert recorded_run.environments[0]["NODE_OPTIONS"] == expected  # WHY: No caller option may change.


def test_the_browser_download_adds_the_option_one_time(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, recorded_run: _RecordedRun
) -> None:
    """FR-003: a caller value that holds the option does not get it a second time."""
    logger.info("Checking that the option shows one time")  # WHY: Report the plan before the work.
    monkeypatch.setenv("NODE_OPTIONS", f"--max-old-space-size=4096 {SYSTEM_CA_OPTION}")  # WHY: Option is set.

    WorktreeBootstrapper(tmp_path).install_browser_driver()  # WHY: Run the download against the recorder.

    options = recorded_run.environments[0]["NODE_OPTIONS"].split()  # WHY: Read each option of the value.
    assert options.count(SYSTEM_CA_OPTION) == 1  # WHY: A second copy adds nothing and hides the caller value.


def test_the_pip_install_gets_no_node_option(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, recorded_run: _RecordedRun
) -> None:
    """FR-004: the pip subprocess gets no new Node option."""
    logger.info("Checking the environment of the pip install")  # WHY: Report the plan before the work.
    monkeypatch.delenv("NODE_OPTIONS", raising=False)  # WHY: Start from a caller that set no Node option.
    monkeypatch.setattr("scripts.bootstrap_worktree.PipIndexProbe.fallback_index", lambda self: None)  # WHY: No probe.
    (tmp_path / "requirements.txt").write_text("", encoding="utf-8")  # WHY: Give the bootstrap one file.

    WorktreeBootstrapper(tmp_path).install_requirements()  # WHY: Run the pip install against the recorder.

    assert recorded_run.commands[0][1:3] == ["-m", "pip"]  # WHY: The recorded run is the pip install.
    assert "NODE_OPTIONS" not in recorded_run.environments[0]  # WHY: pip starts no Node runtime.


def test_the_browser_download_keeps_the_caller_proxy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, recorded_run: _RecordedRun
) -> None:
    """FR-004: the rest of the caller environment reaches the download unchanged."""
    logger.info("Checking that the caller proxy reaches the download")  # WHY: Report the plan before the work.
    monkeypatch.setenv("HTTPS_PROXY", CALLER_PROXY)  # WHY: A corporate network can need a proxy value.

    WorktreeBootstrapper(tmp_path).install_browser_driver()  # WHY: Run the download against the recorder.

    assert recorded_run.environments[0].get("HTTPS_PROXY") == CALLER_PROXY  # WHY: The value must stay.


def test_the_repair_command_for_powershell() -> None:
    """FR-006: Windows gets a PowerShell command that sets the option and then downloads the browser."""
    logger.info("Checking the PowerShell repair command")  # WHY: Report the plan before the work.

    command = WorktreeBootstrapper.browser_repair_command("win32")  # WHY: Build the Windows command.

    assert command == f'$env:NODE_OPTIONS = "{SYSTEM_CA_OPTION}"; {PLAYWRIGHT_INSTALL_HINT}'  # WHY: Exact line.


def test_the_repair_command_for_a_posix_shell() -> None:
    """FR-006: Linux gets a POSIX shell command that sets the option for the download only."""
    logger.info("Checking the POSIX shell repair command")  # WHY: Report the plan before the work.

    command = WorktreeBootstrapper.browser_repair_command("linux")  # WHY: Build the Linux command.

    assert command == f"NODE_OPTIONS={SYSTEM_CA_OPTION} {PLAYWRIGHT_INSTALL_HINT}"  # WHY: Exact line.


def test_a_failed_download_prints_the_repair_command_with_the_option(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """FR-005: the warning of a failed download names a repair command that sets the option."""
    logger.info("Checking the warning of a failed download")  # WHY: Report the plan before the work.
    monkeypatch.setattr("scripts.bootstrap_worktree.subprocess.run", _RecordedRun(1))  # WHY: Fail the download.
    caplog.set_level(logging.WARNING, logger="bootstrap_worktree")  # WHY: Capture the warning lines.

    assert WorktreeBootstrapper(tmp_path).install_browser_driver() is False  # WHY: FR-007 keeps the result.
    assert SYSTEM_CA_OPTION in caplog.text  # WHY: The printed repair must work behind the proxy.


def test_the_report_prints_the_repair_command_with_the_option(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """FR-005: the final report of a failed download names a repair command that sets the option."""
    logger.info("Checking the final report of a failed download")  # WHY: Report the plan before the work.
    caplog.set_level(logging.WARNING, logger="bootstrap_worktree")  # WHY: Capture the warning lines.

    report_result(WorktreeBootstrapper(tmp_path), ["requirements.txt"], browser_ready=False)  # WHY: Print it.

    assert SYSTEM_CA_OPTION in caplog.text  # WHY: The printed repair must work behind the proxy.
    assert PLAYWRIGHT_INSTALL_HINT in caplog.text  # WHY: FR-007 keeps the download command in the line.


def test_a_report_with_no_installed_file_still_prints_the_repair_command(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """FR-005 edge case: a report with an empty file list still names the repair command."""
    logger.info("Checking the final report when no requirement file installed")  # WHY: Report the plan first.
    caplog.set_level(logging.INFO, logger="bootstrap_worktree")  # WHY: Capture the file line and the warnings.

    report_result(WorktreeBootstrapper(tmp_path), [], browser_ready=False)  # WHY: A worktree with no file.

    assert "Installed requirement files: none" in caplog.text  # WHY: The empty list prints a plain word.
    assert SYSTEM_CA_OPTION in caplog.text  # WHY: The repair line does not depend on the file list.
