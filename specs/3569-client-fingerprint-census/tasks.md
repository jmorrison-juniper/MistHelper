# Tasks: Client Device Fingerprint Census

**Input**: Design documents in `specs/3569-client-fingerprint-census/`  
**Prerequisites**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/client-fingerprint-census.md`

## Phase 1: Setup

- [ ] T001 Create `src/reports/client_fingerprint_census/__init__.py` with package exports.
- [ ] T002 Create `tests/unit/reports/client_fingerprint_census/__init__.py` for the new test package.
- [ ] T003 Create `changelog.d/issue-3569-client-fingerprint-census.md` with one `### Added` entry for issue `#3569`.

## Phase 2: Foundation

- [ ] T004 [P] Create pure dataclasses and constants in `src/reports/client_fingerprint_census/model.py`.
- [ ] T005 [P] Create the SDK client seam in `src/reports/client_fingerprint_census/client.py`.
- [ ] T006 Create the operation handler in `src/reports/client_fingerprint_census/operation.py`.

## Phase 3: User Story 1 - Export a site fingerprint census

**Independent Test**: Mock the site prompt, field prompt, API response, and exporter. Verify the operation writes rows and prints the top 20 rows.

- [ ] T007 [P] [US1] Add model tests for enum validation, row normalization, sorting, and the 20-row table limit in `tests/unit/reports/client_fingerprint_census/test_client_fingerprint_census_model.py`.
- [ ] T008 [P] [US1] Add client tests for the SDK call arguments and response shape in `tests/unit/reports/client_fingerprint_census/test_client_fingerprint_census_client.py`.
- [ ] T009 [US1] Add operation tests for prompts, API call, export, and console table output in `tests/unit/reports/client_fingerprint_census/test_client_fingerprint_census_operation.py`.

## Phase 4: User Story 2 - Handle an empty census

**Independent Test**: Mock an empty API response. Verify that the exporter receives field names and no rows, and that the empty message is printed.

- [ ] T010 [US2] Add the empty-response operation test in `tests/unit/reports/client_fingerprint_census/test_client_fingerprint_census_operation.py`.
- [ ] T011 [US2] Implement header-only export behavior in `src/reports/client_fingerprint_census/operation.py`.

## Phase 5: User Story 3 - Keep integration wiring deferred

**Independent Test**: Verify the wiring manifest contains menu `289`, category `interactive_safe`, the site prompt skip reason, the primary key strategy, and the deferred import line.

- [ ] T012 [US3] Create `specs/3569-client-fingerprint-census/wiring.md` with every contract section.
- [ ] T013 [US3] Add a wiring manifest test in `tests/unit/reports/client_fingerprint_census/test_client_fingerprint_census_operation.py`.
- [ ] T014 [US3] Mark the `MistHelper.py` registration as deferred to the integration pull request in `specs/3569-client-fingerprint-census/wiring.md`.

## Phase 6: Polish and Validation

- [ ] T015 Run compile, Ruff, Black, mypy, pydocstyle, pytest, vulture, and interrogate for the package and test directory.
- [ ] T016 Run SpecKit analyze manually and repair any inconsistency in `specs/3569-client-fingerprint-census/`.
- [ ] T017 Create `specs/3569-client-fingerprint-census/pr-body.md` for the draft pull request.

## Dependencies

- Phase 1 must finish before Phase 2.
- Phase 2 must finish before User Stories 1 and 2.
- User Story 3 can run after Phase 1.
- Phase 6 must run after all user stories.

## Parallel Execution Examples

- T004 and T005 can run in parallel because they create different modules.
- T007 and T008 can run in parallel because they test different modules.
- T012 can run while T007 and T008 run because it edits only the spec directory.

## Implementation Strategy

1. Complete the model and client first.
2. Complete operation behavior with tests for populated and empty responses.
3. Complete wiring and release-note files.
4. Run gates before each implementation commit.
