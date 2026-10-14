"""Save complete settings and verify private backups before any Mist settings change."""

from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from .sdk import PolicyError

logger = logging.getLogger(__name__)
BACKUP_DIRECTORY = ".firmware-policy-backups"


class PolicyBackup:
    """Create a private, unique settings bundle and prove its read-back contents."""

    def __init__(self, data_directory: Path) -> None:
        """Locate the ignored product data root without touching an earlier backup."""
        self.root = data_directory.resolve() / BACKUP_DIRECTORY  # Keep backups inside product data storage.

    @staticmethod
    def digest(records: list[dict[str, Any]]) -> str:
        """Hash canonical complete records so verification detects content changes."""
        try:
            content = json.dumps(records, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
        except (TypeError, ValueError) as error:
            logger.error("Firmware policy backup contains invalid JSON values: %s", type(error).__name__)
            raise PolicyError("The complete settings cannot be serialized into a valid backup.") from None
        return hashlib.sha256(content).hexdigest()  # Record integrity without revealing settings.

    def save(self, records: list[dict[str, Any]]) -> Path:
        """Write every target's settings before the workflow can send its first change."""
        logger.info("Save firmware policy backup for %s settings records", len(records))
        document = {  # Retain complete settings, not only the targeted auto-upgrade policy.
            "created_at": datetime.now(UTC).isoformat(),
            "record_count": len(records),
            "sha256": self.digest(records),
            "records": records,
        }
        path = self._create_file(document)  # Exclusive creation preserves every previous backup.
        self.verify(path, records)  # The write alone does not satisfy the backup gate.
        logger.debug("Verified firmware policy backup for %s settings records", len(records))
        return path  # Only the local operator receives its location.

    def _create_file(self, document: dict[str, Any]) -> Path:
        """Restrict local permissions and flush the unique bundle before verification."""
        try:
            if self.root.is_symlink():
                raise PolicyError("The private backup directory must not be a symbolic link.")
            self.root.mkdir(mode=0o700, parents=True, exist_ok=True)  # Do not use public product-output permissions.
            if os.name != "nt":
                self.root.chmod(0o700)  # Restrict this feature-owned private directory.
            path = self.root / f"{uuid4()}.json"  # A new bundle cannot overwrite an earlier backup.
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)  # Refuse an existing path.
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                json.dump(document, stream, sort_keys=True, allow_nan=False)  # Serialize full settings privately.
                stream.flush()  # Send the complete JSON to the operating system.
                os.fsync(stream.fileno())  # Flush the file before any cloud write.
            return path  # The caller must verify the content before using it.
        except (OSError, TypeError, ValueError) as error:
            logger.error("Firmware policy backup write failed: %s", type(error).__name__)
            raise PolicyError("The settings backup could not be written. No settings change is permitted.") from None

    def verify(self, path: Path, expected: list[dict[str, Any]]) -> None:
        """Read the complete bundle and compare every original setting and identifier."""
        logger.info("Verify firmware policy backup for %s settings records", len(expected))
        try:
            if path.is_symlink() or path.parent != self.root:
                raise PolicyError("The backup file is outside the private backup directory.")
            if os.name != "nt" and path.stat().st_mode & 0o077:
                raise PolicyError("The backup file permits access from another account.")
            document = json.loads(path.read_text(encoding="utf-8"))  # Read the actual durable file.
            valid = (  # Verify all records, their count, and their canonical checksum.
                isinstance(document, dict)
                and document.get("records") == expected
                and document.get("record_count") == len(expected)
                and document.get("sha256") == self.digest(expected)
            )
            if not valid:
                raise PolicyError("The settings backup does not match the original settings.")
        except (OSError, TypeError, ValueError) as error:
            logger.error("Firmware policy backup read failed: %s", type(error).__name__)
            raise PolicyError("The settings backup could not be verified. No settings change is permitted.") from None
        logger.debug("Verified %s complete settings backup records", len(expected))
