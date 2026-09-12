"""Unit tests for the multi-site aggregate upgrade boundary."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from threading import Lock, Thread
from types import SimpleNamespace
from typing import Any

import pytest

from src.firmware.aggregate_upgrade_service import AggregateBuildInput, AggregateUpgradeService
from src.firmware.org_upgrade_service import OrgUpgradeResult
from src.firmware.upgrade_service import CancelOutcome, DeviceTarget, UpgradeOptions, UpgradeSubmission

ORG_ID = "11111111-1111-1111-1111-111111111111"
SITE_ONE = "22222222-2222-2222-2222-222222222222"
SITE_TWO = "33333333-3333-3333-3333-333333333333"
SAFE_SESSION = SimpleNamespace(_MAX_429_RETRIES=0, _session=SimpleNamespace(adapters={}))


class CasStore:
    """Keep one aggregate record behind a thread-safe compare-and-set."""

    def __init__(self, record: dict[str, Any]) -> None:
        """Store one detached initial record."""
        self.record = deepcopy(record)  # Keep caller edits outside the durable value.
        self.guard = Lock()  # Serialize each read and compare-and-set action.

    def read_run(self, run_id: str) -> dict[str, Any] | None:
        """Return one detached record."""
        with self.guard:  # Keep the read consistent with concurrent replacements.
            return deepcopy(self.record) if self.record.get("run_id") == run_id else None  # Match the key.

    def compare_and_set_run(self, run_id: str, expected_version: int, replacement: dict[str, Any]) -> bool:
        """Replace the record only when its version matches."""
        with self.guard:  # Keep comparison and replacement atomic.
            if self.record.get("run_id") != run_id or self.record.get("record_version") != expected_version:
                return False  # Reject a stale caller.
            self.record = deepcopy(replacement)  # Store the detached accepted replacement.
            return True  # Report the successful atomic change.


def permit_lock(record: Mapping[str, Any], child: Mapping[str, Any]) -> None:
    """Permit one test child lock refresh."""
    del record, child  # The service tests do not exercise the Redis boundary.


class OrgServiceStandIn:
    """Record AP child calls and return fixed outcomes."""

    def __init__(self) -> None:
        """Start with no calls."""
        self.calls: list[str] = []  # Each entry names one cloud action.

    def submit(self, session: Any, org_id: str, body: Any) -> OrgUpgradeResult:
        """Accept the one AP organization child."""
        self.calls.append("submit")  # Prove that the destructive write ran once.
        return OrgUpgradeResult(org_id, "ap-job", 200, {"id": "ap-job"}, None)  # A valid accepted answer.

    def status(self, session: Any, org_id: str, upgrade_id: str) -> OrgUpgradeResult:
        """Return a completed AP child."""
        self.calls.append("status")  # Prove that the poll reads the child.
        return OrgUpgradeResult(
            org_id,
            upgrade_id,
            200,
            {"id": upgrade_id, "status": "completed", "targets": {"upgraded": ["001122334455"]}},
            None,
        )

    def cancel(self, session: Any, org_id: str, upgrade_id: str) -> OrgUpgradeResult:
        """Accept one AP cancellation."""
        self.calls.append("cancel")  # Prove that cancellation runs once.
        return OrgUpgradeResult(org_id, upgrade_id, 200, {}, None)  # The contract permits an empty body.


class DeviceServiceStandIn:
    """Record site and SSR child calls with one rejected child."""

    ACCEPTED_STATUS = (200, 202)  # Match the production service contract.
    GatewayFamily = SimpleNamespace(SSR="ssr", JUNOS="junos")  # Supply the family values used by the reader.

    def __init__(self) -> None:
        """Start with no calls and reject the switch child."""
        self.calls: list[tuple[str, str]] = []  # Each row names the action and route.

    def invoke_upgrade(self, session: Any, plan: Any) -> UpgradeSubmission:
        """Accept gateway children and reject the switch child."""
        self.calls.append(("submit", plan.endpoint))  # Prove each plan runs once.
        accepted = plan.targets[0].device_type != "switch"  # One refusal creates a partial submission.
        return UpgradeSubmission(
            upgrade_id=f"{plan.endpoint}-job" if accepted else None,
            scope=plan.scope,
            accepted=tuple(target.mac for target in plan.targets) if accepted else (),
            rejected=() if accepted else ((plan.targets[0].mac, "refused"),),
            raw_status=202 if accepted else 400,
        )

    def read_upgrade_status(self, session: Any, scope: str, identifier: str, upgrade_id: str, family: Any) -> dict:
        """Return a running gateway child."""
        self.calls.append(("status", upgrade_id))  # Prove an accepted child is polled.
        return {"raw_status": 200, "status": "running", "status_known": True, "targets": {}}

    def cancel_upgrade(self, session: Any, plan: Any, upgrade_id: str, status: Any) -> CancelOutcome:
        """Return one cancellation result for each accepted gateway child."""
        self.calls.append(("cancel", plan.endpoint))  # Prove each child receives one cancel call.
        return CancelOutcome(tuple(target.mac for target in plan.targets), (), (), "The cloud accepted the cancel.")


def target(mac: str, device_type: str, model: str, site_id: str, version: str) -> DeviceTarget:
    """Build one selected target."""
    return DeviceTarget(mac, device_type, device_type, model, "old", version, site_id)  # Keep the test rows short.


def build_record(service: AggregateUpgradeService) -> dict[str, Any]:
    """Build an AP, switch, Junos gateway, and SSR operation."""
    sites = ({"site_id": SITE_ONE, "name": "One"}, {"site_id": SITE_TWO, "name": "Two"})
    targets = (
        target("001122334455", "ap", "AP45", SITE_ONE, "0.15.1"),
        target("001122334466", "switch", "EX4400", SITE_ONE, "23.4R1.9"),
        target("001122334477", "gateway", "SRX345", SITE_TWO, "23.4R1.9"),
        target("001122334488", "gateway", "SSR120", SITE_TWO, "6.3.0"),
    )
    request = AggregateBuildInput("owner", ORG_ID, sites, targets, UpgradeOptions(), "nonce")  # Group build values.
    return service.build(request)  # No cloud call runs here.


def test_build_routes_each_family_and_keeps_explicit_targets() -> None:
    """The plan uses one AP child and the proven site and SSR routes."""
    service = AggregateUpgradeService(OrgServiceStandIn(), DeviceServiceStandIn())  # Use stand-ins only.
    record = build_record(service)  # Build the complete operation.
    routes = [child["route"] for child in record["children"]]  # Read each cloud route.
    assert routes.count("upgradeOrgDevices") == 1  # All AP targets share one organization child.
    assert "upgradeSiteDevices" in routes  # Switch and Junos gateway groups use the site route.
    assert "upgradeOrgSsrs" in routes  # The existing planner preserves the SSR organization route.
    assert sum(len(child["target_ids"]) for child in record["children"]) == 4  # Every target is explicit.


def test_partial_submission_keeps_each_child_and_blocks_replay() -> None:
    """One child refusal stays visible and no child write repeats."""
    org = OrgServiceStandIn()  # Record AP calls.
    devices = DeviceServiceStandIn()  # Record site and SSR calls.
    service = AggregateUpgradeService(org, devices)  # Join the two safe boundaries.
    record = build_record(service)  # Build before any write.
    store = CasStore(record)  # Coordinate every destructive claim.
    service.submit(SAFE_SESSION, record, store, permit_lock)  # Send each child once.
    assert record["state"] == "partial"  # Active children keep the rejected operation nonterminal.
    assert any(child["status"] == "rejected" for child in record["children"])  # Keep the refused child.
    assert org.calls.count("submit") == 1  # The AP write ran once.
    assert len([call for call in devices.calls if call[0] == "submit"]) == 3  # Three non-AP groups ran once.
    with pytest.raises(ValueError, match="no untouched child"):  # The replay barrier rejects another submission.
        service.submit(SAFE_SESSION, record, store, permit_lock)


def test_mixed_status_and_cancellation_keep_all_results() -> None:
    """A poll and a cancel preserve completed, failed, and running children."""
    org = OrgServiceStandIn()  # Record AP actions.
    devices = DeviceServiceStandIn()  # Record other family actions.
    service = AggregateUpgradeService(org, devices)  # Build the aggregate boundary.
    record = build_record(service)  # Build every child.
    store = CasStore(record)  # Coordinate every state transition.
    service.submit(SAFE_SESSION, record, store, permit_lock)  # Create the partial submission.
    service.status(SAFE_SESSION, record, store)  # Poll each accepted child.
    assert {child["status"] for child in record["children"]} >= {"completed", "rejected", "running"}
    service.cancel(SAFE_SESSION, record, store)  # Cancel every child that has an identifier.
    results = record["cancellation"]["results"]  # Read every child cancellation result.
    assert len(results) == len(record["children"])  # No child result disappears.
    assert any(result["status"] == "unavailable" for result in results)  # The rejected child has no job identifier.
    service.cancel(SAFE_SESSION, record, store)  # A repeated request continues without duplicate cloud calls.
    assert org.calls.count("cancel") == 1  # The AP cancellation did not repeat.


def test_concurrent_parent_claim_allows_one_submitter() -> None:
    """Only one concurrent request can claim and submit the parent."""
    org = OrgServiceStandIn()  # Record AP submissions.
    service = AggregateUpgradeService(org, DeviceServiceStandIn())  # Build one shared service.
    initial = build_record(service)  # Build the durable plan.
    store = CasStore(initial)  # Coordinate both threads under one lock.
    errors: list[Exception] = []  # Keep the losing request result.

    def submit_copy() -> None:
        """Submit one detached request snapshot."""
        snapshot = deepcopy(initial)  # Model two workers that read the same version.
        try:  # One worker must lose the parent claim.
            service.submit(SAFE_SESSION, snapshot, store, permit_lock)  # Attempt the complete flow.
        except Exception as fault:  # Preserve the expected conflict.
            errors.append(fault)  # Let the assertion inspect it.

    threads = [Thread(target=submit_copy) for _ in range(2)]  # Start two simultaneous request workers.
    for thread in threads:  # Start both workers.
        thread.start()  # Run the submission concurrently.
    for thread in threads:  # Wait for both outcomes.
        thread.join()  # Complete the concurrency test.
    assert len(errors) == 1  # Exactly one request lost the atomic parent claim.
    assert org.calls.count("submit") == 1  # The AP cloud write ran once.


def test_stale_submission_claim_becomes_unknown_without_replay() -> None:
    """A later status converts stale claims and stops untouched children."""
    service = AggregateUpgradeService(OrgServiceStandIn(), DeviceServiceStandIn())  # Use offline boundaries.
    record = build_record(service)  # Build a planned operation.
    stale = (datetime.now(UTC) - timedelta(minutes=6)).isoformat()  # Expire both claim leases.
    record["state"] = "submission_claimed"  # Model a lost parent request.
    record["submission_claim_id"] = "parent-claim"  # Preserve the lost request identity.
    record["submission_claimed_at"] = stale  # Make the parent claim recoverable.
    record["children"][0]["status"] = "submission_claimed"  # Model a cloud call with no stored answer.
    record["children"][0]["submission_claim_id"] = "child-claim"  # Preserve the child call identity.
    record["children"][0]["submission_claimed_at"] = stale  # Make the child claim stale.
    store = CasStore(record)  # Persist the interrupted state.
    service.status(SAFE_SESSION, record, store)  # Recover before any ordinary status read.
    assert record["children"][0]["status"] == "submission_unknown"  # Never repeat the claimed call.
    assert all(child["status"] != "planned" for child in record["children"])  # Stop untouched children.
    assert record["state"] == "attention_required"  # Require operator reconciliation.


def test_read_unknown_retries_and_recovers() -> None:
    """A transient status failure remains readable on the next poll."""

    class FlakyOrg(OrgServiceStandIn):
        """Fail one status read and then return completion."""

        def __init__(self) -> None:
            """Start with one pending failure."""
            super().__init__()  # Keep the call recorder.
            self.fail = True  # Fail the first read only.

        def status(self, session: Any, org_id: str, upgrade_id: str) -> OrgUpgradeResult:
            """Fail once and then return the normal result."""
            if self.fail:  # Model one transient timeout.
                self.fail = False  # Let the next read recover.
                raise TimeoutError("stand-in timeout")  # Trigger read_unknown.
            return super().status(session, org_id, upgrade_id)  # Return completion.

    org = FlakyOrg()  # Install the transient AP reader.
    service = AggregateUpgradeService(org, DeviceServiceStandIn())  # Keep all calls offline.
    record = build_record(service)  # Build the complete plan.
    store = CasStore(record)  # Coordinate each transition.
    service.submit(SAFE_SESSION, record, store, permit_lock)  # Create known child identifiers.
    service.status(SAFE_SESSION, record, store)  # Store the transient read failure.
    assert record["children"][0]["status"] == "read_unknown"  # Keep the child retryable.
    service.status(SAFE_SESSION, record, store)  # Retry the safe GET.
    assert record["children"][0]["status"] == "completed"  # Recover on the next poll.


def test_ap_status_derives_nested_mixed_site_state() -> None:
    """Nested AP site states preserve active and failed work as partial."""
    result = OrgUpgradeResult(
        ORG_ID,
        "ap-job",
        200,
        {
            "site_upgrades": [
                {"site_id": SITE_ONE, "upgrade": {"status": "upgrading"}},
                {"site_id": SITE_TWO, "status": "failed"},
            ]
        },
        None,
    )  # Supply no root status.
    assert AggregateUpgradeService._org_status(result) == "partial"  # Active work prevents terminal failure.


def test_lock_loss_marks_current_and_untouched_children() -> None:
    """A lock loss stops later cloud writes and marks untouched children."""
    org = OrgServiceStandIn()  # Record the first AP write.
    devices = DeviceServiceStandIn()  # Record later device writes.
    service = AggregateUpgradeService(org, devices)  # Build the aggregate boundary.
    record = build_record(service)  # Build four planned children.
    store = CasStore(record)  # Coordinate each state change.
    refreshes = 0  # Fail the second child lock refresh.

    def fail_second(operation: Mapping[str, Any], child: Mapping[str, Any]) -> None:
        """Fail the second lock refresh."""
        nonlocal refreshes  # Count refreshes across child calls.
        del operation, child  # The count alone selects the failure.
        refreshes += 1  # Record this immediate pre-claim check.
        if refreshes == 2:  # Simulate a lost lock before the second cloud write.
            raise RuntimeError("lock lost")  # Stop all later submissions.

    service.submit(SAFE_SESSION, record, store, fail_second)  # Submit until the lock fails.
    assert org.calls.count("submit") == 1  # The first child wrote before the later loss.
    assert not [call for call in devices.calls if call[0] == "submit"]  # No later cloud write ran.
    assert [child["status"] for child in record["children"][1:]] == ["not_submitted"] * 3  # Mark all untouched.
    assert record["state"] == "attention_required"  # Show the safe stop.


def test_stale_cancel_claim_does_not_repeat_and_continues() -> None:
    """A later cancellation marks a stale claim unknown and cancels untouched children."""
    org = OrgServiceStandIn()  # Record AP cancellation calls.
    devices = DeviceServiceStandIn()  # Record device cancellation calls.
    service = AggregateUpgradeService(org, devices)  # Build the aggregate boundary.
    record = build_record(service)  # Build four planned children.
    store = CasStore(record)  # Coordinate all claims.
    service.submit(SAFE_SESSION, record, store, permit_lock)  # Create known child jobs.
    stale = (datetime.now(UTC) - timedelta(minutes=6)).isoformat()  # Expire one cancellation claim.
    first = record["children"][0]  # Select the AP child.
    first["cancellation"] = {
        "status": "cancel_claimed",
        "claim_id": "old-cancel",
        "claimed_at": stale,
        "message": "The cancellation request is in progress.",
    }  # Model a lost response after the AP cancel call.
    store.record = deepcopy(record)  # Persist the interrupted cancellation.
    service.cancel(SAFE_SESSION, record, store)  # Recover and continue later children.
    assert record["children"][0]["cancellation"]["status"] == "cancel_unknown"  # Never repeat the AP cancel.
    assert org.calls.count("cancel") == 0  # The stale AP call did not run again.
    assert len([call for call in devices.calls if call[0] == "cancel"]) == 2  # Eligible untouched jobs ran once.
