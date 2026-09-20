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

import logging  # Structured action logging required by Constitution VII
from dataclasses import dataclass  # Underpins the DeviceFetchConfig configuration container
from typing import Any, Literal  # Loose typing for late-bound MistHelper attributes and fetch callables.

from src.config.source_dependency_resolver import (
    SourceDependencyResolver,  # WHY: resolve source dependencies without importing the root module.
)

logger = logging.getLogger(__name__)  # Keep refactor logs tied to this module.
_HTTP_OK = 200  # WHY: a response double without a status should keep legacy success behavior.
_HTTP_ERROR_MIN = 400  # WHY: HTTP 4xx and 5xx statuses mean the payload cannot prove emptiness.
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


_MH = SourceDependencyResolver  # Use the source resolver for lazy dependency access.


def _response_status_code(response: Any) -> int:
    """Return the HTTP status when the SDK response exposes one."""
    status_code = getattr(response, "status_code", _HTTP_OK)  # WHY: old tests use simple response doubles.
    return status_code if isinstance(status_code, int) else _HTTP_OK  # WHY: non-int mock attributes are not statuses.


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

    def fetch(self) -> Literal[False] | None:
        """Orchestrate the device data fetch workflow (main entry point)."""
        logger.info("Starting device data fetch: %s", self.description)  # Announce fetch start for observability
        if not self._resolve_site_id():  # Bail out early if we cannot determine which site to query
            logger.debug("Fetch aborted: site_id could not be resolved")  # Trace early exit
            return None  # Nothing else to do without a site scope
        if not self._resolve_device_id():  # Bail out if we cannot determine which device to query
            logger.debug("Fetch aborted: device_id could not be resolved")  # Trace early exit
            return None  # Nothing else to do without a device scope
        self._log_action()  # Emit the descriptive action log
        data = self._fetch_data()  # Perform the actual API call
        if data is False:  # WHY: only an explicit HTTP failure changes the legacy path.
            return False  # WHY: callers must not log completion after the cloud refuses.
        if data:  # Only process and export when data is non-empty
            self._process_and_output(data)  # Flatten, escape, write CSV, and display
        logger.debug("Completed device data fetch: %s", self.description)  # Trace successful completion
        return None  # WHY: preserve the legacy no-return success path.

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
        if self.site_id is None:  # WHY: device selection needs a site scope before it can query inventory.
            raise RuntimeError("Site ID must be resolved before device ID")  # WHY: keep the assertion message.
        self.device_id = _MH.PromptUtils.select_device_id_from_inventory(  # Interactive device selection
            self.site_id, device_type=self.device_type
        )  # Filter by the caller-configured device type (all/ap/switch/gateway)
        return bool(self.device_id)  # False when the user cancelled or no matching devices exist

    def _log_action(self) -> None:
        """Log the action being performed."""
        logger.info("%s for device ID: %s", self.description, self.device_id)  # Human-readable action trace

    def _fetch_data(self) -> list[dict[str, Any]] | Literal[False] | None:
        """Fetch data using the configured API function."""
        logger.info("Fetching data via %s", getattr(self.fetch_function, "__name__", "<fetch_function>"))  # API trace
        try:  # Guard against transient API failures so we can log and return None
            response = self.fetch_function(_MH.apisession, self.site_id, self.device_id)  # Live authenticated call
            status_code = _response_status_code(response)  # WHY: a 5xx can carry an empty payload without raising.
            if status_code >= _HTTP_ERROR_MIN:  # WHY: a failing HTTP status makes the device result unsafe.
                logger.error(  # WHY: the operator must see the cloud status instead of a false empty result.
                    "The cloud returned HTTP %s for device data at site %s",
                    status_code,
                    self.site_id,
                )
                return False  # WHY: explicit failure lets wrappers suppress success logs.
            result = [response.data] if response.data else None  # Wrap single-device response into a one-element list
            logger.debug("Fetch returned %s record(s)", 0 if result is None else len(result))  # Result-size trace
            return result  # None signals empty response so callers can skip processing
        except Exception as error:  # Any API/network error yields None with a structured log
            logging.error("Failed to fetch device data: %s", error)  # Structured error log
            return None  # Signal failure without raising to preserve interactive UX

    def _process_and_output(self, data: list[dict[str, Any]]) -> None:
        """Process fetched data and output to CSV and table."""
        logger.info("Processing %s record(s) for %s", len(data), self.filename)  # Announce processing start
        processed = _MH.DataProcessingUtils.flatten_nested_fields(data)  # Flatten nested API structures
        processed = _MH.DataProcessingUtils.escape_multiline(processed)  # Escape multiline strings for CSV
        _MH.DataExporter.write_with_format_selection(
            processed, self.filename, api_function_name=self.fetch_function.__name__
        )  # Emit CSV/JSON per user choice
        _MH.DisplayUtils.dict_list_as_pretty_table(processed)  # Render to console via PrettyTable
        logger.debug("Wrote %s and rendered table", self.filename)  # Trace output completion
