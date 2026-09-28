# Tasks: Status Fallback for Quiet Operation Streams

**Input**: Design documents from `specs/3183-status-fallback/`

## Phase 1: Setup

- [ ] T001 Review the stream and status functions in `web_portal/static/js/operations.js`.

## Phase 2: User Story 1 - Recover a Quiet Run (Priority: P1)

**Goal**: A quiet stream causes a status route check and reaches a terminal badge.

**Independent Test**: Static guard confirms the timer, status check, and cleanup paths exist.

- [ ] T002 [US1] Add a fallback guard in `tests/unit/web_portal/test_operation_stream_fallback.py`.
- [ ] T003 [US1] Run the guard before the repair and record the failure.
- [ ] T004 [US1] Add a single active fallback timer in `web_portal/static/js/operations.js`.
- [ ] T005 [US1] Arm the fallback when the stream starts and after nonterminal events in `web_portal/static/js/operations.js`.
- [ ] T006 [US1] Clear the fallback when the run finishes in `web_portal/static/js/operations.js`.
- [ ] T007 [US1] Rerun the guard and record the pass.

## Phase 3: Polish

- [ ] T008 Add `changelog.d/issue-3183-status-fallback.md`.
- [ ] T009 Run targeted quality gates.
- [ ] T010 Verify the local portal on port 9602.
