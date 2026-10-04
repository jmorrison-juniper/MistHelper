"""Test concurrent writes and rollover for the shared application log."""

from __future__ import annotations

import logging
import multiprocessing
import os
from pathlib import Path
from typing import Any

import pytest

from src.foundation.support.utils.process_safe_log_handler import (
    ProcessSafeRotatingFileHandler,
)  # Import the handler from its canonical moved module.


def _write_concurrent_records(log_path: str, barrier: Any, worker_id: int) -> None:
    """Write records from one process so the test exercises the real process boundary."""
    handler = ProcessSafeRotatingFileHandler(log_path, max_bytes=65536, backup_count=10)
    logger = logging.getLogger(f"concurrent-log-worker-{worker_id}")
    logger.handlers = [handler]
    logger.setLevel(logging.INFO)
    logger.propagate = False
    barrier.wait()
    for index in range(10_000):
        logger.info("worker=%d record=%d", worker_id, index)
    handler.close()


class TestProcessSafeRotatingFileHandler:
    """Verify safe writes and rollover across independent processes."""

    def test_handler_uses_bounded_rotation(self, tmp_path: Path) -> None:
        """The handler keeps the configured size and backup limits."""
        log_path = tmp_path / "script.log"
        handler = ProcessSafeRotatingFileHandler(str(log_path), max_bytes=128, backup_count=2)

        assert handler.maxBytes == 128
        assert handler.backupCount == 2
        assert handler.baseFilename.endswith("script.log")
        handler.close()

    @pytest.mark.skipif(
        os.name == "nt",
        reason="The 10000-record rollover proof requires the Linux container lock path.",
    )
    def test_concurrent_processes_preserve_complete_lines_during_rollover(self, tmp_path: Path) -> None:
        """Two processes keep every complete record while one file rolls over."""
        log_path = tmp_path / "script.log"
        context = multiprocessing.get_context("spawn")
        barrier = context.Barrier(2)
        processes = [
            context.Process(target=_write_concurrent_records, args=(str(log_path), barrier, worker_id))
            for worker_id in range(2)
        ]

        for process in processes:
            process.start()
        for process in processes:
            process.join(timeout=30)
            assert process.exitcode == 0

        records: list[str] = []
        for candidate in tmp_path.glob("script.log*"):
            if candidate.suffix == ".lock":
                continue
            records.extend(candidate.read_text(encoding="utf-8").splitlines())

        expected = {f"worker={worker_id} record={index}" for worker_id in range(2) for index in range(10_000)}
        assert set(records) == expected
        assert len(records) == len(expected)
