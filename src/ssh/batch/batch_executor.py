"""BatchExecutor - connect, run multiple commands sequentially on one host (T013c).

Extracted from ``EnhancedSSHRunner._run_multiple_ssh_commands`` (CC=D) per T013c of
specs/198-radon-complexity-decomposition. Every method has cyclomatic complexity <= 10.
User-facing strings (status lines, log file headers/footers, ``[OK]`` / ``[ERROR]``
markers) are preserved verbatim from the original.
"""

from __future__ import annotations  # WHY: enable PEP 604 union types on older Python.

import logging  # WHY: structured logging for the batch executor lifecycle events.
import time  # WHY: inter-command sleep between successive command executions.
from collections.abc import Callable  # WHY: type alias for the log writer closure.
from dataclasses import dataclass  # WHY: frozen bundles collapse parameter counts below the limit.
from datetime import datetime  # WHY: header + footer timestamps embedded in log output.
from typing import TYPE_CHECKING, Any  # WHY: guarded imports + loose runner typing.

from src.ssh.connection.connector import SshConnector  # WHY: real connection collaborator (no façade).

if TYPE_CHECKING:  # WHY: type-only imports avoid a circular runtime import.
    from src.ssh.ssh_runner import SSHConnectionConfig, SSHExecutionConfig  # WHY: legacy config bundle types.


# ---------------------------------------------------------------------------
# Module-level constants (magic values extracted verbatim from the original)
# ---------------------------------------------------------------------------
_SSH_LOGGER_NAME = "ssh_runner_v2"  # WHY: unified logger name shared with other SSH executors.
_INTER_COMMAND_PAUSE = 0.5  # WHY: verbatim delay between successive commands (original behavior).
_HEADER_BAR = "=" * 80  # WHY: full-width bar used in the log header + footer (verbatim).
_COMMAND_BAR = "=" * 60  # WHY: per-command block separator bar (verbatim from original).
_TS_FMT_HUMAN = "%Y-%m-%d %H:%M:%S"  # WHY: header/footer human-readable timestamp format.
_STATUS_SUCCESS = "SUCCESS"  # WHY: literal footer status token when all commands passed.
_STATUS_FAILED = "FAILED"  # WHY: literal footer status token when any command failed.
_REQUIRED_ARGS_MSG = "hostname, username, and password are required"  # WHY: shared validation message.


# ---------------------------------------------------------------------------
# Public request dataclass + internal context dataclasses
# ---------------------------------------------------------------------------
@dataclass(frozen=True, slots=True)
class BatchRunRequest:  # WHY: immutable request bundle collapses the multi-arg entrypoint.
    """Immutable request describing one non-interactive multi-command SSH session."""

    hostname: str  # WHY: SSH target host for the batch session.
    username: str  # WHY: SSH login user for the target host.
    password: str  # WHY: SSH login secret (never logged verbatim).
    commands: tuple[str, ...] = ()  # WHY: ordered command list executed sequentially.
    port: int = 22  # WHY: TCP port used for the SSH connection.
    timeout: int = 30  # WHY: connection + per-command timeout in seconds.
    use_shell: bool = False  # WHY: exec-vs-shell channel toggle passed to the runner.

    def __post_init__(self) -> None:  # WHY: dataclass validation hook enforces required creds.
        """Enforce that required credentials are present."""
        if not self.hostname or not self.username or not self.password:  # WHY: required-arg gate.
            raise ValueError(_REQUIRED_ARGS_MSG)  # WHY: reject partial credential sets.

    @classmethod
    def from_configs(  # WHY: backwards-compatible builder from legacy SSHConnectionConfig pair.
        cls,
        config: SSHConnectionConfig | None = None,
        exec_config: SSHExecutionConfig | None = None,
    ) -> BatchRunRequest:
        """Build a request from the legacy SSHConnectionConfig/SSHExecutionConfig objects."""
        if config is None:  # WHY: config object is required to supply connection fields.
            raise ValueError(_REQUIRED_ARGS_MSG)  # WHY: use the same shared error message.
        commands = tuple(exec_config.commands) if exec_config is not None else ()  # WHY: default empty.
        use_shell = exec_config.use_shell if exec_config is not None else config.use_shell  # WHY: exec overrides.
        return cls(  # WHY: emit an immutable request with the resolved fields.
            hostname=config.hostname,  # WHY: propagate connection hostname.
            username=config.username,  # WHY: propagate connection username.
            password=config.password,  # WHY: propagate connection secret.
            commands=commands,  # WHY: propagate resolved command tuple.
            port=config.port,  # WHY: propagate connection port.
            timeout=config.timeout,  # WHY: propagate connection timeout.
            use_shell=use_shell,  # WHY: propagate resolved shell flag.
        )


@dataclass(frozen=True, slots=True)
class _LogContext:  # WHY: bundle keeps helper signatures under the 5-parameter limit.
    """Bundle of per-host log collaborators (avoids passing them individually)."""

    runner: Any  # WHY: EnhancedSSHRunner instance holding client + timeout state.
    writer: Callable[[str], None]  # WHY: append-to-per-host-log writer closure.
    log_file: str  # WHY: absolute path to the per-host log file for footer output.


@dataclass(frozen=True, slots=True)
class _CommandContext:  # WHY: per-command bundle keeps helper signatures below 5 params.
    """Bundle of per-command inputs (avoids >5-param helper signatures)."""

    hostname: str  # WHY: host string used in console + log prefixes.
    command: str  # WHY: the shell/exec command being run.
    index: int  # WHY: 1-based position of this command in the batch.
    total: int  # WHY: total command count used for progress display.
    use_shell: bool  # WHY: exec-vs-shell channel toggle forwarded to runner.


class BatchExecutor:
    """Run multiple SSH commands sequentially on a single host (non-interactive)."""

    # ------------------------------------------------------------------
    # Public entrypoint (single-request signature - see BatchRunRequest)
    # ------------------------------------------------------------------
    @staticmethod
    def run(request: BatchRunRequest) -> bool:  # WHY: single-request public entrypoint.
        """Execute the batch session described by *request*; return success bool."""
        logger = logging.getLogger(_SSH_LOGGER_NAME)  # WHY: unified SSH logger for all executors.
        BatchExecutor._log_session_start(request, logger)  # WHY: emit start banner + debug details.
        log_ctx = BatchExecutor._setup_host_log(request, logger)  # WHY: build runner + log writer.
        return BatchExecutor._run_guarded(request, log_ctx, logger)  # WHY: run with cleanup + footer.

    @staticmethod
    def _log_session_start(request: BatchRunRequest, logger: logging.Logger) -> None:
        """Emit the info + debug lines that mark session start (verbatim text)."""
        logger.info(  # WHY: info-level start banner for post-mortem log review.
            "BatchExecutor.run starting for %s@%s:%s (%d commands)",
            request.username,
            request.hostname,
            request.port,
            len(request.commands),
        )
        logger.debug(  # WHY: detailed debug view of the batch inputs.
            "BatchExecutor: commands=%r use_shell=%s timeout=%s",
            list(request.commands),
            request.use_shell,
            request.timeout,
        )

    # ------------------------------------------------------------------
    # Top-level guarded flow (owns try/except/finally so run stays small)
    # ------------------------------------------------------------------
    @staticmethod
    def _run_guarded(
        request: BatchRunRequest,
        log_ctx: _LogContext,
        logger: logging.Logger,
    ) -> bool:
        """Guarded session flow: catch fatal errors and always write the footer."""
        overall_success = True  # WHY: default optimistic; flipped on any failure or exception.
        try:
            overall_success = BatchExecutor._execute_with_connection(request, log_ctx, logger)  # WHY: real run.
            return overall_success  # WHY: propagate session outcome to the caller.
        except Exception as run_error:  # noqa: BLE001 - top-level fallback mirrors original behavior
            BatchExecutor._handle_run_error(request.hostname, run_error, log_ctx, logger)  # WHY: log path.
            overall_success = False  # WHY: guarantee failure state before finally-writes footer.
            return False  # WHY: signal caller that the batch failed.
        finally:
            log_ctx.runner._disconnect()  # WHY: teardown; safe when client may be None.
            logger.debug("[%s] SSH multi-command session completed", request.hostname)  # WHY: parity log.
            BatchExecutor._write_footer(log_ctx.writer, overall_success, log_ctx.log_file, logger)  # WHY: footer.

    @staticmethod
    def _handle_run_error(
        hostname: str,
        error: BaseException,
        log_ctx: _LogContext,
        logger: logging.Logger,
    ) -> None:
        """Log the verbatim error message and append the [ERROR] line to the per-host log."""
        logger.exception(  # WHY: full traceback preserved from the original entrypoint.
            "[%s] Unexpected error during multi-command execution: %s: %s",
            hostname,
            type(error).__name__,
            error,
        )
        log_ctx.writer(f"[ERROR] Unexpected error: {error}")  # WHY: verbatim per-host log line.

    # ------------------------------------------------------------------
    # Per-host log file setup
    # ------------------------------------------------------------------
    @staticmethod
    def _setup_host_log(request: BatchRunRequest, logger: logging.Logger) -> _LogContext:
        """Build the runner, create the per-host log file, write the header; return helpers."""
        from src.ssh.ssh_runner import EnhancedSSHRunner  # WHY: local import avoids circular module load.

        runner = EnhancedSSHRunner(timeout=request.timeout, logger=logger)  # WHY: owns timeout + client.
        host_log_file, write_to_host_log = runner._create_secure_log_file(request.hostname)  # WHY: existing helper.
        # WHY: verbatim user-facing status line surfacing the per-host log destination.
        logging.info("- [%s] Logging to: %s", request.hostname, host_log_file)
        header = BatchExecutor._build_header(request.hostname, len(request.commands))  # WHY: verbatim header.
        write_to_host_log(header)  # WHY: persist the header to the per-host log file.
        return _LogContext(runner=runner, writer=write_to_host_log, log_file=host_log_file)  # WHY: bundle.

    @staticmethod
    def _build_header(hostname: str, num_commands: int) -> str:
        """Return the verbatim header block written at the top of each per-host log."""
        return (  # WHY: verbatim header format preserved from original _run_multiple_ssh_commands.
            f"\n{_HEADER_BAR}\n"
            f"SSH Session Log for Host: {hostname}\n"
            f"Started: {datetime.now().strftime(_TS_FMT_HUMAN)}\n"
            f"Commands to execute: {num_commands}\n"
            f"{_HEADER_BAR}"
        )

    # ------------------------------------------------------------------
    # Connection + command loop
    # ------------------------------------------------------------------
    @staticmethod
    def _execute_with_connection(
        request: BatchRunRequest,
        log_ctx: _LogContext,
        logger: logging.Logger,
    ) -> bool:
        """Open SSH connection, iterate commands; return overall success bool."""
        client = BatchExecutor._connect_client(request, log_ctx, logger)  # WHY: real connect step.
        if client is None:  # WHY: connection failed; connector logged the reason already.
            return False  # WHY: propagate failure sentinel to _run_guarded.
        logger.debug("SSH connected to %s, executing %d commands", request.hostname, len(request.commands))
        log_ctx.writer(f"\n>> Executing {len(request.commands)} commands sequentially...")  # WHY: verbatim status.
        overall_success = BatchExecutor._iterate_commands(request, log_ctx, logger)  # WHY: run each command.
        BatchExecutor._write_final_status(  # WHY: verbatim final [OK]/[WARNING] block.
            log_ctx.writer, overall_success, request.hostname, len(request.commands), logger
        )
        return overall_success  # WHY: return the batch outcome to _run_guarded.

    @staticmethod
    def _connect_client(
        request: BatchRunRequest,
        log_ctx: _LogContext,
        logger: logging.Logger,
    ) -> Any:
        """Perform the real SSH connect + wire the client into the runner; return client or None."""
        logger.info(  # WHY: pre-connect log line for post-mortem correlation.
            "Connecting via SshConnector for multi-command session to %s:%s",
            request.hostname,
            request.port,
        )
        connector = SshConnector(timeout=log_ctx.runner.timeout, logger=logger)  # WHY: real collaborator.
        client, kh_path = connector.connect(  # WHY: real connect call returning client + known-hosts path.
            request.hostname, request.username, request.password, request.port
        )
        logger.debug("Multi-command connect returned client=%s", bool(client))  # WHY: post-connect log.
        if client is None:  # WHY: connection failed; write the verbatim error line.
            error_msg = f"Failed to connect to {request.hostname}"  # WHY: verbatim error text.
            logger.error("SSH connection failed: %s:%s", request.hostname, request.port)  # WHY: log level.
            log_ctx.writer(f"X  {error_msg}")  # WHY: verbatim error line on the per-host log.
            return None  # WHY: sentinel triggers batch-level failure return.
        log_ctx.runner.client = client  # WHY: wire the live client into the runner instance.
        log_ctx.runner.managed_known_hosts_path = kh_path  # WHY: preserve TOFU path for save calls.
        return client  # WHY: successful connection propagates the client back.

    @staticmethod
    def _iterate_commands(
        request: BatchRunRequest,
        log_ctx: _LogContext,
        logger: logging.Logger,
    ) -> bool:
        """Run each command, log per-command result, return overall success bool."""
        overall_success = True  # WHY: flip to False on any failed command or interrupt.
        total = len(request.commands)  # WHY: reused in header + inter-command pause check.
        for index, command in enumerate(request.commands, 1):  # WHY: 1-based numbering matches original UX.
            ctx = _CommandContext(  # WHY: bundle keeps _run_one_command signature under 5 params.
                hostname=request.hostname,
                command=command,
                index=index,
                total=total,
                use_shell=request.use_shell,
            )
            step_result = BatchExecutor._step_or_interrupt(log_ctx, ctx, logger)  # WHY: run or Ctrl+C.
            if step_result.stop:  # WHY: interrupt short-circuits remaining commands.
                overall_success = False  # WHY: interrupts always mark the batch failed.
                break
            if not step_result.ok:  # WHY: failed command doesn't stop remaining commands.
                overall_success = False  # WHY: track failure but keep executing (verbatim behavior).
            if index < total:  # WHY: inter-command delay only applies between commands.
                time.sleep(_INTER_COMMAND_PAUSE)  # WHY: preserve original pacing between commands.
        return overall_success  # WHY: overall outcome bool for the whole batch.

    @staticmethod
    def _step_or_interrupt(
        log_ctx: _LogContext,
        ctx: _CommandContext,
        logger: logging.Logger,
    ) -> _StepResult:
        """Run one command; convert KeyboardInterrupt into a stop flag."""
        try:
            step_ok = BatchExecutor._run_one_command(log_ctx.runner, ctx, log_ctx.writer, logger)  # WHY: run.
            return _StepResult(stop=False, ok=step_ok)  # WHY: normal path returns the command's success.
        except KeyboardInterrupt:  # WHY: Ctrl+C halts remaining commands (verbatim UX).
            BatchExecutor._handle_interrupt(ctx, log_ctx.writer, logger)  # WHY: verbatim interrupt block.
            return _StepResult(stop=True, ok=False)  # WHY: stop=True triggers early loop exit.

    @staticmethod
    def _run_one_command(
        runner: Any,
        ctx: _CommandContext,
        writer: Callable[[str], None],
        logger: logging.Logger,
    ) -> bool:
        """Execute one command, write the per-command log block; return success bool."""
        BatchExecutor._write_command_header(ctx, writer)  # WHY: verbatim header block for the command.
        success, stdout, stderr = runner._execute_command(  # WHY: real per-command execution call.
            ctx.command, use_shell=ctx.use_shell, hostname=ctx.hostname
        )
        BatchExecutor._write_command_output(writer, stdout, stderr)  # WHY: verbatim OUTPUT/ERRORS blocks.
        BatchExecutor._log_command_result(ctx, bool(success), writer, logger)  # WHY: [OK]/[ERROR] line.
        return bool(success)  # WHY: return outcome to the iterator.

    @staticmethod
    def _write_command_header(ctx: _CommandContext, writer: Callable[[str], None]) -> None:
        """Write the three-line command header + verbatim console status line."""
        writer(f"\n{_COMMAND_BAR}")  # WHY: verbatim visual separator between commands.
        writer(f"X  Command {ctx.index}/{ctx.total}: {ctx.command}")  # WHY: verbatim command header line.
        writer(_COMMAND_BAR)  # WHY: verbatim trailing separator that closes the header block.
        # WHY: verbatim console status line announcing the current command.
        logging.info("!? [%s] Executing command: %s", ctx.hostname, ctx.command)

    @staticmethod
    def _write_command_output(
        writer: Callable[[str], None],
        stdout: str,
        stderr: str,
    ) -> None:
        """Write the OUTPUT/ERRORS blocks only when the corresponding stream is non-empty."""
        if stdout:  # WHY: skip empty stdout blocks to keep logs concise (verbatim behavior).
            writer("-> OUTPUT:")  # WHY: verbatim OUTPUT header text.
            writer(stdout)  # WHY: raw stdout captured from the runner.
        if stderr:  # WHY: skip empty stderr blocks to keep logs concise (verbatim behavior).
            writer("-> ERRORS:")  # WHY: verbatim ERRORS header text.
            writer(stderr)  # WHY: raw stderr captured from the runner.

    @staticmethod
    def _log_command_result(
        ctx: _CommandContext,
        success: bool,
        writer: Callable[[str], None],
        logger: logging.Logger,
    ) -> None:
        """Log per-command [OK]/[ERROR] status to both logger and per-host writer."""
        if success:  # WHY: verbatim success message + logger level.
            logger.debug("[%s] Command %d/%d completed: %s", ctx.hostname, ctx.index, ctx.total, ctx.command)
            writer(f"[OK] Command {ctx.index} executed successfully")  # WHY: verbatim success line.
            return  # WHY: early return keeps failure branch flat.
        logger.warning(  # WHY: verbatim failure message + level.
            "[%s] Command %d/%d failed: %s...", ctx.hostname, ctx.index, ctx.total, ctx.command[:50]
        )
        writer(f"[ERROR] Command {ctx.index} failed")  # WHY: verbatim failure line.

    @staticmethod
    def _handle_interrupt(
        ctx: _CommandContext,
        writer: Callable[[str], None],
        logger: logging.Logger,
    ) -> None:
        """Print + log the Ctrl+C interrupt block (verbatim text)."""
        # WHY: verbatim console notice for the Ctrl+C interrupt.
        logging.info("\nX  [%s] Ctrl+C detected! Skipping remaining commands...", ctx.hostname)
        interrupt_msg = (  # WHY: verbatim two-line interrupt block written to the log.
            f"\n[ERROR] Command {ctx.index} interrupted by user (Ctrl+C)\n"
            f"[SKIP] Skipping remaining {ctx.total - ctx.index} commands"
        )
        writer(interrupt_msg)  # WHY: persist the interrupt block to the per-host log.
        logger.warning(  # WHY: verbatim logger line at warning level.
            "[%s] Command execution interrupted by user at command %d/%d",
            ctx.hostname,
            ctx.index,
            ctx.total,
        )

    @staticmethod
    def _write_final_status(
        writer: Callable[[str], None],
        overall_success: bool,
        hostname: str,
        total: int,
        logger: logging.Logger,
    ) -> None:
        """Write the final-status block to the per-host log (verbatim text)."""
        writer(f"\n{_COMMAND_BAR}")  # WHY: verbatim final separator (matches original format).
        if overall_success:  # WHY: all commands ran cleanly (verbatim [OK] line).
            logger.info("[%s] All %d commands completed successfully", hostname, total)  # WHY: info log.
            writer("[OK] All commands executed successfully")  # WHY: verbatim success footer text.
            return  # WHY: early return keeps failure branch flat.
        logger.warning("[%s] Some commands failed during execution", hostname)  # WHY: warning log level.
        writer("[WARNING] Some commands failed - check output above")  # WHY: verbatim failure footer text.

    # ------------------------------------------------------------------
    # Footer writing (best-effort, mirrors original safe-fallback shape)
    # ------------------------------------------------------------------
    @staticmethod
    def _write_footer(
        writer: Callable[[str], None],
        overall_success: bool,
        host_log_file: str,
        logger: logging.Logger,
    ) -> None:
        """Write the session footer; fall back to a minimal footer on any error."""
        try:
            final_success = overall_success if isinstance(overall_success, bool) else False  # WHY: type guard.
            writer(BatchExecutor._build_footer(final_success, host_log_file))  # WHY: verbatim footer.
        except Exception as footer_error:  # noqa: BLE001 - footer is best-effort
            BatchExecutor._write_fallback_footer(writer, footer_error, logger)  # WHY: last-resort path.

    @staticmethod
    def _build_footer(final_success: bool, host_log_file: str) -> str:
        """Return the verbatim footer block written at the end of each per-host log."""
        return (  # WHY: verbatim footer format preserved from the original entrypoint.
            f"\n{_HEADER_BAR}\n"
            f"SSH Session Completed: {datetime.now().strftime(_TS_FMT_HUMAN)}\n"
            f"Status: {_STATUS_SUCCESS if final_success else _STATUS_FAILED}\n"
            f"Log file: {host_log_file}\n"
            f"{_HEADER_BAR}"
        )

    @staticmethod
    def _write_fallback_footer(
        writer: Callable[[str], None],
        footer_error: BaseException,
        logger: logging.Logger,
    ) -> None:
        """Best-effort fallback footer used only when the primary footer path fails."""
        logger.error(  # WHY: keep the failure visible even when the primary footer failed.
            "Error in multi-command footer generation: %s: %s", type(footer_error).__name__, footer_error
        )
        try:
            simple_footer = f"Session completed at {datetime.now().strftime(_TS_FMT_HUMAN)}"  # WHY: verbatim.
            writer(simple_footer)  # WHY: attempt to write the minimal fallback footer.
        except Exception as fallback_error:  # noqa: BLE001 - last-resort path
            logger.error("Even simple multi-command footer failed: %s", fallback_error)  # WHY: give up.


@dataclass(frozen=True, slots=True)
class _StepResult:  # WHY: dataclass carries per-step outcome flags back to the iterator.
    """Outcome of one command step (stop flag + success flag)."""

    stop: bool  # WHY: True when the loop must halt (interrupt or fatal exception).
    ok: bool  # WHY: True when this specific command completed without failure.
