# Implementation Plan: Polyglot Data Routing Refactor

**Branch**: `185-polyglot-data-routing` | **Date**: 2026-04-22 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/185-polyglot-data-routing/spec.md`

## Summary

Refactor the MistHelper data pipeline so polyglot backends (ArangoDB, Redis) receive raw unflattened API data before the CSV flatten/escape step. Introduce `timeseries_pk` as a new strategy type for pure-numeric endpoints, route `composite_pk` data to both Redis JSON and ArangoDB (dual-write), and reclassify ~6 endpoints from `composite_pk` to `timeseries_pk`. CSV/SQLite output remains byte-identical to current behavior.

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: `mistapi` 0.59+, `redis-py` (with JSON commands), `python-arango`, `structlog`
**Storage**: ArangoDB 3.12 (documents/graph), Redis Stack (JSON + TimeSeries), SQLite (local), CSV (export)
**Testing**: `python MistHelper.py --test` (skip 14, 18, 63-65, 90-100); manual verification via ArangoDB HTTP API and `redis-cli`
**Target Platform**: Windows 11 (dev), Linux container (production)
**Project Type**: CLI tool with menu-driven operations
**Performance Goals**: Dual-write overhead < 2x single-backend write (SC-007)
**Constraints**: Max 25 lines/function, max 5 params/function (Five-Item Rule)
**Scale/Scope**: ~28K line single-file main + `src/db/` package (4 modules)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Design Check

| Principle | Status | Notes |
|---|---|---|
| I. Five-Item Rule | PASS | New `RedisJSONWriter` class stays within limits. `write_with_format_selection` gains 1 param (5 total = at limit). Router methods remain under 25 lines each. |
| II. Class-Based Architecture | PASS | `RedisJSONWriter` is a new class in `redis_writer.py`. No wrapper functions. |
| III. Safety-First | PASS | No new user input. Backend failures degrade gracefully to CSV-only with warning logs. |
| IV. Full Deployment Pipeline | PASS | All modified files pass `py_compile`, `ruff`, `black` before commit. |
| V. Observability & Logging | PASS | All new writers use `structlog` with ASCII-only output. Backend failures logged at warning level. |
| Technology Constraints | PASS | Uses `redis-py` JSON commands, `python-arango`. No new dependencies. |
| Security: Fix Over Suppress | PASS | No new security suppressions needed. |

### Post-Design Check

| Principle | Status | Notes |
|---|---|---|
| I. Five-Item Rule | PASS | `write_with_format_selection` has 5 params (at limit, acceptable). `RedisJSONWriter.write` has 4 params. `DatabaseRouter.write` unchanged at 3 params. No function exceeds 25 lines in the design. |
| II. Class-Based Architecture | PASS | `RedisJSONWriter` class added. `DatabaseRouter` extended with `_write_dual` method. No standalone wrappers. |
| III. Safety-First | PASS | `raw_data` parameter is optional with `None` default -- backward compatible. All backend failures caught and logged. |
| IV. Full Deployment Pipeline | PASS | Quality gates defined in quickstart.md. |
| V. Observability & Logging | PASS | `RedisJSONWriter` uses `structlog` via `get_logger()`. Dual-write logs both backend results. |

## Project Structure

### Documentation (this feature)

```text
specs/185-polyglot-data-routing/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── internal-interfaces.md  # Phase 1 output
├── checklists/
│   └── requirements.md  # Pre-existing
└── spec.md              # Feature specification
```

### Source Code (repository root)

```text
src/db/
├── __init__.py          # MODIFIED: export RedisJSONWriter
├── arango_writer.py     # UNCHANGED
├── redis_writer.py      # MODIFIED: add RedisJSONWriter class
├── retention.py         # UNCHANGED
└── router.py            # MODIFIED: routing constants, dual-write, timeseries_pk

MistHelper.py            # MODIFIED: raw_data parameter, strategy reclassification
```

**Structure Decision**: All changes fit within the existing `src/db/` package structure. No new packages or directories needed. `RedisJSONWriter` lives alongside `RedisTimeSeriesWriter` in `redis_writer.py` since both are Redis writers sharing the same connection infrastructure.

## Design Decisions

### D1: raw_data Parameter (Not Separate Pre-Route Call)

The `write_with_format_selection()` method gains an optional `raw_data` parameter. Callers pass both flattened data (for CSV) and raw data (for polyglot). This is preferred over:
- **Pre-route call before write**: Would require callers to know about polyglot routing (leaks abstraction)
- **Deep copy inside write**: Wasteful memory for large datasets
- **Global/class variable**: Thread-safety concerns

### D2: RedisJSONWriter in redis_writer.py (Not Separate File)

Both Redis writers share connection setup, module detection, and pipelining patterns. Keeping them in one file avoids import complexity and stays within the 5-item rule for the `src/db/` directory (5 files currently).

### D3: Independent Dual-Write (Not Transactional)

For `composite_pk` endpoints, Redis JSON and ArangoDB writes are independent. One can fail without blocking the other. This matches the existing pattern where polyglot failure never blocks CSV output. The `DualWriteResult` captures both outcomes.

### D4: TTL on Redis JSON Documents

Redis JSON documents get a configurable TTL (default 7 days via `REDIS_JSON_TTL_DAYS`). This prevents unbounded memory growth. ArangoDB serves as the long-term archive. Redis serves recent-event queries only.

### D5: Endpoint Reclassification is Conservative

Only 6 clearly-numeric endpoints move to `timeseries_pk`. All event, alarm, client, and diagnostic endpoints stay as `composite_pk`. This minimizes risk and can be expanded later.

## Implementation Phases

### Phase 1: Raw Data Pipeline (User Story 1 - P1)

**Goal**: Route unflattened API data to polyglot backends while preserving CSV output.

**Changes**:

1. **`MistHelper.py` - `DataExporter.write_with_format_selection()`**:
   - Add `raw_data: list[dict[str, Any]] | None = None` parameter
   - Pass `raw_data` (or `data` fallback) to `_route_to_polyglot()`

2. **`MistHelper.py` - `DataExporter._route_to_polyglot()`**:
   - Add `raw_data` parameter
   - Pass `raw_data or data` to `self._router.write()`

3. **`MistHelper.py` - Caller updates (incremental)**:
   - Update menu operations that flatten before writing to pass both:
     ```python
     # Before
     flattened = DataProcessingUtils.flatten_and_escape_data(raw_results)
     DataExporter.write_with_format_selection(flattened, filename, api_function_name=name)
     
     # After
     flattened = DataProcessingUtils.flatten_and_escape_data(raw_results)
     DataExporter.write_with_format_selection(
         flattened, filename, api_function_name=name, raw_data=raw_results
     )
     ```
   - Start with high-value endpoints: `listOrgSites` (menu 11), `getOrgInventory` (menu 1), `listSiteDevices` (menu 3)

**Verification**: Run menu 11, query ArangoDB for nested fields (e.g., `doc.latlng.lat`).

### Phase 2: Redis JSON Writer + Dual-Write (User Story 2 - P2)

**Goal**: Store `composite_pk` event documents as Redis JSON with dual-write to ArangoDB.

**Changes**:

1. **`src/db/redis_writer.py` - Add `RedisJSONWriter` class**:
   - `__init__`: Reuse Redis connection, verify `ReJSON` module
   - `write()`: Pipeline `JSON.SET` + `EXPIRE` for each record
   - `_build_key()`: Construct key from endpoint name + PK fields
   - Uses `REDIS_JSON_TTL_DAYS` env var (default 7)

2. **`src/db/router.py` - Update routing**:
   - Replace `ARANGO_PK_TYPES` / `REDIS_PK_TYPES` with `ARANGO_ONLY_TYPES` / `DUAL_WRITE_TYPES` / `TIMESERIES_TYPES`
   - Add `_write_dual()` method for `composite_pk`: calls both `_write_redis_json()` and `_write_arango()`
   - Initialize `RedisJSONWriter` alongside `RedisTimeSeriesWriter`

3. **`src/db/__init__.py`**:
   - Add `RedisJSONWriter` to `__all__`

**Verification**: Run menu 13 (Device Events), check Redis JSON documents and ArangoDB archive.

### Phase 3: TimeSeries Strategy Type (User Story 3 - P3)

**Goal**: Route pure-numeric endpoints to Redis TimeSeries with explicit field configuration.

**Changes**:

1. **`src/db/router.py`**:
   - Add `timeseries_pk` to routing dispatch (uses existing `_write_redis()`)
   - `RedisTimeSeriesWriter.write()` already handles numeric extraction; `ts_value_fields` and `ts_label_fields` are passed through the strategy dict

2. **`src/db/redis_writer.py` - `RedisTimeSeriesWriter`**:
   - Update `_extract_chunk()` to respect `ts_value_fields` (only extract listed fields) and `ts_label_fields` (use as TS labels instead of dropping)
   - If `ts_value_fields` not in strategy, fall back to current auto-detect behavior

**Verification**: Run a device stats endpoint, verify Redis TS has labeled data points.

### Phase 4: Endpoint Reclassification (User Story 4 - P2)

**Goal**: Reclassify endpoints in `ENDPOINT_PRIMARY_KEY_STRATEGIES` to correct strategy types.

**Changes**:

1. **`MistHelper.py` - `ENDPOINT_PRIMARY_KEY_STRATEGIES`**:
   - Change 6 stats/port endpoints from `composite_pk` to `timeseries_pk`
   - Add `ts_value_fields` and `ts_label_fields` to each reclassified endpoint
   - All other endpoints remain unchanged

**Endpoints to reclassify**:
| Endpoint | New Fields |
|---|---|
| `listOrgDevicesStats` | `ts_value_fields: [cpu_util, mem_util, ...], ts_label_fields: [hostname, model, ...]` |
| `listSiteDevicesStats` | Same pattern |
| `listSiteWirelessClientsStats` | `ts_value_fields: [rssi, snr, ...], ts_label_fields: [ssid, hostname, ...]` |
| `searchOrgSwOrGwPorts` | `ts_value_fields: [rx_bytes, tx_bytes, ...], ts_label_fields: [port_id, ...]` |
| `searchSiteSwOrGwPorts` | Same pattern |
| `searchOrgPeerPathStats` | `ts_value_fields: [latency, jitter, loss], ts_label_fields: [from_device, to_device]` |

**Verification**: Inspect the strategies dict. Run a stats endpoint and confirm Redis TS receives labeled metrics.

## Dependency Graph

```text
Phase 1 (raw_data pipeline)
    ↓
Phase 2 (RedisJSONWriter + dual-write)  ←── Phase 4 (reclassification)
    ↓
Phase 3 (timeseries_pk routing)  ←── Phase 4 (reclassification)
```

- Phase 1 is prerequisite for all others (provides raw data path)
- Phases 2 and 3 are independent of each other
- Phase 4 depends on both Phase 2 (composite_pk routing must exist) and Phase 3 (timeseries_pk routing must exist)

## Risk Mitigation

| Risk | Mitigation |
|---|---|
| Breaking CSV output | `raw_data` is optional with `None` default; CSV path unchanged |
| Redis JSON module not loaded | Module check at init; graceful degradation to ArangoDB-only |
| Memory pressure from raw_data copy | Raw data is a reference, not a copy; Python shares the list until mutation |
| Large dual-write overhead | Independent writes, pipelined batches, async not needed at current scale |
| Reclassification breaks existing TS data | Only 6 endpoints move; they already have `composite_pk` which was routing to TS |

## Complexity Tracking

No constitution violations requiring justification. All changes stay within the Five-Item Rule limits:
- `write_with_format_selection`: 5 params (at limit, all necessary)
- `RedisJSONWriter`: 3 public methods (write, health_check, __init__)
- `src/db/` directory: 5 files (at limit after adding nothing new -- `RedisJSONWriter` goes in existing `redis_writer.py`)
