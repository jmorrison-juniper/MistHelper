"""Prove the shared stale policy and canonical final-state decisions."""

from __future__ import annotations  # Keep annotations independent from import order.

from dataclasses import FrozenInstanceError  # Prove that a page cannot change an assessment.
from datetime import UTC, datetime, timedelta, timezone  # Build exact age boundaries and valid offsets.
from typing import Any  # The in-memory run store carries JSON-compatible records.

import pytest  # Parametrize every canonical terminal state.

from src.upgrade_portal.api.run_controls.views import RunStalePolicy  # Test the shared stale decision.
from src.upgrade_portal.app.routes import review, upgrade  # Test history and live-run decisions.
from src.upgrade_portal.runtime import signals  # Test the stop decision and removed legacy set.
from src.upgrade_portal.runtime.runs import RunStateMachine  # Read the only terminal-state authority.

TERMINAL_NAMES = tuple(sorted(state.value for state in RunStateMachine.TERMINAL))  # Use the canonical values.
CLOCK = datetime(2026, 9, 11, 8, 0, 0, tzinfo=UTC)  # Keep every boundary independent from wall time.


class RunStore:  # Hold one final run for the focused stop tests.
    """Hold one run record for the stop decision."""

    def __init__(self, state: str) -> None:  # Build one record in the requested state.
        """Create one record in the requested state."""
        self.record: dict[str, Any] = {  # Give the stop store only the fields it reads.
            "run_id": "run-terminal-test",
            "state": state,
            "stop_request": None,
            "updated_at": "2026-09-11T00:00:00+00:00",
        }

    def read_run(self, run_id: str) -> dict[str, Any] | None:  # Read the single test record.
        """Return the single record."""
        del run_id  # One record answers every identifier in this focused test.
        return dict(self.record)  # A copy models a storage round trip.

    def write_run(self, run: dict[str, Any]) -> bool:  # Store one changed test record.
        """Store one changed record."""
        self.record = dict(run)  # A copy protects the stored value.
        return True  # The stand-in never refuses a write.


def test_legacy_terminal_sets_are_removed() -> None:  # Prove both divergent authorities are absent.
    """The two old terminal authorities no longer exist."""
    assert not hasattr(signals, "TERMINAL_RUN_STATES")  # Stop decisions must use the state machine.
    assert not hasattr(review, "FINISHED_RUN_STATES")  # History decisions must use the state machine.


@pytest.mark.parametrize("state", TERMINAL_NAMES)
def test_each_terminal_state_is_not_live(state: str) -> None:  # Prove the live-run decision for one final state.
    """A canonical terminal state cannot count as a live run."""
    assert upgrade.run_is_live({"state": state}) is False  # Live-run guards use the canonical terminal set.


@pytest.mark.parametrize("state", TERMINAL_NAMES)
def test_each_terminal_state_has_a_history_end(state: str) -> None:  # Prove the history decision for one final state.
    """A canonical terminal state uses its final update as the history end."""
    record = {"state": state, "updated_at": "2026-09-11T00:00:00+00:00"}  # Give the view one final moment.
    assert review.run_end_moment(record, state) == record["updated_at"]  # History uses the canonical set.


@pytest.mark.parametrize("state", TERMINAL_NAMES)
def test_each_terminal_state_refuses_a_stop(state: str) -> None:  # Prove the stop decision for one final state.
    """A canonical terminal state refuses a new stop request."""
    store = signals.StopRequestStore(RunStore(state))  # Bind the stop decision to one terminal record.
    with pytest.raises(signals.RunNotStoppableError):  # A final run must fail closed.
        store.request("run-terminal-test", "operator@example.invalid", "STOP")  # Exercise the real stop guard.


@pytest.mark.parametrize(  # Cover the second before, at, and after the exact limit.
    ("age", "expected_stale", "expected_text"),  # Name each visible and eligibility result.
    (
        (timedelta(hours=23, minutes=59, seconds=59), False, "23h 59m"),  # One second remains.
        (timedelta(hours=24), True, "1d"),  # The run becomes stale at the exact limit.
        (timedelta(hours=24, seconds=1), True, "1d"),  # A run stays stale after the limit.
    ),
)
def test_stale_boundary_uses_exactly_24_hours(  # Prove the exact threshold without a wall clock.
    age: timedelta,
    expected_stale: bool,
    expected_text: str,
) -> None:
    """A nonfinal run becomes stale at exactly 24 hours."""
    updated_at = CLOCK - age  # Build the stored time from the one supplied clock.
    assessment = RunStalePolicy(CLOCK).assess(  # Assess through the public policy.
        {"state": "created", "updated_at": updated_at.isoformat()}  # Supply one valid nonfinal record.
    )
    assert assessment.age_seconds == int(age.total_seconds())  # Keep exact whole-second age evidence.
    assert assessment.age_text == expected_text  # Keep the short operator text stable.
    assert assessment.is_stale is expected_stale  # Apply the threshold at 86400 seconds.
    assert assessment.reason == ("run_stale" if expected_stale else "run_current")  # Keep a stable reason.


@pytest.mark.parametrize("state", TERMINAL_NAMES)  # Use every state from the canonical terminal authority.
def test_terminal_runs_show_age_and_never_become_stale(state: str) -> None:
    """Every terminal run can show an old age without a stale result."""
    assessment = RunStalePolicy(CLOCK).assess(  # Use the same policy as both pages.
        {"state": state, "updated_at": (CLOCK - timedelta(days=7)).isoformat()}  # Give the final run an old time.
    )
    assert assessment.age_seconds == 604800  # The terminal override keeps the measured age.
    assert assessment.age_text == "7d"  # The visible age remains available.
    assert assessment.is_stale is False  # No terminal state can become stale.
    assert assessment.reason == "run_terminal"  # Name the canonical terminal override.


def test_valid_offset_normalizes_to_utc() -> None:  # Prove an offset does not change the age.
    """A valid stored offset becomes the equivalent UTC time."""
    eastern = timezone(timedelta(hours=-4))  # Build one valid negative offset.
    stored = datetime(2026, 9, 10, 4, 0, 0, tzinfo=eastern)  # This value equals 08:00 UTC.
    assessment = RunStalePolicy(CLOCK).assess(  # Assess the offset through the shared policy.
        {"state": "created", "updated_at": stored.isoformat()}  # Supply the offset form as stored text.
    )
    assert assessment.updated_at == "2026-09-10T08:00:00+00:00"  # Publish one normalized UTC value.
    assert assessment.age_seconds == 86400  # Preserve the exact instant through normalization.
    assert assessment.is_stale is True  # The normalized instant sits at the exact limit.


@pytest.mark.parametrize(  # Cover each unsafe stored time from the specification.
    ("record", "reason"),  # Bind one record shape to its stable refusal reason.
    (
        ({"state": "created"}, "updated_at_missing"),  # No field gives no age.
        ({"state": "created", "updated_at": ""}, "updated_at_missing"),  # Empty text is missing.
        ({"state": "created", "updated_at": "not-a-time"}, "updated_at_malformed"),  # Bad ISO text is malformed.
        ({"state": "created", "updated_at": "2026-09-10T08:00:00"}, "updated_at_malformed"),  # No offset is unsafe.
        ({"state": "created", "updated_at": "2026-09-11T08:00:01+00:00"}, "updated_at_future"),  # Future time.
    ),
)
def test_unknown_times_fail_closed(record: dict[str, str], reason: str) -> None:
    """A missing, malformed, or future time produces one unknown age."""
    assessment = RunStalePolicy(CLOCK).assess(record)  # Assess the unsafe record with one fixed clock.
    assert assessment.updated_at == ""  # Do not publish an unsafe time to browser updates.
    assert assessment.age_seconds is None  # No unsafe value can become a numeric age.
    assert assessment.age_text == "unknown"  # Give the operator the required visible result.
    assert assessment.is_stale is False  # Unknown time never grants stale eligibility.
    assert assessment.reason == reason  # Keep the refusal reason stable for later actions.


def test_assessment_is_immutable() -> None:  # Prove one adapter cannot change the shared decision.
    """A stale assessment cannot change after the policy returns it."""
    assessment = RunStalePolicy(CLOCK).assess(  # Build one complete immutable result.
        {"state": "created", "updated_at": (CLOCK - timedelta(days=1)).isoformat()}  # Exact stale boundary.
    )
    with pytest.raises(FrozenInstanceError):  # A frozen dataclass must reject a field write.
        assessment.age_text = "changed"  # type: ignore[misc]  # Attempt the prohibited mutation.
