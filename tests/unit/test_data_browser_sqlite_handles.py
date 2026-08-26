"""Regression tests for the SQLite handle release in the data browser service.

issue #1901. Each helper opened a SQLite connection and closed it on the success
path only. An exception between the open call and the close call leaked the
handle. A long-lived Gunicorn worker then reached the per-process descriptor
limit and every later preview failed.
"""

from __future__ import annotations

import os
import sqlite3
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from web_portal.services.data_browser import DataBrowserService


@pytest.fixture(name="service")
def _service(tmp_path) -> DataBrowserService:
    """Return a data browser service rooted at an empty temporary directory."""
    return DataBrowserService(str(tmp_path))


def _failing_connection() -> MagicMock:
    """Return a connection mock that raises when the caller asks for a cursor."""
    connection = MagicMock(name="sqlite_connection")
    connection.cursor.side_effect = sqlite3.DatabaseError("database disk image is malformed")
    return connection


@pytest.mark.parametrize(
    ("method_name", "arguments"),
    [
        ("_list_sqlite_tables", ("some.db",)),
        ("_is_valid_table_name", ("some.db", "devices")),
        ("_preview_sqlite", ("some.db", "devices", 1, 50, "")),
    ],
)
def test_sqlite_handle_closes_when_the_query_fails(
    service: DataBrowserService,
    method_name: str,
    arguments: tuple,
) -> None:
    """Verify each helper closes the connection after a query error."""
    connection = _failing_connection()
    with patch("web_portal.services.data_browser.sqlite3.connect", return_value=connection):
        getattr(service, method_name)(*arguments)

    connection.close.assert_called_once()


def test_list_sqlite_tables_reports_the_error_instead_of_raising(service: DataBrowserService) -> None:
    """Verify the caller still receives an error payload after a query error."""
    with patch("web_portal.services.data_browser.sqlite3.connect", return_value=_failing_connection()):
        result = service._list_sqlite_tables("some.db")

    assert "error" in result


def test_preview_sqlite_closes_the_handle_when_the_table_is_absent(tmp_path) -> None:
    """Verify the empty-table early return still releases the connection."""
    service = DataBrowserService(str(tmp_path))
    connection = MagicMock(name="sqlite_connection")
    connection.cursor.return_value.fetchall.return_value = []

    with patch("web_portal.services.data_browser.sqlite3.connect", return_value=connection):
        result = service._preview_sqlite("some.db", "missing", 1, 50, "")

    assert result == {"error": "Table not found"}
    connection.close.assert_called_once()


def test_sqlite_helpers_close_the_handle_on_the_success_path(tmp_path) -> None:
    """Verify a real database file still opens, answers, and closes."""
    database_path = tmp_path / "sample.db"
    with sqlite3.connect(database_path) as setup_connection:
        setup_connection.execute("CREATE TABLE devices (id INTEGER PRIMARY KEY, name TEXT)")
        setup_connection.execute("INSERT INTO devices (name) VALUES ('ap-01')")
    setup_connection.close()

    service = DataBrowserService(str(tmp_path))
    listing = service._list_sqlite_tables(str(database_path))

    assert [table["table_name"] for table in listing["tables"]] == ["devices"]
    assert service._is_valid_table_name(str(database_path), "devices") is True
    assert service._is_valid_table_name(str(database_path), "absent") is False
