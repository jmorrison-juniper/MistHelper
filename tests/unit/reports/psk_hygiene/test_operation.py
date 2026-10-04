"""Unit tests for PSK hygiene operation orchestration."""

from __future__ import annotations

import builtins
import logging
from collections.abc import Iterator
from typing import Any

import pytest

from src.mist.intelligence.reports.psk_hygiene.operation import PskHygieneReport


class _FakeConfigUtils:
    """Resolve a fixed organization ID without prompts."""

    @staticmethod
    def get_cached_org_id() -> str:
        """Return a fixed organization ID."""
        return "org-1"  # Keep operation tests deterministic.


class _FakeDataExporter:
    """Capture export calls for assertions."""

    rows: list[dict[str, str | int | bool]] = []  # Store exported rows for tests.
    filename = ""  # Store the export file name for tests.
    api_function_name = ""  # Store the API function name for tests.

    @classmethod
    def write_with_format_selection(
        cls,
        rows: list[dict[str, str | int | bool]],
        filename: str,
        api_function_name: str,
        fieldnames: list[str] | None = None,
    ) -> None:
        """Capture a sanitized export call."""
        cls.rows = rows  # Save the exported rows for contract checks.
        cls.filename = filename  # Save the filename for contract checks.
        cls.api_function_name = api_function_name  # Save the source name for contract checks.
        cls.fieldnames = fieldnames or []  # Save column order for contract checks.


class _FakeResolver:
    """Provide operation dependencies without importing MistHelper.py."""

    apisession = object()  # Provide a fake authenticated session.
    ConfigUtils = _FakeConfigUtils  # Provide the organization resolver seam.
    DataExporter = _FakeDataExporter  # Provide the exporter seam.


class _NoOrgConfigUtils:
    """Resolve no organization ID without prompting."""

    @staticmethod
    def get_cached_org_id() -> None:
        """Return no organization ID."""
        return None  # Force the report to use the fail-closed path.


class _NoOrgResolver:
    """Provide dependencies with no configured organization ID."""

    apisession = object()  # Provide a fake authenticated session.
    ConfigUtils = _NoOrgConfigUtils  # Provide a no-org resolver seam.
    DataExporter = _FakeDataExporter  # Provide the exporter seam.


class _FakeClient:
    """Provide PSK hygiene inputs without network access."""

    def __init__(self, apisession: object, org_id: str) -> None:
        """Store operation constructor inputs."""
        self.apisession = apisession  # Prove the operation passed the shared session.
        self.org_id = org_id  # Prove the operation passed the resolved organization.

    def fetch_psks(self) -> list[dict[str, Any]]:
        """Return fake PSK rows with secret fields."""
        return [  # Include secret fields to prove redaction.
            {
                "name": "Kitchen sensor",
                "ssid": "Facility",
                "role": "iot",
                "vlan": 20,
                "usage": 1,
                "max_usage": None,
                "mac": None,
                "passphrase": "secret-value",
                "old_passphrase": "old-secret-value",
            }
        ]

    def fetch_wlans(self) -> list[dict[str, Any]]:
        """Return fake organization WLAN rows."""
        return [{"ssid": "Facility"}]  # Match the fake PSK SSID.

    def fetch_templates(self) -> list[dict[str, Any]]:
        """Return fake organization template rows."""
        return []  # Keep the operation test focused on direct WLAN matching.


class _UnavailableWlanClient(_FakeClient):
    """Provide PSK inputs while making WLAN scope unavailable."""

    def fetch_wlans(self) -> list[dict[str, Any]]:
        """Raise the same way an unavailable WLAN endpoint can fail."""
        raise RuntimeError("wlan read failed")  # Force the operation to mark WLAN match as unknown.


@pytest.fixture(autouse=True)
def _operation_seams() -> Iterator[None]:
    """Replace operation seams without changing the no-argument handler."""
    original_client = PskHygieneReport.CLIENT_CLASS  # Save the production client seam.
    original_resolver = PskHygieneReport.DEPENDENCY_RESOLVER  # Save the production dependency seam.
    original_output = PskHygieneReport.OUTPUT  # Save the production console seam.
    _FakeDataExporter.rows = []  # Clear rows before each test.
    PskHygieneReport.CLIENT_CLASS = _FakeClient  # Use fake client inputs.
    PskHygieneReport.DEPENDENCY_RESOLVER = _FakeResolver  # Use fake runtime dependencies.
    PskHygieneReport.OUTPUT = lambda line: None  # Default tests do not need console text.
    yield  # Let the test run with fake seams.
    PskHygieneReport.CLIENT_CLASS = original_client  # Restore the production client seam.
    PskHygieneReport.DEPENDENCY_RESOLVER = original_resolver  # Restore the production dependency seam.
    PskHygieneReport.OUTPUT = original_output  # Restore the production console seam.


def test_run_does_not_prompt(monkeypatch: Any) -> None:
    """The operation runs without calling input."""
    monkeypatch.setattr(builtins, "input", lambda prompt="": (_ for _ in ()).throw(AssertionError("prompt")))  # Fail.
    result = PskHygieneReport.run()  # Run the no-argument menu handler with fake seams.
    assert result is True  # The operation should return a menu-test success value.


def test_export_contract_columns() -> None:
    """The export receives the required PSK hygiene columns."""
    PskHygieneReport.run()  # Run the report with fake dependencies.
    row = _FakeDataExporter.rows[0]  # Read the captured export row.
    assert _FakeDataExporter.filename == "PskHygiene.csv"  # The output file name must match the contract.
    assert _FakeDataExporter.api_function_name == "psk_hygiene_report"  # The source name must be stable.
    assert _FakeDataExporter.fieldnames == list(row)  # The CSV field order must match the exported row order.
    assert set(row) == {  # The exported row must contain exactly the required safe columns.
        "name",
        "ssid",
        "role",
        "vlan",
        "usage",
        "max_usage",
        "expire_time",
        "days_remaining",
        "rotation_pending",
        "old_passphrase_present",
        "wlan_match",
        "findings",
    }


def test_run_redacts_secrets_from_rows_logs_and_console(caplog: Any) -> None:
    """The operation never emits passphrase values."""
    output_lines: list[str] = []  # Capture console summary lines.
    caplog.set_level(logging.DEBUG)  # Capture debug logs for redaction proof.
    PskHygieneReport.OUTPUT = output_lines.append  # Capture console summary lines.
    PskHygieneReport.run()  # Run the no-argument handler.
    combined_output = "\n".join(output_lines)  # Combine console text for one redaction check.
    combined_rows = str(_FakeDataExporter.rows)  # Combine exported row values for one redaction check.
    assert "secret-value" not in combined_output  # The current passphrase must not reach console output.
    assert "old-secret-value" not in combined_output  # The old passphrase must not reach console output.
    assert "secret-value" not in caplog.text  # The current passphrase must not reach logs.
    assert "old-secret-value" not in caplog.text  # The old passphrase must not reach logs.
    assert "secret-value" not in combined_rows  # The current passphrase must not reach exported rows.
    assert "old-secret-value" not in combined_rows  # The old passphrase must not reach exported rows.
    assert _FakeDataExporter.rows[0]["old_passphrase_present"] is True  # Only the safe presence flag may remain.


def test_console_summary_counts_match_rows() -> None:
    """The console summary includes counts that match rows."""
    output_lines: list[str] = []  # Capture console summary lines.
    PskHygieneReport.OUTPUT = output_lines.append  # Capture console summary lines.
    PskHygieneReport.run()  # Run the no-argument handler.
    assert "Total PSKs reviewed: 1" in output_lines  # The total count should match one fake PSK.
    assert "Uncapped multi-use keys: 1" in output_lines  # The uncapped count should match the fake PSK.
    assert "Pending rotations: 1" in output_lines  # The rotation count should match the fake PSK.
    assert "Site-level WLANs are outside this report scope." in output_lines  # The scope statement is required.


def test_console_summary_redacts_secrets() -> None:
    """The console summary never includes secret values."""
    output_lines: list[str] = []  # Capture console summary lines.
    PskHygieneReport.OUTPUT = output_lines.append  # Capture console summary lines.
    PskHygieneReport.run()  # Run the no-argument handler.
    summary = "\n".join(output_lines)  # Combine summary lines for a redaction check.
    assert "secret-value" not in summary  # The current passphrase must not reach the summary.
    assert "old-secret-value" not in summary  # The old passphrase must not reach the summary.


def test_unavailable_wlan_scope_marks_wlan_match_unknown() -> None:
    """Unavailable organization WLAN data must not create a false orphan finding."""
    PskHygieneReport.CLIENT_CLASS = _UnavailableWlanClient  # Simulate a WLAN endpoint failure.
    result = PskHygieneReport.run()  # Run the no-argument menu handler.
    row = _FakeDataExporter.rows[0]  # Read the captured export row.
    assert result is True  # The PSK report should still export with unknown WLAN scope.
    assert row["wlan_match"] == "unknown"  # The match state must show incomplete scope.
    assert "orphan_ssid" not in str(row["findings"])  # Unknown scope must not create a false orphan finding.


def test_unavailable_wlan_scope_summary_states_unknown_orphan_findings() -> None:
    """Unavailable organization WLAN data must change the summary scope note."""
    output_lines: list[str] = []  # Capture console summary lines.
    PskHygieneReport.CLIENT_CLASS = _UnavailableWlanClient  # Simulate a WLAN endpoint failure.
    PskHygieneReport.OUTPUT = output_lines.append  # Capture the summary.
    PskHygieneReport.run()  # Run the no-argument menu handler.
    assert "Organization WLAN data was unavailable" in "\n".join(output_lines)  # Explain unknown orphan findings.


def test_missing_org_id_fails_closed_without_prompt(monkeypatch: Any) -> None:
    """Missing organization ID must fail without a prompt or export."""
    monkeypatch.delenv("org_id", raising=False)  # Remove lowercase environment fallback.
    monkeypatch.delenv("ORG_ID", raising=False)  # Remove uppercase environment fallback.
    PskHygieneReport.DEPENDENCY_RESOLVER = _NoOrgResolver  # Use the no-org dependency seam.
    result = PskHygieneReport.run()  # Run the no-argument handler.
    assert result is False  # The operation must fail closed.
    assert _FakeDataExporter.rows == []  # The operation must not export without an organization.
