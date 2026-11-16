# Tasks: Export Log Disclosure

## Phase 1: Setup

- [x] T001 Resolve the routed feature directory and ownership in `plan.md`. (delivered: plan.md)

## Phase 2: Foundational

- [x] T002 Record the inventory source hold in `spec.md`. (delivered: spec.md)

## Phase 3: User Story 1 - Export without disclosure

**Goal**: Preserve CSV values without logging them.
**Independent Test**: Compare synthetic CSV output with DEBUG logs.

- [x] T003 [US1] Add CSV marker and carriage-return tests in `tests/unit/export/test_data_exporter.py`. (delivered: tests/unit/export/test_data_exporter.py)
- [x] T004 [US1] Replace row-value logs with counts in `src/operations/exporting/export/data_exporter.py`. (delivered: src/operations/exporting/export/data_exporter.py)
- [ ] T005 [US1] Repair device, table, and address logs in `src/operations/exporting/export/org_inventory_exporter.py` after issue #4762 releases the file.
- [ ] T006 [US1] Add inventory output and log tests in `tests/unit/test_org_inventory_exporter_helpers.py` after T005 is available.

## Phase 4: User Story 2 - Diagnose export progress

**Goal**: Retain count and failure diagnostics.
**Independent Test**: Capture successful and failed CSV export logs.

- [x] T007 [US2] Verify aggregate counts and write failures in `tests/unit/export/test_data_exporter.py`. (delivered: tests/unit/export/test_data_exporter.py)

## Phase 5: Polish

- [x] T008 Add a partial repair release note in `changelog.d/issue-4775-csv-log-disclosure.md`. (delivered: changelog.d/issue-4775-csv-log-disclosure.md)
- [x] T009 Run focused tests and an isolated container smoke in `design/quickstart.md`. (delivered: design/quickstart.md)
- [ ] T010 Run an authenticated staging smoke when an authorized token and verified staging organization are available in `design/quickstart.md`.

## Dependencies and Execution Order

T001 and T002 precede all changes. T003 precedes T004 and T007.
T005 and T006 require release of the inventory source hold.
T008 and T009 follow the unblocked CSV repair. T010 requires credentials.

## Parallel Opportunities

The inventory work cannot run in parallel while issue #4762 holds its source.

## Implementation Strategy

Deliver the CSV repair as an incremental change. Keep issue #4775 open until
the inventory work and authenticated staging smoke are complete.
