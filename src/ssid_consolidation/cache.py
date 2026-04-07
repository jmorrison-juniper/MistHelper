"""SQLite-backed cache helpers for phase 1 SSID consolidation rows."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from json import JSONDecodeError
from typing import Any

from .store import SQLiteStore

LOGGER = logging.getLogger(__name__)
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS phase1_cache (
    site_id TEXT PRIMARY KEY,
    row_json TEXT,
    collected_at TEXT
)
"""
UPSERT_ROW_SQL = """
INSERT OR REPLACE INTO phase1_cache (site_id, row_json, collected_at)
VALUES (?, ?, ?)
"""
SELECT_ALL_SQL = "SELECT row_json, collected_at FROM phase1_cache"
CLEAR_SQL = "DELETE FROM phase1_cache"


class CacheManager(SQLiteStore):
    """Store and retrieve normalized phase 1 rows in a local SQLite cache."""

    def __init__(self, db_path: str | None = None) -> None:
        """Open the cache database and ensure the backing table exists."""
        super().__init__(db_path=db_path, default_path="data/ssid-consolidation/cache.db")

    def ensure_schema(self) -> None:
        """Create the cache table when it does not already exist."""
        self._conn.execute(CREATE_TABLE_SQL)
        self._conn.commit()

    def _default_timestamp(self) -> str:
        """Return a UTC timestamp used when callers do not provide one."""
        return datetime.now(UTC).isoformat()

    def save_rows(self, rows: list[dict[str, Any]], collected_at: str | None = None) -> None:
        """Persist the supplied rows into the cache using site ID as the natural key."""
        timestamp = collected_at or self._default_timestamp()
        for row in rows:
            site_id = row.get("site_id") or row.get("site", "")
            self._conn.execute(
                UPSERT_ROW_SQL,
                (site_id, json.dumps(row), timestamp),
            )
        self._conn.commit()

    def _decode_row(self, row_json: str) -> dict[str, Any] | None:
        """Decode one cached JSON payload into a dictionary, or `None` on failure."""
        try:
            decoded = json.loads(row_json)
        except (JSONDecodeError, TypeError):
            LOGGER.exception("CacheManager: failed to decode cached row JSON")
            return None
        if not isinstance(decoded, dict):
            LOGGER.warning("CacheManager: cached row was not a dictionary payload")
            return None
        return decoded

    def get_all(self) -> list[dict[str, Any]]:
        """Return all cached rows with their collection timestamps."""
        out: list[dict[str, Any]] = []
        for row_json, collected_at in self._conn.execute(SELECT_ALL_SQL).fetchall():
            data = self._decode_row(row_json)
            if data is not None:
                out.append({"data": data, "collected_at": collected_at})
        return out

    def clear(self) -> None:
        """Delete all cached phase 1 rows."""
        self._conn.execute(CLEAR_SQL)
        self._conn.commit()
