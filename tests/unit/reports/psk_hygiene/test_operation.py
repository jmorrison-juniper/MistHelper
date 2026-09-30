"""Unit tests for PSK hygiene operation orchestration."""

from __future__ import annotations

import builtins
import logging
from typing import Any

from src.reports.psk_hygiene.operation import PskHygieneReport


class _FakeConfigUtils:
    """Resolve a fixed organization ID without prompts."""

    @staticmethod
    def get_cached_or_prompted_org_id() -> str:
        """Return a fixed organization ID."""
        return "org-1"  # Keep operation tests deterministic.


class _FakeDataExporter:
    """Capture export calls for assertions."""

    rows: list[dict[str, str | int | bool]] = []  # Store exported rows for tests.
    filename = ""  # Store the export file name for tests.
    api_function_name = ""  # Store the API function name for tests.

    @classmethod
    def write_with_format_selection(
        cls, rows: list[dict[str, str | int | bool]], filename: str, api_function_name: str
    ) -> None:
        """Capture a sanitized export call."""
        cls.rows = rows  # Save the exported rows for contract checks.
        cls.filename = filename  # Save the filename for contract checks.
        cls.api_function_name = api_function_name  # Save the source name for contract checks.


class _FakeResolver:
    """Provide operation dependencies without importing MistHelper.py."""

    apisession = object()  # Provide a fake authenticated session.
    ConfigUtils = _FakeConfigUtils  # Provide the organization resolver seam.
    DataExporter = _FakeDataExporter  # Provide the exporter seam.


class _FakeClient:
    """Provide PSK hygiene inputs without network access."""

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


def test_run_does_not_prompt(monkeypatch: Any) -> None:
    """The operation runs without calling input."""
    monkeypatch.setattr(builtins, "input", lambda prompt="": (_ for _ in ()).throw(AssertionError("prompt")))  # Fail.
    result = PskHygieneReport.run(
        client=_FakeClient(), dependency_resolver=_FakeResolver, output=lambda line: None
    )  # Run the operation with fake dependencies.
    assert result is True  # The operation should return a menu-test success value.


def test_export_contract_columns() -> None:
    """The export receives the required PSK hygiene columns."""
    PskHygieneReport.run(
        client=_FakeClient(), dependency_resolver=_FakeResolver, output=lambda line: None
    )  # Run the report with fake dependencies.
    row = _FakeDataExporter.rows[0]  # Read the captured export row.
    assert _FakeDataExporter.filename == "PskHygiene.csv"  # The output file name must match the contract.
    assert _FakeDataExporter.api_function_name == "pskHygieneReport"  # The source name must be stable.
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
    PskHygieneReport.run(client=_FakeClient(), dependency_resolver=_FakeResolver, output=output_lines.append)  # Run.
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
    PskHygieneReport.run(client=_FakeClient(), dependency_resolver=_FakeResolver, output=output_lines.append)  # Run.
    assert "Total PSKs reviewed: 1" in output_lines  # The total count should match one fake PSK.
    assert "Uncapped multi-use keys: 1" in output_lines  # The uncapped count should match the fake PSK.
    assert "Pending rotations: 1" in output_lines  # The rotation count should match the fake PSK.
    assert "Site-level WLANs are outside this report scope." in output_lines  # The scope statement is required.


def test_console_summary_redacts_secrets() -> None:
    """The console summary never includes secret values."""
    output_lines: list[str] = []  # Capture console summary lines.
    PskHygieneReport.run(client=_FakeClient(), dependency_resolver=_FakeResolver, output=output_lines.append)  # Run.
    summary = "\n".join(output_lines)  # Combine summary lines for a redaction check.
    assert "secret-value" not in summary  # The current passphrase must not reach the summary.
    assert "old-secret-value" not in summary  # The old passphrase must not reach the summary.
