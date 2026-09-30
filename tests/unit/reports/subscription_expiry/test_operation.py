"""Tests for subscription expiry report orchestration."""

from __future__ import annotations  # Keep annotations import-safe during test collection.

from dataclasses import dataclass, field  # Build compact fake dependency classes.
from datetime import date  # Build deterministic report contexts.

from src.reports.subscription_expiry.client import JsiAccountNotLinkedError
from src.reports.subscription_expiry.model import (
    MISSING_VALUE,
    JsiContractSource,
    LicenseSummarySource,
    LicenseUsageSource,
    ReportContext,
)
from src.reports.subscription_expiry.operation import (
    CONTRACT_FILENAME,
    SUBSCRIPTION_FILENAME,
    SubscriptionExpiryReport,
)


@dataclass
class FakeExporter:
    """Capture export calls without writing files."""

    calls: list[tuple[list[dict[str, object]], str, str]] = field(default_factory=list)  # Store export calls.

    def write_with_format_selection(
        self,
        data: list[dict[str, object]],
        filename: str,
        api_function_name: str,
    ) -> bool:
        """Record one export call."""
        self.calls.append((data, filename, api_function_name))  # Capture the export payload for assertions.
        return True  # Simulate a successful DataExporter write.


@dataclass
class FakeDependencies:
    """Hold fake operation dependencies."""

    DataExporter: FakeExporter  # Provide the exporter seam used by the operation.


class FakeClient:
    """Fake client that returns deterministic source data."""

    def fetch_license_summary(self, org_id: str) -> LicenseSummarySource:
        """Return source summary data."""
        return LicenseSummarySource(entitled={"SUB": 1}, licenses=[{"type": "SUB", "end_time": "2026-01-02"}])  # Fake.

    def fetch_license_usage_by_site(self, org_id: str) -> list[LicenseUsageSource]:
        """Return source usage data."""
        return [LicenseUsageSource(usages={"SUB": 1})]  # Fake one matching usage row.

    def search_jsi_assets_and_contracts(self, org_id: str) -> list[JsiContractSource]:
        """Return source contract data."""
        return [JsiContractSource(serial="A", model="AP", warranty_type="Active", eos_time="2027-02-01")]  # Fake.


class NoLinkedAccountClient(FakeClient):
    """Fake client for the JSI 400 no-linked-account path."""

    def search_jsi_assets_and_contracts(self, org_id: str) -> list[JsiContractSource]:
        """Raise the operation-level JSI no-linked-account signal."""
        raise JsiAccountNotLinkedError("No linked account")  # Simulate the client error path.


def test_report_orchestration_exports_both_reports_and_prints_summary(capsys: object) -> None:
    """The operation exports both files and prints summary counts."""
    exporter = FakeExporter()  # Capture export calls without file I/O.
    dependencies = FakeDependencies(exporter)  # Inject the fake exporter.
    context = ReportContext("org-1", date(2026, 1, 1))  # Use a fixed date for deterministic band scoring.
    SubscriptionExpiryReport._run_with_client(context, FakeClient(), dependencies)  # Run operation with fakes.
    filenames = [call[1] for call in exporter.calls]  # Read called output filenames.
    captured = capsys.readouterr().out  # Capture the console summary.
    assert filenames == [SUBSCRIPTION_FILENAME, CONTRACT_FILENAME]  # Both required files are exported in order.
    assert exporter.calls[0][0][0]["subscription_type"] == "SUB"  # Subscription payload is scored.
    assert exporter.calls[1][0][0]["serial"] == "A"  # Contract payload is scored.
    assert "Subscription expiry summary:" in captured  # Subscription summary heading is printed.
    assert "Contract expiry summary:" in captured  # Contract summary heading is printed.
    assert "0-30 days: 1" in captured  # Summary counts match scored subscription rows.


def test_report_continues_with_empty_contracts_for_no_linked_jsi_account(capsys: object) -> None:
    """The operation handles the JSI 400 path with an empty contract export."""
    exporter = FakeExporter()  # Capture export calls without file I/O.
    dependencies = FakeDependencies(exporter)  # Inject the fake exporter.
    context = ReportContext("org-1", date(2026, 1, 1))  # Use a fixed date for deterministic band scoring.
    SubscriptionExpiryReport._run_with_client(context, NoLinkedAccountClient(), dependencies)  # Run error path.
    captured = capsys.readouterr().out  # Capture the operator message and summary.
    assert "No Juniper account is linked" in captured  # The operator sees the clear JSI condition.
    assert exporter.calls[1][1] == CONTRACT_FILENAME  # The contract export still runs.
    assert exporter.calls[1][0][0]["serial"] == MISSING_VALUE  # DataExporter gets a header-safe placeholder row.
    assert "Expired: 0" in captured  # Empty contract rows produce zero bucket counts.
