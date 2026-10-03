"""Preserve backend identities and discover the actual uppercase CSV output."""

from __future__ import annotations

import csv
import json
import logging
import sqlite3
from contextlib import closing
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import Mock, call

import pytest

from src.data.data_processing_utils import DataProcessingUtils
from src.dataclasses.export_backend_options import ExportBackendOptions
from src.db import WriteResult
from src.db.database_schema_utils import DatabaseSchemaUtils
from src.db.router import DatabaseRouter
from src.export import data_exporter as exporter_module
from src.export.data_exporter import DataExporter
from src.refactors import sqlite_database_writer as sqlite_module
from src.refactors.sqlite_database_writer import SQLiteDatabaseWriter
from src.utils.file_path_utils import FilePathUtils
from web_portal.services.data_browser import DataBrowserService
from web_portal.services.output_scan import OutputFileScanner


@pytest.fixture
def private_router(monkeypatch: pytest.MonkeyPatch) -> Mock:
    """Keep the real routing method while preventing external store access."""
    router = Mock(spec=DatabaseRouter)
    router.write.return_value = WriteResult(success=True, backend="arangodb", records_written=1, records_failed=0)
    monkeypatch.setenv("MISTHELPER_STANDALONE", "false")
    monkeypatch.setattr(exporter_module, "DB_LAYER_AVAILABLE", True)
    monkeypatch.setattr(DataExporter, "_router", router)
    monkeypatch.setattr(DataExporter, "_router_initialized", True)
    return router


@pytest.fixture
def private_sqlite(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Use real SQLite schema tools only in a temporary local database."""
    database = tmp_path / "owned.sqlite"
    dependencies = SimpleNamespace(
        DatabaseSchemaUtils=DatabaseSchemaUtils,
        DataProcessingUtils=DataProcessingUtils,
        misthelper_module=SimpleNamespace(DATABASE_PATH=str(database)),
    )
    monkeypatch.setattr(sqlite_module, "_resolve_runtime_dependencies", Mock(return_value=dependencies))
    return database


class TestCsvSuffixBackendIdentity:
    """Filename recognition must not migrate a database target or endpoint."""

    @pytest.mark.parametrize(
        ("target", "expected"),
        [
            ("SiteWiFiClients.csv", "SiteWiFiClients"),
            ("SiteWiFiClients.CSV", "SiteWiFiClients.CSV"),
            ("SiteWiFiClients.Csv", "SiteWiFiClients.Csv"),
            ("SiteWiFiClients.cSv", "SiteWiFiClients.cSv"),
            ("SiteWiFiClients", "SiteWiFiClients"),
            ("Archive.csv/Records.CSV", "Archive.csv/Records.CSV"),
            ("R\u00e9seau.CSV", "R\u00e9seau.CSV"),
        ],
    )
    def test_sqlite_constructor_keeps_current_target(
        self, monkeypatch: pytest.MonkeyPatch, private_router: Mock, target: str, expected: str
    ) -> None:
        """Uppercase suffixes must retain the existing SQLite constructor name."""
        constructor = Mock(spec=SQLiteDatabaseWriter)
        constructor.return_value.write.return_value = True
        monkeypatch.setattr(exporter_module, "SQLiteDatabaseWriter", constructor)
        data: list[dict[str, Any]] = [{"id": "client-1", "hostname": "Lab Client"}]
        options = ExportBackendOptions(format_override="sqlite")
        assert (
            DataExporter.write_with_format_selection(
                data, target, "listSiteWirelessClientsStats", backend_options=options
            )
            is True
        )
        constructor.assert_called_once_with(data, expected, "listSiteWirelessClientsStats")
        private_router.write.assert_called_once_with(data, "listSiteWirelessClientsStats")
        assert constructor.return_value.write.call_count == 1
        print("Checked 1 SQLite target, 1 router call, and 1 record:", ascii(expected))

    @pytest.mark.parametrize(
        "case",
        [("Sites.csv", "Sites"), ("Sites.CSV", "Sites_CSV"), ("Sites.Csv", "Sites_Csv"), ("Sites", "Sites")],
    )
    def test_actual_sqlite_keeps_table_identity_and_natural_key(
        self, private_sqlite: Path, private_router: Mock, case: tuple[str, str]
    ) -> None:
        """The real SQLite writer must retain its table name and replace a natural key."""
        target, expected_table = case
        first: list[dict[str, Any]] = [{"id": "site-1", "name": "First Site"}]
        second: list[dict[str, Any]] = [{"id": "site-1", "name": "Updated Site"}]
        options = ExportBackendOptions(format_override="sqlite")
        assert DataExporter.write_with_format_selection(first, target, "listOrgSites", backend_options=options) is True
        assert DataExporter.write_with_format_selection(second, target, "listOrgSites", backend_options=options) is True
        with closing(sqlite3.connect(private_sqlite)) as connection:
            assert connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall() == [
                (expected_table,)
            ]
            assert connection.execute(f"SELECT id, name FROM {expected_table}").fetchall() == [
                ("site-1", "Updated Site")
            ]
        assert private_router.write.call_args_list == [call(first, "listOrgSites"), call(second, "listOrgSites")]
        print("Checked 2 SQLite writes, 1 table, 1 natural-key record, and 2 private router calls.")

    @pytest.mark.parametrize("target", ["Records.csv", "Records.CSV", "Records.Csv", "Records.cSv", "Records"])
    @pytest.mark.parametrize("output_format", ["csv", "sqlite"])
    def test_router_keeps_raw_data_and_endpoint(
        self, monkeypatch: pytest.MonkeyPatch, private_router: Mock, target: str, output_format: str
    ) -> None:
        """Every filename form must preserve raw payload selection and endpoint identity."""
        constructor = Mock(spec=SQLiteDatabaseWriter)
        constructor.return_value.write.return_value = True
        monkeypatch.setattr(exporter_module, "SQLiteDatabaseWriter", constructor)
        flattened: list[dict[str, Any]] = [{"id": "site-1", "nested_name": "Lab Site"}]
        raw: list[dict[str, Any]] = [{"id": "site-1", "nested": {"name": "Lab Site"}}]
        options = ExportBackendOptions(format_override=output_format, raw_data=raw)
        assert (
            DataExporter.write_with_format_selection(flattened, target, "listOrgSites", backend_options=options) is True
        )
        private_router.write.assert_called_once_with(raw, "listOrgSites")
        assert raw == [{"id": "site-1", "nested": {"name": "Lab Site"}}]
        assert flattened == [{"id": "site-1", "nested_name": "Lab Site"}]


class TestCsvSuffixDiscovery:
    """Existing output services must read the preserved uppercase name."""

    def test_actual_browser_and_scanner_read_uppercase_csv(self, tmp_path: Path) -> None:
        """List, resolve, read, and preview the actual writer's complete file."""
        directory = tmp_path / "data"
        directory.mkdir()
        scanner = OutputFileScanner(str(directory))
        scanner.snapshot()
        try:
            data = [
                {"hostname": "Lab Client", "site_name": "Lab Site", "mac": "aabbccddeeff", "notes": "first\nsecond"}
            ]
            assert DataExporter._write_csv_format(data, "SiteWiFiClients.CSV") is True
        finally:
            changed = scanner.changed_files()
        assert changed == ["SiteWiFiClients.CSV"]
        browser = DataBrowserService(str(directory))
        destination = directory / "SiteWiFiClients.CSV"
        assert FilePathUtils.get_csv_path("SiteWiFiClients.CSV") == str(Path("data") / "SiteWiFiClients.CSV")
        assert browser.resolve_safe_path("SiteWiFiClients.CSV") == str(destination.resolve())
        assert browser.read_column_names("SiteWiFiClients.CSV") == ["hostname", "mac", "notes", "site_name"]
        self.verify_browser_result(browser, destination)
        assert OutputFileScanner._active_scanners == []
        print("Checked 1 scanner filename, 1 browser filename, 4 columns, and 1 preview record.")

    @staticmethod
    def verify_browser_result(browser: DataBrowserService, destination: Path) -> None:
        """Check complete listing metadata and the existing identity-column order."""
        stat = destination.stat()
        assert browser.list_files() == [
            {
                "name": "SiteWiFiClients.CSV",
                "path": "SiteWiFiClients.CSV",
                "size_bytes": stat.st_size,
                "last_modified": stat.st_mtime,
                "file_type": "csv",
                "is_directory": False,
            }
        ]
        assert browser.preview_file("SiteWiFiClients.CSV", 1, 25, "") == {
            "columns": ["hostname", "site_name", "mac", "notes"],
            "rows": [["Lab Client", "Lab Site", "aabbccddeeff", "first\\nsecond"]],
            "total_rows": 1,
            "page": 1,
            "per_page": 25,
            "total_pages": 1,
        }

    def test_existing_duplicate_named_file_is_not_changed(self, tmp_path: Path) -> None:
        """The repair must not rename, remove, or overwrite a historical duplicate."""
        DataExporter.write_to_csv([{"id": "historical"}], "SiteWiFiClients.CSV.csv")
        directory = tmp_path / "data"
        old_file = directory / "SiteWiFiClients.CSV.csv"
        old_content = old_file.read_bytes()
        scanner = OutputFileScanner(str(directory))
        scanner.snapshot()
        try:
            assert DataExporter._write_csv_format([{"id": "current"}], "SiteWiFiClients.CSV") is True
        finally:
            changed = scanner.changed_files()
        assert changed == ["SiteWiFiClients.CSV"]
        assert old_file.read_bytes() == old_content
        assert sorted(path.name for path in directory.iterdir()) == [
            "SiteWiFiClients.CSV",
            "SiteWiFiClients.CSV.csv",
        ]
        with (directory / "SiteWiFiClients.CSV").open(encoding="utf-8", newline="") as stream:
            assert list(csv.reader(stream)) == [["id"], ["current"]]


class TestCsvSuffixErrorBoundaries:
    """Keep primary output, router warnings, and invalid-input behavior."""

    @pytest.mark.parametrize(
        "case",
        [
            (WriteResult(False, "arangodb", 0, 1, "owned backend failure"), "router_write_failed"),
            (WriteResult(True, "csv_only", 0, 0), "router_file_fallback"),
            (ConnectionError("owned connection failure"), "router_write_failed"),
            (TimeoutError("owned timeout"), "router_write_failed"),
        ],
    )
    def test_router_failure_preserves_csv_and_warning(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture, private_router: Mock, case: tuple[Any, str]
    ) -> None:
        """A lost external write must retain the real CSV file and explicit warning."""
        answer, reason = case
        if isinstance(answer, Exception):
            private_router.write.side_effect = answer
        else:
            private_router.write.return_value = answer
        data: list[dict[str, Any]] = [{"id": "client-1"}]
        with caplog.at_level(logging.WARNING):
            result = DataExporter.write_with_format_selection(
                data, "Records.CSV", "listOrgSites", backend_options=ExportBackendOptions(format_override="csv")
            )
        assert result is True
        private_router.write.assert_called_once_with(data, "listOrgSites")
        assert reason in caplog.text
        assert "The database write was dropped for listOrgSites" in caplog.text
        with (tmp_path / "data" / "Records.CSV").open(encoding="utf-8", newline="") as stream:
            assert list(csv.reader(stream)) == [["id"], ["client-1"]]
        assert sorted(path.name for path in (tmp_path / "data").iterdir()) == ["Records.CSV"]

    def test_primary_write_failure_keeps_existing_dispatch_and_router_behavior(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture, private_router: Mock
    ) -> None:
        """The existing dispatch returns False while the independent router still runs."""
        denied = Mock(spec=DataExporter._write_csv_open_and_emit, side_effect=PermissionError("owned write denial"))
        monkeypatch.setattr(DataExporter, "_write_csv_open_and_emit", denied)
        data: list[dict[str, Any]] = [{"id": "client-1"}]
        with caplog.at_level(logging.ERROR):
            result = DataExporter.write_with_format_selection(
                data, "Records.CSV", "listOrgSites", backend_options=ExportBackendOptions(format_override="csv")
            )
        assert result is False
        denied.assert_called_once_with(str(Path("data") / "Records.CSV"), data, ["id"])
        private_router.write.assert_called_once_with(data, "listOrgSites")
        assert "Permission denied when writing to data" in caplog.text
        assert "Failed to write data to Records.CSV in csv format" in caplog.text
        assert list((tmp_path / "data").iterdir()) == []

    def test_empty_data_keeps_refusal_without_output(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture, private_router: Mock
    ) -> None:
        """Empty rows must create no CSV file and request no external write."""
        with caplog.at_level(logging.WARNING):
            result = DataExporter.write_with_format_selection(
                [], "Records.CSV", "listOrgSites", backend_options=ExportBackendOptions(format_override="csv")
            )
        assert result is False
        assert private_router.write.call_count == 0
        assert "No data provided for output to Records.CSV" in caplog.text
        assert list(tmp_path.rglob("*.CSV")) == []
        assert list(tmp_path.rglob("*.csv")) == []

    def test_invalid_format_keeps_refusal_without_output(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture, private_router: Mock
    ) -> None:
        """The filename repair must not enable another output format."""
        with caplog.at_level(logging.ERROR):
            result = DataExporter.write_with_format_selection(
                [{"id": "client-1"}],
                "Records.CSV",
                "listOrgSites",
                backend_options=ExportBackendOptions(format_override="json"),
            )
        assert result is False
        assert private_router.write.call_count == 0
        assert "Invalid output format: json" in caplog.text
        assert list(tmp_path.rglob("*.CSV")) == []
        assert list(tmp_path.rglob("*.csv")) == []

    @pytest.mark.parametrize("body", [pytest.param(b"", id="empty-body"), pytest.param(b"{", id="malformed-json")])
    def test_backend_body_failure_preserves_csv(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture, private_router: Mock, body: bytes
    ) -> None:
        """An empty or malformed backend reply must not remove valid CSV data."""

        def decode_backend_reply(data: list[dict[str, Any]], api_function_name: str) -> WriteResult:
            del data, api_function_name
            json.loads(body)  # The real decoder must reject the controlled backend body.
            raise AssertionError("An invalid body must not produce a backend result")

        with pytest.raises(json.JSONDecodeError, match="Expecting"):
            json.loads(body)
        private_router.write.side_effect = decode_backend_reply
        data: list[dict[str, Any]] = [{"id": "client-1"}]
        with caplog.at_level(logging.WARNING):
            result = DataExporter.write_with_format_selection(
                data, "Records.CSV", "listOrgSites", backend_options=ExportBackendOptions(format_override="csv")
            )
        assert result is True
        private_router.write.assert_called_once_with(data, "listOrgSites")
        assert "router_write_failed" in caplog.text
        assert "The database write was dropped for listOrgSites" in caplog.text
        assert (tmp_path / "data" / "Records.CSV").read_text(encoding="utf-8") == "id\nclient-1\n"
        print("Checked 1 invalid backend body, 1 CSV record, and 1 private router call.")
