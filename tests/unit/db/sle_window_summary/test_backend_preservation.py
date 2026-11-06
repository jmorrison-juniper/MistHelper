"""Verify repeated SLE exports preserve legacy data in isolated backend doubles."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest

from src.foundation.persistence.db.database_schema_utils import DatabaseSchemaUtils
from src.foundation.support.refactors import sqlite_database_writer as sqlite_module
from src.foundation.support.refactors.endpoint_primary_key_strategies import (
    ENDPOINT_PRIMARY_KEY_STRATEGIES,
    SleWindowIdentity,
)
from src.foundation.support.refactors.sqlite_database_writer import SQLiteDatabaseWriter
from tests.unit.arango_indexes.fakes import ArangoIndexWriterHarness

HISTOGRAM_OPERATION = "getSiteSleHistogram"
IMPACT_OPERATION = "getSiteSleImpactSummary"
OPERATIONS = (HISTOGRAM_OPERATION, IMPACT_OPERATION)


@pytest.fixture
def sqlite_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Route real SQLite writer operations to one isolated temporary file."""
    database_path = tmp_path / "sle-window-test.db"
    processing = MagicMock()
    processing.escape_multiline.side_effect = lambda rows: rows
    processing.get_unique_keys.side_effect = lambda rows: sorted({key for row in rows for key in row})
    dependencies = SimpleNamespace(
        DataProcessingUtils=processing,
        DatabaseSchemaUtils=DatabaseSchemaUtils,
        misthelper_module=SimpleNamespace(DATABASE_PATH=str(database_path)),
    )
    monkeypatch.setattr(sqlite_module, "_resolve_runtime_dependencies", lambda: dependencies)
    return database_path


def _window(operation: str) -> dict[str, Any]:
    """Build a local response row with only schema-backed identity fields."""
    row: dict[str, Any] = {
        "site_id": "site-1",
        "scope": "site",
        "scope_id": "scope-1",
        "metric": "coverage",
        "start": 100,
        "end": 200,
        "value": "original",
    }
    if operation == IMPACT_OPERATION:
        row.update(classifier="", failure="")
    return row


def _seed_sqlite_legacy_rows(database_path: Path, row: dict[str, Any]) -> tuple[list[str], list[tuple[Any, ...]]]:
    """Create old auto-increment rows without a new-window marker."""
    fields = list(row)
    legacy_strategy = {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "unique_constraints": [],
    }
    create_sql = DatabaseSchemaUtils.build_create_table_sql("sle_window", fields, legacy_strategy)
    with closing(sqlite3.connect(database_path)) as connection:
        connection.execute(create_sql)
        records = (
            {**row, "value": "legacy-one"},
            {**row, "value": "legacy-two"},
            {**row, "site_id": "other-site", "value": "unrelated"},
        )
        columns = ", ".join(fields)
        placeholders = ", ".join("?" for _ in fields)
        for record in records:
            connection.execute(
                f"INSERT INTO sle_window ({columns}) VALUES ({placeholders})",
                [record[field] for field in fields],
            )
        connection.commit()
        table_columns = [column[1] for column in connection.execute("PRAGMA table_info(sle_window)")]
        stored = connection.execute("SELECT * FROM sle_window ORDER BY misthelper_internal_id").fetchall()
    return table_columns, stored


@pytest.mark.parametrize("operation", OPERATIONS)
def test_sqlite_repeated_exports_preserve_all_legacy_rows(sqlite_path: Path, operation: str) -> None:
    """Replace one keyed row after three exports while retaining old duplicates."""
    row = _window(operation)
    old_columns, old_rows = _seed_sqlite_legacy_rows(sqlite_path, row)
    for value in ("first", "second", "third"):
        assert SQLiteDatabaseWriter([{**row, "value": value}], "sle_window", operation).write() is True
    with closing(sqlite3.connect(sqlite_path)) as connection:
        current_columns = [column[1] for column in connection.execute("PRAGMA table_info(sle_window)")]
        key_column = "misthelper_sle_window_key"
        legacy = connection.execute(
            f"SELECT {', '.join(old_columns)} FROM sle_window WHERE {key_column} IS NULL "
            "ORDER BY misthelper_internal_id"
        ).fetchall()
        keyed = connection.execute(f"SELECT value FROM sle_window WHERE {key_column} IS NOT NULL").fetchall()
    assert legacy == old_rows
    assert current_columns[-1] == key_column
    assert keyed == [("third",)]


@pytest.mark.parametrize("operation", OPERATIONS)
def test_sqlite_distinct_window_adds_a_separate_keyed_row(sqlite_path: Path, operation: str) -> None:
    """Keep a changed response window separate from a matching window."""
    row = _window(operation)
    assert SQLiteDatabaseWriter([row], "sle_window", operation).write() is True
    changed = {**row, "start": 200, "end": 300}
    assert SQLiteDatabaseWriter([changed], "sle_window", operation).write() is True
    with closing(sqlite3.connect(sqlite_path)) as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM sle_window WHERE misthelper_sle_window_key IS NOT NULL"
        ).fetchone()
    assert count == (2,)


@pytest.mark.parametrize("operation", OPERATIONS)
def test_arango_repeated_exports_preserve_legacy_documents(operation: str) -> None:
    """Replace only the new deterministic document while keeping legacy UUID records."""
    harness = ArangoIndexWriterHarness()
    try:
        writer = harness.writer()
        row = _window(operation)
        legacy_strategy = {
            "type": "auto_increment_with_unique",
            "primary_key": ["misthelper_internal_id"],
        }
        unrelated = {**row, "site_id": "other-site", "value": "unrelated"}
        assert writer.write([row, row, unrelated], operation, legacy_strategy).records_written == 3
        collection = harness.database.collections[operation]
        legacy_documents = {key: dict(value) for key, value in collection.state.documents.items()}
        strategy = ENDPOINT_PRIMARY_KEY_STRATEGIES[operation]
        for value in ("first", "second", "third"):
            assert writer.write([{**row, "value": value}], operation, strategy).records_written == 1
        key = SleWindowIdentity.key(row, strategy["primary_key"])
        assert {key: collection.state.documents[key]}[key]["value"] == "third"
        assert {item: collection.state.documents[item] for item in legacy_documents} == legacy_documents
        assert len(collection.state.documents) == 4
    finally:
        harness.close()


@pytest.mark.parametrize("operation", OPERATIONS)
def test_arango_distinct_window_adds_a_separate_document(operation: str) -> None:
    """Use a separate deterministic key when an actual window boundary changes."""
    harness = ArangoIndexWriterHarness()
    try:
        writer = harness.writer()
        row = _window(operation)
        strategy = ENDPOINT_PRIMARY_KEY_STRATEGIES[operation]
        assert writer.write([row], operation, strategy).records_written == 1
        changed = {**row, "start": 200, "end": 300}
        assert writer.write([changed], operation, strategy).records_written == 1
        assert len(harness.database.collections[operation].state.documents) == 2
    finally:
        harness.close()
