"""DatabaseSchemaUtils -- SQLite DDL builder for endpoint-driven persistence.

Extracted from MistHelper.py during initiative 1013 (Cat B, position 38).
Static-method utility class that centralizes CREATE TABLE + CREATE INDEX DDL
generation for the polyglot persistence layer. Dispatches by strategy type
(natural_pk / composite_pk / autoincrement) and appends the standard audit
timestamp columns to every generated table.

Direct imports cover stdlib only (inspect, logging, re, datetime). The
strategy catalog (``ENDPOINT_PRIMARY_KEY_STRATEGIES``) is imported directly
from ``src.refactors.endpoint_primary_key_strategies`` after initiative 1015
T-04 -- the previous ``importlib.import_module("MistHelper")`` bypass is no
longer necessary because the catalog lives in a leaf module with no circular
edge back into MistHelper. Callers continue to reach the class through the
``MistHelper.DatabaseSchemaUtils`` re-export alias.
"""

from __future__ import annotations  # WHY: PEP 604 unions for return types.

import inspect  # WHY: walk the call stack to infer the calling API function name.
import logging  # WHY: structured trace for schema-build lifecycle events.
import re  # WHY: sanitize SQL identifiers before interpolation into DDL.
from datetime import UTC, datetime  # WHY: preserve legacy timestamp-build side effect in build_create_table_sql.
from typing import Any  # WHY: strategy dict payloads are heterogeneous.

from src.refactors.endpoint_primary_key_strategies import (  # WHY: PK catalog leaf module (1015 T-04).
    ENDPOINT_PRIMARY_KEY_STRATEGIES,  # Direct import replaces the lazy `mh.ENDPOINT_PRIMARY_KEY_STRATEGIES` bypass.
)


class DatabaseSchemaUtils:  # Build SQLite DDL from data.
    """Centralized database schema utilities for SQLite operations.

    Groups all schema-related functions per the 5-Item Rule class organization.
    All methods are static to avoid unnecessary object instantiation.
    """

    @staticmethod
    def determine_api_function_name_from_context() -> str:  # Infer API name from the call stack.
        """Walk the call stack and return the first frame whose name looks like a Mist API call; else 'unknown'."""
        frame = inspect.currentframe()  # Start at the current frame.
        try:
            while frame:  # Walk up the stack.
                function_name = frame.f_code.co_name  # Name of this frame's function.
                if any(  # Match known API call patterns.
                    pattern in function_name
                    for pattern in ["getOrg", "listOrg", "searchOrg", "getSite", "listSite", "searchSite"]
                ):
                    logging.debug("Detected API function name from stack: %s", function_name)  # Trace detected name.
                    return function_name  # Use the detected API name.
                frame = frame.f_back  # Step to the caller frame.
        except Exception as error:  # Stack inspection failed.
            logging.debug("Error determining API function name: %s", error)  # Trace the inspection error.
        finally:
            del frame  # Break the reference cycle.
        return "unknown"  # Fallback when undetected.

    @staticmethod
    def get_endpoint_strategy(api_function_name: str, data_fields: list[str]) -> dict[str, Any]:  # Pick PK strategy.
        """Determine the appropriate database schema strategy for an API endpoint.

        Args:
            api_function_name (str): Name of the API function being called
            data_fields (list): List of field names in the data

        Returns:
            dict: Strategy configuration including primary key, indexes, and so on
        """
        # First check if we have a specific strategy for this endpoint
        if api_function_name in ENDPOINT_PRIMARY_KEY_STRATEGIES:  # Use a configured strategy.
            strategy = ENDPOINT_PRIMARY_KEY_STRATEGIES[api_function_name].copy()  # Copy to avoid mutation.
            logging.debug("Using configured strategy for %s: %s", api_function_name, strategy["type"])  # Trace pick.
            return strategy  # Return configured strategy.

        return DatabaseSchemaUtils._build_default_strategy(api_function_name, data_fields)  # Derive from data shape

    @staticmethod
    def _build_default_strategy(api_function_name: str, data_fields: list[str]) -> dict[str, Any]:  # Field-derived PK
        """Build a default PK strategy enhanced by the data's available fields (id + common index columns)."""
        strategy: dict[str, Any] = ENDPOINT_PRIMARY_KEY_STRATEGIES["default"].copy()  # Start from default template

        if "id" in data_fields:  # Data carries an 'id' -- use it as the unique key
            strategy["unique_constraints"] = ["id"]  # Enforce unique id.
            strategy["indexes"] = ["id"]  # Index id for lookups.
            logging.debug("Default strategy for %s: unique constraint on 'id'", api_function_name)  # Trace id keying

        common_index_fields = ["org_id", "site_id", "device_id", "timestamp", "mac", "serial"]  # Common index columns.
        for field_name in common_index_fields:  # Add indexes when present.
            if field_name in data_fields and field_name not in strategy["indexes"]:  # Avoid duplicate indexes.
                strategy["indexes"].append(field_name)  # Index this present field

        logging.debug("Using enhanced default strategy for %s: %s", api_function_name, strategy)  # Trace strategy.
        return strategy  # Return enhanced strategy.

    @staticmethod
    def _sanitize_table_name(name: str) -> str:
        """Sanitize a SQL table name; force a non-digit leading character to keep DDL valid."""
        safe = re.sub(r"[^a-zA-Z0-9_]", "_", name)  # Replace any non-alphanum/underscore with '_'
        if not safe or safe[0].isdigit():  # Empty or digit-led identifier is not valid SQL
            safe = f"table_{safe}"  # Prefix to ensure a valid identifier
        return safe  # Return the sanitized name

    @staticmethod
    def _sanitize_column(field_name: Any) -> str:
        """Sanitize a column identifier for safe inclusion in SQL DDL."""
        return re.sub(r"[^a-zA-Z0-9_]", "_", str(field_name))  # Replace any non-alphanum/underscore with '_'

    @staticmethod
    def _pk_aware_column_defs(fields: list[str], pk_fields: list[str]) -> list[str]:
        """Return TEXT column-def strings; columns named in pk_fields are flagged NOT NULL."""
        defs: list[str] = []  # Collect column definitions in field order
        for field_name in fields:  # Walk each input field name
            safe = DatabaseSchemaUtils._sanitize_column(field_name)  # Sanitize column for SQL safety
            if field_name in pk_fields:  # Primary-key columns require NOT NULL
                defs.append(f"{safe} TEXT NOT NULL")  # Required PK column
            else:
                defs.append(f"{safe} TEXT")  # Optional column
        return defs  # Return the column-def list

    @staticmethod
    def _plain_column_defs(fields: list[str]) -> list[str]:
        """Return TEXT column-def strings for every field (no PK distinction)."""
        return [
            f"{DatabaseSchemaUtils._sanitize_column(field_name)} TEXT" for field_name in fields
        ]  # Plain TEXT columns

    @staticmethod
    def _metadata_column_defs() -> list[str]:
        """Return the standard audit timestamp column definitions appended to every table."""
        return [
            "misthelper_created_time TEXT DEFAULT CURRENT_TIMESTAMP",  # Row-create timestamp
            "misthelper_updated_time TEXT DEFAULT CURRENT_TIMESTAMP",  # Row-update timestamp
        ]

    @staticmethod
    def _assemble_create_sql(safe_table_name: str, field_definitions: list[str], suffix: str) -> str:
        """Assemble the final CREATE TABLE statement from sanitized name, column defs, and suffix clauses."""
        sql_parts = [
            f"CREATE TABLE IF NOT EXISTS {safe_table_name} (",  # Begin the CREATE TABLE
            ", ".join(field_definitions),  # Join all column defs
            suffix,  # Strategy-specific suffix (PK or UNIQUE clauses)
            ")",  # Close the column list
        ]
        return "".join(sql_parts)  # Assemble the DDL string

    @staticmethod
    def _build_natural_pk_sql(safe_table_name: str, fields: list[str], strategy: dict[str, Any]) -> str:
        """Build CREATE TABLE DDL for a natural-key endpoint (stable UUID column)."""
        pk_fields = strategy["primary_key"]  # Natural primary key columns
        field_defs = DatabaseSchemaUtils._pk_aware_column_defs(fields, pk_fields)  # PK-aware column defs
        field_defs.extend(DatabaseSchemaUtils._metadata_column_defs())  # Append audit columns
        suffix = f", PRIMARY KEY ({', '.join(pk_fields)})"  # Compose the PK clause
        return DatabaseSchemaUtils._assemble_create_sql(safe_table_name, field_defs, suffix)  # Final DDL

    @staticmethod
    def _build_composite_pk_sql(safe_table_name: str, fields: list[str], strategy: dict[str, Any]) -> str:
        """Build CREATE TABLE DDL for a composite-key endpoint (only present columns become PK)."""
        pk_fields = strategy["primary_key"]  # Composite key columns
        field_defs = DatabaseSchemaUtils._pk_aware_column_defs(fields, pk_fields)  # PK-aware column defs
        field_defs.extend(DatabaseSchemaUtils._metadata_column_defs())  # Append audit columns
        available = [f for f in pk_fields if f in fields]  # Only key on present columns
        suffix = f", PRIMARY KEY ({', '.join(available)})" if available else ""  # Empty suffix when no key columns
        return DatabaseSchemaUtils._assemble_create_sql(safe_table_name, field_defs, suffix)  # Final DDL

    @staticmethod
    def _build_autoincrement_sql(safe_table_name: str, fields: list[str], strategy: dict[str, Any]) -> str:
        """Build CREATE TABLE DDL for an auto-increment-with-unique endpoint (surrogate id + UNIQUE cols)."""
        field_defs = ["misthelper_internal_id INTEGER PRIMARY KEY AUTOINCREMENT"]  # Surrogate key column first
        field_defs.extend(DatabaseSchemaUtils._plain_column_defs(fields))  # Plain TEXT columns
        field_defs.extend(DatabaseSchemaUtils._metadata_column_defs())  # Append audit columns
        unique_fields = [f for f in strategy["unique_constraints"] if f in fields]  # Constrain present columns only
        unique_suffix = "".join(
            f", UNIQUE({DatabaseSchemaUtils._sanitize_column(f)})" for f in unique_fields
        )  # Comma-separated UNIQUE clauses (empty when no unique fields)
        return DatabaseSchemaUtils._assemble_create_sql(safe_table_name, field_defs, unique_suffix)  # Final DDL

    @staticmethod
    def build_create_table_sql(
        table_name: str,
        fields: list[str],
        strategy: dict[str, Any],
    ) -> str:
        """Build the CREATE TABLE SQL for an endpoint, dispatching by strategy['type']."""
        datetime.now(UTC).isoformat()  # Preserve legacy timestamp-build side effect from prior implementation
        safe_table_name = DatabaseSchemaUtils._sanitize_table_name(table_name)  # Sanitize the table name
        builders = {
            "natural_pk": DatabaseSchemaUtils._build_natural_pk_sql,  # Stable-UUID branch builder
            "composite_pk": DatabaseSchemaUtils._build_composite_pk_sql,  # Time-series branch builder
        }
        builder = builders.get(strategy["type"], DatabaseSchemaUtils._build_autoincrement_sql)  # Auto-incr fallback
        create_sql = builder(safe_table_name, fields, strategy)  # Dispatch to the strategy-specific builder
        logging.debug("Generated CREATE TABLE SQL for %s: %s...", safe_table_name, create_sql[:100])  # Trace DDL
        return create_sql  # Return the CREATE TABLE

    @staticmethod
    def build_indexes_sql(table_name: str, fields: list[str], strategy: dict[str, Any]) -> list[str]:  # Build indexes.
        """Build CREATE INDEX IF NOT EXISTS statements for fields named in strategy['indexes'] that exist in fields."""
        safe_table_name = re.sub(r"[^a-zA-Z0-9_]", "_", table_name)  # Sanitize the table name.
        if not safe_table_name or safe_table_name[0].isdigit():  # Names cannot start with a digit.
            safe_table_name = f"table_{safe_table_name}"  # Prefix to make it valid.
        index_sqls = []  # Collect index statements.
        for field_name in strategy.get("indexes", []):  # One index per configured field.
            if field_name in fields:  # Only index present columns.
                safe_field = re.sub(r"[^a-zA-Z0-9_]", "_", str(field_name))  # Sanitize the column name.
                index_name = f"idx_{safe_table_name}_{safe_field}"  # Deterministic index name.
                index_sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {safe_table_name} ({safe_field})"  # index DDL.
                index_sqls.append(index_sql)  # Collect the statement.
        return index_sqls  # Return all index DDL.
