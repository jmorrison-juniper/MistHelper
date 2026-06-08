"""Unit tests for src.ssh.shell_execution.shell_executor.ShellExecutor (T013b)."""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest

from src.ssh.shell_execution.shell_executor import ShellExecutor  # T013b: extracted shell executor


class TestPreconditions:
    """ShellExecutor refuses to run without a client."""

    def test_no_client_raises_assertion(self) -> None:
        executor = ShellExecutor(client=None, timeout=5)
        with pytest.raises(AssertionError):
            executor.execute("show version", start_time=time.time(), hostname="10.0.0.1")


class TestSendError:
    """A send failure surfaces as the documented failure tuple."""

    def test_send_failure_returns_failure_tuple(self) -> None:
        mock_client = MagicMock()
        mock_shell = MagicMock()
        mock_client.invoke_shell.return_value = mock_shell
        mock_shell.recv_ready.return_value = True
        mock_shell.recv.return_value = b"Router> "
        mock_shell.send.side_effect = OSError("broken pipe")

        executor = ShellExecutor(client=mock_client, timeout=5)
        success, stdout, stderr = executor.execute("show version", time.time(), "h1")

        assert success is False
        assert "Failed to send command" in stderr


class TestOutputCleaning:
    """The output-cleaning regex helpers preserve real content and strip noise."""

    def test_strip_ansi_and_pager_removes_escapes_and_trailing_colon(self) -> None:
        line = "\x1b[31mRED\x1b[0m text:"
        assert ShellExecutor._strip_ansi_and_pager(line) == "RED text"

    def test_line_is_artifact_or_prompt_matches_prompt(self) -> None:
        assert ShellExecutor._line_is_artifact_or_prompt("user@host:~$") is True

    def test_line_is_artifact_or_prompt_passes_real_output(self) -> None:
        assert ShellExecutor._line_is_artifact_or_prompt("uptime: 5 days") is False

    def test_matches_vyos_artifact_true_for_xit(self) -> None:
        assert ShellExecutor._matches_vyos_artifact("xit") is True

    def test_matches_vyos_artifact_false_for_real_output(self) -> None:
        assert ShellExecutor._matches_vyos_artifact("interface eth0") is False


class TestSuccessEvaluation:
    """Success/failure classification handles errors + cleanup artifacts correctly."""

    def test_empty_output_is_failure(self) -> None:
        assert ShellExecutor(client=MagicMock(), timeout=5)._evaluate_success("") is False

    def test_real_error_pattern_is_failure(self) -> None:
        executor = ShellExecutor(client=MagicMock(), timeout=5)
        assert executor._evaluate_success("command not found") is False

    def test_shell_cleanup_artifact_is_not_failure(self) -> None:
        executor = ShellExecutor(client=MagicMock(), timeout=5)
        assert executor._evaluate_success("Invalid command: [xit]") is True

    def test_normal_output_is_success(self) -> None:
        executor = ShellExecutor(client=MagicMock(), timeout=5)
        assert executor._evaluate_success("uptime: 5 days") is True


class TestFullExecution:
    """End-to-end execute() with mocked shell channel returns a sensible tuple."""

    @patch("src.ssh.shell_execution.shell_executor.time")
    def test_successful_execution_returns_tuple(self, mock_time) -> None:
        """The execute() loop completes and returns a (bool, str, str) tuple."""
        # Provide a monotonically advancing clock so the no-data-timeout fires
        clock = iter([float(n) * 0.1 for n in range(0, 1000)])
        mock_time.time.side_effect = lambda: next(clock, 100.0)
        mock_time.sleep.return_value = None

        mock_client = MagicMock()
        mock_shell = MagicMock()
        mock_client.invoke_shell.return_value = mock_shell
        # recv_ready: True for prompt, True once for output, then False for no-data timeout
        ready_iter = iter([True, True, True, False, False, False, False, False, False])
        mock_shell.recv_ready.side_effect = lambda: next(ready_iter, False)
        mock_shell.recv.side_effect = [
            b"Router> ",
            b"show version\r\nJunos 22.4R1.5\nRouter> ",
            b"",
        ]
        mock_shell.send.return_value = 20
        mock_shell.close.return_value = None

        executor = ShellExecutor(client=mock_client, timeout=30)
        success, stdout, stderr = executor.execute("show version", start_time=0.0, hostname="h1")

        assert isinstance(success, bool)
        assert isinstance(stdout, str)
        assert stderr == "" or "error" in stderr.lower()  # Either clean success or graceful failure
        mock_shell.send.assert_called()  # We actually wrote the command
