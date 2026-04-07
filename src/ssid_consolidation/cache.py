import sqlite3
import json
from pathlib import Path
from datetime import datetime
import logging


class CacheManager:
    """Simple SQLite-backed cache for Phase 1 results."""

    def __init__(self, db_path: str = None):
        self.db_path = Path(db_path) if db_path else Path("data/ssid-consolidation/cache.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._ensure_table()

    def _ensure_table(self):
        c = self._conn.cursor()
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS phase1_cache (
                site_id TEXT PRIMARY KEY,
                row_json TEXT,
                collected_at TEXT
            )
            """
        )
        self._conn.commit()

    def save_rows(self, rows, collected_at: str = None):
        collected_at = collected_at or datetime.utcnow().isoformat()
        c = self._conn.cursor()
        for row in rows:
            site_id = row.get("site_id") or row.get("site", "")
            c.execute(
                "INSERT OR REPLACE INTO phase1_cache (site_id, row_json, collected_at) VALUES (?, ?, ?)",
                (site_id, json.dumps(row), collected_at),
            )
        self._conn.commit()

    def get_all(self):
        c = self._conn.cursor()
        c.execute("SELECT row_json, collected_at FROM phase1_cache")
        out = []
        for row_json, collected_at in c.fetchall():
            try:
                data = json.loads(row_json)
            except Exception:
                logging.exception("Failed to decode cached row_json")
                continue
            out.append({"data": data, "collected_at": collected_at})
        return out

    def clear(self):
        c = self._conn.cursor()
        c.execute("DELETE FROM phase1_cache")
        self._conn.commit()
