"""Unit tests for the page view of the multi-site phase watch.

Why:
    Issue #3245. The multi-site page and the status poll read the same phase
    fields. These tests prove the watch line, the poll flag, and the empty
    view of a record from an earlier release.
"""

from __future__ import annotations

from typing import Any

import pytest

from src.upgrade_portal.upgrade.org_cascade.record import (
    NO_CHILD_NOTE,
    NOT_STARTED_NOTE,
    WATCH_KEY,
    OrgPhaseEntries,
    OrgPhaseWatch,
    WatchState,
)
from src.upgrade_portal.upgrade.org_cascade.view import OrgPhaseView
from tests.support.org_cascade import AP_CHILD_KEY, OrgRecordBuilder
from tests.support.rehearsal import cascade_fleet

FLEET = cascade_fleet(1.0)  # Two gateways, two switches, and two access points.


def prepared(state: str = "running", watch_state: str | None = None, refuse_all: bool = False) -> dict[str, Any]:
    """Return one prepared record with the given operation state and watch state."""
    refused = (
        dict.fromkeys([*FLEET.macs(), AP_CHILD_KEY], "rejected") if refuse_all else {}
    )  # The flag controls refusals.
    record = OrgRecordBuilder.build(FLEET, statuses=refused)  # The record after the anchor read.
    record["state"] = state  # The state of the operation.
    if watch_state is not None:  # The walk wrote a later state.
        OrgPhaseWatch.set_state(
            record, WatchState(watch_state), f"Note of {watch_state}.", None
        )  # The watch stores the state.
    return record  # The helper returns the prepared record.


def test_a_record_of_an_earlier_release_shows_no_phase_card() -> None:
    """FR-013. A record with no watch fields gives an empty phase list and no poll."""
    assert OrgPhaseView.build({"operation_id": "op-1", "state": "running"}) == {  # An old record shows no card.
        "phases": [],
        "phase_watch": None,
        "phase_active": False,
    }


def test_the_view_holds_the_four_entries_in_the_single_site_shape() -> None:
    """FR-003. The page reads the same entry fields as the single-site page."""
    record = prepared()  # The record starts with the phase fields.
    OrgPhaseEntries.put(record, OrgPhaseEntries.waiting("switches", 3))  # The switch phase waits.
    view = OrgPhaseView.build(record)  # The view reads the record for the page.
    assert [row["name"] for row in view["phases"]] == [
        "gateways",
        "switches",
        "aps",
        "clients",
    ]  # The order matches the page.
    assert view["phases"][1] == OrgPhaseEntries.waiting("switches", 3)  # The phase entry keeps its shape.


@pytest.mark.parametrize(
    ("state", "watch_state", "label", "active"),
    [
        pytest.param("submission_claimed", None, "Not started", True, id="submission-open"),
        pytest.param("running", None, "Not started", True, id="next-poll-starts"),
        pytest.param("running", "waiting_for_start", "Scheduled", True, id="scheduled"),
        pytest.param("running", "running", "Active", True, id="running"),
        pytest.param("running", "finished", "Finished", False, id="finished"),
        pytest.param("cancelled", "stopped", "Stopped", False, id="stopped"),
        pytest.param("running", "failed", "Failed", False, id="failed"),
    ],
)
def test_the_watch_line_and_the_poll_flag_follow_the_watch_state(
    state: str, watch_state: str | None, label: str, active: bool
) -> None:
    """FR-017. The page keeps the poll alive while the counts can still change."""
    view = OrgPhaseView.build(prepared(state, watch_state))  # The view reads the tested watch state.
    assert view["phase_watch"]["label"] == label  # The label matches the watch state.
    assert view["phase_active"] is active  # The poll flag matches the watch state.


def test_a_submission_with_no_accepted_child_job_explains_the_empty_watch() -> None:
    """FR-005. No watch can start, so the page names the cause and stops the poll."""
    view = OrgPhaseView.build(prepared(state="attention_required", refuse_all=True))  # Every child job fails.
    assert view["phase_watch"]["state"] == "not_started"  # No child job can start the watch.
    assert view["phase_watch"]["note"] == NO_CHILD_NOTE  # The note explains the empty watch.
    assert view["phase_active"] is False  # No poll runs without an accepted child job.


def test_an_open_submission_keeps_the_note_of_the_first_state() -> None:
    """The exclusion count is not final until the submission ends."""
    view = OrgPhaseView.build(prepared(state="submission_claimed", refuse_all=True))  # The submission remains open.
    assert view["phase_watch"]["note"] == NOT_STARTED_NOTE  # The first note stays while counts can change.
    assert view["phase_active"] is True  # The poll remains active during submission.


def test_the_watch_line_carries_the_first_failure_and_the_anchor_gap_note() -> None:
    """FR-002 and FR-007. The page shows the root cause and the gap of the anchor read."""
    record = prepared()  # The record starts with a running watch.
    record[WATCH_KEY]["anchor_note"] = "Gap."  # The anchor gap becomes visible.
    OrgPhaseWatch.set_state(  # The watch stores the first failure.
        record, WatchState.FINISHED, "The switches phase failed. Cause.", "The switches phase failed. Cause."
    )
    watch = OrgPhaseView.build(record)["phase_watch"]  # The page receives the watch line.
    assert watch == {  # The watch line carries the failure data.
        "state": "finished",
        "label": "Finished",
        "note": "The switches phase failed. Cause.",
        "reason": "The switches phase failed. Cause.",
        "anchor_note": "Gap.",
    }
