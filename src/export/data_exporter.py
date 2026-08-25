"""Multi-backend data exporter (CSV / SQLite / polyglot DB) extracted from MistHelper.

Canonical body of ``DataExporter`` per issue #1015 T-08 (Cat E fresh extraction).
The MistHelper module retains only a bare re-export for backward compatibility.
"""

from __future__ import annotations

import csv
import importlib
import logging
import os
import time
from typing import Any

from src.data.data_processing_utils import DataProcessingUtils
from src.dataclasses.export_backend_options import ExportBackendOptions
from src.dataclasses.polyglot_write_outcome import PolyglotWriteOutcome
from src.refactors.endpoint_primary_key_strategies import ENDPOINT_PRIMARY_KEY_STRATEGIES
from src.refactors.sqlite_database_writer import SQLiteDatabaseWriter

# Optional polyglot DB layer — mirror MistHelper's try/except so the exporter
# still works when the optional dependency is missing.
try:  # pragma: no cover - import guard mirrors MistHelper
    from src.db import DatabaseConfig, configure_db_logging, polyglot_hosts_unreachable
    from src.db.router import DatabaseRouter

    DB_LAYER_AVAILABLE = True
except Exception:  # pragma: no cover - graceful degradation when DB layer missing
    DatabaseConfig = None  # type: ignore[assignment, misc]
    configure_db_logging = None  # type: ignore[assignment]
    polyglot_hosts_unreachable = None  # type: ignore[assignment]
    DatabaseRouter = None  # type: ignore[assignment, misc]
    DB_LAYER_AVAILABLE = False

# Cause identifiers for a polyglot write that reached no database (issue #2009).
SKIP_NO_API_FUNCTION_NAME = "no_api_function_name"  # The call site sent no API function name.
SKIP_DB_LAYER_MISSING = "db_layer_missing"  # The optional database layer is not installed.
SKIP_STANDALONE_MODE = "standalone_mode"  # MistHelper runs in CSV and SQLite mode.
SKIP_ROUTER_UNAVAILABLE = "router_unavailable"  # The router could not be built from the settings.
SKIP_ROUTER_FILE_FALLBACK = "router_file_fallback"  # The router returned success after a file fallback.
SKIP_ROUTER_WRITE_FAILED = "router_write_failed"  # The router reported a failed write.

# One plain-language message for each cause. A junior NOC engineer reads these lines.
POLYGLOT_SKIP_MESSAGES: dict[str, str] = {
    SKIP_NO_API_FUNCTION_NAME: (
        "Skipped the polyglot database write, because the caller sent no API function name. Fix the call site."
    ),
    SKIP_DB_LAYER_MISSING: (
        "Skipped the polyglot database write, because the database layer is not installed. "
        "Install the database requirements."
    ),
    SKIP_STANDALONE_MODE: (
        "Skipped the polyglot database write, because MistHelper runs in standalone mode. "
        "MISTHELPER_STANDALONE has three states. The value true skips the database. The value false uses the "
        "database. An unset value probes the hosts, and MistHelper skips the database when no host answers."
    ),
    SKIP_ROUTER_UNAVAILABLE: (
        "Skipped the polyglot database write, because the database router did not build. "
        "Read the connection settings ARANGO_HOST and REDIS_HOST in the .env file."
    ),
    SKIP_ROUTER_FILE_FALLBACK: (
        "The polyglot write reached no database. The router wrote the file and returned success. "
        "Check that ArangoDB and Redis answer."
    ),
    SKIP_ROUTER_WRITE_FAILED: (
        "The polyglot write failed inside the database router. The file output holds the only copy."
    ),
}


class DataExporter:  # Multi-backend export facade.
    """Handles data export operations for CSV and Redis/SQLite output formats.

    Centralizes all data saving logic that was previously scattered across functions.
    Uses static methods to avoid unnecessary object instantiation.
    """

    _router: DatabaseRouter | None = None  # type: ignore[name-defined]
    _router_initialized: bool = False  # One-shot guard so the lazy router init runs exactly once per process.
    _last_snapshot_times: dict[str, float] = {}  # Per-table last-snapshot epoch times used to throttle snapshots.

    @staticmethod
    def _polyglot_db_layer_available() -> bool:
        """True when the optional polyglot DB layer was imported and exposes every name we use."""
        if not DB_LAYER_AVAILABLE:  # Optional dependency not installed
            return False
        if DatabaseConfig is None:  # Module loaded but config class missing — treat as unavailable
            return False
        if configure_db_logging is None:  # Logger setup missing
            return False
        return DatabaseRouter is not None  # Final required symbol

    @classmethod
    def _build_polyglot_router(cls) -> None:
        """Construct DatabaseRouter from env (called only when the polyglot layer is available)."""
        try:  # Router construction reads env and opens connections — guard against any startup failure
            assert configure_db_logging is not None  # nosec B101 - _polyglot_db_layer_available proved this symbol.
            assert DatabaseConfig is not None  # nosec B101 - _polyglot_db_layer_available proved this symbol.
            assert DatabaseRouter is not None  # nosec B101 - _polyglot_db_layer_available proved this symbol.
            configure_db_logging()  # Route DB layer's logger into MistHelper logging before first use
            config = DatabaseConfig.from_env()  # Build connection settings from .env so secrets stay out of code
            cls._router = DatabaseRouter(  # Cache the shared router on the class for every later export call
                config,  # Pass env-derived connection/configuration object
                strategies=ENDPOINT_PRIMARY_KEY_STRATEGIES,  # Per-endpoint primary-key upsert strategies
            )
            logging.info("Polyglot DatabaseRouter initialized")  # Confirm successful backend startup
        except Exception as error:  # Never let optional-backend startup crash a core CSV/SQLite export
            logging.warning("DatabaseRouter init failed, CSV/SQLite only: %s", error)  # Surface degraded mode
            cls._router = None  # Force safe CSV/SQLite path when router could not be constructed

    @classmethod
    def _init_router(cls) -> None:  # Lazy polyglot router init.
        """Initialize polyglot DatabaseRouter once (lazy, idempotent)."""
        if cls._router_initialized:  # Skip when a prior call already attempted init
            return
        cls._router_initialized = True  # Latch the guard before fallible work
        if not DataExporter._polyglot_db_layer_available():  # Optional polyglot layer not installed
            logging.debug("Polyglot DB layer not installed - CSV/SQLite only")
            return
        cls._build_polyglot_router()  # Construct router (catches startup failures internally)

    @staticmethod
    def _dispatch_format_write(
        data: list[dict[str, Any]],
        filename_or_table: str,
        output_format: str,
        fieldnames: list[str] | None,
        api_function_name: str | None,
    ) -> bool:
        """Pick CSV vs SQLite write path. Return success flag. Catches and logs write exceptions."""
        try:
            if output_format == "csv":  # CSV branch
                return DataExporter._write_csv_format(data, filename_or_table, fieldnames=fieldnames)
            return DataExporter._write_sqlite_format(data, filename_or_table, api_function_name)  # SQLite branch
        except Exception as error:  # Never crash on write
            logging.error("Failed to write data to %s in %s format: %s", filename_or_table, output_format, error)
            return False

    @staticmethod
    def write_with_format_selection(  # Public export entry point.
        data: list[dict[str, Any]],
        filename_or_table: str,
        api_function_name: str | None = None,
        fieldnames: list[str] | None = None,
        backend_options: ExportBackendOptions | None = None,
    ) -> bool:
        """Write data to CSV or SQLite per OUTPUT_FORMAT (or backend_options.format_override). Mirror to polyglot DB."""
        opts = backend_options if backend_options is not None else ExportBackendOptions()  # Resolve defaults
        mh = importlib.import_module("MistHelper")  # OUTPUT_FORMAT is a mutable module-level global in MistHelper.
        output_format = opts.format_override if opts.format_override else mh.OUTPUT_FORMAT  # Override or global
        logging.debug(
            "DataExporter.write_with_format_selection: rows=%s, target=%s, format=%s, api_func=%s",
            len(data) if data else 0,
            filename_or_table,
            output_format,
            api_function_name,
        )
        if not DataExporter._validate_write_inputs(data, filename_or_table, output_format):  # Pre-validate
            return False
        csv_ok = DataExporter._dispatch_format_write(
            data, filename_or_table, output_format, fieldnames, api_function_name
        )  # Run the chosen writer
        outcome = DataExporter._route_to_polyglot(
            data, api_function_name, raw_data=opts.raw_data
        )  # Mirror to the polyglot database and keep the true result.
        DataExporter._warn_when_database_write_dropped(outcome, api_function_name, filename_or_table)  # Report a loss.
        return csv_ok  # Return the primary result

    @staticmethod
    def _warn_when_database_write_dropped(
        outcome: PolyglotWriteOutcome,
        api_function_name: str | None,
        filename_or_table: str,
    ) -> None:
        """Warn when the caller asked for a database write and no row reached a database."""
        if api_function_name is None:  # The caller asked for a file write only, so no database write was lost.
            return
        if outcome.written:  # The rows reached a database, so the caller has nothing to fix.
            return
        logging.warning(  # Warning level, because the operator sees a file and an empty database.
            "The database write was dropped for %s. Cause: %s. The file output %s holds the only copy.",
            api_function_name,  # Name the endpoint that lost the write.
            outcome.skip_reason,  # Name the cause identifier so a log search finds every case.
            filename_or_table,  # Name the file that still holds the rows.
        )

    _standalone_logged = False  # One-shot standalone log guard.
    _standalone_probe: bool | None = None  # Cached polyglot reachability verdict for the life of the process.

    @staticmethod
    def _standalone_override() -> bool | None:
        """Return the forced verdict from MISTHELPER_STANDALONE, or None when the operator set no override.

        The variable has three states. The value ``true`` skips the database. The
        value ``false`` uses the database. An unset value returns None here, and
        the caller then probes the hosts.
        """
        standalone_env = os.getenv("MISTHELPER_STANDALONE", "").lower()  # Read the override env.
        if standalone_env == "true":  # Explicit standalone request.
            return True  # Forced standalone.
        if standalone_env == "false":  # Forced non-standalone.
            return False  # Not standalone.
        return None  # No override, so the caller must probe the hosts.

    @classmethod
    def _polyglot_hosts_silent(cls) -> bool:
        """Return True when no configured polyglot host answers. The probe runs one time for each process."""
        if cls._standalone_probe is not None:  # A prior call already paid the probe cost.
            return cls._standalone_probe
        if not DataExporter._polyglot_db_layer_available():  # No DB layer means no host to probe.
            cls._standalone_probe = True  # Cache the verdict so the check stays cheap.
            return True
        logging.debug("Probing the polyglot database hosts")  # Log before the network probe.
        assert polyglot_hosts_unreachable is not None  # nosec B101 - _polyglot_db_layer_available proved the import.
        cls._standalone_probe = polyglot_hosts_unreachable()  # Ask the db package for one TCP verdict.
        logging.debug("Polyglot host probe: unreachable=%s", cls._standalone_probe)  # Log the verdict.
        return cls._standalone_probe

    @classmethod
    def _is_standalone_mode(cls) -> bool:  # Decide whether the polyglot write must be skipped.
        """Return True when MistHelper must write CSV and SQLite only.

        The decision follows the reachability of the configured hosts, not the
        container boundary. A workstation that reaches ArangoDB and Redis writes
        to them.
        """
        override = cls._standalone_override()  # Honor an explicit operator decision first.
        if override is not None:  # The operator named the mode.
            return override
        if not cls._polyglot_hosts_silent():  # At least one backend answers.
            return False  # Run the polyglot write, inside or outside a container.
        if not cls._standalone_logged:  # Emit the degraded-mode warning one time.
            logging.warning(
                "Polyglot database hosts do not answer. MistHelper writes CSV and SQLite only. "
                "Set ARANGO_HOST and REDIS_HOST to reach the databases."
            )  # Make the dropped polyglot write visible in the log.
            cls._standalone_logged = True  # Latch the one-shot warning.
        return True  # No backend answers, so stay in CSV and SQLite mode.

    @staticmethod
    def _polyglot_skip_reason(api_function_name: str | None) -> str | None:
        """Return the cause that blocks the polyglot write, or None when the write can run.

        Each cause needs a different answer from the operator, so each cause has
        its own identifier. See ``POLYGLOT_SKIP_MESSAGES`` for the plain-language text.
        """
        if not api_function_name:  # The call site named no endpoint, so the router cannot pick a strategy.
            return SKIP_NO_API_FUNCTION_NAME
        if not DB_LAYER_AVAILABLE:  # The optional database package failed to import at module load.
            return SKIP_DB_LAYER_MISSING
        if DataExporter._is_standalone_mode():  # The operator or the host probe selected CSV and SQLite only.
            return SKIP_STANDALONE_MODE
        DataExporter._init_router()  # Build the router one time, because the first write pays the setup cost.
        if DataExporter._router is None:  # The router construction failed, so no connection exists.
            return SKIP_ROUTER_UNAVAILABLE
        return None  # Every check passed, so the polyglot write can run.

    @staticmethod
    def _log_polyglot_skip(reason: str, api_function_name: str | None) -> None:
        """Write one warning that names the cause of a dropped polyglot write."""
        logging.warning(  # Warning level, because the operator lost a database write.
            "%s Target: %s.",
            POLYGLOT_SKIP_MESSAGES[reason],  # The plain-language cause for a junior NOC engineer.
            api_function_name or "unnamed call site",  # Name the endpoint so the log points at the call.
        )

    @staticmethod
    def _outcome_from_write_result(result: Any, api_function_name: str) -> PolyglotWriteOutcome:
        """Turn a router result into a truthful outcome. The router returns success after a file fallback."""
        records_written = int(getattr(result, "records_written", 0) or 0)  # Rows the router says it stored.
        records_failed = int(getattr(result, "records_failed", 0) or 0)  # Rows the router says it lost.
        backend = getattr(result, "backend", None)  # Backend label, such as arangodb or csv_only.
        reason: str | None = None  # Start with no cause, because the write may have reached a database.
        if not getattr(result, "success", False):  # The router reported a failed write.
            reason = SKIP_ROUTER_WRITE_FAILED
        elif records_written <= 0:  # Success with zero rows means the file fallback ran.
            reason = SKIP_ROUTER_FILE_FALLBACK
        if reason is not None:  # The rows reached no database, so name the cause.
            DataExporter._log_polyglot_skip(reason, api_function_name)  # Make the loss visible in the log.
            return PolyglotWriteOutcome(False, reason, records_written, records_failed, backend)
        logging.debug("Polyglot write stored %s rows in %s", records_written, backend)  # Log the result after.
        return PolyglotWriteOutcome(True, None, records_written, records_failed, backend)  # Report the true result.

    @staticmethod
    def _perform_polyglot_write(payload: list[dict[str, Any]], api_function_name: str) -> PolyglotWriteOutcome:
        """Issue the router write call and return a truthful outcome. Never raises."""
        logging.info("Writing %s rows to the polyglot database for %s", len(payload), api_function_name)
        try:
            assert DataExporter._router is not None  # nosec B101 - The caller checked _polyglot_skip_reason first.
            result = DataExporter._router.write(payload, api_function_name)  # Write to the polyglot database.
            logging.info(  # Log the router answer before the exporter judges it.
                "Polyglot write: backend=%s, written=%s, failed=%s",
                result.backend,
                result.records_written,
                result.records_failed,
            )
            return DataExporter._outcome_from_write_result(result, api_function_name)  # Judge the answer.
        except Exception as error:  # Never let the polyglot path break the CSV path.
            logging.warning("Polyglot write failed (CSV preserved): %s", error)  # Report the raised error.
            DataExporter._log_polyglot_skip(SKIP_ROUTER_WRITE_FAILED, api_function_name)  # Name the cause.
            return PolyglotWriteOutcome(False, SKIP_ROUTER_WRITE_FAILED, 0, len(payload), None)  # Truthful result.

    @staticmethod
    def _route_to_polyglot(  # Mirror writes to polyglot DB.
        data: list[dict[str, Any]],
        api_function_name: str | None,
        raw_data: list[dict[str, Any]] | None = None,
    ) -> PolyglotWriteOutcome:
        """Send data to the polyglot backends and report whether the rows reached a database."""
        skip_reason = DataExporter._polyglot_skip_reason(api_function_name)  # Find the cause that blocks the write.
        if skip_reason is not None:  # One of the four skip causes applies.
            DataExporter._log_polyglot_skip(skip_reason, api_function_name)  # Name the cause in the log.
            return PolyglotWriteOutcome(False, skip_reason)  # Tell the caller that no row reached a database.
        polyglot_data = raw_data or data  # Prefer the raw payload when the caller supplied it.
        assert api_function_name is not None  # nosec B101 - _polyglot_skip_reason returns a cause for a None name.
        return DataExporter._perform_polyglot_write(polyglot_data, api_function_name)  # Issue the write.

    @classmethod
    def _check_periodic_snapshot(  # Throttle periodic snapshots.
        cls,
        api_function_name: str,
        threshold_seconds: float = 3600.0,
    ) -> bool:
        """Check if enough time elapsed since last snapshot for this API.

        Returns True if a snapshot should be taken (threshold exceeded).
        Updates the timestamp when returning True.
        """
        now = time.time()  # Current time.
        last_time = cls._last_snapshot_times.get(api_function_name, 0.0)  # Last snapshot time.
        if (now - last_time) < threshold_seconds:  # Too soon for another.
            return False  # Skip this snapshot.
        cls._last_snapshot_times[api_function_name] = now  # Record snapshot time.
        return True  # Allow the snapshot.

    @staticmethod
    def _validate_write_inputs(data: list[dict[str, Any]], filename_or_table: str, output_format: str) -> bool:
        """Validate inputs for write operation. Returns True if valid."""
        if not data:  # No rows to write.
            logging.warning("No data provided for output to %s", filename_or_table)  # warn no data.
            return False  # Reject empty data.

        if output_format not in ["csv", "sqlite"]:  # Only csv/sqlite allowed.
            logging.error("Invalid output format: %s. Must be 'csv' or 'sqlite'", output_format)  # bad format.
            return False  # Reject bad format.

        return True  # Inputs valid.

    @staticmethod
    def _write_csv_format(  # Write rows to a CSV file.
        data: list[dict[str, Any]],
        filename_or_table: str,
        fieldnames: list[str] | None = None,
    ) -> bool:
        """Write data to CSV format.  Pass fieldnames to preserve a specific column order."""
        csv_filename = filename_or_table if filename_or_table.endswith(".csv") else f"{filename_or_table}.csv"
        logging.info("Writing %s rows to CSV file: %s", len(data), csv_filename)  # Log CSV write.
        DataExporter.write_to_csv(data, csv_filename, fieldnames=fieldnames)  # Thread explicit column order through
        return True  # CSV written.

    @staticmethod
    def _write_sqlite_format(data: list[dict[str, Any]], filename_or_table: str, api_function_name: str | None) -> bool:
        """Write data to SQLite format. Returns True on success."""
        table_name = filename_or_table[:-4] if filename_or_table.endswith(".csv") else filename_or_table
        logging.debug(  # Trace SQLite write.
            "SQLite write: table=%s, api_function=%s, strategy lookup initiated", table_name, api_function_name
        )
        logging.info("Writing %s rows to SQLite table: %s", len(data), table_name)  # Log SQLite write.
        return SQLiteDatabaseWriter(data, table_name, api_function_name).write()  # Run the writer.

    @staticmethod
    def write_to_csv(
        data: list[dict[str, Any]],
        csv_file: str,
        fieldnames: list[str] | None = None,
    ) -> None:
        """Write rows to a CSV file, escaping multiline values and honoring an optional column order.

        Args:
            data: Rows to write.
            csv_file: Destination filename (placed in data/ if no directory is given).
            fieldnames: Optional explicit column order. Defaults to sorted unique keys.
        """
        logging.debug("ENTRY: DataExporter.write_to_csv(data_rows=%s, csv_file=%s)", len(data) if data else 0, csv_file)
        if not data:  # No rows to write -- short-circuit and trace the early exit
            logging.warning("No data provided to write to %s", csv_file)  # Inform caller of empty payload
            logging.debug("EXIT: DataExporter.write_to_csv - no data to write")  # Trace early exit
            return  # Nothing to do
        csv_file_path = DataExporter._resolve_csv_path(csv_file)  # Place bare filenames under data/
        logging.debug("Preparing to write %s rows to %s...", len(data), csv_file_path)  # Trace write prep
        escaped_data = DataProcessingUtils.escape_multiline(data)  # type: ignore[no-untyped-call]
        fields = DataExporter._resolve_csv_fields(escaped_data, fieldnames)  # Final column order for the CSV
        logging.debug("CSV fields determined: %s", fields)  # Trace fields
        DataExporter._write_csv_with_exception_handling(csv_file_path, escaped_data, fields)  # Open + write rows
        logging.info("File I/O: Successfully wrote %s rows to %s", len(escaped_data), csv_file_path)  # Log success
        logging.debug("EXIT: DataExporter.write_to_csv - success")  # Trace exit

    @staticmethod
    def _resolve_csv_path(csv_file: str) -> str:
        """Return the on-disk path for csv_file, placing bare filenames under data/."""
        data_dir = "data"  # Confine bare filenames to data/ for container persistence
        os.makedirs(data_dir, exist_ok=True)  # Ensure data/ exists before any write
        if not os.path.dirname(csv_file):  # Caller passed a bare filename (no directory component)
            resolved = os.path.join(data_dir, csv_file)  # Place under data/
        else:
            resolved = csv_file  # Caller-provided full path is honored verbatim
        logging.debug("Resolved CSV destination path: %s", resolved)  # Trace path resolution
        return resolved  # Final destination

    @staticmethod
    def _resolve_csv_fields(escaped_data: list[dict[str, Any]], fieldnames: list[str] | None) -> list[str]:
        """Return the CSV column order. Honor caller-supplied fieldnames or fall back to sorted unique keys."""
        if fieldnames is not None:  # Caller supplied an explicit column order -- preserve it verbatim
            logging.debug("Using caller-supplied fieldnames for CSV column order")  # Trace explicit ordering
            return fieldnames  # Use as-is
        derived = DataProcessingUtils.get_unique_keys(escaped_data)  # type: ignore[no-untyped-call]
        logging.debug("Derived %s unique CSV columns from data", len(derived))  # Trace derived ordering
        return derived  # Sorted unique keys

    @staticmethod
    def _emit_rows(writer: csv.DictWriter, escaped_data: list[dict[str, Any]], fields: list[str]) -> None:
        """Write every row in escaped_data through writer. Debug-log the first three for diagnostics."""
        for idx, row in enumerate(escaped_data):  # Walk each row in input order
            writer.writerow({field_name: row.get(field_name, "") for field_name in fields})  # Emit in col order
            if idx < 3:  # Trace the first three rows to aid post-mortem debugging
                logging.debug("Row %s written: %s", idx, row)  # Per-row trace

    @staticmethod
    def _write_csv_open_and_emit(
        csv_file_path: str,
        escaped_data: list[dict[str, Any]],
        fields: list[str],
    ) -> None:
        """Open the destination CSV and write header + rows. Lets I/O errors propagate to the caller."""
        logging.debug("File I/O: Attempting to open %s for writing", csv_file_path)  # Trace pre-open
        with open(csv_file_path, "w", newline="", encoding="utf-8") as file_handle:  # Open CSV for writing
            writer = csv.DictWriter(file_handle, fieldnames=fields)  # Dict-based CSV writer
            writer.writeheader()  # Write the header row first
            logging.debug("File I/O: Successfully wrote CSV header to %s", csv_file_path)  # Trace header write
            DataExporter._emit_rows(writer, escaped_data, fields)  # Stream rows through the writer

    @staticmethod
    def _write_csv_with_exception_handling(
        csv_file_path: str,
        escaped_data: list[dict[str, Any]],
        fields: list[str],
    ) -> None:
        """Run the CSV write under structured error handling -- map I/O failures to user-friendly diagnostics."""
        try:  # Wrap the write to translate I/O failures into the legacy diagnostic surface
            DataExporter._write_csv_open_and_emit(csv_file_path, escaped_data, fields)  # Open + emit
        except PermissionError as perm_error:  # File locked or write denied
            logging.error("File I/O: Permission denied when writing to %s: %s", csv_file_path, perm_error)
            logging.warning("! Cannot write to %s. Is it open in another program?", csv_file_path)  # User-facing hint
            logging.debug("EXIT: DataExporter.write_to_csv - permission error")  # Trace exit on perm denial
            raise  # Propagate to the caller
        except OSError as os_error:  # OS-level write failure (disk full, path invalid, and so on)
            logging.error("File I/O: OS error when writing to %s: %s", csv_file_path, os_error)  # Log OS failure
            logging.debug("EXIT: DataExporter.write_to_csv - OS error")  # Trace OS error exit
            raise  # Propagate to the caller
        except Exception as unexpected_error:  # Any other unexpected failure
            logging.error(
                "File I/O: Unexpected error when writing to %s: %s", csv_file_path, unexpected_error
            )  # Log unexpected
            logging.debug("EXIT: DataExporter.write_to_csv - unexpected error")  # Trace unexpected exit
            raise  # Propagate to the caller

    # save_data_to_output removed per issue #431 (ARCH-DELEGATE). All call
    # sites now invoke DataExporter.write_with_format_selection(data, filename,
    # api_function_name=...) directly -- it is the canonical implementation
    # and accepts the identical (data, filename, api_function_name=) form.

    @staticmethod
    def export_with_processing(data, filename, sort_key=None, api_function_name=None):  # Process then export records.
        """Flatten, optionally sort, and export records via the selected backend.

        Returns the number of records exported (0 when there is no data or the export fails).
        """
        if not data:  # Nothing to export.
            logging.warning("No data to export for %s", filename)  # warn no data.
            return 0  # Zero exported.

        raw_data = [entry for entry in data if isinstance(entry, dict)]  # Keep dict rows only (defensive).
        raw_data = DataExporter._sort_records(raw_data, sort_key)  # Optionally sort by the requested key.

        processed_data = DataProcessingUtils.flatten_nested_fields(raw_data)  # Flatten nested fields for CSV/SQLite.
        processed_data = DataProcessingUtils.escape_multiline(processed_data)  # type: ignore[no-untyped-call]

        success = DataExporter.write_with_format_selection(  # Write flattened to CSV/SQLite, raw to polyglot
            processed_data,
            filename,
            api_function_name=api_function_name,
            backend_options=ExportBackendOptions(raw_data=raw_data),  # Issue #470: raw_data bundled.
        )

        return DataExporter._finalize_export(success, len(processed_data), filename)  # Log outcome, return count

    @staticmethod
    def _sort_records(raw_data: list[dict[str, Any]], sort_key: str | None) -> list[dict[str, Any]]:  # Optional sort
        """Return raw_data sorted by sort_key (missing values sort as ''), or unchanged when no key given."""
        if not sort_key:  # No sort requested
            return raw_data  # Preserve original order
        sorted_data = sorted(raw_data, key=lambda entry: entry.get(sort_key, ""))  # Sort by key (missing -> '')
        logging.debug("Data sorted by key: %s", sort_key)  # Trace the sort.
        return sorted_data  # Sorted rows

    @staticmethod
    def _finalize_export(success: bool, processed_count: int, filename: str) -> int:  # Log + return export outcome
        """Log the export result and return the processed-row count on success, 0 on failure."""
        if success:  # Export succeeded.
            logging.info("Exported %s records to %s", processed_count, filename)  # Log export count.
            return processed_count  # Return rows exported.
        logging.error("Failed to export data to %s", filename)  # log export failure.
        return 0  # Zero exported.
