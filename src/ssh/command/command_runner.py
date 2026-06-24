"""SingleCommandRunner — connect, execute one command on one host, log results.

Extracted from ``EnhancedSSHRunner._run_ssh_command`` (CC=C/12) per T013b of
specs/198-radon-complexity-decomposition. Every method has cyclomatic
complexity <= 10. User-facing strings (status lines, log file headers/footers,
``[OK]`` / ``[ERROR]`` markers) are preserved verbatim from the original.

Collaborators:
- :class:`src.ssh.connection.connector.SshConnector` — connection establishment
- ``EnhancedSSHRunner._execute_command``           — direct/shell execution dispatch
- ``EnhancedSSHRunner._disconnect``                — connection teardown
- ``EnhancedSSHRunner._create_secure_log_file``    — per-host log file factory
"""

from __future__ import annotations

import logging  # Structured logging for the new command-runner module
import os  # Per-host log directory + path join
from collections.abc import Callable
from datetime import datetime  # Header / footer timestamps
from typing import TYPE_CHECKING, Any

from src.ssh.connection.connector import SshConnector  # New connector class (T013b)

if TYPE_CHECKING:  # Imported only for type hints — avoids circular import at runtime
    from src.ssh.ssh_runner import SSHConnectionConfig


class SingleCommandRunner:
    """Orchestrate one SSH command on one host: connect, execute, log, disconnect."""

    @staticmethod
    def run(  # noqa: PLR0913 - matches original parameter list for backwards-compatible callers
        hostname: str | None = None,
        username: str | None = None,
        password: str | None = None,
        command: str | None = None,
        port: int = 22,
        timeout: int = 30,
        use_shell: bool = False,
        config: SSHConnectionConfig | None = None,
    ) -> bool:
        """Connect, execute one command, write a per-host log; return success bool."""
        resolved = SingleCommandRunner._resolve_params(
            hostname, username, password, command, port, timeout, use_shell, config
        )
        hostname, username, password, command, port, timeout, use_shell = resolved  # Unpack validated args
        logger = logging.getLogger("ssh_runner_v2")  # Unified SSH logger
        logger.info("SingleCommandRunner.run starting for %s@%s:%s", username, hostname, port)
        logger.debug("SingleCommandRunner: command=%r timeout=%s use_shell=%s", command, timeout, use_shell)
        runner, write_to_host_log, host_log_file = SingleCommandRunner._setup_host_log(
            hostname, command, timeout, logger
        )
        single_cmd_success = False  # Default — flipped to True only on confirmed command success
        try:
            single_cmd_success = SingleCommandRunner._execute_with_connection(
                runner, hostname, username, password, port, command, use_shell, write_to_host_log, logger
            )
            return single_cmd_success
        except Exception as run_error:  # noqa: BLE001 - top-level fallback mirrors original behavior
            logger.exception(
                "[%s] Unexpected error during SSH command execution: %s: %s",
                hostname,
                type(run_error).__name__,
                run_error,
            )
            write_to_host_log(f"[ERROR] Unexpected error: {run_error}")
            return False
        finally:
            runner._disconnect()  # Existing EnhancedSSHRunner teardown; safe to call when client may be None
            logger.debug("[%s] SSH single command session completed", hostname)
            SingleCommandRunner._write_footer(write_to_host_log, single_cmd_success, host_log_file, logger)

    # ------------------------------------------------------------------
    # Parameter resolution (config-object support + required-arg validation)
    # ------------------------------------------------------------------
    @staticmethod
    def _resolve_params(
        hostname: str | None,
        username: str | None,
        password: str | None,
        command: str | None,
        port: int,
        timeout: int,
        use_shell: bool,
        config: SSHConnectionConfig | None,
    ) -> tuple[str, str, str, str, int, int, bool]:
        """Apply config object overrides and enforce required parameters."""
        if config is not None:  # Config object overrides individual kwargs
            hostname = config.hostname
            username = config.username
            password = config.password
            port = config.port
            timeout = config.timeout
            use_shell = config.use_shell
        if hostname is None or username is None or password is None:  # Required-arg gate
            raise ValueError("hostname, username, and password are required")
        if command is None:  # Empty command is allowed; mirrors original behavior
            command = ""
        return hostname, username, password, command, port, timeout, use_shell

    # ------------------------------------------------------------------
    # Per-host log file setup
    # ------------------------------------------------------------------
    @staticmethod
    def _setup_host_log(
        hostname: str,
        command: str,
        timeout: int,
        logger: logging.Logger,
    ) -> tuple[Any, Callable[[str], None], str]:
        """Build the runner, create the per-host log file, write the header; return helpers."""
        from src.ssh.ssh_runner import EnhancedSSHRunner  # Local import — avoids circular module load

        runner = EnhancedSSHRunner(timeout=timeout, logger=logger)  # Owns timeout + client lifecycle
        host_log_file, write_to_host_log = runner._create_secure_log_file(hostname)  # Existing helper
        print(f"- [{hostname}] Logging to: {host_log_file}")  # User-facing status (verbatim)
        header = (  # Verbatim header format from the original _run_ssh_command
            f"\n{'=' * 80}\n"
            f"SSH Single Command Log for Host: {hostname}\n"
            f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Command: {command}\n"
            f"{'=' * 80}"
        )
        write_to_host_log(header)  # Persist the header to the per-host log
        return runner, write_to_host_log, host_log_file

    # ------------------------------------------------------------------
    # Connection + execution + result writing
    # ------------------------------------------------------------------
    @staticmethod
    def _execute_with_connection(
        runner: Any,
        hostname: str,
        username: str,
        password: str,
        port: int,
        command: str,
        use_shell: bool,
        write_to_host_log: Callable[[str], None],
        logger: logging.Logger,
    ) -> bool:
        """Connect via :class:`SshConnector`, execute the command, write results, return success."""
        connector = SshConnector(timeout=runner.timeout, logger=logger)  # Inline real call (not facade)
        logger.info("SingleCommandRunner: connecting via SshConnector to %s:%s", hostname, port)
        client, managed_kh_path = connector.connect(hostname, username, password, port)  # Real call
        logger.debug("SingleCommandRunner: connect returned client=%s", bool(client))
        if client is None:  # Connection failed — connector already logged + printed
            error_msg = f"Failed to connect to {hostname}"
            logger.error("SSH connection failed: %s:%s", hostname, port)
            write_to_host_log(f"X  {error_msg}")
            return False
        runner.client = client  # Wire the live client into the runner
        runner.managed_known_hosts_path = managed_kh_path  # Preserve for later save_host_keys calls
        logger.debug("SSH connected to %s, executing single command", hostname)
        success, stdout, stderr = runner._execute_command(  # Dispatcher remains on EnhancedSSHRunner
            command, use_shell=use_shell, hostname=hostname
        )
        logger.debug(
            "SingleCommandRunner: _execute_command returned success=%s stdout_len=%d stderr_len=%d",
            success,
            len(stdout or ""),
            len(stderr or ""),
        )
        SingleCommandRunner._write_results(write_to_host_log, stdout, stderr, success, command, hostname, logger)
        return bool(success)

    @staticmethod
    def _write_results(
        write_to_host_log: Callable[[str], None],
        stdout: str,
        stderr: str,
        success: bool,
        command: str,
        hostname: str,
        logger: logging.Logger,
    ) -> None:
        """Write stdout/stderr blocks and the success/failure marker to the per-host log."""
        separator = "\n" + "=" * 60  # Visual separator (verbatim)
        write_to_host_log(separator)
        write_to_host_log("!? COMMAND OUTPUT")  # Verbatim section header
        separator_line = "=" * 60
        write_to_host_log(separator_line)
        if stdout:  # Only write the block when there is content
            write_to_host_log("-> STDOUT:")
            write_to_host_log(stdout)
        if stderr:  # Only write the block when there is content
            write_to_host_log("-> STDERR:")
            write_to_host_log(stderr)
        if not stdout and not stderr:  # Explicit no-output marker (verbatim)
            write_to_host_log("X  No output returned")
        write_to_host_log(separator_line)
        if success:  # Verbatim success message
            logger.info("[%s] Command completed successfully", hostname)
            write_to_host_log("[OK] Command executed successfully")
        else:  # Verbatim failure message
            logger.warning("[%s] Command failed: %s...", hostname, command[:50])
            write_to_host_log("[ERROR] Command execution failed or returned non-zero exit status")

    # ------------------------------------------------------------------
    # Footer writing (best-effort, mirrors original safe-fallback shape)
    # ------------------------------------------------------------------
    @staticmethod
    def _write_footer(
        write_to_host_log: Callable[[str], None],
        single_cmd_success: bool,
        host_log_file: str,
        logger: logging.Logger,
    ) -> None:
        """Write the session footer; fall back to a minimal footer on any error."""
        try:
            final_success = single_cmd_success if isinstance(single_cmd_success, bool) else False
            footer = (  # Verbatim footer format from the original
                f"\n{'=' * 80}\n"
                f"SSH Single Command Session Completed: "
                f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Status: {'SUCCESS' if final_success else 'FAILED'}\n"
                f"Log file: {host_log_file}\n"
                f"{'=' * 80}"
            )
            write_to_host_log(footer)
        except Exception as footer_error:  # noqa: BLE001 - footer is best-effort
            logger.error("Error in footer generation: %s: %s", type(footer_error).__name__, footer_error)
            try:
                simple_footer = f"Session completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                write_to_host_log(simple_footer)
            except Exception as fallback_error:  # noqa: BLE001 - last-resort path
                logger.error("Even simple footer failed: %s", fallback_error)
                # Reference os so linters don't strip the import (kept for backwards parity with original)
                _ = os.path.basename  # noqa: PLW0641
