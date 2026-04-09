# Plan — spec-025: Audit Menu 13

## Goal

Add comprehensive unit and integration tests for Menu 13 (Organization Device
Stats Export). No production code changes. Follow the established spec-024 pattern.

## Phases

### Phase 1: Fixtures

Create `tests/fixtures/device_stats.py` with:
- `STAT_AP`: AP device stat record
- `STAT_SWITCH`: Switch device stat record
- `STAT_GATEWAY`: Gateway device stat record
- `STAT_MINIMAL`: Minimal record (missing optional fields)
- `ALL_STATS`: Combined list of all fixture records
- `make_device_stats_fixtures(count)`: Generator for bulk testing

### Phase 2: Unit Tests

Create `tests/unit/test_menu_13_device_stats.py` with 4 test classes:
- `TestDeviceStatsAPIDataFetcherWiring` (3 tests): FR-001, US-001
- `TestDeviceStatsProgressEmitter` (2 tests): FR-005, US-004
- `TestDeviceStatsFastMode` (4 tests): FR-006, US-005
- `TestDeviceStatsDynamicLookback` (1 test): FR-007, US-006

### Phase 3: Integration Tests

Create `tests/integration/test_menu_13_sqlite_upsert.py` with 2 test classes:
- `TestSQLiteUpsertIdempotency` (4 tests): FR-003, FR-004, US-002
- `TestCSVSchemaStability` (2 tests): FR-002, US-003

### Phase 4: Quality Gates

1. **Ruff format** all three new files:
   ```
   ruff format tests/fixtures/device_stats.py tests/unit/test_menu_13_device_stats.py tests/integration/test_menu_13_sqlite_upsert.py
   ```
2. Run all tests: `python -m pytest tests/unit/test_menu_13_device_stats.py tests/integration/test_menu_13_sqlite_upsert.py -v`
3. Verify 16 tests pass

### Phase 5: Commit and PR

1. `git add tests/ specs/`
2. Commit with conventional commit format referencing #88
3. Push and create PR with `auto-merge` label

## Dependencies

- `APIDataFetcher` and `DataExporter` classes (used in monkeypatched tests)
- `PROGRESS_EMITTER` global (mocked in unit tests)
- `TimeUtils.get_dynamic_lookback_hours` and `TimeUtils.log_dynamic_lookback` (mocked)
- `CSV_FRESHNESS_MINUTES` global (monkeypatched for fast mode tests)
- `ENDPOINT_PRIMARY_KEY_STRATEGIES` entry for `listOrgDevicesStats` (used by integration tests)

## Risks

- None significant — test-only audit with established pattern
