# Tasks: RRM optimize or reset plan capture

**Input**: Design documents from `specs/3571-rrm-reset-plan/`  
**Prerequisites**: `plan.md`, `research.md`, `data-model.md`, `contracts/operation-contract.md`, `quickstart.md`

## Phase 1: Setup

- [ ] T001 Create `src/mist/resources/site/rrm_reset/__init__.py` and `tests/unit/site/rrm_reset/__init__.py`.
- [ ] T002 Create `changelog.d/issue-3571-rrm-reset-plan.md` with one `### Added` heading and one bullet that names issue `#3571`.
- [ ] T003 Create `specs/3571-rrm-reset-plan/wiring.md` with all contract sections and mark `MistHelper.py` registration as deferred to the integration pull request.

## Phase 2: Foundation

- [ ] T004 [P] Create pure data classes and constants in `src/mist/resources/site/rrm_reset/model.py`.
- [ ] T005 [P] Create writer orchestration in `src/mist/resources/site/rrm_reset/writer.py`.
- [ ] T006 [P] Create Mist API client seams in `src/mist/resources/site/rrm_reset/client.py`.

## Phase 3: User Story 1 - Optimize with before capture (P1)

**Goal**: Capture the before plan and send optimize only after typed confirmation.

**Independent Test**: A fake writer records `before` before the fake optimize client call.

- [ ] T007 [P] [US1] Add optimize ordering tests in `tests/unit/site/rrm_reset/test_rrm_reset_operation.py`.
- [ ] T008 [US1] Implement `RrmResetOperation.run()` and optimize workflow in `src/mist/resources/site/rrm_reset/operation.py`.
- [ ] T009 [US1] Run the required gates for `src/mist/resources/site/rrm_reset` and `tests/unit/site/rrm_reset`, then commit the first implementation group.

## Phase 4: User Story 2 - Reset with before capture (P1)

**Goal**: Capture the before plan and send reset only after typed confirmation.

**Independent Test**: A fake writer records `before` before the fake reset client call.

- [ ] T010 [P] [US2] Add reset and refusal tests in `tests/unit/site/rrm_reset/test_rrm_reset_operation.py`.
- [ ] T011 [US2] Implement reset request handling in `src/mist/resources/site/rrm_reset/client.py` and `src/mist/resources/site/rrm_reset/operation.py`.
- [ ] T012 [US2] Run the required gates for `src/mist/resources/site/rrm_reset` and `tests/unit/site/rrm_reset`, then commit the reset group.

## Phase 5: User Story 3 - After capture and diff (P2)

**Goal**: Wait for the configured settle time, capture the after plan, and write a changed-radio diff.

**Independent Test**: Fixture before and after plans produce a diff with changed radios only.

- [ ] T013 [P] [US3] Add model diff tests in `tests/unit/site/rrm_reset/test_rrm_reset_model.py`.
- [ ] T014 [P] [US3] Add client tests in `tests/unit/site/rrm_reset/test_rrm_reset_client.py`.
- [ ] T015 [US3] Implement diff and settle-time model behavior in `src/mist/resources/site/rrm_reset/model.py`.
- [ ] T016 [US3] Implement after capture and diff writing in `src/mist/resources/site/rrm_reset/operation.py` and `src/mist/resources/site/rrm_reset/writer.py`.
- [ ] T017 [US3] Run the required gates for `src/mist/resources/site/rrm_reset` and `tests/unit/site/rrm_reset`, then commit the diff group.

## Phase 6: Polish and pull request

- [ ] T018 Run `vulture` and `interrogate` for `src/mist/resources/site/rrm_reset`, then fix findings.
- [ ] T019 Create `specs/3571-rrm-reset-plan/pr-body.md` with `Closes #3571`, the destructive human review statement, files changed, deferred wiring, and true checklist items.
- [ ] T020 Push the implementation milestone, run SpecKit analyze, repair findings, commit repairs, push the final milestone, and open a draft pull request.

## Dependencies

- Phase 1 blocks all later phases.
- Phase 2 blocks all user stories.
- User Stories 1 and 2 can run after Phase 2.
- User Story 3 depends on the capture model from User Stories 1 and 2.
- Phase 6 depends on all user stories.

## Parallel Examples

- T004, T005, and T006 can run in parallel because they touch different source files.
- T013 and T014 can run in parallel because they touch different test files.

## Implementation Strategy

1. Deliver the model and seams first.
2. Deliver optimize and reset safety next.
3. Deliver after capture and diff last.
4. Keep menu registration in `wiring.md` for the integration pull request.
