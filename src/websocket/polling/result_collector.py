"""Polling loop that waits for a WebSocket command session to complete.

Replaces the body of WebSocketManager.wait_for_command_result. Uses
CompletionDetector + combine_segments collaborators so every method in
this module has CC <= 10.
"""

from __future__ import annotations

import logging  # Shared manager logger
import threading  # Lock around the shared command_results dict
import time  # Timing for the polling loop and idle calculations
from typing import Any  # Result dict shape

from src.websocket.polling.completion_detector import CompletionDetector  # Indicator strategies
from src.websocket.polling.result_combiner import combine_segments  # Final segment merge

# Circuit-breaker constant — preserved from original implementation
_MAX_CHECK_ITERATIONS = 10000
# Default 'no new messages' window before declaring completion
_DEFAULT_ACTIVITY_TIMEOUT = 2
# Polling sleep — 100 ms; critical to avoid busy-loop
_POLL_INTERVAL = 0.1
# Periodic performance logging window in seconds
_PERF_LOG_INTERVAL = 5.0


class _PerformanceMonitor:
    """Lightweight loop monitor preserved from the original module."""

    def __init__(self, name: str, max_iterations: int = _MAX_CHECK_ITERATIONS, log_interval: float = 5.0) -> None:
        self.name = name  # Human-readable monitor label
        self.start_time = time.time()  # When this monitor was created
        self.last_log_time = self.start_time  # Last time we emitted a [PERF] line
        self.iteration_count = 0  # Total loop iterations observed
        self.max_iterations = max_iterations  # Circuit-breaker threshold
        self.log_interval = log_interval  # Seconds between periodic logs

    def check_iteration(self, debug_mode: bool) -> None:
        """Increment iteration counter; emit periodic log; trip circuit breaker."""
        self.iteration_count += 1  # Count this iteration
        current_time = time.time()  # Snapshot now for logging window check
        if debug_mode and (current_time - self.last_log_time) >= self.log_interval:
            elapsed = current_time - self.start_time  # Total elapsed time
            print(f"[PERF] {self.name}: {self.iteration_count} iterations in {elapsed:.1f}s")
            self.last_log_time = current_time  # Reset window
        if self.iteration_count > self.max_iterations:  # Bail out before infinite loop
            error_msg = f"CIRCUIT BREAKER: {self.name} exceeded {self.max_iterations} iterations!"
            print(f"[EMERGENCY] {error_msg}")
            logging.error(error_msg)
            raise RuntimeError(error_msg)

    def finish(self, debug_mode: bool) -> None:
        """Emit completion line when the monitored loop ends normally."""
        elapsed = time.time() - self.start_time  # Total run duration
        if debug_mode:  # Verbose tail line preserved verbatim
            print(f"[PERF] {self.name} completed: {self.iteration_count} iterations in {elapsed:.1f}s")


class ResultCollector:
    """Wait for a command session to complete and combine its segments."""

    def __init__(
        self,
        command_results: dict[str, Any],
        results_lock: threading.Lock,
        logger: logging.Logger,
        debug_mode: bool,
    ) -> None:
        self._results = command_results  # Shared session->segments dict from manager
        self._lock = results_lock  # Lock protecting the shared dict
        self._logger = logger  # Manager logger used for trace lines
        self._debug = debug_mode  # Verbose printing flag

    def collect(
        self,
        session_id: str,
        timeout_seconds: int,
        activity_timeout_seconds: int | None,
    ) -> dict[str, Any] | None:
        """Run the polling loop until completion, activity timeout, or absolute timeout."""
        self._logger.info("Starting result collection for session %s", session_id)  # Pre-action log
        idle_timeout = activity_timeout_seconds if activity_timeout_seconds is not None else _DEFAULT_ACTIVITY_TIMEOUT
        ctx = _CollectorContext(  # Per-call mutable state grouped in a dataclass-like helper
            session_id=session_id,
            start_time=time.time(),
            activity_timeout=idle_timeout,
            perf_monitor=_PerformanceMonitor(
                f"wait_for_command_result({session_id[:8]}...)",
                max_iterations=_MAX_CHECK_ITERATIONS,
                log_interval=_PERF_LOG_INTERVAL,
            ),
        )
        self._emit_start_debug(ctx, timeout_seconds)  # Verbatim startup debug prints
        detector = CompletionDetector(self._logger, self._debug)  # Indicator strategy collection
        final_results = self._poll_loop(ctx, detector, timeout_seconds)  # Run the actual loop
        elapsed = time.time() - ctx.start_time  # Total wall time
        ctx.perf_monitor.finish(self._debug)  # Always finalize the monitor
        if not final_results:  # Timed out with nothing usable
            self._logger.warning("Timeout waiting for command result: %s", session_id)  # Post-action log
            if self._debug:
                print(f"[DEBUG] No results collected for session {session_id}")
            return None
        return combine_segments(final_results, session_id, self._logger, self._debug, elapsed, ctx.check_count)

    def _poll_loop(
        self,
        ctx: _CollectorContext,
        detector: CompletionDetector,
        timeout_seconds: int,
    ) -> list[dict[str, Any]]:
        """Main wait loop; returns the collected segment list on completion or timeout."""
        while time.time() - ctx.start_time < timeout_seconds:  # Absolute timeout guard
            ctx.perf_monitor.check_iteration(self._debug)  # Periodic perf + circuit breaker
            ctx.check_count += 1  # Count this poll
            self._maybe_emit_progress(ctx)  # Periodic 5-second progress trace
            done = self._try_completion(ctx, detector)  # Try to finalize on indicators
            if done is not None:
                return done  # Indicator strategy succeeded
            if ctx.check_count > _MAX_CHECK_ITERATIONS:  # Defensive secondary circuit breaker
                return self._emergency_drain(ctx)
            timeout_results = self._try_activity_timeout(ctx)  # Idle-window completion
            if timeout_results is not None:
                return timeout_results
            time.sleep(_POLL_INTERVAL)  # 100ms — DO NOT REMOVE; throttles the loop
        return self._drain_on_timeout(ctx)  # Absolute timeout fell through

    def _try_completion(
        self,
        ctx: _CollectorContext,
        detector: CompletionDetector,
    ) -> list[dict[str, Any]] | None:
        """Inspect collected output; if an indicator fires, pop and return the segments."""
        with self._lock:  # Snapshot under lock to keep the dict stable
            if ctx.session_id not in self._results:  # Not yet seen any messages for this session
                self._maybe_emit_no_results(ctx)
                return None
            collected = self._results[ctx.session_id]  # Reference to current segment list
            if len(collected) > ctx.last_message_count:  # New messages since last iteration
                ctx.last_activity = time.time()
                ctx.last_message_count = len(collected)
                self._maybe_emit_new_activity(ctx, len(collected))
            if not collected:
                return None
            all_raw = "".join(r.get("raw", "") for r in collected)  # Combined buffer for indicators
            self._maybe_emit_combined_trace(ctx, collected, all_raw)  # Periodic trace
            indicator = detector.detect(collected, all_raw, ctx.last_activity, ctx.check_count)
            if indicator is None:
                return None
            self._emit_completion_debug(indicator, collected, all_raw, ctx)
            return self._results.pop(ctx.session_id)

    def _try_activity_timeout(self, ctx: _CollectorContext) -> list[dict[str, Any]] | None:
        """If we have collected segments but no new ones recently, finalize."""
        with self._lock:  # Brief lock just to read counts
            count = len(self._results.get(ctx.session_id, []))
        if count == 0:  # Need at least one segment to invoke activity timeout
            return None
        if time.time() - ctx.last_activity <= ctx.activity_timeout:
            return None
        if self._debug:
            self._logger.debug(f"Activity timeout reached ({ctx.activity_timeout}s), completing with {count} messages")
            print(f"[DEBUG] Activity timeout reached ({ctx.activity_timeout}s), completing with {count} messages")
        self._logger.info(f"No new data for {ctx.activity_timeout}s, assuming command complete")
        with self._lock:  # Pop under lock
            return self._results.pop(ctx.session_id, [])

    def _emergency_drain(self, ctx: _CollectorContext) -> list[dict[str, Any]]:
        """Trip the secondary circuit breaker and return whatever segments we have."""
        if self._debug:
            self._logger.error(f"Circuit breaker triggered at {ctx.check_count} checks!")
            self._logger.error("This indicates a possible infinite loop or system hang")
            print(f"[EMERGENCY] Circuit breaker triggered at {ctx.check_count} checks!")
            print("[EMERGENCY] This indicates a possible infinite loop or system hang")
        self._logger.error(
            "Emergency circuit breaker: %s checks exceeded for session %s", ctx.check_count, ctx.session_id
        )
        with self._lock:
            return self._results.pop(ctx.session_id, [])

    def _drain_on_timeout(self, ctx: _CollectorContext) -> list[dict[str, Any]]:
        """Pop residual segments after the absolute timeout elapsed."""
        if self._debug:
            self._logger.debug(f"Timeout occurred after polling ended, {ctx.check_count} checks")
            print(f"[DEBUG] Timeout occurred after polling ended, {ctx.check_count} checks")
        with self._lock:
            return self._results.pop(ctx.session_id, [])

    def _emit_start_debug(self, ctx: _CollectorContext, timeout_seconds: int) -> None:
        """Verbatim startup debug trace preserved from the original implementation."""
        if not self._debug:
            return
        self._logger.debug(f"Waiting for session {ctx.session_id} (timeout: {timeout_seconds}s)")
        self._logger.debug(f"Current time: {time.time()}")
        self._logger.debug(f"Activity timeout: {ctx.activity_timeout}s)")
        print(f"[DEBUG] Waiting for session {ctx.session_id} (timeout: {timeout_seconds}s)")
        print(f"[DEBUG] Current time: {time.time()}")
        print(f"[DEBUG] Activity timeout: {ctx.activity_timeout}s)")

    def _maybe_emit_progress(self, ctx: _CollectorContext) -> None:
        """Emit a [PERF] line every 5 seconds in debug mode."""
        current_time = time.time()
        if not self._debug or (current_time - ctx.last_debug_time) < _PERF_LOG_INTERVAL:
            return
        elapsed = current_time - ctx.start_time
        self._logger.debug(f"Check #{ctx.check_count} at {elapsed:.1f}s - Still waiting for session {ctx.session_id}")
        self._logger.debug(f"Last activity: {current_time - ctx.last_activity:.1f}s ago")
        print(f"[PERF] Check #{ctx.check_count} at {elapsed:.1f}s - Still waiting for session {ctx.session_id}")
        print(f"[PERF] Last activity: {current_time - ctx.last_activity:.1f}s ago")
        with self._lock:  # Quick stats snapshot under lock
            available = list(self._results.keys())
            if ctx.session_id in self._results:
                msg_count = len(self._results[ctx.session_id])
                self._logger.debug(f"Found {msg_count} messages for our session")
                print(f"[PERF] Found {msg_count} messages for our session")
            else:
                self._logger.debug(f"Our session not in results yet. Available: {available}")
                print(f"[PERF] Our session not in results yet. Available: {available}")
        ctx.last_debug_time = current_time

    def _maybe_emit_no_results(self, ctx: _CollectorContext) -> None:
        """Periodic trace when the session has not produced any messages yet."""
        if not self._debug or ctx.check_count % 50 != 1:
            return
        self._logger.debug(f"Check #{ctx.check_count}, no results yet for session {ctx.session_id}")
        self._logger.debug(f"Available sessions: {list(self._results.keys())}")
        print(f"[DEBUG] Check #{ctx.check_count}, no results yet for session {ctx.session_id}")
        print(f"[DEBUG] Available sessions: {list(self._results.keys())}")

    def _maybe_emit_new_activity(self, ctx: _CollectorContext, count: int) -> None:
        """Trace when a new message arrives for the session."""
        if not self._debug:
            return
        self._logger.debug(f"New activity detected: {count} messages (+{count - ctx.last_message_count}) ")

    def _maybe_emit_combined_trace(
        self,
        ctx: _CollectorContext,
        collected: list[dict[str, Any]],
        all_raw: str,
    ) -> None:
        """Verbose buffer trace every 50 checks — preserved verbatim from original."""
        if not self._debug or ctx.check_count % 50 != 1:
            return
        latest_raw = collected[-1].get("raw", "") if collected else ""
        self._logger.debug(f"Check #{ctx.check_count}, found {len(collected)} messages")
        self._logger.debug(f"Latest raw (first 100 chars): {repr(latest_raw[:100])}")
        self._logger.debug(f"Total content length: {len(all_raw)} chars")
        print(f"[DEBUG] Check #{ctx.check_count}, found {len(collected)} messages")
        print(f"[DEBUG] Latest raw (first 100 chars): {repr(latest_raw[:100])}")
        print(f"[DEBUG] Total content length: {len(all_raw)} chars")
        if not all_raw:
            return
        self._logger.debug(f"Service ping content sample: {repr(all_raw[:300])}")
        print(f"[DEBUG] Service ping content sample: {repr(all_raw[:300])}")
        lowered = all_raw.lower()
        for pattern in ("bytes from", "seq=", "time="):  # Diagnostic markers preserved
            if pattern in lowered:
                self._logger.debug(f"Service ping: Found '{pattern}' pattern")
                print(f"[DEBUG] Service ping: Found '{pattern}' pattern")

    def _emit_completion_debug(
        self,
        indicator: str,
        collected: list[dict[str, Any]],
        all_raw: str,
        ctx: _CollectorContext,
    ) -> None:
        """Verbatim trace block emitted whenever an indicator fires."""
        if not self._debug:
            return
        self._logger.debug(f"Found completion indicator '{indicator}' in combined content")
        self._logger.debug(f"Completing after {ctx.check_count} checks")
        self._logger.debug(f"Total collected messages: {len(collected)}")
        self._logger.debug(f"Total content length: {len(all_raw)} characters")
        self._logger.debug(f"Raw content sample (first 200 chars): {repr(all_raw[:200])}")
        self._logger.debug(f"Raw content sample (last 200 chars): {repr(all_raw[-200:])}")
        print(f"[DEBUG] Found completion indicator '{indicator}' in combined content")
        print(f"[DEBUG] Completing after {ctx.check_count} checks")
        print(f"[DEBUG] Total collected messages: {len(collected)}")
        print(f"[DEBUG] Total content length: {len(all_raw)} characters")
        print(f"[DEBUG] Raw content sample (first 200 chars): {repr(all_raw[:200])}")
        print(f"[DEBUG] Raw content sample (last 200 chars): {repr(all_raw[-200:])}")


class _CollectorContext:
    """Mutable per-call state for ResultCollector.collect.

    Grouping the bag of state in one object keeps individual method
    signatures within the 5-parameter limit while preserving the original
    semantics of the inline polling loop.
    """

    __slots__ = (
        "session_id",
        "start_time",
        "activity_timeout",
        "perf_monitor",
        "last_activity",
        "last_message_count",
        "check_count",
        "last_debug_time",
    )

    def __init__(
        self,
        session_id: str,
        start_time: float,
        activity_timeout: int,
        perf_monitor: _PerformanceMonitor,
    ) -> None:
        self.session_id = session_id  # Session being collected
        self.start_time = start_time  # When collection began (wall clock)
        self.activity_timeout = activity_timeout  # Idle window in seconds
        self.perf_monitor = perf_monitor  # Loop monitor / circuit breaker
        self.last_activity = start_time  # Updated whenever new messages arrive
        self.last_message_count = 0  # Used to detect new-message edges
        self.check_count = 0  # Total poll iterations
        self.last_debug_time = start_time  # Throttles periodic [PERF] traces
