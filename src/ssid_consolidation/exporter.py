"""Export helpers for phase 1 SSID consolidation artifacts."""

from __future__ import annotations

import csv
import logging
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any

LOGGER = logging.getLogger(__name__)
PHASE1_COLUMNS = (
    "site_id",
    "site_name",
    "template_id",
    "template_name",
    "target_ssid_name",
    "target_ssid_id",
    "psk_detected",
    "edge_cluster_id",
    "edge_cluster_name",
    "anomaly_code",
    "collected_at",
)
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS phase1_matrix (
    site_id TEXT,
    site_name TEXT,
    template_id TEXT,
    template_name TEXT,
    target_ssid_name TEXT,
    target_ssid_id TEXT,
    psk_detected TEXT,
    edge_cluster_id TEXT,
    edge_cluster_name TEXT,
    anomaly_code TEXT,
    collected_at TEXT
)
"""
DELETE_ROWS_SQL = "DELETE FROM phase1_matrix"
INSERT_ROWS_SQL = """
INSERT INTO phase1_matrix (
    site_id,
    site_name,
    template_id,
    template_name,
    target_ssid_name,
    target_ssid_id,
    psk_detected,
    edge_cluster_id,
    edge_cluster_name,
    anomaly_code,
    collected_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""


class Exporter:
    """Export phase 1 rows to CSV and SQLite using a fixed schema."""

    def _normalize_rows(self, rows: list[dict[str, Any]]) -> list[dict[str, str]]:
        """Convert rows to string-valued dictionaries in the fixed export order."""
        normalized_rows: list[dict[str, str]] = []
        for row in rows:
            normalized_rows.append(
                {column: "" if row.get(column) is None else str(row.get(column, "")) for column in PHASE1_COLUMNS}
            )
        return normalized_rows

    def _row_values(self, row: dict[str, str]) -> tuple[str, ...]:
        """Return one row ordered for the SQLite insert statement."""
        return tuple(row[column] for column in PHASE1_COLUMNS)

    def write_csv(self, rows: list[dict[str, str]], csv_path: Path) -> None:
        """Write the CSV export with a stable column order."""
        try:
            with csv_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(PHASE1_COLUMNS))
                writer.writeheader()
                writer.writerows(rows)
        except (OSError, csv.Error):
            LOGGER.exception("Exporter: failed to write CSV export to %s", csv_path)

    def write_sqlite(self, rows: list[dict[str, str]], db_path: Path) -> None:
        """Write the SQLite export using fixed DDL and parameterized inserts."""
        try:
            with closing(sqlite3.connect(str(db_path))) as connection:
                connection.execute(CREATE_TABLE_SQL)
                connection.execute(DELETE_ROWS_SQL)
                if rows:
                    connection.executemany(
                        INSERT_ROWS_SQL,
                        [self._row_values(row) for row in rows],
                    )
                connection.commit()
        except (OSError, sqlite3.Error):
            LOGGER.exception("Exporter: failed to write SQLite export to %s", db_path)

    def write(
        self,
        rows: list[dict[str, Any]],
        outdir: str = "data/ssid-consolidation",
        basename: str = "matrix",
    ) -> dict[str, str]:
        """Write both CSV and SQLite exports and return their filesystem paths."""
        output_dir = Path(outdir)
        output_dir.mkdir(parents=True, exist_ok=True)
        csv_path = output_dir / f"{basename}.csv"
        db_path = output_dir / f"{basename}.db"
        normalized_rows = self._normalize_rows(rows)
        self.write_csv(normalized_rows, csv_path)
        self.write_sqlite(normalized_rows, db_path)
        return {"csv": str(csv_path), "db": str(db_path)}
