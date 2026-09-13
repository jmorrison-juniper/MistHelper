"""Provide controlled ArangoDB fakes for run control integration tests."""

from __future__ import annotations  # Keep each annotation independent from import order.

import logging  # Record fake store actions for deterministic test diagnostics.
from copy import deepcopy  # Isolate stored documents and transaction snapshots.
from typing import Any  # Accept the same flexible values as python-arango.

logger = logging.getLogger(__name__)  # Keep fake store diagnostics in one named module.


class FakeCollection:
    """Provide the python-arango collection operations that the repository uses."""

    def __init__(self, database: Any, name: str) -> None:
        """Bind one collection handle to its fake database view."""
        self.database = database  # Use the root or transaction-owned collection map.
        self.name = name  # Select one fake collection.

    @property
    def _state(self) -> dict[str, Any]:
        """Return the mutable state for this collection."""
        return self.database.collections[self.name]  # Keep state ownership in the database view.

    def add_index(self, definition: dict[str, Any]) -> dict[str, Any]:
        """Create one named index idempotently."""
        logger.info("Create one controlled action store index")  # Record schema work before the change.
        indexes = self._state["indexes"]  # Read the collection index list.
        existing = next((item for item in indexes if item.get("name") == definition.get("name")), None)
        if existing is None:  # A repeated bootstrap must create no duplicate index.
            indexes.append(deepcopy(definition))  # Isolate the stored definition from the caller.
        logger.debug("The controlled collection holds %s index(es)", len(indexes))  # Report a safe count.
        return deepcopy(existing or definition)  # Match the driver result shape closely enough for tests.

    def indexes(self) -> list[dict[str, Any]]:
        """Return isolated index definitions."""
        logger.info("Read controlled action store indexes")  # Record metadata verification before the read.
        indexes = deepcopy(self._state["indexes"])  # Stop a caller from changing fake schema state.
        logger.debug("Read %s controlled action store index(es)", len(indexes))  # Report a safe count.
        return indexes  # Give bootstrap one driver-like list.

    def get(self, key: str) -> dict[str, Any] | None:
        """Return one isolated document by key."""
        logger.info("Read one controlled action store document")  # Record the read without key content.
        document = self._state["documents"].get(key)  # An absent key reads as no document.
        result = deepcopy(document) if document is not None else None  # Stop caller mutation.
        logger.debug("The controlled document read found a record: %s", result is not None)  # Safe result.
        return result  # Match the python-arango get contract.

    def find(self, filters: dict[str, Any], limit: int = 1) -> list[dict[str, Any]]:
        """Return isolated documents that match every supplied field."""
        logger.info("Find one controlled action store document")  # Record the filtered read.
        matches = [  # Preserve insertion order for deterministic actor-scoped reads.
            deepcopy(document)  # Stop a caller from changing fake store state.
            for document in self._state["documents"].values()  # Inspect this collection only.
            if all(document.get(field) == value for field, value in filters.items())  # Apply all filters.
        ][
            :limit
        ]  # Match the repository limit.
        logger.debug("The controlled find returned %s record(s)", len(matches))  # Report a safe count.
        return matches  # A list provides the cursor iteration contract.

    def insert(self, document: dict[str, Any], sync: bool = True) -> dict[str, Any]:
        """Insert one new document and reject an existing key."""
        del sync  # The controlled store commits synchronously by design.
        logger.info("Insert one controlled action store document")  # Record the write before mutation.
        key = str(document["_key"])  # Read the required natural document key.
        if key in self._state["documents"]:  # An existing key models an ArangoDB unique conflict.
            raise RuntimeError("The controlled document key already exists.")  # Stop an overwrite.
        stored = deepcopy(document)  # Isolate the fake durable record.
        stored["_rev"] = "1"  # Start one revision for compare-and-swap tests.
        self._state["documents"][key] = stored  # Make the new record visible in this database view.
        logger.debug("Inserted one controlled action store document")  # Confirm the fake durable write.
        return {"new": deepcopy(stored)}  # Match the useful part of the driver response.

    def replace(self, document: dict[str, Any], check_rev: bool = True, sync: bool = True) -> dict[str, Any]:
        """Replace one document only when its revision matches."""
        del sync  # The controlled store commits synchronously by design.
        logger.info("Replace one controlled action store document")  # Record the write before mutation.
        key = str(document["_key"])  # Read the natural document key.
        stored = self._state["documents"].get(key)  # Read the current revision.
        if stored is None:  # A missing record cannot receive a replacement.
            raise RuntimeError("The controlled document does not exist.")  # Model the driver refusal.
        if check_rev and document.get("_rev") != stored.get("_rev"):  # Enforce compare-and-swap.
            raise RuntimeError("The controlled document revision changed.")  # Model a revision conflict.
        if self.database.root.failure_mode == "run_replace" and self.name == "upgrade_runs":
            self.database.root.failure_mode = None  # Consume the one planned run write failure.
            raise RuntimeError("The controlled run replacement failed.")  # Trigger transaction rollback.
        changed = deepcopy(document)  # Isolate the replacement from caller edits.
        changed["_rev"] = str(int(stored["_rev"]) + 1)  # Advance the fake ArangoDB revision.
        self._state["documents"][key] = changed  # Replace the complete stored document.
        logger.debug("Replaced one controlled action store document")  # Confirm the fake durable write.
        return {"new": deepcopy(changed)}  # Match the useful part of the driver response.


class FakeTransactionDatabase:
    """Own one isolated collection snapshot until commit or abort."""

    def __init__(self, root: FakeDatabase) -> None:
        """Copy the root state for one atomic write unit."""
        self.root = root  # Return commit results to the owning fake database.
        self.collections = deepcopy(root.collections)  # Isolate all uncommitted changes.
        self.closed = False  # Reject a second commit or abort.

    def collection(self, name: str) -> FakeCollection:
        """Return one collection from the transaction snapshot."""
        if name not in self.collections:  # A transaction cannot invent an unbootstrapped collection.
            raise RuntimeError("The controlled transaction collection does not exist.")  # Fail closed.
        return FakeCollection(self, name)  # Route reads and writes to the isolated snapshot.

    def commit_transaction(self) -> None:
        """Commit the complete snapshot or raise at a controlled fault point."""
        logger.info("Commit one controlled action store transaction")  # Record the commit before mutation.
        if self.closed:  # A completed transaction cannot commit twice.
            raise RuntimeError("The controlled transaction is already closed.")  # Model driver behavior.
        if self.root.failure_mode == "before_commit":  # Simulate a fault before durable storage.
            self.root.failure_mode = None  # Consume the one planned fault.
            raise RuntimeError("The controlled transaction stopped before commit.")  # Keep root data unchanged.
        self.root.collections = deepcopy(self.collections)  # Commit every action and run change together.
        self.closed = True  # Stop a second terminal transaction operation.
        if self.root.failure_mode == "after_commit":  # Simulate response loss after durable commit.
            self.root.failure_mode = None  # Consume the one planned fault.
            raise RuntimeError("The controlled transaction response was lost.")  # Leave committed root data.
        logger.debug("Committed one controlled action store transaction")  # Confirm the atomic fake write.

    def abort_transaction(self) -> None:
        """Discard the transaction snapshot."""
        logger.info("Abort one controlled action store transaction")  # Record rollback before state change.
        self.closed = True  # Drop the isolated snapshot without changing root data.
        logger.debug("Aborted one controlled action store transaction")  # Confirm the fake rollback.


class FakeDatabase:
    """Provide a process-owned ArangoDB stand-in with transaction fault controls."""

    def __init__(self) -> None:
        """Start with no collection and no planned fault."""
        self.collections: dict[str, dict[str, Any]] = {}  # Hold documents and indexes by collection.
        self.failure_mode: str | None = None  # Select one controlled transaction fault.
        self.root = self  # Give collection handles one common fault owner.

    def has_collection(self, name: str) -> bool:
        """Report whether one controlled collection exists."""
        return name in self.collections  # Match the python-arango database contract.

    def create_collection(self, name: str) -> FakeCollection:
        """Create one empty controlled collection."""
        logger.info("Create one controlled action store collection")  # Record schema work before mutation.
        self.collections.setdefault(name, {"documents": {}, "indexes": []})  # Keep bootstrap idempotent.
        logger.debug("Created one controlled action store collection")  # Confirm the fake schema change.
        return FakeCollection(self, name)  # Return the new driver-like handle.

    def collection(self, name: str) -> FakeCollection:
        """Return one existing controlled collection."""
        if name not in self.collections:  # An unbootstrapped action store must fail closed.
            raise RuntimeError("The controlled action store collection does not exist.")  # No fallback.
        return FakeCollection(self, name)  # Route operations to root durable state.

    def begin_transaction(self, read: list[str], write: list[str]) -> FakeTransactionDatabase:
        """Start one isolated controlled transaction snapshot."""
        del read, write  # The fake copies all collections and still enforces atomic visibility.
        logger.info("Start one controlled action store transaction")  # Record the transaction before its copy.
        transaction = FakeTransactionDatabase(self)  # Isolate all uncommitted writes.
        logger.debug("Started one controlled action store transaction")  # Confirm the snapshot exists.
        return transaction  # Let the production adapter commit or abort it.

    def seed_run(self, run_id: str, state: str = "created") -> dict[str, Any]:
        """Insert one authoritative run for an atomic mutation test."""
        if "upgrade_runs" not in self.collections:  # Create the existing run collection for a controlled test.
            self.create_collection("upgrade_runs")  # Avoid any action repository fallback behavior.
        document = {"_key": run_id, "run_id": run_id, "state": state, "_rev": "1"}  # Build one current run.
        self.collections["upgrade_runs"]["documents"][run_id] = deepcopy(document)  # Seed durable root state.
        return deepcopy(document)  # Give the test the expected revision and state.
