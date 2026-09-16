"""Test the reconciliation evidence placeholders in durable action records."""

from __future__ import annotations  # Keep each annotation independent from import order.

from datetime import UTC, datetime  # Build an aware reconciliation clock for service tests.
from typing import Any, Final  # Type safe evidence fields and fixed test times.

import pytest  # Exercise the evidence validation refusals.

from src.upgrade_portal.api.run_controls.services.reconciliation import StoppingRunReconciler  # Test the service.
from src.upgrade_portal.persistence.actions import (  # Test only action source and evidence placeholders.
    RUN_COLLECTION,
    ActionIdentity,
    ActionInitialization,
    ActionIntent,
    ActionLease,
    ActionRepository,
    ActionSource,
    DurableActorScope,
    OutcomeCompletion,
    OutcomeState,
    UpgradeRunAction,
    canonical_digest,
)
from tests.integration.upgrade_portal.run_controls import FakeDatabase  # Use a controlled ArangoDB stand-in.

ACTION_TIME: Final[str] = "2026-09-11T14:00:00+00:00"  # Fix the evidence observation and action time.
LEASE_TIME: Final[str] = "2026-09-11T14:05:00+00:00"  # Keep the controlled action lease current.
REQUEST_KEY: Final[str] = "visible-reconcile-key-0001"  # Meet the HTTP request key length.


def _reconciliation_action() -> UpgradeRunAction:
    """Return one pending single-run reconciliation action."""
    actor = DurableActorScope.build("email", "operator@example.invalid")  # Build one stable actor scope.
    fields = {"action": "reconcile", "run_ids": ["run-one"]}  # Bind the source-specific request fields.
    identity = ActionIdentity.from_request(actor, REQUEST_KEY, fields, "RECONCILE run-one")  # Hash raw values.
    source = ActionSource.reconciliation("org-one")  # Store no preview identifier, digest, or history scope.
    intent = ActionIntent("reconcile", ("run-one",), ("site-one",), 1)  # Keep one run and one site.
    request = ActionInitialization(identity, source, intent)  # Enforce the single-run source relation.
    return UpgradeRunAction.initialize(request, ActionLease("worker-one", LEASE_TIME), ACTION_TIME)  # Start.


def _target_evidence() -> dict[str, Any]:
    """Return one safe target evidence row."""
    return {  # Use only the approved safe target evidence fields.
        "target_digest": canonical_digest("target-one"),  # Replace the raw target identifier.
        "stored_stop_result": "cancel_accepted",  # Preserve the prior stored stop result.
        "task_digest": canonical_digest("task-one"),  # Replace the raw cloud task identifier.
        "task_state": "final",  # Prove the cloud task is no longer active.
        "write_state": "not_writing",  # Prove the target does not write firmware.
        "driver_state": "stopped",  # Preserve the stored final driver state.
        "sources": ["cloud_task", "device", "driver", "stored"],  # Keep the approved source names.
        "observed_at": ACTION_TIME,  # State when the current reads completed.
        "is_complete": True,  # State that this target has sufficient proof.
        "has_conflict": False,  # State that the evidence sources agree.
        "conflict_reason": None,  # Store null because no source conflicts.
        "version_target": "24.2R2-S3.3",  # Store the requested firmware version used for comparison.
        "running_version": "24.2R2-S3.3",  # Store the running version from the approved stats endpoint.
        "fwupdate_status": "success",  # Store the firmware job success token from current evidence.
        "firmware_success": True,  # Store the proven firmware success conclusion.
    }


def _evidence_summary() -> dict[str, Any]:
    """Return one canonical safe reconciliation evidence summary."""
    basis = {  # Build every canonical evidence field except its own digest.
        "schema_version": 1,  # Use the first safe evidence schema.
        "run_id": "run-one",  # Link the evidence to its source run.
        "run_revision": "revision-one",  # Bind the decision to the evidence read.
        "collected_at": ACTION_TIME,  # State when collection completed.
        "targets": [_target_evidence()],  # Preserve one safe target evidence row.
        "target_count": 1,  # Match the target list length.
        "complete_target_count": 1,  # Count the target with complete proof.
        "firmware_success_count": 1,  # Count the target with proven firmware success.
        "active_write_count": 0,  # Prove no target writes firmware.
        "active_task_count": 0,  # Prove no cloud task remains active.
        "unknown_target_count": 0,  # Prove no target lacks evidence.
        "has_conflict": False,  # Prove no evidence source conflicts.
        "is_complete": True,  # Prove the complete run has sufficient evidence.
    }
    return {**basis, "decision_basis_digest": canonical_digest(basis)}  # Bind the complete safe summary.


def test_reconciliation_placeholder_starts_with_null_evidence_fields() -> None:
    """A reconciliation placeholder stores no evidence before collection starts."""
    action = _reconciliation_action()  # Build one direct single-run action.
    document = action.document()  # Read the exact durable storage shape.
    assert document["evidence_summary_digest"] is None  # Store no parent proof before evidence exists.
    assert document["items"][0]["evidence_summary"] is None  # Store no item proof before evidence exists.
    assert document["preview_id"] is None  # Require no bulk preview identifier.
    assert document["preview_digest"] is None  # Require no bulk preview digest.
    assert document["history_scope"] is None  # Require no bulk history scope.


def test_stopped_reconciliation_outcome_requires_safe_matching_evidence() -> None:
    """A final stopped result stores one safe summary and its matching parent digest."""
    action = _reconciliation_action()  # Build one pending single-run action.
    claimed = action.item("run-one").claimed("worker-one", LEASE_TIME)  # Claim before possible mutation.
    state = OutcomeState("stopping", "stopped", ACTION_TIME, ACTION_TIME)  # Describe the proven state change.
    completion = OutcomeCompletion(  # Build the final successful reconciliation result.
        "succeeded",  # State the verified successful classification.
        "stopping_run_reconciled",  # Use the stable reconciliation reason.
        "The portal confirmed that no selected firmware task remains.",  # Use safe operator text.
        "run-one",  # Name the changed source run.
        state,  # Preserve prior, final, and observation values.
    )
    outcome = claimed.finalized(completion, _evidence_summary())  # Store safe proof with the final item.
    changed = action.with_item(outcome)  # Bind the matching digest in the same immutable change.
    assert changed.lifecycle.evidence_summary_digest == _evidence_summary()["decision_basis_digest"]  # Match proof.
    assert changed.document()["items"][0]["evidence_summary"]["target_count"] == 1  # Preserve safe summary data.


def test_stopped_reconciliation_outcome_rejects_missing_evidence() -> None:
    """A stopped result cannot claim success without its complete evidence summary."""
    claimed = _reconciliation_action().item("run-one").claimed("worker-one", LEASE_TIME)  # Claim one item.
    state = OutcomeState("stopping", "stopped", ACTION_TIME, ACTION_TIME)  # Describe a stopped claim.
    completion = OutcomeCompletion(
        "succeeded", "stopping_run_reconciled", "The portal reconciled the run.", "run-one", state
    )
    with pytest.raises(ValueError, match="requires evidence"):  # Refuse an unproved stopped state.
        claimed.finalized(completion)  # Store no unsafe success placeholder.


def test_reconciliation_evidence_rejects_an_unsafe_field_or_digest_mismatch() -> None:
    """Evidence rejects raw fields and any changed canonical decision content."""
    action = _reconciliation_action()  # Build one pending single-run action.
    claimed = action.item("run-one").claimed("worker-one", LEASE_TIME)  # Claim before a final result.
    state = OutcomeState("stopping", "", ACTION_TIME, ACTION_TIME)  # Make no final state claim.
    completion = OutcomeCompletion("unknown", "cloud_evidence_conflict", "The cloud evidence conflicts.", "", state)
    unsafe = _evidence_summary()  # Start from one valid canonical safe summary.
    unsafe["raw_target_id"] = "device-secret"  # Add a prohibited raw identifier field.
    with pytest.raises(ValueError, match="unsafe or missing field"):  # Refuse unsafe response content.
        claimed.finalized(completion, unsafe)  # Store no raw target identifier.
    changed = _evidence_summary()  # Start from another valid summary.
    changed["active_task_count"] = 1  # Change the decision basis without changing its digest.
    with pytest.raises(ValueError, match="digest does not match"):  # Refuse unbound evidence.
        claimed.finalized(completion, changed)  # Store no mismatched proof.


class _OpenGuard:
    """Permit one controlled reconciliation request."""

    def refusal(self, organization_id: str, site_id: str) -> None:
        """Return no refusal for the controlled organization and site."""
        assert organization_id == "org-one"  # Prove the service rechecks the requested organization.
        assert site_id == "site-one"  # Prove the service rechecks the requested site.
        return None  # Permit the controlled mutation.


def _issue_2614_run() -> dict[str, Any]:
    """Return the failed stored run from issue #2614."""
    return {  # Keep the stored shape that caused the false failure.
        "_key": "run-51f8c319224a4db099ea2e3b14a16233",
        "run_id": "run-51f8c319224a4db099ea2e3b14a16233",
        "site_id": "site-one",
        "org_id": "org-one",
        "state": "failed",
        "updated_at": "2026-09-13T07:57:26.134040+00:00",
        "error": {
            "stage": "upgrade",
            "message": "The gateways phase failed. 1 device(s) did not return before the phase limit.",
        },
        "targets": [
            {
                "mac": "5800bb5ee100",
                "device_type": "gateway",
                "state": "failed",
                "version_before": "23.4R2-S5.5",
                "version_target": "24.2R2-S3.3",
                "version_after": None,
                "reboot_seen_at": None,
                "settled_at": None,
            }
        ],
        "phases": [{"name": "gateways", "state": "failed", "settled": 0, "total": 1}],
    }


def _issue_2614_evidence() -> list[dict[str, Any]]:
    """Return the positive cloud evidence from issue #2614."""
    return [
        {
            "target_id": "5800bb5ee100",
            "stored_stop_result": "unknown",
            "task_state": "final",
            "write_state": "not_writing",
            "driver_state": "failed",
            "sources": ["device", "driver", "stored"],
            "observed_at": ACTION_TIME,
            "is_complete": True,
            "has_conflict": False,
            "version_target": "24.2R2-S3.3",
            "running_version": "24.2R2-S3.3",
            "fwupdate_status": "success",
        }
    ]


def _repository_with_run(record: dict[str, Any]) -> tuple[FakeDatabase, ActionRepository]:
    """Return one action repository that holds the supplied run."""
    database = FakeDatabase()  # Start one isolated action and run store.
    database.create_collection(RUN_COLLECTION)  # Create the authoritative run collection.
    repository = ActionRepository(database)  # Use the production repository with the fake database.
    repository.bootstrap()  # Create the action collection before reconciliation runs.
    database.collection(RUN_COLLECTION).insert(dict(record))  # Store the source run with a fake revision.
    return database, repository  # Let the test inspect the final run.


def test_issue_2614_failed_gateway_run_reconciles_from_firmware_success() -> None:
    """A stored false failure becomes complete without invented settle times."""
    record = _issue_2614_run()  # Reproduce the failed stored run from the issue.
    database, repository = _repository_with_run(record)  # Store it behind the production action repository.
    service = StoppingRunReconciler(  # Use the production service with controlled seams.
        repository,
        lambda run_id: database.collection(RUN_COLLECTION).get(run_id),
        _OpenGuard(),
        lambda _record, _now: _issue_2614_evidence(),
        lambda: datetime(2026, 9, 15, 14, 0, tzinfo=UTC),
    )
    actor = DurableActorScope.build("email", "operator@example.invalid")  # Bind the durable action owner.
    action = service.reconcile(  # Run the repair through the durable reconciliation path.
        actor=actor,
        idempotency_key="issue-2614-reconcile-key",
        confirmation="RECONCILE run-51f8c319224a4db099ea2e3b14a16233",
        run_id="run-51f8c319224a4db099ea2e3b14a16233",
        organization_id="org-one",
        site_id="site-one",
    )
    repaired = database.collection(RUN_COLLECTION).get("run-51f8c319224a4db099ea2e3b14a16233")  # Read result.
    target = repaired["targets"][0]  # The issue record holds one target.
    assert action.ledger.items[0].completion.reason == "failed_run_reconciled"  # Store the repair reason.
    assert repaired["state"] == "complete"  # Do not keep the false failed terminal state.
    assert repaired["error"] is None  # Remove the false failure message from the active result.
    assert target["state"] == "settled"  # Do not store the target as failed after positive cloud evidence.
    assert target["version_after"] == "24.2R2-S3.3"  # Store the approved running version.
    assert target["reboot_seen_at"] is None  # Do not invent a reboot time that the gate did not measure.
    assert target["settled_at"] is None  # Do not invent a settle time that the gate did not measure.
    assert target["reconciliation_state"] == "firmware_success_unmeasured_settle"  # Explain null proof fields.
