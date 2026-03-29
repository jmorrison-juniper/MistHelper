"""Unit tests for TelemetryEmitter class.

Duplicates TelemetryEmitter from MistHelper.py to avoid import side effects
(research.md R1 pattern). Validates NDJSON output, retention, and event schemas.
"""

import glob
import json
import os
from datetime import UTC, datetime


# ---------------------------------------------------------------------------
# Duplicated class (R1: avoid MistHelper.py import side effects)
# ---------------------------------------------------------------------------
class TelemetryEmitter:
    """Append-only NDJSON event writer (duplicated for offline testing)."""

    RETENTION_LIMIT = 10

    def __init__(self, file_path: str):
        self._path = file_path
        self._handle = None
        try:
            parent = os.path.dirname(file_path)
            if parent:
                os.makedirs(parent, exist_ok=True)
            self._handle = open(file_path, "a", encoding="utf-8")
        except OSError:
            pass

    def emit(self, event: dict) -> None:
        if self._handle is None:
            return
        try:
            self._handle.write(json.dumps(event, default=str) + "\n")
            self._handle.flush()
        except OSError:
            pass

    def close(self) -> None:
        if self._handle is not None:
            try:
                self._handle.close()
            except OSError:
                pass
            self._handle = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def emit_test_start(self, menu_option, operation_name, test_mode):
        self.emit(
            {
                "event_type": "test_start",
                "timestamp": datetime.now(UTC).isoformat(),
                "menu_option": str(menu_option),
                "operation_name": operation_name,
                "test_mode": test_mode,
            }
        )

    def emit_test_pass(self, menu_option, operation_name, duration, test_mode):
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

    def emit_test_fail(self, menu_option, operation_name, duration, error, test_mode):
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

    def emit_test_skip(self, menu_option, operation_name, reason, category, test_mode):
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

    def emit_test_summary(self, total, passed, failed, skipped, elapsed, test_mode):
        overall = "pass" if failed == 0 else "fail"
        self.emit(
            {
                "event_type": "test_summary",
                "timestamp": datetime.now(UTC).isoformat(),
                "menu_option": "0",
                "status": overall,
                "total_operations": total,
                "pass_count": passed,
                "fail_count": failed,
                "skip_count": skipped,
                "total_elapsed_seconds": round(elapsed, 3),
                "test_mode": test_mode,
            }
        )

    def emit_progress_start(self, menu_option, operation_name, total_items):
        self.emit(
            {
                "event_type": "progress_start",
                "timestamp": datetime.now(UTC).isoformat(),
                "menu_option": str(menu_option),
                "operation_name": operation_name,
                "total_items": total_items,
            }
        )

    def emit_progress_tick(self, menu_option, operation_name, total, current, completed, remaining):
        self.emit(
            {
                "event_type": "progress_tick",
                "timestamp": datetime.now(UTC).isoformat(),
                "menu_option": str(menu_option),
                "operation_name": operation_name,
                "total_items": total,
                "current_item": str(current),
                "items_completed": completed,
                "items_remaining": remaining,
            }
        )

    def emit_progress_complete(self, menu_option, operation_name, total, processed, was_stopped, duration):
        self.emit(
            {
                "event_type": "progress_complete",
                "timestamp": datetime.now(UTC).isoformat(),
                "menu_option": str(menu_option),
                "operation_name": operation_name,
                "total_items": total,
                "items_processed": processed,
                "was_stopped": was_stopped,
                "duration_seconds": round(duration, 3),
            }
        )

    def enforce_retention(self, directory: str = "data", prefix: str = "test_events_", limit: int = None):
        if limit is None:
            limit = self.RETENTION_LIMIT
        try:
            pattern = os.path.join(directory, f"{prefix}*.jsonl")
            files = sorted(glob.glob(pattern))
            while len(files) > limit:
                oldest = files.pop(0)
                os.remove(oldest)
        except OSError:
            pass

    @staticmethod
    def timestamped_path(directory: str = "data") -> str:
        stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        return os.path.join(directory, f"test_events_{stamp}.jsonl")


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def read_events(path: str) -> list:
    """Read all NDJSON events from a file."""
    events = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                events.append(json.loads(line))
    return events


# ---------------------------------------------------------------------------
# Tests: basic emit + context manager
# ---------------------------------------------------------------------------
class TestTelemetryEmitterBasic:
    """Tests for core TelemetryEmitter functionality."""

    def test_emit_writes_valid_json_line(self, tmp_path):
        path = str(tmp_path / "events.jsonl")
        with TelemetryEmitter(path) as emitter:
            emitter.emit({"event_type": "test", "value": 42})
        events = read_events(path)
        assert len(events) == 1
        assert events[0]["event_type"] == "test"
        assert events[0]["value"] == 42

    def test_multiple_emits(self, tmp_path):
        path = str(tmp_path / "events.jsonl")
        with TelemetryEmitter(path) as emitter:
            for i in range(5):
                emitter.emit({"index": i})
        events = read_events(path)
        assert len(events) == 5

    def test_context_manager_closes_file(self, tmp_path):
        path = str(tmp_path / "events.jsonl")
        emitter = TelemetryEmitter(path)
        emitter.__enter__()
        emitter.emit({"a": 1})
        emitter.__exit__(None, None, None)
        assert emitter._handle is None

    def test_emit_after_close_is_noop(self, tmp_path):
        path = str(tmp_path / "events.jsonl")
        emitter = TelemetryEmitter(path)
        emitter.emit({"a": 1})
        emitter.close()
        emitter.emit({"b": 2})
        events = read_events(path)
        assert len(events) == 1

    def test_invalid_path_does_not_raise(self):
        """Best-effort: invalid path should not crash."""
        emitter = TelemetryEmitter("/nonexistent/dir/file.jsonl")
        emitter.emit({"a": 1})
        emitter.close()


# ---------------------------------------------------------------------------
# Tests: test event helpers
# ---------------------------------------------------------------------------
class TestTelemetryEmitterTestEvents:
    """Tests for test event helper methods."""

    def test_emit_test_start_schema(self, tmp_path):
        path = str(tmp_path / "events.jsonl")
        with TelemetryEmitter(path) as emitter:
            emitter.emit_test_start("11", "List Sites", "systematic")
        event = read_events(path)[0]
        assert event["event_type"] == "test_start"
        assert event["menu_option"] == "11"
        assert event["test_mode"] == "systematic"
        assert "timestamp" in event

    def test_emit_test_pass_schema(self, tmp_path):
        path = str(tmp_path / "events.jsonl")
        with TelemetryEmitter(path) as emitter:
            emitter.emit_test_pass("11", "List Sites", 3.456, "systematic")
        event = read_events(path)[0]
        assert event["event_type"] == "test_pass"
        assert event["status"] == "pass"
        assert event["duration_seconds"] == 3.456

    def test_emit_test_fail_schema(self, tmp_path):
        path = str(tmp_path / "events.jsonl")
        with TelemetryEmitter(path) as emitter:
            emitter.emit_test_fail("11", "List Sites", 1.0, ValueError("oops"), "systematic")
        event = read_events(path)[0]
        assert event["event_type"] == "test_fail"
        assert event["status"] == "fail"
        assert event["error_type"] == "ValueError"
        assert event["error_message"] == "oops"

    def test_emit_test_skip_schema(self, tmp_path):
        path = str(tmp_path / "events.jsonl")
        with TelemetryEmitter(path) as emitter:
            emitter.emit_test_skip("90", "Firmware", "DESTRUCTIVE", "destructive", "systematic")
        event = read_events(path)[0]
        assert event["event_type"] == "test_skip"
        assert event["status"] == "skip"
        assert event["skip_reason"] == "DESTRUCTIVE"
        assert event["skip_category"] == "destructive"

    def test_emit_test_summary_pass(self, tmp_path):
        path = str(tmp_path / "events.jsonl")
        with TelemetryEmitter(path) as emitter:
            emitter.emit_test_summary(100, 80, 0, 20, 120.5, "systematic")
        event = read_events(path)[0]
        assert event["event_type"] == "test_summary"
        assert event["status"] == "pass"
        assert event["total_operations"] == 100
        assert event["pass_count"] == 80
        assert event["fail_count"] == 0
        assert event["skip_count"] == 20

    def test_emit_test_summary_fail(self, tmp_path):
        path = str(tmp_path / "events.jsonl")
        with TelemetryEmitter(path) as emitter:
            emitter.emit_test_summary(100, 70, 10, 20, 120.5, "systematic")
        event = read_events(path)[0]
        assert event["status"] == "fail"


# ---------------------------------------------------------------------------
# Tests: progress event helpers
# ---------------------------------------------------------------------------
class TestTelemetryEmitterProgressEvents:
    """Tests for progress event helper methods."""

    def test_emit_progress_start(self, tmp_path):
        path = str(tmp_path / "events.jsonl")
        with TelemetryEmitter(path) as emitter:
            emitter.emit_progress_start("11", "List Sites", 50)
        event = read_events(path)[0]
        assert event["event_type"] == "progress_start"
        assert event["total_items"] == 50

    def test_emit_progress_tick(self, tmp_path):
        path = str(tmp_path / "events.jsonl")
        with TelemetryEmitter(path) as emitter:
            emitter.emit_progress_tick("11", "List Sites", 50, "site_abc", 10, 40)
        event = read_events(path)[0]
        assert event["event_type"] == "progress_tick"
        assert event["items_completed"] == 10
        assert event["items_remaining"] == 40

    def test_emit_progress_complete(self, tmp_path):
        path = str(tmp_path / "events.jsonl")
        with TelemetryEmitter(path) as emitter:
            emitter.emit_progress_complete("11", "List Sites", 50, 50, False, 30.5)
        event = read_events(path)[0]
        assert event["event_type"] == "progress_complete"
        assert event["items_processed"] == 50
        assert event["was_stopped"] is False

    def test_full_progress_lifecycle(self, tmp_path):
        path = str(tmp_path / "events.jsonl")
        with TelemetryEmitter(path) as emitter:
            emitter.emit_progress_start("11", "List Sites", 3)
            for i in range(3):
                emitter.emit_progress_tick("11", "List Sites", 3, f"site_{i}", i + 1, 2 - i)
            emitter.emit_progress_complete("11", "List Sites", 3, 3, False, 5.0)
        events = read_events(path)
        assert len(events) == 5
        assert events[0]["event_type"] == "progress_start"
        assert events[-1]["event_type"] == "progress_complete"


# ---------------------------------------------------------------------------
# Tests: retention
# ---------------------------------------------------------------------------
class TestTelemetryEmitterRetention:
    """Tests for enforce_retention file cleanup."""

    def test_enforce_retention_keeps_limit(self, tmp_path):
        data_dir = str(tmp_path / "data")
        os.makedirs(data_dir)
        for i in range(15):
            with open(os.path.join(data_dir, f"test_events_{i:04d}.jsonl"), "w") as handle:
                handle.write("{}\n")
        emitter = TelemetryEmitter(os.path.join(data_dir, "current.jsonl"))
        emitter.enforce_retention(directory=data_dir, limit=10)
        emitter.close()
        remaining = glob.glob(os.path.join(data_dir, "test_events_*.jsonl"))
        assert len(remaining) == 10

    def test_enforce_retention_no_files(self, tmp_path):
        """No crash when directory has no matching files."""
        data_dir = str(tmp_path / "data")
        os.makedirs(data_dir)
        emitter = TelemetryEmitter(os.path.join(data_dir, "current.jsonl"))
        emitter.enforce_retention(directory=data_dir, limit=10)
        emitter.close()

    def test_enforce_retention_under_limit(self, tmp_path):
        """Files under limit should not be deleted."""
        data_dir = str(tmp_path / "data")
        os.makedirs(data_dir)
        for i in range(3):
            with open(os.path.join(data_dir, f"test_events_{i:04d}.jsonl"), "w") as handle:
                handle.write("{}\n")
        emitter = TelemetryEmitter(os.path.join(data_dir, "current.jsonl"))
        emitter.enforce_retention(directory=data_dir, limit=10)
        emitter.close()
        remaining = glob.glob(os.path.join(data_dir, "test_events_*.jsonl"))
        assert len(remaining) == 3


# ---------------------------------------------------------------------------
# Tests: timestamped_path
# ---------------------------------------------------------------------------
class TestTimestampedPath:
    """Tests for static timestamped_path method."""

    def test_format(self):
        path = TelemetryEmitter.timestamped_path("data")
        assert path.startswith("data")
        assert "test_events_" in path
        assert path.endswith(".jsonl")

    def test_custom_directory(self):
        path = TelemetryEmitter.timestamped_path("output")
        assert path.startswith("output")
