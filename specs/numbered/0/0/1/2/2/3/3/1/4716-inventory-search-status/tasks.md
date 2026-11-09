# Tasks: Inventory search status

## Phase 1: Setup

- [x] T001 Verify the assigned base and reservation for `src/operations/exporting/export/org_inventory_search_exporter.py`.

## Phase 2: Foundation

- [x] T002 Restore missing test dependencies offline and create the session `run_offline_checks.py` safety runner.

## Phase 3: Request failures

Independent criterion: invalid initial statuses produce an error and no output.

- [x] T003 [US1] Add real-shaped status, transport, boundary, filter, empty, and cancellation tests in `tests/unit/export/test_org_inventory_search_exporter.py`.
- [x] T004 [US1] Accept only integer statuses from 200 through 299, excluding booleans, in `src/operations/exporting/export/org_inventory_search_exporter.py`.

## Phase 4: Writer failures

Independent criterion: false writer results produce no persistence or success messages.

- [x] T005 [US2] Add failed-writer and successful-output assertions in `tests/unit/export/test_org_inventory_search_exporter.py`.
- [x] T006 [US2] Check the writer result in `src/operations/exporting/export/org_inventory_search_exporter.py`.

## Phase 5: Validation and preservation

- [x] T007 Add `changelog.d/issue-4716-inventory-search-status.md`.
- [x] T008 Prove the regressions fail on the original source and pass on the repair with the session safety runner.
- [x] T009 Run applicable local checks and record exact results in the session files.
- [x] T010 Review `spec.md`, `plan.md`, and `tasks.md`, then preserve the local commit and session evidence.

## Dependencies

T001 precedes T002. T002 precedes both user stories.
T003 precedes T004. T005 precedes T006.
T004 and T006 precede T008.
T007 and T008 precede T009. T009 precedes T010.

## Parallel Opportunities

The two failure stories are logically independent.
Their source and test files overlap, so implement them serially.
Independent local static checks can run in parallel.

## Implementation Strategy

Implement both focused failure cases in one local candidate.
Do not publish the candidate or change shared infrastructure.

## Results

The repaired exporter passed 39 tests with 100 percent statement coverage.
The original source failed 26 regression cases and passed 13 compatibility cases.
The related suite passed 177 tests.
One pull-request-only changelog guard skipped because this local run has no pull request event.
Every test process recorded zero socket and DNS attempts.
The focused test-quality check examined the changed module with `--include-mist-api` and reported zero new findings.
All recorded static and documentation checks passed.
