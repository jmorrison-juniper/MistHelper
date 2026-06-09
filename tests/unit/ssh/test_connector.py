"""Unit tests for src.ssh.connection.connector.SshConnector (T013b)."""

from __future__ import annotations

import os
import socket
from unittest.mock import MagicMock, patch

import paramiko
import pytest

from src.ssh.connection.connector import SshConnector  # T013b: extracted connector


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------
class TestValidateInputs:
    """SshConnector rejects malformed inputs before any paramiko call."""

    def test_rejects_invalid_hostname(self) -> None:
        connector = SshConnector(timeout=5)
        client, kh_path = connector.connect(";evil", "admin", "pw")
        assert client is None and kh_path is None

    def test_rejects_invalid_username(self) -> None:
        connector = SshConnector(timeout=5)
        client, kh_path = connector.connect("10.0.0.1", "bad user", "pw")
        assert client is None and kh_path is None

    def test_rejects_invalid_port(self) -> None:
        connector = SshConnector(timeout=5)
        client, kh_path = connector.connect("10.0.0.1", "admin", "pw", port=99999)
        assert client is None and kh_path is None

    def test_rejects_empty_password(self) -> None:
        connector = SshConnector(timeout=5)
        client, kh_path = connector.connect("10.0.0.1", "admin", "")
        assert client is None and kh_path is None


# ---------------------------------------------------------------------------
# Static helpers (moved from EnhancedSSHRunner)
# ---------------------------------------------------------------------------
class TestStaticHelpers:
    """The static helpers extracted out of EnhancedSSHRunner still work."""

    @pytest.mark.parametrize("port", [1, 22, 2222, 65535])
    def test_validate_port_accepts_valid(self, port: int) -> None:
        assert SshConnector._validate_port(port) is True

    @pytest.mark.parametrize("port", [0, -1, 65536, 99999])
    def test_validate_port_rejects_invalid(self, port: int) -> None:
        assert SshConnector._validate_port(port) is False

    def test_validate_port_rejects_non_int(self) -> None:
        assert SshConnector._validate_port("22") is False  # type: ignore[arg-type]
        assert SshConnector._validate_port(3.14) is False  # type: ignore[arg-type]

    def test_known_hosts_entry_name_bracketed_for_non_default_port(self) -> None:
        assert SshConnector._known_hosts_entry_name("h1", 2222) == "[h1]:2222"

    def test_known_hosts_entry_name_bare_for_port_22(self) -> None:
        assert SshConnector._known_hosts_entry_name("h1", 22) == "h1"

    def test_format_host_key_fingerprint_returns_sha256_prefix(self) -> None:
        fake_key = MagicMock()
        fake_key.asbytes.return_value = b"\x01\x02\x03"
        fp = SshConnector._format_host_key_fingerprint(fake_key)
        assert fp.startswith("SHA256:")


# ---------------------------------------------------------------------------
# Known hosts management
# ---------------------------------------------------------------------------
class TestKnownHostsManagement:
    """Known-hosts file creation + permissions still work after the move."""

    def test_get_managed_known_hosts_path_returns_data_path(self, tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        os.makedirs("data", exist_ok=True)
        path = SshConnector(timeout=5)._get_managed_known_hosts_path()
        assert "data" in path and "ssh_known_hosts" in path

    def test_ensure_creates_file(self, tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        os.makedirs("data", exist_ok=True)
        connector = SshConnector(timeout=5)
        path = connector._ensure_managed_known_hosts_file()
        assert os.path.exists(path)
        assert connector.managed_known_hosts_path == path


# ---------------------------------------------------------------------------
# Connect (mocked paramiko)
# ---------------------------------------------------------------------------
class TestConnect:
    """The full connect flow with paramiko mocked out."""

    @patch("src.ssh.connection.connector.SSHClient")
    def test_connect_success_returns_client_and_kh_path(
        self, mock_ssh_class, tmp_path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        os.makedirs("data", exist_ok=True)
        mock_client = MagicMock()
        mock_ssh_class.return_value = mock_client
        mock_client.get_host_keys.return_value.lookup.return_value = "key_entry"

        client, kh_path = SshConnector(timeout=5).connect("10.0.0.1", "admin", "pw")

        assert client is mock_client
        assert kh_path is not None and "ssh_known_hosts" in kh_path

    @patch("src.ssh.connection.connector.SSHClient")
    def test_connect_auth_failure_returns_none(self, mock_ssh_class, tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        os.makedirs("data", exist_ok=True)
        mock_client = MagicMock()
        mock_ssh_class.return_value = mock_client
        mock_client.get_host_keys.return_value.lookup.return_value = "key_entry"
        mock_client.connect.side_effect = paramiko.AuthenticationException("bad creds")

        client, kh_path = SshConnector(timeout=5).connect("10.0.0.1", "admin", "wrong")

        assert client is None and kh_path is None

    @patch("src.ssh.connection.connector.SSHClient")
    def test_connect_timeout_returns_none(self, mock_ssh_class, tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        os.makedirs("data", exist_ok=True)
        mock_client = MagicMock()
        mock_ssh_class.return_value = mock_client
        mock_client.get_host_keys.return_value.lookup.return_value = "key_entry"
        mock_client.connect.side_effect = TimeoutError("timed out")

        client, kh_path = SshConnector(timeout=5).connect("10.0.0.1", "admin", "pw")

        assert client is None and kh_path is None

    @patch("src.ssh.connection.connector.SSHClient")
    def test_connect_dns_failure_returns_none(self, mock_ssh_class, tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        os.makedirs("data", exist_ok=True)
        mock_client = MagicMock()
        mock_ssh_class.return_value = mock_client
        mock_client.get_host_keys.return_value.lookup.return_value = "key_entry"
        mock_client.connect.side_effect = socket.gaierror("DNS failed")

        client, kh_path = SshConnector(timeout=5).connect("nope.invalid", "admin", "pw")

        assert client is None and kh_path is None

    @patch("src.ssh.connection.connector.SSHClient")
    def test_connect_bad_host_key_returns_none(self, mock_ssh_class, tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        os.makedirs("data", exist_ok=True)
        mock_client = MagicMock()
        mock_ssh_class.return_value = mock_client
        mock_client.get_host_keys.return_value.lookup.return_value = "key_entry"
        mock_client.connect.side_effect = paramiko.BadHostKeyException("h", MagicMock(), MagicMock())

        client, kh_path = SshConnector(timeout=5).connect("10.0.0.1", "admin", "pw")

        assert client is None and kh_path is None

    @patch("src.ssh.connection.connector.SSHClient")
    def test_connect_generic_ssh_exception_returns_none(
        self, mock_ssh_class, tmp_path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        os.makedirs("data", exist_ok=True)
        mock_client = MagicMock()
        mock_ssh_class.return_value = mock_client
        mock_client.get_host_keys.return_value.lookup.return_value = "key_entry"
        mock_client.connect.side_effect = paramiko.SSHException("boom")

        client, kh_path = SshConnector(timeout=5).connect("10.0.0.1", "admin", "pw")

        assert client is None and kh_path is None
