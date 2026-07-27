"""TelemetryEmitter -- append-only NDJSON event writer.

Extracted from MistHelper.py during initiative 1013 (Cat B, position 9).
Writes one JSON object per line to the target file for test and progress
telemetry. All writes are best-effort: an I/O failure is logged but never
interrupts the primary operation (FR-008).
"""

from __future__ import annotations  # WHY: enable PEP 604 unions on Python 3.9+.

import glob  # WHY: retention pruning of oldest timestamped JSONL files.
import json  # WHY: NDJSON serialization for every emitted event.
import logging  # WHY: emit structured trace on write / open failures.
import os  # WHY: cross-platform parent-dir creation + retention file removal.
from datetime import UTC, datetime  # WHY: ISO-8601 UTC timestamps on every event.

from src.dataclasses.progress_event import (
    ProgressContext,  # Bundled progress identity (issue #470).
    TestSummary,  # Bundled test-summary counters (issue #470).
)


class TelemetryEmitter:
    """Append-only NDJSON event writer for test and progress telemetry.

    Writes one JSON object per line to the target file.  All writes are
    best-effort: an I/O failure is logged but never interrupts the
    primary operation (FR-008).

    Usage::

        with TelemetryEmitter("data/test_events.jsonl") as emitter:
            emitter.emit({"event_type": "test_pass", ...})
    """

    RETENTION_LIMIT = 10

    def __init__(self, file_path: str):
        """Open *file_path* for append-only NDJSON writes.

        Why:
            Parent directories are created eagerly so callers can pass a fresh
            path (for example ``data/telemetry/2026-07-21.jsonl``) without a separate
            ``os.makedirs`` step. Open failures downgrade to a warning and leave
            ``self._handle = None`` so subsequent ``emit()`` calls become no-ops
            (FR-008: telemetry must never interrupt the primary operation).

        Args:
            file_path: Filesystem path to the NDJSON target file.
        """
        self._path = file_path
        self._handle = None
        try:
            parent = os.path.dirname(file_path)
            if parent:
                os.makedirs(parent, exist_ok=True)
            self._handle = open(file_path, "a", encoding="utf-8")  # noqa: SIM115  # long-lived append handle
        except OSError as exc:
            logging.warning("TelemetryEmitter: cannot open %s: %s", file_path, exc)

    # -- core write ----------------------------------------------------------

    def emit(self, event: dict) -> None:  # type: ignore[type-arg]
        """Write *event* as a single JSON line (best-effort)."""
        if self._handle is None:
            return
        try:
            self._handle.write(json.dumps(event, default=str) + "\n")
            self._handle.flush()
        except OSError as exc:
            logging.warning("TelemetryEmitter: write failed: %s", exc)

    def close(self) -> None:
        """Flush and close the underlying file handle."""
        if self._handle is not None:
            try:
                self._handle.close()
            except OSError:
                pass
            self._handle = None

    # -- context manager -----------------------------------------------------

    def __enter__(self) -> TelemetryEmitter:
        """Return self so the emitter can be used as a context manager.

        Why:
            The file handle is already opened in ``__init__``; ``__enter__``
            exists purely to enable ``with TelemetryEmitter(...) as e:`` syntax
            and pair with ``__exit__`` for guaranteed close-on-scope-exit.

        Returns:
            The same TelemetryEmitter instance.
        """
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: object) -> None:
        """Close the underlying file handle on scope exit.

        Why:
            Ensures the append handle is flushed and released even if the
            ``with`` block raises. Exception details are intentionally
            discarded — telemetry never suppresses exceptions from the caller.

        Args:
            exc_type: Exception type if the ``with`` block raised, else None.
            exc_val: Exception instance if the ``with`` block raised, else None.
            exc_tb: Traceback if the ``with`` block raised, else None.
        """
        del exc_type, exc_val, exc_tb  # WHY: protocol params unused. Silence vulture without renaming public signature.
        self.close()

    # -- test event helpers ---------------------------------------------------

    def emit_test_start(self, menu_option: str | int, operation_name: str, test_mode: str) -> None:
        """Emit a test_start event."""
        self.emit(
            {
                "event_type": "test_start",
                "timestamp": datetime.now(UTC).isoformat(),
                "menu_option": str(menu_option),
                "operation_name": operation_name,
                "test_mode": test_mode,
            }
        )

    def emit_test_pass(self, menu_option: str | int, operation_name: str, duration: float, test_mode: str) -> None:
        """Emit a test_pass event."""
        self.emit(
            {
                "event_type": "test_pass",
                "timestamp": datetime.now(UTC).isoformat(),
                "menu_option": str(menu_option),
                "status": "pass",
                "operation_name": operation_name,
                "duration_seconds": round(duration, 3),
                "test_mode": test_mode,
            }
        )

    def emit_test_fail(
        self, menu_option: str | int, operation_name: str, duration: float, error: Exception, test_mode: str
    ) -> None:
        """Emit a test_fail event."""
        self.emit(
            {
                "event_type": "test_fail",
                "timestamp": datetime.now(UTC).isoformat(),
                "menu_option": str(menu_option),
                "status": "fail",
                "operation_name": operation_name,
                "duration_seconds": round(duration, 3),
                "error_type": type(error).__name__,
                "error_message": str(error)[:500],
                "test_mode": test_mode,
            }
        )

    def emit_test_skip(
        self, menu_option: str | int, operation_name: str, reason: str, category: str, test_mode: str
    ) -> None:
        """Emit a test_skip event."""
        self.emit(
            {
                "event_type": "test_skip",
                "timestamp": datetime.now(UTC).isoformat(),
                "menu_option": str(menu_option),
                "status": "skip",
                "operation_name": operation_name,
                "duration_seconds": 0.0,
                "skip_reason": reason,
                "skip_category": category,
                "test_mode": test_mode,
            }
        )

    def emit_test_summary(self, summary: TestSummary) -> None:
        """Emit a test_summary event from a bundled TestSummary (issue #470: was 6 positional params)."""
        overall = "pass" if summary.failed == 0 else "fail"  # Overall verdict is pass only when nothing failed.
        self.emit(
            {
                "event_type": "test_summary",
                "timestamp": datetime.now(UTC).isoformat(),
                "menu_option": "0",
                "status": overall,
                "total_operations": summary.total,  # Total operations exercised (issue #470: from dataclass).
                "pass_count": summary.passed,  # Passed count (issue #470: from dataclass).
                "fail_count": summary.failed,  # Failed count (issue #470: from dataclass).
                "skip_count": summary.skipped,  # Skipped count (issue #470: from dataclass).
                "total_elapsed_seconds": round(summary.elapsed, 3),  # Elapsed wall-clock seconds (issue #470).
                "test_mode": summary.test_mode,  # Test mode label (issue #470: from dataclass).
            }
        )

    # -- progress event helpers -----------------------------------------------

    def emit_progress_start(self, menu_option: str | int, operation_name: str, total_items: int) -> None:
        """Emit a progress_start event."""
        self.emit(
            {
                "event_type": "progress_start",
                "timestamp": datetime.now(UTC).isoformat(),
                "menu_option": str(menu_option),
                "operation_name": operation_name,
                "total_items": total_items,
            }
        )

    def emit_progress_tick(self, ctx: ProgressContext, current: object, completed: int, remaining: int) -> None:
        """Emit a progress_tick event from a ProgressContext (issue #470: identity bundled into ctx)."""
        self.emit(
            {
                "event_type": "progress_tick",
                "timestamp": datetime.now(UTC).isoformat(),
                "menu_option": str(ctx.menu_option),  # Menu option from the bundled context (issue #470).
                "operation_name": ctx.operation_name,  # Operation label from the bundled context (issue #470).
                "total_items": ctx.total,  # Total item count from the bundled context (issue #470).
                "current_item": str(current),  # The item currently being processed.
                "items_completed": completed,  # Count of items finished so far.
                "items_remaining": remaining,  # Count of items still pending.
            }
        )

    def emit_progress_complete(
        self,
        ctx: ProgressContext,
        processed: int,
        was_stopped: bool,
        duration: float,
    ) -> None:
        """Emit a progress_complete event from a ProgressContext (issue #470: identity bundled into ctx)."""
        self.emit(
            {
                "event_type": "progress_complete",
                "timestamp": datetime.now(UTC).isoformat(),
                "menu_option": str(ctx.menu_option),  # Menu option from the bundled context (issue #470).
                "operation_name": ctx.operation_name,  # Operation label from the bundled context (issue #470).
                "total_items": ctx.total,  # Total item count from the bundled context (issue #470).
                "items_processed": processed,  # Count of items actually processed before completion.
                "was_stopped": was_stopped,  # True when the operation was interrupted by the user.
                "duration_seconds": round(duration, 3),  # Wall-clock seconds the operation took.
            }
        )

    # -- retention ------------------------------------------------------------

    def enforce_retention(
        self, directory: str = "data", prefix: str = "test_events_", limit: int | None = None
    ) -> None:
        """Delete oldest timestamped JSONL files when count exceeds *limit*."""
        if limit is None:
            limit = self.RETENTION_LIMIT
        try:
            pattern = os.path.join(directory, f"{prefix}*.jsonl")
            files = sorted(glob.glob(pattern))
            while len(files) > limit:
                oldest = files.pop(0)
                os.remove(oldest)
                logging.info("TelemetryEmitter: removed old file %s", oldest)
        except OSError as exc:
            logging.warning("TelemetryEmitter: retention cleanup failed: %s", exc)

    # -- timestamped filename helper -----------------------------------------

    @staticmethod
    def timestamped_path(directory: str = "data") -> str:
        """Return a timestamped JSONL path for a test run."""
        stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        return os.path.join(directory, f"test_events_{stamp}.jsonl")
