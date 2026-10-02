"""Prove that the counted cloud and start checks cannot accept a nonzero call count."""

from __future__ import annotations

import pytest

from tests.e2e.upgrade_portal.strategy_failure_limit.portal import FailureLimitPortal


class TestBoundaryCounts:
    """Exercise each transport refusal and the final zero-call decision directly."""

    @pytest.mark.parametrize("method", ["mist_get", "mist_post", "mist_put", "mist_delete"])
    def test_an_sdk_attempt_fails_the_zero_call_check(self, monkeypatch: pytest.MonkeyPatch, method: str) -> None:
        """An actual call at the SDK boundary increments the counter and then fails the safety check."""
        portal = FailureLimitPortal(monkeypatch)
        with pytest.raises(RuntimeError, match="SDK .* is forbidden"):
            getattr(portal.cloud, method)("controlled-test-call")
        assert (portal.cloud.calls, portal.starts.call_count) == (1, 0)
        with pytest.raises(AssertionError, match="calls must remain zero"):
            portal.require_idle()

    def test_a_start_attempt_fails_the_zero_call_check(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A call at the firmware boundary must not disappear from the measured result."""
        portal = FailureLimitPortal(monkeypatch)
        with pytest.raises(RuntimeError, match="Firmware work is forbidden"):
            portal.starts({"run_id": "direct-negative-control"})
        assert (portal.cloud.calls, portal.starts.call_count) == (0, 1)
        with pytest.raises(AssertionError, match="calls must remain zero"):
            portal.require_idle()
