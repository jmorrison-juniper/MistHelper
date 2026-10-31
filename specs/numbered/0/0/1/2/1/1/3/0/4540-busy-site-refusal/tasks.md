# Tasks: Busy-site refusal

**Input**: [spec.md](spec.md), [plan.md](plan.md), and the supporting records under `design/`.

## Phase 1: Setup

- [x] T001 Confirm source ownership and record the scoped handoff in design/research.md.

## Phase 2: Foundation

- [x] T002 Resolve numeric route #4540 and record the unchanged response contract in design/contracts/refusal.md.

## Phase 3: User Story 1 - Read a busy-site refusal

**Goal**: Show the refusal and permitted owning-operation link without a browser page error.

**Independent test**: Return synthetic 409 responses for permitted, absent, and unsafe owning-operation addresses.

- [x] T003 [US1] Add synthetic browser cases and preserve the full-viewport wait (delivered: tests/e2e/upgrade_portal/journeys/test_upj_multisite_journeys.py).
- [x] T004 [US1] Prove the browser regression fails before the repair in src/interfaces/portals/upgrade_portal/app/assets/static/js/portal.js. The permitted-link case failed with an empty refusal region.
- [x] T005 [US1] Correct only the busy-refusal declaration scope (delivered: src/interfaces/portals/upgrade_portal/app/assets/static/js/portal.js).

## Phase 4: Validation and Release Note

- [x] T006 [P] Add the operator-visible repair note (delivered: changelog.d/issue-4540-busy-site-refusal.md).
- [x] T007 Run focused browser cases and applicable gates from design/quickstart.md. Three browser cases passed, with zero leaked holds.
- [x] T008 Analyze requirement coverage and record results in tasks.md.

## Dependencies and Execution

T001 precedes T002. T002 precedes T003. T003 precedes T004. T004 precedes T005.
T006 can run with T003 through T005.
T007 requires T005 and T006. T008 requires T007.

## Implementation Strategy

Deliver User Story 1 as one bounded repair.
Keep all unrelated journey behavior and PR #4541 records unchanged.
Defer the optional commit hooks until validation completes.

## Requirement Coverage

| Requirements | Tasks | Evidence |
| - | - | - |
| FR-001, SC-001, SC-002 | T003, T004, T005, T007 | Exact message, permitted link, and no browser page errors |
| FR-002, SC-004 | T003, T005, T007 | Empty disabled confirmation and disabled start control |
| FR-003, SC-003 | T003, T005, T007 | Absent and unsafe addresses produce no link. Existing route contracts pass. |
| FR-004 | T003, T007 | Intercepted 409 responses and seeded pre-checks require no cloud writes |
| FR-005 | T003 | The full-viewport assertion uses the retrying `ratio=1` check |
| FR-006 | T001, T008 | The changed-file manifest excludes workflow, fixture, and parity records |

The analysis examined six functional requirements, four success criteria, and eight tasks.
Coverage is 100 percent, with no uncovered requirement or unresolved ambiguity.
The user excludes publishing, merge, and auto-merge.
Existing module and process-folder debt remains outside this scoped repair.
