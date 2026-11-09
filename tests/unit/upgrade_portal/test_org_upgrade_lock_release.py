"""Unit tests of the site lock release rule of a multi-site operation (issue #3220)."""

from __future__ import annotations

from typing import Any

import pytest

from src.interfaces.portals.upgrade_portal.app.routes import org_upgrade


def operation(*states: str, state: str = "running", cancelled: bool = False) -> dict[str, Any]:
    """Build one aggregate operation with one child for each state.

    Args:
        *states: The status of each child.
        state: The aggregate state.
        cancelled: True when the operator requested a cancel.

    Returns:
        The operation record.
    """
    children = [  # One row for each child state.
        {
            "child_id": f"child-{index}",  # Keep each test child distinct.
            "status": value,  # Preserve the requested child state.
            "raw_status": 400 if value == "rejected" else 0,  # Keep legacy refusals distinct from unknown results.
        }
        for index, value in enumerate(states)
    ]
    return {  # Keep the operation shape used by the lock and retry checks.
        "state": state,
        "children": children,
        "cancellation": {"requested": cancelled, "results": []},
    }


@pytest.mark.parametrize("child_state", ["running", "accepted", "partial", "read_unknown", "submission_unknown"])
def test_a_child_that_can_still_write_keeps_the_sites(child_state: str) -> None:
    """A running or uncertain child keeps every site lock, even when the aggregate reads attention_required."""
    record = operation("completed", child_state, state="attention_required")  # One child is not past the write.
    assert org_upgrade._operation_is_settled(record) is False  # The sites stay held.


def test_a_cancel_request_alone_keeps_the_sites() -> None:
    """A cancel does not stop a device that already writes firmware."""
    record = operation("running", "running", cancelled=True)  # The cloud still runs both children.
    assert org_upgrade._operation_is_settled(record) is False  # The sites stay held until the children end.


def test_every_final_child_releases_the_sites() -> None:
    """Each known final child state lets the portal release the sites."""
    record = operation("completed", "failed", "cancelled", "rejected", "not_submitted", state="failed")  # All final.
    assert org_upgrade._operation_is_settled(record) is True  # No firmware write can follow.


def test_a_running_phase_watch_keeps_the_sites_after_every_child_settles() -> None:
    """Issue #3333: the phase watch and its post-check stage keep every selected site lock."""
    record = operation("completed", state="completed")  # The child firmware write reached a final state.
    record["phase_watch"] = {"state": "running"}  # The watch can still read the site for a post-check capture.
    assert org_upgrade._operation_is_settled(record) is False  # The release waits for the post-check stage.


def test_a_finished_phase_watch_releases_the_sites() -> None:
    """Issue #3333: the operation releases each site after the post-check stage ends."""
    record = operation("completed", state="completed")  # The child firmware write reached a final state.
    record["phase_watch"] = {"state": "finished"}  # The phase watch and the post-check stage ended.
    assert org_upgrade._operation_is_settled(record) is True  # No operation step needs the site now.


def test_a_plan_with_no_accepted_child_needs_no_phase_watch_release_gate() -> None:
    """Issue #3333: a refused plan releases its locks because no watch thread can start."""
    record = operation("rejected", "not_submitted", state="failed")  # The cloud accepted no child job.
    record["phase_watch"] = {"state": "not_started"}  # The prepared watch has no accepted target.
    assert org_upgrade._operation_is_settled(record) is True  # No phase or post-check stage can run.


@pytest.mark.parametrize(
    "raw_status",
    [
        pytest.param(503, id="server-error"),
        pytest.param(200, id="damaged-success"),
        pytest.param(0, id="missing-status"),
        pytest.param(None, id="invalid-status"),
    ],
)
@pytest.mark.parametrize(
    "phase_watch",
    [pytest.param(None, id="no-watch"), pytest.param({"state": "not_started"}, id="mapping-watch")],
)
def test_legacy_ambiguous_rejection_keeps_lock_and_blocks_retry(
    monkeypatch: pytest.MonkeyPatch, raw_status: object, phase_watch: dict[str, str] | None
) -> None:
    """Keep old rejected records with no refusal proof away from release and retry."""
    record = operation("rejected", state="failed")  # Model a legacy child that used the broad rejected state.
    child = record["children"][0]  # Select the only child submission.
    child["raw_status"] = raw_status  # Replace the known-refusal status with uncertain evidence.
    record["site_locks"] = {"site-one": {"lock_id": "test-lock"}}  # Model one held site lock.
    if phase_watch is not None:  # Exercise both records with and without a watch map.
        record["phase_watch"] = phase_watch  # Preserve a mapping-shaped watch value.
    callbacks: list[str] = []  # Record physical release and persistence requests.
    monkeypatch.setattr(org_upgrade, "_release_one_lock", lambda *arguments: callbacks.append("release"))
    monkeypatch.setattr(org_upgrade, "_cas_operation", lambda *arguments: callbacks.append("persist"))
    org_upgrade.release_operation_locks(record)  # Run the real release gate with safe callbacks.
    assert org_upgrade._operation_is_settled(record) is False  # The ambiguous child keeps the operation open.
    assert org_upgrade.retry_plan_of(record) is None  # The same certainty rule blocks a retry.
    assert callbacks == []  # No physical release or lock-map persistence occurred.
    assert record["site_locks"]  # Keep the original site-lock record intact.


def test_a_cloud_reported_rejection_keeps_its_existing_final_rule() -> None:
    """A known cloud child state remains final after a successful status read."""
    record = operation("rejected", state="failed")  # Build a child that has already settled.
    child = record["children"][0]  # Select the cloud child state.
    child["raw_status"] = 200  # The status read itself succeeded.
    child["upgrade_id"] = "cloud-job"  # The response names the known cloud job.
    child["cloud_status"] = "rejected"  # The cloud reported the final child state.
    assert org_upgrade._operation_is_settled(record) is True  # Preserve the existing release behavior.


@pytest.mark.parametrize(("state", "settled"), [("completed", True), ("failed", True), ("attention_required", False)])
def test_a_record_without_children_keeps_the_conservative_state_rule(state: str, settled: bool) -> None:
    """A damaged record with no child releases the sites only for a final aggregate state."""
    record = {"state": state, "children": []}  # No child row survived.
    assert org_upgrade._operation_is_settled(record) is settled  # attention_required never releases the sites.
