# Tasks: Synthetic Test Trigger

**Input**: Design artifacts from `specs/3563-synthetic-test-trigger/`.

**Prerequisites**: `plan.md`, `research.md`, `data-model.md`, `contracts/cli.md`, and `quickstart.md`.

## Phase 1: Setup

- [ ] T001 Create `src/troubleshooting/synthetic_test_trigger/__init__.py` with the public `SyntheticTestTrigger` export.
- [ ] T002 Create `tests/unit/troubleshooting/synthetic_test_trigger/__init__.py` for the feature test package.
- [ ] T003 Create `changelog.d/issue-3563-synthetic-test-trigger.md` with one `Added` section for issue `#3563`.
- [ ] T004 Create `specs/3563-synthetic-test-trigger/wiring.md` and mark `MistHelper.py` registration as deferred to the integration pull request.

## Phase 2: Foundational

- [ ] T005 Create `src/troubleshooting/synthetic_test_trigger/models.py` with dataclasses, safe body builders, result normalization, timeout messages, and export row builders.
- [ ] T006 Create `src/troubleshooting/synthetic_test_trigger/client.py` with SDK-backed trigger and poll calls for the five Mist operation IDs.
- [ ] T007 Create `src/troubleshooting/synthetic_test_trigger/operation.py` with prompt flow, confirmation, polling, reporting, and export wiring.

## Phase 3: User Story 1 - Start a site validation now (P1)

**Independent Test**: Mock the Mist API, accept `y`, return one result, and verify the export row.

- [ ] T008 [P] [US1] Add a unit test in `tests/unit/troubleshooting/synthetic_test_trigger/test_synthetic_test_trigger.py` for site request body shape.
- [ ] T009 [US1] Add a unit test in `tests/unit/troubleshooting/synthetic_test_trigger/test_synthetic_test_trigger.py` that verifies confirmation cancels every answer except `y`.
- [ ] T010 [US1] Add a unit test in `tests/unit/troubleshooting/synthetic_test_trigger/test_synthetic_test_trigger.py` that verifies `SyntheticTestTrigger.csv` export rows for a completed site result.

## Phase 4: User Story 2 - Start one device validation now (P2)

**Independent Test**: Mock one device selection and assert the device body matches the OpenAPI schema.

- [ ] T011 [P] [US2] Add a unit test in `tests/unit/troubleshooting/synthetic_test_trigger/test_synthetic_test_trigger.py` for device request body shape.
- [ ] T012 [US2] Add a unit test in `tests/unit/troubleshooting/synthetic_test_trigger/test_synthetic_test_trigger.py` that verifies timeout behavior after `SYNTHETIC_TEST_TIMEOUT_SECONDS`.

## Phase 5: User Story 3 - Prove switch RADIUS reachability (P3)

**Independent Test**: Mock the RADIUS trigger and verify the password is absent from logs and export rows.

- [ ] T013 [P] [US3] Add a unit test in `tests/unit/troubleshooting/synthetic_test_trigger/test_synthetic_test_trigger.py` for RADIUS request body shape.
- [ ] T014 [US3] Add a unit test in `tests/unit/troubleshooting/synthetic_test_trigger/test_synthetic_test_trigger.py` that verifies password masking in summaries and export rows.

## Phase 6: Polish and analysis

- [ ] T015 Run `py_compile`, `ruff`, `black --check`, `mypy`, `pydocstyle`, `pytest`, `vulture`, and `interrogate` for the feature package and tests.
- [ ] T016 Run SpecKit analyze, repair each finding, and commit the repaired artifacts.

## Dependencies

- Phase 1 must finish before Phase 2.
- Phase 2 must finish before user-story tests.
- User Story 1 is the MVP and must finish before final validation.
- User Stories 2 and 3 can run after Phase 2 and do not depend on each other.

## Parallel Execution Examples

- T008, T011, and T013 can be drafted in parallel because they target different body shapes.
- T003 and T004 can run in parallel because they create different documentation files.

## Implementation Strategy

1. Build the package skeleton and wiring manifest first.
2. Implement the pure model and client code before the operation prompts.
3. Prove the MVP site trigger path.
4. Add device and RADIUS tests.
5. Run the full feature gate list.
