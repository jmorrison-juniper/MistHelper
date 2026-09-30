"""Run the site variable audit report operation."""

from __future__ import annotations  # Keep annotations lightweight at import time.

import logging  # Log resolver, transform, and export actions.
from typing import Any  # Accept dynamic resolver-owned helpers.

from src.config.source_dependency_resolver import (  # Resolve legacy runtime dependencies at call time.
    SourceDependencyResolver,
)
from src.reports.site_variable_audit.client import (  # Read required Mist datasets.
    SiteVariableAuditClient,
    SiteVariableAuditReadError,
)
from src.reports.site_variable_audit.model import SiteVariableAuditModel  # Build report rows.
from src.utils.console import echo  # Print the operator-facing summary.

logger = logging.getLogger(__name__)  # Keep log records tied to this module.


class SiteVariableAudit:
    """Run the read-only site variable coverage audit."""

    AUDIT_API_NAME = "siteVariableAudit"  # Use one stable DataExporter API function name for audit rows.
    SUMMARY_API_NAME = "siteVariableSummary"  # Use one stable DataExporter API function name for summary rows.
    AUDIT_FILENAME = "SiteVariableAudit.csv"  # Match the required audit CSV name.
    SUMMARY_FILENAME = "SiteVariableSummary.csv"  # Match the required summary CSV name.

    @staticmethod
    def run() -> None:
        """Run the audit through resolver-owned dependencies."""
        logger.info("Resolving site variable audit dependencies")  # Log before resolver reads.
        dependencies = SourceDependencyResolver  # Use the project resolver seam for runtime dependencies.
        apisession = dependencies.apisession  # Resolve the active Mist API session.
        config_utils = dependencies.ConfigUtils  # Resolve the configuration helper.
        data_exporter = dependencies.DataExporter  # Resolve the output backend helper.
        test_mode = dependencies.IS_TEST_MODE  # Resolve test mode for observability.
        logger.debug("Resolved audit dependencies with test mode %s", test_mode)  # Log non-secret resolver state.
        org_id = SiteVariableAudit._resolve_org_id(config_utils)  # Resolve the selected organization ID.
        SiteVariableAudit._validate_inputs(apisession, org_id)  # Fail early when required context is missing.
        client = SiteVariableAuditClient(apisession, org_id)  # Create the Mist client after validation.
        records = SiteVariableAudit._fetch_records(client)  # Read all required organization datasets.
        result = SiteVariableAudit._build_result(records)  # Convert Mist records into report rows.
        SiteVariableAudit._export_reports(data_exporter, result)  # Write both required reports.
        SiteVariableAudit._print_summary(result.missing_site_count)  # Show the console summary.

    @staticmethod
    def _resolve_org_id(config_utils: Any) -> str:
        """Return the selected organization ID through the shared helper."""
        logger.info("Resolving organization ID for site variable audit")  # Log before organization lookup.
        org_id = str(config_utils.get_cached_or_prompted_org_id() or "")  # Use the repository standard org helper.
        logger.debug(
            "Resolved organization ID for site variable audit: %s", "<set>" if org_id else "<missing>"
        )  # Avoid leaking data.
        return org_id  # Return the selected organization ID.

    @staticmethod
    def _validate_inputs(apisession: Any, org_id: str) -> None:
        """Stop the audit when the required Mist context is absent."""
        logger.info("Validating site variable audit organization context")  # Log before validation.
        if apisession is None:  # A Mist read cannot run without a session.
            raise RuntimeError(
                "Site variable audit cannot run because the API session is unavailable."
            )  # Stop clearly.
        if not org_id:  # A Mist read cannot run without an organization.
            raise RuntimeError(
                "Site variable audit cannot run because the organization ID is unavailable."
            )  # Stop clearly.
        logger.debug("Validated site variable audit organization context")  # Log successful validation.

    @staticmethod
    def _fetch_records(client: SiteVariableAuditClient) -> dict[str, list[dict[str, Any]]]:
        """Return all organization records required by the audit."""
        logger.info("Fetching site variable audit records")  # Log before the client reads.
        try:  # Stop the operation when one required dataset fails.
            records = client.fetch()  # Fetch all required datasets one time.
        except SiteVariableAuditReadError:  # Preserve the clear client error for the caller.
            logger.error("Site variable audit stopped because a Mist read failed")  # Log the stop reason.
            raise  # Stop before writing any report.
        logger.debug("Fetched %s site variable audit record groups", len(records))  # Log group count.
        return records  # Return raw records to the model layer.

    @staticmethod
    def _build_result(records: dict[str, list[dict[str, Any]]]) -> Any:
        """Return report rows built from already loaded records."""
        logger.info("Building site variable audit report rows")  # Log before model transform.
        result = SiteVariableAuditModel.build_result(records)  # Build findings and summaries.
        logger.debug("Built audit result with %s findings", len(result.findings))  # Log finding count.
        return result  # Return the complete result.

    @staticmethod
    def _export_reports(data_exporter: Any, result: Any) -> None:
        """Write the audit and summary reports through DataExporter."""
        logger.info("Writing site variable audit report")  # Log before the audit export.
        audit_rows = [finding.to_row() for finding in result.findings]  # Convert findings to exporter rows.
        data_exporter.write_with_format_selection(
            audit_rows, SiteVariableAudit.AUDIT_FILENAME, api_function_name=SiteVariableAudit.AUDIT_API_NAME
        )  # Write audit rows through DataExporter.
        logger.debug("Wrote %s site variable audit rows", len(audit_rows))  # Log audit export count.
        logger.info("Writing site variable summary report")  # Log before the summary export.
        summary_rows = [summary.to_row() for summary in result.summaries]  # Convert summaries to exporter rows.
        data_exporter.write_with_format_selection(
            summary_rows, SiteVariableAudit.SUMMARY_FILENAME, api_function_name=SiteVariableAudit.SUMMARY_API_NAME
        )  # Write summary rows through DataExporter.
        logger.debug("Wrote %s site variable summary rows", len(summary_rows))  # Log summary export count.

    @staticmethod
    def _print_summary(missing_site_count: int) -> None:
        """Print the required missing-site count summary."""
        logger.info("Printing site variable audit summary")  # Log before console output.
        echo(  # Print the required operator-facing summary.
            "Site variable audit found %s site(s) with missing variables. Wrote %s and %s.",
            missing_site_count,
            SiteVariableAudit.AUDIT_FILENAME,
            SiteVariableAudit.SUMMARY_FILENAME,
        )
        logger.debug(
            "Printed site variable audit summary for %s missing sites", missing_site_count
        )  # Log output state.
