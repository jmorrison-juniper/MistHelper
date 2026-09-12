# Contract: DatabaseRouter

**Feature**: 184-polyglot-db-migration | **Date**: 2026-04-20

## Overview

`DatabaseRouter` is the central dispatch class that replaces direct `SQLiteDatabaseWriter` calls in `DataExporter`. It reads the `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary, determines the backend for each dataset, and delegates to the appropriate writer class.

## Public Interface

### `DatabaseRouter.__init__(self, config: DatabaseConfig)`

Initialize the router with connection configuration.

**Parameters**:

| Name | Type | Required | Description |
| - | - | - | - |
| `config` | `DatabaseConfig` | Yes | Dataclass with connection settings (from `.env`) |

**Behavior**:
- Attempts connection to ArangoDB and Redis on init
- Logs connection status at Info level
- Sets internal `_arango_available` and `_redis_available` flags
- Does NOT raise on connection failure (degraded mode)
- In standalone mode (no containers), sets both flags to False without attempting connections

### `DatabaseRouter.write(self, data: list[dict], api_function_name: str)`

Route and write data to the appropriate backend.

**Parameters**:

| Name | Type | Required | Description |
| - | - | - | - |
| `data` | `list[dict]` | Yes | Flattened records from API response |
| `api_function_name` | `str` | Yes | Key into `ENDPOINT_PRIMARY_KEY_STRATEGIES` |

**Behavior**:
1. Look up `api_function_name` in `ENDPOINT_PRIMARY_KEY_STRATEGIES`
2. Determine backend from strategy `type`:
   - `natural_pk` or `auto_increment_with_unique` → ArangoDB
   - `composite_pk` → Redis TimeSeries
3. If target backend is unavailable, log warning and skip (CSV already written by caller)
4. Call appropriate writer's `write()` method
5. Return `WriteResult` with success/failure status

**Returns**: `WriteResult` dataclass

**Error handling**:
- Connection errors: log error, set backend unavailable, return `WriteResult(success=False)`
- Data validation errors: log error per-record, continue with remaining records
- Never raises exceptions to caller

### `DatabaseRouter.health_check(self) -> dict[str, bool]`

Check connectivity to all backends.

**Returns**:

```python
{
    "arangodb": True,   # or False
    "redis": True,      # or False
    "standalone": False  # True if running without containers
}
```

### `DatabaseRouter.close(self)`

Close all database connections gracefully.

## Supporting Types

### `DatabaseConfig` (dataclass)

```python
@dataclass
class DatabaseConfig:
    arango_host: str = "http://arangodb:8529"
    arango_database: str = "misthelper"
    arango_username: str = "root"
    arango_password: str = ""  # from ARANGO_ROOT_PASSWORD env
    redis_host: str = "redis-stack"
    redis_port: int = 6379
    redis_password: str = ""  # from REDIS_PASSWORD env
    standalone_mode: bool = False  # True = skip all backend connections
```

### `WriteResult` (dataclass)

```python
@dataclass
class WriteResult:
    success: bool
    backend: str  # "arangodb", "redis", "csv_only"
    records_written: int
    records_failed: int
    error_message: str = ""
```

## Integration Point: DataExporter

The existing `DataExporter.write_with_format_selection()` method (line ~9410 in MistHelper.py) is modified to:

1. **Always write CSV** (existing behavior, unchanged)
2. **If not standalone mode**: call `DatabaseRouter.write(data, api_function_name)`
3. **Log WriteResult** at Info level

```python
# Pseudocode for modified DataExporter
class DataExporter:
    def __init__(self):
        config = DatabaseConfig.from_env()
        self.router = DatabaseRouter(config)

    def write_with_format_selection(self, data, filename, api_function_name=None):
        # Step 1: Always write CSV (existing code)
        self._write_csv(data, filename)

        # Step 2: Route to polyglot backend (new code)
        if api_function_name and not self.router.config.standalone_mode:
            result = self.router.write(data, api_function_name)
            if not result.success:
                logging.warning(f"Backend write failed: {result.error_message}")
```

## ArangoDBWriter Contract

### `ArangoDBWriter.write(self, data: list[dict], collection_name: str, strategy: dict)`

Upsert documents into ArangoDB.

- Uses `collection.insert(doc, overwrite=True, overwrite_mode="replace")`
- Sets `_key` from strategy's `primary_key[0]` field value
- Adds `_misthelper_updated_at` with current epoch
- Manages edge collections for known graph relationships
- Creates collection on first write if it doesn't exist

### `ArangoDBWriter.snapshot(self, entity_type: str, entity_id: str, config_body: dict)`

Create a configuration snapshot if content has changed.

- Computes `config_hash` (SHA-256 of sorted JSON)
- Skips if hash matches latest snapshot for this entity
- Stores in `config_snapshots` collection

## RedisTimeSeriesWriter Contract

### `RedisTimeSeriesWriter.write(self, data: list[dict], api_function_name: str, strategy: dict)`

Write time-series data to Redis.

- Converts each record to one or more TS.ADD commands
- Extracts numeric values from flattened records
- Key pattern: `{api_function_name}:{entity_id}:{field_name}`
- Creates TS key with labels + retention on first write
- Creates compaction rules (hourly, daily) on first write per key
- Uses pipeline for batch writes (performance)

## Error Contracts

| Scenario | Behavior | Log Level |
| - | - | - |
| ArangoDB unreachable on init | Set `_arango_available = False` | Warning |
| Redis unreachable on init | Set `_redis_available = False` | Warning |
| ArangoDB connection lost mid-write | Set unavailable, return failed result | Error |
| Redis connection lost mid-write | Set unavailable, return failed result | Error |
| Unknown api_function_name | Skip routing, CSV-only | Debug |
| Invalid document (missing _key field) | Skip record, continue others | Error |
| Redis key creation failure | Skip key, continue others | Error |
