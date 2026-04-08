# Implementation Plan: Audit Menu 12 - Organization Inventory Export

**Branch**: `feat/73-audit-menu-12-org-inventory` | **Date**: 2026-04-08 | **Spec**: [spec.md](../../024-audit-menu-12-org-inventory/spec.md)
**Input**: Feature specification from `/specs/024-audit-menu-12-org-inventory/spec.md`

## Summary

Menu 12 (`OrgInventoryExporter.inventory()`) is **already fully implemented** and uses
`APIDataFetcher` to call `getOrgInventory`, flatten results, and export to CSV or SQLite
via `DataExporter`. The PK strategy (`natural_pk` on `["id"]`) is defined. This plan
focuses exclusively on **adding test coverage** — no MistHelper.py modifications are needed.

Deliverables:
1. Unit tests for `OrgInventoryExporter.inventory()` (mock APIDataFetcher, verify params)
2. Unit tests for progress emitter integration (mock PROGRESS_EMITTER lifecycle)
3. Integration tests for SQLite upsert idempotency (DataExporter + SQLiteDatabaseWriter)
4. Integration test for CSV schema stability

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: mistapi 0.59+, pytest, sqlite3 (stdlib), csv (stdlib)
**Storage**: SQLite (`data/mist_data.db`) + CSV (`data/OrgInventory.csv`)
**Testing**: pytest with monkeypatch + unittest.mock; tmp_path fixture for isolation
**Target Platform**: Windows 11 (dev), Linux container (CI/prod)
**Project Type**: CLI tool with dual-output data pipeline
**Performance Goals**: Tests complete in < 5 seconds (no real API calls)
**Constraints**: Tests must run offline, no API credentials, no side effects on `data/`
**Scale/Scope**: 2 test files, ~10 test functions total

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
| - | - | - |
| I. Five-Item Rule | PASS | No new classes/functions in MistHelper.py; test files follow flat structure |
| II. Class-Based Architecture | PASS | No new production code; tests use standard pytest function style |
| III. Safety-First | N/A | No input handling added; audit-only scope |
| IV. Full Deployment Pipeline | PASS | No MistHelper.py changes → no deployment needed (tests-only PR) |
| V. Observability & Logging | PASS | Tests verify logging.info calls exist; no new log statements |
| Security: Fix Over Suppress | PASS | No security suppressions needed; parameterized queries already used |
| MistHelper.py Hot File | PASS | No modifications to MistHelper.py; only test files created |

**Multi-Agent Safety**: This PR touches only `tests/unit/test_menu_12_*.py` and
`tests/integration/test_menu_12_*.py`. No overlap with feat/72 (SSID consolidation)
which modifies `src/ssid_consolidation/` files.

## Project Structure

### Documentation (this feature)

```text
specs/024-audit-menu-12-org-inventory/
├── spec.md              # Feature specification (complete)
├── plan.md              # Existing plan (will be updated)
├── tasks.md             # Existing tasks (will be updated)
└── checklists/          # Review checklists

specs/feat/73-audit-menu-12-org-inventory/
├── plan.md              # This file (implementation plan)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
└── quickstart.md        # Phase 1 output
```

### Source Code (repository root)

```text
tests/
├── conftest.py                          # Shared fixtures (existing)
├── unit/
│   ├── test_pk_strategies.py            # Existing PK validation
│   ├── test_exports.py                  # Existing export tests (menu 63-65)
│   └── test_menu_12_inventory.py        # NEW: unit tests for Menu 12
└── integration/
    └── test_menu_12_sqlite_upsert.py    # NEW: SQLite upsert + CSV schema tests
```

**Structure Decision**: Tests follow the existing `tests/unit/` and `tests/integration/`
layout. No new directories needed. File naming uses `test_menu_12_*` prefix for discoverability.

---

## Phase 0: Research

### R1: MistHelper.py Import Side Effects

**Decision**: Use `monkeypatch` to mock global state rather than importing
MistHelper.py directly in unit tests. The existing `tests/conftest.py` already
handles forced module loading with `SystemExit` suppression.

**Rationale**: Direct import of MistHelper.py triggers side effects (logging setup,
dotenv loading, global variable initialization). The existing conftest pattern
(`importlib.util.spec_from_file_location`) handles this but is fragile. For unit
tests that only need to verify method behavior, monkeypatching specific attributes
on the already-imported module is safer.

**Alternatives Considered**: Separate fixture module with duplicated classes — rejected
because it drifts from production code. Import-time patching via conftest — chosen,
already proven in test_exports.py.

### R2: APIDataFetcher Mocking Strategy

**Decision**: Mock `APIDataFetcher.__init__` and `APIDataFetcher.execute` to verify
that `OrgInventoryExporter.inventory()` passes the correct parameters without
executing real API calls.

**Rationale**: The unit test goal is to verify the **wiring** — that the correct
API function, filename, sort key, and limit are passed to APIDataFetcher. We do not
need to test APIDataFetcher internals (that's APIDataFetcher's own test scope).

**Pattern** (from test_exports.py):
```python
monkeypatch.setattr(MistHelper.ConfigUtils, "get_cached_or_prompted_org_id", lambda: "org1")
# Mock APIDataFetcher to capture init args
```

### R3: SQLite Integration Test Strategy

**Decision**: Bypass APIDataFetcher entirely and test `DataExporter.write_with_format_selection()`
directly with fixture data, passing `api_function_name="getOrgInventory"` to trigger
the correct PK strategy resolution.

**Rationale**: Integration tests should validate that the PK strategy resolves correctly,
that `INSERT OR REPLACE` works with natural keys, and that indexes are created. Coupling
to APIDataFetcher would make tests brittle to API-layer changes.

**Pattern**: Create fixture data as `list[dict]`, write to SQLite via DataExporter,
read back with raw `sqlite3`, assert row counts and field values.

### R4: PROGRESS_EMITTER Mocking

**Decision**: Set `MistHelper.PROGRESS_EMITTER` to a `MagicMock()` object before
calling `inventory()`, then assert `emit_progress_start` and `emit_progress_complete`
were called with correct menu ID ("12") and operation name ("inventory").

**Rationale**: The progress emitter is a global that defaults to `None`. When set,
the inventory method calls `emit_progress_start` before and `emit_progress_complete`
after the export. This is the web portal's feedback mechanism and must be verified.

### R5: Fixture Data - Representative Device Records

**Decision**: Use a static fixture of 3 device records that cover:
- Standard AP record (all common fields populated)
- Switch record (different `type` field)
- Device with missing optional fields (to test None handling)

**Rationale**: Covers the primary field variations without over-engineering. The
`getOrgInventory` API returns flat records with minimal nesting, so 3 records
is sufficient.

**Representative fields**: `id`, `mac`, `serial`, `model`, `type`, `site_id`,
`org_id`, `name`, `sku`, `hw_rev`, `created_time`, `modified_time`, `magic`.

---

## Phase 1: Design & Data Model

### Data Model

**Entity: OrgInventory Device Record**

| Field | Type | Required | Source |
| - | - | - | - |
| id | str (UUID) | Yes | API - device UUID, PK |
| mac | str | Yes | API - device MAC address |
| serial | str | Yes | API - serial number |
| model | str | Yes | API - device model (e.g., AP43) |
| type | str | Yes | API - device type (ap/switch/gateway) |
| site_id | str (UUID) | No | API - assigned site UUID |
| org_id | str (UUID) | Yes | API - organization UUID |
| name | str | No | API - device hostname |
| sku | str | No | API - product SKU |
| hw_rev | str | No | API - hardware revision |
| created_time | int | No | API - epoch timestamp |
| modified_time | int | No | API - epoch timestamp |
| magic | str | No | API - claim code |

**PK Strategy** (already defined in `ENDPOINT_PRIMARY_KEY_STRATEGIES`):
```python
"getOrgInventory": {
    "type": "natural_pk",
    "primary_key": ["id"],
    "indexes": ["org_id", "site_id", "mac", "serial", "model", "type"],
}
```

**Upsert Behavior**: `INSERT OR REPLACE` keyed on `id`. Repeated inserts with same
`id` overwrite the existing row. This is correct for inventory (stable entity, not
time-series).

### Test Fixtures

```python
DEVICE_AP = {
    "id": "d1000000-0000-0000-0000-000000000001",
    "mac": "aabbccddeef1",
    "serial": "SN-AP-001",
    "model": "AP43",
    "type": "ap",
    "site_id": "s1000000-0000-0000-0000-000000000001",
    "org_id": "o1000000-0000-0000-0000-000000000001",
    "name": "Lobby-AP-1",
    "sku": "AP43-US",
    "hw_rev": "A1",
    "created_time": 1700000000,
    "modified_time": 1700100000,
}

DEVICE_SWITCH = {
    "id": "d2000000-0000-0000-0000-000000000002",
    "mac": "aabbccddeef2",
    "serial": "SN-SW-001",
    "model": "EX4400",
    "type": "switch",
    "site_id": "s1000000-0000-0000-0000-000000000001",
    "org_id": "o1000000-0000-0000-0000-000000000001",
    "name": "Core-SW-1",
}

DEVICE_MISSING_OPTIONAL = {
    "id": "d3000000-0000-0000-0000-000000000003",
    "mac": "aabbccddeef3",
    "serial": "SN-GW-001",
    "model": "SRX320",
    "type": "gateway",
    "org_id": "o1000000-0000-0000-0000-000000000001",
}
```

### Contracts

**No external interfaces are added by this feature.** The existing contracts are:

1. **APIDataFetcher contract**: Accepts `api_call`, `filename`, `sort_key`, `limit`,
   `**kwargs`. Calls `execute()` to run the full pipeline.
2. **DataExporter contract**: `write_with_format_selection(data, filename, api_function_name=...)`
   routes to CSV or SQLite based on `OUTPUT_FORMAT`.
3. **Menu 12 contract**: `OrgInventoryExporter.inventory()` is a no-arg static method
   that uses globals (`apisession`, `PROGRESS_EMITTER`).

### Test Architecture

```text
Unit Tests (test_menu_12_inventory.py)
├── test_inventory_calls_api_data_fetcher_with_correct_params
├── test_inventory_passes_correct_limit
├── test_inventory_uses_model_as_sort_key
├── test_inventory_emits_progress_start_and_complete
└── test_inventory_handles_no_emitter_gracefully

Integration Tests (test_menu_12_sqlite_upsert.py)
├── test_sqlite_upsert_no_duplicates_on_repeated_insert
├── test_sqlite_upsert_updates_changed_fields
├── test_sqlite_indexes_created_for_org_inventory
├── test_csv_schema_contains_expected_columns
└── test_csv_roundtrip_matches_source_data
```

### Quickstart

```bash
# Run only Menu 12 tests
cd <worktree-root>
pytest tests/unit/test_menu_12_inventory.py tests/integration/test_menu_12_sqlite_upsert.py -v

# Run all tests to verify no regressions
pytest tests/ -v --timeout=30
```

---

## Constitution Re-Check (Post-Design)

| Principle | Status | Notes |
| - | - | - |
| I. Five-Item Rule | PASS | Each test file has ≤5 test functions. No new production classes. |
| II. Class-Based Architecture | PASS | Tests use pytest function style (no new wrapper classes). |
| III. Safety-First | N/A | Test-only scope; no production input handling. |
| IV. Full Deployment Pipeline | PASS | No MistHelper.py changes → tests-only PR, no container rebuild. |
| V. Observability & Logging | PASS | Tests verify existing logging calls; no new log statements. |
| Multi-Agent Hot File | PASS | Zero modifications to MistHelper.py. |

## Complexity Tracking

No violations to justify. This plan adds only test files within the existing project structure.
