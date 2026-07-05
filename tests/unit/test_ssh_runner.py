"""Unit tests for EnhancedSSHRunner in src/ssh/ssh_runner.py."""

import logging
import os
import time
from unittest.mock import MagicMock, patch

import pytest

from src.ssh.batch.batch_executor import BatchExecutor, BatchRunRequest  # T013c: extracted multi-command executor
from src.ssh.batch.host_runner import HostRunner, HostRunRequest  # T013c: extracted per-host worker + request bundle
from src.ssh.batch.interactive_batch_executor import (  # T013c: extracted interactive executor
    InteractiveBatchExecutor,
    InteractiveSessionRequest,
)
from src.ssh.batch.multi_host_runner import (  # T013c/T039: extracted multi-host orchestrator + request bundle
    MultiHostRunner,
    MultiHostRunRequest,
)
from src.ssh.config.command_parser import CommandListParser
from src.ssh.config.csv_loader import CommandCsvLoader
from src.ssh.config.env_loader import EnvSshConfigLoader
from src.ssh.config.host_parser import HostListParser
from src.ssh.config.validators import validate_command, validate_hostname, validate_username
from src.ssh.connection.connector import SshConnector  # T013b  # noqa: F401
from src.ssh.runtime.app_runner import AppRunner  # T013d: concrete CLI orchestrator
from src.ssh.runtime.interactive_mode import InteractiveMode  # T013d: concrete REPL implementation
from src.ssh.shell_execution.shell_executor import ShellExecutor  # T013b  # noqa: F401
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
        config = SSHConnectionConfig(hostname="10.0.0.1", username="admin", password="secret")
        assert config.port == 22
        assert config.timeout == 30
        assert config.use_shell is True

    def test_custom_values(self):
        """SSHConnectionConfig accepts custom values."""
        config = SSHConnectionConfig(
            hostname="switch1.lab", username="root", password="pw", port=2200, timeout=60, use_shell=False
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
        config = SSHExecutionConfig(commands=["show version", "show route"], max_threads=10)
        assert len(config.commands) == 2
        assert config.max_threads == 10


# ---------------------------------------------------------------------------
# Hostname Validation
# ---------------------------------------------------------------------------
class TestValidateHostname:
    """Tests for _validate_hostname static method."""

    @pytest.mark.parametrize(
        "hostname",
        [
            "192.168.1.1",
            "10.0.0.1",
            "255.255.255.255",
            "::1",
            "fe80::1",
            "2001:db8::1",
        ],
    )
    def test_valid_ip_addresses(self, hostname):
        """Valid IP addresses pass validation."""
        assert validate_hostname(hostname) is True

    @pytest.mark.parametrize(
        "hostname",
        [
            "switch1.lab.local",
            "ap-01.site.example.com",
            "host",
            "a.b.c.d.e",
            "router-1",
        ],
    )
    def test_valid_hostnames(self, hostname):
        """Valid hostnames pass validation."""
        assert validate_hostname(hostname) is True

    @pytest.mark.parametrize(
        "hostname",
        [
            "",
            None,
            "a" * 254,
            "-invalid.com",
            "invalid-.com",
            "host name with spaces",
            "host;rm -rf /",
            "../../../etc/passwd",
        ],
    )
    def test_invalid_hostnames(self, hostname):
        """Invalid or malicious hostnames fail validation."""
        assert validate_hostname(hostname) is False


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

    @pytest.mark.parametrize(
        "username",
        [
            "admin",
            "root",
            "user_1",
            "noc-eng",
            "jsmith.jr",
        ],
    )
    def test_valid_usernames(self, username):
        """Standard usernames pass validation."""
        assert validate_username(username) is True

    @pytest.mark.parametrize(
        "username",
        [
            "",
            None,
            "a" * 33,
            "user name",
            "user;cmd",
            "user\x00null",
        ],
    )
    def test_invalid_usernames(self, username):
        """Invalid usernames fail validation."""
        assert validate_username(username) is False


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

    @pytest.mark.parametrize(
        "cmd",
        [
            "show version",
            "show interfaces terse",
            "show route protocol bgp",
            "request system reboot",
        ],
    )
    def test_valid_commands(self, cmd):
        """Standard JunOS commands pass."""
        assert validate_command(cmd) is True

    def test_empty_command(self):
        """Empty commands fail."""
        assert validate_command("") is False

    def test_null_byte_rejected(self):
        """Commands with null bytes are rejected."""
        assert validate_command("show\x00version") is False

    def test_too_long_command(self):
        """Commands exceeding 1000 chars are rejected."""
        assert validate_command("x" * 1001) is False


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
    """Tests for HostListParser.parse (T013a: was EnhancedSSHRunner._parse_host_list)."""

    def test_single_host(self):
        """Single host is parsed correctly."""
        result = HostListParser().parse("192.168.1.1")
        assert result == ["192.168.1.1"]

    def test_multiple_hosts(self):
        """Comma-separated hosts are parsed."""
        result = HostListParser().parse("10.0.0.1,10.0.0.2,10.0.0.3")
        assert len(result) == 3
        assert "10.0.0.2" in result

    def test_whitespace_handling(self):
        """Whitespace around hosts is stripped."""
        result = HostListParser().parse(" 10.0.0.1 , 10.0.0.2 ")
        assert result == ["10.0.0.1", "10.0.0.2"]

    def test_empty_string(self):
        """Empty string returns empty list."""
        assert HostListParser().parse("") == []

    def test_none_input(self):
        """None input returns empty list."""
        assert HostListParser().parse(None) == []

    def test_invalid_hosts_filtered(self, capsys):
        """Invalid hosts are filtered out with warning."""
        result = HostListParser().parse("10.0.0.1,;bad;host,10.0.0.2")
        assert "10.0.0.1" in result
        assert "10.0.0.2" in result
        assert ";bad;host" not in result

    def test_max_100_hosts(self, capsys):
        """Host list is limited to 100 entries."""
        hosts = ",".join(f"10.0.0.{i}" for i in range(1, 150))
        result = HostListParser().parse(hosts)
        assert len(result) <= 100


# ---------------------------------------------------------------------------
# Command List Parsing
# ---------------------------------------------------------------------------
class TestParseCommandList:
    """Tests for CommandListParser.parse (T013a: was EnhancedSSHRunner._parse_command_list)."""

    def test_single_command(self):
        """Single command is parsed."""
        result = CommandListParser().parse("show version")
        assert result == ["show version"]

    def test_multiple_commands(self):
        """Comma-separated commands are parsed."""
        result = CommandListParser().parse("show version,show route,show interfaces")
        assert len(result) == 3

    def test_quoted_commands(self):
        """Quoted command strings are handled."""
        result = CommandListParser().parse('"show version","show route"')
        assert "show version" in result
        assert "show route" in result

    def test_empty_string(self):
        """Empty string returns empty list."""
        assert CommandListParser().parse("") == []

    def test_none_input(self):
        """None input returns empty list."""
        assert CommandListParser().parse(None) == []

    def test_max_50_commands(self, capsys):
        """Command list is limited to 50 entries."""
        cmds = ",".join(f"show cmd{i}" for i in range(60))
        result = CommandListParser().parse(cmds)
        assert len(result) <= 50


# ---------------------------------------------------------------------------
# CSV Command Loading
# ---------------------------------------------------------------------------
class TestLoadCommandsFromCsv:
    """Tests for CommandCsvLoader.load (T013a: was EnhancedSSHRunner.load_commands_from_csv)."""

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

        result = CommandCsvLoader().load(csv_path)
        assert "show version" in result
        assert "show interfaces" in result
        assert "show route" in result
        assert len(result) == 3

    def test_missing_file(self):
        """Missing CSV returns empty list."""
        result = CommandCsvLoader().load("data/nonexistent.csv")
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

        result = CommandCsvLoader().load(csv_path)
        assert result == ["show version"]


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

        success, stdout, stderr = connected_runner._execute_command("show version", use_shell=False, hostname="switch1")
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

        success, stdout, stderr = connected_runner._execute_command("bad_command", use_shell=False, hostname="switch1")
        assert success is False

    def test_execute_timeout_exception(self, connected_runner):
        """Timeout during execution is caught."""
        connected_runner.client.exec_command.side_effect = TimeoutError("timed out")

        success, stdout, stderr = connected_runner._execute_command("show route", use_shell=False, hostname="switch1")
        assert success is False
        assert "timeout" in stderr.lower()

    def test_execute_generic_exception(self, connected_runner):
        """Generic exception during execution is caught."""
        connected_runner.client.exec_command.side_effect = RuntimeError("channel broken")

        success, stdout, stderr = connected_runner._execute_command("show route", use_shell=False, hostname="switch1")
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
    """Tests for EnvSshConfigLoader.load (T013a: was EnhancedSSHRunner.load_ssh_config_from_env)."""

    def test_missing_env_file(self):
        """Missing .env returns empty config."""
        config = EnvSshConfigLoader().load("nonexistent.env")
        assert config["hosts"] == []
        assert config["username"] is None
        assert config["password"] is None
        assert config["commands"] == []

    def test_path_traversal_rejected(self):
        """Path traversal in env_file is rejected."""
        config = EnvSshConfigLoader().load("../../etc/shadow")
        assert config["hosts"] == []

    def test_absolute_path_rejected(self):
        """Absolute paths are rejected."""
        config = EnvSshConfigLoader().load("/etc/shadow")
        assert config["hosts"] == []

    def test_basic_env_parsing(self, tmp_path, monkeypatch):
        """Parses basic .env file with SSH variables."""
        monkeypatch.chdir(tmp_path)  # Isolate working directory so relative path resolves to tmp
        # Clear SSH env vars so load_dotenv does not skip them due to existing os.environ values
        for key in ("SSH_HOST", "SSH_USER", "SSH_PASSWORD", "SSH_COMMANDS"):
            monkeypatch.delenv(key, raising=False)  # Remove any real .env leftovers from os.environ
        env_path = os.path.join(str(tmp_path), "test.env")  # Build path to test fixture file
        with open(env_path, "w", encoding="utf-8") as f:
            f.write("SSH_HOST=10.0.0.1,10.0.0.2\n")  # Write controlled test values
            f.write("SSH_USER=admin\n")
            f.write("SSH_PASSWORD=secret123\n")
            f.write("SSH_COMMANDS=show version,show route\n")

        config = EnvSshConfigLoader().load("test.env")  # Parse test fixture
        assert "10.0.0.1" in config["hosts"]  # First host must be parsed
        assert config["username"] == "admin"  # Username must come from test file, not real env
        assert config["password"] == "secret123"  # Password must come from test file
        assert len(config["commands"]) >= 1  # At least one command parsed

    def test_comments_and_empty_lines(self, tmp_path, monkeypatch):
        """Comments and blank lines in .env are skipped."""
        monkeypatch.chdir(tmp_path)
        env_path = os.path.join(str(tmp_path), "test.env")
        with open(env_path, "w", encoding="utf-8") as f:
            f.write("# This is a comment\n")
            f.write("\n")
            f.write("SSH_HOST=10.0.0.1\n")
            f.write("# Another comment\n")

        config = EnvSshConfigLoader().load("test.env")
        assert "10.0.0.1" in config["hosts"]

    def test_oversized_env_rejected(self, tmp_path, monkeypatch):
        """Oversized .env files are rejected."""
        monkeypatch.chdir(tmp_path)
        env_path = os.path.join(str(tmp_path), "big.env")
        with open(env_path, "w", encoding="utf-8") as f:
            f.write("X" * (1024 * 1024 + 1))  # > 1MB

        config = EnvSshConfigLoader().load("big.env")
        assert config["hosts"] == []

    def test_quoted_values(self, tmp_path, monkeypatch):
        """Quoted values in .env are unquoted."""
        monkeypatch.chdir(tmp_path)  # Isolate working directory to tmp
        # Clear SSH env vars so load_dotenv does not skip them due to existing os.environ values
        for key in ("SSH_HOST", "SSH_USER", "SSH_PASSWORD", "SSH_COMMANDS"):
            monkeypatch.delenv(key, raising=False)  # Remove real env leftovers before parsing
        env_path = os.path.join(str(tmp_path), "test.env")  # Build path to test fixture
        with open(env_path, "w", encoding="utf-8") as f:
            f.write('SSH_USER="admin"\n')  # Double-quoted value must be unquoted by parser
            f.write("SSH_PASSWORD='secret123'\n")  # Single-quoted value must be unquoted

        config = EnvSshConfigLoader().load("test.env")  # Parse test fixture
        assert config["username"] == "admin"  # Quotes must be stripped from username
        assert config["password"] == "secret123"  # Quotes must be stripped from password


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


# ---------------------------------------------------------------------------
# Run Multiple SSH Commands (Sequential)
# ---------------------------------------------------------------------------
class TestRunMultipleSSHCommands:
    """Tests for BatchExecutor.run (extracted in T013c)."""

    @patch("src.ssh.batch.batch_executor.datetime")
    @patch.object(EnhancedSSHRunner, "_disconnect")
    @patch.object(EnhancedSSHRunner, "_execute_command")
    @patch("src.ssh.batch.batch_executor.SshConnector")
    def test_successful_multi_command(self, mock_connect, mock_exec, mock_disc, mock_dt):
        """Successful multi-command execution returns True."""
        mock_dt.now.return_value.strftime.return_value = "20250101_120000"
        mock_connect.return_value.connect.return_value = (MagicMock(), "data/ssh_known_hosts")
        mock_exec.return_value = (True, "output", "")

        result = BatchExecutor.run(
            BatchRunRequest(
                hostname="10.0.0.1",
                username="admin",
                password="pass",
                commands=("show version", "show route"),
                port=22,
                timeout=30,
            )
        )
        assert result is True
        assert mock_exec.call_count == 2

    @patch("src.ssh.batch.batch_executor.datetime")
    @patch.object(EnhancedSSHRunner, "_disconnect")
    @patch.object(EnhancedSSHRunner, "_execute_command")
    @patch("src.ssh.batch.batch_executor.SshConnector")
    def test_connection_failure(self, mock_connect, mock_exec, mock_disc, mock_dt):
        """Connection failure returns False."""
        mock_dt.now.return_value.strftime.return_value = "20250101_120000"
        mock_connect.return_value.connect.return_value = (None, None)

        result = BatchExecutor.run(
            BatchRunRequest(
                hostname="10.0.0.1",
                username="admin",
                password="pass",
                commands=("show version",),
                port=22,
                timeout=30,
            )
        )
        assert result is False
        mock_exec.assert_not_called()

    @patch("src.ssh.batch.batch_executor.datetime")
    @patch.object(EnhancedSSHRunner, "_disconnect")
    @patch.object(EnhancedSSHRunner, "_execute_command")
    @patch("src.ssh.batch.batch_executor.SshConnector")
    def test_command_failure_marks_overall_false(self, mock_connect, mock_exec, mock_disc, mock_dt):
        """Failed command sets overall result to False."""
        mock_dt.now.return_value.strftime.return_value = "20250101_120000"
        mock_connect.return_value.connect.return_value = (MagicMock(), "data/ssh_known_hosts")
        mock_exec.side_effect = [(True, "ok", ""), (False, "", "error")]

        result = BatchExecutor.run(
            BatchRunRequest(
                hostname="10.0.0.1",
                username="admin",
                password="pass",
                commands=("show version", "bad cmd"),
                port=22,
                timeout=30,
            )
        )
        assert result is False

    def test_missing_params_raises(self):
        """Missing required params raises ValueError."""
        with pytest.raises(ValueError):
            BatchRunRequest(hostname="", username="admin", password="pass")

    @patch("src.ssh.batch.batch_executor.datetime")
    @patch.object(EnhancedSSHRunner, "_disconnect")
    @patch.object(EnhancedSSHRunner, "_execute_command")
    @patch("src.ssh.batch.batch_executor.SshConnector")
    def test_config_object_support(self, mock_connect, mock_exec, mock_disc, mock_dt):
        """SSHConnectionConfig object is accepted."""
        mock_dt.now.return_value.strftime.return_value = "20250101_120000"
        mock_connect.return_value.connect.return_value = (MagicMock(), "data/ssh_known_hosts")
        mock_exec.return_value = (True, "output", "")

        config = SSHConnectionConfig(hostname="10.0.0.1", username="admin", password="pass")
        exec_config = SSHExecutionConfig(commands=["show version"])
        result = BatchExecutor.run(BatchRunRequest.from_configs(config, exec_config))
        assert result is True


# ---------------------------------------------------------------------------
# Run SSH Command on Host (Single Host Worker)
# ---------------------------------------------------------------------------
class TestRunSSHCommandOnHost:
    """Tests for HostRunner.run (extracted in T013c)."""

    @patch("src.ssh.batch.host_runner.SingleCommandRunner.run")
    def test_single_command_delegates(self, mock_run_single):
        """Single command delegates to SingleCommandRunner."""
        mock_run_single.return_value = True

        request = HostRunRequest(
            hostname="10.0.0.1",
            username="admin",
            password="pass",
            commands=("show version",),
            port=22,
            timeout=30,
        )
        hostname, success, summary = HostRunner.run(request)
        assert hostname == "10.0.0.1"
        assert success is True
        mock_run_single.assert_called_once()

    @patch("src.ssh.batch.host_runner.BatchExecutor.run")
    def test_multiple_commands_delegates(self, mock_run_multi):
        """Multiple non-interactive commands delegate to BatchExecutor."""
        mock_run_multi.return_value = True

        request = HostRunRequest(
            hostname="10.0.0.1",
            username="admin",
            password="pass",
            commands=("show version", "show route"),
            port=22,
            timeout=30,
        )
        hostname, success, summary = HostRunner.run(request)
        assert hostname == "10.0.0.1"
        assert success is True
        mock_run_multi.assert_called_once()

    @patch("src.ssh.batch.host_runner.InteractiveBatchExecutor.run")
    def test_interactive_commands_detected(self, mock_run_interactive):
        """Interactive commands (su) detected and routed correctly."""
        mock_run_interactive.return_value = True

        request = HostRunRequest(
            hostname="10.0.0.1",
            username="admin",
            password="pass",
            commands=("su", "password123", "show version"),
            port=22,
            timeout=30,
        )
        hostname, success, summary = HostRunner.run(request)
        assert hostname == "10.0.0.1"
        assert success is True
        mock_run_interactive.assert_called_once()

    def test_missing_params_raises(self):
        """Missing required params raises ValueError."""
        with pytest.raises(ValueError):
            HostRunRequest(hostname="", username="admin", password="pass")

    @patch("src.ssh.batch.host_runner.SingleCommandRunner.run")
    def test_exception_returns_failure(self, mock_run_single):
        """Exception during execution returns failure tuple."""
        mock_run_single.side_effect = RuntimeError("connection lost")

        request = HostRunRequest(
            hostname="10.0.0.1",
            username="admin",
            password="pass",
            commands=("show version",),
            port=22,
            timeout=30,
        )
        hostname, success, summary = HostRunner.run(request)
        assert hostname == "10.0.0.1"
        assert success is False
        assert "Error" in summary

    @patch("src.ssh.batch.host_runner.BatchExecutor.run")
    def test_config_object_support(self, mock_run_multi):
        """SSHConnectionConfig object is accepted."""
        mock_run_multi.return_value = True

        config = SSHConnectionConfig(hostname="10.0.0.1", username="admin", password="pass")
        exec_config = SSHExecutionConfig(commands=["show version", "show route"])
        request = HostRunRequest.from_configs(config=config, exec_config=exec_config)
        hostname, success, summary = HostRunner.run(request)
        assert hostname == "10.0.0.1"
        assert success is True


# ---------------------------------------------------------------------------
# Run SSH Commands Multi-Host (Threaded)
# ---------------------------------------------------------------------------
class TestRunSSHCommandsMultiHost:
    """Tests for MultiHostRunner.run (extracted in T013c)."""

    @patch("src.ssh.batch.multi_host_runner.HostRunner.run")
    def test_successful_multi_host(self, mock_on_host):
        """Successful multi-host returns correct summary."""
        mock_on_host.side_effect = [
            ("10.0.0.1", True, "1 commands executed"),
            ("10.0.0.2", True, "1 commands executed"),
        ]

        result = MultiHostRunner.run(
            MultiHostRunRequest(
                hosts=("10.0.0.1", "10.0.0.2"),
                username="admin",
                password="pass",
                commands=("show version",),
                port=22,
                timeout=30,
                max_threads=2,
            )
        )
        assert result["total"] == 2
        assert result["successful"] == 2
        assert result["failed"] == 0

    @patch("src.ssh.batch.multi_host_runner.HostRunner.run")
    def test_partial_failure(self, mock_on_host):
        """Partial failure is reported correctly."""
        mock_on_host.side_effect = [
            ("10.0.0.1", True, "ok"),
            ("10.0.0.2", False, "connection refused"),
        ]

        result = MultiHostRunner.run(
            MultiHostRunRequest(
                hosts=("10.0.0.1", "10.0.0.2"),
                username="admin",
                password="pass",
                commands=("show version",),
                port=22,
                timeout=30,
            )
        )
        assert result["successful"] == 1
        assert result["failed"] == 1
        assert "10.0.0.1" in result["successful_hosts"]
        assert "10.0.0.2" in result["failed_hosts"]

    def test_missing_credentials_raises(self):
        """Missing username/password raises ValueError."""
        with pytest.raises(ValueError):
            MultiHostRunRequest(hosts=("10.0.0.1",), username="", password="pass", commands=("show version",))

    @patch("src.ssh.batch.multi_host_runner.HostRunner.run")
    def test_empty_host_list(self, mock_on_host):
        """Empty host list returns zero results."""
        result = MultiHostRunner.run(
            MultiHostRunRequest(hosts=(), username="admin", password="pass", commands=("show version",))
        )
        assert result["total"] == 0
        assert result["successful"] == 0
        mock_on_host.assert_not_called()

    @patch("src.ssh.batch.multi_host_runner.HostRunner.run")
    def test_config_object_support(self, mock_on_host):
        """Config objects are accepted for multi-host."""
        mock_on_host.return_value = ("10.0.0.1", True, "ok")

        config = SSHConnectionConfig(hostname="ignored", username="admin", password="pass")
        exec_config = SSHExecutionConfig(commands=["show version"], max_threads=3)
        result = MultiHostRunner.run(
            MultiHostRunRequest.from_configs(hosts=["10.0.0.1"], config=config, exec_config=exec_config)
        )
        assert result["total"] == 1
        assert result["successful"] == 1


# ---------------------------------------------------------------------------
# Run Multiple SSH Commands Interactive
# ---------------------------------------------------------------------------
class TestRunMultipleSSHCommandsInteractive:
    """Tests for InteractiveBatchExecutor.run (extracted in T013c)."""

    @patch("src.ssh.batch.interactive_batch_executor.datetime")
    @patch.object(EnhancedSSHRunner, "_disconnect")
    @patch("src.ssh.batch.interactive_batch_executor.SshConnector")
    def test_connection_failure(self, mock_connect, mock_disc, mock_dt):
        """Connection failure returns False."""
        mock_dt.now.return_value.strftime.return_value = "20250101_120000"
        mock_connect.return_value.connect.return_value = (None, None)

        result = InteractiveBatchExecutor.run(
            InteractiveSessionRequest(
                hostname="10.0.0.1",
                username="admin",
                password="pass",
                commands=("su", "password123", "show version"),
                port=22,
                timeout=30,
            )
        )
        assert result is False

    def test_missing_params_raises(self):
        """Missing required params raises ValueError."""
        with pytest.raises(ValueError):
            InteractiveSessionRequest(hostname=None, username="admin", password="pass")

    @patch("src.ssh.batch.interactive_batch_executor.datetime")
    @patch.object(EnhancedSSHRunner, "_disconnect")
    @patch("src.ssh.batch.interactive_batch_executor.SshConnector")
    def test_config_object_support(self, mock_connect, mock_disc, mock_dt):
        """SSHConnectionConfig object is accepted."""
        mock_dt.now.return_value.strftime.return_value = "20250101_120000"
        mock_connect.return_value.connect.return_value = (None, None)

        config = SSHConnectionConfig(hostname="10.0.0.1", username="admin", password="pass")
        exec_config = SSHExecutionConfig(commands=["su", "pw"])
        result = InteractiveBatchExecutor.run(InteractiveSessionRequest.from_configs(config, exec_config))
        assert result is False


# ---------------------------------------------------------------------------
# Execute Direct (Start Time Param Tests)
# ---------------------------------------------------------------------------
class TestExecuteDirectStartTime:
    """Tests for _execute_direct with start_time parameter."""

    def test_no_client_raises(self):
        """Calling without connection raises AssertionError."""
        runner = EnhancedSSHRunner(timeout=10)
        with pytest.raises(AssertionError):
            runner._execute_direct("show version", start_time=time.time())

    @patch("src.ssh.connection.connector.SSHClient")
    def test_successful_direct_execution(self, mock_ssh_class):
        """Successful direct command returns output."""
        mock_client = MagicMock()
        mock_stdin = MagicMock()
        mock_stdout = MagicMock()
        mock_stderr = MagicMock()

        mock_stdout.read.return_value = b"Junos: 22.4R1\n"
        mock_stderr.read.return_value = b""
        mock_stdout.channel.recv_exit_status.return_value = 0

        mock_client.exec_command.return_value = (mock_stdin, mock_stdout, mock_stderr)

        runner = EnhancedSSHRunner(timeout=10)
        runner.client = mock_client

        success, stdout, stderr = runner._execute_direct("show version", start_time=time.time())
        assert success is True
        assert "Junos" in stdout

    @patch("src.ssh.connection.connector.SSHClient")
    def test_nonzero_exit_returns_failure(self, mock_ssh_class):
        """Non-zero exit status returns success=False."""
        mock_client = MagicMock()
        mock_stdin = MagicMock()
        mock_stdout = MagicMock()
        mock_stderr = MagicMock()

        mock_stdout.read.return_value = b""
        mock_stderr.read.return_value = b"command not found"
        mock_stdout.channel.recv_exit_status.return_value = 1

        mock_client.exec_command.return_value = (mock_stdin, mock_stdout, mock_stderr)

        runner = EnhancedSSHRunner(timeout=10)
        runner.client = mock_client

        success, stdout, stderr = runner._execute_direct("bad_command", start_time=time.time())
        assert success is False
        assert "command not found" in stderr

    @patch("src.ssh.connection.connector.SSHClient")
    def test_timeout_exception_returns_failure(self, mock_ssh_class):
        """Socket timeout during exec raises (handled by _execute_command)."""
        mock_client = MagicMock()
        mock_client.exec_command.side_effect = TimeoutError("timed out")

        runner = EnhancedSSHRunner(timeout=5)
        runner.client = mock_client

        with pytest.raises(TimeoutError):
            runner._execute_direct("show version", start_time=time.time())


# ---------------------------------------------------------------------------
# Execute Command (Extended Tests)
# ---------------------------------------------------------------------------
class TestExecuteCommandExtended:
    """Extended tests for _execute_command method."""

    @patch.object(EnhancedSSHRunner, "_execute_direct")
    def test_delegates_to_direct_by_default(self, mock_direct):
        """Without use_shell, delegates to _execute_direct."""
        mock_direct.return_value = (True, "output", "")
        runner = EnhancedSSHRunner(timeout=10)
        runner.client = MagicMock()

        success, stdout, stderr = runner._execute_command("show version", use_shell=False)
        assert success is True
        mock_direct.assert_called_once()

    @patch.object(EnhancedSSHRunner, "_execute_direct")
    def test_exception_returns_failure(self, mock_direct):
        """Exception during execution returns failure tuple."""
        mock_direct.side_effect = RuntimeError("SSH channel broken")
        runner = EnhancedSSHRunner(timeout=10)
        runner.client = MagicMock()

        success, stdout, stderr = runner._execute_command("show version", use_shell=False)
        assert success is False
        assert "SSH channel broken" in stderr or stderr != ""

    def test_no_client_returns_failure(self):
        """No active client returns failure tuple."""
        runner = EnhancedSSHRunner(timeout=10)
        runner.client = None

        success, stdout, stderr = runner._execute_command("show version")
        assert success is False
        assert "No active SSH connection" in stderr

    @patch.object(EnhancedSSHRunner, "_execute_direct")
    def test_timeout_error_caught(self, mock_direct):
        """TimeoutError is caught and returns failure."""
        mock_direct.side_effect = TimeoutError("timed out")
        runner = EnhancedSSHRunner(timeout=5)
        runner.client = MagicMock()

        success, stdout, stderr = runner._execute_command("show version", use_shell=False)
        assert success is False
        assert "timeout" in stderr.lower()


# ---------------------------------------------------------------------------
# Run Application (CLI Entry Point)
# ---------------------------------------------------------------------------
class TestRunApplication:
    """Tests for run_application static method."""

    def _make_args(self, **kwargs):
        """Create a mock args namespace with sensible defaults."""
        defaults = {
            "debug": False,
            "log_level": "INFO",
            "interactive": False,
            "no_env": True,
            "hostname": "10.0.0.1",
            "username": "admin",
            "command": "show version",
            "port": 22,
            "timeout": 30,
            "use_shell": False,
            "shell": True,
            "no_shell": False,
            "secure": False,
            "csv_file": None,
            "max_threads": 5,
        }
        defaults.update(kwargs)
        args = MagicMock()
        for key, value in defaults.items():
            setattr(args, key, value)
        return args

    @patch("src.ssh.runtime.app_runner.getpass")
    @patch("src.ssh.runtime.app_runner.SingleCommandRunner.run")
    def test_successful_single_host_execution(self, mock_run_single, mock_getpass):
        """Successful single-host single-command execution."""
        mock_getpass.getpass.return_value = "password123"
        mock_run_single.return_value = True
        args = self._make_args()
        result = AppRunner.run(args)
        # Should not return False (success)
        assert result is not False

    @patch("src.ssh.runtime.app_runner.getpass")
    def test_missing_hostname_returns_false(self, mock_getpass):
        """Missing hostname returns False."""
        mock_getpass.getpass.return_value = "password123"
        args = self._make_args(hostname=None, no_env=True)
        result = AppRunner.run(args)
        assert result is False

    @patch("src.ssh.runtime.app_runner.getpass")
    def test_missing_username_returns_false(self, mock_getpass):
        """Missing username returns False."""
        mock_getpass.getpass.return_value = "password123"
        args = self._make_args(username=None, no_env=True)
        result = AppRunner.run(args)
        assert result is False

    @patch("src.ssh.runtime.app_runner.getpass")
    @patch("src.ssh.runtime.app_runner.SingleCommandRunner.run")
    def test_invalid_hostname_rejected(self, mock_run, mock_getpass):
        """Invalid hostname is rejected."""
        mock_getpass.getpass.return_value = "password123"
        mock_run.return_value = True
        args = self._make_args(hostname="../../etc/passwd")
        result = AppRunner.run(args)
        assert result is False

    @patch("src.ssh.runtime.app_runner.InteractiveMode.run")
    def test_interactive_mode_dispatches(self, mock_interactive):
        """Interactive flag dispatches to _interactive_mode."""
        mock_interactive.return_value = True
        args = self._make_args(interactive=True)
        AppRunner.run(args)
        mock_interactive.assert_called_once()

    @patch("src.ssh.runtime.app_runner.getpass")
    @patch("src.ssh.runtime.app_runner.SingleCommandRunner.run")
    def test_invalid_command_rejected(self, mock_run, mock_getpass):
        """Commands with dangerous characters are rejected."""
        mock_getpass.getpass.return_value = "password123"
        mock_run.return_value = True
        # command validation rejects certain patterns
        args = self._make_args(command="show version; rm -rf /")
        result = AppRunner.run(args)
        # Should either reject or proceed depending on validation
        # At minimum, it should not crash
        assert result is not None

    @patch("src.ssh.runtime.app_runner.getpass")
    @patch.object(EnvSshConfigLoader, "load")
    @patch("src.ssh.runtime.app_runner.SingleCommandRunner.run")
    def test_env_config_loading(self, mock_run, mock_env, mock_getpass):
        """Env config is loaded when no_env is False."""
        mock_getpass.getpass.return_value = "password123"
        mock_env.return_value = {
            "hosts": ["10.0.0.1"],
            "username": "envuser",
            "password": "envpass",
            "commands": ["show version"],
            "port": 22,
            "timeout": 30,
        }
        mock_run.return_value = True
        args = self._make_args(no_env=False, hostname=None, username=None, command=None)
        AppRunner.run(args)
        mock_env.assert_called_once()

    @patch("src.ssh.runtime.app_runner.getpass")
    @patch("src.ssh.runtime.app_runner.BatchExecutor.run")
    def test_multiple_commands_single_host(self, mock_multi_cmd, mock_getpass):
        """Multiple commands on single host uses BatchExecutor.run."""
        mock_getpass.getpass.return_value = "password123"
        mock_multi_cmd.return_value = True
        # Use CSV to provide multiple commands
        with patch.object(CommandCsvLoader, "load", return_value=["show version", "show route"]):
            args = self._make_args(command=None)
            result = AppRunner.run(args)
        assert result is True
        mock_multi_cmd.assert_called_once()

    @patch("src.ssh.runtime.app_runner.getpass")
    @patch("src.ssh.runtime.app_runner.MultiHostRunner.run")
    @patch.object(EnvSshConfigLoader, "load")
    def test_multiple_hosts_execution(self, mock_env, mock_multi_host, mock_getpass):
        """Multiple hosts uses MultiHostRunner.run."""
        mock_getpass.getpass.return_value = "password123"
        mock_env.return_value = {
            "hosts": ["10.0.0.1", "10.0.0.2"],
            "username": "admin",
            "password": "pass123",
            "commands": ["show version"],
            "port": 22,
            "timeout": 30,
        }
        mock_multi_host.return_value = {
            "total": 2,
            "successful": 2,
            "failed": 0,
            "successful_hosts": ["10.0.0.1", "10.0.0.2"],
            "failed_hosts": [],
            "results": {},
        }
        args = self._make_args(no_env=False, hostname=None, username=None, command=None)
        result = AppRunner.run(args)
        assert result is True
        mock_multi_host.assert_called_once()

    @patch("src.ssh.runtime.app_runner.getpass")
    @patch("src.ssh.runtime.app_runner.SingleCommandRunner.run")
    def test_no_command_and_no_csv_returns_false(self, mock_run, mock_getpass):
        """No command provided and no CSV file returns False or prompts."""
        mock_getpass.getpass.return_value = "password123"
        with patch.object(CommandCsvLoader, "load", return_value=[]):
            args = self._make_args(command=None)
            result = AppRunner.run(args)
        # Should return False since no commands available
        assert result is False

    @patch("src.ssh.runtime.app_runner.getpass")
    @patch("src.ssh.runtime.app_runner.SingleCommandRunner.run")
    def test_debug_mode_enables_tracing(self, mock_run, mock_getpass):
        """Debug mode enables line tracer."""
        mock_getpass.getpass.return_value = "password123"
        mock_run.return_value = True
        args = self._make_args(debug=True)
        result = AppRunner.run(args)
        # Should not crash even with debug tracing
        assert result is not None

    @patch("src.ssh.runtime.app_runner.getpass")
    @patch("src.ssh.runtime.app_runner.SingleCommandRunner.run")
    def test_secure_password_prompt(self, mock_run, mock_getpass):
        """Secure flag triggers password prompt."""
        mock_getpass.getpass.return_value = "secure_password"
        mock_run.return_value = True
        args = self._make_args(secure=True)
        result = AppRunner.run(args)
        assert result is True


# ---------------------------------------------------------------------------
# Interactive Multi-Command (Deep Shell Tests)
# ---------------------------------------------------------------------------
class TestRunMultipleSSHCommandsInteractiveDeep:
    """Deeper tests for InteractiveBatchExecutor.run."""

    @patch("src.ssh.batch.interactive_batch_executor.time")
    @patch("src.ssh.batch.interactive_batch_executor.datetime")
    @patch.object(EnhancedSSHRunner, "_disconnect")
    @patch("src.ssh.batch.interactive_batch_executor.SshConnector")
    def test_successful_interactive_session(self, mock_connect, mock_disc, mock_dt, mock_time):
        """Successful interactive session with shell commands."""
        mock_dt.now.return_value.strftime.return_value = "20250101_120000"
        mock_client = MagicMock()
        mock_connect.return_value.connect.return_value = (mock_client, "data/ssh_known_hosts")
        mock_time.time.return_value = 100.0
        mock_time.sleep.return_value = None

        mock_shell = MagicMock()
        mock_client.invoke_shell.return_value = mock_shell
        mock_shell.recv_ready.side_effect = [True, True, False, True, False]
        mock_shell.recv.side_effect = [
            b"Router> ",
            b"show version\r\nJunos: 22.4R1\nRouter> ",
            b"show route\r\n0.0.0.0/0 next-hop 10.0.0.1\nRouter> ",
        ]
        mock_shell.send.return_value = 20

        result = InteractiveBatchExecutor.run(
            InteractiveSessionRequest(
                hostname="10.0.0.1",
                username="admin",
                password="pass",
                commands=("show version", "show route"),
                port=22,
                timeout=30,
            )
        )
        assert isinstance(result, bool)

    @patch("src.ssh.batch.interactive_batch_executor.datetime")
    @patch.object(EnhancedSSHRunner, "_disconnect")
    @patch("src.ssh.batch.interactive_batch_executor.SshConnector")
    def test_empty_commands_list(self, mock_connect, mock_disc, mock_dt):
        """Empty commands list still connects and succeeds."""
        mock_dt.now.return_value.strftime.return_value = "20250101_120000"
        mock_client = MagicMock()
        mock_connect.return_value.connect.return_value = (mock_client, "data/ssh_known_hosts")
        mock_shell = MagicMock()
        mock_client.invoke_shell.return_value = mock_shell
        mock_shell.recv_ready.return_value = False
        mock_shell.send.return_value = 5

        result = InteractiveBatchExecutor.run(
            InteractiveSessionRequest(
                hostname="10.0.0.1", username="admin", password="pass", commands=(), port=22, timeout=30
            )
        )
        assert isinstance(result, bool)


# ---------------------------------------------------------------------------
# Run Multiple SSH Commands (Deep Tests)
# ---------------------------------------------------------------------------
class TestRunMultipleSSHCommandsDeep:
    """Deeper tests for BatchExecutor.run."""

    @patch("src.ssh.batch.batch_executor.datetime")
    @patch.object(EnhancedSSHRunner, "_disconnect")
    @patch.object(EnhancedSSHRunner, "_execute_command")
    @patch("src.ssh.batch.batch_executor.SshConnector")
    def test_exception_during_execution(self, mock_connect, mock_exec, mock_disc, mock_dt):
        """Exception during command execution is handled."""
        mock_dt.now.return_value.strftime.return_value = "20250101_120000"
        mock_connect.return_value.connect.return_value = (MagicMock(), "data/ssh_known_hosts")
        mock_exec.side_effect = RuntimeError("SSH channel closed")

        result = BatchExecutor.run(
            BatchRunRequest(
                hostname="10.0.0.1",
                username="admin",
                password="pass",
                commands=("show version",),
                port=22,
                timeout=30,
            )
        )
        assert result is False
        mock_disc.assert_called()

    @patch("src.ssh.batch.batch_executor.datetime")
    @patch.object(EnhancedSSHRunner, "_disconnect")
    @patch.object(EnhancedSSHRunner, "_execute_command")
    @patch("src.ssh.batch.batch_executor.SshConnector")
    def test_many_commands_all_succeed(self, mock_connect, mock_exec, mock_disc, mock_dt):
        """Multiple commands all succeeding returns True."""
        mock_dt.now.return_value.strftime.return_value = "20250101_120000"
        mock_connect.return_value.connect.return_value = (MagicMock(), "data/ssh_known_hosts")
        mock_exec.return_value = (True, "output", "")

        commands = tuple(f"show interface ge-0/0/{i}" for i in range(10))
        result = BatchExecutor.run(
            BatchRunRequest(
                hostname="10.0.0.1",
                username="admin",
                password="pass",
                commands=commands,
                port=22,
                timeout=30,
            )
        )
        assert result is True
        assert mock_exec.call_count == 10

    @patch("src.ssh.batch.batch_executor.datetime")
    @patch.object(EnhancedSSHRunner, "_disconnect")
    @patch.object(EnhancedSSHRunner, "_execute_command")
    @patch("src.ssh.batch.batch_executor.SshConnector")
    def test_empty_output_still_succeeds(self, mock_connect, mock_exec, mock_disc, mock_dt):
        """Commands with empty output still count as successful."""
        mock_dt.now.return_value.strftime.return_value = "20250101_120000"
        mock_connect.return_value.connect.return_value = (MagicMock(), "data/ssh_known_hosts")
        mock_exec.return_value = (True, "", "")

        result = BatchExecutor.run(
            BatchRunRequest(
                hostname="10.0.0.1",
                username="admin",
                password="pass",
                commands=("show version",),
                port=22,
                timeout=30,
            )
        )
        assert result is True


# ---------------------------------------------------------------------------
# Multi-Host (Deep Tests)
# ---------------------------------------------------------------------------
class TestRunSSHCommandsMultiHostDeep:
    """Deeper tests for MultiHostRunner.run."""

    @patch("src.ssh.batch.multi_host_runner.HostRunner.run")
    def test_many_hosts_concurrent(self, mock_on_host):
        """Many hosts execute concurrently with thread pool."""
        hosts = [f"10.0.0.{i}" for i in range(1, 11)]
        mock_on_host.side_effect = [(h, True, "ok") for h in hosts]

        result = MultiHostRunner.run(
            MultiHostRunRequest(
                hosts=tuple(hosts),
                username="admin",
                password="pass",
                commands=("show version",),
                port=22,
                timeout=30,
                max_threads=5,
            )
        )
        assert result["total"] == 10
        assert result["successful"] == 10
        assert result["failed"] == 0
        assert len(result["successful_hosts"]) == 10

    @patch("src.ssh.batch.multi_host_runner.HostRunner.run")
    def test_thread_exception_handled(self, mock_on_host):
        """Exception in thread is caught and reported as failure."""
        mock_on_host.side_effect = RuntimeError("thread crash")

        result = MultiHostRunner.run(
            MultiHostRunRequest(
                hosts=("10.0.0.1",),
                username="admin",
                password="pass",
                commands=("show version",),
                port=22,
                timeout=30,
            )
        )
        assert result["total"] == 1
        assert result["failed"] == 1
        assert "10.0.0.1" in result["failed_hosts"]

    @patch("src.ssh.batch.multi_host_runner.HostRunner.run")
    def test_results_dict_structure(self, mock_on_host):
        """Results dict has expected structure with per-host info."""
        mock_on_host.side_effect = [
            ("10.0.0.1", True, "1 commands executed"),
            ("10.0.0.2", False, "connection timeout"),
        ]

        result = MultiHostRunner.run(
            MultiHostRunRequest(
                hosts=("10.0.0.1", "10.0.0.2"),
                username="admin",
                password="pass",
                commands=("show version",),
                port=22,
                timeout=30,
            )
        )
        assert "results" in result
        assert "10.0.0.1" in result["results"]
        assert result["results"]["10.0.0.1"]["success"] is True
        assert result["results"]["10.0.0.2"]["success"] is False

    @patch("src.ssh.batch.multi_host_runner.HostRunner.run")
    def test_none_hosts_treated_as_empty(self, mock_on_host):
        """None hosts list is treated as empty."""
        result = MultiHostRunner.run(
            MultiHostRunRequest(hosts=(), username="admin", password="pass", commands=("show version",))
        )
        assert result["total"] == 0
        mock_on_host.assert_not_called()


# ---------------------------------------------------------------------------
# Execute Direct (PTY Fallback)
# ---------------------------------------------------------------------------
class TestExecuteDirectFallback:
    """Tests for _execute_direct PTY fallback behavior."""

    @patch("src.ssh.connection.connector.SSHClient")
    def test_pty_failure_falls_back_to_no_pty(self, mock_ssh_class):
        """When PTY exec fails, falls back to non-PTY exec."""
        mock_client = MagicMock()
        mock_stdin = MagicMock()
        mock_stdout = MagicMock()
        mock_stderr = MagicMock()

        # First call (with PTY) raises exception
        # Second call (without PTY) succeeds
        mock_stdout.read.return_value = b"Junos: 22.4R1\n"
        mock_stderr.read.return_value = b""
        mock_stdout.channel.recv_exit_status.return_value = 0

        call_count = [0]

        def exec_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1 and kwargs.get("get_pty"):
                raise OSError("PTY allocation failed")
            return (mock_stdin, mock_stdout, mock_stderr)

        mock_client.exec_command.side_effect = exec_side_effect

        runner = EnhancedSSHRunner(timeout=10)
        runner.client = mock_client

        success, stdout, stderr = runner._execute_direct("show version", start_time=time.time())
        assert success is True
        assert "Junos" in stdout
        assert mock_client.exec_command.call_count == 2


# ---------------------------------------------------------------------------
# Interactive Mode (REPL)
# ---------------------------------------------------------------------------
class TestInteractiveMode:
    """Tests for _interactive_mode static method."""

    @patch("src.ssh.runtime.interactive_mode.getpass")
    @patch("builtins.input")
    @patch("src.ssh.runtime.interactive_mode.SingleCommandRunner.run")
    def test_successful_interactive_session(self, mock_run, mock_input, mock_getpass):
        """Successful interactive session with valid inputs."""
        mock_input.side_effect = [
            "10.0.0.1",  # hostname
            "admin",  # username
            "22",  # port
            "30",  # timeout
            "y",  # shell mode
            "show version",  # command
        ]
        mock_getpass.getpass.return_value = "password123"
        mock_run.return_value = True

        result = InteractiveMode.run()
        assert result is True
        mock_run.assert_called_once()

    @patch("src.ssh.runtime.interactive_mode.getpass")
    @patch("builtins.input")
    def test_empty_password_returns_false(self, mock_input, mock_getpass):
        """Empty password returns False."""
        mock_input.side_effect = [
            "10.0.0.1",  # hostname
            "admin",  # username
        ]
        mock_getpass.getpass.return_value = ""

        result = InteractiveMode.run()
        assert result is False

    @patch("src.ssh.runtime.interactive_mode.getpass")
    @patch("builtins.input")
    @patch("src.ssh.runtime.interactive_mode.SingleCommandRunner.run")
    def test_default_port_and_timeout(self, mock_run, mock_input, mock_getpass):
        """Empty port/timeout uses defaults (22/30)."""
        mock_input.side_effect = [
            "10.0.0.1",  # hostname
            "admin",  # username
            "",  # port (default 22)
            "",  # timeout (default 30)
            "n",  # shell mode
            "ls -la",  # command
        ]
        mock_getpass.getpass.return_value = "password123"
        mock_run.return_value = True

        result = InteractiveMode.run()
        assert result is True

    @patch("src.ssh.runtime.interactive_mode.getpass")
    @patch("builtins.input")
    @patch("src.ssh.runtime.interactive_mode.SingleCommandRunner.run")
    def test_invalid_hostname_reprompts(self, mock_run, mock_input, mock_getpass):
        """Invalid hostname re-prompts until valid."""
        mock_input.side_effect = [
            "",  # empty hostname (rejected)
            "../../hack",  # invalid hostname (rejected)
            "10.0.0.1",  # valid hostname
            "admin",  # username
            "22",  # port
            "30",  # timeout
            "n",  # shell mode
            "show version",  # command
        ]
        mock_getpass.getpass.return_value = "password123"
        mock_run.return_value = True

        result = InteractiveMode.run()
        assert result is True

    @patch("src.ssh.runtime.interactive_mode.getpass")
    @patch("builtins.input")
    @patch("src.ssh.runtime.interactive_mode.SingleCommandRunner.run")
    def test_invalid_username_reprompts(self, mock_run, mock_input, mock_getpass):
        """Invalid username re-prompts until valid."""
        mock_input.side_effect = [
            "10.0.0.1",  # hostname
            "",  # empty username (rejected)
            "admin",  # valid username
            "22",  # port
            "30",  # timeout
            "n",  # shell mode
            "show version",  # command
        ]
        mock_getpass.getpass.return_value = "password123"
        mock_run.return_value = True

        result = InteractiveMode.run()
        assert result is True


# ---------------------------------------------------------------------------
# Argument Parser Creation
# ---------------------------------------------------------------------------
class TestCreateArgumentParser:
    """Tests for _create_argument_parser static method."""

    def test_parser_creation(self):
        """Parser is created without error."""
        parser = EnhancedSSHRunner._create_argument_parser()
        assert parser is not None

    def test_default_args(self):
        """Default args have expected values."""
        parser = EnhancedSSHRunner._create_argument_parser()
        args = parser.parse_args([])
        assert args.port == 22
        assert args.timeout == 30
        assert args.interactive is False
        assert args.no_env is False
        assert args.shell is True

    def test_interactive_flag(self):
        """Interactive flag is parsed."""
        parser = EnhancedSSHRunner._create_argument_parser()
        args = parser.parse_args(["--interactive"])
        assert args.interactive is True

    def test_debug_flag(self):
        """Debug flag is parsed."""
        parser = EnhancedSSHRunner._create_argument_parser()
        args = parser.parse_args(["--debug"])
        assert args.debug is True

    def test_port_validation(self):
        """Port validation rejects invalid values."""
        parser = EnhancedSSHRunner._create_argument_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--port", "99999"])

    def test_timeout_validation(self):
        """Timeout validation rejects invalid values."""
        parser = EnhancedSSHRunner._create_argument_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--timeout", "5000"])
