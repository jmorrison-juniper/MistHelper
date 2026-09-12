"""DeviceDataFetcher extracted from MistHelper.

Interactive device data fetcher for single-device operations. Originally
defined as ``DeviceDataFetcher`` inside MistHelper.py. Extracted here per
initiative 1011 to shrink the monolith.

Runtime dependencies (``PromptUtils``, ``DataProcessingUtils``,
``DataExporter``, ``DisplayUtils``, ``apisession``) still live inside
MistHelper.py and are resolved lazily via the ``_MH`` module-level proxy so
this module keeps its import graph flat and honours any test monkey-patches
applied at runtime.
"""

from __future__ import annotations  # Enable postponed evaluation for forward-ref typing

import importlib  # Late-import MistHelper to avoid circular src<->MistHelper dependency
import logging  # Structured action logging required by Constitution VII
from dataclasses import dataclass  # Underpins the DeviceFetchConfig configuration container
from typing import Any  # Loose typing for late-bound MistHelper attributes and fetch callables

# ============================================================================
# CONFIGURATION DATACLASS (5-Item Rule Compliance)
# ============================================================================
# DeviceFetchConfig groups the six parameters needed for an interactive fetch
# so callers stay within the 5-parameter limit per function (Constitution).
# Extracted from MistHelper.py per initiative 1015 (T-01, Cat E).


@dataclass
class DeviceFetchConfig:
    """Configuration for interactive device data fetching - groups fetch parameters."""

    fetch_function: Any  # Callable that performs the actual API fetch for the chosen data
    filename: str  # Output filename for the exported data
    description: str  # Human-readable description shown to the user during the fetch
    device_type: str = "all"  # Device type filter (all/ap/switch/gateway); 'all' avoids the AP-only API default
    site_id: str | None = None  # Optional site scope. None means an org-wide fetch
    device_id: str | None = None  # Optional single-device scope. None means all matching devices


class _MistHelperProxy:  # Attribute forwarder to MistHelper module attributes
    """Forward attribute access to the currently-loaded MistHelper module."""

    def __getattr__(self, name: str) -> Any:  # Called only when the attribute is not found normally
        """Resolve name against the live MistHelper module (call-time lookup)."""
        misthelper_module = importlib.import_module("MistHelper")  # Lazy import at call time
        return getattr(misthelper_module, name)  # Fetch the current bound value from MistHelper


_MH = _MistHelperProxy()  # Sole module-level proxy handle used inside the class body


class DeviceDataFetcher:
    """Interactive device data fetcher for single-device operations.

    Fetches data for a specific device (by site_id/device_id or via user prompt),
    writes the result to CSV, and displays as PrettyTable.

    SECURITY: Uses authenticated API session for all device queries.

    Usage:
        DeviceDataFetcher(DeviceFetchConfig(fetch_function, filename, description)).fetch()
        DeviceDataFetcher(DeviceFetchConfig(fetch_function, filename, description, device_type="gateway")).fetch()
    """

    def __init__(self, config: DeviceFetchConfig) -> None:
        """Initialize fetcher from a DeviceFetchConfig (issue #470: 6 params bundled into one per 5-Item Rule)."""
        self.fetch_function = config.fetch_function  # Callable that performs the actual API fetch.
        self.filename = config.filename  # Output filename for the exported data.
        self.description = config.description  # Human-readable description shown during the fetch.
        self.device_type = config.device_type  # Device type filter (all/ap/switch/gateway).
        self.site_id = config.site_id  # Optional site scope (None means an org-wide fetch).
        self.device_id = config.device_id  # Optional single-device scope (None means all matching devices).

    def fetch(self) -> None:
        """Orchestrate the device data fetch workflow (main entry point)."""
        logging.info("Starting device data fetch: %s", self.description)  # Announce fetch start for observability
        if not self._resolve_site_id():  # Bail out early if we cannot determine which site to query
            logging.debug("Fetch aborted: site_id could not be resolved")  # Trace early exit
            return  # Nothing else to do without a site scope
        if not self._resolve_device_id():  # Bail out if we cannot determine which device to query
            logging.debug("Fetch aborted: device_id could not be resolved")  # Trace early exit
            return  # Nothing else to do without a device scope
        self._log_action()  # Emit the descriptive action log
        data = self._fetch_data()  # Perform the actual API call
        if data:  # Only process and export when data is non-empty
            self._process_and_output(data)  # Flatten, escape, write CSV, and display
        logging.debug("Completed device data fetch: %s", self.description)  # Trace successful completion

    def _resolve_site_id(self) -> bool:
        """Resolve site ID from parameter or user prompt."""
        if self.site_id:  # Caller may have pre-supplied the site. Reuse it verbatim
            return True  # Already resolved
        self.site_id = _MH.PromptUtils.select_site_id_from_csv()  # Interactive site selection from CSV inventory
        return bool(self.site_id)  # False when the user cancelled or no sites exist

    def _resolve_device_id(self) -> bool:
        """Resolve device ID from parameter or user prompt."""
        if self.device_id:  # Caller may have pre-supplied the device. Reuse it verbatim
            return True  # Already resolved
        assert self.site_id is not None, "Site ID must be resolved before device ID"  # nosec B101
        self.device_id = _MH.PromptUtils.select_device_id_from_inventory(  # Interactive device selection
            self.site_id, device_type=self.device_type
        )  # Filter by the caller-configured device type (all/ap/switch/gateway)
        return bool(self.device_id)  # False when the user cancelled or no matching devices exist

    def _log_action(self) -> None:
        """Log the action being performed."""
        logging.info("%s for device ID: %s", self.description, self.device_id)  # Human-readable action trace

    def _fetch_data(self) -> list[dict[str, Any]] | None:
        """Fetch data using the configured API function."""
        logging.info("Fetching data via %s", getattr(self.fetch_function, "__name__", "<fetch_function>"))  # API trace
        try:  # Guard against transient API failures so we can log and return None
            response = self.fetch_function(_MH.apisession, self.site_id, self.device_id)  # Live authenticated call
            result = [response.data] if response.data else None  # Wrap single-device response into a one-element list
            logging.debug("Fetch returned %s record(s)", 0 if result is None else len(result))  # Result-size trace
            return result  # None signals empty response so callers can skip processing
        except Exception as error:  # Any API/network error yields None with a structured log
            logging.error("Failed to fetch device data: %s", error)  # Structured error log
            return None  # Signal failure without raising to preserve interactive UX

    def _process_and_output(self, data: list[dict[str, Any]]) -> None:
        """Process fetched data and output to CSV and table."""
        logging.info("Processing %s record(s) for %s", len(data), self.filename)  # Announce processing start
        processed = _MH.DataProcessingUtils.flatten_nested_fields(data)  # Flatten nested API structures
        processed = _MH.DataProcessingUtils.escape_multiline(processed)  # Escape multiline strings for CSV
        _MH.DataExporter.write_with_format_selection(processed, self.filename)  # Emit CSV/JSON per user choice
        _MH.DisplayUtils.dict_list_as_pretty_table(processed)  # Render to console via PrettyTable
        logging.debug("Wrote %s and rendered table", self.filename)  # Trace output completion
