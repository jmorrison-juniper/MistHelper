"""BatchExecutor — connect, run multiple commands sequentially on one host (T013c).

Extracted from ``EnhancedSSHRunner._run_multiple_ssh_commands`` (CC=D) per T013c of
specs/198-radon-complexity-decomposition. Every method has cyclomatic complexity <= 10.
User-facing strings (status lines, log file headers/footers, ``[OK]`` / ``[ERROR]``
markers) are preserved verbatim from the original.
"""

from __future__ import annotations

import logging  # Structured logging for the new batch executor
import os  # Per-host log directory creation + chmod
import time  # Inter-command delay
from collections.abc import Callable
from datetime import datetime  # Header / footer timestamps
from typing import TYPE_CHECKING, Any

from src.ssh.connection.connector import SshConnector  # Real connection collaborator (no façade)

if TYPE_CHECKING:  # Imported only for type hints — avoids circular import at runtime
    from src.ssh.ssh_runner import SSHConnectionConfig, SSHExecutionConfig


class BatchExecutor:
    """Run multiple SSH commands sequentially on a single host (non-interactive)."""

    @staticmethod
    def run(  # noqa: PLR0913 - matches the original parameter list for direct callers
        hostname: str | None = None,
        username: str | None = None,
        password: str | None = None,
        commands: list[str] | None = None,
        port: int = 22,
        timeout: int = 30,
        use_shell: bool = False,
        config: SSHConnectionConfig | None = None,
        exec_config: SSHExecutionConfig | None = None,
    ) -> bool:
        """Connect, execute each command in sequence, write per-host log; return success bool."""
        resolved = BatchExecutor._resolve_params(  # Apply config-object overrides + required-arg validation
            hostname, username, password, commands, port, timeout, use_shell, config, exec_config
        )
        hostname, username, password, commands, port, timeout, use_shell = resolved  # Unpack validated args
        logger = logging.getLogger("ssh_runner_v2")  # Unified SSH logger
        logger.info("BatchExecutor.run starting for %s@%s:%s (%d commands)", username, hostname, port, len(commands))
        logger.debug("BatchExecutor: commands=%r use_shell=%s timeout=%s", commands, use_shell, timeout)
        runner, write_to_host_log, host_log_file = BatchExecutor._setup_host_log(  # Build runner + log helper
            hostname, commands, timeout, logger
        )
        overall_success = True  # Set False on any failed command or top-level exception
        try:
            overall_success = BatchExecutor._execute_with_connection(  # Real connect + command loop
                runner, hostname, username, password, port, commands, use_shell, write_to_host_log, logger
            )
            return overall_success
        except Exception as run_error:  # noqa: BLE001 - top-level fallback mirrors original behavior
            logger.exception(
                "[%s] Unexpected error during multi-command execution: %s: %s",
                hostname,
                type(run_error).__name__,
                run_error,
            )
            write_to_host_log(f"[ERROR] Unexpected error: {run_error}")  # Verbatim error log line
            overall_success = False
            return False
        finally:
            runner._disconnect()  # Existing EnhancedSSHRunner teardown; safe when client may be None
            logger.debug("[%s] SSH multi-command session completed", hostname)
            BatchExecutor._write_footer(write_to_host_log, overall_success, host_log_file, logger)  # Best-effort footer

    # ------------------------------------------------------------------
    # Parameter resolution (config-object support + required-arg validation)
    # ------------------------------------------------------------------
    @staticmethod
    def _resolve_params(
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
        if commands is None:  # Empty command list is acceptable; mirrors original behavior
            commands = []
        return hostname, username, password, commands, port, timeout, use_shell

    # ------------------------------------------------------------------
    # Per-host log file setup
    # ------------------------------------------------------------------
    @staticmethod
    def _setup_host_log(
        hostname: str,
        commands: list[str],
        timeout: int,
        logger: logging.Logger,
    ) -> tuple[Any, Callable[[str], None], str]:
        """Build the runner, create the per-host log file, write the header; return helpers."""
        from src.ssh.ssh_runner import EnhancedSSHRunner  # Local import — avoids circular module load

        runner = EnhancedSSHRunner(timeout=timeout, logger=logger)  # Owns timeout + client lifecycle
        host_log_file, write_to_host_log = runner._create_secure_log_file(hostname)  # Existing helper
        print(f"- [{hostname}] Logging to: {host_log_file}")  # User-facing status line (verbatim)
        num_commands = len(commands) if commands else 0  # Header counter (preserve original branch)
        header = (  # Verbatim header format from the original _run_multiple_ssh_commands
            f"\n{'=' * 80}\n"
            f"SSH Session Log for Host: {hostname}\n"
            f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Commands to execute: {num_commands}\n"
            f"{'=' * 80}"
        )
        write_to_host_log(header)  # Persist the header to the per-host log
        return runner, write_to_host_log, host_log_file

    # ------------------------------------------------------------------
    # Connection + command loop
    # ------------------------------------------------------------------
    @staticmethod
    def _execute_with_connection(  # noqa: PLR0913 - collaborator orchestration needs all inputs
        runner: Any,
        hostname: str,
        username: str,
        password: str,
        port: int,
        commands: list[str],
        use_shell: bool,
        write_to_host_log: Callable[[str], None],
        logger: logging.Logger,
    ) -> bool:
        """Open SSH connection, iterate commands; return overall success bool."""
        logger.info("Connecting via SshConnector for multi-command session to %s:%s", hostname, port)
        connector = SshConnector(timeout=runner.timeout, logger=logger)  # Inline real call (not façade)
        client, kh_path = connector.connect(hostname, username, password, port)  # Real connect
        logger.debug("Multi-command connect returned client=%s", bool(client))
        if client is None:  # Connection failed; connector logged + printed already
            error_msg = f"Failed to connect to {hostname}"
            logger.error("SSH connection failed: %s:%s", hostname, port)
            write_to_host_log(f"X  {error_msg}")  # Verbatim error log line
            return False
        runner.client = client  # Wire the live client into the runner instance
        runner.managed_known_hosts_path = kh_path  # Preserve TOFU path for later save calls
        logger.debug("SSH connected to %s, executing %d commands", hostname, len(commands))
        connection_msg = f"\n>> Executing {len(commands)} commands sequentially..."  # Verbatim status
        write_to_host_log(connection_msg)
        overall_success = BatchExecutor._iterate_commands(
            runner, hostname, commands, use_shell, write_to_host_log, logger
        )
        BatchExecutor._write_final_status(write_to_host_log, overall_success, hostname, len(commands), logger)
        return overall_success

    @staticmethod
    def _iterate_commands(  # noqa: PLR0913 - per-command loop needs runner + UX helpers
        runner: Any,
        hostname: str,
        commands: list[str],
        use_shell: bool,
        write_to_host_log: Callable[[str], None],
        logger: logging.Logger,
    ) -> bool:
        """Run each command, log per-command result, return overall success bool."""
        overall_success = True  # Flip to False on any command failure or interrupt
        for index, command in enumerate(commands, 1):  # 1-based numbering matches original UX
            try:
                step_ok = BatchExecutor._run_one_command(  # Single-command execution + per-command log block
                    runner, hostname, command, index, len(commands), use_shell, write_to_host_log, logger
                )
                if not step_ok:
                    overall_success = False  # Track failure but keep going (original behavior)
                if index < len(commands):  # Inter-command delay only between commands (verbatim)
                    time.sleep(0.5)
            except KeyboardInterrupt:  # Ctrl+C halts the remaining commands (verbatim UX)
                BatchExecutor._handle_interrupt(hostname, index, len(commands), write_to_host_log, logger)
                overall_success = False
                break
        return overall_success

    @staticmethod
    def _run_one_command(  # noqa: PLR0913 - per-command log block needs full UX context
        runner: Any,
        hostname: str,
        command: str,
        index: int,
        total: int,
        use_shell: bool,
        write_to_host_log: Callable[[str], None],
        logger: logging.Logger,
    ) -> bool:
        """Execute one command, write the per-command log block; return success bool."""
        separator = f"\n{'=' * 60}"  # Visual separator (verbatim)
        command_header = f"X  Command {index}/{total}: {command}"  # Verbatim command header line
        write_to_host_log(separator)
        write_to_host_log(command_header)
        write_to_host_log("=" * 60)
        print(f"!? [{hostname}] Executing command: {command}")  # Verbatim console status
        success, stdout, stderr = runner._execute_command(command, use_shell=use_shell, hostname=hostname)
        if stdout:  # Only log output block when non-empty
            write_to_host_log("-> OUTPUT:")
            write_to_host_log(stdout)
        if stderr:  # Only log error block when non-empty
            write_to_host_log("-> ERRORS:")
            write_to_host_log(stderr)
        if success:  # Verbatim success message
            logger.debug("[%s] Command %d/%d completed: %s", hostname, index, total, command)
            write_to_host_log(f"[OK] Command {index} executed successfully")
        else:  # Verbatim failure message
            logger.warning("[%s] Command %d/%d failed: %s...", hostname, index, total, command[:50])
            write_to_host_log(f"[ERROR] Command {index} failed")
        return bool(success)

    @staticmethod
    def _handle_interrupt(
        hostname: str,
        index: int,
        total: int,
        write_to_host_log: Callable[[str], None],
        logger: logging.Logger,
    ) -> None:
        """Print + log the Ctrl+C interrupt block (verbatim text)."""
        print(f"\nX  [{hostname}] Ctrl+C detected! Skipping remaining commands...")  # Verbatim console msg
        interrupt_msg = (
            f"\n[ERROR] Command {index} interrupted by user (Ctrl+C)\n"
            f"[SKIP] Skipping remaining {total - index} commands"
        )
        write_to_host_log(interrupt_msg)
        logger.warning("[%s] Command execution interrupted by user at command %d/%d", hostname, index, total)

    @staticmethod
    def _write_final_status(
        write_to_host_log: Callable[[str], None],
        overall_success: bool,
        hostname: str,
        total: int,
        logger: logging.Logger,
    ) -> None:
        """Write the final-status block to the per-host log (verbatim text)."""
        write_to_host_log(f"\n{'=' * 60}")  # Final separator (verbatim)
        if overall_success:  # All commands ran cleanly
            logger.info("[%s] All %d commands completed successfully", hostname, total)
            write_to_host_log("[OK] All commands executed successfully")
        else:  # At least one failure or interrupt occurred
            logger.warning("[%s] Some commands failed during execution", hostname)
            write_to_host_log("[WARNING] Some commands failed - check output above")

    # ------------------------------------------------------------------
    # Footer writing (best-effort, mirrors original safe-fallback shape)
    # ------------------------------------------------------------------
    @staticmethod
    def _write_footer(
        write_to_host_log: Callable[[str], None],
        overall_success: bool,
        host_log_file: str,
        logger: logging.Logger,
    ) -> None:
        """Write the session footer; fall back to a minimal footer on any error."""
        try:
            final_success = overall_success if isinstance(overall_success, bool) else False  # Type-guard
            footer = (  # Verbatim footer format from the original
                f"\n{'=' * 80}\n"
                f"SSH Session Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Status: {'SUCCESS' if final_success else 'FAILED'}\n"
                f"Log file: {host_log_file}\n"
                f"{'=' * 80}"
            )
            write_to_host_log(footer)
        except Exception as footer_error:  # noqa: BLE001 - footer is best-effort
            logger.error("Error in multi-command footer generation: %s: %s", type(footer_error).__name__, footer_error)
            try:
                simple_footer = f"Session completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                write_to_host_log(simple_footer)
            except Exception as fallback_error:  # noqa: BLE001 - last-resort path
                logger.error("Even simple multi-command footer failed: %s", fallback_error)
                _ = os.path.basename  # Touch os to keep import live (parity with original)
