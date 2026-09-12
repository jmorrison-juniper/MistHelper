"""Test atomic compare-and-set behavior of both run-store implementations."""

from __future__ import annotations

from copy import deepcopy
from threading import Barrier, Lock, Thread
from types import SimpleNamespace
from typing import Any

from src.upgrade_portal.app import wiring
from src.upgrade_portal.app.routes import upgrade


def test_memory_run_store_allows_one_concurrent_child_claim() -> None:
    """Two workers that hold one version can complete only one replacement."""
    store = upgrade.MemoryRunStore()  # Use the production in-memory lock.
    run_id = "aggregate-memory-cas"  # Keep this test record separate from route records.
    initial = {"run_id": run_id, "record_version": 0, "child": "planned"}  # Build the shared version.
    assert store.write_run(initial) is True  # Seed the record before the race.
    barrier = Barrier(2)  # Release both workers after they read version zero.
    results: list[bool] = []  # Record each compare-and-set result.
    guard = Lock()  # Protect the result list from concurrent appends.

    def claim(name: str) -> None:
        """Attempt one child claim from the same record version."""
        replacement = deepcopy(initial)  # Give each worker an independent replacement.
        replacement["record_version"] = 1  # Advance the candidate version.
        replacement["child"] = name  # Give the winner a visible identity.
        barrier.wait()  # Start both compare-and-set calls together.
        changed = store.compare_and_set_run(run_id, 0, replacement)  # Attempt the atomic replacement.
        with guard:  # Serialize the test result append.
            results.append(changed)  # Preserve success and failure.

    threads = [Thread(target=claim, args=(name,)) for name in ("first", "second")]  # Build both workers.
    for thread in threads:  # Start the race.
        thread.start()  # Run one claim.
    for thread in threads:  # Wait for both results.
        thread.join()  # Complete the race.
    assert sorted(results) == [False, True]  # Exactly one worker won.
    assert store.read_run(run_id)["record_version"] == 1  # The store advanced one version only.


class AqlStandIn:
    """Record one atomic AQL replacement and return its result rows."""

    def __init__(self, rows: list[dict[str, Any]]) -> None:
        """Store the rows that the query returns."""
        self.rows = rows  # Empty rows represent a failed comparison.
        self.calls: list[tuple[str, dict[str, Any]]] = []  # Keep the query and bind values.

    def execute(self, query: str, *, bind_vars: dict[str, Any]) -> list[dict[str, Any]]:
        """Record and answer one query."""
        self.calls.append((query, bind_vars))  # Preserve the exact atomic statement.
        return self.rows  # Return the configured compare result.


def test_document_run_store_uses_atomic_aql_and_no_fallback(monkeypatch: Any) -> None:
    """The production store reports success only when Arango replaces a row."""
    replacement = {"run_id": "run-a", "_key": "run-a", "record_version": 2}  # Build the next version.
    aql = AqlStandIn([replacement])  # Make the database accept the comparison.
    module = SimpleNamespace(  # Supply the production module fields used by the store.
        RUN_COLLECTION="upgrade_runs",  # Bind the real collection name.
        connect_database=lambda: SimpleNamespace(aql=aql),  # Return an online database.
    )
    monkeypatch.setattr(wiring, "load_module", lambda name: module)  # Keep the test offline.
    store = wiring.DocumentRunStore()  # Use the production compare-and-set method.
    assert store.compare_and_set_run("run-a", 1, replacement) is True  # Accept the matching row.
    query, bind_vars = aql.calls[0]  # Inspect the one database action.
    assert "run.record_version == @expected" in query  # Keep the version condition in Arango.
    assert "REPLACE run" in query  # Replace the complete record atomically.
    assert bind_vars["expected"] == 1  # Bind the caller's expected version.
    module.connect_database = lambda: None  # Model an unavailable production database.
    assert store.compare_and_set_run("run-a", 2, replacement) is False  # Never claim mirror success.
