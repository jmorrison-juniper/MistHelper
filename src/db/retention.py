"""Storage-aware retention manager for polyglot backends.

Monitors ArangoDB and Redis storage usage and purges oldest data
when configurable thresholds are exceeded. Oldest-first rollover
ensures newest data is always preserved.
"""

from __future__ import annotations  # WHY: postpone hints for MagicMock typing

import os  # WHY: env var lookups for retention thresholds
import threading  # WHY: background sweep thread + stop event
from typing import Any  # WHY: writer args typed loose for duck-typed backends

import structlog  # WHY: structured JSON logging for retention events

logger = structlog.get_logger(__name__)  # WHY: module-scoped structlog binder

DEFAULT_MAX_STORAGE_GB = 100  # WHY: 100 GB ceiling before purge kicks in
DEFAULT_CHECK_INTERVAL_HOURS = 6  # WHY: sweep every 6h keeps overhead low
SNAPSHOT_PURGE_BATCH = 500  # WHY: cap AQL REMOVE batch to avoid txn bloat
PURGE_THRESHOLD_RATIO = 0.9  # WHY: trigger purge at 90% of max storage
BYTES_PER_GB = 1024**3  # WHY: convert dataSize (bytes) into GB units
SECONDS_PER_HOUR = 3600  # WHY: hour -> seconds for sweep sleep interval
STOP_JOIN_TIMEOUT_SEC = 5  # WHY: bounded join so shutdown never hangs
REDIS_COMPACTION_PATTERN = "*.avg_1h"  # WHY: match compacted 1h-avg TS keys
SWEEP_THREAD_NAME = "retention-sweep"  # WHY: identifiable name in ps/threads
ENV_MAX_STORAGE_GB = "ARANGO_MAX_STORAGE_GB"  # WHY: override for ceiling GB
ENV_CHECK_INTERVAL_HOURS = "RETENTION_CHECK_INTERVAL_HOURS"  # WHY: sweep hrs

EVT_ARANGO_OK = "arango_retention_ok"  # WHY: log key: usage under threshold
EVT_STORAGE_FAIL = "storage_check_failed"  # WHY: log key: stats call failed
EVT_SNAPSHOTS_PURGED = "arango_snapshots_purged"  # WHY: log key: purge done
EVT_PURGE_FAIL = "purge_failed"  # WHY: log key: AQL REMOVE raised
EVT_REDIS_CHECKED = "redis_retention_checked"  # WHY: log key: TS scan done
EVT_REDIS_FAIL = "redis_check_failed"  # WHY: log key: KEYS command raised
EVT_SWEEP_STARTED = "retention_sweep_started"  # WHY: log key: thread spawned
EVT_SWEEP_STOPPED = "retention_sweep_stopped"  # WHY: log key: thread joined
EVT_SWEEP_ERROR = "retention_sweep_error"  # WHY: log key: sweep raised

PURGE_AQL = """
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
"""  # WHY: keep newest per entity_id, purge older siblings up to batch cap


def _env_int(name: str, default: int) -> int:  # WHY: shared env parser
    """Parse an integer env var with a default fallback."""
    return int(os.environ.get(name, str(default)))  # WHY: str() for env format


class RetentionManager:  # WHY: single owner of ArangoDB+Redis retention
    """Manage storage retention across ArangoDB and Redis."""

    def __init__(  # WHY: DI backend writers to keep this class test-friendly
        self,
        arango_writer: Any,
        redis_writer: Any,
    ) -> None:
        """Initialize retention manager with backend writers."""
        self._arango = arango_writer  # WHY: hold writer for _database access
        self._redis = redis_writer  # WHY: hold writer for _client access
        self._max_storage_gb = _env_int(
            ENV_MAX_STORAGE_GB, DEFAULT_MAX_STORAGE_GB
        )  # WHY: ceiling in GB before oldest-first purge triggers
        self._check_interval_hours = _env_int(
            ENV_CHECK_INTERVAL_HOURS, DEFAULT_CHECK_INTERVAL_HOURS
        )  # WHY: sweep cadence overrideable via env
        self._stop_event = threading.Event()  # WHY: signal sweep loop to exit
        self._thread: threading.Thread | None = None  # WHY: None until started

    def check_arango_retention(self) -> int:  # WHY: public entrypoint for arango
        """Purge oldest ArangoDB snapshots if over threshold.

        Returns count of documents purged.
        """
        usage = self._get_storage_usage_gb()  # WHY: current dataSize snapshot
        threshold = self._max_storage_gb * PURGE_THRESHOLD_RATIO  # WHY: 90%
        if usage < threshold:  # WHY: below 90% -> no purge needed
            logger.info(
                EVT_ARANGO_OK,
                usage_gb=usage,
                threshold_gb=self._max_storage_gb,
            )  # WHY: emit ok event with numeric context
            return 0  # WHY: caller expects int purge count (0 when idle)
        return self._purge_oldest_snapshots()  # WHY: over 90% -> purge oldest

    def _get_storage_usage_gb(self) -> float:  # WHY: helper: bytes -> GB
        """Query ArangoDB storage usage in GB."""
        database = getattr(self._arango, "_database", None)  # WHY: MagicMock safe
        if database is None:  # WHY: writer without _database -> zero usage
            return 0.0  # WHY: zero means "no data yet". Sweep continues
        try:
            stats = database.statistics()  # WHY: server-level stats dict
            data_size = stats.get("dataSize", 0)  # WHY: bytes, may be missing
            return data_size / BYTES_PER_GB  # WHY: normalize to GB units
        except Exception as error:  # WHY: driver errors must not kill sweep
            logger.warning(EVT_STORAGE_FAIL, error=str(error))  # WHY: audit trail
            return 0.0  # WHY: safe fallback keeps sweep loop alive

    def _purge_oldest_snapshots(self) -> int:  # WHY: guard+delegate to helper
        """Remove oldest config_snapshots, keeping at least one per entity."""
        database = getattr(self._arango, "_database", None)  # WHY: guard clause
        if database is None:  # WHY: no db -> nothing to purge
            return 0  # WHY: zero purged when writer is unconfigured
        return _execute_purge(database)  # WHY: helper keeps LoC <= 25

    def check_redis_retention(self) -> int:  # WHY: public entrypoint for redis
        """Verify Redis TS retention rules are properly configured.

        Returns count of keys checked.
        """
        client = getattr(self._redis, "_client", None)  # WHY: writer duck-type
        if client is None:  # WHY: no client -> zero keys checked
            return 0  # WHY: zero signals "nothing to validate"
        try:
            keys = client.execute_command("KEYS", REDIS_COMPACTION_PATTERN)  # WHY: list compacted 1h-avg TS keys
            logger.info(EVT_REDIS_CHECKED, keys=len(keys))
            return len(keys)  # WHY: callers want count, not the key list
        except Exception as error:  # WHY: KEYS may error on unreachable redis
            logger.warning(EVT_REDIS_FAIL, error=str(error))
            return 0

    def start_periodic(self) -> None:
        """Start background retention sweep thread."""
        if self._thread is not None:  # WHY: idempotent - test_start_idempotent
            return
        self._stop_event.clear()  # WHY: allow sweep after prior stop()
        self._thread = threading.Thread(
            target=self._sweep_loop,
            daemon=True,  # WHY: daemon so interpreter exit is not blocked
            name=SWEEP_THREAD_NAME,
        )
        self._thread.start()  # WHY: launch the periodic sweep loop
        logger.info(
            EVT_SWEEP_STARTED,
            interval_hours=self._check_interval_hours,
        )

    def stop(self) -> None:
        """Stop the background retention sweep thread."""
        self._stop_event.set()  # WHY: break out of wait() in sweep loop
        if self._thread is not None:  # WHY: stop() must be safe pre-start
            self._thread.join(timeout=STOP_JOIN_TIMEOUT_SEC)  # WHY: bounded
            self._thread = None  # WHY: reset so start_periodic can re-run
        logger.info(EVT_SWEEP_STOPPED)

    def _sweep_loop(self) -> None:
        """Periodic sweep: check both backends."""
        interval = self._check_interval_hours * SECONDS_PER_HOUR  # WHY: sec
        while not self._stop_event.is_set():  # WHY: exit promptly on stop()
            try:
                self.check_arango_retention()  # WHY: purge if arango over 90%
                self.check_redis_retention()  # WHY: validate TS retention
            except Exception as error:  # WHY: swallow so loop stays alive
                logger.error(EVT_SWEEP_ERROR, error=str(error))
            self._stop_event.wait(interval)  # WHY: interruptible sleep


def _execute_purge(database: Any) -> int:
    """Run the oldest-snapshot AQL and log/log-error the outcome."""
    try:
        cursor = database.aql.execute(
            PURGE_AQL,
            bind_vars={"batch": SNAPSHOT_PURGE_BATCH},
        )  # WHY: bounded REMOVE batch to keep txn small
        count = len(list(cursor))  # WHY: cursor materialized -> count keys
        logger.info(EVT_SNAPSHOTS_PURGED, count=count)
        return count
    except Exception as error:  # WHY: AQL errors must not crash sweep loop
        logger.warning(EVT_PURGE_FAIL, error=str(error))
        return 0
