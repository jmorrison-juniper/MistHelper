# Spec-025: Audit Menu 13 — Organization Device Stats Export

## Problem / Goal

Menu 13 (Organization Device Stats Export) functions correctly at runtime but lacks
unit and integration tests. This audit adds comprehensive test coverage following
the same pattern established by spec-024 (Menu 12).

**Non-goals**: No changes to MistHelper.py production code.

## Current Implementation

- **Class**: `OrgDeviceStatsExporter` (MistHelper.py ~line 12295)
- **Method**: `device_stats(fast=False)` — static method (~line 12304)
- **API**: `mistapi.api.v1.orgs.stats.listOrgDevicesStats`
- **Output file**: `OrgDeviceStats.csv`
- **Sort key**: `"type"`
- **API params**: `type="all"`, `duration="{hours}h"`, `limit=1000`
- **PK Strategy**: `composite_pk` on `["device_id", "timestamp"]`
- **Indexes**: `["device_id", "timestamp", "org_id", "site_id", "type"]`
- **Progress emitter**: `emit_progress_start("13", "device_stats", 1)` / `emit_progress_complete("13", ...)`
- **Fast mode**: CSV caching with `CSV_FRESHNESS_MINUTES` freshness check
- **Dynamic lookback**: `TimeUtils.get_dynamic_lookback_hours(24, 1)`

## Functional Requirements

| ID | Requirement |
| - | - |
| FR-001 | APIDataFetcher receives correct params (api_call, filename, sort_key, type, duration, limit) |
| FR-002 | Dual output (CSV + SQLite) via DataExporter.write_with_format_selection |
| FR-003 | SQLite upsert idempotency (composite PK on device_id, timestamp) |
| FR-004 | Indexes created on device_id, timestamp, org_id, site_id, type |
| FR-005 | Progress emitter lifecycle (start + complete with menu_id="13") |
| FR-006 | Fast mode cache-hit skips API call when CSV is fresh |
| FR-007 | Dynamic lookback hours from TimeUtils passed to duration param |

## User Stories

| ID | Story |
| - | - |
| US-001 | NOC engineer exports device stats for all device types (AP, switch, gateway) |
| US-002 | Repeated export doesn't create SQLite duplicates (upsert idempotency) |
| US-003 | CSV schema is stable with expected column headers |
| US-004 | Progress tracking emits start/complete events for web UI |
| US-005 | Fast mode cache-hit/miss/no-file behavior works correctly |
| US-006 | Dynamic lookback value used in API duration parameter |

## Test Plan

Follow spec-024 pattern with three test files:

1. **tests/fixtures/device_stats.py** — Representative device stats payloads (AP, switch, gateway, minimal)
2. **tests/unit/test_menu_13_device_stats.py** — APIDataFetcher wiring, progress emitter, fast mode, lookback
3. **tests/integration/test_menu_13_sqlite_upsert.py** — SQLite upsert idempotency, CSV schema stability, index creation

### Unit Tests (10 tests)

| Test | Covers |
| - | - |
| test_creates_fetcher_with_correct_params | FR-001 |
| test_calls_execute_exactly_once | US-001 |
| test_handles_empty_api_response | US-001 |
| test_emits_start_and_complete | FR-005, US-004 |
| test_handles_no_emitter_gracefully | US-004 |
| test_fast_mode_cache_hit_skips_fetch | FR-006, US-005 |
| test_fast_mode_cache_miss_stale_file | FR-006, US-005 |
| test_fast_mode_cache_miss_no_file | FR-006, US-005 |
| test_fast_mode_disabled_by_default | US-005 |
| test_dynamic_lookback_value_passed_to_fetcher | FR-007, US-006 |

### Integration Tests (6 tests)

| Test | Covers |
| - | - |
| test_no_duplicates_on_repeated_insert | FR-003, US-002 |
| test_updates_changed_fields | FR-003, US-002 |
| test_composite_key_time_series_granularity | FR-003 |
| test_indexes_created | FR-004 |
| test_csv_schema_contains_expected_columns | US-003 |
| test_csv_roundtrip_matches_source_data | US-003 |

## Acceptance Criteria

1. All 16 tests pass with pytest
2. Ruff formatting passes on all new files
3. No production code changes
4. Fixtures cover all three device types plus minimal record
5. SQLite upsert is idempotent (no duplicates on repeated insert)
6. CSV column schema includes device_id, mac, model, type, org_id, timestamp

## Purpose
Provide a repeatable operation to export device statistics (time-series metrics) from the Mist API into CSV and SQL backends using the existing exporter plumbing so NOC engineers can analyze device behavior offline.

## Stakeholders
- NOC engineers (primary users)
- Platform engineers (maintainers of exporter and DB schemas)
- QA (test and verification)

## Required API function
- OrgDeviceStatsExporter.device_stats (function_ref)

## Acceptance criteria
1. The exporter calls OrgDeviceStatsExporter.device_stats and passes responses through existing flatten/normalize helpers.
2. Dual-output support: CSV and SQLite (via DataExporter.write_with_format_selection) must be available.
3. SQL behavior: upsert semantics must prevent duplicate rows and preserve latest sample values:
   - For composite_pk endpoints, use INSERT OR REPLACE keyed by (device_id, metric_id, timestamp) to allow time-series granularity.
   - For natural PK endpoints (if any), use INSERT OR REPLACE on the UUID.
   - For aggregated summaries, use auto_increment_with_unique with a generated misthelper_internal_id and a uniqueness constraint if needed.
4. Indexes exists to support typical queries (device_id, timestamp).  
5. No regressions in existing exporters; exporter remains idempotent and rate-limited per APIDataFetcher.
6. Unit tests present and passing for all new logic; integration test validates end-to-end export to SQLite with upsert verification.

## Recommended primary-key strategy and rationale
- Recommended: composite_pk
  - Reason: device statistics are time-series. Composite key of [device_id, metric_name (or metric_id), timestamp] prevents accidental aggregation collisions and supports efficient upserts of individual samples.
  - Suggested primary_key fields: ["device_id","metric_name","timestamp"]
  - Suggested indexes: (device_id, timestamp), (metric_name, timestamp)

## Test plan outline
1. Unit tests (missing today):
   - Mock OrgDeviceStatsExporter.device_stats to return representative payloads.
   - Validate JSON flattening, field types (timestamps normalized), and CSV rows generated.
   - Verify that DataExporter.write_with_format_selection is called with expected parameters (CSV and SQL paths).
2. Integration tests:
   - Run the exporter against a local test SQLite DB via APIDataFetcher mocks and fixture responses.
   - Verify row counts, sample values and indexes.
3. SQL verification steps:
   - Insert fixture rows twice; confirm row count does not duplicate when keys equal (upsert happened).
   - Insert later-timestamped sample for same device+metric; confirm row replaced or new row inserted according to composite key semantics.
4. Edge cases:
   - Missing metric_name or timestamp fields (assert and normalize or drop depending on contract).
   - Large payloads and rate-limit handling (simulate paginated API responses).

