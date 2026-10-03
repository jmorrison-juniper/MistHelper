"""Menu operation 272 -- export the organization certificate expiry report."""

from __future__ import annotations  # Keep annotations import-safe during startup.

import logging  # Log each report phase for operators.
from datetime import UTC, datetime  # Stamp the report in UTC.

from src.foundation.runtime.config.source_dependency_resolver import (
    SourceDependencyResolver,  # Resolve session, org, and exporter without importing the root module.
)
from src.mist.intelligence.reports.certificate_expiry.client import (
    CertificateExpiryClient,
)  # Read Mist certificate sources.
from src.mist.intelligence.reports.certificate_expiry.model import (
    BANDS,  # Print every band in stable order.
    CertificateExpiryNormalizer,  # Convert source payloads into report rows.
    CertificateExpiryRecord,  # Provide the export column contract.
    CertificatePrivacyGuard,  # Reject sensitive values before export.
    CertificateReport,  # Type the report object passed between phases.
)

logger = logging.getLogger(__name__)  # Name logs for this operation module.

EXPORT_FILENAME = "CertificateExpiry.csv"  # Write the contract file in the data directory.
EXPORT_ENDPOINT_NAME = "certificate_expiry_report"  # Use the planned primary-key strategy name.


class CertificateExpiryReport:
    """Run the organization certificate expiry report."""

    @staticmethod
    def _resolve_org_id() -> str:
        """Return the organization identifier for the report."""
        logger.info("Certificate expiry report resolves the organization")  # Log before dependency resolution.
        org_id = SourceDependencyResolver.ConfigUtils.get_cached_or_prompted_org_id()  # Use the shared org resolver.
        logger.debug("Certificate expiry report resolved organization org=%s", org_id)  # Log the safe identifier.
        return str(org_id)  # Return text for report rows.

    @staticmethod
    def _resolve_session() -> object:
        """Return the shared Mist API session."""
        logger.info("Certificate expiry report resolves the Mist API session")  # Log before dependency resolution.
        session = SourceDependencyResolver.apisession  # Use the shared session from the resolver.
        logger.debug("Certificate expiry report resolved session type=%s", type(session).__name__)  # Log type only.
        return session  # Return the live session object.

    @staticmethod
    def _privacy_check(report: CertificateReport) -> None:
        """Fail closed if a row contains sensitive material."""
        logger.info(
            "Certificate expiry report checks output privacy rows=%d", len(report.records)
        )  # Log before scanning.
        for row in report.export_rows():  # Serialize rows through the model guard.
            CertificatePrivacyGuard.assert_safe_row(row)  # Fail closed before export.
        logger.debug("Certificate expiry report privacy check passed rows=%d", len(report.records))  # Log scan count.

    @staticmethod
    def _print_summary(report: CertificateReport) -> None:
        """Print the band and failed-source summary."""
        logger.info("Certificate expiry report prints band summary")  # Log before summary output.
        for band in BANDS:  # Print all bands, including zero-count bands.
            message = f"Certificate expiry band {band}: {report.band_counts[band]}"  # Build the console line.
            print(message)  # Print the summary for menu users.
            logger.info("%s", message)  # Log the summary for session evidence.
        if report.failed_sources:  # Failed sources are different from empty sources.
            message = f"Certificate expiry failed sources: {', '.join(report.failed_sources)}"  # Build a safe list.
            print(message)  # Print failed sources for menu users.
            logger.warning("%s", message)  # Name sources only.
        logger.debug(
            "Certificate expiry report summary printed rows=%d failed=%d",
            len(report.records),
            len(report.failed_sources),
        )  # Log result.

    @staticmethod
    def _primary_key_strategy_ready() -> bool:
        """Return true when the integration pull request installed the export strategy."""
        from src.foundation.support.refactors.endpoint_primary_key_strategies import (  # Import the moved dependency.
            ENDPOINT_PRIMARY_KEY_STRATEGIES,
        )

        return EXPORT_ENDPOINT_NAME in ENDPOINT_PRIMARY_KEY_STRATEGIES  # Require a strategy before live export.

    @staticmethod
    def _ensure_primary_key_strategy() -> None:
        """Stop export until integration adds the primary key strategy."""
        logger.info("Certificate expiry report checks primary key strategy")  # Log before the guard check.
        if not CertificateExpiryReport._primary_key_strategy_ready():  # Block unregistered live exports.
            raise RuntimeError(
                "certificate_expiry_report primary key strategy is not registered"
            )  # Stop before DataExporter writes.
        logger.debug("Certificate expiry report primary key strategy is registered")  # Log the guard result.

    @staticmethod
    def _export(report: CertificateReport) -> bool:
        """Write the report rows to the configured backend."""
        CertificateExpiryReport._ensure_primary_key_strategy()  # Block export until integration completes wiring.
        rows = report.export_rows()  # Convert records to export dictionaries after the privacy guard.
        logger.info("Certificate expiry report writes rows=%d to %s", len(rows), EXPORT_FILENAME)  # Log before export.
        written = SourceDependencyResolver.DataExporter.write_with_format_selection(  # Use the shared export pipeline.
            rows,
            EXPORT_FILENAME,
            api_function_name=EXPORT_ENDPOINT_NAME,
            fieldnames=CertificateExpiryRecord.column_names(),
        )
        logger.debug("Certificate expiry report export finished written=%s", written)  # Log export result.
        return bool(written)  # Return a simple success flag for the caller.

    @staticmethod
    def run() -> None:
        """Run the report, print the summary, and export the rows."""
        logger.info("Menu #272: Starting the certificate expiry report")  # Log the menu operation start.
        org_id = CertificateExpiryReport._resolve_org_id()  # Resolve the organization once for all rows.
        session = CertificateExpiryReport._resolve_session()  # Resolve the Mist session once for the client.
        generated_at = datetime.now(tz=UTC)  # Use one report timestamp for all date math.
        logger.info("Certificate expiry report collects Mist sources")  # Log before API collection.
        source_result = CertificateExpiryClient(session, org_id).collect_sources()  # Read each source safely.
        logger.debug(
            "Certificate expiry report collected sources=%d failed=%d",
            len(source_result.payloads),
            len(source_result.failed_sources),
        )  # Log counts.
        logger.info("Certificate expiry report normalizes certificate rows")  # Log before normalization.
        report = CertificateExpiryNormalizer(org_id, generated_at).normalize(
            source_result.payloads, source_result.failed_sources
        )  # Normalize all rows.
        logger.debug("Certificate expiry report normalized rows=%d", len(report.records))  # Log row count.
        CertificateExpiryReport._privacy_check(report)  # Verify that no raw certificate text reaches output.
        CertificateExpiryReport._print_summary(report)  # Print the operator summary.
        if not CertificateExpiryReport._export(report):  # Export rows and detect failure.
            logger.error("Certificate expiry report could not write %s", EXPORT_FILENAME)  # Report the failed write.
