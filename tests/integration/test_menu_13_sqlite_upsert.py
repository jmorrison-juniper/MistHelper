"""Integration tests for Menu 13 - SQLite upsert and CSV schema.

Tests verify that DataExporter correctly writes device statistics data
to SQLite with upsert idempotency (composite key on device_id + timestamp)
and to CSV with stable column schema. All tests use temporary directories.

Covers: FR-002, FR-003, FR-004, US2, US3 from spec-025.
"""

import csv
import sqlite3

import MistHelper
from tests.fixtures.device_stats import (
    ALL_STATS,
    STAT_AP,
    make_device_stats_fixtures,
)


class TestSQLiteUpsertIdempotency:
    """Verify INSERT OR REPLACE produces no duplicates on repeated writes."""

    def test_no_duplicates_on_repeated_insert(self, monkeypatch, tmp_path):
        """FR-003 / US2 Scenario 1: Same 10 records twice = 10 rows."""
        db_path = str(tmp_path / "data" / "mist_data.db")
        monkeypatch.setattr(MistHelper, "DATABASE_PATH", db_path)
        monkeypatch.setattr(MistHelper, "OUTPUT_FORMAT", "sqlite")
        monkeypatch.chdir(tmp_path)

        stats = make_device_stats_fixtures(10)

        first = MistHelper.DataExporter.write_with_format_selection(
            stats,
            "OrgDeviceStats.csv",
            api_function_name="listOrgDevicesStats",
        )
        second = MistHelper.DataExporter.write_with_format_selection(
            stats,
            "OrgDeviceStats.csv",
            api_function_name="listOrgDevicesStats",
        )

        assert first is True
        assert second is True

        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM OrgDeviceStats")
        count = cursor.fetchone()[0]
        connection.close()

        assert count == 10

    def test_updates_changed_fields(self, monkeypatch, tmp_path):
        """FR-003 / US2 Scenario 2: Changed cpu_stat value is updated."""
        db_path = str(tmp_path / "data" / "mist_data.db")
        monkeypatch.setattr(MistHelper, "DATABASE_PATH", db_path)
        monkeypatch.setattr(MistHelper, "OUTPUT_FORMAT", "sqlite")
        monkeypatch.chdir(tmp_path)

        stats = make_device_stats_fixtures(10)

        MistHelper.DataExporter.write_with_format_selection(
            stats,
            "OrgDeviceStats.csv",
            api_function_name="listOrgDevicesStats",
        )

        updated_stats = [dict(stat) for stat in stats]
        updated_stats[0]["cpu_stat"] = 99

        MistHelper.DataExporter.write_with_format_selection(
            updated_stats,
            "OrgDeviceStats.csv",
            api_function_name="listOrgDevicesStats",
        )

        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM OrgDeviceStats")
        count = cursor.fetchone()[0]
        target_device_id = stats[0]["device_id"]
        target_timestamp = stats[0]["timestamp"]
        cursor.execute(
            "SELECT cpu_stat FROM OrgDeviceStats WHERE device_id = ? AND timestamp = ?",
            (target_device_id, target_timestamp),
        )
        cpu_stat = cursor.fetchone()[0]
        connection.close()

        assert count == 10
        assert int(cpu_stat) == 99

    def test_composite_key_time_series(self, monkeypatch, tmp_path):
        """FR-003 / US2 Scenario 3: Same device_id + different timestamps = 2 rows."""
        db_path = str(tmp_path / "data" / "mist_data.db")
        monkeypatch.setattr(MistHelper, "DATABASE_PATH", db_path)
        monkeypatch.setattr(MistHelper, "OUTPUT_FORMAT", "sqlite")
        monkeypatch.chdir(tmp_path)

        record_time_1 = dict(STAT_AP)
        record_time_1["timestamp"] = 1700000000

        record_time_2 = dict(STAT_AP)
        record_time_2["timestamp"] = 1700003600

        MistHelper.DataExporter.write_with_format_selection(
            [record_time_1, record_time_2],
            "OrgDeviceStats.csv",
            api_function_name="listOrgDevicesStats",
        )

        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM OrgDeviceStats")
        count = cursor.fetchone()[0]
        connection.close()

        assert count == 2

    def test_indexes_created(self, monkeypatch, tmp_path):
        """FR-004: Indexes exist on device_id, timestamp, org_id, site_id, type."""
        db_path = str(tmp_path / "data" / "mist_data.db")
        monkeypatch.setattr(MistHelper, "DATABASE_PATH", db_path)
        monkeypatch.setattr(MistHelper, "OUTPUT_FORMAT", "sqlite")
        monkeypatch.chdir(tmp_path)

        MistHelper.DataExporter.write_with_format_selection(
            ALL_STATS,
            "OrgDeviceStats.csv",
            api_function_name="listOrgDevicesStats",
        )

        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='OrgDeviceStats'")
        index_names = [row[0] for row in cursor.fetchall()]
        connection.close()

        expected_columns = ["device_id", "timestamp", "org_id", "site_id", "type"]
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
            ALL_STATS,
            "OrgDeviceStats.csv",
            api_function_name="listOrgDevicesStats",
        )

        csv_path = tmp_path / "data" / "OrgDeviceStats.csv"
        assert csv_path.exists(), f"Expected CSV at {csv_path}"

        with open(csv_path, newline="", encoding="utf-8") as file_handle:
            reader = csv.DictReader(file_handle)
            headers = reader.fieldnames or []

        required_columns = [
            "device_id",
            "mac",
            "model",
            "type",
            "org_id",
            "timestamp",
        ]
        for column in required_columns:
            assert column in headers, f"Missing required column: {column}"

    def test_csv_roundtrip_matches_source_data(self, monkeypatch, tmp_path):
        """US3 Scenario 2: CSV data matches source fixture values."""
        monkeypatch.setattr(MistHelper, "OUTPUT_FORMAT", "csv")
        monkeypatch.chdir(tmp_path)

        MistHelper.DataExporter.write_with_format_selection(
            ALL_STATS,
            "OrgDeviceStats.csv",
            api_function_name="listOrgDevicesStats",
        )

        csv_path = tmp_path / "data" / "OrgDeviceStats.csv"
        with open(csv_path, newline="", encoding="utf-8") as file_handle:
            reader = csv.DictReader(file_handle)
            rows = list(reader)

        assert len(rows) == len(ALL_STATS)

        source_ids = sorted(str(stat["device_id"]) for stat in ALL_STATS)
        csv_ids = sorted(row["device_id"] for row in rows)
        assert csv_ids == source_ids

        ap_row = next(row for row in rows if row["device_id"] == str(STAT_AP["device_id"]))
        assert ap_row["model"] == str(STAT_AP["model"])
        assert ap_row["type"] == str(STAT_AP["type"])
