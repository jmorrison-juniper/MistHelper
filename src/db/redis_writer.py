"""Redis writers for polyglot data routing.

RedisTimeSeriesWriter: Stores numeric metric values as Redis TimeSeries keys
with automatic compaction rules for hourly and daily aggregation.

RedisJSONWriter: Stores composite_pk event documents as Redis JSON with
configurable TTL for fast recent-event queries.

Both use pipelined batch operations for high-throughput bulk imports.
"""

from __future__ import annotations

import os
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import redis

from . import DatabaseConfig, WriteResult, get_logger

RAW_RETENTION_MS = int(os.environ.get("REDIS_RAW_RETENTION_DAYS", "7")) * 86_400_000
HOURLY_RETENTION_MS = 90 * 86_400_000  # 90 days
DAILY_RETENTION_MS = 365 * 86_400_000  # 365 days
REDIS_JSON_TTL_SECONDS = int(os.environ.get("REDIS_JSON_TTL_DAYS", "7")) * 86_400
JSON_PIPELINE_BATCH = 500
HOURLY_BUCKET_MS = 3_600_000  # 1 hour
DAILY_BUCKET_MS = 86_400_000  # 1 day
KEY_CREATION_BATCH = 500
ADD_PIPELINE_BATCH = 10_000

_TOPIC_KEY_PREFIX: dict[str, str] = {
    "client-sessions": "client_stats",
    "device-updowns": "device_events",
    "device-events": "device_events",
    "client-latency": "client_latency",
}


class RedisTimeSeriesWriter:
    """Writes composite_pk data into Redis TimeSeries.

    Performance strategy:
    - Key creation uses pipelined TS.CREATE + CREATERULE batches
    - Data writes use pipelined TS.ADD with DUPLICATE_POLICY LAST
    - Numeric field extraction runs in thread pool across records
    """

    def __init__(self, config: DatabaseConfig) -> None:
        """Initialize Redis TimeSeries connection and verify module."""
        self._log = get_logger("redis_writer")
        self._client = redis.Redis(
            host=config.redis_host,
            port=config.redis_port,
            password=config.redis_password or None,
            decode_responses=True,
        )
        self._verify_timeseries_module()
        self._ts = self._client.ts()
        self._created_keys: set[str] = set()
        self._log.info("redis_connected", host=config.redis_host)

    def _verify_timeseries_module(self) -> None:
        modules: list[dict[str, Any]] = self._client.module_list()  # type: ignore[assignment]
        names = [
            m.get("name", b"").lower() if isinstance(m.get("name"), str) else m.get("name", b"").decode().lower()
            for m in modules
        ]
        if "timeseries" not in names:
            raise RuntimeError("Redis TimeSeries module not loaded. " "Use redis/redis-stack-server image.")

    def write(
        self,
        data: list[dict[str, Any]],
        api_function_name: str,
        strategy: dict[str, Any],
    ) -> WriteResult:
        """Write numeric fields as TimeSeries data points.

        Three-phase pipeline approach:
        1. Extract all (key, value) pairs using thread pool
        2. Batch-create missing keys with compaction rules
        3. Pipeline all TS.ADD commands
        """
        if not data:
            return WriteResult(
                success=True,
                backend="redis",
                records_written=0,
                records_failed=0,
            )

        primary_keys = strategy.get("primary_key", [])
        entity_key_field = self._pick_entity_field(primary_keys)
        ts_value_fields = strategy.get("ts_value_fields")
        ts_label_fields = strategy.get("ts_label_fields")

        adds, key_records = self._extract_all_adds(
            data,
            api_function_name,
            primary_keys,
            entity_key_field,
            ts_value_fields,
        )
        self._batch_ensure_keys(key_records, api_function_name, ts_label_fields)
        written, failed = self._execute_pipeline(adds)

        return WriteResult(
            success=failed == 0,
            backend="redis",
            records_written=written,
            records_failed=failed,
        )

    def _extract_all_adds(
        self,
        data: list[dict[str, Any]],
        api_function_name: str,
        primary_keys: list[str],
        entity_key_field: str,
        ts_value_fields: list[str] | None = None,
    ) -> tuple[list[tuple[str, float]], dict[str, dict[str, Any]]]:
        """Extract (ts_key, value) pairs and first-seen record per key.

        Uses a thread pool to parallelize numeric extraction across
        record chunks for large datasets (>1000 records).
        """
        if len(data) <= 1000:
            return self._extract_chunk(
                data,
                api_function_name,
                primary_keys,
                entity_key_field,
                ts_value_fields,
            )

        workers = min(8, os.cpu_count() or 4)
        chunk_size = max(1, len(data) // workers)
        chunks = [data[i : i + chunk_size] for i in range(0, len(data), chunk_size)]

        all_adds: list[tuple[str, float]] = []
        key_records: dict[str, dict[str, Any]] = {}

        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [
                pool.submit(
                    self._extract_chunk,
                    chunk,
                    api_function_name,
                    primary_keys,
                    entity_key_field,
                    ts_value_fields,
                )
                for chunk in chunks
            ]
            for future in futures:
                chunk_adds, chunk_keys = future.result()
                all_adds.extend(chunk_adds)
                key_records.update(chunk_keys)

        self._log.info(
            "extraction_complete",
            data_points=len(all_adds),
            unique_keys=len(key_records),
            workers=workers,
        )
        return all_adds, key_records

    def _extract_chunk(
        self,
        records: list[dict[str, Any]],
        api_function_name: str,
        primary_keys: list[str],
        entity_key_field: str,
        ts_value_fields: list[str] | None = None,
    ) -> tuple[list[tuple[str, float]], dict[str, dict[str, Any]]]:
        """Extract adds and key->record map from a chunk of records."""
        adds: list[tuple[str, float]] = []
        key_records: dict[str, dict[str, Any]] = {}
        for record in records:
            entity_id = str(record.get(entity_key_field, "unknown"))
            if ts_value_fields:
                numeric = self._extract_listed_fields(record, ts_value_fields)
            else:
                numeric = self._extract_numeric(record, primary_keys)
            for field_name, value in numeric.items():
                ts_key = f"{api_function_name}:{entity_id}:{field_name}"
                adds.append((ts_key, value))
                if ts_key not in key_records:
                    key_records[ts_key] = record
        return adds, key_records

    def _batch_ensure_keys(
        self,
        key_records: dict[str, dict[str, Any]],
        api_function_name: str,
        ts_label_fields: list[str] | None = None,
    ) -> None:
        """Create all missing TS keys and compaction rules via pipeline."""
        new_keys = {k: v for k, v in key_records.items() if k not in self._created_keys}
        if not new_keys:
            return

        keys_list = list(new_keys.items())
        for start in range(0, len(keys_list), KEY_CREATION_BATCH):
            batch = keys_list[start : start + KEY_CREATION_BATCH]
            self._pipeline_create_keys(batch, api_function_name, ts_label_fields)

        self._log.info("keys_created", count=len(new_keys))

    def _pipeline_create_keys(
        self,
        batch: list[tuple[str, dict[str, Any]]],
        api_function_name: str,
        ts_label_fields: list[str] | None = None,
    ) -> None:
        """Pipeline-create a batch of TS keys with compaction."""
        pipe = self._client.pipeline(transaction=False)

        for ts_key, record in batch:
            labels = self._build_labels(record, api_function_name, ts_key, ts_label_fields)
            label_args = []
            for label_key, label_val in labels.items():
                label_args.extend([label_key, label_val])
            pipe.execute_command(
                "TS.CREATE",
                ts_key,
                "RETENTION",
                RAW_RETENTION_MS,
                "DUPLICATE_POLICY",
                "LAST",
                "LABELS",
                *label_args,
            )

        results = pipe.execute(raise_on_error=False)
        self._pipeline_create_compaction(batch, results)

    def _pipeline_create_compaction(
        self,
        batch: list[tuple[str, dict[str, Any]]],
        create_results: list,
    ) -> None:
        """Create compaction keys and rules for successfully created keys."""
        pipe = self._client.pipeline(transaction=False)
        pending: list[str] = []

        for idx, (ts_key, _record) in enumerate(batch):
            result = create_results[idx]
            is_new = not isinstance(result, Exception)
            is_exists = isinstance(result, redis.ResponseError) and "already exists" in str(result).lower()
            if not is_new and not is_exists:
                continue

            hourly = f"{ts_key}:avg_1h"
            daily = f"{ts_key}:avg_1d"
            pipe.execute_command(
                "TS.CREATE",
                hourly,
                "RETENTION",
                HOURLY_RETENTION_MS,
            )
            pipe.execute_command(
                "TS.CREATE",
                daily,
                "RETENTION",
                DAILY_RETENTION_MS,
            )
            pipe.execute_command(
                "TS.CREATERULE",
                ts_key,
                hourly,
                "AGGREGATION",
                "avg",
                HOURLY_BUCKET_MS,
            )
            pipe.execute_command(
                "TS.CREATERULE",
                ts_key,
                daily,
                "AGGREGATION",
                "avg",
                DAILY_BUCKET_MS,
            )
            pending.append(ts_key)

        if pending:
            pipe.execute(raise_on_error=False)

        for ts_key in pending:
            self._created_keys.add(ts_key)
            self._created_keys.add(f"{ts_key}:avg_1h")
            self._created_keys.add(f"{ts_key}:avg_1d")

    def _execute_pipeline(
        self,
        adds: list[tuple[str, float]],
    ) -> tuple[int, int]:
        """Execute TS.ADD commands in batched pipelines."""
        written = 0
        failed = 0
        for start in range(0, len(adds), ADD_PIPELINE_BATCH):
            batch = adds[start : start + ADD_PIPELINE_BATCH]
            pipe = self._client.pipeline(transaction=False)
            for ts_key, value in batch:
                pipe.execute_command(
                    "TS.ADD",
                    ts_key,
                    "*",
                    value,
                    "DUPLICATE_POLICY",
                    "LAST",
                )
            results = pipe.execute(raise_on_error=False)
            for idx, result in enumerate(results):
                if isinstance(result, Exception):
                    failed += 1
                    self._log.error(
                        "ts_add_failed",
                        key=batch[idx][0],
                        error=str(result),
                    )
                else:
                    written += 1
        return written, failed

    def _ensure_key_single(
        self,
        ts_key: str,
        record: dict[str, Any],
        api_function_name: str,
    ) -> None:
        """Create a single TimeSeries key (used by webhook path)."""
        if ts_key in self._created_keys:
            return
        labels = self._build_labels(record, api_function_name, ts_key)
        try:
            self._ts.create(
                ts_key,
                retention_msecs=RAW_RETENTION_MS,
                labels=labels,
                duplicate_policy="last",
            )
        except redis.ResponseError as error:
            if "already exists" not in str(error).lower():
                raise
        self._ensure_single_compaction(ts_key)
        self._created_keys.add(ts_key)

    def _ensure_single_compaction(self, source_key: str) -> None:
        """Create compaction rules for a single key (webhook path)."""
        hourly_key = f"{source_key}:avg_1h"
        daily_key = f"{source_key}:avg_1d"

        if hourly_key in self._created_keys:
            return

        for dest_key, retention, bucket in [
            (hourly_key, HOURLY_RETENTION_MS, HOURLY_BUCKET_MS),
            (daily_key, DAILY_RETENTION_MS, DAILY_BUCKET_MS),
        ]:
            try:
                self._ts.create(dest_key, retention_msecs=retention)
            except redis.ResponseError as error:
                if "already exists" not in str(error).lower():
                    raise
            try:
                self._ts.createrule(source_key, dest_key, "avg", bucket)
            except redis.ResponseError as error:
                if "already exists" not in str(error).lower():
                    raise

        self._created_keys.add(hourly_key)
        self._created_keys.add(daily_key)

    def ingest_webhook(
        self,
        events: list[dict],
        topic: str,
    ) -> int:
        """Ingest webhook stats events into Redis TimeSeries.

        Returns the count of successfully written data points.
        """
        written = 0
        key_prefix = _TOPIC_KEY_PREFIX.get(topic, topic)
        pipe = self._client.pipeline(transaction=False)
        timestamp_ms = int(time.time() * 1000)

        for event in events:
            entity_id = str(event.get("mac", event.get("device_id", "unknown")))
            numeric = self._extract_numeric(event, ["mac", "device_id"])
            for field_name, value in numeric.items():
                ts_key = f"{key_prefix}:{entity_id}:{field_name}"
                self._ensure_key_single(
                    ts_key,
                    event,
                    key_prefix,
                )
                pipe.execute_command(
                    "TS.ADD",
                    ts_key,
                    timestamp_ms,
                    value,
                    "DUPLICATE_POLICY",
                    "LAST",
                )
                written += 1

        if written > 0:
            pipe.execute()
            self._log.info(
                "webhook_ingested",
                topic=topic,
                points=written,
            )
        return written

    def close(self) -> None:
        """Close the Redis connection."""
        self._client.close()
        self._log.info("redis_disconnected")

    @staticmethod
    def _pick_entity_field(primary_keys: list[str]) -> str:
        """Choose the entity identifier from PK fields."""
        preferred = ["device_id", "site_id", "org_id", "mac", "id"]
        for field in preferred:
            if field in primary_keys:
                return field
        return primary_keys[0] if primary_keys else "id"

    @staticmethod
    def _extract_numeric(
        record: dict[str, Any],
        exclude_keys: list[str],
    ) -> dict[str, float]:
        """Return only numeric (int/float) fields, excluding PKs."""
        result: dict[str, float] = {}
        for key, value in record.items():
            if key in exclude_keys:
                continue
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                result[key] = float(value)
        return result

    @staticmethod
    def _extract_listed_fields(
        record: dict[str, Any],
        value_fields: list[str],
    ) -> dict[str, float]:
        """Extract only named fields that have numeric values."""
        result: dict[str, float] = {}
        for field in value_fields:
            value = record.get(field)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                result[field] = float(value)
        return result

    @staticmethod
    def _build_labels(
        record: dict[str, Any],
        api_function_name: str,
        ts_key: str,
        ts_label_fields: list[str] | None = None,
    ) -> dict[str, str]:
        """Build TimeSeries labels from record metadata."""
        parts = ts_key.rsplit(":", 1)
        metric_name = parts[-1] if len(parts) > 1 else ts_key
        labels: dict[str, str] = {
            "api_function": api_function_name,
            "metric_name": metric_name,
        }
        if ts_label_fields:
            for field in ts_label_fields:
                if field in record:
                    labels[field] = str(record[field])
        else:
            for field in ("org_id", "site_id", "device_id"):
                if field in record:
                    labels[field] = str(record[field])
        return labels


class RedisJSONWriter:
    """Writes composite_pk data as Redis JSON documents with TTL.

    Stores full unflattened API responses as JSON documents for fast
    recent-event queries. Documents expire after a configurable TTL
    (default 7 days). ArangoDB serves as the long-term archive.
    """

    def __init__(self, config: DatabaseConfig) -> None:
        """Initialize Redis JSON connection and verify module."""
        self._log = get_logger("redis_json_writer")
        self._client = redis.Redis(
            host=config.redis_host,
            port=config.redis_port,
            password=config.redis_password or None,
            decode_responses=True,
        )
        self._verify_json_module()
        self._log.info("redis_json_connected", host=config.redis_host)

    def _verify_json_module(self) -> None:
        """Check that the ReJSON module is loaded."""
        modules: list[dict[str, Any]] = self._client.module_list()  # type: ignore[assignment]
        names = [
            m.get("name", b"").lower() if isinstance(m.get("name"), str) else m.get("name", b"").decode().lower()
            for m in modules
        ]
        if "rejson" not in names and "redisjson" not in names:
            raise RuntimeError("Redis JSON module not loaded. Use redis/redis-stack-server image.")

    def write(
        self,
        data: list[dict[str, Any]],
        api_function_name: str,
        strategy: dict[str, Any],
    ) -> WriteResult:
        """Write records as JSON documents with TTL via pipeline."""
        if not data:
            return WriteResult(
                success=True,
                backend="redis_json",
                records_written=0,
                records_failed=0,
            )

        pk_fields = strategy.get("primary_key", [])
        written = 0
        failed = 0

        for start in range(0, len(data), JSON_PIPELINE_BATCH):
            batch = data[start : start + JSON_PIPELINE_BATCH]
            batch_ok, batch_fail = self._pipeline_write_batch(batch, api_function_name, pk_fields)
            written += batch_ok
            failed += batch_fail

        self._log.info(
            "json_write_complete",
            endpoint=api_function_name,
            written=written,
            failed=failed,
        )
        return WriteResult(
            success=failed == 0,
            backend="redis_json",
            records_written=written,
            records_failed=failed,
        )

    def _pipeline_write_batch(
        self,
        batch: list[dict[str, Any]],
        api_function_name: str,
        pk_fields: list[str],
    ) -> tuple[int, int]:
        """Pipeline JSON.SET + EXPIRE for a batch of records."""
        pipe = self._client.pipeline(transaction=False)
        for record in batch:
            key = self._build_key(api_function_name, record, pk_fields)
            pipe.json().set(key, "$", record)
            pipe.expire(key, REDIS_JSON_TTL_SECONDS)

        results = pipe.execute(raise_on_error=False)
        written = 0
        failed = 0
        for idx in range(0, len(results), 2):
            if isinstance(results[idx], Exception):
                failed += 1
                self._log.error(
                    "json_set_failed",
                    error=str(results[idx]),
                )
            else:
                written += 1
        return written, failed

    @staticmethod
    def _build_key(
        endpoint: str,
        record: dict[str, Any],
        pk_fields: list[str],
    ) -> str:
        """Build Redis key from endpoint name and PK field values."""
        parts = [endpoint]
        for field in pk_fields:
            parts.append(str(record.get(field, "unknown")))
        return ":".join(parts)

    def close(self) -> None:
        """Close the Redis connection."""
        self._client.close()
        self._log.info("redis_json_disconnected")
