"""Integration tests for Menu 12 - SQLite upsert and CSV schema.

Tests verify that DataExporter correctly writes device inventory data
to SQLite with upsert idempotency and to CSV with stable column schema.
All tests use temporary directories — no writes to real data/.

Covers: FR-002, FR-003, FR-004, FR-006, US2, US3 from spec-024.
"""

import csv
import sqlite3

import MistHelper
from tests.fixtures.device_inventory import (
    ALL_DEVICES,
    DEVICE_AP,
    make_device_fixtures,
)


class TestSQLiteUpsertIdempotency:
    """Verify INSERT OR REPLACE produces no duplicates on repeated writes."""

    def test_no_duplicates_on_repeated_insert(self, monkeypatch, tmp_path):
        """FR-003 / US2 Scenario 1: Same 10 devices twice = 10 rows."""
        db_path = str(tmp_path / "data" / "mist_data.db")
        monkeypatch.setattr(MistHelper, "DATABASE_PATH", db_path)
        monkeypatch.setattr(MistHelper, "OUTPUT_FORMAT", "sqlite")
        monkeypatch.chdir(tmp_path)

        devices = make_device_fixtures(10)

        first = MistHelper.DataExporter.write_with_format_selection(
            devices, "OrgInventory.csv", api_function_name="getOrgInventory",
        )
        second = MistHelper.DataExporter.write_with_format_selection(
            devices, "OrgInventory.csv", api_function_name="getOrgInventory",
        )

        assert first is True
        assert second is True

        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM OrgInventory")
        count = cursor.fetchone()[0]
        connection.close()

        assert count == 10

    def test_updates_changed_fields(self, monkeypatch, tmp_path):
        """FR-003 / US2 Scenario 2: Changed model value is updated."""
        db_path = str(tmp_path / "data" / "mist_data.db")
        monkeypatch.setattr(MistHelper, "DATABASE_PATH", db_path)
        monkeypatch.setattr(MistHelper, "OUTPUT_FORMAT", "sqlite")
        monkeypatch.chdir(tmp_path)

        devices = make_device_fixtures(10)

        MistHelper.DataExporter.write_with_format_selection(
            devices, "OrgInventory.csv", api_function_name="getOrgInventory",
        )

        updated_devices = [dict(device) for device in devices]
        updated_devices[0]["model"] = "AP45"

        MistHelper.DataExporter.write_with_format_selection(
            updated_devices, "OrgInventory.csv", api_function_name="getOrgInventory",
        )

        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM OrgInventory")
        count = cursor.fetchone()[0]
        target_id = devices[0]["id"]
        cursor.execute("SELECT model FROM OrgInventory WHERE id = ?", (target_id,))
        model = cursor.fetchone()[0]
        connection.close()

        assert count == 10
        assert model == "AP45"

    def test_indexes_created(self, monkeypatch, tmp_path):
        """FR-004: Indexes exist on org_id, site_id, mac, serial, model, type."""
        db_path = str(tmp_path / "data" / "mist_data.db")
        monkeypatch.setattr(MistHelper, "DATABASE_PATH", db_path)
        monkeypatch.setattr(MistHelper, "OUTPUT_FORMAT", "sqlite")
        monkeypatch.chdir(tmp_path)

        MistHelper.DataExporter.write_with_format_selection(
            ALL_DEVICES, "OrgInventory.csv", api_function_name="getOrgInventory",
        )

        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='OrgInventory'"
        )
        index_names = [row[0] for row in cursor.fetchall()]
        connection.close()

        expected_columns = ["org_id", "site_id", "mac", "serial", "model", "type"]
        for column in expected_columns:
            matching = [name for name in index_names if column in name]
            assert matching, f"No index found for column: {column}"


class TestCSVSchemaStability:
    """Verify CSV output contains expected column headers."""

    def test_csv_schema_contains_expected_columns(self, monkeypatch, tmp_path):
        """US3 Scenario 1: CSV headers match expected API response fields."""
        monkeypatch.setattr(MistHelper, "OUTPUT_FORMAT", "csv")
        monkeypatch.chdir(tmp_path)

        MistHelper.DataExporter.write_with_format_selection(
            ALL_DEVICES, "OrgInventory.csv", api_function_name="getOrgInventory",
        )

        csv_path = tmp_path / "data" / "OrgInventory.csv"
        assert csv_path.exists(), f"Expected CSV at {csv_path}"

        with open(csv_path, newline="", encoding="utf-8") as file_handle:
            reader = csv.DictReader(file_handle)
            headers = reader.fieldnames or []

        required_columns = ["id", "mac", "serial", "model", "type", "org_id"]
        for column in required_columns:
            assert column in headers, f"Missing required column: {column}"

    def test_csv_roundtrip_matches_source_data(self, monkeypatch, tmp_path):
        """US3 Scenario 2: CSV data matches source fixture values."""
        monkeypatch.setattr(MistHelper, "OUTPUT_FORMAT", "csv")
        monkeypatch.chdir(tmp_path)

        MistHelper.DataExporter.write_with_format_selection(
            ALL_DEVICES, "OrgInventory.csv", api_function_name="getOrgInventory",
        )

        csv_path = tmp_path / "data" / "OrgInventory.csv"
        with open(csv_path, newline="", encoding="utf-8") as file_handle:
            reader = csv.DictReader(file_handle)
            rows = list(reader)

        assert len(rows) == len(ALL_DEVICES)

        source_ids = sorted(str(device["id"]) for device in ALL_DEVICES)
        csv_ids = sorted(row["id"] for row in rows)
        assert csv_ids == source_ids

        ap_row = next(row for row in rows if row["id"] == str(DEVICE_AP["id"]))
        assert ap_row["model"] == str(DEVICE_AP["model"])
        assert ap_row["serial"] == str(DEVICE_AP["serial"])
