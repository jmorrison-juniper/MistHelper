"""Operation orchestration for the subscription and contract expiry report."""

from __future__ import annotations  # Keep annotations import-safe during tests.

import csv  # Write explicit header-only CSV files for empty reports.
import logging  # Record operation actions for operator traceability.
import os  # Read direct organization and customer name settings without prompts.
from dataclasses import replace  # Preserve organization scope while changing status.
from datetime import date  # Type report date for source scoring.
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
CROSS_ORG_STOCK_INVENTORY_FILENAME = "CrossOrgStockInventory.csv"
CROSS_ORG_CONTRACT_EVIDENCE_FILENAME = "CrossOrgContractEvidence.csv"


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
    def _write_empty_csv(filename: str, fieldnames: list[str]) -> None:
        """Write one header-only CSV with no fake data row."""
        path = Path("data") / filename  # Build the platform-safe data path.
        path.parent.mkdir(parents=True, exist_ok=True)  # Create data for a new worktree.
        logger.info("Writing empty cross-org report header to %s", path)  # Log before file output.
        with path.open("w", newline="", encoding="utf-8") as csv_file:  # Open the report for writing.
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)  # Use explicit header order.
            writer.writeheader()  # Write headers without a fake Missing row.
        logger.debug("Wrote header-only cross-org report %s", path)  # Log after file output.

    @staticmethod
    def _export_reports(
        organization_rows: list[dict[str, Any]],
        purchase_rows: list[dict[str, Any]],
        balance_rows: list[dict[str, Any]],
        stock_rows: list[dict[str, Any]],
        contract_rows: list[dict[str, Any]],
        dependencies: Any,
    ) -> None:
        """Export five linked CSV reports through DataExporter."""
        reports = (
            (
                organization_rows,
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
                purchase_rows,
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
                balance_rows,
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
                stock_rows,
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
                    "source_attribution",
                ],
            ),
            (
                contract_rows,
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
            dependencies.DataExporter.write_with_format_selection(
                payload,
                filename,
                api_function_name=api_name,
                fieldnames=fieldnames,
                backend_options=ExportBackendOptions(format_override="csv"),
            )  # Write CSV through the shared exporter.
            logger.debug("Exported %d rows to %s", len(payload), filename)  # Log export count.

    @staticmethod
    def _print_summary(
        organization_rows: list[dict[str, Any]],
        purchase_rows: list[dict[str, Any]],
        balance_rows: list[dict[str, Any]],
        stock_rows: list[dict[str, Any]],
        contract_rows: list[dict[str, Any]],
    ) -> None:
        """Print concise counts for every cross-org report category."""
        success_count = sum(
            1 for row in organization_rows if row.get("request_status") in ("success", "partial")
        )  # Count organizations with usable data.
        failed_count = sum(
            1 for row in organization_rows if row.get("request_status") in ("failed", "unavailable")
        )  # Count organizations with failures.
        print("Cross-org subscription inventory summary:")  # Print summary heading.
        print(f"  Organizations discovered: {len(organization_rows)}")  # Print org count.
        print(f"  Organizations with data: {success_count}")  # Print usable count.
        print(f"  Organizations with failure: {failed_count}")  # Print failure count.
        print(f"  Subscription purchase rows: {len(purchase_rows)}")  # Print purchase count.
        print(f"  Subscription balance rows: {len(balance_rows)}")  # Print balance count.
        print(f"  Stock inventory rows: {len(stock_rows)}")  # Print stock count.
        print(f"  Contract evidence rows: {len(contract_rows)}")  # Print contract count.

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
        organization_status_rows = [failure.to_dict() for failure in discovery_failures]  # Add failures.
        if not organizations:  # No authorized organization exists.
            CrossOrgSubscriptionInventoryReport._export_no_organizations(
                active_org_id,
                active_org_name,
                organization_status_rows,
                dependencies,
            )  # Export no-access evidence.
            return  # Stop without success-shaped subscription data.
        purchase_rows: list[dict[str, Any]] = []  # Accumulate purchase evidence.
        balance_rows: list[dict[str, Any]] = []  # Accumulate balance evidence.
        stock_rows: list[dict[str, Any]] = []  # Accumulate stock evidence.
        contract_rows: list[dict[str, Any]] = []  # Accumulate contract evidence.
        report_date = __import__("datetime").datetime.now(__import__("datetime").UTC).date()  # Use UTC run date.
        organization_status_by_id: dict[str, OrganizationScope] = {}  # Track final organization status.
        for organization in organizations:  # Read one authorized organization at a time.
            CrossOrgSubscriptionInventoryReport._read_one_organization(
                organization,
                client,
                report_date,
                purchase_rows,
                balance_rows,
                stock_rows,
                contract_rows,
                organization_status_by_id,
            )  # Read and score one organization.
        CrossOrgSubscriptionInventoryReport._read_msp_purchases(
            organizations,
            client,
            report_date,
            purchase_rows,
        )  # Read optional MSP license evidence.
        organization_status_rows.extend(
            organization_status.to_dict() for organization_status in organization_status_by_id.values()
        )  # Add organization status rows.
        deduplicated_purchase_rows: dict[tuple[str, str, str], dict[str, Any]] = {}  # Dedupe purchase evidence.
        for purchase_row in purchase_rows:  # Walk organization plus MSP purchases.
            key = (
                str(purchase_row.get("org_id", MISSING_VALUE)),
                str(purchase_row.get("record_id", MISSING_VALUE)),
                str(purchase_row.get("subscription_type", MISSING_VALUE)),
            )  # Use org, record, and type as the purchase key.
            deduplicated_purchase_rows.setdefault(key, purchase_row)  # Keep the first source row.
        deduplicated_purchase_payload = list(deduplicated_purchase_rows.values())  # Materialize rows.
        CrossOrgSubscriptionInventoryReport._export_reports(
            organization_status_rows,
            deduplicated_purchase_payload,
            balance_rows,
            stock_rows,
            contract_rows,
            dependencies,
        )  # Export all five reports.
        CrossOrgSubscriptionInventoryReport._print_summary(
            organization_status_rows,
            deduplicated_purchase_payload,
            balance_rows,
            stock_rows,
            contract_rows,
        )  # Print linked result counts.

    @staticmethod
    def _export_no_organizations(
        active_org_id: str,
        active_org_name: str,
        organization_status_rows: list[dict[str, Any]],
        dependencies: Any,
    ) -> None:
        """Export failure status and empty reports when no organization is accessible."""
        if not organization_status_rows:  # Discovery returned no visible failure.
            organization_status_rows.append(
                OrganizationScope(
                    org_id=active_org_id or MISSING_VALUE,
                    org_name=active_org_name or MISSING_VALUE,
                    source="none",
                    request_status="failed",
                    error="No accessible organization",
                ).to_dict()
            )  # Name the no-access condition.
        CrossOrgSubscriptionInventoryReport._export_reports(
            organization_status_rows,
            [],
            [],
            [],
            [],
            dependencies,
        )  # Export failure status and empty reports.
        CrossOrgSubscriptionInventoryReport._print_summary(
            organization_status_rows,
            [],
            [],
            [],
            [],
        )  # Print zero and failure counts.

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
        purchase_rows: list[dict[str, Any]],
        balance_rows: list[dict[str, Any]],
        stock_rows: list[dict[str, Any]],
        contract_rows: list[dict[str, Any]],
        organization_status_by_id: dict[str, OrganizationScope],
    ) -> None:
        """Read and score one organization."""
        logger.info("Reading cross-org data for %s", organization.org_id)  # Log before org reads.
        success_count = 0  # Count successful source reads.
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
        if summary is not None:  # Summary is usable.
            purchase_rows.extend(
                row.to_dict()
                for row in CrossOrgSubscriptionInventoryModel.build_purchase_rows(
                    organization,
                    summary.licenses,
                    report_date,
                )
            )  # Add purchase rows.
            balance_rows.extend(
                row.to_dict()
                for row in CrossOrgSubscriptionInventoryModel.build_subscription_balances(
                    organization,
                    summary,
                    usages,
                    report_date,
                )
            )  # Add balance rows.
        stock_rows.extend(
            row.to_dict()
            for row in CrossOrgSubscriptionInventoryModel.build_stock_rows(
                organization,
                inventory,
                jsi,
            )
        )  # Add stock rows.
        contract_rows.extend(
            row.to_dict()
            for row in CrossOrgSubscriptionInventoryModel.build_contract_rows(
                organization,
                jsi,
            )
        )  # Add contract rows.
        request_status = "success" if success_count == 4 else "partial" if success_count > 0 else "failed"
        organization_status_by_id[organization.org_id] = replace(
            organization,
            request_status=request_status,
            error="; ".join(errors) if errors else None,
        )  # Preserve final organization status.

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
