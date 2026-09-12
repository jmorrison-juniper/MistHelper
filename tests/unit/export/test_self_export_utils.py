"""Wave 7 P2 coverage for src/export/self_export_utils.py (initiative #1018).

Covers every branch of ``SelfExportUtils``:

- ``_persist_self_audit_rows``: empty-rows path (warning + empty write) and
  non-empty path (flatten + write with api_function_name kwarg).
- ``audit_logs``: happy path (dynamic lookback lookup, listSelfAuditLogs call
  with duration + limit kwargs, pagination, persist), and exception path
  (logging.exception invoked; no crash).

Every collaborator (``TimeUtils``, ``DataProcessingUtils``, ``mistapi``,
``MistHelper.DataExporter`` and ``MistHelper.apisession``) is monkeypatched.
No live network, no real writes.
"""

from __future__ import annotations  # WHY: PEP 604 unions on Python 3.10+.

import logging  # WHY: caplog verification of warning + exception log paths.
from typing import Any  # WHY: monkeypatched fakes have loose typing.
from unittest.mock import MagicMock, call  # WHY: FR-008 collaborator doubles + call assertions.

import pytest  # WHY: monkeypatch + caplog fixtures.

from src.export.self_export_utils import SelfExportUtils  # WHY: direct SUT import; only static methods.


@pytest.fixture
def wired_deps(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Wire every collaborator SelfExportUtils reaches through.

    Returns a dict of mocks so tests can assert argument bindings + call counts.
    Uses monkeypatch to intercept both module-level collaborators (mistapi,
    TimeUtils, DataProcessingUtils) and the lazy MistHelper attributes
    (DataExporter, apisession).
    """
    data_exporter = MagicMock(name="DataExporter")  # WHY: write_with_format_selection observed only.
    apisession = MagicMock(name="apisession")  # WHY: forwarded into mistapi calls.
    monkeypatch.setattr("MistHelper.DataExporter", data_exporter, raising=False)  # WHY: proxy lookup path.
    monkeypatch.setattr("MistHelper.apisession", apisession, raising=False)  # WHY: proxy lookup path.

    time_utils = MagicMock(name="TimeUtils")  # WHY: get_dynamic_lookback_hours + log_dynamic_lookback observed.
    time_utils.get_dynamic_lookback_hours.return_value = 6  # WHY: deterministic lookback for assertions.
    monkeypatch.setattr("src.export.self_export_utils.TimeUtils", time_utils, raising=True)  # WHY: intercept helper.

    data_processing = MagicMock(name="DataProcessingUtils")  # WHY: flatten_nested_fields observed + identity here.
    data_processing.flatten_nested_fields.side_effect = lambda rows: rows  # WHY: identity for round-trip check.
    monkeypatch.setattr(  # WHY: intercept the imported name at module scope.
        "src.export.self_export_utils.DataProcessingUtils", data_processing, raising=True
    )

    mistapi_mod = MagicMock(name="mistapi")  # WHY: intercept both listSelfAuditLogs and get_all.
    monkeypatch.setattr("src.export.self_export_utils.mistapi", mistapi_mod, raising=True)  # WHY: patch import ref.

    return {
        "DataExporter": data_exporter,
        "apisession": apisession,
        "TimeUtils": time_utils,
        "DataProcessingUtils": data_processing,
        "mistapi": mistapi_mod,
    }


class TestPersistSelfAuditRows:
    """Cover both branches of `_persist_self_audit_rows`."""

    def test_empty_rows_writes_empty_file_and_warns(
        self, wired_deps: dict[str, Any], caplog: pytest.LogCaptureFixture
    ) -> None:
        """Empty rows -> warning log + empty-list write via DataExporter."""
        with caplog.at_level(logging.WARNING, logger="root"):  # WHY: verify warning emitted.
            SelfExportUtils._persist_self_audit_rows([], "SelfAuditLogs.csv", hours=12)  # WHY: empty-rows branch.

        # WHY: warning includes hours context per SUT log format.
        assert any("last 12 hours" in rec.message for rec in caplog.records)
        # WHY: empty file signals successful run rather than silent failure.
        wired_deps["DataExporter"].write_with_format_selection.assert_called_once_with([], "SelfAuditLogs.csv")
        # WHY: no flattening should occur on the empty path.
        wired_deps["DataProcessingUtils"].flatten_nested_fields.assert_not_called()

    def test_non_empty_rows_flattens_and_writes(self, wired_deps: dict[str, Any]) -> None:
        """Non-empty rows -> flatten_nested_fields + write with api_function_name kwarg."""
        rows = [{"id": "r1"}, {"id": "r2"}]  # WHY: minimal non-empty payload.
        SelfExportUtils._persist_self_audit_rows(rows, "SelfAuditLogs.csv", hours=6)  # WHY: non-empty branch.

        wired_deps["DataProcessingUtils"].flatten_nested_fields.assert_called_once_with(rows)  # WHY: flatten step.
        wired_deps["DataExporter"].write_with_format_selection.assert_called_once_with(
            rows, "SelfAuditLogs.csv", api_function_name="listSelfAuditLogs"
        )  # WHY: exact kwargs contract.


class TestAuditLogsHappyPath:
    """`audit_logs()` end-to-end: lookback -> fetch -> paginate -> persist."""

    def test_happy_path_full_pipeline(self, wired_deps: dict[str, Any]) -> None:
        """Full path forwards the dynamic lookback into the API call and paginates."""
        response = MagicMock(name="api_response")  # WHY: opaque handle forwarded into mistapi.get_all.
        wired_deps["mistapi"].api.v1.self.logs.listSelfAuditLogs.return_value = response  # WHY: seed API call.
        wired_deps["mistapi"].get_all.return_value = [{"id": "log1"}, {"id": "log2"}]  # WHY: pagination result.

        SelfExportUtils.audit_logs()  # WHY: exercise full flow under wired collaborators.

        # WHY: lookback helper called with the documented defaults (24 default, 1 min).
        wired_deps["TimeUtils"].get_dynamic_lookback_hours.assert_called_once_with(24, 1)
        # WHY: lookback window logged for observability.
        wired_deps["TimeUtils"].log_dynamic_lookback.assert_called_once_with("self audit logs export", 6)
        # WHY: API call receives session, duration=6h, limit=1000 per SUT.
        wired_deps["mistapi"].api.v1.self.logs.listSelfAuditLogs.assert_called_once_with(
            wired_deps["apisession"], duration="6h", limit=1000
        )
        # WHY: pagination step reached with the raw response + session.
        wired_deps["mistapi"].get_all.assert_called_once_with(response=response, mist_session=wired_deps["apisession"])
        # WHY: persist step writes the paginated rows to SelfAuditLogs.csv.
        wired_deps["DataExporter"].write_with_format_selection.assert_called_once_with(
            [{"id": "log1"}, {"id": "log2"}], "SelfAuditLogs.csv", api_function_name="listSelfAuditLogs"
        )

    def test_empty_pagination_writes_empty_file(self, wired_deps: dict[str, Any]) -> None:
        """When mistapi.get_all returns [], the persist helper writes an empty file."""
        wired_deps["mistapi"].api.v1.self.logs.listSelfAuditLogs.return_value = MagicMock(name="resp")
        wired_deps["mistapi"].get_all.return_value = []  # WHY: no data returned.

        SelfExportUtils.audit_logs()  # WHY: exercise the empty-pagination branch.

        # WHY: empty-rows persist path writes without the api_function_name kwarg.
        wired_deps["DataExporter"].write_with_format_selection.assert_called_once_with([], "SelfAuditLogs.csv")


class TestAuditLogsExceptionPath:
    """`audit_logs()` swallows every collaborator error and logs an exception."""

    def test_exception_during_fetch_is_logged(
        self, wired_deps: dict[str, Any], caplog: pytest.LogCaptureFixture
    ) -> None:
        """A raised exception during the API call is caught + logged via logging.exception."""
        wired_deps["mistapi"].api.v1.self.logs.listSelfAuditLogs.side_effect = RuntimeError("boom")  # WHY: fail.

        with caplog.at_level(logging.ERROR, logger="root"):  # WHY: logging.exception logs at ERROR.
            SelfExportUtils.audit_logs()  # WHY: exercise exception branch.

        # WHY: error log contains the SUT's contextual prefix.
        assert any("Failed to export self audit logs" in rec.message for rec in caplog.records)
        # WHY: since fetch failed, no data was persisted.
        wired_deps["DataExporter"].write_with_format_selection.assert_not_called()

    def test_exception_during_pagination_is_logged(
        self, wired_deps: dict[str, Any], caplog: pytest.LogCaptureFixture
    ) -> None:
        """An exception raised by mistapi.get_all is also caught."""
        wired_deps["mistapi"].api.v1.self.logs.listSelfAuditLogs.return_value = MagicMock(name="resp")
        wired_deps["mistapi"].get_all.side_effect = ValueError("pagination failure")  # WHY: fail after API call.

        with caplog.at_level(logging.ERROR, logger="root"):  # WHY: capture error log.
            SelfExportUtils.audit_logs()  # WHY: exercise exception branch.

        assert any("Failed to export self audit logs" in rec.message for rec in caplog.records)  # WHY: error logged.
        wired_deps["DataExporter"].write_with_format_selection.assert_not_called()  # WHY: no write on failure.

    def test_info_log_before_fetch(self, wired_deps: dict[str, Any], caplog: pytest.LogCaptureFixture) -> None:
        """The 'Starting export' info log fires before any API interaction."""
        wired_deps["mistapi"].api.v1.self.logs.listSelfAuditLogs.return_value = MagicMock(name="resp")
        wired_deps["mistapi"].get_all.return_value = []  # WHY: no data so we focus on log ordering.

        with caplog.at_level(logging.INFO, logger="root"):  # WHY: INFO includes 'Starting export'.
            SelfExportUtils.audit_logs()  # WHY: exercise the log-emission path.

        assert any(
            "Starting export of self (admin account) audit logs" in rec.message for rec in caplog.records
        )  # WHY: exact message contract preserved.

    def test_calls_are_ordered_dynamic_lookback_then_api(self, wired_deps: dict[str, Any]) -> None:
        """The lookback helper runs before the API call so duration reflects lookup result."""
        wired_deps["mistapi"].api.v1.self.logs.listSelfAuditLogs.return_value = MagicMock(name="resp")
        wired_deps["mistapi"].get_all.return_value = []  # WHY: focus on ordering.

        order_manager = MagicMock()  # WHY: call-ordering witness.
        order_manager.attach_mock(wired_deps["TimeUtils"].get_dynamic_lookback_hours, "lookback")
        order_manager.attach_mock(wired_deps["TimeUtils"].log_dynamic_lookback, "log_lookback")
        order_manager.attach_mock(wired_deps["mistapi"].api.v1.self.logs.listSelfAuditLogs, "api")

        SelfExportUtils.audit_logs()  # WHY: exercise the full flow.

        assert order_manager.mock_calls[:3] == [  # WHY: exact prefix of the call sequence.
            call.lookback(24, 1),
            call.log_lookback("self audit logs export", 6),
            call.api(wired_deps["apisession"], duration="6h", limit=1000),
        ]
