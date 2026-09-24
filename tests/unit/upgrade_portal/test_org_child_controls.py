"""Unit tests for the retry, reconciliation, and schedule rules of a multi-site operation.

Why:
    Issue #3247. The single-site portal can retry the failed devices,
    reconcile an uncertain submission from the running versions, and move the
    start time before the upgrade begins. The multi-site portal could do none
    of the three. These tests prove the pure rules that the new controls use.
"""

from __future__ import annotations

from typing import Any

import pytest

from src.upgrade_portal.upgrade.org_child_controls import OrgControlsView, OrgScheduleView
from src.upgrade_portal.upgrade.org_reconcile import OrgReconcileCheck
from src.upgrade_portal.upgrade.org_retry import OrgRetryPlan, OrgRetrySelection

ORG_ID = "11111111-1111-1111-1111-111111111111"
SITE_ONE = "22222222-2222-2222-2222-222222222222"
SITE_TWO = "33333333-3333-3333-3333-333333333333"
OPERATION_ID = "org-run-unit-0001"
AP = "000000000001"
GATEWAY = "000000000002"
SWITCH = "000000000103"
AP_TARGET = "0.15.1"
JUNOS_TARGET = "23.4R1.9"
JUNOS_OLD = "23.4R1.8"


def target(mac: str, site_id: str, device_type: str, before: str, wanted: str) -> dict[str, str]:
    """Build one stored target record, in the shape that the aggregate service stores."""
    return {
        "mac": mac,
        "name": f"{device_type}-{mac[-3:]}",
        "device_type": device_type,
        "model": "AP45" if device_type == "ap" else "EX4400",
        "version_before": before,
        "version_target": wanted,
        "site_id": site_id,
    }


def child(child_id: str, status: str, targets: list[dict[str, str]], site_id: str | None) -> dict[str, Any]:
    """Build one aggregate child row with its stored targets."""
    return {
        "child_id": child_id,
        "device_family": targets[0]["device_type"] if targets else "ap",
        "site_id": site_id,
        "site_name": "One" if site_id == SITE_ONE else "Two",
        "status": status,
        "target_ids": [row["mac"] for row in targets],
        "targets": targets,
        "status_data": {},
        "error": None if status == "completed" else "The cloud refused the request.",
        "body": {"version": targets[0]["version_target"] if targets else ""},
    }


def record(children: list[dict[str, Any]], **extra: Any) -> dict[str, Any]:
    """Build one durable operation record with two sites."""
    base: dict[str, Any] = {
        "operation_id": OPERATION_ID,
        "run_id": OPERATION_ID,
        "org_id": ORG_ID,
        "site_ids": [SITE_ONE, SITE_TWO],
        "site_names": {SITE_ONE: "One", SITE_TWO: "Two"},
        "state": "failed",
        "children": children,
        "device_versions": {},
    }
    base.update(extra)
    return base


def settled_record() -> dict[str, Any]:
    """Build a settled operation with one match, one mismatch, and one refusal."""
    ap_child = child("child-ap", "completed", [target(AP, SITE_ONE, "ap", "0.14.29216", AP_TARGET)], None)
    gateway_child = child(
        "child-gateway", "completed", [target(GATEWAY, SITE_ONE, "gateway", JUNOS_OLD, JUNOS_TARGET)], SITE_ONE
    )
    switch_child = child(
        "child-switch", "rejected", [target(SWITCH, SITE_TWO, "switch", JUNOS_OLD, JUNOS_TARGET)], SITE_TWO
    )
    readings = {
        AP: {"version": AP_TARGET, "read_at": "t", "reads": 1},
        GATEWAY: {"version": JUNOS_OLD, "read_at": "t", "reads": 1},
    }
    plan_options = {
        "selected_types": ["ap", "switch", "gateway"],
        "version_ap": AP_TARGET,
        "version_switch": JUNOS_TARGET,
        "version_gateway": JUNOS_TARGET,
        "strategy": "big_bang",
        "reboot": True,
        "reboot_at": "2h",
        "start_time": 1790000000,
        "operation_id": "org-run-older",
        "target_count": 3,
    }
    return record([ap_child, gateway_child, switch_child], device_versions=readings, plan_options=plan_options)


def test_a_refused_device_and_a_mismatched_device_need_a_retry() -> None:
    """The retry holds a refused switch and a gateway that runs the old version, and never the matched AP."""
    plan = OrgRetrySelection.plan(settled_record())
    assert isinstance(plan, OrgRetryPlan)  # A retry device exists, so the selection returns a plan.
    assert sorted(device["mac"] for device in plan.devices) == [GATEWAY, SWITCH]
    assert plan.site_ids == (SITE_ONE, SITE_TWO)
    assert plan.operation_id == OPERATION_ID
    assert plan.org_id == ORG_ID


def test_a_matched_device_never_needs_a_retry_in_a_failed_child() -> None:
    """A device that runs the target version stays out of the retry, whatever the child state is."""
    matched = settled_record()
    matched["device_versions"][SWITCH] = {"version": JUNOS_TARGET, "read_at": "t", "reads": 1}
    matched["device_versions"][GATEWAY] = {"version": JUNOS_TARGET, "read_at": "t", "reads": 1}
    assert OrgRetrySelection.plan(matched) is None


@pytest.mark.parametrize("state", ["failed", "rejected", "not_submitted", "cancelled", "skipped"])
def test_each_retry_state_needs_a_retry(state: str) -> None:
    """A device in a retry state with no matching reading needs a retry."""
    row = {"state": state, "version_outcome": "version_pending"}
    assert OrgRetrySelection.needs_retry(row) is True


@pytest.mark.parametrize("state", ["completed", "upgraded", "pending", "submission_unknown"])
def test_a_quiet_state_with_no_mismatch_needs_no_retry(state: str) -> None:
    """A device outside the retry states needs a retry only after a version mismatch."""
    assert OrgRetrySelection.needs_retry({"state": state, "version_outcome": "version_pending"}) is False
    assert OrgRetrySelection.needs_retry({"state": state, "version_outcome": "version_mismatch"}) is True


def test_the_prefill_narrows_the_families_and_drops_the_old_start() -> None:
    """The retry form keeps the earlier choices, narrows the families, and drops the start and the identity."""
    plan = OrgRetrySelection.plan(settled_record())
    assert isinstance(plan, OrgRetryPlan)  # A retry device exists, so the selection returns a plan.
    assert plan.options["selected_types"] == ["switch", "gateway"]
    assert plan.options["version_switch"] == JUNOS_TARGET
    assert plan.options["strategy"] == "big_bang"
    assert plan.options["reboot_at"] == "2h"
    assert "start_time" not in plan.options
    assert "operation_id" not in plan.options
    assert "target_count" not in plan.options


def test_the_prefill_without_stored_options_uses_the_device_versions() -> None:
    """An operation from an earlier release names the families and the target versions only."""
    older = settled_record()
    del older["plan_options"]
    plan = OrgRetrySelection.plan(older)
    assert isinstance(plan, OrgRetryPlan)  # A retry device exists, so the selection returns a plan.
    assert plan.options == {
        "selected_types": ["switch", "gateway"],
        "version_switch": JUNOS_TARGET,
        "version_gateway": JUNOS_TARGET,
    }


def test_the_narrow_keeps_only_the_retry_devices() -> None:
    """The narrow keeps each retry device in any MAC spelling and keeps the other view fields."""
    plan = OrgRetrySelection.plan(settled_record())
    assert isinstance(plan, OrgRetryPlan)  # A retry device exists, so the selection returns a plan.
    view = {
        "targets": [
            {"mac": "00:00:00:00:00:01", "device_type": "ap"},
            {"mac": "00-00-00-00-00-02", "device_type": "gateway"},
            {"mac": "000000000099", "device_type": "switch"},
        ],
        "versions": {"ap": [AP_TARGET]},
    }
    narrowed = plan.narrow(view)
    assert [row["mac"] for row in narrowed["targets"]] == ["00-00-00-00-00-02"]
    assert narrowed["versions"] == {"ap": [AP_TARGET]}
    assert len(view["targets"]) == 3


def test_the_session_value_holds_the_reference_only() -> None:
    """The signed cookie holds the operation identity and the organization, and never a device list."""
    plan = OrgRetrySelection.plan(settled_record())
    assert isinstance(plan, OrgRetryPlan)  # A retry device exists, so the selection returns a plan.
    value = plan.to_session()
    assert value == {"operation_id": OPERATION_ID, "org_id": ORG_ID}
    assert OrgRetryPlan.session_reference(value, ORG_ID) == OPERATION_ID
    assert OrgRetryPlan.session_reference(value, "another-org") is None
    assert OrgRetryPlan.session_reference({"operation_id": 7, "org_id": ORG_ID}, ORG_ID) is None
    assert OrgRetryPlan.session_reference("damaged", ORG_ID) is None


def test_an_empty_plan_narrows_every_device_away() -> None:
    """A retry plan with no device fails closed, so the save plans no device."""
    empty = OrgRetryPlan.empty(OPERATION_ID, ORG_ID)
    assert empty.devices == ()
    assert empty.narrow({"targets": [{"mac": AP}]})["targets"] == []


def uncertain_record(before: str = JUNOS_OLD) -> dict[str, Any]:
    """Build an operation with two uncertain children and one completed child."""
    switch_child = child(
        "child-switch", "submission_unknown", [target(SWITCH, SITE_ONE, "switch", before, JUNOS_TARGET)], SITE_ONE
    )
    gateway_child = child(
        "child-gateway", "unknown", [target(GATEWAY, SITE_TWO, "gateway", JUNOS_OLD, JUNOS_TARGET)], SITE_TWO
    )
    ap_child = child("child-ap", "completed", [target(AP, SITE_ONE, "ap", "0.14.29216", AP_TARGET)], None)
    return record([switch_child, gateway_child, ap_child], state="attention_required")


def test_the_check_lists_only_the_uncertain_children() -> None:
    """The check reads the sites of the uncertain children only, in plan order."""
    check = OrgReconcileCheck(uncertain_record())
    assert [one.child_id for one in check.children()] == ["child-switch", "child-gateway"]
    assert check.site_ids() == [SITE_ONE, SITE_TWO]


def test_the_readings_hold_only_the_uncertain_devices() -> None:
    """A failed site gives no reading, an absent device reads empty, and other devices stay out."""
    check = OrgReconcileCheck(uncertain_record())
    answers = {SITE_ONE: {SWITCH: JUNOS_TARGET, AP: AP_TARGET, "000000000777": "x"}, SITE_TWO: None}
    assert check.readings(answers) == {SWITCH: JUNOS_TARGET}
    assert check.readings({SITE_ONE: {AP: AP_TARGET}}) == {SWITCH: ""}


def test_a_child_is_proven_when_every_device_runs_the_target() -> None:
    """Every device on the target version proves the child job complete."""
    verdicts = OrgReconcileCheck(uncertain_record()).verdicts({SWITCH: JUNOS_TARGET})
    switch_verdict = verdicts[0]
    assert switch_verdict["child_id"] == "child-switch"
    assert switch_verdict["proven"] is True
    assert (switch_verdict["matched"], switch_verdict["total"], switch_verdict["unread"]) == (1, 1, 0)
    assert "1 of 1" in switch_verdict["summary"]


def test_a_failed_site_read_keeps_the_child_uncertain() -> None:
    """A device with no reading proves nothing, so the child stays uncertain."""
    verdicts = OrgReconcileCheck(uncertain_record()).verdicts({SWITCH: JUNOS_TARGET})
    gateway_verdict = verdicts[1]
    assert gateway_verdict["child_id"] == "child-gateway"
    assert gateway_verdict["proven"] is False
    assert (gateway_verdict["matched"], gateway_verdict["total"], gateway_verdict["unread"]) == (0, 1, 1)
    assert "Mist dashboard" in gateway_verdict["summary"]


def test_a_forced_reinstall_is_never_proven() -> None:
    """A device that ran the target before the upgrade proves nothing about the child job."""
    verdicts = OrgReconcileCheck(uncertain_record(before=JUNOS_TARGET)).verdicts({SWITCH: JUNOS_TARGET})
    assert verdicts[0]["proven"] is False
    assert "before the upgrade" in verdicts[0]["summary"]


def test_a_child_with_no_device_is_never_proven() -> None:
    """An uncertain child that names no device can never read as complete."""
    empty = record([child("child-empty", "submission_unknown", [], SITE_ONE)], state="attention_required")
    verdicts = OrgReconcileCheck(empty).verdicts({})
    assert verdicts[0]["proven"] is False
    assert verdicts[0]["total"] == 0


def test_a_planned_operation_accepts_a_reschedule() -> None:
    """A plan that no request submitted shows the start and accepts a new start time."""
    planned = record(
        [child("child-switch", "planned", [target(SWITCH, SITE_ONE, "switch", JUNOS_OLD, JUNOS_TARGET)], SITE_ONE)]
    )
    planned["state"] = "planned"
    view = OrgScheduleView.build(planned, "2026-09-24T10:00")
    assert view == {
        "available": True,
        "operation_id": OPERATION_ID,
        "start_value": "2026-09-24T10:00",
        "start_text": "The upgrade starts at 2026-09-24 10:00 UTC.",
    }
    assert OrgScheduleView.build(planned, "")["start_text"] == "The upgrade starts at once after you confirm."


def test_a_claimed_or_submitted_operation_refuses_a_reschedule() -> None:
    """A claim, a submitted child, or an absent record removes the reschedule form."""
    planned = record(
        [child("child-switch", "planned", [target(SWITCH, SITE_ONE, "switch", JUNOS_OLD, JUNOS_TARGET)], SITE_ONE)]
    )
    planned["state"] = "planned"
    claimed = {**planned, "submission_claim_id": "claim"}
    submitted = {**planned, "children": [{**planned["children"][0], "status": "accepted"}]}
    assert OrgScheduleView.build(claimed, "")["available"] is False
    assert OrgScheduleView.build(submitted, "")["available"] is False
    assert OrgScheduleView.build(None, "")["available"] is False


def test_the_controls_name_the_retry_devices_and_the_uncertain_children() -> None:
    """The controls list each retry device and each uncertain child with its typed word."""
    settled = settled_record()
    retry = OrgRetrySelection.plan(settled)
    controls = OrgControlsView.build(uncertain_record(), retry)
    assert controls["retry"]["available"] is True
    assert controls["retry"]["count"] == 2
    assert {device["mac"] for device in controls["retry"]["devices"]} == {GATEWAY, SWITCH}
    assert set(controls["retry"]["devices"][0]) == {"name", "mac", "site_name", "device_type", "state"}
    assert controls["reconcile"]["available"] is True
    assert controls["reconcile"]["word"] == f"RECONCILE {OPERATION_ID}"
    assert [one["child_id"] for one in controls["reconcile"]["children"]] == ["child-switch", "child-gateway"]


def test_the_controls_show_the_last_reconciliation_evidence() -> None:
    """A child that the portal checked before shows the stored summary of that check."""
    checked = uncertain_record()
    checked["children"][0]["reconciliation"] = {"summary": "0 of 1 devices run the target version."}
    controls = OrgControlsView.build(checked, None)
    assert controls["reconcile"]["children"][0]["evidence"] == "0 of 1 devices run the target version."
    assert controls["reconcile"]["children"][1]["evidence"] == ""
    assert controls["retry"] == {"available": False, "count": 0, "devices": []}


def test_the_signature_follows_the_controls_only() -> None:
    """The same controls give the same signature, and a new control gives a new signature."""
    first = OrgControlsView.build(uncertain_record(), None)["signature"]
    again = OrgControlsView.build(uncertain_record(), None)["signature"]
    retry = OrgRetrySelection.plan(settled_record())
    changed = OrgControlsView.build(uncertain_record(), retry)["signature"]
    quiet = OrgControlsView.build(record([]), None)["signature"]
    assert first == again
    assert changed != first
    assert quiet not in (first, changed)
