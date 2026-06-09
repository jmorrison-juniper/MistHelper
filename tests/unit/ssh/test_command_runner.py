"""Unit tests for src.ssh.command.command_runner.SingleCommandRunner (T013b)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.ssh.command.command_runner import SingleCommandRunner  # T013b: extracted orchestrator


class TestResolveParams:
    """_resolve_params normalizes positional + config-object inputs."""

    def test_required_args_missing_raises(self) -> None:
        with pytest.raises(ValueError):
            SingleCommandRunner.run(hostname=None, username="u", password="p", command="show")

    def test_config_object_overrides_positional(self) -> None:
        # Build a config with non-default values so we can verify override happened
        from src.ssh.ssh_runner import SSHConnectionConfig

        cfg = SSHConnectionConfig(
            hostname="h-from-cfg",
            username="u-from-cfg",
            password="p-from-cfg",
            port=2222,
            timeout=42,
            use_shell=True,
        )
        resolved = SingleCommandRunner._resolve_params(
            hostname="ignored",
            username="ignored",
            password="ignored",
            command="show",
            port=22,
            timeout=30,
            use_shell=False,
            config=cfg,
        )
        hostname, username, password, command, port, timeout, use_shell = resolved
        assert (hostname, username, password) == ("h-from-cfg", "u-from-cfg", "p-from-cfg")
        assert (port, timeout, use_shell) == (2222, 42, True)
        assert command == "show"


class TestRunOrchestration:
    """SingleCommandRunner.run wires SshConnector + _execute_command + footer correctly."""

    @patch("src.ssh.command.command_runner.SshConnector")
    @patch("src.ssh.ssh_runner.EnhancedSSHRunner._create_secure_log_file")
    @patch("src.ssh.ssh_runner.EnhancedSSHRunner._execute_command")
    @patch("src.ssh.ssh_runner.EnhancedSSHRunner._disconnect")
    def test_successful_run_returns_true(self, mock_disconnect, mock_execute, mock_log, mock_connector_class) -> None:
        # Connector returns live client + kh_path
        mock_client = MagicMock()
        mock_connector_class.return_value.connect.return_value = (mock_client, "data/ssh_known_hosts")
        # Log file factory returns (path, no-op writer)
        mock_log.return_value = ("/tmp/host.log", lambda _msg: None)
        # Execute reports success
        mock_execute.return_value = (True, "Junos 22.4R1.5", "")

        ok = SingleCommandRunner.run("10.0.0.1", "admin", "pw", "show version")

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
        # Connector returns (None, None) on failure
        mock_connector_class.return_value.connect.return_value = (None, None)
        mock_log.return_value = ("/tmp/host.log", lambda _msg: None)

        ok = SingleCommandRunner.run("10.0.0.1", "admin", "pw", "show version")

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

        ok = SingleCommandRunner.run("10.0.0.1", "admin", "pw", "bad cmd")

        assert ok is False
        mock_disconnect.assert_called_once()
