"""Tests for CountExporter -- the count-endpoint family added under issue #1802."""

from __future__ import annotations

import importlib
import inspect
import pathlib
import re
from typing import Any
from unittest.mock import MagicMock, patch

import mistapi
import pytest

from src.export.count_exporter import _MSP_OPS, _ORG_OPS, _SITE_OPS, CountExporter, _CountOp
from src.refactors.endpoint_primary_key_strategies import ENDPOINT_PRIMARY_KEY_STRATEGIES

ALL_OPS = list(_ORG_OPS) + list(_SITE_OPS) + list(_MSP_OPS)


def _sdk_count_operations() -> set[str]:
    """Return every count operation the installed SDK defines."""
    root = pathlib.Path(mistapi.__file__).parent
    names: set[str] = set()
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8", errors="replace")
        names.update(m.group(1) for m in re.finditer(r"^def (count\w+)\s*\(", text, re.MULTILINE))
    return names


def test_table_covers_every_sdk_count_operation() -> None:
    """The table must not drift from the SDK in either direction."""
    assert {entry.operation for entry in ALL_OPS} == _sdk_count_operations()


@pytest.mark.parametrize("entry", ALL_OPS, ids=lambda entry: entry.operation)
def test_every_entry_resolves_to_a_callable(entry: _CountOp) -> None:
    """Each table row must name a real function in a real module."""
    resolved = CountExporter._resolve(entry)
    assert resolved is not None
    assert inspect.isfunction(resolved)


@pytest.mark.parametrize("entry", ALL_OPS, ids=lambda entry: entry.operation)
def test_every_callable_takes_session_and_identifier(entry: _CountOp) -> None:
    """``_run`` passes exactly two positional arguments, so the SDK must accept them."""
    target = getattr(importlib.import_module(entry.module), entry.operation)
    assert len(inspect.signature(target).parameters) >= 2


def test_every_operation_has_a_primary_key_strategy() -> None:
    """A count response has no natural identifier, so each needs a registered strategy."""
    missing = [e.operation for e in ALL_OPS if e.operation not in ENDPOINT_PRIMARY_KEY_STRATEGIES]
    assert missing == []


def test_all_strategies_are_auto_increment() -> None:
    """Count distributions carry no stable key, so every strategy must auto-increment."""
    kinds = {ENDPOINT_PRIMARY_KEY_STRATEGIES[e.operation]["type"] for e in ALL_OPS}
    assert kinds == {"auto_increment_with_unique"}


def test_resolve_returns_none_for_a_missing_module() -> None:
    """A bad module path must be reported, not raised, so the menu survives."""
    assert CountExporter._resolve(_CountOp("countNothing", "mistapi.api.v1.not_a_module")) is None


def test_resolve_returns_none_for_a_missing_operation() -> None:
    """A real module without the named operation must also return None."""
    assert CountExporter._resolve(_CountOp("countNothing", "mistapi.api.v1.orgs.alarms")) is None


def _fake_mist_helper() -> Any:
    """Build a MistHelper stand-in that records what the exporter wrote."""
    module = MagicMock()
    module.apisession = MagicMock()
    return module


def test_choose_rejects_a_non_numeric_answer() -> None:
    """A non-numeric answer aborts rather than indexing the table."""
    fake = _fake_mist_helper()
    fake.InputUtils.safe_input.return_value = "abc"
    with patch.object(importlib, "import_module", return_value=fake):
        assert CountExporter._choose(_ORG_OPS, "org") is None


def test_choose_rejects_an_out_of_range_answer() -> None:
    """A number past the end of the table aborts rather than raising IndexError."""
    fake = _fake_mist_helper()
    fake.InputUtils.safe_input.return_value = str(len(_ORG_OPS) + 1)
    with patch.object(importlib, "import_module", return_value=fake):
        assert CountExporter._choose(_ORG_OPS, "org") is None


def test_choose_returns_the_selected_operation() -> None:
    """A valid one-based selection maps to the matching zero-based table row."""
    fake = _fake_mist_helper()
    fake.InputUtils.safe_input.return_value = "1"
    with patch.object(importlib, "import_module", return_value=fake):
        assert CountExporter._choose(_ORG_OPS, "org") == _ORG_OPS[0]


def test_persist_skips_the_write_when_there_are_no_rows() -> None:
    """An empty count response is legitimate and must not create a file."""
    fake = _fake_mist_helper()
    with patch.object(importlib, "import_module", return_value=fake):
        CountExporter._persist([], "Empty.csv", "countOrgAlarms")
    fake.DataExporter.write_with_format_selection.assert_not_called()


def test_persist_routes_the_operation_name_to_the_exporter() -> None:
    """The operationId selects the primary key strategy, so it must reach the writer."""
    fake = _fake_mist_helper()
    with patch.object(importlib, "import_module", return_value=fake):
        CountExporter._persist([{"count": 3}], "Counts.csv", "countOrgAlarms")
    _, kwargs = fake.DataExporter.write_with_format_selection.call_args
    assert kwargs["api_function_name"] == "countOrgAlarms"
