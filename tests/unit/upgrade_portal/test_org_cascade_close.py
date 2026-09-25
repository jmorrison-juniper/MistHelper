"""Unit tests for the end of the multi-site phase watch.

Why:
    Issue #3244. The single-site driver takes the post-check capture before
    it writes the end of the run. The multi-site watch must take the
    post-check capture of each site before it writes the finished state or the
    stopped state. These tests drive the shipped close against the versioned
    test store and a stand-in taker. No test reads a cloud.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from src.upgrade_portal.upgrade.driver import PhaseOutcome
from src.upgrade_portal.upgrade.org_cascade.close import OrgCascadeClose
from src.upgrade_portal.upgrade.org_cascade.record import (
    FINISHED_NOTE,
    STOPPED_NOTE,
    WATCH_KEY,
    OrgPhaseEntries,
    OrgPhaseStore,
)
from src.upgrade_portal.upgrade.org_postcheck import FAILURE_REASON, STAGE_NOTE, OrgPostCheckRows
from tests.support.org_cascade import (
    OPERATION_ID,
    SITE_IDS,
    SITE_NAMES,
    OrgRecordBuilder,
    StandInPostCheckTaker,
    VersionedStore,
)
from tests.support.rehearsal import RehearsalClock, cascade_fleet

BRAVO = SITE_IDS[1]  # The second site of the plan.
NOW_TEXT = "2026-09-24T00:00:00+00:00"  # The fixed clock text of every write.
FAILED_TEXT = "The capture stopped. Read the portal log for the cause."  # The capture failure text.


def planned_record() -> dict[str, Any]:
    """Return one operation record with the site plan of two sites."""
    fleet = cascade_fleet(RehearsalClock().now())  # Each site holds one gateway, one switch, and one access point.
    return OrgRecordBuilder.with_site_plan(OrgRecordBuilder.build(fleet))  # The plan fields.


def close_of(record: dict[str, Any], taker: StandInPostCheckTaker | None) -> tuple[VersionedStore, OrgCascadeClose]:
    """Return the test store and the close that writes into it."""
    store = VersionedStore(record)  # The store holds the record.
    records = OrgPhaseStore(store, OPERATION_ID, lambda: NOW_TEXT)  # The bounded writer of the watch.
    return store, OrgCascadeClose(records, taker, OPERATION_ID)  # The caller ends the watch.


def watch(store: VersionedStore) -> dict[str, Any]:
    """Return the stored watch fields."""
    return dict((store.read_run(OPERATION_ID) or {})[WATCH_KEY])  # The caller receives the watch fields.


def row_states(store: VersionedStore) -> list[str]:
    """Return the state of each stored post-check row, in the plan order."""
    return [row["state"] for row in OrgPostCheckRows.of(store.read_run(OPERATION_ID) or {}).values()]  # The states.


def test_finish_takes_each_postcheck_before_the_finished_state() -> None:
    """FR-001 and FR-015. The watch stays active while the captures run, and it finishes after them."""
    taker = StandInPostCheckTaker()  # Every capture verifies.
    store, close = close_of(planned_record(), taker)  # The close writes into the test store.
    seen: list[tuple[str, str]] = []  # The watch state and note inside each capture.
    taker.on_take = lambda site: seen.append((watch(store)["state"], watch(store)["note"]))  # Read the watch.
    assert close.finish() == "finished"  # The watch must finish.
    assert seen == [("running", STAGE_NOTE)] * 2  # Both captures ran under the active watch.
    assert (watch(store)["state"], watch(store)["note"], watch(store)["reason"]) == (
        "finished",
        FINISHED_NOTE,
        None,
    )  # No failure, so the finished note stays.
    assert row_states(store) == ["verified", "verified"]  # Both rows verified before the final state.


def test_finish_names_a_failed_postcheck_as_the_reason() -> None:
    """FR-011. No phase failed, so the finished watch names the first failed capture."""
    taker = StandInPostCheckTaker(faults={BRAVO: FAILED_TEXT})  # Bravo answers a failure.
    store, close = close_of(planned_record(), taker)  # The close writes into the test store.
    close.finish()  # End the watch.
    expected = FAILURE_REASON.format(site=SITE_NAMES[BRAVO])  # The reason names Bravo.
    assert (watch(store)["note"], watch(store)["reason"]) == (expected, expected)  # The page shows the reason.


def test_finish_keeps_a_phase_failure_as_the_first_reason() -> None:
    """FR-011. A failed phase is the root cause, so it outranks a failed capture."""
    record = planned_record()  # The record of the current release.
    lost = PhaseOutcome("gateways", "failed", 1, 2, ("aa0000000002",))  # One gateway never returned.
    OrgPhaseEntries.put(record, entry=OrgPhaseEntries.from_outcome(lost, NOW_TEXT))  # The gateway phase failed.
    phase_reason = OrgPhaseEntries.first_failure(record)  # The reason that the walk names.
    gateway_failure = "The gateways phase failed."  # The first sentence of the single-site phase reason.
    taker = StandInPostCheckTaker(faults={BRAVO: FAILED_TEXT})  # Bravo answers a failure too.
    store, close = close_of(record, taker)  # The close writes into the test store.
    close.finish()  # End the watch.
    assert str(phase_reason)[: len(gateway_failure)] == gateway_failure  # The failed phase gives the reason.
    assert watch(store)["reason"] == phase_reason  # The phase reason wins.


def test_stop_takes_each_postcheck_and_puts_the_waiting_phase_back_to_pending() -> None:
    """FR-002. A stop takes the captures, and the page shows no wait that no thread performs."""
    record = planned_record()  # The record of the current release.
    OrgPhaseEntries.put(record, entry=OrgPhaseEntries.waiting("switches", 2))  # The switch gate waited.
    record["cancellation"] = {"requested": True, "results": []}  # The operator cancelled.
    taker = StandInPostCheckTaker()  # Every capture verifies.
    store, close = close_of(record, taker)  # The close writes into the test store.
    seen: list[str] = []  # The switch phase state inside each capture.
    taker.on_take = lambda site: seen.append(
        OrgPhaseEntries.entry(store.read_run(OPERATION_ID) or {}, "switches")["state"]
    )  # Read the phase.
    assert close.stop() == "stopped"  # The watch must stop.
    assert seen == ["pending", "pending"]  # No phase showed a wait during the captures.
    assert (watch(store)["state"], watch(store)["note"]) == ("stopped", STOPPED_NOTE)  # The page shows the stop.
    assert row_states(store) == ["verified", "verified"]  # Both captures ran.


@pytest.mark.parametrize(
    ("end", "state"),
    [(OrgCascadeClose.finish, "finished"), (OrgCascadeClose.stop, "stopped")],
    ids=["finish", "stop"],
)
def test_the_end_with_no_seam_writes_one_final_state(end: Callable[[OrgCascadeClose], str], state: str) -> None:
    """A walk with no capture seam keeps the one final write of issue #3245."""
    store, close = close_of(planned_record(), None)  # No seam.
    assert end(close) == state  # The watch must end.
    assert store.writes == 1  # One write, as before issue #3244.
    assert watch(store)["state"] == state  # The final state landed.
