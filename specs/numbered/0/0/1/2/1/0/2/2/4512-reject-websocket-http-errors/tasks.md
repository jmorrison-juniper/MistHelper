# Tasks: Discovery HTTP errors

**Input**: [Specification](spec.md), [plan](plan.md), and supporting records under `design/`.

## Phase 1: Setup

- [x] T001 Prepare `.venv/` with `scripts/bootstrap_worktree.py` and inspect issue #4512. (delivered: scripts/bootstrap_worktree.py)

## Phase 2: Foundation

- [x] T002 Resolve the managed feature route and record response rules in `design/data-model.md`. (delivered: design/data-model.md)

## Phase 3: User Story 1 - Reject failed discovery data

**Goal**: Failed responses cannot populate normal caches.
**Independent Test**: Inject failed SDK responses with plausible device names.

- [x] T003 [US1] Add configuration and statistics HTTP-error regression tests. (delivered: tests/unit/websocket/test_service_ping_discovery.py)
- [x] T004 [US1] Reject failed statuses before data access. (delivered: src/mist/realtime/websocket/service_ping_discovery.py)

## Phase 4: User Story 2 - Preserve successful discovery

**Goal**: Keep successful extraction, sorting, and filtering unchanged.
**Independent Test**: Compare exact names from successful configuration and statistics.

- [x] T005 [US2] Update successful SDK response doubles and test empty success. (delivered: tests/unit/websocket/test_service_ping_discovery.py)

## Phase 5: Polish

- [x] T006 Add the release note. (delivered: changelog.d/issue-4512-reject-websocket-http-errors.md)
- [x] T007 Run focused gates and attach the read-only specification analysis as issue artifact 1. (delivered: plan.md)

## Dependencies & Execution Order

T001 precedes T002. T002 precedes both user stories.
T003 precedes T004. T005 can be designed independently, but shares the test file with T003.
T006 can run independently after T002. T007 follows both stories and T006.

## Parallel Opportunities

Run independent validation commands together. Do not edit the shared test file concurrently.
For either story, review supporting documentation while its tests run.

## Implementation Strategy

First prove the error-cache defect with failing tests. Then repair both boundaries.
Verify successful and partial-success behavior before the commit and pull request.
