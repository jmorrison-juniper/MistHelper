"""One-time migration utility: SQLite -> polyglot backends.

Reads the existing data/mist_data.db, classifies tables by primary key
strategy from ENDPOINT_PRIMARY_KEY_STRATEGIES, and exports:
  - natural_pk / auto_increment_with_unique -> ArangoDB
  - composite_pk -> Redis TimeSeries

Usage:
    python scripts/migrate_sqlite_to_polyglot.py [--dry-run] [--db-path data/mist_data.db]

Requires ArangoDB and Redis Stack to be running (use compose.yml).
"""

from __future__ import annotations

import argparse
import logging
import os
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("migrate_sqlite_to_polyglot")


class MigrationConfig:
    """Configuration for the migration run."""

    def __init__(self, db_path: str, dry_run: bool = False):
        self.db_path = db_path
        self.dry_run = dry_run


class StrategyLoader:
    """Load ENDPOINT_PRIMARY_KEY_STRATEGIES from MistHelper.py."""

    @staticmethod
    def load_strategies() -> dict:
        """Import strategies dict from MistHelper module."""
        try:
            import MistHelper

            strategies = getattr(MistHelper, "ENDPOINT_PRIMARY_KEY_STRATEGIES", {})
            logger.info(
                "Loaded %d endpoint strategies from MistHelper",
                len(strategies),
            )
            return strategies
        except ImportError:
            logger.error("Cannot import MistHelper.py -- run from project root")
            sys.exit(1)


class TableClassifier:
    """Classify SQLite tables by their PK strategy type."""

    ARANGO_TYPES = {"natural_pk", "auto_increment_with_unique"}
    REDIS_TYPES = {"composite_pk"}

    def __init__(self, strategies: dict):
        self._strategies = strategies
        self._reverse_map = self._build_reverse_map()

    def _build_reverse_map(self) -> dict:
        """Map table names to their strategy config."""
        reverse = {}
        for api_name, strategy in self._strategies.items():
            table_name = api_name
            reverse[table_name] = strategy
        return reverse

    def classify(self, table_name: str) -> str | None:
        """Return 'arango', 'redis', or None for unknown tables."""
        strategy = self._reverse_map.get(table_name)
        if not strategy:
            return None
        pk_type = strategy.get("type", "")
        if pk_type in self.ARANGO_TYPES:
            return "arango"
        if pk_type in self.REDIS_TYPES:
            return "redis"
        return None


class SqliteReader:
    """Read data from SQLite database."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._connection: sqlite3.Connection | None = None

    def connect(self) -> None:
        """Open read-only connection to SQLite."""
        if not os.path.exists(self.db_path):
            logger.error("Database not found: %s", self.db_path)
            sys.exit(1)
        uri = f"file:{self.db_path}?mode=ro"
        self._connection = sqlite3.connect(uri, uri=True)
        self._connection.row_factory = sqlite3.Row
        logger.info("Connected to SQLite: %s", self.db_path)

    def list_tables(self) -> list[str]:
        """Return list of user table names."""
        cursor = self._connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master " "WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        return [row[0] for row in cursor.fetchall()]

    def read_table(self, table_name: str) -> list[dict]:
        """Read all rows from a table as list of dicts."""
        cursor = self._connection.cursor()
        cursor.execute(f'SELECT * FROM "{table_name}"')  # nosec B608 - name comes from sqlite_master
        columns = [desc[0] for desc in cursor.description]
        rows = []
        for row in cursor.fetchall():
            rows.append(dict(zip(columns, row, strict=True)))
        return rows

    def close(self) -> None:
        """Close the SQLite connection."""
        if self._connection:
            self._connection.close()


class MigrationRunner:
    """Orchestrate the full migration pipeline."""

    def __init__(self, config: MigrationConfig):
        self._config = config
        self._strategies: dict = {}
        self._classifier: TableClassifier | None = None
        self._reader: SqliteReader | None = None

    def run(self) -> None:
        """Execute the migration end-to-end."""
        self._strategies = StrategyLoader.load_strategies()
        self._classifier = TableClassifier(self._strategies)
        self._reader = SqliteReader(self._config.db_path)
        self._reader.connect()

        try:
            self._execute_migration()
        finally:
            self._reader.close()

    def _execute_migration(self) -> None:
        """Classify tables and export to appropriate backends."""
        tables = self._reader.list_tables()
        logger.info("Found %d tables in SQLite", len(tables))

        classification = self._classify_all(tables)
        self._print_summary(classification)

        if self._config.dry_run:
            logger.info("DRY RUN -- no data written to backends")
            return

        self._export_arango(classification.get("arango", []))
        self._export_redis(classification.get("redis", []))
        logger.info("Migration complete")

    def _classify_all(self, tables: list[str]) -> dict:
        """Group tables by target backend."""
        result: dict[str, list[str]] = {
            "arango": [],
            "redis": [],
            "unknown": [],
        }
        for table in tables:
            target = self._classifier.classify(table)
            if target:
                result[target].append(table)
            else:
                result["unknown"].append(table)
        return result

    def _print_summary(self, classification: dict) -> None:
        """Log migration plan summary."""
        logger.info("--- Migration Plan ---")
        logger.info("ArangoDB targets: %d tables", len(classification["arango"]))
        for table in classification["arango"]:
            logger.info("  -> %s", table)
        logger.info("Redis TS targets: %d tables", len(classification["redis"]))
        for table in classification["redis"]:
            logger.info("  -> %s", table)
        logger.info("Unclassified: %d tables", len(classification["unknown"]))
        for table in classification["unknown"]:
            logger.info("  ?? %s (skipped)", table)

    def _export_arango(self, tables: list[str]) -> None:
        """Export document tables to ArangoDB."""
        from src.db import DatabaseConfig
        from src.db.arango_writer import ArangoDBWriter

        config = DatabaseConfig.from_env()
        writer = ArangoDBWriter(config)
        try:
            for table in tables:
                rows = self._reader.read_table(table)
                if not rows:
                    logger.info("Skipping empty table: %s", table)
                    continue
                strategy = self._strategies.get(table, {})
                result = writer.write(rows, table, strategy)
                logger.info(
                    "ArangoDB <- %s: %d written, %d failed",
                    table,
                    result.records_written,
                    result.records_failed,
                )
        finally:
            writer.close()

    def _export_redis(self, tables: list[str]) -> None:
        """Export time-series tables to Redis."""
        from src.db import DatabaseConfig
        from src.db.redis_writer import RedisTimeSeriesWriter

        config = DatabaseConfig.from_env()
        writer = RedisTimeSeriesWriter(config)
        try:
            for table in tables:
                rows = self._reader.read_table(table)
                if not rows:
                    logger.info("Skipping empty table: %s", table)
                    continue
                strategy = self._strategies.get(table, {})
                result = writer.write(rows, table, strategy)
                logger.info(
                    "Redis TS <- %s: %d written, %d failed",
                    table,
                    result.records_written,
                    result.records_failed,
                )
        finally:
            writer.close()


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Migrate SQLite data to polyglot backends")
    parser.add_argument(
        "--db-path",
        default="data/mist_data.db",
        help="Path to SQLite database (default: data/mist_data.db)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show migration plan without writing data",
    )
    return parser.parse_args()


def main() -> None:
    """Entry point for the migration utility."""
    args = parse_args()
    config = MigrationConfig(db_path=args.db_path, dry_run=args.dry_run)
    runner = MigrationRunner(config)
    runner.run()


if __name__ == "__main__":
    main()
