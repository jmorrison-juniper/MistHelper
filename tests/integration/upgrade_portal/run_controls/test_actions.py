"""Test durable action repository behavior with one controlled ArangoDB fake."""

from __future__ import annotations  # Keep each annotation independent from import order.

import inspect  # Verify the production repository has no fallback dependency.
from typing import Final  # Mark the fixed test times and request key.

import pytest  # Exercise stable failure and compare-and-swap behavior.

import src.upgrade_portal.persistence.actions.repository as action_repository_module  # Inspect production imports.
from src.upgrade_portal.persistence.actions import (  # Test the public action persistence surface.
    ACTION_COLLECTION,
    RUN_COLLECTION,
    ActionIdentity,
    ActionInitialization,
    ActionIntent,
    ActionLease,
    ActionRepository,
    ActionRequestConflict,
    ActionSource,
    ActionStateConflict,
    ActionStoreUnavailable,
    DurableActorScope,
    OutcomeCompletion,
    OutcomeState,
    RunActionOutcome,
    RunMutation,
    canonical_digest,
)
from tests.integration.upgrade_portal.run_controls import FakeDatabase  # Use no live ArangoDB store.

CREATED_AT: Final[str] = "2026-09-11T14:00:00+00:00"  # Fix action creation for stable assertions.
LEASE_END: Final[str] = "2026-09-11T14:05:00+00:00"  # Keep the initial lease active.
REQUEST_KEY: Final[str] = "visible-request-key-0001"  # Meet the HTTP request key length.


def _initialization(
    run_ids: tuple[str, ...] = ("run-one", "run-two"),
    site_ids: tuple[str, ...] = ("site-one", "site-two"),
    request_key: str = REQUEST_KEY,
    request_tag: str = "first",
) -> ActionInitialization:  # Build one source-specific durable action request.
    """Return one valid bulk action initialization."""
    actor = DurableActorScope.build("email", "operator@example.invalid")  # Build one stable actor scope.
    request_fields = {"action": "cancel", "run_ids": list(run_ids), "tag": request_tag}  # Bind request order.
    identity = ActionIdentity.from_request(actor, request_key, request_fields, "CANCEL 2 RUNS")  # Hash secrets.
    preview_digest = canonical_digest({"preview": "preview-one"})  # Store no raw preview value.
    source = ActionSource.bulk("preview-one", preview_digest, "org-one", "all-sites")  # Require preview fields.
    intent = ActionIntent("cancel", run_ids, site_ids, len(set(site_ids)))  # Keep ordered distinct runs.
    return ActionInitialization(identity, source, intent)  # Enforce source-specific action rules.


def _repository() -> tuple[FakeDatabase, ActionRepository]:  # Create one isolated action repository.
    """Return one bootstrapped ArangoDB-only action repository."""
    database = FakeDatabase()  # Start one process-owned controlled store.
    database.create_collection(RUN_COLLECTION)  # Model the existing authoritative run collection.
    repository = ActionRepository(database)  # Inject only the controlled ArangoDB handle.
    repository.bootstrap()  # Create and verify the action collection and indexes.
    return database, repository  # Give each test isolated durable state.


def _lease(owner: str = "worker-one", expires_at: str = LEASE_END) -> ActionLease:  # Build one opaque controlled lease.
    """Return one opaque controlled processing lease."""
    return ActionLease(owner, expires_at)  # Keep worker and expiry values together.


def _final_outcome(
    item: RunActionOutcome,
    classification: str = "refused",
    reason: str = "run_changed",
    final_state: str = "",
) -> RunActionOutcome:  # Build one final durable outcome for a claimed item.
    """Return one final outcome from a claimed controlled item."""
    state = OutcomeState("created", final_state, CREATED_AT, CREATED_AT)  # Store final check and outcome times.
    message = "The portal did not change this run."  # Use safe operator text.
    result_run_id = item.identity.source_run_id if classification == "succeeded" else ""  # Name verified success.
    completion = OutcomeCompletion(classification, reason, message, result_run_id, state)  # Build final fields.
    return item.finalized(completion)  # Preserve the durable item claim and identity.


def test_bootstrap_creates_only_the_action_collection_and_required_indexes() -> None:
    """Bootstrap creates the ArangoDB action collection and its approved indexes."""
    database, repository = _repository()  # Run the real repository bootstrap against a controlled fake.
    repository.bootstrap()  # Repeat bootstrap to prove collection and index creation is idempotent.
    assert repository.database is database  # Keep one authoritative ArangoDB handle.
    assert ACTION_COLLECTION in database.collections  # Create the approved action journal.
    indexes = database.collection(ACTION_COLLECTION).indexes()  # Read the durable definitions back.
    assert len(indexes) == 3  # Create no expiry or fallback index.
    assert {tuple(index["fields"]) for index in indexes} == {  # Match all approved index fields.
        ("actor_scope", "idempotency_key_digest"),  # Enforce the composite domain key.
        ("action_id",),  # Keep each public action identifier unique.
        ("actor_scope", "created_at"),  # Support actor-scoped history reads.
    }


def test_initialize_keeps_order_and_actor_scoped_reads() -> None:
    """Initialization stores ordered placeholders and hides them from another actor."""
    _, repository = _repository()  # Use one isolated action journal.
    request = _initialization()  # Build two requested runs in a fixed order.
    action = repository.initialize(request, _lease(), CREATED_AT)  # Create all placeholders atomically.
    owned = repository.read(request.identity.actor_scope, action.key.action_id)  # Read with the durable owner.
    other = DurableActorScope.build("email", "other@example.invalid")  # Build a different durable actor.
    hidden = repository.read(other.actor_scope, action.key.action_id)  # Use the same public action identifier.
    assert owned is not None  # Return the action to its durable owner.
    assert [item.identity.source_run_id for item in owned.ledger.items] == ["run-one", "run-two"]  # Keep order.
    assert hidden is None  # Reveal no information to another actor.


def test_initialize_returns_the_same_action_for_the_same_request_key() -> None:
    """The same actor, request key, and request content create no second action."""
    database, repository = _repository()  # Use one isolated action journal.
    request = _initialization()  # Build one durable request binding.
    first = repository.initialize(request, _lease(), CREATED_AT)  # Create the first action.
    second = repository.initialize(request, _lease("worker-two"), CREATED_AT)  # Replay the same request.
    assert second.key.action_id == first.key.action_id  # Return the first durable action identifier.
    assert len(database.collections[ACTION_COLLECTION]["documents"]) == 1  # Create no duplicate record.


def test_initialize_rejects_the_same_key_for_different_request_content() -> None:
    """The same actor and request key cannot bind a different action request."""
    _, repository = _repository()  # Use one isolated action journal.
    first = _initialization(request_tag="first")  # Build the first request digest.
    changed = _initialization(request_tag="second")  # Keep the raw key and change bound content.
    repository.initialize(first, _lease(), CREATED_AT)  # Store the first durable request.
    with pytest.raises(ActionRequestConflict, match="different request"):  # Return the stable HTTP conflict.
        repository.initialize(changed, _lease("worker-two"), CREATED_AT)  # Refuse a second request binding.


def test_item_claim_uses_compare_and_swap_and_verifies_the_read_back() -> None:
    """Only one worker can change a pending item to claimed."""
    _, repository = _repository()  # Use one isolated action journal.
    action = repository.initialize(_initialization(), _lease(), CREATED_AT)  # Create pending placeholders.
    claimed = repository.claim_item(action.identity.actor_scope, action.key.action_id, "run-one", _lease())
    assert claimed.item("run-one").claim.processing_state == "claimed"  # Verify the durable claim.
    assert claimed.item("run-one").claim.claim_owner == "worker-one"  # Keep the opaque claim owner.
    with pytest.raises(ActionStateConflict, match="different processing lease"):  # Refuse another worker.
        repository.claim_item(action.identity.actor_scope, action.key.action_id, "run-one", _lease("worker-two"))


@pytest.mark.parametrize(  # Prove every no-mutation classification uses the same durable path.
    ("classification", "reason"),  # Name the final result values under test.
    [
        ("refused", "run_changed"),  # A guard or state rule prevented a mutation.
        ("failed", "run_write_failed"),  # The attempted write failed before a commit.
        ("unknown", "run_write_unverified"),  # The portal cannot prove a mutation result.
    ],
)
def test_outcome_only_write_finalizes_one_claimed_item_and_changes_no_run(classification: str, reason: str) -> None:
    """Each no-mutation result uses one action compare-and-swap write."""
    database, repository = _repository()  # Use one isolated action journal.
    action = repository.initialize(_initialization(), _lease(), CREATED_AT)  # Create pending placeholders.
    claimed = repository.claim_item(action.identity.actor_scope, action.key.action_id, "run-one", _lease())
    outcome = _final_outcome(claimed.item("run-one"), classification, reason)  # Build one no-mutation result.
    changed = repository.write_outcome(action.identity.actor_scope, action.key.action_id, outcome)  # Store only it.
    assert changed.item("run-one").claim.processing_state == "final"  # Close exactly one durable item.
    assert changed.item("run-two").claim.processing_state == "pending"  # Leave the other placeholder untouched.
    assert database.collections[RUN_COLLECTION]["documents"] == {}  # Perform no run write for a refusal.


def test_atomic_success_changes_the_run_and_outcome_together() -> None:
    """A successful cancel and its outcome commit in one transaction."""
    database, repository = _repository()  # Use one isolated action journal.
    seeded = database.seed_run("run-one", "created")  # Create one authoritative pre-cloud run.
    request = _initialization(("run-one",), ("site-one",))  # Request one cancel outcome.
    action = repository.initialize(request, _lease(), CREATED_AT)  # Create the pending placeholder.
    claimed = repository.claim_item(action.identity.actor_scope, action.key.action_id, "run-one", _lease())
    outcome = _final_outcome(claimed.item("run-one"), "succeeded", "precloud_run_cancelled", "cancelled")
    mutation = RunMutation("update", "run-one", seeded["_rev"], "created", {"state": "cancelled"})  # Bind revision.
    result = repository.commit_success(action.identity.actor_scope, action.key.action_id, outcome, mutation)
    assert result.run["state"] == "cancelled"  # Verify the authoritative run mutation.
    assert result.action.item("run-one").completion.classification == "succeeded"  # Verify durable success.
    assert result.action.item("run-one").claim.processing_state == "final"  # Close the claimed item.


def test_atomic_success_rolls_back_the_run_and_outcome_on_write_failure() -> None:
    """A run write fault leaves the run unchanged and the item claimed."""
    database, repository = _repository()  # Use one isolated action journal.
    seeded = database.seed_run("run-one", "created")  # Create one authoritative pre-cloud run.
    request = _initialization(("run-one",), ("site-one",))  # Request one cancel outcome.
    action = repository.initialize(request, _lease(), CREATED_AT)  # Create the pending placeholder.
    claimed = repository.claim_item(action.identity.actor_scope, action.key.action_id, "run-one", _lease())
    outcome = _final_outcome(claimed.item("run-one"), "succeeded", "precloud_run_cancelled", "cancelled")
    mutation = RunMutation("update", "run-one", seeded["_rev"], "created", {"state": "cancelled"})  # Bind revision.
    database.failure_mode = "run_replace"  # Stop the transaction before either replacement commits.
    with pytest.raises(ActionStoreUnavailable, match="unavailable"):  # Fail closed with no fallback.
        repository.commit_success(action.identity.actor_scope, action.key.action_id, outcome, mutation)
    stored_run = database.collection(RUN_COLLECTION).get("run-one")  # Read root state after rollback.
    stored_action = repository.read(action.identity.actor_scope, action.key.action_id)  # Read the durable item.
    assert stored_run is not None and stored_run["state"] == "created"  # Roll back the run mutation.
    assert stored_action is not None  # Keep the prior claimed action record.
    assert stored_action.item("run-one").claim.processing_state == "claimed"  # Store no false success.


def test_atomic_success_can_insert_one_retry_run_with_its_outcome() -> None:
    """A retry insert and its succeeded source outcome commit together."""
    database, repository = _repository()  # Use one isolated action journal.
    request = _initialization(("run-source",), ("site-one",))  # Request one source outcome.
    action = repository.initialize(request, _lease(), CREATED_AT)  # Create the pending placeholder.
    claimed = repository.claim_item(action.identity.actor_scope, action.key.action_id, "run-source", _lease())
    item = claimed.item("run-source")  # Read the durable claimed source item.
    state = OutcomeState("failed", "created", CREATED_AT, CREATED_AT)  # Describe the verified new run.
    completion = OutcomeCompletion("succeeded", "retry_created", "The portal created a retry run.", "run-new", state)
    outcome = item.finalized(completion)  # Build success for the current durable claim.
    run_document = {"run_id": "run-new", "state": "created", "site_id": "site-one"}  # Build the new run.
    mutation = RunMutation("insert", "run-new", None, None, run_document)  # Request one atomic insert.
    result = repository.commit_success(action.identity.actor_scope, action.key.action_id, outcome, mutation)
    assert result.run["run_id"] == "run-new"  # Verify the inserted natural run identifier.
    assert database.collection(RUN_COLLECTION).get("run-new") is not None  # Keep the new run durable.
    assert result.action.item("run-source").result_run_id == "run-new"  # Bind the source outcome to the new run.


def test_finalize_requires_every_item_to_have_one_final_outcome() -> None:
    """The action cannot become complete while one placeholder remains pending."""
    _, repository = _repository()  # Use one isolated action journal.
    action = repository.initialize(_initialization(), _lease(), CREATED_AT)  # Create two placeholders.
    claimed = repository.claim_item(action.identity.actor_scope, action.key.action_id, "run-one", _lease())
    first = _final_outcome(claimed.item("run-one"))  # Build one durable refusal.
    partly_final = repository.write_outcome(action.identity.actor_scope, action.key.action_id, first)  # Store it.
    with pytest.raises(ValueError, match="before every item is final"):  # Refuse partial completion.
        repository.finalize(partly_final.identity.actor_scope, partly_final.key.action_id, CREATED_AT)
    claimed_second = repository.claim_item(  # Claim the one remaining placeholder.
        partly_final.identity.actor_scope,  # Keep the claim actor-scoped.
        partly_final.key.action_id,  # Name the same action.
        "run-two",  # Claim the remaining requested run.
        _lease(),  # Use the same opaque worker lease.
    )
    second = _final_outcome(claimed_second.item("run-two"), "unknown", "run_write_unverified")  # Close it.
    all_final = repository.write_outcome(action.identity.actor_scope, action.key.action_id, second)  # Store it.
    complete = repository.finalize(all_final.identity.actor_scope, all_final.key.action_id, CREATED_AT)  # Finish.
    assert complete.lifecycle.status == "complete"  # Report success only after every item is final.
    assert all(item.claim.processing_state == "final" for item in complete.ledger.items)  # Keep exact outcomes.


def test_missing_arango_store_has_no_fallback_path() -> None:
    """An unavailable ArangoDB store refuses bootstrap and initialization."""
    repository = ActionRepository(None)  # Supply no database and no alternate backend.
    with pytest.raises(ActionStoreUnavailable, match="unavailable"):  # Refuse schema work.
        repository.bootstrap()  # Create no SQLite, Redis, memory, or file record.
    with pytest.raises(ActionStoreUnavailable, match="unavailable"):  # Refuse action initialization.
        repository.initialize(_initialization(), _lease(), CREATED_AT)  # Mutate no run and write no fallback.


def test_action_repository_imports_no_fallback_backend() -> None:
    """The production repository has no SQLite, Redis, memory, file, or exporter dependency."""
    source = inspect.getsource(action_repository_module)  # Read only the scoped production repository.
    forbidden = ("sqlite", "redis", "DataExporter", "DatabaseRouter", "open(")  # Name each prohibited fallback.
    assert all(name not in source for name in forbidden)  # Keep ArangoDB as the only action authority.


def test_fifty_requested_runs_receive_fifty_ordered_durable_outcomes() -> None:
    """The maximum batch creates one durable placeholder for each requested run."""
    _, repository = _repository()  # Use one isolated action journal.
    run_ids = tuple(f"run-{index:02d}" for index in range(50))  # Build the maximum distinct ordered list.
    site_ids = tuple(f"site-{index:02d}" for index in range(50))  # Give each run one known site.
    action = repository.initialize(_initialization(run_ids, site_ids), _lease(), CREATED_AT)  # Store all items.
    assert len(action.ledger.items) == 50  # Create one durable outcome per request identifier.
    assert tuple(item.identity.source_run_id for item in action.ledger.items) == run_ids  # Preserve exact order.
