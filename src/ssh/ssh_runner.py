"""Enhanced SSH runner for MistHelper remote command execution."""

from __future__ import annotations

import argparse
import getpass
import logging
import multiprocessing
import os
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from src.ssh.batch.batch_executor import BatchExecutor  # T013c: extracted non-interactive multi-command executor
from src.ssh.batch.multi_host_runner import MultiHostRunner  # T013c: extracted threaded multi-host orchestrator
from src.ssh.command.command_runner import SingleCommandRunner  # T013b: extracted single-command orchestrator
from src.ssh.config.csv_loader import CommandCsvLoader  # T013a: extracted CSV loader
from src.ssh.config.env_loader import EnvSshConfigLoader  # T013a: extracted .env loader
from src.ssh.config.validators import (  # T013a: shared validators (no more static-method dupes)
    validate_command,
    validate_hostname,
    validate_username,
)
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
    # InteractiveBatchExecutor.run() / BatchExecutor.run() / HostRunner.run() / MultiHostRunner.run() are
    # invoked directly by callers (run_application below, src/ssh/ssh_runner_manager.py, and tests).

    @staticmethod
    def run_application(args):  # type: ignore[no-untyped-def]  # noqa: C901, PLR0912, PLR0915
        """Main application logic - handles all the SSH runner functionality."""
        # Determine logging level (--debug flag overrides --log-level)
        log_level = "DEBUG" if args.debug else args.log_level

        # Setup logging with specified level
        logger = EnhancedSSHRunner._setup_logging(log_level)

        # Optional line-level tracing (only when debug enabled) to capture exact failing line
        tracer_installed = False
        previous_tracer = None
        if logger.isEnabledFor(logging.DEBUG):
            try:
                import sys

                runner_file = __file__
                # Rough bounds: limit tracing to lines inside this file within the class region to reduce noise
                CLASS_START = 14300  # approximate lower bound (keep generous)
                CLASS_END = 16600  # approximate upper bound

                def _ssh_line_tracer(frame, event, _arg):  # type: ignore[no-untyped-def]
                    if event == "line":
                        try:
                            if frame.f_code.co_filename == runner_file and CLASS_START <= frame.f_lineno <= CLASS_END:
                                logger.debug(f"[LINE] {frame.f_code.co_name}:{frame.f_lineno}")
                        except Exception:  # nosec B110
                            pass
                    return _ssh_line_tracer

                previous_tracer = sys.gettrace()
                sys.settrace(_ssh_line_tracer)
                tracer_installed = True
                logger.debug("[TRACE] Line-level tracer installed for EnhancedSSHRunner region")
            except Exception as _trace_e:
                logger.debug(f"[TRACE] Failed to install line tracer: {_trace_e}")

        # Interactive mode
        if args.interactive:
            return EnhancedSSHRunner._interactive_mode()  # type: ignore[no-untyped-call]

        # Determine if we should use .env file (default behavior unless --no-env is specified)
        use_env = not args.no_env

        # Try to load .env configuration
        env_config: dict[str, Any] = {}
        if use_env:
            logger.info("Loading SSH credentials from .env file (default behavior)")
            env_config = EnvSshConfigLoader().load()  # T013a: extracted loader
            if any([env_config.get("hosts"), env_config["username"], env_config["password"]]):
                host_count = len(env_config.get("hosts", []))
                hosts_str = ", ".join(env_config.get("hosts", [])) if host_count <= 3 else f"{host_count} hosts"
                logger.info(
                    f"Found .env credentials - Hosts: {hosts_str}, User: {env_config['username']}, Commands: {len(env_config['commands'])}"  # noqa: E501
                )

        # Determine final connection parameters (command line overrides .env)
        final_hosts = []
        if args.hostname:
            final_hosts = [args.hostname]  # Single host from command line
        elif env_config.get("hosts"):
            final_hosts = env_config["hosts"]  # Multiple hosts from .env

        final_username = args.username or env_config.get("username")
        final_password = env_config.get("password")  # Only from .env, never from command line

        # Handle secure password input if needed
        if not final_password and not args.secure:
            if final_username and final_hosts:
                host_display = final_hosts[0] if len(final_hosts) == 1 else f"{len(final_hosts)} hosts"
                final_password = getpass.getpass(f"!? Enter password for {final_username}@{host_display}: ")
            else:
                print("X  Password required but not provided")
                return False
        elif args.secure and not final_password:
            host_display = final_hosts[0] if len(final_hosts) == 1 else f"{len(final_hosts)} hosts"
            final_password = getpass.getpass(f"!? Enter password for {final_username}@{host_display}: ")
        # SECURITY: Password argument removed - this code block is no longer needed

        # Validate final parameters
        validated_hosts = []
        invalid_hosts = []

        for host in final_hosts:
            if validate_hostname(host):  # T013a: shared validator
                validated_hosts.append(host)
            else:
                invalid_hosts.append(host)

        if invalid_hosts:
            print(f"X  Invalid hosts detected: {', '.join(invalid_hosts)}")
            if not validated_hosts:
                print("X  No valid hosts remaining")
                return False
            else:
                print(f"[WARNING] Proceeding with {len(validated_hosts)} valid hosts")
                final_hosts = validated_hosts

        # Validate username
        if final_username and not validate_username(final_username):  # T013a: shared validator
            print(f"[ERROR] Invalid username format: {final_username}")
            return False

        # Check if we have minimum required parameters
        if not all([final_hosts, final_username, final_password]):
            missing = []
            if not final_hosts:
                missing.append("hostname/SSH_HOST")
            if not final_username:
                missing.append("username/SSH_USER")
            if not final_password:
                missing.append("password/SSH_PASSWORD")

            print(f"X  Error: Missing required parameters: {', '.join(missing)}")
            if use_env:
                print("!? Add these to your .env file or provide as command line arguments")
                print("!? Use --no-env flag to disable .env file loading")
            else:
                print("!? Provide as command line arguments or remove --no-env flag to use .env file")
                # Since we can't access the parser here, we'll let the caller handle help display
            return False

        # Determine commands to execute
        commands_to_run = []

        # Priority 1: Command line argument
        if args.command:
            commands_to_run = [args.command]
            logger.info(f"Using command from command line: {args.command}")
        # Priority 2: SSH_COMMANDS from .env file
        elif use_env and env_config.get("commands"):
            commands_to_run = env_config["commands"]
            logger.info(f"Using {len(commands_to_run)} commands from .env file: {commands_to_run}")
        # Priority 3: data/SSH_COMMANDS.CSV file as fallback
        elif not args.command:
            csv_commands = CommandCsvLoader().load()  # T013a: extracted CSV loader
            if csv_commands:
                commands_to_run = csv_commands
                logger.info(f"Using {len(commands_to_run)} commands from data/SSH_COMMANDS.CSV: {commands_to_run}")
                print(f"!? Loaded {len(commands_to_run)} commands from data/SSH_COMMANDS.CSV")
        # Priority 4: Interactive input
        else:
            # Check what command sources are available
            env_commands = env_config.get("commands", []) if use_env else []
            csv_commands = CommandCsvLoader().load() if not commands_to_run else []  # T013a: extracted CSV loader

            if env_commands and csv_commands:
                command = input(
                    f"!? Enter command to execute (or press Enter to use {len(env_commands)} commands from .env, or 'csv' for {len(csv_commands)} commands from CSV): "  # noqa: E501
                ).strip()
                if not command:
                    commands_to_run = env_commands
                    print(f"!? Using {len(commands_to_run)} commands from .env file: {commands_to_run}")
                elif command.lower() == "csv":
                    commands_to_run = csv_commands
                    print(f"!? Using {len(commands_to_run)} commands from data/SSH_COMMANDS.CSV: {commands_to_run}")
                else:
                    commands_to_run = [command]
            elif env_commands:
                command = input(
                    f"!? Enter command to execute (or press Enter to use {len(env_commands)} commands from .env): "
                ).strip()
                if not command:
                    commands_to_run = env_commands
                    print(f"!? Using {len(commands_to_run)} commands from .env file: {commands_to_run}")
                else:
                    commands_to_run = [command]
            elif csv_commands:
                command = input(
                    f"!? Enter command to execute (or press Enter to use {len(csv_commands)} commands from data/SSH_COMMANDS.CSV): "  # noqa: E501
                ).strip()
                if not command:
                    commands_to_run = csv_commands
                    print(f"!? Using {len(commands_to_run)} commands from data/SSH_COMMANDS.CSV: {commands_to_run}")
                else:
                    commands_to_run = [command]
            else:
                command = input("!? Enter command to execute: ").strip()
                if not command:
                    print("X  No commands specified")
                    return False
                commands_to_run = [command]

        # Validate commands
        validated_commands = []
        invalid_commands = []

        for cmd in commands_to_run:
            if validate_command(cmd):  # T013a: shared validator
                validated_commands.append(cmd)
            else:
                invalid_cmd = cmd[:50] + "..." if len(cmd) > 50 else cmd
                invalid_commands.append(invalid_cmd)

        if invalid_commands:
            print(f"X  Invalid commands detected: {', '.join(invalid_commands)}")
            if not validated_commands:
                print("X  No valid commands remaining")
                return False
            else:
                print(f"!? Proceeding with {len(validated_commands)} valid commands")
                commands_to_run = validated_commands

        if not commands_to_run:
            print("X  No commands to execute")
            return False

        # Determine shell mode (default is True unless --no-shell is specified)
        use_shell_mode = args.shell and not args.no_shell

        # Execute SSH commands
        # At this point, credentials are validated to be non-None
        assert final_username is not None, "Username should be validated"  # nosec B101
        assert final_password is not None, "Password should be validated"  # nosec B101

        try:
            if len(final_hosts) == 1:
                # Single host execution
                hostname = final_hosts[0]
                if len(commands_to_run) == 1:
                    # T013b: single-command orchestration moved to SingleCommandRunner.run()
                    ssh_success = SingleCommandRunner.run(
                        hostname,
                        str(final_username),
                        str(final_password),
                        commands_to_run[0],
                        args.port,
                        args.timeout,
                        use_shell_mode,
                    )
                else:
                    # Multiple commands on single host — T013c: direct call to BatchExecutor (no façade)
                    ssh_success = BatchExecutor.run(
                        hostname,
                        str(final_username),
                        str(final_password),
                        commands_to_run,
                        args.port,
                        args.timeout,
                        use_shell_mode,
                    )

                return ssh_success

            else:
                # Multiple host execution (multi-threaded)
                default_threads = multiprocessing.cpu_count()
                requested_threads = args.max_threads or default_threads
                max_threads = EnhancedSSHRunner._validate_thread_count(requested_threads, len(final_hosts))

                if max_threads != requested_threads:
                    print(f"!? Adjusted thread count from {requested_threads} to {max_threads}")

                ssh_results = MultiHostRunner.run(  # T013c: direct call to MultiHostRunner (no façade)
                    final_hosts,
                    str(final_username),
                    str(final_password),
                    commands_to_run,
                    args.port,
                    args.timeout,
                    use_shell_mode,
                    max_threads,
                )

                # Return success if all hosts succeeded
                return ssh_results["failed"] == 0

        except KeyboardInterrupt:
            print("\n[INTERRUPT] Operation cancelled by user")
            return False
        except Exception as e:
            # Enhanced diagnostic logging for elusive dict+float TypeError
            logger.error("Fatal error during SSH runner execution", exc_info=True)
            try:
                logger.debug(f"[DIAG] Type of exception object: {type(e)}")
            except Exception:  # nosec B110
                pass
            print(f"X  Fatal error: {e}")
            return False
        finally:
            if tracer_installed:
                try:
                    import sys

                    sys.settrace(previous_tracer)
                    logger.debug("[TRACE] Line-level tracer removed")
                except Exception as _trace_cleanup_e:
                    logger.debug(f"[TRACE] Failed to remove line tracer: {_trace_cleanup_e}")

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

    @staticmethod
    def _interactive_mode():  # type: ignore[no-untyped-def]  # noqa: C901, PLR0912, PLR0915
        """Interactive mode for SSH command execution with input validation."""
        print("- Enhanced SSH Command Runner v2 - Interactive Mode")
        print("=" * 60)

        # Get connection details with validation
        while True:
            hostname = input("- Enter hostname or IP address: ").strip()
            if not hostname:
                print("X  Hostname is required")
                continue
            if not validate_hostname(hostname):  # T013a: shared validator
                print("X  Invalid hostname or IP address format")
                continue
            break

        while True:
            username = input("X  Enter username: ").strip()
            if not username:
                print("X  Username is required")
                continue
            if not validate_username(username):  # T013a: shared validator
                print("X  Invalid username format (alphanumeric, underscore, hyphen, dot only)")
                continue
            break

        password = getpass.getpass("!? Enter password: ")
        if not password:
            print("X  Password is required")
            return False

        # Optional settings with validation
        while True:
            try:
                port_input = input(">> Enter SSH port (default 22): ").strip()
                if not port_input:
                    port = 22
                    break
                port = int(port_input)
                if not SshConnector._validate_port(port):
                    print("X  Port must be between 1 and 65535")
                    continue
                break
            except ValueError:
                print("X  Port must be a valid number")

        while True:
            try:
                timeout_input = input("- Enter timeout in seconds (default 30): ").strip()
                if not timeout_input:
                    timeout = 30
                    break
                timeout = int(timeout_input)
                if not EnhancedSSHRunner._validate_timeout(timeout):
                    print("X  Timeout must be between 1 and 3600 seconds")
                    continue
                break
            except ValueError:
                print("X  Timeout must be a valid number")

        # Execution mode
        shell_mode = input("X  Use interactive shell mode? (y/N - recommended for network devices): ").strip().lower()
        use_shell = shell_mode in ["y", "yes", "true", "1"]

        # Get command with validation
        while True:
            command = input("!? Enter command to execute: ").strip()
            if not command:
                print("X  Command is required")
                continue
            if not validate_command(command):  # T013a: shared validator
                print("X  Invalid command (too long or contains null bytes)")
                continue
            break

        print(f"\n>> Starting SSH session (shell_mode={use_shell})...")

        # T013b: single-command orchestration moved to SingleCommandRunner.run()
        return SingleCommandRunner.run(hostname, username, password, command, port, timeout, use_shell)
