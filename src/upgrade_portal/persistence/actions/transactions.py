"""Provide the explicit ArangoDB transaction boundary for run actions.

Why:
    The database router can use fallback stores. A run mutation and its action
    outcome need one ArangoDB transaction with no fallback path.
"""

from __future__ import annotations  # Keep each annotation independent from import order.

import logging  # Record each transaction without document or actor content.
from collections.abc import Callable, Mapping  # Type the operation and immutable run fields.
from dataclasses import dataclass  # Build immutable transaction request values.
from types import MappingProxyType  # Stop a caller from changing a pending run mutation.
from typing import Any, TypeVar  # Accept the python-arango handle and typed results.

logger = logging.getLogger(__name__)  # Keep transaction logs in one named module.

TransactionResult = TypeVar("TransactionResult")  # Preserve the callback result type.


@dataclass(frozen=True, slots=True)
class TransactionScope:  # Hold the collection locks for one atomic write unit.
    """Hold the ArangoDB collections for one transaction."""

    read: tuple[str, ...]  # Name collections that the transaction only reads.
    write: tuple[str, ...]  # Name collections that the transaction can change.


@dataclass(frozen=True, slots=True)
class RunMutation:  # Hold one safe run update or insert request.
    """Describe one run update or insert for an atomic success write."""

    operation: str  # Select update or insert.
    run_id: str  # Name the source or new run document key.
    expected_revision: str | None  # Bind an update to the evidence read revision.
    expected_state: str | None  # Bind an update to the final eligibility state.
    document: Mapping[str, Any]  # Hold the fields that the transaction must store.

    def __post_init__(self) -> None:  # Freeze and validate one run mutation request.
        """Validate the mutation mode and required compare values."""
        object.__setattr__(self, "document", MappingProxyType(dict(self.document)))  # Freeze all run fields.
        self._validate_operation()  # Require one supported write mode and one run key.
        self._validate_update_compare()  # Require revision and state for an update.
        self._validate_document()  # Prevent system key replacement and a mismatched run identifier.

    def _validate_operation(self) -> None:  # Validate the mutation mode and natural run key.
        """Require one supported write mode and one run identifier."""
        if self.operation not in {"update", "insert"}:  # No other write mode has an atomic contract.
            raise ValueError("The run mutation operation is not supported.")  # Refuse an unsafe write.
        if not self.run_id:  # An empty key cannot identify the run in ArangoDB.
            raise ValueError("The run mutation identifier is empty.")  # Stop before a transaction.

    def _validate_update_compare(self) -> None:  # Validate compare-and-swap fields for a run update.
        """Require revision and state values for an update."""
        if self.operation == "update" and (not self.expected_revision or not self.expected_state):
            raise ValueError("A run update requires its revision and state.")  # Require compare-and-swap inputs.

    def _validate_document(self) -> None:  # Validate safe fields in one run mutation body.
        """Refuse system fields and a mismatched natural run identifier."""
        if {"_key", "_id", "_rev"}.intersection(self.document):  # The repository owns every system field.
            raise ValueError("A run mutation cannot replace an ArangoDB system field.")  # Preserve CAS behavior.
        if self.document.get("run_id", self.run_id) != self.run_id:  # Keep the natural key consistent.
            raise ValueError("The run mutation document has a different run identifier.")  # Refuse split keys.


@dataclass(frozen=True, slots=True)
class RetryRunMutation:  # Hold one source-bound retry insert request.
    """Describe one retry insert with its source and site checks."""

    run_id: str  # Name the new run.
    source_run_id: str  # Name the terminal source.
    expected_source_revision: str  # Bind the source to the final eligibility read.
    expected_source_state: str  # Bind the source to its retryable state.
    site_id: str  # Scope the live-run check.
    document: Mapping[str, Any]  # Hold the complete new run document.

    def __post_init__(self) -> None:
        """Freeze and validate one retry insert request."""
        object.__setattr__(self, "document", MappingProxyType(dict(self.document)))
        required = (
            self.run_id,
            self.source_run_id,
            self.expected_source_revision,
            self.expected_source_state,
            self.site_id,
        )
        if not all(required):
            raise ValueError("A retry mutation requires every source and site field.")
        if self.document.get("run_id") != self.run_id or self.document.get("site_id") != self.site_id:
            raise ValueError("The retry mutation document does not match its run or site.")
        if {"_key", "_id", "_rev"}.intersection(self.document):
            raise ValueError("A retry mutation cannot replace an ArangoDB system field.")


@dataclass(frozen=True, slots=True)
class AtomicWriteResult:  # Return both verified records from one atomic success.
    """Hold the verified action and run after one successful transaction."""

    action: Any  # Hold the immutable action record without an import cycle.
    run: dict[str, Any]  # Hold the verified run document.


class ArangoTransactionAdapter:  # Own the explicit python-arango transaction lifecycle.
    """Run explicit python-arango transactions with commit and rollback."""

    def __init__(self, database: Any) -> None:  # Bind one authoritative ArangoDB database.
        """Bind the adapter to one ArangoDB database handle."""
        self.database = database  # Use no router or fallback backend.

    def run(
        self, scope: TransactionScope, operation: Callable[[Any], TransactionResult]
    ) -> TransactionResult:  # Commit or roll back one complete write unit.
        """Run one callback and commit all writes together."""
        if self.database is None:  # A missing store must fail before any mutation.
            raise RuntimeError("The ArangoDB action store is unavailable.")  # Refuse a fallback path.
        logger.info("Start one action store transaction")  # Record the atomic write before it starts.
        transaction = self.database.begin_transaction(  # Ask python-arango for one stream transaction.
            read=list(scope.read),  # Lock each read-only collection for this unit.
            write=list(scope.write),  # Lock each changed collection for this unit.
        )
        try:  # A failure must roll back the action and run together.
            result = operation(transaction)  # Execute all work through the transaction database.
            transaction.commit_transaction()  # Make the complete write unit durable.
        except Exception:  # A database or validation fault must commit no partial result.
            self._abort(transaction)  # Roll back both action and run changes.
            logger.exception("The action store transaction failed")  # Record full context without record data.
            raise  # Let the repository convert the failure to its stable error.
        logger.debug("Committed one action store transaction")  # Confirm the complete atomic write.
        return result  # Return only after the transaction commit succeeds.

    @staticmethod
    def _abort(transaction: Any) -> None:  # Roll back one failed transaction without hiding its cause.
        """Abort one transaction without hiding the original fault."""
        logger.info("Abort one action store transaction")  # Record the rollback attempt.
        try:  # A disconnected transaction can also refuse its abort call.
            transaction.abort_transaction()  # Discard every uncommitted action and run change.
        except Exception:  # The original transaction fault remains the primary error.
            logger.exception("The action store transaction abort failed")  # Record full safe fault context.
        logger.debug("Finished the action store transaction abort")  # Mark the rollback attempt complete.
