"""Enhanced SSH runner for MistHelper remote command execution."""

from __future__ import annotations  # WHY: enable PEP 563 postponed evaluation for cleaner type hints

import argparse  # WHY: build the CLI argument parser used by the runner entrypoint
import logging  # WHY: emit structured logs at each stage of SSH execution
import multiprocessing  # WHY: default the thread cap to the machine's CPU count
import os  # WHY: filesystem operations for data/log directories and chmod
import re  # WHY: compile the filename sanitization regex once at module scope
import time  # WHY: measure command execution wall-clock time
from collections.abc import Callable  # WHY: annotate the write-log callable returned to callers
from dataclasses import dataclass, field  # WHY: define the two SSH configuration dataclasses
from datetime import datetime  # WHY: build timestamped log filenames (patched by tests at module scope)
from functools import partial  # WHY: build a per-log-file writer without an inner def (CC/blocks reduction)

from src.ssh.connection.connector import SshConnector  # WHY: T013b - extracted connection establishment
from src.ssh.shell_execution.shell_executor import ShellExecutor  # WHY: T013b - extracted interactive-shell executor

# ---------------------------------------------------------------------------
# Module constants (replace magic values scattered through the class body)
# ---------------------------------------------------------------------------
_DEFAULT_TIMEOUT_SEC: int = 30  # WHY: default SSH connect/exec timeout
_MIN_TIMEOUT_SEC: int = 1  # WHY: lower bound for accepted timeout values
_MAX_TIMEOUT_SEC: int = 3600  # WHY: upper bound (1 hour) for accepted timeout values
_DEFAULT_PORT: int = 22  # WHY: standard SSH port used everywhere in this module
_DEFAULT_MAX_THREADS: int = 5  # WHY: default multi-host thread cap used by SSHExecutionConfig
_MAX_FILENAME_LEN: int = 100  # WHY: cap sanitized filenames to a filesystem-safe length
_MAX_THREADS_HARD_CAP: int = 50  # WHY: do not let callers request more than 50 SSH worker threads
_THREADS_PER_HOST_MULTIPLIER: int = 2  # WHY: cap threads at 2x the host count for a sensible default
_MAX_STDOUT_SAMPLE_CHARS: int = 200  # WHY: only sample the first 200 chars of stdout/stderr into logs
_DEFAULT_LOGGER_NAME: str = "ssh_runner_v2"  # WHY: named logger asserted by tests and callers
_DATA_DIR_NAME: str = "data"  # WHY: workspace-relative directory for runtime data
_PER_HOST_LOG_DIR_NAME: str = "per-host-logs"  # WHY: subdirectory holding per-host command output logs
_LOG_DIR_MODE: int = 0o700  # WHY: restrict per-host-logs to owner rwx only
_TIMESTAMP_FORMAT: str = "%Y%m%d_%H%M%S"  # WHY: filesystem-safe timestamp used in log filenames
_SANITIZE_PATTERN: re.Pattern[str] = re.compile(r"[^\w\-_\.]")  # WHY: precompile filename char whitelist regex
_FALLBACK_SANITIZED: str = "sanitized_host"  # WHY: used when sanitization strips all characters
_UNKNOWN_SANITIZED: str = "unknown"  # WHY: used when the caller passes an empty filename
_UNKNOWN_HOSTNAME: str = "unknown"  # WHY: default hostname sentinel for exec logging
_LOG_INIT_MSG: str = "Enhanced SSH Runner v2 logging initialized (root handlers)"  # WHY: consistent init log line
_RESERVED_INDEX_RANGE = range(1, 10)  # WHY: Windows COM/LPT device names are COM1..COM9 and LPT1..LPT9
_WINDOWS_RESERVED: frozenset[str] = frozenset(  # WHY: precompute reserved device set to remove branching from function
    ["CON", "PRN", "AUX", "NUL"]  # WHY: single-word Windows reserved device names
    + [f"COM{index}" for index in _RESERVED_INDEX_RANGE]  # WHY: COM1..COM9 serial device names
    + [f"LPT{index}" for index in _RESERVED_INDEX_RANGE]  # WHY: LPT1..LPT9 parallel device names
)

_ARGPARSE_EPILOG: str = """
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
            """  # WHY: help-text epilog kept identical to preserve CLI --help output


# ---------------------------------------------------------------------------
# Module-level helper functions (pull nested logic out to keep methods small)
# ---------------------------------------------------------------------------
def _is_windows_reserved(name: str) -> bool:
    """Return True when the supplied filename matches a Windows reserved device name."""
    return name.upper() in _WINDOWS_RESERVED  # WHY: precomputed frozenset lookup keeps caller CC low


def _apply_length_limit(name: str) -> str:
    """Truncate the filename to _MAX_FILENAME_LEN characters when it exceeds the limit."""
    return name[:_MAX_FILENAME_LEN] if len(name) > _MAX_FILENAME_LEN else name  # WHY: filesystem length safety


def _sanitize_log_message(message: str) -> str:
    """Remove NUL bytes and normalize CRLF pairs so log injection is not possible."""
    without_nul = message.replace("\x00", "")  # WHY: NUL breaks many log viewers - strip it first
    return without_nul.replace("\r\n", "\n")  # WHY: normalize to LF to avoid double-blank-lines in the log


def _ascii_fallback(message: str) -> str:
    """Convert a message to ASCII, replacing bytes that cannot be encoded."""
    return message.encode("ascii", errors="replace").decode("ascii")  # WHY: recover after UnicodeEncodeError


def _append_log_line(log_path: str, line: str) -> None:
    """Append a single line to the log file, flushing immediately for durability."""
    with open(log_path, "a", encoding="utf-8") as handle:  # WHY: append mode preserves prior host log content
        handle.write(f"{line}\n")  # WHY: caller supplies pre-sanitized text - just append + newline
        handle.flush()  # WHY: flush so an interrupted run still leaves a readable log


def _format_output_sample(output: str) -> str:
    """Return the first _MAX_STDOUT_SAMPLE_CHARS with control chars escaped for one-line logging."""
    head = output[:_MAX_STDOUT_SAMPLE_CHARS]  # WHY: slice before escaping to bound sample length
    return head.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")  # WHY: keep sample single-line


def _sample_suffix(output: str) -> str:
    """Return '...' when the output was truncated by _format_output_sample, else ''."""
    return "..." if len(output) > _MAX_STDOUT_SAMPLE_CHARS else ""  # WHY: mirrors original truncation indicator


def _validate_port_arg(value: str) -> int:
    """Validate the --port argparse value ensuring it is in 1..65535."""
    parsed = int(value)  # WHY: argparse hands strings; convert to int for range validation
    if not SshConnector._validate_port(parsed):  # WHY: delegate to canonical port validator in connector
        msg = f"Port must be between 1 and 65535, got {parsed}"  # WHY: shorten for line length
        raise argparse.ArgumentTypeError(msg)  # WHY: same message as before
    return parsed  # WHY: return the validated int back to argparse


def _validate_timeout_arg(value: str) -> int:
    """Validate the --timeout argparse value ensuring it is in 1..3600."""
    parsed = int(value)  # WHY: argparse gives strings; convert to int for validation
    if not EnhancedSSHRunner._validate_timeout(parsed):  # WHY: reuse the same runner-level timeout validator
        raise argparse.ArgumentTypeError(  # WHY: preserve legacy error text so users' scripts still parse it
            f"Timeout must be between 1 and 3600 seconds, got {parsed}"
        )
    return parsed  # WHY: hand the validated timeout back to argparse


def _validate_threads_arg(value: str) -> int:
    """Validate the --max-threads argparse value ensuring 1..100 inclusive."""
    parsed = int(value)  # WHY: argparse hands strings; convert to int for range validation
    if parsed <= 0 or parsed > 100:  # WHY: explicit bounds keep the CLI safe and predictable
        raise argparse.ArgumentTypeError(f"Thread count must be between 1 and 100, got {parsed}")  # WHY: keep msg
    return parsed  # WHY: return validated thread cap


@dataclass
class SSHConnectionConfig:
    """Configuration for SSH connections - groups connection parameters."""

    hostname: str  # WHY: target SSH host required for every connection
    username: str  # WHY: SSH account used for the login
    password: str  # WHY: SSH password paired with username (may be empty when using keys)
    port: int = _DEFAULT_PORT  # WHY: default to standard SSH port 22
    timeout: int = _DEFAULT_TIMEOUT_SEC  # WHY: default 30s matches historical CLI behavior
    use_shell: bool = True  # WHY: shell mode is preferred for network devices by default


@dataclass
class SSHExecutionConfig:
    """Configuration for SSH command execution - groups execution parameters."""

    commands: list[str] = field(default_factory=list)  # WHY: empty command list is a valid default
    max_threads: int = _DEFAULT_MAX_THREADS  # WHY: default multi-host worker count kept identical to legacy CLI
    use_shell: bool = True  # WHY: shell mode is preferred for network devices by default


class EnhancedSSHRunner:
    """Advanced SSH connection and command execution handler with comprehensive validation."""

    def __init__(self, timeout: int = _DEFAULT_TIMEOUT_SEC, logger: logging.Logger | None = None) -> None:
        """Initialize SSH runner.

        Args:
            timeout: Connection timeout in seconds
            logger: Logger instance
        """
        self.timeout = timeout  # WHY: store timeout for both connect and command exec paths
        self.client = None  # WHY: paramiko client is attached by the connector; None means not connected
        self.logger = logger or logging.getLogger(_DEFAULT_LOGGER_NAME)  # WHY: fall back to the module logger name
        self.managed_known_hosts_path: str | None = None  # WHY: connector writes the managed known-hosts path here
        self.logger.debug("EnhancedSSHRunner initialized with timeout=%s", timeout)  # WHY: trace-level init evidence

    @staticmethod
    def _get_data_directory() -> str:
        """Return the workspace data directory used for persistent SSH metadata."""
        data_dir = _DATA_DIR_NAME  # WHY: use the module constant so tests and callers agree on the folder name
        os.makedirs(data_dir, exist_ok=True)  # WHY: create-on-demand so first call succeeds on fresh checkouts
        return data_dir  # WHY: hand back the string path for use in os.path.join()

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
        # WHY: require int and in [1, 3600] to avoid absurd timeouts propagating to paramiko
        return isinstance(timeout, int) and _MIN_TIMEOUT_SEC <= timeout <= _MAX_TIMEOUT_SEC

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename to prevent directory traversal and invalid characters.

        Args:
            filename: Original filename

        Returns:
            str: Sanitized filename safe for filesystem use
        """
        if not filename:  # WHY: empty inputs get a stable placeholder rather than an empty path segment
            return _UNKNOWN_SANITIZED  # WHY: preserves legacy "unknown" return value for empty inputs
        sanitized = _SANITIZE_PATTERN.sub("_", filename)  # WHY: whitelist alnum/dot/dash/underscore; replace rest
        sanitized = sanitized.strip(".-") or _FALLBACK_SANITIZED  # WHY: drop leading/trailing dots and dashes safely
        sanitized = _apply_length_limit(sanitized)  # WHY: cap filename length to keep filesystem happy
        if _is_windows_reserved(sanitized):  # WHY: rewrite reserved device names so Windows will not reject them
            sanitized = f"host_{sanitized}"  # WHY: preserved legacy prefix pattern used by callers/tests
        return sanitized  # WHY: return the finalized filesystem-safe string

    @staticmethod
    def _validate_thread_count(thread_count: int, max_hosts: int) -> int:
        """Validate and adjust thread count to reasonable limits.

        Args:
            thread_count: Requested thread count
            max_hosts: Maximum number of hosts

        Returns:
            int: Validated thread count
        """
        if not isinstance(thread_count, int) or thread_count <= 0:  # WHY: coerce invalid input to a sane default
            return min(max_hosts, multiprocessing.cpu_count())  # WHY: use CPU count when caller was ambiguous
        max_reasonable = min(_MAX_THREADS_HARD_CAP, max_hosts * _THREADS_PER_HOST_MULTIPLIER)  # WHY: bound growth
        return min(thread_count, max_reasonable, max_hosts)  # WHY: final cap is the smallest of the three limits

    def _create_secure_log_file(self, hostname: str) -> tuple[str, Callable[[str], None]]:
        """Create a secure per-host log file with proper sanitization.

        Args:
            hostname: Original hostname

        Returns:
            tuple: (log_file_path, write_function)
        """
        log_dir, safe_hostname = self._prepare_log_directory(hostname)  # WHY: extract dir setup to a helper
        timestamp = datetime.now().strftime(_TIMESTAMP_FORMAT)  # WHY: filesystem-safe timestamp for the filename
        log_path = os.path.join(log_dir, f"ssh_output_{safe_hostname}_{timestamp}.log")  # WHY: canonical filename shape
        writer = partial(self._write_to_host_log, log_path)  # WHY: bind log_path once so callers pass only messages
        return log_path, writer  # WHY: return path + callable exactly as legacy contract requires

    def _prepare_log_directory(self, hostname: str) -> tuple[str, str]:
        """Ensure the per-host log directory exists and return (dir, safe_hostname)."""
        safe_hostname = self.sanitize_filename(hostname)  # WHY: guard against traversal and invalid characters
        data_dir = EnhancedSSHRunner._get_data_directory()  # WHY: workspace data folder acts as the parent dir
        log_dir = os.path.join(data_dir, _PER_HOST_LOG_DIR_NAME)  # WHY: per-host-logs is scoped under data/
        try:
            os.makedirs(log_dir, exist_ok=True)  # WHY: create the subdir on demand for the very first host
            self._maybe_lock_log_dir(log_dir)  # WHY: chmod only when the platform supports it (POSIX-only)
        except OSError as exc:  # WHY: creation can fail on read-only or exotic mounts; fall back gracefully
            self.logger.error("Failed to create log directory %s: %s", log_dir, exc)  # WHY: surface the failure
            return data_dir, f"fallback_{safe_hostname}"  # WHY: legacy fallback path when subdir cannot be made
        return log_dir, safe_hostname  # WHY: happy-path return of the newly-ensured directory + safe hostname

    @staticmethod
    def _maybe_lock_log_dir(log_dir: str) -> None:
        """Restrict the log directory to owner rwx on platforms that support chmod."""
        if hasattr(os, "chmod"):  # WHY: os.chmod exists on Windows but is a no-op; still safe to call
            os.chmod(log_dir, _LOG_DIR_MODE)  # WHY: lock down access to per-host logs

    def _write_to_host_log(self, log_path: str, message: str) -> None:
        """Append a message to the per-host log, tolerating unicode/OS errors."""
        if not message:  # WHY: legacy contract silently ignores empty write requests
            return  # WHY: nothing to write - early exit keeps CC minimal
        try:
            _append_log_line(log_path, _sanitize_log_message(message))  # WHY: sanitize + write in one call
        except UnicodeEncodeError as exc:  # WHY: some devices emit non-UTF8 bytes we still want to record
            self._write_ascii_fallback(log_path, message, exc)  # WHY: retry with ASCII-replaced payload
        except OSError as exc:  # WHY: disk full / permissions - log and drop the line rather than crash the batch
            self.logger.error("IO error writing to host log %s: %s", log_path, exc)  # WHY: surface the error
        except Exception as exc:  # WHY: last-resort guard so a single bad line never kills the SSH batch
            self.logger.error("Unexpected error writing to host log %s: %s", log_path, exc)  # WHY: still log it

    def _write_ascii_fallback(self, log_path: str, message: str, exc: UnicodeEncodeError) -> None:
        """Retry writing after replacing bytes that could not be encoded as UTF-8."""
        self.logger.error("Unicode encoding error writing to host log %s: %s", log_path, exc)  # WHY: original err
        try:
            _append_log_line(log_path, _ascii_fallback(message))  # WHY: last-chance write with lossy conversion
        except Exception:  # WHY: swallow all errors here - we already logged the primary UnicodeEncodeError
            self.logger.error("Failed to write sanitized message to host log")  # WHY: keep legacy log wording

    # T013b: _connect moved to src.ssh.connection.connector.SshConnector. Callers within this
    # module construct SshConnector inline (a real call, not a façade) and wire the returned
    # client into the runner's ``client``/``managed_known_hosts_path`` attributes themselves.

    def _execute_command(
        self, command: str, use_shell: bool = False, hostname: str = _UNKNOWN_HOSTNAME
    ) -> tuple[bool, str, str]:
        """Execute command on remote host.

        Args:
            command: Command to execute
            use_shell: Use interactive shell instead of exec_command (better for network devices)
            hostname: Hostname for display purposes

        Returns:
            Tuple of (success, stdout, stderr)
        """
        if not self.client:  # WHY: bail out with a helpful error if no SSH session is active
            error_msg = "No active SSH connection"  # WHY: exact string checked by tests
            self.logger.error(error_msg)  # WHY: surface at ERROR since it is a caller misuse
            return False, "", error_msg  # WHY: legacy tuple shape (success, stdout, stderr)
        try:
            return self._dispatch_execution(command, use_shell, hostname)  # WHY: pure dispatch keeps CC low
        except TimeoutError:  # WHY: distinguish timeouts so callers can react differently to slow devices
            return self._timeout_result()  # WHY: build the timeout tuple in a helper for reuse/clarity
        except Exception as exc:  # WHY: catch-all so a single command never crashes the batch orchestrator
            return self._generic_error_result(exc)  # WHY: format legacy error string with exception details

    def _dispatch_execution(self, command: str, use_shell: bool, hostname: str) -> tuple[bool, str, str]:
        """Route execution to the shell or direct exec_command path."""
        self.logger.debug("Executing command: '%s' (shell_mode=%s)", command, use_shell)  # WHY: trace entry
        self.logger.debug("Command execution method: %s", "shell" if use_shell else "direct")  # WHY: which path
        command_start = time.time()  # WHY: capture start time before entering either execution mode
        if use_shell:  # WHY: shell mode is required by many network devices with fancy prompts
            return self._run_via_shell(command, command_start, hostname)  # WHY: extracted helper below
        self.logger.debug("Using direct exec_command execution")  # WHY: log which branch we picked
        return self._execute_direct(command, command_start, hostname)  # WHY: fall through to direct exec path

    def _run_via_shell(self, command: str, command_start: float, hostname: str) -> tuple[bool, str, str]:
        """Delegate to the extracted ShellExecutor for interactive-shell command execution."""
        self.logger.debug("Using shell-based execution for network device compatibility")  # WHY: log path taken
        shell_executor = ShellExecutor(  # WHY: T013b - real instance, not a façade around a helper function
            client=self.client, timeout=self.timeout, logger=self.logger
        )
        return shell_executor.execute(command, command_start, hostname)  # WHY: real call with runner instance state

    def _timeout_result(self) -> tuple[bool, str, str]:
        """Build the (success, stdout, stderr) tuple used when a command timed out."""
        error_msg = f"Command execution timeout after {self.timeout} seconds"  # WHY: keep legacy error text
        self.logger.error(error_msg)  # WHY: ERROR level matches legacy behavior asserted by test suite
        return False, "", error_msg  # WHY: legacy failure tuple shape

    def _generic_error_result(self, exc: BaseException) -> tuple[bool, str, str]:
        """Build the (success, stdout, stderr) tuple for unexpected exceptions."""
        error_msg = f"Execution error: {type(exc).__name__}: {exc}"  # WHY: legacy format includes class + message
        self.logger.exception(error_msg)  # WHY: exception() dumps traceback for post-mortem
        return False, "", error_msg  # WHY: legacy failure tuple shape

    def _execute_direct(
        self,
        command: str,
        start_time: float,
        hostname: str = _UNKNOWN_HOSTNAME,
    ) -> tuple[bool, str, str]:  # nosec B101
        """Execute command using exec_command with PTY support."""
        assert self.client is not None, "No active SSH connection"  # nosec B101  # WHY: guarded by _execute_command
        try:
            return self._exec_with_pty(command, start_time, hostname)  # WHY: try PTY first for network devices
        except Exception as pty_exc:  # WHY: many devices refuse PTY - fall back to non-PTY exec_command
            self.logger.warning("exec_command with PTY failed: %s, trying without PTY", pty_exc)  # WHY: log
            return self._exec_without_pty(command, start_time, hostname)  # WHY: fallback path

    def _exec_with_pty(self, command: str, start_time: float, hostname: str) -> tuple[bool, str, str]:
        """Run the command with get_pty=True and collect the result."""
        assert self.client is not None  # nosec B101  # WHY: caller guarantees an active client
        self.logger.debug("Attempting exec_command with get_pty=True")  # WHY: mark the branch in logs
        _, stdout, stderr = self.client.exec_command(  # WHY: paramiko returns (stdin, stdout, stderr)
            command, timeout=self.timeout, get_pty=True  # nosec B601  # WHY: caller-supplied command by design
        )
        return self._collect_and_log(stdout, stderr, start_time, hostname, with_pty=True)  # WHY: shared reader

    def _exec_without_pty(self, command: str, start_time: float, hostname: str) -> tuple[bool, str, str]:
        """Run the command without PTY - the fallback path if PTY allocation fails."""
        assert self.client is not None  # nosec B101  # WHY: caller guarantees an active client
        try:
            _, stdout, stderr = self.client.exec_command(command, timeout=self.timeout)  # nosec B601  # WHY: no-PTY
            return self._collect_and_log(stdout, stderr, start_time, hostname, with_pty=False)  # WHY: shared reader
        except Exception as exc:  # WHY: both PTY and non-PTY failed - propagate so _execute_command can format it
            self.logger.error("Both PTY and non-PTY exec_command failed: %s", exc)  # WHY: preserve legacy log line
            raise  # WHY: bubble up to _execute_command's outer catch for the legacy error string

    def _collect_and_log(
        self,
        stdout: object,
        stderr: object,
        start_time: float,
        hostname: str,
        with_pty: bool,
    ) -> tuple[bool, str, str]:
        """Read stdout/stderr and log a bounded sample of each."""
        stdout_output = stdout.read().decode("utf-8", errors="ignore")  # type: ignore[attr-defined]  # WHY: paramiko file-like
        stderr_output = stderr.read().decode("utf-8", errors="ignore")  # type: ignore[attr-defined]  # WHY: paramiko file-like
        exit_status = stdout.channel.recv_exit_status()  # type: ignore[attr-defined]  # WHY: paramiko exit code
        elapsed = time.time() - start_time  # WHY: measure wall-clock time spent on the exec
        self._log_exec_details(stdout_output, stderr_output, exit_status, elapsed, with_pty)  # WHY: bounded log
        logging.warning(  # WHY: user-visible per-host completion banner (previously print()).
            "- [%s] Command completed with exit status: %s", hostname, exit_status
        )
        return exit_status == 0, stdout_output, stderr_output  # WHY: legacy success/stdout/stderr tuple shape

    def _log_exec_details(
        self,
        stdout_output: str,
        stderr_output: str,
        exit_status: int,
        elapsed: float,
        with_pty: bool,
    ) -> None:
        """Emit debug-level completion + bounded stdout/stderr samples."""
        label = "" if with_pty else " (no PTY)"  # WHY: preserve original branch-specific wording
        self.logger.debug(  # WHY: single-line summary matching legacy format string
            "Command completed%s in %.2f seconds with exit status: %s", label, elapsed, exit_status
        )
        stdout_sample = _format_output_sample(stdout_output)  # WHY: bound + escape control chars for one-liner
        self.logger.debug(  # WHY: DEBUG-level stdout preview keeps prod logs quiet by default
            "STDOUT (%s chars): %s%s", len(stdout_output), stdout_sample, _sample_suffix(stdout_output)
        )
        if stderr_output:  # WHY: only log stderr sample when there is stderr content
            self._log_stderr_sample(stderr_output)  # WHY: separate helper keeps CC low here

    def _log_stderr_sample(self, stderr_output: str) -> None:
        """Emit a bounded warning-level sample of stderr when there is stderr content."""
        stderr_sample = _format_output_sample(stderr_output)  # WHY: escape control chars for the log line
        self.logger.warning(  # WHY: legacy behavior - stderr is WARNING even if command succeeded
            "STDERR (%s chars): %s%s", len(stderr_output), stderr_sample, _sample_suffix(stderr_output)
        )

    # T013b: _execute_with_shell moved to src.ssh.shell_execution.shell_executor.ShellExecutor.
    # Callers (_execute_command) instantiate ShellExecutor inline (real call, not facade).

    def _disconnect(self) -> None:
        """Close SSH connection."""
        if self.client:  # WHY: only close when a client is attached; no-op otherwise
            self.logger.debug("Closing SSH connection")  # WHY: trace so users can confirm clean teardown
            self.client.close()  # WHY: releases paramiko file descriptors and server-side session
            self.client = None  # WHY: reset so subsequent _execute_command calls fail fast with a clear message
            logging.warning(">> SSH connection closed")  # WHY: user-visible teardown banner (previously print()).
        else:
            self.logger.debug("No SSH connection to close")  # WHY: helpful trace during teardown of failed connect

    @staticmethod
    def _setup_logging(log_level: str = "INFO") -> logging.Logger:
        """Setup comprehensive logging configuration with syslog-style levels.

        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

        Returns:
            logging.Logger: Configured logger instance
        """
        logger = logging.getLogger(_DEFAULT_LOGGER_NAME)  # WHY: single-named logger asserted by tests
        logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))  # WHY: fall back to INFO on bad names
        for handler in list(logger.handlers):  # WHY: drop prior dedicated handlers so root config wins
            logger.removeHandler(handler)  # WHY: prevents double-output when this is called multiple times
        logger.propagate = True  # WHY: ensure messages flow up to the root logger's handlers
        EnhancedSSHRunner._emit_logging_init(logger, log_level)  # WHY: single init log line at DEBUG or INFO
        return logger  # WHY: hand back the configured logger to callers

    @staticmethod
    def _emit_logging_init(logger: logging.Logger, log_level: str) -> None:
        """Emit the one-time 'logging initialized' message at the correct level."""
        if log_level.upper() == "DEBUG":  # WHY: keep init noise at DEBUG when the user asked for DEBUG
            logger.debug(_LOG_INIT_MSG)  # WHY: legacy DEBUG-level init evidence
        else:
            logger.info(_LOG_INIT_MSG)  # WHY: legacy INFO-level init evidence for all other levels

    # T013c: _run_multiple_ssh_commands_interactive, _run_multiple_ssh_commands, _run_ssh_command_on_host,
    # and run_ssh_commands_multi_host have all been moved out of EnhancedSSHRunner into src.ssh.batch.*.
    # T013d: run_application + _interactive_mode have been moved to src.ssh.runtime.{app_runner,interactive_mode}.
    # Callers MUST use AppRunner.run(args) / InteractiveMode.run() directly (no façade indirection).

    @staticmethod
    def _create_argument_parser() -> argparse.ArgumentParser:
        """Create and configure the argument parser."""
        parser = argparse.ArgumentParser(  # WHY: single parser holds every CLI option for ssh_runner_v2
            description="Enhanced SSH Command Runner v2 - Execute commands on remote hosts via SSH",  # WHY: legacy
            formatter_class=argparse.RawDescriptionHelpFormatter,  # WHY: preserve literal newlines in epilog
            epilog=_ARGPARSE_EPILOG,  # WHY: multi-line help text lives at module scope for reuse
        )
        EnhancedSSHRunner._add_mode_args(parser)  # WHY: --interactive, --no-env
        EnhancedSSHRunner._add_positional_args(parser)  # WHY: hostname/username/password/command positionals
        EnhancedSSHRunner._add_connection_args(parser)  # WHY: --port, --timeout, --secure
        EnhancedSSHRunner._add_shell_args(parser)  # WHY: --shell, --no-shell
        EnhancedSSHRunner._add_logging_args(parser)  # WHY: --log-level, --debug, --max-threads
        return parser  # WHY: return the fully-configured parser to callers/tests

    @staticmethod
    def _add_mode_args(parser: argparse.ArgumentParser) -> None:
        """Add mode-selection flags to the parser."""
        parser.add_argument("--interactive", "-i", action="store_true", help="Run in interactive mode")  # WHY: REPL
        parser.add_argument(  # WHY: allow users to bypass .env loading when they want fully-explicit CLI args
            "--no-env", action="store_true", help="Disable automatic .env file loading (use manual credentials)"
        )

    @staticmethod
    def _add_positional_args(parser: argparse.ArgumentParser) -> None:
        """Add the four optional positional args that override .env values."""
        parser.add_argument("hostname", nargs="?", help="Hostname or IP address (overrides SSH_HOST)")  # WHY: CLI arg
        parser.add_argument("username", nargs="?", help="SSH username (overrides SSH_USER)")  # WHY: CLI override
        parser.add_argument("password", nargs="?", help="SSH password (overrides SSH_PASSWORD)")  # WHY: CLI override
        parser.add_argument("command", nargs="?", help="Command to execute (overrides SSH_COMMANDS)")  # WHY: CLI arg

    @staticmethod
    def _add_connection_args(parser: argparse.ArgumentParser) -> None:
        """Add connection-related options with validators."""
        parser.add_argument(  # WHY: --port validated via module-level _validate_port_arg (kept out of nested defs)
            "--port", "-p", type=_validate_port_arg, default=_DEFAULT_PORT, help="SSH port (default: 22)"
        )
        parser.add_argument(  # WHY: --timeout validated via module-level _validate_timeout_arg helper
            "--timeout",
            "-t",
            type=_validate_timeout_arg,
            default=_DEFAULT_TIMEOUT_SEC,
            help="Connection timeout in seconds (default: 30)",
        )
        parser.add_argument(  # WHY: --secure enables getpass so passwords never appear in shell history
            "--secure", "-s", action="store_true", help="Prompt for password securely instead of command line"
        )

    @staticmethod
    def _add_shell_args(parser: argparse.ArgumentParser) -> None:
        """Add shell-mode flags to the parser."""
        parser.add_argument(  # WHY: interactive shell mode is the default because it works for network devices
            "--shell",
            action="store_true",
            default=True,
            help="Use interactive shell mode (default, recommended for network devices)",
        )
        parser.add_argument(  # WHY: give users an escape hatch back to exec_command when they need it
            "--no-shell", action="store_true", help="Disable shell mode and use exec_command instead"
        )

    @staticmethod
    def _add_logging_args(parser: argparse.ArgumentParser) -> None:
        """Add logging and thread-count flags to the parser."""
        parser.add_argument(  # WHY: --log-level supports the four syslog-style levels the runner emits
            "--log-level",
            choices=["DEBUG", "INFO", "WARNING", "ERROR"],
            default="INFO",
            help="Set logging level (default: INFO)",
        )
        parser.add_argument(  # WHY: --debug is the ergonomic shortcut for --log-level DEBUG
            "--debug", "-d", action="store_true", help="Enable debug logging (equivalent to --log-level DEBUG)"
        )
        parser.add_argument(  # WHY: --max-threads validated by module-level _validate_threads_arg helper
            "--max-threads",
            type=_validate_threads_arg,
            default=None,
            help=f"Maximum threads for multi-host execution (default: {multiprocessing.cpu_count()} cores)",
        )
