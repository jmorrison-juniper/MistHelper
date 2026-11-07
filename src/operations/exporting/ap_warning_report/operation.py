"""Export AP trouble evidence through the existing output backend selection."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from requests import RequestException

from src.foundation.runtime.config import runtime_settings
from src.foundation.runtime.config.source_dependency_resolver import SourceDependencyResolver
from src.operations.exporting.ap_warning_report.client import ApWarningClient, RecoveryEvidenceReader
from src.operations.exporting.ap_warning_report.codes import RecoveryClassifier
from src.operations.exporting.ap_warning_report.rows import WarningRows

logger = logging.getLogger(__name__)

REPORT_COLUMNS = [
    "org_id",
    "device_id",
    "mac",
    "name",
    "serial",
    "model",
    "site_id",
    "site_name",
    "site_lookup_status",
    "connection_status",
    "code",
    "definition_status",
    "code_key",
    "code_name",
    "code_description",
    "trouble_source",
    "trouble_timestamp",
    "reported_at",
    "recovery_status",
    "recovery_reason",
    "evidence_status",
    "interruptions_60m",
    "recovery_connection_at",
    "statistics_observed_at",
    "fresh_connection_status",
    "fresh_trouble_code",
    "fresh_trouble_timestamp",
    "history_start",
    "history_end",
]


class ApWarningReport:
    """Run a read-only organization report without treating missing evidence as health."""

    @staticmethod
    def run() -> int:
        """Select an organization and return the number of exported warning rows."""
        logger.info("Selecting the organization for the AP warning report")
        org_id = SourceDependencyResolver.ConfigUtils.get_cached_or_prompted_org_id()
        logger.debug("AP warning report organization selected=%s", bool(org_id))
        if not org_id:
            logger.info("No organization was selected. No report was written.")
            return 0
        try:
            return ApWarningReport._export(str(UUID(org_id)))
        except (RequestException, RuntimeError, ValueError, OSError) as error:
            logger.error("AP warning report failed (%s)", type(error).__name__)
            raise RuntimeError("The AP warning report failed. Check source reads and output write errors.") from None

    @staticmethod
    def _export(org_id: str) -> int:
        """Finish all source reads and selection before any output write."""
        client = ApWarningClient(SourceDependencyResolver.apisession, org_id, runtime_settings.DEFAULT_API_PAGE_LIMIT)
        report = WarningRows(org_id, client.read())
        rows = report.build(datetime.now(UTC).isoformat())
        logger.info(
            "AP warning report scanned inventory APs=%d site statistics APs=%d missing trouble codes=%d "
            "outside-window trouble codes=%d recent trouble APs=%d",
            report.summary["inventory_aps"],
            report.summary["site_statistics_aps"],
            report.summary["missing_trouble"],
            report.summary["excluded_trouble"],
            report.summary["matched"],
        )
        if not rows:
            logger.info("No AP warning records matched. No report was written.")
            return 0
        retained, recovered = ApWarningReport._classify(rows, org_id)
        if recovered:
            ApWarningReport._persist(recovered, org_id, recovered=True)
        if not retained:
            logger.info(
                "No AP warning records matched after recovery filtering. Recovered records were exported separately."
            )
            return 0
        return ApWarningReport._persist(retained, org_id)

    @staticmethod
    def _classify(rows: list[dict[str, Any]], org_id: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Retain uncertain evidence and make each recovery visible in its own report."""
        reader = RecoveryEvidenceReader(
            SourceDependencyResolver.apisession, org_id, runtime_settings.DEFAULT_API_PAGE_LIMIT
        )
        retained: list[dict[str, Any]] = []
        recovered: list[dict[str, Any]] = []
        logger.info("Classifying AP warning candidates=%d", len(rows))
        for row in rows:
            row.update(RecoveryClassifier.classify(row, reader.read(row)))
            destination = recovered if row["recovery_status"] == "recovered" else retained
            destination.append(row)
            logger.info(
                "AP recovery decision mac=%s status=%s reason=%s evidence=%s interruptions=%s",
                row["mac"],
                row["recovery_status"],
                row["recovery_reason"],
                row["evidence_status"],
                row["interruptions_60m"],
            )
        logger.info(
            "AP recovery summary candidates=%d retained=%d recovered=%d", len(rows), len(retained), len(recovered)
        )
        logger.debug("Completed AP recovery classification")
        return retained, recovered

    @staticmethod
    def _persist(rows: list[dict[str, Any]], org_id: str, recovered: bool = False) -> int:
        """Require a successful standard output write before reporting completion."""
        prefix = "ApRecoveredReport" if recovered else "ApWarningReport"
        filename = f"{prefix}_{org_id}.csv"
        logger.info("Writing AP warning report rows=%d", len(rows))
        written = SourceDependencyResolver.DataExporter.write_with_format_selection(
            rows,
            filename,
            api_function_name="ap_recovered_report" if recovered else "ap_warning_report",
            fieldnames=REPORT_COLUMNS,
        )
        if written is not True:
            logger.error("The AP warning report output write failed")
            raise RuntimeError("The AP warning report output write failed")
        logger.debug("Wrote AP warning report rows=%d", len(rows))
        logger.info("Exported %d AP warning records to %s", len(rows), filename)
        return len(rows)
