"""Operation tests for the site variable audit."""

from __future__ import annotations  # Keep test annotations import-safe.

from typing import Any  # Type fake dependency seams.

import pytest  # Use pytest monkeypatch and exception assertions.

import src.mist.intelligence.reports.site_variable_audit.operation as operation_module  # Import the moved dependency.
from src.mist.intelligence.reports.site_variable_audit.operation import (
    SiteVariableAudit,
)  # Test the public operation class.
from tests.unit.reports.site_variable_audit.site_variable_audit_fixtures_test import (  # Reuse offline records.
    SiteVariableAuditFixtures,
)


class _FakeConfigUtils:
    """Resolve a fixed organization ID for operation tests."""

    @staticmethod
    def get_cached_or_prompted_org_id() -> str:
        """Return a deterministic organization ID."""
        return "org-1"  # Avoid prompts and network calls in unit tests.


class _FakeDataExporter:
    """Capture export calls without writing files."""

    calls: list[tuple[list[dict[str, Any]], str, str]] = []  # Store rows, filename, and API name.

    @classmethod
    def write_with_format_selection(
        cls,
        rows: list[dict[str, Any]],
        filename: str,
        api_function_name: str,
    ) -> bool:
        """Capture one DataExporter call."""
        cls.calls.append((rows, filename, api_function_name))  # Store the export request for assertions.
        return True  # Match DataExporter success behavior for the operation.


class _FakeResolver:
    """Provide resolver-owned dependencies for operation tests."""

    apisession = "session"  # Supply a non-empty Mist session sentinel.
    ConfigUtils = _FakeConfigUtils  # Supply the fixed org helper.
    DataExporter = _FakeDataExporter  # Supply the export capture helper.
    IS_TEST_MODE = True  # Prove run does not prompt in test mode.


class _MissingOrgConfigUtils:
    """Return no organization ID for validation tests."""

    @staticmethod
    def get_cached_or_prompted_org_id() -> str:
        """Return an empty organization ID."""
        return ""  # Force the operation to stop before any Mist read.


class _MissingOrgResolver:
    """Provide dependencies with no organization ID."""

    apisession = "session"  # Keep the session valid so only org validation fails.
    ConfigUtils = _MissingOrgConfigUtils  # Supply the missing organization helper.
    DataExporter = _FakeDataExporter  # Supply the export capture helper.
    IS_TEST_MODE = True  # Keep test mode visible to operation logging.


class _FakeClient:
    """Return offline records for operation tests."""

    def __init__(self, apisession: Any, org_id: str) -> None:
        """Capture constructor arguments without network access."""
        assert apisession == "session"  # Prove the operation passes the resolver session.
        assert org_id == "org-1"  # Prove the operation passes the resolved organization.

    def fetch(self) -> dict[str, list[dict[str, Any]]]:
        """Return the missing-variable fixture records."""
        fixture = SiteVariableAuditFixtures.missing_gateway_variable()  # Build offline records for the operation.
        return fixture.to_records()  # Return the exact client output shape.


class _FailingClient:
    """Raise a Mist read error before any report is written."""

    def __init__(self, apisession: Any, org_id: str) -> None:
        """Accept the same constructor shape as the real client."""
        assert apisession == "session"  # Prove the operation passes the resolver session.
        assert org_id == "org-1"  # Prove the operation passes the resolved organization.

    def fetch(self) -> dict[str, list[dict[str, Any]]]:
        """Raise the clear read error used by the real client."""
        raise operation_module.SiteVariableAuditReadError(
            "Site variable audit could not read listOrgSites."
        )  # Stop before any success-shaped output.


def test_run_writes_both_reports_without_prompt(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prove run writes both required reports from fixture data."""
    _FakeDataExporter.calls = []  # Clear prior export calls for deterministic assertions.
    messages: list[str] = []  # Capture the console summary without printing.
    monkeypatch.setattr(operation_module, "SourceDependencyResolver", _FakeResolver)  # Use offline resolver.
    monkeypatch.setattr(operation_module, "SiteVariableAuditClient", _FakeClient)  # Use offline client.
    monkeypatch.setattr(
        operation_module, "echo", lambda message, *args: messages.append(message % args)
    )  # Capture echo.
    SiteVariableAudit.run()  # Run the operation with no positional argument.
    filenames = [call[1] for call in _FakeDataExporter.calls]  # Collect exported filenames.
    assert filenames == ["SiteVariableAudit.csv", "SiteVariableSummary.csv"]  # Prove both reports are exported.
    api_names = [call[2] for call in _FakeDataExporter.calls]  # Collect DataExporter strategy names.
    assert api_names == ["siteVariableAudit", "siteVariableSummary"]  # Prove both primary-key strategies are distinct.
    assert _FakeDataExporter.calls[0][0][0]["site_name"] == "Alpha"  # Prove the audit row names the missing site.


def test_console_summary_counts_distinct_sites_with_findings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prove the console summary reports distinct missing-site count."""
    _FakeDataExporter.calls = []  # Clear prior export calls for deterministic assertions.
    messages: list[str] = []  # Capture summary text for assertions.
    monkeypatch.setattr(operation_module, "SourceDependencyResolver", _FakeResolver)  # Use offline resolver.
    monkeypatch.setattr(operation_module, "SiteVariableAuditClient", _FakeClient)  # Use offline client.
    monkeypatch.setattr(
        operation_module, "echo", lambda message, *args: messages.append(message % args)
    )  # Capture echo.
    SiteVariableAudit.run()  # Run the operation with no positional argument.
    assert "1 site(s) with missing variables" in messages[0]  # Prove the distinct missing-site count is shown.


def test_missing_organization_data_stops_before_export(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prove missing organization data reports a clear error and writes nothing."""
    _FakeDataExporter.calls = []  # Clear prior export calls for deterministic assertions.
    monkeypatch.setattr(operation_module, "SourceDependencyResolver", _MissingOrgResolver)  # Use missing org data.
    with pytest.raises(RuntimeError, match="organization ID is unavailable"):  # Prove the operator-facing error.
        SiteVariableAudit.run()  # Run the operation with no prompt or network call.
    assert _FakeDataExporter.calls == []  # Prove no success-shaped output is written.


def test_failed_mist_read_stops_before_export(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prove a failed Mist read reports a clear error and writes nothing."""
    _FakeDataExporter.calls = []  # Clear prior export calls for deterministic assertions.
    monkeypatch.setattr(operation_module, "SourceDependencyResolver", _FakeResolver)  # Use valid resolver data.
    monkeypatch.setattr(operation_module, "SiteVariableAuditClient", _FailingClient)  # Force a read failure.
    with pytest.raises(operation_module.SiteVariableAuditReadError, match="listOrgSites"):  # Prove read error text.
        SiteVariableAudit.run()  # Run the operation with no report output.
    assert _FakeDataExporter.calls == []  # Prove the failed read writes no reports.
