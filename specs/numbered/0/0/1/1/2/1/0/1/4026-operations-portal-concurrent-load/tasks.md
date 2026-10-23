# Tasks: Concurrent operations portal access

**Input**: [Specification](spec.md), [plan](plan.md), and supporting records under `design/`.

## Phase 1: Setup

- [x] T001 Inspect current route ownership and managed feature routing in `web_portal/routes/operations.py` and `design/research.md`. (delivered: design/research.md)

## Phase 2: Foundation

- [x] T002 Define the request contract and synthetic validation procedure in `design/contracts/requests.md` and `design/quickstart.md`. (delivered: design/contracts/requests.md)

## Phase 3: User Story 1 - Share operation state

**Goal**: One executor per application during simultaneous first access.

**Independent test**: Force all first reads to observe an absent executor before delayed construction can finish.

- [x] T003 [US1] Add deterministic race, existing-instance, isolation, retry, and lock-release tests. (delivered: tests/unit/web_portal/test_operation_executor_concurrency.py)
- [x] T004 [US1] Prove the race test fails against the original helper in `web_portal/routes/operations.py`. (delivered: analysis.md)
- [x] T005 [US1] Synchronize lazy creation without locking operation execution. (delivered: web_portal/routes/operations.py)

## Phase 4: Verification

- [x] T006 [P] Add the user-visible release fragment. (delivered: changelog.d/issue-4026-operation-executor-race.md)
- [x] T007 Run focused and applicable local gates, then record results. (delivered: analysis.md)

## Dependencies and parallel work

T001 precedes T002. T002 precedes T003. T003 precedes T004. T004 precedes T005.
T006 can proceed independently after T002. T007 follows T005 and T006.
The single user story is the complete repair. No additional feature increment is required.

## Implementation strategy

First prove duplicate construction with synthetic requests.
Then add synchronization and verify normal behavior, failure recovery, and operation-lock independence.
Commit only the explicit feature files.
