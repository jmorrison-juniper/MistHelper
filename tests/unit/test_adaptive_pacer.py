"""Unit tests for the AdaptivePacer quota-aware pacing class.

These tests cover issues #1695 through #1699. Each of those issues replaced a
hard-coded sleep in a bulk write loop with the PID rate limiter. The tests
prove three properties. The pacer asks the rate limiter for every delay. The
pacer carries the smoothed PID state between iterations. A disabled pacer
performs no sleep, so a dry run costs no wall-clock time.
"""

from __future__ import annotations  # WHY: enable PEP 604 unions on the helper signatures.

from typing import Any  # WHY: the fake session and cache are duck-typed stand-ins.

import pytest  # WHY: fixtures and monkeypatch drive the isolation of the sleep call.

from src.utils import rate_limiting  # WHY: patch the module attributes the pacer reads.
from src.utils.rate_limiting import AdaptivePacer  # WHY: the class under test.


class _DelayRecorder:  # WHY: capture every rate-limiter call so a test can assert the sequence.
    """Record each get_rate_limited_delay call and return a scripted result."""

    def __init__(self, results: list[tuple[float | None, float]]) -> None:
        """Store the scripted results and prepare the call log."""
        self._results = list(results)  # WHY: copy so the caller list stays unchanged.
        self.calls: list[tuple[float | None, Any, Any]] = []  # WHY: one entry per call for assertions.

    def __call__(
        self, smoothed_delay: float | None = None, apisession: Any = None, api_usage_cache: Any = None
    ) -> tuple[float | None, float]:
        """Log the arguments and return the next scripted result."""
        self.calls.append((smoothed_delay, apisession, api_usage_cache))  # WHY: record the exact inputs.
        if self._results:  # WHY: fall back to a constant once the script runs out.
            return self._results.pop(0)  # WHY: consume the scripted results in order.
        return smoothed_delay, 0.0  # WHY: a stable tail keeps a long loop from raising IndexError.


@pytest.fixture
def no_sleep(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    """Replace time.sleep with a recorder so the test suite never waits."""
    slept: list[float] = []  # WHY: collect every requested wait for assertions.
    monkeypatch.setattr(rate_limiting.time, "sleep", slept.append)  # WHY: remove real wall-clock delay.
    return slept  # WHY: hand the log to the test body.


def test_pace_asks_the_rate_limiter_and_sleeps(monkeypatch: pytest.MonkeyPatch, no_sleep: list[float]) -> None:
    """The pacer must request a delay and then wait for exactly that delay."""
    recorder = _DelayRecorder([(0.4, 0.4)])  # WHY: one scripted call returns a 0.4 second delay.
    monkeypatch.setattr(rate_limiting.RateLimitingUtils, "get_rate_limited_delay", recorder)  # WHY: isolate PID.
    pacer = AdaptivePacer(apisession="session", api_usage_cache={"limit": 5000})  # WHY: build the object under test.

    waited = pacer.pace()  # WHY: exercise the single public entry point.

    assert waited == 0.4  # WHY: the pacer must report the delay it applied.
    assert no_sleep == [0.4]  # WHY: the pacer must sleep one time for the computed delay.
    assert len(recorder.calls) == 1  # WHY: one pace call means one rate-limiter call.


def test_pace_carries_the_smoothed_delay_between_iterations(
    monkeypatch: pytest.MonkeyPatch, no_sleep: list[float]
) -> None:
    """The pacer must feed the previous smoothed delay into the next call."""
    recorder = _DelayRecorder([(0.2, 0.2), (0.6, 0.6), (0.9, 0.9)])  # WHY: three iterations of a bulk loop.
    monkeypatch.setattr(rate_limiting.RateLimitingUtils, "get_rate_limited_delay", recorder)  # WHY: isolate PID.
    pacer = AdaptivePacer(apisession="session", api_usage_cache={"limit": 5000})  # WHY: object under test.

    for _ in range(3):  # WHY: simulate a three-item bulk write loop.
        pacer.pace()  # WHY: each iteration must advance the PID state.

    smoothed_inputs = [call[0] for call in recorder.calls]  # WHY: read the first argument of every call.
    assert smoothed_inputs == [None, 0.2, 0.6]  # WHY: the state must carry forward, not reset to None.
    assert pacer.smoothed_delay == 0.9  # WHY: the final smoothed value must remain readable.
    assert no_sleep == [0.2, 0.6, 0.9]  # WHY: every iteration waits for its own computed delay.


def test_pace_passes_the_shared_session_and_cache(monkeypatch: pytest.MonkeyPatch, no_sleep: list[float]) -> None:
    """The pacer must forward the injected session and the shared usage cache."""
    recorder = _DelayRecorder([(0.1, 0.1)])  # WHY: a single call is enough to inspect the arguments.
    monkeypatch.setattr(rate_limiting.RateLimitingUtils, "get_rate_limited_delay", recorder)  # WHY: isolate PID.
    shared_cache = {"limit": 5000, "used": 10}  # WHY: stand in for the module-level MistHelper cache.
    pacer = AdaptivePacer(apisession="live-session", api_usage_cache=shared_cache)  # WHY: object under test.

    pacer.pace()  # WHY: trigger the single rate-limiter call.

    _, session, cache = recorder.calls[0]  # WHY: unpack the recorded arguments.
    assert session == "live-session"  # WHY: the PID pipeline needs the live session to read the quota.
    assert cache is shared_cache  # WHY: identity proves every menu shares one quota view.


def test_disabled_pacer_never_sleeps(monkeypatch: pytest.MonkeyPatch, no_sleep: list[float]) -> None:
    """A disabled pacer must report a zero wait and must not call the rate limiter."""
    recorder = _DelayRecorder([(0.5, 0.5)])  # WHY: a call would show up here if the guard failed.
    monkeypatch.setattr(rate_limiting.RateLimitingUtils, "get_rate_limited_delay", recorder)  # WHY: isolate PID.
    pacer = AdaptivePacer(apisession="session", api_usage_cache={}, enabled=False)  # WHY: model a dry run.

    waited = pacer.pace()  # WHY: a dry run must return immediately.

    assert waited == 0.0  # WHY: a dry run sends no request, so it must not wait.
    assert no_sleep == []  # WHY: no sleep may occur in a dry run.
    assert recorder.calls == []  # WHY: a dry run must not spend a rate-limiter cycle either.


def test_next_delay_computes_without_sleeping(monkeypatch: pytest.MonkeyPatch, no_sleep: list[float]) -> None:
    """next_delay must return the delay and update the state without waiting."""
    recorder = _DelayRecorder([(0.7, 0.7)])  # WHY: one scripted result is enough.
    monkeypatch.setattr(rate_limiting.RateLimitingUtils, "get_rate_limited_delay", recorder)  # WHY: isolate PID.
    pacer = AdaptivePacer(apisession=None, api_usage_cache={})  # WHY: object under test.

    delay = pacer.next_delay()  # WHY: exercise the computation-only entry point.

    assert delay == 0.7  # WHY: the caller decides whether to wait for this delay.
    assert pacer.smoothed_delay == 0.7  # WHY: the state must advance even without a sleep.
    assert no_sleep == []  # WHY: next_delay must never sleep by itself.


def test_missing_cache_falls_back_without_raising(no_sleep: list[float]) -> None:
    """A pacer built without a cache must still return a usable fallback delay."""
    pacer = AdaptivePacer(apisession=None, api_usage_cache=None)  # WHY: model a wire-up that forgot the cache.

    delay = pacer.next_delay()  # WHY: the real rate limiter runs here, with no cache available.

    assert delay > 0.0  # WHY: a missing cache must degrade to a safe non-zero delay, not to zero.
    assert no_sleep == []  # WHY: next_delay must never sleep by itself.
