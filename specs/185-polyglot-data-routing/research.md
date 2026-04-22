# Research: Polyglot Data Routing Refactor

**Feature**: 185-polyglot-data-routing | **Date**: 2026-04-22

## R1: Where does flattening occur relative to polyglot routing?

**Decision**: The polyglot routing call currently happens **after** the flatten/CSV write step.

**Evidence**: In `MistHelper.py` line ~9489, `_route_to_polyglot(data, api_function_name)` is called at the end of `write_with_format_selection()`, after `_write_csv_format()` or `_write_sqlite_format()` have already consumed and potentially flattened the data. The `data` parameter passed to polyglot is the same list that was already processed by the flatten step.

**Fix approach**: The `write_with_format_selection()` method must accept a `raw_data` parameter containing the unflattened API response. The call sequence becomes:
1. Store raw copy before flatten
2. Flatten for CSV/SQLite
3. Route raw data to polyglot backends

**Alternatives rejected**:
- Deep-copy before flatten: Wasteful for large datasets (10K+ records)
- Flatten inside write method: Flattening already happens at callers before `write_with_format_selection()`

**Key finding**: Flattening is done by individual menu operation functions (callers), not inside `write_with_format_selection()`. The callers call `DataProcessingUtils.flatten_and_escape_data()` then pass the flattened result. This means the raw data is available at the caller level before flattening and can be passed alongside.

## R2: RedisJSON best practices for document upsert

**Decision**: Use `JSON.SET` with the key pattern `{endpoint_name}:{pk_value}` and `NX`/`XX` flags not needed (SET is always upsert by default in RedisJSON).

**Rationale**:
- `JSON.SET key $ document` creates or replaces the document atomically
- For composite PKs, join fields with `:` separator: `searchOrgAlarms:alarm_id:org_id:1234567890`
- Key length limit is 512MB (not a practical concern); hash PKs only if composite key exceeds ~200 chars
- Use pipelining for bulk writes (same pattern as existing TimeSeries writer)

**Alternatives considered**:
- `JSON.MERGE`: Only available in Redis 7.4+; not universally available in redis-stack images
- Separate `JSON.GET` then `JSON.SET`: Unnecessary round-trip; SET is idempotent

## R3: Redis module detection for JSON vs TimeSeries

**Decision**: Extend existing `_verify_timeseries_module()` pattern to also check for `ReJSON` module.

**Rationale**: The `RedisTimeSeriesWriter` already has `_verify_timeseries_module()` that calls `self._client.module_list()`. The same approach works for detecting JSON support. Module name is `ReJSON` (case variations handled by lowering).

## R4: Endpoint reclassification strategy

**Decision**: Introduce `timeseries_pk` as a fourth strategy type. Reclassify endpoints based on data shape:

| Current Type | Endpoint Pattern | New Type | Reason |
|---|---|---|---|
| `composite_pk` | `*Events`, `*Alarms` | `composite_pk` (unchanged) | Text-heavy documents |
| `composite_pk` | `*Stats`, `*Ports` | `timeseries_pk` (new) | Numeric metrics with labels |
| `composite_pk` | `*Clients` (search) | `composite_pk` (unchanged) | Mixed text/numeric documents |
| `composite_pk` | Device utility commands | `composite_pk` (unchanged) | Text-heavy diagnostic output |
| `natural_pk` | Entity endpoints | `natural_pk` (unchanged) | Stable UUID entities |
| `auto_increment_with_unique` | Summary endpoints | `auto_increment_with_unique` (unchanged) | No stable key |

Endpoints moving to `timeseries_pk`:
- `listOrgDevicesStats`
- `listSiteDevicesStats`
- `listSiteWirelessClientsStats`
- `searchOrgSwOrGwPorts`
- `searchSiteSwOrGwPorts`
- `searchOrgPeerPathStats`

New fields for `timeseries_pk` strategy:
```python
{
    "type": "timeseries_pk",
    "primary_key": ["device_id", "timestamp"],
    "ts_value_fields": ["cpu_util", "mem_util", "uptime", ...],  # numeric only
    "ts_label_fields": ["hostname", "model", "type"],  # text metadata
    ...
}
```

## R5: Dual-write architecture for composite_pk

**Decision**: `composite_pk` endpoints write to both Redis JSON (recent/fast access) and ArangoDB (archival/graph). Writes are independent -- one failure does not block the other.

**Rationale**: Events need fast recent-access (Redis JSON with TTL) and long-term archive (ArangoDB). Making writes independent ensures CSV-first reliability is preserved.

**Implementation**: Router dispatches to both writers in sequence. Each returns a `WriteResult`. Combined result reports both backend statuses.

## R6: How callers provide raw data

**Decision**: Add `raw_data` optional parameter to `write_with_format_selection()`. Callers that flatten before calling pass both `data` (flattened) and `raw_data` (original). If `raw_data` is None, fall back to using `data` (backward compatible).

**Rationale**: This is the least disruptive change. Existing callers that don't pass `raw_data` continue working exactly as before. New/updated callers can opt in by passing the raw data.

**Alternatives rejected**:
- Refactoring all callers at once: Too risky for a ~28K line file; incremental is safer
- Storing raw data as a class variable: Thread-safety concerns with concurrent operations
