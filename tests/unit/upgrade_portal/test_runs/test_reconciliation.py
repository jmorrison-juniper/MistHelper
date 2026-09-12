"""Test the reconciliation evidence placeholders in durable action records."""

from __future__ import annotations  # Keep each annotation independent from import order.

from datetime import datetime
from typing import Any, Final  # Type safe evidence fields and fixed test times.

import pytest  # Exercise the evidence validation refusals.

from src.upgrade_portal.api.run_controls.services import (
    ReconciliationEvidence,
    SiteMutationGuard,
    StoppingRunReconciler,
    TargetEvidence,
)
from src.upgrade_portal.persistence.actions import (  # Test only action source and evidence placeholders.
    ActionIdentity,
    ActionInitialization,
    ActionIntent,
    ActionLease,
    ActionSource,
    DurableActorScope,
    OutcomeCompletion,
    OutcomeState,
    UpgradeRunAction,
    canonical_digest,
)
from tests.support.upgrade_portal_e2e.records.actions import ActionRecordStore
from tests.support.upgrade_portal_e2e.records.portal import PortalRecordStore

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


def test_evidence_summary_sorts_targets_and_sources_before_digest() -> None:
    """The canonical summary has stable target and source order."""
    second = TargetEvidence.from_mapping(
        {
            "target_id": "target-b",
            "stored_stop_result": "cancel_accepted",
            "task_state": "final",
            "write_state": "not_writing",
            "driver_state": "stopped",
            "sources": ["stored", "device", "cloud_task"],
            "observed_at": ACTION_TIME,
            "is_complete": True,
            "has_conflict": False,
        }
    )
    first = TargetEvidence.from_mapping(
        {
            "target_id": "target-a",
            "stored_stop_result": "not_requested",
            "task_state": "absent",
            "write_state": "not_writing",
            "sources": ["device", "stored"],
            "observed_at": ACTION_TIME,
            "is_complete": True,
            "has_conflict": False,
        }
    )

    summary = ReconciliationEvidence("run-one", "1", ACTION_TIME, (second, first)).summary()

    assert [row["target_digest"] for row in summary["targets"]] == sorted(
        [canonical_digest("target-a"), canonical_digest("target-b")]
    )
    row_b = next(row for row in summary["targets"] if row["target_digest"] == canonical_digest("target-b"))
    assert row_b["sources"] == ["cloud_task", "device", "stored"]
    assert summary["decision_basis_digest"] == canonical_digest(
        {key: value for key, value in summary.items() if key != "decision_basis_digest"}
    )


def test_precloud_reconciliation_cancels_without_reading_cloud_evidence() -> None:
    """A stale pre-cloud run and its success outcome change in one action."""
    portal = PortalRecordStore("unit-reconcile")
    portal.write_run(
        {
            "run_id": "run-one",
            "org_id": "org-one",
            "site_id": "site-one",
            "state": "awaiting_confirmation",
            "updated_at": "2026-09-09T10:00:00+00:00",
            "targets": [],
        }
    )
    actions = ActionRecordStore("unit-reconcile", portal)
    cloud_reads: list[str] = []
    guard = SiteMutationGuard(
        lambda _org, _site: True,
        lambda _org, _site: {"lock_token": "token-one"},
        {"site-one": "token-one"},
    )
    service = StoppingRunReconciler(
        actions,
        portal.read_run,
        guard,
        lambda _run, _now: cloud_reads.append("read") or [],
        clock=lambda: datetime.fromisoformat(ACTION_TIME),
    )
    actor = DurableActorScope.build("email", "operator@example.invalid")

    result = service.reconcile(
        actor=actor,
        idempotency_key=REQUEST_KEY,
        confirmation="RECONCILE run-one",
        run_id="run-one",
        organization_id="org-one",
        site_id="site-one",
    )

    assert result.status == "complete"
    assert result.item("run-one").reason == "precloud_run_cancelled"
    assert portal.read_run("run-one")["state"] == "cancelled"
    assert cloud_reads == []


def test_incomplete_stopping_evidence_is_unknown_and_changes_no_run() -> None:
    """Incomplete evidence stores unknown and leaves a stopping run unchanged."""
    portal = PortalRecordStore("unit-reconcile")
    portal.write_run(
        {
            "run_id": "run-one",
            "org_id": "org-one",
            "site_id": "site-one",
            "state": "stopping",
            "updated_at": "2026-09-09T10:00:00+00:00",
            "targets": [{"device_id": "target-one"}],
        }
    )
    actions = ActionRecordStore("unit-reconcile", portal)
    guard = SiteMutationGuard(
        lambda _org, _site: True,
        lambda _org, _site: {"lock_token": "token-one"},
        {"site-one": "token-one"},
    )
    evidence = [
        {
            "target_id": "target-one",
            "stored_stop_result": "cancel_accepted",
            "task_state": "unknown",
            "write_state": "unknown",
            "sources": ["stored"],
            "observed_at": ACTION_TIME,
            "is_complete": False,
            "has_conflict": False,
        }
    ]
    service = StoppingRunReconciler(
        actions,
        portal.read_run,
        guard,
        lambda _run, _now: evidence,
        clock=lambda: datetime.fromisoformat(ACTION_TIME),
    )
    actor = DurableActorScope.build("email", "operator@example.invalid")

    result = service.reconcile(
        actor=actor,
        idempotency_key=REQUEST_KEY,
        confirmation="RECONCILE run-one",
        run_id="run-one",
        organization_id="org-one",
        site_id="site-one",
    )

    assert result.item("run-one").classification == "unknown"
    assert result.item("run-one").reason == "cloud_evidence_incomplete"
    assert result.evidence_summary_digest == result.item("run-one").evidence_summary["decision_basis_digest"]
    assert portal.read_run("run-one")["state"] == "stopping"
