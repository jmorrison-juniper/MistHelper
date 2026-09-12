"""ShellExecutor - interactive-shell command execution over an existing SSH client.

Extracted from ``EnhancedSSHRunner._execute_with_shell`` (CC=51, F) per T013b of
specs/198-radon-complexity-decomposition. The monolithic original is replaced by
a class whose every method has cyclomatic complexity <= 8, organized around the
five phases of an interactive-shell command execution:

1. ``_open_shell``               - invoke a PTY, drain the initial prompt
2. ``_send_command``             - write the command, return error tuple on send failure
3. ``_wait_for_command_start``   - wait briefly for the device to begin producing output
4. ``_collect_output``           - main data-collection loop with timeout/limits/Ctrl+C
5. ``_drain_excess``             - drain remaining bytes after output cap reached
6. ``_cleanup_shell``            - send ``exit`` and close the channel
7. ``_clean_output_lines``       - strip prompts, ANSI codes, shell artifacts
8. ``_evaluate_success``         - classify the cleaned output as success/failure

All user-facing strings (status lines, ``[TIMEOUT]``, ``[OK]``, ``[STATUS]``,
``X  [host]`` markers) are preserved verbatim from the original implementation.
"""

from __future__ import annotations  # WHY: PEP 563 postponed annotations for forward Any typing

import logging  # WHY: Structured logging for the new shell-execution module
import re  # WHY: Output cleaning regexes
import time  # WHY: Timing for output loops, cleanup, total duration
from dataclasses import dataclass  # WHY: Frozen slotted state bundle keeps _collect_output CC low
from typing import Any  # WHY: paramiko Channel type is dynamic across paramiko versions

from src.utils.console import echo  # WHY: spec 1031 console echo keeps stdout text and drops the WARNING level.

logger = logging.getLogger(__name__)  # WHY: Module-scoped logger for the drain-progress staticmethod

# Module-level constants - extracted so each method's CC stays low (no magic numbers in branches)
_INITIAL_PROMPT_MAX_WAIT_S = 3.0  # WHY: Max seconds to wait for initial shell prompt
_WAIT_INCREMENT_S = 0.2  # WHY: Polling interval while waiting for shell events
_CMD_START_MAX_WAIT_S = 6.0  # WHY: Max seconds to wait for command to begin producing output
_NO_DATA_TIMEOUT_S = 3.0  # WHY: Seconds of silence after which we consider the command finished
_TOTAL_MAX_WAIT_S = 120.0  # WHY: Hard overall ceiling per command (2 minutes)
_HANG_DETECTION_S = 90.0  # WHY: Threshold for forced-completion "hang detected" message
_MAX_OUTPUT_BYTES = 100 * 1024 * 1024  # WHY: 100 MB output cap before draining excess
_RECV_CHUNK_BYTES = 131072  # WHY: 128 KB chunks from the channel for efficiency
_DRAIN_CHUNK_BYTES = 262144  # WHY: 256 KB chunks while draining excess data
_DRAIN_MAX_S = 30.0  # WHY: Max seconds to drain excess data after cap reached
_CLEANUP_MAX_S = 2.0  # WHY: Max seconds to spend on post-command cleanup
_PROGRESS_INTERVAL_CHUNKS = 100  # WHY: Log progress every N chunks for large outputs
_LONG_RUNNING_THRESHOLD_S = 30.0  # WHY: After this many seconds, print periodic "still running" progress
_LONG_RUNNING_CADENCE_CHUNKS = 150  # WHY: Cadence (in chunks) of long-running progress prints
_POLL_SLEEP_S = 0.05  # WHY: Brief poll sleep when no bytes are ready
_READ_SLEEP_S = 0.01  # WHY: Tiny pause between reads when not truncating
_SEND_SETTLE_S = 0.1  # WHY: Delay after send so the device can buffer the full command line
_CLEANUP_LOG_THRESHOLD_S = 1.0  # WHY: Only log cleanup duration when it exceeds this
_LARGE_OUTPUT_LOG_LIMIT = 10000  # WHY: Log a full sample for outputs smaller than this many chars
_OUTPUT_SAMPLE_CHARS = 200  # WHY: Sample size when logging cleaned output
_INITIAL_SAMPLE_CHARS = 100  # WHY: Sample size when logging drained initial prompt
_LARGE_OUTPUT_PRINT_MB = 5.0  # WHY: Only print "receiving large output" for outputs above this size
_INITIAL_DRAIN_BUFFER = 4096  # WHY: Buffer size for initial-prompt / cleanup-tail drains
_CLEANUP_TAIL_SLEEP_S = 0.1  # WHY: Cleanup-tail poll cadence and post-drain pause
_MB_DIVISOR = 1024 * 1024  # WHY: Bytes-to-megabytes conversion factor
_NO_ACTIVE_CONNECTION_MSG = "No active SSH connection"  # WHY: shared guard message, issue #1720
_SHELL_ARTIFACTS: tuple[str, ...] = (  # WHY: Substrings (case-insensitive) that mark filterable shell noise
    "exit",
    "logout",
    "Connection to",
    "Last login:",
    "Welcome to",
    "Match except:",
    "---(more)---",
    "No next tag",
    "press RETURN",
    "Invalid command:",
    "xit",
    "vyos@vyos:~$",
    "Connection closed",
)
_SHELL_PROMPT_PATTERNS: tuple[str, ...] = (  # WHY: Regexes that identify shell prompts to strip
    r".*[$#>]\s*$",
    r"vyos@.*[$#>]\s*$",
    r".*@.*:.*[$#>]\s*$",
    r"{master:\d+}",
    r"^\s*$",
    r":+.*\[.*\d+;\d+.*H.*",
    r"^:.*press RETURN.*",
    r"^>vyos@.*\$ xit$",
    r"^vyos@.*:~\$.*xit$",
    r"^Invalid command: \[xit\]$",
    r"^.*Connection to .* closed\.$",
    r"^\s*xit\s*$",
)
_VYOS_ARTIFACT_PATTERNS: tuple[str, ...] = (  # WHY: VyOS-specific noise lines stripped after ANSI removal
    r"^\s*xit\s*$",
    r"^Invalid command: \[xit\]$",
    r"^vyos@.*:~\$",
    r"^Connection.*closed\.$",
)
_ERROR_PATTERNS: tuple[str, ...] = (  # WHY: Substrings that indicate a real command failure
    "command not found",
    "syntax error",
    "permission denied",
    "authentication failed",
    "connection refused",
    "host unreachable",
    "network unreachable",
    "no such file or directory",
)
_SHELL_CLEANUP_INDICATORS: tuple[str, ...] = (  # WHY: Substrings that look like errors but are cleanup noise
    "invalid command: [xit]",
    "unknown command: xit",
    "invalid command: exit",
    "connection to .* closed",
)
_ANSI_COLOR_RE = re.compile(r"\x1b\[[0-9;]*[mK]")  # WHY: ANSI color/erase escape sequence pattern
_ANSI_MODE_RE = re.compile(r"\x1b\[\?[0-9]+[hl]")  # WHY: ANSI mode-change escape sequence pattern
_ANSI_CURSOR_RE = re.compile(r"\x1b\[[0-9]+;[0-9]+H")  # WHY: ANSI cursor-positioning escape sequence pattern
_TRAILING_COLON_RE = re.compile(r":\s*$")  # WHY: Trailing pager colon that must be stripped


@dataclass(frozen=True, slots=True)
class _CollectContext:
    """Immutable bundle threaded through the output-collection loop (shrinks _collect_output CC)."""

    command: str  # WHY: Command string used for log context and hang messages
    start_time: float  # WHY: Wall-clock start used for total-timeout / hang detection
    hostname: str  # WHY: Host label included in printed status lines


@dataclass(slots=True)
class _CollectState:
    """Mutable per-iteration state for the output-collection loop."""

    output: str = ""  # WHY: Accumulated raw bytes decoded as UTF-8
    last_data_time: float = 0.0  # WHY: When we last saw bytes (resets after each chunk)
    chunk_count: int = 0  # WHY: Total chunks read - drives progress logging cadence
    truncated: bool = False  # WHY: True once the output cap has been hit


class ShellExecutor:
    """Run one command over an interactive paramiko shell with PTY semantics.

    Construct with an already-connected SSH client, then call :meth:`execute`.
    The class does NOT own the SSH connection lifecycle - callers (typically
    ``EnhancedSSHRunner._execute_command`` or ``SingleCommandRunner``) must open
    and close the underlying client themselves.
    """

    def __init__(
        self, client: Any, timeout: int = 30, logger: logging.Logger | None = None
    ) -> None:  # WHY: Bind SSH client and per-command timeout for later phases
        """Capture the live SSH client, command timeout, and logger."""
        self.client = client  # WHY: paramiko SSHClient - must already be connected
        self.timeout = timeout  # WHY: Per-command socket timeout
        self.logger = logger or logging.getLogger("ssh_runner_v2")  # WHY: Reuse the unified SSH logger

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------
    def execute(
        self, command: str, start_time: float, hostname: str = "unknown"
    ) -> tuple[bool, str, str]:  # WHY: Public entry orchestrates every phase of shell execution
        """Execute ``command`` over an interactive shell and return ``(success, stdout, stderr)``."""
        if self.client is None:  # WHY: a runtime guard must survive python -O, issue #1720
            raise ValueError(_NO_ACTIVE_CONNECTION_MSG)  # WHY: reject a call made without a live client
        self.logger.info(
            "ShellExecutor: starting interactive shell command on %s", hostname
        )  # WHY: Diagnostic breadcrumb for host-scoped log filtering
        try:
            return self._run_phases(
                command, start_time, hostname
            )  # WHY: Delegate the phase pipeline to a bounded helper
        except Exception as shell_error:  # WHY: Top-level fallback mirrors original behavior
            # WHY: Any escape from the pipeline surfaces as the documented failure tuple
            err_type = type(shell_error).__name__  # WHY: Class name only for concise error phrasing
            error_msg = f"Shell execution error: {err_type}: {shell_error}"  # WHY: Preserve original phrasing
            self.logger.exception(error_msg)  # WHY: Include traceback for post-mortem debugging
            return False, "", error_msg  # WHY: Documented failure-tuple shape

    def _run_phases(
        self, command: str, start_time: float, hostname: str
    ) -> tuple[bool, str, str]:  # WHY: Sequences phases 1-8 with early-return on send failure
        """Run phases 1-8 of shell execution and return the result tuple."""
        shell = self._open_shell()  # WHY: Phase 1: open PTY, drain prompt
        send_error = self._send_command(shell, command)  # WHY: Phase 2: write command line
        if send_error is not None:  # WHY: Guard clause - send failed, return error tuple immediately
            return send_error
        self._wait_for_command_start(shell)  # WHY: Phase 3: brief wait for first response bytes
        context = _CollectContext(
            command=command, start_time=start_time, hostname=hostname
        )  # WHY: Frozen bundle for phase 4/5 helpers
        output = self._collect_output(shell, context)  # WHY: Phase 4: main read loop
        self._cleanup_shell(shell, hostname)  # WHY: Phase 6: send exit + close channel
        cleaned_output = self._clean_output_lines(output, command)  # WHY: Phase 7: strip prompts/artifacts
        self._log_output_summary(cleaned_output, start_time)  # WHY: Diagnostic logging only
        success = self._evaluate_success(cleaned_output)  # WHY: Phase 8: classify as success/failure
        command_time = time.time() - start_time  # WHY: Final wall-clock duration
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        self.logger.info("[STATUS] [%s] Command completed in %.2f seconds", hostname, command_time)
        self.logger.debug(
            "ShellExecutor: command completed on %s in %.2fs", hostname, command_time
        )  # WHY: Duration breadcrumb
        return success, cleaned_output, ""  # WHY: Documented success tuple

    # ------------------------------------------------------------------
    # Phase 1: open shell + initial prompt drain
    # ------------------------------------------------------------------
    def _open_shell(self) -> Any:  # WHY: Encapsulates PTY invocation and initial prompt drain
        """Invoke a PTY shell, set socket timeout, and drain the initial prompt."""
        self.logger.debug("Using interactive shell mode")  # WHY: Trace which execution mode we chose
        shell = self.client.invoke_shell(term="vt100", width=120, height=24)  # WHY: Standard VT100 sizing
        shell.settimeout(self.timeout)  # WHY: Per-recv socket timeout
        self._drain_initial_prompt(shell)  # WHY: Best-effort prompt drain (failure here is non-fatal)
        return shell  # WHY: Hand back the ready channel

    def _drain_initial_prompt(self, shell: Any) -> None:  # WHY: Wait up to the configured cap for prompt bytes
        """Wait up to ``_INITIAL_PROMPT_MAX_WAIT_S`` for the initial prompt and discard it."""
        total_wait = 0.0  # WHY: Accumulated wait time
        while total_wait < _INITIAL_PROMPT_MAX_WAIT_S:  # WHY: Bounded polling loop
            time.sleep(_WAIT_INCREMENT_S)  # WHY: Wait one polling interval
            total_wait += _WAIT_INCREMENT_S  # WHY: Track progress against the cap
            if shell.recv_ready():  # WHY: Initial bytes available - drain and exit loop
                initial_output = shell.recv(_INITIAL_DRAIN_BUFFER).decode(
                    "utf-8", errors="ignore"
                )  # WHY: Discard prompt bytes
                initial_sample = _escape_sample(
                    initial_output[:_INITIAL_SAMPLE_CHARS]
                )  # WHY: Escape for single-line log rendering
                self.logger.debug("Initial shell output: %s...", initial_sample)  # WHY: Trace prompt content
                return

    # ------------------------------------------------------------------
    # Phase 2: send command
    # ------------------------------------------------------------------
    def _send_command(
        self, shell: Any, command: str
    ) -> tuple[bool, str, str] | None:  # WHY: Write command + return error tuple on failure
        r"""Send ``command\n`` to the shell. Return an error tuple on failure, ``None`` on success."""
        try:
            command_with_newline = command + "\n"  # WHY: Newline triggers command execution
            shell.send(command_with_newline.encode("utf-8"))  # WHY: Byte-level write to channel
            time.sleep(_SEND_SETTLE_S)  # WHY: Small delay so the device has time to buffer the full line
            self.logger.debug("Sent command to shell: %s", command)  # WHY: Trace outbound command
            return None  # WHY: Caller proceeds with phases 3+
        # WHY: a blanket except keeps the compatibility of the returned tuple,
        # because any send failure mirrors the original handling.
        except Exception as send_error:
            self.logger.warning("Error sending command: %s", send_error)  # WHY: Log root cause for debugging
            return False, "", f"Failed to send command: {send_error}"  # WHY: Documented failure tuple

    # ------------------------------------------------------------------
    # Phase 3: wait for command to start producing output
    # ------------------------------------------------------------------
    def _wait_for_command_start(self, shell: Any) -> None:  # WHY: Bounded poll waiting for first response bytes
        """Wait up to ``_CMD_START_MAX_WAIT_S`` for the channel to indicate readable bytes."""
        cmd_wait = 0.0  # WHY: Accumulated wait time
        while cmd_wait < _CMD_START_MAX_WAIT_S:  # WHY: Bounded wait - device may take a moment
            time.sleep(_WAIT_INCREMENT_S)  # WHY: Poll interval
            cmd_wait += _WAIT_INCREMENT_S  # WHY: Track progress against cap
            if shell.recv_ready():  # WHY: Device has begun responding
                return

    # ------------------------------------------------------------------
    # Phase 4: main output-collection loop (decomposed to keep CC <= 5)
    # ------------------------------------------------------------------
    def _collect_output(
        self, shell: Any, context: _CollectContext
    ) -> str:  # WHY: Top-level read loop delegating each step to a helper
        """Run the main read loop, returning the accumulated raw output string."""
        self.logger.info(
            "ShellExecutor: collecting output for %s on %s", context.command[:40], context.hostname
        )  # WHY: Trace which command we are reading
        state = _CollectState(last_data_time=time.time())  # WHY: Fresh mutable state bundle for this run
        try:
            self._run_collect_loop(shell, context, state)  # WHY: Bounded loop lives in a helper to keep CC low
        except KeyboardInterrupt:  # WHY: Operator interrupted - preserve partial output
            self._handle_interrupt(state, context)  # WHY: Emit warning + append interrupted marker
        return state.output  # WHY: Accumulated bytes returned to caller

    def _run_collect_loop(
        self, shell: Any, context: _CollectContext, state: _CollectState
    ) -> None:  # WHY: Bounded wall-clock loop delegating each iteration to a helper
        """Drive the bounded read loop until timeout, silence, hang, or truncation."""
        while (time.time() - context.start_time) < _TOTAL_MAX_WAIT_S:  # WHY: Hard total ceiling
            if self._loop_step(shell, context, state):  # WHY: Iteration returns True when the loop should exit
                return

    def _loop_step(
        self, shell: Any, context: _CollectContext, state: _CollectState
    ) -> bool:  # WHY: One loop iteration - returns True when the loop should exit
        """Perform one iteration of the collect loop. Return True when the loop should terminate."""
        if self._detect_hang(state, context):  # WHY: 90s "hang" forced-completion appends marker and exits
            return True
        self._maybe_print_long_running_progress(
            context.start_time, state.chunk_count, context.hostname
        )  # WHY: Periodic UX progress line
        if not shell.recv_ready():  # WHY: No bytes ready - defer to silence-vs-poll helper
            return self._await_bytes_or_finish(state)
        self._read_one_chunk(shell, state, context.hostname)  # WHY: Bytes available - read one chunk into state
        if state.truncated:  # WHY: Output cap hit - drain remainder + exit loop
            self._drain_excess(shell, state.last_data_time, context.hostname)
            return True
        return False

    def _await_bytes_or_finish(
        self, state: _CollectState
    ) -> bool:  # WHY: Idle branch - return True when silence deadline reached
        """Return True when silence has exceeded ``_NO_DATA_TIMEOUT_S``. Else sleep briefly and return False."""
        if self._silence_exceeded(state.last_data_time):  # WHY: Silence threshold reached - command considered finished
            return True
        time.sleep(_POLL_SLEEP_S)  # WHY: Brief sleep before next poll
        return False

    def _detect_hang(
        self, state: _CollectState, context: _CollectContext
    ) -> bool:  # WHY: Isolates hang-message side effect from loop body
        """Return True and append the timeout marker when the hang threshold is exceeded."""
        if not self._handle_hang_detection(
            context.start_time, context.command, context.hostname
        ):  # WHY: Delegate detection to reused helper
            return False
        elapsed = time.time() - context.start_time  # WHY: Duration used in the appended marker
        state.output += (
            f"\n\n[COMMAND TIMEOUT - Forced completion after {elapsed:.0f}s]\n"  # WHY: Verbatim timeout marker
        )
        return True

    @staticmethod
    def _silence_exceeded(last_data_time: float) -> bool:  # WHY: Pure predicate reused inside the loop
        """Return True when no bytes have arrived within ``_NO_DATA_TIMEOUT_S``."""
        return (
            time.time() - last_data_time
        ) >= _NO_DATA_TIMEOUT_S  # WHY: Silence threshold reached - command considered finished

    def _handle_interrupt(
        self, state: _CollectState, context: _CollectContext
    ) -> None:  # WHY: Keep KeyboardInterrupt bookkeeping out of the loop
        """Record the interrupt marker on ``state`` and emit the operator-facing status line."""
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        self.logger.warning("X  [%s] Ctrl+C detected! Interrupting command: %s", context.hostname, context.command)
        self.logger.warning("Command interrupted by user: %s", context.command)  # WHY: Log for post-mortem
        # WHY: Marker preserved verbatim so downstream log parity is unaffected
        state.output += "\n\n[COMMAND INTERRUPTED BY USER - Ctrl+C pressed during data collection]\n"

    def _handle_hang_detection(
        self, start_time: float, command: str, hostname: str
    ) -> bool:  # WHY: Detects the 90s forced-completion threshold
        """Return True if the command has exceeded the hang threshold (forces caller to break)."""
        current_duration = time.time() - start_time  # WHY: Wall-clock elapsed
        if current_duration <= _HANG_DETECTION_S:  # WHY: Guard clause - not yet at threshold
            return False
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        self.logger.warning(
            "[TIMEOUT] [%s] HANG DETECTED: Command running for %.0fs, forcing completion",
            hostname,
            current_duration,
        )
        self.logger.warning(
            "Command hang detected after %.0fs, forcing completion: %s", current_duration, command
        )  # WHY: Log for post-mortem
        return True

    def _maybe_print_long_running_progress(
        self, start_time: float, chunk_count: int, hostname: str
    ) -> None:  # WHY: Periodic "still running" status print
        """Every 150 chunks after 30s elapsed, print a "still running" status line."""
        current_duration = time.time() - start_time  # WHY: Wall-clock elapsed
        if (
            current_duration > _LONG_RUNNING_THRESHOLD_S and chunk_count % _LONG_RUNNING_CADENCE_CHUNKS == 0
        ):  # WHY: Match original cadence verbatim
            # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
            self.logger.info(
                "- [%s] Long-running command... %.0fs elapsed (Ctrl+C to interrupt)",
                hostname,
                current_duration,
            )

    def _read_one_chunk(
        self, shell: Any, state: _CollectState, hostname: str
    ) -> None:  # WHY: Reads one chunk and mutates state in place
        """Read one chunk from the channel and update ``state`` (output, timers, truncation)."""
        chunk = shell.recv(_RECV_CHUNK_BYTES).decode("utf-8", errors="ignore")  # WHY: 128 KB read
        state.output += chunk  # WHY: Append to accumulator
        state.last_data_time = time.time()  # WHY: Reset silence timer
        state.chunk_count += 1  # WHY: Track for progress logging
        if state.chunk_count % _PROGRESS_INTERVAL_CHUNKS == 0:  # WHY: Every 100 chunks log/print progress
            self._log_chunk_progress(state.output, state.chunk_count, hostname)
        if len(state.output) > _MAX_OUTPUT_BYTES:  # WHY: Output cap reached - signal caller to drain + break
            self._apply_truncation(state, hostname)
            return
        time.sleep(_READ_SLEEP_S)  # WHY: Tiny pause between reads when not truncating

    def _apply_truncation(
        self, state: _CollectState, hostname: str
    ) -> None:  # WHY: Emit the "output truncated" marker once cap is hit
        """Append the truncation marker and set the flag so the caller can drain the tail."""
        cap_mb = _MAX_OUTPUT_BYTES // _MB_DIVISOR  # WHY: Cap expressed in megabytes for the log/print lines
        self.logger.warning(
            "Output size limit (%dMB) reached, draining remaining data...", cap_mb
        )  # WHY: Warn once cap hit
        state.output += (
            f"\n\n[OUTPUT TRUNCATED - Size limit of {cap_mb}MB reached]\n"  # WHY: Verbatim truncation marker
        )
        # WHY: spec 1031 console echo. The genuine truncation warning stays above at WARNING.
        echo("!? [%s] Output truncated at %dMB, draining remaining data...", hostname, cap_mb)  # WHY: notify operator.
        state.truncated = True  # WHY: Loop will drain the tail and exit

    def _log_chunk_progress(
        self, output: str, chunk_count: int, hostname: str
    ) -> None:  # WHY: Debug + user print for large outputs
        """Periodic progress logging - debug + user print when output exceeds 5 MB."""
        output_mb = len(output) / _MB_DIVISOR  # WHY: Megabytes received so far
        self.logger.debug(
            "Receiving data... %d chunks, %.1fMB", chunk_count, output_mb
        )  # WHY: Structured trace of progress
        if output_mb > _LARGE_OUTPUT_PRINT_MB:  # WHY: User-facing print only for large outputs
            # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
            self.logger.info("- [%s] Receiving large output... %.1fMB (Press Ctrl+C to interrupt)", hostname, output_mb)

    # ------------------------------------------------------------------
    # Phase 5: drain excess data after output cap
    # ------------------------------------------------------------------
    def _drain_excess(
        self, shell: Any, last_data_time: float, hostname: str
    ) -> None:  # WHY: Discard tail bytes so device does not block
        """Drain remaining bytes (up to ``_DRAIN_MAX_S``) to keep the device from blocking."""
        drain_start = time.time()  # WHY: Drain start time
        drained_chunks = 0  # WHY: Counter for status reporting
        while (time.time() - drain_start) < _DRAIN_MAX_S:  # WHY: Bounded drain window
            if shell.recv_ready():  # WHY: Bytes available - read and discard
                shell.recv(_DRAIN_CHUNK_BYTES)  # WHY: Discard immediately (no accumulator)
                drained_chunks += 1  # WHY: Track for progress reporting
                last_data_time = time.time()  # WHY: Reset silence timer
                self._maybe_print_drain_progress(
                    drain_start, drained_chunks, hostname
                )  # WHY: Emit periodic status line
                continue
            if (time.time() - last_data_time) >= _NO_DATA_TIMEOUT_S:  # WHY: Silence threshold - device finished sending
                break
            time.sleep(_POLL_SLEEP_S)  # WHY: Brief sleep before next poll
        drain_duration = time.time() - drain_start  # WHY: Final drain wall-clock
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        self.logger.info(
            "[OK] [%s] Data drain completed in %.1fs (%d chunks discarded)",
            hostname,
            drain_duration,
            drained_chunks,
        )

    @staticmethod
    def _maybe_print_drain_progress(
        drain_start: float, drained_chunks: int, hostname: str
    ) -> None:  # WHY: Periodic drain-progress print
        """Every 100 discarded chunks, print a drain-progress status line."""
        if drained_chunks % _PROGRESS_INTERVAL_CHUNKS != 0:  # WHY: Guard clause - not yet at cadence
            return
        drain_duration = time.time() - drain_start  # WHY: Elapsed drain wall-clock for the print
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.warning(
            "X  [%s] Draining excess data... %.0fs (%d chunks discarded)",
            hostname,
            drain_duration,
            drained_chunks,
        )

    # ------------------------------------------------------------------
    # Phase 6: cleanup shell channel
    # ------------------------------------------------------------------
    def _cleanup_shell(
        self, shell: Any, hostname: str
    ) -> None:  # WHY: Send exit + close channel, tolerating any failure
        """Send ``exit`` + extra newline, drain any tail output, then close the channel."""
        cleanup_start = time.time()  # WHY: For cleanup-duration logging
        try:
            shell.send(b"exit\n")  # WHY: Logout command
            shell.send(b"\n")  # WHY: Extra newline to ensure command commits
            self._drain_cleanup_tail(shell)  # WHY: Drain any remaining bytes within the cleanup budget
        except KeyboardInterrupt:  # WHY: Ctrl+C during cleanup - force-close immediately
            # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
            self.logger.warning("X  [%s] Ctrl+C during cleanup - forcing shell close", hostname)
            self.logger.warning("Command cleanup interrupted by user")  # WHY: Log operator-driven interrupt
        except (
            Exception
        ) as cleanup_error:  # cleanup errors are best-effort  # WHY: Preserve blanket-except behavior for compatibility
            self.logger.debug("Warning during cleanup: %s", cleanup_error)  # WHY: Trace non-fatal cleanup issue
        cleanup_duration = time.time() - cleanup_start  # WHY: Final cleanup wall-clock
        if cleanup_duration > _CLEANUP_LOG_THRESHOLD_S:  # WHY: Only log when cleanup was unusually slow
            self.logger.debug("Cleanup took %.2fs", cleanup_duration)
        self._close_shell(shell)  # WHY: Force channel close to prevent hangs (best-effort)

    def _close_shell(self, shell: Any) -> None:  # WHY: Best-effort close isolated so cleanup CC stays low
        """Close the shell channel, swallowing any exception."""
        try:
            shell.close()  # WHY: Force channel close to prevent hangs
        except (
            Exception
        ) as close_error:  # close errors are best-effort  # WHY: Preserve blanket-except behavior for compatibility
            self.logger.debug("Warning during shell close: %s", close_error)  # WHY: Trace non-fatal close issue

    def _drain_cleanup_tail(self, shell: Any) -> None:  # WHY: Drain within cleanup budget - exit early on silence
        """Drain any remaining bytes within the ``_CLEANUP_MAX_S`` budget. Exit early on silence."""
        cleanup_timeout = time.time() + _CLEANUP_MAX_S  # WHY: Absolute deadline
        while time.time() < cleanup_timeout:  # WHY: Bounded loop
            if not shell.recv_ready():  # WHY: No data ready - brief pause then exit
                time.sleep(_CLEANUP_TAIL_SLEEP_S)
                return
            try:
                shell.recv(_INITIAL_DRAIN_BUFFER)  # WHY: Small drain buffer is fine for cleanup
                time.sleep(_CLEANUP_TAIL_SLEEP_S)  # WHY: Brief pause before next poll
            except Exception:  # nosec B112 - cleanup is best-effort  # WHY: Any error during cleanup ends the drain
                return

    # ------------------------------------------------------------------
    # Phase 7: clean output (strip prompts, ANSI, artifacts)
    # ------------------------------------------------------------------
    def _clean_output_lines(
        self, output: str, command: str
    ) -> str:  # WHY: Strip echo, prompts, ANSI, and VyOS artifacts
        """Strip command echo, shell prompts, ANSI codes, and VyOS-specific artifacts."""
        cleaned_lines: list[str] = []  # WHY: Accumulator for surviving lines
        command_stripped = command.strip()  # WHY: Pre-strip once so the loop stays a pure filter
        echo_state = {"seen": False}  # WHY: Mutable flag lets the helper flip the state without a nonlocal
        for raw_line in output.split("\n"):  # WHY: Per-line processing
            surviving = self._process_line(
                raw_line, command_stripped, echo_state
            )  # WHY: Delegate all filtering decisions to helper
            if surviving:
                cleaned_lines.append(surviving)  # WHY: Only keep surviving cleaned lines
        return "\n".join(cleaned_lines).strip()  # WHY: Final whitespace-stripped output

    @classmethod
    def _process_line(
        cls, raw_line: str, command_stripped: str, echo_state: dict[str, bool]
    ) -> str:  # WHY: Pure per-line filter - returns kept text or ""
        """Return the cleaned form of ``raw_line`` or ``""`` when the line should be dropped."""
        line = raw_line.strip()  # WHY: Strip leading/trailing whitespace
        if cls._should_drop_raw(line, command_stripped, echo_state):  # WHY: Raw-line filters run before ANSI cleaning
            return ""
        cleaned = cls._strip_ansi_and_pager(line)  # WHY: Strip ANSI + pager noise
        if cls._should_drop_cleaned(cleaned):  # WHY: Post-clean filters (empty / VyOS artifact)
            return ""
        return cleaned

    @classmethod
    def _should_drop_raw(
        cls, line: str, command_stripped: str, echo_state: dict[str, bool]
    ) -> bool:  # WHY: First-pass filters that examine the raw stripped line
        """Return True when the raw line is empty, the echo, or a shell artifact/prompt."""
        if not line:  # WHY: Drop empty lines
            return True
        if not echo_state["seen"] and command_stripped in line:  # WHY: Drop the first command-echo occurrence
            echo_state["seen"] = True
            return True
        return cls._line_is_artifact_or_prompt(line)  # WHY: Drop known noise

    @classmethod
    def _should_drop_cleaned(cls, cleaned: str) -> bool:  # WHY: Second-pass filters after ANSI/pager cleanup
        """Return True when the cleaned line is empty or matches a VyOS-specific artifact regex."""
        if not cleaned:  # WHY: Drop lines that became empty after cleaning
            return True
        return cls._matches_vyos_artifact(cleaned)  # WHY: Drop VyOS-only artifacts

    @staticmethod
    def _line_is_artifact_or_prompt(line: str) -> bool:  # WHY: Substring + regex noise detection
        """Return True when ``line`` matches any known shell artifact substring or prompt regex."""
        line_lower = line.lower()  # WHY: Case-insensitive substring match
        if any(artifact.lower() in line_lower for artifact in _SHELL_ARTIFACTS):  # WHY: Substring artifacts
            return True
        return any(re.match(pattern, line) for pattern in _SHELL_PROMPT_PATTERNS)  # WHY: Regex prompts

    @staticmethod
    def _strip_ansi_and_pager(line: str) -> str:  # WHY: Pure sanitization of ANSI + pager artifacts
        """Strip ANSI escape sequences, pager prompts, CR/backspace, and trailing colons."""
        cleaned = _ANSI_COLOR_RE.sub("", line)  # WHY: ANSI color/erase
        cleaned = _ANSI_MODE_RE.sub("", cleaned)  # WHY: ANSI mode changes
        cleaned = _ANSI_CURSOR_RE.sub("", cleaned)  # WHY: ANSI cursor positioning
        cleaned = _TRAILING_COLON_RE.sub("", cleaned)  # WHY: Trailing pager colon
        return cleaned.replace("\r", "").replace("\x08", "").strip()  # WHY: CR + backspace removal

    @staticmethod
    def _matches_vyos_artifact(line: str) -> bool:  # WHY: VyOS-specific noise regex scan
        """Return True when ``line`` matches any VyOS-specific shell-artifact regex."""
        return any(re.match(pattern, line) for pattern in _VYOS_ARTIFACT_PATTERNS)  # WHY: Regex any-match keeps CC=1

    # ------------------------------------------------------------------
    # Logging + success evaluation
    # ------------------------------------------------------------------
    def _log_output_summary(
        self, cleaned_output: str, start_time: float
    ) -> None:  # WHY: Summarize cleaned output for diagnostics
        """Log a sample of the cleaned output (small outputs) or just its length (large)."""
        command_time = time.time() - start_time  # WHY: For log context
        self.logger.debug("Shell command completed in %.2f seconds", command_time)  # WHY: Duration breadcrumb
        if len(cleaned_output) >= _LARGE_OUTPUT_LOG_LIMIT:  # WHY: Guard clause - large output logs length only
            self.logger.debug("Shell output: %d characters (large output, sample not logged)", len(cleaned_output))
            return
        output_sample = _escape_sample(cleaned_output[:_OUTPUT_SAMPLE_CHARS])  # WHY: Escaped single-line sample
        suffix = "..." if len(cleaned_output) > _OUTPUT_SAMPLE_CHARS else ""  # WHY: Indicate truncation
        self.logger.debug(
            "Shell output (%d chars): %s%s", len(cleaned_output), output_sample, suffix
        )  # WHY: Detailed sample log

    def _evaluate_success(self, cleaned_output: str) -> bool:  # WHY: Classify command result as success/failure
        """Classify the cleaned output as success (True) or failure (False)."""
        if len(cleaned_output) == 0:  # WHY: No output = no success signal
            return False
        output_lower = cleaned_output.lower()  # WHY: Case-insensitive substring scan
        if self._is_shell_cleanup_only(output_lower):  # WHY: Cleanup artifacts are NOT errors
            return True
        for pattern in _ERROR_PATTERNS:  # WHY: Real-error scan
            if pattern in output_lower:
                self.logger.warning("Command error detected: %s", pattern)  # WHY: Trace which pattern matched
                return False
        return True  # WHY: Output present + no error patterns matched

    @staticmethod
    def _is_shell_cleanup_only(output_lower: str) -> bool:  # WHY: Suppress false-positive errors from cleanup noise
        """Return True when the only "errors" are shell cleanup indicators (false positives)."""
        return any(
            cleanup_pattern in output_lower for cleanup_pattern in _SHELL_CLEANUP_INDICATORS
        )  # WHY: Any-match keeps CC=1


def _escape_sample(text: str) -> str:  # WHY: Render control characters as escaped literals for single-line logs
    """Escape newline/carriage-return/tab so logged samples stay on one line."""
    return (
        text.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
    )  # WHY: Same transform used at multiple sites
