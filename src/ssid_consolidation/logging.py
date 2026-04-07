"""Persistent operation log helpers for resumable SSID consolidation work."""

from __future__ import annotations

from .models import OperationLogEntry
from .store import SQLiteStore

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS operations_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phase INTEGER,
    site_id TEXT,
    action TEXT,
    status TEXT,
    message TEXT,
    timestamp TEXT
)
"""
INSERT_ENTRY_SQL = """
INSERT INTO operations_log (phase, site_id, action, status, message, timestamp)
VALUES (?, ?, ?, ?, ?, ?)
"""
SELECT_BY_PHASE_SQL = """
SELECT id, phase, site_id, action, status, message, timestamp
FROM operations_log
WHERE phase = ?
"""


class OperationsLog(SQLiteStore):
    """Persist resumable SSID consolidation work items in SQLite."""

    def __init__(self, db_path: str | None = None) -> None:
        """Open the operations database and ensure the table exists."""
        super().__init__(db_path=db_path, default_path="data/ssid-consolidation/operations.db")

    def ensure_schema(self) -> None:
        """Create the operations log table when it does not already exist."""
        self._conn.execute(CREATE_TABLE_SQL)
        self._conn.commit()

    def append(self, entry: OperationLogEntry) -> None:
        """Append one typed operations-log entry to the backing database."""
        self._conn.execute(
            INSERT_ENTRY_SQL,
            (
                entry.phase,
                entry.site_id or "",
                entry.action or "",
                entry.status or "",
                entry.message or "",
                entry.timestamp or "",
            ),
        )
        self._conn.commit()

    def query_by_phase(self, phase: int) -> list[OperationLogEntry]:
        """Return typed log entries for one execution phase."""
        cursor = self._conn.execute(SELECT_BY_PHASE_SQL, (phase,))
        return [
            OperationLogEntry(
                id=row[0],
                phase=row[1],
                site_id=row[2],
                action=row[3],
                status=row[4],
                message=row[5],
                timestamp=row[6],
            )
            for row in cursor.fetchall()
        ]
