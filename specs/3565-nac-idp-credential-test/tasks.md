# Tasks: NAC IDP Credential Test

**Input**: Design documents from `specs/3565-nac-idp-credential-test/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/client-contract.md, quickstart.md

**Tests**: Tests are required by the feature specification and acceptance criteria.

**Organization**: Tasks are grouped by user story so each story stays independently testable.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the owned feature paths and non-code feature records.

- [x] T001 Create package structure in `src/troubleshooting/nac_idp_credential_test/` with `__init__.py`. (delivered: src/troubleshooting/nac_idp_credential_test/__init__.py)
- [x] T002 Create test structure in `tests/unit/troubleshooting/nac_idp_credential_test/` with `__init__.py`. (delivered: tests/unit/troubleshooting/nac_idp_credential_test/__init__.py)
- [x] T003 Create release note `changelog.d/issue-3565-nac-idp-credential-test.md`. (delivered: changelog.d/issue-3565-nac-idp-credential-test.md)
- [x] T004 Create wiring manifest `specs/3565-nac-idp-credential-test/wiring.md` and mark `MistHelper.py` registration as deferred to the integration pull request. (delivered: specs/3565-nac-idp-credential-test/wiring.md)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build the pure model and client contracts that every story uses.

- [x] T005 [P] Create `src/troubleshooting/nac_idp_credential_test/model.py` with dataclasses for provider choices, requests, results, and export rows. (delivered: src/troubleshooting/nac_idp_credential_test/model.py)
- [x] T006 [P] Create `tests/unit/troubleshooting/nac_idp_credential_test/test_nac_idp_credential_test_model.py` for request body shape, response normalization, and password-free export rows. (delivered: tests/unit/troubleshooting/nac_idp_credential_test/test_nac_idp_credential_test_model.py)
- [x] T007 Create `src/troubleshooting/nac_idp_credential_test/client.py` with SDK-backed `getOrgSettings`, `listOrgSsos`, and `validateOrgIdpCredential` calls. (delivered: src/troubleshooting/nac_idp_credential_test/client.py)
- [x] T008 Create `tests/unit/troubleshooting/nac_idp_credential_test/test_nac_idp_credential_test_client.py` with fixtures that prove provider source selection and request dispatch without network access. (delivered: tests/unit/troubleshooting/nac_idp_credential_test/test_nac_idp_credential_test_client.py)

**Checkpoint**: Foundation ready. User story work can start.

---

## Phase 3: User Story 1 - Validate an identity provider bind (Priority: P1)

**Goal**: Let an operator select one NAC identity provider and run one credential validation.

**Independent Test**: Stub the client and prompts, run the operation, and verify one validation call and one export row.

### Tests for User Story 1

- [x] T009 [US1] Add operation success test in `tests/unit/troubleshooting/nac_idp_credential_test/test_nac_idp_credential_test_operation.py`. (delivered: `test_nac_idp_credential_test_operation_writes_safe_csv`)

### Implementation for User Story 1

- [x] T010 [US1] Create `src/troubleshooting/nac_idp_credential_test/prompts.py` with numbered provider selection and username prompts. (delivered: `NacIdpCredentialPrompts`)
- [x] T011 [US1] Create `src/troubleshooting/nac_idp_credential_test/operation.py` with class `NacIdpCredentialTest` and static `run()`. (delivered: `NacIdpCredentialTest.run`)
- [x] T012 [US1] Export `NacIdpCredentialTest` from `src/troubleshooting/nac_idp_credential_test/__init__.py`. (delivered: package `__all__`)

**Checkpoint**: User Story 1 is functional and testable.

---

## Phase 4: User Story 2 - Protect the password (Priority: P1)

**Goal**: Use hidden input for the password and keep the password out of logs and output files.

**Independent Test**: Patch hidden input, capture logs and export rows, and assert the password is absent.

### Tests for User Story 2

- [x] T013 [US2] Add password protection test in `tests/unit/troubleshooting/nac_idp_credential_test/test_nac_idp_credential_test_operation.py`. (delivered: hidden prompt and no-secret assertions)

### Implementation for User Story 2

- [x] T014 [US2] Add hidden password prompt and `y` or `N` confirmation in `src/troubleshooting/nac_idp_credential_test/prompts.py`. (delivered: `ask_password` and `ask_confirmation`)
- [x] T015 [US2] Ensure operation logging and export rows never include the password in `src/troubleshooting/nac_idp_credential_test/operation.py`. (delivered: result export uses password-free rows)

**Checkpoint**: User Story 2 is functional and testable.

---

## Phase 5: User Story 3 - Handle a rejected credential (Priority: P2)

**Goal**: Print the API failure reason and stop cleanly without a traceback.

**Independent Test**: Stub a failure response and verify a clean operation result.

### Tests for User Story 3

- [x] T016 [US3] Add failed validation test in `tests/unit/troubleshooting/nac_idp_credential_test/test_nac_idp_credential_test_operation.py`. (delivered: `test_nac_idp_credential_test_failure_prints_reason`)

### Implementation for User Story 3

- [x] T017 [US3] Add failure reason formatting in `src/troubleshooting/nac_idp_credential_test/model.py` and `operation.py`. (delivered: `read_reason` and `_log_result`)
- [x] T018 [US3] Add no-provider and declined-confirmation paths in `src/troubleshooting/nac_idp_credential_test/operation.py`. (delivered: no-provider and declined-confirmation returns)

**Checkpoint**: All user stories are functional and testable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finish validation, documentation, and final SpecKit analysis repairs.

- [x] T019 Run quickstart validation gates for `src/troubleshooting/nac_idp_credential_test` and `tests/unit/troubleshooting/nac_idp_credential_test`. (delivered: compile, Ruff, Black, mypy, pydocstyle, and pytest pass)
- [x] T020 Run `vulture` and `interrogate` on `src/troubleshooting/nac_idp_credential_test`. (delivered: vulture passed and interrogate reported 100.0 percent)
- [x] T021 Verify inline comment coverage and action logging across the owned package. (delivered: each executable source line has a `WHY` comment, and prompts, API calls, transforms, validation results, and exports have safe action logs)
- [x] T022 Add an operation test for export-backend failure handling without password leakage. (delivered: `test_nac_idp_credential_test_export_failure_logs_error`)
- [x] T023 Add an operation test for the five-prompt acceptance limit. (delivered: `test_nac_idp_credential_test_happy_path_uses_five_or_fewer_prompts`)
- [x] T024 Record that README and menu reference changes are deferred to the integration pull request. (delivered: `wiring.md` and `pr-body.md` both state the deferred registration work)
- [x] T025 Record that the full deployment pipeline continues after this feature branch. (delivered: `plan.md` and `pr-body.md` state the CI, integration, merge, image, deploy, and health-check handoff)
- [x] T026 Run `speckit.analyze` equivalent checks across `spec.md`, `plan.md`, and `tasks.md`, then repair findings. (delivered: re-run reported no findings remain)
- [x] T027 Write draft pull request body in `specs/3565-nac-idp-credential-test/pr-body.md`. (delivered: PR body with issue closure, files, deferred wiring, and gate results)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on setup completion and blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on foundational tasks.
- **User Story 2 (Phase 4)**: Depends on User Story 1 prompt and operation seams.
- **User Story 3 (Phase 5)**: Depends on foundational result normalization.
- **Polish (Phase 6)**: Depends on all selected user stories.

### Parallel Opportunities

- T005 and T006 can run in parallel after setup.
- T010 and T014 can run in parallel with T011 only after the prompt interface is stable.
- Model and client tests can run independently because they use separate files.

## Implementation Strategy

### MVP First

1. Complete setup and foundational model and client tasks.
2. Complete User Story 1 to validate one provider credential and export one row.
3. Run the targeted unit tests.

### Incremental Delivery

1. Add password protection tests and hidden prompt behavior.
2. Add failure-path tests and clean failure output.
3. Run all owned quality gates.
4. Update tasks as delivered with evidence notes.
