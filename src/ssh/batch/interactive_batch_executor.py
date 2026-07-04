"""InteractiveBatchExecutor - interactive multi-step SSH session (T013c).

Extracted from ``EnhancedSSHRunner._run_multiple_ssh_commands_interactive`` per
T013c of specs/198-radon-complexity-decomposition. User-facing strings (status
lines, log file headers/footers, [STEP], [OK], [ERROR], [INTERRUPT] markers)
and magic wait-window values are preserved verbatim from the original.

The interactive flow drives a persistent paramiko shell channel to support
sequences that require interactive input (e.g. ``su`` -> ``Password:`` ->
response -> ``show ...``).
"""

from __future__ import annotations  # WHY: enable PEP 604 union types on older Python.

import logging  # WHY: structured logging for the interactive executor.
import os  # WHY: filesystem chmod + path joining for per-host log files.
import re  # WHY: ANSI escape + control-sequence cleanup on shell output.
import time  # WHY: inter-command pacing + response-wait windows.
from collections.abc import Callable  # WHY: type alias for injected writer/closure.
from dataclasses import dataclass  # WHY: frozen dataclasses collapse param counts.
from datetime import datetime  # WHY: per-host log timestamps + headers/footers.
from typing import TYPE_CHECKING, Any  # WHY: type hints + guarded runtime imports.

from src.ssh.connection.connector import SshConnector  # WHY: real SSH connect collaborator.

if TYPE_CHECKING:  # WHY: type-only imports avoid circular runtime import.
    from src.ssh.ssh_runner import SSHConnectionConfig, SSHExecutionConfig  # WHY: legacy config types.


# ---------------------------------------------------------------------------
# Module-level constants (magic values extracted verbatim from the original)
# ---------------------------------------------------------------------------
_MAX_WAIT_SECONDS = 10  # WHY: maximum total wait for a step response (verbatim).
_WAIT_INCREMENT = 0.1  # WHY: polling interval inside the response-wait loop (verbatim).
_NO_DATA_TIMEOUT = 3.0  # WHY: bail-out when no new data arrives for this many seconds.
_INIT_PROMPT_WAIT = 1.0  # WHY: pause after invoke_shell to let device print prompt.
_STEP_SEND_PAUSE = 0.2  # WHY: brief pause after sending a step so device registers input.
_STEP_STABILITY_PAUSE = 0.5  # WHY: stability delay between successive steps (verbatim).
_SHELL_EXIT_PAUSE = 0.5  # WHY: give the device a moment to process the closing 'exit'.
_RECV_BUFFER = 4096  # WHY: buffer size for shell.recv() reads (verbatim).
_TERM_WIDTH = 120  # WHY: virtual TTY width passed to invoke_shell (verbatim).
_TERM_HEIGHT = 24  # WHY: virtual TTY height passed to invoke_shell (verbatim).
_PW_MIN_MASK_LEN = 5  # WHY: only mask password-like items longer than this threshold.
_PROMPT_QUIET_SECS = 1.0  # WHY: quiet period after a prompt suffix to stop waiting.
_PROMPT_TAIL_LEN = 50  # WHY: number of trailing chars scanned for prompt patterns.
_LOG_DIR_MODE = 0o700  # WHY: owner-only permissions on the per-host log directory.
_LOG_FILE_MODE = 0o600  # WHY: owner-only permissions on the per-host log file.
_HEADER_BAR = "=" * 80  # WHY: full-width bar used in header/footer text (verbatim).
_STEP_BAR = "=" * 60  # WHY: step-block separator bar (verbatim).
_REDACTION_MARK = "***REDACTED***"  # WHY: literal replacement token for password scrubbing.
_TS_FMT_HUMAN = "%Y-%m-%d %H:%M:%S"  # WHY: header/footer human-readable timestamp format.
_TS_FMT_FILE = "%Y%m%d_%H%M%S"  # WHY: filesystem-safe timestamp component for filenames.

_PASSWORD_HINTS = ("password", "pass", "pwd")  # WHY: substrings used for redaction check.
_PASSWORD_PROMPTS = ("password:", "password ", "passwd:")  # WHY: prompt suffixes to detect.
_PROMPT_PATTERNS = ("$", "#", ">", "pcli")  # WHY: recognized shell prompt suffixes.
_FAILURE_PATTERNS: tuple[tuple[str, str], ...] = (  # WHY: lower-cased failure indicators.
    ("command not found", "command not found"),
    ("permission denied", "permission denied"),
    ("authentication failed", "authentication failed"),
)

_ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*[mGKHfABCDsuJ]")  # WHY: ANSI color/cursor sequences.
_CONTROL_SEQ_RES: tuple[re.Pattern[str], ...] = (  # WHY: additional terminal-control cleaners.
    re.compile(r"\x1b\[\?[0-9]+[lh]"),
    re.compile(r"\x1b\[[0-9]+[ABCDGK]"),
    re.compile(r"\x1b\[[0-9]+;[0-9]+[Hf]"),
    re.compile(r"\x1b\[[0-9]*[J]"),
    re.compile(r"\x1b\[6n"),
    re.compile(r"\x1b\[[0-9]+D"),
    re.compile(r"\x1b\[\?2004[hl]"),
    re.compile(r"\x1b\[\?25[lh]"),
    re.compile(r"\x1b\[\?7[lh]"),
    re.compile(r"\x1b\[\?12[lh]"),
)
_MULTI_BLANK_RE = re.compile(r"\n\s*\n\s*\n")  # WHY: collapse 3+ blank lines to 2.
_TRAIL_WS_RE = re.compile(r"[ \t]+\n")  # WHY: trim trailing horizontal whitespace.


# ---------------------------------------------------------------------------
# Public request dataclass + internal context dataclasses
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class InteractiveSessionRequest:  # WHY: immutable request bundle collapses the 7-param entrypoint.
    """Immutable request describing one interactive SSH session."""

    hostname: str  # WHY: SSH target host.
    username: str  # WHY: SSH login user.
    password: str  # WHY: SSH login secret (scrubbed from logs).
    commands: tuple[str, ...] = ()  # WHY: ordered scripted command/response steps.
    port: int = 22  # WHY: TCP port for the SSH connection.
    timeout: int = 30  # WHY: connection + shell-channel timeout (seconds).
    use_shell: bool = True  # WHY: interactive mode always requires shell=True.

    def __post_init__(self) -> None:  # WHY: dataclass validation hook enforces required creds.
        """Enforce that required credentials are present."""
        if not self.hostname or not self.username or not self.password:  # WHY: required-arg gate.
            raise ValueError("hostname, username, and password are required")  # WHY: reject partial creds.

    @classmethod
    def from_configs(  # WHY: backwards-compatible builder from legacy SSHConnectionConfig pair.
        cls,
        config: SSHConnectionConfig | None = None,
        exec_config: SSHExecutionConfig | None = None,
    ) -> InteractiveSessionRequest:
        """Build a request from the legacy SSHConnectionConfig/SSHExecutionConfig objects."""
        if config is None:  # WHY: config object is required for the legacy config-object path.
            raise ValueError("hostname, username, and password are required")  # WHY: same message as init.
        commands = tuple(exec_config.commands) if exec_config is not None else ()  # WHY: fall back to empty tuple.
        use_shell = exec_config.use_shell if exec_config is not None else config.use_shell  # WHY: exec overrides.
        return cls(  # WHY: emit an immutable request with the resolved fields.
            hostname=config.hostname,
            username=config.username,
            password=config.password,
            commands=commands,
            port=config.port,
            timeout=config.timeout,
            use_shell=use_shell,
        )


@dataclass(frozen=True)
class _LogContext:  # WHY: bundle keeps helper signatures under the 5-param limit.
    """Bundle of per-host log collaborators (avoids passing them individually)."""

    runner: Any  # WHY: EnhancedSSHRunner holding connection + timeout state.
    writer: Callable[[str], None]  # WHY: scrubbing log writer closure.
    log_file: str  # WHY: absolute path to the per-host log file.


@dataclass(frozen=True)
class _StepContext:  # WHY: bundle keeps per-step helper signatures under 5 params.
    """Bundle of per-step inputs (avoids >5-param helper signatures)."""

    hostname: str  # WHY: for prefixed log/console messages.
    command: str  # WHY: the command/response line to send.
    step_num: int  # WHY: 1-based step index used in headers.
    total: int  # WHY: total step count used in step headers.


@dataclass(frozen=True)
class _StepResult:  # WHY: dataclass carries the step outcome triple back to the iterator.
    """Outcome of one step iteration (stop flag, success flag, pause-required flag)."""

    stop: bool  # WHY: True when the loop must halt (interrupt or fatal exception).
    step_ok: bool  # WHY: True when this specific step completed without a failure indicator.
    pause: bool  # WHY: True when the caller should apply the inter-step stability pause.


# ---------------------------------------------------------------------------
# Module-level helpers used by the executor (kept out of the class body so
# they are counted as small, single-purpose functions by the analyzer).
# ---------------------------------------------------------------------------
def _apply_regex_cleaners(message: str) -> str:  # WHY: module-level for reuse + easy unit-testing.
    """Strip ANSI + control sequences and normalise whitespace on a log line."""
    clean = _ANSI_ESCAPE_RE.sub("", message)  # WHY: strip ANSI color + cursor codes.
    for pattern in _CONTROL_SEQ_RES:  # WHY: strip remaining terminal-control sequences.
        clean = pattern.sub("", clean)  # WHY: apply one terminal-control cleaner per iteration.
    clean = _MULTI_BLANK_RE.sub("\n\n", clean)  # WHY: collapse 3+ blank lines to 2 (verbatim).
    clean = _TRAIL_WS_RE.sub("\n", clean)  # WHY: trim trailing horizontal whitespace.
    return clean.replace("\x00", "").replace("\r\n", "\n")  # WHY: prevent log injection.


def _persist_log_line(host_log_file: str, safe_message: str) -> None:  # WHY: owner-only append helper.
    """Append one already-sanitized line to the per-host log with owner-only perms."""
    with open(host_log_file, "a", encoding="utf-8") as log_file:  # WHY: append preserves history.
        # lgtm[py/clear-text-storage-sensitive-data] - messages are pre-scrubbed by
        # _build_scrubbing_writer; CodeQL cannot model str.replace as a sanitizer.
        log_file.write(f"{safe_message}\n")  # WHY: newline-terminated log record.
        log_file.flush()  # WHY: guarantee flush before chmod tightens perms.
    if hasattr(os, "chmod"):  # WHY: best-effort owner-only permission on POSIX.
        os.chmod(host_log_file, _LOG_FILE_MODE)  # WHY: enforce 0o600 owner-only file mode.


def _write_ascii_fallback(
    message: str, host_log_file: str, logger: logging.Logger
) -> None:  # WHY: encoding-fallback path.
    """ASCII-only fallback used when UTF-8 encoding of the sanitised line fails."""
    try:
        safe_message = message.encode("ascii", errors="replace").decode("ascii")  # WHY: last-resort encoding.
        _persist_log_line(host_log_file, safe_message)  # WHY: reuse the sanitised persister.
    except Exception:  # noqa: BLE001 - last-resort path (verbatim behaviour)
        logger.error("Failed to write sanitized message to host log")  # WHY: preserve original error line.


def _write_clean_line(
    message: str, host_log_file: str, logger: logging.Logger
) -> None:  # WHY: primary log-write entrypoint.
    """Clean + persist one log line, falling back to ASCII on unicode errors."""
    if not message:  # WHY: skip empty writes (parity with original behaviour).
        return  # WHY: preserve original no-op behaviour for falsy messages.
    try:
        safe_message = _apply_regex_cleaners(message)  # WHY: strip ANSI + normalise whitespace.
        _persist_log_line(host_log_file, safe_message)  # WHY: durable append with owner-only perms.
    except UnicodeEncodeError:  # WHY: ASCII fallback path mirrors original behaviour.
        _write_ascii_fallback(message, host_log_file, logger)  # WHY: retry via ASCII-encoded persister.
    except Exception as write_error:  # noqa: BLE001 - last-resort path (verbatim)
        logger.error(
            "Unexpected error writing to host log %s: %s", host_log_file, write_error
        )  # WHY: preserve original error line.


def _resolve_log_dir(logger: logging.Logger) -> str:  # WHY: shared per-host log-dir resolver.
    """Resolve the per-host-logs directory, creating it with owner-only perms when needed."""
    from src.ssh.ssh_runner import EnhancedSSHRunner  # WHY: local import avoids circular module load.

    data_dir = EnhancedSSHRunner._get_data_directory()  # WHY: reuse the runner's resolved data dir.
    log_dir = os.path.join(data_dir, "per-host-logs")  # WHY: conventional subdirectory for logs.
    try:
        os.makedirs(log_dir, exist_ok=True)  # WHY: idempotent create of the log subdirectory.
        if hasattr(os, "chmod"):  # WHY: best-effort owner-only permission on POSIX.
            os.chmod(log_dir, _LOG_DIR_MODE)  # WHY: enforce 0o700 owner-only dir mode.
        return log_dir  # WHY: return the created/verified log directory path.
    except OSError as mkdir_error:  # WHY: fall back to data_dir when subdir cannot be created.
        logger.error(
            "Failed to create log directory %s: %s", log_dir, mkdir_error
        )  # WHY: preserve original error line.
        return data_dir  # WHY: fallback so logging never fully fails.


def _build_header(hostname: str, num_commands: int) -> str:  # WHY: verbatim per-host header builder.
    """Return the verbatim header block written at the top of each per-host log."""
    started = datetime.now().strftime(_TS_FMT_HUMAN)  # WHY: human-readable start timestamp.
    return (  # WHY: verbatim header format preserved from the original entrypoint.
        f"\n{_HEADER_BAR}\n"
        f"SSH Interactive Session Log for Host: {hostname}\n"
        f"Started: {started}\n"
        f"Commands/responses to execute: {num_commands}\n"
        f"{_HEADER_BAR}"
    )


def _build_footer_text(overall_success: bool, host_log_file: str) -> str:  # WHY: verbatim footer builder.
    """Return the verbatim footer block appended at the end of each per-host log."""
    final_success = overall_success if isinstance(overall_success, bool) else False  # WHY: coerce non-bool.
    completed = datetime.now().strftime(_TS_FMT_HUMAN)  # WHY: human-readable completion timestamp.
    status = "SUCCESS" if final_success else "FAILED"  # WHY: verbatim status label.
    return (  # WHY: verbatim footer format preserved from the original entrypoint.
        f"\n{_HEADER_BAR}\n"
        f"SSH Interactive Session Completed: {completed}\n"
        f"Status: {status}\n"
        f"Log file: {host_log_file}\n"
        f"{_HEADER_BAR}"
    )


class InteractiveBatchExecutor:  # WHY: static-method container for the interactive-session flow.
    """Drive a persistent shell channel through a scripted command/response sequence."""

    # ------------------------------------------------------------------
    # Public entrypoint (single-request signature — see InteractiveSessionRequest)
    # ------------------------------------------------------------------
    @staticmethod
    def run(request: InteractiveSessionRequest) -> bool:  # WHY: single-request public entrypoint.
        """Execute the interactive session described by *request*; return success bool."""
        logger = logging.getLogger("ssh_runner_v2")  # WHY: unified SSH logger for all executors.
        logger.info(  # WHY: session start line for post-mortem log review.
            "InteractiveBatchExecutor.run starting for %s@%s:%s (%d steps)",
            request.username,
            request.hostname,
            request.port,
            len(request.commands),
        )
        logger.debug(  # WHY: detailed step inputs at debug level to keep info logs terse.
            "InteractiveBatchExecutor: steps=%r use_shell=%s timeout=%s",
            list(request.commands),
            request.use_shell,
            request.timeout,
        )
        log_ctx = InteractiveBatchExecutor._setup_log_context(request, logger)  # WHY: build log writer.
        return InteractiveBatchExecutor._run_guarded(request, log_ctx, logger)  # WHY: run with cleanup.

    # ------------------------------------------------------------------
    # Top-level guarded flow (owns try/except/finally so run stays small)
    # ------------------------------------------------------------------
    @staticmethod
    def _run_guarded(  # WHY: top-level guarded flow (try/except/finally isolated here).
        request: InteractiveSessionRequest,
        log_ctx: _LogContext,
        logger: logging.Logger,
    ) -> bool:
        """Guarded session flow: catch fatal errors and always write the footer."""
        overall_success = True  # WHY: default to success; flipped on any failed step or error.
        try:
            overall_success = InteractiveBatchExecutor._execute_session(request, log_ctx, logger)  # WHY: run session.
            return overall_success  # WHY: propagate session outcome to caller.
        except Exception as session_error:  # noqa: BLE001 - top-level fallback (verbatim)
            InteractiveBatchExecutor._handle_session_error(
                request.hostname, session_error, log_ctx, logger
            )  # WHY: verbatim error path.
            overall_success = False  # WHY: guarantee failure state before finally-writes footer.
            return False  # WHY: signal caller that the session failed.
        finally:
            log_ctx.runner._disconnect()  # WHY: teardown; safe when client may be None.
            logger.debug("[%s] SSH interactive session completed", request.hostname)  # WHY: parity log line.
            InteractiveBatchExecutor._write_footer(
                log_ctx.writer, overall_success, log_ctx.log_file, logger
            )  # WHY: always emit footer.

    @staticmethod
    def _handle_session_error(  # WHY: verbatim error-log path split out of _run_guarded.
        hostname: str,
        error: BaseException,
        log_ctx: _LogContext,
        logger: logging.Logger,
    ) -> None:
        """Log an unexpected top-level error and write the verbatim [ERROR] line."""
        logger.exception(  # WHY: full traceback preserved from the original entrypoint.
            "[%s] Unexpected error during interactive session: %s: %s",
            hostname,
            type(error).__name__,
            error,
        )
        log_ctx.writer(f"[ERROR] Unexpected error: {error}")  # WHY: verbatim per-host log line.

    # ------------------------------------------------------------------
    # Per-host log setup
    # ------------------------------------------------------------------
    @staticmethod
    def _setup_log_context(
        request: InteractiveSessionRequest, logger: logging.Logger
    ) -> _LogContext:  # WHY: builds log collaborators.
        """Create the runner + per-host log file + credential-scrubbing writer."""
        from src.ssh.ssh_runner import EnhancedSSHRunner  # WHY: local import avoids circular load.

        runner = EnhancedSSHRunner(timeout=request.timeout, logger=logger)  # WHY: owns client lifecycle.
        host_log_file = InteractiveBatchExecutor._build_log_path(request.hostname, logger)  # WHY: sanitised path.
        print(f"** [{request.hostname}] Logging to: {host_log_file}")  # WHY: verbatim console status line.
        raw_writer = InteractiveBatchExecutor._make_log_writer(host_log_file, logger)  # WHY: ANSI-cleaning writer.
        writer = InteractiveBatchExecutor._build_scrubbing_writer(raw_writer, request.password)  # WHY: scrub creds.
        writer(_build_header(request.hostname, len(request.commands)))  # WHY: persist header verbatim.
        return _LogContext(runner=runner, writer=writer, log_file=host_log_file)  # WHY: emit bundled log context.

    @staticmethod
    def _build_log_path(hostname: str, logger: logging.Logger) -> str:  # WHY: sanitised per-host log path.
        """Construct the sanitised per-host log file path; fall back on chmod errors."""
        from src.ssh.ssh_runner import EnhancedSSHRunner  # WHY: local import avoids circular load.

        timestamp = datetime.now().strftime(_TS_FMT_FILE)  # WHY: verbatim filename timestamp format.
        safe_hostname = EnhancedSSHRunner.sanitize_filename(hostname)  # WHY: filesystem-safe hostname.
        log_dir = _resolve_log_dir(logger)  # WHY: resolve subdir (falls back on OSError).
        data_dir = EnhancedSSHRunner._get_data_directory()  # WHY: detect subdir-fallback path.
        if log_dir == data_dir:  # WHY: when subdir creation failed, tag filename to match original.
            safe_hostname = f"fallback_{safe_hostname}"  # WHY: verbatim fallback-name prefix.
        return os.path.join(log_dir, f"ssh_output_{safe_hostname}_{timestamp}.log")  # WHY: verbatim filename format.

    @staticmethod
    def _build_scrubbing_writer(  # WHY: closure-based credential scrubber for log lines.
        inner_writer: Callable[[str], None],
        password: str | None,
    ) -> Callable[[str], None]:
        """Wrap *inner_writer* so each message has *password* replaced with ``***REDACTED***``.

        Returning a new callable keeps the password reference confined to this
        helper's closure; the inner writer never receives the credential value
        as a parameter, satisfying the minimum-scope rule for sensitive data.
        """
        if not password:  # WHY: no credential to scrub - callers get the raw writer.
            return inner_writer  # WHY: passthrough writer when no password to hide.

        def scrubbing_writer(message: str) -> None:  # WHY: closure captures password only here.
            """Inner closure: scrub then forward each message to the disk writer."""
            inner_writer(message.replace(password, _REDACTION_MARK))  # WHY: literal-token replacement.

        return scrubbing_writer  # WHY: hand the scrubbing closure back to the caller.

    @staticmethod
    def _make_log_writer(host_log_file: str, logger: logging.Logger) -> Callable[[str], None]:  # WHY: writer factory.
        """Return a closure that strips ANSI/control sequences before writing each line.

        Credential scrubbing happens in the caller's wrapper closure (NOT here)
        so this writer never holds a reference to any password value.
        """

        def write_to_host_log(message: str) -> None:  # WHY: closure shared by all callers in a session.
            """Sanitise then persist one log message to the per-host file."""
            _write_clean_line(message, host_log_file, logger)  # WHY: delegate to module-level helper.

        return write_to_host_log  # WHY: hand the sanitising writer to the caller.

    # ------------------------------------------------------------------
    # Session orchestration (connect -> shell -> step loop -> cleanup)
    # ------------------------------------------------------------------
    @staticmethod
    def _execute_session(  # WHY: end-to-end session runner (connect -> steps -> status).
        request: InteractiveSessionRequest,
        log_ctx: _LogContext,
        logger: logging.Logger,
    ) -> bool:
        """Open connection + shell, run all steps, write final status; return success bool."""
        shell = InteractiveBatchExecutor._connect_and_open_shell(request, log_ctx, logger)  # WHY: real connect.
        if shell is None:  # WHY: connection or shell setup failed (already logged by helper).
            return False
        log_ctx.writer(  # WHY: verbatim status line before the step loop.
            f"\n>> Starting interactive session with {len(request.commands)} steps..."
        )
        overall_success = InteractiveBatchExecutor._iterate_steps(  # WHY: walk scripted step list.
            shell, request.hostname, list(request.commands), log_ctx.writer, logger
        )
        InteractiveBatchExecutor._cleanup_shell(shell, request.hostname, logger)  # WHY: best-effort teardown.
        InteractiveBatchExecutor._write_final_status(  # WHY: verbatim [OK]/[WARNING] block.
            log_ctx.writer, overall_success, request.hostname, len(request.commands), logger
        )
        return overall_success

    @staticmethod
    def _connect_and_open_shell(
        request: InteractiveSessionRequest,
        log_ctx: _LogContext,
        logger: logging.Logger,
    ) -> Any | None:
        """Connect via SshConnector, open a persistent shell channel, capture initial prompt."""
        client = InteractiveBatchExecutor._connect_client(request, log_ctx, logger)  # WHY: real connect step.
        if client is None:  # WHY: connection failed - already logged by helper.
            return None
        if not request.use_shell:  # WHY: interactive mode requires shell=True (verbatim warn).
            logger.warning("Interactive mode requires shell=True, enabling shell mode")
        shell = client.invoke_shell(term="vt100", width=_TERM_WIDTH, height=_TERM_HEIGHT)  # WHY: PTY shell.
        shell.settimeout(request.timeout)  # WHY: apply session timeout to the shell channel.
        time.sleep(_INIT_PROMPT_WAIT)  # WHY: give device a moment to print its initial prompt.
        InteractiveBatchExecutor._drain_initial_prompt(shell, log_ctx.writer, logger)  # WHY: capture prompt.
        return shell

    @staticmethod
    def _connect_client(
        request: InteractiveSessionRequest,
        log_ctx: _LogContext,
        logger: logging.Logger,
    ) -> Any | None:
        """Run SshConnector.connect and wire the client into the runner; return client or None."""
        logger.info(  # WHY: session-connect line preserved for log parity.
            "Connecting via SshConnector for interactive session to %s:%s", request.hostname, request.port
        )
        connector = SshConnector(timeout=log_ctx.runner.timeout, logger=logger)  # WHY: real connector (no facade).
        client, kh_path = connector.connect(  # WHY: real connect; failures return (None, None).
            request.hostname, request.username, request.password, request.port
        )
        logger.debug("Interactive connect returned client=%s", bool(client))  # WHY: debug diag.
        if client is None:  # WHY: connection failed - connector already logged + printed.
            logger.error("SSH connection failed: %s:%s", request.hostname, request.port)  # WHY: log parity.
            log_ctx.writer(f"[ERROR] Failed to connect to {request.hostname}")  # WHY: verbatim error line.
            return None
        log_ctx.runner.client = client  # WHY: wire the live client into the runner instance.
        log_ctx.runner.managed_known_hosts_path = kh_path  # WHY: preserve TOFU path for later save.
        logger.debug("SSH connected to %s, starting interactive session", request.hostname)  # WHY: parity.
        return client

    @staticmethod
    def _drain_initial_prompt(shell: Any, writer: Callable[[str], None], logger: logging.Logger) -> None:
        """Capture the initial device prompt (if any) and write it to the per-host log."""
        if not shell.recv_ready():  # WHY: nothing to drain - device produced no banner.
            return
        initial_output = shell.recv(_RECV_BUFFER).decode("utf-8", errors="ignore")  # WHY: safe decode.
        writer(f"[OUTPUT] INITIAL PROMPT:\n{initial_output}")  # WHY: verbatim log block.
        logger.debug("Initial shell prompt received")  # WHY: parity debug line.

    # ------------------------------------------------------------------
    # Step iteration
    # ------------------------------------------------------------------
    @staticmethod
    def _iterate_steps(
        shell: Any,
        hostname: str,
        commands: list[str],
        writer: Callable[[str], None],
        logger: logging.Logger,
    ) -> bool:
        """Walk the step list; return overall success bool. Each step is one helper call."""
        overall_success = True  # WHY: flipped to False on any failed step or interrupt.
        total = len(commands)  # WHY: total step count cached for the loop guard + pause helper.
        command_index = 0  # WHY: manual index because blank entries are skipped by helper.
        while command_index < total:  # WHY: hand-rolled loop keeps parity with original behaviour.
            step_ctx = InteractiveBatchExecutor._build_step_context(hostname, commands, command_index, total)
            command_index += 1  # WHY: always advance so blank entries don't loop forever.
            if step_ctx is None:  # WHY: helper returned None to signal a blank-line skip (no pause).
                continue
            result = InteractiveBatchExecutor._maybe_run_step(shell, step_ctx, writer, logger)  # WHY: run step.
            overall_success = overall_success and result.step_ok  # WHY: latch first failure into overall.
            if result.stop:  # WHY: interrupt/exception halts remaining steps (verbatim behaviour).
                break
            InteractiveBatchExecutor._apply_step_pause(result.pause, command_index, total)  # WHY: pause helper.
        return overall_success

    @staticmethod
    def _build_step_context(
        hostname: str,
        commands: list[str],
        command_index: int,
        total: int,
    ) -> _StepContext | None:
        """Return a per-step context for non-blank entries; None signals a blank-line skip."""
        current_item = commands[command_index].strip()  # WHY: strip once so downstream code is simple.
        if not current_item:  # WHY: skip blank entries (verbatim behaviour) - no pause needed.
            return None
        return _StepContext(  # WHY: bundle keeps helper signatures small (<=5 params).
            hostname=hostname, command=current_item, step_num=command_index + 1, total=total
        )

    @staticmethod
    def _apply_step_pause(pause: bool, command_index: int, total: int) -> None:
        """Sleep the verbatim inter-step stability pause when the caller requested it."""
        if pause and command_index < total:  # WHY: skip pause when the loop is about to exit.
            time.sleep(_STEP_STABILITY_PAUSE)

    @staticmethod
    def _maybe_run_step(
        shell: Any,
        step_ctx: _StepContext,
        writer: Callable[[str], None],
        logger: logging.Logger,
    ) -> _StepResult:
        """Run one step and return the (stop, step_ok, pause) tuple as a _StepResult."""
        stop, step_ok = InteractiveBatchExecutor._safe_run_step(shell, step_ctx, writer, logger)  # WHY: guarded.
        return _StepResult(stop=stop, step_ok=step_ok, pause=True)

    @staticmethod
    def _safe_run_step(
        shell: Any,
        step_ctx: _StepContext,
        writer: Callable[[str], None],
        logger: logging.Logger,
    ) -> tuple[bool, bool]:
        """Run one step; return (stop_flag, step_success). Handles Ctrl+C + step exceptions."""
        try:
            step_ok = InteractiveBatchExecutor._run_one_step(shell, step_ctx, writer, logger)  # WHY: run step.
            return False, step_ok
        except KeyboardInterrupt:  # WHY: Ctrl+C halts remaining steps (verbatim UX).
            InteractiveBatchExecutor._handle_step_interrupt(step_ctx, writer, logger)  # WHY: verbatim logs.
            return True, False
        except Exception as step_error:  # noqa: BLE001 - per-step fallback (verbatim)
            InteractiveBatchExecutor._handle_step_exception(step_ctx, step_error, writer, logger)  # WHY: log.
            return True, False

    @staticmethod
    def _handle_step_interrupt(
        step_ctx: _StepContext,
        writer: Callable[[str], None],
        logger: logging.Logger,
    ) -> None:
        """Emit the verbatim Ctrl+C interrupt lines (console + logger + per-host log)."""
        print(  # WHY: verbatim console interrupt line.
            f"\n[INTERRUPT] [{step_ctx.hostname}] Ctrl+C detected! Stopping interactive session..."
        )
        logger.warning(  # WHY: log parity for interrupt event.
            "Interactive session interrupted by user at step %d", step_ctx.step_num
        )
        writer(f"\n[INTERRUPT] Session interrupted by user at step {step_ctx.step_num}")  # WHY: verbatim.

    @staticmethod
    def _handle_step_exception(
        step_ctx: _StepContext,
        step_error: BaseException,
        writer: Callable[[str], None],
        logger: logging.Logger,
    ) -> None:
        """Emit the verbatim per-step exception lines (logger + per-host log)."""
        logger.error(  # WHY: verbatim per-step error line preserving type + message.
            "[%s] Error at step %d: %s: %s",
            step_ctx.hostname,
            step_ctx.step_num,
            type(step_error).__name__,
            step_error,
        )
        writer(f"[ERROR] Step {step_ctx.step_num} error: {step_error}")  # WHY: verbatim log line.

    @staticmethod
    def _run_one_step(
        shell: Any,
        step_ctx: _StepContext,
        writer: Callable[[str], None],
        logger: logging.Logger,
    ) -> bool:
        """Send one command/response, capture reply, log block; return step success bool."""
        InteractiveBatchExecutor._write_step_header(step_ctx, writer, logger)  # WHY: verbatim header block.
        shell.send((step_ctx.command + "\n").encode("utf-8"))  # WHY: send the command/response line.
        time.sleep(_STEP_SEND_PAUSE)  # WHY: brief pause so device registers input (verbatim).
        response_output = InteractiveBatchExecutor._wait_for_response(shell, step_ctx.hostname, logger)
        InteractiveBatchExecutor._log_step_response(step_ctx, response_output, writer, logger)  # WHY: log block.
        step_success = InteractiveBatchExecutor._check_step_success(  # WHY: scan for failure indicators.
            response_output, step_ctx.hostname, step_ctx.step_num, logger
        )
        if step_success:  # WHY: verbatim [OK] line.
            writer(f"[OK] Step {step_ctx.step_num} completed successfully")
            logger.debug("[%s] Step %d completed successfully", step_ctx.hostname, step_ctx.step_num)
        else:  # WHY: verbatim [ERROR] line.
            writer(f"[ERROR] Step {step_ctx.step_num} failed")
        return step_success

    @staticmethod
    def _write_step_header(
        step_ctx: _StepContext,
        writer: Callable[[str], None],
        logger: logging.Logger,
    ) -> None:
        """Write the [STEP] header block and echo a redacted status line to the console."""
        writer(f"\n{_STEP_BAR}")  # WHY: verbatim step separator.
        writer(f"[STEP] Step {step_ctx.step_num}/{step_ctx.total}: {step_ctx.command}")  # WHY: verbatim.
        writer(_STEP_BAR)  # WHY: closing bar (verbatim).
        display_item = InteractiveBatchExecutor._redact_for_display(step_ctx.command)  # WHY: mask pwd.
        print(f"* [{step_ctx.hostname}] Executing step {step_ctx.step_num}: {display_item}")  # WHY: parity.
        logger.debug("[%s] Sending: %s", step_ctx.hostname, step_ctx.command)  # WHY: debug diag line.

    @staticmethod
    def _log_step_response(
        step_ctx: _StepContext,
        response_output: str,
        writer: Callable[[str], None],
        logger: logging.Logger,
    ) -> None:
        """Write the response block (or the no-output marker) to the per-host log."""
        if response_output.strip():  # WHY: log response block only when non-empty (verbatim).
            writer("[OUTPUT] RESPONSE:")
            writer(response_output)
            logger.debug("[%s] Response received: %d chars", step_ctx.hostname, len(response_output))
        else:  # WHY: verbatim no-response marker.
            writer("[STATUS] No response output")
            logger.debug("[%s] No response output received", step_ctx.hostname)

    @staticmethod
    def _redact_for_display(current_item: str) -> str:
        """Return ``current_item`` masked when it looks like a password value."""
        lowered = current_item.lower()  # WHY: case-insensitive hint match.
        looks_like_pw = any(hint in lowered for hint in _PASSWORD_HINTS)  # WHY: substring check.
        if looks_like_pw and len(current_item) > _PW_MIN_MASK_LEN:  # WHY: threshold from original.
            return "*" * len(current_item)  # WHY: fully mask password-like items in console output.
        return current_item

    # ------------------------------------------------------------------
    # Response-wait loop (drain shell until prompt appears or times out)
    # ------------------------------------------------------------------
    @staticmethod
    def _wait_for_response(shell: Any, hostname: str, logger: logging.Logger) -> str:
        """Drain the shell until a prompt appears or no data arrives for the timeout window."""
        response_output = ""  # WHY: accumulated decoded bytes from the shell channel.
        last_data_time = time.time()  # WHY: reset whenever new data arrives.
        total_wait = 0.0  # WHY: cumulative polling time (capped by _MAX_WAIT_SECONDS).
        while total_wait < _MAX_WAIT_SECONDS:
            response_output, last_data_time, should_stop = InteractiveBatchExecutor._poll_once(
                shell, hostname, response_output, last_data_time, logger
            )
            if should_stop:  # WHY: password prompt / quiet prompt / no-data timeout ended the wait.
                break
            time.sleep(_WAIT_INCREMENT)  # WHY: verbatim polling interval.
            total_wait += _WAIT_INCREMENT  # WHY: advance the wait-clock counter.
        return response_output

    @staticmethod
    def _poll_once(
        shell: Any,
        hostname: str,
        response_output: str,
        last_data_time: float,
        logger: logging.Logger,
    ) -> tuple[str, float, bool]:
        """Read one chunk (if ready) and return (updated_output, last_data_time, should_stop)."""
        if shell.recv_ready():  # WHY: new bytes are available on the channel.
            chunk = shell.recv(_RECV_BUFFER).decode("utf-8", errors="ignore")  # WHY: safe decode.
            response_output += chunk  # WHY: accumulate for prompt scan + caller return.
            last_data_time = time.time()  # WHY: reset the no-data timer.
            stop = InteractiveBatchExecutor._prompt_ended_wait(response_output, last_data_time, hostname, logger)
            return response_output, last_data_time, stop
        if (time.time() - last_data_time) >= _NO_DATA_TIMEOUT:  # WHY: no new data for the bail-out window.
            return response_output, last_data_time, True
        return response_output, last_data_time, False

    @staticmethod
    def _prompt_ended_wait(
        response_output: str,
        last_data_time: float,
        hostname: str,
        logger: logging.Logger,
    ) -> bool:
        """Return True when the accumulated output ends in a password prompt or quiet prompt."""
        lowered = response_output.lower()  # WHY: case-insensitive prompt match.
        if any(prompt in lowered for prompt in _PASSWORD_PROMPTS):  # WHY: caller sends the pw response next.
            logger.debug("[%s] Password prompt detected", hostname)
            return True
        tail = response_output[-_PROMPT_TAIL_LEN:]  # WHY: only scan the trailing chars for prompt patterns.
        if any(pattern in tail for pattern in _PROMPT_PATTERNS):  # WHY: prompt suffix seen.
            return (time.time() - last_data_time) > _PROMPT_QUIET_SECS  # WHY: verbatim quiet-window rule.
        return False

    @staticmethod
    def _check_step_success(
        response_output: str,
        hostname: str,
        step_num: int,
        logger: logging.Logger,
    ) -> bool:
        """Return False when the response contains a known failure indicator."""
        lowered = response_output.lower()  # WHY: canonical case for substring match.
        for needle, label in _FAILURE_PATTERNS:  # WHY: iterate canonical failure substrings.
            if needle in lowered:  # WHY: presence of any failure needle marks the step as failed.
                logger.warning("[%s] Step %d failed: %s", hostname, step_num, label)  # WHY: log parity.
                return False
        return True

    # ------------------------------------------------------------------
    # Cleanup + final status + footer
    # ------------------------------------------------------------------
    @staticmethod
    def _cleanup_shell(shell: Any, hostname: str, logger: logging.Logger) -> None:
        """Best-effort graceful close of the shell channel (verbatim behaviour)."""
        try:
            shell.send(b"exit\n")  # WHY: send a clean exit (mirrors interactive terminal behaviour).
            time.sleep(_SHELL_EXIT_PAUSE)  # WHY: give the device a moment to process the exit.
            shell.close()  # WHY: release the paramiko shell channel.
            logger.debug("[%s] Interactive shell closed gracefully", hostname)  # WHY: parity debug.
        except Exception as cleanup_error:  # noqa: BLE001 - cleanup is best-effort (verbatim)
            logger.debug("[%s] Shell cleanup warning: %s", hostname, cleanup_error)  # WHY: parity debug.

    @staticmethod
    def _write_final_status(
        writer: Callable[[str], None],
        overall_success: bool,
        hostname: str,
        total: int,
        logger: logging.Logger,
    ) -> None:
        """Write the final-status block to the per-host log (verbatim text)."""
        if overall_success:  # WHY: verbatim [OK] all-succeeded line.
            logger.info("[%s] All %d interactive steps completed successfully", hostname, total)
            writer("[OK] All interactive steps completed successfully")
        else:  # WHY: verbatim [WARNING] some-failed line.
            logger.warning("[%s] Some interactive steps failed", hostname)
            writer("[WARNING] Some interactive steps failed - check output above")

    @staticmethod
    def _write_footer(
        writer: Callable[[str], None],
        overall_success: bool,
        host_log_file: str,
        logger: logging.Logger,
    ) -> None:
        """Write the session footer; fall back to a minimal footer on any error."""
        try:
            writer(_build_footer_text(overall_success, host_log_file))  # WHY: verbatim footer block.
        except Exception as footer_error:  # noqa: BLE001 - footer is best-effort (verbatim)
            InteractiveBatchExecutor._write_simple_footer(writer, footer_error, logger)  # WHY: fallback path.

    @staticmethod
    def _write_simple_footer(
        writer: Callable[[str], None],
        footer_error: BaseException,
        logger: logging.Logger,
    ) -> None:
        """Log the footer error and emit a one-line simple footer (last-resort path)."""
        logger.error(  # WHY: verbatim footer-error line preserving type + message.
            "Error in interactive session footer generation: %s: %s",
            type(footer_error).__name__,
            footer_error,
        )
        try:
            simple_footer = f"Session completed at {datetime.now().strftime(_TS_FMT_HUMAN)}"  # WHY: parity.
            writer(simple_footer)  # WHY: best-effort persistence of the minimal footer.
        except Exception as fallback_error:  # noqa: BLE001 - last-resort path (verbatim)
            logger.error("Even simple interactive footer failed: %s", fallback_error)  # WHY: log parity.
