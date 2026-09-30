# Tasks: Organization Security Posture Checklist

**Input**: Design documents from `specs/3557-org-security-posture/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, and `quickstart.md`

**Tests**: Tests are required because the specification defines independent tests for all user stories.

**Organization**: Tasks are grouped by user story so each story can be implemented and tested independently.

**Fleet contract**: This task-generation step edits only `specs/3557-org-security-posture/**`. Implementation tasks below reference future files but do not edit them now.

**Deferred integration**: `MistHelper.py` menu registration is deferred to the integration pull request. No task in this list edits `MistHelper.py`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it uses different files and has no dependency on incomplete tasks.
- **[Story]**: Identifies the user story that the task serves.
- Each task includes an exact file path.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the feature structure, release artifact, and feature-owned wiring record.

- [X] T001 Create the report package directories in `src/reports/org_security_posture/`, `src/reports/org_security_posture/checks/`, and `src/reports/org_security_posture/io/`
- [X] T002 [P] Create the unit test package directories in `tests/unit/reports/org_security_posture/` and `tests/unit/reports/org_security_posture/fixtures/`
- [X] T003 [P] Add the release note fragment for menu 276 in `changelog.d/issue-3557-org-security-posture.md`
- [X] T004 Update the deferred wiring manifest in `specs/3557-org-security-posture/wiring.md` to state that `MistHelper.py` registration stays deferred to the integration pull request

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build the shared model, source, registry, and export foundation that all user stories need.

**Critical**: Complete this phase before any user story implementation starts.

- [X] T005 [P] Add unit tests for source operation verification in `tests/unit/reports/org_security_posture/test_mist_api_sources.py`
- [X] T006 [P] Add unit tests for safe display values and one-sentence reasons in `tests/unit/reports/org_security_posture/test_result_formatting.py`
- [X] T007 Define `SecurityPostureCheck`, `SecurityPostureCheckResult`, and `OrganizationSecuritySourceData` in `src/reports/org_security_posture/models.py`
- [X] T008 Implement source operation verification for `getOrgSettings`, `listOrgSsos`, `listOrgAdmins`, `listOrgApiTokens`, and `listOrgWebhooks` in `src/reports/org_security_posture/io/sources.py`
- [X] T009 Implement safe display value formatting and reason validation in `src/reports/org_security_posture/io/formatting.py`
- [X] T010 Implement `OrgSecurityPostureCheckRegistry` with stable order and duplicate ID rejection in `src/reports/org_security_posture/checks/registry.py`
- [X] T011 Add package exports for the runner and data model in `src/reports/org_security_posture/__init__.py`

**Checkpoint**: The source, model, formatting, and registry foundation is ready.

---

## Phase 3: User Story 1 - Generate an organization security checklist (Priority: P1) MVP

**Goal**: Menu 276 can generate `data/OrgSecurityPosture.csv` with at least twelve stable checks.

**Independent Test**: Run the runner with representative fixture data and confirm it writes the CSV with required columns, stable check IDs, and at least twelve rows.

### Tests for User Story 1

- [X] T012 [P] [US1] Add CSV column and minimum row count tests in `tests/unit/reports/org_security_posture/test_output_contract.py`
- [X] T013 [P] [US1] Add stable registry order and duplicate check ID tests in `tests/unit/reports/org_security_posture/test_registry.py`
- [X] T014 [P] [US1] Add password policy check tests in `tests/unit/reports/org_security_posture/test_password_checks.py`
- [X] T015 [P] [US1] Add session policy check tests in `tests/unit/reports/org_security_posture/test_session_checks.py`
- [X] T016 [P] [US1] Add remote shell, packet capture, and stale cleanup check tests in `tests/unit/reports/org_security_posture/test_setting_switch_checks.py`
- [X] T017 [P] [US1] Add representative fixture data in `tests/unit/reports/org_security_posture/fixtures/representative_org_security_posture.py`

### Implementation for User Story 1

- [X] T018 [P] [US1] Implement password policy check classes in `src/reports/org_security_posture/checks/password.py`
- [X] T019 [P] [US1] Implement session policy check classes in `src/reports/org_security_posture/checks/access.py`
- [X] T020 [P] [US1] Implement remote shell, packet capture, and stale cleanup check classes in `src/reports/org_security_posture/checks/access.py`
- [X] T021 [US1] Register all P1 check classes in stable order in `src/reports/org_security_posture/checks/registry.py`
- [X] T022 [US1] Implement checklist evaluation in `src/reports/org_security_posture/runner.py`
- [X] T023 [US1] Implement CSV export to `data/OrgSecurityPosture.csv` in `src/reports/org_security_posture/io/exporter.py`
- [X] T024 [US1] Connect representative fixture data to the test-mode runner path in `src/reports/org_security_posture/runner.py`

**Checkpoint**: User Story 1 is complete when the CSV is produced with stable rows and required columns.

---

## Phase 4: User Story 2 - Understand security posture at a glance (Priority: P2)

**Goal**: The operation prints pass, fail, and review counts that match the CSV rows.

**Independent Test**: Run the runner with fixture rows that contain pass, fail, and review verdicts and confirm the printed counts match the CSV counts.

### Tests for User Story 2

- [X] T025 [P] [US2] Add console summary count tests in `tests/unit/reports/org_security_posture/test_console_summary.py`
- [X] T026 [P] [US2] Add all-pass summary tests in `tests/unit/reports/org_security_posture/test_console_summary.py`

### Implementation for User Story 2

- [X] T027 [US2] Implement pass, fail, and review count aggregation in `src/reports/org_security_posture/runner.py`
- [X] T028 [US2] Implement operator-facing console summary output in `src/reports/org_security_posture/runner.py`
- [X] T029 [US2] Verify exported verdict counts match summary counts in `src/reports/org_security_posture/runner.py`

**Checkpoint**: User Story 2 is complete when the console summary matches the CSV verdict counts.

---

## Phase 5: User Story 3 - Flag uncertain or unsafe API posture (Priority: P3)

**Goal**: Absent API settings become `review`, and non-HTTPS webhook URLs become `fail`.

**Independent Test**: Run API posture fixtures and confirm absent API settings produce `review` with `absent` in the reason, while non-HTTPS webhooks produce `fail`.

### Tests for User Story 3

- [X] T030 [P] [US3] Add absent API setting tests in `tests/unit/reports/org_security_posture/test_api_checks.py`
- [X] T031 [P] [US3] Add non-HTTPS webhook URL failure tests in `tests/unit/reports/org_security_posture/test_api_checks.py`
- [X] T032 [P] [US3] Add API token expiration tests in `tests/unit/reports/org_security_posture/test_api_checks.py`
- [X] T033 [P] [US3] Add API posture fixture data in `tests/unit/reports/org_security_posture/fixtures/api_posture_cases.py`

### Implementation for User Story 3

- [X] T034 [US3] Implement API access, token expiration, and webhook HTTPS check classes in `src/reports/org_security_posture/checks/api.py`
- [X] T035 [US3] Add API source data extraction for tokens, webhooks, administrators, and SSO evidence in `src/reports/org_security_posture/io/sources.py`
- [X] T036 [US3] Register API posture checks in stable order in `src/reports/org_security_posture/checks/registry.py`
- [X] T037 [US3] Ensure absent, unreadable, and ambiguous API values return `review` in `src/reports/org_security_posture/checks/api.py`

**Checkpoint**: User Story 3 is complete when API posture fixtures produce the required `review` and `fail` verdicts.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Validate the feature and prepare it for the later integration pull request.

- [X] T038 [P] Add quickstart validation coverage for `--test` behavior in `tests/unit/reports/org_security_posture/test_quickstart_contract.py`
- [X] T039 [P] Add import and package smoke tests in `tests/unit/reports/org_security_posture/test_package_imports.py`
- [X] T040 Run `python -m py_compile` on `src/reports/org_security_posture/runner.py` and all touched Python files
- [X] T041 Run `python -m ruff check` on `src/reports/org_security_posture/` and `tests/unit/reports/org_security_posture/`
- [X] T042 Run `python -m black --check` on `src/reports/org_security_posture/` and `tests/unit/reports/org_security_posture/`
- [X] T043 Run `python -m pytest tests/unit/reports/org_security_posture/`

---

## Phase 7: Pull Request Pipeline

**Purpose**: Record the constitution-required pipeline steps that happen after local implementation.

**Fleet boundary**: This branch opens a draft pull request. CI, squash merge,
main build verification, revision verification, deployment, and health check
run after reviewer approval and integration wiring.

- [X] T044 Create or update the implementation manifest in `specs/3557-org-security-posture/wiring.md`
- [ ] T045 Stage only owned files with explicit `git add` paths
- [ ] T046 Commit implementation and analysis repair groups with Conventional Commits messages as required by `FLEET_CONTRACT.md`
- [ ] T047 Push branch `feat/3557-org-security-posture` to `origin`
- [ ] T048 Open a draft pull request with `Closes #3557`
- [ ] T049 Run pull request CI and repair branch-owned failures
- [ ] T050 Request review after CI passes
- [ ] T051 Squash merge after approval and required checks
- [ ] T052 Verify the main branch build after merge
- [ ] T053 Verify the released revision that contains menu 276
- [ ] T054 Deploy through the normal release process
- [ ] T055 Complete the post-deploy health check for menu 276 output

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup completion and blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational completion.
- **User Story 2 (Phase 4)**: Depends on User Story 1 because it summarizes generated rows.
- **User Story 3 (Phase 5)**: Depends on Foundational completion and can run in parallel with User Story 1 after shared source data exists.
- **Polish (Phase 6)**: Depends on all selected user stories.

### User Story Dependencies

- **User Story 1 (P1)**: Starts after Foundational. It is the MVP.
- **User Story 2 (P2)**: Starts after User Story 1 creates result rows.
- **User Story 3 (P3)**: Starts after Foundational. It can proceed beside User Story 1 after source extraction exists.

### Within Each User Story

- Write tests before implementation.
- Implement models and helpers before check classes.
- Register checks after check classes exist.
- Export and summarize after result rows exist.
- Validate each story at its checkpoint before the next story changes shared behavior.

---

## Parallel Opportunities

- T002 and T003 can run in parallel after T001 starts.
- T005 and T006 can run in parallel because they test different files.
- T012 through T017 can run in parallel because each test file is separate.
- T018 through T020 can run in parallel because each check module is separate.
- T025 and T026 can run in parallel because they use separate summary cases.
- T030 through T033 can run in parallel because they are independent API posture test cases and fixtures.
- T038 and T039 can run in parallel during polish because they cover different verification surfaces.

## Parallel Example: User Story 1

```text
Task: "Add password policy check tests in tests/unit/reports/org_security_posture/test_password_checks.py"
Task: "Add session policy check tests in tests/unit/reports/org_security_posture/test_session_checks.py"
Task: "Add remote shell, packet capture, and stale cleanup check tests in tests/unit/reports/org_security_posture/test_setting_switch_checks.py"
Task: "Implement password policy check classes in src/reports/org_security_posture/checks/password.py"
Task: "Implement session policy check classes in src/reports/org_security_posture/checks/access.py"
Task: "Implement remote shell, packet capture, and stale cleanup check classes in src/reports/org_security_posture/checks/access.py"
```

## Parallel Example: User Story 3

```text
Task: "Add absent API setting tests in tests/unit/reports/org_security_posture/test_api_checks.py"
Task: "Add non-HTTPS webhook URL failure tests in tests/unit/reports/org_security_posture/test_api_checks.py"
Task: "Add API token expiration tests in tests/unit/reports/org_security_posture/test_api_checks.py"
Task: "Add API posture fixture data in tests/unit/reports/org_security_posture/fixtures/api_posture_cases.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1.
2. Complete Phase 2.
3. Complete Phase 3 for User Story 1.
4. Validate that fixture data writes `data/OrgSecurityPosture.csv`.
5. Stop before menu registration because `MistHelper.py` wiring is deferred to the integration pull request.

### Incremental Delivery

1. Deliver the CSV checklist foundation.
2. Add the console summary.
3. Add API posture edge cases.
4. Run the local gates for touched report and test files.
5. Prepare a separate integration pull request for menu 276 registration and generated references.

### Integration Pull Request Boundary

The integration pull request owns these deferred surfaces:

- `MistHelper.py`
- `src/utils/operation_registry.py`
- `README.md`
- `documentation/menu_reference.md`
- Generated menu reference artifacts

Do not edit these files in the report implementation pull request.
