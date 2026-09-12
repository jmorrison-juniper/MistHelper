"""Tests for the stage two endpoint family exporter."""

from __future__ import annotations

import importlib
import inspect
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.export.endpoint_family_exporter import (
    _MSP_DETAIL_OPS,
    _ORG_DETAIL_OPS,
    _OTHER_DETAIL_OPS,
    _SITE_DETAIL_OPS,
    _SITE_MAP_OPS,
    _SITE_SLE_OPS,
    ALL_STAGE_TWO_ENDPOINT_OPS,
    EndpointFamilyExporter,
    _EndpointFamilyOp,
)
from src.refactors.endpoint_primary_key_strategies import ENDPOINT_PRIMARY_KEY_STRATEGIES

EXPECTED_BUCKET_COUNTS = {
    "SITE_SLE": 17,
    "SITE_MAP": 7,
    "SITE_DETAIL": 33,
    "ORG_DETAIL": 61,
    "MSP_DETAIL": 10,
    "OTHER_DETAIL": 6,
}
GROUPS = {
    "SITE_SLE": _SITE_SLE_OPS,
    "SITE_MAP": _SITE_MAP_OPS,
    "SITE_DETAIL": _SITE_DETAIL_OPS,
    "ORG_DETAIL": _ORG_DETAIL_OPS,
    "MSP_DETAIL": _MSP_DETAIL_OPS,
    "OTHER_DETAIL": _OTHER_DETAIL_OPS,
}


def _fake_mist_helper() -> Any:
    """Build a MistHelper stand-in that records exporter calls."""
    module = MagicMock()
    module.apisession = MagicMock()
    module.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-one"
    module.SiteDeviceExporter._resolve_site_for_stats.return_value = ("site-one", "site name")
    return module


def _expected_value(param: str) -> str:
    """Return the synthetic value that the prompt test supplies."""
    if param == "org_id":
        return "org-one"
    if param == "site_id":
        return "site-one"
    if param == "msp_id":
        return "msp-one"
    return f"{param}-value"


def _safe_input(prompt: str, allow_empty: bool, context: str) -> str:
    """Return a value that encodes the final context token."""
    return f"{context.rsplit('.', 1)[-1]}-value"


def test_group_counts_match_discovery() -> None:
    """The shipped tables must match the measured stage-two groups."""
    assert {name: len(entries) for name, entries in GROUPS.items()} == EXPECTED_BUCKET_COUNTS
    assert len(ALL_STAGE_TWO_ENDPOINT_OPS) == 134


def test_operation_table_has_no_duplicate_operation() -> None:
    """Duplicate operation rows make the prompt ambiguous."""
    names = [entry.operation for entry in ALL_STAGE_TWO_ENDPOINT_OPS]
    assert len(names) == len(set(names))


def test_phantom_and_active_endpoint_entries_do_not_ship() -> None:
    """Known phantom and active endpoints must not ship in the read-only family."""
    names = {entry.operation for entry in ALL_STAGE_TWO_ENDPOINT_OPS}
    assert "searchOrgClientFingerprints" not in names
    assert "optimizeInstallerRrm" not in names


@pytest.mark.parametrize("entry", ALL_STAGE_TWO_ENDPOINT_OPS, ids=lambda entry: entry.operation)
def test_every_entry_resolves_to_a_callable(entry: _EndpointFamilyOp) -> None:
    """Each table row must name a real function in a real SDK module."""
    resolved = EndpointFamilyExporter._resolve(entry)
    assert resolved is not None
    assert inspect.isfunction(resolved)


@pytest.mark.parametrize("entry", ALL_STAGE_TWO_ENDPOINT_OPS, ids=lambda entry: entry.operation)
def test_required_identifier_order_matches_sdk_signature(entry: _EndpointFamilyOp) -> None:
    """Each table row must preserve the SDK required-identifier order."""
    target = getattr(importlib.import_module(entry.module), entry.operation)
    required = [
        param.name
        for param in list(inspect.signature(target).parameters.values())[1:]
        if param.default is inspect._empty
    ]
    assert tuple(required) == entry.required


def test_every_operation_has_a_primary_key_strategy() -> None:
    """Each exported endpoint must pass a known strategy to the data writer."""
    missing = [
        entry.operation
        for entry in ALL_STAGE_TWO_ENDPOINT_OPS
        if entry.operation not in ENDPOINT_PRIMARY_KEY_STRATEGIES
    ]
    assert missing == []


@pytest.mark.parametrize("entry", ALL_STAGE_TWO_ENDPOINT_OPS, ids=lambda entry: entry.operation)
def test_prompt_sequence_preserves_identifier_order(entry: _EndpointFamilyOp) -> None:
    """The collected values must match the identifier tuple order."""
    fake = _fake_mist_helper()
    fake.InputUtils.safe_input.side_effect = _safe_input
    with (
        patch.object(EndpointFamilyExporter, "_mist_helper", return_value=fake),
        patch("src.export.endpoint_family_exporter.InputUtils.prompt_msp_id", return_value="msp-one"),
    ):
        result = EndpointFamilyExporter._collect_arguments(entry)
    assert result is not None
    assert result.values == tuple(_expected_value(param) for param in entry.required)


def test_choose_rejects_a_non_numeric_answer() -> None:
    """A non-number answer must return to the menu safely."""
    fake = _fake_mist_helper()
    fake.InputUtils.safe_input.return_value = "abc"
    with patch.object(EndpointFamilyExporter, "_mist_helper", return_value=fake):
        assert EndpointFamilyExporter._choose(_ORG_DETAIL_OPS, "org detail") is None


def test_choose_rejects_an_out_of_range_answer() -> None:
    """An out-of-range answer must not index the table."""
    fake = _fake_mist_helper()
    fake.InputUtils.safe_input.return_value = str(len(_ORG_DETAIL_OPS) + 1)
    with patch.object(EndpointFamilyExporter, "_mist_helper", return_value=fake):
        assert EndpointFamilyExporter._choose(_ORG_DETAIL_OPS, "org detail") is None


def test_persist_skips_empty_rows() -> None:
    """An empty endpoint response must not create an export file."""
    fake = _fake_mist_helper()
    with patch.object(EndpointFamilyExporter, "_mist_helper", return_value=fake):
        EndpointFamilyExporter._persist([], "empty.csv", "getOrgSso")
    fake.DataExporter.write_with_format_selection.assert_not_called()


def test_persist_wraps_single_object_response() -> None:
    """A single JSON object response must export as one row."""
    fake = _fake_mist_helper()
    with patch.object(EndpointFamilyExporter, "_mist_helper", return_value=fake):
        EndpointFamilyExporter._persist({"id": "one"}, "one.csv", "getOrgSso")
    args, kwargs = fake.DataExporter.write_with_format_selection.call_args
    assert args[0] == [{"id": "one"}]
    assert kwargs["api_function_name"] == "getOrgSso"


def test_resolve_returns_none_for_a_missing_module() -> None:
    """A bad SDK module path must not crash the menu."""
    bad = _EndpointFamilyOp("listNothing", "mistapi.api.v1.not_a_module", ("org_id", "item_id"), (1,))
    assert EndpointFamilyExporter._resolve(bad) is None


def test_run_uses_identifiers_in_order() -> None:
    """Endpoint calls must receive identifiers in table order."""
    fake = _fake_mist_helper()
    callable_obj = MagicMock(return_value=MagicMock())
    entry = _SITE_MAP_OPS[0]
    with (
        patch.object(EndpointFamilyExporter, "_mist_helper", return_value=fake),
        patch.object(EndpointFamilyExporter, "_resolve", return_value=callable_obj),
        patch.object(
            EndpointFamilyExporter,
            "_collect_arguments",
            return_value=MagicMock(values=("site-one", "map-one"), label="target"),
        ),
        patch("src.export.endpoint_family_exporter.mistapi.get_all", return_value=[]),
    ):
        EndpointFamilyExporter._run(entry)
    callable_obj.assert_called_once_with(fake.apisession, "site-one", "map-one")


def test_run_reports_sdk_errors_without_raising() -> None:
    """The menu must survive an SDK exception."""
    fake = _fake_mist_helper()
    callable_obj = MagicMock(side_effect=RuntimeError("boom"))
    with (
        patch.object(EndpointFamilyExporter, "_mist_helper", return_value=fake),
        patch.object(EndpointFamilyExporter, "_resolve", return_value=callable_obj),
        patch.object(
            EndpointFamilyExporter,
            "_collect_arguments",
            return_value=MagicMock(values=("org-one", "sso-one"), label="target"),
        ),
    ):
        EndpointFamilyExporter._run(_ORG_DETAIL_OPS[0])
    callable_obj.assert_called_once_with(fake.apisession, "org-one", "sso-one")
