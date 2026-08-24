"""Unit tests for the spec 1031 console echo sweep across ``src/ssh`` (issue #1736).

Why:
    Spec 1031 moved every legacy console echo from the WARNING channel to the
    ``echo()`` helper. The sweep missed eight lines under ``src/ssh``. These
    tests lock the two properties that the sweep must hold. The stdout text
    stays the same, and the record never lands on the WARNING channel.
"""

from __future__ import annotations

import logging
from unittest.mock import patch

import pytest

from src.ssh.runtime.app_runner import AppRunner
from src.ssh.shell_execution.shell_executor import ShellExecutor, _CollectState
from src.ssh.ssh_runner_manager import SSHRunnerManager

_ECHO_PREFIX = "!?"  # WHY: the marker that identifies a legacy console echo line.


def _echo_records_above_info(caplog: pytest.LogCaptureFixture) -> list[str]:
    """Return every captured message at WARNING or above that carries the echo marker.

    Why:
        The converted lines must never reach the WARNING channel again. A
        genuine warning on the same code path is allowed, so the filter looks
        for the echo marker instead of counting every WARNING record.

    Args:
        caplog (pytest.LogCaptureFixture): The pytest log capture fixture.

    Returns:
        list[str]: The offending messages. An empty list means the sweep holds.
    """
    offenders = []  # WHY: collect the offending messages so a failure names them.
    for record in caplog.records:  # WHY: inspect one captured record per iteration.
        message = record.getMessage()  # WHY: render the template so the marker is visible.
        if record.levelno >= logging.WARNING and _ECHO_PREFIX in message:  # WHY: flag echo text above INFO.
            offenders.append(message)  # WHY: keep the message for the assertion report.
    return offenders  # WHY: the caller asserts that this list is empty.


def test_echo_plan_prints_expected_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    """The execution plan echo keeps the exact text that the operator saw before."""
    SSHRunnerManager._echo_plan(["10.0.0.1", "10.0.0.2"], "netops", ["show version", "show chassis"])

    captured = capsys.readouterr()  # WHY: read the stdout that the helper produced.
    assert captured.out == ("!? Target hosts: 10.0.0.1, 10.0.0.2\n!? Username: netops\n!? Commands: 2 command(s)\n")
    assert captured.err == ""  # WHY: the helper never writes to stderr.


def test_echo_plan_never_records_on_the_warning_channel(caplog: pytest.LogCaptureFixture) -> None:
    """The execution plan echo records at INFO, so a log grep for WARNING stays clean."""
    caplog.set_level(logging.DEBUG)  # WHY: capture every level so an INFO record is visible.

    SSHRunnerManager._echo_plan(["10.0.0.1"], "netops", [])

    assert _echo_records_above_info(caplog) == []  # WHY: no echo text on the WARNING channel.
    assert "!? Username: netops" in caplog.text  # WHY: the audit trail still holds the echoed line.


def test_echo_plan_handles_an_empty_command_list(capsys: pytest.CaptureFixture[str]) -> None:
    """An empty command list echoes a zero count, which matches the legacy text."""
    SSHRunnerManager._echo_plan(["10.0.0.1"], "netops", [])

    assert "!? Commands: 0 command(s)\n" in capsys.readouterr().out  # WHY: zero count text is preserved.


def test_execute_multi_host_echoes_start_and_summary(
    capsys: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture
) -> None:
    """The fan-out banner and the summary line print to stdout and record at INFO."""
    caplog.set_level(logging.DEBUG)  # WHY: capture every level so the INFO record is visible.
    fake_summary = {"10.0.0.1": {"success": True}, "10.0.0.2": {"success": False}}  # WHY: one pass, one fail.

    with patch("src.ssh.ssh_runner_manager.MultiHostRunner.run", return_value=fake_summary):
        result = SSHRunnerManager._execute_multi_host(["10.0.0.1", "10.0.0.2"], "netops", "secret", ["show version"])

    assert result is True  # WHY: one successful host makes the run succeed.
    assert capsys.readouterr().out == (
        "\n!? Executing 1 command(s) on 2 host(s)\n\n!? Execution Summary: 1/2 hosts successful\n"
    )
    assert _echo_records_above_info(caplog) == []  # WHY: neither banner reaches the WARNING channel.


def test_validate_commands_echoes_the_soft_failure_notice(
    capsys: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture
) -> None:
    """The soft failure notice prints to stdout while the reject warning stays a warning."""
    caplog.set_level(logging.DEBUG)  # WHY: capture every level so both records are visible.

    validated = AppRunner._validate_commands(["show version", "bad\x00command"])

    assert validated == ["show version"]  # WHY: the NUL command is rejected by the shared validator.
    assert capsys.readouterr().out == "!? Proceeding with 1 valid commands\n"  # WHY: text is unchanged.
    assert _echo_records_above_info(caplog) == []  # WHY: the echo left the WARNING channel.
    assert "X  Invalid commands detected" in caplog.text  # WHY: the genuine warning is untouched.


def test_apply_truncation_echoes_and_keeps_the_genuine_warning(
    capsys: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture
) -> None:
    """The truncation echo moves to stdout while the size-limit warning stays at WARNING."""
    caplog.set_level(logging.DEBUG)  # WHY: capture every level so both records are visible.
    executor = ShellExecutor(client=None)  # WHY: the truncation helper never touches the client.
    state = _CollectState()  # WHY: fresh collection state so the marker append is measurable.

    executor._apply_truncation(state, "sw-01")

    assert capsys.readouterr().out == "!? [sw-01] Output truncated at 100MB, draining remaining data...\n"
    assert state.truncated is True  # WHY: the caller drains the tail once this flag is set.
    assert _echo_records_above_info(caplog) == []  # WHY: the echo left the WARNING channel.
    warnings = [r.getMessage() for r in caplog.records if r.levelno == logging.WARNING]  # WHY: keep real warnings.
    assert "Output size limit (100MB) reached, draining remaining data..." in warnings
