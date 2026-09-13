# Feature Specification: Polyglot Data Routing Refactor

**Feature Branch**: `185-polyglot-data-routing`
**Created**: 2026-04-22
**Status**: Draft
**Input**: Refactor MistHelper data pipeline so polyglot backends (ArangoDB, Redis) receive raw API data before CSV flattening, and Redis is used to its full capabilities (JSON, Search, TimeSeries) instead of TimeSeries-only.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Raw Document Persistence in ArangoDB (Priority: P1)

As a NOC engineer querying ArangoDB, I want device inventories, site configs, and templates stored as rich nested JSON documents so that I can query nested fields (e.g., `device.radio_config.band_24.power`) without data loss from CSV flattening.

**Why this priority**: ArangoDB currently receives flattened data, losing all nested structure. This is the core pipeline fix that all other stories depend on -- moving the polyglot routing call before the flatten step.

**Independent Test**: Run menu 11 (Org Sites) and verify ArangoDB documents contain nested objects (e.g., `latlng`, `rftemplate_id` as nested references) while CSV output remains identical to current behavior.

**Acceptance Scenarios**:

1. **Given** a Mist API returns nested JSON for org sites, **When** menu 11 runs, **Then** ArangoDB stores the raw nested document and CSV output matches the current flattened format exactly.
2. **Given** a `natural_pk` endpoint executes, **When** data is exported, **Then** ArangoDB receives raw data BEFORE flatten and CSV receives flattened data AFTER flatten.
3. **Given** ArangoDB is unavailable, **When** an export runs, **Then** CSV/SQLite output succeeds normally and a warning is logged for the ArangoDB failure.

---

### User Story 2 - Event Documents in Redis JSON (Priority: P2)

As a NOC engineer investigating incidents, I want event data (device events, alarms, client events) stored as full JSON documents in Redis so that I can query recent events by type, hostname, SSID, or severity without data loss from numeric-only extraction.

**Why this priority**: Currently, `composite_pk` endpoints route to Redis TimeSeries which silently drops all non-numeric fields (event types, hostnames, error messages). This makes Redis useless for event investigation. Storing events as RedisJSON documents preserves the full record for fast recent-event queries.

**Independent Test**: Run menu 13 (Device Events) and verify Redis contains full JSON documents with all fields (event type, device name, text, timestamp) and ArangoDB also receives the full document for archival.

**Acceptance Scenarios**:

1. **Given** device events are fetched from Mist API, **When** menu 13 runs, **Then** Redis stores each event as a JSON document with all original fields preserved.
2. **Given** events are stored in Redis JSON, **When** the same endpoint runs again with overlapping events, **Then** existing documents are updated (upsert) rather than duplicated.
3. **Given** `composite_pk` endpoints execute, **When** data is exported, **Then** both Redis JSON and ArangoDB receive the full raw document (dual-write).

---

### User Story 3 - Numeric Metrics via Redis TimeSeries (Priority: P3)

As a NOC engineer monitoring network health, I want device statistics and port utilization stored in Redis TimeSeries as pure numeric time-series data so that I can chart trends and set threshold alerts on metrics like signal strength, throughput, and port utilization.

**Why this priority**: TimeSeries already works for numeric data. This story introduces the `timeseries_pk` strategy type that explicitly identifies pure-numeric endpoints, replacing the current `composite_pk` classification that incorrectly groups numeric stats with text-heavy events.

**Independent Test**: Run a device stats endpoint and verify Redis TimeSeries receives numeric metrics (CPU, memory, uplink throughput) while non-numeric metadata (hostname, model) is stored as TimeSeries labels rather than dropped.

**Acceptance Scenarios**:

1. **Given** device stats are fetched, **When** a `timeseries_pk` endpoint executes, **Then** numeric fields are stored as TimeSeries data points and text fields are stored as TimeSeries labels.
2. **Given** a `timeseries_pk` endpoint configuration, **When** it specifies `ts_value_fields` and `ts_label_fields`, **Then** only those fields are used for values and labels respectively.
3. **Given** a device stats endpoint runs, **When** the same timestamp data is re-imported, **Then** duplicate data points are not created (idempotent upsert).

---

### User Story 4 - Endpoint Strategy Reclassification (Priority: P2)

As a maintainer of MistHelper, I want each API endpoint classified into the correct primary key strategy (`natural_pk`, `composite_pk`, `timeseries_pk`, `auto_increment_with_unique`) so that data routes to the optimal storage backend for its data shape.

**Why this priority**: The reclassification determines which data goes where. Without it, the pipeline changes from Stories 1-3 would route data incorrectly. This must be done alongside Story 2.

**Independent Test**: Inspect the `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary and verify that pure-numeric endpoints use `timeseries_pk`, event/alarm endpoints use `composite_pk`, and entity endpoints use `natural_pk`.

**Acceptance Scenarios**:

1. **Given** the strategies dictionary is updated, **When** a stats endpoint (e.g., `listOrgDevicesStats`) is classified, **Then** it uses `timeseries_pk` with defined `ts_value_fields` and `ts_label_fields`.
2. **Given** the strategies dictionary is updated, **When** an event endpoint (e.g., `searchOrgDeviceEvents`) is classified, **Then** it uses `composite_pk` routing to Redis JSON + ArangoDB.
3. **Given** existing `natural_pk` and `auto_increment_with_unique` endpoints, **When** the refactor completes, **Then** their classification and behavior remain unchanged.

---

### Edge Cases

- What happens when Redis is unavailable but ArangoDB is up? Data must still persist to ArangoDB and CSV; Redis failure is logged as a warning.
- What happens when an endpoint has no strategy defined? Falls back to `auto_increment_with_unique` with ArangoDB-only routing (current behavior preserved).
- What happens when raw API data contains fields that exceed Redis key length limits? Keys are truncated or hashed with a documented maximum length.
- What happens when a `timeseries_pk` endpoint returns zero numeric fields in a record? The record is skipped for TimeSeries but logged at debug level.
- What happens when `composite_pk` dual-write partially fails (Redis succeeds, ArangoDB fails)? Each backend write is independent; partial success is logged with the failing backend identified.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST route raw (unflattened) API response data to polyglot backends before the CSV flatten/escape step.
- **FR-002**: System MUST preserve existing CSV and SQLite output format exactly (backward compatible).
- **FR-003**: System MUST support a new `timeseries_pk` strategy type that routes pure numeric data to Redis TimeSeries with text metadata as labels.
- **FR-004**: System MUST route `composite_pk` endpoints to both Redis JSON (for fast recent access) and ArangoDB (for archival and graph queries).
- **FR-005**: System MUST store `composite_pk` documents in Redis JSON with all original fields preserved (no field dropping).
- **FR-006**: System MUST continue routing `natural_pk` endpoints to ArangoDB only, with raw nested documents instead of flattened data.
- **FR-007**: System MUST continue routing `auto_increment_with_unique` endpoints to ArangoDB only (unchanged behavior).
- **FR-008**: System MUST handle backend unavailability gracefully -- CSV/SQLite always succeeds; polyglot failures are logged as warnings without blocking the user.
- **FR-009**: System MUST reclassify endpoint strategies in `ENDPOINT_PRIMARY_KEY_STRATEGIES` to correctly separate numeric-only endpoints (`timeseries_pk`) from document endpoints (`composite_pk`).
- **FR-010**: System MUST support upsert semantics for Redis JSON documents using the endpoint's primary key fields.
- **FR-011**: Each function in the modified code MUST conform to the 5-item rule (max 5 parameters, max 25 lines, max 5 logical blocks).
- **FR-012**: All modified files MUST pass quality gates: `py_compile`, `ruff check`, `black --check`.

### Key Entities

- **API Response**: Raw JSON data returned by the Mist API, containing nested objects, arrays, and mixed types. The source of truth for all backends.
- **Endpoint Strategy**: Configuration entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES` that determines primary key type, key fields, index fields, and routing behavior for each API endpoint.
- **TimeSeries Metric**: A numeric measurement associated with a timestamp, device identifier, and descriptive labels. Stored in Redis TimeSeries.
- **Document Record**: A full JSON object representing an event, alarm, client session, or command output. Stored in Redis JSON (recent) and ArangoDB (archive).
- **Entity Record**: A JSON object representing a stable business entity (site, device, template). Stored in ArangoDB with upsert by natural UUID.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: ArangoDB documents for `natural_pk` endpoints contain nested objects (verified by querying a nested field path like `doc.latlng.lat`) rather than flattened key names.
- **SC-002**: Redis JSON documents for `composite_pk` endpoints contain 100% of the fields present in the raw API response (zero field loss compared to current TimeSeries approach).
- **SC-003**: CSV output for any menu operation produces identical content before and after the refactor (byte-level comparison of output files).
- **SC-004**: `timeseries_pk` endpoints store numeric values as Redis TimeSeries data points with at least device identifier and metric name as labels.
- **SC-005**: Backend failure (Redis or ArangoDB unavailable) does not prevent CSV/SQLite output from completing successfully.
- **SC-006**: All modified files pass `py_compile`, `ruff check`, and `black --check` with zero violations.
- **SC-007**: Dual-write for `composite_pk` endpoints completes within 2x the time of single-backend write (acceptable overhead for data completeness).

## Assumptions

- Redis Stack container is already running with RedisJSON, RediSearch, and RedisTimeSeries modules loaded.
- ArangoDB 3.12 is running at `localhost:8529` with the `misthelper` database created.
- The existing `src/db/router.py`, `src/db/redis_writer.py`, and `src/db/arango_writer.py` modules provide the integration points for routing changes.
- The `_route_to_polyglot()` method signature can accept a `raw_data` parameter without breaking existing callers.
- Redis JSON key naming will follow the pattern `{endpoint_name}:{primary_key_value}` for document lookup.
- RediSearch index creation is deferred to a future feature (not part of this refactor).

## Scope Boundaries

### In Scope

- Moving the polyglot routing call to occur before CSV flattening in `MistHelper.py`
- Adding `timeseries_pk` strategy type to the router and strategies dictionary
- Adding a Redis JSON writer class to `src/db/redis_writer.py`
- Reclassifying ~40 endpoint strategies in `ENDPOINT_PRIMARY_KEY_STRATEGIES`
- Dual-write for `composite_pk` endpoints (Redis JSON + ArangoDB)
- Passing raw data to ArangoDB for `natural_pk` endpoints

### Out of Scope

- Redis Streams integration for webhook event streaming (future feature)
- RediSearch secondary index creation and query API
- Changing CSV or SQLite output format
- Adding new menu operations
- Graph edge creation in ArangoDB (already exists)
- Performance benchmarking or load testing
- Migration of existing data from old format to new format

## Dependencies

- `redis-stack` container with RedisJSON module (`JSON.SET`, `JSON.GET`, `JSON.MGET` commands)
- `redis-py` library with JSON command support (`redis.commands.json`)
- Existing `src/db/` module structure (router, writers, `__init__.py`)
- Existing `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary in `MistHelper.py`
