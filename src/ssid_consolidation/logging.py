import sqlite3
from pathlib import Path
from dataclasses import asdict
import logging


class OperationsLog:
    """Simple persistent operations log for resumable work units."""

    def __init__(self, db_path: str = None):
        self.db_path = Path(db_path) if db_path else Path("data/ssid-consolidation/operations.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._ensure_table()

    def _ensure_table(self):
        cur = self._conn.cursor()
        cur.execute(
            """
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
        )
        self._conn.commit()

    def append(self, phase: int, site_id: str, action: str, status: str, message: str = None, timestamp: str = None):
        ts = timestamp or ""
        cur = self._conn.cursor()
        cur.execute(
            "INSERT INTO operations_log (phase, site_id, action, status, message, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
            (phase, site_id, action, status, message or "", ts),
        )
        self._conn.commit()

    def query_by_phase(self, phase: int):
        cur = self._conn.cursor()
        cur.execute("SELECT id, phase, site_id, action, status, message, timestamp FROM operations_log WHERE phase = ?", (phase,))
        return cur.fetchall()
