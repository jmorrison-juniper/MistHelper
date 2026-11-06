"""Export AP trouble evidence through the existing output backend selection."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from requests import RequestException

from src.foundation.runtime.config import runtime_settings
from src.foundation.runtime.config.source_dependency_resolver import SourceDependencyResolver
from src.operations.exporting.ap_warning_report.client import ApWarningClient
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
            "AP warning report scanned APs=%d missing trouble evidence=%d matched APs=%d",
            report.summary["inventory_aps"],
            report.summary["missing_trouble"],
            report.summary["matched"],
        )
        if not rows:
            logger.info("No AP warning records matched. No report was written.")
            return 0
        return ApWarningReport._persist(rows, org_id)

    @staticmethod
    def _persist(rows: list[dict[str, Any]], org_id: str) -> int:
        """Require a successful standard output write before reporting completion."""
        filename = f"ApWarningReport_{org_id}.csv"
        logger.info("Writing AP warning report rows=%d", len(rows))
        written = SourceDependencyResolver.DataExporter.write_with_format_selection(
            rows, filename, api_function_name="ap_warning_report", fieldnames=REPORT_COLUMNS
        )
        if written is not True:
            logger.error("The AP warning report output write failed")
            raise RuntimeError("The AP warning report output write failed")
        logger.debug("Wrote AP warning report rows=%d", len(rows))
        logger.info("Exported %d AP warning records to %s", len(rows), filename)
        return len(rows)
