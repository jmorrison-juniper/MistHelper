"""Hold process-owned action records for one E2E server."""

from __future__ import annotations  # Keep annotations independent from import order.

import logging  # Record each process-owned action operation.
from copy import deepcopy  # Stop a caller from changing a stored action.
from threading import RLock
from typing import Any  # Action records contain different JSON-compatible fields.

from src.upgrade_portal.persistence.actions import (
    ActionInitialization,
    ActionLease,
    ActionRequestConflict,
    ActionStateConflict,
    AtomicWriteResult,
    RetryRunMutation,
    RunActionOutcome,
    RunMutation,
    UpgradeRunAction,
    evidence_summary_digest,
)

logger = logging.getLogger(__name__)  # Keep action activity tied to this module.


class ActionRecordStore:  # Own action records for one isolated server process.
    """Own action records for one test run."""

    def __init__(self, test_run_id: str, run_store: Any | None = None) -> None:
        """Create an empty action store."""
        self.test_run_id = test_run_id  # Bind every action to one E2E server.
        self._actions: dict[str, dict[str, Any]] = {}  # Hold actions by public identifier.
        self._run_store = run_store
        self._guard = run_store.transaction_lock if run_store is not None else RLock()

    def write(self, action: dict[str, Any]) -> bool:  # Store one owned action record.
        """Store one action and reject a different owner."""
        logger.info("Store one E2E action record")  # Record the action write.
        copied = deepcopy(action)  # Isolate the stored record from the caller.
        owner = copied.get("test_run_id")  # Read the supplied owner before adding one.
        if owner not in (None, self.test_run_id):  # Another E2E server owns this action.
            raise ValueError("The record belongs to a different E2E test run.")  # Reject cross-process data.
        copied["test_run_id"] = self.test_run_id  # Make ownership explicit on the stored action.
        self._actions[str(copied["action_id"])] = copied  # Store the action under its public identifier.
        logger.debug("The E2E action store now holds %s record(s)", len(self._actions))  # Report a safe count.
        return True  # Match the action repository write contract.

    def read(self, actor_scope: str, action_id: str | None = None) -> UpgradeRunAction | dict[str, Any] | None:
        """Return one actor-scoped action record."""
        logger.info("Read one E2E action record")  # Record the action read.
        public_id = actor_scope if action_id is None else action_id
        record = self._actions.get(public_id)  # An absent identifier returns no record.
        if action_id is None:
            return deepcopy(record) if record is not None else None
        owned = record if record is not None and record.get("actor_scope") == actor_scope else None
        result = UpgradeRunAction.from_document(owned) if owned is not None else None
        logger.debug("The E2E action read found a record: %s", result is not None)  # Report no action data.
        return result  # Give the caller an isolated copy.

    def find_request(self, actor_scope: str, idempotency_key_digest: str) -> UpgradeRunAction | None:
        """Return one action by its durable actor request key."""
        with self._guard:
            for document in self._actions.values():
                if (
                    document.get("actor_scope") == actor_scope
                    and document.get("idempotency_key_digest") == idempotency_key_digest
                ):
                    return UpgradeRunAction.from_document(document)
        return None

    def initialize(
        self,
        request: ActionInitialization,
        lease: ActionLease,
        created_at: str,
    ) -> UpgradeRunAction:
        """Create all ordered placeholders before item work."""
        candidate = UpgradeRunAction.initialize(request, lease, created_at)
        with self._guard:
            stored = self.find_request(request.identity.actor_scope, request.identity.idempotency_key_digest)
            if stored is not None:
                if stored.identity.request_digest != request.identity.request_digest:
                    raise ActionRequestConflict("The idempotency key already binds a different request.")
                return stored
            self._store_action(candidate)
        return self._required(candidate.identity.actor_scope, candidate.key.action_id)

    def claim_item(
        self,
        actor_scope: str,
        action_id: str,
        run_id: str,
        lease: ActionLease,
    ) -> UpgradeRunAction:
        """Claim one pending item under the current action lease."""
        with self._guard:
            action = self._required(actor_scope, action_id)
            if action.lifecycle.lease != lease:
                raise ActionStateConflict("The upgrade action has a different processing lease.")
            changed = action.with_item(action.item(run_id).claimed(lease.owner, lease.expires_at))
            self._store_action(changed)
            return changed

    def write_outcome(
        self,
        actor_scope: str,
        action_id: str,
        outcome: RunActionOutcome,
    ) -> UpgradeRunAction:
        """Store one no-mutation final outcome."""
        with self._guard:
            action = self._required(actor_scope, action_id)
            current = action.item(outcome.identity.source_run_id)
            if current.claim.claim_owner != outcome.claim.claim_owner:
                raise ActionStateConflict("The upgrade action item has a different claim owner.")
            changed = action.with_item(outcome)
            if outcome.evidence_summary is not None:
                changed = changed.with_evidence_digest(evidence_summary_digest(outcome.evidence_summary))
            self._store_action(changed)
            return changed

    def commit_success(
        self,
        actor_scope: str,
        action_id: str,
        outcome: RunActionOutcome,
        mutation: RunMutation | RetryRunMutation,
    ) -> AtomicWriteResult:
        """Store one run mutation and success outcome as one process step."""
        if self._run_store is None:
            raise RuntimeError("The E2E action store has no run store.")
        with self._guard:
            action = self._required(actor_scope, action_id)
            current = action.item(outcome.identity.source_run_id)
            if current.claim.claim_owner != outcome.claim.claim_owner:
                raise ActionStateConflict("The upgrade action item has a different claim owner.")
            if isinstance(mutation, RetryRunMutation):
                source = self._run_store._runs.get(mutation.source_run_id)
                if source is None:
                    raise ActionStateConflict("The source run does not exist.")
                if (
                    source.get("_rev") != mutation.expected_source_revision
                    or source.get("state") != mutation.expected_source_state
                ):
                    raise ActionStateConflict("The source run changed before the transaction.")
                for candidate in self._run_store._runs.values():
                    if candidate.get("site_id") != mutation.site_id:
                        continue
                    if candidate.get("run_id") == mutation.source_run_id:
                        continue
                    if candidate.get("state") not in {"complete", "failed", "stopped", "cancelled"}:
                        raise ActionStateConflict("upgrade_already_running")
                if mutation.run_id in self._run_store._runs:
                    raise ActionStateConflict("The retry run already exists.")
                changed_run = deepcopy(dict(mutation.document))
                changed_run["_rev"] = "1"
            else:
                run = self._run_store._runs.get(mutation.run_id)
                if run is None:
                    raise ActionStateConflict("The source run does not exist.")
                if run.get("_rev") != mutation.expected_revision or run.get("state") != mutation.expected_state:
                    raise ActionStateConflict("The source run changed before the transaction.")
                changed_run = deepcopy(run)
                changed_run.update(dict(mutation.document))
                changed_run["_rev"] = str(int(str(run["_rev"])) + 1)
            changed = action.with_item(outcome)
            if outcome.evidence_summary is not None:
                changed = changed.with_evidence_digest(evidence_summary_digest(outcome.evidence_summary))
            self._run_store._runs[mutation.run_id] = changed_run
            self._store_action(changed)
            return AtomicWriteResult(changed, deepcopy(changed_run))

    def store_site_block(
        self,
        actor_scope: str,
        action_id: str,
        site_id: str,
        reason: str,
    ) -> UpgradeRunAction:
        """Store one durable site guard stop."""
        with self._guard:
            action = self._required(actor_scope, action_id).with_site_block(site_id, reason)
            self._store_action(action)
            return action

    def finalize(self, actor_scope: str, action_id: str, completed_at: str) -> UpgradeRunAction:
        """Change one all-final action to complete."""
        with self._guard:
            action = self._required(actor_scope, action_id).completed(completed_at)
            self._store_action(action)
            return action

    def _required(self, actor_scope: str, action_id: str) -> UpgradeRunAction:
        """Return one owned action or raise a state conflict."""
        record = self._actions.get(action_id)
        if record is None or record.get("actor_scope") != actor_scope:
            raise ActionStateConflict("The upgrade action does not exist.")
        return UpgradeRunAction.from_document(record)

    def _store_action(self, action: UpgradeRunAction) -> None:
        """Store one immutable action with a process revision."""
        prior = self._actions.get(action.key.action_id)
        document = action.document()
        document["_rev"] = str(int(str(prior.get("_rev", "0"))) + 1) if prior is not None else "1"
        document["test_run_id"] = self.test_run_id
        self._actions[action.key.action_id] = document

    def list(self) -> list[dict[str, Any]]:  # List owned action records in stable order.
        """Return all action records in insertion order."""
        logger.info("List E2E action records")  # Record the process-owned scan.
        rows = [deepcopy(record) for record in self._actions.values()]  # Protect every stored action.
        logger.debug("The E2E action list holds %s record(s)", len(rows))  # Report a safe count.
        return rows  # Preserve deterministic insertion order.
