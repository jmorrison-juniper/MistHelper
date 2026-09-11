"""Store upgrade run actions only in ArangoDB.

Why:
    A fallback store cannot join a run mutation and its action outcome. This
    repository fails closed and verifies each durable write before success.
"""

from __future__ import annotations  # Keep each annotation independent from import order.

import logging  # Record each store action without raw actor or request values.
from collections.abc import Mapping  # Accept stored ArangoDB documents as read-only values.
from typing import Any  # Accept python-arango and controlled fake handles.

from src.refactors.endpoint_primary_key_strategies import (  # Use the registered composite domain key directly.
    ENDPOINT_PRIMARY_KEY_STRATEGIES,
)

from .models import (  # Import only immutable action records and safe digest helpers.
    ActionInitialization,
    ActionLease,
    RunActionOutcome,
    UpgradeRunAction,
    evidence_summary_digest,
)
from .transactions import (  # Import the explicit no-fallback transaction boundary.
    ArangoTransactionAdapter,
    AtomicWriteResult,
    RunMutation,
    TransactionScope,
)

logger = logging.getLogger(__name__)  # Keep action repository logs in one named module.

ACTION_COLLECTION = "upgrade_run_actions"  # Match the approved action journal collection.
RUN_COLLECTION = "upgrade_runs"  # Join successful outcomes to the authoritative run collection.
_ACTION_STRATEGY = ENDPOINT_PRIMARY_KEY_STRATEGIES["upgradeRunActions"]  # Read the registered action key plan.
_DOMAIN_KEY_FIELDS = tuple(_ACTION_STRATEGY["primary_key"])  # Keep domain key field order authoritative.
_INDEX_DEFINITIONS = (  # Create the three approved persistent indexes.
    {  # Enforce the composite actor and request domain key.
        "type": "persistent",  # Use an ordinary durable ArangoDB index.
        "fields": list(_DOMAIN_KEY_FIELDS),  # Use the registered composite primary-key fields directly.
        "name": "idx_upgrade_run_actions_actor_request",  # Keep bootstrap idempotent.
        "unique": True,  # Refuse two actions for one durable actor request.
        "sparse": False,  # Require both domain key fields on every action.
    },
    {  # Enforce one globally unique public action identifier.
        "type": "persistent",  # Use an ordinary durable ArangoDB index.
        "fields": ["action_id"],  # Support result reads by the public identifier.
        "name": "idx_upgrade_run_actions_action_id",  # Keep bootstrap idempotent.
        "unique": True,  # Prevent one public identifier from naming two records.
        "sparse": False,  # Require the public identifier on every action.
    },
    {  # Support actor-scoped action history reads.
        "type": "persistent",  # Use an ordinary durable ArangoDB index.
        "fields": ["actor_scope", "created_at"],  # Match the approved read index.
        "name": "idx_upgrade_run_actions_actor_created",  # Keep bootstrap idempotent.
        "unique": False,  # Let one actor create many actions over time.
        "sparse": False,  # Require both indexed fields on every action.
    },
)  # Keep the collection free of an expiry index.


class ActionStoreError(RuntimeError):
    """Base error for the durable action journal."""


class ActionStoreUnavailable(ActionStoreError):
    """State that ArangoDB could not complete or verify an action operation."""


class ActionRequestConflict(ActionStoreError):
    """State that one idempotency key already binds different request content."""


class ActionStateConflict(ActionStoreError):
    """State that a compare-and-swap precondition no longer matches."""


class ActionRepository:
    """Own ArangoDB action bootstrap, reads, compare-and-swap, and transactions."""

    def __init__(self, database: Any, transactions: Any | None = None) -> None:
        """Bind the repository to one ArangoDB database and no fallback store."""
        self.database = database  # Keep the authoritative store handle only.
        self.transactions = transactions or ArangoTransactionAdapter(database)  # Use explicit ArangoDB writes.

    def bootstrap(self) -> bool:
        """Create the action collection and its three durable indexes."""
        self._require_database()  # Fail before any fallback can run.
        logger.info("Create the upgrade action collection and indexes")  # Record schema work before it starts.
        try:  # A store fault must fail the complete bootstrap.
            self._verify_strategy()  # Refuse schema work when the registered domain key differs.
            if not self.database.has_collection(ACTION_COLLECTION):  # Create the collection one time only.
                self.database.create_collection(ACTION_COLLECTION)  # Create no alternate collection.
            collection = self.database.collection(ACTION_COLLECTION)  # Read the authoritative collection handle.
            for definition in _INDEX_DEFINITIONS:  # Install each approved index idempotently.
                collection.add_index(dict(definition))  # Give the driver a fresh definition map.
            self._verify_indexes(collection)  # Read the index definitions back before success.
        except Exception as error:  # Convert every driver fault to the stable fail-closed error.
            logger.exception("The upgrade action store bootstrap failed")  # Record full safe fault context.
            raise ActionStoreUnavailable("The ArangoDB action store is unavailable.") from error
        logger.debug("Created the upgrade action collection with three indexes")  # Confirm safe schema counts.
        return True  # Report success only after index read-back.

    def read(self, actor_scope: str, action_id: str) -> UpgradeRunAction | None:
        """Return one actor-scoped action without revealing another actor."""
        self._require_database()  # Fail closed when ArangoDB is absent.
        logger.info("Read one actor-scoped upgrade action")  # Record the read without actor content.
        try:  # A read fault must not look like an absent action.
            collection = self.database.collection(ACTION_COLLECTION)  # Use only the action journal.
            stored = self._find_action(collection, actor_scope, action_id)  # Filter by actor and public identifier.
            action = UpgradeRunAction.from_document(stored) if stored is not None else None  # Validate a found row.
        except Exception as error:  # Convert driver and corrupt-record faults to one store error.
            logger.exception("The actor-scoped upgrade action read failed")  # Record full safe fault context.
            raise ActionStoreUnavailable("The ArangoDB action store is unavailable.") from error
        logger.debug("The actor-scoped action read found a record: %s", action is not None)  # Report no identity.
        return action  # Return None for an absent or differently owned action.

    def find_request(self, actor_scope: str, idempotency_key_digest: str) -> UpgradeRunAction | None:
        """Return one action by its composite durable domain key."""
        self._require_database()  # Fail closed when ArangoDB is absent.
        logger.info("Read one upgrade action by its durable request key")  # Record the safe key read.
        key = UpgradeRunAction.document_key(actor_scope, idempotency_key_digest)  # Rebuild the ArangoDB key.
        try:  # A read fault must not look like an unused request key.
            stored = self.database.collection(ACTION_COLLECTION).get(key)  # Use the composite digest directly.
            owned = stored if stored is not None and stored.get("actor_scope") == actor_scope else None
            action = UpgradeRunAction.from_document(owned) if owned is not None else None  # Validate a found row.
        except Exception as error:  # Convert driver and corrupt-record faults to one store error.
            logger.exception("The durable request key read failed")  # Record full safe fault context.
            raise ActionStoreUnavailable("The ArangoDB action store is unavailable.") from error
        logger.debug("The durable request key read found a record: %s", action is not None)  # Report no key value.
        return action  # Return only the action of the supplied durable actor.

    def initialize(
        self,
        request: ActionInitialization,
        lease: ActionLease,
        created_at: str,
    ) -> UpgradeRunAction:
        """Create ordered placeholders or return the same stored request."""
        self._require_database()  # Fail before any run mutation can start.
        candidate = UpgradeRunAction.initialize(request, lease, created_at)  # Build one validated action record.
        logger.info("Initialize one durable upgrade action")  # Record initialization before its transaction.
        try:  # A transaction fault must create no fallback record.
            action = self.transactions.run(  # Create or resolve the composite key atomically.
                TransactionScope((), (ACTION_COLLECTION,)),  # Change only the action journal.
                lambda database: self._initialize_in(database, candidate),  # Use the transaction database only.
            )
        except ActionRequestConflict:  # Keep the stable different-request conflict.
            raise  # Let the route map this error to HTTP 409.
        except Exception as error:  # Resolve a possible concurrent same-key insert before failure.
            action = self._resolve_initialize_fault(candidate, error)  # Return only a verified matching action.
        verified = self._verify_action(action)  # Read the stored action back before success.
        logger.debug("Initialized one durable action with %s item(s)", len(verified.ledger.items))  # Safe count.
        return verified  # Return the stored record, not the unverified candidate.

    def claim_item(
        self,
        actor_scope: str,
        action_id: str,
        run_id: str,
        lease: ActionLease,
    ) -> UpgradeRunAction:
        """Change one pending item to claimed with compare-and-swap."""
        logger.info("Claim one pending upgrade action item")  # Record the claim before the transaction.
        changed = self._change_action(  # Use one action revision for the complete claim.
            actor_scope,  # Keep the read actor-scoped.
            action_id,  # Name the public action.
            lambda action: self._claim_action_item(action, run_id, lease),  # Require the current action lease.
        )
        verified = self._verify_action(changed)  # Read the claimed item back before work starts.
        logger.debug("Claimed one upgrade action item")  # Confirm the claim without run or actor content.
        return verified  # Give the worker the durable claimed action.

    def write_outcome(
        self,
        actor_scope: str,
        action_id: str,
        outcome: RunActionOutcome,
    ) -> UpgradeRunAction:
        """Store one refused, failed, or unknown outcome with no run mutation."""
        if outcome.completion.classification == "succeeded":  # Success requires the run transaction.
            raise ValueError("A succeeded outcome requires an atomic run mutation.")  # Prevent split success.
        logger.info("Store one outcome-only upgrade action result")  # Record the final write before its transaction.
        changed = self._change_action(  # Use one compare-and-swap action write.
            actor_scope,  # Keep the write actor-scoped.
            action_id,  # Name the public action.
            lambda action: self._apply_outcome(action, outcome),  # Replace only the claimed matching item.
        )
        verified = self._verify_outcome(changed, outcome)  # Read the final item back before success.
        logger.debug("Stored one outcome-only upgrade action result")  # Confirm one durable final item.
        return verified  # Return the verified stored action.

    def commit_success(
        self,
        actor_scope: str,
        action_id: str,
        outcome: RunActionOutcome,
        mutation: RunMutation,
    ) -> AtomicWriteResult:
        """Store one run mutation and its succeeded outcome atomically."""
        self._require_success(outcome)  # Keep outcome-only results away from the run transaction.
        logger.info("Store one run mutation with its action outcome")  # Record the atomic write before it starts.
        write_request = (actor_scope, action_id, outcome, mutation)  # Keep the transaction callback concise.
        try:  # A transaction fault must roll back both records.
            self.transactions.run(  # Join the authoritative run and action writes.
                TransactionScope((), (ACTION_COLLECTION, RUN_COLLECTION)),  # Lock both changed collections.
                lambda database: self._commit_success_in(database, write_request),  # Use one cohesive request.
            )
        except ActionStateConflict:  # Keep a stable compare-and-swap refusal.
            raise  # Let the caller choose the correct durable refusal.
        except Exception as error:  # Convert all database faults to the fail-closed error.
            logger.exception("The atomic run and action write failed")  # Record full safe fault context.
            raise ActionStoreUnavailable("The ArangoDB action store is unavailable.") from error
        action = self._verify_outcome(self._read_required(actor_scope, action_id), outcome)  # Verify the item.
        run = self._verify_run(mutation)  # Verify the authoritative run write.
        logger.debug("Stored and verified one atomic run and action outcome")  # Confirm both durable records.
        return AtomicWriteResult(action, run)  # Return only verified stored values.

    @staticmethod
    def _require_success(outcome: RunActionOutcome) -> None:
        """Require one succeeded final outcome for a run transaction."""
        if outcome.completion.classification != "succeeded":  # Atomic success is not an outcome-only path.
            raise ValueError("An atomic run mutation requires a succeeded outcome.")  # Keep write units explicit.

    def store_site_block(
        self,
        actor_scope: str,
        action_id: str,
        site_id: str,
        reason: str,
    ) -> UpgradeRunAction:
        """Store one durable site stop decision with compare-and-swap."""
        logger.info("Store one durable site block")  # Record the safety decision before its write.
        changed = self._change_action(  # Use the current action revision.
            actor_scope,  # Keep the write actor-scoped.
            action_id,  # Name the public action.
            lambda action: action.with_site_block(site_id, reason),  # Preserve all ordered outcomes.
        )
        verified = self._verify_action(changed)  # Read the site block back before later item work.
        logger.debug("Stored one durable site block")  # Confirm the safety decision without site data.
        return verified  # Give recovery the stored block map.

    def take_over(
        self,
        actor_scope: str,
        action_id: str,
        lease: ActionLease,
        now: str,
    ) -> UpgradeRunAction:
        """Take one expired action lease and close abandoned claimed items."""
        logger.info("Take ownership of one expired upgrade action")  # Record recovery before its transaction.
        changed = self._change_action(  # Use one action revision for lease and interrupted outcomes.
            actor_scope,  # Keep the recovery actor-scoped.
            action_id,  # Name the public action.
            lambda action: self._take_over_action(action, lease, now),  # Preserve pending and final items.
        )
        verified = self._verify_action(changed)  # Read the lease and interrupted items back.
        logger.debug("Took ownership of one expired upgrade action")  # Confirm recovery without owner data.
        return verified  # Give the recovery service only durable state.

    def finalize(self, actor_scope: str, action_id: str, completed_at: str) -> UpgradeRunAction:
        """Change one all-final processing action to complete."""
        logger.info("Finalize one durable upgrade action")  # Record finalization before its transaction.
        changed = self._change_action(  # Use one action revision for processing-to-complete.
            actor_scope,  # Keep the finalization actor-scoped.
            action_id,  # Name the public action.
            lambda action: action.completed(completed_at),  # Refuse while one item is not final.
        )
        verified = self._verify_action(changed)  # Read the complete action back before success.
        logger.debug("Finalized one durable upgrade action")  # Confirm the verified complete status.
        return verified  # Return the complete stored action.

    def _require_database(self) -> None:
        """Refuse an operation when the ArangoDB handle is absent."""
        if self.database is None:  # No alternate store can preserve the required transaction.
            raise ActionStoreUnavailable("The ArangoDB action store is unavailable.")  # Fail closed.

    @staticmethod
    def _verify_indexes(collection: Any) -> None:
        """Verify the exact required index fields and uniqueness."""
        indexes = collection.indexes() or []  # Read the durable collection metadata back.
        actual = {(tuple(item.get("fields", ())), bool(item.get("unique"))) for item in indexes}  # Normalize.
        expected = {(tuple(item["fields"]), bool(item["unique"])) for item in _INDEX_DEFINITIONS}  # Normalize.
        if not expected.issubset(actual):  # A missing key or actor index makes the bootstrap incomplete.
            raise RuntimeError("The upgrade action collection is missing a required index.")  # Fail before use.

    @staticmethod
    def _verify_strategy() -> None:
        """Require the approved composite action key strategy."""
        if _ACTION_STRATEGY.get("type") != "composite_pk":  # A different route can fan out or lose key meaning.
            raise RuntimeError("The upgrade action primary-key strategy is not composite.")  # Fail closed.
        if _DOMAIN_KEY_FIELDS != ("actor_scope", "idempotency_key_digest"):  # Preserve the approved field order.
            raise RuntimeError("The upgrade action primary-key fields do not match.")  # Refuse schema drift.
        if tuple(_ACTION_STRATEGY.get("indexes", ())) != ("action_id", "actor_scope", "created_at"):
            raise RuntimeError("The upgrade action index fields do not match.")  # Refuse read index drift.
        if tuple(_ACTION_STRATEGY.get("unique_constraints", ())) != ("action_id",):
            raise RuntimeError("The upgrade action unique constraint does not match.")  # Refuse key drift.

    @staticmethod
    def _find_action(collection: Any, actor_scope: str, action_id: str) -> Mapping[str, Any] | None:
        """Return one raw action that matches both actor and public identifier."""
        cursor = collection.find({"actor_scope": actor_scope, "action_id": action_id}, limit=1)  # Use both filters.
        return next(iter(cursor), None)  # Return no hint for a differently owned action.

    @staticmethod
    def _initialize_in(database: Any, candidate: UpgradeRunAction) -> UpgradeRunAction:
        """Insert one candidate or resolve the existing composite key."""
        collection = database.collection(ACTION_COLLECTION)  # Use the transaction collection handle.
        stored = collection.get(candidate.key.document_key)  # Read the composite domain key.
        if stored is not None:  # A prior request already owns this durable key.
            return ActionRepository._matching_request(stored, candidate)  # Return only the same request.
        collection.insert(candidate.document(), sync=True)  # Create all ordered placeholders in one write.
        return candidate  # The caller performs the required read-back after commit.

    @staticmethod
    def _matching_request(stored: Mapping[str, Any], candidate: UpgradeRunAction) -> UpgradeRunAction:
        """Return an existing same request or raise the stable conflict."""
        action = UpgradeRunAction.from_document(stored)  # Validate the existing durable record.
        if action.identity.request_digest != candidate.identity.request_digest:  # The raw key has new content.
            raise ActionRequestConflict("The idempotency key already binds a different request.")  # HTTP 409.
        return action  # Reuse the first durable request without new work.

    def _resolve_initialize_fault(self, candidate: UpgradeRunAction, error: Exception) -> UpgradeRunAction:
        """Resolve a possible concurrent insert or raise an unavailable-store error."""
        try:  # Another worker can commit the same key before this transaction.
            stored = self.find_request(candidate.identity.actor_scope, candidate.identity.idempotency_key_digest)
        except ActionStoreUnavailable:  # The read-back also failed, so persistence is unknown.
            stored = None  # Keep the original transaction fault as the cause.
        if stored is not None:  # A concurrent durable record can resolve this insert fault.
            return self._matching_request(stored.document(), candidate)  # Enforce request digest equality.
        logger.exception("The durable action initialization failed")  # Record the active fault with traceback.
        raise ActionStoreUnavailable("The ArangoDB action store is unavailable.") from error  # No fallback.

    def _change_action(self, actor_scope: str, action_id: str, change: Any) -> UpgradeRunAction:
        """Apply one compare-and-swap transformation to an action."""
        self._require_database()  # Fail before a fallback can run.
        try:  # A revision mismatch or database fault must commit no change.
            return self.transactions.run(  # Execute one action-only atomic write.
                TransactionScope((), (ACTION_COLLECTION,)),  # Change only the action journal.
                lambda database: self._change_action_in(database, actor_scope, action_id, change),
            )
        except (ActionStateConflict, ValueError):  # Keep stable validation and compare conflicts.
            raise  # Let the caller store the correct durable refusal.
        except Exception as error:  # Convert driver faults to the stable fail-closed error.
            logger.exception("The upgrade action compare-and-swap write failed")  # Record full safe context.
            raise ActionStoreUnavailable("The ArangoDB action store is unavailable.") from error

    def _change_action_in(self, database: Any, actor_scope: str, action_id: str, change: Any) -> UpgradeRunAction:
        """Apply one action transformation inside a transaction."""
        collection = database.collection(ACTION_COLLECTION)  # Use the transaction collection handle.
        stored = self._find_action(collection, actor_scope, action_id)  # Keep the write actor-scoped.
        if stored is None:  # An absent or differently owned action has no writable state.
            raise ActionStateConflict("The upgrade action does not exist.")  # Reveal no other actor.
        current = UpgradeRunAction.from_document(stored)  # Validate the current durable action.
        changed = change(current)  # Build one immutable changed record.
        self._replace_action(collection, stored, changed)  # Compare the current ArangoDB revision.
        return changed  # The public method performs read-back verification.

    @staticmethod
    def _replace_action(collection: Any, stored: Mapping[str, Any], changed: UpgradeRunAction) -> None:
        """Replace one action only when its stored revision still matches."""
        revision = str(stored.get("_rev", ""))  # Read the ArangoDB compare-and-swap value.
        if not revision:  # A missing revision cannot protect against a second worker.
            raise ActionStateConflict("The upgrade action has no revision for compare-and-swap.")
        document = changed.document()  # Build the complete validated replacement record.
        document["_rev"] = revision  # Ask ArangoDB to reject a stale action version.
        try:  # A revision conflict is a stable state conflict, not store unavailability.
            collection.replace(document, check_rev=True, sync=True)  # Replace all fields under revision control.
        except Exception as error:  # Keep driver details out of the stable error message.
            error_name = type(error).__name__.casefold()  # Read only the safe exception class name.
            error_text = str(error).casefold()  # Inspect the driver reason without logging record content.
            if "revision" in error_name or "conflict" in error_name or "revision" in error_text:
                raise ActionStateConflict("The upgrade action changed before this write.") from error
            raise  # Let the caller report store unavailability for every other driver fault.

    @staticmethod
    def _apply_outcome(action: UpgradeRunAction, outcome: RunActionOutcome) -> UpgradeRunAction:
        """Replace one claimed item and bind any safe evidence digest."""
        current = action.item(outcome.identity.source_run_id)  # Read the durable item that owns possible work.
        if current.claim.processing_state != "claimed":  # A pending or final item cannot accept a final write.
            raise ActionStateConflict("The upgrade action item is not claimed.")  # Prevent duplicate outcomes.
        if current.claim.claim_owner != outcome.claim.claim_owner:  # Only the claiming worker can finalize.
            raise ActionStateConflict("The upgrade action item has a different claim owner.")  # Refuse takeover.
        if outcome.claim.processing_state != "final":  # A final write must close the processing state.
            raise ValueError("The supplied action outcome is not final.")  # Refuse another placeholder.
        if outcome.identity != current.identity:  # A worker cannot change run, site, or action identity.
            raise ValueError("The supplied action outcome has different identity fields.")  # Preserve order.
        changed = action.with_item(outcome)  # Replace exactly one ordered durable item.
        if outcome.evidence_summary is not None:  # Store the matching parent digest in the same write.
            changed = changed.with_evidence_digest(evidence_summary_digest(outcome.evidence_summary))
        return changed  # Give the transaction one complete action replacement.

    @staticmethod
    def _claim_action_item(action: UpgradeRunAction, run_id: str, lease: ActionLease) -> UpgradeRunAction:
        """Claim one pending item only for the current action lease."""
        if action.lifecycle.status != "processing":  # A complete action cannot start another mutation.
            raise ActionStateConflict("A complete action cannot claim an item.")  # Preserve finality.
        if action.lifecycle.lease != lease:  # A stale or different worker cannot claim pending work.
            raise ActionStateConflict("The upgrade action has a different processing lease.")  # Refuse work.
        item = action.item(run_id)  # Read exactly one ordered durable placeholder.
        return action.with_item(item.claimed(lease.owner, lease.expires_at))  # Store the item claim atomically.

    def _commit_success_in(
        self,
        database: Any,
        request: tuple[str, str, RunActionOutcome, RunMutation],
    ) -> None:
        """Change one run and its successful action item in one transaction."""
        actor_scope, action_id, outcome, mutation = request  # Read the cohesive atomic write request.
        action_collection = database.collection(ACTION_COLLECTION)  # Use the transaction action handle.
        stored = self._find_action(action_collection, actor_scope, action_id)  # Keep the write actor-scoped.
        if stored is None:  # An absent or differently owned action has no writable state.
            raise ActionStateConflict("The upgrade action does not exist.")  # Reveal no other actor.
        action = UpgradeRunAction.from_document(stored)  # Validate the current durable action.
        changed = self._apply_outcome(action, outcome)  # Enforce the item claim and evidence rules.
        self._mutate_run(database.collection(RUN_COLLECTION), mutation)  # Change the authoritative run first.
        self._replace_action(action_collection, stored, changed)  # Store success in the same transaction.

    @staticmethod
    def _mutate_run(collection: Any, mutation: RunMutation) -> None:
        """Apply one revision-bound run update or one new run insert."""
        if mutation.operation == "insert":  # A retry success creates one new run.
            if collection.get(mutation.run_id) is not None:  # A repeated retry key cannot overwrite a run.
                raise ActionStateConflict("The retry run already exists.")  # Prevent duplicate creation.
            document = dict(mutation.document)  # Stop the caller from changing the inserted run.
            document["_key"] = mutation.run_id  # Use the requested natural run key.
            collection.insert(document, sync=True)  # Insert the new run in the action transaction.
            return  # The insert path needs no prior revision check.
        stored = collection.get(mutation.run_id)  # Read the authoritative run inside the transaction.
        if stored is None:  # An absent source cannot receive a successful mutation.
            raise ActionStateConflict("The source run does not exist.")  # Refuse a false success.
        if stored.get("_rev") != mutation.expected_revision or stored.get("state") != mutation.expected_state:
            raise ActionStateConflict("The source run changed before the transaction.")  # Refuse stale evidence.
        document = dict(stored)  # Preserve all run fields that this mutation does not change.
        document.update(mutation.document)  # Apply only the approved changed fields.
        collection.replace(document, check_rev=True, sync=True)  # Bind the update to the stored revision.

    def _verify_action(self, expected: UpgradeRunAction) -> UpgradeRunAction:
        """Read one action back and compare every modeled field."""
        stored = self._read_required(expected.identity.actor_scope, expected.key.action_id)  # Actor-scoped read.
        if stored.document() != expected.document():  # A partial or changed write cannot report success.
            raise ActionStoreUnavailable("The ArangoDB action write did not pass verification.")  # Fail closed.
        return stored  # Return the verified stored value.

    def _read_required(self, actor_scope: str, action_id: str) -> UpgradeRunAction:
        """Read one required actor-scoped action or fail verification."""
        stored = self.read(actor_scope, action_id)  # Use the same actor-scoped result path as the API.
        if stored is None:  # A missing record cannot prove a prior write.
            raise ActionStoreUnavailable("The ArangoDB action write did not persist.")  # Report no success.
        return stored  # Give verification the validated immutable record.

    def _verify_outcome(self, expected: UpgradeRunAction, outcome: RunActionOutcome) -> UpgradeRunAction:
        """Read one final item back and compare its complete durable shape."""
        stored = self._verify_action(expected)  # Compare every parent action field first.
        if stored.item(outcome.identity.source_run_id).document() != outcome.document():
            raise ActionStoreUnavailable("The ArangoDB action outcome did not persist.")  # Refuse partial success.
        return stored  # Return the complete verified action.

    def _verify_run(self, mutation: RunMutation) -> dict[str, Any]:
        """Read one run back and verify each field the mutation supplied."""
        logger.info("Read one run after the atomic action transaction")  # Record verification before its read.
        try:  # A read fault makes the prior write result unknown.
            stored = self.database.collection(RUN_COLLECTION).get(mutation.run_id)  # Read the natural run key.
        except Exception as error:  # Convert a failed verification read to store unavailability.
            logger.exception("The atomic run read-back failed")  # Record full safe fault context.
            raise ActionStoreUnavailable("The ArangoDB run write is not verified.") from error
        if stored is None or any(stored.get(key) != value for key, value in mutation.document.items()):
            raise ActionStoreUnavailable("The ArangoDB run write is not verified.")  # Refuse a mismatch.
        logger.debug("Verified one run after the atomic action transaction")  # Confirm no run content.
        return dict(stored)  # Give the caller an isolated verified run record.

    @staticmethod
    def _take_over_action(action: UpgradeRunAction, lease: ActionLease, now: str) -> UpgradeRunAction:
        """Replace an expired lease and close each abandoned claimed item."""
        if action.lifecycle.status != "processing":  # A complete action needs no recovery.
            raise ActionStateConflict("A complete action cannot receive a recovery lease.")  # Preserve finality.
        if action.lifecycle.lease.is_current(now):  # A current owner still protects all possible writes.
            raise ActionStateConflict("The upgrade action processing lease is still active.")  # Do not take over.
        if not lease.is_current(now):  # A replacement lease must protect the complete recovery pass.
            raise ValueError("The replacement action lease is not current.")  # Refuse an expired new owner.
        changed = action.with_lease(lease)  # Store the new opaque owner and lease end.
        for item in action.ledger.items:  # Inspect every item in stable request order.
            if item.claim.processing_state == "claimed":  # A claimed mutation can already have committed.
                changed = changed.with_item(item.interrupted(now))  # Finalize it and never repeat it.
        return changed  # Preserve pending items, final items, order, and durable site blocks.
