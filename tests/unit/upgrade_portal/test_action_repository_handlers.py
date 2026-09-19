"""Tests for narrowed action repository exception handlers."""

from __future__ import annotations

from types import SimpleNamespace  # WHY: small outcome and mutation seams avoid full run setup.
from typing import Any  # WHY: fake database seams accept the repository's dynamic driver calls.

import pytest
from arango.exceptions import ArangoError  # WHY: tests drive the narrowed driver-fault handlers.

from src.upgrade_portal.persistence.actions import (
    ActionIdentity,
    ActionInitialization,
    ActionIntent,
    ActionLease,
    ActionRepository,
    ActionSource,
    ActionStateConflict,
    ActionStoreUnavailable,
    DurableActorScope,
    UpgradeRunAction,
    canonical_digest,
)

ACTION_TIME = "2026-09-18T00:00:00+00:00"  # WHY: stable timestamp for action construction.
REQUEST_KEY = "visible-handler-key-0001"  # WHY: valid idempotency key length for action identity.


def _initialization() -> ActionInitialization:
    """Return one valid action initialization."""
    actor = DurableActorScope.build("email", "operator@example.invalid")  # WHY: build one durable actor.
    fields = {"action": "cancel", "run_ids": ["run-one"]}  # WHY: bind the request digest to one run.
    identity = ActionIdentity.from_request(actor, REQUEST_KEY, fields, "CANCEL run-one")  # WHY: build identity.
    source = ActionSource.bulk(  # WHY: satisfy source rules with a valid digest.
        "preview-one", canonical_digest("preview-one"), "org-one", "site-one"
    )
    intent = ActionIntent("cancel", ("run-one",), ("site-one",), 1)  # WHY: request one run at one site.
    return ActionInitialization(identity, source, intent)  # WHY: repository initialize requires this value.


class _FakeCollection:
    """A collection seam that can raise one configured ArangoDB error."""

    def __init__(self, failure: Exception | None = None) -> None:
        """Store the optional failure."""
        self.failure = failure  # WHY: each test chooses the driver failure site.

    def find(self, *_args: Any, **_kwargs: Any) -> list[Any]:
        """Raise or return no rows for actor-scoped reads."""
        if self.failure is not None:  # WHY: drive the repository read handler.
            raise self.failure  # WHY: simulate a python-arango read failure.
        return []  # WHY: absent action is the safe non-error default.

    def get(self, *_args: Any, **_kwargs: Any) -> Any:
        """Raise or return no document for key reads."""
        if self.failure is not None:  # WHY: drive the repository key-read handler.
            raise self.failure  # WHY: simulate a python-arango get failure.
        return None  # WHY: absent action is the safe non-error default.

    def replace(self, *_args: Any, **_kwargs: Any) -> None:
        """Raise the configured replacement failure."""
        if self.failure is not None:  # WHY: drive the compare-and-swap handler.
            raise self.failure  # WHY: simulate a python-arango replace failure.


class _FakeDatabase:
    """A database seam that can raise one configured ArangoDB error."""

    def __init__(self, failure: Exception | None = None) -> None:
        """Store the optional failure."""
        self.failure = failure  # WHY: each test chooses the driver failure site.
        self.collection_handle = _FakeCollection(failure)  # WHY: reuse one controlled collection handle.

    def has_collection(self, _name: str) -> bool:
        """Raise or report that the collection already exists."""
        if self.failure is not None:  # WHY: drive the bootstrap handler.
            raise self.failure  # WHY: simulate a python-arango schema read failure.
        return True  # WHY: skip collection creation in tests that do not target bootstrap.

    def collection(self, _name: str) -> _FakeCollection:
        """Return the controlled collection handle."""
        return self.collection_handle  # WHY: repository calls all collection operations through this seam.


class _FailingTransactions:
    """A transaction seam that raises one configured ArangoDB error."""

    def __init__(self, failure: ArangoError) -> None:
        """Store the transaction failure."""
        self.failure = failure  # WHY: each transaction test chooses the driver failure.

    def run(self, *_args: Any, **_kwargs: Any) -> Any:
        """Raise the configured transaction failure."""
        raise self.failure  # WHY: simulate begin, callback, or commit failure.


def test_bootstrap_converts_arango_fault_to_unavailable() -> None:
    """Bootstrap converts a schema driver fault to the stable store error."""
    repository = ActionRepository(_FakeDatabase(ArangoError("schema failed")))  # WHY: fail has_collection.
    with pytest.raises(ActionStoreUnavailable, match="unavailable"):  # WHY: caller handles this stable error.
        repository.bootstrap()  # WHY: drive the narrowed bootstrap handler.


def test_read_converts_arango_fault_to_unavailable() -> None:
    """Actor-scoped read converts a driver fault to the stable store error."""
    repository = ActionRepository(_FakeDatabase(ArangoError("find failed")))  # WHY: fail collection.find.
    with pytest.raises(ActionStoreUnavailable, match="unavailable"):  # WHY: route callers map this stable error.
        repository.read("actor-one", "action-one")  # WHY: drive the narrowed read handler.


def test_read_propagates_an_unexpected_collection_bug() -> None:
    """Actor-scoped read does not hide a non-driver programming fault."""
    repository = ActionRepository(_FakeDatabase(RuntimeError("unexpected bug")))  # WHY: fail collection.find.
    with pytest.raises(RuntimeError, match="unexpected bug"):  # WHY: unexpected faults must not become store outages.
        repository.read("actor-one", "action-one")  # WHY: drive the narrowed read handler.


def test_find_request_converts_arango_fault_to_unavailable() -> None:
    """Request-key read converts a driver fault to the stable store error."""
    repository = ActionRepository(_FakeDatabase(ArangoError("get failed")))  # WHY: fail collection.get.
    with pytest.raises(ActionStoreUnavailable, match="unavailable"):  # WHY: route callers map this stable error.
        repository.find_request("actor-one", "digest-one")  # WHY: drive the narrowed find_request handler.


def test_initialize_converts_transaction_arango_fault_to_unavailable() -> None:
    """Initialize converts an unresolved transaction driver fault to unavailable."""
    failure = ArangoError("transaction failed")  # WHY: one driver failure proves the narrowed handler.
    repository = ActionRepository(_FakeDatabase(), _FailingTransactions(failure))  # WHY: transaction fails first.
    with pytest.raises(ActionStoreUnavailable, match="unavailable"):  # WHY: caller handles this stable error.
        repository.initialize(_initialization(), ActionLease("worker-one", ACTION_TIME), ACTION_TIME)  # WHY: drive it.


def test_commit_success_converts_transaction_arango_fault_to_unavailable() -> None:
    """Atomic success converts a transaction driver fault to unavailable."""
    failure = ArangoError("transaction failed")  # WHY: one driver failure proves the narrowed handler.
    repository = ActionRepository(_FakeDatabase(), _FailingTransactions(failure))  # WHY: transaction fails first.
    outcome = SimpleNamespace(completion=SimpleNamespace(classification="succeeded"))  # WHY: pass success precheck.
    mutation = SimpleNamespace(run_id="run-one", document={})  # WHY: transaction failure happens before verification.
    with pytest.raises(ActionStoreUnavailable, match="unavailable"):  # WHY: caller handles this stable error.
        repository.commit_success("actor-one", "action-one", outcome, mutation)  # WHY: drive commit handler.


def test_change_action_converts_transaction_arango_fault_to_unavailable() -> None:
    """Compare-and-swap converts a transaction driver fault to unavailable."""
    failure = ArangoError("transaction failed")  # WHY: one driver failure proves the narrowed handler.
    repository = ActionRepository(_FakeDatabase(), _FailingTransactions(failure))  # WHY: transaction fails first.
    with pytest.raises(ActionStoreUnavailable, match="unavailable"):  # WHY: caller handles this stable error.
        repository._change_action("actor-one", "action-one", lambda action: action)  # WHY: drive private handler.


def test_replace_action_maps_revision_arango_fault_to_state_conflict() -> None:
    """Replace maps a driver revision conflict to the stable state conflict."""
    collection = _FakeCollection(ArangoError("revision conflict"))  # WHY: simulate a stale ArangoDB revision.
    action = UpgradeRunAction.initialize(_initialization(), ActionLease("worker-one", ACTION_TIME), ACTION_TIME)
    with pytest.raises(ActionStateConflict, match="changed before this write"):  # WHY: caller handles this conflict.
        ActionRepository._replace_action(collection, {"_rev": "rev-one"}, action)  # WHY: drive replace handler.


def test_verify_run_converts_arango_fault_to_unavailable() -> None:
    """Run read-back converts a driver fault to the stable store error."""
    repository = ActionRepository(_FakeDatabase(ArangoError("run read failed")))  # WHY: fail collection.get.
    mutation = SimpleNamespace(run_id="run-one", document={})  # WHY: _verify_run reads these two fields only.
    with pytest.raises(ActionStoreUnavailable, match="not verified"):  # WHY: caller sees an unverified run write.
        repository._verify_run(mutation)  # WHY: drive the narrowed run verification handler.
