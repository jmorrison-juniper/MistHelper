"""Operation execution service for the MistHelper web portal.

Dispatches menu operations in background threads, tracks run state,
captures log output, and publishes SSE events via PortalEventBus.
"""

import io
import logging
import sys
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Optional


CATEGORY_RANGES = [
    (1, 4, "Core Organization"),
    (5, 8, "WebSocket Device Commands"),
    (9, 10, "Packet Captures"),
    (11, 19, "Organization Exports"),
    (20, 28, "Location Exports"),
    (29, 34, "Site Data Exports"),
    (35, 39, "Template Exports"),
    (40, 41, "Statistics & Analytics"),
    (42, 48, "Security & Configuration"),
    (49, 62, "Site Config & Monitoring"),
    (63, 65, "Work In Progress"),
    (66, 89, "Insights & Diagnostics"),
]

DESTRUCTIVE_THRESHOLD = 90


class OperationExecutor:
    """Execute MistHelper menu operations in background threads.

    Tracks OperationRun state, captures stdout/log output,
    and publishes real-time SSE events via the event bus.
    """

    def __init__(
        self,
        menu_actions: dict,
        apisession: Optional[Any],
        org_id: Optional[str],
        event_bus: Optional[Any],
    ):
        """Initialize with shared MistHelper dependencies."""
        self._menu_actions = menu_actions
        self._apisession = apisession
        self._org_id = org_id
        self._event_bus = event_bus
        self._runs = {}
        self._lock = threading.Lock()
        self._pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="op")

    def start_operation(self, menu_number: str, parameters: dict) -> dict:
        """Validate and start an operation in a background thread."""
        error = self._validate_operation(menu_number)
        if error:
            return error
        conflict = self._check_conflict(menu_number)
        if conflict:
            return conflict
        run = self._create_run(menu_number)
        self._pool.submit(self._execute_operation, run, parameters)
        return self._run_to_dict(run)

    def get_run_status(self, run_id: str) -> Optional[dict]:
        """Return current status of a specific operation run."""
        with self._lock:
            run = self._runs.get(run_id)
        if run is None:
            return None
        return self._run_to_dict(run)

    def get_active_runs(self) -> list:
        """Return list of currently running operations."""
        with self._lock:
            return [
                self._run_to_summary(run)
                for run in self._runs.values()
                if run["status"] in ("pending", "running")
            ]

    def build_category_list(self, menu_actions: dict) -> list:
        """Build categorized operation list for the UI."""
        categories = {}
        for key, value in menu_actions.items():
            num = self._parse_menu_number(key)
            if num is None or num >= DESTRUCTIVE_THRESHOLD:
                continue
            category = self._get_category(num)
            desc = value[1] if isinstance(value, tuple) and len(value) > 1 else str(value)
            if category not in categories:
                categories[category] = []
            categories[category].append({
                "menu_number": key,
                "description": desc,
            })
        return [
            {"name": name, "operations": ops}
            for name, ops in sorted(categories.items(), key=lambda x: x[0])
        ]

    def get_operation_parameters(self, menu_number: str) -> Optional[dict]:
        """Return parameter requirements for an operation."""
        if menu_number not in self._menu_actions:
            return None
        value = self._menu_actions[menu_number]
        desc = value[1] if isinstance(value, tuple) and len(value) > 1 else str(value)
        return {
            "menu_number": menu_number,
            "description": desc,
            "parameters": [],
        }

    def _validate_operation(self, menu_number: str) -> Optional[dict]:
        """Check if the operation is valid and non-destructive."""
        if menu_number not in self._menu_actions:
            return {"error": f"Operation {menu_number} not found"}
        num = self._parse_menu_number(menu_number)
        if num is not None and num >= DESTRUCTIVE_THRESHOLD:
            return {"error": f"Menu number {menu_number} is a destructive operation and cannot be run from the portal"}
        value = self._menu_actions[menu_number]
        func = value[0] if isinstance(value, tuple) else value
        if func is None:
            return {"error": "API not authenticated. Connect via SSH to run operations."}
        return None

    def _check_conflict(self, menu_number: str) -> Optional[dict]:
        """Check if the same operation is already running."""
        with self._lock:
            for run in self._runs.values():
                if run["menu_number"] == menu_number and run["status"] in ("pending", "running"):
                    return {
                        "error": f"Operation {menu_number} is already running",
                        "run_id": run["run_id"],
                    }
        return None

    def _create_run(self, menu_number: str) -> dict:
        """Create a new OperationRun record."""
        value = self._menu_actions[menu_number]
        desc = value[1] if isinstance(value, tuple) and len(value) > 1 else str(value)
        run = {
            "run_id": str(uuid.uuid4()),
            "menu_number": menu_number,
            "description": desc,
            "status": "pending",
            "started_at": time.time(),
            "completed_at": None,
            "progress_pct": 0,
            "log_messages": [],
            "error_message": None,
            "output_files": [],
        }
        with self._lock:
            self._runs[run["run_id"]] = run
        return run

    def _execute_operation(self, run: dict, parameters: dict) -> None:
        """Execute the operation function in a background thread."""
        self._update_status(run, "running", 0)
        try:
            func = self._menu_actions[run["menu_number"]][0]
            self._capture_and_run(run, func)
            self._update_status(run, "completed", 100)
            self._publish_complete(run)
        except (EOFError, SystemExit):
            self._handle_failure(run, "Operation requires interactive input (not available in web portal)")
        except Exception as exc:
            self._handle_failure(run, str(exc))

    def _capture_and_run(self, run: dict, func) -> None:
        """Run function with stdout and log capture via handlers."""
        handler = _RunLogHandler(run, self._event_bus)
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
        stdout_capture = _StdoutCapture(run, self._event_bus)
        old_stdout = sys.stdout
        sys.stdout = stdout_capture
        try:
            func()
        finally:
            sys.stdout = old_stdout
            root_logger.removeHandler(handler)

    def _update_status(self, run: dict, status: str, progress: int) -> None:
        """Update run status and publish SSE event."""
        with self._lock:
            run["status"] = status
            run["progress_pct"] = progress
            if status in ("completed", "failed"):
                run["completed_at"] = time.time()
        if self._event_bus:
            self._event_bus.publish("status", {
                "run_id": run["run_id"],
                "status": status,
                "progress_pct": progress,
                "menu_number": run["menu_number"],
                "description": run["description"],
            })

    def _publish_complete(self, run: dict) -> None:
        """Publish completion SSE event."""
        if not self._event_bus:
            return
        duration = (run["completed_at"] or time.time()) - run["started_at"]
        self._event_bus.publish("complete", {
            "run_id": run["run_id"],
            "status": "completed",
            "output_files": run["output_files"],
            "duration_seconds": round(duration, 1),
        })

    def _handle_failure(self, run: dict, message: str) -> None:
        """Update run to failed state and publish error event."""
        with self._lock:
            run["status"] = "failed"
            run["error_message"] = message
            run["completed_at"] = time.time()
        if self._event_bus:
            duration = run["completed_at"] - run["started_at"]
            self._event_bus.publish("error", {
                "run_id": run["run_id"],
                "status": "failed",
                "error_message": message,
                "duration_seconds": round(duration, 1),
            })

    def _run_to_dict(self, run: dict) -> dict:
        """Convert run record to API response format."""
        return {
            "run_id": run["run_id"],
            "menu_number": run["menu_number"],
            "description": run["description"],
            "status": run["status"],
            "started_at": run["started_at"],
            "completed_at": run["completed_at"],
            "progress_pct": run["progress_pct"],
            "error_message": run["error_message"],
            "output_files": run["output_files"],
        }

    def _run_to_summary(self, run: dict) -> dict:
        """Convert run to abbreviated summary for active list."""
        return {
            "run_id": run["run_id"],
            "menu_number": run["menu_number"],
            "description": run["description"],
            "status": run["status"],
            "progress_pct": run["progress_pct"],
        }

    def _parse_menu_number(self, key: str) -> Optional[int]:
        """Parse string menu key to integer, return None if non-numeric."""
        try:
            return int(key)
        except (ValueError, TypeError):
            return None

    def _get_category(self, num: int) -> str:
        """Map a menu number to its category name."""
        for low, high, name in CATEGORY_RANGES:
            if low <= num <= high:
                return name
        return "Other"


class _StdoutCapture(io.TextIOBase):
    """Capture print() output and publish via SSE."""

    def __init__(self, run: dict, event_bus):
        """Initialize with the run record and event bus."""
        super().__init__()
        self._run = run
        self._event_bus = event_bus
        self._buffer = ""

    def write(self, text: str) -> int:
        """Capture written text, publish complete lines via SSE."""
        if not text:
            return 0
        self._buffer += text
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            line = line.rstrip()
            if line:
                self._publish_line(line)
        return len(text)

    def flush(self) -> None:
        """Flush remaining buffer content."""
        if self._buffer.strip():
            self._publish_line(self._buffer.strip())
            self._buffer = ""

    def _publish_line(self, message: str) -> None:
        """Append line to run log and publish as SSE event."""
        self._run["log_messages"].append(message)
        if self._event_bus:
            self._event_bus.publish("log", {
                "run_id": self._run["run_id"],
                "message": message,
                "level": "info",
                "timestamp": time.strftime(
                    "%Y-%m-%dT%H:%M:%SZ", time.gmtime()
                ),
            })


class _RunLogHandler(logging.Handler):
    """Logging handler that captures log lines to an OperationRun."""

    def __init__(self, run: dict, event_bus):
        """Initialize with the run record and event bus."""
        super().__init__()
        self._run = run
        self._event_bus = event_bus

    def emit(self, record: logging.LogRecord) -> None:
        """Capture a log record and publish as SSE log event."""
        message = self.format(record)
        self._run["log_messages"].append(message)
        if self._event_bus:
            self._event_bus.publish("log", {
                "run_id": self._run["run_id"],
                "message": message,
                "level": record.levelname.lower(),
                "timestamp": time.strftime(
                    "%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created)
                ),
            })
