"""Persist sanitized status atomically with private access beneath DATA_DIR."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.operations.execution.firmware_policy.recovery.backup import BACKUP_DIRECTORY, BackupAccess
from src.operations.execution.firmware_policy.sdk import PolicyError

logger = logging.getLogger(__name__)


class JobDocuments:
    """Validate private status documents before recovering any public outcome."""

    @staticmethod
    def read(path: Path) -> dict[str, Any]:
        """Check the opened file rather than trusting an earlier path inspection."""
        BackupAccess.verify(path)  # Reject shared access and alternate links before opening.
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))  # Refuse a substituted symbolic link.
        with os.fdopen(descriptor, encoding="utf-8") as stream:
            BackupAccess.verify(path, status=os.fstat(stream.fileno()))  # Verify the actual opened file.
            document = json.load(stream)  # Invalid JSON fails initialization rather than implying no jobs.
        if not isinstance(document, dict):
            raise PolicyError("The persistent job document is not valid.")
        return document  # No executable settings plan can be recovered from this format.

    @staticmethod
    def status(path: Path) -> dict[str, Any]:
        """Require an owned job identity and a documented state in each record."""
        record = JobDocuments.read(path)  # Native private access precedes content validation.
        states = {"queued", "preparing", "ready", "applying", "complete", "partial", "failed", "interrupted"}
        if (
            record.get("job_id") != path.stem
            or not isinstance(record.get("owner"), str)
            or not isinstance(record.get("state"), str)
            or record["state"] not in states
        ):
            raise PolicyError("The persistent job status is not valid.")
        return record  # The owner digest binds terminal outcomes to the original browser.

    @staticmethod
    def progress(path: Path, record: dict[str, Any]) -> None:
        """Recover the latest small progress event without changing the durable job state."""
        document = JobDocuments.read(path)  # Progress requires the same native private access.
        if document.get("job_id") != record["job_id"] or not isinstance(document.get("progress"), dict):
            raise PolicyError("The persistent job progress is not valid.")
        record["progress"] = document["progress"]  # A restart retains its last wait but never a token.


class JobFiles:
    """Refuse links and shared files before reading or replacing a job status."""

    def __init__(self, data_dir: Path) -> None:
        """Create a private status directory without changing unrelated permissions."""
        root = data_dir.resolve() / BACKUP_DIRECTORY  # Existing download guards protect every descendant.
        root.mkdir(mode=0o700, parents=True, exist_ok=True)  # Create the feature-owned private root.
        BackupAccess.verify(root, directory=True)  # Check native Windows ACLs or POSIX owner permissions.
        self.directory = root / ".portal-jobs"  # Bundle listings examine only root-level backup files.
        self.directory.mkdir(mode=0o700, exist_ok=True)  # New records need private access.
        BackupAccess.verify(self.directory, directory=True)  # Reject linked or shared existing storage.

    def save(self, record: dict[str, Any]) -> None:
        """Replace one sanitized file only after a complete private write."""
        path = self.directory / f"{record['job_id']}.json"  # Identifiers originate only from uuid4.
        self._write(path, record)  # Full rows change only at preparation and completion boundaries.

    def progress(self, record: dict[str, Any]) -> None:
        """Persist a small progress record instead of repeatedly rewriting thousands of rows."""
        path = self.directory / f"{record['job_id']}.progress"  # Bundle enumeration ignores these private files.
        document: dict[str, Any] = {
            key: record[key] for key in ("job_id", "progress", "updated_at") if key in record
        }  # Explicit string keys keep the progress document compatible with the shared writer.
        self._write(path, document)  # Large runs need constant-sized admission updates.

    def _write(self, path: Path, record: dict[str, Any]) -> None:
        """Flush one complete sanitized document before replacing its private destination."""
        BackupAccess.verify(self.directory.parent, directory=True)  # Reject a substituted backup root.
        BackupAccess.verify(self.directory, directory=True)  # Recheck private access at each write boundary.
        if path.exists() or path.is_symlink():
            BackupAccess.verify(path)  # Refuse an unsafe destination before replacement.
        staging = self.directory / f".{uuid4()}.pending"  # Never use a system temporary directory.
        logger.info("Persist firmware job status for %s", record["job_id"])
        try:
            descriptor = os.open(staging, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)  # Prevent shared creation.
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                json.dump(record, stream, ensure_ascii=True, allow_nan=False)  # Persist only sanitized metadata.
                stream.flush()  # Finish the file before making it visible.
                os.fsync(stream.fileno())  # Preserve the explicit status across process termination.
            os.replace(staging, path)  # Polling never observes a partially written record.
            BackupAccess.verify(path)  # Native access checks must cover the replacement file.
        finally:
            staging.unlink(missing_ok=True)  # Remove only this writer's incomplete file.
        logger.debug("Persisted firmware job %s with %s status fields", record["job_id"], len(record))

    def read_all(self) -> list[dict[str, Any]]:
        """Read durable outcomes and fail closed on unreadable status input."""
        BackupAccess.verify(self.directory, directory=True)  # Refuse a substituted directory before enumeration.
        records: list[dict[str, Any]] = []  # Executable settings plans are never restored.
        logger.info("Read persistent firmware job status")
        for path in self.directory.glob("*.json"):
            record = JobDocuments.status(path)  # Refuse unreadable, shared, linked, or malformed input.
            progress_path = (
                self.directory / f"{record['job_id']}.progress"
            )  # Recover the last admission wait after interruption.
            if progress_path.exists() and record["state"] in {"queued", "preparing", "ready", "applying"}:
                JobDocuments.progress(progress_path, record)  # Recover only the last observed admission event.
            records.append(record)  # Only status survives a worker restart.
        logger.debug("Read %s persistent firmware job records", len(records))
        return records  # Recovery never submits writes.
