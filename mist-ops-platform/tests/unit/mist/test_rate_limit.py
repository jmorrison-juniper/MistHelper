"""Tests for OrgRateLimiter.wait_and_acquire (Issue #1886).

Before this fix, the method slept once and returned, so a caller
proceeded without ever confirming it held a rate-limit slot. These
tests prove the loop retries until it truly acquires a slot, and
gives up at a bounded timeout instead of hanging forever.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from src.shared.mist.rate_limit import OrgRateLimiter

EXPECTED_ACQUIRE_CALLS_ON_IMMEDIATE_SUCCESS = 1  # WHY: no retry needed when a slot is free.
EXPECTED_ACQUIRE_CALLS_AFTER_ONE_RETRY = 2  # WHY: one retry means two acquire calls total.
EXPECTED_SLEEP_CALLS_AFTER_ONE_RETRY = 1  # WHY: one retry means exactly one sleep.
EXPECTED_ACQUIRE_CALLS_AFTER_THREE_RETRIES = 4  # WHY: three retries plus the first attempt.
FIRST_DELAY_SECONDS = 2.0  # WHY: the delay the first acquire call reports.
OVER_BOUND_DELAY_SECONDS = 40.0  # WHY: two of these exceed a 60s bound.
BOUND_SECONDS = 60.0  # WHY: the max_wait_seconds passed to the method under test.


def _make_limiter() -> OrgRateLimiter:
    """Build a limiter with a mock Redis client that acquire() never touches directly."""
    return OrgRateLimiter(AsyncMock(), "org-1")  # WHY: acquire() is patched in each test.


class TestWaitAndAcquireRetriesUntilItHoldsASlot:
    """Verify the method loops on acquire instead of sleeping once and returning."""

    async def test_it_returns_immediately_when_a_slot_is_free(self) -> None:
        limiter = _make_limiter()
        # WHY: a delay of 0 means a slot was free on the very first try.
        acquire_mock = AsyncMock(return_value=0.0)

        with patch.object(limiter, "acquire", acquire_mock):
            await limiter.wait_and_acquire()  # WHY: the call under test.

        # WHY: no retry should happen when the first attempt already succeeds.
        assert acquire_mock.call_count == EXPECTED_ACQUIRE_CALLS_ON_IMMEDIATE_SUCCESS

    async def test_it_retries_after_a_wait_and_then_succeeds(self) -> None:
        limiter = _make_limiter()
        # WHY: first call reports a wait, second call reports a free slot.
        acquire_mock = AsyncMock(side_effect=[FIRST_DELAY_SECONDS, 0.0])

        with (
            patch.object(limiter, "acquire", acquire_mock),
            patch("src.shared.mist.rate_limit.asyncio.sleep", AsyncMock()) as mock_sleep,
        ):
            await limiter.wait_and_acquire()  # WHY: the call under test.

        # WHY: this is the proof the old code lacked: a second real attempt.
        assert acquire_mock.call_count == EXPECTED_ACQUIRE_CALLS_AFTER_ONE_RETRY
        # WHY: the method must sleep the exact delay acquire() reported.
        mock_sleep.assert_awaited_once_with(FIRST_DELAY_SECONDS)
        assert mock_sleep.await_count == EXPECTED_SLEEP_CALLS_AFTER_ONE_RETRY

    async def test_it_keeps_retrying_across_several_waits(self) -> None:
        limiter = _make_limiter()
        # WHY: three waits in a row, then a free slot on the fourth attempt.
        acquire_mock = AsyncMock(side_effect=[1.0, 1.0, 1.0, 0.0])

        with (
            patch.object(limiter, "acquire", acquire_mock),
            patch("src.shared.mist.rate_limit.asyncio.sleep", AsyncMock()),
        ):
            await limiter.wait_and_acquire(max_wait_seconds=BOUND_SECONDS)

        # WHY: every one of the four attempts must have run, not just the first.
        assert acquire_mock.call_count == EXPECTED_ACQUIRE_CALLS_AFTER_THREE_RETRIES


class TestWaitAndAcquireGivesUpAtTheBound:
    """Verify the method raises instead of blocking the caller forever."""

    async def test_it_raises_timeout_error_past_the_bound(self) -> None:
        limiter = _make_limiter()
        # WHY: a constant large delay must eventually exceed the bound.
        acquire_mock = AsyncMock(return_value=OVER_BOUND_DELAY_SECONDS)

        with (
            patch.object(limiter, "acquire", acquire_mock),
            patch("src.shared.mist.rate_limit.asyncio.sleep", AsyncMock()),
            pytest.raises(TimeoutError, match="exceeded"),
        ):
            await limiter.wait_and_acquire(max_wait_seconds=BOUND_SECONDS)

    async def test_it_never_sleeps_past_what_the_bound_allows(self) -> None:
        limiter = _make_limiter()
        acquire_mock = AsyncMock(return_value=OVER_BOUND_DELAY_SECONDS)

        with (
            patch.object(limiter, "acquire", acquire_mock),
            patch("src.shared.mist.rate_limit.asyncio.sleep", AsyncMock()) as mock_sleep,
            pytest.raises(TimeoutError),
        ):
            await limiter.wait_and_acquire(max_wait_seconds=BOUND_SECONDS)

        # WHY: 40s + 40s > 60s bound, so the second sleep must never happen.
        assert mock_sleep.await_count == 1
