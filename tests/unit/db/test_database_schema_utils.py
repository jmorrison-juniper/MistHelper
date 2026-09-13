"""Tests for DatabaseSchemaUtils -- SQLite DDL builder for endpoint-driven persistence.

Why:
    Covers 100% of ``src/db/database_schema_utils.py``: sanitization helpers,
    strategy dispatch (natural_pk / composite_pk / autoincrement fallback),
    stack-walking API function detection, and CREATE INDEX generation. These
    tests un-omit the module for the tranche-11 slice of initiative #878.
"""

from __future__ import annotations

import logging

import pytest

from src.db.database_schema_utils import DatabaseSchemaUtils
from src.refactors.endpoint_primary_key_strategies import ENDPOINT_PRIMARY_KEY_STRATEGIES


class TestDetermineApiFunctionNameFromContext:
    """Verify the stack walker returns a matching API function name or 'unknown'."""

    def test_returns_unknown_when_no_api_frame_on_stack(self) -> None:
        """No caller name matches the known API prefixes -> 'unknown'."""
        result = DatabaseSchemaUtils.determine_api_function_name_from_context()
        assert result == "unknown"

    def test_detects_getOrg_prefix_in_calling_frame(self) -> None:
        """A frame named ``getOrgSomething`` should surface directly."""

        def getOrgInventory() -> str:
            return DatabaseSchemaUtils.determine_api_function_name_from_context()

        assert getOrgInventory() == "getOrgInventory"

    def test_detects_listSite_prefix_in_calling_frame(self) -> None:
        """A frame named ``listSiteWebhooks`` should surface directly."""

        def listSiteWebhooks() -> str:
            return DatabaseSchemaUtils.determine_api_function_name_from_context()

        assert listSiteWebhooks() == "listSiteWebhooks"

    def test_detects_searchOrg_prefix_via_intermediate_frame(self) -> None:
        """The walker climbs multiple frames until it finds a matching prefix."""

        def intermediate() -> str:
            return DatabaseSchemaUtils.determine_api_function_name_from_context()

        def searchOrgClients() -> str:
            return intermediate()

        assert searchOrgClients() == "searchOrgClients"

    def test_handles_stack_inspection_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """When frame introspection raises, the try/except returns the 'unknown' fallback."""
        import src.db.database_schema_utils as module

        class _ExplodingFrame:
            """Frame stand-in whose f_code access raises inside the walker loop."""

            @property
            def f_code(self) -> object:
                raise RuntimeError("frame introspection failed")

        monkeypatch.setattr(module.inspect, "currentframe", lambda: _ExplodingFrame())
        assert DatabaseSchemaUtils.determine_api_function_name_from_context() == "unknown"


class TestGetEndpointStrategy:
    """Cover the configured-strategy hit path and the default-derivation path."""

    def test_returns_configured_strategy_copy_when_present(self) -> None:
        """When ``api_function_name`` is in the catalog, a copy is returned."""
        # Pick any known configured key so we do not depend on a specific fixture entry.
        known_key = next(k for k in ENDPOINT_PRIMARY_KEY_STRATEGIES if k != "default")
        strategy = DatabaseSchemaUtils.get_endpoint_strategy(known_key, [])
        assert strategy["type"] == ENDPOINT_PRIMARY_KEY_STRATEGIES[known_key]["type"]
        # Mutating the returned dict must not corrupt the catalog.
        strategy["_probe"] = True
        assert "_probe" not in ENDPOINT_PRIMARY_KEY_STRATEGIES[known_key]

    def test_falls_back_to_default_strategy_for_unknown_endpoint(self) -> None:
        """Unknown endpoint routes through ``_build_default_strategy``."""
        result = DatabaseSchemaUtils.get_endpoint_strategy("noSuchEndpoint", ["id", "org_id"])
        assert result["type"] == ENDPOINT_PRIMARY_KEY_STRATEGIES["default"]["type"]
        assert "id" in result["indexes"]
        assert "org_id" in result["indexes"]


class TestBuildDefaultStrategy:
    """Directly exercise ``_build_default_strategy`` corner cases."""

    def test_marks_id_as_unique_when_present(self) -> None:
        """The 'id' field, when present, becomes a unique constraint and index."""
        result = DatabaseSchemaUtils._build_default_strategy("fn", ["id", "site_id"])
        assert result["unique_constraints"] == ["id"]
        assert "id" in result["indexes"]
        assert "site_id" in result["indexes"]

    def test_does_not_add_id_constraint_when_absent(self) -> None:
        """No 'id' field -> unique_constraints stays as the template default (empty)."""
        result = DatabaseSchemaUtils._build_default_strategy("fn", ["mac", "timestamp"])
        assert result["unique_constraints"] == []
        assert "mac" in result["indexes"]
        assert "timestamp" in result["indexes"]

    def test_does_not_duplicate_indexes_already_present(self) -> None:
        """Fields already in strategy['indexes'] are not appended twice."""
        # Pre-warm by exercising once so any prior mutation of the default copy is neutralized.
        result = DatabaseSchemaUtils._build_default_strategy("fn", ["org_id", "org_id"])
        # 'org_id' appears once in data_fields deduped view but the outer loop only walks common_index_fields once.
        assert result["indexes"].count("org_id") == 1


class TestSanitizeHelpers:
    """Cover ``_sanitize_table_name``, ``_sanitize_column``, and column-def helpers."""

    def test_sanitize_table_name_replaces_illegal_chars(self) -> None:
        """Non-alphanumeric characters are replaced with underscores."""
        assert DatabaseSchemaUtils._sanitize_table_name("my-table.name!") == "my_table_name_"

    def test_sanitize_table_name_prefixes_digit_leading_identifier(self) -> None:
        """Names starting with a digit gain a 'table_' prefix."""
        assert DatabaseSchemaUtils._sanitize_table_name("123abc") == "table_123abc"

    def test_sanitize_table_name_handles_empty_input(self) -> None:
        """Empty string becomes 'table_'."""
        assert DatabaseSchemaUtils._sanitize_table_name("") == "table_"

    def test_sanitize_table_name_leaves_valid_identifier_unchanged(self) -> None:
        """Fully valid identifiers pass through untouched."""
        assert DatabaseSchemaUtils._sanitize_table_name("clean_name_42") == "clean_name_42"

    def test_sanitize_column_replaces_illegal_chars(self) -> None:
        """Column sanitization mirrors table sanitization rules."""
        assert DatabaseSchemaUtils._sanitize_column("col-name.foo") == "col_name_foo"

    def test_sanitize_column_coerces_non_string_input(self) -> None:
        """Non-string field names are stringified first."""
        assert DatabaseSchemaUtils._sanitize_column(123) == "123"

    def test_pk_aware_column_defs_flags_pk_columns_not_null(self) -> None:
        """PK-listed columns get ``NOT NULL``; others get plain ``TEXT``."""
        defs = DatabaseSchemaUtils._pk_aware_column_defs(["id", "name"], ["id"])
        assert "id TEXT NOT NULL" in defs
        assert "name TEXT" in defs

    def test_plain_column_defs_returns_all_text(self) -> None:
        """All columns render as plain ``TEXT``."""
        defs = DatabaseSchemaUtils._plain_column_defs(["a", "b-c"])
        assert defs == ["a TEXT", "b_c TEXT"]

    def test_metadata_column_defs_returns_expected_pair(self) -> None:
        """Standard audit columns match the documented shape."""
        defs = DatabaseSchemaUtils._metadata_column_defs()
        assert defs == [
            "misthelper_created_time TEXT DEFAULT CURRENT_TIMESTAMP",
            "misthelper_updated_time TEXT DEFAULT CURRENT_TIMESTAMP",
        ]

    def test_assemble_create_sql_joins_parts_correctly(self) -> None:
        """Statement joins the sanitized name, columns, and suffix cleanly."""
        sql = DatabaseSchemaUtils._assemble_create_sql("t", ["a TEXT", "b TEXT"], ", PRIMARY KEY (a)")
        assert sql == "CREATE TABLE IF NOT EXISTS t (a TEXT, b TEXT, PRIMARY KEY (a))"


class TestBuildNaturalPkSql:
    """Exercise the natural-key DDL builder directly."""

    def test_emits_primary_key_clause_and_not_null_on_key_column(self) -> None:
        """Natural-key columns get ``NOT NULL`` and a trailing ``PRIMARY KEY`` clause."""
        strategy = {"type": "natural_pk", "primary_key": ["id"], "indexes": []}
        sql = DatabaseSchemaUtils._build_natural_pk_sql("t", ["id", "name"], strategy)
        assert "id TEXT NOT NULL" in sql
        assert "name TEXT" in sql
        assert "PRIMARY KEY (id)" in sql
        assert "misthelper_created_time" in sql


class TestBuildCompositePkSql:
    """Exercise the composite-key DDL builder including the missing-key edge case."""

    def test_emits_composite_primary_key_when_all_columns_present(self) -> None:
        """All PK columns present -> a full ``PRIMARY KEY (...)`` clause."""
        strategy = {"type": "composite_pk", "primary_key": ["org_id", "timestamp"], "indexes": []}
        sql = DatabaseSchemaUtils._build_composite_pk_sql("t", ["org_id", "timestamp", "value"], strategy)
        assert "PRIMARY KEY (org_id, timestamp)" in sql

    def test_emits_partial_composite_when_only_some_key_columns_present(self) -> None:
        """Only present columns become the PK clause."""
        strategy = {"type": "composite_pk", "primary_key": ["org_id", "missing"], "indexes": []}
        sql = DatabaseSchemaUtils._build_composite_pk_sql("t", ["org_id"], strategy)
        assert "PRIMARY KEY (org_id)" in sql

    def test_emits_no_primary_key_when_no_key_columns_present(self) -> None:
        """When none of the PK columns are in ``fields``, no PK clause is emitted."""
        strategy = {"type": "composite_pk", "primary_key": ["a", "b"], "indexes": []}
        sql = DatabaseSchemaUtils._build_composite_pk_sql("t", ["other"], strategy)
        assert "PRIMARY KEY" not in sql


class TestBuildAutoincrementSql:
    """Exercise the autoincrement-with-unique DDL builder."""

    def test_emits_surrogate_key_and_unique_clause(self) -> None:
        """Surrogate PK column is first; UNIQUE clause appears for present columns."""
        strategy = {"type": "auto_increment_with_unique", "unique_constraints": ["id"], "indexes": []}
        sql = DatabaseSchemaUtils._build_autoincrement_sql("t", ["id", "name"], strategy)
        assert "misthelper_internal_id INTEGER PRIMARY KEY AUTOINCREMENT" in sql
        assert "UNIQUE(id)" in sql
        assert "id TEXT" in sql

    def test_omits_unique_clause_when_no_constrained_columns_present(self) -> None:
        """No configured unique columns present -> the UNIQUE suffix is empty."""
        strategy = {"type": "auto_increment_with_unique", "unique_constraints": ["missing"], "indexes": []}
        sql = DatabaseSchemaUtils._build_autoincrement_sql("t", ["name"], strategy)
        assert "UNIQUE" not in sql


class TestBuildCreateTableSql:
    """Dispatcher for the three DDL branches."""

    def test_dispatches_to_natural_pk_branch(self) -> None:
        """A ``natural_pk`` strategy routes through the natural builder."""
        strategy = {"type": "natural_pk", "primary_key": ["id"], "indexes": []}
        sql = DatabaseSchemaUtils.build_create_table_sql("nat", ["id"], strategy)
        assert "PRIMARY KEY (id)" in sql

    def test_dispatches_to_composite_pk_branch(self) -> None:
        """A ``composite_pk`` strategy routes through the composite builder."""
        strategy = {"type": "composite_pk", "primary_key": ["a", "b"], "indexes": []}
        sql = DatabaseSchemaUtils.build_create_table_sql("comp", ["a", "b"], strategy)
        assert "PRIMARY KEY (a, b)" in sql

    def test_dispatches_to_autoincrement_fallback_for_unknown_type(self) -> None:
        """An unrecognized ``type`` falls back to the autoincrement builder."""
        strategy = {"type": "something_else", "unique_constraints": ["id"], "indexes": []}
        sql = DatabaseSchemaUtils.build_create_table_sql("auto", ["id"], strategy)
        assert "misthelper_internal_id INTEGER PRIMARY KEY AUTOINCREMENT" in sql

    def test_sanitizes_table_name_before_emitting_ddl(self) -> None:
        """The dispatcher sanitizes the table name before delegation."""
        strategy = {"type": "natural_pk", "primary_key": ["id"], "indexes": []}
        sql = DatabaseSchemaUtils.build_create_table_sql("weird-name!", ["id"], strategy)
        assert "CREATE TABLE IF NOT EXISTS weird_name_ (" in sql


class TestBuildIndexesSql:
    """Cover ``build_indexes_sql`` including sanitization and filtering."""

    def test_returns_one_index_per_configured_and_present_field(self) -> None:
        """Only fields both listed in ``strategy['indexes']`` and present in ``fields`` yield DDL."""
        strategy = {"indexes": ["org_id", "site_id", "missing"]}
        sqls = DatabaseSchemaUtils.build_indexes_sql("t", ["org_id", "site_id"], strategy)
        assert any("idx_t_org_id" in s and "ON t (org_id)" in s for s in sqls)
        assert any("idx_t_site_id" in s for s in sqls)
        assert not any("missing" in s for s in sqls)

    def test_returns_empty_list_when_no_indexes_configured(self) -> None:
        """Missing ``indexes`` key yields an empty result."""
        assert DatabaseSchemaUtils.build_indexes_sql("t", ["a"], {}) == []

    def test_sanitizes_table_and_column_names_in_index_ddl(self) -> None:
        """Illegal characters in table/column names are scrubbed in the emitted DDL."""
        strategy = {"indexes": ["bad-col"]}
        sqls = DatabaseSchemaUtils.build_indexes_sql("bad-table", ["bad-col"], strategy)
        assert sqls == ["CREATE INDEX IF NOT EXISTS idx_bad_table_bad_col ON bad_table (bad_col)"]

    def test_prefixes_digit_leading_table_name_in_index_ddl(self) -> None:
        """Digit-led table names get the ``table_`` prefix in index DDL too."""
        strategy = {"indexes": ["a"]}
        sqls = DatabaseSchemaUtils.build_indexes_sql("9tbl", ["a"], strategy)
        assert sqls[0].startswith("CREATE INDEX IF NOT EXISTS idx_table_9tbl_a ON table_9tbl (a)")

    def test_handles_empty_table_name(self) -> None:
        """Empty table name becomes ``table_``."""
        strategy = {"indexes": ["a"]}
        sqls = DatabaseSchemaUtils.build_indexes_sql("", ["a"], strategy)
        assert sqls[0].endswith("ON table_ (a)")


class TestLoggingSideEffects:
    """Smoke-test the debug logging paths (branch coverage for logging.debug lines)."""

    def test_get_endpoint_strategy_logs_when_configured(self, caplog: pytest.LogCaptureFixture) -> None:
        """Configured strategy path emits a debug trace."""
        known_key = next(k for k in ENDPOINT_PRIMARY_KEY_STRATEGIES if k != "default")
        with caplog.at_level(logging.DEBUG):
            DatabaseSchemaUtils.get_endpoint_strategy(known_key, [])
        assert any("Using configured strategy" in r.message for r in caplog.records)

    def test_build_create_table_sql_logs_ddl_snippet(self, caplog: pytest.LogCaptureFixture) -> None:
        """The dispatcher logs the first 100 chars of the emitted DDL."""
        strategy = {"type": "natural_pk", "primary_key": ["id"], "indexes": []}
        with caplog.at_level(logging.DEBUG):
            DatabaseSchemaUtils.build_create_table_sql("t", ["id"], strategy)
        assert any("Generated CREATE TABLE SQL" in r.message for r in caplog.records)
