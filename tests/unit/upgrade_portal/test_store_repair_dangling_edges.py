"""Unit tests for the one-time repair of dangling capture edges.

Why:
    Issue 2096 left a second defect. The old start invented a run for a
    run-less capture and wrote a ``capture_for_run`` edge to that invented run.
    The run document never existed, so the edge dangled and the history view
    walked into nothing. The repair scans every edge, reads the run each edge
    names, and removes only an edge whose run is absent. The repair leaves every
    capture and every live edge, and a second run removes nothing (D2, FR-098,
    FR-099, SC-017).

    The fake database below holds three named collections in memory, so the
    scan, the run read, and the edge removal all run offline. The query seam
    reads the live edge collection, so a removal shows up on the next scan and
    the repair proves idempotent.
"""

from __future__ import annotations

import logging  # WHY: One test reads the log records of each removal.
from collections.abc import Mapping
from typing import Any

import pytest

from src.upgrade_portal.capture import store

_LIVE_RUN = "run-live"  # WHY: The run that the live edge points at.
_MISSING_RUN = "run-missing"  # WHY: The run that the dangling edge names but no document holds.
_LIVE_CAPTURE = "cap-live-01"  # WHY: The capture of the live pair.
_DANGLING_CAPTURE = "cap-dangling-01"  # WHY: The capture whose run went missing.


class _FakeCollection:
    """One named collection of the fake database.

    Why:
        The repair reads a run by key and removes an edge by key. This
        collection answers both calls from an in-memory dictionary, so a test
        seeds a run, a capture, or an edge with no database.
    """

    def __init__(self) -> None:
        """Create one empty collection."""
        self.documents: dict[str, dict[str, Any]] = {}  # WHY: Holds every document of this collection by key.

    def get(self, key: str) -> dict[str, Any] | None:
        """Return the stored document for one key.

        Args:
            key: The document key.

        Returns:
            The stored document, or None when the key is absent.
        """
        return self.documents.get(key)  # WHY: An absent run reads as None, which marks a dangling edge.

    def delete(self, key: str) -> None:
        """Remove the document under one key.

        Args:
            key: The document key.
        """
        self.documents.pop(key, None)  # WHY: The scan of the next run then no longer sees this edge.


class _FakeAql:
    """The query seam that reads the live edge collection.

    Why:
        The repair scans the edge collection through one query. The seam reads
        the live collection every call, so a removal shows on the next scan.
    """

    def __init__(self, edges: _FakeCollection) -> None:
        """Bind the seam to the edge collection.

        Args:
            edges: The edge collection the scan reads.
        """
        self._edges = edges  # WHY: The scan returns the live edge documents.

    def execute(self, query: str, bind_vars: Mapping[str, Any] | None = None) -> list[Any]:
        """Return the edge documents for the scan query.

        Args:
            query: The query text. The seam checks it names the edge collection.
            bind_vars: The bind values. The scan passes none.

        Returns:
            One copy of each live edge document.
        """
        if store.EDGE_COLLECTION not in query:  # WHY: The repair scans the edge collection alone.
            return []
        return [dict(edge) for edge in self._edges.documents.values()]  # A copy stops a caller edit.


class _FakeDatabase:
    """A fake handle that holds the run, capture, and edge collections apart.

    Why:
        The single-collection fake of the store tests cannot separate a live
        run from a missing run. This handle keeps three named collections, so a
        test seeds a live edge and a dangling edge in one store.
    """

    def __init__(self) -> None:
        """Create a handle with three empty collections."""
        self.stores: dict[str, _FakeCollection] = {
            store.EDGE_COLLECTION: _FakeCollection(),  # WHY: The edges the repair scans.
            store.RUN_COLLECTION: _FakeCollection(),  # WHY: The runs the repair reads back.
            store.CAPTURE_COLLECTION: _FakeCollection(),  # WHY: The captures the repair must leave.
        }
        self.aql = _FakeAql(self.stores[store.EDGE_COLLECTION])  # WHY: The scan reads the live edge collection.

    def collection(self, name: str) -> _FakeCollection:
        """Return the named collection.

        Args:
            name: The collection name.

        Returns:
            The named fake collection.
        """
        return self.stores[name]  # WHY: The repair asks for the run collection and the edge collection by name.


def _seed_pair(database: _FakeDatabase, capture_key: str, run_key: str, run_present: bool) -> str:
    """Seed one capture, one edge, and maybe its run.

    Args:
        database: The fake handle to seed.
        capture_key: The capture key of the pair.
        run_key: The run key the edge names.
        run_present: True writes the run document, so the edge stays live.

    Returns:
        The edge key of the seeded pair.
    """
    capture = {"capture_id": capture_key, "run_id": run_key, "role": "pre"}  # The three fields the edge needs.
    edge = store.build_edge(capture)  # The edge that links the capture to its run.
    database.stores[store.CAPTURE_COLLECTION].documents[capture_key] = dict(capture)  # The capture the repair leaves.
    database.stores[store.EDGE_COLLECTION].documents[str(edge["_key"])] = dict(edge)  # The edge the repair scans.
    if run_present:  # A live pair holds its run, so the repair keeps the edge.
        database.stores[store.RUN_COLLECTION].documents[run_key] = {"_key": run_key, "run_id": run_key}
    return str(edge["_key"])  # The caller asserts on this key.


def _seeded_database() -> tuple[_FakeDatabase, str, str]:
    """Return a fake handle with one live pair and one dangling pair.

    Returns:
        The handle, the live edge key, and the dangling edge key.
    """
    database = _FakeDatabase()  # A fresh store for one test.
    live = _seed_pair(database, _LIVE_CAPTURE, _LIVE_RUN, True)  # The run exists, so this edge stays.
    dangling = _seed_pair(database, _DANGLING_CAPTURE, _MISSING_RUN, False)  # The run is absent, so this edge goes.
    return database, live, dangling


def test_repair_removes_the_dangling_edge_and_keeps_the_live_edge() -> None:
    """The repair removes the edge whose run is absent and keeps the live edge."""
    database, live, dangling = _seeded_database()  # One live pair and one dangling pair.
    report = store.repair_dangling_edges(database)  # The one-time repair runs.
    edges = database.stores[store.EDGE_COLLECTION].documents  # The edge collection after the repair.
    assert dangling not in edges  # The repair removed the dangling edge.
    assert live in edges  # The repair kept the live edge.
    assert report.removed == 1  # The report counts the one removal.
    assert report.scanned == 2  # The report counts both edges it read.


def test_repair_leaves_every_capture_document() -> None:
    """The repair removes no capture, so a run-less capture survives."""
    database, _live, _dangling = _seeded_database()  # One live pair and one dangling pair.
    store.repair_dangling_edges(database)  # The one-time repair runs.
    captures = database.stores[store.CAPTURE_COLLECTION].documents  # The capture collection after the repair.
    assert _LIVE_CAPTURE in captures  # The live capture survives.
    assert _DANGLING_CAPTURE in captures  # The run-less capture survives, so its data is never lost.


def test_repair_logs_each_removed_edge(caplog: pytest.LogCaptureFixture) -> None:
    """The repair logs each removal with the edge key and the missing run key."""
    database, _live, dangling = _seeded_database()  # One live pair and one dangling pair.
    with caplog.at_level(logging.INFO, logger=store.logger.name):  # WHY: The removal logs at the info level.
        store.repair_dangling_edges(database)  # The one-time repair runs.
    removals = [record.getMessage() for record in caplog.records if dangling in record.getMessage()]  # The removal log.
    assert removals  # The repair logged the removal.
    assert any(_MISSING_RUN in message for message in removals)  # The log names the missing run key.


def test_repair_removes_zero_on_a_second_run() -> None:
    """A second repair removes nothing, so the repair stays idempotent."""
    database, live, _dangling = _seeded_database()  # One live pair and one dangling pair.
    store.repair_dangling_edges(database)  # The first repair removes the dangling edge.
    report = store.repair_dangling_edges(database)  # The second repair reads a clean store.
    assert report.removed == 0  # The second run removes nothing.
    assert live in database.stores[store.EDGE_COLLECTION].documents  # The live edge still stands.
