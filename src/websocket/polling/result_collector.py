"""Polling loop that waits for a WebSocket command session to complete.

Replaces the body of WebSocketManager.wait_for_command_result. Uses
CompletionDetector + combine_segments collaborators so every method in
this module has CC <= 5.
"""

from __future__ import annotations  # WHY: PEP 563 postponed evaluation of type hints.

import logging  # WHY: Shared manager logger for trace parity.
import threading  # WHY: Lock guarding the shared command_results dict.
import time  # WHY: Timing for polling loop and idle detection.
from dataclasses import dataclass, field  # WHY: Frozen slotted holders for ctx + state.
from typing import Any  # WHY: Generic segment dict shape.

from src.websocket.polling.completion_detector import CompletionDetector  # WHY: Indicator strategies.
from src.websocket.polling.result_combiner import CombineRequest, combine_segments  # WHY: Final segment merge.

# Circuit-breaker constant preserved verbatim from the original implementation.
_MAX_CHECK_ITERATIONS = 10000  # WHY: Hard cap on polling iterations to avoid infinite loops.
_DEFAULT_ACTIVITY_TIMEOUT = 2  # WHY: Default idle-window seconds before declaring completion.
_POLL_INTERVAL = 0.1  # WHY: 100 ms sleep throttles the polling loop; DO NOT REMOVE.
_PERF_LOG_INTERVAL = 5.0  # WHY: Periodic [PERF] logging cadence in seconds.
_TRACE_MODULUS = 50  # WHY: Emit verbose diagnostic traces every N poll iterations.
_TRACE_REMAINDER = 1  # WHY: Offset chosen so first trace fires on iteration 1.

# Log/print message templates preserved verbatim for downstream log parsers.
_PERF_LOOP_LINE = "[PERF] {name}: {count} iterations in {elapsed:.1f}s"  # WHY: Per-window loop trace.
_PERF_DONE_LINE = "[PERF] {name} completed: {count} iterations in {elapsed:.1f}s"  # WHY: Loop finish trace.
_EMERG_PREFIX = "[EMERGENCY]"  # WHY: Circuit-breaker prefix expected by ops runbooks.
_DBG_PREFIX = "[DEBUG]"  # WHY: Debug print prefix preserved verbatim.
_PERF_PREFIX = "[PERF]"  # WHY: Periodic performance prefix preserved verbatim.
_CB_ERROR_TMPL = "CIRCUIT BREAKER: {name} exceeded {max_iters} iterations!"  # WHY: Emergency message.

# Diagnostic markers emitted when service-ping content is seen in the buffer.
_PING_MARKERS = ("bytes from", "seq=", "time=")  # WHY: Substrings signalling ICMP echo output.


@dataclass(frozen=True, slots=True)  # WHY: Immutable slotted holder for shared manager state.
class _CollectorDeps:  # WHY: Bundle the 4 constructor args to keep signatures within limits.
    """Immutable manager-owned collaborators referenced by the collector."""

    results: dict[str, Any]  # WHY: Shared session->segments dict owned by the manager.
    lock: threading.Lock  # WHY: Lock guarding mutations of the results map.
    logger: logging.Logger  # WHY: Shared logger used for parity trace lines.
    debug: bool  # WHY: Verbose print toggle propagated from the manager.


@dataclass(slots=True)  # WHY: Mutable per-call state; frozen would block field updates.
class _CollectorContext:  # WHY: Groups poll-loop state to stay within 5-param limit.
    """Mutable per-call state threaded through the poll loop helpers."""

    session_id: str  # WHY: Session being collected in this call.
    start_time: float  # WHY: Wall-clock when collect() began.
    activity_timeout: int  # WHY: Idle window in seconds before completion.
    perf_monitor: _PerformanceMonitor  # WHY: Loop monitor + circuit breaker.
    last_activity: float = 0.0  # WHY: Updated whenever new messages arrive.
    last_message_count: int = 0  # WHY: Used to detect new-message edges.
    check_count: int = 0  # WHY: Total poll iterations observed.
    last_debug_time: float = 0.0  # WHY: Throttles periodic [PERF] traces.
    _init_ts: float = field(default=0.0, repr=False)  # WHY: Internal helper for post-init defaults.

    def __post_init__(self) -> None:  # WHY: Seed activity/debug timestamps to start_time.
        if self.last_activity == 0.0:  # WHY: Only seed when caller left the default.
            self.last_activity = self.start_time  # WHY: Anchor idle-timeout math at start.
        if self.last_debug_time == 0.0:  # WHY: Only seed when caller left the default.
            self.last_debug_time = self.start_time  # WHY: Anchor periodic trace at start.


class _PerformanceMonitor:  # WHY: Lightweight loop monitor preserved from the original module.
    """Loop monitor that periodically logs iteration counts and trips a circuit breaker."""

    def __init__(
        self,
        name: str,
        max_iterations: int = _MAX_CHECK_ITERATIONS,
        log_interval: float = _PERF_LOG_INTERVAL,
    ) -> None:  # WHY: Constructor mirrors original monitor signature.
        self.name = name  # WHY: Human-readable monitor label used in log lines.
        self.start_time = time.time()  # WHY: Anchor wall clock when this monitor was created.
        self.last_log_time = self.start_time  # WHY: Last time we emitted a [PERF] line.
        self.iteration_count = 0  # WHY: Total loop iterations observed so far.
        self.max_iterations = max_iterations  # WHY: Circuit-breaker threshold.
        self.log_interval = log_interval  # WHY: Seconds between periodic logs.

    def check_iteration(self, debug_mode: bool) -> None:  # WHY: Public per-iteration monitor hook.
        """Increment iteration counter, emit periodic log, and trip the circuit breaker."""
        self.iteration_count += 1  # WHY: Count this iteration for the periodic log.
        current_time = time.time()  # WHY: Snapshot now for the window check.
        self._maybe_log(current_time, debug_mode)  # WHY: Delegate periodic trace to helper.
        if self.iteration_count > self.max_iterations:  # WHY: Bail out before infinite loop.
            self._trip_circuit_breaker()  # WHY: Emit emergency trace and raise.

    def _maybe_log(self, current_time: float, debug_mode: bool) -> None:  # WHY: Rate-limited perf log.
        """Emit the periodic [PERF] line when the log window has elapsed."""
        if not debug_mode:  # WHY: Verbose trace suppressed outside debug mode.
            return  # WHY: Skip when not in debug mode.
        if (current_time - self.last_log_time) < self.log_interval:  # WHY: Rate limit.
            return  # WHY: Log window has not elapsed yet.
        elapsed = current_time - self.start_time  # WHY: Total elapsed since monitor start.
        print(_PERF_LOOP_LINE.format(name=self.name, count=self.iteration_count, elapsed=elapsed))  # WHY: Trace.
        self.last_log_time = current_time  # WHY: Reset window anchor for next log.

    def _trip_circuit_breaker(self) -> None:  # WHY: Emergency stop when iteration cap exceeded.
        """Emit emergency trace and raise a RuntimeError to abort the loop."""
        error_msg = _CB_ERROR_TMPL.format(name=self.name, max_iters=self.max_iterations)  # WHY: Prep msg.
        print(f"{_EMERG_PREFIX} {error_msg}")  # WHY: Preserve verbatim emergency print.
        logging.error(error_msg)  # WHY: Also route through the root logger for ops.
        raise RuntimeError(error_msg)  # WHY: Signal caller the safety limit tripped.

    def finish(self, debug_mode: bool) -> None:  # WHY: Public loop-completion hook.
        """Emit completion line when the monitored loop ends normally."""
        elapsed = time.time() - self.start_time  # WHY: Total run duration since monitor start.
        if debug_mode:  # WHY: Verbose tail line preserved verbatim.
            print(_PERF_DONE_LINE.format(name=self.name, count=self.iteration_count, elapsed=elapsed))  # WHY: Trace.


class ResultCollector:  # WHY: Public API preserved for WebSocketManager collaborator wiring.
    """Wait for a command session to complete and combine its segments."""

    def __init__(
        self,
        command_results: dict[str, Any],
        results_lock: threading.Lock,
        logger: logging.Logger,
        debug_mode: bool,
    ) -> None:  # WHY: Preserve original four-argument constructor for the manager.
        self._deps = _CollectorDeps(  # WHY: Pack manager state into one immutable holder.
            results=command_results,
            lock=results_lock,
            logger=logger,
            debug=debug_mode,
        )

    def collect(
        self,
        session_id: str,
        timeout_seconds: int,
        activity_timeout_seconds: int | None,
    ) -> dict[str, Any] | None:  # WHY: Public API preserved verbatim for manager.wait_for_command_result.
        """Run the polling loop until completion, activity timeout, or absolute timeout."""
        self._deps.logger.info("Starting result collection for session %s", session_id)  # WHY: Pre-action.
        ctx = self._build_context(session_id, activity_timeout_seconds)  # WHY: Group per-call state.
        self._emit_start_debug(ctx, timeout_seconds)  # WHY: Verbatim startup debug prints.
        detector = CompletionDetector(self._deps.logger, self._deps.debug)  # WHY: Indicator strategies.
        final_results = self._poll_loop(ctx, detector, timeout_seconds)  # WHY: Run the actual loop.
        ctx.perf_monitor.finish(self._deps.debug)  # WHY: Always finalize the monitor.
        return self._finalize(ctx, final_results)  # WHY: Merge or return None per contract.

    def _build_context(self, session_id: str, activity_timeout: int | None) -> _CollectorContext:  # WHY: Ctx factory.
        """Assemble the mutable per-call context used by the poll loop."""
        idle_timeout = activity_timeout if activity_timeout is not None else _DEFAULT_ACTIVITY_TIMEOUT  # WHY: Default.
        return _CollectorContext(  # WHY: Group per-call state within param limits.
            session_id=session_id,
            start_time=time.time(),
            activity_timeout=idle_timeout,
            perf_monitor=_PerformanceMonitor(  # WHY: Fresh monitor per collect() invocation.
                f"wait_for_command_result({session_id[:8]}...)",
                max_iterations=_MAX_CHECK_ITERATIONS,
                log_interval=_PERF_LOG_INTERVAL,
            ),
        )

    def _finalize(
        self,
        ctx: _CollectorContext,
        final_results: list[dict[str, Any]],
    ) -> dict[str, Any] | None:  # WHY: Return-path helper keeping collect() short.
        """Combine segments or return None when the poll loop yielded nothing usable."""
        elapsed = time.time() - ctx.start_time  # WHY: Total wall time for downstream metrics.
        if not final_results:  # WHY: Timed out with nothing usable.
            self._deps.logger.warning("Timeout waiting for command result: %s", ctx.session_id)  # WHY: Warn.
            if self._deps.debug:  # WHY: Preserve verbatim debug print.
                print(f"{_DBG_PREFIX} No results collected for session {ctx.session_id}")  # WHY: Debug trace.
            return None  # WHY: Contract: return None on empty timeout drain.
        return combine_segments(  # WHY: Delegate merge to the shared combiner.
            CombineRequest(
                final_results=final_results,
                session_id=ctx.session_id,
                logger=self._deps.logger,
                debug_mode=self._deps.debug,
                elapsed=elapsed,
                check_count=ctx.check_count,
            )
        )

    def _poll_loop(
        self,
        ctx: _CollectorContext,
        detector: CompletionDetector,
        timeout_seconds: int,
    ) -> list[dict[str, Any]]:  # WHY: Central polling driver invoked by collect().
        """Main wait loop; returns the collected segment list on completion or timeout."""
        while time.time() - ctx.start_time < timeout_seconds:  # WHY: Absolute timeout guard.
            result = self._poll_once(ctx, detector)  # WHY: Delegate per-iteration work.
            if result is not None:  # WHY: Helper returned finalized segments.
                return result  # WHY: Indicator or activity timeout succeeded.
            time.sleep(_POLL_INTERVAL)  # WHY: 100ms throttle; DO NOT REMOVE.
        return self._drain_on_timeout(ctx)  # WHY: Absolute timeout fell through.

    def _poll_once(
        self,
        ctx: _CollectorContext,
        detector: CompletionDetector,
    ) -> list[dict[str, Any]] | None:  # WHY: Single-iteration worker keeps _poll_loop short.
        """Perform one poll iteration; returns segments when the loop should stop."""
        ctx.perf_monitor.check_iteration(self._deps.debug)  # WHY: Periodic perf + circuit breaker.
        ctx.check_count += 1  # WHY: Count this poll for downstream telemetry.
        self._maybe_emit_progress(ctx)  # WHY: Periodic 5-second progress trace.
        done = self._try_completion(ctx, detector)  # WHY: Try to finalize on indicators.
        if done is not None:  # WHY: Indicator strategy succeeded.
            return done  # WHY: Return finalized segments to caller.
        if ctx.check_count > _MAX_CHECK_ITERATIONS:  # WHY: Defensive secondary breaker.
            return self._emergency_drain(ctx)  # WHY: Drain buffer and abort loop.
        return self._try_activity_timeout(ctx)  # WHY: None keeps loop going; list stops it.

    def _try_completion(
        self,
        ctx: _CollectorContext,
        detector: CompletionDetector,
    ) -> list[dict[str, Any]] | None:  # WHY: Indicator-driven completion path.
        """Inspect collected output; if an indicator fires, pop and return the segments."""
        with self._deps.lock:  # WHY: Snapshot under lock to keep the dict stable.
            collected = self._results_for(ctx)  # WHY: Guard clause when session absent.
            if collected is None:  # WHY: No entry yet for this session id.
                return None  # WHY: Nothing to do this iteration.
            self._refresh_activity(ctx, collected)  # WHY: Bump timestamps on new messages.
            if not collected:  # WHY: Cannot detect on empty buffer.
                return None  # WHY: Wait for the next iteration.
            all_raw = "".join(r.get("raw", "") for r in collected)  # WHY: Concat raw buffer.
            self._maybe_emit_combined_trace(ctx, collected, all_raw)  # WHY: Periodic trace.
            indicator = detector.detect(collected, all_raw, ctx.last_activity, ctx.check_count)  # WHY: Match.
            if indicator is None:  # WHY: No completion signal on this pass.
                return None  # WHY: Keep polling.
            self._emit_completion_debug(indicator, collected, all_raw, ctx)  # WHY: Verbatim log.
            return self._deps.results.pop(ctx.session_id)  # WHY: Consume segments on success.

    def _results_for(self, ctx: _CollectorContext) -> list[dict[str, Any]] | None:  # WHY: Lookup helper.
        """Return the segment list for the session, or None when nothing has arrived."""
        if ctx.session_id not in self._deps.results:  # WHY: No messages yet for this session.
            self._maybe_emit_no_results(ctx)  # WHY: Periodic trace when buffer is empty.
            return None  # WHY: Signal caller to skip this iteration.
        return self._deps.results[ctx.session_id]  # WHY: Reference to current segment list.

    def _refresh_activity(self, ctx: _CollectorContext, collected: list[dict[str, Any]]) -> None:  # WHY: Ctx update.
        """Update activity timestamps when new messages have arrived since last poll."""
        current_count = len(collected)  # WHY: Snapshot list length once.
        if current_count <= ctx.last_message_count:  # WHY: No new messages this iteration.
            return  # WHY: Nothing changed; skip trace + bookkeeping.
        ctx.last_activity = time.time()  # WHY: Anchor new idle window.
        self._maybe_emit_new_activity(ctx, current_count)  # WHY: Trace before overwriting count.
        ctx.last_message_count = current_count  # WHY: Advance edge detector cursor.

    def _try_activity_timeout(self, ctx: _CollectorContext) -> list[dict[str, Any]] | None:  # WHY: Idle path.
        """If we have collected segments but no new ones recently, finalize."""
        with self._deps.lock:  # WHY: Brief lock just to read counts.
            count = len(self._deps.results.get(ctx.session_id, []))  # WHY: Snapshot message count.
        if count == 0:  # WHY: Need at least one segment to invoke activity timeout.
            return None  # WHY: Keep polling until first message arrives.
        if time.time() - ctx.last_activity <= ctx.activity_timeout:  # WHY: Still within window.
            return None  # WHY: Wait longer before declaring completion.
        self._emit_activity_timeout_debug(ctx, count)  # WHY: Verbatim trace preserved.
        self._deps.logger.info(  # WHY: Always log activity timeout at info level.
            "No new data for %ss, assuming command complete", ctx.activity_timeout
        )
        with self._deps.lock:  # WHY: Pop under lock to avoid races with writer thread.
            return self._deps.results.pop(ctx.session_id, [])  # WHY: Consume segments on idle-out.

    def _emit_activity_timeout_debug(self, ctx: _CollectorContext, count: int) -> None:  # WHY: Debug helper.
        """Emit verbatim debug trace when the activity timeout fires."""
        if not self._deps.debug:  # WHY: Guard clause avoids noisy prints in prod.
            return  # WHY: Skip when debug mode is off.
        self._deps.logger.debug(  # WHY: Preserve verbatim logger.debug trace.
            "Activity timeout reached (%ss), completing with %s messages", ctx.activity_timeout, count
        )
        print(  # WHY: Preserve verbatim stdout print for downstream log scrapers.
            f"{_DBG_PREFIX} Activity timeout reached ({ctx.activity_timeout}s)," f" completing with {count} messages"
        )

    def _emergency_drain(self, ctx: _CollectorContext) -> list[dict[str, Any]]:  # WHY: Circuit-breaker path.
        """Trip the secondary circuit breaker and return whatever segments we have."""
        self._emit_emergency_debug(ctx)  # WHY: Verbatim trace preserved for ops.
        self._deps.logger.error(  # WHY: Always log emergency at error level.
            "Emergency circuit breaker: %s checks exceeded for session %s",
            ctx.check_count,
            ctx.session_id,
        )
        with self._deps.lock:  # WHY: Lock guards the pop against concurrent writers.
            return self._deps.results.pop(ctx.session_id, [])  # WHY: Drain residual segments.

    def _emit_emergency_debug(self, ctx: _CollectorContext) -> None:  # WHY: Verbatim ops trace helper.
        """Emit verbatim emergency trace when the secondary breaker trips."""
        if not self._deps.debug:  # WHY: Guard clause keeps prod logs quiet.
            return  # WHY: Skip when debug is off.
        self._deps.logger.error("Circuit breaker triggered at %s checks!", ctx.check_count)  # WHY: Log.
        self._deps.logger.error("This indicates a possible infinite loop or system hang")  # WHY: Log.
        print(f"{_EMERG_PREFIX} Circuit breaker triggered at {ctx.check_count} checks!")  # WHY: Print.
        print(f"{_EMERG_PREFIX} This indicates a possible infinite loop or system hang")  # WHY: Print.

    def _drain_on_timeout(self, ctx: _CollectorContext) -> list[dict[str, Any]]:  # WHY: Timeout drain.
        """Pop residual segments after the absolute timeout elapsed."""
        if self._deps.debug:  # WHY: Preserve verbatim trace inside guard.
            self._deps.logger.debug(  # WHY: Timeout diagnostic line preserved verbatim.
                "Timeout occurred after polling ended, %s checks", ctx.check_count
            )
            print(f"{_DBG_PREFIX} Timeout occurred after polling ended, {ctx.check_count} checks")  # WHY: Trace.
        with self._deps.lock:  # WHY: Lock guards residual pop.
            return self._deps.results.pop(ctx.session_id, [])  # WHY: Drain residual segments.

    def _emit_start_debug(self, ctx: _CollectorContext, timeout_seconds: int) -> None:  # WHY: Startup trace.
        """Verbatim startup debug trace preserved from the original implementation."""
        if not self._deps.debug:  # WHY: Guard clause avoids noisy startup prints.
            return  # WHY: Skip when debug is off.
        now = time.time()  # WHY: Snapshot once for consistent log values.
        self._deps.logger.debug("Waiting for session %s (timeout: %ss)", ctx.session_id, timeout_seconds)  # WHY: Log.
        self._deps.logger.debug("Current time: %s", now)  # WHY: Wall-clock trace.
        self._deps.logger.debug("Activity timeout: %ss)", ctx.activity_timeout)  # WHY: Idle window trace.
        print(f"{_DBG_PREFIX} Waiting for session {ctx.session_id} (timeout: {timeout_seconds}s)")  # WHY: Print.
        print(f"{_DBG_PREFIX} Current time: {now}")  # WHY: Wall-clock print.
        print(f"{_DBG_PREFIX} Activity timeout: {ctx.activity_timeout}s)")  # WHY: Idle window print.

    def _maybe_emit_progress(self, ctx: _CollectorContext) -> None:
        """Emit a [PERF] line every 5 seconds in debug mode."""
        current_time = time.time()  # WHY: Snapshot once for window check + trace values.
        if not self._deps.debug:  # WHY: Progress traces are debug-only.
            return  # WHY: Skip when debug is off.
        if (current_time - ctx.last_debug_time) < _PERF_LOG_INTERVAL:  # WHY: Rate limit.
            return  # WHY: Log window has not elapsed yet.
        self._emit_progress_lines(ctx, current_time)  # WHY: Delegate the print block.
        self._emit_session_stats(ctx)  # WHY: Delegate the locked stats block.
        ctx.last_debug_time = current_time  # WHY: Reset window anchor for next log.

    def _emit_progress_lines(self, ctx: _CollectorContext, current_time: float) -> None:
        """Emit the elapsed-time and last-activity trace lines."""
        elapsed = current_time - ctx.start_time  # WHY: Wall time since collect started.
        idle = current_time - ctx.last_activity  # WHY: Time since last new message.
        self._deps.logger.debug(
            "Check #%s at %.1fs - Still waiting for session %s",
            ctx.check_count,
            elapsed,
            ctx.session_id,
        )
        self._deps.logger.debug("Last activity: %.1fs ago", idle)
        print(
            f"{_PERF_PREFIX} Check #{ctx.check_count} at {elapsed:.1f}s -"
            f" Still waiting for session {ctx.session_id}"
        )
        print(f"{_PERF_PREFIX} Last activity: {idle:.1f}s ago")

    def _emit_session_stats(self, ctx: _CollectorContext) -> None:
        """Emit trace lines summarizing which sessions are visible right now."""
        with self._deps.lock:  # WHY: Quick stats snapshot under lock.
            available = list(self._deps.results.keys())  # WHY: Snapshot before releasing lock.
            present = ctx.session_id in self._deps.results  # WHY: Cheap membership check.
            msg_count = len(self._deps.results[ctx.session_id]) if present else 0
        if present:  # WHY: Distinct log format when our session has data.
            self._deps.logger.debug("Found %s messages for our session", msg_count)
            print(f"{_PERF_PREFIX} Found {msg_count} messages for our session")
            return  # WHY: Skip absent-session branch.
        self._deps.logger.debug("Our session not in results yet. Available: %s", available)
        print(f"{_PERF_PREFIX} Our session not in results yet. Available: {available}")

    def _maybe_emit_no_results(self, ctx: _CollectorContext) -> None:
        """Periodic trace when the session has not produced any messages yet."""
        if not self._deps.debug:  # WHY: Debug-only trace.
            return  # WHY: Skip when debug is off.
        if ctx.check_count % _TRACE_MODULUS != _TRACE_REMAINDER:  # WHY: Rate limit.
            return  # WHY: Only fire every _TRACE_MODULUS iterations.
        available = list(self._deps.results.keys())  # WHY: Snapshot available sessions.
        self._deps.logger.debug("Check #%s, no results yet for session %s", ctx.check_count, ctx.session_id)
        self._deps.logger.debug("Available sessions: %s", available)
        print(f"{_DBG_PREFIX} Check #{ctx.check_count}, no results yet for session {ctx.session_id}")
        print(f"{_DBG_PREFIX} Available sessions: {available}")

    def _maybe_emit_new_activity(self, ctx: _CollectorContext, count: int) -> None:
        """Trace when a new message arrives for the session."""
        if not self._deps.debug:  # WHY: Debug-only trace.
            return  # WHY: Skip when debug is off.
        delta = count - ctx.last_message_count  # WHY: Number of newly arrived messages.
        self._deps.logger.debug("New activity detected: %s messages (+%s) ", count, delta)

    def _maybe_emit_combined_trace(
        self,
        ctx: _CollectorContext,
        collected: list[dict[str, Any]],
        all_raw: str,
    ) -> None:
        """Verbose buffer trace every 50 checks - preserved verbatim from original."""
        if not self._deps.debug:  # WHY: Debug-only trace.
            return  # WHY: Skip when debug is off.
        if ctx.check_count % _TRACE_MODULUS != _TRACE_REMAINDER:  # WHY: Rate limit.
            return  # WHY: Only fire every _TRACE_MODULUS iterations.
        self._emit_buffer_summary(ctx, collected, all_raw)  # WHY: Delegate summary lines.
        if not all_raw:  # WHY: No buffer content -> skip marker scan.
            return  # WHY: Nothing to scan for ping markers.
        self._emit_ping_markers(all_raw)  # WHY: Delegate marker sweep for CC parity.

    def _emit_buffer_summary(
        self,
        ctx: _CollectorContext,
        collected: list[dict[str, Any]],
        all_raw: str,
    ) -> None:
        """Emit summary log/print block describing the current buffer state."""
        latest_raw = collected[-1].get("raw", "") if collected else ""  # WHY: Head of tail message.
        self._deps.logger.debug("Check #%s, found %s messages", ctx.check_count, len(collected))
        self._deps.logger.debug("Latest raw (first 100 chars): %s", repr(latest_raw[:100]))
        self._deps.logger.debug("Total content length: %s chars", len(all_raw))
        print(f"{_DBG_PREFIX} Check #{ctx.check_count}, found {len(collected)} messages")
        print(f"{_DBG_PREFIX} Latest raw (first 100 chars): {latest_raw[:100]!r}")
        print(f"{_DBG_PREFIX} Total content length: {len(all_raw)} chars")

    def _emit_ping_markers(self, all_raw: str) -> None:
        """Emit diagnostic hits when known ping markers appear in the buffer."""
        self._deps.logger.debug("Service ping content sample: %s", repr(all_raw[:300]))
        print(f"{_DBG_PREFIX} Service ping content sample: {all_raw[:300]!r}")
        lowered = all_raw.lower()  # WHY: Case-insensitive marker match preserved.
        for pattern in _PING_MARKERS:  # WHY: Diagnostic markers preserved verbatim.
            if pattern in lowered:  # WHY: Marker hit triggers trace.
                self._deps.logger.debug("Service ping: Found '%s' pattern", pattern)
                print(f"{_DBG_PREFIX} Service ping: Found '{pattern}' pattern")

    def _emit_completion_debug(
        self,
        indicator: str,
        collected: list[dict[str, Any]],
        all_raw: str,
        ctx: _CollectorContext,
    ) -> None:
        """Verbatim trace block emitted whenever an indicator fires."""
        if not self._deps.debug:  # WHY: Debug-only trace.
            return  # WHY: Skip when debug is off.
        self._log_completion_trace(indicator, collected, all_raw, ctx)  # WHY: Structured logger calls.
        self._print_completion_trace(indicator, collected, all_raw, ctx)  # WHY: Verbatim stdout block.

    def _log_completion_trace(
        self,
        indicator: str,
        collected: list[dict[str, Any]],
        all_raw: str,
        ctx: _CollectorContext,
    ) -> None:
        """Emit logger.debug lines describing the completion event."""
        log = self._deps.logger.debug  # WHY: Local alias trims repeated attribute access.
        log("Found completion indicator '%s' in combined content", indicator)
        log("Completing after %s checks", ctx.check_count)
        log("Total collected messages: %s", len(collected))
        log("Total content length: %s characters", len(all_raw))
        log("Raw content sample (first 200 chars): %s", repr(all_raw[:200]))
        log("Raw content sample (last 200 chars): %s", repr(all_raw[-200:]))

    def _print_completion_trace(
        self,
        indicator: str,
        collected: list[dict[str, Any]],
        all_raw: str,
        ctx: _CollectorContext,
    ) -> None:
        """Emit stdout lines describing the completion event."""
        print(f"{_DBG_PREFIX} Found completion indicator '{indicator}' in combined content")
        print(f"{_DBG_PREFIX} Completing after {ctx.check_count} checks")
        print(f"{_DBG_PREFIX} Total collected messages: {len(collected)}")
        print(f"{_DBG_PREFIX} Total content length: {len(all_raw)} characters")
        print(f"{_DBG_PREFIX} Raw content sample (first 200 chars): {all_raw[:200]!r}")
        print(f"{_DBG_PREFIX} Raw content sample (last 200 chars): {all_raw[-200:]!r}")
