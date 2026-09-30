"""Operation tests for the site variable audit."""

from __future__ import annotations  # Keep test annotations import-safe.

from typing import Any  # Type fake dependency seams.

import pytest  # Use pytest monkeypatch and exception assertions.

import src.reports.site_variable_audit.operation as operation_module  # Patch operation seams in one module.
from src.reports.site_variable_audit.operation import SiteVariableAudit  # Test the public operation class.
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
