"""CSV audit writer for client session control request attempts."""

from __future__ import annotations  # WHY: keep annotations stable on Python 3.13.

import csv  # WHY: audit trail is a CSV file for operator review.
import logging  # WHY: action logging is required around file writes.
from pathlib import Path  # WHY: cross platform paths are required.

from src.device.client_session_control.models import ClientSessionControlLogRow  # WHY: writer accepts typed rows.

logger = logging.getLogger(__name__)  # WHY: module logger supports audit write troubleshooting.
DEFAULT_LOG_PATH = Path("data") / "ClientSessionControlLog.csv"  # WHY: contract requires this runtime file.
FIELD_NAMES: tuple[str, ...] = (  # WHY: stable CSV schema for audits and tests.
    "timestamp_utc",  # WHY: event time in UTC.
    "site_id",  # WHY: Mist site identifier.
    "site_name",  # WHY: readable site name.
    "action_key",  # WHY: stable action key.
    "action_label",  # WHY: readable action label.
    "target_type",  # WHY: client MAC or rogue BSSID.
    "target",  # WHY: normalized target.
    "dry_run",  # WHY: preview only flag.
    "confirmed",  # WHY: confirmation status.
    "operation_id",  # WHY: Mist operation ID.
    "result",  # WHY: final result.
    "message",  # WHY: safe summary.
)


class ClientSessionAuditWriter:  # WHY: class owns the durable audit file boundary.
    """Append client session control attempts to the CSV audit file."""

    def __init__(self, log_path: Path = DEFAULT_LOG_PATH) -> None:
        """Create an audit writer for one CSV path."""
        self._log_path = log_path  # WHY: path is injected for tests and defaults to data/.

    def write(self, row: ClientSessionControlLogRow) -> None:
        """Append one audit row and create the header when needed."""
        logger.info("Writing client session control audit row to %s", self._log_path)  # WHY: before file write.
        self._log_path.parent.mkdir(parents=True, exist_ok=True)  # WHY: data/ may not exist on first run.
        needs_header = not self._log_path.exists() or self._log_path.stat().st_size == 0  # WHY: header once.
        with self._log_path.open("a", newline="", encoding="utf-8") as file_handle:  # WHY: append text CSV safely.
            writer = csv.DictWriter(file_handle, fieldnames=FIELD_NAMES)  # WHY: enforce column order.
            if needs_header:  # WHY: new CSV files need a header for operator review.
                writer.writeheader()  # WHY: write the schema before the first row.
            writer.writerow(row.as_dict())  # WHY: append exactly one row per request attempt.
        logger.debug("Wrote client session control audit row with result %s", row.result)  # WHY: after write.
