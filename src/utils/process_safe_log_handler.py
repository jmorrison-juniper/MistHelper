"""Process-safe rotating file logging for shared container mounts."""

from __future__ import annotations

import hashlib
import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Any


class ProcessSafeRotatingFileHandler(RotatingFileHandler):
    """Write and rotate one log file safely from multiple processes."""

    def __init__(self, filename: str, max_bytes: int, backup_count: int) -> None:
        """Create a delayed rotating handler with a shared lock file."""
        super().__init__(filename, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8", delay=True)
        self._process_lock_path = f"{self.baseFilename}.lock"
        digest = hashlib.sha256(self.baseFilename.encode("utf-8")).hexdigest()
        self._windows_mutex_name = f"Local\\MistHelperLog-{digest}"
        with open(self._process_lock_path, "ab") as lock_file:
            if lock_file.tell() == 0:
                lock_file.write(b"\0")

    def _acquire_windows_mutex(self) -> Any:
        """Acquire a named mutex for Windows hosts."""
        ctypes_module = __import__("ctypes")  # Load Windows APIs without platform-stub attribute errors.
        kernel32 = ctypes_module.WinDLL("kernel32", use_last_error=True)  # Load the mutex API for coordination.
        handle = kernel32.CreateMutexW(None, False, self._windows_mutex_name)
        if not handle:
            raise ctypes_module.WinError(ctypes_module.get_last_error())
        result = kernel32.WaitForSingleObject(handle, 0xFFFFFFFF)
        if result != 0:
            kernel32.CloseHandle(handle)
            raise ctypes_module.WinError(ctypes_module.get_last_error())
        return kernel32, handle

    def _acquire_process_lock(self) -> Any:
        """Acquire the shared lock file before one write or rollover."""
        if os.name == "nt":
            return self._acquire_windows_mutex()
        lock_file = open(self._process_lock_path, "r+b")
        lock_file.seek(0)
        fcntl_module = __import__("fcntl")  # Load the POSIX lock API without Windows stub errors.
        fcntl_module.flock(lock_file.fileno(), fcntl_module.LOCK_EX)
        return lock_file

    def _release_process_lock(self, lock_file: Any) -> None:
        """Release the shared lock file after one write or rollover."""
        if os.name == "nt":
            kernel32, handle = lock_file
            kernel32.ReleaseMutex(handle)
            kernel32.CloseHandle(handle)
            return
        fcntl_module = __import__("fcntl")  # Load the POSIX lock API without Windows stub errors.
        fcntl_module.flock(lock_file.fileno(), fcntl_module.LOCK_UN)
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

    def _close_windows_stream(self) -> None:
        """Close the Windows stream so another process can rename the active file."""
        if os.name == "nt" and self.stream is not None:
            self.stream.flush()
            self.stream.close()
            self.stream = None

    def emit(self, record: logging.LogRecord) -> None:
        """Serialize one complete record and any required rollover."""
        lock_file = self._acquire_process_lock()
        try:
            self._reopen_if_rotated()
            super().emit(record)
        finally:
            self._close_windows_stream()
            self._release_process_lock(lock_file)
