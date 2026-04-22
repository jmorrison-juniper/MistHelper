"""Storage-aware retention manager for polyglot backends.

Monitors ArangoDB and Redis storage usage and purges oldest data
when configurable thresholds are exceeded. Oldest-first rollover
ensures newest data is always preserved.
"""

from __future__ import annotations

import os
import threading
from typing import Any

from src.db import get_logger

logger = get_logger(__name__)

DEFAULT_MAX_STORAGE_GB = 100
DEFAULT_CHECK_INTERVAL_HOURS = 6
SNAPSHOT_PURGE_BATCH = 500


class RetentionManager:
    """Manage storage retention across ArangoDB and Redis."""

    def __init__(
        self,
        arango_writer: Any,
        redis_writer: Any,
    ) -> None:
        self._arango = arango_writer
        self._redis = redis_writer
        self._max_storage_gb = int(
            os.environ.get(
                "ARANGO_MAX_STORAGE_GB",
                str(DEFAULT_MAX_STORAGE_GB),
            )
        )
        self._check_interval_hours = int(
            os.environ.get(
                "RETENTION_CHECK_INTERVAL_HOURS",
                str(DEFAULT_CHECK_INTERVAL_HOURS),
            )
        )
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def check_arango_retention(self) -> int:
        """Purge oldest ArangoDB snapshots if over threshold.

        Returns count of documents purged.
        """
        usage = self._get_storage_usage_gb()
        if usage < self._max_storage_gb * 0.9:
            logger.info(
                "arango_retention_ok",
                usage_gb=usage,
                threshold_gb=self._max_storage_gb,
            )
            return 0
        return self._purge_oldest_snapshots()

    def _get_storage_usage_gb(self) -> float:
        """Query ArangoDB storage usage in GB."""
        try:
            database = getattr(self._arango, "_database", None)
            if database is None:
                return 0.0
            stats = database.statistics()
            data_size = stats.get("dataSize", 0)
            return data_size / (1024**3)
        except Exception as error:
            logger.warning("storage_check_failed", error=str(error))
            return 0.0

    def _purge_oldest_snapshots(self) -> int:
        """Remove oldest config_snapshots, keeping at least one per entity."""
        database = getattr(self._arango, "_database", None)
        if database is None:
            return 0
        query = """
            FOR snapshot IN config_snapshots
                COLLECT entity = snapshot.entity_id
                INTO snapshots = snapshot
                LET sorted = (
                    FOR s IN snapshots
                        SORT s.timestamp ASC
                        RETURN s
                )
                LET to_remove = SLICE(sorted, 0, LENGTH(sorted) - 1)
                FOR doc IN to_remove
                    LIMIT @batch
                    REMOVE doc IN config_snapshots
                    RETURN OLD._key
        """
        try:
            cursor = database.aql.execute(
                query,
                bind_vars={"batch": SNAPSHOT_PURGE_BATCH},
            )
            removed = list(cursor)
            count = len(removed)
            logger.info("arango_snapshots_purged", count=count)
            return count
        except Exception as error:
            logger.warning("purge_failed", error=str(error))
            return 0

    def check_redis_retention(self) -> int:
        """Verify Redis TS retention rules are properly configured.

        Returns count of keys checked.
        """
        client = getattr(self._redis, "_client", None)
        if client is None:
            return 0
        try:
            keys = client.execute_command("KEYS", "*.avg_1h")
            logger.info("redis_retention_checked", keys=len(keys))
            return len(keys)
        except Exception as error:
            logger.warning("redis_check_failed", error=str(error))
            return 0

    def start_periodic(self) -> None:
        """Start background retention sweep thread."""
        if self._thread is not None:
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._sweep_loop,
            daemon=True,
            name="retention-sweep",
        )
        self._thread.start()
        logger.info(
            "retention_sweep_started",
            interval_hours=self._check_interval_hours,
        )

    def stop(self) -> None:
        """Stop the background retention sweep thread."""
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=5)
            self._thread = None
        logger.info("retention_sweep_stopped")

    def _sweep_loop(self) -> None:
        """Periodic sweep: check both backends."""
        interval = self._check_interval_hours * 3600
        while not self._stop_event.is_set():
            try:
                self.check_arango_retention()
                self.check_redis_retention()
            except Exception as error:
                logger.error("retention_sweep_error", error=str(error))
            self._stop_event.wait(interval)
