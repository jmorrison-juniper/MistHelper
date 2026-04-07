# Plan

## Goal
Bring menu item 13 (Export device statistics) from current state (SQL-compliant but missing unit tests) to done: fully specified, planned, and ready for safe implementation and testing.

## Phases
1. Specification & design (complete)
   - Produce spec.md (this file) and place under specs/025-audit-menu-13-org-device-stats.
   - Define PK strategy and API metadata.
2. Preparation (pre-implementation)
   - Create task list and test skeletons.
   - Prepare fixtures and SQL verification scripts.
   - Produce change proposal for ENDPOINT_PRIMARY_KEY_STRATEGIES entry for this endpoint.
3. Implementation (NOT in scope for this output)
   - Implement code changes: exporter wiring, call to write_with_format_selection, add PK strategy into runtime config.
4. Testing
   - Run unit tests, integration tests, and SQL verification tests; iterate until green.
5. Release & documentation
   - Update README/menu index, add changelog entry, and update spec directory with final artifacts.

## Milestones
- M1: Spec and plan completed (this milestone).
- M2: Tasks and test skeletons created, fixtures prepared.
- M3: PK strategy approved and added to configuration (proposal prepared in Pre-Implementation tasks).
- M4: All unit and integration tests created and passing (post-implementation).
- M5: Docs updated and PR ready for review (post-implementation).

## Dependencies
- APIDataFetcher and DataExporter utilities must remain available.
- ENDPOINT_PRIMARY_KEY_STRATEGIES must be extended (dependency for implementation).
- Access to test SQLite environment and ability to run test suite.

## Risks & mitigations
- Ambiguity in metric identifier (name vs id): use metric_name if stable; otherwise include metric_id in composite key to be safe.
- Large time-series volumes: rely on existing exporter pagination and rate-limit behavior in APIDataFetcher.

## Deliverables for implement-phase handoff
- PK strategy proposal payload.
- Unit test skeletons and fixtures.
- SQL verification scripts and expected assertions.
- README/menu update diff.

