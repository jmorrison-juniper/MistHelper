"""Unit tests for WiredClientManufacturerReportGenerator (issue #878 tranche 4 -- un-omit).

Covers all nine static methods on ``src.reports.wired_client_manufacturer_report_generator``:
``execute`` (three flow branches: no records, records but no selection, records +
selection), ``_fetch_all_clients`` (happy path + exception path),
``_build_manufacturer_summary`` (counting, "Unknown" fallback, alphabetical
sort), ``_print_manufacturer_table``, ``_parse_manufacturer_choice`` (empty /
non-numeric / in-range / out-of-range), ``_prompt_selection``,
``_filter_by_manufacturer`` (empty filter + match + case-insensitive),
``_build_filename`` (ALL slug + slugified manufacturer + truncation), and
``_write_outputs`` (empty vs non-empty pipeline).
"""

from __future__ import annotations

import logging
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from src.reports.wired_client_manufacturer_report_generator import (
    WiredClientManufacturerReportGenerator as R,
)


def _make_mh(**extra):
    """Assemble a stub MistHelper module with the attributes each method touches."""
    defaults = {
        "ConfigUtils": MagicMock(name="ConfigUtils"),
        "InputUtils": MagicMock(name="InputUtils"),
        "DataExporter": MagicMock(name="DataExporter"),
        "apisession": MagicMock(name="apisession"),
    }
    defaults.update(extra)
    return SimpleNamespace(**defaults)


# ---------- execute ----------


def test_execute_aborts_when_no_records(caplog: pytest.LogCaptureFixture) -> None:
    """Empty fetch -> warning + user notice, no exports invoked."""
    caplog.set_level(logging.INFO, logger="src.utils.console")  # 1031: echo() logs INFO on src.utils.console.
    fake_mh = _make_mh()
    fake_mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-uuid"
    with (
        patch(
            "src.reports.wired_client_manufacturer_report_generator.importlib.import_module",
            return_value=fake_mh,
        ),
        patch.object(R, "_fetch_all_clients", return_value=[]),
        patch.object(R, "_write_outputs") as write_outputs,
    ):
        R.execute()
    write_outputs.assert_not_called()
    assert "No wired clients found" in caplog.text


def test_execute_writes_all_only_when_selection_skipped() -> None:
    """When user skips the picker only the ALL export runs."""
    fake_mh = _make_mh()
    fake_mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-uuid"
    records = [{"manufacture": "Cisco"}]
    with (
        patch(
            "src.reports.wired_client_manufacturer_report_generator.importlib.import_module",
            return_value=fake_mh,
        ),
        patch.object(R, "_fetch_all_clients", return_value=records),
        patch.object(R, "_prompt_selection", return_value=None),
        patch.object(R, "_write_outputs") as write_outputs,
    ):
        R.execute()
    write_outputs.assert_called_once_with(records, "")


def test_execute_writes_all_and_filtered_when_manufacturer_selected() -> None:
    """When user picks a manufacturer both ALL and filtered exports run."""
    fake_mh = _make_mh()
    fake_mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-uuid"
    records = [{"manufacture": "Cisco"}, {"manufacture": "Juniper"}]
    filtered = [{"manufacture": "Cisco"}]
    with (
        patch(
            "src.reports.wired_client_manufacturer_report_generator.importlib.import_module",
            return_value=fake_mh,
        ),
        patch.object(R, "_fetch_all_clients", return_value=records),
        patch.object(R, "_prompt_selection", return_value="Cisco"),
        patch.object(R, "_filter_by_manufacturer", return_value=filtered) as filter_call,
        patch.object(R, "_write_outputs") as write_outputs,
    ):
        R.execute()
    filter_call.assert_called_once_with(records, "Cisco")
    assert write_outputs.call_args_list[0].args == (records, "")
    assert write_outputs.call_args_list[1].args == (filtered, "Cisco")


# ---------- _fetch_all_clients ----------


def test_fetch_all_clients_returns_paginated_records() -> None:
    """Happy path: searchOrgWiredClients + get_all return the paginated list."""
    fake_mh = _make_mh()
    fake_response = MagicMock(name="searchResp")
    fake_mistapi = MagicMock(name="mistapi")
    fake_mistapi.api.v1.orgs.wired_clients.searchOrgWiredClients.return_value = fake_response
    fake_mistapi.get_all.return_value = [{"mac": "aa"}]
    with (
        patch("src.reports.wired_client_manufacturer_report_generator.mistapi", fake_mistapi),
        patch(
            "src.reports.wired_client_manufacturer_report_generator.importlib.import_module",
            return_value=fake_mh,
        ),
    ):
        result = R._fetch_all_clients("org-uuid")
    fake_mistapi.api.v1.orgs.wired_clients.searchOrgWiredClients.assert_called_once_with(
        fake_mh.apisession, "org-uuid", limit=1000
    )
    fake_mistapi.get_all.assert_called_once_with(response=fake_response, mist_session=fake_mh.apisession)
    assert result == [{"mac": "aa"}]


def test_fetch_all_clients_defaults_none_pagination_to_empty_list() -> None:
    """get_all returning None (no pages) must yield an empty list."""
    fake_mh = _make_mh()
    fake_mistapi = MagicMock(name="mistapi")
    fake_mistapi.api.v1.orgs.wired_clients.searchOrgWiredClients.return_value = MagicMock()
    fake_mistapi.get_all.return_value = None
    with (
        patch("src.reports.wired_client_manufacturer_report_generator.mistapi", fake_mistapi),
        patch(
            "src.reports.wired_client_manufacturer_report_generator.importlib.import_module",
            return_value=fake_mh,
        ),
    ):
        assert R._fetch_all_clients("org-uuid") == []


def test_fetch_all_clients_returns_empty_on_api_exception(caplog: pytest.LogCaptureFixture) -> None:
    """API failure logs + prints and returns an empty list (no re-raise)."""
    caplog.set_level(logging.INFO, logger="src.utils.console")  # 1031: echo() logs INFO on src.utils.console.
    fake_mh = _make_mh()
    fake_mistapi = MagicMock(name="mistapi")
    fake_mistapi.api.v1.orgs.wired_clients.searchOrgWiredClients.side_effect = RuntimeError("boom")
    with (
        patch("src.reports.wired_client_manufacturer_report_generator.mistapi", fake_mistapi),
        patch(
            "src.reports.wired_client_manufacturer_report_generator.importlib.import_module",
            return_value=fake_mh,
        ),
    ):
        assert R._fetch_all_clients("org-uuid") == []
    assert "Error retrieving wired clients" in caplog.text


# ---------- _build_manufacturer_summary ----------


def test_build_manufacturer_summary_counts_and_sorts_alphabetically() -> None:
    """Records are grouped, counted, and returned sorted case-insensitively."""
    records = [
        {"manufacture": "Cisco"},
        {"manufacture": "Juniper"},
        {"manufacture": "Cisco"},
        {"manufacture": "arista"},
    ]
    summary = R._build_manufacturer_summary(records)
    assert summary == [("arista", 1), ("Cisco", 2), ("Juniper", 1)]


def test_build_manufacturer_summary_uses_unknown_for_missing_or_empty() -> None:
    """Missing/None/empty manufacturer values collapse into 'Unknown'."""
    records = [
        {"manufacture": None},
        {"manufacture": ""},
        {},
    ]
    assert R._build_manufacturer_summary(records) == [("Unknown", 3)]


# ---------- _print_manufacturer_table ----------


def test_print_manufacturer_table_renders_totals_and_rows(caplog: pytest.LogCaptureFixture) -> None:
    """Header shows totals; rows list each manufacturer with count."""
    caplog.set_level(logging.INFO, logger="src.utils.console")  # 1031: echo() logs INFO on src.utils.console.
    R._print_manufacturer_table([("Cisco", 3), ("Juniper", 1)])
    output = caplog.text
    assert "Found 4 clients from 2 manufacturers" in output
    assert "Cisco" in output
    assert "Juniper" in output


def test_print_manufacturer_table_truncates_long_names(caplog: pytest.LogCaptureFixture) -> None:
    """Names longer than 44 characters are truncated for column alignment."""
    caplog.set_level(logging.INFO, logger="src.utils.console")  # 1031: echo() logs INFO on src.utils.console.
    long_name = "X" * 60
    R._print_manufacturer_table([(long_name, 1)])
    output = caplog.text
    assert "X" * 44 in output
    assert "X" * 45 not in output


# ---------- _parse_manufacturer_choice ----------


def test_parse_manufacturer_choice_returns_none_for_empty_input() -> None:
    """Empty input maps to None (no filter)."""
    assert R._parse_manufacturer_choice("", [("Cisco", 1)]) is None


def test_parse_manufacturer_choice_returns_none_for_non_numeric(caplog: pytest.LogCaptureFixture) -> None:
    """Non-numeric input prints an error and returns None."""
    caplog.set_level(logging.INFO, logger="src.utils.console")  # 1031: echo() logs INFO on src.utils.console.
    assert R._parse_manufacturer_choice("abc", [("Cisco", 1)]) is None
    assert "Invalid selection" in caplog.text


def test_parse_manufacturer_choice_returns_selected_name_for_valid_index() -> None:
    """A 1-based index within range returns the manufacturer name."""
    summary = [("Cisco", 1), ("Juniper", 2)]
    assert R._parse_manufacturer_choice("2", summary) == "Juniper"


def test_parse_manufacturer_choice_returns_none_when_out_of_range(caplog: pytest.LogCaptureFixture) -> None:
    """Out-of-range indexes print an error and return None."""
    caplog.set_level(logging.INFO, logger="src.utils.console")  # 1031: echo() logs INFO on src.utils.console.
    assert R._parse_manufacturer_choice("99", [("Cisco", 1)]) is None
    assert "out of range" in caplog.text


# ---------- _prompt_selection ----------


def test_prompt_selection_delegates_to_input_utils_and_parses_choice() -> None:
    """Prompt invokes InputUtils.safe_input then routes the choice through the parser."""
    fake_mh = _make_mh()
    fake_mh.InputUtils.safe_input.return_value = "1"
    summary = [("Cisco", 1)]
    with patch(
        "src.reports.wired_client_manufacturer_report_generator.importlib.import_module",
        return_value=fake_mh,
    ):
        assert R._prompt_selection(summary) == "Cisco"
    fake_mh.InputUtils.safe_input.assert_called_once()


# ---------- _filter_by_manufacturer ----------


def test_filter_by_manufacturer_returns_all_when_manufacturer_is_empty() -> None:
    """An empty selection means 'no filter': the original list is returned."""
    records = [{"manufacture": "Cisco"}, {"manufacture": "Juniper"}]
    assert R._filter_by_manufacturer(records, "") is records


def test_filter_by_manufacturer_matches_case_insensitively() -> None:
    """Comparison is case-insensitive on the normalized manufacture field."""
    records = [
        {"manufacture": "Cisco"},
        {"manufacture": "CISCO"},
        {"manufacture": "Juniper"},
        {"manufacture": None},
    ]
    assert R._filter_by_manufacturer(records, "cisco") == [
        {"manufacture": "Cisco"},
        {"manufacture": "CISCO"},
    ]


# ---------- _build_filename ----------


def test_build_filename_uses_all_slug_when_no_manufacturer() -> None:
    """Empty manufacturer -> 'ALL' slug."""
    assert R._build_filename("") == "WiredClientManufacturerReport_ALL"


def test_build_filename_slugifies_and_truncates_manufacturer() -> None:
    """Non-word characters collapse to underscores; slug truncates at 40 chars."""
    name = "Cisco Systems, Inc. " + ("X" * 60)
    filename = R._build_filename(name)
    assert filename.startswith("WiredClientManufacturerReport_Cisco_Systems_Inc_")
    slug = filename.removeprefix("WiredClientManufacturerReport_")
    assert len(slug) <= 40


# ---------- _write_outputs ----------


def test_write_outputs_writes_empty_list_when_no_records() -> None:
    """Empty filtered list skips the flatten/escape pipeline but still writes."""
    fake_mh = _make_mh()
    with (
        patch("src.reports.wired_client_manufacturer_report_generator.DataProcessingUtils") as fake_dpu,
        patch(
            "src.reports.wired_client_manufacturer_report_generator.importlib.import_module",
            return_value=fake_mh,
        ),
    ):
        R._write_outputs([], "Cisco")
    fake_dpu.flatten_nested_fields.assert_not_called()
    fake_mh.DataExporter.write_with_format_selection.assert_called_once_with(
        [], "WiredClientManufacturerReport_Cisco", api_function_name="wiredClientManufacturerReport"
    )


def test_write_outputs_runs_pipeline_and_writes_when_records_present() -> None:
    """Non-empty list flows through flatten -> escape_multiline -> write."""
    fake_mh = _make_mh()
    with (
        patch("src.reports.wired_client_manufacturer_report_generator.DataProcessingUtils") as fake_dpu,
        patch(
            "src.reports.wired_client_manufacturer_report_generator.importlib.import_module",
            return_value=fake_mh,
        ),
    ):
        fake_dpu.flatten_nested_fields.return_value = [{"flat": True}]
        fake_dpu.escape_multiline.return_value = [{"safe": True}]
        R._write_outputs([{"mac": "aa"}], "")
    fake_dpu.flatten_nested_fields.assert_called_once_with([{"mac": "aa"}])
    fake_dpu.escape_multiline.assert_called_once_with([{"flat": True}])
    fake_mh.DataExporter.write_with_format_selection.assert_called_once_with(
        [{"safe": True}], "WiredClientManufacturerReport_ALL", api_function_name="wiredClientManufacturerReport"
    )
