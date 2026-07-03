"""Shared assertion helpers for tests/unit/test_arango_writer.py.

The underscore prefix on the filename tells pytest not to collect this
module (rule: python_files = ["test_*.py", "*_test.py"]) so nothing in
here is executed as a test — every entry point is a pure helper that a
sibling test module imports and calls.

Rationale: the arango_writer test suite performs the same handful of
schema-shape assertions dozens of times (edge-collection presence,
entity->vertex mapping, per-mapping vertex config, edge-column presence).
Repeating the raw ``assert`` chain in each test balloons cyclomatic
complexity (each ``assert`` node counts as one branch in McCabe scoring)
and duplicates the intent behind the check. Every helper below wraps a
whole chain into a single ``assert`` that keeps the failure diagnostic
readable while collapsing complexity back to CC=1 in callers.
"""

from __future__ import annotations  # WHY: postponed evaluation keeps forward refs cheap in a helper module

from dataclasses import dataclass  # WHY: frozen dataclass gives cheap immutable rows for assertion tables
from typing import Any  # WHY: mapping payloads from arango_writer are opaque dict-of-dict shapes


# ---------------------------------------------------------------------------
# Edge-definition assertions
# ---------------------------------------------------------------------------


def assert_edges_registered(expected_edges: set[str]) -> None:
    """Assert every edge name in ``expected_edges`` appears in EDGE_DEFINITIONS.

    Collapses N assertions ("assert 'X' in edge_names") into one subset
    check so the enclosing test stays at CC=1.
    """
    from src.db.arango_writer import EDGE_DEFINITIONS  # WHY: local import avoids import cycles in helper collection

    edge_names = {d["edge_collection"] for d in EDGE_DEFINITIONS}  # WHY: schema contract — every edge must register a name
    missing = expected_edges - edge_names  # WHY: set-diff produces a readable failure diagnostic
    assert not missing, f"Expected edges missing from EDGE_DEFINITIONS: {sorted(missing)}"  # WHY: single assert keeps CC low


def assert_edges_equal(expected_edges: set[str]) -> None:
    """Assert EDGE_DEFINITIONS names match ``expected_edges`` exactly.

    Used by the comprehensive edge-definition audit test; catches both
    missing edges and unexpected new edges that were not added to the spec.
    """
    from src.db.arango_writer import EDGE_DEFINITIONS  # WHY: local import isolates test-only dependency

    edge_names = {d["edge_collection"] for d in EDGE_DEFINITIONS}  # WHY: canonical shape — set of registered edge names
    assert edge_names == expected_edges, (  # WHY: single equality check keeps CC=1 in callers
        f"EDGE_DEFINITIONS mismatch: "
        f"missing={sorted(expected_edges - edge_names)}, "
        f"unexpected={sorted(edge_names - expected_edges)}"
    )


def assert_edge_to_vertex(edge_collection: str, vertex: str) -> None:
    """Assert the named edge lists ``vertex`` among its to_vertex_collections."""
    from src.db.arango_writer import EDGE_DEFINITIONS  # WHY: schema source of truth

    match = next(  # WHY: next() raises StopIteration if the edge does not exist — surfaces bad expectations
        d for d in EDGE_DEFINITIONS if d["edge_collection"] == edge_collection
    )
    assert vertex in match["to_vertex_collections"], (  # WHY: contract — edge must resolve to declared vertex
        f"Edge {edge_collection!r} does not target vertex {vertex!r}: "
        f"got {match['to_vertex_collections']!r}"
    )


# ---------------------------------------------------------------------------
# Entity-type -> vertex mapping assertions
# ---------------------------------------------------------------------------


def assert_entity_types_mapped(expected: dict[str, str]) -> None:
    """Assert every (entity_type -> vertex) pair in ``expected`` matches.

    Replaces long chains of ``assert ENTITY_TYPE_TO_VERTEX[key] == value``
    with a single dict-subset check.
    """
    from src.db.arango_writer import ENTITY_TYPE_TO_VERTEX  # WHY: schema map under test

    actual = {  # WHY: build a same-shape view so the diff-based failure below is precise
        key: ENTITY_TYPE_TO_VERTEX.get(key) for key in expected
    }
    assert actual == expected, (  # WHY: single equality assertion diagnoses all mismatches at once
        f"ENTITY_TYPE_TO_VERTEX mismatch: expected {expected!r}, got {actual!r}"
    )


# ---------------------------------------------------------------------------
# COLLECTION_VERTEX_MAP assertions
# ---------------------------------------------------------------------------


def _get_mapping(entity_type: str) -> dict[str, Any]:
    """Return the COLLECTION_VERTEX_MAP entry for ``entity_type`` (raises KeyError)."""
    from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: schema map under test

    return COLLECTION_VERTEX_MAP[entity_type]  # WHY: KeyError surfaces missing entries directly


def assert_vertex_config(entity_type: str, vertex: str, key_field: str) -> None:
    """Assert ``entity_type`` maps to ``vertex`` with the given ``key_field``."""
    mapping = _get_mapping(entity_type)  # WHY: single lookup keeps helper simple
    got = (mapping.get("vertex"), mapping.get("key_field"))  # WHY: tuple compare beats two asserts
    assert got == (vertex, key_field), (  # WHY: single equality on the (vertex, key_field) pair holds CC=1
        f"Mapping {entity_type!r} config mismatch: expected {(vertex, key_field)!r}, got {got!r}"
    )


def assert_edge_cols_include(entity_type: str, expected_cols: set[str]) -> None:
    """Assert every edge_col in ``expected_cols`` exists on the mapping's edges."""
    mapping = _get_mapping(entity_type)  # WHY: retrieve schema entry
    actual = {e["edge_col"] for e in mapping["edges"]}  # WHY: set for subset check
    missing = expected_cols - actual  # WHY: named diff makes failure message actionable
    assert not missing, (  # WHY: single assert keeps caller CC low
        f"Mapping {entity_type!r} missing edge cols: {sorted(missing)}; present: {sorted(actual)}"
    )


def assert_edge_fields(entity_type: str, edge_col: str, expected: dict[str, Any]) -> None:
    """Assert the named edge on ``entity_type`` matches all ``expected`` fields."""
    mapping = _get_mapping(entity_type)  # WHY: retrieve schema entry
    edge = next(  # WHY: next() surfaces missing edge as StopIteration — clearer than a bool
        e for e in mapping["edges"] if e["edge_col"] == edge_col
    )
    actual = {key: edge.get(key) for key in expected}  # WHY: project only the fields under test
    assert actual == expected, (  # WHY: single dict-equality assertion checks all fields at once
        f"Edge {edge_col!r} on {entity_type!r} field mismatch: "
        f"expected {expected!r}, got {actual!r}"
    )


def assert_ensure_target(entity_type: str, target: tuple[str, str]) -> None:
    """Assert ``target`` tuple is registered in the mapping's ensure_target_vertices."""
    mapping = _get_mapping(entity_type)  # WHY: retrieve schema entry
    targets = mapping.get("ensure_target_vertices", [])  # WHY: field is optional per schema
    assert target in targets, (  # WHY: single membership check keeps CC=1
        f"ensure_target_vertices on {entity_type!r} missing {target!r}: got {targets!r}"
    )


# ---------------------------------------------------------------------------
# Structured rows for parametrized / table-driven checks
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EdgeCase:
    """One row in an edge-definition assertion table.

    Bundling (name, from_vertex, to_vertex) into a frozen dataclass lets
    table-driven tests iterate the tuple without exposing internal shape.
    """

    name: str  # WHY: edge collection name that should appear in EDGE_DEFINITIONS
    from_vertex: str  # WHY: expected source vertex collection
    to_vertex: str  # WHY: expected target vertex collection


def assert_edge_case(case: EdgeCase) -> None:
    """Assert one EdgeCase row is honored by EDGE_DEFINITIONS."""
    from src.db.arango_writer import EDGE_DEFINITIONS  # WHY: schema under test

    match = next(  # WHY: StopIteration on missing edge is a clear failure signal
        d for d in EDGE_DEFINITIONS if d["edge_collection"] == case.name
    )
    got = (match["from_vertex_collections"], match["to_vertex_collections"])  # WHY: normalized tuple for compare
    expected = ([case.from_vertex], [case.to_vertex])  # WHY: EDGE_DEFINITIONS stores lists per side
    assert got == expected, (  # WHY: single tuple-equality assertion covers both sides at once
        f"Edge {case.name!r} vertex config: expected {expected!r}, got {got!r}"
    )
