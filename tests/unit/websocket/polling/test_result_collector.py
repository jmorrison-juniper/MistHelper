"""Unit tests for :mod:`src.websocket.polling.result_collector`.

Why:
    Issue #878 tranche 37k un-omits ``result_collector.py`` from the coverage
    gate. The module coordinates the WebSocket command-completion polling loop
    (indicator detection, activity/absolute timeouts, emergency circuit breaker,
    verbatim debug traces). These tests exercise every helper branch so the
    module lands at ~100% coverage under ``pytest --cov`` and locks in the
    verbatim log/print prefixes that ops runbooks scrape.
"""

from __future__ import annotations

import logging
import threading
from typing import Any
from unittest.mock import MagicMock

import pytest

from src.websocket.polling import result_collector as rc_mod
from src.websocket.polling.result_collector import (
    _CB_ERROR_TMPL,
    _DBG_PREFIX,
    _DEFAULT_ACTIVITY_TIMEOUT,
    _EMERG_PREFIX,
    _MAX_CHECK_ITERATIONS,
    _PERF_LOG_INTERVAL,
    _PERF_PREFIX,
    ResultCollector,
    _CollectorContext,
    _CollectorDeps,
    _PerformanceMonitor,
)


def _make_deps(debug: bool = False) -> tuple[_CollectorDeps, dict[str, Any], threading.Lock]:
    """Build a fresh ``_CollectorDeps`` with a real lock + empty results dict.

    Why:
        Every test needs isolated shared state; helper avoids repetition and
        keeps the ``ResultCollector`` construction identical to production.
    """
    results: dict[str, Any] = {}
    lock = threading.Lock()
    logger = logging.getLogger(f"rc-test-{id(results)}")
    deps = _CollectorDeps(results=results, lock=lock, logger=logger, debug=debug)
    return deps, results, lock


def _make_collector(debug: bool = False) -> tuple[ResultCollector, dict[str, Any], threading.Lock]:
    """Build a :class:`ResultCollector` sharing state with the caller.

    Why:
        Same reasoning as :func:`_make_deps` — reduces per-test scaffolding.
    """
    results: dict[str, Any] = {}
    lock = threading.Lock()
    logger = logging.getLogger(f"rc-collector-{id(results)}")
    collector = ResultCollector(results, lock, logger, debug)
    return collector, results, lock


def _make_ctx(
    *,
    session_id: str = "sess-abcdef01",
    start_time: float = 100.0,
    activity_timeout: int = 2,
    monitor_name: str = "test-mon",
) -> _CollectorContext:
    """Build a :class:`_CollectorContext` anchored at a deterministic clock.

    Why:
        Many helper tests need a ctx without running :meth:`collect`; this
        keeps them focused on the branch under test.
    """
    return _CollectorContext(
        session_id=session_id,
        start_time=start_time,
        activity_timeout=activity_timeout,
        perf_monitor=_PerformanceMonitor(monitor_name),
    )


# ---------------------------------------------------------------------------
# _PerformanceMonitor
# ---------------------------------------------------------------------------


class TestPerformanceMonitor:
    """Exercises every branch of :class:`_PerformanceMonitor`."""

    def test_init_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Constructor snapshots wall clock and default thresholds.

        Why:
            The class is instantiated implicitly inside ``_build_context`` and
            must default to the module-level circuit-breaker limits.
        """
        monkeypatch.setattr(rc_mod.time, "time", lambda: 500.0)
        mon = _PerformanceMonitor("mon")
        assert mon.name == "mon"
        assert mon.start_time == 500.0
        assert mon.last_log_time == 500.0
        assert mon.iteration_count == 0
        assert mon.max_iterations == _MAX_CHECK_ITERATIONS
        assert mon.log_interval == _PERF_LOG_INTERVAL

    def test_init_custom_thresholds(self) -> None:
        """Constructor accepts overrides for max/interval.

        Why:
            Ensures we can build tight monitors in unit tests without waiting
            10k iterations.
        """
        mon = _PerformanceMonitor("mon", max_iterations=3, log_interval=0.5)
        assert mon.max_iterations == 3
        assert mon.log_interval == 0.5

    def test_check_iteration_increments_only(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Iteration counter advances but no [PERF] line fires without debug.

        Why:
            Verifies the ``debug_mode`` guard clause in ``_maybe_log``.
        """
        monkeypatch.setattr(rc_mod.time, "time", lambda: 0.0)
        mon = _PerformanceMonitor("mon", max_iterations=5, log_interval=1.0)
        mon.check_iteration(debug_mode=False)
        assert mon.iteration_count == 1
        assert capsys.readouterr().out == ""

    def test_maybe_log_skips_when_window_open(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Second-tick within the log window suppresses the trace line.

        Why:
            Locks the rate-limit branch of ``_maybe_log``.
        """
        times = iter([0.0, 0.1, 0.2])
        monkeypatch.setattr(rc_mod.time, "time", lambda: next(times))
        mon = _PerformanceMonitor("mon", log_interval=1.0)
        mon.check_iteration(debug_mode=True)
        assert capsys.readouterr().out == ""

    def test_maybe_log_emits_when_window_elapsed(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """After ``log_interval`` seconds the [PERF] line prints and resets.

        Why:
            Locks the emitting branch and the ``last_log_time`` reset.
        """
        clock = [0.0]

        def fake_time() -> float:
            return clock[0]

        monkeypatch.setattr(rc_mod.time, "time", fake_time)
        mon = _PerformanceMonitor("mon", log_interval=1.0)
        clock[0] = 5.0
        mon.check_iteration(debug_mode=True)
        out = capsys.readouterr().out
        assert "[PERF] mon: 1 iterations in 5.0s" in out
        assert mon.last_log_time == 5.0

    def test_check_iteration_trips_circuit_breaker(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Exceeding ``max_iterations`` raises and emits the emergency line.

        Why:
            Locks the safety net that halts runaway loops.
        """
        monkeypatch.setattr(rc_mod.time, "time", lambda: 0.0)
        mon = _PerformanceMonitor("mon", max_iterations=1, log_interval=999.0)
        mon.check_iteration(debug_mode=False)  # count=1, OK
        with pytest.raises(RuntimeError) as excinfo:
            mon.check_iteration(debug_mode=False)  # count=2 -> trip
        expected = _CB_ERROR_TMPL.format(name="mon", max_iters=1)
        assert str(excinfo.value) == expected
        assert f"{_EMERG_PREFIX} {expected}" in capsys.readouterr().out

    def test_finish_debug_off_stays_silent(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """No completion line when ``debug_mode`` is disabled.

        Why:
            Prevents ops noise in production runs.
        """
        monkeypatch.setattr(rc_mod.time, "time", lambda: 0.0)
        mon = _PerformanceMonitor("mon")
        mon.finish(debug_mode=False)
        assert capsys.readouterr().out == ""

    def test_finish_debug_on_emits_completion_line(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Debug mode prints the verbatim ``[PERF] ... completed`` line.

        Why:
            Downstream log parsers depend on this exact prefix.
        """
        clock = [0.0]
        monkeypatch.setattr(rc_mod.time, "time", lambda: clock[0])
        mon = _PerformanceMonitor("mon")
        clock[0] = 12.5
        mon.finish(debug_mode=True)
        out = capsys.readouterr().out
        assert "[PERF] mon completed: 0 iterations in 12.5s" in out


# ---------------------------------------------------------------------------
# _CollectorContext
# ---------------------------------------------------------------------------


class TestCollectorContext:
    """Locks the ``__post_init__`` defaults for the mutable context."""

    def test_post_init_seeds_activity_and_debug(self) -> None:
        """When caller leaves defaults, both timestamps mirror ``start_time``.

        Why:
            Every poll-loop rate-limit calculation subtracts from these
            timestamps; seeding them to ``start_time`` avoids off-by-huge deltas.
        """
        ctx = _make_ctx(start_time=42.0)
        assert ctx.last_activity == 42.0
        assert ctx.last_debug_time == 42.0

    def test_post_init_respects_explicit_values(self) -> None:
        """Explicit non-default values pass through unchanged.

        Why:
            Guards against a naive ``__post_init__`` that clobbers overrides.
        """
        ctx = _CollectorContext(
            session_id="s",
            start_time=100.0,
            activity_timeout=5,
            perf_monitor=_PerformanceMonitor("m"),
            last_activity=999.0,
            last_debug_time=888.0,
        )
        assert ctx.last_activity == 999.0
        assert ctx.last_debug_time == 888.0


# ---------------------------------------------------------------------------
# ResultCollector — construction + collect()
# ---------------------------------------------------------------------------


class TestResultCollectorInit:
    """Locks the constructor's dep-packing behaviour."""

    def test_packs_deps(self) -> None:
        """Constructor wires the four args into an immutable :class:`_CollectorDeps`.

        Why:
            The manager passes shared state — the collector must hold references
            (not copies) so writes from the reader thread are visible.
        """
        results: dict[str, Any] = {"a": [1]}
        lock = threading.Lock()
        logger = logging.getLogger("rc-init")
        col = ResultCollector(results, lock, logger, True)
        assert col._deps.results is results
        assert col._deps.lock is lock
        assert col._deps.logger is logger
        assert col._deps.debug is True


class TestBuildContext:
    """Locks ``_build_context`` behaviour."""

    def test_defaults_activity_timeout_when_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Passing ``None`` falls back to :data:`_DEFAULT_ACTIVITY_TIMEOUT`.

        Why:
            Preserves the original ``wait_for_command_result`` default.
        """
        monkeypatch.setattr(rc_mod.time, "time", lambda: 10.0)
        col, _results, _lock = _make_collector()
        ctx = col._build_context("abcdef1234", None)
        assert ctx.activity_timeout == _DEFAULT_ACTIVITY_TIMEOUT
        assert ctx.start_time == 10.0
        assert ctx.session_id == "abcdef1234"

    def test_explicit_activity_timeout(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Explicit int overrides the default.

        Why:
            Callers can widen the idle window for slow devices.
        """
        monkeypatch.setattr(rc_mod.time, "time", lambda: 0.0)
        col, _r, _l = _make_collector()
        ctx = col._build_context("sess", 7)
        assert ctx.activity_timeout == 7


class TestFinalize:
    """Locks ``_finalize`` for both empty and populated segment lists."""

    def test_finalize_empty_returns_none_debug_off(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Empty ``final_results`` logs a warning and returns ``None`` silently.

        Why:
            Contract: absolute-timeout with no data yields ``None``.
        """
        monkeypatch.setattr(rc_mod.time, "time", lambda: 20.0)
        col, _r, _l = _make_collector(debug=False)
        ctx = _make_ctx(start_time=10.0)
        assert col._finalize(ctx, []) is None
        assert _DBG_PREFIX not in capsys.readouterr().out

    def test_finalize_empty_debug_on_prints_trace(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Empty result in debug mode emits the ``No results collected`` line.

        Why:
            Verbatim trace preserved for ops log scrapers.
        """
        monkeypatch.setattr(rc_mod.time, "time", lambda: 20.0)
        col, _r, _l = _make_collector(debug=True)
        ctx = _make_ctx(session_id="sess-1", start_time=10.0)
        assert col._finalize(ctx, []) is None
        assert "[DEBUG] No results collected for session sess-1" in capsys.readouterr().out

    def test_finalize_non_empty_calls_combiner(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Populated ``final_results`` delegate to :func:`combine_segments`.

        Why:
            The collector must NOT reimplement segment merging.
        """
        monkeypatch.setattr(rc_mod.time, "time", lambda: 30.0)
        captured: dict[str, Any] = {}

        def fake_combine(request: rc_mod.CombineRequest) -> dict[str, Any]:
            captured["request"] = request
            return {"merged": True}

        monkeypatch.setattr(rc_mod, "combine_segments", fake_combine)
        col, _r, _l = _make_collector(debug=True)
        ctx = _make_ctx(session_id="sess-x", start_time=10.0)
        ctx.check_count = 7
        segments = [{"raw": "hello"}]
        result = col._finalize(ctx, segments)
        assert result == {"merged": True}
        req = captured["request"]
        assert req.final_results is segments
        assert req.session_id == "sess-x"
        assert req.elapsed == pytest.approx(20.0)
        assert req.check_count == 7
        assert req.debug_mode is True


# ---------------------------------------------------------------------------
# collect() end-to-end (drives the loop deterministically)
# ---------------------------------------------------------------------------


class TestCollectEndToEnd:
    """Runs :meth:`ResultCollector.collect` through the polling loop."""

    def test_collect_absolute_timeout_no_data(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Absolute timeout with no messages returns ``None``.

        Why:
            Locks the fall-through path from ``_poll_loop`` -> ``_drain_on_timeout``
            -> ``_finalize`` (empty).
        """
        clock = [1000.0]

        def fake_time() -> float:
            return clock[0]

        def fake_sleep(_secs: float) -> None:
            clock[0] += 5.0

        monkeypatch.setattr(rc_mod.time, "time", fake_time)
        monkeypatch.setattr(rc_mod.time, "sleep", fake_sleep)

        # Make CompletionDetector inert.
        detector = MagicMock()
        detector.detect.return_value = None
        monkeypatch.setattr(rc_mod, "CompletionDetector", lambda *_a, **_kw: detector)

        col, _results, _lock = _make_collector()
        assert col.collect("sess-none", timeout_seconds=3, activity_timeout_seconds=None) is None

    def test_collect_indicator_hit_returns_merged(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """When the detector fires we pop the segments and call the combiner.

        Why:
            End-to-end proof that indicator success reaches ``_finalize``.
        """
        clock = [0.0]
        monkeypatch.setattr(rc_mod.time, "time", lambda: clock[0])

        def fake_sleep(_secs: float) -> None:
            clock[0] += 0.1

        monkeypatch.setattr(rc_mod.time, "sleep", fake_sleep)

        col, results, _lock = _make_collector()
        results["sess-hit"] = [{"raw": "ok\n"}]

        detector = MagicMock()
        detector.detect.return_value = "prompt#"
        monkeypatch.setattr(rc_mod, "CompletionDetector", lambda *_a, **_kw: detector)
        monkeypatch.setattr(
            rc_mod,
            "combine_segments",
            lambda req: {"raw": "ok\n", "session": req.session_id},
        )

        out = col.collect("sess-hit", timeout_seconds=60, activity_timeout_seconds=1)
        assert out == {"raw": "ok\n", "session": "sess-hit"}
        # Segments must have been popped from the shared results dict.
        assert "sess-hit" not in results

    def test_collect_activity_timeout_drains(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Idle window elapses -> collector drains segments via the idle path.

        Why:
            Locks ``_try_activity_timeout`` firing and reaching the combiner.
        """
        clock = [0.0]
        monkeypatch.setattr(rc_mod.time, "time", lambda: clock[0])

        def fake_sleep(_secs: float) -> None:
            clock[0] += 5.0  # each sleep advances well past the 1s window

        monkeypatch.setattr(rc_mod.time, "sleep", fake_sleep)

        col, results, _lock = _make_collector()
        results["sess-idle"] = [{"raw": "output"}]

        detector = MagicMock()
        detector.detect.return_value = None  # never fires -> activity path wins
        monkeypatch.setattr(rc_mod, "CompletionDetector", lambda *_a, **_kw: detector)
        monkeypatch.setattr(
            rc_mod,
            "combine_segments",
            lambda req: {"segments": len(req.final_results)},
        )

        out = col.collect("sess-idle", timeout_seconds=60, activity_timeout_seconds=1)
        assert out == {"segments": 1}
        assert "sess-idle" not in results


# ---------------------------------------------------------------------------
# _poll_loop / _poll_once / _try_completion helpers
# ---------------------------------------------------------------------------


class TestPollLoop:
    """Locks the driver-level branches inside ``_poll_loop``."""

    def test_poll_loop_returns_immediately_on_completion(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``_poll_once`` returning a list short-circuits the wait.

        Why:
            Prevents unnecessary sleeps after completion is detected.
        """
        monkeypatch.setattr(rc_mod.time, "time", lambda: 0.0)
        sleep_calls: list[float] = []
        monkeypatch.setattr(rc_mod.time, "sleep", lambda s: sleep_calls.append(s))

        col, _r, _l = _make_collector()
        ctx = _make_ctx(start_time=0.0)
        detector = MagicMock()

        expected = [{"raw": "done"}]
        monkeypatch.setattr(col, "_poll_once", lambda _c, _d: expected)
        assert col._poll_loop(ctx, detector, timeout_seconds=10) is expected
        assert sleep_calls == []

    def test_poll_loop_drains_on_absolute_timeout(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Loop exits via ``_drain_on_timeout`` when the wall clock expires.

        Why:
            Guarantees the collector never hangs past the absolute timeout.
        """
        clock = [0.0]
        monkeypatch.setattr(rc_mod.time, "time", lambda: clock[0])

        def fake_sleep(_secs: float) -> None:
            clock[0] += 10.0  # jump past the 5s timeout

        monkeypatch.setattr(rc_mod.time, "sleep", fake_sleep)
        col, results, _l = _make_collector()
        ctx = _make_ctx(session_id="sess-drain", start_time=0.0)
        results["sess-drain"] = [{"raw": "leftover"}]

        detector = MagicMock()
        monkeypatch.setattr(col, "_poll_once", lambda _c, _d: None)
        out = col._poll_loop(ctx, detector, timeout_seconds=5)
        assert out == [{"raw": "leftover"}]
        assert "sess-drain" not in results


class TestPollOnce:
    """Locks the per-iteration ``_poll_once`` branches."""

    def test_poll_once_returns_completion_result(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """When ``_try_completion`` fires we return the segments.

        Why:
            Directly locks the indicator-driven branch.
        """
        monkeypatch.setattr(rc_mod.time, "time", lambda: 0.0)
        col, _r, _l = _make_collector()
        ctx = _make_ctx()
        detector = MagicMock()
        segments = [{"raw": "done"}]
        monkeypatch.setattr(col, "_try_completion", lambda _c, _d: segments)
        assert col._poll_once(ctx, detector) is segments
        assert ctx.check_count == 1

    def test_poll_once_falls_through_to_activity_timeout(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """No completion + count under cap -> defer to activity timeout branch.

        Why:
            Locks the None-return path used by the wait loop.
        """
        monkeypatch.setattr(rc_mod.time, "time", lambda: 0.0)
        col, _r, _l = _make_collector()
        ctx = _make_ctx()
        detector = MagicMock()
        monkeypatch.setattr(col, "_try_completion", lambda _c, _d: None)
        monkeypatch.setattr(col, "_try_activity_timeout", lambda _c: None)
        assert col._poll_once(ctx, detector) is None

    def test_poll_once_secondary_breaker(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """When ``check_count`` exceeds the cap, we drain via emergency path.

        Why:
            Defensive breaker preserves the original safety behaviour.
        """
        monkeypatch.setattr(rc_mod.time, "time", lambda: 0.0)
        col, results, _l = _make_collector()
        ctx = _make_ctx(session_id="sess-em")
        ctx.check_count = _MAX_CHECK_ITERATIONS  # after +=1 becomes cap+1
        results["sess-em"] = [{"raw": "abandoned"}]
        detector = MagicMock()
        monkeypatch.setattr(col, "_try_completion", lambda _c, _d: None)
        out = col._poll_once(ctx, detector)
        assert out == [{"raw": "abandoned"}]


class TestTryCompletion:
    """Locks every branch inside ``_try_completion``."""

    def test_returns_none_when_session_absent(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """No entry in the shared dict -> nothing to do.

        Why:
            The manager may schedule ``collect`` before any message arrives.
        """
        monkeypatch.setattr(rc_mod.time, "time", lambda: 0.0)
        col, _r, _l = _make_collector()
        ctx = _make_ctx(session_id="sess-missing")
        detector = MagicMock()
        assert col._try_completion(ctx, detector) is None

    def test_returns_none_when_empty_buffer(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Session present but empty list -> defer detection.

        Why:
            Avoid running the detector against ``""``.
        """
        monkeypatch.setattr(rc_mod.time, "time", lambda: 0.0)
        col, results, _l = _make_collector()
        results["sess-e"] = []
        ctx = _make_ctx(session_id="sess-e")
        detector = MagicMock()
        assert col._try_completion(ctx, detector) is None
        detector.detect.assert_not_called()

    def test_returns_none_when_detector_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Populated buffer + no indicator -> keep polling.

        Why:
            Locks the "keep waiting" branch.
        """
        monkeypatch.setattr(rc_mod.time, "time", lambda: 0.0)
        col, results, _l = _make_collector()
        results["sess-w"] = [{"raw": "still going"}]
        ctx = _make_ctx(session_id="sess-w")
        detector = MagicMock()
        detector.detect.return_value = None
        assert col._try_completion(ctx, detector) is None

    def test_returns_segments_when_indicator_hits(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Indicator hit pops segments and returns them.

        Why:
            The success path must clear the shared dict.
        """
        monkeypatch.setattr(rc_mod.time, "time", lambda: 0.0)
        col, results, _l = _make_collector()
        results["sess-h"] = [{"raw": "done"}]
        ctx = _make_ctx(session_id="sess-h")
        detector = MagicMock()
        detector.detect.return_value = "prompt#"
        out = col._try_completion(ctx, detector)
        assert out == [{"raw": "done"}]
        assert "sess-h" not in results


# ---------------------------------------------------------------------------
# _results_for / _refresh_activity / _try_activity_timeout
# ---------------------------------------------------------------------------


class TestResultsFor:
    """Locks ``_results_for`` — the small lookup helper."""

    def test_returns_none_when_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Missing session yields ``None`` and calls the no-results trace.

        Why:
            Guards against ``KeyError`` and drives the debug trace helper.
        """
        monkeypatch.setattr(rc_mod.time, "time", lambda: 0.0)
        col, _r, _l = _make_collector(debug=True)
        ctx = _make_ctx(session_id="sess-miss")
        ctx.check_count = 1  # matches _TRACE_REMAINDER so trace prints
        assert col._results_for(ctx) is None

    def test_returns_reference_when_present(self) -> None:
        """Present session yields the live list reference.

        Why:
            Confirms we do not copy — writes from the reader thread stay visible.
        """
        col, results, _l = _make_collector()
        results["sess-present"] = [{"raw": "x"}]
        ctx = _make_ctx(session_id="sess-present")
        out = col._results_for(ctx)
        assert out is results["sess-present"]


class TestRefreshActivity:
    """Locks the activity edge-detector."""

    def test_no_new_messages_skips_update(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Same count as last poll -> timestamps stay put.

        Why:
            Prevents idle window from resetting when no data has arrived.
        """
        monkeypatch.setattr(rc_mod.time, "time", lambda: 999.0)
        col, _r, _l = _make_collector()
        ctx = _make_ctx(start_time=100.0)
        ctx.last_message_count = 2
        collected = [{"raw": "a"}, {"raw": "b"}]
        col._refresh_activity(ctx, collected)
        assert ctx.last_activity == 100.0
        assert ctx.last_message_count == 2

    def test_new_messages_bumps_timestamp(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """New messages -> ``last_activity`` snaps to current clock.

        Why:
            Locks the freshness bookkeeping used by the idle timeout.
        """
        monkeypatch.setattr(rc_mod.time, "time", lambda: 500.0)
        col, _r, _l = _make_collector(debug=True)
        ctx = _make_ctx(start_time=100.0)
        ctx.last_message_count = 1
        collected = [{"raw": "a"}, {"raw": "b"}, {"raw": "c"}]
        col._refresh_activity(ctx, collected)
        assert ctx.last_activity == 500.0
        assert ctx.last_message_count == 3


class TestTryActivityTimeout:
    """Locks every branch of ``_try_activity_timeout``."""

    def test_returns_none_when_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """No messages yet -> cannot invoke the idle timeout.

        Why:
            Ensures we do not "complete" a session that never produced output.
        """
        monkeypatch.setattr(rc_mod.time, "time", lambda: 0.0)
        col, _r, _l = _make_collector()
        ctx = _make_ctx(session_id="sess-no")
        assert col._try_activity_timeout(ctx) is None

    def test_returns_none_when_within_window(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Time since last activity is still within the idle window -> None.

        Why:
            Locks the "keep waiting" branch.
        """
        monkeypatch.setattr(rc_mod.time, "time", lambda: 100.0)
        col, results, _l = _make_collector()
        results["sess-w"] = [{"raw": "x"}]
        ctx = _make_ctx(session_id="sess-w", activity_timeout=5, start_time=99.0)
        ctx.last_activity = 100.0
        assert col._try_activity_timeout(ctx) is None

    def test_fires_when_idle_window_elapsed(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Idle window elapsed -> drains and returns collected segments.

        Why:
            Locks the successful timeout drain and its debug trace.
        """
        monkeypatch.setattr(rc_mod.time, "time", lambda: 200.0)
        col, results, _l = _make_collector(debug=True)
        results["sess-out"] = [{"raw": "x"}, {"raw": "y"}]
        ctx = _make_ctx(session_id="sess-out", activity_timeout=1, start_time=100.0)
        ctx.last_activity = 100.0  # 100s ago >> 1s window
        out = col._try_activity_timeout(ctx)
        assert out == [{"raw": "x"}, {"raw": "y"}]
        assert "sess-out" not in results
        assert "[DEBUG] Activity timeout reached (1s)" in capsys.readouterr().out


class TestActivityTimeoutDebug:
    """Locks the standalone debug helper."""

    def test_silent_when_debug_off(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Guard clause suppresses trace outside debug mode.

        Why:
            Prod hygiene: no ``[DEBUG]`` lines when debug is disabled.
        """
        col, _r, _l = _make_collector(debug=False)
        ctx = _make_ctx()
        col._emit_activity_timeout_debug(ctx, 3)
        assert capsys.readouterr().out == ""


# ---------------------------------------------------------------------------
# _emergency_drain / _emit_emergency_debug / _drain_on_timeout
# ---------------------------------------------------------------------------


class TestEmergencyDrain:
    """Locks the secondary circuit-breaker helpers."""

    def test_drain_returns_segments(self, capsys: pytest.CaptureFixture[str]) -> None:
        """``_emergency_drain`` pops the session and returns its list.

        Why:
            Locks the drain semantics of the secondary breaker.
        """
        col, results, _l = _make_collector(debug=True)
        results["sess-em"] = [{"raw": "x"}]
        ctx = _make_ctx(session_id="sess-em")
        ctx.check_count = 12345
        out = col._emergency_drain(ctx)
        assert out == [{"raw": "x"}]
        assert "sess-em" not in results
        stdout = capsys.readouterr().out
        assert f"{_EMERG_PREFIX} Circuit breaker triggered at 12345 checks!" in stdout
        assert f"{_EMERG_PREFIX} This indicates a possible infinite loop or system hang" in stdout

    def test_drain_missing_session_returns_empty(self) -> None:
        """Absent session -> ``pop`` default returns ``[]``.

        Why:
            Locks the defensive default; downstream callers accept ``[]``.
        """
        col, _r, _l = _make_collector()
        ctx = _make_ctx(session_id="sess-nowhere")
        assert col._emergency_drain(ctx) == []

    def test_emergency_debug_silent_when_off(self, capsys: pytest.CaptureFixture[str]) -> None:
        """No prints when debug disabled — logger.error still fires elsewhere.

        Why:
            Prevents production stdout pollution.
        """
        col, _r, _l = _make_collector(debug=False)
        ctx = _make_ctx()
        ctx.check_count = 5
        col._emit_emergency_debug(ctx)
        assert capsys.readouterr().out == ""


class TestDrainOnTimeout:
    """Locks the absolute-timeout drain helper."""

    def test_debug_off_silent_and_pops(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Debug off: no trace but still drains the segments.

        Why:
            Ensures functional correctness regardless of debug flag.
        """
        col, results, _l = _make_collector(debug=False)
        results["sess-t"] = [{"raw": "leftover"}]
        ctx = _make_ctx(session_id="sess-t")
        ctx.check_count = 3
        assert col._drain_on_timeout(ctx) == [{"raw": "leftover"}]
        assert capsys.readouterr().out == ""

    def test_debug_on_emits_trace(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Debug on: verbatim trace line prints alongside the drain.

        Why:
            Locks the exact prefix that ops runbooks scrape.
        """
        col, results, _l = _make_collector(debug=True)
        results["sess-t"] = [{"raw": "leftover"}]
        ctx = _make_ctx(session_id="sess-t")
        ctx.check_count = 4
        col._drain_on_timeout(ctx)
        assert "[DEBUG] Timeout occurred after polling ended, 4 checks" in capsys.readouterr().out

    def test_drain_missing_session_returns_empty(self) -> None:
        """Session absent from results -> returns ``[]``.

        Why:
            Locks the defensive default.
        """
        col, _r, _l = _make_collector()
        ctx = _make_ctx(session_id="sess-gone")
        assert col._drain_on_timeout(ctx) == []


# ---------------------------------------------------------------------------
# _emit_start_debug / _maybe_emit_progress / _emit_progress_lines / stats
# ---------------------------------------------------------------------------


class TestEmitStartDebug:
    """Locks the verbatim startup trace."""

    def test_silent_when_debug_off(self, capsys: pytest.CaptureFixture[str]) -> None:
        """No trace lines when debug is off.

        Why:
            Startup noise would drown routine ops logs.
        """
        col, _r, _l = _make_collector(debug=False)
        ctx = _make_ctx()
        col._emit_start_debug(ctx, 30)
        assert capsys.readouterr().out == ""

    def test_prints_all_three_lines(self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        """Emits the three verbatim startup lines when debug is on.

        Why:
            Locks the exact wording ops runbooks scrape.
        """
        monkeypatch.setattr(rc_mod.time, "time", lambda: 100.0)
        col, _r, _l = _make_collector(debug=True)
        ctx = _make_ctx(session_id="sess-hello", activity_timeout=3)
        col._emit_start_debug(ctx, 60)
        out = capsys.readouterr().out
        assert "[DEBUG] Waiting for session sess-hello (timeout: 60s)" in out
        assert "[DEBUG] Current time: 100.0" in out
        assert "[DEBUG] Activity timeout: 3s)" in out


class TestMaybeEmitProgress:
    """Locks the throttled 5-second progress trace."""

    def test_skips_when_debug_off(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Debug off -> no progress trace, no state change.

        Why:
            Rate-limit branch must exit before any print.
        """
        col, _r, _l = _make_collector(debug=False)
        ctx = _make_ctx()
        col._maybe_emit_progress(ctx)
        assert capsys.readouterr().out == ""

    def test_skips_within_window(self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        """No trace when the log window has not elapsed yet.

        Why:
            Prevents ``[PERF]`` spam on tight poll cycles.
        """
        monkeypatch.setattr(rc_mod.time, "time", lambda: 100.5)
        col, _r, _l = _make_collector(debug=True)
        ctx = _make_ctx(start_time=100.0)
        col._maybe_emit_progress(ctx)
        assert capsys.readouterr().out == ""

    def test_emits_when_window_elapsed(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """After the window elapses the trace prints and the anchor resets.

        Why:
            Locks the emit branch of the rate limiter.
        """
        clock = [100.0]
        monkeypatch.setattr(rc_mod.time, "time", lambda: clock[0])
        col, results, _l = _make_collector(debug=True)
        results["sess-p"] = [{"raw": "chunk"}]
        ctx = _make_ctx(session_id="sess-p", start_time=100.0)
        ctx.check_count = 7
        ctx.last_activity = 100.0
        clock[0] = 108.0
        col._maybe_emit_progress(ctx)
        out = capsys.readouterr().out
        assert f"{_PERF_PREFIX} Check #7 at 8.0s" in out
        assert f"{_PERF_PREFIX} Last activity: 8.0s ago" in out
        assert f"{_PERF_PREFIX} Found 1 messages for our session" in out
        assert ctx.last_debug_time == 108.0


class TestEmitSessionStats:
    """Locks the two branches of ``_emit_session_stats``."""

    def test_present(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Session present -> ``Found N messages`` variant.

        Why:
            Distinct format on the present path.
        """
        col, results, _l = _make_collector(debug=True)
        results["sess-p"] = [{"raw": "a"}, {"raw": "b"}]
        ctx = _make_ctx(session_id="sess-p")
        col._emit_session_stats(ctx)
        out = capsys.readouterr().out
        assert f"{_PERF_PREFIX} Found 2 messages for our session" in out

    def test_absent(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Session absent -> ``not in results yet`` variant with available list.

        Why:
            Locks the "not yet" branch.
        """
        col, results, _l = _make_collector(debug=True)
        results["other"] = [{"raw": "x"}]
        ctx = _make_ctx(session_id="sess-missing")
        col._emit_session_stats(ctx)
        out = capsys.readouterr().out
        assert "not in results yet. Available: ['other']" in out


# ---------------------------------------------------------------------------
# _maybe_emit_no_results / _maybe_emit_new_activity / _maybe_emit_combined_trace
# ---------------------------------------------------------------------------


class TestMaybeEmitNoResults:
    """Locks the throttled no-results trace."""

    def test_silent_when_debug_off(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Debug off -> immediate return.

        Why:
            Prevents noise in prod.
        """
        col, _r, _l = _make_collector(debug=False)
        ctx = _make_ctx()
        ctx.check_count = 1
        col._maybe_emit_no_results(ctx)
        assert capsys.readouterr().out == ""

    def test_skips_when_modulus_mismatch(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Only fires on ``check_count % 50 == 1``.

        Why:
            Locks the rate-limit branch.
        """
        col, _r, _l = _make_collector(debug=True)
        ctx = _make_ctx()
        ctx.check_count = 2
        col._maybe_emit_no_results(ctx)
        assert capsys.readouterr().out == ""

    def test_emits_on_modulus_hit(self, capsys: pytest.CaptureFixture[str]) -> None:
        """First modulus hit prints the two trace lines.

        Why:
            Locks the emit branch.
        """
        col, results, _l = _make_collector(debug=True)
        results["other"] = [{"raw": "x"}]
        ctx = _make_ctx(session_id="sess-void")
        ctx.check_count = 51  # 51 % 50 == 1
        col._maybe_emit_no_results(ctx)
        out = capsys.readouterr().out
        assert "[DEBUG] Check #51, no results yet for session sess-void" in out
        assert "[DEBUG] Available sessions: ['other']" in out


class TestMaybeEmitNewActivity:
    """Locks the new-activity trace helper."""

    def test_silent_when_debug_off(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Debug off -> no logger call.

        Why:
            Verifies the guard clause.
        """
        col, _r, _l = _make_collector(debug=False)
        ctx = _make_ctx()
        col._maybe_emit_new_activity(ctx, 10)
        assert capsys.readouterr().out == ""

    def test_logs_delta_when_debug_on(self, caplog: pytest.LogCaptureFixture) -> None:
        """Debug on -> emits logger.debug with the delta count.

        Why:
            Locks the diagnostic content.
        """
        col, _r, _l = _make_collector(debug=True)
        col._deps.logger.setLevel(logging.DEBUG)
        ctx = _make_ctx()
        ctx.last_message_count = 2
        with caplog.at_level(logging.DEBUG, logger=col._deps.logger.name):
            col._maybe_emit_new_activity(ctx, 5)
        assert any("New activity detected: 5 messages (+3)" in rec.message for rec in caplog.records)


class TestMaybeEmitCombinedTrace:
    """Locks the throttled 50-check verbose trace."""

    def test_silent_when_debug_off(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Debug off -> immediate return.

        Why:
            Guard clause branch.
        """
        col, _r, _l = _make_collector(debug=False)
        ctx = _make_ctx()
        ctx.check_count = 1
        col._maybe_emit_combined_trace(ctx, [{"raw": "x"}], "x")
        assert capsys.readouterr().out == ""

    def test_skips_off_modulus(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Only fires when ``check_count % 50 == 1``.

        Why:
            Locks the rate-limit branch.
        """
        col, _r, _l = _make_collector(debug=True)
        ctx = _make_ctx()
        ctx.check_count = 25
        col._maybe_emit_combined_trace(ctx, [{"raw": "x"}], "x")
        assert capsys.readouterr().out == ""

    def test_emits_summary_without_markers_when_raw_empty(self, capsys: pytest.CaptureFixture[str]) -> None:
        """When ``all_raw`` is empty we emit the summary but skip marker scan.

        Why:
            Locks the ``if not all_raw`` short-circuit branch.
        """
        col, _r, _l = _make_collector(debug=True)
        ctx = _make_ctx()
        ctx.check_count = 1  # matches modulus
        col._maybe_emit_combined_trace(ctx, [{"raw": ""}], "")
        out = capsys.readouterr().out
        assert "[DEBUG] Check #1, found 1 messages" in out
        assert "Service ping content sample" not in out

    def test_emits_markers_when_all_three_hit(self, capsys: pytest.CaptureFixture[str]) -> None:
        """All three ping markers present -> each emits a diagnostic line.

        Why:
            Locks the full ping-marker scan branch.
        """
        col, _r, _l = _make_collector(debug=True)
        ctx = _make_ctx()
        ctx.check_count = 1
        raw = "64 bytes from 1.2.3.4 seq=1 time=0.5 ms"
        col._maybe_emit_combined_trace(ctx, [{"raw": raw}], raw)
        out = capsys.readouterr().out
        assert "[DEBUG] Service ping: Found 'bytes from' pattern" in out
        assert "[DEBUG] Service ping: Found 'seq=' pattern" in out
        assert "[DEBUG] Service ping: Found 'time=' pattern" in out


class TestEmitBufferSummary:
    """Locks the small summary print block."""

    def test_empty_collected(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Empty list -> latest_raw defaults to ``""``.

        Why:
            Guards against IndexError on the tail-message path.
        """
        col, _r, _l = _make_collector(debug=True)
        ctx = _make_ctx()
        ctx.check_count = 5
        col._emit_buffer_summary(ctx, [], "")
        out = capsys.readouterr().out
        assert "[DEBUG] Check #5, found 0 messages" in out
        assert "[DEBUG] Latest raw (first 100 chars): ''" in out


# ---------------------------------------------------------------------------
# _emit_completion_debug / _log_completion_trace / _print_completion_trace
# ---------------------------------------------------------------------------


class TestEmitCompletionDebug:
    """Locks the completion-trace fan-out."""

    def test_silent_when_debug_off(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Debug off -> no logger or stdout trace.

        Why:
            Guard clause.
        """
        col, _r, _l = _make_collector(debug=False)
        ctx = _make_ctx()
        col._emit_completion_debug("done", [{"raw": "x"}], "x", ctx)
        assert capsys.readouterr().out == ""

    def test_emits_full_trace(
        self,
        capsys: pytest.CaptureFixture[str],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Debug on -> emits all six log + six print lines.

        Why:
            Locks the verbatim trace ops depends on.
        """
        col, _r, _l = _make_collector(debug=True)
        col._deps.logger.setLevel(logging.DEBUG)
        ctx = _make_ctx(session_id="sess-c")
        ctx.check_count = 9
        with caplog.at_level(logging.DEBUG, logger=col._deps.logger.name):
            col._emit_completion_debug("prompt#", [{"raw": "hello"}], "hello", ctx)
        out = capsys.readouterr().out
        assert "[DEBUG] Found completion indicator 'prompt#' in combined content" in out
        assert "[DEBUG] Completing after 9 checks" in out
        assert "[DEBUG] Total collected messages: 1" in out
        assert "[DEBUG] Total content length: 5 characters" in out
        assert "[DEBUG] Raw content sample (first 200 chars): 'hello'" in out
        assert "[DEBUG] Raw content sample (last 200 chars): 'hello'" in out
        messages = " ".join(rec.message for rec in caplog.records)
        assert "Found completion indicator" in messages
        assert "Completing after 9 checks" in messages
