"""Unit tests for the reschedule and the reconciliation of one multi-site operation.

Why:
    Issue #3247. The single-site portal can move the start time of a planned
    upgrade and can reconcile an uncertain submission from the running
    versions. These tests prove the two service writes that give the
    multi-site portal the same controls. No test makes a cloud call.
"""

from __future__ import annotations

from copy import deepcopy
from threading import Lock
from typing import Any

import pytest

from src.firmware.aggregate_upgrade_service import (
    AggregateBuildInput,
    AggregateUpgradeService,
    ReconcileEvidence,
    RescheduleRequest,
)
from src.firmware.upgrade_service import DeviceTarget, UpgradeOptions

ORG_ID = "11111111-1111-1111-1111-111111111111"
SITE_ONE = "22222222-2222-2222-2222-222222222222"
SITE_TWO = "33333333-3333-3333-3333-333333333333"
AP_MAC = "001122334455"
SWITCH_MAC = "001122334466"
GATEWAY_MAC = "001122334477"
SSR_MAC = "001122334488"
FIRST_START = 1790000000
FIRST_REBOOT = 1790003600
NEW_START = 1790086400
NEW_REBOOT = 1790090000
ACTOR = "actor-digest"


class CasStore:
    """Keep one aggregate record behind a thread-safe compare-and-set."""

    def __init__(self, record: dict[str, Any]) -> None:
        """Store one detached initial record."""
        self.record = deepcopy(record)  # Keep caller edits outside the durable value.
        self.guard = Lock()  # Serialize each read and compare-and-set action.
        self.writes = 0  # Count each accepted replacement.

    def read_run(self, run_id: str) -> dict[str, Any] | None:
        """Return one detached record."""
        with self.guard:  # Keep the read consistent with the replacements.
            return deepcopy(self.record) if self.record.get("run_id") == run_id else None  # Match the key.

    def compare_and_set_run(self, run_id: str, expected_version: int, replacement: dict[str, Any]) -> bool:
        """Replace the record only when its version matches."""
        with self.guard:  # Keep the comparison and the replacement atomic.
            if self.record.get("run_id") != run_id or self.record.get("record_version") != expected_version:
                return False  # Reject a stale caller.
            self.record = deepcopy(replacement)  # Store the detached replacement.
            self.writes += 1  # Count the accepted write.
            return True  # Report the successful change.


def target(mac: str, device_type: str, model: str, site_id: str, version: str) -> DeviceTarget:
    """Build one selected target."""
    return DeviceTarget(mac, device_type, device_type, model, "old", version, site_id)  # Keep the rows short.


def build_record(options: UpgradeOptions) -> dict[str, Any]:
    """Build an AP, switch, Junos gateway, and SSR operation with the given options."""
    service = AggregateUpgradeService()  # The build makes no cloud call.
    sites = ({"site_id": SITE_ONE, "name": "One"}, {"site_id": SITE_TWO, "name": "Two"})
    targets = (
        target(AP_MAC, "ap", "AP45", SITE_ONE, "0.15.1"),
        target(SWITCH_MAC, "switch", "EX4400", SITE_ONE, "23.4R1.9"),
        target(GATEWAY_MAC, "gateway", "SRX345", SITE_TWO, "23.4R1.9"),
        target(SSR_MAC, "gateway", "SSR120", SITE_TWO, "6.3.0"),
    )
    record = service.build(AggregateBuildInput("owner", ORG_ID, sites, targets, options, "nonce"))
    record["plan_options"] = {"start_time": options.start_time, "reboot_at": "1h", "strategy": "big_bang"}
    return record


def scheduled_record() -> dict[str, Any]:
    """Build a planned operation with a start time and a reboot moment."""
    return build_record(UpgradeOptions(start_time=FIRST_START, reboot=True, reboot_at=FIRST_REBOOT))


def child_of(record: dict[str, Any], mac: str) -> dict[str, Any]:
    """Return the child that holds one device."""
    return next(child for child in record["children"] if mac in child["target_ids"])


def test_the_reschedule_moves_the_start_and_the_reboot_of_every_child() -> None:
    """Every child body and the stored options carry the new moments after one write."""
    record = scheduled_record()
    store = CasStore(record)
    AggregateUpgradeService().reschedule(record, store, RescheduleRequest(NEW_START, NEW_REBOOT, ACTOR))
    stored = store.record
    assert store.writes == 1
    assert {child["body"]["start_time"] for child in stored["children"]} == {NEW_START}
    for mac in (SWITCH_MAC, GATEWAY_MAC, SSR_MAC):
        assert child_of(stored, mac)["body"]["reboot_at"] == NEW_REBOOT
        assert child_of(stored, mac)["reboot_at"] == NEW_REBOOT
    assert "reboot_at" not in child_of(stored, AP_MAC)["body"]
    assert stored["plan_options"]["start_time"] == NEW_START
    assert stored["plan_options"]["reboot_at"] == "1h"
    assert stored["rescheduled_by"] == ACTOR
    assert stored["rescheduled_at"]
    assert stored["state"] == "planned"
    assert record == stored


def test_a_reschedule_to_now_removes_every_start() -> None:
    """An empty start removes the field, so the cloud starts the upgrade at once."""
    record = build_record(UpgradeOptions(start_time=FIRST_START, reboot=True))
    store = CasStore(record)
    AggregateUpgradeService().reschedule(record, store, RescheduleRequest(None, None, ACTOR))
    assert all("start_time" not in child["body"] for child in store.record["children"])
    assert "start_time" not in store.record["plan_options"]


def test_the_reschedule_refuses_a_reboot_moment_it_cannot_move() -> None:
    """A stored reboot moment with no new moment stops the write, so no child keeps a stale reboot."""
    record = scheduled_record()
    store = CasStore(record)
    with pytest.raises(ValueError, match="reboot"):
        AggregateUpgradeService().reschedule(record, store, RescheduleRequest(NEW_START, None, ACTOR))
    assert store.writes == 0
    assert child_of(store.record, SWITCH_MAC)["body"]["start_time"] == FIRST_START


def test_the_reschedule_keeps_the_disabled_router_reboot() -> None:
    """The value -1 holds the router reboot back, so the reschedule never moves it."""
    record = build_record(UpgradeOptions(start_time=FIRST_START, reboot=False))
    store = CasStore(record)
    AggregateUpgradeService().reschedule(record, store, RescheduleRequest(NEW_START, None, ACTOR))
    assert child_of(store.record, SSR_MAC)["body"]["reboot_at"] == -1
    assert "reboot_at" not in child_of(store.record, SSR_MAC)
    assert child_of(store.record, SWITCH_MAC)["body"]["start_time"] == NEW_START


@pytest.mark.parametrize("change", ["state", "claim", "child"])
def test_the_reschedule_refuses_an_operation_that_left_the_plan(change: str) -> None:
    """A submitted, claimed, or started operation keeps its schedule."""
    record = scheduled_record()
    if change == "state":
        record["state"] = "running"
    elif change == "claim":
        record["submission_claim_id"] = "claim"
    else:
        record["children"][0]["status"] = "accepted"
    store = CasStore(record)
    with pytest.raises(ValueError):
        AggregateUpgradeService().reschedule(record, store, RescheduleRequest(NEW_START, NEW_REBOOT, ACTOR))
    assert store.writes == 0


def uncertain_record() -> dict[str, Any]:
    """Build an operation with two uncertain children and two completed children."""
    record = scheduled_record()
    for child in record["children"]:
        child["status"] = "completed"
    child_of(record, SWITCH_MAC).update(status="submission_unknown", error="The outcome is unknown.")
    child_of(record, GATEWAY_MAC).update(status="unknown", error="The status read failed.")
    record["state"] = "attention_required"
    return record


def verdict(child: dict[str, Any], proven: bool) -> dict[str, Any]:
    """Build one verdict of the portal check."""
    matched = 1 if proven else 0  # One device in each test child.
    return {
        "child_id": child["child_id"],
        "proven": proven,
        "matched": matched,
        "total": 1,
        "unread": 0,
        "summary": f"{matched} of 1 devices run the target version.",
    }


def test_a_proven_child_reads_completed_with_its_evidence() -> None:
    """A proven child moves to completed, and a child that is not proven keeps its state."""
    record = uncertain_record()
    switch = child_of(record, SWITCH_MAC)
    gateway = child_of(record, GATEWAY_MAC)
    store = CasStore(record)
    evidence = ReconcileEvidence((verdict(switch, True), verdict(gateway, False)), {SWITCH_MAC: "23.4R1.9"}, ACTOR)
    AggregateUpgradeService().reconcile(record, store, evidence)
    stored_switch = child_of(store.record, SWITCH_MAC)
    stored_gateway = child_of(store.record, GATEWAY_MAC)
    assert (stored_switch["status"], stored_switch["error"]) == ("completed", None)
    assert stored_switch["reconciliation"]["prior_status"] == "submission_unknown"
    assert stored_switch["reconciliation"]["prior_error"] == "The outcome is unknown."
    assert stored_switch["reconciliation"]["checked_by"] == ACTOR
    assert stored_switch["reconciliation"]["checked_at"]
    assert stored_gateway["status"] == "unknown"
    assert stored_gateway["reconciliation"]["summary"] == "0 of 1 devices run the target version."
    assert store.record["device_versions"][SWITCH_MAC]["version"] == "23.4R1.9"
    assert store.record["state"] == "attention_required"
    assert store.writes == 1


def test_two_proven_children_complete_the_operation() -> None:
    """The aggregate state follows the children after the last uncertain child is proven."""
    record = uncertain_record()
    verdicts = (verdict(child_of(record, SWITCH_MAC), True), verdict(child_of(record, GATEWAY_MAC), True))
    store = CasStore(record)
    AggregateUpgradeService().reconcile(record, store, ReconcileEvidence(verdicts, {}, ACTOR))
    assert store.record["state"] == "completed"


def test_the_reconcile_skips_a_child_that_left_the_uncertain_state() -> None:
    """A child that a poll settled during the check keeps the result of that poll."""
    record = uncertain_record()
    switch = child_of(record, SWITCH_MAC)
    store = CasStore(record)
    child_of(store.record, SWITCH_MAC)["status"] = "failed"
    evidence = ReconcileEvidence((verdict(switch, True), {"child_id": "child-absent", "proven": True}), {}, ACTOR)
    AggregateUpgradeService().reconcile(record, store, evidence)
    stored_switch = child_of(store.record, SWITCH_MAC)
    assert stored_switch["status"] == "failed"
    assert "reconciliation" not in stored_switch


def test_the_reconcile_refuses_a_live_submission() -> None:
    """A live submission claim can still write, so the portal refuses to decide the outcome."""
    record = uncertain_record()
    record["submission_claim_id"] = "claim"
    store = CasStore(record)
    evidence = ReconcileEvidence((verdict(child_of(record, SWITCH_MAC), True),), {}, ACTOR)
    with pytest.raises(ValueError):
        AggregateUpgradeService().reconcile(record, store, evidence)
    assert store.writes == 0
