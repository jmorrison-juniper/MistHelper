"""DatabaseRouter: central dispatch for polyglot database writes.

Routes API data to ArangoDB or Redis TimeSeries based on the
ENDPOINT_PRIMARY_KEY_STRATEGIES configuration in MistHelper.py.
"""

from __future__ import annotations  # WHY: postponed annotations for forward-ref types

import hashlib  # WHY: sha256 config-body fingerprints for snapshot dedup
import json  # WHY: canonicalize records before hashing
from dataclasses import dataclass  # WHY: frozen slotted snapshot-arg bundle
from typing import Any  # WHY: strategy dicts hold heterogeneous values

import structlog  # WHY: structured JSON logging for the db package

from . import DatabaseConfig, DualWriteResult, WriteResult  # WHY: reuse shared package value types
from .arango_writer import ArangoDBWriter  # WHY: primary document store writer
from .redis_writer import RedisJSONWriter, RedisTimeSeriesWriter  # WHY: event and metric writers

logger = structlog.get_logger(__name__)  # WHY: module-scoped structured logger

ARANGO_ONLY_TYPES = {"natural_pk", "auto_increment_with_unique"}  # WHY: arango-only strategy labels
DUAL_WRITE_TYPES = {"composite_pk"}  # WHY: dual-fanout (redis-json + arango) strategy labels
TIMESERIES_TYPES = {"timeseries_pk"}  # WHY: redis timeseries strategy labels
DEFAULT_STRATEGY_TYPE = "auto_increment_with_unique"  # WHY: fallback strategy label when unspecified

BACKEND_CSV_ONLY = "csv_only"  # WHY: shared csv_only backend marker
BACKEND_ARANGO = "arangodb"  # WHY: shared arangodb backend marker
BACKEND_REDIS = "redis"  # WHY: shared redis (timeseries) backend marker
BACKEND_REDIS_JSON = "redis_json"  # WHY: shared redis_json backend marker

SNAPSHOT_SOURCE_API = "api_pull"  # WHY: snapshot origin tag for polled data
SNAPSHOT_SOURCE_WEBHOOK = "webhook"  # WHY: snapshot origin tag for webhook payloads
DEVICE_CONFIG_ENTITY_TYPE = "device_config"  # WHY: snapshot bucket for device config history rows
UNKNOWN_ENTITY_TYPE = "unknown"  # WHY: fallback entity_type when webhook payload lacks it
DEFAULT_PK_FIELDS: list[str] = ["id"]  # WHY: fallback primary_key list when strategy omits it

CONFIG_SNAPSHOT_APIS = {
    "listOrgSites",
    "listSiteDevices",
    "getOrgWlans",
    "listOrgRfTemplates",
    "listOrgDeviceProfiles",
    "listOrgNetworkTemplates",
    "listOrgGatewayTemplates",
    "listOrgServices",
    "listOrgServicePolicies",
}  # WHY: APIs whose successful writes trigger config snapshot writes

DEFAULT_STRATEGY: dict[str, Any] = {
    "type": DEFAULT_STRATEGY_TYPE,
    "primary_key": ["misthelper_internal_id"],
}  # WHY: applied when no strategy is configured for an api function

EVT_ARANGO_UNAVAIL = "arangodb_unavailable"  # WHY: log event name for arango connect failure
EVT_REDIS_UNAVAIL = "redis_unavailable"  # WHY: log event name for redis-ts connect failure
EVT_REDIS_JSON_UNAVAIL = "redis_json_unavailable"  # WHY: log event name for redis-json connect failure
EVT_ARANGO_WRITE_ERR = "arango_write_error"  # WHY: log event name for arango write exceptions
EVT_REDIS_WRITE_ERR = "redis_write_error"  # WHY: log event name for redis write exceptions
EVT_REDIS_JSON_WRITE_ERR = "redis_json_write_error"  # WHY: log event name for redis-json write exceptions
EVT_SNAPSHOT_FAILED = "snapshot_failed"  # WHY: log event name for per-record snapshot failures
EVT_WEBHOOK_SNAPSHOT_FAILED = "webhook_snapshot_failed"  # WHY: log event name for webhook snapshot failures
EVT_CFG_HISTORY_FAILED = "config_history_failed"  # WHY: log event name for config-history snapshot failures
EVT_ARANGO_CLOSE_ERR = "arangodb_close_error"  # WHY: log event name for arango close failure
EVT_REDIS_CLOSE_ERR = "redis_close_error"  # WHY: log event name for redis close failure
EVT_ROUTER_CLOSED = "router_closed"  # WHY: log event name emitted at end of close()
EVT_STANDALONE_MODE = "standalone_mode"  # WHY: log event name emitted when router starts in csv-only mode
EVT_DEGRADED_MODE = "degraded_mode"  # WHY: log event name for csv-fallback dispatch


@dataclass(frozen=True, slots=True)
class SnapshotRequest:
    """Immutable bundle of arguments for ``ArangoDBWriter.snapshot``."""

    entity_type: str  # WHY: entity or api-function label used to bucket snapshots
    entity_id: str  # WHY: primary-key value that identifies the record
    record: dict[str, Any]  # WHY: raw record body captured in the snapshot
    config_hash: str  # WHY: sha256 fingerprint used for dedup
    source: str  # WHY: origin tag (api_pull, webhook)


def _hash_payload(payload: Any) -> str:  # WHY: shared canonical-hash helper for snapshot bodies
    """Return a sha256 hex digest for a JSON-canonicalized payload."""
    body = json.dumps(payload, sort_keys=True, default=str)  # WHY: canonicalize for stable hash
    return hashlib.sha256(body.encode()).hexdigest()  # WHY: fixed-length dedupe fingerprint


def _error_write_result(data: list[dict], error: str) -> WriteResult:  # WHY: uniform failure envelope
    """Return a failure ``WriteResult`` carrying the given error string."""
    return WriteResult(
        success=False,
        backend=BACKEND_CSV_ONLY,
        records_written=0,
        records_failed=len(data),
        error_message=error,
    )  # WHY: shared shape reused by every backend write path


class DatabaseRouter:
    """Route and write data to the appropriate backend."""

    def __init__(
        self,
        config: DatabaseConfig,
        strategies: dict[str, Any] | None = None,
    ) -> None:  # WHY: constructor wires config and probes each backend
        """Initialize database router and connect to available backends."""
        self.config = config  # WHY: retain config for standalone_mode + reconnect checks
        self._strategies = strategies or {}  # WHY: default empty map so lookups never NPE
        self._arango_available = False  # WHY: flip true only after successful arango connect
        self._redis_available = False  # WHY: flip true only after successful redis-ts connect
        self._redis_json_available = False  # WHY: flip true only after successful redis-json connect
        self._arango_writer: ArangoDBWriter | None = None  # WHY: writer or None when unreachable
        self._redis_writer: RedisTimeSeriesWriter | None = None  # WHY: writer or None when unreachable
        self._redis_json_writer: RedisJSONWriter | None = None  # WHY: writer or None when unreachable
        if config.standalone_mode:  # WHY: skip DB connects entirely in csv-only mode
            logger.info(EVT_STANDALONE_MODE, msg="CSV-only output")  # WHY: single breadcrumb per boot
            return  # WHY: standalone router serves csv_only results without backends
        self._connect_arango()  # WHY: attempt arango connect (non-fatal on failure)
        self._connect_redis()  # WHY: attempt redis-ts connect (non-fatal on failure)
        self._connect_redis_json()  # WHY: attempt redis-json connect (non-fatal on failure)

    def _connect_arango(self) -> None:  # WHY: isolate connect errors from constructor
        """Attempt ArangoDB connection. Set availability flag."""
        try:
            self._arango_writer = ArangoDBWriter(self.config)  # WHY: sync connect + probe
            self._arango_available = True  # WHY: mark healthy for later dispatch
        except Exception as error:  # WHY: any connect exception downgrades to csv mode
            self._arango_available = False  # WHY: force csv fallback for arango-bound writes
            logger.warning(EVT_ARANGO_UNAVAIL, error=str(error))  # WHY: single warning per attempt

    def _connect_redis(self) -> None:  # WHY: isolate connect errors from constructor
        """Attempt Redis connection. Set availability flag."""
        try:
            self._redis_writer = RedisTimeSeriesWriter(self.config)  # WHY: sync connect + probe
            self._redis_available = True  # WHY: mark healthy for later dispatch
        except Exception as error:  # WHY: any connect exception downgrades to csv mode
            self._redis_available = False  # WHY: force csv fallback for redis-ts-bound writes
            logger.warning(EVT_REDIS_UNAVAIL, error=str(error))  # WHY: single warning per attempt

    def _connect_redis_json(self) -> None:  # WHY: isolate connect errors from constructor
        """Attempt Redis JSON connection. Set availability flag."""
        try:
            self._redis_json_writer = RedisJSONWriter(self.config)  # WHY: sync connect + probe
            self._redis_json_available = True  # WHY: mark healthy for later dispatch
        except Exception as error:  # WHY: any connect exception downgrades to csv mode
            self._redis_json_available = False  # WHY: force csv fallback for redis-json writes
            logger.warning(EVT_REDIS_JSON_UNAVAIL, error=str(error))  # WHY: single warning per attempt

    def write(self, data: list[dict], api_function_name: str) -> WriteResult:  # WHY: public dispatch entry
        """Route data to the correct backend based on PK strategy."""
        if self.config.standalone_mode:  # WHY: standalone mode never touches a backend
            return WriteResult(
                success=True,
                backend=BACKEND_CSV_ONLY,
                records_written=0,
                records_failed=0,
            )  # WHY: csv-only success envelope for standalone runs
        strategy = self._resolve_strategy(api_function_name)  # WHY: look up strategy for this api
        strategy_type = strategy.get("type", DEFAULT_STRATEGY_TYPE)  # WHY: fall back to default label
        if strategy_type in TIMESERIES_TYPES:  # WHY: timeseries goes to redis-ts
            return self._write_redis(data, api_function_name, strategy)
        if strategy_type in DUAL_WRITE_TYPES:  # WHY: composite_pk fans out to redis-json + arango
            return self._write_dual(data, api_function_name, strategy)
        return self._write_arango(data, api_function_name, strategy)  # WHY: default routes to arango

    def _write_arango(
        self,
        data: list[dict],
        api_function_name: str,
        strategy: dict[str, Any],
    ) -> WriteResult:  # WHY: arango-only write path with snapshot side-effect
        """Dispatch to ArangoDB. Degrade to csv_only if unavailable."""
        if not self._arango_available or self._arango_writer is None:  # WHY: guard clause for unavailable
            return self._csv_fallback(api_function_name, BACKEND_ARANGO)
        try:
            result = self._arango_writer.write(data, api_function_name, strategy)  # WHY: perform arango write
            if result.success:  # WHY: only snapshot after a successful primary write
                self._snapshot_if_config(data, api_function_name, strategy)
            return result  # WHY: propagate underlying writer result verbatim
        except Exception as error:  # WHY: convert unexpected writer failure to csv envelope
            logger.error(EVT_ARANGO_WRITE_ERR, error=str(error))  # WHY: preserve original error diagnostic
            return _error_write_result(data, str(error))

    def _snapshot_if_config(
        self,
        data: list[dict],
        api_function_name: str,
        strategy: dict[str, Any],
    ) -> None:  # WHY: side-effect snapshot pass for configuration entity types
        """Create config snapshots for configuration entity types."""
        if api_function_name not in CONFIG_SNAPSHOT_APIS:  # WHY: only snapshot known config APIs
            return
        if self._arango_writer is None:  # WHY: cannot snapshot without an arango writer
            return
        pk_field = strategy.get("primary_key", DEFAULT_PK_FIELDS)[0]  # WHY: first pk column drives id
        for record in data:  # WHY: snapshot each record independently to isolate failures
            self._snapshot_one_record(api_function_name, record, pk_field)

    def _snapshot_one_record(
        self,
        api_function_name: str,
        record: dict[str, Any],
        pk_field: str,
    ) -> None:  # WHY: extract per-record work so caller CC stays low
        """Snapshot a single record if it has a non-empty primary key."""
        entity_id = str(record.get(pk_field, ""))  # WHY: coerce pk value into string id
        if not entity_id:  # WHY: skip rows missing the primary key entirely
            return
        request = SnapshotRequest(
            entity_type=api_function_name,
            entity_id=entity_id,
            record=record,
            config_hash=_hash_payload(record),
            source=SNAPSHOT_SOURCE_API,
        )  # WHY: bundle arango.snapshot args into a single frozen value
        self._safe_snapshot(request, EVT_SNAPSHOT_FAILED)

    def _safe_snapshot(self, request: SnapshotRequest, error_event: str) -> bool:  # WHY: reused wrapper
        """Call ``arango_writer.snapshot`` and swallow/log failures."""
        if self._arango_writer is None:  # WHY: guard against snapshot when arango is absent
            return False
        try:
            self._arango_writer.snapshot(
                request.entity_type,
                request.entity_id,
                request.record,
                request.config_hash,
                request.source,
            )  # WHY: writer contract accepts positional args (preserved from original)
            return True  # WHY: signal caller to increment stored counter
        except Exception as error:  # WHY: never let a snapshot failure escape upward
            logger.warning(error_event, entity_id=request.entity_id, error=str(error))
            return False  # WHY: signal caller not to count this record

    def _write_redis(
        self,
        data: list[dict],
        api_function_name: str,
        strategy: dict[str, Any],
    ) -> WriteResult:  # WHY: redis timeseries write path with csv fallback
        """Dispatch to Redis TS. Degrade to csv_only if unavailable."""
        if not self._redis_available or self._redis_writer is None:  # WHY: guard clause for unavailable
            return self._csv_fallback(api_function_name, BACKEND_REDIS)
        try:
            return self._redis_writer.write(data, api_function_name, strategy)  # WHY: perform ts write
        except Exception as error:  # WHY: convert unexpected writer failure to csv envelope
            logger.error(EVT_REDIS_WRITE_ERR, error=str(error))
            return _error_write_result(data, str(error))

    def _write_redis_json(
        self,
        data: list[dict],
        api_function_name: str,
        strategy: dict[str, Any],
    ) -> WriteResult:  # WHY: redis JSON write path with csv fallback
        """Dispatch to Redis JSON. Degrade to csv_only if unavailable."""
        if not self._redis_json_available or self._redis_json_writer is None:  # WHY: guard for unavailable
            return self._csv_fallback(api_function_name, BACKEND_REDIS_JSON)
        try:
            return self._redis_json_writer.write(data, api_function_name, strategy)  # WHY: perform json write
        except Exception as error:  # WHY: convert unexpected writer failure to csv envelope
            logger.error(EVT_REDIS_JSON_WRITE_ERR, error=str(error))
            return _error_write_result(data, str(error))

    def _write_dual(
        self,
        data: list[dict],
        api_function_name: str,
        strategy: dict[str, Any],
    ) -> WriteResult:  # WHY: composite_pk fanout to redis-json + arango
        """Dual-write to Redis JSON + ArangoDB independently."""
        redis_result = self._write_redis_json(data, api_function_name, strategy)  # WHY: leg 1 (redis-json)
        arango_result = self._write_arango(data, api_function_name, strategy)  # WHY: leg 2 (arango)
        dual = DualWriteResult(
            arango_result=arango_result,
            redis_result=redis_result,
        )  # WHY: merge both legs into a single reportable envelope
        return dual.combined  # WHY: caller receives a single WriteResult regardless of leg outcomes

    def _resolve_strategy(self, api_function_name: str) -> dict[str, Any]:  # WHY: strategy lookup helper
        """Look up PK strategy. Fall back to default."""
        if api_function_name in self._strategies:  # WHY: prefer per-endpoint override
            return self._strategies[api_function_name]
        return self._strategies.get("default", DEFAULT_STRATEGY)  # WHY: user default > module default

    def health_check(self) -> dict[str, bool]:  # WHY: exposed for /health endpoints and tests
        """Check connectivity to all backends."""
        return {
            "arangodb": self._arango_available,
            "redis": self._redis_available,
            "redis_json": self._redis_json_available,
            "standalone": self.config.standalone_mode,
        }  # WHY: uniform status dict consumed by health probes

    def handle_webhook_audit(self, payload: dict[str, Any]) -> None:  # WHY: webhook side-effect snapshot
        """Snapshot config when an audit webhook payload arrives."""
        if self._arango_writer is None:  # WHY: cannot snapshot without arango
            return
        entity_id = str(payload.get("object_id", ""))  # WHY: coerce object_id to string
        if not entity_id:  # WHY: skip payloads missing the primary identifier
            return
        config_body = payload.get("after", payload)  # WHY: prefer post-change body when present
        request = SnapshotRequest(
            entity_type=payload.get("object_type", UNKNOWN_ENTITY_TYPE),
            entity_id=entity_id,
            record=config_body,
            config_hash=_hash_payload(config_body),
            source=SNAPSHOT_SOURCE_WEBHOOK,
        )  # WHY: bundle snapshot args into a single frozen value
        self._safe_snapshot(request, EVT_WEBHOOK_SNAPSHOT_FAILED)  # WHY: reuse shared snapshot wrapper

    def ingest_stats_batch(
        self,
        data: list[dict],
        api_function_name: str,
    ) -> WriteResult:  # WHY: entry point used by the periodic-stats background thread
        """Ingest periodic stats pull data into Redis TimeSeries.

        Called by the periodic stats collector background thread.
        """
        if not self._redis_available or self._redis_writer is None:  # WHY: guard against unavailable
            return self._csv_fallback(api_function_name, BACKEND_REDIS)
        strategy = self._resolve_strategy(api_function_name)  # WHY: look up strategy for this api
        return self._write_redis(data, api_function_name, strategy)  # WHY: reuse the shared ts path

    def pull_config_history(self, configs: list[dict]) -> int:  # WHY: bulk snapshot of device configs
        """Import device config history into ArangoDB snapshots.

        Called on startup or periodically via
        searchOrgDeviceLastConfigs / searchSiteDeviceLastConfigs.
        Returns count of new snapshots stored.
        """
        if self._arango_writer is None:  # WHY: no arango means nothing to store
            return 0
        stored = 0  # WHY: accumulator for successfully stored snapshots
        for config_record in configs:  # WHY: iterate to isolate per-record failures
            if self._snapshot_config_history_record(config_record):  # WHY: helper returns True on store
                stored += 1
        return stored  # WHY: return count so caller can log ingestion progress

    def _snapshot_config_history_record(self, config_record: dict[str, Any]) -> bool:  # WHY: per-record helper
        """Snapshot a single config-history record. Return True on store."""
        entity_id = str(config_record.get("device_id", config_record.get("mac", "")))  # WHY: device_id or mac
        if not entity_id:  # WHY: skip rows missing both identifiers
            return False
        request = SnapshotRequest(
            entity_type=DEVICE_CONFIG_ENTITY_TYPE,
            entity_id=entity_id,
            record=config_record,
            config_hash=_hash_payload(config_record),
            source=SNAPSHOT_SOURCE_API,
        )  # WHY: bundle snapshot args into a single frozen value
        return self._safe_snapshot(request, EVT_CFG_HISTORY_FAILED)  # WHY: reuse shared snapshot wrapper

    def close(self) -> None:  # WHY: gracefully release backend handles on shutdown
        """Close all database connections gracefully."""
        self._close_writer(self._arango_writer, EVT_ARANGO_CLOSE_ERR)  # WHY: shut arango down first
        self._close_writer(self._redis_writer, EVT_REDIS_CLOSE_ERR)  # WHY: shut redis-ts down second
        logger.info(EVT_ROUTER_CLOSED)  # WHY: single breadcrumb marking clean shutdown

    @staticmethod
    def _close_writer(writer: Any, error_event: str) -> None:  # WHY: shared close helper
        """Close a writer if present, swallowing errors as warnings."""
        if writer is None:  # WHY: nothing to close for unavailable backends
            return
        try:
            writer.close()  # WHY: release sockets / pools inside the writer
        except Exception as error:  # WHY: shutdown must never raise upstream
            logger.warning(error_event, error=str(error))

    @staticmethod
    def _csv_fallback(api_function_name: str, backend: str) -> WriteResult:  # WHY: shared csv fallback envelope
        """Return a csv_only result when the target backend is down."""
        logger.warning(EVT_DEGRADED_MODE, api=api_function_name, backend=backend)  # WHY: single breadcrumb
        return WriteResult(
            success=True,
            backend=BACKEND_CSV_ONLY,
            records_written=0,
            records_failed=0,
            error_message=f"{backend} unavailable, CSV only",
        )  # WHY: success=True keeps callers from treating csv fallback as a hard error
