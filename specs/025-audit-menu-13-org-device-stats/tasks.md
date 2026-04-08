# Tasks — spec-025: Audit Menu 13

## T001: Create fixture file

- [x] Create `tests/fixtures/device_stats.py`
- [x] Add STAT_AP, STAT_SWITCH, STAT_GATEWAY, STAT_MINIMAL constants
- [x] Add ALL_STATS list combining all fixtures
- [x] Add `make_device_stats_fixtures(count)` generator function
- **Covers**: US-001, US-002, US-003

## T002: Create unit test file

- [x] Create `tests/unit/test_menu_13_device_stats.py`
- [x] TestDeviceStatsAPIDataFetcherWiring (3 tests): FR-001, US-001
- [x] TestDeviceStatsProgressEmitter (2 tests): FR-005, US-004
- [x] TestDeviceStatsFastMode (4 tests): FR-006, US-005
- [x] TestDeviceStatsDynamicLookback (1 test): FR-007, US-006

## T003: Create integration test file

- [x] Create `tests/integration/test_menu_13_sqlite_upsert.py`
- [x] TestSQLiteUpsertIdempotency (4 tests): FR-003, FR-004, US-002
- [x] TestCSVSchemaStability (2 tests): FR-002, US-003

## T004: Update spec artifacts

- [x] Rewrite spec.md with full requirements and test plan
- [x] Rewrite plan.md with phased implementation plan
- [x] Rewrite tasks.md (this file) with actionable checklist
- [x] Create checklists/requirements.md

## T005: Quality gates

- [x] Run `ruff format` on all three test files
- [x] Run pytest — all 16 tests pass
- [x] Verify no production code changes

## T006: Commit and PR

- [ ] Stage all files: `git add tests/ specs/`
- [ ] Commit: `feat(tests): add Menu 13 device stats audit tests (spec-025)`
- [ ] Push to `feat/88-audit-menu-13-org-device-stats`
- [ ] Create PR linking to issue #88
- [ ] Add `auto-merge` label
