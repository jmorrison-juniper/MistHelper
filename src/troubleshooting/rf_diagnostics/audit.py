"""Append-only audit writer for RF diagnostics."""

from __future__ import annotations  # WHY: keep annotations simple across imports.

import csv  # WHY: write the operator audit trail in the existing CSV format.
import logging  # WHY: record file actions before and after they happen.
from pathlib import Path  # WHY: build data paths without platform-specific separators.

from src.troubleshooting.rf_diagnostics.models import RfDiagnosticRun  # WHY: the audit writer stores run rows.

logger = logging.getLogger(__name__)  # WHY: let operators filter audit-writer logs by module.


class RfDiagnosticsAuditWriter:
    """Append one row per RF diagnostics run."""

    def __init__(self, csv_path: Path | str = Path("data") / "RfDiagnostics.csv") -> None:
        """Store the audit CSV path."""
        self.csv_path = Path(csv_path)  # WHY: normalize strings and paths once at construction.

    def append(self, run: RfDiagnosticRun) -> bool:
        """Append one RF diagnostics row and report whether the write succeeded."""
        logger.info("Writing RF diagnostics audit row to %s", self.csv_path)  # WHY: action log before file write.
        try:  # WHY: a failed audit write must not hide the diagnostic result.
            self.csv_path.parent.mkdir(parents=True, exist_ok=True)  # WHY: data/ may not exist in a new worktree.
            exists = self.csv_path.exists()  # WHY: the header is needed only for a new file.
            with self.csv_path.open("a", newline="", encoding="utf-8") as file_handle:  # WHY: append preserves history.
                writer = csv.DictWriter(file_handle, fieldnames=RfDiagnosticRun.column_names())  # WHY: stable columns.
                if not exists:  # WHY: a new file needs one header row.
                    writer.writeheader()  # WHY: operators can read the CSV without a data dictionary.
                writer.writerow(run.as_row())  # WHY: one call writes exactly one run row.
            logger.debug("Wrote RF diagnostics audit row status=%s", run.status)  # WHY: result summary after write.
            return True  # WHY: the caller can report successful persistence.
        except OSError as error:  # WHY: disk errors must be visible but non-fatal.
            logger.error("RF diagnostics audit write failed: %s", error)  # WHY: no secret values appear in the log.
            return False  # WHY: the caller can report that audit persistence failed.
