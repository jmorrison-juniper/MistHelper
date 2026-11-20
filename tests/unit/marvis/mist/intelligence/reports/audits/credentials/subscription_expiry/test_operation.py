"""Tests for subscription expiry report orchestration."""

from __future__ import annotations  # Keep annotations import-safe during test collection.

from dataclasses import dataclass, field  # Build compact fake dependency classes.
from datetime import date  # Build deterministic report contexts.

from src.mist.intelligence.reports.subscription_expiry.client import (
    JsiAccountNotLinkedError,
    SubscriptionExpiryClientError,
)
from src.mist.intelligence.reports.subscription_expiry.model import (
    CONTRACT_RECORD_ABSENT_NOTE,
    MISSING_VALUE,
    STATE_UNSUPPORTED,
    JsiContractSource,
    LicenseSummarySource,
    LicenseUsageSource,
    OrganizationScope,
    ReportContext,
)
from src.mist.intelligence.reports.subscription_expiry.operation import (
    CONTRACT_FILENAME,
    SUBSCRIPTION_FILENAME,
    CrossOrgSubscriptionInventoryReport,
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
        fieldnames: list[str] | None = None,
        backend_options: object | None = None,
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
    contract_row = exporter.calls[1][0][0]  # Read the empty-contract placeholder row from the export payload.
    assert contract_row["serial"] == MISSING_VALUE  # Identity stays visibly absent when JSI returns no records.
    assert contract_row["contract_state"] == STATE_UNSUPPORTED  # The row states that contract support is absent.
    assert contract_row["note"] == CONTRACT_RECORD_ABSENT_NOTE  # The row explains the missing JSI contract record.
    assert "Expired: 0" in captured  # Empty contract rows produce zero bucket counts.


def test_cross_org_report_exports_linked_reports(capsys: object) -> None:
    """The cross-org operation exports four exporter calls plus a header-only contract report."""
    exporter = FakeExporter()  # Capture export calls without file I/O.
    dependencies = FakeDependencies(exporter)  # Inject the fake exporter.

    class FakeCrossOrgClient:
        """Fake cross-org client with one successful organization."""

        def discover_organizations(self, _org_id: str, _org_name: str) -> tuple[list[object], list[object]]:
            return [
                OrganizationScope(
                    org_id="org-1",
                    org_name="T-Mobile",
                    source="direct",
                    request_status="success",
                )
            ], []  # Return one synthetic authorized organization.

        def fetch_license_summary(self, _org_id: str) -> LicenseSummarySource:
            return LicenseSummarySource(
                entitled={"SUB-SSR": 2},
                licenses=[{"type": "SUB-SSR", "quantity": 2, "end_time": "2027-01-31"}],
            )

        def fetch_license_usage_by_site(self, _org_id: str) -> list[LicenseUsageSource]:
            return [LicenseUsageSource(usages={"SUB-SSR": 1})]

        def fetch_inventory(self, _org_id: str) -> list[dict[str, object]]:
            return [
                {
                    "serial": "AP1",
                    "mac": "mac-ap",
                    "model": "AP43",
                    "type": "ap",
                    "site_id": "site-1",
                    "site_name": "HQ",
                    "connected": True,
                },
                {
                    "serial": "SSR1",
                    "mac": "mac-ssr",
                    "model": "SSR130",
                    "type": "gateway",
                },
            ]

        def search_jsi_assets_and_contracts(self, _org_id: str) -> list[JsiContractSource]:
            return []

    CrossOrgSubscriptionInventoryReport._run_with_client(
        "org-1",
        "T-Mobile",
        FakeCrossOrgClient(),
        dependencies,
    )  # Run the synthetic cross-org operation.
    filenames = [call[1] for call in exporter.calls]  # Read export names.
    captured = capsys.readouterr().out  # Capture the console summary.
    assert len(filenames) == 7  # Header-only contract evidence writes no exporter call.
    assert "CrossOrgOrganizationStatus.csv" in filenames  # Organization status is present.
    assert "CrossOrgSubscriptionPurchase.csv" in filenames  # Purchase records are present.
    assert "CrossOrgSubscriptionBalance.csv" in filenames  # Balance records are present.
    assert "CrossOrgDeployedInventory.csv" in filenames  # Deployed inventory detail is present.
    assert "CrossOrgDeployedInventorySummary.csv" in filenames  # Deployed inventory summary is present.
    assert "CrossOrgInventorySummary.csv" in filenames  # Combined deployed and stock summary is present.
    assert "CrossOrgStockInventory.csv" in filenames  # Stock inventory is present.
    assert "CrossOrgContractEvidence.csv" not in filenames  # Header-only contract evidence uses a direct file write.
    assert "Cross-org subscription inventory summary:" in captured  # The console summary is printed.
    assert "Organization inventory rows: 2" in captured  # The deployed and stock counts combine once.


def test_cross_org_empty_export_writes_header_only(tmp_path: object, monkeypatch: object) -> None:
    """An empty report writes headers and no fake Missing data row."""
    import csv

    data_path = tmp_path / "data"  # Isolate the empty report under pytest temp storage.
    monkeypatch.chdir(tmp_path)  # Make the report write inside the test directory.
    fieldnames = ["org_id", "org_name", "source", "request_status"]  # Use a stable header contract.
    CrossOrgSubscriptionInventoryReport._write_empty_csv("EmptyCrossOrg.csv", fieldnames)  # Write headers.
    output_path = data_path / "EmptyCrossOrg.csv"  # Resolve the isolated output path.
    with output_path.open(newline="", encoding="utf-8") as csv_file:  # Read the generated CSV.
        reader = csv.DictReader(csv_file)  # Parse header and rows.
        rows = list(reader)  # Materialize data rows.
    assert reader.fieldnames == fieldnames  # Preserve the exact header order.
    assert rows == []  # No fake Missing row exists.


def test_cross_org_empty_export_uses_fallback_when_stable_name_is_locked(
    tmp_path: object,
    monkeypatch: object,
) -> None:
    """A locked stable report name produces a visible timestamped fallback file."""
    import csv

    data_path = tmp_path / "data"  # Isolate locked output under pytest temp storage.
    data_path.mkdir()  # Create the report directory for the negative write test.
    stable_path = data_path / "LockedCrossOrg.csv"  # Select the stable target name.
    fieldnames = ["org_id", "org_name", "source", "request_status"]  # Use a stable header contract.
    real_open = type(stable_path).open  # Preserve the real pathlib open method.

    def deny_stable_open(candidate: object, *args: object, **kwargs: object) -> object:
        if str(candidate).replace("/", "\\").endswith("LockedCrossOrg.csv"):  # Match stable relative or absolute path.
            raise PermissionError(13, "locked by another process", str(candidate))
        return real_open(candidate, *args, **kwargs)  # Allow the timestamped fallback write.

    monkeypatch.chdir(tmp_path)  # Resolve data relative to the isolated workspace.
    monkeypatch.setattr(type(stable_path), "open", deny_stable_open)  # Simulate a Windows file lock.
    fallback_path = CrossOrgSubscriptionInventoryReport._write_empty_csv(
        "LockedCrossOrg.csv",
        fieldnames,
    )  # Write the fallback header.
    assert fallback_path != stable_path  # The stable locked name is not reused.
    assert fallback_path.exists()  # The fallback file must be visible.
    assert fallback_path.stem.startswith("LockedCrossOrg_")  # The fallback name carries a timestamp.
    with fallback_path.open(newline="", encoding="utf-8") as csv_file:  # Read the fallback CSV.
        reader = csv.DictReader(csv_file)  # Parse header-only output.
        rows = list(reader)  # Materialize the zero data rows.
    assert reader.fieldnames == fieldnames  # Preserve the exact header contract.
    assert rows == []  # The fallback remains header-only.


def test_cross_org_populated_export_uses_fallback_when_stable_name_is_locked(
    tmp_path: object,
    monkeypatch: object,
) -> None:
    """A populated report writes every row to a UTC fallback when the stable file is locked."""
    import csv

    data_path = tmp_path / "data"  # Isolate locked output under pytest temp storage.
    data_path.mkdir()  # Create the report directory for the negative write test.
    stable_path = data_path / "LockedCrossOrgPurchase.csv"  # Select the stable purchase name.
    fieldnames = ["org_id", "subscription_type", "quantity"]  # Use a small report contract.
    payload = [
        {"org_id": "org-1", "subscription_type": "SUB-AP", "quantity": 30},
        {"org_id": "org-2", "subscription_type": "SUB-SSR", "quantity": 12},
    ]  # Provide one row for each synthetic organization.
    real_open = type(stable_path).open  # Preserve the real pathlib open method.

    def deny_stable_open(candidate: object, *args: object, **kwargs: object) -> object:
        if str(candidate).replace("/", "\\").endswith("LockedCrossOrgPurchase.csv"):  # Match stable names.
            raise PermissionError(13, "locked by another process", str(candidate))
        return real_open(candidate, *args, **kwargs)  # Allow the timestamped fallback write.

    monkeypatch.chdir(tmp_path)  # Resolve data relative to the isolated workspace.
    monkeypatch.setattr(type(stable_path), "open", deny_stable_open)  # Simulate a Windows file lock.
    fallback_path = CrossOrgSubscriptionInventoryReport._write_payload_csv(
        payload,
        "LockedCrossOrgPurchase.csv",
        fieldnames,
    )  # Write the populated fallback.
    assert fallback_path != stable_path  # The stable locked name is not reused.
    assert fallback_path.exists()  # The fallback file must be visible.
    assert fallback_path.stem.startswith("LockedCrossOrgPurchase_")  # The fallback name carries a timestamp.
    with fallback_path.open(newline="", encoding="utf-8") as csv_file:  # Read the fallback CSV.
        reader = csv.DictReader(csv_file)  # Parse the populated report.
        rows = list(reader)  # Materialize every source row.
    assert reader.fieldnames == fieldnames  # Preserve the exact header contract.
    assert rows == [
        {"org_id": "org-1", "subscription_type": "SUB-AP", "quantity": "30"},
        {"org_id": "org-2", "subscription_type": "SUB-SSR", "quantity": "12"},
    ]  # Preserve every source row in the fallback.


def test_cross_org_msp_purchase_read_runs_once_for_duplicate_grants() -> None:
    """One MSP grant produces one MSP license request for all matched organizations."""
    exporter = FakeExporter()  # Capture export calls without file I/O.
    dependencies = FakeDependencies(exporter)  # Inject the fake exporter.
    fetched_msp_ids: list[str] = []  # Track MSP license request IDs.

    class FakeMspCrossOrgClient:
        """Fake client with duplicate organizations under one MSP grant."""

        def discover_organizations(self, _org_id: str, _org_name: str) -> tuple[list[object], list[object]]:
            organizations = [
                OrganizationScope(
                    org_id="org-1",
                    org_name="Campus",
                    msp_id="msp-1",
                    source="msp",
                    request_status="success",
                ),
                OrganizationScope(
                    org_id="org-2",
                    org_name="Branch",
                    msp_id="msp-1",
                    source="msp",
                    request_status="success",
                ),
            ]  # Return two organizations with one MSP grant.
            return organizations, []  # Return synthetic discovery scope.

        def fetch_msp_licenses(self, msp_id: str) -> dict[str, object]:
            fetched_msp_ids.append(msp_id)  # Record one MSP license request.
            return {
                "licenses": [
                    {"org_id": "org-1", "type": "SUB-SSR", "quantity": 2, "end_time": "2027-01-31"},
                    {"org_id": "org-2", "type": "SUB-AP", "quantity": 5, "end_time": "2027-02-28"},
                ]
            }  # Return one purchase row for each organization.

        def fetch_license_summary(self, _org_id: str) -> LicenseSummarySource:
            return LicenseSummarySource(entitled={}, licenses=[])  # Avoid organization purchase overlap.

        def fetch_license_usage_by_site(self, _org_id: str) -> list[LicenseUsageSource]:
            return []  # Return no synthetic usage data.

        def fetch_inventory(self, _org_id: str) -> list[dict[str, object]]:
            return []  # Return no stock inventory data.

        def search_jsi_assets_and_contracts(self, _org_id: str) -> list[JsiContractSource]:
            return []  # Return no contract evidence.

    CrossOrgSubscriptionInventoryReport._run_with_client(
        "org-1",
        "Campus",
        FakeMspCrossOrgClient(),
        dependencies,
    )  # Run synthetic duplicate-MSP orchestration.
    purchase_call = next(
        call for call in exporter.calls if call[1] == "CrossOrgSubscriptionPurchase.csv"
    )  # Locate the purchase report export.
    assert fetched_msp_ids == ["msp-1"]  # The duplicate grant causes one MSP request.
    assert len(purchase_call[0]) == 2  # Each organization receives one matched MSP purchase row.


def test_cross_org_inventory_failure_keeps_missing_summary_and_partial_results() -> None:
    """A failed inventory read remains Missing while another organization succeeds."""
    exporter = FakeExporter()  # Capture export calls without file I/O.
    dependencies = FakeDependencies(exporter)  # Inject the fake exporter.

    class FakePartialInventoryClient:
        """Fake cross-org client with one inventory success and one inventory failure."""

        def discover_organizations(self, _org_id: str, _org_name: str) -> tuple[list[object], list[object]]:
            return [
                OrganizationScope(
                    org_id="org-1",
                    org_name="Failed Org",
                    msp_id="msp-1",
                    source="msp",
                    request_status="success",
                ),
                OrganizationScope(
                    org_id="org-2",
                    org_name="Working Org",
                    msp_id="msp-1",
                    source="msp",
                    request_status="success",
                ),
            ], []  # Return two synthetic authorized organizations.

        def fetch_license_summary(self, _org_id: str) -> LicenseSummarySource:
            return LicenseSummarySource(entitled={}, licenses=[])  # Avoid purchase overlap.

        def fetch_license_usage_by_site(self, _org_id: str) -> list[LicenseUsageSource]:
            return []  # Return no usage rows.

        def fetch_inventory(self, org_id: str) -> list[dict[str, object]]:
            if org_id == "org-1":  # Simulate one inventory denial.
                raise SubscriptionExpiryClientError("Inventory returned HTTP 403")
            return [
                {
                    "serial": "AP2",
                    "mac": "mac-ap",
                    "model": "AP43",
                    "type": "ap",
                    "site_id": "site-2",
                    "connected": True,
                }
            ]  # Return one deployed AP for the successful organization.

        def search_jsi_assets_and_contracts(self, _org_id: str) -> list[JsiContractSource]:
            return []  # Return no contract evidence.

    CrossOrgSubscriptionInventoryReport._run_with_client(
        "org-1",
        "Failed Org",
        FakePartialInventoryClient(),
        dependencies,
    )  # Run synthetic partial inventory orchestration.
    summary_call = next(
        call for call in exporter.calls if call[1] == "CrossOrgDeployedInventorySummary.csv"
    )  # Locate the deployed summary export.
    missing_row = next(row for row in summary_call[0] if row["org_id"] == "org-1")  # Find failed org.
    working_row = next(row for row in summary_call[0] if row["org_id"] == "org-2")  # Find successful org.
    assert missing_row["deployed_quantity"] == MISSING_VALUE  # The failed read remains Missing.
    assert missing_row["request_status"] == "failed"  # The failed inventory source is visible.
    assert working_row["deployed_quantity"] == 1  # The successful inventory count remains usable.
    assert working_row["request_status"] == "success"  # The successful inventory source is visible.
