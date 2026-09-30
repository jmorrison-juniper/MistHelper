"""Output writers for alert digest and acknowledgement files."""

from __future__ import annotations  # Enable modern annotations without runtime imports.

import logging  # Record file writes before and after execution.
from pathlib import Path  # Build Windows-compatible paths without hardcoded separators.
from typing import Any  # Accept injected exporter objects in unit tests.

from src.config.source_dependency_resolver import SourceDependencyResolver  # Resolve the shared DataExporter seam.
from src.reports.alert_digest.model import AcknowledgementResult, AlarmGroup  # Type writer inputs.

logger = logging.getLogger(__name__)  # Keep log records tied to this module.

DIGEST_CSV = "AlertDigest.csv"  # Required CSV digest file name.
DIGEST_MARKDOWN = "AlertDigest.md"  # Required Markdown digest file name.
ACK_LOG_CSV = "AlertAcknowledgeLog.csv"  # Required acknowledgement log file name.
DIGEST_API_NAME = "alertDigest"  # API name used for export routing metadata.
ACK_API_NAME = "alertAcknowledgeLog"  # API name used for export routing metadata.
DIGEST_FIELDS = [  # Preserve the required CSV column order.
    "category",
    "severity",
    "alarm_type",
    "site",
    "recurrence",
    "first_seen",
    "last_seen",
    "sample_device_or_client",
    "acknowledged_state",
]
ACK_FIELDS = ["alarm_id", "alarm_type", "site", "outcome", "http_status", "message", "run_time"]  # Ack columns.


class AlertDigestWriter:
    """Write alert digest and acknowledgement outputs."""

    def __init__(self, exporter: Any | None = None, data_dir: Path | None = None) -> None:
        """Keep the exporter seam and the output directory."""
        self._exporter = exporter or SourceDependencyResolver.DataExporter  # Use shared exporter unless injected.
        self._data_dir = data_dir or Path("data")  # Match DataExporter for bare CSV file names.

    def write_digest(self, groups: list[AlarmGroup]) -> bool:
        """Write the CSV and Markdown digest outputs."""
        logger.info("Writing alert digest outputs")  # Log before file writes.
        csv_rows = [group.to_row() for group in groups] or [self._empty_digest_row()]  # Ensure an empty-state file.
        csv_ok = self._exporter.write_with_format_selection(
            csv_rows, DIGEST_CSV, api_function_name=DIGEST_API_NAME, fieldnames=DIGEST_FIELDS
        )
        markdown_ok = self._write_markdown(groups)  # Write the companion handover summary.
        logger.debug("Alert digest output result csv_ok=%s markdown_ok=%s", csv_ok, markdown_ok)  # Log result.
        return bool(csv_ok and markdown_ok)  # Report success only when both files were written.

    def write_acknowledgement_log(self, results: list[AcknowledgementResult]) -> bool:
        """Write acknowledgement result rows to CSV."""
        logger.info("Writing alert acknowledgement log")  # Log before file write.
        rows = [result.to_row() for result in results]  # Convert value objects to CSV rows.
        csv_ok = self._exporter.write_with_format_selection(
            rows, ACK_LOG_CSV, api_function_name=ACK_API_NAME, fieldnames=ACK_FIELDS
        )
        logger.debug("Alert acknowledgement log write result=%s rows=%d", csv_ok, len(rows))  # Log result.
        return bool(csv_ok)  # Return the exporter result.

    def _write_markdown(self, groups: list[AlarmGroup]) -> bool:
        """Write the Markdown handover summary."""
        logger.info("Writing alert digest Markdown output")  # Log before direct file write.
        path = self._data_dir / DIGEST_MARKDOWN  # Build the Markdown path under data/.
        try:
            path.parent.mkdir(parents=True, exist_ok=True)  # Ensure data/ exists before writing.
            path.write_text(self._markdown_text(groups), encoding="utf-8")  # Write the operator handover document.
        except OSError:
            logger.exception("Failed to write alert digest Markdown output to %s", path)  # Include traceback.
            return False  # Report failure to the operation.
        logger.debug("Wrote alert digest Markdown output to %s", path)  # Log result path.
        return True  # Report success.

    @staticmethod
    def _markdown_text(groups: list[AlarmGroup]) -> str:
        """Return the Markdown handover content."""
        lines = ["# Alert Digest", ""]  # Start with a stable title.
        if not groups:  # No alarms still needs an operator-readable file.
            return "\n".join([*lines, "No alarms were found in the lookback window.", ""])  # Empty state.
        for category in sorted({group.category for group in groups}):  # Create one section for each category.
            lines.extend([f"## {category}", ""])  # Add the category section.
            for group in [item for item in groups if item.category == category]:  # Add each group in that category.
                lines.append(
                    f"- {group.severity}: {group.alarm_type} at {group.site} "
                    f"occurred {group.recurrence} time(s), last seen {group.last_seen or 'unknown'}."
                )
            lines.append("")  # Separate sections with one blank line.
        return "\n".join(lines)  # Return the full Markdown document.

    @staticmethod
    def _empty_digest_row() -> dict[str, Any]:
        """Return one CSV row that makes the empty state visible."""
        return {field: "" for field in DIGEST_FIELDS} | {"category": "none", "alarm_type": "no_alarms", "site": "none"}
