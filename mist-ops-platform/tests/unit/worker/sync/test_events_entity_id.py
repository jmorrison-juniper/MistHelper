"""Tests for the audit event sync fallback path.

Why:
    ``src/worker/sync/events.py`` builds an ``AuditRecord`` for every audit event
    that the Mist API returns. ``_extract_entity_id`` falls back to a random UUID
    when the event carries no usable identifier. Issue #1975 reports that the
    fallback called ``uuid4`` without importing it, so the documented path raised
    ``NameError`` on every run. These tests hold that path open.
"""

from __future__ import annotations

import ast
import builtins
import inspect
from pathlib import Path
from uuid import UUID

import pytest

from src.worker.sync.events import EventSyncService

# WHY: the two keys that the production code reads before it falls back.
IDENTIFIER_KEYS = ("obj_id", "id")


class TestExtractEntityIdFallback:
    """Cover the branch that returns a random UUID."""

    @pytest.mark.parametrize(
        "event",
        [
            {},  # WHY: the event carries neither key, so the guard is falsy.
            {"obj_id": None, "id": None},  # WHY: both keys present and empty.
            {"obj_id": "", "id": ""},  # WHY: an empty string is falsy too.
        ],
    )
    def test_missing_identifier_returns_a_uuid(self, event: dict[str, object]) -> None:
        """An event with no identifier must return a UUID, not raise."""
        # WHY: issue #1975 recorded a NameError here, so the call itself is the test.
        result = EventSyncService._extract_entity_id(event)
        assert isinstance(result, UUID)  # WHY: the caller stores this as a UUID column.

    def test_unparsable_identifier_returns_a_uuid(self) -> None:
        """A value that is not a UUID must fall through to the random branch."""
        # WHY: UUID(str(raw)) raises ValueError here, so the except branch runs.
        result = EventSyncService._extract_entity_id({"obj_id": "not-a-uuid"})
        assert isinstance(result, UUID)  # WHY: the fallback must still produce a UUID.

    def test_each_fallback_returns_a_new_value(self) -> None:
        """Two fallback calls must not share one identifier."""
        # WHY: a shared value would collide on the audit table primary key.
        first = EventSyncService._extract_entity_id({})
        second = EventSyncService._extract_entity_id({})
        assert first != second

    def test_a_valid_identifier_is_preserved(self) -> None:
        """A well formed UUID must pass through unchanged."""
        # WHY: the fallback must not replace a real identifier from Mist.
        known = "12345678-1234-5678-1234-567812345678"
        assert EventSyncService._extract_entity_id({"obj_id": known}) == UUID(known)

    @pytest.mark.parametrize("key", IDENTIFIER_KEYS)
    def test_either_key_supplies_the_identifier(self, key: str) -> None:
        """The production code reads obj_id first and id second."""
        # WHY: a regression that drops one key would lose the real identifier.
        known = "abcdefab-1234-5678-1234-567812345678"
        assert EventSyncService._extract_entity_id({key: known}) == UUID(known)


class TestEventsModuleNamespace:
    """Guard the import that issue #1975 restored."""

    def test_every_called_name_is_bound(self) -> None:
        """No call in the module may reference a name that the module never binds."""
        # WHY: the original defect compiled cleanly and failed only at run time.
        # A namespace check catches the whole class, not the one known symbol.
        source = Path(inspect.getfile(EventSyncService)).read_text(encoding="utf-8")
        tree = ast.parse(source)
        bound = self._collect_bound_names(tree)
        called = {
            node.func.id for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        assert called <= bound, f"unbound names called: {sorted(called - bound)}"

    @staticmethod
    def _collect_bound_names(tree: ast.Module) -> set[str]:
        """Return every name the module binds, plus the builtins."""
        bound = set(dir(builtins))  # WHY: a builtin needs no import to be callable.
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                bound.update(alias.asname or alias.name for alias in node.names)
            elif isinstance(node, ast.Import):
                bound.update((alias.asname or alias.name).split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
                bound.add(node.name)
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                bound.add(node.id)
            elif isinstance(node, ast.arg):
                bound.add(node.arg)
        return bound
