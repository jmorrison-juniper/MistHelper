"""Operation orchestration for the subscription and contract expiry report."""

from __future__ import annotations  # Keep annotations import-safe during tests.

import logging  # Record operation actions for operator traceability.
from typing import Any  # Type injectable test seams without importing root modules.

from src.config.source_dependency_resolver import SourceDependencyResolver  # Resolve root-owned runtime dependencies.
from src.reports.subscription_expiry.client import JsiAccountNotLinkedError, SubscriptionExpiryClient
from src.reports.subscription_expiry.model import (
    CONTRACT_BUCKETS,
    CONTRACT_RECORD_ABSENT_NOTE,
    MISSING_VALUE,
    STATE_UNSUPPORTED,
    SUBSCRIPTION_BANDS,
    ConsoleSummary,
    ContractExpiryRow,
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
