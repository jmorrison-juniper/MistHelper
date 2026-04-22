# Contracts: Polyglot Data Routing Refactor

**Feature**: 185-polyglot-data-routing | **Date**: 2026-04-22

## Internal Python Interfaces

These are internal module contracts -- not external APIs. They define the signatures that implementation tasks must conform to.

### 1. DataExporter.write_with_format_selection (updated)

```python
@staticmethod
def write_with_format_selection(
    data: list[dict[str, Any]],
    filename_or_table: str,
    format_override: str | None = None,
    api_function_name: str | None = None,
    raw_data: list[dict[str, Any]] | None = None,  # NEW
) -> bool:
    """
    Writes data to CSV/SQLite and routes to polyglot backends.

    Args:
        data: Flattened data for CSV/SQLite output.
        filename_or_table: Target filename or table name.
        format_override: Optional output format override.
        api_function_name: Endpoint name for strategy lookup.
        raw_data: Unflattened API response for polyglot backends.
                  If None, falls back to `data` (backward compatible).

    Returns:
        True if CSV/SQLite write succeeded.
    """
```

**Contract**: CSV/SQLite always receives `data` (flattened). Polyglot backends receive `raw_data` if provided, otherwise `data`.

### 2. DataExporter._route_to_polyglot (updated)

```python
@staticmethod
def _route_to_polyglot(
    data: list[dict[str, Any]],
    api_function_name: str | None,
    raw_data: list[dict[str, Any]] | None = None,
) -> None:
    """Route data to polyglot backends, preferring raw_data."""
```

**Contract**: Passes `raw_data or data` to `DatabaseRouter.write()`.

### 3. DatabaseRouter.write (updated)

```python
def write(
    self,
    data: list[dict[str, Any]],
    api_function_name: str,
) -> WriteResult:
    """
    Route data to backends based on endpoint strategy type.

    Routing:
    - natural_pk → ArangoDB (raw documents)
    - composite_pk → Redis JSON + ArangoDB (dual-write)
    - timeseries_pk → Redis TimeSeries
    - auto_increment_with_unique → ArangoDB
    """
```

**Contract**: Signature unchanged. The `data` parameter now receives raw (unflattened) data from the updated caller chain.

### 4. RedisJSONWriter (new class)

```python
class RedisJSONWriter:
    """Writes composite_pk data as Redis JSON documents."""

    def __init__(self, config: DatabaseConfig) -> None: ...

    def write(
        self,
        data: list[dict[str, Any]],
        api_function_name: str,
        strategy: dict[str, Any],
    ) -> WriteResult: ...
```

**Contract**:
- Upserts documents using `JSON.SET` with key pattern `{endpoint}:{pk_values}`
- Preserves all fields from raw API response (zero field loss)
- Applies TTL via `EXPIRE` (configurable via `REDIS_JSON_TTL_DAYS`)
- Uses pipelined batch writes for performance
- Returns `WriteResult` with `backend="redis_json"`

### 5. DatabaseRouter routing constants (updated)

```python
ARANGO_ONLY_TYPES = {"natural_pk", "auto_increment_with_unique"}
DUAL_WRITE_TYPES = {"composite_pk"}
TIMESERIES_TYPES = {"timeseries_pk"}
```

**Contract**: Router uses these sets to dispatch to the correct writer(s).
