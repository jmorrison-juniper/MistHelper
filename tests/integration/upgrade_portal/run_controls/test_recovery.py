"""Test replay and crash recovery with controlled transactional failures."""

from __future__ import annotations  # Keep each annotation independent from import order.

from typing import Final  # Mark deterministic lease and request values.

import pytest  # Exercise crash faults and compare-and-swap conflicts.

from src.upgrade_portal.persistence.actions import (  # Test the public durable replay surface.
    RUN_COLLECTION,
    ActionIdentity,
    ActionInitialization,
    ActionIntent,
    ActionLease,
    ActionReplayService,
    ActionRepository,
    ActionRequestConflict,
    ActionSource,
    ActionStateConflict,
    ActionStoreUnavailable,
    DurableActorScope,
    OutcomeCompletion,
    OutcomeState,
    RecoveryDecision,
    ReplayRequest,
    RunActionOutcome,
    RunMutation,
    canonical_digest,
)
from tests.integration.upgrade_portal.run_controls import FakeDatabase  # Use no live ArangoDB store.

START: Final[str] = "2026-09-11T14:00:00+00:00"  # Fix action creation for stable recovery tests.
EXPIRED: Final[str] = "2026-09-11T14:01:00+00:00"  # End the abandoned worker lease before recovery.
NOW: Final[str] = "2026-09-11T14:02:00+00:00"  # Run each recovery after the abandoned lease.
ACTIVE: Final[str] = "2026-09-11T14:05:00+00:00"  # Keep one current worker lease active.
RECOVERY_END: Final[str] = "2026-09-11T14:10:00+00:00"  # Protect the complete recovery pass.
REQUEST_KEY: Final[str] = "visible-recovery-key-0001"  # Meet the HTTP request key length.


class RecordingProcessor:
    """Return controlled final outcomes and record each resumed run."""

    def __init__(self, site_block: tuple[str, str] | None = None) -> None:
        """Start with no processed run and an optional first site block."""
        self.calls: list[str] = []  # Record only source run identifiers.
        self.site_block = site_block  # Model a guard loss for one processor result.

    def __call__(self, action: object, item: RunActionOutcome) -> RecoveryDecision:
        """Return one durable refusal for the supplied claimed item."""
        del action  # The controlled processor needs the claimed item only.
        self.calls.append(item.identity.source_run_id)  # Prove recovery processes pending items only.
        state = OutcomeState("created", "", NOW, NOW)  # Make no final run state claim.
        completion = OutcomeCompletion("refused", "run_changed", "The run changed before this action.", "", state)
        outcome = item.finalized(completion)  # Close the current durable claim.
        block = self.site_block if len(self.calls) == 1 else None  # Store a guard loss once.
        return RecoveryDecision(outcome, None, block)  # Use the outcome-only compare-and-swap path.


def _initialization(
    run_ids: tuple[str, ...] = ("run-one",),
    site_ids: tuple[str, ...] = ("site-one",),
    request_tag: str = "first",
) -> ActionInitialization:
    """Return one valid controlled bulk request."""
    actor = DurableActorScope.build("email", "operator@example.invalid")  # Build one stable actor scope.
    fields = {"action": "cancel", "run_ids": list(run_ids), "tag": request_tag}  # Bind ordered content.
    identity = ActionIdentity.from_request(actor, REQUEST_KEY, fields, "CANCEL RUNS")  # Store safe digests.
    preview_digest = canonical_digest({"preview": "preview-one"})  # Store no raw preview value.
    source = ActionSource.bulk("preview-one", preview_digest, "org-one", "all-sites")  # Require preview fields.
    intent = ActionIntent("cancel", run_ids, site_ids, len(set(site_ids)))  # Keep exact ordered identifiers.
    return ActionInitialization(identity, source, intent)  # Enforce the source and action relation.


def _repository() -> tuple[FakeDatabase, ActionRepository]:
    """Return one bootstrapped controlled action repository."""
    database = FakeDatabase()  # Start one process-owned controlled store.
    database.create_collection(RUN_COLLECTION)  # Model the existing authoritative run collection.
    repository = ActionRepository(database)  # Inject no router or fallback store.
    repository.bootstrap()  # Create and verify the action journal and indexes.
    return database, repository  # Give each test isolated durable state.


def _final_refusal(item: RunActionOutcome) -> RunActionOutcome:
    """Return one durable final refusal for a claimed item."""
    state = OutcomeState("created", "", START, START)  # Make no final run state claim.
    completion = OutcomeCompletion("refused", "run_changed", "The run changed before this action.", "", state)
    return item.finalized(completion)  # Preserve item identity and claim ownership.


def _attempt_atomic_cancel(failure_mode: str) -> tuple[FakeDatabase, ActionRepository, ActionInitialization]:
    """Attempt one controlled atomic cancel with the selected commit fault."""
    database, repository = _repository()  # Use one isolated action journal.
    seeded = database.seed_run("run-one", "created")  # Create one authoritative pre-cloud run.
    initialization = _initialization()  # Build one requested cancel.
    old_lease = ActionLease("worker-old", EXPIRED)  # Use the abandoned worker lease.
    action = repository.initialize(initialization, old_lease, START)  # Create the pending placeholder.
    claimed = repository.claim_item(action.identity.actor_scope, action.key.action_id, "run-one", old_lease)
    state = OutcomeState("created", "cancelled", START, START)  # Describe the verified run result.
    completion = OutcomeCompletion(
        "succeeded", "precloud_run_cancelled", "The portal cancelled the run.", "run-one", state
    )
    outcome = claimed.item("run-one").finalized(completion)  # Build success for the durable current claim.
    mutation = RunMutation("update", "run-one", seeded["_rev"], "created", {"state": "cancelled"})  # Bind revision.
    database.failure_mode = failure_mode  # Select the exact controlled transaction fault.
    with pytest.raises(ActionStoreUnavailable, match="unavailable"):  # Report no unverified response success.
        repository.commit_success(action.identity.actor_scope, action.key.action_id, outcome, mutation)
    return database, repository, initialization  # Give recovery the durable state after the fault.


def test_same_key_active_lease_returns_processing_without_new_work() -> None:
    """A current processing lease returns the stored action and calls no processor."""
    _, repository = _repository()  # Use one isolated action journal.
    initialization = _initialization()  # Build one durable request binding.
    stored = repository.initialize(initialization, ActionLease("worker-one", ACTIVE), START)  # Start processing.
    processor = RecordingProcessor()  # Record any unsafe repeated item work.
    service = ActionReplayService(repository, lambda: NOW)  # Use a time inside the current lease.
    replayed = service.resolve(ReplayRequest(initialization, ActionLease("worker-two", RECOVERY_END)), processor)
    assert replayed.key.action_id == stored.key.action_id  # Return the first durable action.
    assert replayed.lifecycle.status == "processing"  # Keep the current worker status visible.
    assert processor.calls == []  # Perform no new item check or mutation.


def test_replay_rejects_the_same_key_with_different_request_content() -> None:
    """Replay rejects changed content before lease takeover or item work."""
    _, repository = _repository()  # Use one isolated action journal.
    first = _initialization(request_tag="first")  # Build the stored request digest.
    changed = _initialization(request_tag="second")  # Keep the request key and change its content.
    repository.initialize(first, ActionLease("worker-old", EXPIRED), START)  # Store the first request.
    processor = RecordingProcessor()  # Record any unsafe work after the mismatch.
    service = ActionReplayService(repository, lambda: NOW)  # Use a time after the old lease.
    with pytest.raises(ActionRequestConflict, match="different request"):  # Return the stable HTTP conflict.
        service.resolve(ReplayRequest(changed, ActionLease("worker-new", RECOVERY_END)), processor)
    assert processor.calls == []  # Perform no item work for a mismatched request.


def test_expired_lease_takeover_uses_compare_and_swap_for_one_owner() -> None:
    """Only the first recovery owner can replace one expired action lease."""
    _, repository = _repository()  # Use one isolated action journal.
    action = repository.initialize(_initialization(), ActionLease("worker-old", EXPIRED), START)  # Expire it.
    first = repository.take_over(  # Take the expired lease with one compare-and-swap write.
        action.identity.actor_scope,  # Keep takeover actor-scoped.
        action.key.action_id,  # Name the public action.
        ActionLease("worker-new", RECOVERY_END),  # Install the first recovery owner.
        NOW,  # Compare after the old lease expiry.
    )
    assert first.lifecycle.lease.owner == "worker-new"  # Persist the first recovery owner.
    with pytest.raises(ActionStateConflict, match="still active"):  # Refuse the second recovery owner.
        repository.take_over(  # Attempt takeover while the new lease is current.
            action.identity.actor_scope,  # Keep the second attempt actor-scoped.
            action.key.action_id,  # Name the same public action.
            ActionLease("worker-other", RECOVERY_END),  # Offer another opaque worker.
            NOW,  # Use the same recovery time.
        )


def test_crash_before_claim_resumes_the_pending_item_once() -> None:
    """Recovery processes a pending item after the first worker stops before claim."""
    _, repository = _repository()  # Use one isolated action journal.
    initialization = _initialization()  # Build one requested run.
    repository.initialize(initialization, ActionLease("worker-old", EXPIRED), START)  # Leave it pending.
    processor = RecordingProcessor()  # Record each resumed item.
    service = ActionReplayService(repository, lambda: NOW)  # Recover after lease expiry.
    complete = service.resolve(ReplayRequest(initialization, ActionLease("worker-new", RECOVERY_END)), processor)
    assert processor.calls == ["run-one"]  # Resume the pending item exactly once.
    assert complete.lifecycle.status == "complete"  # Finalize after the durable outcome.
    assert complete.item("run-one").completion.classification == "refused"  # Preserve processor result.


def test_crash_after_claim_finalizes_interrupted_without_repeating_work() -> None:
    """Recovery closes an abandoned claimed item and performs no processor call."""
    _, repository = _repository()  # Use one isolated action journal.
    initialization = _initialization()  # Build one requested run.
    action = repository.initialize(initialization, ActionLease("worker-old", EXPIRED), START)  # Expire it.
    repository.claim_item(  # Leave one durable item claimed at the crash point.
        action.identity.actor_scope,  # Keep the claim actor-scoped.
        action.key.action_id,  # Name the public action.
        "run-one",  # Claim the only requested run.
        ActionLease("worker-old", EXPIRED),  # Use the abandoned item lease.
    )
    processor = RecordingProcessor()  # Record any unsafe repeated work.
    service = ActionReplayService(repository, lambda: NOW)  # Recover after the claim lease expires.
    complete = service.resolve(ReplayRequest(initialization, ActionLease("worker-new", RECOVERY_END)), processor)
    assert processor.calls == []  # Never repeat a possibly committed mutation.
    assert complete.item("run-one").completion.classification == "unknown"  # Claim no result.
    assert complete.item("run-one").completion.reason == "processing_interrupted"  # Use the exact reason.
    assert complete.lifecycle.status == "complete"  # Close the action after all items become final.


def test_crash_before_transaction_commit_rolls_back_and_recovers_as_interrupted() -> None:
    """A pre-commit fault changes no run and recovery never repeats its claimed item."""
    database, repository, initialization = _attempt_atomic_cancel("before_commit")  # Keep both writes pending.
    processor = RecordingProcessor()  # Record any unsafe repeated work.
    service = ActionReplayService(repository, lambda: NOW)  # Recover after the old lease expiry.
    complete = service.resolve(ReplayRequest(initialization, ActionLease("worker-new", RECOVERY_END)), processor)
    stored_run = database.collection(RUN_COLLECTION).get("run-one")  # Read the authoritative run after recovery.
    assert stored_run is not None and stored_run["state"] == "created"  # Keep the rolled-back run unchanged.
    assert processor.calls == []  # Do not repeat the claimed mutation after an uncertain failure.
    assert complete.item("run-one").completion.reason == "processing_interrupted"  # Close with unknown.


def test_crash_after_transaction_commit_keeps_success_and_repeats_no_mutation() -> None:
    """A lost commit response leaves durable success that recovery only finalizes."""
    database, repository, initialization = _attempt_atomic_cancel("after_commit")  # Lose the commit response.
    processor = RecordingProcessor()  # Record any repeated work during replay.
    service = ActionReplayService(repository, lambda: NOW)  # Recover after the old action lease expires.
    complete = service.resolve(ReplayRequest(initialization, ActionLease("worker-new", RECOVERY_END)), processor)
    stored_run = database.collection(RUN_COLLECTION).get("run-one")  # Read the durable run after response loss.
    assert stored_run is not None and stored_run["state"] == "cancelled"  # Keep the committed mutation.
    assert processor.calls == []  # Never repeat the final item mutation.
    assert complete.item("run-one").completion.classification == "succeeded"  # Keep the first durable result.


def test_recovery_resumes_only_pending_items_and_finalizes_every_item() -> None:
    """Recovery preserves final items, interrupts claimed items, and processes pending items."""
    _, repository = _repository()  # Use one isolated action journal.
    initialization = _initialization(  # Build three ordered runs on separate sites.
        ("run-final", "run-claimed", "run-pending"),  # Name each lifecycle state.
        ("site-final", "site-claimed", "site-pending"),  # Keep one site for each run.
    )
    action = repository.initialize(initialization, ActionLease("worker-old", EXPIRED), START)  # Expire it.
    first_claim = repository.claim_item(  # Claim the item that will already be final.
        action.identity.actor_scope, action.key.action_id, "run-final", ActionLease("worker-old", EXPIRED)
    )
    first_final = _final_refusal(first_claim.item("run-final"))  # Build the durable prior result.
    repository.write_outcome(action.identity.actor_scope, action.key.action_id, first_final)  # Store final.
    repository.claim_item(  # Leave the second item claimed at the crash point.
        action.identity.actor_scope, action.key.action_id, "run-claimed", ActionLease("worker-old", EXPIRED)
    )
    processor = RecordingProcessor()  # Record only safely resumed pending work.
    service = ActionReplayService(repository, lambda: NOW)  # Recover after lease expiry.
    complete = service.resolve(ReplayRequest(initialization, ActionLease("worker-new", RECOVERY_END)), processor)
    assert processor.calls == ["run-pending"]  # Process only the item that had no prior claim.
    assert complete.item("run-final").completion.reason == "run_changed"  # Preserve the first final result.
    assert complete.item("run-claimed").completion.reason == "processing_interrupted"  # Close abandoned work.
    assert all(item.claim.processing_state == "final" for item in complete.ledger.items)  # Finalize all items.
    assert complete.lifecycle.status == "complete"  # Complete only after all three final outcomes.


def test_recovery_preserves_site_blocks_and_finishes_other_sites() -> None:
    """A durable site block closes later site items while another site continues."""
    _, repository = _repository()  # Use one isolated action journal.
    initialization = _initialization(  # Build two blocked-site runs and one valid-site run.
        ("run-a-one", "run-a-two", "run-b-one"),  # Preserve preview order.
        ("site-a", "site-a", "site-b"),  # Put the first two runs on one site.
    )
    action = repository.initialize(initialization, ActionLease("worker-old", EXPIRED), START)  # Expire it.
    repository.store_site_block(action.identity.actor_scope, action.key.action_id, "site-a", "site_lock_token_changed")
    processor = RecordingProcessor()  # Record work that reaches the valid site only.
    service = ActionReplayService(repository, lambda: NOW)  # Recover after lease expiry.
    complete = service.resolve(ReplayRequest(initialization, ActionLease("worker-new", RECOVERY_END)), processor)
    assert processor.calls == ["run-b-one"]  # Skip every pending item on the blocked site.
    assert complete.ledger.block_map() == {"site-a": "site_lock_token_changed"}  # Preserve the stop decision.
    assert complete.item("run-a-one").completion.reason == "not_processed_after_site_guard_loss"  # Close first.
    assert complete.item("run-a-two").completion.reason == "not_processed_after_site_guard_loss"  # Close second.
    assert complete.item("run-b-one").completion.reason == "run_changed"  # Continue a different valid site.
