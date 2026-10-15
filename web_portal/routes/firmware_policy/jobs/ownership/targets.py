"""Exclude overlapping policy and restoration writers across local worker processes."""

from __future__ import annotations

import hashlib
import os
from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from pathlib import Path
from typing import Any

from src.operations.execution.firmware_policy.recovery.backup import BackupAccess
from src.operations.execution.firmware_policy.sdk import PolicyError

from . import WorkerLock


class TargetWrites:
    """Hold every selected organization's native lock through all domain apply safeguards."""

    @staticmethod
    @contextmanager
    def hold(directory: Path, cloud: str, organizations: set[str]) -> Iterator[None]:
        """Refuse another live writer before freshness, mutation, or readback starts."""
        root = directory / ".writer-locks"  # Keep lock ownership under the existing private backup guard.
        root.mkdir(mode=0o700, exist_ok=True)
        BackupAccess.verify(root, directory=True)
        with ExitStack() as stack:
            for identifier in sorted(organizations):
                digest = hashlib.sha256(f"{cloud}:{identifier}".encode()).hexdigest()
                path = root / f"{digest}.lock"  # Scope locks never expose cloud or organization identifiers.
                descriptor = os.open(path, os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0), 0o600)
                stream: Any = stack.enter_context(os.fdopen(descriptor, "r+b"))
                BackupAccess.verify(path)  # Reject shared permissions and alternate links.
                if not stream.read(1):
                    stream.write(b"1")
                    stream.flush()
                if not WorkerLock.acquire(stream):
                    raise PolicyError(
                        "The selected organization has another active settings writer. Prepare again after it finishes."
                    )
            yield  # Domain backup freshness, settings writes, and saved-state checks run while all locks remain held.
