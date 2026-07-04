"""Unit tests for src.ssh.command.command_runner.SingleCommandRunner (T013b)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.ssh.command.command_runner import (  # T013b: extracted orchestrator
    SingleCommandRequest,
    SingleCommandRunner,
)


class TestSingleCommandRequest:
    """SingleCommandRequest validation + config-object builder."""

    def test_required_args_missing_raises(self) -> None:
        with pytest.raises(ValueError):
            SingleCommandRequest(hostname="", username="u", password="p", command="show")

    def test_from_config_copies_connection_fields(self) -> None:
        from src.ssh.ssh_runner import SSHConnectionConfig

        cfg = SSHConnectionConfig(
            hostname="h-from-cfg",
            username="u-from-cfg",
            password="p-from-cfg",
            port=2222,
            timeout=42,
            use_shell=True,
        )
        request = SingleCommandRequest.from_config(cfg, command="show")

        assert (request.hostname, request.username, request.password) == (
            "h-from-cfg",
            "u-from-cfg",
            "p-from-cfg",
        )
        assert (request.port, request.timeout, request.use_shell) == (2222, 42, True)
        assert request.command == "show"


class TestRunOrchestration:
    """SingleCommandRunner.run wires SshConnector + _execute_command + footer correctly."""

    @staticmethod
    def _make_request(command: str = "show version") -> SingleCommandRequest:
        return SingleCommandRequest(
            hostname="10.0.0.1",
            username="admin",
            password="pw",
            command=command,
        )

    @patch("src.ssh.command.command_runner.SshConnector")
    @patch("src.ssh.ssh_runner.EnhancedSSHRunner._create_secure_log_file")
    @patch("src.ssh.ssh_runner.EnhancedSSHRunner._execute_command")
    @patch("src.ssh.ssh_runner.EnhancedSSHRunner._disconnect")
    def test_successful_run_returns_true(self, mock_disconnect, mock_execute, mock_log, mock_connector_class) -> None:
        mock_client = MagicMock()
        mock_connector_class.return_value.connect.return_value = (mock_client, "data/ssh_known_hosts")
        mock_log.return_value = ("/tmp/host.log", lambda _msg: None)
        mock_execute.return_value = (True, "Junos 22.4R1.5", "")

        ok = SingleCommandRunner.run(self._make_request())

        assert ok is True
        mock_execute.assert_called_once()
        mock_disconnect.assert_called_once()

    @patch("src.ssh.command.command_runner.SshConnector")
    @patch("src.ssh.ssh_runner.EnhancedSSHRunner._create_secure_log_file")
    @patch("src.ssh.ssh_runner.EnhancedSSHRunner._execute_command")
    @patch("src.ssh.ssh_runner.EnhancedSSHRunner._disconnect")
    def test_connection_failure_returns_false(
        self, mock_disconnect, mock_execute, mock_log, mock_connector_class
    ) -> None:
        mock_connector_class.return_value.connect.return_value = (None, None)
        mock_log.return_value = ("/tmp/host.log", lambda _msg: None)

        ok = SingleCommandRunner.run(self._make_request())

        assert ok is False
        mock_execute.assert_not_called()  # Skipped because connect failed
        mock_disconnect.assert_called_once()  # Cleanup still runs in finally

    @patch("src.ssh.command.command_runner.SshConnector")
    @patch("src.ssh.ssh_runner.EnhancedSSHRunner._create_secure_log_file")
    @patch("src.ssh.ssh_runner.EnhancedSSHRunner._execute_command")
    @patch("src.ssh.ssh_runner.EnhancedSSHRunner._disconnect")
    def test_command_failure_returns_false(self, mock_disconnect, mock_execute, mock_log, mock_connector_class) -> None:
        mock_client = MagicMock()
        mock_connector_class.return_value.connect.return_value = (mock_client, "data/ssh_known_hosts")
        mock_log.return_value = ("/tmp/host.log", lambda _msg: None)
        mock_execute.return_value = (False, "", "syntax error")

        ok = SingleCommandRunner.run(self._make_request("bad cmd"))

        assert ok is False
        mock_disconnect.assert_called_once()
