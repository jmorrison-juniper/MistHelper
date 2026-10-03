"""Process-safe rotating file logging for shared container mounts."""

from __future__ import annotations

import logging
import os
import time
from logging.handlers import RotatingFileHandler
from typing import Any


class ProcessSafeRotatingFileHandler(RotatingFileHandler):
    """Write and rotate one log file safely from multiple processes."""

    def __init__(self, filename: str, max_bytes: int, backup_count: int) -> None:
        """Create a delayed rotating handler with a shared lock file."""
        super().__init__(filename, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8", delay=True)
        self._process_lock_path = f"{self.baseFilename}.lock"
        with open(self._process_lock_path, "ab") as lock_file:
            if lock_file.tell() == 0:
                lock_file.write(b"\0")

    def _acquire_process_lock(self) -> Any:
        """Acquire the shared lock file before one write or rollover."""
        lock_file = open(self._process_lock_path, "a+b")
        lock_file.seek(0)
        if os.name == "nt":
            import msvcrt

            while True:
                try:
                    msvcrt.locking(lock_file.fileno(), msvcrt.LK_LOCK, 1)
                    break
                except OSError:
                    time.sleep(0.01)
        else:
            import fcntl

            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        return lock_file

    def _release_process_lock(self, lock_file: Any) -> None:
        """Release the shared lock file after one write or rollover."""
        if os.name == "nt":
            import msvcrt

            lock_file.seek(0)
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
        lock_file.close()

    def _reopen_if_rotated(self) -> None:
        """Reopen the active file when another process completed a rollover."""
        if self.stream is None:
            return
        try:
            active_stat = os.stat(self.baseFilename)
            stream_stat = os.fstat(self.stream.fileno())
        except OSError:
            self.stream.close()
            self.stream = self._open()
            return
        if (active_stat.st_dev, active_stat.st_ino) == (stream_stat.st_dev, stream_stat.st_ino):
            return
        self.stream.flush()
        self.stream.close()
        self.stream = self._open()

    def emit(self, record: logging.LogRecord) -> None:
        """Serialize one complete record and any required rollover."""
        lock_file = self._acquire_process_lock()
        try:
            self._reopen_if_rotated()
            super().emit(record)
        finally:
            self._release_process_lock(lock_file)
