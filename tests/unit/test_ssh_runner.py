"""Unit tests for EnhancedSSHRunner in src/ssh/ssh_runner.py."""

import logging
import os
import time
from unittest.mock import MagicMock, patch

import pytest

from src.ssh.ssh_runner import EnhancedSSHRunner, SSHConnectionConfig, SSHExecutionConfig


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _clean_env(tmp_path, monkeypatch):
    """Run each test in a temp directory to avoid file side effects."""
    monkeypatch.chdir(tmp_path)
    os.makedirs("data", exist_ok=True)
    yield


@pytest.fixture()
def runner():
    """Return a fresh EnhancedSSHRunner instance."""
    return EnhancedSSHRunner(timeout=10)


@pytest.fixture()
def connected_runner():
    """Return an EnhancedSSHRunner with a mock SSH client attached."""
    r = EnhancedSSHRunner(timeout=10)
    r.client = MagicMock()
    return r


# ---------------------------------------------------------------------------
# Dataclass Tests
# ---------------------------------------------------------------------------
class TestSSHConnectionConfig:
    """Tests for the SSHConnectionConfig dataclass."""

    def test_defaults(self):
        """SSHConnectionConfig uses expected defaults."""
        config = SSHConnectionConfig(
            hostname="10.0.0.1", username="admin", password="secret"
        )
        assert config.port == 22
        assert config.timeout == 30
        assert config.use_shell is True

    def test_custom_values(self):
        """SSHConnectionConfig accepts custom values."""
        config = SSHConnectionConfig(
            hostname="switch1.lab", username="root", password="pw",
            port=2200, timeout=60, use_shell=False
        )
        assert config.hostname == "switch1.lab"
        assert config.port == 2200
        assert config.timeout == 60
        assert config.use_shell is False


class TestSSHExecutionConfig:
    """Tests for the SSHExecutionConfig dataclass."""

    def test_defaults(self):
        """SSHExecutionConfig uses expected defaults."""
        config = SSHExecutionConfig()
        assert config.commands == []
        assert config.max_threads == 5
        assert config.use_shell is True

    def test_custom_commands(self):
        """SSHExecutionConfig holds custom command list."""
        config = SSHExecutionConfig(
            commands=["show version", "show route"], max_threads=10
        )
        assert len(config.commands) == 2
        assert config.max_threads == 10


# ---------------------------------------------------------------------------
# Hostname Validation
# ---------------------------------------------------------------------------
class TestValidateHostname:
    """Tests for _validate_hostname static method."""

    @pytest.mark.parametrize("hostname", [
        "192.168.1.1",
        "10.0.0.1",
        "255.255.255.255",
        "::1",
        "fe80::1",
        "2001:db8::1",
    ])
    def test_valid_ip_addresses(self, hostname):
        """Valid IP addresses pass validation."""
        assert EnhancedSSHRunner._validate_hostname(hostname) is True

    @pytest.mark.parametrize("hostname", [
        "switch1.lab.local",
        "ap-01.site.example.com",
        "host",
        "a.b.c.d.e",
        "router-1",
    ])
    def test_valid_hostnames(self, hostname):
        """Valid hostnames pass validation."""
        assert EnhancedSSHRunner._validate_hostname(hostname) is True

    @pytest.mark.parametrize("hostname", [
        "",
        None,
        "a" * 254,
        "-invalid.com",
        "invalid-.com",
        "host name with spaces",
        "host;rm -rf /",
        "../../../etc/passwd",
    ])
    def test_invalid_hostnames(self, hostname):
        """Invalid or malicious hostnames fail validation."""
        assert EnhancedSSHRunner._validate_hostname(hostname) is False


# ---------------------------------------------------------------------------
# Port Validation
# ---------------------------------------------------------------------------
class TestValidatePort:
    """Tests for _validate_port static method."""

    @pytest.mark.parametrize("port", [1, 22, 443, 2200, 8080, 65535])
    def test_valid_ports(self, port):
        """Ports in 1-65535 range pass."""
        assert EnhancedSSHRunner._validate_port(port) is True

    @pytest.mark.parametrize("port", [0, -1, 65536, 99999])
    def test_invalid_ports(self, port):
        """Ports outside 1-65535 fail."""
        assert EnhancedSSHRunner._validate_port(port) is False

    def test_non_integer_port(self):
        """Non-integer ports fail."""
        assert EnhancedSSHRunner._validate_port("22") is False  # type: ignore[arg-type]
        assert EnhancedSSHRunner._validate_port(3.14) is False  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Timeout Validation
# ---------------------------------------------------------------------------
class TestValidateTimeout:
    """Tests for _validate_timeout static method."""

    @pytest.mark.parametrize("timeout", [1, 30, 60, 300, 3600])
    def test_valid_timeouts(self, timeout):
        """Timeouts in 1-3600 range pass."""
        assert EnhancedSSHRunner._validate_timeout(timeout) is True

    @pytest.mark.parametrize("timeout", [0, -1, 3601, 99999])
    def test_invalid_timeouts(self, timeout):
        """Timeouts outside 1-3600 fail."""
        assert EnhancedSSHRunner._validate_timeout(timeout) is False


# ---------------------------------------------------------------------------
# Username Validation
# ---------------------------------------------------------------------------
class TestValidateUsername:
    """Tests for _validate_username static method."""

    @pytest.mark.parametrize("username", [
        "admin", "root", "user_1", "noc-eng", "jsmith.jr",
    ])
    def test_valid_usernames(self, username):
        """Standard usernames pass validation."""
        assert EnhancedSSHRunner._validate_username(username) is True

    @pytest.mark.parametrize("username", [
        "", None, "a" * 33, "user name", "user;cmd", "user\x00null",
    ])
    def test_invalid_usernames(self, username):
        """Invalid usernames fail validation."""
        assert EnhancedSSHRunner._validate_username(username) is False


# ---------------------------------------------------------------------------
# Filename Sanitization
# ---------------------------------------------------------------------------
class TestSanitizeFilename:
    """Tests for sanitize_filename static method."""

    def test_normal_filename(self):
        """Normal filenames are preserved."""
        assert EnhancedSSHRunner.sanitize_filename("switch1") == "switch1"

    def test_ip_address_filename(self):
        """IP addresses are sanitized to safe filenames."""
        result = EnhancedSSHRunner.sanitize_filename("192.168.1.1")
        assert result == "192.168.1.1"

    def test_path_traversal_blocked(self):
        """Path traversal characters are sanitized."""
        result = EnhancedSSHRunner.sanitize_filename("../../etc/passwd")
        # Slashes are replaced with underscores, preventing directory traversal
        assert "/" not in result
        assert "\\" not in result

    def test_empty_input(self):
        """Empty input returns 'unknown'."""
        assert EnhancedSSHRunner.sanitize_filename("") == "unknown"

    def test_length_limit(self):
        """Long filenames are truncated to 100 chars."""
        long_name = "a" * 200
        assert len(EnhancedSSHRunner.sanitize_filename(long_name)) <= 100

    def test_windows_reserved_names(self):
        """Windows reserved names are prefixed."""
        result = EnhancedSSHRunner.sanitize_filename("CON")
        assert result.startswith("host_")

    def test_special_characters(self):
        """Special characters are replaced with underscore."""
        result = EnhancedSSHRunner.sanitize_filename("host<>name|test")
        assert "<" not in result
        assert ">" not in result
        assert "|" not in result


# ---------------------------------------------------------------------------
# Command Validation
# ---------------------------------------------------------------------------
class TestValidateCommand:
    """Tests for _validate_command static method."""

    @pytest.mark.parametrize("cmd", [
        "show version",
        "show interfaces terse",
        "show route protocol bgp",
        "request system reboot",
    ])
    def test_valid_commands(self, cmd):
        """Standard JunOS commands pass."""
        assert EnhancedSSHRunner._validate_command(cmd) is True

    def test_empty_command(self):
        """Empty commands fail."""
        assert EnhancedSSHRunner._validate_command("") is False

    def test_null_byte_rejected(self):
        """Commands with null bytes are rejected."""
        assert EnhancedSSHRunner._validate_command("show\x00version") is False

    def test_too_long_command(self):
        """Commands exceeding 1000 chars are rejected."""
        assert EnhancedSSHRunner._validate_command("x" * 1001) is False


# ---------------------------------------------------------------------------
# Thread Count Validation
# ---------------------------------------------------------------------------
class TestValidateThreadCount:
    """Tests for _validate_thread_count static method."""

    def test_reasonable_count(self):
        """Normal thread counts are accepted."""
        result = EnhancedSSHRunner._validate_thread_count(5, 10)
        assert result == 5

    def test_zero_uses_cpu_count(self):
        """Zero thread count falls back to cpu_count."""
        result = EnhancedSSHRunner._validate_thread_count(0, 10)
        assert result >= 1

    def test_negative_uses_cpu_count(self):
        """Negative thread count falls back to cpu_count."""
        result = EnhancedSSHRunner._validate_thread_count(-1, 10)
        assert result >= 1

    def test_limited_by_max_hosts(self):
        """Thread count is limited to max_hosts."""
        result = EnhancedSSHRunner._validate_thread_count(100, 3)
        assert result <= 3

    def test_limited_to_50(self):
        """Thread count never exceeds 50."""
        result = EnhancedSSHRunner._validate_thread_count(200, 200)
        assert result <= 50


# ---------------------------------------------------------------------------
# Host List Parsing
# ---------------------------------------------------------------------------
class TestParseHostList:
    """Tests for _parse_host_list static method."""

    def test_single_host(self):
        """Single host is parsed correctly."""
        result = EnhancedSSHRunner._parse_host_list("192.168.1.1")
        assert result == ["192.168.1.1"]

    def test_multiple_hosts(self):
        """Comma-separated hosts are parsed."""
        result = EnhancedSSHRunner._parse_host_list("10.0.0.1,10.0.0.2,10.0.0.3")
        assert len(result) == 3
        assert "10.0.0.2" in result

    def test_whitespace_handling(self):
        """Whitespace around hosts is stripped."""
        result = EnhancedSSHRunner._parse_host_list(" 10.0.0.1 , 10.0.0.2 ")
        assert result == ["10.0.0.1", "10.0.0.2"]

    def test_empty_string(self):
        """Empty string returns empty list."""
        assert EnhancedSSHRunner._parse_host_list("") == []

    def test_none_input(self):
        """None input returns empty list."""
        assert EnhancedSSHRunner._parse_host_list(None) == []

    def test_invalid_hosts_filtered(self, capsys):
        """Invalid hosts are filtered out with warning."""
        result = EnhancedSSHRunner._parse_host_list("10.0.0.1,;bad;host,10.0.0.2")
        assert "10.0.0.1" in result
        assert "10.0.0.2" in result
        assert ";bad;host" not in result

    def test_max_100_hosts(self, capsys):
        """Host list is limited to 100 entries."""
        hosts = ",".join(f"10.0.0.{i}" for i in range(1, 150))
        result = EnhancedSSHRunner._parse_host_list(hosts)
        assert len(result) <= 100


# ---------------------------------------------------------------------------
# Command List Parsing
# ---------------------------------------------------------------------------
class TestParseCommandList:
    """Tests for _parse_command_list static method."""

    def test_single_command(self):
        """Single command is parsed."""
        result = EnhancedSSHRunner._parse_command_list("show version")
        assert result == ["show version"]

    def test_multiple_commands(self):
        """Comma-separated commands are parsed."""
        result = EnhancedSSHRunner._parse_command_list("show version,show route,show interfaces")
        assert len(result) == 3

    def test_quoted_commands(self):
        """Quoted command strings are handled."""
        result = EnhancedSSHRunner._parse_command_list('"show version","show route"')
        assert "show version" in result
        assert "show route" in result

    def test_empty_string(self):
        """Empty string returns empty list."""
        assert EnhancedSSHRunner._parse_command_list("") == []

    def test_none_input(self):
        """None input returns empty list."""
        assert EnhancedSSHRunner._parse_command_list(None) == []

    def test_max_50_commands(self, capsys):
        """Command list is limited to 50 entries."""
        cmds = ",".join(f"show cmd{i}" for i in range(60))
        result = EnhancedSSHRunner._parse_command_list(cmds)
        assert len(result) <= 50


# ---------------------------------------------------------------------------
# CSV Command Loading
# ---------------------------------------------------------------------------
class TestLoadCommandsFromCsv:
    """Tests for load_commands_from_csv static method."""

    def test_basic_csv(self, tmp_path, monkeypatch):
        """Load commands from a basic CSV file."""
        monkeypatch.chdir(tmp_path)
        os.makedirs("data", exist_ok=True)
        csv_path = os.path.join("data", "SSH_COMMANDS.CSV")
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write("# Comment line\n")
            f.write("show version\n")
            f.write("show interfaces,Interface status check\n")
            f.write("\n")
            f.write("show route\n")

        result = EnhancedSSHRunner.load_commands_from_csv(csv_path)
        assert "show version" in result
        assert "show interfaces" in result
        assert "show route" in result
        assert len(result) == 3

    def test_missing_file(self):
        """Missing CSV returns empty list."""
        result = EnhancedSSHRunner.load_commands_from_csv("data/nonexistent.csv")
        assert result == []

    def test_comments_and_empty_lines_skipped(self, tmp_path, monkeypatch):
        """Comments and blank lines are ignored."""
        monkeypatch.chdir(tmp_path)
        os.makedirs("data", exist_ok=True)
        csv_path = os.path.join("data", "test.csv")
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write("# This is a comment\n")
            f.write("\n")
            f.write("# Another comment\n")
            f.write("show version\n")
            f.write("\n")

        result = EnhancedSSHRunner.load_commands_from_csv(csv_path)
        assert result == ["show version"]


# ---------------------------------------------------------------------------
# Known Hosts Entry Name
# ---------------------------------------------------------------------------
class TestKnownHostsEntryName:
    """Tests for _known_hosts_entry_name static method."""

    def test_default_port(self):
        """Default port 22 uses plain hostname."""
        result = EnhancedSSHRunner._known_hosts_entry_name("switch1.lab", 22)
        assert result == "switch1.lab"

    def test_non_default_port(self):
        """Non-default port uses bracketed format."""
        result = EnhancedSSHRunner._known_hosts_entry_name("switch1.lab", 2200)
        assert result == "[switch1.lab]:2200"


# ---------------------------------------------------------------------------
# Host Key Fingerprint Formatting
# ---------------------------------------------------------------------------
class TestFormatHostKeyFingerprint:
    """Tests for _format_host_key_fingerprint static method."""

    def test_returns_sha256_prefix(self):
        """Fingerprint string starts with SHA256:."""
        mock_key = MagicMock()
        mock_key.asbytes.return_value = b"fake_key_bytes_for_test_1234"
        result = EnhancedSSHRunner._format_host_key_fingerprint(mock_key)
        assert result.startswith("SHA256:")

    def test_consistent_output(self):
        """Same key produces same fingerprint."""
        mock_key = MagicMock()
        mock_key.asbytes.return_value = b"consistent_key_data"
        r1 = EnhancedSSHRunner._format_host_key_fingerprint(mock_key)
        r2 = EnhancedSSHRunner._format_host_key_fingerprint(mock_key)
        assert r1 == r2


# ---------------------------------------------------------------------------
# Data Directory
# ---------------------------------------------------------------------------
class TestGetDataDirectory:
    """Tests for _get_data_directory static method."""

    def test_returns_data_string(self, tmp_path, monkeypatch):
        """Returns 'data' directory path."""
        monkeypatch.chdir(tmp_path)
        result = EnhancedSSHRunner._get_data_directory()
        assert result == "data"
        assert os.path.isdir("data")

    def test_creates_directory_if_missing(self, tmp_path, monkeypatch):
        """Creates data directory if it does not exist."""
        monkeypatch.chdir(tmp_path)
        EnhancedSSHRunner._get_data_directory()
        assert os.path.isdir("data")


# ---------------------------------------------------------------------------
# Runner Initialization
# ---------------------------------------------------------------------------
class TestEnhancedSSHRunnerInit:
    """Tests for EnhancedSSHRunner initialization."""

    def test_default_timeout(self):
        """Default runner uses 30s timeout."""
        runner = EnhancedSSHRunner()
        assert runner.timeout == 30

    def test_custom_timeout(self):
        """Custom timeout is stored."""
        runner = EnhancedSSHRunner(timeout=60)
        assert runner.timeout == 60

    def test_client_starts_none(self, runner):
        """SSH client starts as None."""
        assert runner.client is None

    def test_custom_logger(self):
        """Custom logger is used when provided."""
        custom_logger = MagicMock()
        runner = EnhancedSSHRunner(logger=custom_logger)
        assert runner.logger is custom_logger


# ---------------------------------------------------------------------------
# Known Hosts Management
# ---------------------------------------------------------------------------
class TestKnownHostsManagement:
    """Tests for known hosts file management."""

    def test_get_managed_known_hosts_path(self, runner, tmp_path, monkeypatch):
        """Returns path inside data directory."""
        monkeypatch.chdir(tmp_path)
        os.makedirs("data", exist_ok=True)
        path = runner._get_managed_known_hosts_path()
        assert "data" in path
        assert "ssh_known_hosts" in path

    def test_ensure_creates_file(self, runner, tmp_path, monkeypatch):
        """Ensure method creates file if missing."""
        monkeypatch.chdir(tmp_path)
        os.makedirs("data", exist_ok=True)
        path = runner._ensure_managed_known_hosts_file()
        assert os.path.exists(path)

    def test_ensure_sets_permissions(self, runner, tmp_path, monkeypatch):
        """Ensure method sets restrictive permissions."""
        monkeypatch.chdir(tmp_path)
        os.makedirs("data", exist_ok=True)
        path = runner._ensure_managed_known_hosts_file()
        mode = oct(os.stat(path).st_mode)[-3:]
        assert mode == "600"


# ---------------------------------------------------------------------------
# Connection Tests (Mocked)
# ---------------------------------------------------------------------------
class TestConnect:
    """Tests for _connect method with mocked paramiko."""

    def test_connect_invalid_hostname(self, runner):
        """Connection fails with invalid hostname."""
        result = runner._connect(";evil", "admin", "pass123")
        assert result is False

    def test_connect_invalid_username(self, runner):
        """Connection fails with invalid username."""
        result = runner._connect("10.0.0.1", "bad user", "pass123")
        assert result is False

    def test_connect_invalid_port(self, runner):
        """Connection fails with invalid port."""
        result = runner._connect("10.0.0.1", "admin", "pass123", port=99999)
        assert result is False

    def test_connect_empty_password(self, runner):
        """Connection fails with empty password."""
        result = runner._connect("10.0.0.1", "admin", "")
        assert result is False

    @patch("src.ssh.ssh_runner.SSHClient")
    def test_connect_success(self, mock_ssh_class, runner, tmp_path, monkeypatch):
        """Successful connection returns True."""
        monkeypatch.chdir(tmp_path)
        os.makedirs("data", exist_ok=True)
        mock_client = MagicMock()
        mock_ssh_class.return_value = mock_client
        mock_client.get_host_keys.return_value.lookup.return_value = "key_entry"

        result = runner._connect("10.0.0.1", "admin", "password123")
        assert result is True
        assert runner.client is not None

    @patch("src.ssh.ssh_runner.SSHClient")
    def test_connect_timeout(self, mock_ssh_class, runner, tmp_path, monkeypatch):
        """Connection timeout returns False."""
        monkeypatch.chdir(tmp_path)
        os.makedirs("data", exist_ok=True)
        mock_client = MagicMock()
        mock_ssh_class.return_value = mock_client
        mock_client.get_host_keys.return_value.lookup.return_value = "key_entry"
        mock_client.connect.side_effect = TimeoutError("timed out")

        result = runner._connect("10.0.0.1", "admin", "password123")
        assert result is False

    @patch("src.ssh.ssh_runner.SSHClient")
    def test_connect_auth_failure(self, mock_ssh_class, runner, tmp_path, monkeypatch):
        """Authentication failure returns False."""
        import paramiko as real_paramiko
        monkeypatch.chdir(tmp_path)
        os.makedirs("data", exist_ok=True)
        mock_client = MagicMock()
        mock_ssh_class.return_value = mock_client
        mock_client.get_host_keys.return_value.lookup.return_value = "key_entry"
        mock_client.connect.side_effect = real_paramiko.AuthenticationException("bad creds")

        result = runner._connect("10.0.0.1", "admin", "wrongpass")
        assert result is False

    @patch("src.ssh.ssh_runner.SSHClient")
    def test_connect_dns_failure(self, mock_ssh_class, runner, tmp_path, monkeypatch):
        """DNS resolution failure returns False."""
        import socket
        monkeypatch.chdir(tmp_path)
        os.makedirs("data", exist_ok=True)
        mock_client = MagicMock()
        mock_ssh_class.return_value = mock_client
        mock_client.get_host_keys.return_value.lookup.return_value = "key_entry"
        mock_client.connect.side_effect = socket.gaierror("DNS failed")

        result = runner._connect("nonexistent.host", "admin", "pass")
        assert result is False


# ---------------------------------------------------------------------------
# Disconnect Tests
# ---------------------------------------------------------------------------
class TestDisconnect:
    """Tests for _disconnect method."""

    def test_disconnect_with_client(self, connected_runner):
        """Disconnecting closes client and sets to None."""
        mock_client = connected_runner.client
        connected_runner._disconnect()
        mock_client.close.assert_called_once()
        assert connected_runner.client is None

    def test_disconnect_without_client(self, runner):
        """Disconnecting with no client is safe no-op."""
        runner._disconnect()  # Should not raise
        assert runner.client is None


# ---------------------------------------------------------------------------
# Execute Command Tests (Mocked)
# ---------------------------------------------------------------------------
class TestExecuteCommand:
    """Tests for _execute_command method."""

    def test_no_client_returns_error(self, runner):
        """Execution without connection returns error."""
        success, stdout, stderr = runner._execute_command("show version")
        assert success is False
        assert "No active SSH connection" in stderr

    def test_execute_direct_mode(self, connected_runner):
        """Direct execution mode calls exec_command."""
        mock_stdout = MagicMock()
        mock_stdout.read.return_value = b"Junos 21.4R3\n"
        mock_stdout.channel.recv_exit_status.return_value = 0
        mock_stderr = MagicMock()
        mock_stderr.read.return_value = b""
        connected_runner.client.exec_command.return_value = (MagicMock(), mock_stdout, mock_stderr)

        success, stdout, stderr = connected_runner._execute_command(
            "show version", use_shell=False, hostname="switch1"
        )
        assert success is True
        assert "Junos 21.4R3" in stdout

    def test_execute_direct_failure(self, connected_runner):
        """Direct execution with non-zero exit returns failure."""
        mock_stdout = MagicMock()
        mock_stdout.read.return_value = b""
        mock_stdout.channel.recv_exit_status.return_value = 1
        mock_stderr = MagicMock()
        mock_stderr.read.return_value = b"command not found"
        connected_runner.client.exec_command.return_value = (MagicMock(), mock_stdout, mock_stderr)

        success, stdout, stderr = connected_runner._execute_command(
            "bad_command", use_shell=False, hostname="switch1"
        )
        assert success is False

    def test_execute_timeout_exception(self, connected_runner):
        """Timeout during execution is caught."""
        connected_runner.client.exec_command.side_effect = TimeoutError("timed out")

        success, stdout, stderr = connected_runner._execute_command(
            "show route", use_shell=False, hostname="switch1"
        )
        assert success is False
        assert "timeout" in stderr.lower()

    def test_execute_generic_exception(self, connected_runner):
        """Generic exception during execution is caught."""
        connected_runner.client.exec_command.side_effect = RuntimeError("channel broken")

        success, stdout, stderr = connected_runner._execute_command(
            "show route", use_shell=False, hostname="switch1"
        )
        assert success is False
        assert "RuntimeError" in stderr


# ---------------------------------------------------------------------------
# Execute Direct Tests
# ---------------------------------------------------------------------------
class TestExecuteDirect:
    """Tests for _execute_direct method."""

    def test_successful_execution(self, connected_runner):
        """Successful direct execution returns stdout."""
        mock_stdout = MagicMock()
        mock_stdout.read.return_value = b"output data"
        mock_stdout.channel.recv_exit_status.return_value = 0
        mock_stderr = MagicMock()
        mock_stderr.read.return_value = b""
        connected_runner.client.exec_command.return_value = (MagicMock(), mock_stdout, mock_stderr)

        success, stdout, stderr = connected_runner._execute_direct("show ver", time.time())
        assert success is True
        assert stdout == "output data"

    def test_pty_failure_fallback(self, connected_runner):
        """Falls back to non-PTY if PTY fails."""
        # First call (with PTY) raises, second (without PTY) succeeds
        mock_stdout = MagicMock()
        mock_stdout.read.return_value = b"fallback output"
        mock_stdout.channel.recv_exit_status.return_value = 0
        mock_stderr = MagicMock()
        mock_stderr.read.return_value = b""

        call_count = [0]

        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise OSError("PTY not available")
            return (MagicMock(), mock_stdout, mock_stderr)

        connected_runner.client.exec_command.side_effect = side_effect

        success, stdout, stderr = connected_runner._execute_direct("show ver", time.time())
        assert success is True
        assert stdout == "fallback output"


# ---------------------------------------------------------------------------
# Secure Log File Creation
# ---------------------------------------------------------------------------
class TestCreateSecureLogFile:
    """Tests for _create_secure_log_file method."""

    @patch("src.ssh.ssh_runner.datetime")
    def test_creates_log_directory(self, mock_dt, runner, tmp_path, monkeypatch):
        """Creates per-host-logs directory."""
        mock_dt.now.return_value.strftime.return_value = "20250101_120000"
        monkeypatch.chdir(tmp_path)
        os.makedirs("data", exist_ok=True)
        log_path, write_fn = runner._create_secure_log_file("switch1.lab")
        assert os.path.isdir(os.path.join("data", "per-host-logs"))
        assert "switch1" in log_path

    @patch("src.ssh.ssh_runner.datetime")
    def test_write_function_works(self, mock_dt, runner, tmp_path, monkeypatch):
        """Write function writes to log file."""
        mock_dt.now.return_value.strftime.return_value = "20250101_120000"
        monkeypatch.chdir(tmp_path)
        os.makedirs("data", exist_ok=True)
        log_path, write_fn = runner._create_secure_log_file("10.0.0.1")
        write_fn("test log message")
        assert os.path.exists(log_path)
        with open(log_path, encoding="utf-8") as f:
            content = f.read()
        assert "test log message" in content

    @patch("src.ssh.ssh_runner.datetime")
    def test_write_function_handles_empty(self, mock_dt, runner, tmp_path, monkeypatch):
        """Write function handles empty message gracefully."""
        mock_dt.now.return_value.strftime.return_value = "20250101_120000"
        monkeypatch.chdir(tmp_path)
        os.makedirs("data", exist_ok=True)
        log_path, write_fn = runner._create_secure_log_file("host1")
        write_fn("")  # Should not raise
        # File may or may not exist (early return on empty)

    @patch("src.ssh.ssh_runner.datetime")
    def test_sanitizes_hostname(self, mock_dt, runner, tmp_path, monkeypatch):
        """Hostname is sanitized for safe file creation."""
        mock_dt.now.return_value.strftime.return_value = "20250101_120000"
        monkeypatch.chdir(tmp_path)
        os.makedirs("data", exist_ok=True)
        log_path, _ = runner._create_secure_log_file("bad/host<name>")
        assert "/" not in os.path.basename(log_path).replace("per-host-logs/", "")
        assert "<" not in os.path.basename(log_path)


# ---------------------------------------------------------------------------
# Load SSH Config from .env
# ---------------------------------------------------------------------------
class TestLoadSSHConfigFromEnv:
    """Tests for load_ssh_config_from_env static method."""

    def test_missing_env_file(self):
        """Missing .env returns empty config."""
        config = EnhancedSSHRunner.load_ssh_config_from_env("nonexistent.env")
        assert config["hosts"] == []
        assert config["username"] is None
        assert config["password"] is None
        assert config["commands"] == []

    def test_path_traversal_rejected(self):
        """Path traversal in env_file is rejected."""
        config = EnhancedSSHRunner.load_ssh_config_from_env("../../etc/shadow")
        assert config["hosts"] == []

    def test_absolute_path_rejected(self):
        """Absolute paths are rejected."""
        config = EnhancedSSHRunner.load_ssh_config_from_env("/etc/shadow")
        assert config["hosts"] == []

    def test_basic_env_parsing(self, tmp_path, monkeypatch):
        """Parses basic .env file with SSH variables."""
        monkeypatch.chdir(tmp_path)
        env_path = os.path.join(str(tmp_path), "test.env")
        with open(env_path, "w", encoding="utf-8") as f:
            f.write("SSH_HOST=10.0.0.1,10.0.0.2\n")
            f.write("SSH_USER=admin\n")
            f.write("SSH_PASSWORD=secret123\n")
            f.write("SSH_COMMANDS=show version,show route\n")

        config = EnhancedSSHRunner.load_ssh_config_from_env("test.env")
        assert "10.0.0.1" in config["hosts"]
        assert config["username"] == "admin"
        assert config["password"] == "secret123"
        assert len(config["commands"]) >= 1

    def test_comments_and_empty_lines(self, tmp_path, monkeypatch):
        """Comments and blank lines in .env are skipped."""
        monkeypatch.chdir(tmp_path)
        env_path = os.path.join(str(tmp_path), "test.env")
        with open(env_path, "w", encoding="utf-8") as f:
            f.write("# This is a comment\n")
            f.write("\n")
            f.write("SSH_HOST=10.0.0.1\n")
            f.write("# Another comment\n")

        config = EnhancedSSHRunner.load_ssh_config_from_env("test.env")
        assert "10.0.0.1" in config["hosts"]

    def test_oversized_env_rejected(self, tmp_path, monkeypatch):
        """Oversized .env files are rejected."""
        monkeypatch.chdir(tmp_path)
        env_path = os.path.join(str(tmp_path), "big.env")
        with open(env_path, "w", encoding="utf-8") as f:
            f.write("X" * (1024 * 1024 + 1))  # > 1MB

        config = EnhancedSSHRunner.load_ssh_config_from_env("big.env")
        assert config["hosts"] == []

    def test_quoted_values(self, tmp_path, monkeypatch):
        """Quoted values in .env are unquoted."""
        monkeypatch.chdir(tmp_path)
        env_path = os.path.join(str(tmp_path), "test.env")
        with open(env_path, "w", encoding="utf-8") as f:
            f.write('SSH_USER="admin"\n')
            f.write("SSH_PASSWORD='secret123'\n")

        config = EnhancedSSHRunner.load_ssh_config_from_env("test.env")
        assert config["username"] == "admin"
        assert config["password"] == "secret123"


# ---------------------------------------------------------------------------
# Setup Logging
# ---------------------------------------------------------------------------
class TestSetupLogging:
    """Tests for _setup_logging static method."""

    def test_returns_logger(self):
        """Returns a configured logger instance."""
        logger = EnhancedSSHRunner._setup_logging("INFO")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "ssh_runner_v2"

    def test_debug_level(self):
        """Debug level is set correctly."""
        logger = EnhancedSSHRunner._setup_logging("DEBUG")
        assert logger.level == logging.DEBUG

    def test_propagation_enabled(self):
        """Logger propagates to root handlers."""
        logger = EnhancedSSHRunner._setup_logging("INFO")
        assert logger.propagate is True

    def test_invalid_level_defaults_to_info(self):
        """Invalid log level defaults to INFO."""
        logger = EnhancedSSHRunner._setup_logging("INVALID")
        assert logger.level == logging.INFO

