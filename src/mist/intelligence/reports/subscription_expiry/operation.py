"""Operation orchestration for the subscription and contract expiry report."""

from __future__ import annotations  # Keep annotations import-safe during tests.

import csv  # Write explicit header-only CSV files for empty reports.
import logging  # Record operation actions for operator traceability.
import os  # Read direct organization and customer name settings without prompts.
from dataclasses import dataclass, replace  # Preserve report payload and organization status.
from datetime import UTC, date, datetime  # Stamp fallback CSV names and type report dates.
from pathlib import Path  # Build data paths with the platform path library.
from typing import Any  # Type injectable test seams without importing root modules.

from src.foundation.models.dataclasses.export_backend_options import ExportBackendOptions  # Force CSV for the report.
from src.foundation.runtime.config.source_dependency_resolver import (
    SourceDependencyResolver,
)  # Resolve root-owned runtime dependencies.
from src.mist.intelligence.reports.subscription_expiry.client import (
    JsiAccountNotLinkedError,
    SubscriptionExpiryClient,
    SubscriptionExpiryClientError,
)
from src.mist.intelligence.reports.subscription_expiry.model import (
    CONTRACT_BUCKETS,
    CONTRACT_RECORD_ABSENT_NOTE,
    MISSING_VALUE,
    STATE_UNSUPPORTED,
    SUBSCRIPTION_BANDS,
    ConsoleSummary,
    ContractExpiryRow,
    CrossOrgSubscriptionInventoryModel,
    JsiContractSource,
    LicenseSummarySource,
    LicenseUsageSource,
    OrganizationScope,
    ReportContext,
    SubscriptionExpiryModel,
    SubscriptionExpiryRow,
)

logger = logging.getLogger(__name__)  # Give this module a stable logger name.
SUBSCRIPTION_FILENAME = "SubscriptionExpiry.csv"  # Required subscription report output file.
CONTRACT_FILENAME = "ContractExpiry.csv"  # Required contract report output file.
SUBSCRIPTION_API_NAME = "SubscriptionExpiryReport"  # Future wiring can add a primary-key strategy for this output.
CONTRACT_API_NAME = "ContractExpiryReport"  # Future wiring can add a primary-key strategy for this output.
SUBSCRIPTION_COLUMNS = (  # Preserve required columns when there are no source subscription rows.
    "subscription_type",
    "entitled",
    "usage",
    "status",
    "end_date",
    "days_remaining",
    "band",
)
CONTRACT_COLUMNS = (  # Preserve required columns when there are no source contract rows.
    "serial",
    "model",
    "contract_status",
    "contract_state",
    "end_date",
    "bucket",
    "note",
)
SOURCE_ATTRIBUTION = (
    "MistOrgLicensingComparison by jmorrison-juniper is licensed under "
    "CC BY-NC-SA 4.0 (https://creativecommons.org/licenses/by-nc-sa/4.0/)."
)  # Preserve source terms in the migrated report.
CROSS_ORG_ORGANIZATION_STATUS_FILENAME = "CrossOrgOrganizationStatus.csv"
CROSS_ORG_SUBSCRIPTION_PURCHASE_FILENAME = "CrossOrgSubscriptionPurchase.csv"
CROSS_ORG_SUBSCRIPTION_BALANCE_FILENAME = "CrossOrgSubscriptionBalance.csv"
CROSS_ORG_DEPLOYED_INVENTORY_FILENAME = "CrossOrgDeployedInventory.csv"
CROSS_ORG_DEPLOYED_INVENTORY_SUMMARY_FILENAME = "CrossOrgDeployedInventorySummary.csv"
CROSS_ORG_STOCK_INVENTORY_FILENAME = "CrossOrgStockInventory.csv"
CROSS_ORG_CONTRACT_EVIDENCE_FILENAME = "CrossOrgContractEvidence.csv"


@dataclass
class CrossOrgReportPayload:
    """Hold one menu 308 export payload for five or more linked reports."""

    organization_rows: list[dict[str, Any]]
    purchase_rows: list[dict[str, Any]]
    balance_rows: list[dict[str, Any]]
    deployed_inventory_rows: list[dict[str, Any]]
    deployed_inventory_summary_rows: list[dict[str, Any]]
    inventory_summary_rows: list[dict[str, Any]]
    stock_rows: list[dict[str, Any]]
    contract_rows: list[dict[str, Any]]


class SubscriptionExpiryReport:
    """Run the subscription and contract expiry report."""

    @staticmethod
    def run() -> None:
        """Resolve context, fetch source data, score rows, export reports, and print a summary."""
        logger.info("Starting the subscription and contract expiry report")  # Log operation start.
        dependencies = SourceDependencyResolver  # Resolve runtime dependencies without importing MistHelper.py.
        context = SubscriptionExpiryReport._resolve_context(dependencies)  # Resolve the active organization.
        client = SubscriptionExpiryClient(dependencies.apisession)  # Build the SDK seam with the active session.
        SubscriptionExpiryReport._run_with_client(context, client, dependencies)  # Execute the report workflow.
        logger.debug("Finished the subscription and contract expiry report")  # Log operation completion.

    @staticmethod
    def _run_with_client(context: ReportContext, client: SubscriptionExpiryClient, dependencies: Any) -> None:
        """Execute the report with injectable dependencies for unit tests."""
        logger.info("Fetching subscription expiry source data")  # Log before source collection.
        summary = client.fetch_license_summary(context.org_id)  # Fetch entitlement and license date source.
        usages = client.fetch_license_usage_by_site(context.org_id)  # Fetch usage source.
        contracts = SubscriptionExpiryReport._fetch_contracts(client, context.org_id)  # Fetch contract source.
        logger.debug("Fetched %d usage rows and %d contract rows", len(usages), len(contracts))  # Log source counts.
        logger.info("Scoring subscription expiry rows")  # Log before subscription scoring.
        subscription_rows = SubscriptionExpiryModel.score_subscriptions(context, summary, usages)  # Score rows.
        logger.debug("Scored %d subscription expiry rows", len(subscription_rows))  # Log scored row count.
        logger.info("Scoring contract expiry rows")  # Log before contract scoring.
        contract_rows = SubscriptionExpiryModel.score_contracts(context, contracts)  # Score rows.
        logger.debug("Scored %d contract expiry rows", len(contract_rows))  # Log scored row count.
        SubscriptionExpiryReport._export_reports(subscription_rows, contract_rows, dependencies)  # Export both CSVs.
        summary_counts = SubscriptionExpiryModel.build_summary(subscription_rows, contract_rows)  # Count summary.
        SubscriptionExpiryReport._print_summary(summary_counts)  # Print operator summary.

    @staticmethod
    def _resolve_context(dependencies: Any) -> ReportContext:
        """Resolve the active organization context through SourceDependencyResolver."""
        logger.info("Resolving the organization for the subscription expiry report")  # Log before org resolution.
        org_id = dependencies.ConfigUtils.get_cached_or_prompted_org_id()  # Match existing menu resolver pattern.
        logger.debug(
            "Resolved organization for the subscription expiry report"
        )  # Do not repeat potentially secret data.
        return ReportContext(org_id=str(org_id))  # Build a report context with the UTC run date.

    @staticmethod
    def _fetch_contracts(client: SubscriptionExpiryClient, org_id: str) -> list[Any]:
        """Fetch JSI contracts, or continue with an empty report when no account is linked."""
        try:
            logger.info("Fetching contract expiry source data")  # Log before the JSI source call.
            contracts = client.search_jsi_assets_and_contracts(org_id)  # Fetch JSI contracts through the client seam.
            logger.debug("Fetched %d contract source rows", len(contracts))  # Log contract source count.
            return contracts  # Return fetched contract rows.
        except JsiAccountNotLinkedError:
            logger.warning(
                "No Juniper account is linked. ContractExpiry.csv will contain no contract rows."
            )  # Clear path.
            print("No Juniper account is linked. Contract expiry data is unavailable.")  # Tell the operator.
            return []  # Continue with an empty contract report by requirement.

    @staticmethod
    def _export_reports(
        subscription_rows: list[SubscriptionExpiryRow],
        contract_rows: list[ContractExpiryRow],
        dependencies: Any,
    ) -> None:
        """Export both report files through the project DataExporter."""
        subscription_payload = SubscriptionExpiryReport._subscription_payload(subscription_rows)  # Build export rows.
        contract_payload = SubscriptionExpiryReport._contract_payload(contract_rows)  # Build export rows.
        logger.info("Exporting %s", SUBSCRIPTION_FILENAME)  # Log before subscription export.
        dependencies.DataExporter.write_with_format_selection(
            subscription_payload,
            SUBSCRIPTION_FILENAME,
            api_function_name=SUBSCRIPTION_API_NAME,
        )  # Export SubscriptionExpiry.csv through DataExporter.
        logger.debug("Exported %d rows to %s", len(subscription_payload), SUBSCRIPTION_FILENAME)  # Log export count.
        logger.info("Exporting %s", CONTRACT_FILENAME)  # Log before contract export.
        dependencies.DataExporter.write_with_format_selection(
            contract_payload,
            CONTRACT_FILENAME,
            api_function_name=CONTRACT_API_NAME,
        )  # Export ContractExpiry.csv through DataExporter.
        logger.debug("Exported %d rows to %s", len(contract_payload), CONTRACT_FILENAME)  # Log export count.

    @staticmethod
    def _subscription_payload(rows: list[SubscriptionExpiryRow]) -> list[dict[str, object]]:
        """Return export rows that still create a CSV when the report is empty."""
        if rows:  # Real source rows should export one row per subscription type.
            return [row.to_dict() for row in rows]  # Convert subscription rows for export.
        return [{column: MISSING_VALUE for column in SUBSCRIPTION_COLUMNS}]  # Force DataExporter to create headers.

    @staticmethod
    def _contract_payload(rows: list[ContractExpiryRow]) -> list[dict[str, object]]:
        """Return export rows that still create a CSV when the report is empty."""
        if rows:  # Real source rows should export one row per device.
            return [row.to_dict() for row in rows]  # Convert contract rows for export.
        payload: dict[str, object] = {column: MISSING_VALUE for column in CONTRACT_COLUMNS}  # Create CSV headers.
        payload["contract_state"] = STATE_UNSUPPORTED  # State that no source contract record supports the device.
        payload["note"] = CONTRACT_RECORD_ABSENT_NOTE  # Explain why the placeholder row exists.
        return [payload]  # Return one explicit unsupported row for empty JSI contract data.

    @staticmethod
    def _print_summary(summary: ConsoleSummary) -> None:
        """Print every summary count for the operator."""
        logger.info("Printing subscription and contract expiry summary")  # Log before console output.
        print("Subscription expiry summary:")  # Print the subscription summary heading.
        for band in SUBSCRIPTION_BANDS:  # Print every required subscription band.
            print(f"  {band}: {summary.subscription_band_counts[band]}")  # Print subscription band count.
        print("Contract expiry summary:")  # Print the contract summary heading.
        for bucket in CONTRACT_BUCKETS:  # Print every required contract bucket.
            print(f"  {bucket}: {summary.contract_bucket_counts[bucket]}")  # Print contract bucket count.
        logger.debug("Printed subscription and contract expiry summary")  # Log after console output.


class CrossOrgSubscriptionInventoryReport:
    """Run the complete cross-org subscription and stock inventory report."""

    @staticmethod
    def run() -> None:
        """Resolve active organization context and run the cross-org report."""
        logger.info("Starting the cross-org subscription and stock inventory report")  # Log operation start.
        dependencies = SourceDependencyResolver  # Resolve runtime dependencies.
        active_org_id = (
            getattr(dependencies, "org_id", "") or os.getenv("org_id") or os.getenv("ORG_ID") or ""
        )  # Use cached values without a prompt.
        active_org_name = (
            getattr(dependencies, "org_name", "") or os.getenv("END_CUSTOMER_NAME") or active_org_id or "Unknown"
        )  # Preserve a readable fallback name.
        client = SubscriptionExpiryClient(dependencies.apisession)  # Build the SDK client.
        CrossOrgSubscriptionInventoryReport._run_with_client(
            str(active_org_id),
            str(active_org_name),
            client,
            dependencies,
        )  # Execute the complete report.
        logger.debug("Finished the cross-org subscription and stock inventory report")  # Log completion.

    @staticmethod
    def _safe_payload(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Neutralize formula-like strings and add source attribution."""
        payload: list[dict[str, Any]] = []  # Accumulate formula-safe rows.
        for row in rows:  # Walk each result row.
            safe_row: dict[str, Any] = {"source_attribution": SOURCE_ATTRIBUTION}  # Add source terms.
            for key, value in row.items():  # Walk each source cell.
                if isinstance(value, str) and value.lstrip(" \t\r\n").startswith(("=", "+", "-", "@")):
                    safe_row[key] = "'" + value  # Neutralize spreadsheet formulas.
                else:
                    safe_row[key] = value  # Preserve the source value.
            payload.append(safe_row)  # Add one formula-safe row.
        return payload  # Return portable CSV payload.

    @staticmethod
    def _write_empty_csv(filename: str, fieldnames: list[str]) -> Path:
        """Write one header-only CSV with no fake data row."""
        path = Path("data") / filename  # Build the platform-safe data path.
        path.parent.mkdir(parents=True, exist_ok=True)  # Create data for a new worktree.
        logger.info("Writing empty cross-org report header to %s", path)  # Log before file output.
        try:  # The stable report name can be locked by Excel or OneDrive.
            with path.open("w", newline="", encoding="utf-8") as csv_file:  # Open the report for writing.
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)  # Use explicit header order.
                writer.writeheader()  # Write headers without a fake Missing row.
            logger.debug("Wrote header-only cross-org report %s", path)  # Log after file output.
            return path  # Return the stable output path.
        except OSError as error:  # File lock or write denial needs a visible fallback.
            logger.error("Cannot write stable cross-org CSV %s: %s", path, error)  # Preserve the local failure.
            timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")  # Make a collision-resistant UTC name.
            fallback_path = path.with_name(f"{path.stem}_{timestamp}{path.suffix}")  # Keep a visible report copy.
            try:  # A fallback file must remain outside the locked stable name.
                with fallback_path.open("w", newline="", encoding="utf-8") as csv_file:  # Open the fallback.
                    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)  # Use the required headers.
                    writer.writeheader()  # Write one header-only fallback.
            except OSError as fallback_error:  # Neither stable nor fallback write can proceed.
                logger.error(
                    "Cannot write fallback cross-org CSV %s: %s",
                    fallback_path,
                    fallback_error,
                )  # Preserve the fallback failure.
                raise RuntimeError(
                    f"Cannot write cross-org CSV {filename} or its fallback"
                ) from fallback_error  # Stop with an explicit output failure.
            print(f"Warning: {filename} is locked. Wrote {fallback_path} instead.")  # Tell the operator.
            logger.warning("Used fallback cross-org CSV %s for locked %s", fallback_path, path)  # Log fallback.
            return fallback_path  # Return the visible fallback path.

    @staticmethod
    def _write_payload_csv(
        payload: list[dict[str, Any]],
        filename: str,
        fieldnames: list[str],
    ) -> Path:
        """Write a populated CSV or an UTC timestamped fallback for a locked stable name."""
        path = Path("data") / filename  # Build the platform-safe stable report path.
        path.parent.mkdir(parents=True, exist_ok=True)  # Create data for a new worktree.
        logger.info("Writing populated cross-org report %s", path)  # Log before file output.
        try:  # A stable report name can be locked by Excel or OneDrive.
            with path.open("w", newline="", encoding="utf-8") as csv_file:  # Open the stable report.
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)  # Use the exact report columns.
                writer.writeheader()  # Write the report header.
                writer.writerows(payload)  # Write every current source row.
            logger.debug("Wrote populated cross-org report %s", path)  # Log after successful output.
            return path  # Return the stable output path.
        except OSError as error:  # A file lock or write denial needs a visible fallback.
            logger.error("Cannot write stable cross-org CSV %s: %s", path, error)  # Preserve the local failure.
            timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")  # Make a UTC fallback name.
            fallback_path = path.with_name(f"{path.stem}_{timestamp}{path.suffix}")  # Keep a visible copy.
            try:  # The fallback must use a name that is not locked.
                with fallback_path.open("w", newline="", encoding="utf-8") as csv_file:  # Open the fallback.
                    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)  # Use the exact report columns.
                    writer.writeheader()  # Write the report header.
                    writer.writerows(payload)  # Write every current source row.
            except OSError as fallback_error:  # Both stable and fallback writes can fail.
                logger.error(
                    "Cannot write fallback cross-org CSV %s: %s",
                    fallback_path,
                    fallback_error,
                )  # Preserve the fallback failure.
                raise RuntimeError(
                    f"Cannot write cross-org CSV {filename} or its fallback"
                ) from fallback_error  # Stop with an explicit output failure.
            print(f"Warning: {filename} is locked. Wrote {fallback_path} instead.")  # Tell the operator.
            logger.warning("Used fallback cross-org CSV %s for locked %s", fallback_path, path)  # Log fallback.
            return fallback_path  # Return the visible fallback path.

    @staticmethod
    def _export_reports(
        payload: CrossOrgReportPayload,
        dependencies: Any,
    ) -> None:
        """Export linked cross-org CSV reports through DataExporter."""
        reports = (
            (
                payload.organization_rows,
                CROSS_ORG_ORGANIZATION_STATUS_FILENAME,
                "CrossOrgOrganizationStatus",
                [
                    "msp_id",
                    "org_id",
                    "org_name",
                    "source",
                    "request_status",
                    "error",
                    "source_attribution",
                ],
            ),
            (
                payload.purchase_rows,
                CROSS_ORG_SUBSCRIPTION_PURCHASE_FILENAME,
                "CrossOrgSubscriptionPurchase",
                [
                    "msp_id",
                    "org_id",
                    "org_name",
                    "record_id",
                    "subscription_id",
                    "order_id",
                    "subscription_type",
                    "quantity",
                    "remaining_quantity",
                    "start_date",
                    "end_date",
                    "created_date",
                    "deal_period",
                    "source",
                    "source_attribution",
                ],
            ),
            (
                payload.balance_rows,
                CROSS_ORG_SUBSCRIPTION_BALANCE_FILENAME,
                "CrossOrgSubscriptionBalance",
                [
                    "msp_id",
                    "org_id",
                    "org_name",
                    "subscription_type",
                    "purchased_quantity",
                    "entitled_quantity",
                    "in_use_quantity",
                    "unused_entitlement",
                    "over_entitlement",
                    "status",
                    "start_date",
                    "end_date",
                    "days_remaining",
                    "band",
                    "source_attribution",
                ],
            ),
            (
                payload.deployed_inventory_rows,
                CROSS_ORG_DEPLOYED_INVENTORY_FILENAME,
                "CrossOrgDeployedInventory",
                [
                    "msp_id",
                    "org_id",
                    "org_name",
                    "site_id",
                    "site_name",
                    "serial",
                    "mac",
                    "model",
                    "name",
                    "device_type",
                    "deployment_status",
                    "connected",
                    "vc_mac",
                    "chassis_serial",
                    "chassis_mac",
                    "chassis_model",
                    "source_attribution",
                ],
            ),
            (
                payload.deployed_inventory_summary_rows,
                CROSS_ORG_DEPLOYED_INVENTORY_SUMMARY_FILENAME,
                "CrossOrgDeployedInventorySummary",
                [
                    "msp_id",
                    "org_id",
                    "org_name",
                    "device_type",
                    "deployed_quantity",
                    "request_status",
                    "source_attribution",
                ],
            ),
            (
                payload.inventory_summary_rows,
                "CrossOrgInventorySummary.csv",
                "CrossOrgInventorySummary",
                [
                    "msp_id",
                    "org_id",
                    "org_name",
                    "device_type",
                    "deployed_quantity",
                    "stock_quantity",
                    "inventory_quantity",
                    "request_status",
                    "source_attribution",
                ],
            ),
            (
                payload.stock_rows,
                CROSS_ORG_STOCK_INVENTORY_FILENAME,
                "CrossOrgStockInventory",
                [
                    "msp_id",
                    "org_id",
                    "org_name",
                    "serial",
                    "mac",
                    "model",
                    "name",
                    "device_type",
                    "deployment_status",
                    "license_review_required",
                    "jsi_match_status",
                    "contract_status",
                    "contract_end_date",
                    "vc_mac",
                    "chassis_serial",
                    "chassis_mac",
                    "chassis_model",
                    "source_attribution",
                ],
            ),
            (
                payload.contract_rows,
                CROSS_ORG_CONTRACT_EVIDENCE_FILENAME,
                "CrossOrgContractEvidence",
                [
                    "msp_id",
                    "org_id",
                    "org_name",
                    "serial",
                    "model",
                    "status",
                    "has_support",
                    "claimed",
                    "contract_end_date",
                    "request_status",
                    "source_attribution",
                ],
            ),
        )  # Define report payload, name, API key, and field order.
        for rows, filename, api_name, fieldnames in reports:  # Export each report once.
            if not rows:  # Empty source data needs headers, not fake rows.
                CrossOrgSubscriptionInventoryReport._write_empty_csv(filename, fieldnames)  # Write header-only.
                continue  # Do not call the shared exporter with fake rows.
            payload = CrossOrgSubscriptionInventoryReport._safe_payload(rows)  # Neutralize formula text.
            logger.info("Exporting cross-org report %s", filename)  # Log before export.
            written = dependencies.DataExporter.write_with_format_selection(
                payload,
                filename,
                api_function_name=api_name,
                fieldnames=fieldnames,
                backend_options=ExportBackendOptions(format_override="csv"),
            )  # Write CSV through the shared exporter.
            if written is False:  # The exporter rejected the stable file name.
                CrossOrgSubscriptionInventoryReport._write_payload_csv(
                    payload,
                    filename,
                    fieldnames,
                )  # Write one UTC timestamped fallback.
            logger.debug("Exported %d rows to %s", len(payload), filename)  # Log export count.

    @staticmethod
    def _print_summary(
        payload: CrossOrgReportPayload,
    ) -> None:
        """Print concise counts for every cross-org report category."""
        success_count = sum(
            1 for row in payload.organization_rows if row.get("request_status") in ("success", "partial")
        )  # Count organizations with usable data.
        failed_count = sum(
            1 for row in payload.organization_rows if row.get("request_status") in ("failed", "unavailable")
        )  # Count organizations with failures.
        print("Cross-org subscription inventory summary:")  # Print summary heading.
        print(f"  Organizations discovered: {len(payload.organization_rows)}")  # Print org count.
        print(f"  Organizations with data: {success_count}")  # Print usable count.
        print(f"  Organizations with failure: {failed_count}")  # Print failure count.
        print(f"  Subscription purchase rows: {len(payload.purchase_rows)}")  # Print purchase count.
        print(f"  Subscription balance rows: {len(payload.balance_rows)}")  # Print balance count.
        print(f"  Deployed inventory rows: {len(payload.deployed_inventory_rows)}")  # Print deployed count.
        print(
            f"  Deployed inventory summary rows: {len(payload.deployed_inventory_summary_rows)}"
        )  # Print deployed summary count.
        print(
            f"  Organization inventory rows: " f"{len(payload.deployed_inventory_rows) + len(payload.stock_rows)}"
        )  # Print the combined assigned and stock inventory count.
        print(f"  Inventory summary rows: {len(payload.inventory_summary_rows)}")  # Print combined summary count.
        print(f"  Stock inventory rows: {len(payload.stock_rows)}")  # Print stock count.
        print(f"  Contract evidence rows: {len(payload.contract_rows)}")  # Print contract count.

    @staticmethod
    def _run_with_client(
        active_org_id: str,
        active_org_name: str,
        client: SubscriptionExpiryClient,
        dependencies: Any,
    ) -> None:
        """Run the cross-org source reads and exports."""
        organizations, discovery_failures = client.discover_organizations(
            active_org_id,
            active_org_name,
        )  # Discover authorized scope.
        payload = CrossOrgReportPayload(
            organization_rows=[failure.to_dict() for failure in discovery_failures],
            purchase_rows=[],
            balance_rows=[],
            deployed_inventory_rows=[],
            deployed_inventory_summary_rows=[],
            inventory_summary_rows=[],
            stock_rows=[],
            contract_rows=[],
        )  # Initialize one linked report payload.
        if not organizations:  # No authorized organization exists.
            CrossOrgSubscriptionInventoryReport._export_no_organizations(
                active_org_id,
                active_org_name,
                payload,
                dependencies,
            )  # Export no-access evidence.
            return  # Stop without success-shaped subscription data.
        report_date = __import__("datetime").datetime.now(__import__("datetime").UTC).date()  # Use UTC run date.
        organization_status_by_id: dict[str, OrganizationScope] = {}  # Track final organization status.
        for organization in organizations:  # Read one authorized organization at a time.
            CrossOrgSubscriptionInventoryReport._read_one_organization(
                organization,
                client,
                report_date,
                payload,
                organization_status_by_id,
            )  # Read and score one organization.
        CrossOrgSubscriptionInventoryReport._read_msp_purchases(
            organizations,
            client,
            report_date,
            payload.purchase_rows,
        )  # Read optional MSP license evidence.
        payload.organization_rows.extend(
            organization_status.to_dict() for organization_status in organization_status_by_id.values()
        )  # Add organization status rows.
        deduplicated_purchase_rows: dict[tuple[str, str, str], dict[str, Any]] = {}  # Dedupe purchase evidence.
        for purchase_row in payload.purchase_rows:  # Walk organization plus MSP purchases.
            key = (
                str(purchase_row.get("org_id", MISSING_VALUE)),
                str(purchase_row.get("record_id", MISSING_VALUE)),
                str(purchase_row.get("subscription_type", MISSING_VALUE)),
            )  # Use org, record, and type as the purchase key.
            deduplicated_purchase_rows.setdefault(key, purchase_row)  # Keep the first source row.
        payload.purchase_rows = list(deduplicated_purchase_rows.values())  # Materialize deduplicated rows.
        CrossOrgSubscriptionInventoryReport._export_reports(payload, dependencies)  # Export linked reports.
        CrossOrgSubscriptionInventoryReport._print_summary(payload)  # Print linked result counts.

    @staticmethod
    def _export_no_organizations(
        active_org_id: str,
        active_org_name: str,
        payload: CrossOrgReportPayload,
        dependencies: Any,
    ) -> None:
        """Export failure status and empty reports when no organization is accessible."""
        if not payload.organization_rows:  # Discovery returned no visible failure.
            payload.organization_rows.append(
                OrganizationScope(
                    org_id=active_org_id or MISSING_VALUE,
                    org_name=active_org_name or MISSING_VALUE,
                    source="none",
                    request_status="failed",
                    error="No accessible organization",
                ).to_dict()
            )  # Name the no-access condition.
        CrossOrgSubscriptionInventoryReport._export_reports(payload, dependencies)  # Export empty reports.
        CrossOrgSubscriptionInventoryReport._print_summary(payload)  # Print zero and failure counts.

    @staticmethod
    def _read_summary(
        client: SubscriptionExpiryClient,
        org_id: str,
        errors: list[str],
    ) -> tuple[LicenseSummarySource | None, int]:
        """Read one license summary and count success."""
        try:  # Read license summary.
            return client.fetch_license_summary(org_id), 1  # Return data and success.
        except SubscriptionExpiryClientError as error:  # License summary failed.
            errors.append(str(error))  # Preserve safe status text.
            return None, 0  # Return no data and no success.

    @staticmethod
    def _read_usage(
        client: SubscriptionExpiryClient,
        org_id: str,
        errors: list[str],
    ) -> tuple[list[LicenseUsageSource], int]:
        """Read one license usage source and count success."""
        try:  # Read license usage.
            return client.fetch_license_usage_by_site(org_id), 1  # Return usage and success.
        except SubscriptionExpiryClientError as error:  # License usage failed.
            errors.append(str(error))  # Preserve safe status text.
            return [], 0  # Return no data and no success.

    @staticmethod
    def _read_inventory(
        client: SubscriptionExpiryClient,
        org_id: str,
        errors: list[str],
    ) -> tuple[list[dict[str, Any]], int]:
        """Read one inventory source and count success."""
        try:  # Read inventory.
            return client.fetch_inventory(org_id), 1  # Return inventory and success.
        except SubscriptionExpiryClientError as error:  # Inventory failed.
            errors.append(str(error))  # Preserve safe status text.
            return [], 0  # Return no data and no success.

    @staticmethod
    def _read_jsi(
        client: SubscriptionExpiryClient,
        org_id: str,
        errors: list[str],
    ) -> tuple[list[JsiContractSource] | None, int]:
        """Read JSI evidence and preserve unavailable status."""
        try:  # Read JSI evidence.
            return client.search_jsi_assets_and_contracts(org_id), 1  # Return JSI and success.
        except JsiAccountNotLinkedError:  # JSI account is unavailable.
            errors.append("JSI account not linked")  # Preserve visible condition.
            return None, 0  # Return unavailable JSI and no success.
        except SubscriptionExpiryClientError as error:  # JSI request failed.
            errors.append(str(error))  # Preserve safe status text.
            return None, 0  # Return unavailable JSI and no success.

    @staticmethod
    def _read_one_organization(
        organization: OrganizationScope,
        client: SubscriptionExpiryClient,
        report_date: date,
        payload: CrossOrgReportPayload,
        organization_status_by_id: dict[str, OrganizationScope],
    ) -> None:
        """Read and score one organization."""
        logger.info("Reading cross-org data for %s", organization.org_id)  # Log before org reads.
        errors: list[str] = []  # Collect visible source failures.
        summary, summary_success = CrossOrgSubscriptionInventoryReport._read_summary(
            client,
            organization.org_id,
            errors,
        )  # Read license summary.
        usages, usage_success = CrossOrgSubscriptionInventoryReport._read_usage(
            client,
            organization.org_id,
            errors,
        )  # Read license usage.
        inventory, inventory_success = CrossOrgSubscriptionInventoryReport._read_inventory(
            client,
            organization.org_id,
            errors,
        )  # Read inventory.
        jsi, jsi_success = CrossOrgSubscriptionInventoryReport._read_jsi(
            client,
            organization.org_id,
            errors,
        )  # Read JSI evidence.
        success_count = summary_success + usage_success + inventory_success + jsi_success  # Sum success.
        CrossOrgSubscriptionInventoryReport._add_subscription_rows(
            organization,
            report_date,
            summary,
            usages,
            payload,
        )  # Add subscription purchase and balance rows.
        CrossOrgSubscriptionInventoryReport._add_inventory_rows(
            organization,
            inventory,
            inventory_success,
            jsi,
            payload,
        )  # Add deployed and stock inventory rows.
        CrossOrgSubscriptionInventoryReport._add_contract_rows(organization, jsi, payload)  # Add contract evidence.
        request_status = CrossOrgSubscriptionInventoryReport._organization_request_status(success_count)
        organization_status_by_id[organization.org_id] = replace(
            organization,
            request_status=request_status,
            error="; ".join(errors) if errors else None,
        )  # Preserve final organization status.

    @staticmethod
    def _organization_request_status(success_count: int) -> str:
        """Score organization status from the number of successful source reads."""
        if success_count == 4:  # All four source reads succeeded.
            return "success"  # Preserve full source success.
        if success_count > 0:  # One or more source reads succeeded.
            return "partial"  # Preserve visible partial evidence.
        return "failed"  # Preserve complete source failure.

    @staticmethod
    def _add_subscription_rows(
        organization: OrganizationScope,
        report_date: date,
        summary: LicenseSummarySource | None,
        usages: list[LicenseUsageSource],
        payload: CrossOrgReportPayload,
    ) -> None:
        """Add purchase and balance rows when a license summary is usable."""
        if summary is None:  # License summary unavailable.
            return  # Preserve organization status and no false rows.
        payload.purchase_rows.extend(
            row.to_dict()
            for row in CrossOrgSubscriptionInventoryModel.build_purchase_rows(
                organization,
                summary.licenses,
                report_date,
            )
        )  # Add purchase rows.
        payload.balance_rows.extend(
            row.to_dict()
            for row in CrossOrgSubscriptionInventoryModel.build_subscription_balances(
                organization,
                summary,
                usages,
                report_date,
            )
        )  # Add balance rows.

    @staticmethod
    def _add_inventory_rows(
        organization: OrganizationScope,
        inventory: list[dict[str, Any]],
        inventory_success: int,
        jsi: list[JsiContractSource] | None,
        payload: CrossOrgReportPayload,
    ) -> None:
        """Add deployed inventory, deployed summary, and stock rows."""
        logger.info("Scoring inventory rows for %s", organization.org_id)  # Log before inventory classification.
        inventory_status = "success" if inventory_success == 1 else "failed"  # Score source read.
        deployed_rows = CrossOrgSubscriptionInventoryModel.build_deployed_inventory_rows(
            organization,
            inventory,
        )  # Classify deployed inventory once.
        payload.deployed_inventory_rows.extend(row.to_dict() for row in deployed_rows)  # Add deployed detail.
        payload.deployed_inventory_summary_rows.extend(
            row.to_dict()
            for row in CrossOrgSubscriptionInventoryModel.build_deployed_inventory_summary(
                organization,
                deployed_rows,
                inventory_status,
            )
        )  # Add deployed summary.
        stock_rows = CrossOrgSubscriptionInventoryModel.build_stock_rows(
            organization,
            inventory,
            jsi,
        )  # Build stock rows once for the detail and combined summary.
        payload.stock_rows.extend(row.to_dict() for row in stock_rows)  # Add stock detail.
        payload.inventory_summary_rows.extend(
            row.to_dict()
            for row in CrossOrgSubscriptionInventoryModel.build_inventory_summary(
                organization,
                deployed_rows,
                stock_rows,
                inventory_status,
            )
        )  # Add deployed, stock, and combined inventory counts.
        logger.debug(
            "Added %d deployed rows and %d stock rows",
            len(deployed_rows),
            len(payload.stock_rows),
        )  # Log inventory result counts.

    @staticmethod
    def _add_contract_rows(
        organization: OrganizationScope,
        jsi: list[JsiContractSource] | None,
        payload: CrossOrgReportPayload,
    ) -> None:
        """Add JSI contract evidence rows to the report payload."""
        payload.contract_rows.extend(
            row.to_dict()
            for row in CrossOrgSubscriptionInventoryModel.build_contract_rows(
                organization,
                jsi,
            )
        )  # Add contract evidence.

    @staticmethod
    def _read_msp_purchases(
        organizations: list[OrganizationScope],
        client: SubscriptionExpiryClient,
        report_date: date,
        purchase_rows: list[dict[str, Any]],
    ) -> None:
        """Read optional MSP purchase evidence once per MSP."""
        for msp_id in CrossOrgSubscriptionInventoryReport._unique_msp_ids(organizations):  # Read each MSP once.
            msp_records = CrossOrgSubscriptionInventoryReport._fetch_msp_records(client, msp_id)  # Read MSP evidence.
            if not msp_records:  # MSP evidence is unavailable.
                continue  # Preserve organization evidence.
            CrossOrgSubscriptionInventoryReport._add_msp_purchase_rows(
                organizations,
                msp_records,
                report_date,
                purchase_rows,
            )  # Add matched MSP purchases.

    @staticmethod
    def _unique_msp_ids(organizations: list[OrganizationScope]) -> list[str]:
        """Return one ordered MSP ID for each organization grant."""
        seen_msp_ids: set[str] = set()  # Avoid repeated MSP license reads.
        msp_ids: list[str] = []  # Accumulate unique ordered IDs.
        for organization in organizations:  # Walk organization scopes.
            msp_id = organization.msp_id  # Read the MSP grant.
            if msp_id and msp_id not in seen_msp_ids:  # Accept only a new valid MSP ID.
                seen_msp_ids.add(msp_id)  # Remember this MSP.
                msp_ids.append(msp_id)  # Preserve discovery order.
        return msp_ids  # Return deduplicated MSP IDs.

    @staticmethod
    def _fetch_msp_records(
        client: SubscriptionExpiryClient,
        msp_id: str,
    ) -> list[dict[str, Any]]:
        """Fetch and validate optional MSP license records."""
        fetch_msp_licenses = getattr(client, "fetch_msp_licenses", None)  # Locate optional method.
        if fetch_msp_licenses is None:  # Synthetic or old client lacks MSP licenses.
            return []  # Preserve organization evidence.
        msp_payload = fetch_msp_licenses(msp_id)  # Read optional MSP purchase evidence.
        if not isinstance(msp_payload, dict):  # MSP endpoint denied or returned no mapping.
            return []  # Continue with organization evidence.
        msp_records = msp_payload.get("licenses")  # Read MSP license records.
        if not isinstance(msp_records, list):  # MSP records are unavailable.
            return []  # Keep organization evidence.
        return [record for record in msp_records if isinstance(record, dict)]  # Return mapping records only.

    @staticmethod
    def _add_msp_purchase_rows(
        organizations: list[OrganizationScope],
        msp_records: list[dict[str, Any]],
        report_date: date,
        purchase_rows: list[dict[str, Any]],
    ) -> None:
        """Match MSP purchase records to organizations and append rows."""
        for organization in organizations:  # Match MSP records to organizations.
            matching_records = CrossOrgSubscriptionInventoryReport._matching_msp_records(
                organization,
                msp_records,
            )  # Match by org ID or unknown scope.
            purchase_rows.extend(
                row.to_dict()
                for row in CrossOrgSubscriptionInventoryModel.build_purchase_rows(
                    organization,
                    matching_records,
                    report_date,
                )
            )  # Add MSP purchase evidence.

    @staticmethod
    def _matching_msp_records(
        organization: OrganizationScope,
        msp_records: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Match one MSP record set to one organization."""
        return [
            record for record in msp_records if record.get("org_id") == organization.org_id or not record.get("org_id")
        ]  # Match explicit org IDs or preserve unknown scope.
