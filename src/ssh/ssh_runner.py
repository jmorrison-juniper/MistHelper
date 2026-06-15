"""Enhanced SSH runner for MistHelper remote command execution."""

from __future__ import annotations

import argparse
import logging
import multiprocessing
import os
import re
import time
from dataclasses import dataclass, field
from datetime import datetime

from src.ssh.connection.connector import SshConnector  # T013b: extracted connection establishment
from src.ssh.shell_execution.shell_executor import ShellExecutor  # T013b: extracted interactive-shell executor


@dataclass
class SSHConnectionConfig:
    """Configuration for SSH connections - groups connection parameters."""

    hostname: str
    username: str
    password: str
    port: int = 22
    timeout: int = 30
    use_shell: bool = True


@dataclass
class SSHExecutionConfig:
    """Configuration for SSH command execution - groups execution parameters."""

    commands: list[str] = field(default_factory=list)
    max_threads: int = 5
    use_shell: bool = True


class EnhancedSSHRunner:
    """Advanced SSH connection and command execution handler with comprehensive validation."""

    def __init__(self, timeout: int = 30, logger: logging.Logger | None = None):
        """Initialize SSH runner.

        Args:
            timeout: Connection timeout in seconds
            logger: Logger instance
        """
        self.timeout = timeout
        self.client = None
        self.logger = logger or logging.getLogger("ssh_runner_v2")
        self.managed_known_hosts_path: str | None = None
        self.logger.debug(f"EnhancedSSHRunner initialized with timeout={timeout}")

    @staticmethod
    def _get_data_directory() -> str:
        """Return the workspace data directory used for persistent SSH metadata."""
        data_dir = "data"
        os.makedirs(data_dir, exist_ok=True)
        return data_dir

    # T013b: Known-hosts management + _connect moved to src.ssh.connection.connector.SshConnector.
    # T013b: _validate_port moved to SshConnector._validate_port (still a staticmethod there).

    @staticmethod
    def _validate_timeout(timeout: int) -> bool:
        """Validate timeout value is reasonable.

        Args:
            timeout: Timeout in seconds

        Returns:
            bool: True if valid (1-3600), False otherwise
        """
        return isinstance(timeout, int) and 1 <= timeout <= 3600

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename to prevent directory traversal and invalid characters.

        Args:
            filename: Original filename

        Returns:
            str: Sanitized filename safe for filesystem use
        """
        if not filename:
            return "unknown"

        # Remove or replace dangerous characters
        # Keep only alphanumeric, underscore, hyphen, and dot
        sanitized = re.sub(r"[^\w\-_\.]", "_", filename)

        # Remove leading/trailing dots and dashes
        sanitized = sanitized.strip(".-")

        # Ensure filename isn't empty after sanitization
        if not sanitized:
            sanitized = "sanitized_host"

        # Limit length to prevent filesystem issues
        if len(sanitized) > 100:
            sanitized = sanitized[:100]

        # Prevent reserved filenames on Windows
        reserved_names = (
            ["CON", "PRN", "AUX", "NUL"]
            + [f"COM{port_num}" for port_num in range(1, 10)]
            + [f"LPT{port_num}" for port_num in range(1, 10)]
        )
        if sanitized.upper() in reserved_names:
            sanitized = f"host_{sanitized}"

        return sanitized

    @staticmethod
    def _validate_thread_count(thread_count: int, max_hosts: int) -> int:
        """Validate and adjust thread count to reasonable limits.

        Args:
            thread_count: Requested thread count
            max_hosts: Maximum number of hosts

        Returns:
            int: Validated thread count
        """
        if not isinstance(thread_count, int) or thread_count <= 0:
            return min(max_hosts, multiprocessing.cpu_count())

        # Limit to reasonable maximum (don't overwhelm system)
        max_reasonable_threads = min(50, max_hosts * 2)
        return min(thread_count, max_reasonable_threads, max_hosts)

    def _create_secure_log_file(self, hostname: str) -> tuple:  # type: ignore[type-arg]
        """Create a secure per-host log file with proper sanitization.

        Args:
            hostname: Original hostname

        Returns:
            tuple: (log_file_path, write_function)
        """
        # Create per-host log file in subfolder with proper sanitization
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_hostname = self.sanitize_filename(hostname)

        # Ensure per-host-logs directory exists and is secure (in data folder)
        # SECURITY: Use proper data directory path to avoid permission issues
        data_dir = EnhancedSSHRunner._get_data_directory()
        log_dir = os.path.join(data_dir, "per-host-logs")
        try:
            os.makedirs(log_dir, exist_ok=True)
            # Set secure permissions on directory (owner read/write/execute only)
            if hasattr(os, "chmod"):
                os.chmod(log_dir, 0o700)
        except OSError as e:
            self.logger.error(f"Failed to create log directory {log_dir}: {e}")
            # Fallback to data directory
            log_dir = data_dir
            safe_hostname = f"fallback_{safe_hostname}"

        host_log_file = os.path.join(log_dir, f"ssh_output_{safe_hostname}_{timestamp}.log")

        def write_to_host_log(message: str):  # type: ignore[no-untyped-def]
            """Write message to host-specific log file only (not console)."""
            if not message:
                return

            try:
                # Sanitize message to prevent log injection
                safe_message = message.replace("\x00", "").replace("\r\n", "\n")

                with open(host_log_file, "a", encoding="utf-8") as f:
                    f.write(f"{safe_message}\n")
                    f.flush()  # Ensure data is written immediately
            except OSError as e:
                self.logger.error(f"IO error writing to host log {host_log_file}: {e}")
            except UnicodeEncodeError as e:
                self.logger.error(f"Unicode encoding error writing to host log {host_log_file}: {e}")
                # Try writing a sanitized version
                try:
                    safe_message = message.encode("ascii", errors="replace").decode("ascii")
                    with open(host_log_file, "a", encoding="utf-8") as f:
                        f.write(f"{safe_message}\n")
                        f.flush()
                except Exception:
                    self.logger.error("Failed to write sanitized message to host log")
            except Exception as e:
                self.logger.error(f"Unexpected error writing to host log {host_log_file}: {e}")

        return host_log_file, write_to_host_log

    # T013b: _connect moved to src.ssh.connection.connector.SshConnector. Callers within this
    # module construct SshConnector inline (a real call, not a façade) and wire the returned
    # client into the runner's ``client``/``managed_known_hosts_path`` attributes themselves.

    def _execute_command(
        self, command: str, use_shell: bool = False, hostname: str = "unknown"
    ) -> tuple[bool, str, str]:
        """Execute command on remote host.

        Args:
            command: Command to execute
            use_shell: Use interactive shell instead of exec_command (better for network devices)
            hostname: Hostname for display purposes

        Returns:
            Tuple of (success, stdout, stderr)
        """
        if not self.client:
            error_msg = "No active SSH connection"
            self.logger.error(error_msg)
            return False, "", error_msg

        try:
            self.logger.debug(f"Executing command: '{command}' (shell_mode={use_shell})")
            self.logger.debug(f"Command execution method: {'shell' if use_shell else 'direct'}")

            command_start = time.time()

            if use_shell:
                # T013b: shell execution moved to ShellExecutor; construct inline (real call, not façade)
                self.logger.debug("Using shell-based execution for network device compatibility")
                shell_executor = ShellExecutor(  # T013b: instantiate the extracted shell executor
                    client=self.client, timeout=self.timeout, logger=self.logger
                )
                return shell_executor.execute(command, command_start, hostname)  # Real delegation w/ instance state
            else:
                # Use direct exec_command (try with PTY first for network devices)
                self.logger.debug("Using direct exec_command execution")
                return self._execute_direct(command, command_start, hostname)

        except TimeoutError:
            error_msg = f"Command execution timeout after {self.timeout} seconds"
            self.logger.error(error_msg)
            return False, "", error_msg
        except Exception as e:
            error_msg = f"Execution error: {type(e).__name__}: {e}"
            self.logger.error(error_msg, exc_info=True)
            return False, "", error_msg

    def _execute_direct(
        self,
        command: str,
        start_time: float,
        hostname: str = "unknown",
    ) -> tuple[bool, str, str]:  # nosec B101
        """Execute command using exec_command with PTY support."""
        assert self.client is not None, "No active SSH connection"  # nosec B101
        try:
            # Try with PTY first (better for network devices)  # nosec B601
            self.logger.debug("Attempting exec_command with get_pty=True")
            stdin, stdout, stderr = self.client.exec_command(command, timeout=self.timeout, get_pty=True)  # nosec B601

            # Get output
            stdout_output = stdout.read().decode("utf-8", errors="ignore")
            stderr_output = stderr.read().decode("utf-8", errors="ignore")
            exit_status = stdout.channel.recv_exit_status()
            command_time = time.time() - start_time

            self.logger.debug(f"Command completed in {command_time:.2f} seconds with exit status: {exit_status}")
            # Escape newlines and special characters for clean logging
            stdout_sample = stdout_output[:200].replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
            self.logger.debug(
                f"STDOUT ({len(stdout_output)} chars): {stdout_sample}{'...' if len(stdout_output) > 200 else ''}"
            )

            if stderr_output:
                stderr_sample = stderr_output[:200].replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
                self.logger.warning(
                    f"STDERR ({len(stderr_output)} chars): {stderr_sample}{'...' if len(stderr_output) > 200 else ''}"
                )

            print(f"- [{hostname}] Command completed with exit status: {exit_status}")
            return exit_status == 0, stdout_output, stderr_output

        except Exception as e:
            # If PTY fails, try without PTY
            self.logger.warning(f"exec_command with PTY failed: {e}, trying without PTY")
            try:
                stdin, stdout, stderr = self.client.exec_command(command, timeout=self.timeout)  # nosec B601
                stdout_output = stdout.read().decode("utf-8", errors="ignore")
                stderr_output = stderr.read().decode("utf-8", errors="ignore")
                exit_status = stdout.channel.recv_exit_status()
                command_time = time.time() - start_time

                self.logger.debug(
                    f"Command completed (no PTY) in {command_time:.2f} seconds with exit status: {exit_status}"
                )
                print(f"- [{hostname}] Command completed with exit status: {exit_status}")
                return exit_status == 0, stdout_output, stderr_output
            except Exception as e2:
                self.logger.error(f"Both PTY and non-PTY exec_command failed: {e2}")
                raise e2

    # T013b: _execute_with_shell moved to src.ssh.shell_execution.shell_executor.ShellExecutor.
    # Callers (_execute_command) instantiate ShellExecutor inline (real call, not facade).

    def connect(self, hostname: str, username: str, password: str, port: int = 22) -> bool:
        """Establish SSH connection to the remote host.

        Delegates to :class:`src.ssh.connection.connector.SshConnector` (T013b:
        extracted connection logic) and wires the returned paramiko client into
        ``self.client`` / ``self.managed_known_hosts_path`` so callers that access
        ``runner.client.invoke_shell()`` directly keep working unchanged.

        Args:
            hostname: IP address or hostname of the target device.
            username: SSH username.
            password: SSH password.
            port: SSH port number (default 22).

        Returns:
            bool: True when the connection is established, False on any error.
        """
        logging.info("EnhancedSSHRunner.connect called for %s@%s:%s", username, hostname, port)  # Pre-action log
        from src.ssh.connection.connector import SshConnector  # Late import; avoids circular deps at module load
        connector = SshConnector(timeout=self.timeout, logger=self.logger)  # Real delegation to T013b module
        client, kh_path = connector.connect(hostname, username, password, port)  # Returns (SSHClient|None, path|None)
        if client is None:  # SshConnector already logged and printed the specific error
            self.logger.debug("SshConnector.connect returned None for %s; connection failed", hostname)
            return False  # Propagate failure to caller for early-return guard
        self.client = client  # Wire the live paramiko client so invoke_shell() / exec_command() work
        self.managed_known_hosts_path = kh_path  # Persist TOFU known-hosts path for cleanup on disconnect
        self.logger.debug("EnhancedSSHRunner.connect succeeded for %s:%s; client wired", hostname, port)
        return True  # Connection live; caller can now use runner.client directly

    def _disconnect(self):  # type: ignore[no-untyped-def]
        """Close SSH connection."""
        if self.client:
            self.logger.debug("Closing SSH connection")
            self.client.close()
            self.client = None
            print(">> SSH connection closed")
        else:
            self.logger.debug("No SSH connection to close")

    @staticmethod
    def _setup_logging(log_level: str = "INFO") -> logging.Logger:
        """Setup comprehensive logging configuration with syslog-style levels.

        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

        Returns:
            logging.Logger: Configured logger instance
        """
        # Unified logging: use root handlers (script.log + console) only
        logger = logging.getLogger("ssh_runner_v2")
        logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        # Remove any prior dedicated handlers so we don't duplicate output
        for h in list(logger.handlers):
            logger.removeHandler(h)
        # Ensure messages bubble to root configuration
        logger.propagate = True
        # Emit initialization message (will land in script.log)
        if log_level.upper() == "DEBUG":
            logger.debug("Enhanced SSH Runner v2 logging initialized (root handlers)")
        else:
            logger.info("Enhanced SSH Runner v2 logging initialized (root handlers)")
        return logger

    # T013c: _run_multiple_ssh_commands_interactive, _run_multiple_ssh_commands, _run_ssh_command_on_host,
    # and run_ssh_commands_multi_host have all been moved out of EnhancedSSHRunner into src.ssh.batch.*.
    # T013d: run_application + _interactive_mode have been moved to src.ssh.runtime.{app_runner,interactive_mode}.
    # Callers MUST use AppRunner.run(args) / InteractiveMode.run() directly (no façade indirection).

    @staticmethod
    def _create_argument_parser():  # type: ignore[no-untyped-def]
        """Create and configure the argument parser."""
        parser = argparse.ArgumentParser(
            description="Enhanced SSH Command Runner v2 - Execute commands on remote hosts via SSH",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
    # Default: Uses .env file and shell mode (recommended)
    python ssh_runner_v2.py

    # Override with specific command (still uses shell mode by default)
    python ssh_runner_v2.py "show version"

    # Manual SSH connection (uses secure password prompt)
    python ssh_runner_v2.py 192.168.1.1 vyos --secure "show version"

    # Use exec_command mode instead of shell mode
    python ssh_runner_v2.py --no-shell "ls -la"

    # Multi-host with custom thread count
    python ssh_runner_v2.py --max-threads 10

    # Interactive mode
    python ssh_runner_v2.py --interactive

    # Disable .env loading and use exec_command mode with secure password
    python ssh_runner_v2.py --no-env --no-shell --secure 192.168.1.1 vyos "show version"

.env file format (SECURITY: Keep this file private and out of version control):
    SSH_HOST=192.168.1.1,192.168.1.2,192.168.1.3
    SSH_USER=vyos
    SSH_PASSWORD=your_password
    SSH_COMMANDS=show version,show interfaces,show route

SECURITY NOTES:
    - Never commit .env files containing passwords to version control
    - Use secure password prompts (--secure flag) when possible
    - Consider using SSH keys instead of passwords for better security
    - Add .env to your .gitignore file
            """,
        )

        # Interactive mode
        parser.add_argument("--interactive", "-i", action="store_true", help="Run in interactive mode")

        # .env file mode controls
        parser.add_argument(
            "--no-env", action="store_true", help="Disable automatic .env file loading (use manual credentials)"
        )

        # Connection parameters
        parser.add_argument("hostname", nargs="?", help="Hostname or IP address (overrides SSH_HOST)")
        parser.add_argument("username", nargs="?", help="SSH username (overrides SSH_USER)")
        parser.add_argument("password", nargs="?", help="SSH password (overrides SSH_PASSWORD)")
        parser.add_argument("command", nargs="?", help="Command to execute (overrides SSH_COMMANDS)")

        # Optional parameters with validation
        def validate_port_arg(value):  # type: ignore[no-untyped-def]
            ivalue = int(value)
            if not SshConnector._validate_port(ivalue):
                raise argparse.ArgumentTypeError(f"Port must be between 1 and 65535, got {ivalue}")
            return ivalue

        def validate_timeout_arg(value):  # type: ignore[no-untyped-def]
            ivalue = int(value)
            if not EnhancedSSHRunner._validate_timeout(ivalue):
                raise argparse.ArgumentTypeError(f"Timeout must be between 1 and 3600 seconds, got {ivalue}")
            return ivalue

        def validate_threads_arg(value):  # type: ignore[no-untyped-def]
            ivalue = int(value)
            if ivalue <= 0 or ivalue > 100:
                raise argparse.ArgumentTypeError(f"Thread count must be between 1 and 100, got {ivalue}")
            return ivalue

        parser.add_argument("--port", "-p", type=validate_port_arg, default=22, help="SSH port (default: 22)")
        parser.add_argument(
            "--timeout", "-t", type=validate_timeout_arg, default=30, help="Connection timeout in seconds (default: 30)"
        )
        parser.add_argument(
            "--secure", "-s", action="store_true", help="Prompt for password securely instead of command line"
        )
        parser.add_argument(
            "--shell",
            action="store_true",
            default=True,
            help="Use interactive shell mode (default, recommended for network devices)",
        )
        parser.add_argument("--no-shell", action="store_true", help="Disable shell mode and use exec_command instead")
        parser.add_argument(
            "--log-level",
            choices=["DEBUG", "INFO", "WARNING", "ERROR"],
            default="INFO",
            help="Set logging level (default: INFO)",
        )
        parser.add_argument(
            "--debug", "-d", action="store_true", help="Enable debug logging (equivalent to --log-level DEBUG)"
        )
        parser.add_argument(
            "--max-threads",
            type=validate_threads_arg,
            default=None,
            help=f"Maximum threads for multi-host execution (default: {multiprocessing.cpu_count()} cores)",
        )

        return parser
