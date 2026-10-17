# Tasks: Generated Operations control labels

**Input**: [plan.md](plan.md), [spec.md](spec.md), and the [label contract](design/contracts/labels.md).

## Phase 1: Setup

- [x] T001 Read #4059 and check ownership for `web_portal/static/js/operations.js`. (delivered: plan.md)
- [x] T002 Reproduce the existing expected failures in `tests/e2e/web_portal/test_operations_accessible_names.py`. (delivered: design/research.md)

## Phase 2: Foundation

- [x] T003 Record the bounded scope and label contract in `design/contracts/labels.md`. (delivered: design/contracts/labels.md)

## Phase 3: User Story 1 - Identify a generated parameter

- [x] T004 [US1] Expand the regression proof across menus and endpoint replacements. (delivered: tests/e2e/web_portal/test_operations_accessible_names.py)
- [x] T005 [US1] Associate labels with unchanged IDs. (delivered: web_portal/static/js/operations.js)
- [x] T006 [US1] Run focused browser and unit tests. (delivered: design/quickstart.md)

## Phase 4: Publication

- [x] T007 [P] Document #4059. (delivered: changelog.d/issue-4059-fix-generated-control-labels.md)
- [x] T008 Run relevant gates and record evidence. (delivered: design/analysis.md)

## Dependencies

T001 precedes T002 and T003. T003 precedes T004 and T005.
T004 and T005 precede T006. T006 precedes T008.
T007 is independent after the scope is fixed.

## Parallel Opportunities

The release-note fragment can be written while the focused tests run.

## Implementation Strategy

Deliver User Story 1 as one minimal bug repair.
Keep the existing field behavior and use the shared builder rather than per-control changes.
