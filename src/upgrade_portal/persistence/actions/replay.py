"""Recover durable upgrade actions without repeating possible mutations.

Why:
    A worker can stop before or after an unknown commit point. Recovery closes
    claimed items as unknown and resumes only items that remain pending.
"""

from __future__ import annotations  # Keep each annotation independent from import order.

import logging  # Record each recovery action without actor or request content.
from collections.abc import Callable  # Type the injected pending-item processor.
from dataclasses import dataclass  # Build immutable replay request and decision values.

from .models import (  # Import immutable action and outcome records.
    ActionInitialization,
    ActionLease,
    OutcomeCompletion,
    OutcomeState,
    RunActionOutcome,
    UpgradeRunAction,
)
from .repository import (  # Reuse actor-scoped durable operations and stable conflicts.
    ActionRepository,
    ActionRequestConflict,
    ActionStateConflict,
)
from .transactions import RunMutation  # Join a resumed success to its run mutation.

logger = logging.getLogger(__name__)  # Keep recovery logs in one named module.


@dataclass(frozen=True, slots=True)
class ReplayRequest:
    """Hold one action initialization and its requested processing lease."""

    initialization: ActionInitialization  # Bind the durable actor, request, source, and ordered items.
    lease: ActionLease  # Name the opaque worker that can process pending items.


@dataclass(frozen=True, slots=True)
class RecoveryDecision:
    """Hold one final outcome, optional run mutation, and optional site block."""

    outcome: RunActionOutcome  # Give the claimed item one final durable result.
    mutation: RunMutation | None = None  # Join only a succeeded result to a run write.
    site_block: tuple[str, str] | None = None  # Stop later writes for one site after guard loss.


class ActionReplayService:
    """Resolve idempotent replay and resume only safe pending work."""

    def __init__(self, repository: ActionRepository, clock: Callable[[], str]) -> None:
        """Bind durable operations and one controlled UTC clock."""
        self.repository = repository  # Use only the ArangoDB action repository.
        self.clock = clock  # Make every lease and crash test deterministic.

    def resolve(
        self,
        request: ReplayRequest,
        processor: Callable[[UpgradeRunAction, RunActionOutcome], RecoveryDecision],
    ) -> UpgradeRunAction:
        """Return a replay or recover an expired action to completion."""
        logger.info("Resolve one durable upgrade action request")  # Record replay before its actor-scoped read.
        now, stored = self._read_request(request)  # Validate the new lease and read the durable request key.
        if stored is None:  # The first request must create all ordered placeholders.
            action = self.repository.initialize(request.initialization, request.lease, now)  # Create once.
            can_resume = action.lifecycle.lease == request.lease  # Detect a concurrent initialization winner.
            if not can_resume:  # A concurrent action can need active return or expired takeover handling.
                action, can_resume = self._resolve_stored(action, request, now)  # Apply normal replay rules.
        else:  # A replay must compare content before any item work.
            action, can_resume = self._resolve_stored(stored, request, now)  # Return active or take an expired lease.
        if not can_resume:  # A complete action or current lease performs no new item work.
            logger.debug("Returned one durable upgrade action without new item work")  # Confirm no repeat.
            return action  # A complete or active foreign lease performs no mutation.
        completed = self._resume_pending(action, request.lease, processor, now)  # Process safe items only.
        logger.debug("Resolved one durable upgrade action request")  # Confirm all recoverable work completed.
        return completed  # Return the verified complete action.

    def _read_request(self, request: ReplayRequest) -> tuple[str, UpgradeRunAction | None]:
        """Validate the new lease and read the actor-scoped request key."""
        now = self.clock()  # Use one time for all decisions in this recovery pass.
        if not request.lease.is_current(now):  # A recovery worker needs a lease that extends beyond this pass.
            raise ValueError("The requested recovery lease is not current.")  # Refuse an immediately stale owner.
        stored = self.repository.find_request(  # Read by the composite actor and idempotency key.
            request.initialization.identity.actor_scope,  # Keep replay bound to the durable actor.
            request.initialization.identity.idempotency_key_digest,  # Use only the safe request key digest.
        )
        return now, stored  # Give replay one controlled time and durable request result.

    def _resolve_stored(
        self,
        stored: UpgradeRunAction,
        request: ReplayRequest,
        now: str,
    ) -> tuple[UpgradeRunAction, bool]:
        """Validate one replay and take ownership only after lease expiry."""
        expected = request.initialization.identity.request_digest  # Read the new request binding once.
        if stored.identity.request_digest != expected:  # One raw key cannot bind different content.
            raise ActionRequestConflict("The idempotency key already binds a different request.")  # HTTP 409.
        if stored.lifecycle.status == "complete":  # A final action never performs work again.
            return stored, False  # Return the first durable result without item work.
        if stored.lifecycle.lease.is_current(now):  # The current worker still owns possible writes.
            return stored, False  # Return processing without a new cloud read or run write.
        return self._take_over_or_read(stored, request.lease, now)  # Resolve one compare-and-swap winner.

    def _take_over_or_read(
        self,
        stored: UpgradeRunAction,
        lease: ActionLease,
        now: str,
    ) -> tuple[UpgradeRunAction, bool]:
        """Take an expired lease or return the concurrent winner."""
        try:  # One of two recovery workers can lose the compare-and-swap.
            recovered = self.repository.take_over(  # One worker replaces the expired lease.
                stored.identity.actor_scope,  # Keep takeover bound to the durable actor.
                stored.key.action_id,  # Name the public action.
                lease,  # Install the new opaque worker lease.
                now,  # Close every abandoned claim at this recovery time.
            )
        except ActionStateConflict:  # Another worker can win after the first replay read.
            latest = self.repository.read(stored.identity.actor_scope, stored.key.action_id)  # Read the winner.
            if latest is None:  # A missing record cannot safely resume or report processing.
                raise  # Preserve the actor-scoped state conflict.
            return latest, False  # Let only the compare-and-swap winner resume pending items.
        return recovered, True  # Resume only the pending items under the new durable lease.

    def _resume_pending(
        self,
        action: UpgradeRunAction,
        lease: ActionLease,
        processor: Callable[[UpgradeRunAction, RunActionOutcome], RecoveryDecision],
        now: str,
    ) -> UpgradeRunAction:
        """Process each pending item once and then complete the action."""
        current = action  # Carry the newest verified action through ordered items.
        for item in action.ledger.items:  # Preserve the original request order.
            if item.claim.processing_state != "pending":  # Never repeat a claimed or final item.
                continue  # Leave the durable prior outcome unchanged.
            if item.identity.site_id in current.ledger.block_map():  # Preserve a prior site guard loss.
                current = self._finalize_blocked(current, item, lease, now)  # Close with no mutation.
                continue  # Process a different site or the next ordered item.
            current = self._process_pending(current, item, lease, processor)  # Claim before any work.
        if current.lifecycle.status == "complete":  # A concurrent finalizer already completed the action.
            return current  # Avoid a second processing-to-complete write.
        return self.repository.finalize(current.identity.actor_scope, current.key.action_id, now)  # Complete once.

    def _process_pending(
        self,
        action: UpgradeRunAction,
        item: RunActionOutcome,
        lease: ActionLease,
        processor: Callable[[UpgradeRunAction, RunActionOutcome], RecoveryDecision],
    ) -> UpgradeRunAction:
        """Claim one pending item and store one final processor decision."""
        logger.info("Claim and process one pending upgrade action item")  # Record work before the durable claim.
        claimed_action = self.repository.claim_item(  # Mark possible work before any processor call.
            action.identity.actor_scope,  # Keep the claim actor-scoped.
            action.key.action_id,  # Name the public action.
            item.identity.source_run_id,  # Claim exactly one ordered item.
            lease,  # Reuse the current opaque action owner and expiry.
        )
        claimed_item = claimed_action.item(item.identity.source_run_id)  # Read the durable claimed copy.
        decision = processor(claimed_action, claimed_item)  # Perform current checks and build one final result.
        current = self._store_decision(claimed_action, decision)  # Store a site block before later site work.
        logger.debug("Processed one pending upgrade action item")  # Confirm one durable final outcome.
        return current  # Carry the newest verified action to the next item.

    def _store_decision(self, action: UpgradeRunAction, decision: RecoveryDecision) -> UpgradeRunAction:
        """Store an optional site block and then one final item result."""
        current = self._store_site_block(action, decision)  # Persist a guard loss before later site work.
        if decision.mutation is None:  # Refused, failed, and unknown results change no run.
            return self.repository.write_outcome(  # Use one outcome-only compare-and-swap write.
                current.identity.actor_scope,  # Keep the final write actor-scoped.
                current.key.action_id,  # Name the public action.
                decision.outcome,  # Replace only the claimed matching item.
            )
        result = self.repository.commit_success(  # Join success to the authoritative run mutation.
            current.identity.actor_scope,  # Keep the atomic write actor-scoped.
            current.key.action_id,  # Name the public action.
            decision.outcome,  # Store the succeeded final outcome.
            decision.mutation,  # Store the matching run change in the same transaction.
        )
        return result.action  # Carry the verified stored action to the next item.

    def _store_site_block(self, action: UpgradeRunAction, decision: RecoveryDecision) -> UpgradeRunAction:
        """Store a matching optional site block before the final item result."""
        if decision.site_block is None:  # A normal result adds no durable site stop decision.
            return action  # Preserve the verified claimed action.
        site_id, reason = decision.site_block  # Read the durable site stop values.
        if site_id != decision.outcome.identity.site_id:  # A result can block only its own guarded site.
            raise ValueError("The recovery site block does not match its outcome.")  # Refuse cross-site stop.
        return self.repository.store_site_block(  # Persist the stop before another item can run.
            action.identity.actor_scope,  # Keep the safety write actor-scoped.
            action.key.action_id,  # Name the public action.
            site_id,  # Name the site that lost its guard.
            reason,  # Preserve the first stable guard refusal reason.
        )

    def _finalize_blocked(
        self,
        action: UpgradeRunAction,
        item: RunActionOutcome,
        lease: ActionLease,
        now: str,
    ) -> UpgradeRunAction:
        """Finalize one pending item after a durable site guard loss."""
        logger.info("Finalize one item after a durable site block")  # Record the no-write result before its claim.
        claimed = self.repository.claim_item(  # Claim the placeholder before its outcome-only write.
            action.identity.actor_scope,  # Keep the claim actor-scoped.
            action.key.action_id,  # Name the public action.
            item.identity.source_run_id,  # Claim exactly one blocked item.
            lease,  # Use the current opaque recovery lease.
        )
        durable_item = claimed.item(item.identity.source_run_id)  # Read the claimed copy with its owner.
        outcome = self._blocked_outcome(durable_item, now)  # Build the stable no-write result.
        final = self.repository.write_outcome(claimed.identity.actor_scope, claimed.key.action_id, outcome)
        logger.debug("Finalized one item after a durable site block")  # Confirm one durable unknown outcome.
        return final  # Carry the newest verified action to later items.

    @staticmethod
    def _blocked_outcome(item: RunActionOutcome, now: str) -> RunActionOutcome:
        """Return the final unknown result for one blocked pending item."""
        state = OutcomeState("", "", now, now)  # Make no final run state claim.
        completion = OutcomeCompletion(  # Build the required durable unknown result.
            "unknown",  # A guard block leaves the mutation result unknown because no work ran.
            "not_processed_after_site_guard_loss",  # State the stable recovery reason.
            "The portal did not process this run after the site guard changed.",  # Give safe operator text.
            "",  # No run changed or was created.
            state,  # Preserve the safe check and completion time.
        )
        return item.finalized(completion)  # Replace the claimed placeholder without evidence.
