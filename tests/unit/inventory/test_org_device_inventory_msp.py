"""Unit tests for extracted MSP orchestration module."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any  # WHY: type mixed-value dicts for mypy strict.
from unittest.mock import MagicMock

import pytest

from src.inventory.org_device_inventory_msp import (
    OrgDeviceInventoryMSPOrchestrator,
    _flatten_model_rows,
    _flatten_version_rows,
    _normalise_orgs_payload,
    _OrgProcessedResult,
    _sanitize_msp_name,
    _to_org_result,
    configure_org_device_inventory_msp_dependencies,
)


def _configure_msp(*, privileges: list[dict] | None = None, safe_input_return: str = "1") -> MagicMock:
    """Configure MSP module dependencies and return exporter mock."""
    exporter = MagicMock()  # WHY: capture writer calls for assertions
    configure_org_device_inventory_msp_dependencies(
        apisession_dependency=object(),  # WHY: opaque non-None object satisfies apisession check
        input_utils=SimpleNamespace(safe_input=MagicMock(return_value=safe_input_return)),  # WHY: stub input
        data_exporter=SimpleNamespace(write_with_format_selection=exporter),  # WHY: capture exporter side effect
        msp_privileges_value=privileges or [],  # WHY: default to empty MSP privilege list
    )
    return exporter


def test_resolve_active_msp_returns_none_without_privileges() -> None:
    """MSP resolver should return None when MSP privileges are not available."""
    _configure_msp(privileges=[])
    assert OrgDeviceInventoryMSPOrchestrator._resolve_active_msp() is None


def test_resolve_active_msp_autoselects_single_privilege() -> None:
    """MSP resolver should auto-select when exactly one MSP privilege exists."""
    _configure_msp(privileges=[{"msp_id": "m1", "msp_name": "One MSP", "role": "admin"}])
    selected = OrgDeviceInventoryMSPOrchestrator._resolve_active_msp()
    assert selected is not None
    assert selected["msp_id"] == "m1"


def test_resolve_active_msp_prompts_when_multiple_privileges() -> None:
    """MSP resolver should call prompt helper when multiple privileges exist."""
    privs = [
        {"msp_id": "m1", "msp_name": "One", "role": "admin"},
        {"msp_id": "m2", "msp_name": "Two", "role": "admin"},
    ]
    _configure_msp(privileges=privs, safe_input_return="2")
    selected = OrgDeviceInventoryMSPOrchestrator._resolve_active_msp()
    assert selected is not None
    assert selected["msp_id"] == "m2"


def test_resolve_active_msp_returns_none_on_bad_input() -> None:
    """MSP resolver should return None when operator provides out-of-range selection."""
    privs = [
        {"msp_id": "m1", "msp_name": "One", "role": "admin"},
        {"msp_id": "m2", "msp_name": "Two", "role": "admin"},
    ]
    _configure_msp(privileges=privs, safe_input_return="99")
    assert OrgDeviceInventoryMSPOrchestrator._resolve_active_msp() is None


def test_resolve_active_msp_returns_none_on_parse_error() -> None:
    """MSP resolver should return None when operator input cannot be parsed."""
    privs = [
        {"msp_id": "m1", "msp_name": "One", "role": "admin"},
        {"msp_id": "m2", "msp_name": "Two", "role": "admin"},
    ]
    _configure_msp(privileges=privs, safe_input_return="not-a-number")
    assert OrgDeviceInventoryMSPOrchestrator._resolve_active_msp() is None


def test_dispatch_routes_to_selected_mode() -> None:
    """Dispatcher should call the correct callback for mode selections."""
    _configure_msp(privileges=[{"msp_id": "m1", "msp_name": "One MSP", "role": "admin"}], safe_input_return="3")
    single_mock = MagicMock()
    select_mock = MagicMock()
    batch_mock = MagicMock()

    OrgDeviceInventoryMSPOrchestrator.dispatch(
        single_org_fn=single_mock,
        select_org_fn=select_mock,
        batch_fn=batch_mock,
    )

    batch_mock.assert_called_once()
    single_mock.assert_not_called()
    select_mock.assert_not_called()


def test_dispatch_mode_2_calls_select() -> None:
    """Dispatcher mode 2 should route to select_org_fn."""
    _configure_msp(privileges=[{"msp_id": "m1", "msp_name": "One MSP", "role": "admin"}], safe_input_return="2")
    single_mock, select_mock, batch_mock = MagicMock(), MagicMock(), MagicMock()
    OrgDeviceInventoryMSPOrchestrator.dispatch(
        single_org_fn=single_mock, select_org_fn=select_mock, batch_fn=batch_mock
    )
    select_mock.assert_called_once()
    single_mock.assert_not_called()
    batch_mock.assert_not_called()


def test_dispatch_mode_1_calls_single() -> None:
    """Dispatcher mode 1 or unknown should route to single_org_fn."""
    _configure_msp(privileges=[{"msp_id": "m1", "msp_name": "One MSP", "role": "admin"}], safe_input_return="1")
    single_mock, select_mock, batch_mock = MagicMock(), MagicMock(), MagicMock()
    OrgDeviceInventoryMSPOrchestrator.dispatch(
        single_org_fn=single_mock, select_org_fn=select_mock, batch_fn=batch_mock
    )
    single_mock.assert_called_once()
    select_mock.assert_not_called()
    batch_mock.assert_not_called()


def test_dispatch_without_privileges_calls_single_directly() -> None:
    """Dispatcher without any MSP privileges should skip the menu and call single_org_fn."""
    _configure_msp(privileges=[])
    single_mock, select_mock, batch_mock = MagicMock(), MagicMock(), MagicMock()
    OrgDeviceInventoryMSPOrchestrator.dispatch(
        single_org_fn=single_mock, select_org_fn=select_mock, batch_fn=batch_mock
    )
    single_mock.assert_called_once()
    select_mock.assert_not_called()
    batch_mock.assert_not_called()


def test_execute_msp_builds_combined_reports_for_multiple_orgs(monkeypatch: pytest.MonkeyPatch) -> None:
    """MSP batch should build combined reports when at least two orgs are processed."""
    _configure_msp(privileges=[{"msp_id": "m1", "msp_name": "MSP Name", "role": "admin"}])
    monkeypatch.setattr(
        OrgDeviceInventoryMSPOrchestrator,
        "_resolve_active_msp",
        staticmethod(lambda: {"msp_id": "m1", "msp_name": "MSP Name", "role": "admin"}),
    )
    monkeypatch.setattr(
        OrgDeviceInventoryMSPOrchestrator,
        "_fetch_org_list",
        staticmethod(lambda active_msp: [{"id": "org-1", "name": "Org One"}, {"id": "org-2", "name": "Org Two"}]),
    )
    combined_mock = MagicMock()
    monkeypatch.setattr(OrgDeviceInventoryMSPOrchestrator, "_build_combined_reports", staticmethod(combined_mock))

    def _run_for_org(org_id: str) -> tuple[list[dict], list[dict], list[dict], str]:
        return (
            [{"device_type": "ap", "model": "A", "count": 1}],
            [{"device_type": "ap", "version": "1", "count": 1}],
            [{"device_type": "ap", "model": "A", "version": "1", "count": 1}],
            org_id,
        )

    OrgDeviceInventoryMSPOrchestrator.execute_msp(_run_for_org)

    combined_mock.assert_called_once()


def test_execute_msp_skips_combined_reports_for_single_org(monkeypatch: pytest.MonkeyPatch) -> None:
    """MSP batch should skip combined reports when fewer than 2 orgs processed."""
    _configure_msp(privileges=[{"msp_id": "m1", "msp_name": "One", "role": "admin"}])
    monkeypatch.setattr(
        OrgDeviceInventoryMSPOrchestrator,
        "_resolve_active_msp",
        staticmethod(lambda: {"msp_id": "m1", "msp_name": "One", "role": "admin"}),
    )
    monkeypatch.setattr(
        OrgDeviceInventoryMSPOrchestrator,
        "_fetch_org_list",
        staticmethod(lambda active_msp: [{"id": "org-1", "name": "Solo"}]),
    )
    combined_mock = MagicMock()
    monkeypatch.setattr(OrgDeviceInventoryMSPOrchestrator, "_build_combined_reports", staticmethod(combined_mock))

    def _run(org_id: str) -> tuple[list[dict], list[dict], list[dict], str]:
        return ([], [], [], org_id)

    OrgDeviceInventoryMSPOrchestrator.execute_msp(_run)
    combined_mock.assert_not_called()


def test_execute_msp_short_circuits_when_no_msp(monkeypatch: pytest.MonkeyPatch) -> None:
    """execute_msp should return early when resolve_active_msp yields None."""
    _configure_msp(privileges=[])
    monkeypatch.setattr(OrgDeviceInventoryMSPOrchestrator, "_resolve_active_msp", staticmethod(lambda: None))
    OrgDeviceInventoryMSPOrchestrator.execute_msp(lambda org_id: ([], [], [], org_id))


def test_execute_msp_short_circuits_when_no_orgs(monkeypatch: pytest.MonkeyPatch) -> None:
    """execute_msp should print no-orgs message and return when org list is empty."""
    _configure_msp(privileges=[{"msp_id": "m1", "msp_name": "M", "role": "admin"}])
    monkeypatch.setattr(
        OrgDeviceInventoryMSPOrchestrator,
        "_resolve_active_msp",
        staticmethod(lambda: {"msp_id": "m1", "msp_name": "M", "role": "admin"}),
    )
    monkeypatch.setattr(OrgDeviceInventoryMSPOrchestrator, "_fetch_org_list", staticmethod(lambda active_msp: []))
    OrgDeviceInventoryMSPOrchestrator.execute_msp(lambda org_id: ([], [], [], org_id))


def test_normalise_orgs_payload_returns_list_when_list() -> None:
    """List payloads should pass through unchanged."""
    payload = [{"id": "o1"}, {"id": "o2"}]
    assert _normalise_orgs_payload(payload) == payload


def test_normalise_orgs_payload_wraps_dict() -> None:
    """Single dict payload should be wrapped in a one-element list."""
    payload = {"id": "solo"}
    assert _normalise_orgs_payload(payload) == [payload]


def test_normalise_orgs_payload_returns_empty_for_none() -> None:
    """None/falsy payloads should normalise to an empty list."""
    assert _normalise_orgs_payload(None) == []
    assert _normalise_orgs_payload(0) == []


def test_sanitize_msp_name_replaces_non_alnum() -> None:
    """Special characters outside alnum/-/_ should be replaced with underscore."""
    assert _sanitize_msp_name("Acme Corp / West") == "Acme_Corp___West"


def test_sanitize_msp_name_keeps_allowed_chars() -> None:
    """Alphanumeric plus dash/underscore should pass through unchanged."""
    assert _sanitize_msp_name("Acme-Corp_2024") == "Acme-Corp_2024"


def test_flatten_model_rows_produces_tagged_rows() -> None:
    """Model rows should be flattened with Org tag column added."""
    collected = [
        _OrgProcessedResult(
            safe_org="OrgA",
            model_rows=[{"device_type": "ap", "model": "M1", "count": 3}],
            version_rows=[],
            ver_per_model=[],
        )
    ]
    flat = _flatten_model_rows(collected)
    assert flat == [{"Org": "OrgA", "Device Type": "ap", "Model": "M1", "Count": 3}]


def test_flatten_model_rows_uses_defaults_for_missing_fields() -> None:
    """Missing model/count fields should default to '' and 0 respectively."""
    collected = [
        _OrgProcessedResult(
            safe_org="OrgB",
            model_rows=[{"device_type": "switch"}],
            version_rows=[],
            ver_per_model=[],
        )
    ]
    flat = _flatten_model_rows(collected)
    assert flat == [{"Org": "OrgB", "Device Type": "switch", "Model": "", "Count": 0}]


def test_flatten_version_rows_produces_tagged_rows() -> None:
    """Version rows should be flattened with Org tag column added."""
    collected = [
        _OrgProcessedResult(
            safe_org="OrgA",
            model_rows=[],
            version_rows=[{"device_type": "ap", "version": "1.0", "count": 2}],
            ver_per_model=[],
        )
    ]
    flat = _flatten_version_rows(collected)
    assert flat == [{"Org": "OrgA", "Device Type": "ap", "Version": "1.0", "Count": 2}]


def test_to_org_result_converts_dict_to_dataclass() -> None:
    """_to_org_result should build a frozen _OrgProcessedResult from a plain dict."""
    entry = {
        "safe_org": "OrgX",
        "model_rows": [{"a": 1}],
        "version_rows": [{"b": 2}],
        "ver_per_model": [{"c": 3}],
    }
    result = _to_org_result(entry)
    assert isinstance(result, _OrgProcessedResult)
    assert result.safe_org == "OrgX"
    assert result.model_rows == [{"a": 1}]
    assert result.version_rows == [{"b": 2}]
    assert result.ver_per_model == [{"c": 3}]


def test_flatten_msp_version_rows_tags_and_merges() -> None:
    """MSP version flattener should tag each row with the owning org name."""
    data = [
        ("OrgA", [{"model": "M1", "version": "1", "count": 1, "device_type": "ap"}]),
        ("OrgB", [{"model": "M2", "version": "2", "count": 5, "device_type": "switch"}]),
    ]
    flat = OrgDeviceInventoryMSPOrchestrator._flatten_msp_version_rows(data)
    assert len(flat) == 2
    assert flat[0]["org"] == "OrgA"
    assert flat[1]["org"] == "OrgB"


def test_build_msp_version_pivot_builds_ordered_columns() -> None:
    """Version pivot builder should return sorted versions and (org, model) keyed pivot."""
    flat = [
        {"org": "A", "model": "M1", "version": "1.1", "count": 3, "device_type": "ap"},
        {"org": "A", "model": "M1", "version": "1.0", "count": 2, "device_type": "ap"},
    ]
    versions, pivot = OrgDeviceInventoryMSPOrchestrator._build_msp_version_pivot(flat)
    assert versions == ["1.0", "1.1"]
    assert pivot[("A", "M1")]["1.0"] == 2
    assert pivot[("A", "M1")]["1.1"] == 3
    assert pivot[("A", "M1")]["device_type"] == "ap"


def test_make_export_row_populates_all_versions_with_defaults() -> None:
    """Export row should fill every requested version, defaulting missing to zero."""
    row = OrgDeviceInventoryMSPOrchestrator._make_export_row(
        safe_org="OrgA",
        model="M1",
        ver_counts={"device_type": "ap", "1.0": 5},
        versions=["1.0", "2.0"],
        row_total=5,
    )
    assert row == {"Org": "OrgA", "Model": "M1", "Device Type": "ap", "1.0": 5, "2.0": 0, "Total": 5}


def test_build_msp_pivot_table_and_rows_produces_totals() -> None:
    """Pivot builder should include a TOTAL row and column totals."""
    versions = ["1.0", "2.0"]
    pivot = {
        ("OrgA", "M1"): {"device_type": "ap", "1.0": 3, "2.0": 5},
        ("OrgB", "M2"): {"device_type": "switch", "1.0": 1, "2.0": 0},
    }
    table, export_rows, col_totals, grand_total = OrgDeviceInventoryMSPOrchestrator._build_msp_pivot_table_and_rows(
        versions, pivot
    )
    assert len(export_rows) == 2  # WHY: one row per (org, model) key
    assert col_totals == {"1.0": 4, "2.0": 5}
    assert grand_total == 9
    assert table is not None


def test_display_combined_pivot_empty_short_circuits() -> None:
    """Combined pivot displayer should short-circuit when no data present."""
    exporter = _configure_msp()
    OrgDeviceInventoryMSPOrchestrator._display_combined_pivot_and_export([], "prefix")
    exporter.assert_not_called()  # WHY: no data -> no export


def test_display_combined_pivot_populated_calls_exporter() -> None:
    """Combined pivot displayer should call the exporter when rows exist."""
    exporter = _configure_msp()
    data = [("OrgA", [{"model": "M1", "version": "1.0", "count": 2, "device_type": "ap"}])]
    OrgDeviceInventoryMSPOrchestrator._display_combined_pivot_and_export(data, "prefix")
    exporter.assert_called_once()


def test_emit_combined_model_calls_exporter() -> None:
    """emit_combined_model should delegate to DataExporter.write_with_format_selection."""
    exporter = _configure_msp()
    collected = [
        _OrgProcessedResult(
            safe_org="OrgA",
            model_rows=[{"device_type": "ap", "model": "M1", "count": 1}],
            version_rows=[],
            ver_per_model=[],
        )
    ]
    OrgDeviceInventoryMSPOrchestrator._emit_combined_model("MSP_TEST", collected)
    exporter.assert_called_once()
    args, kwargs = exporter.call_args
    assert args[1] == "MSP_TEST_CombinedDeviceModelCounts"


def test_emit_combined_version_calls_exporter() -> None:
    """emit_combined_version should delegate to DataExporter.write_with_format_selection."""
    exporter = _configure_msp()
    collected = [
        _OrgProcessedResult(
            safe_org="OrgA",
            model_rows=[],
            version_rows=[{"device_type": "ap", "version": "1.0", "count": 1}],
            ver_per_model=[],
        )
    ]
    OrgDeviceInventoryMSPOrchestrator._emit_combined_version("MSP_TEST", collected)
    exporter.assert_called_once()
    args, kwargs = exporter.call_args
    assert args[1] == "MSP_TEST_CombinedDeviceFirmwareSummary"


def test_build_combined_reports_emits_all_three_reports(monkeypatch: pytest.MonkeyPatch) -> None:
    """build_combined_reports should invoke model, version, and pivot emitters in sequence."""
    _configure_msp()
    model_mock = MagicMock()
    version_mock = MagicMock()
    pivot_mock = MagicMock()
    monkeypatch.setattr(OrgDeviceInventoryMSPOrchestrator, "_emit_combined_model", staticmethod(model_mock))
    monkeypatch.setattr(OrgDeviceInventoryMSPOrchestrator, "_emit_combined_version", staticmethod(version_mock))
    monkeypatch.setattr(
        OrgDeviceInventoryMSPOrchestrator, "_display_combined_pivot_and_export", staticmethod(pivot_mock)
    )
    collected = [
        {"safe_org": "OrgA", "model_rows": [], "version_rows": [], "ver_per_model": []},
    ]
    OrgDeviceInventoryMSPOrchestrator._build_combined_reports("MSP_TEST", collected)
    model_mock.assert_called_once()
    version_mock.assert_called_once()
    pivot_mock.assert_called_once()


def test_process_org_skips_record_without_id() -> None:
    """_process_org should skip records without an id and log a warning."""
    _configure_msp()
    collected: list[dict] = []
    OrgDeviceInventoryMSPOrchestrator._process_org(
        {"name": "no-id-org"}, 1, 1, lambda oid: ([], [], [], oid), collected
    )
    assert collected == []


def test_process_org_invokes_runner_on_valid_record() -> None:
    """_process_org should invoke runner and append result on valid record."""
    _configure_msp()
    collected: list[dict] = []

    def _runner(oid: str) -> tuple[list[dict], list[dict], list[dict], str]:
        return ([{"a": 1}], [{"b": 2}], [{"c": 3}], oid)

    OrgDeviceInventoryMSPOrchestrator._process_org({"id": "org-1", "name": "Org One"}, 1, 1, _runner, collected)
    assert len(collected) == 1
    assert collected[0]["safe_org"] == "org-1"


def test_run_org_and_collect_appends_on_success() -> None:
    """_run_org_and_collect should append normalised dict on successful runner call."""
    _configure_msp()
    collected: list[dict[str, Any]] = []  # WHY: mypy strict — Any values (mixed shapes per collection call).
    OrgDeviceInventoryMSPOrchestrator._run_org_and_collect(
        "org-1", "Org One", lambda oid: ([{"m": 1}], [{"v": 2}], [{"vpm": 3}], "safe-org"), collected
    )
    assert collected == [
        {"safe_org": "safe-org", "model_rows": [{"m": 1}], "version_rows": [{"v": 2}], "ver_per_model": [{"vpm": 3}]}
    ]


def test_run_org_and_collect_tolerates_runner_exception() -> None:
    """_run_org_and_collect should swallow per-org runner exceptions and continue."""
    _configure_msp()
    collected: list[dict] = []

    def _boom(oid: str) -> tuple[list[dict], list[dict], list[dict], str]:
        raise RuntimeError("boom")

    OrgDeviceInventoryMSPOrchestrator._run_org_and_collect("org-1", "Org One", _boom, collected)
    assert collected == []  # WHY: exception path must not append


def test_process_orgs_batch_iterates_all_orgs() -> None:
    """_process_orgs_batch should invoke the runner for every valid org."""
    _configure_msp()

    def _runner(oid: str) -> tuple[list[dict], list[dict], list[dict], str]:
        return ([], [], [], oid)

    orgs = [{"id": "o1", "name": "One"}, {"id": "o2", "name": "Two"}]
    collected = OrgDeviceInventoryMSPOrchestrator._process_orgs_batch(orgs, _runner)
    assert len(collected) == 2
    assert [c["safe_org"] for c in collected] == ["o1", "o2"]


def test_run_single_msp_org_short_circuits_without_msp(monkeypatch: pytest.MonkeyPatch) -> None:
    """run_single_msp_org should short-circuit when resolve returns None."""
    _configure_msp()
    monkeypatch.setattr(OrgDeviceInventoryMSPOrchestrator, "_resolve_active_msp", staticmethod(lambda: None))
    run_mock = MagicMock()
    OrgDeviceInventoryMSPOrchestrator.run_single_msp_org(run_mock)
    run_mock.assert_not_called()


def test_run_single_msp_org_short_circuits_without_orgs(monkeypatch: pytest.MonkeyPatch) -> None:
    """run_single_msp_org should short-circuit when org list is empty."""
    _configure_msp(privileges=[{"msp_id": "m1", "msp_name": "M", "role": "admin"}])
    monkeypatch.setattr(
        OrgDeviceInventoryMSPOrchestrator,
        "_resolve_active_msp",
        staticmethod(lambda: {"msp_id": "m1", "msp_name": "M", "role": "admin"}),
    )
    monkeypatch.setattr(OrgDeviceInventoryMSPOrchestrator, "_fetch_org_list", staticmethod(lambda active_msp: []))
    run_mock = MagicMock()
    OrgDeviceInventoryMSPOrchestrator.run_single_msp_org(run_mock)
    run_mock.assert_not_called()


def test_run_single_msp_org_invokes_runner_on_valid_selection(monkeypatch: pytest.MonkeyPatch) -> None:
    """run_single_msp_org should invoke the runner when a valid org is chosen."""
    _configure_msp(privileges=[{"msp_id": "m1", "msp_name": "M", "role": "admin"}], safe_input_return="1")
    monkeypatch.setattr(
        OrgDeviceInventoryMSPOrchestrator,
        "_resolve_active_msp",
        staticmethod(lambda: {"msp_id": "m1", "msp_name": "M", "role": "admin"}),
    )
    monkeypatch.setattr(
        OrgDeviceInventoryMSPOrchestrator,
        "_fetch_org_list",
        staticmethod(lambda active_msp: [{"id": "org-1", "name": "Org One"}]),
    )
    run_mock = MagicMock()
    OrgDeviceInventoryMSPOrchestrator.run_single_msp_org(run_mock)
    run_mock.assert_called_once_with("org-1")


def test_run_single_msp_org_rejects_org_without_id(monkeypatch: pytest.MonkeyPatch) -> None:
    """run_single_msp_org should not invoke runner when selected org lacks an id."""
    _configure_msp(privileges=[{"msp_id": "m1", "msp_name": "M", "role": "admin"}], safe_input_return="1")
    monkeypatch.setattr(
        OrgDeviceInventoryMSPOrchestrator,
        "_resolve_active_msp",
        staticmethod(lambda: {"msp_id": "m1", "msp_name": "M", "role": "admin"}),
    )
    monkeypatch.setattr(
        OrgDeviceInventoryMSPOrchestrator,
        "_fetch_org_list",
        staticmethod(lambda active_msp: [{"name": "no-id"}]),
    )
    run_mock = MagicMock()
    OrgDeviceInventoryMSPOrchestrator.run_single_msp_org(run_mock)
    run_mock.assert_not_called()


def test_fetch_org_list_returns_empty_without_apisession() -> None:
    """_fetch_org_list should return empty list when apisession is not configured."""
    configure_org_device_inventory_msp_dependencies(
        apisession_dependency=None,  # WHY: force session-missing branch
        input_utils=SimpleNamespace(safe_input=MagicMock(return_value="")),
        data_exporter=SimpleNamespace(write_with_format_selection=MagicMock()),
        msp_privileges_value=[],
    )
    result = OrgDeviceInventoryMSPOrchestrator._fetch_org_list({"msp_id": "m1", "msp_name": "M"})
    assert result == []
