"""Offline integration test for aggregate persistence and orchestration."""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any

from src.firmware.aggregate_upgrade_service import AggregateBuildInput, AggregateUpgradeService
from src.firmware.org_upgrade_service import OrgUpgradeResult
from src.firmware.upgrade_service import CancelOutcome, DeviceTarget, UpgradeOptions, UpgradeSubmission

ORG_ID = "11111111-1111-1111-1111-111111111111"
SITE_ID = "22222222-2222-2222-2222-222222222222"
SAFE_SESSION = SimpleNamespace(_MAX_429_RETRIES=0, _session=SimpleNamespace(adapters={}))


class JsonStore:
    """Simulate a durable document store through a JSON round trip."""

    def __init__(self) -> None:
        """Start with no document."""
        self.document: dict[str, Any] | None = None

    def write(self, record: dict[str, Any]) -> None:
        """Persist one detached JSON document."""
        self.document = json.loads(json.dumps(record))  # Reject a value that the real store cannot serialize.

    def read_run(self, run_id: str) -> dict[str, Any] | None:
        """Return one detached JSON record."""
        if self.document is None or self.document.get("run_id") != run_id:  # Match the durable key.
            return None  # Report an absent record.
        return json.loads(json.dumps(self.document))  # Detach the returned value.

    def compare_and_set_run(self, run_id: str, expected_version: int, replacement: dict[str, Any]) -> bool:
        """Replace one JSON record only when its version matches."""
        if self.document is None or self.document.get("run_id") != run_id:  # Require the stored key.
            return False  # Reject an absent record.
        if self.document.get("record_version") != expected_version:  # Reject a stale version.
            return False  # Preserve the current record.
        self.write(replacement)  # Store the accepted JSON replacement.
        return True  # Report the successful comparison.


class OrgStandIn:
    """Return an accepted AP child and an unknown status."""

    @staticmethod
    def submit(session: Any, org_id: str, body: Any) -> OrgUpgradeResult:
        """Accept the AP child."""
        return OrgUpgradeResult(org_id, "ap-job", 200, {"id": "ap-job"}, None)

    @staticmethod
    def status(session: Any, org_id: str, upgrade_id: str) -> OrgUpgradeResult:
        """Preserve an unreadable AP status."""
        raise TimeoutError("stand-in timeout")

    @staticmethod
    def cancel(session: Any, org_id: str, upgrade_id: str) -> OrgUpgradeResult:
        """Accept the AP cancellation."""
        return OrgUpgradeResult(org_id, upgrade_id, 200, {}, None)


class DeviceStandIn:
    """Accept and read each site child."""

    ACCEPTED_STATUS = (200, 202)  # Match the production contract.

    @staticmethod
    def invoke_upgrade(session: Any, plan: Any) -> UpgradeSubmission:
        """Accept one site child."""
        return UpgradeSubmission(
            f"{plan.targets[0].device_type}-job",
            plan.scope,
            tuple(target.mac for target in plan.targets),
            (),
            202,
        )

    @staticmethod
    def read_upgrade_status(
        session: Any,
        scope: str,
        identifier: str,
        upgrade_id: str,
        family: Any,
    ) -> dict[str, Any]:
        """Return a completed site child."""
        return {"raw_status": 200, "status": "completed", "status_known": True, "targets": {}}

    @staticmethod
    def cancel_upgrade(session: Any, plan: Any, upgrade_id: str, status: Any) -> CancelOutcome:
        """Accept one site cancellation."""
        return CancelOutcome(tuple(target.mac for target in plan.targets), (), (), "The cancel was accepted.")


def test_persisted_operation_keeps_partial_submission_status_and_cancel_results() -> None:
    """The JSON record keeps every child through submit, status, and cancel."""
    service = AggregateUpgradeService(OrgStandIn, DeviceStandIn)  # Use no live API.
    store = JsonStore()  # Force every save through serialization.
    targets = (
        DeviceTarget("001122334455", "ap", "ap", "AP45", "old", "0.15.1", SITE_ID),
        DeviceTarget("001122334466", "switch", "switch", "EX4400", "old", "23.4R1.9", SITE_ID),
        DeviceTarget("001122334477", "gateway", "gateway", "SRX345", "old", "23.4R1.9", SITE_ID),
    )
    request = AggregateBuildInput(
        "owner",
        ORG_ID,
        ({"site_id": SITE_ID, "name": "Site"},),
        targets,
        UpgradeOptions(),
        "nonce",
    )
    record = service.build(request)  # Build the durable operation without a cloud call.
    store.write(record)  # Persist the plan before a destructive call.
    service.submit(SAFE_SESSION, record, store, lambda operation, child: None)  # Submit every child once.
    service.status(SAFE_SESSION, record, store)  # Keep the AP timeout and completed site results.
    service.cancel(SAFE_SESSION, record, store)  # Keep every cancellation result.
    assert store.document is not None  # The operation survived every transition.
    assert {child["status"] for child in store.document["children"]} >= {"read_unknown", "completed"}
    assert len(store.document["cancellation"]["results"]) == 3  # Every child has a cancellation result.
