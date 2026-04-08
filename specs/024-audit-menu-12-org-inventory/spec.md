# Feature Specification: Audit Menu 12 - Organization Inventory Export

**Feature Branch**: `feat/73-audit-menu-12-org-inventory`
**Created**: 2025-04-08
**Status**: Draft
**Issue**: [#73](https://github.com/jmorrison-juniper/MistHelper/issues/73)
**Spec Directory**: `specs/024-audit-menu-12-org-inventory/`

## Summary of Current State

- **Menu ID**: 12
- **Description**: Export the full inventory of devices in the organization
- **Function**: `OrgInventoryExporter.inventory()` (line ~11838 of MistHelper.py)
- **API Endpoint**: `mistapi.api.v1.orgs.inventory.getOrgInventory`
- **Output File**: `OrgInventory.csv`
- **SQL Export Relevant**: Yes
- **Primary Key Strategy**: Already defined as `natural_pk` with `["id"]`
- **Current Test Coverage**: PK strategy structure validated in `tests/unit/test_pk_strategies.py`; no dedicated functional tests exist

## Purpose

Audit the existing Menu 12 implementation to verify correctness, add comprehensive test coverage, and confirm that the dual-output (CSV/SQLite) pipeline produces idempotent, upsert-safe results. The exporter must survive repeated runs without creating duplicate rows in SQLite and must produce a stable CSV column schema that matches the Mist API response fields.

## Stakeholders

- NOC Engineers (primary consumers who run Menu 12 to export inventory)
- Platform Engineers (maintain APIDataFetcher and DataExporter infrastructure)
- QA / Test Engineers (validate export correctness and CI gate coverage)
- Release Manager (must verify no regressions before tagging)

---

## User Scenarios & Testing

### User Story 1 - Export Organization Inventory to CSV (Priority: P1)

A NOC engineer selects Menu 12 from MistHelper to export the complete device inventory for their organization. The system calls the Mist API, retrieves all devices (APs, switches, gateways), flattens nested JSON fields, and writes the results to `OrgInventory.csv` in the `data/` directory. The engineer uses this CSV for offline analysis, reporting, or importing into other tools.

**Why this priority**: This is the core purpose of Menu 12 -- producing a usable inventory export. Without this working correctly, everything else is irrelevant.

**Independent Test**: Can be tested by mocking the Mist API response and verifying that `APIDataFetcher` is instantiated with the correct parameters (api_call, filename, sort_key, limit) and that `execute()` is called.

**Acceptance Scenarios**:

1. **Given** a valid Mist API session and org_id, **When** the user selects Menu 12, **Then** `OrgInventoryExporter.inventory()` calls `APIDataFetcher` with `api_call=mistapi.api.v1.orgs.inventory.getOrgInventory`, `filename="OrgInventory.csv"`, `sort_key="model"`, and `limit=1000`.
2. **Given** the API returns 500 device records, **When** the export completes, **Then** the output file contains exactly 500 rows (plus header) with all fields from the API response flattened into columns.
3. **Given** the API returns an empty result set, **When** the export runs, **Then** the system logs a warning and does not create an empty file or crash.

---

### User Story 2 - Idempotent SQLite Upsert on Repeated Runs (Priority: P1)

A NOC engineer runs Menu 12 twice in succession (or on a daily schedule). The SQLite backend must produce the same row count after both runs -- no duplicate rows. If a device's attributes changed between runs (e.g., firmware version updated), the second run overwrites the stale row using `INSERT OR REPLACE` keyed on the device `id`.

**Why this priority**: Duplicate rows in SQLite corrupt downstream queries and reports. Upsert correctness is a data integrity requirement on par with the export itself.

**Independent Test**: Can be tested by inserting a known fixture into a temporary SQLite database, running the export pipeline a second time with a modified record, and asserting row count stability plus field update.

**Acceptance Scenarios**:

1. **Given** an initial export of 10 devices to SQLite, **When** the same 10 devices are exported again with no changes, **Then** the table contains exactly 10 rows.
2. **Given** an initial export of 10 devices, **When** one device's `model` field changes and the export runs again, **Then** the table contains 10 rows and the updated device reflects the new `model` value.
3. **Given** the PK strategy defines `["id"]` as the primary key, **When** two devices with the same `id` appear in the same batch, **Then** only one row exists in the database (last-write-wins).

---

### User Story 3 - Stable CSV Column Schema (Priority: P2)

Platform engineers and downstream automation depend on a predictable set of columns in the CSV output. The column names must match the flattened field names from the Mist API `getOrgInventory` response. Adding or removing columns without documentation breaks integrations.

**Why this priority**: Schema stability prevents breakage in downstream tooling but is secondary to basic export correctness and upsert safety.

**Independent Test**: Can be tested by asserting that a mocked API response with known fields produces a CSV with exactly those field names as column headers.

**Acceptance Scenarios**:

1. **Given** a representative API response with fields `[id, mac, serial, model, type, site_id, org_id, name, sku, hw_rev, created_time, modified_time]`, **When** the export completes, **Then** the CSV header row contains all of these fields (order may vary based on sort).
2. **Given** a device record with nested fields, **When** the record is flattened, **Then** nested keys are represented as dot-separated column names (e.g., `config_status.config_pushed`).

---

### User Story 4 - Progress Reporting via WebSocket Emitter (Priority: P3)

When MistHelper runs with the web UI active, Menu 12 emits progress events via `PROGRESS_EMITTER` so the web portal can show real-time status. The emitter must receive `emit_progress_start` before the API call and `emit_progress_complete` after, with accurate timing and step counts.

**Why this priority**: Progress reporting is a UX enhancement -- the export works correctly without it, but the web UI experience degrades.

**Independent Test**: Can be tested by mocking `PROGRESS_EMITTER` and verifying the correct method calls and arguments.

**Acceptance Scenarios**:

1. **Given** `PROGRESS_EMITTER` is set, **When** Menu 12 runs, **Then** `emit_progress_start("12", "inventory", 1)` is called before the API fetch.
2. **Given** `PROGRESS_EMITTER` is set and the export takes 3.5 seconds, **When** Menu 12 completes, **Then** `emit_progress_complete("12", "inventory", 1, 1, False, elapsed)` is called with `elapsed` approximately equal to 3.5.
3. **Given** `PROGRESS_EMITTER` is None, **When** Menu 12 runs, **Then** no progress methods are called and no exception occurs.

---

### Edge Cases

- What happens when the API returns HTTP 429 (rate limited)? APIDataFetcher retries with exponential backoff -- verify retry behavior is triggered.
- What happens when the API returns HTTP 500+ (server error)? APIDataFetcher retries up to `API_REQUEST_MAX_RETRIES` -- verify failure after exhausting retries raises an exception.
- What happens when the API returns a malformed response (missing `data` key)? APIDataFetcher attempts data recovery -- verify recovery path or clean failure.
- What happens when a device record is missing the `id` field? The SQLite upsert must handle this gracefully (skip or raise, not corrupt the table).
- What happens when the `data/` directory does not exist or is not writable? The system should fail with a clear error message, not a cryptic traceback.

## Requirements

### Functional Requirements

- **FR-001**: `OrgInventoryExporter.inventory()` MUST instantiate `APIDataFetcher` with `api_call=mistapi.api.v1.orgs.inventory.getOrgInventory`, `filename="OrgInventory.csv"`, `sort_key="model"`, and `limit=1000`.
- **FR-002**: The export pipeline MUST pass `api_function_name="getOrgInventory"` to the DataExporter so the correct PK strategy is resolved for SQLite writes.
- **FR-003**: Repeated exports of the same dataset MUST NOT create duplicate rows in SQLite. The upsert uses `INSERT OR REPLACE` keyed on `["id"]`.
- **FR-004**: The SQLite table MUST have indexes on `[org_id, site_id, mac, serial, model, type]` as defined in the PK strategy.
- **FR-005**: Unit tests MUST exist in `tests/unit/` covering `OrgInventoryExporter.inventory()` with mocked `APIDataFetcher`.
- **FR-006**: Integration tests MUST exist in `tests/integration/` verifying SQLite upsert idempotency against a temporary database.
- **FR-007**: All new tests MUST mock API calls (no live network calls) and MUST pass in CI.

### Key Entities

- **Device**: Represents a physical network device (AP, switch, gateway) in the Mist organization inventory. Key attributes: `id` (UUID), `mac`, `serial`, `model`, `type`, `site_id`, `org_id`, `name`, `sku`, `hw_rev`, `created_time`, `modified_time`.
- **OrgInventory Table**: SQLite table keyed by device `id`, containing all flattened device attributes. Subject to `INSERT OR REPLACE` upsert semantics.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Unit tests for `OrgInventoryExporter.inventory()` achieve 100% branch coverage of the method (all code paths: emitter present, emitter absent, successful export, empty result).
- **SC-002**: Integration test demonstrates upsert idempotency: two consecutive exports of 10 devices result in exactly 10 rows in SQLite.
- **SC-003**: Integration test demonstrates field update: modifying one device's attributes between exports results in the updated values in SQLite with no row count change.
- **SC-004**: All CI quality gates pass: ruff (lint), mypy (types), pytest (tests), bandit (security), pip-audit (dependencies).
- **SC-005**: CSV column schema test validates that a known API response fixture produces a deterministic set of column headers.

## Required API Function Name (SQL Relevant)

- **Canonical name**: `getOrgInventory`
- **PK strategy**: Already defined in `ENDPOINT_PRIMARY_KEY_STRATEGIES`:
  ```python
  "getOrgInventory": {
      "type": "natural_pk",
      "primary_key": ["id"],
      "indexes": ["org_id", "site_id", "mac", "serial", "model", "type"],
      "unique_constraints": [],
      "description": "Organization device inventory with stable UUID identifiers",
  }
  ```
- **Status**: Correctly defined. No changes needed.

## Recommended Primary Key Strategy

- **Recommended**: `natural_pk`
- **Primary Key**: `["id"]` (API-provided device UUID)
- **Indexes**: `["org_id", "site_id", "mac", "serial", "model", "type"]`
- **Rationale**: Devices expose stable UUIDs from the Mist API. Using the API-provided UUID as the natural primary key ensures deterministic upserts and straightforward joins. This is not time-series data, so composite keys are unnecessary. Auto-increment with unique is inappropriate because device identity is business-provided.
- **Status**: Already correctly configured. No changes needed.

## Test Plan Outline

### Unit Tests (`tests/unit/test_menu_12_org_inventory.py`)

1. **test_inventory_creates_api_data_fetcher_with_correct_params**: Mock `APIDataFetcher` class, call `OrgInventoryExporter.inventory()`, assert constructor receives correct `title`, `api_call`, `filename`, `sort_key`, `limit`.
2. **test_inventory_calls_execute**: Mock `APIDataFetcher`, call `inventory()`, assert `.execute()` was called exactly once.
3. **test_inventory_emits_progress_start_when_emitter_set**: Set `PROGRESS_EMITTER` to a mock, call `inventory()`, verify `emit_progress_start("12", "inventory", 1)`.
4. **test_inventory_emits_progress_complete_when_emitter_set**: Set `PROGRESS_EMITTER` to a mock, call `inventory()`, verify `emit_progress_complete` called with correct arguments.
5. **test_inventory_skips_progress_when_emitter_none**: Set `PROGRESS_EMITTER = None`, call `inventory()`, verify no progress-related calls and no exception.

### Integration Tests (`tests/integration/test_menu_12_sqlite_upsert.py`)

**Mock boundary**: Integration tests bypass `APIDataFetcher` and test the `DataExporter`/SQLite layer directly with device fixtures, using `api_function_name="getOrgInventory"`. This avoids coupling to `APIDataFetcher` internals while still validating that the PK strategy resolves correctly for Menu 12's data.

1. **test_upsert_idempotency**: Inject 10 device fixtures into `DataExporter.write_with_format_selection()` with `api_function_name="getOrgInventory"` twice, assert SQLite table has exactly 10 rows after both runs.
2. **test_upsert_updates_changed_fields**: Inject 10 device fixtures, then inject the same 10 with one device's `model` field changed, assert row count is 10 and the modified device has the new `model` value.
3. **test_indexes_created**: After export, query `sqlite_master` to verify indexes exist on `org_id`, `site_id`, `mac`, `serial`, `model`, `type`.
4. **test_csv_schema_matches_api_fields**: Inject known device fixtures, export to CSV, read CSV headers, assert expected field set.

## Constraints

- Do NOT change the API endpoint or PK strategy (already correct)
- Do NOT refactor `APIDataFetcher` (separate concern)
- Do NOT change other menu operations
- Python 3.13+, mistapi 0.59+
- Tests must work in CI (no live API calls -- mock everything)
- Follow project conventions: max 5 params per function, max 25 lines per function, class-based design, ASCII-only logging

## Assumptions

- The `getOrgInventory` API response schema is stable and returns a flat-ish JSON structure with device attributes at the top level (some nested fields may exist for config status).
- The `APIDataFetcher.execute()` method correctly handles pagination via `mistapi.get_all()` -- this is shared infrastructure and not in scope for this audit.
- The `DataExporter` correctly resolves `api_function_name` to the PK strategy -- this is shared infrastructure and tested separately.
- The `PROGRESS_EMITTER` global variable is either a valid emitter object or `None` -- there is no third state.
