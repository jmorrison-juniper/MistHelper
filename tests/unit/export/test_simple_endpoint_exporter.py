"""Tests for the simple endpoint exporter added for issue #1807."""

from __future__ import annotations

import importlib
import inspect
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.export.simple_endpoint_exporter import (
    _MSP_OPS,
    _NONE_OPS,
    _ORG_OPS,
    _SITE_OPS,
    SimpleEndpointExporter,
    _SimpleEndpointOp,
)
from src.refactors.endpoint_primary_key_strategies import ENDPOINT_PRIMARY_KEY_STRATEGIES

ALL_OPS = list(_NONE_OPS) + list(_ORG_OPS) + list(_SITE_OPS) + list(_MSP_OPS)


def _fake_mist_helper() -> Any:
    """Build a MistHelper stand-in that records exporter calls."""
    module = MagicMock()
    module.apisession = MagicMock()
    return module


def test_scope_table_counts_match_discovery() -> None:
    """The shipped tables must match the measured unique stage-one counts."""
    assert len(_NONE_OPS) == 29
    assert len(_ORG_OPS) == 55
    assert len(_SITE_OPS) == 57
    assert len(_MSP_OPS) == 10


def test_operation_table_has_no_duplicate_operation() -> None:
    """Duplicate operation rows make the prompt ambiguous."""
    names = [entry.operation for entry in ALL_OPS]
    assert len(names) == len(set(names))


def test_phantom_endpoint_is_not_in_the_table() -> None:
    """The known phantom from issue 1369 must not ship as a callable row."""
    assert "searchOrgClientFingerprints" not in {entry.operation for entry in ALL_OPS}


@pytest.mark.parametrize("entry", ALL_OPS, ids=lambda entry: entry.operation)
def test_every_entry_resolves_to_a_callable(entry: _SimpleEndpointOp) -> None:
    """Each table row must name a real function in a real SDK module."""
    resolved = SimpleEndpointExporter._resolve(entry)
    assert resolved is not None
    assert inspect.isfunction(resolved)


@pytest.mark.parametrize("entry", _NONE_OPS, ids=lambda entry: entry.operation)
def test_no_identifier_entries_take_only_session(entry: _SimpleEndpointOp) -> None:
    """No-identifier rows must take no required value after the session."""
    target = getattr(importlib.import_module(entry.module), entry.operation)
    required = [
        param.name
        for param in list(inspect.signature(target).parameters.values())[1:]
        if param.default is inspect._empty
    ]
    assert required == []


@pytest.mark.parametrize(
    ("entries", "required_name"),
    [(_ORG_OPS, "org_id"), (_SITE_OPS, "site_id"), (_MSP_OPS, "msp_id")],
)
def test_scoped_entries_take_one_required_identifier(
    entries: tuple[_SimpleEndpointOp, ...], required_name: str
) -> None:
    """Scoped rows must take exactly one required identifier after the session."""
    for entry in entries:
        target = getattr(importlib.import_module(entry.module), entry.operation)
        required = [
            param.name
            for param in list(inspect.signature(target).parameters.values())[1:]
            if param.default is inspect._empty
        ]
        assert required == [required_name]


def test_every_operation_has_a_primary_key_strategy() -> None:
    """Each exported endpoint must pass a known strategy to the data writer."""
    missing = [entry.operation for entry in ALL_OPS if entry.operation not in ENDPOINT_PRIMARY_KEY_STRATEGIES]
    assert missing == []


def test_choose_rejects_a_non_numeric_answer() -> None:
    """A non-number answer must return to the menu safely."""
    fake = _fake_mist_helper()
    fake.InputUtils.safe_input.return_value = "abc"
    with patch.object(importlib, "import_module", return_value=fake):
        assert SimpleEndpointExporter._choose(_ORG_OPS, "org") is None


def test_choose_rejects_an_out_of_range_answer() -> None:
    """An out-of-range answer must not index the table."""
    fake = _fake_mist_helper()
    fake.InputUtils.safe_input.return_value = str(len(_ORG_OPS) + 1)
    with patch.object(importlib, "import_module", return_value=fake):
        assert SimpleEndpointExporter._choose(_ORG_OPS, "org") is None


def test_choose_returns_the_selected_operation() -> None:
    """A valid selection must return the matching table row."""
    fake = _fake_mist_helper()
    fake.InputUtils.safe_input.return_value = "1"
    with patch.object(importlib, "import_module", return_value=fake):
        assert SimpleEndpointExporter._choose(_ORG_OPS, "org") == _ORG_OPS[0]


def test_persist_skips_empty_rows() -> None:
    """An empty endpoint response must not create an export file."""
    fake = _fake_mist_helper()
    with patch.object(importlib, "import_module", return_value=fake):
        SimpleEndpointExporter._persist([], "empty.csv", "listAlarmDefinitions")
    fake.DataExporter.write_with_format_selection.assert_not_called()


def test_persist_wraps_single_object_response() -> None:
    """A single JSON object response must export as one row."""
    fake = _fake_mist_helper()
    with patch.object(importlib, "import_module", return_value=fake):
        SimpleEndpointExporter._persist({"id": "one"}, "one.csv", "getSelf")
    args, kwargs = fake.DataExporter.write_with_format_selection.call_args
    assert args[0] == [{"id": "one"}]
    assert kwargs["api_function_name"] == "getSelf"


def test_resolve_returns_none_for_a_missing_module() -> None:
    """A bad SDK module path must not crash the menu."""
    bad = _SimpleEndpointOp("listNothing", "mistapi.api.v1.not_a_module")
    assert SimpleEndpointExporter._resolve(bad) is None


def test_run_uses_session_only_for_global_operation() -> None:
    """Global endpoints must not receive an identifier argument."""
    fake = _fake_mist_helper()
    callable_obj = MagicMock(return_value=MagicMock())
    with (
        patch.object(importlib, "import_module", return_value=fake),
        patch.object(SimpleEndpointExporter, "_resolve", return_value=callable_obj),
        patch("src.export.simple_endpoint_exporter.mistapi.get_all", return_value=[]),
    ):
        SimpleEndpointExporter._run(_NONE_OPS[0], None, "global")
    callable_obj.assert_called_once_with(fake.apisession)


def test_run_uses_identifier_for_scoped_operation() -> None:
    """Scoped endpoints must receive the selected identifier argument."""
    fake = _fake_mist_helper()
    callable_obj = MagicMock(return_value=MagicMock())
    with (
        patch.object(importlib, "import_module", return_value=fake),
        patch.object(SimpleEndpointExporter, "_resolve", return_value=callable_obj),
        patch("src.export.simple_endpoint_exporter.mistapi.get_all", return_value=[]),
    ):
        SimpleEndpointExporter._run(_ORG_OPS[0], "org-one", "org-one")
    callable_obj.assert_called_once_with(fake.apisession, "org-one")
