"""Shared SQLite persistence helpers for SSID consolidation stores."""

from __future__ import annotations

import sqlite3
from pathlib import Path


class SQLiteStore:
    """Provide shared SQLite connection lifecycle management for store classes."""

    def __init__(self, db_path: str | None, default_path: str) -> None:
        """Open the SQLite database and let subclasses create their schema."""
        self.db_path = Path(db_path) if db_path else Path(default_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self.ensure_schema()

    def ensure_schema(self) -> None:
        """Create or update the schema required by the concrete store."""
        raise NotImplementedError

    def close(self) -> None:
        """Close the underlying SQLite connection."""
        self._conn.close()
