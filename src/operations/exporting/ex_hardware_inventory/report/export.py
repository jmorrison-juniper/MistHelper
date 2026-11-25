"""Write the one CSV report of a CLI run through the standard exporter.

Why:
    The CLI must send the rows through the configured output backends, so it
    writes through ``DataExporter`` and not through a private writer. That
    exporter swallows some file errors and does not write atomically. So this
    module forces the CSV format, picks a name that no earlier report holds,
    reads the file back, and removes it when the read-back does not match the
    rows. A damaged file can then never pass as a report.
"""

from __future__ import annotations

import logging  # Record each write and each check for the operator trace.
from collections.abc import Mapping, Sequence  # Accept any rows and any column list.
from dataclasses import dataclass  # Keep the result immutable.
from datetime import datetime  # The file name carries the run time.
from pathlib import Path  # Build paths for Windows, macOS, and Linux.

from src.foundation.models.dataclasses.export_backend_options import ExportBackendOptions  # Force the CSV format.
from src.foundation.runtime.config.source_dependency_resolver import SourceDependencyResolver  # Standard exporter.
from src.operations.exporting.ex_hardware_inventory.report.csv_file import (
    CsvRenderer,
    CsvVerifier,
    ReportCheckError,
)  # Size check and file check.

logger = logging.getLogger(__name__)  # Name the logger after this module so log lines carry their source.


@dataclass(frozen=True)
class ReportFile:
    """The file that a run wrote.

    Attributes:
        path: The path of the CSV file.
        row_count: The number of data rows in the file.
    """

    path: Path  # Shown to the operator.
    row_count: int  # Shown to the operator.


class ReportExporter:
    """Write the one CSV report and prove the file."""

    LIMIT_BYTES = 64 * 1024 * 1024  # The saved-output limit of one run, the same as the portal limit.
    API_NAME = "ExHardwareInventory"  # The key of the natural-key strategy for the database backends.

    def __init__(self, data_dir: Path = Path("data")) -> None:
        """Store the folder of the report.

        Args:
            data_dir: The folder that holds product output.
        """
        self._data_dir = data_dir  # The product output folder, a test passes a temporary folder.

    def write(
        self, rows: Sequence[Mapping[str, str]], fieldnames: Sequence[str], run_time: datetime
    ) -> ReportFile | None:
        """Write the report, check the file, and return it.

        Args:
            rows: The report rows.
            fieldnames: The column list and order.
            run_time: The run start in UTC. It names the file.

        Returns:
            The written file, or None when there is no row.

        Raises:
            ReportTooLarge: When the file would pass the saved-output limit. No file is written.
            ReportCheckError: When the exporter fails or the file does not match the rows. No file stays.
        """
        if not rows:  # FR-042: a run with no row writes no file.
            logger.info("No report rows. No file is written.")  # Say so in the log.
            return None  # Nothing to write.
        CsvRenderer.render(rows, fieldnames, self.LIMIT_BYTES)  # Refuse a report over the limit before any write.
        path = self._unique_path(run_time)  # A name that no earlier report holds.
        logger.info("Writing %d report rows through the standard exporter", len(rows))  # Log before the write.
        written = SourceDependencyResolver.DataExporter.write_with_format_selection(
            list(rows),
            str(path),
            api_function_name=self.API_NAME,
            fieldnames=list(fieldnames),
            backend_options=ExportBackendOptions(format_override="csv"),
        )  # The CSV format is forced, whatever OUTPUT_FORMAT holds.
        try:  # The check removes the file on any failure.
            if written is not True:  # The exporter reports its own failure.
                raise ReportCheckError("The exporter did not write the report.")
            CsvVerifier.verify(path.read_bytes(), fieldnames, len(rows))  # Read the file back.
        except (ReportCheckError, OSError) as error:  # A missing, unreadable, or damaged file.
            path.unlink(missing_ok=True)  # No damaged file may stay under the report name.
            logger.error("The report file failed its check and was removed (%s)", type(error).__name__)
            raise ReportCheckError(str(error)) from None  # One documented error for the operation.
        logger.debug("Wrote and checked the report file with %d rows", len(rows))  # Log the result.
        return ReportFile(path, len(rows))  # Hand the file to the operation.

    def _unique_path(self, run_time: datetime) -> Path:
        """Return a path that no earlier report uses, and make sure its folder exists."""
        self._data_dir.mkdir(parents=True, exist_ok=True)  # The exporter creates the folder for bare names only.
        base = f"{self.API_NAME}_{run_time.strftime('%Y%m%dT%H%M%SZ')}"  # The UTC stamp of the run.
        path = self._data_dir / f"{base}.csv"  # The first choice.
        counter = 2  # A second report in the same second gets the suffix _2.
        while path.exists():  # Never overwrite an earlier report.
            path = self._data_dir / f"{base}_{counter}.csv"  # The next free name.
            counter += 1  # Try the next suffix.
        return path  # A free path.
