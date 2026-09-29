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

- [ ] T005 [P] Create `src/troubleshooting/nac_idp_credential_test/model.py` with dataclasses for provider choices, requests, results, and export rows.
- [ ] T006 [P] Create `tests/unit/troubleshooting/nac_idp_credential_test/test_nac_idp_credential_test_model.py` for request body shape, response normalization, and password-free export rows.
- [ ] T007 Create `src/troubleshooting/nac_idp_credential_test/client.py` with SDK-backed `getOrgSettings`, `listOrgSsos`, and `validateOrgIdpCredential` calls.
- [ ] T008 Create `tests/unit/troubleshooting/nac_idp_credential_test/test_nac_idp_credential_test_client.py` with fixtures that prove provider source selection and request dispatch without network access.

**Checkpoint**: Foundation ready. User story work can start.

---

## Phase 3: User Story 1 - Validate an identity provider bind (Priority: P1)

**Goal**: Let an operator select one NAC identity provider and run one credential validation.

**Independent Test**: Stub the client and prompts, run the operation, and verify one validation call and one export row.

### Tests for User Story 1

- [ ] T009 [US1] Add operation success test in `tests/unit/troubleshooting/nac_idp_credential_test/test_nac_idp_credential_test_operation.py`.

### Implementation for User Story 1

- [ ] T010 [US1] Create `src/troubleshooting/nac_idp_credential_test/prompts.py` with numbered provider selection and username prompts.
- [ ] T011 [US1] Create `src/troubleshooting/nac_idp_credential_test/operation.py` with class `NacIdpCredentialTest` and static `run()`.
- [ ] T012 [US1] Export `NacIdpCredentialTest` from `src/troubleshooting/nac_idp_credential_test/__init__.py`.

**Checkpoint**: User Story 1 is functional and testable.

---

## Phase 4: User Story 2 - Protect the password (Priority: P1)

**Goal**: Use hidden input for the password and keep the password out of logs and output files.

**Independent Test**: Patch hidden input, capture logs and export rows, and assert the password is absent.

### Tests for User Story 2

- [ ] T013 [US2] Add password protection test in `tests/unit/troubleshooting/nac_idp_credential_test/test_nac_idp_credential_test_operation.py`.

### Implementation for User Story 2

- [ ] T014 [US2] Add hidden password prompt and `y` or `N` confirmation in `src/troubleshooting/nac_idp_credential_test/prompts.py`.
- [ ] T015 [US2] Ensure operation logging and export rows never include the password in `src/troubleshooting/nac_idp_credential_test/operation.py`.

**Checkpoint**: User Story 2 is functional and testable.

---

## Phase 5: User Story 3 - Handle a rejected credential (Priority: P2)

**Goal**: Print the API failure reason and stop cleanly without a traceback.

**Independent Test**: Stub a failure response and verify a clean operation result.

### Tests for User Story 3

- [ ] T016 [US3] Add failed validation test in `tests/unit/troubleshooting/nac_idp_credential_test/test_nac_idp_credential_test_operation.py`.

### Implementation for User Story 3

- [ ] T017 [US3] Add failure reason formatting in `src/troubleshooting/nac_idp_credential_test/model.py` and `operation.py`.
- [ ] T018 [US3] Add no-provider and declined-confirmation paths in `src/troubleshooting/nac_idp_credential_test/operation.py`.

**Checkpoint**: All user stories are functional and testable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finish validation, documentation, and final SpecKit analysis repairs.

- [ ] T019 Run quickstart validation gates for `src/troubleshooting/nac_idp_credential_test` and `tests/unit/troubleshooting/nac_idp_credential_test`.
- [ ] T020 Run `vulture` and `interrogate` on `src/troubleshooting/nac_idp_credential_test`.
- [ ] T021 Run `speckit.analyze` equivalent checks across `spec.md`, `plan.md`, and `tasks.md`, then repair findings.
- [ ] T022 Write draft pull request body in `specs/3565-nac-idp-credential-test/pr-body.md`.

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

