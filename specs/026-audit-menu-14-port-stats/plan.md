# Plan

## Goal
Deliver a fully specified, tested, and documented port-level statistics export (menu_id=14) that supports SQL upsert semantics and has unit and integration tests in place.

## High-level phases
1. Specification finalization (this artifact)
   - Deliverables: spec.md in specs/026-audit-menu-14-port-stats
   - Exit criteria: sign-off on PK strategy and test plan
2. Design & preparation
   - Add an ENDPOINT_PRIMARY_KEY_STRATEGIES entry draft for this endpoint
   - Define schema/column mapping and indexes
   - Create test skeletons and CI job entries (no implementation yet)
   - Exit criteria: design doc + test skeletons created
3. Implementation (IMPLEMENT phase — stop before this)
   - Refactor OrgDeviceStatsExporter.device_port_stats to call DataExporter.write_with_format_selection
   - Implement composite PK upsert logic in database exporter layer
   - Add index creation and migrations (if required)
   - Implement unit and integration tests
   - Exit criteria: all tests pass locally and in CI
4. Verification & QA
   - Run full test suite, perform performance check for bulk inserts
   - Update README/CHANGELOG with version tag
   - Exit criteria: green CI and QA sign-off

## Milestones
- M1: spec.md committed to specs/026-audit-menu-14-port-stats (this deliverable)
- M2: PK strategy and schema drafted and reviewed
- M3: Test skeletons added to tests/ (unit + integration + sql)
- M4: Implementation merged with green CI

## Dependencies
- Access to DataExporter utilities and existing write_with_format_selection behavior
- Standard test harness/CI configuration (pytest and sqlite available)
- Endpoint mapping in ENDPOINT_PRIMARY_KEY_STRATEGIES (must be added prior to implementation)

## Risks & mitigations
- Risk: schema mismatch with existing exporter conventions. Mitigation: review existing endpoint PK patterns and reuse naming conventions.
- Risk: SQLite upsert semantics differ across versions. Mitigation: use `INSERT INTO ... ON CONFLICT (...) DO UPDATE` if SQLite >=3.24; fall back to `INSERT OR REPLACE` if needed and document consequences.

