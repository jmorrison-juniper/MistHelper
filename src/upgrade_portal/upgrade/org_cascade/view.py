"""The page view of the phase watch of one multi-site upgrade.

Why:
    Issue #3245. The multi-site progress page and the status poll show the
    four cascade phases in the single-site shape. This module builds the
    fields of both from the durable record, so the page and the poll always
    agree.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any, Final

from src.upgrade_portal.upgrade.org_cascade.record import (
    NO_CHILD_NOTE,
    SUBMISSION_OPEN_STATES,
    WATCH_KEY,
    OrgPhaseEntries,
    OrgPhaseTargets,
    OrgPhaseWatch,
    WatchState,
)

logger = logging.getLogger(__name__)  # One logger for the phase fields of the multi-site page.

# WHY: The page shows one short label for each watch state.
WATCH_LABELS: Final[Mapping[str, str]] = {  # The single-site page uses the same six words.
    WatchState.NOT_STARTED.value: "Not started",
    WatchState.WAITING_FOR_START.value: "Scheduled",
    WatchState.RUNNING.value: "Active",
    WatchState.FINISHED.value: "Finished",
    WatchState.STOPPED.value: "Stopped",
    WatchState.FAILED.value: "Failed",
}

# WHY: FR-017. The poll continues while the watch holds one of these states.
ACTIVE_WATCH_STATES: Final[frozenset[str]] = frozenset(  # A later start or a running watch keeps the poll.
    {WatchState.WAITING_FOR_START.value, WatchState.RUNNING.value}
)


class OrgPhaseView:
    """Build the phase fields of the multi-site page and the status poll."""

    @staticmethod
    def build(record: Mapping[str, Any]) -> dict[str, Any]:
        """Return the phases, the watch line, and the poll flag of one record.

        Args:
            record: The durable operation record.

        Returns:
            The three view fields. A record of an earlier release gets an empty phase list.
        """
        watch = record.get(WATCH_KEY)  # The watch fields that the submission stored.
        if not isinstance(watch, Mapping):  # A record of an earlier release holds no watch.
            logger.debug(  # After the read. A record of an earlier release holds no watch.
                "org cascade: the record holds no phase watch, so the page shows no phase card"
            )
            return {"phases": [], "phase_watch": None, "phase_active": False}  # FR-013: no phase card.
        state = OrgPhaseWatch.state_of(record)  # The stored watch state.
        no_child = OrgPhaseView._no_child(record)  # The submission ended with no accepted child job.
        return {
            "phases": OrgPhaseEntries.of(record),  # The four entries in the single-site shape.
            "phase_watch": OrgPhaseView._watch_line(watch, state, no_child),  # The watch line of the page.
            "phase_active": OrgPhaseView._active(state, no_child),  # FR-017: the poll continues while True.
        }

    @staticmethod
    def _watch_line(watch: Mapping[str, Any], state: str, no_child: bool) -> dict[str, Any]:
        """Return the watch line fields of the page.

        Args:
            watch: The stored watch fields.
            state: The watch state.
            no_child: True when the cloud accepted no child job.

        Returns:
            The state, the label, the note, the first failure, and the anchor gap note.
        """
        note = str(watch.get("note") or "")  # The sentence that the walk wrote.
        if state == WatchState.NOT_STARTED.value and no_child:  # FR-005: no watch can start.
            note = NO_CHILD_NOTE  # Tell the operator why no phase moves.
        return {
            "state": state,  # The machine state for the test and the paint.
            "label": WATCH_LABELS.get(state, state),  # The short label of the page.
            "note": note,  # The sentence of the page.
            "reason": watch.get("reason"),  # FR-007: the first failure, or None.
            "anchor_note": str(watch.get("anchor_note") or ""),  # FR-002: the gap note of the anchor read.
        }

    @staticmethod
    def _active(state: str, no_child: bool) -> bool:
        """Return True when the page must keep the poll alive for the watch."""
        if state in ACTIVE_WATCH_STATES:  # A thread waits for the start or for a phase.
            return True  # The counts can still change.
        return state == WatchState.NOT_STARTED.value and not no_child  # The next poll starts the watch.

    @staticmethod
    def _no_child(record: Mapping[str, Any]) -> bool:
        """Return True when the submission ended and the cloud accepted no child job."""
        if str(record.get("state", "")) in SUBMISSION_OPEN_STATES:  # The submission can still accept a child.
            return False  # Wait for the end of the submission.
        return OrgPhaseTargets.accepted_count(record) == 0  # FR-005: no child job can hold an upgrade.
