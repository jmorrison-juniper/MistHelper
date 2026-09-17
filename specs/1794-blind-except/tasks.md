# Tasks: Blind Exception Handler Cleanup Slice

**Input**: Design documents from `specs\1794-blind-except\`

**Prerequisites**: `plan.md`, `spec.md`

**Tests**: The unit tests are required because issue #1794 demands failure proof.

## Phase 1: Setup

- [x] T001 Read issue #1794, #1793, #1924, and #2750. (delivered: issue context)
- [x] T002 Create the worktree `..\MistHelper-1794-blind-except`. (delivered: worktree)
- [x] T003 Measure the current broad handler count. (delivered: total 813 before, 812 after)

## Phase 2: Implementation

- [x] T004 [US1] Narrow the firmware stats handler in `src\firmware\running_version.py`. (delivered: `src\firmware\running_version.py`)
- [x] T005 [US1] Add a test for runtime failure reporting in `tests\unit\firmware\test_running_version.py`. (delivered: `tests\unit\firmware\test_running_version.py`)
- [x] T006 [US1] Add a test for programming error propagation in `tests\unit\firmware\test_running_version.py`. (delivered: `tests\unit\firmware\test_running_version.py`)
- [x] T007 [US1] Patch SSR flow tests to isolate the running-version overlay in `tests\unit\firmware\test_firmware_manager_ssr.py`. (delivered: `tests\unit\firmware\test_firmware_manager_ssr.py`)

## Phase 3: Follow-up Tracking

- [x] T008 File the firmware follow-up issue. (delivered: #2833)
- [x] T009 File the API and credential follow-up issue. (delivered: #2834)
- [x] T010 File the persistence follow-up issue. (delivered: #2835)
- [x] T011 File the display follow-up issue. (delivered: #2836)

## Phase 4: Validation

- [x] T012 Run targeted pytest for the changed unit test file. (delivered: 16 passed)
- [ ] T013 Run all requested repository validation shards.
- [ ] T014 Push the branch and open the pull request.

## Dependencies & Execution Order

Phase 1 must finish before implementation. T004 must finish before T005 and T006 can pass. Phase 3 and Phase 4 can run after T004 through T006.
