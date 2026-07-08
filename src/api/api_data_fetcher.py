"""APIDataFetcher -- generic Mist API fetch/export/display pipeline.

Extracted from MistHelper.py during initiative 1013 (Cat B, position 21).
Wraps a single mistapi call with rate-limit-aware retries, best-effort partial
saves on failure, PrettyTable rendering, and CSV/SQLite persistence via
DataExporter.  Callers continue to reach it through the
``MistHelper.APIDataFetcher`` re-export alias.
"""

from __future__ import annotations  # WHY: enable PEP 604 unions on Python 3.9+.

import importlib  # WHY: lazy MistHelper import to reach live helper globals without circular load.
import logging  # WHY: structured trace for fetch lifecycle events.
import time  # WHY: sleep between retry attempts + rate-limit throttling.
from typing import Any  # WHY: api_call/response are duck-typed mistapi callables/objects.

import mistapi  # WHY: direct SDK access for mistapi.get_all pagination.
from prettytable import PrettyTable  # WHY: render result rows for logging.
from tqdm import tqdm  # WHY: progress bar during table build.


class APIDataFetcher:
    """Fetches data from Mist API, processes it, and exports to CSV/SQLite.

    Handles API rate limiting, malformed responses, and provides emergency
    data saves on errors. Displays results in PrettyTable for logging.

    Safety Features:
        - Emergency data saves on any exception
        - Handles HTTP 429 rate limiting gracefully
        - Recovers data from malformed API responses
        - Detailed logging for troubleshooting
    """

    def __init__(  # Capture the fetch parameters.
        self,
        title: str,
        api_call: Any,
        filename: str,
        sort_key: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Capture fetch parameters: title, api_call, filename, sort_key, and **kwargs for the API call."""
        self.title = title  # Human-readable title.
        self.api_call = api_call  # Callable that fetches data.
        self.filename = filename  # Output filename.
        self.sort_key = sort_key  # Optional sort key.
        self.kwargs = kwargs  # Extra API arguments.
        self.org_id = ""  # Resolved org id.
        self.rawdata: list[dict[str, Any]] = []  # Raw API rows.
        self.smoothed: float | None = None  # Smoothed delay metric.

    def execute(self) -> None:  # Run fetch/export/display.
        """Execute the complete API fetch workflow."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of ConfigUtils helper.
        self._log_entry()  # Log the run start.
        self.org_id = mh.ConfigUtils.get_cached_or_prompted_org_id()  # Resolve the org.

        try:
            self._fetch_api_data()  # Fetch from the API.

            if self.rawdata is None or len(self.rawdata) == 0:  # No data returned.
                logging.warning("! No data returned from API for %s. Skipping.", self.title)  # warn no data.
                logging.debug("EXIT: APIDataFetcher.execute - no data")  # Trace early exit.
                return  # Skip export.

            self._export_and_display_data()  # Export and display.
            logging.debug("EXIT: APIDataFetcher.execute - success")  # Trace success.

        except Exception as error:  # Handle run failure.
            self._handle_outer_exception(error)  # Log/report the failure.
            raise  # Propagate the error.

    # =========================================================================
    # INITIALIZATION AND LOGGING METHODS
    # =========================================================================

    def _log_entry(self) -> None:  # Log fetch parameters.
        """Log entry point with parameters."""
        api_name = self.api_call.__name__  # API callable name.
        logging.debug(  # Trace the entry.
            "ENTRY: APIDataFetcher(title=%s, api_call=%s, filename=%s, sort_key=%s, kwargs=%s)",
            self.title,
            api_name,
            self.filename,
            self.sort_key,
            self.kwargs,
        )
        logging.info("Starting data fetch: %s", self.title)  # Log fetch start.
        print(self.title)  # Show the title.

    # =========================================================================
    # API CALL METHODS
    # =========================================================================

    def _fetch_api_data(self) -> None:  # Call the API and store rows.
        """Make API call and retrieve paginated results with retry on timeout."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of apisession module global.
        api_name = self.api_call.__name__  # API callable name.
        logging.debug("Making API call: %s with kwargs: %s", api_name, self.kwargs)  # Trace the call.

        response = self._call_api_with_retry(api_name)  # Call with retry.
        self._apply_rate_limiting()  # Throttle after the call.
        self._log_response_structure(response)  # Trace response shape.

        try:
            self.rawdata = mistapi.get_all(response=response, mist_session=mh.apisession)  # Page through all rows.
            record_count = len(self.rawdata) if self.rawdata else 0  # Count retrieved rows.
            logging.debug("API call successful, retrieved %s raw records", record_count)  # Trace the count.
        except KeyError as error:  # Malformed response key.
            self._handle_key_error(response, error)  # Try to recover data.
        except Exception as error:  # Other API failure.
            self._handle_api_exception(error)  # Handle/raise the failure.

    def _call_api_with_retry(self, api_name: str) -> Any:  # Retry the API call.
        """Call API with retry/backoff (mistapi swallows timeouts as status_code=None)."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of apisession + retry constants.
        max_retries = mh.API_REQUEST_MAX_RETRIES  # Retry ceiling.
        retry_delay = mh.API_REQUEST_RETRY_DELAY  # Base backoff delay.
        last_response = None  # Track the last response.
        for attempt in range(max_retries + 1):  # Bounded retry loop.
            response = self.api_call(mh.apisession, self.org_id, **self.kwargs)  # Invoke the API.
            last_response = response  # Remember it.
            if self._is_response_valid(response):  # Good response?
                return response  # Return on success.
            if attempt < max_retries:  # More attempts left.
                delay = retry_delay * (2**attempt)  # Exponential backoff.
                APIDataFetcher._log_retry_attempt(api_name, attempt, delay)  # Log + print + sleep.
        logging.error("API call %s failed after %s attempts", api_name, max_retries + 1)
        return last_response  # Return last response.

    @staticmethod
    def _log_retry_attempt(api_name: str, attempt: int, delay: float) -> None:  # Log + sleep before retry.
        """Log a warning, print user-visible retry notice, and sleep for the backoff window."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of retry-ceiling constant.
        max_retries = mh.API_REQUEST_MAX_RETRIES  # Retry ceiling.
        logging.warning(  # Warn and back off.
            "API call %s failed (attempt %s/%s) - retrying in %.0fs",
            api_name,
            attempt + 1,
            max_retries + 1,
            delay,
        )
        print(f"! API call timed out - retrying in {delay:.0f}s (attempt {attempt + 2}/{max_retries + 1})")
        time.sleep(delay)  # Wait before retry.

    @staticmethod
    def _is_response_valid(response: Any) -> bool:  # Validate an API response.
        """Check if an API response indicates a successful call.

        Returns False when status_code is None (timeout/connection error
        swallowed by mistapi) or when it indicates a server error.
        """
        status = getattr(response, "status_code", None)  # Read status code.
        if status is None:  # No status present.
            return False  # Treat as invalid.
        if status >= 500:  # Server error.
            return False  # Retry on 5xx.
        return True  # Response is usable.

    def _apply_rate_limiting(self) -> None:  # Sleep to respect rate limits.
        """Apply rate limiting delay between API calls."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of RateLimitingUtils + globals.
        self.smoothed, delay = mh.RateLimitingUtils.get_rate_limited_delay(
            self.smoothed, mh.apisession, mh._api_usage_cache
        )
        logging.debug("Applying rate limit delay: %.2fs", delay)  # Trace the delay.
        time.sleep(delay)  # Apply the delay.

    def _log_response_structure(self, response: Any) -> None:  # Trace the response shape.
        """Log API response structure for debugging."""
        logging.debug("API response type: %s", type(response))  # Trace response type.
        if not hasattr(response, "data"):  # No data attribute.
            return  # Nothing to inspect.

        logging.debug("Response.data type: %s", type(response.data))  # Trace data type.
        if isinstance(response.data, dict):  # Dict payload.
            logging.debug("Response.data keys: %s", list(response.data.keys()))  # Trace dict keys.
        elif isinstance(response.data, list):  # List payload.
            logging.debug("Response.data is list with %s items", len(response.data))  # Trace list size.

    # =========================================================================
    # ERROR HANDLING METHODS
    # =========================================================================

    def _handle_key_error(self, response: Any, error: KeyError) -> None:  # Recover from missing keys.
        """Handle missing 'results' key or other structure issues."""
        logging.error("API response structure error - missing key: %s", error)  # log key error.
        self._log_response_error_details(response)  # Log response details.

        recovered_data = self._attempt_data_recovery(response)  # Try to salvage rows.

        if recovered_data:  # Recovery succeeded.
            self.rawdata = recovered_data  # Use the recovered rows.
            self._save_recovered_data()  # Persist them.
        else:
            self._handle_no_recovery()  # Give up cleanly.

    def _log_response_error_details(self, response: Any) -> None:  # Log response diagnostics.
        """Log detailed response information during error handling."""
        has_data = hasattr(response, "data")  # Has a data attribute?
        logging.error("Response details: type=%s, hasattr(data)=%s", type(response), has_data)  # log details.

        if has_data:  # Inspect the data.
            logging.error("Response.data type=%s", type(response.data))  # log data type.
            if isinstance(response.data, dict):  # Dict payload.
                logging.error("Available keys: %s", list(response.data.keys()))  # log keys.

    def _attempt_data_recovery(self, response: Any) -> list[dict[str, Any]] | None:  # Salvage rows from odd shapes.
        """Attempt to recover data from alternate response structures."""
        if not hasattr(response, "data"):  # No data to recover.
            return None  # Nothing to recover.

        if isinstance(response.data, dict):  # Dict payload.
            if "data" in response.data:  # Nested data key.
                recovered = response.data.get("data", [])  # Pull nested rows.
                logging.info("Recovered %s records from response.data['data']", len(recovered))  # log recovered.
                return recovered  # type: ignore[no-any-return]

        if isinstance(response.data, list):  # List payload.
            logging.info("Recovered %s records from response.data (list)", len(response.data))  # log recovered list.
            return response.data  # Use the list directly.

        return None  # Nothing to recover.

    def _save_recovered_data(self) -> None:  # Persist recovered rows.
        """Save recovered data and notify user."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of DataExporter helper.
        print(f"! API returned unexpected structure. Recovered {len(self.rawdata)} records.")  # Tell the user.
        api_name = self.api_call.__name__  # API callable name.
        mh.DataExporter.write_with_format_selection(self.rawdata, self.filename, api_function_name=api_name)
        logging.info("Recovered data saved to %s (%s rows)", self.filename, len(self.rawdata))  # log saved.

    def _handle_no_recovery(self) -> None:  # Report unrecoverable response.
        """Handle case where no data could be recovered."""
        print("! API response missing expected 'results' key. No data could be recovered.")  # Tell the user.
        logging.error("Unable to recover any data from malformed response for %s", self.title)  # log no recovery.
        logging.debug("EXIT: APIDataFetcher - structure error, no recovery")  # Trace exit.

    def _handle_api_exception(self, error: Exception) -> None:  # Handle a fetch exception.
        """Handle exceptions during API data retrieval."""
        logging.error("Exception occurred during API data retrieval: %s", error)  # log exception.
        logging.error("Exception type: %s", type(error).__name__)  # log type.
        print(f"! Exception occurred during API call: {error}")  # Tell the user.

        if self._is_rate_limit_error(error):  # Rate limited?
            self._handle_rate_limit()  # Save partial and stop.
            return  # Done.

        self._emergency_save_and_raise(error)  # Save then raise.

    def _is_rate_limit_error(self, error: Exception) -> bool:  # Detect HTTP 429.
        """Check if exception is HTTP 429 rate limit error."""
        status_code = getattr(getattr(error, "response", None), "status_code", None)  # Read the status code.
        return status_code == 429  # True only on 429.

    def _handle_rate_limit(self) -> None:  # Save partial on rate limit.
        """Handle HTTP 429 rate limit error."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of DataExporter helper.
        logging.warning("API rate limit (HTTP 429) reached. Saving partial results and exiting.")  # warn rate limit.

        if self.rawdata:  # Have partial data?
            api_name = self.api_call.__name__  # API callable name.
            mh.DataExporter.write_with_format_selection(self.rawdata, self.filename, api_function_name=api_name)
            logging.info("Partial results saved to %s (%s rows)", self.filename, len(self.rawdata))  # log partial.
            print(f"* Partial data saved: {len(self.rawdata)} records written to {self.filename}")  # Tell the user.

        logging.debug("EXIT: APIDataFetcher - rate limited")  # Trace exit.

    def _emergency_save_and_raise(self, error: Exception) -> None:  # Save partial then re-raise.
        """Save partial data before re-raising exception."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of DataExporter helper.
        if self.rawdata:  # Have partial data?
            try:
                api_name = self.api_call.__name__  # API callable name.
                mh.DataExporter.write_with_format_selection(self.rawdata, self.filename, api_function_name=api_name)
                logging.info("Emergency save: %s partial records saved before error exit", len(self.rawdata))
                print(f"* Emergency save: {len(self.rawdata)} partial records written to {self.filename}")
            except Exception as save_error:  # Save failed.
                logging.error("Failed to save partial data during error handling: %s", save_error)  # log save fail.

        logging.debug("EXIT: APIDataFetcher - API error")  # Trace exit.
        raise error  # Re-raise the original.

    def _handle_outer_exception(self, error: Exception) -> None:  # Handle a top-level error.
        """Handle exceptions at the top level."""
        logging.error("! Error during data fetch for %s: %s", self.title, error)  # log error.
        logging.error("Exception type: %s, Traceback info available in logs", type(error).__name__)  # log type.

        if self.rawdata:  # Have partial data?
            self._save_partial_data_on_error(error)  # Save what we have.
        else:
            print("! No data was collected before the error occurred")  # Tell the user none saved.

        logging.debug("EXIT: APIDataFetcher - error")  # Trace exit.

    def _save_partial_data_on_error(self, error: Exception) -> None:  # Persist partial rows on error.
        """Save partial data when outer exception occurs."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of DataExporter helper.
        try:
            api_name = self.api_call.__name__  # API callable name.
            mh.DataExporter.write_with_format_selection(self.rawdata, self.filename, api_function_name=api_name)
            logging.info("Partial results saved to %s (%s rows)", self.filename, len(self.rawdata))  # log partial.

            print("\n!! PARTIAL DATA SAVED !!")  # Notify the user.
            print(f"   * Despite the error, {len(self.rawdata)} records were successfully saved to {self.filename}")
            print(f"   * Error: {str(error)}")  # Show the error.
            print("   * You can retry the operation later to get remaining data")  # Suggest a retry.
        except Exception as save_error:  # Save failed.
            logging.error("Failed to save partial data in outer exception handler: %s", save_error)  # log save fail.
            print(f"! Critical: Could not save partial data. Error: {save_error}")  # Tell the user.

    # =========================================================================
    # DATA PROCESSING AND DISPLAY METHODS
    # =========================================================================

    def _export_and_display_data(self) -> None:  # Export then show a table.
        """Export data and display in table format."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of DataExporter helper.
        logging.info("Fetched %s raw records from API.", len(self.rawdata))  # log raw count.

        api_name = self.api_call.__name__  # API callable name.
        mh.DataExporter.export_with_processing(
            self.rawdata, self.filename, sort_key=self.sort_key, api_function_name=api_name
        )
        print(f"! {len(self.rawdata)} records exported to {self.filename}")  # Tell the user.

        self._display_table()  # Render the table.

    def _display_table(self) -> None:  # Build and log a table.
        """Prepare and display data in PrettyTable format."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of DataProcessingUtils helper.
        data = self._prepare_data_for_display()  # Normalize rows.
        fields = mh.DataProcessingUtils.get_unique_keys(data)
        logging.debug("Unique fields for table: %s", fields)  # Trace fields.

        table = self._build_pretty_table(data, fields)  # Build the table.
        logging.debug("\n%s", table.get_string())  # Log the table.

    def _prepare_data_for_display(self) -> list[dict[str, Any]]:  # Filter, sort, flatten rows.
        """Prepare raw data for table display."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of DataProcessingUtils helper.
        data = [entry for entry in self.rawdata if isinstance(entry, dict)]  # Dict rows only.

        if self.sort_key:  # Optional sort.
            sort_key_str: str = self.sort_key  # Type narrowing
            data = sorted(data, key=lambda x: x.get(sort_key_str, ""))  # Sort by key.

        data = mh.DataProcessingUtils.flatten_nested_fields(data)  # Flatten nested fields.
        data = mh.DataProcessingUtils.escape_multiline(data)
        return data  # type: ignore[no-any-return]

    def _build_pretty_table(self, data: list[dict[str, Any]], fields: list[str]) -> Any:  # Build a PrettyTable.
        """Build PrettyTable from processed data."""
        table = PrettyTable()  # New table.
        table.field_names = fields  # Use the auto-derived field list as the table columns.
        table.valign = "t"  # Top-align cells.

        for item in tqdm(data, desc="Processing", unit="record"):
            row = [item.get(field, "") for field in table.field_names]  # Build a row.
            table.add_row(row)  # Add the row.

        return table  # Return the table.
