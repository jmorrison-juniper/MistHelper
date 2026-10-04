"""Output writer for site RRM plan captures and diffs."""

from __future__ import annotations  # WHY: keep annotations import-safe.

import logging  # WHY: log before and after each output write.
from typing import Any  # WHY: exporter and processing helpers are runtime dependencies.

from src.mist.resources.site.rrm_reset.model import (
    RRM_AFTER_FILENAME,
    RRM_BEFORE_FILENAME,
    RRM_DIFF_ENDPOINT,
    RRM_DIFF_FILENAME,
)

logger = logging.getLogger(__name__)  # WHY: module logger lets operators filter this feature.


class RrmPlanWriter:
    """Write RRM before, after, and diff rows through the shared exporter."""

    def __init__(self, data_exporter: Any, data_processing_utils: Any) -> None:
        """Store shared export dependencies."""
        self.data_exporter = data_exporter  # WHY: keep the project output backend selection.
        self.data_processing_utils = data_processing_utils  # WHY: flatten rows the same way site exports do.

    def write_before(self, rows: list[dict[str, Any]]) -> bool:
        """Write the before capture."""
        return self._write(rows, RRM_BEFORE_FILENAME, "getSiteCurrentChannelPlanning")  # WHY: before uses read key.

    def write_after(self, rows: list[dict[str, Any]]) -> bool:
        """Write the after capture."""
        return self._write(rows, RRM_AFTER_FILENAME, "getSiteCurrentChannelPlanning")  # WHY: after uses read key.

    def write_diff(self, rows: list[dict[str, Any]]) -> bool:
        """Write the changed-radio diff."""
        return self._write(rows, RRM_DIFF_FILENAME, RRM_DIFF_ENDPOINT)  # WHY: diff uses feature-specific key.

    def _write(self, rows: list[dict[str, Any]], filename: str, endpoint: str) -> bool:
        """Write rows and return whether the exporter accepted them."""
        logger.info("Writing %d RRM rows to %s", len(rows), filename)  # WHY: action log before output.
        flat_rows = self.data_processing_utils.flatten_nested_fields(rows)  # WHY: CSV output needs flat columns.
        result = self.data_exporter.write_with_format_selection(  # WHY: use the shared backend dispatcher.
            flat_rows,
            filename,
            api_function_name=endpoint,
        )
        logger.debug("RRM output write finished filename=%s written=%s", filename, bool(result))  # WHY: result log.
        return bool(result)  # WHY: operation stops if the before write fails.
