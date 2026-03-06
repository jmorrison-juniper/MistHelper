"""Operation execution service for the MistHelper web portal.

Dispatches menu operations in background threads, tracks run state,
captures log output, and publishes SSE events via PortalEventBus.
"""

import logging
import os
import re
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

# --- Parameter Definitions -------------------------------------------------
# Each entry maps a menu number to its category and ordered parameter list.
# param_type: site, device, client, choice, text, number
# depends_on: name of parameter this depends on (for cascading dropdowns)
# device_filter: ap, switch, gateway, all (only for param_type=device)

PARAMETER_REGISTRY = {}


def _site_param(required: bool = True) -> dict:
    """Build a site-type parameter definition."""
    return {
        "name": "site_id",
        "label": "Site",
        "param_type": "site",
        "required": required,
    }


def _device_param(device_filter: str = "all") -> dict:
    """Build a device-type parameter definition."""
    return {
        "name": "device_id",
        "label": "Device",
        "param_type": "device",
        "required": True,
        "depends_on": "site_id",
        "device_filter": device_filter,
    }


def _text_param(name: str, label: str, **kwargs) -> dict:
    """Build a text-type parameter definition."""
    param = {"name": name, "label": label, "param_type": "text", "required": False}
    param.update(kwargs)
    return param


def _number_param(name: str, label: str, **kwargs) -> dict:
    """Build a number-type parameter definition."""
    param = {"name": name, "label": label, "param_type": "number", "required": False}
    param.update(kwargs)
    return param


def _choice_param(name: str, label: str, options: list, **kwargs) -> dict:
    """Build a choice-type parameter definition."""
    param = {
        "name": name,
        "label": label,
        "param_type": "choice",
        "required": True,
        "options": options,
    }
    param.update(kwargs)
    return param


def _build_registry() -> dict:
    """Build the full PARAMETER_REGISTRY mapping."""
    registry = {}

    # --- Simple site-only operations (1 prompt: site) ---
    site_only_menus = [
        "29", "30", "31", "32", "34", "49", "50",
        "51", "52", "53", "68", "70", "71", "84",
    ]
    for menu in site_only_menus:
        registry[menu] = {
            "category": "interactive",
            "parameters": [_site_param()],
        }

    # --- Site + device (all types) ---
    site_device_all_menus = ["72", "74", "80", "81", "85"]
    for menu in site_device_all_menus:
        registry[menu] = {
            "category": "interactive",
            "parameters": [_site_param(), _device_param("all")],
        }

    # --- Site + switch ---
    for menu in ["5", "33"]:
        registry[menu] = {
            "category": "interactive",
            "parameters": [_site_param(), _device_param("switch")],
        }

    # --- Site + gateway ---
    registry["73"] = {
        "category": "interactive",
        "parameters": [_site_param(), _device_param("gateway")],
    }

    # --- Forwarding table (menu 6): gateway + text fields ---
    registry["6"] = {
        "category": "interactive",
        "parameters": [
            _site_param(),
            _device_param("gateway"),
            _text_param("prefix", "IP Prefix", placeholder="0.0.0.0/0", default="0.0.0.0/0"),
            _text_param("service_name", "Service Name", placeholder="press Enter to skip"),
            _text_param("vrf", "VRF Name", placeholder="press Enter to skip"),
            _text_param("node", "Node", placeholder="node0/node1 for HA"),
        ],
    }

    # --- Routing table (menu 7): switch + text fields ---
    registry["7"] = {
        "category": "interactive",
        "parameters": [
            _site_param(),
            _device_param("switch"),
            _text_param("prefix", "Route Prefix", placeholder="press Enter to show all"),
            _text_param("protocol", "Protocol Filter", placeholder="press Enter for any"),
            _text_param("vrf", "VRF Name", placeholder="press Enter to skip"),
            _text_param("neighbor", "BGP Neighbor IP", placeholder="press Enter to skip"),
        ],
    }

    # --- SSR routes (menu 8): gateway + many params ---
    registry["8"] = {
        "category": "interactive",
        "parameters": [
            _site_param(),
            _device_param("gateway"),
            _text_param("protocol", "Protocol", placeholder="press Enter for API default"),
            _text_param("prefix", "Route Prefix", placeholder="e.g. 192.168.1.0/24"),
            _text_param("vrf", "VRF Name", placeholder="press Enter for default VRF"),
            _text_param("neighbor", "BGP Neighbor IP", placeholder="press Enter to skip"),
        ],
    }

    # --- Ping device (menu 87) ---
    registry["87"] = {
        "category": "interactive",
        "parameters": [
            _site_param(),
            _device_param("all"),
            _text_param("target_host", "Target Host/IP", default="8.8.8.8", placeholder="8.8.8.8"),
            _number_param("ping_count", "Ping Count", default="4", min_value=1, max_value=100),
        ],
    }

    # --- ARP device (menu 88) ---
    registry["88"] = {
        "category": "interactive",
        "parameters": [_site_param(), _device_param("all")],
    }

    # --- Client operations ---
    registry["69"] = {
        "category": "interactive",
        "parameters": [
            _site_param(),
            {"name": "client_mac", "label": "Client", "param_type": "client",
             "required": True, "depends_on": "site_id"},
        ],
    }
    registry["86"] = {
        "category": "interactive",
        "parameters": [
            _site_param(),
            {"name": "client_mac", "label": "Client", "param_type": "client",
             "required": True, "depends_on": "site_id"},
        ],
    }

    # --- Service ping (menu 89): gateway + many params ---
    registry["89"] = {
        "category": "interactive",
        "parameters": [
            _site_param(),
            _device_param("gateway"),
            _text_param("tenant", "Tenant", placeholder="select index or skip"),
            _text_param("service", "Service", placeholder="select index or enter custom"),
            _text_param("host", "Target Host/IP", default="8.8.8.8", placeholder="8.8.8.8"),
            _number_param("count", "Ping Count", default="4", min_value=1, max_value=100),
        ],
    }

    # --- Packet captures (complex interactive) ---
    registry["9"] = {
        "category": "interactive",
        "parameters": [
            _choice_param("capture_type", "Capture Type", [
                {"value": "1", "label": "Wireless Client"},
                {"value": "2", "label": "Wired Client"},
                {"value": "3", "label": "Gateway"},
                {"value": "4", "label": "Switch"},
                {"value": "5", "label": "New Association"},
                {"value": "6", "label": "Scan Radio"},
            ]),
            _site_param(),
            _text_param("client_mac", "Client MAC", placeholder="e.g. aa:bb:cc:dd:ee:ff"),
            _number_param("duration", "Duration (seconds)", default="60", min_value=10, max_value=300),
            _number_param("num_packets", "Packet Count", default="100", min_value=1, max_value=10000),
            _number_param("max_pkt_len", "Max Packet Length", default="128", min_value=64, max_value=1500),
        ],
    }

    registry["10"] = {
        "category": "interactive",
        "parameters": [
            _text_param("mxedge_index", "MxEdge Index", placeholder="select MxEdge index"),
            _text_param("port_index", "Port Index", placeholder="select port index"),
            _text_param("tcpdump_filter", "Tcpdump Filter", placeholder="press Enter for none"),
            _number_param("duration", "Duration (seconds)", default="30", min_value=1, max_value=86400),
            _number_param("num_packets", "Packet Count", default="1024", min_value=0, max_value=10000),
            _number_param("max_pkt_len", "Max Packet Length", default="128", min_value=1, max_value=2048),
        ],
    }

    # --- CLI-only operations ---
    registry["62"] = {
        "category": "cli_only",
        "parameters": [],
        "cli_only_message": (
            "Interactive troubleshooting requires multi-step keyboard input. "
            "Use SSH access on port 2200."
        ),
    }
    registry["79"] = {
        "category": "cli_only",
        "parameters": [],
        "cli_only_message": (
            "Interactive CLI shell requires persistent keyboard input. "
            "Use SSH access on port 2200."
        ),
    }

    return registry


PARAMETER_REGISTRY = _build_registry()


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
        cpu_count = os.cpu_count() or 2
        max_workers = max(1, cpu_count - 1)
        logging.info(
            "Operation pool: %d workers (CPUs detected: %d)", max_workers, cpu_count
        )
        self._pool = ThreadPoolExecutor(
            max_workers=max_workers, thread_name_prefix="op"
        )

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

    def stop_operation(self, run_id: str) -> dict:
        """Request graceful stop of a running operation.

        Creates the ``stop_loop.txt`` sentinel file that loop-style
        operations (Menu 75/76) check between iterations.  Also marks
        the run as ``failed`` so that ``_check_conflict`` no longer
        blocks a fresh start of the same menu number.

        Returns:
            Dict with status message or error.
        """
        with self._lock:
            run = self._runs.get(run_id)
        if run is None:
            return {"error": "Run not found"}
        if run["status"] not in ("pending", "running"):
            return {"error": "Operation is not running"}
        run["_stop_requested"] = True
        self._update_status(run, "failed", 100)
        run["error_message"] = "Stopped by user"
        try:
            stop_path = os.path.join(os.getcwd(), "stop_loop.txt")
            with open(stop_path, "w", encoding="utf-8") as fh:
                fh.write("stop requested by web portal\n")
            logging.info("Stop signal sent for run %s (stop_loop.txt created)", run_id)
        except OSError as exc:
            logging.warning("Could not create stop_loop.txt: %s", exc)
        return {"status": "stop_requested", "run_id": run_id}

    def build_category_list(self, menu_actions: dict) -> list:
        """Build categorized operation list for the UI."""
        categories = {}
        for key, value in menu_actions.items():
            num = self._parse_menu_number(key)
            if num is None or num >= DESTRUCTIVE_THRESHOLD:
                continue
            category = self._get_category(num)
            desc = value[1] if isinstance(value, tuple) and len(value) > 1 else str(value)
            reg_entry = PARAMETER_REGISTRY.get(key)
            op_category = reg_entry["category"] if reg_entry else "non_interactive"
            if category not in categories:
                categories[category] = []
            categories[category].append({
                "menu_number": key,
                "description": desc,
                "category": op_category,
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
        entry = PARAMETER_REGISTRY.get(menu_number)
        if entry is not None:
            result = {
                "menu_number": menu_number,
                "description": desc,
                "category": entry.get("category", "interactive"),
                "parameters": entry.get("parameters", []),
            }
            if "cli_only_message" in entry:
                result["cli_only_message"] = entry["cli_only_message"]
            return result
        return {
            "menu_number": menu_number,
            "description": desc,
            "category": "non_interactive",
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
            "debug_messages": [],
            "error_message": None,
            "output_files": [],
        }
        with self._lock:
            self._runs[run["run_id"]] = run
        return run

    def _execute_operation(self, run: dict, parameters: dict) -> None:
        """Execute the operation function in a background thread."""
        from web_portal.services.input_hook import web_input_context

        self._update_status(run, "running", 0)
        input_answers = parameters.get("input_answers", [])
        try:
            func = self._menu_actions[run["menu_number"]][0]
            if input_answers:
                with web_input_context(input_answers):
                    self._capture_and_run(run, func)
            else:
                self._capture_and_run(run, func)
            if not run.get("_stop_requested"):
                self._update_status(run, "completed", 100)
                self._publish_complete(run)
        except (EOFError, SystemExit):
            if not run.get("_stop_requested"):
                self._handle_failure(run, "Operation requires interactive input (not available in web portal)")
        except Exception as exc:
            if not run.get("_stop_requested"):
                self._handle_failure(run, str(exc))

    def _capture_and_run(self, run: dict, func) -> None:
        """Run function with log capture via a logging handler.

        Captures logging output from the operation function and publishes
        it via SSE. Print output goes to container stdout (not captured)
        since MistHelper logs all meaningful progress via logging.info().
        """
        handler = _RunLogHandler(run, self._event_bus)
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
        try:
            func()
        finally:
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
            "message": "Operation completed",
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
            self._event_bus.publish("error_event", {
                "run_id": run["run_id"],
                "status": "failed",
                "message": message,
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
            "log_messages": list(run.get("log_messages", [])),
            "debug_messages": list(run.get("debug_messages", [])),
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


class _RunLogHandler(logging.Handler):
    """Logging handler that captures log lines to an OperationRun.

    Routes log output into two tiers based on source and content:
    - Main log: user-facing progress messages (fetched N records, wrote file)
    - Debug log: library internals, rate limiter, API plumbing

    Also auto-detects output file paths from log messages so the
    Output Files section populates without changes to legacy menu code.
    """

    # Logger name prefixes whose output always goes to debug panel
    _DEBUG_LOGGERS = frozenset((
        "urllib3", "requests", "werkzeug", "flask", "mistapi",
    ))

    # Message prefixes that indicate internal plumbing (even at INFO)
    _INTERNAL_PREFIXES = (
        "apiresponse:", "apirequest:", "apitoken:",
        "Rate limiting:", "Hour boundary crossed",
        "Adaptive delay", "PID controller",
        "request headers:", "_gen_query:", "_check_next", "_url:",
        "Processing ", "Connection-aware threading:",
        "CPU-aware threading:", "Connection pool protection:",
        "API Optimization:", "Fast mode:",
        "Retry ", "FAST RETRY",
    )

    # Regex to extract output filenames from log messages
    _OUTPUT_FILE_RE = re.compile(
        r"(?:wrote \d+ rows to|written to|wrote results to)"
        r"\s+(?:data[/\\])?(\S+\.(?:csv|db|json|sqlite))",
        re.IGNORECASE,
    )

    def __init__(self, run: dict, event_bus):
        """Initialize with the run record and event bus."""
        super().__init__()
        self._run = run
        self._event_bus = event_bus

    def emit(self, record: logging.LogRecord) -> None:
        """Capture a log record and route to appropriate SSE channel."""
        message = self.format(record)
        level = record.levelname.lower()
        timestamp = time.strftime(
            "%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created)
        )
        is_main = self._is_user_facing(record, message)
        event_type = "log" if is_main else "debug_log"
        storage = "log_messages" if is_main else "debug_messages"
        self._run[storage].append({"message": message, "level": level})
        if is_main:
            self._check_output_file(message)
        if self._event_bus:
            self._event_bus.publish(event_type, {
                "run_id": self._run["run_id"],
                "message": message,
                "level": level,
                "timestamp": timestamp,
            })

    def _is_user_facing(self, record: logging.LogRecord, message: str) -> bool:
        """Decide if a message belongs in the main execution log."""
        if record.levelno >= logging.WARNING:
            return True
        if record.levelno < logging.INFO:
            return False
        logger_root = record.name.split(".")[0]
        if logger_root in self._DEBUG_LOGGERS:
            return False
        if any(message.startswith(prefix) for prefix in self._INTERNAL_PREFIXES):
            return False
        if self._looks_like_http_log(message):
            return False
        return True

    @staticmethod
    def _looks_like_http_log(message: str) -> bool:
        """Detect urllib3-style HTTP request log lines."""
        return message.startswith("http") and "HTTP/" in message

    def _check_output_file(self, message: str) -> None:
        """Extract output filenames from log messages."""
        match = self._OUTPUT_FILE_RE.search(message)
        if match:
            filename = match.group(1)
            if filename not in self._run["output_files"]:
                self._run["output_files"].append(filename)
