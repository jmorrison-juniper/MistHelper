"""SingleCommandRunner - connect, execute one command on one host, log results.

Extracted from ``EnhancedSSHRunner._run_ssh_command`` (CC=C/12) per T013b of
specs/198-radon-complexity-decomposition. Every method has cyclomatic
complexity <= 10. User-facing strings (status lines, log file headers/footers,
``[OK]`` / ``[ERROR]`` markers) are preserved verbatim from the original.

Collaborators:
- :class:`src.ssh.connection.connector.SshConnector` - connection establishment
- ``EnhancedSSHRunner._execute_command``           - direct/shell execution dispatch
- ``EnhancedSSHRunner._disconnect``                - connection teardown
- ``EnhancedSSHRunner._create_secure_log_file``    - per-host log file factory
"""

from __future__ import annotations  # WHY: enable PEP 604 union types on older Python.

import logging  # WHY: structured logging for the single-command executor lifecycle events.
from collections.abc import Callable  # WHY: type alias for the log-writer closure.
from dataclasses import dataclass  # WHY: frozen bundles collapse parameter counts below the limit.
from datetime import datetime  # WHY: header + footer timestamps embedded in log output.
from typing import TYPE_CHECKING, Any  # WHY: guarded imports + loose runner typing.

from src.ssh.connection.connector import SshConnector  # WHY: real connect collaborator (no facade).

if TYPE_CHECKING:  # WHY: type-only imports avoid a circular runtime import.
    from src.ssh.ssh_runner import SSHConnectionConfig  # WHY: legacy config bundle type for builder API.


# ---------------------------------------------------------------------------
# Module-level constants (magic values extracted verbatim from the original)
# ---------------------------------------------------------------------------
_SSH_LOGGER_NAME = "ssh_runner_v2"  # WHY: unified logger name shared with other SSH executors.
_HEADER_BAR = "=" * 80  # WHY: full-width bar used in the log header + footer (verbatim).
_COMMAND_BAR = "=" * 60  # WHY: per-command block separator bar (verbatim from original).
_TS_FMT_HUMAN = "%Y-%m-%d %H:%M:%S"  # WHY: header/footer human-readable timestamp format.
_STATUS_SUCCESS = "SUCCESS"  # WHY: literal footer status token when the command succeeded.
_STATUS_FAILED = "FAILED"  # WHY: literal footer status token when the command failed.
_REQUIRED_ARGS_MSG = "hostname, username, and password are required"  # WHY: shared validation message.


# ---------------------------------------------------------------------------
# Public request dataclass + internal context dataclasses
# ---------------------------------------------------------------------------
@dataclass(frozen=True, slots=True)
class SingleCommandRequest:  # WHY: immutable request bundle collapses the multi-arg entrypoint.
    """Immutable request describing one single-command SSH session on one host."""

    hostname: str  # WHY: SSH target host for the session.
    username: str  # WHY: SSH login user for the target host.
    password: str  # WHY: SSH login secret (never logged verbatim).
    command: str = ""  # WHY: shell/exec command; empty string preserves original permissive behavior.
    port: int = 22  # WHY: TCP port used for the SSH connection.
    timeout: int = 30  # WHY: connection + per-command timeout in seconds.
    use_shell: bool = False  # WHY: exec-vs-shell channel toggle passed to the runner.

    def __post_init__(self) -> None:  # WHY: dataclass validation hook enforces required creds.
        """Enforce that required credentials are present."""
        if not self.hostname or not self.username or not self.password:  # WHY: required-arg gate.
            raise ValueError(_REQUIRED_ARGS_MSG)  # WHY: reject partial credential sets.

    @classmethod
    def from_config(  # WHY: backwards-compatible builder from legacy SSHConnectionConfig.
        cls,
        config: SSHConnectionConfig,
        command: str = "",
    ) -> SingleCommandRequest:
        """Build a request from a legacy SSHConnectionConfig plus an explicit command string."""
        if config is None:  # WHY: config object is required to supply connection fields.
            raise ValueError(_REQUIRED_ARGS_MSG)  # WHY: reuse the shared validation message.
        return cls(  # WHY: emit an immutable request with the resolved fields.
            hostname=config.hostname,  # WHY: propagate connection hostname.
            username=config.username,  # WHY: propagate connection username.
            password=config.password,  # WHY: propagate connection secret.
            command=command,  # WHY: explicit command; config carries no command field.
            port=config.port,  # WHY: propagate connection port.
            timeout=config.timeout,  # WHY: propagate connection timeout.
            use_shell=config.use_shell,  # WHY: propagate the exec-vs-shell flag.
        )


@dataclass(frozen=True, slots=True)
class _LogContext:  # WHY: bundle keeps helper signatures under the 5-parameter limit.
    """Bundle of per-host log collaborators (avoids passing them individually)."""

    runner: Any  # WHY: EnhancedSSHRunner instance holding client + timeout state.
    writer: Callable[[str], None]  # WHY: append-to-per-host-log writer closure.
    log_file: str  # WHY: absolute path to the per-host log file for footer output.


@dataclass(frozen=True, slots=True)
class _ResultContext:  # WHY: bundle keeps _write_results signature under the 5-parameter limit.
    """Bundle of command-execution outputs consumed by the result-writing helpers."""

    stdout: str  # WHY: stdout captured from the runner's _execute_command call.
    stderr: str  # WHY: stderr captured from the runner's _execute_command call.
    success: bool  # WHY: True when the command completed with a zero exit status.
    command: str  # WHY: original command string used in the failure-log line.
    hostname: str  # WHY: host string used in status log prefixes.


class SingleCommandRunner:
    """Orchestrate one SSH command on one host: connect, execute, log, disconnect."""

    # ------------------------------------------------------------------
    # Public entrypoint (single-request signature - see SingleCommandRequest)
    # ------------------------------------------------------------------
    @staticmethod
    def run(request: SingleCommandRequest) -> bool:  # WHY: single-request public entrypoint.
        """Execute the session described by *request*; return success bool."""
        logger = logging.getLogger(_SSH_LOGGER_NAME)  # WHY: unified SSH logger for all executors.
        SingleCommandRunner._log_session_start(request, logger)  # WHY: emit start banner + debug details.
        log_ctx = SingleCommandRunner._setup_host_log(request, logger)  # WHY: build runner + log writer.
        return SingleCommandRunner._run_guarded(request, log_ctx, logger)  # WHY: run with cleanup + footer.

    @staticmethod
    def _log_session_start(request: SingleCommandRequest, logger: logging.Logger) -> None:
        """Emit the info + debug lines that mark session start (verbatim text)."""
        logger.info(  # WHY: info-level start banner for post-mortem log review.
            "SingleCommandRunner.run starting for %s@%s:%s",
            request.username,
            request.hostname,
            request.port,
        )
        logger.debug(  # WHY: detailed debug view of the single-command inputs.
            "SingleCommandRunner: command=%r timeout=%s use_shell=%s",
            request.command,
            request.timeout,
            request.use_shell,
        )

    # ------------------------------------------------------------------
    # Top-level guarded flow (owns try/except/finally so run stays small)
    # ------------------------------------------------------------------
    @staticmethod
    def _run_guarded(
        request: SingleCommandRequest,
        log_ctx: _LogContext,
        logger: logging.Logger,
    ) -> bool:
        """Guarded session flow: catch fatal errors and always write the footer."""
        single_cmd_success = False  # WHY: default False; flipped only on confirmed success.
        try:
            single_cmd_success = SingleCommandRunner._execute_with_connection(  # WHY: real run.
                request, log_ctx, logger
            )
            return single_cmd_success  # WHY: propagate session outcome to the caller.
        except Exception as run_error:  # noqa: BLE001 - top-level fallback mirrors original behavior
            SingleCommandRunner._handle_run_error(request.hostname, run_error, log_ctx, logger)  # WHY: log path.
            return False  # WHY: signal caller that the command failed.
        finally:
            log_ctx.runner._disconnect()  # WHY: teardown; safe when client may be None.
            logger.debug("[%s] SSH single command session completed", request.hostname)  # WHY: parity log.
            SingleCommandRunner._write_footer(log_ctx, single_cmd_success, logger)  # WHY: footer always runs.

    @staticmethod
    def _handle_run_error(
        hostname: str,
        error: BaseException,
        log_ctx: _LogContext,
        logger: logging.Logger,
    ) -> None:
        """Log the verbatim error message and append the [ERROR] line to the per-host log."""
        logger.exception(  # WHY: full traceback preserved from the original entrypoint.
            "[%s] Unexpected error during SSH command execution: %s: %s",
            hostname,
            type(error).__name__,
            error,
        )
        log_ctx.writer(f"[ERROR] Unexpected error: {error}")  # WHY: verbatim per-host log line.

    # ------------------------------------------------------------------
    # Per-host log file setup
    # ------------------------------------------------------------------
    @staticmethod
    def _setup_host_log(request: SingleCommandRequest, logger: logging.Logger) -> _LogContext:
        """Build the runner, create the per-host log file, write the header; return helpers."""
        from src.ssh.ssh_runner import EnhancedSSHRunner  # WHY: local import avoids circular module load.

        runner = EnhancedSSHRunner(timeout=request.timeout, logger=logger)  # WHY: owns timeout + client.
        host_log_file, write_to_host_log = runner._create_secure_log_file(request.hostname)  # WHY: existing helper.
        print(f"- [{request.hostname}] Logging to: {host_log_file}")  # WHY: verbatim user-facing status line.
        header = SingleCommandRunner._build_header(request.hostname, request.command)  # WHY: verbatim header.
        write_to_host_log(header)  # WHY: persist the header to the per-host log file.
        return _LogContext(runner=runner, writer=write_to_host_log, log_file=host_log_file)  # WHY: bundle.

    @staticmethod
    def _build_header(hostname: str, command: str) -> str:
        """Return the verbatim header block written at the top of each per-host log."""
        return (  # WHY: verbatim header format preserved from original _run_ssh_command.
            f"\n{_HEADER_BAR}\n"
            f"SSH Single Command Log for Host: {hostname}\n"
            f"Started: {datetime.now().strftime(_TS_FMT_HUMAN)}\n"
            f"Command: {command}\n"
            f"{_HEADER_BAR}"
        )

    # ------------------------------------------------------------------
    # Connection + execution + result writing
    # ------------------------------------------------------------------
    @staticmethod
    def _execute_with_connection(
        request: SingleCommandRequest,
        log_ctx: _LogContext,
        logger: logging.Logger,
    ) -> bool:
        """Connect via SshConnector, execute the command, write results, return success."""
        client = SingleCommandRunner._connect_client(request, log_ctx, logger)  # WHY: real connect step.
        if client is None:  # WHY: connection failed; connector logged the reason already.
            return False  # WHY: propagate failure sentinel to _run_guarded.
        logger.debug("SSH connected to %s, executing single command", request.hostname)  # WHY: parity log.
        success, stdout, stderr = log_ctx.runner._execute_command(  # WHY: dispatcher remains on EnhancedSSHRunner.
            request.command, use_shell=request.use_shell, hostname=request.hostname
        )
        SingleCommandRunner._log_execute_return(success, stdout, stderr, logger)  # WHY: debug telemetry.
        result_ctx = _ResultContext(  # WHY: bundle keeps _write_results signature under 5 params.
            stdout=stdout or "",  # WHY: normalize None to empty so downstream checks stay simple.
            stderr=stderr or "",  # WHY: normalize None to empty so downstream checks stay simple.
            success=bool(success),  # WHY: normalize non-bool truthiness to a real bool.
            command=request.command,  # WHY: needed for the truncated failure log line.
            hostname=request.hostname,  # WHY: needed for the status log prefix.
        )
        SingleCommandRunner._write_results(log_ctx.writer, result_ctx, logger)  # WHY: verbatim result block.
        return bool(success)  # WHY: propagate outcome to _run_guarded.

    @staticmethod
    def _connect_client(
        request: SingleCommandRequest,
        log_ctx: _LogContext,
        logger: logging.Logger,
    ) -> Any:
        """Perform the real SSH connect + wire the client into the runner; return client or None."""
        connector = SshConnector(timeout=log_ctx.runner.timeout, logger=logger)  # WHY: real collaborator.
        logger.info(  # WHY: pre-connect log line for post-mortem correlation.
            "SingleCommandRunner: connecting via SshConnector to %s:%s", request.hostname, request.port
        )
        client, managed_kh_path = connector.connect(  # WHY: real connect call returning client + kh path.
            request.hostname, request.username, request.password, request.port
        )
        logger.debug("SingleCommandRunner: connect returned client=%s", bool(client))  # WHY: post-connect log.
        if client is None:  # WHY: connection failed; write the verbatim error line.
            error_msg = f"Failed to connect to {request.hostname}"  # WHY: verbatim error text.
            logger.error("SSH connection failed: %s:%s", request.hostname, request.port)  # WHY: log level.
            log_ctx.writer(f"X  {error_msg}")  # WHY: verbatim error line on the per-host log.
            return None  # WHY: sentinel triggers session-level failure return.
        log_ctx.runner.client = client  # WHY: wire the live client into the runner instance.
        log_ctx.runner.managed_known_hosts_path = managed_kh_path  # WHY: preserve TOFU path for save calls.
        return client  # WHY: successful connection propagates the client back.

    @staticmethod
    def _log_execute_return(success: bool, stdout: str, stderr: str, logger: logging.Logger) -> None:
        """Emit the debug line summarizing the runner._execute_command return values."""
        logger.debug(  # WHY: debug telemetry mirrors the original single-line summary.
            "SingleCommandRunner: _execute_command returned success=%s stdout_len=%d stderr_len=%d",
            success,
            len(stdout or ""),
            len(stderr or ""),
        )

    # ------------------------------------------------------------------
    # Result writing (verbatim output blocks + [OK]/[ERROR] status line)
    # ------------------------------------------------------------------
    @staticmethod
    def _write_results(
        writer: Callable[[str], None],
        result_ctx: _ResultContext,
        logger: logging.Logger,
    ) -> None:
        """Write stdout/stderr blocks and the success/failure marker to the per-host log."""
        SingleCommandRunner._write_output_blocks(writer, result_ctx.stdout, result_ctx.stderr)  # WHY: body.
        SingleCommandRunner._write_status_line(writer, result_ctx, logger)  # WHY: [OK]/[ERROR] line.

    @staticmethod
    def _write_output_blocks(
        writer: Callable[[str], None],
        stdout: str,
        stderr: str,
    ) -> None:
        """Write the verbatim COMMAND OUTPUT block including STDOUT/STDERR/no-output markers."""
        writer("\n" + _COMMAND_BAR)  # WHY: verbatim leading visual separator (with leading newline).
        writer("!? COMMAND OUTPUT")  # WHY: verbatim section header preserved from original.
        writer(_COMMAND_BAR)  # WHY: verbatim trailing separator for the section header.
        if stdout:  # WHY: only write the stdout block when there is content (verbatim behavior).
            writer("-> STDOUT:")  # WHY: verbatim STDOUT header.
            writer(stdout)  # WHY: raw stdout captured from the runner.
        if stderr:  # WHY: only write the stderr block when there is content (verbatim behavior).
            writer("-> STDERR:")  # WHY: verbatim STDERR header.
            writer(stderr)  # WHY: raw stderr captured from the runner.
        if not stdout and not stderr:  # WHY: explicit no-output marker (verbatim behavior).
            writer("X  No output returned")  # WHY: verbatim no-output marker.
        writer(_COMMAND_BAR)  # WHY: verbatim final separator that closes the OUTPUT block.

    @staticmethod
    def _write_status_line(
        writer: Callable[[str], None],
        result_ctx: _ResultContext,
        logger: logging.Logger,
    ) -> None:
        """Log the [OK] or [ERROR] status line for this single command (verbatim text)."""
        if result_ctx.success:  # WHY: verbatim success message + logger level.
            logger.info("[%s] Command completed successfully", result_ctx.hostname)  # WHY: info log.
            writer("[OK] Command executed successfully")  # WHY: verbatim success line.
            return  # WHY: early return keeps the failure branch flat.
        logger.warning(  # WHY: verbatim failure message + level.
            "[%s] Command failed: %s...", result_ctx.hostname, result_ctx.command[:50]
        )
        writer("[ERROR] Command execution failed or returned non-zero exit status")  # WHY: verbatim.

    # ------------------------------------------------------------------
    # Footer writing (best-effort, mirrors original safe-fallback shape)
    # ------------------------------------------------------------------
    @staticmethod
    def _write_footer(
        log_ctx: _LogContext,
        single_cmd_success: bool,
        logger: logging.Logger,
    ) -> None:
        """Write the session footer; fall back to a minimal footer on any error."""
        try:
            final_success = single_cmd_success if isinstance(single_cmd_success, bool) else False  # WHY: type guard.
            log_ctx.writer(SingleCommandRunner._build_footer(final_success, log_ctx.log_file))  # WHY: verbatim.
        except Exception as footer_error:  # noqa: BLE001 - footer is best-effort
            SingleCommandRunner._write_fallback_footer(log_ctx.writer, footer_error, logger)  # WHY: last-resort.

    @staticmethod
    def _build_footer(final_success: bool, host_log_file: str) -> str:
        """Return the verbatim footer block written at the end of each per-host log."""
        return (  # WHY: verbatim footer format preserved from the original entrypoint.
            f"\n{_HEADER_BAR}\n"
            f"SSH Single Command Session Completed: {datetime.now().strftime(_TS_FMT_HUMAN)}\n"
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
            "Error in footer generation: %s: %s", type(footer_error).__name__, footer_error
        )
        try:
            simple_footer = f"Session completed at {datetime.now().strftime(_TS_FMT_HUMAN)}"  # WHY: verbatim.
            writer(simple_footer)  # WHY: attempt to write the minimal fallback footer.
        except Exception as fallback_error:  # noqa: BLE001 - last-resort path
            logger.error("Even simple footer failed: %s", fallback_error)  # WHY: give up gracefully.
