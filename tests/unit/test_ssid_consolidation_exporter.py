import csv
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from src.ssid_consolidation.exporter import Exporter


class TestExporter(unittest.TestCase):
    def setUp(self):
        self.exporter = Exporter()

    def test_write_creates_csv_and_sqlite_exports(self):
        rows = [
            {
                "site_id": "site-1",
                "site_name": "Site One",
                "template_id": "tmpl-1",
                "template_name": "Template One",
                "target_ssid_name": "Corp",
                "target_ssid_id": "ssid-1",
                "psk_detected": 1,
                "edge_cluster_id": "ec-1",
                "edge_cluster_name": "Edge Cluster 1",
                "anomaly_code": None,
                "collected_at": "2026-04-07T00:00:00+00:00",
            }
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            output = self.exporter.write(rows, outdir=temp_dir, basename="phase1")
            csv_path = Path(output["csv"])
            db_path = Path(output["db"])

            self.assertTrue(csv_path.exists())
            self.assertTrue(db_path.exists())

            with csv_path.open(newline="", encoding="utf-8") as handle:
                reader = list(csv.DictReader(handle))
            self.assertEqual(reader[0]["site_name"], "Site One")

            with closing(sqlite3.connect(str(db_path))) as connection:
                site_name = connection.execute(
                    "SELECT site_name FROM phase1_matrix WHERE site_id = ?",
                    ("site-1",),
                ).fetchone()[0]
            self.assertEqual(site_name, "Site One")

    def test_write_handles_empty_rows_with_header_only_outputs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = self.exporter.write([], outdir=temp_dir, basename="empty")
            csv_path = Path(output["csv"])

            with csv_path.open(newline="", encoding="utf-8") as handle:
                lines = handle.read().splitlines()
            self.assertEqual(len(lines), 1)


if __name__ == "__main__":
    unittest.main()
