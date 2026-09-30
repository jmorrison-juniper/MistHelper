# Tasks: Test the guest portal SMS provider

**Input**: Design documents from `specs/3564-sms-provider-test/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, and `contracts/`

**Tests**: Unit tests are required for provider body shapes, secret handling, confirmation refusal, non-2xx handling, and export rows.

**Organization**: Tasks are grouped by user story and by implementation dependency.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: The task can run in parallel with other tasks in different files.
- **[Story]**: The user story that the task supports.
- Each task names an exact file path.

---

## Phase 1: Setup

**Purpose**: Create the feature package, test directory, release note, and deferred wiring manifest.

- [x] T001 [P] Create `src/troubleshooting/sms_provider_test/__init__.py` with package exports.
- [x] T002 [P] Create `tests/unit/troubleshooting/sms_provider_test/__init__.py`.
- [x] T003 [P] Create `changelog.d/issue-3564-sms-provider-test.md` with one `### Added` heading.
- [x] T004 Create `specs/3564-sms-provider-test/wiring.md` with every section required by the fleet contract.
- [x] T005 Record the deferred `MistHelper.py` import and menu registration in `specs/3564-sms-provider-test/wiring.md`.

---

## Phase 2: Foundational

**Purpose**: Build pure model logic and OpenAPI-aligned provider definitions.

- [x] T006 [US3] Create provider definitions in `src/troubleshooting/sms_provider_test/model.py`.
- [x] T007 [US3] Add body-building methods in `src/troubleshooting/sms_provider_test/model.py`.
- [x] T008 [US1] Add result-row dataclass in `src/troubleshooting/sms_provider_test/model.py`.
- [x] T009 [US3] Add provider body shape tests in `tests/unit/troubleshooting/sms_provider_test/test_sms_provider_test_model.py`.
- [x] T010 [US2] Add credential exclusion tests in `tests/unit/troubleshooting/sms_provider_test/test_sms_provider_test_model.py`.

---

## Phase 3: API client

**Purpose**: Encapsulate the three Mist SDK calls and response handling.

- [x] T011 [US3] Create `SmsProviderTestClient` in `src/troubleshooting/sms_provider_test/client.py`.
- [x] T012 [US1] Add a response normalizer for 2xx and non-2xx responses in `src/troubleshooting/sms_provider_test/client.py`.
- [x] T013 [US3] Add client dispatch tests for all three SDK call sites in `tests/unit/troubleshooting/sms_provider_test/test_sms_provider_test_client.py`.
- [x] T014 [US1] Add non-2xx response tests in `tests/unit/troubleshooting/sms_provider_test/test_sms_provider_test_client.py`.

---

## Phase 4: Prompt and operation flow

**Purpose**: Add safe prompts, hidden secret input, confirmation, API call, verdict print, and export.

- [x] T015 [US2] Create hidden-input prompt helpers in `src/troubleshooting/sms_provider_test/inputs.py`.
- [x] T016 [US1] Create `SmsProviderTest.run()` in `src/troubleshooting/sms_provider_test/operation.py`.
- [x] T017 [US1] Add confirmation refusal tests in `tests/unit/troubleshooting/sms_provider_test/test_sms_provider_test_operation.py`.
- [x] T018 [US2] Add hidden-input and no-secret-output tests in `tests/unit/troubleshooting/sms_provider_test/test_sms_provider_test_operation.py`.
- [x] T019 [US1] Add export call tests for `SmsProviderTest.csv` in `tests/unit/troubleshooting/sms_provider_test/test_sms_provider_test_operation.py`.

---

## Phase 5: Validation and analysis

**Purpose**: Prove the implementation and repair findings.

- [x] T020 Run `py_compile`, `ruff`, `black --check`, `mypy`, `pydocstyle`, and targeted `pytest` for this package and test directory.
- [x] T021 Run `vulture` and `interrogate` for `src/troubleshooting/sms_provider_test`.
- [x] T022 Run `speckit.analyze` and repair each finding.
- [ ] T023 Push the implementation milestone.
- [ ] T024 Open a draft pull request with `Closes #3564`.

---

## Deferred integration task

The integration pull request, not this branch, edits `MistHelper.py`, `src/utils/operation_registry.py`, `src/refactors/endpoint_primary_key_strategies.py`, `README.md`, generated menu references, and any web portal file. This branch records exact instructions in `specs/3564-sms-provider-test/wiring.md`.

## Dependencies

- T004 and T005 block the integration handoff.
- T006 through T010 block the client and operation tests.
- T011 through T014 block operation execution.
- T015 through T019 block validation.
- T020 through T022 block the final push and draft pull request.

