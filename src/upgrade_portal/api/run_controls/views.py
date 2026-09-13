"""Assess the age and stale state of one upgrade run.

Why:
    The history page and the run page must use one rule and one clock value.
    This module keeps that decision independent from page rendering.
"""

from __future__ import annotations  # Keep annotations independent from import order.

import logging  # Record each stale assessment without a run identifier.
from collections.abc import Mapping  # Accept each stored run record without a concrete store type.
from dataclasses import dataclass  # Build the immutable assessment value.
from datetime import UTC, datetime  # Normalize stored offsets and the supplied clock.
from typing import Any  # Stored run fields can contain different JSON-compatible values.

from ...runtime.runs import RunState, RunStateMachine, RunTransitionError  # Use the canonical state authority.

logger = logging.getLogger(__name__)  # Keep stale policy records tied to this module.


@dataclass(frozen=True, slots=True)
class StaleAssessment:  # Return one value that no page adapter can change.
    """Hold the normalized age and stale decision for one run."""

    updated_at: str  # Give the page the normalized UTC time, or empty text.
    age_seconds: int | None  # Give scripts the whole age, or no value.
    age_text: str  # Give the operator a short age, or `unknown`.
    is_stale: bool  # Mark only a nonfinal run at or above the limit.
    reason: str  # Give tests and later actions one stable decision reason.


class RunStalePolicy:  # Own the one stale rule that every page uses.
    """Assess one run against one supplied UTC clock value."""

    def __init__(self, clock: datetime) -> None:  # Bind all assessments to one caller-supplied clock.
        """Store one aware clock value in UTC."""
        logger.info("Validate the stale policy clock")  # Record the validation before conversion.
        if clock.tzinfo is None or clock.utcoffset() is None:  # A naive clock cannot give a safe age.
            logger.error("The stale policy clock has no time zone")  # State the invalid condition.
            raise ValueError("The stale policy clock must include a time zone.")  # Fail before an unsafe decision.
        self._clock = clock.astimezone(UTC)  # Use one UTC value for every assessment from this policy.
        logger.debug("The stale policy clock is ready in UTC")  # Confirm the safe normalized clock.

    def assess(self, run: Mapping[str, Any]) -> StaleAssessment:  # Apply the shared age and state rules.
        """Return the age and stale decision for one stored run."""
        logger.info("Assess one upgrade run age")  # Record the decision before any time parsing.
        updated_at, invalid_reason = self._parse_updated_at(run.get("updated_at"))  # Parse one stored value.
        if updated_at is None:  # A missing or malformed time has no safe age.
            result = StaleAssessment("", None, "unknown", False, invalid_reason)  # Fail closed with a stable reason.
            logger.debug("The run age is unknown because %s", result.reason)  # Report only the safe reason.
            return result  # No stale action can use an unknown time.
        elapsed = (self._clock - updated_at).total_seconds()  # Compare the normalized values once.
        if elapsed < 0:  # A future update cannot prove that a run is stale.
            result = StaleAssessment("", None, "unknown", False, "updated_at_future")  # Keep the future value hidden.
            logger.debug("The run age is unknown because %s", result.reason)  # Report only the stable reason.
            return result  # A future time always fails closed.
        age_seconds = int(elapsed)  # Use whole elapsed seconds for the exact threshold.
        state = self._read_state(run)  # Use the canonical state model for terminal membership.
        is_stale = state is not None and state not in RunStateMachine.TERMINAL and age_seconds >= 86400  # Exact day.
        reason = "run_state_unknown"  # Use a safe default for an invalid stored state.
        if state is not None:  # A known state can receive the current or stale reason.
            reason = "run_stale" if is_stale else "run_current"  # Name the exact age decision.
        if state in RunStateMachine.TERMINAL:  # A terminal run can show an age but can never be stale.
            reason = "run_terminal"  # Name the terminal override without a second state set.
        result = StaleAssessment(updated_at.isoformat(), age_seconds, self._age_text(age_seconds), is_stale, reason)
        logger.debug("The run age assessment is %s at %s second(s)", result.reason, result.age_seconds)  # Safe summary.
        return result  # Give both page adapters the same immutable value.

    @staticmethod
    def _parse_updated_at(value: Any) -> tuple[datetime | None, str]:  # Parse and normalize one stored time.
        """Return one UTC time and an empty reason, or one stable failure reason."""
        if value is None or value == "":  # An absent or empty field is a missing stored time.
            return None, "updated_at_missing"  # Keep missing data distinct from bad data.
        if not isinstance(value, str):  # A non-text stored value cannot be an ISO 8601 time.
            return None, "updated_at_malformed"  # Refuse the unsupported stored type.
        try:  # ISO parsing accepts valid positive and negative offsets.
            parsed = datetime.fromisoformat(value)  # Read the stored ISO 8601 value.
        except ValueError:  # A malformed value cannot produce a safe age.
            return None, "updated_at_malformed"  # Return the stable parse reason.
        if parsed.tzinfo is None or parsed.utcoffset() is None:  # A time with no offset is ambiguous.
            return None, "updated_at_malformed"  # Treat a naive value as malformed.
        return parsed.astimezone(UTC), ""  # Normalize every valid offset before age calculation.

    @staticmethod
    def _age_text(age_seconds: int) -> str:  # Format one nonnegative whole-second age.
        """Return a short age that fits a table cell."""
        days, day_remainder = divmod(age_seconds, 86400)  # Split complete days from the remainder.
        hours, hour_remainder = divmod(day_remainder, 3600)  # Split complete hours from the remainder.
        minutes, seconds = divmod(hour_remainder, 60)  # Split complete minutes from the remainder.
        if days:  # A day-scale age needs days and optional hours only.
            return f"{days}d {hours}h" if hours else f"{days}d"  # Keep the text short and stable.
        if hours:  # An hour-scale age needs hours and optional minutes only.
            return f"{hours}h {minutes}m" if minutes else f"{hours}h"  # Keep the two largest units.
        return f"{minutes}m" if minutes else f"{seconds}s"  # Show one useful unit below one hour.

    @staticmethod
    def _read_state(run: Mapping[str, Any]) -> RunState | None:  # Read one state through the canonical model.
        """Return the canonical state, or no state for an invalid record."""
        try:  # A damaged record must not produce a stale action.
            return RunStateMachine.read_state(run)  # Use the canonical state parser and no copied state set.
        except RunTransitionError:  # An unknown state cannot prove stale eligibility.
            return None  # Fail closed while the page can still show the known age.
