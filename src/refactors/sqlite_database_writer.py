"""SQLiteDatabaseWriter extracted from MistHelper.

Hybrid SQLite upsert writer that persists Mist API result rows into a local
SQLite database using natural business keys wherever possible and falling
back to auto-increment when the endpoint has no natural key.

Runtime dependencies (`DATABASE_PATH`, `DatabaseSchemaUtils`,
`DataProcessingUtils`) are still owned by MistHelper.py; they are resolved
lazily via `importlib.import_module` to keep the extracted module import-
graph flat and to preserve monkeypatch-friendly test hooks that address
`MistHelper.DATABASE_PATH` directly.
"""

from __future__ import annotations  # Enable postponed evaluation for forward-ref typing on 3.10+

import importlib  # Late-import MistHelper module to avoid circular src<->MistHelper dependency
import logging  # Structured action logging required by coding standards
import re  # Sanitise table and column names for SQL identifier positions
import sqlite3  # Direct SQLite driver for connect/execute/commit
from datetime import UTC, datetime  # UTC-aware timestamps for audit and log context
from pathlib import Path  # Filesystem-safe directory creation for the DB parent path
from types import SimpleNamespace  # Bundle runtime dependencies without coupling to a dataclass
from typing import Any  # Column values from the Mist API are heterogeneous


def _resolve_runtime_dependencies() -> SimpleNamespace:
    """Resolve MistHelper-owned runtime dependencies without static cross-module imports."""
    logging.info("Resolving SQLiteDatabaseWriter runtime dependencies from MistHelper")  # Log before import
    misthelper_module = importlib.import_module("MistHelper")  # Late import avoids circular dependency
    logging.debug("SQLiteDatabaseWriter runtime dependencies resolved successfully")  # Log after resolution
    return SimpleNamespace(
        DatabaseSchemaUtils=misthelper_module.DatabaseSchemaUtils,  # DDL builder + PK/index strategy picker
        DataProcessingUtils=misthelper_module.DataProcessingUtils,  # JSON flatten + escape helpers
        misthelper_module=misthelper_module,  # Retained so DATABASE_PATH lookups honour monkeypatch
    )


class SQLiteDatabaseWriter:  # Upsert records into SQLite.
    """Write list of dictionaries to SQLite database using hybrid primary key strategies.

    Eliminates artificial api_id fields and uses proper business keys from Mist API.
    Follows NASA/JPL coding standards with comprehensive logging and error handling.

    SECURITY: Parameterized queries prevent SQL injection

    Usage:
        SQLiteDatabaseWriter(data, table_name, api_function_name).write()
    """

    def __init__(
        self,
        data: list[dict[str, Any]],
        table_name: str,
        api_function_name: str | None = None,
    ) -> None:
        """Initialize writer with data, table name, and optional API function name."""
        logging.info(  # Log construction with row/table context for traceability
            "SQLiteDatabaseWriter init: rows=%s table=%s api_fn=%s",
            len(data) if data else 0,  # Guard against None while still capturing the count for logs
            table_name,  # Target table name
            api_function_name,  # Source API function (may be None -> resolved later)
        )
        self.data = data  # Rows to persist.
        self.table_name = table_name  # Destination table.
        self.api_function_name = api_function_name  # Source API for strategy.
        self.timestamp = datetime.now(UTC).isoformat()  # Write timestamp.
        self.processed_data: list[dict[str, Any]] = []  # Normalized rows.
        self.fields: list[str] = []  # Resolved column list.
        self.strategy: dict[str, Any] = {}  # Chosen PK/index strategy.
        self.connection: sqlite3.Connection | None = None  # Lazy DB connection.
        self.cursor: sqlite3.Cursor | None = None  # Lazy DB cursor.
        self._deps: SimpleNamespace = _resolve_runtime_dependencies()  # Late-bound MistHelper handles
        logging.debug("SQLiteDatabaseWriter init complete for table %s", table_name)  # Log after construction

    def _database_path(self) -> str:
        """Return the current DATABASE_PATH from MistHelper so monkeypatched values are honoured."""
        return str(self._deps.misthelper_module.DATABASE_PATH)  # Resolve at call-time, not import-time

    def write(self) -> bool:  # Run the full upsert pipeline.
        """Main entry point - orchestrates the database write operation."""
        self._log_entry()  # Log the write start.
        if not self._validate_inputs():  # Abort on invalid input.
            return False  # Nothing written.
        self._resolve_api_function_name()  # Infer API name if missing.
        if not self._ensure_database_directory():  # Abort if dir not writable.
            return False  # Nothing written.
        if not self._process_data():  # Abort on processing failure.
            return False  # Nothing written.
        if not self._determine_fields_and_strategy():  # Abort if schema undetermined.
            return False  # Abort: schema undetermined.
        return self._execute_database_operations()  # Run the DB writes.

    def _log_entry(self) -> None:  # Log write parameters.
        """Log entry point with input parameters."""
        row_count = len(self.data) if self.data else 0  # Count rows for the log.
        logging.debug(  # Trace the write entry.
            "ENTRY: SQLiteDatabaseWriter.write(data_rows=%s, table_name=%s, api_function_name=%s) at %s",
            row_count,
            self.table_name,
            self.api_function_name,
            self.timestamp,
        )

    def _validate_inputs(self) -> bool:  # Validate data and table name.
        """Validate data and table name inputs."""
        if not self._validate_data():  # Data must be valid.
            return False  # Reject bad data.
        return self._validate_table_name()  # Then validate table name.

    def _validate_data(self) -> bool:  # Ensure data is a non-empty list.
        """Validate that data is a non-empty list."""
        if not self.data:  # No rows to write.
            logging.warning(  # Warn that the writer was called with no rows to persist
                "No data provided to write to table %s at %s", self.table_name, self.timestamp
            )
            logging.debug("EXIT: SQLiteDatabaseWriter.write - no data to write")  # Trace early exit.
            return False  # Reject empty data.
        if not isinstance(self.data, list):  # Data must be a list.
            logging.error(  # Log a hard type mismatch so callers see the actual type name
                "Invalid data type: expected list, got %s at %s", type(self.data), self.timestamp
            )
            logging.debug("EXIT: SQLiteDatabaseWriter.write - invalid data type")  # Trace early exit.
            return False  # Reject wrong type.
        return True  # Data is valid.

    def _validate_table_name(self) -> bool:  # Ensure a usable table name.
        """Validate that table name is a non-empty string."""
        if not self.table_name or not isinstance(self.table_name, str):  # Name must be a non-empty str.
            logging.error("Invalid table name: %s at %s", self.table_name, self.timestamp)  # Log the bad name.
            logging.debug("EXIT: SQLiteDatabaseWriter.write - invalid table name")  # Trace early exit.
            return False  # Reject bad name.
        return True  # Name is valid.

    def _resolve_api_function_name(self) -> None:  # Backfill API name if missing.
        """Determine API function name from context if not provided."""
        if not self.api_function_name:  # Only when unset.
            # Infer the caller-frame API function name via MistHelper's existing utility
            self.api_function_name = self._deps.DatabaseSchemaUtils.determine_api_function_name_from_context()
        logging.debug(  # Trace the resolved name.
            "Processing %s rows for table %s using API function %s at %s",
            len(self.data),
            self.table_name,
            self.api_function_name,
            self.timestamp,
        )

    def _ensure_database_directory(self) -> bool:  # Create the DB directory.
        """Create database directory if it does not exist."""
        database_path = self._database_path()  # Resolve DATABASE_PATH at call-time for monkeypatch support
        db_dir_path = Path(database_path).parent  # pathlib gives a canonical parent-directory object
        if str(db_dir_path) == "" or db_dir_path.exists():  # Empty parent or already present.
            return True  # Directory ready.
        try:
            logging.info(  # Log before creating the directory to preserve action-order tracing
                "Creating database directory: %s at %s", db_dir_path, self.timestamp
            )
            db_dir_path.mkdir(parents=True, exist_ok=True)  # Create the directory (idempotent)
            logging.debug(  # Log after creation success
                "Database directory created: %s at %s", db_dir_path, self.timestamp
            )
            return True  # Directory ready.
        except OSError as error:  # Creation failed.
            logging.error(  # Log the OS error with context so operators can diagnose permissions
                "Failed to create database directory %s: %s at %s", db_dir_path, error, self.timestamp
            )
            logging.debug("EXIT: SQLiteDatabaseWriter.write - directory creation failed")  # Trace early exit.
            return False  # Cannot proceed without dir.

    def _process_data(self) -> bool:  # Normalize data for SQLite.
        """Process data to handle formatting for database storage."""
        try:
            self.processed_data = self._deps.DataProcessingUtils.escape_multiline(
                self.data
            )  # Sanitise multi-line values
            logging.debug("Successfully processed data for SQLite compatibility at %s", self.timestamp)  # Trace ok.
            return True  # Processing succeeded.
        except Exception as error:  # Processing failed.
            logging.error("Failed to process data: %s at %s", error, self.timestamp)  # Log the failure.
            logging.debug("EXIT: SQLiteDatabaseWriter.write - data processing failed")  # Trace early exit.
            return False  # Abort on failure.

    def _determine_fields_and_strategy(self) -> bool:  # Resolve columns and strategy.
        """Get all unique fields and determine primary key strategy."""
        try:
            self.fields = self._deps.DataProcessingUtils.get_unique_keys(self.processed_data)  # Collect all keys used
            if not self.fields:  # Need at least one field.
                logging.error(  # Log a hard failure when the row set carries no columns
                    "No fields found in data for table %s at %s", self.table_name, self.timestamp
                )
                logging.debug("EXIT: SQLiteDatabaseWriter.write - no fields")  # Trace early exit.
                return False  # Abort: no fields.
            api_func_name = self.api_function_name if self.api_function_name else ""  # Default empty name.
            self.strategy = self._deps.DatabaseSchemaUtils.get_endpoint_strategy(  # Pick the PK/index strategy
                api_func_name, self.fields
            )
            self._log_strategy_info()  # Log the chosen strategy.
            return True  # Fields and strategy ready.
        except Exception as error:  # Determination failed.
            logging.error("Failed to determine fields and strategy: %s at %s", error, self.timestamp)  # Log failure.
            logging.debug("EXIT: SQLiteDatabaseWriter.write - field determination failed")  # Trace early exit.
            return False  # Abort on failure.

    def _log_strategy_info(self) -> None:  # Log strategy and fields.
        """Log strategy selection details."""
        logging.info(  # Log the strategy summary.
            "Using hybrid SQLite strategy '%s' for table %s: %s",
            self.strategy["type"],
            self.table_name,
            self.strategy["description"],
        )
        logging.debug("Database fields determined: %s at %s", self.fields, self.timestamp)  # Trace the field list.
        logging.debug(  # Trace strategy details.
            "Endpoint %s mapped to %s strategy - eliminates need for artificial api_id fields",
            self.api_function_name,
            self.strategy["type"],
        )

    def _execute_database_operations(self) -> bool:  # Connect, create, insert, commit.
        """Execute database operations with comprehensive error handling."""
        try:
            self._connect_to_database()  # Open the DB connection.
            self._create_table_and_indexes()  # Ensure schema exists.
            insert_mode = self._determine_insert_mode()  # Pick insert/upsert mode.
            safe_fields = self._prepare_safe_fields()  # Sanitize column names.
            successful_inserts = self._insert_all_rows(insert_mode, safe_fields)  # Insert all rows.
            self._commit_and_verify(successful_inserts)  # Commit and verify counts.
            logging.debug("EXIT: SQLiteDatabaseWriter.write - success")  # Trace success.
            return True  # Write succeeded.
        except sqlite3.Error as error:  # Handle SQLite errors.
            self._handle_sqlite_error(error)  # Log and rollback.
            return False  # Write failed.
        except Exception as error:  # Handle unexpected errors.
            self._handle_unexpected_error(error)  # Log and rollback.
            return False  # Write failed.
        finally:
            self._close_connection()  # Always close the connection.

    def _connect_to_database(self) -> None:  # Open a SQLite connection.
        """Connect to SQLite database."""
        database_path = self._database_path()  # Resolve DATABASE_PATH at call-time for monkeypatch support
        logging.debug("Attempting to connect to database: %s at %s", database_path, self.timestamp)  # Trace connect.
        self.connection = sqlite3.connect(database_path)  # Open the database file.
        self.cursor = self.connection.cursor()  # Create a cursor.
        logging.info("Successfully connected to database: %s at %s", database_path, self.timestamp)  # Log connection.

    def _create_table_and_indexes(self) -> None:  # Create table then indexes.
        """Create table with strategy-appropriate schema and indexes."""
        assert (
            self.cursor is not None
        ), "Database cursor not initialized"  # nosec B101  # Defensive: ensure connect() succeeded
        self._create_schema_table()  # Delegate DDL creation to keep this function under STRUCT-LENGTH limit
        self._create_schema_indexes()  # Delegate index creation to keep this function under STRUCT-LENGTH limit

    def _create_schema_table(self) -> None:  # Extract table DDL to keep parent under 25 lines
        """Build and execute the CREATE TABLE DDL for the current strategy."""
        assert self.cursor is not None, "Database cursor not initialized"  # nosec B101
        # Build the CREATE TABLE SQL using the strategy (natural/composite/auto-increment)
        create_table_sql = self._deps.DatabaseSchemaUtils.build_create_table_sql(
            self.table_name, self.fields, self.strategy
        )
        self.cursor.execute(create_table_sql)  # Execute DDL to create or verify the table structure
        logging.debug(  # Trace the DDL.
            "Table %s created/verified with hybrid %s schema - using natural business keys from API",
            self.table_name,
            self.strategy["type"],
        )

    def _create_schema_indexes(self) -> None:  # Extract index DDL to keep parent under 25 lines
        """Build and execute the CREATE INDEX statements paired with the schema strategy."""
        assert self.cursor is not None, "Database cursor not initialized"  # nosec B101
        # Compute the CREATE INDEX DDL statements that pair with the chosen strategy
        index_sqls = self._deps.DatabaseSchemaUtils.build_indexes_sql(self.table_name, self.fields, self.strategy)
        for index_sql in index_sqls:  # Create each index.
            self.cursor.execute(index_sql)  # Execute the index DDL.
        if index_sqls:  # Only log when indexes exist.
            logging.debug(  # Trace index creation.
                "Created %s performance indexes for table %s with %s strategy",
                len(index_sqls),
                self.table_name,
                self.strategy["type"],
            )

    def _determine_insert_mode(self) -> str:  # Choose upsert vs insert.
        """Determine insert strategy based on schema type."""
        assert self.cursor is not None, "Database cursor not initialized"  # nosec B101
        if self.strategy["type"] in ["natural_pk", "composite_pk"]:  # Keyed tables upsert.
            logging.debug(  # Trace upsert mode.
                "Using REPLACE mode for %s strategy - enables efficient upsert operations with natural keys",
                self.strategy["type"],
            )
            return "INSERT OR REPLACE"  # Upsert on conflict.
        safe_table = self._get_safe_table_name()  # Sanitize for the clear.
        self.cursor.execute(f"DELETE FROM {safe_table}")  # nosec B608
        logging.debug("Cleared existing data and using INSERT mode for auto-increment fallback strategy")  # fallback.
        return "INSERT"  # Plain insert (cleared table).

    def _get_safe_table_name(self) -> str:  # Sanitize the table name.
        """Get sanitized table name safe for SQL."""
        safe_table_name = re.sub(r"[^a-zA-Z0-9_]", "_", self.table_name)  # Strip unsafe chars.
        if not safe_table_name or safe_table_name[0].isdigit():  # Cannot start with a digit.
            safe_table_name = f"table_{safe_table_name}"  # Prefix to make valid.
        return safe_table_name  # Return the safe name.

    def _prepare_safe_fields(self) -> list[str]:  # Sanitize and add audit cols.
        """Prepare sanitized field names with metadata columns."""
        safe_fields = [re.sub(r"[^a-zA-Z0-9_]", "_", str(field)) for field in self.fields]  # Sanitize field names.
        safe_fields.extend(["misthelper_created_time", "misthelper_updated_time"])  # Append audit timestamp cols.
        return safe_fields  # Return the column list.

    def _insert_all_rows(self, insert_mode: str, safe_fields: list[str]) -> int:  # Insert every processed row.
        """Insert all data rows and return count of successful inserts."""
        current_time = datetime.now(UTC).isoformat()  # One timestamp per batch.
        successful_inserts = 0  # Count successes.
        for idx, row in enumerate(self.processed_data):  # Insert each row.
            if self._insert_single_row(idx, row, insert_mode, safe_fields, current_time):  # Count successful inserts.
                successful_inserts += 1  # Tally the success.
        return successful_inserts  # Return the success count.

    def _insert_single_row(  # Insert one row safely.
        self,
        idx: int,
        row: dict[str, Any],
        insert_mode: str,
        safe_fields: list[str],
        current_time: str,
    ) -> bool:
        """Insert a single row into the database."""
        assert self.cursor is not None, "Database cursor not initialized"  # nosec B101
        try:
            values = self._prepare_row_values(row, current_time)  # Build the value tuple.
            insert_sql = self._build_insert_sql(insert_mode, safe_fields, len(values))  # Build the INSERT SQL.
            self.cursor.execute(insert_sql, values)  # Execute the insert.
            self._log_sample_insert(idx, insert_mode)  # Trace first few rows for diagnostics
            return True  # Row inserted.
        except Exception as error:  # Per-row failure.
            self._log_row_failure(idx, error)  # Emit structured per-row failure trace
            return False  # Row failed.

    def _log_sample_insert(self, idx: int, insert_mode: str) -> None:  # Extract to keep parent under 25 lines
        """Log the first three inserts for diagnostics without spamming the log for large batches."""
        if idx < 3:  # Sample-log the first rows.
            logging.debug(  # Trace a sample insert.
                "Row %s inserted into %s using %s at %s",
                idx,
                self.table_name,
                insert_mode,
                self.timestamp,
            )

    def _log_row_failure(self, idx: int, error: Exception) -> None:  # Extract to keep parent under 25 lines
        """Log a per-row insertion failure so the batch can continue while retaining triage context."""
        logging.error(  # Log the per-row failure with the row index for triage
            "Failed to insert row %s into %s: %s at %s",
            idx,
            self.table_name,
            error,
            self.timestamp,
        )

    def _prepare_row_values(self, row: dict[str, Any], current_time: str) -> list[str]:  # Stringify row values.
        """Prepare values for a single row including metadata."""
        values = []  # Collect string values.
        for field_name in self.fields:  # In field order.
            value = row.get(field_name, "")  # Default missing fields.
            values.append("" if value is None else str(value))  # Stringify; None -> empty.
        values.extend([current_time, current_time])  # Append audit timestamps.
        return values  # Return the value list.

    def _build_insert_sql(  # Compose INSERT.
        self,
        insert_mode: str,
        safe_fields: list[str],
        value_count: int,
    ) -> str:
        """Build parameterized INSERT SQL statement."""
        placeholders = ", ".join(["?"] * value_count)  # Bind placeholders.
        safe_table_name = self._get_safe_table_name()  # Sanitize the table name.
        return (  # nosec B608 - identifiers are sanitised above; values are bound via placeholders
            f"{insert_mode} INTO {safe_table_name} ({', '.join(safe_fields)}) VALUES ({placeholders})"
        )

    def _commit_and_verify(self, successful_inserts: int) -> None:  # Commit then verify row count.
        """Commit transaction and verify row count."""
        assert self.connection is not None, "Database connection not initialized"  # nosec B101
        assert self.cursor is not None, "Database cursor not initialized"  # nosec B101
        self.connection.commit()  # Persist the transaction.
        logging.info(  # Log inserts committed.
            "Successfully wrote %s/%s rows to table %s in database %s using %s strategy at %s",
            successful_inserts,
            len(self.processed_data),
            self.table_name,
            self._database_path(),
            self.strategy["type"],
            self.timestamp,
        )
        safe_table_name = self._get_safe_table_name()  # Sanitize for the count query.
        self.cursor.execute(f"SELECT COUNT(*) FROM {safe_table_name}")  # nosec B608
        row_count = self.cursor.fetchone()[0]  # Read the verified count.
        logging.info(  # Log the verified count.
            "Database verification: %s rows confirmed in table %s at %s",
            row_count,
            self.table_name,
            self.timestamp,
        )

    def _handle_sqlite_error(self, error: sqlite3.Error) -> None:  # Log and roll back SQLite errors.
        """Handle SQLite-specific errors with rollback."""
        logging.error(  # Log the SQLite driver error verbatim with context
            "SQLite error when writing to %s: %s at %s", self.table_name, error, self.timestamp
        )
        self._rollback_transaction()  # Undo partial writes.
        logging.debug("EXIT: SQLiteDatabaseWriter.write - SQLite error")  # Trace early exit.

    def _handle_unexpected_error(self, error: Exception) -> None:  # Log and roll back other errors.
        """Handle unexpected errors with rollback."""
        logging.error(  # Log any non-SQLite exception with context for post-mortem triage
            "Unexpected error when writing to table %s: %s at %s",
            self.table_name,
            error,
            self.timestamp,
        )
        self._rollback_transaction()  # Undo partial writes.
        logging.debug("EXIT: SQLiteDatabaseWriter.write - unexpected error")  # Trace early exit.

    def _rollback_transaction(self) -> None:  # Roll back the transaction.
        """Rollback transaction if connection exists."""
        if not self.connection:  # Nothing to roll back.
            return  # No connection open.
        try:
            self.connection.rollback()  # Undo uncommitted writes.
            logging.debug("Transaction rolled back for table %s at %s", self.table_name, self.timestamp)  # Trace undo.
        except Exception as rollback_error:  # Rollback itself failed.
            logging.error("Failed to rollback transaction: %s at %s", rollback_error, self.timestamp)  # rollback fail.

    def _close_connection(self) -> None:  # Close the DB connection.
        """Close database connection (safety-critical: resource cleanup)."""
        if not self.connection:  # Nothing to close.
            return  # No connection open.
        try:
            self.connection.close()  # Release the connection.
            logging.debug("Database connection closed for table %s at %s", self.table_name, self.timestamp)  # closed.
        except Exception as error:  # Close failed.
            logging.error("Failed to close database connection: %s at %s", error, self.timestamp)  # log close error.


__all__ = ["SQLiteDatabaseWriter"]  # Public surface of this module - the extracted class only
