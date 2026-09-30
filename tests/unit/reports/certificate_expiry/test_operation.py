"""Unit tests for the certificate expiry report operation."""

from __future__ import annotations  # Keep annotations import-safe during test collection.

import logging  # Capture operation logs for privacy and summary tests.
from datetime import UTC, datetime, timedelta  # Build stable fixture dates.
from pathlib import Path  # Read feature-owned evidence files.
from types import SimpleNamespace  # Build lightweight resolver fakes.

import pytest  # Provide monkeypatch and caplog fixtures.

from src.reports.certificate_expiry import operation  # Import the operation module for monkeypatching.
from src.reports.certificate_expiry.operation import CertificateExpiryReport  # Import the static handler under test.
from tests.unit.reports.certificate_expiry.test_model import CertificateFixtureFactory  # Reuse no-network PEM fixtures.


class ExporterStub:
    """Capture DataExporter calls without writing files."""

    calls: list[dict[str, object]] = []  # Store export calls for assertions.

    @classmethod
    def write_with_format_selection(
        cls,
        rows: list[dict[str, object]],
        filename: str,
        api_function_name: str | None = None,
        fieldnames: list[str] | None = None,
    ) -> bool:
        """Capture one export request."""
        cls.calls.append(
            {"rows": rows, "filename": filename, "api_function_name": api_function_name, "fieldnames": fieldnames}
        )  # Store the call contract.
        return True  # Simulate a successful export.


class ConfigStub:
    """Return a fixed organization without prompting."""

    @staticmethod
    def get_cached_or_prompted_org_id() -> str:
        """Return a fixed test organization."""
        return "org-1"  # Keep the operation no-prompt in tests.


class SourceDependencyResolverStub:
    """Provide operation dependencies through the expected resolver names."""

    ConfigUtils = ConfigStub  # Supply the organization resolver.
    DataExporter = ExporterStub  # Supply the exporter.
    apisession = object()  # Supply a non-network session object.


class ClientStub:
    """Return synthetic source payloads without network access."""

    payloads: dict[str, object] = {}  # Store payloads per test.
    failed_sources: list[str] = []  # Store failed sources per test.

    def __init__(self, session: object, org_id: str) -> None:
        """Capture constructor dependencies."""
        self.session = session  # Store the session for assertions if needed.
        self.org_id = org_id  # Store the org id for assertions if needed.

    def collect_sources(self) -> SimpleNamespace:
        """Return synthetic payloads."""
        return SimpleNamespace(
            payloads=self.payloads, failed_sources=self.failed_sources
        )  # Match the client result shape.


@pytest.fixture(autouse=True)
def operation_fixture(monkeypatch) -> None:
    """Replace external dependencies for every operation test."""
    ExporterStub.calls = []  # Clear captured export calls.
    ClientStub.payloads = {}  # Clear source payloads.
    ClientStub.failed_sources = []  # Clear failed sources.
    monkeypatch.setattr(
        operation, "SourceDependencyResolver", SourceDependencyResolverStub
    )  # Replace the resolver seam.
    monkeypatch.setattr(operation, "CertificateExpiryClient", ClientStub)  # Replace the client seam.


def test_operation_runs_without_prompt_and_exports_contract() -> None:
    """The static run handler writes the expected exporter contract."""
    generated_at = datetime.now(tz=UTC)  # Build a current fixture expiry window.
    ClientStub.payloads = {
        "listOrgDevicesStats": [{"name": "ap-1", "cert_expiry": int((generated_at + timedelta(days=10)).timestamp())}]
    }  # Add one device row.
    CertificateExpiryReport.run()  # Run the operation with fakes.
    call = ExporterStub.calls[0]  # Read the captured export call.
    assert call["filename"] == "CertificateExpiry.csv"  # Verify the required file name.
    assert call["api_function_name"] == "certificate_expiry_report"  # Verify the required endpoint name.
    assert call["fieldnames"] == [
        "org_id",
        "source_name",
        "scope",
        "owner_name",
        "subject",
        "issuer",
        "serial",
        "not_after",
        "days_remaining",
        "band",
        "note",
    ]  # Verify columns.
    assert call["rows"][0]["owner_name"] == "ap-1"  # Verify the row came from the fixture.


def test_mixed_source_resilience_keeps_valid_rows() -> None:
    """One unparsable value does not remove a valid row."""
    generated_at = datetime.now(tz=UTC)  # Build a current fixture expiry window.
    good_pem = CertificateFixtureFactory.pem(
        generated_at + timedelta(days=60), "good.example"
    )  # Build one valid certificate.
    ClientStub.payloads = {
        "listOrgCertificates": [{"name": "ca-good", "cert": good_pem}, {"name": "ca-bad", "cert": "not a certificate"}]
    }  # Mix good and bad values.
    CertificateExpiryReport.run()  # Run the operation with fakes.
    rows = ExporterStub.calls[0]["rows"]  # Read exported rows.
    assert len(rows) == 2  # Verify both rows survived.
    assert {row["note"] for row in rows} == {"", "unparsable"}  # Verify the parse failure is visible.


def test_privacy_logs_and_rows_do_not_expose_certificate_text(caplog) -> None:
    """Logs and output rows omit PEM bodies and private-key markers."""
    generated_at = datetime.now(tz=UTC)  # Build a current fixture expiry window.
    pem = CertificateFixtureFactory.pem(
        generated_at + timedelta(days=60), "private.example"
    )  # Build a valid certificate.
    ClientStub.payloads = {
        "listOrgCertificates": [
            {"name": "ca-safe", "cert": pem},
            {"name": "ca-key", "cert": "-----BEGIN PRIVATE KEY-----secret"},
        ]
    }  # Mix PEM and key-like text.
    caplog.set_level(logging.DEBUG)  # Capture operation and model logs.
    CertificateExpiryReport.run()  # Run the operation with fakes.
    output_text = str(ExporterStub.calls[0]["rows"])  # Inspect the exported metadata only.
    log_text = caplog.text  # Inspect captured log messages.
    assert "BEGIN CERTIFICATE" not in output_text  # Verify no PEM marker in rows.
    assert "BEGIN PRIVATE KEY" not in output_text  # Verify no private-key marker in rows.
    assert "BEGIN CERTIFICATE" not in log_text  # Verify no PEM marker in logs.
    assert "BEGIN PRIVATE KEY" not in log_text  # Verify no private-key marker in logs.


def test_console_summary_counts_match_export_rows(capsys) -> None:
    """Band summary counts match exported rows."""
    generated_at = datetime.now(tz=UTC)  # Build a current fixture expiry window.
    ClientStub.payloads = {
        "listOrgDevicesStats": [
            {"name": "expired", "cert_expiry": int((generated_at - timedelta(days=1)).timestamp())},
            {"name": "soon", "cert_expiry": int((generated_at + timedelta(days=10)).timestamp())},
            {"name": "planned", "cert_expiry": int((generated_at + timedelta(days=45)).timestamp())},
            {"name": "later", "cert_expiry": int((generated_at + timedelta(days=120)).timestamp())},
        ]
    }  # Cover all bands.
    CertificateExpiryReport.run()  # Run the operation with fakes.
    rows = ExporterStub.calls[0]["rows"]  # Read exported rows.
    console_text = capsys.readouterr().out  # Capture console summary lines.
    expected_counts = {
        band: sum(1 for row in rows if row["band"] == band) for band in ("expired", "0-30", "31-90", "more than 90")
    }  # Count exported rows by band.
    for band, count in expected_counts.items():  # Verify each summary line.
        assert f"Certificate expiry band {band}: {count}" in console_text  # Match the console contract.


def test_failed_source_summary_is_separate_from_empty_sources(caplog) -> None:
    """Failed sources are reported separately from empty sources."""
    ClientStub.payloads = {"listOrgDevicesStats": []}  # Provide one empty successful source.
    ClientStub.failed_sources = ["listOrgCertificates"]  # Simulate one failed source.
    caplog.set_level(logging.WARNING)  # Capture warning lines.
    CertificateExpiryReport.run()  # Run the operation with fakes.
    assert "Certificate expiry failed sources: listOrgCertificates" in caplog.text  # Verify failed source summary.


def test_wiring_manifest_contains_deferred_sections() -> None:
    """The wiring manifest keeps integration-only files deferred."""
    root = Path(__file__).resolve().parents[4]  # Resolve the repository root from the test path.
    wiring = (root / "specs" / "3553-certificate-expiry-report" / "wiring.md").read_text(
        encoding="utf-8"
    )  # Read the feature-owned manifest.
    for text in (
        "Menu entries",
        "OperationRegistry comment",
        "Primary key strategies",
        "copilot-instructions category table",
        "Import line for MistHelper.py",
        "Deferred integration notes",
    ):  # Check required sections.
        assert text in wiring  # Verify each required section exists.
    for path in (
        "MistHelper.py",
        "src/utils/operation_registry.py",
        "src/refactors/endpoint_primary_key_strategies.py",
        "README.md",
        "generated menu references",
    ):  # Check deferred paths.
        assert path in wiring  # Verify each integration-only path is named.


def test_release_note_fragment_exists() -> None:
    """The release note fragment exists and names issue #3553."""
    root = Path(__file__).resolve().parents[4]  # Resolve the repository root from the test path.
    release_note = root / "changelog.d" / "issue-3553-certificate-expiry-report.md"  # Build the fragment path.
    content = release_note.read_text(encoding="utf-8")  # Read the fragment content.
    assert "### Added" in content  # Verify the required heading.
    assert "#3553" in content  # Verify the issue reference.
