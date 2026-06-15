"""ShellExecutor — interactive-shell command execution over an existing SSH client.

Extracted from ``EnhancedSSHRunner._execute_with_shell`` (CC=51, F) per T013b of
specs/198-radon-complexity-decomposition. The monolithic original is replaced by
a class whose every method has cyclomatic complexity <= 10, organized around the
five phases of an interactive-shell command execution:

1. ``_open_shell``               — invoke a PTY, drain the initial prompt
2. ``_send_command``             — write the command, return error tuple on send failure
3. ``_wait_for_command_start``   — wait briefly for the device to begin producing output
4. ``_collect_output``           — main data-collection loop with timeout/limits/Ctrl+C
5. ``_drain_excess``             — drain remaining bytes after output cap reached
6. ``_cleanup_shell``            — send ``exit`` and close the channel
7. ``_clean_output_lines``       — strip prompts, ANSI codes, shell artifacts
8. ``_evaluate_success``         — classify the cleaned output as success/failure

All user-facing strings (status lines, ``[TIMEOUT]``, ``[OK]``, ``[STATUS]``,
``X  [host]`` markers) are preserved verbatim from the original implementation.
"""

from __future__ import annotations

import logging  # Structured logging for the new shell-execution module
import re  # Output cleaning regexes
import time  # Timing for output loops, cleanup, total duration
from typing import Any  # paramiko Channel type is dynamic across paramiko versions

# Module-level constants — extracted so each method's CC stays low (no magic numbers in branches)
_INITIAL_PROMPT_MAX_WAIT_S = 3.0  # Max seconds to wait for initial shell prompt
_WAIT_INCREMENT_S = 0.2  # Polling interval while waiting for shell events
_CMD_START_MAX_WAIT_S = 6.0  # Max seconds to wait for command to begin producing output
_NO_DATA_TIMEOUT_S = 3.0  # Seconds of silence after which we consider the command finished
_TOTAL_MAX_WAIT_S = 120.0  # Hard overall ceiling per command (2 minutes)
_HANG_DETECTION_S = 90.0  # Threshold for forced-completion "hang detected" message
_MAX_OUTPUT_BYTES = 100 * 1024 * 1024  # 100 MB output cap before draining excess
_RECV_CHUNK_BYTES = 131072  # 128 KB chunks from the channel for efficiency
_DRAIN_CHUNK_BYTES = 262144  # 256 KB chunks while draining excess data
_DRAIN_MAX_S = 30.0  # Max seconds to drain excess data after cap reached
_CLEANUP_MAX_S = 2.0  # Max seconds to spend on post-command cleanup
_PROGRESS_INTERVAL_CHUNKS = 100  # Log progress every N chunks for large outputs
_SHELL_ARTIFACTS: tuple[str, ...] = (  # Substrings (case-insensitive) that mark filterable shell noise
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
_SHELL_PROMPT_PATTERNS: tuple[str, ...] = (  # Regexes that identify shell prompts to strip
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
_VYOS_ARTIFACT_PATTERNS: tuple[str, ...] = (  # VyOS-specific noise lines stripped after ANSI removal
    r"^\s*xit\s*$",
    r"^Invalid command: \[xit\]$",
    r"^vyos@.*:~\$",
    r"^Connection.*closed\.$",
)
_ERROR_PATTERNS: tuple[str, ...] = (  # Substrings that indicate a real command failure
    "command not found",
    "syntax error",
    "permission denied",
    "authentication failed",
    "connection refused",
    "host unreachable",
    "network unreachable",
    "no such file or directory",
)
_SHELL_CLEANUP_INDICATORS: tuple[str, ...] = (  # Substrings that look like errors but are cleanup noise
    "invalid command: [xit]",
    "unknown command: xit",
    "invalid command: exit",
    "connection to .* closed",
)


class ShellExecutor:
    """Run one command over an interactive paramiko shell with PTY semantics.

    Construct with an already-connected SSH client, then call :meth:`execute`.
    The class does NOT own the SSH connection lifecycle — callers (typically
    ``EnhancedSSHRunner._execute_command`` or ``SingleCommandRunner``) must open
    and close the underlying client themselves.
    """

    def __init__(self, client: Any, timeout: int = 30, logger: logging.Logger | None = None) -> None:
        """Capture the live SSH client, command timeout, and logger."""
        self.client = client  # paramiko SSHClient — must already be connected
        self.timeout = timeout  # Per-command socket timeout
        self.logger = logger or logging.getLogger("ssh_runner_v2")  # Reuse the unified SSH logger

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------
    def execute(self, command: str, start_time: float, hostname: str = "unknown") -> tuple[bool, str, str]:
        """Execute ``command`` over an interactive shell and return ``(success, stdout, stderr)``."""
        assert self.client is not None, "No active SSH connection"  # nosec B101 - precondition
        self.logger.info("ShellExecutor: starting interactive shell command on %s", hostname)
        try:
            shell = self._open_shell()  # Phase 1: open PTY, drain prompt
            send_error = self._send_command(shell, command)  # Phase 2: write command line
            if send_error is not None:
                return send_error  # Send failed — return error tuple immediately
            self._wait_for_command_start(shell)  # Phase 3: brief wait for first response bytes
            output = self._collect_output(shell, command, start_time, hostname)  # Phase 4: main read loop
            self._cleanup_shell(shell, hostname)  # Phase 6: send exit + close channel
            cleaned_output = self._clean_output_lines(output, command)  # Phase 7: strip prompts/artifacts
            self._log_output_summary(cleaned_output, start_time)  # Diagnostic logging only
            success = self._evaluate_success(cleaned_output)  # Phase 8: classify as success/failure
            command_time = time.time() - start_time  # Final wall-clock duration
            print(f"[STATUS] [{hostname}] Command completed in {command_time:.2f} seconds")  # Verbatim line
            self.logger.debug("ShellExecutor: command completed on %s in %.2fs", hostname, command_time)
            return success, cleaned_output, ""
        except Exception as shell_error:
            error_msg = f"Shell execution error: {type(shell_error).__name__}: {shell_error}"
            self.logger.error(error_msg, exc_info=True)
            return False, "", error_msg

    # ------------------------------------------------------------------
    # Phase 1: open shell + initial prompt drain
    # ------------------------------------------------------------------
    def _open_shell(self) -> Any:
        """Invoke a PTY shell, set socket timeout, and drain the initial prompt."""
        self.logger.debug("Using interactive shell mode")
        shell = self.client.invoke_shell(term="vt100", width=120, height=24)  # Standard VT100 sizing
        shell.settimeout(self.timeout)  # Per-recv socket timeout
        self._drain_initial_prompt(shell)  # Best-effort prompt drain (failure here is non-fatal)
        return shell

    def _drain_initial_prompt(self, shell: Any) -> None:
        """Wait up to ``_INITIAL_PROMPT_MAX_WAIT_S`` for the initial prompt and discard it."""
        total_wait = 0.0  # Accumulated wait time
        while total_wait < _INITIAL_PROMPT_MAX_WAIT_S:  # Bounded polling loop
            time.sleep(_WAIT_INCREMENT_S)  # Wait one polling interval
            total_wait += _WAIT_INCREMENT_S  # Track progress against the cap
            if shell.recv_ready():  # Initial bytes available — drain and exit loop
                initial_output = shell.recv(4096).decode("utf-8", errors="ignore")
                initial_sample = initial_output[:100].replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
                self.logger.debug("Initial shell output: %s...", initial_sample)
                return

    # ------------------------------------------------------------------
    # Phase 2: send command
    # ------------------------------------------------------------------
    def _send_command(self, shell: Any, command: str) -> tuple[bool, str, str] | None:
        r"""Send ``command\n`` to the shell; return an error tuple on failure, ``None`` on success."""
        try:
            command_with_newline = command + "\n"  # Newline triggers command execution
            shell.send(command_with_newline.encode("utf-8"))  # Byte-level write to channel
            time.sleep(0.1)  # Small delay so the device has time to buffer the full line
            self.logger.debug("Sent command to shell: %s", command)
            return None  # Caller proceeds with phases 3+
        except Exception as send_error:
            self.logger.warning("Error sending command: %s", send_error)
            return False, "", f"Failed to send command: {send_error}"

    # ------------------------------------------------------------------
    # Phase 3: wait for command to start producing output
    # ------------------------------------------------------------------
    def _wait_for_command_start(self, shell: Any) -> None:
        """Wait up to ``_CMD_START_MAX_WAIT_S`` for the channel to indicate readable bytes."""
        cmd_wait = 0.0  # Accumulated wait time
        while cmd_wait < _CMD_START_MAX_WAIT_S:  # Bounded wait — device may take a moment
            time.sleep(_WAIT_INCREMENT_S)  # Poll interval
            cmd_wait += _WAIT_INCREMENT_S  # Track progress against cap
            if shell.recv_ready():  # Device has begun responding
                return

    # ------------------------------------------------------------------
    # Phase 4: main output-collection loop (decomposed to keep CC <= 10)
    # ------------------------------------------------------------------
    def _collect_output(self, shell: Any, command: str, start_time: float, hostname: str) -> str:
        """Run the main read loop, returning the accumulated raw output string."""
        self.logger.info("ShellExecutor: collecting output for %s on %s", command[:40], hostname)
        output = ""  # Accumulated raw bytes decoded as UTF-8
        last_data_time = time.time()  # When we last saw bytes (resets after each chunk)
        chunk_count = 0  # Total chunks read — drives progress logging cadence
        try:
            while (time.time() - start_time) < _TOTAL_MAX_WAIT_S:  # Hard total ceiling
                if self._handle_hang_detection(start_time, command, hostname):  # 90s "hang" forced-completion
                    output += f"\n\n[COMMAND TIMEOUT - Forced completion after {time.time() - start_time:.0f}s]\n"
                    break
                self._maybe_print_long_running_progress(start_time, chunk_count, hostname)  # Periodic UX
                if shell.recv_ready():  # Bytes available — read one chunk
                    output, last_data_time, chunk_count, truncated = self._read_one_chunk(
                        shell, output, chunk_count, hostname
                    )
                    if truncated:  # Output cap hit — drain remainder + exit loop
                        self._drain_excess(shell, last_data_time, hostname)
                        break
                else:  # No bytes ready — check for end-of-command silence
                    if (time.time() - last_data_time) >= _NO_DATA_TIMEOUT_S:
                        break  # Silence threshold reached — command considered finished
                    time.sleep(0.05)  # Brief sleep before next poll
        except KeyboardInterrupt:  # Operator interrupted — preserve partial output
            print(f"\nX  [{hostname}] Ctrl+C detected! Interrupting command: {command}")
            self.logger.warning("Command interrupted by user: %s", command)
            output += "\n\n[COMMAND INTERRUPTED BY USER - Ctrl+C pressed during data collection]\n"
        return output

    def _handle_hang_detection(self, start_time: float, command: str, hostname: str) -> bool:
        """Return True if the command has exceeded the hang threshold (forces caller to break)."""
        current_duration = time.time() - start_time  # Wall-clock elapsed
        if current_duration > _HANG_DETECTION_S:  # 90-second forced-completion threshold
            print(
                f"[TIMEOUT] [{hostname}] HANG DETECTED: Command running for {current_duration:.0f}s, "
                f"forcing completion"
            )
            self.logger.warning("Command hang detected after %.0fs, forcing completion: %s", current_duration, command)
            return True
        return False

    def _maybe_print_long_running_progress(self, start_time: float, chunk_count: int, hostname: str) -> None:
        """Every 150 chunks after 30s elapsed, print a "still running" status line."""
        current_duration = time.time() - start_time  # Wall-clock elapsed
        if current_duration > 30 and chunk_count % 150 == 0:  # Match original cadence verbatim
            print(f"- [{hostname}] Long-running command... {current_duration:.0f}s elapsed (Ctrl+C to interrupt)")

    def _read_one_chunk(
        self,
        shell: Any,
        output: str,
        chunk_count: int,
        hostname: str,
    ) -> tuple[str, float, int, bool]:
        """Read one chunk from the channel. Returns ``(output, last_data_time, chunk_count, truncated)``."""
        chunk = shell.recv(_RECV_CHUNK_BYTES).decode("utf-8", errors="ignore")  # 128 KB read
        output += chunk  # Append to accumulator
        last_data_time = time.time()  # Reset silence timer
        chunk_count += 1  # Track for progress logging
        if chunk_count % _PROGRESS_INTERVAL_CHUNKS == 0:  # Every 100 chunks log/print progress
            self._log_chunk_progress(output, chunk_count, hostname)
        truncated = False  # Default: did not hit output cap
        if len(output) > _MAX_OUTPUT_BYTES:  # Output cap reached — signal caller to drain + break
            self.logger.warning(
                "Output size limit (%dMB) reached, draining remaining data...",
                _MAX_OUTPUT_BYTES // (1024 * 1024),
            )
            output += f"\n\n[OUTPUT TRUNCATED - Size limit of {_MAX_OUTPUT_BYTES // (1024 * 1024)}MB reached]\n"
            print(
                f"!? [{hostname}] Output truncated at {_MAX_OUTPUT_BYTES // (1024 * 1024)}MB, "
                f"draining remaining data..."
            )
            truncated = True
        else:
            time.sleep(0.01)  # Tiny pause between reads when not truncating
        return output, last_data_time, chunk_count, truncated

    def _log_chunk_progress(self, output: str, chunk_count: int, hostname: str) -> None:
        """Periodic progress logging — debug + user print when output exceeds 5 MB."""
        output_mb = len(output) / (1024 * 1024)  # Megabytes received so far
        self.logger.debug("Receiving data... %d chunks, %.1fMB", chunk_count, output_mb)
        if output_mb > 5:  # User-facing print only for large outputs
            print(f"- [{hostname}] Receiving large output... {output_mb:.1f}MB " f"(Press Ctrl+C to interrupt)")

    # ------------------------------------------------------------------
    # Phase 5: drain excess data after output cap
    # ------------------------------------------------------------------
    def _drain_excess(self, shell: Any, last_data_time: float, hostname: str) -> None:
        """Drain remaining bytes (up to ``_DRAIN_MAX_S``) to keep the device from blocking."""
        drain_start = time.time()  # Drain start time
        drained_chunks = 0  # Counter for status reporting
        while (time.time() - drain_start) < _DRAIN_MAX_S:  # Bounded drain window
            if shell.recv_ready():  # Bytes available — read and discard
                shell.recv(_DRAIN_CHUNK_BYTES)  # Discard immediately (no accumulator)
                drained_chunks += 1  # Track for progress reporting
                last_data_time = time.time()  # Reset silence timer
                if drained_chunks % _PROGRESS_INTERVAL_CHUNKS == 0:  # Every 100 chunks print progress
                    drain_duration = time.time() - drain_start
                    print(
                        f"X  [{hostname}] Draining excess data... {drain_duration:.0f}s "
                        f"({drained_chunks} chunks discarded)"
                    )
            else:  # No bytes — check silence threshold
                if (time.time() - last_data_time) >= _NO_DATA_TIMEOUT_S:
                    break  # Device finished sending
                time.sleep(0.05)  # Brief sleep before next poll
        drain_duration = time.time() - drain_start  # Final drain wall-clock
        print(
            f"[OK] [{hostname}] Data drain completed in {drain_duration:.1f}s " f"({drained_chunks} chunks discarded)"
        )

    # ------------------------------------------------------------------
    # Phase 6: cleanup shell channel
    # ------------------------------------------------------------------
    def _cleanup_shell(self, shell: Any, hostname: str) -> None:
        """Send ``exit`` + extra newline, drain any tail output, then close the channel."""
        cleanup_start = time.time()  # For cleanup-duration logging
        try:
            shell.send(b"exit\n")  # Logout command
            shell.send(b"\n")  # Extra newline to ensure command commits
            self._drain_cleanup_tail(shell)  # Drain any remaining bytes within the cleanup budget
        except KeyboardInterrupt:  # Ctrl+C during cleanup — force-close immediately
            print(f"X  [{hostname}] Ctrl+C during cleanup - forcing shell close")
            self.logger.warning("Command cleanup interrupted by user")
        except Exception as cleanup_error:
            self.logger.debug("Warning during cleanup: %s", cleanup_error)
        cleanup_duration = time.time() - cleanup_start  # Final cleanup wall-clock
        if cleanup_duration > 1.0:  # Only log when cleanup was unusually slow
            self.logger.debug("Cleanup took %.2fs", cleanup_duration)
        try:
            shell.close()  # Force channel close to prevent hangs
        except Exception as close_error:
            self.logger.debug("Warning during shell close: %s", close_error)

    def _drain_cleanup_tail(self, shell: Any) -> None:
        """Drain any remaining bytes within the ``_CLEANUP_MAX_S`` budget; exit early on silence."""
        cleanup_timeout = time.time() + _CLEANUP_MAX_S  # Absolute deadline
        while time.time() < cleanup_timeout:  # Bounded loop
            if shell.recv_ready():  # Bytes still arriving — drain quickly
                try:
                    shell.recv(4096)  # Small drain buffer is fine for cleanup
                    time.sleep(0.1)  # Brief pause before next poll
                except Exception:  # nosec B112 - cleanup is best-effort
                    break  # Any error during cleanup ends the drain
            else:
                time.sleep(0.1)  # Brief pause then exit (no data ready)
                break

    # ------------------------------------------------------------------
    # Phase 7: clean output (strip prompts, ANSI, artifacts)
    # ------------------------------------------------------------------
    def _clean_output_lines(self, output: str, command: str) -> str:
        """Strip command echo, shell prompts, ANSI codes, and VyOS-specific artifacts."""
        cleaned_lines: list[str] = []  # Accumulator for surviving lines
        command_found = False  # Track whether we've already removed the command echo
        for raw_line in output.split("\n"):  # Per-line processing
            line = raw_line.strip()  # Strip leading/trailing whitespace
            if not line:  # Drop empty lines
                continue
            if not command_found and command.strip() in line:  # Drop the first command-echo occurrence
                command_found = True
                continue
            if self._line_is_artifact_or_prompt(line):  # Drop known noise
                continue
            cleaned_line = self._strip_ansi_and_pager(line)  # Strip ANSI + pager noise
            if cleaned_line and not self._matches_vyos_artifact(cleaned_line):  # Drop VyOS-only artifacts
                cleaned_lines.append(cleaned_line)
        return "\n".join(cleaned_lines).strip()  # Final whitespace-stripped output

    @staticmethod
    def _line_is_artifact_or_prompt(line: str) -> bool:
        """Return True when ``line`` matches any known shell artifact substring or prompt regex."""
        line_lower = line.lower()  # Case-insensitive substring match
        for artifact in _SHELL_ARTIFACTS:  # Substring artifacts
            if artifact.lower() in line_lower:
                return True
        for pattern in _SHELL_PROMPT_PATTERNS:  # Regex prompts
            if re.match(pattern, line):
                return True
        return False

    @staticmethod
    def _strip_ansi_and_pager(line: str) -> str:
        """Strip ANSI escape sequences, pager prompts, CR/backspace, and trailing colons."""
        cleaned = re.sub(r"\x1b\[[0-9;]*[mK]", "", line)  # ANSI color/erase
        cleaned = re.sub(r"\x1b\[\?[0-9]+[hl]", "", cleaned)  # ANSI mode changes
        cleaned = re.sub(r"\x1b\[[0-9]+;[0-9]+H", "", cleaned)  # ANSI cursor positioning
        cleaned = re.sub(r":\s*$", "", cleaned)  # Trailing pager colon
        return cleaned.replace("\r", "").replace("\x08", "").strip()  # CR + backspace removal

    @staticmethod
    def _matches_vyos_artifact(line: str) -> bool:
        """Return True when ``line`` matches any VyOS-specific shell-artifact regex."""
        for pattern in _VYOS_ARTIFACT_PATTERNS:  # All VyOS noise lines
            if re.match(pattern, line):
                return True
        return False

    # ------------------------------------------------------------------
    # Logging + success evaluation
    # ------------------------------------------------------------------
    def _log_output_summary(self, cleaned_output: str, start_time: float) -> None:
        """Log a sample of the cleaned output (small outputs) or just its length (large)."""
        command_time = time.time() - start_time  # For log context
        self.logger.debug("Shell command completed in %.2f seconds", command_time)
        if len(cleaned_output) < 10000:  # Only log a sample for small outputs
            output_sample = cleaned_output[:200].replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
            suffix = "..." if len(cleaned_output) > 200 else ""
            self.logger.debug("Shell output (%d chars): %s%s", len(cleaned_output), output_sample, suffix)
        else:
            self.logger.debug("Shell output: %d characters (large output, sample not logged)", len(cleaned_output))

    def _evaluate_success(self, cleaned_output: str) -> bool:
        """Classify the cleaned output as success (True) or failure (False)."""
        if len(cleaned_output) == 0:  # No output = no success signal
            return False
        output_lower = cleaned_output.lower()  # Case-insensitive substring scan
        if self._is_shell_cleanup_only(output_lower):  # Cleanup artifacts are NOT errors
            return True
        for pattern in _ERROR_PATTERNS:  # Real-error scan
            if pattern in output_lower:
                self.logger.warning("Command error detected: %s", pattern)
                return False
        return True  # Output present + no error patterns matched

    @staticmethod
    def _is_shell_cleanup_only(output_lower: str) -> bool:
        """Return True when the only "errors" are shell cleanup indicators (false positives)."""
        for cleanup_pattern in _SHELL_CLEANUP_INDICATORS:  # Cleanup substring scan
            if cleanup_pattern in output_lower:
                return True
        return False
