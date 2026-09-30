"""CSV export for the organization security posture report."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from src.export.data_exporter import DataExporter

logger = logging.getLogger(__name__)


class OrgSecurityPostureExporter:
    """Persist organization security posture rows through DataExporter."""

    FILENAME = "OrgSecurityPosture.csv"
    FIELDNAMES = ["check id", "area", "setting path", "current value", "recommended value", "verdict", "reason"]
    API_FUNCTION_NAME = "orgSecurityPostureChecklist"

    def __init__(self, write_fn: Callable[..., bool] | None = None) -> None:
        """Store the export function dependency."""
        self.write_fn = write_fn or DataExporter.write_with_format_selection  # Allow tests to avoid file writes.

    def export(self, rows: list[dict[str, Any]]) -> bool:
        """Write rows to the standard CSV output path."""
        logging.info("Writing organization security posture CSV")  # Log before DataExporter runs.
        result = self.write_fn(  # Delegate output backend behavior to the existing exporter.
            rows,
            self.FILENAME,
            api_function_name=self.API_FUNCTION_NAME,
            fieldnames=self.FIELDNAMES,
        )
        logging.debug("Organization security posture CSV write status: %s", result)  # Log the exporter result.
        return bool(result)  # Normalize mock or exporter return values to a bool.
