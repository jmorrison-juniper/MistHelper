"""Device events 52-week exporter extracted from MistHelper.py."""

from __future__ import annotations  # WHY: PEP 563 postponed annotations for forward Any typing

import csv  # WHY: CSV writer for streaming append + initial batch output paths
import os  # WHY: File paths, checkpoint existence, directory creation
import time  # WHY: Exponential backoff sleeps between retry attempts
from dataclasses import dataclass  # WHY: Frozen slotted bundles keep exporter + stream params compact
from typing import Any  # WHY: mistapi response / logger / utility types are dynamic

from src.dataclasses.export_backend_options import (
    ExportBackendOptions,  # WHY: Issue #470 backend overrides for write_with_format_selection
)

# Module-level constants - centralize magic numbers/strings so branch logic stays low-complexity
_DATA_DIR = "data"  # WHY: Output directory for CSV and checkpoint artifacts
_CSV_FILENAME = "OrgDeviceEvents_52w.csv"  # WHY: Fixed output filename preserved from original
_TABLE_NAME = "OrgDeviceEvents_52w"  # WHY: SQLite table + logical export identifier
_CHECKPOINT_TEMPLATE = "OrgDeviceEvents_52w.{org_id}.checkpoint"  # WHY: Per-org checkpoint file name
_API_FUNCTION_NAME = "searchOrgDeviceEvents"  # WHY: API endpoint name recorded in backend metadata
_DEVICE_TYPE_ALL = "all"  # WHY: Query all device types in a single sweep
_ENCODING = "utf-8"  # WHY: Unicode-safe encoding for CSV + checkpoint I/O
_SQLITE_FORMAT = "sqlite"  # WHY: Output format sentinel controlling write branch
_DEFAULT_LIMIT = 1000  # WHY: Page size for searchOrgDeviceEvents pagination
_DEFAULT_DURATION = "52w"  # WHY: 52-week fixed export window
_DEFAULT_PRELOAD_PAGES = 3  # WHY: Preload N pages so CSV header covers all seen fields
_DEFAULT_RETRIES = 3  # WHY: Attempt count for transient API failures
_DEFAULT_BACKOFF_SECONDS = 1.0  # WHY: Base backoff before exponential growth
_TOKEN_KEYS: tuple[str, ...] = ("search_after", "next")  # WHY: Continuation token keys probed in order
_RESULT_KEYS: tuple[str, ...] = ("results", "data")  # WHY: Result payload keys probed in order

# Log message templates - defined once so callers stay readable at 120 cols with WHY anchors
_LOG_START = "Exporting all org device events from the last 52 weeks..."  # WHY: Header line at export start
_LOG_NO_ORG = "No org_id available. Exiting."  # WHY: Early-exit reason when org context missing
_LOG_EMPTY = "No device events found for the 52-week period."  # WHY: Empty-result branch info line
_LOG_HEADER = "Using CSV header with %s fields for OrgDeviceEvents_52w.csv"  # WHY: Header shape trace
_LOG_RESUME = "Resuming OrgDeviceEvents_52w from checkpoint token: %s"  # WHY: Checkpoint resume trace
_LOG_CHECKPOINT_READ_FAIL = "Could not read checkpoint file %s: %s"  # WHY: Non-fatal read failure warn
_LOG_CHECKPOINT_WRITE_FAIL = "Could not write checkpoint file %s: %s"  # WHY: Non-fatal write failure warn
_LOG_CHECKPOINT_REMOVE_FAIL = "Could not remove checkpoint file after completion"  # WHY: Debug-only removal miss
_LOG_ATTEMPT_FAIL = "Attempt %s/%s to fetch page failed: %s"  # WHY: Retry attempt trace
_LOG_RETRY_WAIT = "Waiting %ss before retrying"  # WHY: Backoff sleep trace
_LOG_DONE_SQLITE = (  # WHY: Completion message when SQLite backend was selected
    "All org device events (52w) exported to SQLite table OrgDeviceEvents_52w (DB: %s)"
)
_LOG_DONE_CSV = "All org device events (52w) exported to %s."  # WHY: Completion message for CSV backend


@dataclass(frozen=True, slots=True)  # WHY: Frozen + slots keeps the bundle immutable and compact
class _StreamRequest:  # WHY: Immutable transport of streaming loop parameters
    """Immutable bundle of parameters threaded through the streaming loop."""

    next_token: str | None  # WHY: Continuation token seeded from preload phase
    duration: str  # WHY: Query window (matches preload window for consistency)
    limit: int  # WHY: Page size shared with preload phase
    csv_file: str  # WHY: Destination CSV path for append writes
    header_fields: list[str]  # WHY: Frozen CSV header schema computed during preload
    checkpoint_file: str  # WHY: Checkpoint destination for resume support


@dataclass(frozen=True, slots=True)  # WHY: Frozen + slots keeps the exporter immutable and compact
class DeviceEvents52wExporter:  # WHY: Public streaming exporter bound to a single org context
    """Stream and export org device events across 52 weeks with checkpointing."""

    apisession: Any  # WHY: Authenticated mistapi session handle
    mistapi: Any  # WHY: mistapi module reference for API call dispatch
    org_id: str  # WHY: Target organization identifier
    data_processing_utils: Any  # WHY: Flatten/escape/key-derivation helpers
    data_exporter: Any  # WHY: Backend writer supporting CSV and SQLite formats
    output_format: str  # WHY: Selected output format ("sqlite" enables backend path)
    database_path: str  # WHY: SQLite database location reported in completion log
    logger: Any  # WHY: Structured logger for info/debug/warning output

    def export(self) -> None:  # WHY: Public entrypoint orchestrating the 52w export
        """Run export with preload, checkpoint resume, and streaming append."""
        self.logger.info(_LOG_START)  # WHY: Announce start of 52-week export sweep
        if not self.org_id:  # WHY: Guard - no org context means nothing to export
            self.logger.error(_LOG_NO_ORG)  # WHY: Log operator-visible reason before returning
            return  # WHY: Abort export when no org context is available
        csv_file, checkpoint_file = self._paths()  # WHY: Resolve stable output paths
        search_after = self._read_checkpoint(checkpoint_file)  # WHY: Resume token if present
        buffered_rows, next_token = self._preload_rows(  # WHY: Preload rows to derive stable header
            _DEFAULT_LIMIT,
            _DEFAULT_DURATION,
            _DEFAULT_PRELOAD_PAGES,
            search_after,
        )
        if not buffered_rows:  # WHY: Empty result branch - emit empty output and exit
            return self._handle_empty_result()  # WHY: Empty branch short-circuits streaming
        header_fields = self._build_header(buffered_rows)  # WHY: Freeze schema before streaming loop
        self._write_initial_batch(csv_file, buffered_rows, header_fields)  # WHY: Write preload rows once
        self._write_checkpoint(checkpoint_file, next_token)  # WHY: Persist resume token after batch
        self._finalize_streaming(next_token, csv_file, header_fields, checkpoint_file)  # WHY: Delegate tail

    def _finalize_streaming(  # WHY: Tail-of-export helper keeps export() under length limit
        self,
        next_token: str | None,
        csv_file: str,
        header_fields: list[str],
        checkpoint_file: str,
    ) -> None:
        """Stream remaining pages, clean checkpoint, and emit completion log."""
        self._stream_remaining_pages(
            _StreamRequest(  # WHY: Bundled params keep signature <=5 wide
                next_token=next_token,
                duration=_DEFAULT_DURATION,
                limit=_DEFAULT_LIMIT,
                csv_file=csv_file,
                header_fields=header_fields,
                checkpoint_file=checkpoint_file,
            )
        )
        self._remove_checkpoint(checkpoint_file)  # WHY: Best-effort cleanup on successful completion
        self._log_completion(csv_file)  # WHY: Final operator-facing status line

    def _handle_empty_result(self) -> None:  # WHY: Empty-result branch emits zero-row output
        """Log empty branch and emit an empty output file via the backend."""
        self.logger.info(_LOG_EMPTY)  # WHY: Announce empty-result branch for operator visibility
        self.data_exporter.write_with_format_selection([], _CSV_FILENAME)  # WHY: Emit zero-row output

    def _build_header(self, buffered_rows: list[dict[str, Any]]) -> list[str]:  # WHY: Header discovery
        """Derive stable CSV header from buffered preload rows."""
        header_fields = self.data_processing_utils.get_unique_keys(buffered_rows)  # WHY: Union of keys
        self.logger.info(_LOG_HEADER, len(header_fields))  # WHY: Trace derived header size
        return header_fields  # WHY: Return frozen schema used by initial + append writers

    def _paths(self) -> tuple[str, str]:  # WHY: Resolve portable CSV + checkpoint paths
        """Return output CSV and checkpoint file paths."""
        os.makedirs(_DATA_DIR, exist_ok=True)  # WHY: Ensure data directory exists before writes
        checkpoint_name = _CHECKPOINT_TEMPLATE.format(org_id=self.org_id)  # WHY: Per-org checkpoint file
        checkpoint_file = os.path.join(_DATA_DIR, checkpoint_name)  # WHY: Portable absolute path
        csv_file = os.path.join(_DATA_DIR, _CSV_FILENAME)  # WHY: Portable CSV destination path
        return csv_file, checkpoint_file  # WHY: Tuple of both paths for unpack at caller

    def _read_checkpoint(self, checkpoint_file: str) -> str | None:  # WHY: Optional resume-token loader
        """Read checkpoint token if present."""
        if not os.path.exists(checkpoint_file):  # WHY: Guard - no checkpoint means fresh run
            return None  # WHY: Absent checkpoint file means no resume token
        try:
            with open(checkpoint_file, encoding=_ENCODING) as handle:  # WHY: Read persisted resume token
                token = handle.read().strip()  # WHY: Strip trailing newline written by _write_checkpoint
        except Exception as error:  # noqa: BLE001  # WHY: Any read failure downgrades to non-fatal warn
            self.logger.warning(_LOG_CHECKPOINT_READ_FAIL, checkpoint_file, error)  # WHY: Trace failure
            return None  # WHY: Read failure treated as no checkpoint (fresh run)
        if not token:  # WHY: Empty file behaves like missing checkpoint
            return None  # WHY: Empty token behaves like no resume token
        self.logger.info(_LOG_RESUME, token)  # WHY: Trace which token we are resuming from
        return token  # WHY: Return resume token for continuation of pagination

    def _fetch_page(self, token: str | None, duration: str, limit: int) -> Any:  # WHY: Single-page fetcher
        """Fetch one page of org device events."""
        kwargs = self._fetch_kwargs(token, duration, limit)  # WHY: Table-driven kwargs keep CC low
        return self.mistapi.api.v1.orgs.devices.searchOrgDeviceEvents(  # WHY: Single call site
            self.apisession,
            self.org_id,
            **kwargs,
        )

    @staticmethod
    def _fetch_kwargs(token: str | None, duration: str, limit: int) -> dict[str, Any]:  # WHY: Kwargs builder
        """Build kwargs for the API call, adding search_after only when a token is present."""
        kwargs: dict[str, Any] = {  # WHY: Base kwargs shared by first and continuation fetches
            "device_type": _DEVICE_TYPE_ALL,
            "limit": limit,
            "duration": duration,
        }
        if token:  # WHY: Continuation fetch adds resume token to kwargs
            kwargs["search_after"] = token  # WHY: Attach resume token so backend continues pagination
        return kwargs  # WHY: Return finalized kwargs dict for the mistapi call

    def _normalize_page(self, response: Any) -> tuple[list[dict[str, Any]], str | None]:  # WHY: Payload normalizer
        """Normalize response payload to results list and continuation token."""
        page_data = getattr(response, "data", None)  # WHY: Extract payload from mistapi response object
        if not page_data:  # WHY: Guard - empty payload short-circuits to empty tuple
            return [], None  # WHY: Empty payload yields no rows and no token
        if isinstance(page_data, list):  # WHY: List payload has no continuation token
            return page_data, None  # WHY: Raw list is already the results with no token
        if isinstance(page_data, dict):  # WHY: Dict payload uses table-driven key probes
            return self._extract_from_dict(page_data)  # WHY: Table probes drive dict extraction
        return [], None  # WHY: Unknown payload shape defaults to empty tuple

    @staticmethod
    def _extract_from_dict(page_data: dict[str, Any]) -> tuple[list[dict[str, Any]], str | None]:  # WHY: Dict probe
        """Probe dict payload for results and continuation token using module constant tables."""
        results = _first_present(page_data, _RESULT_KEYS, default=[])  # WHY: Table-driven results probe
        next_token = _first_present(page_data, _TOKEN_KEYS, default=None)  # WHY: Table-driven token probe
        return results, next_token  # WHY: Return (rows, token) tuple for caller unpack

    def _preload_rows(  # WHY: Bounded preload phase to derive stable CSV header
        self,
        limit: int,
        duration: str,
        preload_pages: int,
        search_after: str | None,
    ) -> tuple[list[dict[str, Any]], str | None]:
        """Preload initial pages to compute a stable export header."""
        buffered_rows: list[dict[str, Any]] = []  # WHY: Accumulator for preload page rows
        next_token: str | None = None  # WHY: Last-seen continuation token returned to caller
        for _ in range(preload_pages):  # WHY: Bounded preload window (limits header discovery cost)
            response = self._fetch_page(search_after, duration, limit)  # WHY: Fetch one page
            results, next_token = self._normalize_page(response)  # WHY: Normalize to (rows, token)
            if not results:  # WHY: Empty page ends preload early
                break  # WHY: No more rows means preload window is exhausted
            buffered_rows.extend(self._process_rows(results))  # WHY: Flatten + escape then buffer
            if not next_token:  # WHY: No continuation token ends preload
                break  # WHY: No token means backend has no more pages
            search_after = next_token  # WHY: Advance to next page for header discovery
        return buffered_rows, next_token  # WHY: Return buffered rows plus last-seen token

    def _process_rows(self, results: list[dict[str, Any]]) -> list[dict[str, Any]]:  # WHY: Row normalizer
        """Flatten nested fields and escape multi-line values for CSV/SQLite output."""
        processed = self.data_processing_utils.flatten_nested_fields(results)  # WHY: Flatten first
        return self.data_processing_utils.escape_multiline(processed)  # WHY: Then escape newlines

    def _fetch_with_retries(  # WHY: Retry wrapper with exponential backoff for transient errors
        self,
        token: str,
        duration: str,
        limit: int,
        retries: int = _DEFAULT_RETRIES,
        backoff: float = _DEFAULT_BACKOFF_SECONDS,
    ) -> Any:
        """Fetch a page with retry and exponential backoff."""
        last_error: Exception | None = None  # WHY: Preserve final exception for re-raise
        for attempt in range(retries):  # WHY: Bounded retry loop with exponential backoff
            try:
                return self._fetch_page(token, duration, limit)  # WHY: Happy-path returns immediately
            except Exception as error:  # noqa: BLE001  # WHY: Preserve blanket-except for compatibility
                last_error = error  # WHY: Track for terminal re-raise
                self.logger.warning(_LOG_ATTEMPT_FAIL, attempt + 1, retries, error)  # WHY: Trace attempt
                self._sleep_before_retry(attempt, retries, backoff)  # WHY: Backoff isolated in helper
        if last_error is not None:  # WHY: Re-raise last observed error to caller
            raise last_error  # WHY: Propagate original exception with its stack context
        raise RuntimeError("All retries failed with no exception captured")  # WHY: Defensive fallback

    def _sleep_before_retry(self, attempt: int, retries: int, backoff: float) -> None:  # WHY: Backoff helper
        """Sleep an exponentially growing interval unless this was the final attempt."""
        if attempt >= retries - 1:  # WHY: Final attempt does not sleep
            return  # WHY: Skip sleeping after the last attempt - caller will re-raise
        sleep_time = backoff * (2**attempt)  # WHY: Exponential backoff (1x, 2x, 4x, ...)
        self.logger.debug(_LOG_RETRY_WAIT, sleep_time)  # WHY: Trace planned wait
        time.sleep(sleep_time)  # WHY: Actual delay before next attempt

    def _write_initial_batch(  # WHY: First-batch writer picks CSV-truncate or SQLite backend
        self,
        csv_file: str,
        rows: list[dict[str, Any]],
        header_fields: list[str],
    ) -> None:
        """Write initial preload rows to destination output."""
        if self.output_format == _SQLITE_FORMAT:  # WHY: SQLite branch dispatches to backend writer
            self.data_exporter.write_with_format_selection(  # WHY: Backend picks SQLite via options
                rows,
                _TABLE_NAME,
                api_function_name=_API_FUNCTION_NAME,
                backend_options=ExportBackendOptions(format_override=_SQLITE_FORMAT),  # WHY: #470
            )
            return  # WHY: SQLite branch fully handled - skip CSV writer
        with open(csv_file, "w", newline="", encoding=_ENCODING) as handle:  # WHY: Fresh CSV file
            writer = csv.DictWriter(handle, fieldnames=header_fields)  # WHY: Fixed schema for consistency
            writer.writeheader()  # WHY: Emit header row once
            _write_rows(writer, rows, header_fields)  # WHY: Shared row-writing helper

    def _append_rows(  # WHY: Continuation writer appends CSV rows or dispatches to SQLite backend
        self,
        csv_file: str,
        rows: list[dict[str, Any]],
        header_fields: list[str],
    ) -> None:
        """Append normalized rows to destination output."""
        if self.output_format == _SQLITE_FORMAT:  # WHY: SQLite branch dispatches to backend writer
            self.data_exporter.write_with_format_selection(  # WHY: Backend picks SQLite via options
                rows,
                _TABLE_NAME,
                api_function_name=_API_FUNCTION_NAME,
                backend_options=ExportBackendOptions(format_override=_SQLITE_FORMAT),  # WHY: #470
            )
            return  # WHY: SQLite branch fully handled - skip CSV append
        with open(csv_file, "a", newline="", encoding=_ENCODING) as handle:  # WHY: Append to CSV
            writer = csv.DictWriter(handle, fieldnames=header_fields)  # WHY: Reuse frozen schema
            _write_rows(writer, rows, header_fields)  # WHY: Shared row-writing helper

    def _stream_remaining_pages(self, request: _StreamRequest) -> None:  # WHY: Post-preload streaming loop
        """Continue exporting pages until no continuation token remains."""
        next_token = request.next_token  # WHY: Local mutable copy - request stays frozen
        while next_token:  # WHY: Loop until API stops returning continuation tokens
            response = self._fetch_with_retries(next_token, request.duration, request.limit)  # WHY: Retry
            results, next_token = self._normalize_page(response)  # WHY: Normalize to (rows, token)
            if not results:  # WHY: Empty page terminates streaming
                break  # WHY: Empty page signals end of pagination
            processed = self._process_rows(results)  # WHY: Flatten + escape rows before write
            self._append_rows(request.csv_file, processed, request.header_fields)  # WHY: Append batch
            self._write_checkpoint(request.checkpoint_file, next_token)  # WHY: Persist resume point

    def _write_checkpoint(self, checkpoint_file: str, token: str | None) -> None:  # WHY: Resume-token persist
        """Persist continuation token checkpoint for resume support."""
        if not token:  # WHY: Guard - nothing to persist without a token
            return  # WHY: Skip persistence when no continuation token exists
        try:
            with open(checkpoint_file, "w", encoding=_ENCODING) as handle:  # WHY: Truncate + write token
                handle.write(str(token))  # WHY: Coerce token to string for portability
        except Exception as error:  # noqa: BLE001  # WHY: Preserve blanket-except for compatibility
            self.logger.warning(_LOG_CHECKPOINT_WRITE_FAIL, checkpoint_file, error)  # WHY: Non-fatal warn

    def _remove_checkpoint(self, checkpoint_file: str) -> None:  # WHY: Best-effort checkpoint cleanup
        """Best-effort removal of checkpoint after successful completion."""
        try:
            if os.path.exists(checkpoint_file):  # WHY: Guard - avoid FileNotFoundError from race
                os.remove(checkpoint_file)  # WHY: Cleanup so next run starts fresh
        except Exception:  # noqa: BLE001  # WHY: Preserve blanket-except for compatibility
            self.logger.debug(_LOG_CHECKPOINT_REMOVE_FAIL)  # WHY: Debug-only breadcrumb

    def _log_completion(self, csv_file: str) -> None:  # WHY: Emit final completion status per backend
        """Log completion message according to active output format."""
        if self.output_format == _SQLITE_FORMAT:  # WHY: SQLite branch reports DB path
            self.logger.info(_LOG_DONE_SQLITE, self.database_path)  # WHY: DB-oriented completion message
            return  # WHY: SQLite branch fully logged - skip CSV completion line
        self.logger.info(_LOG_DONE_CSV, csv_file)  # WHY: CSV branch reports output file path


def _first_present(payload: dict[str, Any], keys: tuple[str, ...], default: Any) -> Any:  # WHY: Table probe helper
    """Return the first truthy value from ``payload`` for the given ``keys`` (else ``default``)."""
    for key in keys:  # WHY: Table-driven probe keeps callers CC=1
        value = payload.get(key)  # WHY: dict.get avoids KeyError on missing keys
        if value:  # WHY: Truthy check treats empty list/None as absent
            return value  # WHY: First truthy match short-circuits the probe
    return default  # WHY: Fallback when no key was present with a truthy value


def _write_rows(  # WHY: CSV row writer restricted to the frozen header schema
    writer: csv.DictWriter,
    rows: list[dict[str, Any]],
    header_fields: list[str],
) -> None:
    """Write ``rows`` through ``writer`` restricted to ``header_fields`` (missing keys blank)."""
    for row in rows:  # WHY: Restrict each row to the frozen schema so DictWriter never sees extras
        writer.writerow({key: row.get(key, "") for key in header_fields})  # WHY: Blank for missing
