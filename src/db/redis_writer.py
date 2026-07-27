"""Redis writers for polyglot data routing.

RedisTimeSeriesWriter: Stores numeric metric values as Redis TimeSeries keys
with automatic compaction rules for hourly and daily aggregation.

RedisJSONWriter: Stores composite_pk event documents as Redis JSON with
configurable TTL for fast recent-event queries.

Both use pipelined batch operations for high-throughput bulk imports.
"""

from __future__ import annotations  # WHY: postpone annotations for cross-version dataclass slots.

import os  # WHY: read env-driven retention/TTL knobs at import time.
import socket  # WHY: pre-flight DNS resolution before opening the Redis socket.
import time  # WHY: webhook path stamps points with wall-clock ms rather than server '*'.
from collections.abc import Callable  # WHY: type helper wrappers that swallow "already exists" errors.
from concurrent.futures import ThreadPoolExecutor  # WHY: parallel numeric extraction on large batches.
from dataclasses import dataclass  # WHY: frozen extraction context collapses many parallel params.
from typing import Any, cast  # WHY: cast around redis-py's Any-typed client for module_list().

import redis  # WHY: sync redis client + ResponseError type for "already exists" detection.
import structlog  # WHY: structured logging for connection/pipeline lifecycle events.

from . import DatabaseConfig, WriteResult  # WHY: shared config + result dataclasses across DB writers.

RAW_RETENTION_MS = (
    int(os.environ.get("REDIS_RAW_RETENTION_DAYS", "7")) * 86_400_000
)  # WHY: raw points TTL (7d default).
HOURLY_RETENTION_MS = 90 * 86_400_000  # WHY: hourly rollup retained 90 days for medium-term analytics.
DAILY_RETENTION_MS = 365 * 86_400_000  # WHY: daily rollup retained 365 days for long-term trends.
REDIS_JSON_TTL_SECONDS = int(os.environ.get("REDIS_JSON_TTL_DAYS", "7")) * 86_400  # WHY: JSON docs mirror raw TTL.
JSON_PIPELINE_BATCH = 500  # WHY: batch JSON.SET+EXPIRE to bound pipeline memory per round-trip.
HOURLY_BUCKET_MS = 3_600_000  # WHY: 1h aggregation bucket for hourly compaction rule.
DAILY_BUCKET_MS = 86_400_000  # WHY: 1d aggregation bucket for daily compaction rule.
KEY_CREATION_BATCH = 500  # WHY: pipeline TS.CREATE in modest batches to avoid slow-log spikes.
ADD_PIPELINE_BATCH = 10_000  # WHY: TS.ADD batch size tuned for throughput versus Redis latency.
PARALLEL_EXTRACT_THRESHOLD = 1000  # WHY: below this, sequential extract avoids pool startup overhead.
MAX_EXTRACT_WORKERS = 8  # WHY: cap parallelism to prevent GIL thrash on typical hosts.
DEFAULT_LABEL_FIELDS = (
    "org_id",
    "site_id",
    "device_id",
)  # WHY: fallback TS labels when strategy omits ts_label_fields.
WEBHOOK_ENTITY_KEYS = ("mac", "device_id")  # WHY: webhook events identify entities via one of these fields.
ALREADY_EXISTS_TOKEN = "already exists"  # WHY: substring used to distinguish benign duplicate-create errors.

_TOPIC_KEY_PREFIX: dict[str, str] = {  # WHY: map Kafka topic names to TS key prefixes for webhook ingest.
    "client-sessions": "client_stats",
    "device-updowns": "device_events",
    "device-events": "device_events",
    "client-latency": "client_latency",
}


@dataclass(frozen=True, slots=True)
class _ExtractContext:  # WHY: collapse the 5-arg extract signature into one immutable context.
    """Immutable inputs shared across numeric extraction helpers."""

    api_function_name: str  # WHY: prefix component for every emitted TS key.
    primary_keys: list[str]  # WHY: fields excluded from generic numeric scan.
    entity_key_field: str  # WHY: field whose value becomes the entity id in the TS key.
    ts_value_fields: list[str] | None  # WHY: explicit numeric field allow-list. None means auto-detect.


def _swallow_already_exists(action: Callable[[], Any]) -> None:  # WHY: reused around TS.CREATE / TS.CREATERULE calls.
    """Run `action`. Re-raise any ResponseError that is not a duplicate-key error."""
    try:
        action()  # WHY: single call site so both create and createrule share the same suppression policy.
    except redis.ResponseError as error:  # WHY: only ResponseError carries the "already exists" text.
        if ALREADY_EXISTS_TOKEN not in str(error).lower():  # WHY: bubble anything that is not benign.
            raise


def _module_names(client: Any) -> list[str]:  # WHY: shared between TS and JSON verifiers.
    """Return loaded Redis module names as lowercase strings."""
    modules: list[dict[str, Any]] = cast(list[dict[str, Any]], client.module_list())  # WHY: client is Any-typed.
    return [_decode_name(m.get("name", b"")) for m in modules]  # WHY: normalize bytes/str variants in one place.


def _decode_name(raw: Any) -> str:  # WHY: decode_responses varies with server config. Handle both.
    """Return a lowercase str name whether the source is bytes or str."""
    if isinstance(raw, str):  # WHY: fast path when decode_responses already yielded a str.
        return raw.lower()
    return raw.decode().lower()  # WHY: fall back to bytes decode for the raw-response case.


class RedisTimeSeriesWriter:
    """Writes composite_pk data into Redis TimeSeries.

    Performance strategy:
    - Key creation uses pipelined TS.CREATE + CREATERULE batches
    - Data writes use pipelined TS.ADD with DUPLICATE_POLICY LAST
    - Numeric field extraction runs in thread pool across records
    """

    def __init__(self, config: DatabaseConfig) -> None:  # WHY: DatabaseConfig fans out host/port/password.
        """Initialize Redis TimeSeries connection and verify module."""
        self._log = structlog.get_logger("redis_writer")  # WHY: structured logger scoped to this writer.
        self._preflight_dns(config.redis_host)  # WHY: fail fast with a clear message before opening the socket.
        self._client = redis.Redis(  # WHY: sync client is fine. Writers run in worker threads.
            host=config.redis_host,
            port=config.redis_port,
            password=config.redis_password or None,  # WHY: pass None (not "") so redis-py skips AUTH.
            decode_responses=True,  # WHY: returns str from server so key handling stays text-based.
        )
        self._verify_timeseries_module()  # WHY: fail fast if operator forgot redis-stack-server image.
        self._ts = self._client.ts()  # WHY: cache the TimeSeries wrapper used by webhook path.
        self._created_keys: set[str] = set()  # WHY: idempotency cache so we skip repeat TS.CREATE round-trips.
        self._log.info("redis_connected", host=config.redis_host)  # WHY: single audit line on successful bring-up.

    @staticmethod
    def _preflight_dns(host: str) -> None:  # WHY: shared behavior between TS and JSON writers.
        """Raise ConnectionError with a clean message when DNS fails."""
        try:
            socket.getaddrinfo(host, None)  # WHY: cheap resolution check surfaces bad hosts before Redis handshake.
        except socket.gaierror as dns_error:  # WHY: convert opaque gaierror into a caller-friendly type.
            raise ConnectionError(f"Redis host '{host}' not resolvable") from dns_error

    def _verify_timeseries_module(self) -> None:  # WHY: writer is useless without the TimeSeries module.
        """Raise RuntimeError if the TimeSeries module is not loaded."""
        if "timeseries" not in _module_names(self._client):  # WHY: match against normalized lowercase list.
            raise RuntimeError("Redis TimeSeries module not loaded. Use redis/redis-stack-server image.")

    def write(  # WHY: primary batch entry point used by the bulk importer.
        self,
        data: list[dict[str, Any]],
        api_function_name: str,
        strategy: dict[str, Any],
    ) -> WriteResult:
        """Write numeric fields as TimeSeries data points."""
        if not data:  # WHY: skip pipeline overhead on empty input.
            return WriteResult(success=True, backend="redis", records_written=0, records_failed=0)
        ctx = self._build_context(api_function_name, strategy)  # WHY: freeze shared inputs once for all helpers.
        adds, key_records = self._extract_all_adds(data, ctx)  # WHY: phase 1 flatten records into (key, value) tuples.
        self._batch_ensure_keys(key_records, ctx.api_function_name, strategy.get("ts_label_fields"))  # WHY: phase 2.
        written, failed = self._execute_pipeline(adds)  # WHY: phase 3 dispatch TS.ADD in bounded pipelines.
        return WriteResult(success=failed == 0, backend="redis", records_written=written, records_failed=failed)

    @staticmethod
    def _build_context(api_function_name: str, strategy: dict[str, Any]) -> _ExtractContext:  # WHY: freeze inputs.
        """Freeze strategy-derived fields for extract helpers."""
        primary_keys = strategy.get("primary_key", [])  # WHY: pk list drives auto numeric-field exclusion.
        return _ExtractContext(  # WHY: single object flows through extraction rather than 4 loose args.
            api_function_name=api_function_name,
            primary_keys=primary_keys,
            entity_key_field=RedisTimeSeriesWriter._pick_entity_field(primary_keys),
            ts_value_fields=strategy.get("ts_value_fields"),
        )

    def _extract_all_adds(  # WHY: dispatch sequential versus parallel extraction based on input size.
        self,
        data: list[dict[str, Any]],
        ctx: _ExtractContext,
    ) -> tuple[list[tuple[str, float]], dict[str, dict[str, Any]]]:
        """Extract (ts_key, value) pairs and first-seen record per key."""
        if len(data) <= PARALLEL_EXTRACT_THRESHOLD:  # WHY: small inputs skip the pool for lower latency.
            return self._extract_chunk(data, ctx)
        return self._extract_parallel(data, ctx)  # WHY: large inputs benefit from thread-pool parallelism.

    def _extract_parallel(  # WHY: extracted helper keeps _extract_all_adds within length/complexity limits.
        self,
        data: list[dict[str, Any]],
        ctx: _ExtractContext,
    ) -> tuple[list[tuple[str, float]], dict[str, dict[str, Any]]]:
        """Run _extract_chunk across a thread pool and merge results."""
        workers = min(MAX_EXTRACT_WORKERS, os.cpu_count() or 4)  # WHY: fall back to 4 on hosts w/o cpu_count.
        chunk_size = max(1, len(data) // workers)  # WHY: at least one record per chunk to avoid empties.
        chunks = [data[i : i + chunk_size] for i in range(0, len(data), chunk_size)]  # WHY: fixed-size slicing.
        all_adds: list[tuple[str, float]] = []  # WHY: accumulator for (key, value) pairs across chunks.
        key_records: dict[str, dict[str, Any]] = {}  # WHY: first-seen record per key for label extraction.
        with ThreadPoolExecutor(max_workers=workers) as pool:  # WHY: context manager ensures pool shutdown.
            futures = [pool.submit(self._extract_chunk, chunk, ctx) for chunk in chunks]  # WHY: fan out extraction.
            for future in futures:  # WHY: preserve chunk order for deterministic first-seen mapping.
                chunk_adds, chunk_keys = future.result()  # WHY: block for chunk completion.
                all_adds.extend(chunk_adds)  # WHY: append rather than assign to preserve running total.
                key_records.update(chunk_keys)  # WHY: dict.update is last-write-wins. Chunks are disjoint.
        self._log.info("extraction_complete", data_points=len(all_adds), unique_keys=len(key_records), workers=workers)
        return all_adds, key_records

    def _extract_chunk(  # WHY: pure worker. Safe to call from any thread.
        self,
        records: list[dict[str, Any]],
        ctx: _ExtractContext,
    ) -> tuple[list[tuple[str, float]], dict[str, dict[str, Any]]]:
        """Extract adds and key->record map from a chunk of records."""
        adds: list[tuple[str, float]] = []  # WHY: local accumulator so callers can merge from many threads.
        key_records: dict[str, dict[str, Any]] = {}  # WHY: local first-seen map merged by caller.
        for record in records:  # WHY: per-record loop is simple enough to inline.
            entity_id = str(record.get(ctx.entity_key_field, "unknown"))  # WHY: "unknown" keeps schema stable.
            numeric = self._select_numeric(record, ctx)  # WHY: single call site for the two extraction modes.
            for field_name, value in numeric.items():  # WHY: each numeric field becomes its own TS key.
                ts_key = f"{ctx.api_function_name}:{entity_id}:{field_name}"  # WHY: three-part key aids querying.
                adds.append((ts_key, value))  # WHY: preserve emission order to keep timestamps monotonic.
                key_records.setdefault(ts_key, record)  # WHY: first-seen only. Label state is stable per key.
        return adds, key_records

    @staticmethod
    def _select_numeric(record: dict[str, Any], ctx: _ExtractContext) -> dict[str, float]:  # WHY: mode dispatch.
        """Choose listed-fields versus auto numeric extraction based on ctx."""
        if ctx.ts_value_fields:  # WHY: explicit allow-list wins over generic numeric scan.
            return RedisTimeSeriesWriter._extract_listed_fields(record, ctx.ts_value_fields)
        return RedisTimeSeriesWriter._extract_numeric(record, ctx.primary_keys)  # WHY: fallback auto-detect path.

    def _batch_ensure_keys(  # WHY: guarantees TS.CREATE + compaction rules exist before TS.ADD runs.
        self,
        key_records: dict[str, dict[str, Any]],
        api_function_name: str,
        ts_label_fields: list[str] | None = None,
    ) -> None:
        """Create all missing TS keys and compaction rules via pipeline."""
        new_keys = {k: v for k, v in key_records.items() if k not in self._created_keys}  # WHY: skip proven keys.
        if not new_keys:  # WHY: warm cache short-circuits both round-trips.
            return
        keys_list = list(new_keys.items())  # WHY: freeze order so slicing is stable.
        for start in range(0, len(keys_list), KEY_CREATION_BATCH):  # WHY: bound pipeline size per iteration.
            batch = keys_list[start : start + KEY_CREATION_BATCH]  # WHY: contiguous slice into current batch.
            self._pipeline_create_keys(batch, api_function_name, ts_label_fields)  # WHY: create + compaction for batch.
        self._log.info("keys_created", count=len(new_keys))  # WHY: single audit event per bulk-create.

    def _pipeline_create_keys(  # WHY: TS.CREATE the raw keys then delegate compaction handling.
        self,
        batch: list[tuple[str, dict[str, Any]]],
        api_function_name: str,
        ts_label_fields: list[str] | None = None,
    ) -> None:
        """Pipeline-create a batch of TS keys with compaction."""
        pipe = self._client.pipeline(transaction=False)  # WHY: non-transactional pipeline maximises throughput.
        for ts_key, record in batch:  # WHY: enqueue one TS.CREATE per key in the batch.
            labels = self._build_labels(record, api_function_name, ts_key, ts_label_fields)  # WHY: metadata per key.
            self._queue_ts_create(pipe, ts_key, labels)  # WHY: encapsulate the LABELS flag-args expansion.
        results = pipe.execute(raise_on_error=False)  # WHY: capture per-command errors. Do not abort the batch.
        self._pipeline_create_compaction(batch, results)  # WHY: proceed with compaction using result-driven filter.

    @staticmethod
    def _queue_ts_create(pipe: Any, ts_key: str, labels: dict[str, str]) -> None:  # WHY: flatten labels for TS.CREATE.
        """Enqueue a TS.CREATE command with LABELS args on the given pipeline."""
        label_args: list[str] = []  # WHY: TS.CREATE expects alternating k, v tokens after LABELS.
        for label_key, label_val in labels.items():  # WHY: order is preserved by dict insertion order.
            label_args.extend([label_key, label_val])  # WHY: pair-append yields the flat token stream.
        pipe.execute_command(  # WHY: raw execute_command lets us pass RETENTION/DUPLICATE_POLICY inline.
            "TS.CREATE",
            ts_key,
            "RETENTION",
            RAW_RETENTION_MS,
            "DUPLICATE_POLICY",
            "LAST",
            "LABELS",
            *label_args,
        )

    def _pipeline_create_compaction(  # WHY: orchestrates compaction creation for the successful subset of keys.
        self,
        batch: list[tuple[str, dict[str, Any]]],
        create_results: list,
    ) -> None:
        """Create compaction keys and rules for successfully created keys."""
        pending = self._collect_pending(batch, create_results)  # WHY: filter down to keys we should compact.
        if not pending:  # WHY: nothing to enqueue means no round-trip needed.
            return
        pipe = self._client.pipeline(transaction=False)  # WHY: dedicated pipeline keeps concerns separate.
        for ts_key in pending:  # WHY: one loop enqueues all four compaction commands per key.
            self._queue_compaction_commands(pipe, ts_key)  # WHY: keeps the loop body a single call.
        pipe.execute(raise_on_error=False)  # WHY: swallow benign "already exists" outcomes on rerun.
        for ts_key in pending:  # WHY: register raw + compaction keys so subsequent writes skip re-create.
            self._register_compaction_keys(ts_key)

    @staticmethod
    def _collect_pending(  # WHY: pure filter over create results. Easy to test in isolation.
        batch: list[tuple[str, dict[str, Any]]],
        create_results: list,
    ) -> list[str]:
        """Return TS keys that were newly created or already existed (both are compactable)."""
        pending: list[str] = []  # WHY: preserve original batch order for deterministic pipeline layout.
        for idx, (ts_key, _record) in enumerate(batch):  # WHY: index-align to results list.
            if RedisTimeSeriesWriter._is_creatable(create_results[idx]):  # WHY: helper collapses two branches into one.
                pending.append(ts_key)
        return pending

    @staticmethod
    def _is_creatable(result: Any) -> bool:  # WHY: cyclomatic-simple predicate reused by tests.
        """Return True when a TS.CREATE result means the key is ready for compaction."""
        if not isinstance(result, Exception):  # WHY: success path always counts as creatable.
            return True
        return isinstance(result, redis.ResponseError) and ALREADY_EXISTS_TOKEN in str(result).lower()

    @staticmethod
    def _queue_compaction_commands(pipe: Any, ts_key: str) -> None:  # WHY: single site for the 4-command sequence.
        """Enqueue TS.CREATE for hourly+daily plus TS.CREATERULE for both buckets."""
        hourly = f"{ts_key}:avg_1h"  # WHY: naming convention makes derived keys discoverable.
        daily = f"{ts_key}:avg_1d"  # WHY: same suffix pattern for daily rollups.
        pipe.execute_command("TS.CREATE", hourly, "RETENTION", HOURLY_RETENTION_MS)  # WHY: hourly compaction target.
        pipe.execute_command("TS.CREATE", daily, "RETENTION", DAILY_RETENTION_MS)  # WHY: daily compaction target.
        pipe.execute_command("TS.CREATERULE", ts_key, hourly, "AGGREGATION", "avg", HOURLY_BUCKET_MS)  # WHY: 1h avg.
        pipe.execute_command("TS.CREATERULE", ts_key, daily, "AGGREGATION", "avg", DAILY_BUCKET_MS)  # WHY: 1d avg.

    def _register_compaction_keys(self, ts_key: str) -> None:  # WHY: state mutation is trivial but centralized.
        """Cache raw + hourly + daily key names so re-writes skip TS.CREATE."""
        self._created_keys.add(ts_key)  # WHY: raw key is confirmed present.
        self._created_keys.add(f"{ts_key}:avg_1h")  # WHY: hourly key is confirmed present.
        self._created_keys.add(f"{ts_key}:avg_1d")  # WHY: daily key is confirmed present.

    def _execute_pipeline(  # WHY: TS.ADD dispatch loop with success/failure accounting.
        self,
        adds: list[tuple[str, float]],
    ) -> tuple[int, int]:
        """Execute TS.ADD commands in batched pipelines."""
        written = 0  # WHY: running total of successful TS.ADD results.
        failed = 0  # WHY: running total of exceptions returned by pipeline.
        for start in range(0, len(adds), ADD_PIPELINE_BATCH):  # WHY: bound pipeline size per round-trip.
            batch = adds[start : start + ADD_PIPELINE_BATCH]  # WHY: contiguous batch slice.
            results = self._run_add_batch(batch)  # WHY: helper isolates the enqueue+execute step.
            batch_ok, batch_fail = self._tally_add_results(batch, results)  # WHY: pure counter helper.
            written += batch_ok  # WHY: accumulate per-batch success count.
            failed += batch_fail  # WHY: accumulate per-batch failure count.
        return written, failed

    def _run_add_batch(self, batch: list[tuple[str, float]]) -> list[Any]:  # WHY: keep pipeline enqueue localized.
        """Enqueue TS.ADD commands for a batch and return per-command results."""
        pipe = self._client.pipeline(transaction=False)  # WHY: non-transactional matches TS.CREATE strategy.
        for ts_key, value in batch:  # WHY: TS.ADD with '*' timestamps for server-side clock authority.
            pipe.execute_command("TS.ADD", ts_key, "*", value, "DUPLICATE_POLICY", "LAST")
        return pipe.execute(raise_on_error=False)  # WHY: return the raw result list for downstream tally.

    def _tally_add_results(  # WHY: separates counting from side-effectful logging.
        self,
        batch: list[tuple[str, float]],
        results: list[Any],
    ) -> tuple[int, int]:
        """Count successes versus failures, logging each failure with its key."""
        written = 0  # WHY: local counter avoids mutating caller state directly.
        failed = 0  # WHY: local counter for failed adds.
        for idx, result in enumerate(results):  # WHY: index-align back to batch entries for error context.
            if isinstance(result, Exception):  # WHY: pipeline returns Exception instances on failure.
                failed += 1  # WHY: bump failure count.
                self._log.error("ts_add_failed", key=batch[idx][0], error=str(result))  # WHY: emit per-key error.
            else:
                written += 1  # WHY: bump success count.
        return written, failed

    def _ensure_key_single(  # WHY: webhook path lacks a batched key list, so we serialize creates per key.
        self,
        ts_key: str,
        record: dict[str, Any],
        api_function_name: str,
    ) -> None:
        """Create a single TimeSeries key (used by webhook path)."""
        if ts_key in self._created_keys:  # WHY: cache hit skips network round-trip.
            return
        labels = self._build_labels(record, api_function_name, ts_key)  # WHY: label extraction identical to batch.
        _swallow_already_exists(  # WHY: idempotent create. Parallel workers may have raced ahead.
            lambda: self._ts.create(  # WHY: use TimeSeries wrapper for the single-shot path.
                ts_key,
                retention_msecs=RAW_RETENTION_MS,
                labels=labels,
                duplicate_policy="last",
            )
        )
        self._ensure_single_compaction(ts_key)  # WHY: mirror the batch behavior around compaction rules.
        self._created_keys.add(ts_key)  # WHY: memoize so the next event on this key skips create.

    def _ensure_single_compaction(self, source_key: str) -> None:  # WHY: webhook variant of _queue_compaction_commands.
        """Create compaction rules for a single key (webhook path)."""
        hourly_key = f"{source_key}:avg_1h"  # WHY: hourly compaction target name.
        daily_key = f"{source_key}:avg_1d"  # WHY: daily compaction target name.
        if hourly_key in self._created_keys:  # WHY: cache hit means daily was cached at the same time.
            return
        for dest_key, retention, bucket in (  # WHY: table-driven loop keeps this helper under the block limit.
            (hourly_key, HOURLY_RETENTION_MS, HOURLY_BUCKET_MS),
            (daily_key, DAILY_RETENTION_MS, DAILY_BUCKET_MS),
        ):
            self._ensure_single_rule(source_key, dest_key, retention, bucket)  # WHY: per-rule helper handles errors.
        self._created_keys.add(hourly_key)  # WHY: cache hourly key so future webhook events skip create.
        self._created_keys.add(daily_key)  # WHY: cache daily key so future webhook events skip create.

    def _ensure_single_rule(  # WHY: helper wraps the two "already exists"-swallowing create calls per rule.
        self,
        source_key: str,
        dest_key: str,
        retention_ms: int,
        bucket_ms: int,
    ) -> None:
        """Create one compaction destination + rule, ignoring benign duplicate errors."""
        _swallow_already_exists(lambda: self._ts.create(dest_key, retention_msecs=retention_ms))  # WHY: idempotent.
        _swallow_already_exists(  # WHY: same swallow policy for the rule itself.
            lambda: self._ts.createrule(source_key, dest_key, "avg", bucket_ms)
        )

    def ingest_webhook(  # WHY: single-shot ingestion path called by webhook receivers.
        self,
        events: list[dict],
        topic: str,
    ) -> int:
        """Ingest webhook stats events into Redis TimeSeries."""
        key_prefix = _TOPIC_KEY_PREFIX.get(topic, topic)  # WHY: fall back to topic name for unknown streams.
        pipe = self._client.pipeline(transaction=False)  # WHY: match batch-path pipeline strategy.
        timestamp_ms = int(time.time() * 1000)  # WHY: use one timestamp per webhook flush for coherency.
        written = self._queue_webhook_events(events, key_prefix, pipe, timestamp_ms)  # WHY: helper stays under limit.
        if written > 0:  # WHY: avoid an empty pipe.execute() round-trip.
            pipe.execute()  # WHY: single sync point for all queued TS.ADD commands.
            self._log.info("webhook_ingested", topic=topic, points=written)  # WHY: one audit event per ingest call.
        return written

    def _queue_webhook_events(  # WHY: pulls the enqueue loop out of ingest_webhook to satisfy length.
        self,
        events: list[dict],
        key_prefix: str,
        pipe: Any,
        timestamp_ms: int,
    ) -> int:
        """Enqueue TS.ADD commands for every numeric field of each webhook event."""
        written = 0  # WHY: running count of enqueued points.
        for event in events:  # WHY: process events serially; pipe.execute() is one round-trip.
            entity_id = self._pick_webhook_entity(event)  # WHY: keeps the loop body linear.
            numeric = self._extract_numeric(event, list(WEBHOOK_ENTITY_KEYS))  # WHY: exclude PK-like fields.
            for field_name, value in numeric.items():  # WHY: each numeric field maps to its own TS key.
                ts_key = f"{key_prefix}:{entity_id}:{field_name}"  # WHY: consistent naming versus batch path.
                self._ensure_key_single(ts_key, event, key_prefix)  # WHY: guarantees key exists before ADD.
                pipe.execute_command(  # WHY: enqueue explicit-timestamp TS.ADD command.
                    "TS.ADD",
                    ts_key,
                    timestamp_ms,
                    value,
                    "DUPLICATE_POLICY",
                    "LAST",
                )
                written += 1  # WHY: bump running total.
        return written

    @staticmethod
    def _pick_webhook_entity(event: dict[str, Any]) -> str:  # WHY: helper mirrors batch _pick_entity_field intent.
        """Return the first WEBHOOK_ENTITY_KEYS field present on the event, else 'unknown'."""
        for key in WEBHOOK_ENTITY_KEYS:  # WHY: preference order matches historical behavior (mac before device_id).
            if key in event:
                return str(event[key])
        return "unknown"  # WHY: schema-stable fallback so downstream queries never miss the label.

    def close(self) -> None:  # WHY: called by lifecycle owner to release the connection cleanly.
        """Close the Redis connection."""
        self._client.close()  # WHY: shutdown returns the socket to the OS.
        self._log.info("redis_disconnected")  # WHY: audit trail complements the connect log.

    @staticmethod
    def _pick_entity_field(primary_keys: list[str]) -> str:  # WHY: shared preference order for entity id fields.
        """Choose the entity identifier from PK fields."""
        for field in ("device_id", "site_id", "org_id", "mac", "id"):  # WHY: inline tuple avoids module-level table.
            if field in primary_keys:
                return field
        return primary_keys[0] if primary_keys else "id"  # WHY: fall back to first PK or literal 'id'.

    @staticmethod
    def _extract_numeric(  # WHY: pure helper used by both batch and webhook paths.
        record: dict[str, Any],
        exclude_keys: list[str],
    ) -> dict[str, float]:
        """Return only numeric (int/float) fields, excluding PKs."""
        result: dict[str, float] = {}  # WHY: build fresh dict. Caller may merge with others.
        for key, value in record.items():  # WHY: single pass over the record.
            if key in exclude_keys:  # WHY: skip PK fields to avoid emitting identifiers as metrics.
                continue
            if isinstance(value, (int, float)) and not isinstance(value, bool):  # WHY: bool is int subclass. Exclude.
                result[key] = float(value)  # WHY: normalize to float so TS.ADD gets a consistent type.
        return result

    @staticmethod
    def _extract_listed_fields(  # WHY: allow-list variant for endpoints that ship non-metric numerics.
        record: dict[str, Any],
        value_fields: list[str],
    ) -> dict[str, float]:
        """Extract only named fields that have numeric values."""
        result: dict[str, float] = {}  # WHY: local dict. Caller merges into per-chunk totals.
        for field in value_fields:  # WHY: iterate over the caller's explicit list.
            value = record.get(field)  # WHY: absent fields silently drop.
            if isinstance(value, (int, float)) and not isinstance(value, bool):  # WHY: bool exclusion mirrors above.
                result[field] = float(value)  # WHY: normalize numeric type.
        return result

    @staticmethod
    def _build_labels(  # WHY: builds TS labels for both batch and webhook paths.
        record: dict[str, Any],
        api_function_name: str,
        ts_key: str,
        ts_label_fields: list[str] | None = None,
    ) -> dict[str, str]:
        """Build TimeSeries labels from record metadata."""
        parts = ts_key.rsplit(":", 1)  # WHY: metric name is the trailing token after the final colon.
        metric_name = parts[-1] if len(parts) > 1 else ts_key  # WHY: fall back to full key when no colon.
        labels: dict[str, str] = {"api_function": api_function_name, "metric_name": metric_name}  # WHY: base labels.
        fields = ts_label_fields or DEFAULT_LABEL_FIELDS  # WHY: single loop. Removes if/else branching.
        for field in fields:  # WHY: only fields actually present on the record are emitted.
            if field in record:
                labels[field] = str(record[field])  # WHY: TS labels must be strings.
        return labels


class RedisJSONWriter:
    """Writes composite_pk data as Redis JSON documents with TTL.

    Stores full unflattened API responses as JSON documents for fast
    recent-event queries. Documents expire after a configurable TTL
    (default 7 days). ArangoDB serves as the long-term archive.
    """

    def __init__(self, config: DatabaseConfig) -> None:  # WHY: mirror the TS-writer connect ceremony.
        """Initialize Redis JSON connection and verify module."""
        self._log = structlog.get_logger("redis_json_writer")  # WHY: separate logger keeps events distinguishable.
        RedisTimeSeriesWriter._preflight_dns(config.redis_host)  # WHY: reuse the shared DNS pre-flight.
        self._client = redis.Redis(  # WHY: sync client shared strategy across writers.
            host=config.redis_host,
            port=config.redis_port,
            password=config.redis_password or None,  # WHY: empty string means no AUTH.
            decode_responses=True,  # WHY: keep keys as str for straightforward composition.
        )
        self._verify_json_module()  # WHY: fail fast if ReJSON module is missing.
        self._log.info("redis_json_connected", host=config.redis_host)  # WHY: single audit line on bring-up.

    def _verify_json_module(self) -> None:  # WHY: writer requires ReJSON (or its alias RedisJSON).
        """Check that the ReJSON module is loaded."""
        names = _module_names(self._client)  # WHY: shared helper normalizes bytes/str differences.
        if "rejson" not in names and "redisjson" not in names:  # WHY: accept both historical module names.
            raise RuntimeError("Redis JSON module not loaded. Use redis/redis-stack-server image.")

    def write(  # WHY: batch entry point for JSON-flavored writes.
        self,
        data: list[dict[str, Any]],
        api_function_name: str,
        strategy: dict[str, Any],
    ) -> WriteResult:
        """Write records as JSON documents with TTL via pipeline."""
        if not data:  # WHY: short-circuit empty batches.
            return WriteResult(success=True, backend="redis_json", records_written=0, records_failed=0)
        pk_fields = strategy.get("primary_key", [])  # WHY: PK fields drive the composite Redis key.
        written, failed = self._write_all_batches(data, api_function_name, pk_fields)  # WHY: helper keeps length low.
        self._log.info("json_write_complete", endpoint=api_function_name, written=written, failed=failed)
        return WriteResult(success=failed == 0, backend="redis_json", records_written=written, records_failed=failed)

    def _write_all_batches(  # WHY: extracted loop so `write` stays inside the STRUCT-LENGTH limit.
        self,
        data: list[dict[str, Any]],
        api_function_name: str,
        pk_fields: list[str],
    ) -> tuple[int, int]:
        """Iterate JSON_PIPELINE_BATCH-sized slices and accumulate write counts."""
        written = 0  # WHY: running total across every batch.
        failed = 0  # WHY: running total of failures across every batch.
        for start in range(0, len(data), JSON_PIPELINE_BATCH):  # WHY: bound pipeline size to control memory.
            batch = data[start : start + JSON_PIPELINE_BATCH]  # WHY: contiguous batch slice.
            batch_ok, batch_fail = self._pipeline_write_batch(batch, api_function_name, pk_fields)  # WHY: per-batch.
            written += batch_ok  # WHY: accumulate success count.
            failed += batch_fail  # WHY: accumulate failure count.
        return written, failed

    def _pipeline_write_batch(  # WHY: JSON.SET + EXPIRE pair per record inside one pipeline round-trip.
        self,
        batch: list[dict[str, Any]],
        api_function_name: str,
        pk_fields: list[str],
    ) -> tuple[int, int]:
        """Pipeline JSON.SET + EXPIRE for a batch of records."""
        pipe = self._client.pipeline(transaction=False)  # WHY: non-transactional for throughput.
        for record in batch:  # WHY: enqueue two commands per record (set + expire).
            key = self._build_key(api_function_name, record, pk_fields)  # WHY: deterministic composite key.
            pipe.json().set(key, "$", record)  # WHY: overwrite entire document at root path.
            pipe.expire(key, REDIS_JSON_TTL_SECONDS)  # WHY: apply TTL so old docs are pruned by Redis.
        results = pipe.execute(raise_on_error=False)  # WHY: keep going even if some records fail.
        return self._tally_json_results(results)  # WHY: pure counting helper keeps this method short.

    def _tally_json_results(  # WHY: separates logging/counting from the pipeline enqueue step.
        self,
        results: list[Any],
    ) -> tuple[int, int]:
        """Count JSON.SET successes and failures from a paired results list (set, expire, ...)."""
        written = 0  # WHY: counter for successful JSON.SET operations.
        failed = 0  # WHY: counter for failed JSON.SET operations.
        for idx in range(0, len(results), 2):  # WHY: stride 2 so we only inspect the SET half of each pair.
            if isinstance(results[idx], Exception):  # WHY: pipeline returns Exception on per-command failure.
                failed += 1  # WHY: bump failure count.
                self._log.error("json_set_failed", error=str(results[idx]))  # WHY: per-record error line.
            else:
                written += 1  # WHY: bump success count.
        return written, failed

    @staticmethod
    def _build_key(  # WHY: deterministic composite key so re-writes overwrite the same record.
        endpoint: str,
        record: dict[str, Any],
        pk_fields: list[str],
    ) -> str:
        """Build Redis key from endpoint name and PK field values."""
        parts = [endpoint]  # WHY: endpoint anchors the namespace so different APIs never collide.
        for field in pk_fields:  # WHY: append each PK component in strategy-defined order.
            parts.append(str(record.get(field, "unknown")))  # WHY: unknown sentinel keeps key length stable.
        return ":".join(parts)  # WHY: colon-delimited keys align with Redis convention.

    def close(self) -> None:  # WHY: mirror TS-writer close semantics.
        """Close the Redis connection."""
        self._client.close()  # WHY: release the socket back to the OS.
        self._log.info("redis_json_disconnected")  # WHY: audit trail for shutdown symmetry.
