"""Unit tests for the refusal of a cancel of a final multi-site operation.

Why:
    Issue #3225. A cancel of a completed operation sent one cloud cancel call
    for each child job, and the result listed each upgraded access point as a
    cancelled device. The single-site stop refuses a final run with no cloud
    request. These tests prove that the aggregate service refuses a final
    operation before any store write and before any cloud call.
"""

from __future__ import annotations

from copy import deepcopy
from types import SimpleNamespace
from typing import Any

import pytest

from src.firmware.aggregate_upgrade_service import (
    FINAL_OPERATION_STATES,
    AggregateBuildInput,
    AggregateUpgradeService,
    FinalOperationError,
)
from src.firmware.org_upgrade_service import OrgUpgradeResult
from src.firmware.upgrade_service import CancelOutcome, DeviceTarget, UpgradeOptions

ORG_ID = "44444444-4444-4444-4444-444444444444"  # The organization of the operation.
SITE_ID = "55555555-5555-5555-5555-555555555555"  # The one site of the operation.
AP_MAC = "001122334455"  # The access point of the organization child job.
SWITCH_MAC = "001122334466"  # The switch of the site child job.
WRITE_SESSION = SimpleNamespace(_MAX_429_RETRIES=0, _session=SimpleNamespace(adapters={}))  # A no-retry session.


class CountingStore:
    """Keep one record behind a compare-and-set, and count each accepted write."""

    def __init__(self, record: dict[str, Any]) -> None:
        """Store one detached record, and start with no write."""
        self.record = deepcopy(record)  # The durable value.
        self.writes = 0  # Each accepted compare-and-set adds one.

    def read_run(self, run_id: str) -> dict[str, Any] | None:
        """Return one detached record, or None for another key."""
        return deepcopy(self.record) if self.record.get("run_id") == run_id else None  # Match the key.

    def compare_and_set_run(self, run_id: str, expected_version: int, replacement: dict[str, Any]) -> bool:
        """Replace the record only when its version matches."""
        if self.record.get("run_id") != run_id or self.record.get("record_version") != expected_version:
            return False  # A stale caller changes nothing.
        self.record = deepcopy(replacement)  # Store the detached replacement.
        self.writes += 1  # Count the write for the test.
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


def submitted_operation(service: AggregateUpgradeService, state: str, child_state: str) -> dict[str, Any]:
    """Build one operation whose two child jobs reached the cloud.

    Args:
        service: The production service with the cloud stand-in.
        state: The stored state of the operation.
        child_state: The stored state of each child job.

    Returns:
        The record, as the store holds it after the reads.
    """
    sites = ({"site_id": SITE_ID, "name": "Final Site"},)  # One approved site.
    targets = (  # One access point and one switch, so the operation holds two child jobs.
        DeviceTarget(AP_MAC, "ap-one", "ap", "AP45", "0.14.1", "0.15.1", SITE_ID),
        DeviceTarget(SWITCH_MAC, "switch-one", "switch", "EX4400", "23.4R1.8", "23.4R1.9", SITE_ID),
    )
    record = service.build(AggregateBuildInput("owner", ORG_ID, sites, targets, UpgradeOptions(), "nonce"))
    for child in record["children"]:  # Each child job holds a cloud job.
        child["upgrade_id"] = f"job-{child['device_family']}"  # The cloud identity of the child job.
        child["status"] = child_state  # The last read state.
    record["state"] = state  # The stored state of the operation.
    return record


@pytest.mark.parametrize("state", sorted(FINAL_OPERATION_STATES))
def test_a_final_operation_refuses_the_cancel_with_no_write_and_no_call(state: str) -> None:
    """A final operation raises the refusal, and the store and the cloud see nothing."""
    edge = CloudEdge()  # The cloud edge of both child job families.
    service = AggregateUpgradeService(edge, edge)  # The production cancel.
    record = submitted_operation(service, state, "completed")  # The stored operation.
    store = CountingStore(record)  # The durable store.
    with pytest.raises(FinalOperationError, match=f"The operation is final: {state}."):
        service.cancel(WRITE_SESSION, deepcopy(record), store)  # The operator sends the typed cancel.
    assert (edge.cancels, store.writes) == ([], 0)  # No cloud call and no store write.
    assert store.record["cancellation"] == record["cancellation"]  # The stored marker stays as it was.


def test_the_refusal_reads_the_stored_state_and_not_the_page_copy() -> None:
    """A stale copy that reads running cannot pass a stored final state."""
    edge = CloudEdge()  # The cloud edge of both child job families.
    service = AggregateUpgradeService(edge, edge)  # The production cancel.
    stored = submitted_operation(service, "completed", "completed")  # The store holds the final state.
    store = CountingStore(stored)  # The durable store.
    stale = {**deepcopy(stored), "state": "running"}  # The copy of an old page.
    with pytest.raises(FinalOperationError):
        service.cancel(WRITE_SESSION, stale, store)  # The service reads the store first.
    assert (edge.cancels, store.writes) == ([], 0)  # No cloud call and no store write.


def test_the_refusal_is_a_value_error_for_the_existing_handlers() -> None:
    """Each existing handler of a cancel conflict still catches the refusal."""
    assert issubclass(FinalOperationError, ValueError)  # The route and the tests catch ValueError.
    assert FINAL_OPERATION_STATES == frozenset({"cancelled", "completed", "failed"})  # The three final words.


@pytest.mark.parametrize("state", ["running", "partial", "attention_required"])
def test_a_live_operation_still_sends_each_child_cancel(state: str) -> None:
    """A live operation keeps the cancel of issue #3246."""
    edge = CloudEdge()  # The cloud edge of both child job families.
    service = AggregateUpgradeService(edge, edge)  # The production cancel.
    record = submitted_operation(service, state, "running")  # A live operation.
    store = CountingStore(record)  # The durable store.
    service.cancel(WRITE_SESSION, deepcopy(record), store)  # The operator sends the typed cancel.
    assert sorted(edge.cancels) == ["job-ap", "job-switch"]  # One cancel call for each child job.
    assert store.record["cancellation"]["requested"] is True  # The store holds the cancel marker.
