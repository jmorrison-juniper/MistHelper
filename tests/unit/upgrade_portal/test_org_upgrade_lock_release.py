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
    children = [{"child_id": f"child-{index}", "status": value} for index, value in enumerate(states)]  # One row each.
    return {"state": state, "children": children, "cancellation": {"requested": cancelled, "results": []}}


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
    record["children"][3]["raw_status"] = 400  # A known refusal is final only with explicit evidence.
    record["children"][3]["response_data_valid"] = True
    assert org_upgrade._operation_is_settled(record) is True  # No firmware write can follow.


@pytest.mark.parametrize(
    "raw_status",
    [
        pytest.param(None, id="missing-status"),  # Old records may not retain refusal evidence.
        pytest.param(400, id="legacy-refusal-without-body-proof"),
        pytest.param(405, id="undocumented-method-status"),  # This status is absent from the upgrade OpenAPI.
        pytest.param(408, id="request-timeout"),  # A timeout does not prove refusal.
        pytest.param(429, id="rate-limit"),  # A rate limit does not prove refusal.
        pytest.param(409, id="undocumented-conflict-status"),  # This status is absent from the upgrade OpenAPI.
        pytest.param(499, id="unlisted-client-status"),  # An unlisted status stays uncertain.
        pytest.param(503, id="server-error"),  # A server error does not prove refusal.
    ],
)
def test_a_rejected_child_without_refusal_evidence_keeps_the_sites(  # Retain locks without proof.
    raw_status: object,
) -> None:
    """A rejected word alone does not prove that the cloud created no job."""
    record = operation("rejected", state="failed")  # The aggregate state cannot override child evidence.
    if raw_status is not None:  # Keep a missing status distinct from a stored status.
        record["children"][0]["raw_status"] = raw_status  # Store the tested response evidence.
    assert org_upgrade._operation_is_settled(record) is False  # The site locks stay held.


@pytest.mark.parametrize("raw_status", [400, 405, 408, 409, 429, 499, 503])
def test_release_does_not_call_the_lock_boundary_for_uncertain_refusal(  # Guard the physical lock boundary.
    raw_status: int,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An uncertain rejected child does not reach the physical lock release."""
    record = operation("rejected", state="failed")  # Model a legacy child with an ambiguous result.
    record["children"][0]["raw_status"] = raw_status  # Keep the exact response code.
    record["org_id"] = "org-one"  # Supply the lock key context.
    record["site_locks"] = {"site-one": {"token": "lock-token"}}  # Model the stored site lock.
    released: list[tuple[str, str, object]] = []  # Record any physical release request.

    def record_release(org_id: str, site_id: str, value: object) -> None:  # Capture one release request.
        """Record one call to the physical lock boundary."""
        released.append((org_id, site_id, value))  # Keep the exact release arguments.

    monkeypatch.setattr(org_upgrade, "_release_one_lock", record_release)  # Replace only the physical boundary.
    org_upgrade.release_operation_locks(record)  # Apply the production release decision.
    assert released == []  # No site lock release can follow uncertain evidence.
    assert record["site_locks"]  # Keep the operation's durable lock map intact.


@pytest.mark.parametrize(
    "evidence",
    [
        pytest.param({"upgrade_id": "job-one"}, id="retained-upgrade-identity"),
        pytest.param({"status_data": {"targets": {"upgraded": ["device-one"]}}}, id="accepted-target"),
        pytest.param({"status_data": {"id": "job-one"}}, id="identity-in-response-data"),
    ],
)
def test_a_documented_refusal_with_conflicting_legacy_evidence_keeps_the_sites(
    evidence: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A legacy rejected record cannot settle when it retains evidence of a cloud job."""
    record = operation("rejected", state="failed")  # Model a previously misclassified refusal.
    record["children"][0].update(
        {"raw_status": 400, "response_data_valid": True, **evidence}
    )  # Retained body proof cannot override a conflicting job identity.
    record["org_id"] = "org-one"  # Supply the lock key context.
    record["site_locks"] = {"site-one": {"token": "lock-token"}}  # Model the stored site lock.
    released: list[tuple[str, str, object]] = []  # Record any physical release request.

    def record_release(org_id: str, site_id: str, value: object) -> None:  # Capture one release request.
        """Record one call to the physical lock boundary."""
        released.append((org_id, site_id, value))  # Keep the exact release arguments.

    monkeypatch.setattr(org_upgrade, "_release_one_lock", record_release)  # Replace only the physical boundary.
    org_upgrade.release_operation_locks(record)  # Apply the production release decision.
    assert released == []  # No site lock release can follow conflicting evidence.
    assert record["site_locks"]  # Keep the operation's durable lock map intact.


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
    record["children"][0]["raw_status"] = 400  # The refusal carries evidence that no job exists.
    record["children"][0]["response_data_valid"] = True
    record["phase_watch"] = {"state": "not_started"}  # The prepared watch has no accepted target.
    assert org_upgrade._operation_is_settled(record) is True  # No phase or post-check stage can run.


@pytest.mark.parametrize(("state", "settled"), [("completed", True), ("failed", True), ("attention_required", False)])
def test_a_record_without_children_keeps_the_conservative_state_rule(state: str, settled: bool) -> None:
    """A damaged record with no child releases the sites only for a final aggregate state."""
    record = {"state": state, "children": []}  # No child row survived.
    assert org_upgrade._operation_is_settled(record) is settled  # attention_required never releases the sites.
