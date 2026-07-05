"""Utilities for processing Marvis AI API responses into CSV-ready format.

src/marvis/marvis_utils.py -- extracted from MistHelper.py to keep the monolith
under the 5-Item Rule limit.

Dependencies are injected via the constructor to avoid circular imports
with MistHelper.py. Callers must pass the data-processing callables they
hold (escape_multiline and flatten_nested_fields from DataProcessingUtils).

Target audience: Junior NOC engineers.  Every line is commented.
"""

from __future__ import annotations  # WHY: PEP 563 postponed annotations for forward refs

import logging  # WHY: Standard library logging for info/debug/error trace
from collections.abc import Callable  # WHY: UP035 requires collections.abc.Callable
from typing import Any  # WHY: Generic Any type hint for untyped API payloads

# Module-level constants avoid magic values scattered through the logic.
_SITES_ANALYSIS_TYPE = "sites"  # WHY: Sentinel driving the sites SLE expansion branch
_RESULTS_KEY = "results"  # WHY: Nested key that Marvis wraps troubleshoot rows under
_SITE_METADATA_KEYS: tuple[str, ...] = (  # WHY: Parent-item keys copied to each site row
    "start",
    "end",
    "limit",
    "page",
    "total",
)


class MarvisDataUtils:  # WHY: Class groups Marvis-to-CSV helpers with injected deps
    """Process Marvis AI API responses into CSV-ready row lists.

    Uses dependency injection for data-processing helpers to keep this
    module free of imports from MistHelper.py (which would create a
    circular dependency).

    Usage in MistHelper.py::

        marvis_data_utils = MarvisDataUtils(
            escape_fn=DataProcessingUtils.escape_multiline,
            flatten_fn=DataProcessingUtils.flatten_nested_fields,
        )
        rows = marvis_data_utils.format_for_csv(response.data, "client")
    """

    def __init__(  # WHY: Constructor injects data-processing callables (no import of MistHelper)
        self,
        escape_fn: Callable[[list[dict[str, Any]]], list[dict[str, Any]]],
        flatten_fn: Callable[[list[Any]], list[dict[str, Any]]],
    ) -> None:
        """Initialise MarvisDataUtils with injected data-processing helpers.

        Args:
            escape_fn:  Callable matching DataProcessingUtils.escape_multiline
                        signature -- takes a list of dicts, returns a list of dicts
                        with multiline strings escaped.
            flatten_fn: Callable matching DataProcessingUtils.flatten_nested_fields
                        signature -- takes a list of arbitrary items and returns a
                        flat list of dicts suitable for CSV export.
        """
        self._escape_fn = escape_fn  # WHY: Store escape callable for primary + fallback paths
        self._flatten_fn = flatten_fn  # WHY: Store flatten callable for fallback path

    def format_for_csv(  # WHY: Public entry -- try structured path, fall back on error
        self,
        api_response_data: Any,
        analysis_type: str = "generic",
    ) -> list[dict[str, Any]]:
        """Convert a raw Marvis API response into a flat list of dicts for CSV export.

        Handles the sites SLE expansion and generic per-item flattening; any
        internal error routes to the legacy flatten+escape fallback so callers
        always receive a list rather than an exception.
        """
        try:  # WHY: Bad payloads must never crash the caller
            return self._run_primary_pipeline(api_response_data, analysis_type)  # WHY: Structured path
        except Exception as error:  # WHY: Any failure routes to the legacy fallback
            self._log_primary_failure(analysis_type, error)  # WHY: Diagnostic before fallback
            return self._recover_via_flatten_pipeline(api_response_data)  # WHY: Injected fallback

    @staticmethod
    def _log_primary_failure(analysis_type: str, error: Exception) -> None:  # WHY: Split logging out
        """Emit error + info logs describing the fallback transition."""
        logging.error(  # WHY: Preserve full error context for operator triage
            "Error formatting Marvis data for CSV (analysis_type='%s'): %s",
            analysis_type,
            error,
        )
        logging.info("Falling back to legacy flatten+escape method for Marvis data")  # WHY: Signal fallback

    def _run_primary_pipeline(  # WHY: Extract structured formatting from the try/except shell
        self,
        api_response_data: Any,
        analysis_type: str,
    ) -> list[dict[str, Any]]:
        """Run the structured format-then-escape pipeline on a normalised list."""
        logging.info("Starting Marvis CSV formatting for analysis_type='%s'", analysis_type)  # WHY: Trace entry
        if not api_response_data:  # WHY: None / empty responses short-circuit to []
            logging.warning("Empty Marvis API response received -- returning empty list")
            return []  # WHY: Empty list keeps callers safe from None-iteration errors
        data_list = self._normalise_to_list(api_response_data)  # WHY: Uniform iteration
        formatted = self._collect_rows(data_list, analysis_type)  # WHY: Dispatch per-item strategy
        logging.info("Applying multiline escape to %d Marvis rows", len(formatted))  # WHY: Trace escape call
        formatted = self._escape_fn(formatted)  # WHY: CSV-safe multiline escaping
        logging.debug(  # WHY: Post-escape count aids operator verification
            "Marvis data formatting complete: %d rows for analysis_type='%s'",
            len(formatted),
            analysis_type,
        )
        return formatted  # WHY: Fully formatted list returned to caller

    @staticmethod
    def _normalise_to_list(data: Any) -> list[Any]:  # WHY: Wrap single dict responses in list
        """Return the response as a list so the rest of the pipeline can iterate."""
        return data if isinstance(data, list) else [data]  # WHY: Single-item wrap when not list

    def _collect_rows(  # WHY: Iterate response items and dispatch per analysis type
        self,
        data_list: list[Any],
        analysis_type: str,
    ) -> list[dict[str, Any]]:
        """Iterate the normalised list and delegate to the right expansion helper."""
        formatted: list[dict[str, Any]] = []  # WHY: Accumulator for output rows
        for item in data_list:  # WHY: One item can produce one or many rows
            if not isinstance(item, dict):  # WHY: Skip malformed non-dict entries
                logging.warning(
                    "Unexpected data type in Marvis response: %s -- skipping item",
                    type(item),
                )
                continue  # WHY: Malformed entries are logged and dropped
            self._dispatch_item(item, analysis_type, formatted)  # WHY: Delegate to sites or generic path
        return formatted  # WHY: Row accumulator ready for escape pass

    def _dispatch_item(  # WHY: Route a single item to the sites or generic builder
        self,
        item: dict[str, Any],
        analysis_type: str,
        formatted: list[dict[str, Any]],
    ) -> None:
        """Dispatch one response item to the sites expansion or generic flattener."""
        if self._is_sites_expansion(item, analysis_type):  # WHY: Sites SLE branch fans out rows
            logging.info(  # WHY: Report site count for operator visibility
                "Processing organization sites SLE data with %d sites",
                len(item[_RESULTS_KEY]),
            )
            self._expand_sites_rows(item, formatted)  # WHY: Mutates formatted in place
            logging.info(  # WHY: Report resulting row count after expansion
                "Converted %d sites into %d readable rows",
                len(item[_RESULTS_KEY]),
                len(formatted),
            )
            return  # WHY: Sites branch is fully handled
        row = self._build_flat_row(item)  # WHY: Non-sites items flatten to a single row
        if row:  # WHY: Skip empty-dict results to avoid blank CSV rows
            formatted.append(row)  # WHY: Append the flattened row

    @staticmethod
    def _is_sites_expansion(  # WHY: Predicate isolates the sites-SLE branch condition
        item: dict[str, Any],
        analysis_type: str,
    ) -> bool:
        """Return True when the item should be expanded per-site."""
        return (  # WHY: All three checks are needed to safely index item[results]
            analysis_type == _SITES_ANALYSIS_TYPE and _RESULTS_KEY in item and isinstance(item[_RESULTS_KEY], list)
        )

    def _expand_sites_rows(  # WHY: Fan out nested results list into per-site rows
        self,
        item: dict[str, Any],
        accumulated: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Expand the nested 'results' list from a sites SLE response into per-site rows.

        One row is emitted per site entry in item["results"].  Metadata keys
        (start, end, limit, page, total) from the parent item are copied into
        every site row so context is preserved after flattening.

        Args:
            item:        The response dict that contains a "results" list of site dicts.
            accumulated: The running list of formatted rows to append into.

        Returns:
            Updated list of formatted rows with the newly expanded site rows appended.
        """
        for idx, site_data in enumerate(item[_RESULTS_KEY]):  # WHY: Each site becomes one row
            accumulated.append(self._build_site_row(item, idx, site_data))  # WHY: Append per-site row
        return accumulated  # WHY: Return same list for chaining / test parity

    @staticmethod
    def _build_site_row(  # WHY: Assemble a single site row from parent metadata + site fields
        item: dict[str, Any],
        idx: int,
        site_data: Any,
    ) -> dict[str, Any]:
        """Build one row combining parent metadata, site index, and site fields."""
        site_row: dict[str, Any] = {  # WHY: Seed row with parent-level metadata keys
            key: item[key] for key in _SITE_METADATA_KEYS if key in item
        }
        site_row["site_index"] = idx  # WHY: Sequential index preserves original ordering
        if isinstance(site_data, dict):  # WHY: Skip malformed non-dict site entries silently
            for key, value in site_data.items():  # WHY: Copy every site-level field
                site_row[key.replace("-", "_")] = value  # WHY: Normalise hyphens for CSV columns
        return site_row  # WHY: Fully built site row ready to append

    def _build_flat_row(  # WHY: Flatten one Marvis response item into a CSV-ready dict
        self,
        item: dict[str, Any],
    ) -> dict[str, Any]:
        """Flatten one Marvis response item (client / device / network) into a single dict.

        The Marvis API wraps troubleshoot results in a nested "results" array.
        This method un-nests that array and emits columns like result_0_category,
        result_0_reason, etc.  Other nested dicts are flattened with underscored
        composite keys.  Lists are joined as comma-separated strings.

        Args:
            item: A single response dict that may contain nested dicts and lists.

        Returns:
            A flat dict with all nested values promoted to top-level keys.
        """
        formatted_row: dict[str, Any] = {}  # WHY: Accumulate every flattened column here
        for key, value in item.items():  # WHY: Walk every top-level field of the item
            self._flatten_field(formatted_row, key, value)  # WHY: Table-free per-field dispatch
        return formatted_row  # WHY: Fully flattened dict ready for escape pass

    def _flatten_field(  # WHY: Guard clause peels off the results-array special case first
        self,
        row: dict[str, Any],
        key: str,
        value: Any,
    ) -> None:
        """Flatten a single (key, value) pair into the accumulating row dict."""
        if key == _RESULTS_KEY and isinstance(value, list):  # WHY: Special nested results array
            self._flatten_results_array(row, value)  # WHY: Delegate index-expansion helper
            return  # WHY: Guard-clause return keeps the sibling dispatch simple
        self._store_typed_value(row, key, value)  # WHY: Dispatch by scalar / dict / list type

    @staticmethod
    def _store_typed_value(  # WHY: Split by value type -- keeps _flatten_field CC low
        row: dict[str, Any],
        key: str,
        value: Any,
    ) -> None:
        """Store a value into the row using per-type flattening rules."""
        if isinstance(value, dict):  # WHY: Nested dict flattens via parent_child keys
            for nested_key, nested_value in value.items():  # WHY: Enumerate nested entries
                row[f"{key}_{nested_key}".replace("-", "_")] = nested_value  # WHY: Composite key
            return  # WHY: Dict branch fully handled
        if isinstance(value, list):  # WHY: Plain list becomes comma-separated string
            row[key] = ",".join(map(str, value))  # WHY: CSV-friendly single-cell representation
            return  # WHY: List branch fully handled
        row[key] = value  # WHY: Scalar values map directly to their column

    def _flatten_results_array(  # WHY: Expand each result dict into result_N_key columns
        self,
        row: dict[str, Any],
        results: list[Any],
    ) -> dict[str, Any]:
        """Expand each entry in a Marvis 'results' array into prefixed columns.

        E.g. results[0] = {"category": "WiFi", "reason": "low RSSI"} becomes
        result_0_category and result_0_reason columns in the CSV row.

        Args:
            row:     Partial row dict already populated with other top-level fields.
            results: The list stored under the "results" key in a Marvis response.

        Returns:
            The updated row dict with result_N_key columns added.
        """
        for idx, result in enumerate(results):  # WHY: Index each entry so columns stay ordered
            self._store_result_columns(row, idx, result)  # WHY: One helper handles dict + scalar
        return row  # WHY: Return same dict so caller / tests can chain

    @staticmethod
    def _store_result_columns(  # WHY: Emit result_N or result_N_key columns for one entry
        row: dict[str, Any],
        idx: int,
        result: Any,
    ) -> None:
        """Store one result entry into the row using indexed column names."""
        if isinstance(result, dict):  # WHY: Dict results expand into multiple prefixed columns
            for result_key, result_value in result.items():  # WHY: Walk nested result fields
                row[f"result_{idx}_{result_key.replace('-', '_')}"] = result_value  # WHY: Prefixed key
            return  # WHY: Dict branch fully handled
        row[f"result_{idx}"] = str(result)  # WHY: Non-dict results stringify into a single column

    def _recover_via_flatten_pipeline(  # WHY: Legacy fallback path for unexpected errors
        self,
        api_response_data: Any,
    ) -> list[dict[str, Any]]:
        """Recover from a formatting failure using the two injected processing callables.

        Falls back to the same flatten+escape pipeline that was used before the
        structured formatting was introduced.  Ensures the caller still gets data
        even if the structured formatter has a bug.

        Args:
            api_response_data: The raw API response that triggered the exception.

        Returns:
            A list of flattened dicts (may be less readable than the primary path).
        """
        logging.info("Beginning legacy Marvis fallback: normalise to list")  # WHY: Trace fallback entry
        fallback_data = self._normalise_to_list(api_response_data)  # WHY: Same wrap logic as primary
        logging.info("Applying flatten to %d legacy Marvis items", len(fallback_data))  # WHY: Trace flatten
        fallback_data = self._flatten_fn(fallback_data)  # WHY: Injected flatten callable
        logging.debug("Legacy flatten produced %d rows; applying escape", len(fallback_data))  # WHY: Trace escape
        fallback_data = self._escape_fn(fallback_data)  # WHY: Injected escape callable
        logging.debug("Legacy Marvis fallback complete: %d rows", len(fallback_data))  # WHY: Trace exit
        return fallback_data  # WHY: Return fallback rows to caller
