"""Unit tests for GlobalWiredClientReportGenerator (issue #878 tranche 32 -- un-omit).

Covers every branch of every static method on
``src.reports.global_wired_client_report_generator``: ``execute`` (cancel /
no-records / happy paths), ``_prompt_filter_criteria`` (mac cancel, mfg cancel,
both skipped, mac provided), ``_collect_single_filter`` (no-operator,
value-required-and-invalid, value-required-and-valid, operator-with-no-value),
``_resolve_operator_choice`` ("0" / empty / valid-index / out-of-range /
ValueError), ``_prompt_operator`` (display + delegation), ``_fetch_clients``
(happy + None pagination + exception), ``_build_remote_params`` (mac push,
mfg push, unsupported operators, missing values), ``_apply_filters``
(no-criteria + with-criteria), ``_record_matches`` (mac fail, mfg fail,
both pass), ``_build_no_filter_result``, ``_build_metadata`` (mac only,
mfg only, both, no criteria), and ``_write_outputs`` /
``_write_standard_export`` / ``_write_local_report`` (zero matches,
matches, OSError branch).
"""

from __future__ import annotations

import logging
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from src.reports.global_wired_client_report_generator import (
    GlobalWiredClientReportGenerator as R,
)


def _make_mh(**extra):
    """Assemble a stub MistHelper module with the attributes each method touches."""
    op_engine = MagicMock(name="FilterOperatorEngine")
    op_engine.VALUE_REQUIRED_OPERATORS = {"equals", "contains", "starts_with"}
    op_engine.REMOTE_PREFILTER_OPERATORS = {"equals"}
    op_engine.OPERATOR_CATALOG = [
        "equals",
        "not_equals",
        "contains",
        "not_contains",
        "starts_with",
        "ends_with",
        "regex",
        "empty",
        "not_empty",
        "in",
        "not_in",
        "any",
    ]
    op_engine.validate_operator_value = MagicMock(return_value=True)
    op_engine.evaluate_operator = MagicMock(return_value=True)
    defaults = {
        "ConfigUtils": MagicMock(name="ConfigUtils"),
        "InputUtils": MagicMock(name="InputUtils"),
        "DataExporter": MagicMock(name="DataExporter"),
        "FilterOperatorEngine": op_engine,
        "apisession": MagicMock(name="apisession"),
    }
    defaults.update(extra)
    return SimpleNamespace(**defaults)


def _patch_mh(fake_mh):
    """Patch importlib.import_module in the target module to return ``fake_mh``."""
    return patch(
        "src.reports.global_wired_client_report_generator.importlib.import_module",
        return_value=fake_mh,
    )


# ---------- execute ----------


def test_execute_returns_when_user_cancels_filter_prompt() -> None:
    """User-cancelled prompt short-circuits before fetch."""
    fake_mh = _make_mh()
    fake_mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-uuid"
    with (
        _patch_mh(fake_mh),
        patch.object(R, "_prompt_filter_criteria", return_value=False),
        patch.object(R, "_fetch_clients") as fetch,
    ):
        R.execute()
    fetch.assert_not_called()


def test_execute_returns_when_no_records(caplog: pytest.LogCaptureFixture) -> None:
    """Empty fetch prints notice and skips write."""
    caplog.set_level(logging.WARNING)
    fake_mh = _make_mh()
    fake_mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-uuid"
    with (
        _patch_mh(fake_mh),
        patch.object(R, "_prompt_filter_criteria", return_value=None),
        patch.object(R, "_fetch_clients", return_value=([], False)),
        patch.object(R, "_write_outputs") as write_outputs,
    ):
        R.execute()
    write_outputs.assert_not_called()
    assert "No wired clients found" in caplog.text


def test_execute_happy_path_invokes_write_outputs() -> None:
    """Happy path applies filters then writes outputs."""
    fake_mh = _make_mh()
    fake_mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-uuid"
    records = [{"mac": "aa"}]
    with (
        _patch_mh(fake_mh),
        patch.object(R, "_prompt_filter_criteria", return_value={"mac_operator": "equals", "mac_value": "aa"}),
        patch.object(R, "_fetch_clients", return_value=(records, True)),
        patch.object(R, "_apply_filters", return_value=(records, {"k": 1})),
        patch.object(R, "_write_outputs") as write_outputs,
    ):
        R.execute()
    write_outputs.assert_called_once_with(records, {"k": 1})


# ---------- _prompt_filter_criteria ----------


def test_prompt_filter_criteria_returns_none_when_all_skipped() -> None:
    """No filters entered -> None (no criteria to record)."""
    with patch.object(R, "_collect_single_filter", return_value=None):
        assert R._prompt_filter_criteria() is None


def test_prompt_filter_criteria_returns_false_on_mac_cancel() -> None:
    """MAC collector returning False propagates as cancel."""
    with patch.object(R, "_collect_single_filter", side_effect=[False]):
        assert R._prompt_filter_criteria() is False


def test_prompt_filter_criteria_returns_false_on_mfg_cancel() -> None:
    """Manufacturer collector cancelling after MAC succeeded returns False."""
    with patch.object(R, "_collect_single_filter", side_effect=[None, False]):
        assert R._prompt_filter_criteria() is False


def test_prompt_filter_criteria_returns_dict_when_filter_set() -> None:
    """A collected filter mutates the dict which is returned."""

    def _collector(_field, key_prefix, criteria):
        criteria[f"{key_prefix}_operator"] = "equals"
        return True

    with patch.object(R, "_collect_single_filter", side_effect=_collector):
        result = R._prompt_filter_criteria()
    assert result == {"mac_operator": "equals", "mfg_operator": "equals"}


# ---------- _collect_single_filter ----------


def test_collect_single_filter_skips_when_no_operator() -> None:
    """None operator -> collector returns None and criteria unchanged."""
    criteria: dict[str, str] = {}
    with (
        _patch_mh(_make_mh()),
        patch.object(R, "_prompt_operator", return_value=None),
    ):
        assert R._collect_single_filter("MAC", "mac", criteria) is None
    assert criteria == {}


def test_collect_single_filter_records_operator_without_value() -> None:
    """Operator not in VALUE_REQUIRED_OPERATORS records operator only."""
    fake_mh = _make_mh()
    criteria: dict[str, str] = {}
    with (
        _patch_mh(fake_mh),
        patch.object(R, "_prompt_operator", return_value="empty"),
    ):
        assert R._collect_single_filter("MAC", "mac", criteria) is True
    assert criteria == {"mac_operator": "empty"}


def test_collect_single_filter_returns_false_on_invalid_value() -> None:
    """Invalid value from FilterOperatorEngine.validate_operator_value -> False."""
    fake_mh = _make_mh()
    fake_mh.InputUtils.safe_input.return_value = "bad"
    fake_mh.FilterOperatorEngine.validate_operator_value.return_value = False
    criteria: dict[str, str] = {}
    with (
        _patch_mh(fake_mh),
        patch.object(R, "_prompt_operator", return_value="equals"),
    ):
        assert R._collect_single_filter("MAC", "mac", criteria) is False
    assert criteria == {"mac_operator": "equals"}


def test_collect_single_filter_records_valid_value() -> None:
    """Valid operator+value -> True with both keys in criteria."""
    fake_mh = _make_mh()
    fake_mh.InputUtils.safe_input.return_value = "aa:bb:cc"
    criteria: dict[str, str] = {}
    with (
        _patch_mh(fake_mh),
        patch.object(R, "_prompt_operator", return_value="equals"),
    ):
        assert R._collect_single_filter("MAC", "mac", criteria) is True
    assert criteria == {"mac_operator": "equals", "mac_value": "aa:bb:cc"}


# ---------- _resolve_operator_choice ----------


def test_resolve_operator_choice_returns_none_for_zero() -> None:
    """Explicit '0' -> None (skip)."""
    with _patch_mh(_make_mh()):
        assert R._resolve_operator_choice("0", "MAC") is None


def test_resolve_operator_choice_returns_none_for_empty() -> None:
    """Empty string -> None (skip)."""
    with _patch_mh(_make_mh()):
        assert R._resolve_operator_choice("", "MAC") is None


def test_resolve_operator_choice_returns_catalog_entry_for_valid_index() -> None:
    """Valid 1-based index returns the corresponding catalog entry."""
    with _patch_mh(_make_mh()):
        assert R._resolve_operator_choice("1", "MAC") == "equals"
        assert R._resolve_operator_choice("3", "MAC") == "contains"


def test_resolve_operator_choice_returns_none_when_out_of_range(caplog: pytest.LogCaptureFixture) -> None:
    """Index outside catalog -> None + warning."""
    caplog.set_level(logging.WARNING)
    with _patch_mh(_make_mh()):
        assert R._resolve_operator_choice("99", "MAC") is None
    assert "Invalid selection" in caplog.text


def test_resolve_operator_choice_returns_none_for_non_numeric(caplog: pytest.LogCaptureFixture) -> None:
    """Non-numeric input -> None + warning."""
    caplog.set_level(logging.WARNING)
    with _patch_mh(_make_mh()):
        assert R._resolve_operator_choice("abc", "MAC") is None
    assert "Invalid selection" in caplog.text


# ---------- _prompt_operator ----------


def test_prompt_operator_delegates_to_resolve(caplog: pytest.LogCaptureFixture) -> None:
    """Prompt shows menu, reads input, then delegates parsing."""
    caplog.set_level(logging.WARNING)
    fake_mh = _make_mh()
    fake_mh.InputUtils.safe_input.return_value = "1"
    with _patch_mh(fake_mh):
        result = R._prompt_operator("MAC")
    assert result == "equals"
    out = caplog.text
    assert "MAC filter operator" in out
    assert "No filter" in out
    fake_mh.InputUtils.safe_input.assert_called_once()


# ---------- _fetch_clients ----------


def test_fetch_clients_success_without_criteria() -> None:
    """No criteria -> base params only; remote_used is False."""
    fake_mh = _make_mh()
    fake_mistapi = MagicMock(name="mistapi")
    fake_mistapi.api.v1.orgs.wired_clients.searchOrgWiredClients.return_value = "resp"
    fake_mistapi.get_all.return_value = [{"mac": "aa"}]
    with (
        patch("src.reports.global_wired_client_report_generator.mistapi", fake_mistapi),
        _patch_mh(fake_mh),
    ):
        records, remote_used = R._fetch_clients("org-uuid", None)
    assert records == [{"mac": "aa"}]
    assert remote_used is False
    fake_mistapi.api.v1.orgs.wired_clients.searchOrgWiredClients.assert_called_once_with(
        fake_mh.apisession, "org-uuid", limit=1000
    )


def test_fetch_clients_success_with_pushable_criteria() -> None:
    """Pushable criteria populate remote params and remote_used is True."""
    fake_mh = _make_mh()
    fake_mistapi = MagicMock(name="mistapi")
    fake_mistapi.api.v1.orgs.wired_clients.searchOrgWiredClients.return_value = "resp"
    fake_mistapi.get_all.return_value = None  # exercise `or []`
    criteria = {"mac_operator": "equals", "mac_value": "aa"}
    with (
        patch("src.reports.global_wired_client_report_generator.mistapi", fake_mistapi),
        _patch_mh(fake_mh),
    ):
        records, remote_used = R._fetch_clients("org-uuid", criteria)
    assert records == []
    assert remote_used is True
    kwargs = fake_mistapi.api.v1.orgs.wired_clients.searchOrgWiredClients.call_args.kwargs
    assert kwargs["mac"] == "aa"


def test_fetch_clients_returns_empty_on_exception(caplog: pytest.LogCaptureFixture) -> None:
    """API failure returns ([], False) and prints error."""
    caplog.set_level(logging.WARNING)
    fake_mh = _make_mh()
    fake_mistapi = MagicMock(name="mistapi")
    fake_mistapi.api.v1.orgs.wired_clients.searchOrgWiredClients.side_effect = RuntimeError("boom")
    with (
        patch("src.reports.global_wired_client_report_generator.mistapi", fake_mistapi),
        _patch_mh(fake_mh),
    ):
        records, remote_used = R._fetch_clients("org-uuid", None)
    assert records == []
    assert remote_used is False
    assert "Error retrieving wired clients" in caplog.text


# ---------- _build_remote_params ----------


def test_build_remote_params_pushes_mac_and_mfg_when_supported() -> None:
    """Both pushable operators + values populate params and return True."""
    fake_mh = _make_mh()
    criteria = {
        "mac_operator": "equals",
        "mac_value": "aa",
        "mfg_operator": "equals",
        "mfg_value": "Cisco",
    }
    params: dict = {}
    with _patch_mh(fake_mh):
        assert R._build_remote_params(criteria, params) is True
    assert params == {"mac": "aa", "manufacture": "Cisco"}


def test_build_remote_params_skips_when_operator_not_pushable() -> None:
    """Non-pushable operators leave params untouched and return False."""
    fake_mh = _make_mh()
    criteria = {"mac_operator": "contains", "mac_value": "aa"}
    params: dict = {}
    with _patch_mh(fake_mh):
        assert R._build_remote_params(criteria, params) is False
    assert params == {}


def test_build_remote_params_skips_when_value_missing() -> None:
    """Empty value with pushable operator does not populate params."""
    fake_mh = _make_mh()
    criteria = {"mac_operator": "equals", "mac_value": "", "mfg_operator": "equals", "mfg_value": ""}
    params: dict = {}
    with _patch_mh(fake_mh):
        assert R._build_remote_params(criteria, params) is False
    assert params == {}


# ---------- _apply_filters + _build_no_filter_result ----------


def test_apply_filters_no_criteria_returns_all_records() -> None:
    """Empty criteria returns all records with local_filter_used False."""
    records = [{"mac": "aa"}, {"mac": "bb"}]
    matched, metadata = R._apply_filters(records, None, remote_used=False)
    assert matched == records
    assert metadata["records_retrieved"] == 2
    assert metadata["records_matched"] == 2
    assert metadata["local_filter_used"] is False


def test_apply_filters_with_criteria_filters_records() -> None:
    """Records failing _record_matches are dropped; metadata reflects filter."""
    records = [{"mac": "aa"}, {"mac": "bb"}]
    with patch.object(R, "_record_matches", side_effect=[True, False]):
        matched, metadata = R._apply_filters(records, {"mac_operator": "equals"}, remote_used=True)
    assert matched == [{"mac": "aa"}]
    assert metadata["records_matched"] == 1
    assert metadata["local_filter_used"] is True
    assert metadata["remote_filter_used"] is True


# ---------- _record_matches ----------


def test_record_matches_returns_false_when_mac_fails() -> None:
    """Failing MAC comparison short-circuits to False."""
    fake_mh = _make_mh()
    fake_mh.FilterOperatorEngine.evaluate_operator.return_value = False
    with _patch_mh(fake_mh):
        assert (
            R._record_matches(
                {"mac": "aa"},
                {"mac_operator": "equals", "mac_value": "bb"},
            )
            is False
        )


def test_record_matches_returns_false_when_mfg_fails() -> None:
    """Failing manufacturer comparison after successful MAC -> False."""
    fake_mh = _make_mh()
    fake_mh.FilterOperatorEngine.evaluate_operator.side_effect = [True, False]
    with _patch_mh(fake_mh):
        assert (
            R._record_matches(
                {"mac": "aa", "manufacture": "Cisco"},
                {
                    "mac_operator": "equals",
                    "mac_value": "aa",
                    "mfg_operator": "equals",
                    "mfg_value": "Juniper",
                },
            )
            is False
        )


def test_record_matches_returns_true_when_all_pass() -> None:
    """Every criterion passes -> True."""
    fake_mh = _make_mh()
    with _patch_mh(fake_mh):
        assert (
            R._record_matches(
                {"mac": "aa", "manufacture": "Cisco"},
                {
                    "mac_operator": "equals",
                    "mac_value": "aa",
                    "mfg_operator": "equals",
                    "mfg_value": "Cisco",
                },
            )
            is True
        )


def test_record_matches_returns_true_when_no_criteria() -> None:
    """Empty criteria dict -> True."""
    with _patch_mh(_make_mh()):
        assert R._record_matches({"mac": "aa"}, {}) is True


# ---------- _build_metadata ----------


def test_build_metadata_without_criteria() -> None:
    """Metadata omits filter keys when criteria is None."""
    metadata = R._build_metadata(5, 5, False, False, None)
    assert metadata["records_retrieved"] == 5
    assert metadata["records_matched"] == 5
    assert metadata["remote_filter_used"] is False
    assert metadata["local_filter_used"] is False
    assert "mac_operator" not in metadata
    assert "mfg_operator" not in metadata
    assert "generated_at" in metadata


def test_build_metadata_with_mac_only() -> None:
    """Metadata includes mac keys when MAC criterion is present."""
    metadata = R._build_metadata(3, 1, True, True, {"mac_operator": "equals", "mac_value": "aa"})
    assert metadata["mac_operator"] == "equals"
    assert metadata["mac_value"] == "aa"
    assert "mfg_operator" not in metadata


def test_build_metadata_with_mfg_only() -> None:
    """Metadata includes mfg keys when manufacturer criterion is present."""
    metadata = R._build_metadata(3, 1, False, True, {"mfg_operator": "contains", "mfg_value": "Cisco"})
    assert metadata["mfg_operator"] == "contains"
    assert metadata["mfg_value"] == "Cisco"
    assert "mac_operator" not in metadata


def test_build_metadata_with_both_filters() -> None:
    """Metadata includes both filter blocks when both criteria are set."""
    metadata = R._build_metadata(
        4,
        2,
        True,
        True,
        {"mac_operator": "equals", "mac_value": "aa", "mfg_operator": "equals", "mfg_value": "Cisco"},
    )
    assert metadata["mac_operator"] == "equals"
    assert metadata["mfg_operator"] == "equals"


# ---------- _write_outputs / _write_standard_export / _write_local_report ----------


def test_write_outputs_prints_zero_match_message(caplog: pytest.LogCaptureFixture) -> None:
    """Zero matched records prints the no-matches notice."""
    caplog.set_level(logging.WARNING)
    metadata = {"records_matched": 0, "records_retrieved": 5}
    with (
        patch.object(R, "_write_standard_export") as write_export,
        patch.object(R, "_write_local_report") as write_report,
    ):
        R._write_outputs([], metadata)
    write_export.assert_called_once_with([])
    write_report.assert_called_once_with([], metadata)
    assert "No records matched" in caplog.text


def test_write_outputs_with_matches_skips_no_match_notice(caplog: pytest.LogCaptureFixture) -> None:
    """When records match, only summary is printed; no zero-match notice."""
    caplog.set_level(logging.WARNING)
    metadata = {"records_matched": 1, "records_retrieved": 5}
    matched = [{"mac": "aa"}]
    with (
        patch.object(R, "_write_standard_export"),
        patch.object(R, "_write_local_report"),
    ):
        R._write_outputs(matched, metadata)
    out = caplog.text
    assert "Matched 1 of 5" in out
    assert "No records matched" not in out


def test_write_standard_export_skips_pipeline_when_empty() -> None:
    """Empty matches skip flatten/escape but still call write."""
    fake_mh = _make_mh()
    with (
        patch("src.reports.global_wired_client_report_generator.DataProcessingUtils") as fake_dpu,
        _patch_mh(fake_mh),
    ):
        R._write_standard_export([])
    fake_dpu.flatten_nested_fields.assert_not_called()
    fake_mh.DataExporter.write_with_format_selection.assert_called_once_with(
        [], "GlobalWiredClientReport", api_function_name="globalWiredClientReport"
    )


def test_write_standard_export_runs_pipeline_when_populated() -> None:
    """Populated matches flow through flatten -> escape_multiline -> write."""
    fake_mh = _make_mh()
    with (
        patch("src.reports.global_wired_client_report_generator.DataProcessingUtils") as fake_dpu,
        _patch_mh(fake_mh),
    ):
        fake_dpu.flatten_nested_fields.return_value = [{"flat": True}]
        fake_dpu.escape_multiline.return_value = [{"safe": True}]
        R._write_standard_export([{"mac": "aa"}])
    fake_dpu.flatten_nested_fields.assert_called_once_with([{"mac": "aa"}])
    fake_dpu.escape_multiline.assert_called_once_with([{"flat": True}])
    fake_mh.DataExporter.write_with_format_selection.assert_called_once_with(
        [{"safe": True}], "GlobalWiredClientReport", api_function_name="globalWiredClientReport"
    )


def test_write_local_report_writes_summary_json(tmp_path, monkeypatch, caplog: pytest.LogCaptureFixture) -> None:
    """Writes JSON summary file to the data/ directory."""
    caplog.set_level(logging.WARNING)
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir()
    metadata = {"records_matched": 1, "records_retrieved": 5}
    R._write_local_report([{"mac": "aa"}], metadata)
    written = (tmp_path / "data" / "GlobalWiredClientReport_summary.json").read_text(encoding="utf-8")
    assert "records_matched" in written
    assert "Report summary written" in caplog.text


def test_write_local_report_handles_os_error(caplog: pytest.LogCaptureFixture) -> None:
    """OSError during write logs + warns without raising."""
    caplog.set_level(logging.WARNING)
    metadata = {"records_matched": 0, "records_retrieved": 0}
    with patch(
        "src.reports.global_wired_client_report_generator.open",
        side_effect=OSError("disk full"),
    ):
        R._write_local_report([], metadata)
    assert "Could not write report summary" in caplog.text
