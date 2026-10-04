# Tasks: Client Device Fingerprint Census

**Input**: Design documents in `specs/3569-client-fingerprint-census/`  
**Prerequisites**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/client-fingerprint-census.md`

## Phase 1: Setup

- [x] T001 Create `src/mist/intelligence/reports/client_fingerprint_census/__init__.py` with package exports.
- [x] T002 Create `tests/unit/reports/client_fingerprint_census/__init__.py` for the new test package.
- [x] T003 Create `changelog.d/issue-3569-client-fingerprint-census.md` with one `### Added` entry for issue `#3569`.

## Phase 2: Foundation

- [x] T004 [P] Create pure dataclasses and constants in `src/mist/intelligence/reports/client_fingerprint_census/model.py`.
- [x] T005 [P] Create the SDK client seam in `src/mist/intelligence/reports/client_fingerprint_census/client.py`.
- [x] T006 Create the operation handler in `src/mist/intelligence/reports/client_fingerprint_census/operation.py`.

## Phase 3: User Story 1 - Export a site fingerprint census

**Independent Test**: Mock the site prompt, field prompt, API response, and exporter. Verify the operation writes rows and prints the top 20 rows.

- [x] T007 [P] [US1] Add model tests for enum validation, row normalization, sorting, and the 20-row table limit in `tests/unit/reports/client_fingerprint_census/test_client_fingerprint_census_model.py`.
- [x] T008 [P] [US1] Add client tests for the SDK call arguments and response shape in `tests/unit/reports/client_fingerprint_census/test_client_fingerprint_census_client.py`.
- [x] T009 [US1] Add operation tests for prompts, API call, export, and console table output in `tests/unit/reports/client_fingerprint_census/test_client_fingerprint_census_operation.py`.

## Phase 4: User Story 2 - Handle an empty census

**Independent Test**: Mock an empty API response. Verify that the exporter receives field names and no rows, and that the empty message is printed.

- [x] T010 [US2] Add the empty-response operation test in `tests/unit/reports/client_fingerprint_census/test_client_fingerprint_census_operation.py`.
- [x] T011 [US2] Implement header-only export behavior in `src/mist/intelligence/reports/client_fingerprint_census/operation.py`.

## Phase 5: User Story 3 - Keep integration wiring deferred

**Independent Test**: Verify the wiring manifest contains menu `289`, category `interactive_safe`, the site prompt skip reason, the primary key strategy, and the deferred import line.

- [x] T012 [US3] Verify and update `specs/3569-client-fingerprint-census/wiring.md` with every contract section.
- [x] T013 [US3] Add a wiring manifest test in `tests/unit/reports/client_fingerprint_census/test_client_fingerprint_census_operation.py`.
- [x] T014 [US3] Mark the `MistHelper.py` registration as deferred to the integration pull request in `specs/3569-client-fingerprint-census/wiring.md`.
- [x] T014A [US3] Mark the README menu table update as deferred to the integration pull request in `specs/3569-client-fingerprint-census/wiring.md`.
- [x] T014B [US3] Mark final menu acceptance as blocked until the integration pull request updates README and shared menu files.

## Phase 6: Polish and Validation

- [x] T015 Run compile, Ruff, Black, mypy, pydocstyle, pytest, vulture, and interrogate for the package and test directory.
- [x] T016 Run SpecKit analyze manually and repair any inconsistency in `specs/3569-client-fingerprint-census/`.
- [x] T017 Verify and update `specs/3569-client-fingerprint-census/pr-body.md` for the draft pull request.
- [x] T018 Record the fleet artifact count remediation path in `specs/3569-client-fingerprint-census/plan.md`.
- [x] T019 Verify inline-comment, action-logging, and secret-safe logging compliance in `src/mist/intelligence/reports/client_fingerprint_census/`.

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
