# Tasks: Organization Switch Scorecard

**Input**: Design documents from `specs/3558-switch-scorecard/`  
**Prerequisites**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/report-contract.md`

## Phase 1: Setup

- [ ] T001 Create `src/mist/intelligence/reports/switch_scorecard/__init__.py` with the package export.
- [ ] T002 Create `tests/unit/reports/switch_scorecard/__init__.py` for the unit test package.
- [ ] T003 Create `changelog.d/issue-3558-switch-scorecard.md` with one `### Added` section.

## Phase 2: Foundation

- [ ] T004 Create `src/mist/intelligence/reports/switch_scorecard/model.py` with dataclasses, column constants, threshold parsing, row builders, and site summary builders.
- [ ] T005 Create `src/mist/intelligence/reports/switch_scorecard/client.py` with a class that reuses `APIDataFetcher` for `listOrgDevicesStats` with `type="switch"`.
- [ ] T006 Create `src/mist/intelligence/reports/switch_scorecard/operation.py` with `SwitchScorecard.run()` and no prompt path.
- [ ] T007 Create `specs/3558-switch-scorecard/wiring.md` with every contract section and mark root menu wiring as deferred to integration.

## Phase 3: User Story 1 - Review Every Switch

**Independent Test**: Unit tests build two switch rows from fixture API data and validate all required detail fields.

- [ ] T008 [P] [US1] Add detail-row tests in `tests/unit/reports/switch_scorecard/test_switch_scorecard_model.py`.
- [ ] T009 [US1] Implement switch detail row construction in `src/mist/intelligence/reports/switch_scorecard/model.py`.
- [ ] T010 [US1] Implement module aggregation for PoE, BIOS, FPGA, backup, fan, PSU, and temperature fields in `src/mist/intelligence/reports/switch_scorecard/model.py`.
- [ ] T011 [US1] Run the unit test for detail rows and repair failures.

## Phase 4: User Story 2 - Compare Sites

**Independent Test**: Unit tests build site rows for two sites and validate percentage and count columns.

- [ ] T012 [P] [US2] Add site-summary tests in `tests/unit/reports/switch_scorecard/test_switch_scorecard_model.py`.
- [ ] T013 [US2] Implement site summary percentage and count logic in `src/mist/intelligence/reports/switch_scorecard/model.py`.
- [ ] T014 [US2] Implement org summary percentage and count logic in `src/mist/intelligence/reports/switch_scorecard/model.py`.
- [ ] T015 [US2] Run the unit test for site summary rows and repair failures.

## Phase 5: User Story 3 - No-Prompt Operation

**Independent Test**: Unit tests run `SwitchScorecard.run()` with fake dependencies and verify two export writes.

- [ ] T016 [P] [US3] Add client tests in `tests/unit/reports/switch_scorecard/test_switch_scorecard_client.py`.
- [ ] T017 [P] [US3] Add operation tests in `tests/unit/reports/switch_scorecard/test_switch_scorecard_operation.py`.
- [ ] T018 [US3] Implement the shared fetcher seam in `src/mist/intelligence/reports/switch_scorecard/client.py`.
- [ ] T019 [US3] Implement `SwitchScorecard.run()` orchestration and console summary in `src/mist/intelligence/reports/switch_scorecard/operation.py`.
- [ ] T020 [US3] Run the operation tests and repair failures.

## Phase 6: Polish and Gates

- [ ] T021 Run `py_compile`, `ruff`, `black --check`, `mypy`, `pydocstyle`, and `pytest` for the package and tests.
- [ ] T022 Run `vulture` and `interrogate` for `src/mist/intelligence/reports/switch_scorecard`.
- [ ] T023 Confirm the SDK symbol `mistapi.api.v1.orgs.stats.listOrgDevicesStats` exists and record the result in `research.md`.
- [ ] T024 Confirm `specs/3558-switch-scorecard/wiring.md` names the deferred `MistHelper.py` import and menu registration.

## Deferred Integration Task

- [ ] T025 [Integration] Apply the menu 277 registration in `MistHelper.py`, `src/foundation/support/utils/operation_registry.py`, generated menu references, and primary key strategies from `specs/3558-switch-scorecard/wiring.md`.

## Dependencies

1. T001 through T007 must complete before user story implementation.
2. US1 can complete before US2 and US3.
3. US2 depends on detail rows from US1.
4. US3 depends on the model and client seams.
5. T025 is not part of this feature branch.

## Parallel Examples

- T008, T012, T016, and T017 can run in parallel after the package skeleton exists.
- T009 and T010 must stay sequential because both edit `model.py`.
- T018 and T019 must stay sequential because the operation imports the client.

## Implementation Strategy

1. Build the model first because it is pure and has no network dependency.
2. Build the client second because it only fetches rows.
3. Build the operation last because it connects the model, client, and exporter.
4. Write the wiring manifest before the first implementation commit so integration has no missing fields.
