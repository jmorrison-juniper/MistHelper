"""File persistence for RMA device replacement evidence."""

from __future__ import annotations  # WHY: keep annotations import-safe.

import csv  # WHY: DeviceReplaceLog.csv is a change-record CSV file.
import json  # WHY: old device configuration backups are JSON files.
import logging  # WHY: log before and after each file action.
from datetime import UTC, datetime  # WHY: stamp backups and rows in a stable timezone.
from pathlib import Path  # WHY: Windows-compatible path construction.
from typing import Any  # WHY: configuration payloads contain arbitrary JSON values.

from src.mist.resources.inventory.device_replace.models import (
    DeviceReplaceLogEntry,
    InventoryDevice,
)  # WHY: persistence writes models.

logger = logging.getLogger(__name__)  # WHY: module log records identify the file seam.

DATA_DIR = Path("data")  # WHY: MistHelper stores runtime outputs under data.


class DeviceReplacePersistence:
    """Write backup JSON files and the replacement CSV log."""

    def __init__(self, data_dir: Path = DATA_DIR) -> None:
        """Store the data directory for evidence files."""
        self._data_dir = data_dir  # WHY: tests inject a controlled project-relative directory.
        self._backup_dir = data_dir / "rma_backups"  # WHY: backup location follows the contract.
        self._log_path = data_dir / "DeviceReplaceLog.csv"  # WHY: log location follows the contract.

    @staticmethod
    def timestamp() -> str:
        """Return a UTC timestamp for evidence rows."""
        return datetime.now(tz=UTC).replace(microsecond=0).isoformat()  # WHY: readable and stable.

    def write_backup(self, org_id: str, old_device: InventoryDevice, configuration: dict[str, Any]) -> Path:
        """Write the old device configuration backup and return its path."""
        logger.info("Writing RMA backup for old device=%s", old_device.mac)  # WHY: action log before file write.
        self._backup_dir.mkdir(parents=True, exist_ok=True)  # WHY: a fresh worktree may not have the directory.
        backup_path = self._backup_dir / f"{old_device.mac}_{self._safe_stamp()}.json"  # WHY: one file per run.
        payload = self._backup_payload(org_id, old_device, configuration)  # WHY: keep metadata with configuration.
        backup_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")  # WHY: durable JSON.
        logger.debug("Wrote RMA backup path=%s bytes=%d", backup_path, backup_path.stat().st_size)  # WHY: result.
        return backup_path  # WHY: operation must log the backup path.

    def append_log(self, entry: DeviceReplaceLogEntry) -> None:
        """Append one replacement result row to the CSV log."""
        logger.info("Appending RMA replacement log result=%s", entry.result)  # WHY: action log before file write.
        self._data_dir.mkdir(parents=True, exist_ok=True)  # WHY: a fresh worktree may not have data.
        file_exists = self._log_path.exists()  # WHY: write the header only for a new file.
        with self._log_path.open("a", encoding="utf-8", newline="") as handle:  # WHY: append preserves history.
            writer = csv.DictWriter(handle, fieldnames=DeviceReplaceLogEntry.COLUMNS)  # WHY: stable CSV columns.
            if not file_exists:  # WHY: the first row needs headers for operators.
                writer.writeheader()  # WHY: human-readable CSV output.
            writer.writerow(entry.as_row())  # WHY: append the one operation result.
        logger.debug("RMA replacement log path=%s exists=%s", self._log_path, self._log_path.exists())  # WHY: result.

    @staticmethod
    def _backup_payload(org_id: str, old_device: InventoryDevice, configuration: dict[str, Any]) -> dict[str, Any]:
        """Return the JSON payload for one backup file."""
        return {
            "backup_time": DeviceReplacePersistence.timestamp(),
            "org_id": org_id,
            "old_device": old_device.raw,
            "configuration": configuration,
        }

    @staticmethod
    def _safe_stamp() -> str:
        """Return a filename-safe UTC timestamp."""
        return DeviceReplacePersistence.timestamp().replace(":", "").replace("+", "Z")  # WHY: Windows path safe.
