"""Unit tests for the cancel of a multi-site operation with a child job that already ended.

Why:
    Issue #3367. A cancel of a running operation sent a cancel request to each
    child job with an upgrade identifier. A child job that already ended also
    got a request, and the cancel sort then listed each upgraded access point
    as a cancelled device. The single-site stop refuses a final run with no
    cloud request. These tests prove that the service sends no request to an
    ended child job, and that a running sibling still gets its request.
"""

from __future__ import annotations

from copy import deepcopy
from types import SimpleNamespace
from typing import Any

import pytest

from src.firmware.aggregate_upgrade_service import (
    ENDED_CHILD_STATUS,
    ENDED_CHILD_TEXT,
    FINAL_CHILD_STATES,
    AggregateBuildInput,
    AggregateUpgradeService,
)
from src.firmware.org_upgrade_service import OrgUpgradeResult
from src.firmware.upgrade_service import CancelOutcome, DeviceTarget, UpgradeOptions

ORG_ID = "44444444-4444-4444-4444-444444444444"  # The organization of the operation.
SITE_ID = "55555555-5555-5555-5555-555555555555"  # The one site of the operation.
AP_MAC = "001122334455"  # The access point of the organization child job.
SWITCH_MAC = "001122334466"  # The switch of the site child job.
WRITE_SESSION = SimpleNamespace(_MAX_429_RETRIES=0, _session=SimpleNamespace(adapters={}))  # A no-retry session.
EMPTY_LISTS = {"cancelled": [], "already_writing": [], "no_cancel_available": []}  # No device of an ended job.


class CasStore:
    """Keep one record behind a compare-and-set."""

    def __init__(self, record: dict[str, Any]) -> None:
        """Store one detached record."""
        self.record = deepcopy(record)  # The durable value.

    def read_run(self, run_id: str) -> dict[str, Any] | None:
        """Return one detached record, or None for another key."""
        return deepcopy(self.record) if self.record.get("run_id") == run_id else None  # Match the key.

    def compare_and_set_run(self, run_id: str, expected_version: int, replacement: dict[str, Any]) -> bool:
        """Replace the record only when its version matches."""
        if self.record.get("run_id") != run_id or self.record.get("record_version") != expected_version:
            return False  # A stale caller changes nothing.
        self.record = deepcopy(replacement)  # Store the detached replacement.
        return True  # Report the accepted change.


class CloudEdge:
    """Record each cancel call of the organization edge and of the site edge."""

    ACCEPTED_STATUS = (200, 202)  # Match the production service contract.
    GatewayFamily = SimpleNamespace(SSR="ssr", JUNOS="junos")  # Supply the family values that the reader uses.

    def __init__(self) -> None:
        """Start with no call."""
        self.cancels: list[str] = []  # Each entry names the job of one cancel call.

    def cancel(self, session: Any, org_id: str, upgrade_id: str) -> OrgUpgradeResult:
        """Accept one organization cancel."""
        del session  # The stand-in opens no socket.
        self.cancels.append(upgrade_id)  # A test counts the cancel calls.
        return OrgUpgradeResult(org_id, upgrade_id, 200, {}, None)  # The contract permits an empty body.

    def cancel_upgrade(self, session: Any, plan: Any, upgrade_id: str, status: Any) -> CancelOutcome:
        """Stop each device of one site child job."""
        del session, status  # The fixed answer needs the plan targets only.
        self.cancels.append(upgrade_id)  # A test counts the cancel calls.
        return CancelOutcome(tuple(device.mac for device in plan.targets), (), (), "The cloud stopped the job.")


def running_operation(service: AggregateUpgradeService, states: dict[str, str]) -> dict[str, Any]:
    """Build one running operation whose two child jobs reached the cloud.

    Args:
        service: The production service with the cloud stand-in.
        states: The stored state of the child job of each family, "ap" and "switch".

    Returns:
        The record, as the store holds it after the last status read.
    """
    sites = ({"site_id": SITE_ID, "name": "Mixed Site"},)  # One approved site.
    targets = (  # One access point and one switch, so the operation holds two child jobs.
        DeviceTarget(AP_MAC, "ap-one", "ap", "AP45", "0.14.1", "0.15.1", SITE_ID),
        DeviceTarget(SWITCH_MAC, "switch-one", "switch", "EX4400", "23.4R1.8", "23.4R1.9", SITE_ID),
    )
    record = service.build(AggregateBuildInput("owner", ORG_ID, sites, targets, UpgradeOptions(), "nonce"))
    for child in record["children"]:  # Each child job holds a cloud job.
        child["upgrade_id"] = f"job-{child['device_family']}"  # The cloud identity of the child job.
        child["status"] = states[child["device_family"]]  # The state of the last status read.
    record["state"] = "running"  # One child job still runs, so the operation takes a cancel.
    return record


def cancel_of(store: CasStore, family: str) -> dict[str, Any]:
    """Return the stored cancel result of the child job of one family."""
    child = next(child for child in store.record["children"] if child["device_family"] == family)  # One family.
    return child["cancellation"]  # The result that the cancel stored.


def test_a_completed_child_job_gets_no_call_and_its_running_sibling_does() -> None:
    """The completed access point job keeps its devices, and the running switch job stops."""
    edge = CloudEdge()  # The cloud edge of both child job families.
    service = AggregateUpgradeService(edge, edge)  # The production cancel.
    store = CasStore(running_operation(service, {"ap": "completed", "switch": "running"}))  # The durable store.
    service.cancel(WRITE_SESSION, deepcopy(store.record), store)  # The operator sends the typed cancel.
    assert edge.cancels == ["job-switch"]  # Only the running child job got a cancel request.
    ended = cancel_of(store, "ap")  # The result of the completed child job.
    assert ended["status"] == ENDED_CHILD_STATUS  # The word that the page prints.
    assert ended["state"] == "completed"  # The final state of the child job.
    assert ended["message"] == "The child job already ended: completed. The portal sent no cancel request."
    assert {key: ended[key] for key in EMPTY_LISTS} == EMPTY_LISTS  # No access point reads as cancelled.
    assert cancel_of(store, "switch")["cancelled"] == [SWITCH_MAC]  # The running switch job stopped.


def test_a_running_access_point_job_still_gets_its_sorted_cancel() -> None:
    """The access point job still runs, so the cancel of issue #3246 still sorts its devices."""
    edge = CloudEdge()  # The cloud edge of both child job families.
    service = AggregateUpgradeService(edge, edge)  # The production cancel.
    store = CasStore(running_operation(service, {"ap": "running", "switch": "failed"}))  # The durable store.
    service.cancel(WRITE_SESSION, deepcopy(store.record), store)  # The operator sends the typed cancel.
    assert edge.cancels == ["job-ap"]  # The failed switch job got no request.
    assert cancel_of(store, "ap")["status"] == "requested"  # The access point job took the cancel.
    assert cancel_of(store, "switch")["status"] == ENDED_CHILD_STATUS  # The failed job ended before the cancel.


@pytest.mark.parametrize("state", sorted(FINAL_CHILD_STATES))
def test_each_final_child_state_gets_no_call(state: str) -> None:
    """A child job in any final state gets no request, and its result names the state."""
    edge = CloudEdge()  # The cloud edge of both child job families.
    service = AggregateUpgradeService(edge, edge)  # The production cancel.
    store = CasStore(running_operation(service, {"ap": "running", "switch": state}))  # The durable store.
    service.cancel(WRITE_SESSION, deepcopy(store.record), store)  # The operator sends the typed cancel.
    assert edge.cancels == ["job-ap"]  # The ended switch job got no request.
    assert cancel_of(store, "switch")["state"] == state  # The result keeps the final state.
    assert cancel_of(store, "switch")["message"] == ENDED_CHILD_TEXT.format(state=state)  # One sentence.


def test_a_child_job_with_no_identifier_stays_unavailable() -> None:
    """The identifier check stays first, so the proof of no cloud job stays (issue #3327)."""
    edge = CloudEdge()  # The cloud edge of both child job families.
    service = AggregateUpgradeService(edge, edge)  # The production cancel.
    record = running_operation(service, {"ap": "running", "switch": "rejected"})  # The cloud refused the switch.
    switch = next(child for child in record["children"] if child["device_family"] == "switch")  # The refused job.
    switch["upgrade_id"] = None  # The cloud created no job for it.
    store = CasStore(record)  # The durable store.
    service.cancel(WRITE_SESSION, deepcopy(store.record), store)  # The operator sends the typed cancel.
    assert edge.cancels == ["job-ap"]  # The refused job got no request.
    assert cancel_of(store, "switch")["status"] == "unavailable"  # The result of issue #3246 stays.


def test_a_repeated_cancel_sends_no_second_call() -> None:
    """The stored results block a second request to each child job."""
    edge = CloudEdge()  # The cloud edge of both child job families.
    service = AggregateUpgradeService(edge, edge)  # The production cancel.
    store = CasStore(running_operation(service, {"ap": "completed", "switch": "running"}))  # The durable store.
    service.cancel(WRITE_SESSION, deepcopy(store.record), store)  # The first typed cancel.
    service.cancel(WRITE_SESSION, deepcopy(store.record), store)  # A second typed cancel.
    assert edge.cancels == ["job-switch"]  # One request in total.
    assert len(store.record["cancellation"]["results"]) == 2  # Each child job keeps one result.


def test_the_ended_words_stay_fixed() -> None:
    """The page and the tests read these two values."""
    assert ENDED_CHILD_STATUS == "already_ended"  # The status word of an ended child job.
    assert ENDED_CHILD_TEXT.format(state="failed") == (
        "The child job already ended: failed. The portal sent no cancel request."
    )
