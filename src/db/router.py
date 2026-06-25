"""DatabaseRouter: central dispatch for polyglot database writes.

Routes API data to ArangoDB or Redis TimeSeries based on the
ENDPOINT_PRIMARY_KEY_STRATEGIES configuration in MistHelper.py.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

import structlog

from . import DatabaseConfig, DualWriteResult, WriteResult
from .arango_writer import ArangoDBWriter
from .redis_writer import RedisJSONWriter, RedisTimeSeriesWriter

logger = structlog.get_logger(__name__)

ARANGO_ONLY_TYPES = {"natural_pk", "auto_increment_with_unique"}
DUAL_WRITE_TYPES = {"composite_pk"}
TIMESERIES_TYPES = {"timeseries_pk"}

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
}

DEFAULT_STRATEGY: dict[str, Any] = {
    "type": "auto_increment_with_unique",
    "primary_key": ["misthelper_internal_id"],
}


class DatabaseRouter:
    """Route and write data to the appropriate backend."""

    def __init__(
        self,
        config: DatabaseConfig,
        strategies: dict[str, Any] | None = None,
    ) -> None:
        """Initialize database router and connect to available backends."""
        self.config = config
        self._strategies = strategies or {}
        self._arango_available = False
        self._redis_available = False
        self._redis_json_available = False
        self._arango_writer: ArangoDBWriter | None = None
        self._redis_writer: RedisTimeSeriesWriter | None = None
        self._redis_json_writer: RedisJSONWriter | None = None

        if config.standalone_mode:
            logger.info("standalone_mode", msg="CSV-only output")
            return

        self._connect_arango()
        self._connect_redis()
        self._connect_redis_json()

    def _connect_arango(self) -> None:
        """Attempt ArangoDB connection; set availability flag."""
        try:
            self._arango_writer = ArangoDBWriter(self.config)
            self._arango_available = True
        except Exception as error:
            self._arango_available = False
            logger.warning("arangodb_unavailable", error=str(error))

    def _connect_redis(self) -> None:
        """Attempt Redis connection; set availability flag."""
        try:
            self._redis_writer = RedisTimeSeriesWriter(self.config)
            self._redis_available = True
        except Exception as error:
            self._redis_available = False
            logger.warning("redis_unavailable", error=str(error))

    def _connect_redis_json(self) -> None:
        """Attempt Redis JSON connection; set availability flag."""
        try:
            self._redis_json_writer = RedisJSONWriter(self.config)
            self._redis_json_available = True
        except Exception as error:
            self._redis_json_available = False
            logger.warning("redis_json_unavailable", error=str(error))

    def write(self, data: list[dict], api_function_name: str) -> WriteResult:
        """Route data to the correct backend based on PK strategy."""
        if self.config.standalone_mode:
            return WriteResult(
                success=True,
                backend="csv_only",
                records_written=0,
                records_failed=0,
            )

        strategy = self._resolve_strategy(api_function_name)
        strategy_type = strategy.get("type", "auto_increment_with_unique")

        if strategy_type in TIMESERIES_TYPES:
            return self._write_redis(data, api_function_name, strategy)
        if strategy_type in DUAL_WRITE_TYPES:
            return self._write_dual(data, api_function_name, strategy)
        return self._write_arango(data, api_function_name, strategy)

    def _write_arango(
        self,
        data: list[dict],
        api_function_name: str,
        strategy: dict[str, Any],
    ) -> WriteResult:
        """Dispatch to ArangoDB; degrade to csv_only if unavailable."""
        if not self._arango_available or self._arango_writer is None:
            return self._csv_fallback(api_function_name, "arangodb")
        try:
            result = self._arango_writer.write(
                data,
                api_function_name,
                strategy,
            )
            if result.success:
                self._snapshot_if_config(
                    data,
                    api_function_name,
                    strategy,
                )
            return result
        except Exception as error:
            logger.error("arango_write_error", error=str(error))
            return WriteResult(
                success=False,
                backend="csv_only",
                records_written=0,
                records_failed=len(data),
                error_message=str(error),
            )

    def _snapshot_if_config(
        self,
        data: list[dict],
        api_function_name: str,
        strategy: dict[str, Any],
    ) -> None:
        """Create config snapshots for configuration entity types."""
        if api_function_name not in CONFIG_SNAPSHOT_APIS:
            return
        if self._arango_writer is None:
            return
        pk_field = strategy.get("primary_key", ["id"])[0]
        for record in data:
            entity_id = str(record.get(pk_field, ""))
            if not entity_id:
                continue
            body = json.dumps(record, sort_keys=True, default=str)
            config_hash = hashlib.sha256(body.encode()).hexdigest()
            try:
                self._arango_writer.snapshot(
                    api_function_name,
                    entity_id,
                    record,
                    config_hash,
                    "api_pull",
                )
            except Exception as error:
                logger.warning(
                    "snapshot_failed",
                    entity_id=entity_id,
                    error=str(error),
                )

    def _write_redis(
        self,
        data: list[dict],
        api_function_name: str,
        strategy: dict[str, Any],
    ) -> WriteResult:
        """Dispatch to Redis TS; degrade to csv_only if unavailable."""
        if not self._redis_available or self._redis_writer is None:
            return self._csv_fallback(api_function_name, "redis")
        try:
            return self._redis_writer.write(
                data,
                api_function_name,
                strategy,
            )
        except Exception as error:
            logger.error("redis_write_error", error=str(error))
            return WriteResult(
                success=False,
                backend="csv_only",
                records_written=0,
                records_failed=len(data),
                error_message=str(error),
            )

    def _write_redis_json(
        self,
        data: list[dict],
        api_function_name: str,
        strategy: dict[str, Any],
    ) -> WriteResult:
        """Dispatch to Redis JSON; degrade to csv_only if unavailable."""
        if not self._redis_json_available or self._redis_json_writer is None:
            return self._csv_fallback(api_function_name, "redis_json")
        try:
            return self._redis_json_writer.write(
                data,
                api_function_name,
                strategy,
            )
        except Exception as error:
            logger.error("redis_json_write_error", error=str(error))
            return WriteResult(
                success=False,
                backend="csv_only",
                records_written=0,
                records_failed=len(data),
                error_message=str(error),
            )

    def _write_dual(
        self,
        data: list[dict],
        api_function_name: str,
        strategy: dict[str, Any],
    ) -> WriteResult:
        """Dual-write to Redis JSON + ArangoDB independently."""
        redis_result = self._write_redis_json(data, api_function_name, strategy)
        arango_result = self._write_arango(data, api_function_name, strategy)
        dual = DualWriteResult(
            arango_result=arango_result,
            redis_result=redis_result,
        )
        return dual.combined

    def _resolve_strategy(self, api_function_name: str) -> dict[str, Any]:
        """Look up PK strategy; fall back to default."""
        if api_function_name in self._strategies:
            return self._strategies[api_function_name]
        return self._strategies.get("default", DEFAULT_STRATEGY)

    def health_check(self) -> dict[str, bool]:
        """Check connectivity to all backends."""
        return {
            "arangodb": self._arango_available,
            "redis": self._redis_available,
            "redis_json": self._redis_json_available,
            "standalone": self.config.standalone_mode,
        }

    def handle_webhook_audit(self, payload: dict[str, Any]) -> None:
        """Snapshot config when an audit webhook payload arrives."""
        if self._arango_writer is None:
            return
        entity_type = payload.get("object_type", "unknown")
        entity_id = str(payload.get("object_id", ""))
        if not entity_id:
            return
        config_body = payload.get("after", payload)
        body = json.dumps(config_body, sort_keys=True, default=str)
        config_hash = hashlib.sha256(body.encode()).hexdigest()
        try:
            self._arango_writer.snapshot(
                entity_type,
                entity_id,
                config_body,
                config_hash,
                "webhook",
            )
        except Exception as error:
            logger.warning(
                "webhook_snapshot_failed",
                entity_id=entity_id,
                error=str(error),
            )

    def ingest_stats_batch(
        self,
        data: list[dict],
        api_function_name: str,
    ) -> WriteResult:
        """Ingest periodic stats pull data into Redis TimeSeries.

        Called by the periodic stats collector background thread.
        """
        if not self._redis_available or self._redis_writer is None:
            return self._csv_fallback(api_function_name, "redis")
        strategy = self._resolve_strategy(api_function_name)
        return self._write_redis(data, api_function_name, strategy)

    def pull_config_history(
        self,
        configs: list[dict],
    ) -> int:
        """Import device config history into ArangoDB snapshots.

        Called on startup or periodically via
        searchOrgDeviceLastConfigs / searchSiteDeviceLastConfigs.
        Returns count of new snapshots stored.
        """
        if self._arango_writer is None:
            return 0
        stored = 0
        for config_record in configs:
            entity_id = str(config_record.get("device_id", config_record.get("mac", "")))
            if not entity_id:
                continue
            body = json.dumps(
                config_record,
                sort_keys=True,
                default=str,
            )
            config_hash = hashlib.sha256(body.encode()).hexdigest()
            try:
                self._arango_writer.snapshot(
                    "device_config",
                    entity_id,
                    config_record,
                    config_hash,
                    "api_pull",
                )
                stored += 1
            except Exception as error:
                logger.warning(
                    "config_history_failed",
                    entity_id=entity_id,
                    error=str(error),
                )
        return stored

    def close(self) -> None:
        """Close all database connections gracefully."""
        if self._arango_writer is not None:
            try:
                self._arango_writer.close()
            except Exception as error:
                logger.warning("arangodb_close_error", error=str(error))
        if self._redis_writer is not None:
            try:
                self._redis_writer.close()
            except Exception as error:
                logger.warning("redis_close_error", error=str(error))
        logger.info("router_closed")

    @staticmethod
    def _csv_fallback(api_function_name: str, backend: str) -> WriteResult:
        """Return a csv_only result when the target backend is down."""
        logger.warning(
            "degraded_mode",
            api=api_function_name,
            backend=backend,
        )
        return WriteResult(
            success=True,
            backend="csv_only",
            records_written=0,
            records_failed=0,
            error_message=f"{backend} unavailable, CSV only",
        )
