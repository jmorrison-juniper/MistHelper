"""CSV export for the organization security posture report."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from src.export.data_exporter import DataExporter

logger = logging.getLogger(__name__)
POSTURE_API_FUNCTION_NAME = "orgSecurityPostureChecklist"


class OrgSecurityPostureExporter:
    """Persist organization security posture rows through DataExporter."""

    FILENAME = "OrgSecurityPosture.csv"
    FIELDNAMES = ["check id", "area", "setting path", "current value", "recommended value", "verdict", "reason"]

    def __init__(self, write_fn: Callable[..., bool] | None = None) -> None:
        """Store the export function dependency."""
        self.write_fn = write_fn or DataExporter._dispatch_format_write  # Keep this fleet branch CSV-only.

    def export(self, rows: list[dict[str, Any]]) -> bool:
        """Write rows to the standard CSV output path."""
        logging.info("Writing organization security posture CSV")  # Log before DataExporter runs.
        result = self.write_fn(  # Delegate output backend behavior to the existing exporter.
            rows,
            self.FILENAME,
            output_format="csv",
            fieldnames=self.FIELDNAMES,
            api_function_name=POSTURE_API_FUNCTION_NAME,
        )
        logging.debug("Organization security posture CSV write status: %s", result)  # Log the exporter result.
        return bool(result)  # Normalize mock or exporter return values to a bool.
