"""InteractiveBatchExecutor — interactive multi-step SSH session (T013c).

Extracted from ``EnhancedSSHRunner._run_multiple_ssh_commands_interactive`` (CC=F, ~42)
per T013c of specs/198-radon-complexity-decomposition. Every method has cyclomatic
complexity <= 10. User-facing strings (status lines, log file headers/footers,
[STEP], [OK], [ERROR], [INTERRUPT] markers) are preserved verbatim from the original.

The interactive flow drives a persistent paramiko shell channel to support sequences
that require interactive input (e.g. ``su`` → ``Password:`` → response → ``show ...``).
"""

from __future__ import annotations

import logging  # Structured logging for the new interactive executor
import os  # chmod for secure log permissions
import re  # ANSI escape + control-sequence cleanup
import time  # Inter-command pacing + response-wait windows
from collections.abc import Callable
from datetime import datetime  # Per-host log timestamps + headers/footers
from typing import TYPE_CHECKING, Any

from src.ssh.connection.connector import SshConnector  # Real connection collaborator (no façade)

if TYPE_CHECKING:  # Imported only for type hints — avoids circular import at runtime
    from src.ssh.ssh_runner import SSHConnectionConfig, SSHExecutionConfig


# Constants — preserve original wait window magic numbers
_MAX_WAIT_SECONDS = 10  # Maximum total wait for a step response (verbatim)
_WAIT_INCREMENT = 0.1  # Polling interval inside the response wait loop (verbatim)
_NO_DATA_TIMEOUT = 3.0  # Bail-out when no new data for this many seconds (verbatim)
_PASSWORD_HINTS = ("password", "pass", "pwd")  # Lower-cased substrings used for redaction
_PASSWORD_PROMPTS = ("password:", "password ", "passwd:")  # Lower-cased prompt suffixes
_PROMPT_PATTERNS = ("$", "#", ">", "pcli")  # Recognized shell prompt suffixes
_FAILURE_PATTERNS = (  # Lower-cased response substrings that indicate failure
    ("command not found", "command not found"),
    ("permission denied", "permission denied"),
    ("authentication failed", "authentication failed"),
)


class InteractiveBatchExecutor:
    """Drive a persistent shell channel through a scripted command/response sequence."""

    @staticmethod
    def run(  # noqa: PLR0913 - mirrors the original interactive entrypoint signature
        hostname: str | None = None,
        username: str | None = None,
        password: str | None = None,
        commands: list[str] | None = None,
        port: int = 22,
        timeout: int = 30,
        use_shell: bool = True,
        config: SSHConnectionConfig | None = None,
        exec_config: SSHExecutionConfig | None = None,
    ) -> bool:
        """Connect, open shell, walk command/response steps; return overall success bool."""
        resolved = InteractiveBatchExecutor._resolve_params(  # Apply config-object overrides + required-arg validation
            hostname, username, password, commands, port, timeout, use_shell, config, exec_config
        )
        hostname, username, password, commands, port, timeout, use_shell = resolved  # Unpack
        logger = logging.getLogger("ssh_runner_v2")  # Unified SSH logger
        logger.info(
            "InteractiveBatchExecutor.run starting for %s@%s:%s (%d steps)",
            username,
            hostname,
            port,
            len(commands),
        )
        logger.debug("InteractiveBatchExecutor: steps=%r use_shell=%s timeout=%s", commands, use_shell, timeout)
        runner, raw_write_to_host_log, host_log_file = InteractiveBatchExecutor._setup_host_log(
            hostname, commands, timeout, logger
        )
        # Build a credential-scrubbing wrapper here, where 'password' is already
        # in scope. The inner writer never receives 'password' as a parameter,
        # so the smallest possible scope holds the credential reference.
        write_to_host_log: Callable[[str], None] = InteractiveBatchExecutor._build_scrubbing_writer(
            raw_write_to_host_log, password
        )
        overall_success = True  # Track failures across all steps
        try:
            overall_success = InteractiveBatchExecutor._execute_session(  # Real connect + shell loop
                runner, hostname, username, password, port, commands, timeout, use_shell, write_to_host_log, logger
            )
            return overall_success
        except Exception as session_error:  # noqa: BLE001 - top-level fallback mirrors original behavior
            logger.exception(
                "[%s] Unexpected error during interactive session: %s: %s",
                hostname,
                type(session_error).__name__,
                session_error,
            )
            write_to_host_log(f"[ERROR] Unexpected error: {session_error}")  # Verbatim error log line
            overall_success = False
            return False
        finally:
            runner._disconnect()  # Existing EnhancedSSHRunner teardown; safe when client may be None
            logger.debug("[%s] SSH interactive session completed", hostname)
            InteractiveBatchExecutor._write_footer(write_to_host_log, overall_success, host_log_file, logger)

    # ------------------------------------------------------------------
    # Parameter resolution
    # ------------------------------------------------------------------
    @staticmethod
    def _resolve_params(  # noqa: PLR0913 - matches original kwargs surface
        hostname: str | None,
        username: str | None,
        password: str | None,
        commands: list[str] | None,
        port: int,
        timeout: int,
        use_shell: bool,
        config: SSHConnectionConfig | None,
        exec_config: SSHExecutionConfig | None,
    ) -> tuple[str, str, str, list[str], int, int, bool]:
        """Apply config-object overrides and enforce required parameters."""
        if config is not None:  # Connection-config object overrides individual kwargs
            hostname = config.hostname
            username = config.username
            password = config.password
            port = config.port
            timeout = config.timeout
            use_shell = config.use_shell
        if exec_config is not None:  # Execution-config object overrides commands + shell flag
            commands = exec_config.commands
            use_shell = exec_config.use_shell
        if hostname is None or username is None or password is None:  # Required-arg gate
            raise ValueError("hostname, username, and password are required")
        if commands is None:  # Empty step list is acceptable; mirrors original behavior
            commands = []
        return hostname, username, password, commands, port, timeout, use_shell

    # ------------------------------------------------------------------
    # Per-host log setup (ANSI-cleaning writer)
    # ------------------------------------------------------------------
    @staticmethod
    def _setup_host_log(
        hostname: str,
        commands: list[str],
        timeout: int,
        logger: logging.Logger,
    ) -> tuple[Any, Callable[[str], None], str]:
        """Build the runner, create the ANSI-cleaning per-host log writer, write header."""
        from src.ssh.ssh_runner import EnhancedSSHRunner  # Local import — avoids circular module load

        runner = EnhancedSSHRunner(timeout=timeout, logger=logger)  # Owns timeout + client lifecycle
        host_log_file = InteractiveBatchExecutor._build_log_path(hostname, logger)  # Sanitized per-host path
        print(f"** [{hostname}] Logging to: {host_log_file}")  # Verbatim console status line
        write_to_host_log = InteractiveBatchExecutor._make_log_writer(host_log_file, logger)  # ANSI cleaner
        num_commands = len(commands) if commands else 0  # Header counter
        header = (  # Verbatim header format from the original interactive entrypoint
            f"\n{'=' * 80}\n"
            f"SSH Interactive Session Log for Host: {hostname}\n"
            f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Commands/responses to execute: {num_commands}\n"
            f"{'=' * 80}"
        )
        write_to_host_log(header)  # Persist the header to the per-host log
        return runner, write_to_host_log, host_log_file

    @staticmethod
    def _build_log_path(hostname: str, logger: logging.Logger) -> str:
        """Construct the sanitized per-host log file path; fall back to data/ on chmod errors."""
        from src.ssh.ssh_runner import EnhancedSSHRunner  # Local import — avoids circular module load

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # Verbatim filename timestamp format
        safe_hostname = EnhancedSSHRunner.sanitize_filename(hostname)  # Filesystem-safe variant of hostname
        data_dir = EnhancedSSHRunner._get_data_directory()  # Resolved workspace data directory
        log_dir = os.path.join(data_dir, "per-host-logs")  # Conventional subdirectory for per-host logs
        try:
            os.makedirs(log_dir, exist_ok=True)  # Create the subdirectory if missing
            if hasattr(os, "chmod"):  # Best-effort owner-only permission on POSIX
                os.chmod(log_dir, 0o700)
        except OSError as mkdir_error:  # Fallback to data_dir when subdirectory creation fails
            logger.error("Failed to create log directory %s: %s", log_dir, mkdir_error)
            log_dir = data_dir
            safe_hostname = f"fallback_{safe_hostname}"
        return os.path.join(log_dir, f"ssh_output_{safe_hostname}_{timestamp}.log")

    @staticmethod
    def _build_scrubbing_writer(inner_writer: Callable[[str], None], password: str | None) -> Callable[[str], None]:
        """Wrap *inner_writer* so each message has *password* replaced with ``***REDACTED***``.

        Returning a new callable keeps the password reference confined to this
        helper's closure; the inner writer never receives the credential value
        as a parameter, satisfying the minimum-scope rule for sensitive data.
        """
        if not password:  # No credential to scrub — callers get the raw writer
            return inner_writer

        def scrubbing_writer(message: str) -> None:  # noqa: D401
            """Inner closure: scrub then forward each message to the disk writer."""
            inner_writer(message.replace(password, "***REDACTED***"))

        return scrubbing_writer

    @staticmethod
    def _make_log_writer(host_log_file: str, logger: logging.Logger) -> Callable[[str], None]:
        """Return a closure that strips ANSI/control sequences before writing each line.

        Credential scrubbing happens in the caller's wrapper closure, NOT here,
        so this writer never holds a reference to any password value.
        """
        ansi_escape = re.compile(r"\x1b\[[0-9;]*[mGKHfABCDsuJ]")  # ANSI color + cursor sequences (verbatim)
        control_sequences = [  # Additional terminal-control sequences cleaned for readability (verbatim)
            r"\x1b\[\?[0-9]+[lh]",
            r"\x1b\[[0-9]+[ABCDGK]",
            r"\x1b\[[0-9]+;[0-9]+[Hf]",
            r"\x1b\[[0-9]*[J]",
            r"\x1b\[6n",
            r"\x1b\[[0-9]+D",
            r"\x1b\[\?2004[hl]",
            r"\x1b\[\?25[lh]",
            r"\x1b\[\?7[lh]",
            r"\x1b\[\?12[lh]",
        ]

        def write_to_host_log(message: str) -> None:  # Closure shared by all callers in this session
            if not message:  # Skip empty writes (parity with original)
                return
            try:
                clean = ansi_escape.sub("", message)  # Strip color + cursor sequences
                for pattern in control_sequences:  # Strip remaining mode + cursor sequences
                    clean = re.sub(pattern, "", clean)
                clean = re.sub(r"\n\s*\n\s*\n", "\n\n", clean)  # Collapse 3+ blank lines to 2 (verbatim)
                clean = re.sub(r"[ \t]+\n", "\n", clean)  # Trim trailing horizontal whitespace
                safe_message = clean.replace("\x00", "").replace("\r\n", "\n")  # Prevent log injection
                with open(host_log_file, "a", encoding="utf-8") as log_file:
                    # lgtm[py/clear-text-storage-sensitive-data] — messages are pre-scrubbed by
                    # _build_scrubbing_writer in _run_host_session; CodeQL cannot model str.replace as
                    # a sanitizer. The redaction is locked by unit tests in tests/unit/ssh/batch/.
                    log_file.write(f"{safe_message}\n")
                    log_file.flush()
                if hasattr(os, "chmod"):  # Owner-only permission on POSIX
                    os.chmod(host_log_file, 0o600)
            except UnicodeEncodeError:  # ASCII fallback path mirrors original behavior
                InteractiveBatchExecutor._write_ascii_fallback(message, host_log_file, logger)
            except Exception as write_error:  # noqa: BLE001 - last-resort path (verbatim)
                logger.error("Unexpected error writing to host log %s: %s", host_log_file, write_error)

        return write_to_host_log

    @staticmethod
    def _write_ascii_fallback(message: str, host_log_file: str, logger: logging.Logger) -> None:
        """ASCII-only fallback used when UTF-8 encoding fails."""
        try:
            safe_message = message.encode("ascii", errors="replace").decode("ascii")
            with open(host_log_file, "a", encoding="utf-8") as log_file:
                # lgtm[py/clear-text-storage-sensitive-data] — messages are pre-scrubbed by
                # _build_scrubbing_writer in _run_host_session; CodeQL cannot model str.replace as
                # a sanitizer. The redaction is locked by unit tests in tests/unit/ssh/batch/.
                log_file.write(f"{safe_message}\n")
                log_file.flush()
        except Exception:  # noqa: BLE001 - last-resort path (verbatim)
            logger.error("Failed to write sanitized message to host log")

    # ------------------------------------------------------------------
    # Session orchestration (connect → open shell → step loop → cleanup)
    # ------------------------------------------------------------------
    @staticmethod
    def _execute_session(  # noqa: PLR0913 - orchestrator needs all session inputs
        runner: Any,
        hostname: str,
        username: str,
        password: str,
        port: int,
        commands: list[str],
        timeout: int,
        use_shell: bool,
        write_to_host_log: Callable[[str], None],
        logger: logging.Logger,
    ) -> bool:
        """Open SSH connection + shell, run all steps, write final status; return success bool."""
        shell = InteractiveBatchExecutor._connect_and_open_shell(
            runner, hostname, username, password, port, timeout, use_shell, write_to_host_log, logger
        )
        if shell is None:  # Connection or shell setup failed; failure already logged
            return False
        write_to_host_log(f"\n>> Starting interactive session with {len(commands)} steps...")  # Verbatim status line
        overall_success = InteractiveBatchExecutor._iterate_steps(shell, hostname, commands, write_to_host_log, logger)
        InteractiveBatchExecutor._cleanup_shell(shell, hostname, logger)
        InteractiveBatchExecutor._write_final_status(
            write_to_host_log, overall_success, hostname, len(commands), logger
        )
        return overall_success

    @staticmethod
    def _connect_and_open_shell(  # noqa: PLR0913 - shell setup needs full session inputs
        runner: Any,
        hostname: str,
        username: str,
        password: str,
        port: int,
        timeout: int,
        use_shell: bool,
        write_to_host_log: Callable[[str], None],
        logger: logging.Logger,
    ) -> Any | None:
        """Connect via SshConnector, open a persistent shell channel, capture initial prompt."""
        logger.info("Connecting via SshConnector for interactive session to %s:%s", hostname, port)
        connector = SshConnector(timeout=runner.timeout, logger=logger)  # Inline real call (not façade)
        client, kh_path = connector.connect(hostname, username, password, port)  # Real connect
        logger.debug("Interactive connect returned client=%s", bool(client))
        if client is None:  # Connection failed; connector logged + printed already
            error_msg = f"Failed to connect to {hostname}"
            logger.error("SSH connection failed: %s:%s", hostname, port)
            write_to_host_log(f"[ERROR] {error_msg}")  # Verbatim error log line
            return None
        runner.client = client  # Wire the live client into the runner instance
        runner.managed_known_hosts_path = kh_path  # Preserve TOFU path for later save calls
        logger.debug("SSH connected to %s, starting interactive session", hostname)
        if not use_shell:  # Interactive mode requires a real shell; warn + flip (verbatim behavior)
            logger.warning("Interactive mode requires shell=True, enabling shell mode")
            use_shell = True
        shell = client.invoke_shell(term="vt100", width=120, height=24)  # Persistent shell channel
        shell.settimeout(timeout)  # Apply session timeout to the shell channel
        time.sleep(1)  # Allow the initial prompt to arrive (verbatim)
        if shell.recv_ready():  # Capture the initial prompt for the per-host log
            initial_output = shell.recv(4096).decode("utf-8", errors="ignore")
            write_to_host_log(f"[OUTPUT] INITIAL PROMPT:\n{initial_output}")
            logger.debug("Initial shell prompt received")
        return shell

    @staticmethod
    def _iterate_steps(
        shell: Any,
        hostname: str,
        commands: list[str],
        write_to_host_log: Callable[[str], None],
        logger: logging.Logger,
    ) -> bool:
        """Walk the step list; return overall success bool. Each step is one helper call."""
        overall_success = True  # Flip to False on any failed step or interrupt
        command_index = 0  # Manual index because empty steps are skipped without advancing total
        while command_index < len(commands):
            current_item = commands[command_index].strip()
            if not current_item:  # Skip blank entries (verbatim)
                command_index += 1
                continue
            step_num = command_index + 1
            try:
                step_ok = InteractiveBatchExecutor._run_one_step(
                    shell, hostname, current_item, step_num, len(commands), write_to_host_log, logger
                )
                if not step_ok:
                    overall_success = False
                command_index += 1
                if command_index < len(commands):  # Stability pause between steps (verbatim)
                    time.sleep(0.5)
            except KeyboardInterrupt:  # Ctrl+C halts the remaining steps (verbatim UX)
                print(f"\n[INTERRUPT] [{hostname}] Ctrl+C detected! Stopping interactive session...")
                logger.warning("Interactive session interrupted by user at step %d", step_num)
                write_to_host_log(f"\n[INTERRUPT] Session interrupted by user at step {step_num}")
                overall_success = False
                break
            except Exception as step_error:  # noqa: BLE001 - per-step fallback mirrors original
                logger.error("[%s] Error at step %d: %s: %s", hostname, step_num, type(step_error).__name__, step_error)
                write_to_host_log(f"[ERROR] Step {step_num} error: {step_error}")
                overall_success = False
                break
        return overall_success

    @staticmethod
    def _run_one_step(  # noqa: PLR0913 - per-step helper needs full step context
        shell: Any,
        hostname: str,
        current_item: str,
        step_num: int,
        total: int,
        write_to_host_log: Callable[[str], None],
        logger: logging.Logger,
    ) -> bool:
        """Send one command/response, capture reply, log block; return step success bool."""
        write_to_host_log(f"\n{'=' * 60}")  # Step separator (verbatim)
        write_to_host_log(f"[STEP] Step {step_num}/{total}: {current_item}")  # Step header (verbatim)
        write_to_host_log("=" * 60)
        display_item = InteractiveBatchExecutor._redact_for_display(current_item)  # Redact password-like items
        print(f"* [{hostname}] Executing step {step_num}: {display_item}")  # Verbatim console status
        logger.debug("[%s] Sending: %s", hostname, current_item)
        shell.send((current_item + "\n").encode("utf-8"))  # Send the command/response line
        time.sleep(0.2)  # Brief pause to let the device register the input (verbatim)
        response_output = InteractiveBatchExecutor._wait_for_response(shell, hostname, logger)
        if response_output.strip():  # Log response block only when non-empty (verbatim)
            write_to_host_log("[OUTPUT] RESPONSE:")
            write_to_host_log(response_output)
            logger.debug("[%s] Response received: %d chars", hostname, len(response_output))
        else:
            write_to_host_log("[STATUS] No response output")
            logger.debug("[%s] No response output received", hostname)
        step_success = InteractiveBatchExecutor._check_step_success(response_output, hostname, step_num, logger)
        if step_success:
            write_to_host_log(f"[OK] Step {step_num} completed successfully")
            logger.debug("[%s] Step %d completed successfully", hostname, step_num)
        else:
            write_to_host_log(f"[ERROR] Step {step_num} failed")
        return step_success

    @staticmethod
    def _redact_for_display(current_item: str) -> str:
        """Return ``current_item`` masked when it looks like a password value."""
        if any(hint in current_item.lower() for hint in _PASSWORD_HINTS) and len(current_item) > 5:
            return "*" * len(current_item)  # Mask password-like items in console output (verbatim)
        return current_item

    @staticmethod
    def _wait_for_response(shell: Any, hostname: str, logger: logging.Logger) -> str:
        """Drain the shell until a prompt appears or no data arrives for the timeout window."""
        response_output = ""  # Accumulated bytes from the shell channel
        last_data_time = time.time()  # Reset whenever new data arrives
        total_wait = 0.0  # Cumulative polling time (capped by _MAX_WAIT_SECONDS)
        while total_wait < _MAX_WAIT_SECONDS:
            if shell.recv_ready():  # New data available
                chunk = shell.recv(4096).decode("utf-8", errors="ignore")
                response_output += chunk
                last_data_time = time.time()
                if any(prompt in response_output.lower() for prompt in _PASSWORD_PROMPTS):
                    logger.debug("[%s] Password prompt detected", hostname)
                    break  # Stop waiting — caller will send the next step (the password response)
                if any(pattern in response_output[-50:] for pattern in _PROMPT_PATTERNS):
                    if (time.time() - last_data_time) > 1.0:  # Quiet period after a prompt-looking suffix
                        break
            elif (time.time() - last_data_time) >= _NO_DATA_TIMEOUT:  # No new data for the bail-out window
                break
            time.sleep(_WAIT_INCREMENT)
            total_wait += _WAIT_INCREMENT
        return response_output

    @staticmethod
    def _check_step_success(
        response_output: str,
        hostname: str,
        step_num: int,
        logger: logging.Logger,
    ) -> bool:
        """Return False when the response contains a known failure indicator."""
        lowered = response_output.lower()
        for needle, label in _FAILURE_PATTERNS:  # Iterate canonical failure substrings
            if needle in lowered:
                logger.warning("[%s] Step %d failed: %s", hostname, step_num, label)
                return False
        return True

    # ------------------------------------------------------------------
    # Cleanup + final status + footer
    # ------------------------------------------------------------------
    @staticmethod
    def _cleanup_shell(shell: Any, hostname: str, logger: logging.Logger) -> None:
        """Best-effort graceful close of the shell channel (verbatim behavior)."""
        try:
            shell.send(b"exit\n")  # Send a clean exit (mirrors interactive terminal behavior)
            time.sleep(0.5)  # Give the device a moment to process the exit
            shell.close()
            logger.debug("[%s] Interactive shell closed gracefully", hostname)
        except Exception as cleanup_error:  # noqa: BLE001 - cleanup is best-effort
            logger.debug("[%s] Shell cleanup warning: %s", hostname, cleanup_error)

    @staticmethod
    def _write_final_status(
        write_to_host_log: Callable[[str], None],
        overall_success: bool,
        hostname: str,
        total: int,
        logger: logging.Logger,
    ) -> None:
        """Write the final-status block to the per-host log (verbatim text)."""
        if overall_success:
            logger.info("[%s] All %d interactive steps completed successfully", hostname, total)
            write_to_host_log("[OK] All interactive steps completed successfully")
        else:
            logger.warning("[%s] Some interactive steps failed", hostname)
            write_to_host_log("[WARNING] Some interactive steps failed - check output above")

    @staticmethod
    def _write_footer(
        write_to_host_log: Callable[[str], None],
        overall_success: bool,
        host_log_file: str,
        logger: logging.Logger,
    ) -> None:
        """Write the session footer; fall back to a minimal footer on any error."""
        try:
            final_success = overall_success if isinstance(overall_success, bool) else False
            footer = (  # Verbatim footer format from the original
                f"\n{'=' * 80}\n"
                f"SSH Interactive Session Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Status: {'SUCCESS' if final_success else 'FAILED'}\n"
                f"Log file: {host_log_file}\n"
                f"{'=' * 80}"
            )
            write_to_host_log(footer)
        except Exception as footer_error:  # noqa: BLE001 - footer is best-effort
            logger.error(
                "Error in interactive session footer generation: %s: %s",
                type(footer_error).__name__,
                footer_error,
            )
            try:
                simple_footer = f"Session completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                write_to_host_log(simple_footer)
            except Exception as fallback_error:  # noqa: BLE001 - last-resort path
                logger.error("Even simple interactive footer failed: %s", fallback_error)
