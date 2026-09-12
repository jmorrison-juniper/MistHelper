"""Hold process-owned audit records for one E2E server."""

from __future__ import annotations  # Keep annotations independent from import order.

import logging  # Record each process-owned audit operation.
from copy import deepcopy  # Stop a caller from changing a stored audit row.
from typing import Any  # Audit records contain different JSON-compatible fields.

logger = logging.getLogger(__name__)  # Keep audit activity tied to this module.


class AuditRecordStore:  # Own audit records for one isolated server process.
    """Own audit rows for one test run."""

    def __init__(self, test_run_id: str) -> None:  # Bind the empty store to one test owner.
        """Create an empty audit store."""
        self.test_run_id = test_run_id  # Bind every audit row to one E2E server.
        self._rows: list[dict[str, Any]] = []  # Preserve audit insertion order.

    def append(self, record: dict[str, Any]) -> None:  # Store one owned audit record.
        """Store one audit row and reject a different owner."""
        logger.info("Store one E2E audit record")  # Record the audit write.
        copied = deepcopy(record)  # Isolate the stored row from the caller.
        owner = copied.get("test_run_id")  # Read the supplied owner before adding one.
        if owner not in (None, self.test_run_id):  # Another E2E server owns this row.
            raise ValueError("The record belongs to a different E2E test run.")  # Reject cross-process data.
        copied["test_run_id"] = self.test_run_id  # Make ownership explicit on the stored row.
        self._rows.append(copied)  # Keep the row in stable action order.
        logger.debug("The E2E audit store now holds %s record(s)", len(self._rows))  # Report a safe count.

    def list(self) -> list[dict[str, Any]]:  # List owned audit records in newest-first order.
        """Return all audit rows in newest-first order."""
        logger.info("List E2E audit records")  # Record the process-owned scan.
        rows = [deepcopy(record) for record in reversed(self._rows)]  # Protect and reverse the stored rows.
        logger.debug("The E2E audit list holds %s record(s)", len(rows))  # Report a safe count.
        return rows  # Match the history page order.
