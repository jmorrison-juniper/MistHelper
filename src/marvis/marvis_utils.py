"""Utilities for processing Marvis AI API responses into CSV-ready format.

src/marvis/marvis_utils.py — extracted from MistHelper.py to keep the monolith
under the 5-Item Rule limit.

Dependencies are injected via the constructor to avoid circular imports
with MistHelper.py. Callers must pass the data-processing callables they
hold (escape_multiline and flatten_nested_fields from DataProcessingUtils).

Target audience: Junior NOC engineers.  Every line is commented.
"""

from __future__ import annotations  # Enable PEP 563 postponed annotations for forward refs

import logging  # Standard library logging for info/debug/error messages
from collections.abc import Callable  # Use collections.abc.Callable per UP035 (not typing.Callable)
from typing import Any  # Generic Any type hint for untyped API response data


class MarvisDataUtils:
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

    def __init__(  # Constructor that injects the two required data-processing callables
        self,
        escape_fn: Callable[
            [list[dict[str, Any]]], list[dict[str, Any]]
        ],  # Callable to escape multiline strings in CSV data
        flatten_fn: Callable[
            [list[Any]], list[dict[str, Any]]
        ],  # Callable to flatten deeply nested dicts into flat rows
    ) -> None:
        """Initialise MarvisDataUtils with injected data-processing helpers.

        Args:
            escape_fn:  Callable matching DataProcessingUtils.escape_multiline
                        signature — takes a list of dicts, returns a list of dicts
                        with multiline strings escaped.
            flatten_fn: Callable matching DataProcessingUtils.flatten_nested_fields
                        signature — takes a list of arbitrary items and returns a
                        flat list of dicts suitable for CSV export.
        """
        self._escape_fn = escape_fn  # Store escape callable for use in format_for_csv
        self._flatten_fn = flatten_fn  # Store flatten callable for fallback processing

    def format_for_csv(  # noqa: C901, PLR0912  # Complex method with intentional branching for analysis types
        self,
        api_response_data: Any,  # Raw API response from a Marvis troubleshoot call
        analysis_type: str = "generic",  # Category label used to choose formatting strategy
    ) -> list[dict[str, Any]]:
        """Convert a raw Marvis API response into a flat list of dicts for CSV export.

        Handles four known analysis types (client, device, network, sites) plus a
        generic fallback.  For "sites", each site in the results list becomes its
        own row.  For other types, each top-level item becomes a single flattened row.

        Args:
            api_response_data: Raw Marvis API response (dict or list of dicts).
            analysis_type:     One of "client", "device", "network", "sites", or
                               "generic".  Drives the formatting strategy.

        Returns:
            List of flat dicts suitable for csv.DictWriter or similar.
        """
        try:  # Wrap entire method in try/except so a bad response never crashes the caller
            logging.info(  # Log entry point so operators can trace which analysis_type was processed
                "Starting Marvis CSV formatting for analysis_type='%s'", analysis_type
            )

            if not api_response_data:  # Guard against None or empty responses from the API
                logging.warning(
                    "Empty Marvis API response received — returning empty list"
                )  # Warn so operators know the API gave nothing
                return []  # Return empty list instead of crashing

            # Normalise the response: the Marvis API sometimes returns a single dict
            # instead of a list; wrap it so the rest of the logic always iterates.
            if not isinstance(api_response_data, list):  # Check if response is a single dict
                data_list: list[Any] = [api_response_data]  # Wrap single dict in a list for uniform processing
            else:
                data_list = api_response_data  # Already a list — use directly

            formatted_data: list[dict[str, Any]] = []  # Accumulator for processed rows

            for item in data_list:  # Iterate over each top-level response item
                if not isinstance(item, dict):  # Skip non-dict items (malformed data)
                    logging.warning(  # Warn operators so they can investigate malformed API responses
                        "Unexpected data type in Marvis response: %s — skipping item", type(item)
                    )
                    continue  # Move to next item without crashing

                # The "sites" analysis type returns an SLE summary with a nested
                # "results" list — one entry per site.  Expand that list so each
                # site becomes its own CSV row.
                if (  # Check for sites SLE structure with a results list
                    analysis_type == "sites"  # Only apply special handling for the sites analysis type
                    and "results" in item  # Response must have a results key
                    and isinstance(item["results"], list)  # Results must be a list of site dicts
                ):
                    logging.info(  # Log how many sites are being processed for operator visibility
                        "Processing organization sites SLE data with %d sites",
                        len(item["results"]),
                    )
                    formatted_data = self._expand_sites_rows(item, formatted_data)  # Delegate site expansion to helper
                    logging.info(  # Log the row count so operators can verify the expansion worked
                        "Converted %d sites into %d readable rows",
                        len(item["results"]),
                        len(formatted_data),
                    )

                else:  # All non-sites types (client, device, network, generic)
                    formatted_row = self._build_flat_row(item)  # Flatten one response item into a dict row
                    if formatted_row:  # Only append if the flattening produced at least one key-value pair
                        formatted_data.append(formatted_row)  # Add the flattened row to the accumulator

            # Apply CSV-safe escaping to all collected rows so multiline strings
            # don't break spreadsheet imports (e.g. embedded newlines in descriptions).
            logging.info(  # Log before calling the injected escape function so the call is traceable
                "Applying multiline escape to %d Marvis rows", len(formatted_data)
            )
            formatted_data = self._escape_fn(formatted_data)  # Call the injected escape_multiline function
            logging.debug(  # Log after escaping so operators know the post-escape row count
                "Marvis data formatting complete: %d rows for analysis_type='%s'",
                len(formatted_data),
                analysis_type,
            )
            return formatted_data  # Return the fully formatted list of flat row dicts

        except Exception as error:  # Catch any unexpected error so Marvis failures don't crash the whole export
            logging.error(  # Log the full error context so operators can diagnose failures
                "Error formatting Marvis data for CSV (analysis_type='%s'): %s",
                analysis_type,
                error,
            )
            logging.info(
                "Falling back to legacy flatten+escape method for Marvis data"
            )  # Inform operators that the fallback path is being used
            return self._recover_via_flatten_pipeline(api_response_data)  # Use injected callables for safe fallback

    # ------------------------------------------------------------------
    # Private helpers — extract sub-logic to stay within the 25-line rule
    # ------------------------------------------------------------------

    def _expand_sites_rows(  # Helper that converts the sites SLE results list into per-site CSV rows
        self,
        item: dict[str, Any],  # Top-level response item that contains the nested "results" list
        accumulated: list[dict[str, Any]],  # Existing list to append the new site rows into
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
        metadata_keys = [
            "start",
            "end",
            "limit",
            "page",
            "total",
        ]  # Keys to copy from the parent object into each site row

        for idx, site_data in enumerate(item["results"]):  # Iterate over each site entry in the results list
            site_row: dict[str, Any] = {}  # Start a fresh dict for this site's CSV row

            for meta_key in metadata_keys:  # Copy metadata from the parent response into this site's row
                if meta_key in item:  # Only copy keys that actually exist in this response
                    site_row[meta_key] = item[meta_key]  # Preserve metadata context alongside per-site data

            site_row["site_index"] = idx  # Add a sequential index so analysts can re-sort to original order

            if isinstance(site_data, dict):  # Only process dict entries — skip malformed items
                for key, value in site_data.items():  # Iterate over all site-level fields
                    clean_key = key.replace("-", "_")  # Normalise hyphens to underscores for CSV column compatibility
                    site_row[clean_key] = value  # Store the normalised field in the row

            accumulated.append(site_row)  # Append the fully constructed site row to the accumulator

        return accumulated  # Return the updated list with all new site rows appended

    def _build_flat_row(  # Helper that flattens a single Marvis response item into a CSV-ready dict
        self,
        item: dict[str, Any],  # A single dict from the top-level Marvis response list
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
        formatted_row: dict[str, Any] = {}  # Accumulate all key-value pairs for this row

        for key, value in item.items():  # Iterate over every field in the response item
            if key == "results" and isinstance(
                value, list
            ):  # "results" is a special nested array requiring index-based expansion
                formatted_row = self._flatten_results_array(
                    formatted_row, value
                )  # Delegate results-array expansion to dedicated helper
            elif isinstance(value, dict):  # Nested dict — flatten by prepending the parent key name
                for nested_key, nested_value in value.items():  # Iterate nested dict keys
                    clean_key = f"{key}_{nested_key}".replace("-", "_")  # Build composite key, normalising hyphens
                    formatted_row[clean_key] = nested_value  # Store flattened nested value
            elif isinstance(value, list):  # Lists that aren't "results" — join as comma-separated string
                formatted_row[key] = ",".join(map(str, value))  # Convert list to single string for CSV compatibility
            else:  # Scalar value — store directly
                formatted_row[key] = value  # Simple direct assignment for strings, ints, booleans, etc.

        return formatted_row  # Return the fully flattened row dict

    def _flatten_results_array(  # Helper that index-expands the nested "results" array into prefixed columns
        self,
        row: dict[str, Any],  # Existing partial row dict to add result columns into
        results: list[Any],  # The "results" list from a single Marvis troubleshoot response item
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
        for idx, result in enumerate(results):  # Enumerate results so we can prefix columns with the result index
            if isinstance(result, dict):  # Only expand dict entries — skip malformed items
                for result_key, result_value in result.items():  # Iterate each field within this result entry
                    # Build column name like result_0_category (underscores, no hyphens)
                    clean_key = f"result_{idx}_{result_key.replace('-', '_')}"  # Index-prefixed column name for CSV
                    row[clean_key] = result_value  # Store indexed result field in the row
            else:  # Non-dict result entry — store as a plain indexed column
                row[f"result_{idx}"] = str(result)  # Convert to string to ensure CSV writeability

        return row  # Return the row with all result columns appended

    def _recover_via_flatten_pipeline(  # Fallback path used when the primary formatter raises unexpectedly
        self,
        api_response_data: Any,  # The original raw API response that caused the formatting error
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
        logging.info(
            "Beginning legacy Marvis fallback: normalise to list"
        )  # Log before normalising so operators can trace the fallback
        fallback_data: list[Any] = (  # Normalise to list so flatten_fn can iterate
            [api_response_data]  # Wrap a single dict in a list if needed
            if not isinstance(api_response_data, list)  # Check if the raw data is already a list
            else api_response_data  # Already a list — use as-is
        )
        logging.info(
            "Applying flatten to %d legacy Marvis items", len(fallback_data)
        )  # Log before flatten so operators know it was called
        fallback_data = self._flatten_fn(fallback_data)  # Flatten nested fields using the injected flatten callable
        logging.debug(
            "Legacy flatten produced %d rows; applying escape", len(fallback_data)
        )  # Log row count after flatten before escaping
        fallback_data = self._escape_fn(fallback_data)  # Escape multiline strings using the injected escape callable
        logging.debug(
            "Legacy Marvis fallback complete: %d rows", len(fallback_data)
        )  # Log final row count so operators know the fallback finished
        return fallback_data  # Return the fallback result to the caller
