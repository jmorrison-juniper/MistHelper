# Tasks: Admin Token Hygiene

**Input**: Design documents from `specs/3554-admin-token-hygiene/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`,
`contracts/hygiene-report.md`, and `quickstart.md`

**Tests**: Unit tests are required because the specification requires proof for
each acceptance criterion.

**Organization**: Tasks are grouped by user story to keep each story testable.

## Phase 1: Setup

**Purpose**: Create the owned package and test structure.

- [x] T001 Create `src/mist/intelligence/reports/admin_token_hygiene/__init__.py` with exported package metadata.
- [x] T002 Create `tests/unit/reports/admin_token_hygiene/__init__.py` for the new unit test package.
- [x] T003 Verify `specs/3554-admin-token-hygiene/wiring.md` has the contract sections for menu `273`, registry comments, primary key strategies, category counts, and the import line.

---

## Phase 2: Foundational

**Purpose**: Add shared models and client seams before story work begins.

- [x] T004 [P] Create `src/mist/intelligence/reports/admin_token_hygiene/model.py` with dataclasses for admin rows, token rows, and console summary.
- [x] T005 [P] Create `src/mist/intelligence/reports/admin_token_hygiene/client.py` with the SDK calls for `listOrgAdmins`, `listOrgApiTokens`, and `getOrgSettings`.
- [x] T006 Create `src/mist/intelligence/reports/admin_token_hygiene/operation.py` with `AdminTokenHygieneReport.run()` and the shared session and organization resolver seam.
- [x] T007 [P] Create `tests/unit/reports/admin_token_hygiene/test_admin_token_hygiene_client.py` with fake SDK response coverage.

**Checkpoint**: Foundation ready. User story implementation can start.

---

## Phase 3: User Story 1 - Generate hygiene reports without prompts (P1)

**Goal**: The operation writes both report files and prints a summary without a
prompt in test mode.

**Independent Test**: Run the operation with fake source data and confirm both
CSV files are requested, no prompt is used, and summary counts are produced.

### Tests for User Story 1

- [x] T008 [P] [US1] Add operation export tests in `tests/unit/reports/admin_token_hygiene/test_admin_token_hygiene_operation.py`.
- [x] T009 [P] [US1] Add empty source data header tests in `tests/unit/reports/admin_token_hygiene/test_admin_token_hygiene_operation.py`.

### Implementation for User Story 1

- [x] T010 [US1] Implement CSV row export and summary output in `src/mist/intelligence/reports/admin_token_hygiene/operation.py`.
- [x] T011 [US1] Implement no-prompt test-mode behavior through dependency injection in `src/mist/intelligence/reports/admin_token_hygiene/operation.py`.

**Checkpoint**: User Story 1 works with fake source data.

---

## Phase 4: User Story 2 - Review admin risk findings (P2)

**Goal**: The admin report scores roles, scope, two-factor state, SSO state,
password age, invite expiry, and findings.

**Independent Test**: Feed admin fixtures with Super User, local no-two-factor,
SSO, and expired invite cases into the model and verify rows and summary counts.

### Tests for User Story 2

- [x] T012 [P] [US2] Add admin scoring tests in `tests/unit/reports/admin_token_hygiene/test_admin_token_hygiene_model.py`.
- [x] T013 [P] [US2] Add admin password and invite age tests in `tests/unit/reports/admin_token_hygiene/test_admin_token_hygiene_model.py`.

### Implementation for User Story 2

- [x] T014 [US2] Implement admin role, scope, two-factor, SSO, password age, and invite scoring in `src/mist/intelligence/reports/admin_token_hygiene/model.py`.
- [x] T015 [US2] Add admin summary counting in `src/mist/intelligence/reports/admin_token_hygiene/model.py`.

**Checkpoint**: User Story 2 works from model tests.

---

## Phase 5: User Story 3 - Review token risk findings (P3)

**Goal**: The token report scores idle age, never-used state, write privilege,
source IP restrictions, and token findings without exposing token keys.

**Independent Test**: Feed token fixtures with sentinel keys into the model and
operation tests. Confirm findings, summary counts, and redaction.

### Tests for User Story 3

- [x] T016 [P] [US3] Add token idle and never-used tests in `tests/unit/reports/admin_token_hygiene/test_admin_token_hygiene_model.py`.
- [x] T017 [P] [US3] Add unrestricted write token tests in `tests/unit/reports/admin_token_hygiene/test_admin_token_hygiene_model.py`.
- [x] T018 [P] [US3] Add token key redaction tests in `tests/unit/reports/admin_token_hygiene/test_admin_token_hygiene_redaction.py`.
- [x] T019 [P] [US3] Add `TOKEN_IDLE_DAYS` environment tests in `tests/unit/reports/admin_token_hygiene/test_admin_token_hygiene_model.py`.

### Implementation for User Story 3

- [x] T020 [US3] Implement token scoring and key removal in `src/mist/intelligence/reports/admin_token_hygiene/model.py`.
- [x] T021 [US3] Implement `TOKEN_IDLE_DAYS` parsing in `src/mist/intelligence/reports/admin_token_hygiene/model.py`.
- [x] T022 [US3] Ensure `src/mist/intelligence/reports/admin_token_hygiene/operation.py` logs token counts only and never logs token payloads.

**Checkpoint**: User Story 3 works from model and operation tests.

---

## Phase 6: User Story 4 - Track delivery artifacts (P4)

**Goal**: The wiring manifest and release note fragment exist for review.

**Independent Test**: Confirm `wiring.md` and the release note fragment exist.

### Tests for User Story 4

- [x] T023 [P] [US4] Add artifact existence tests in `tests/unit/reports/admin_token_hygiene/test_admin_token_hygiene_artifacts.py`.

### Implementation for User Story 4

- [x] T024 [US4] Create `changelog.d/issue-3554-admin-token-hygiene.md` with one `### Added` heading and one bullet that names `#3554`.
- [x] T025 [US4] Recheck `specs/3554-admin-token-hygiene/wiring.md` after implementation and keep shared source edits deferred.

**Checkpoint**: User Story 4 artifacts exist.

---

## Phase 7: Deferred Integration Tasks

**Purpose**: Record required shared wiring that this fleet branch must not edit.

- [x] T026 Record the `MistHelper.py` import and menu registration as deferred in `specs/3554-admin-token-hygiene/wiring.md`.
- [x] T027 Record the `src/foundation/support/utils/operation_registry.py` safe category update as deferred in `specs/3554-admin-token-hygiene/wiring.md`.
- [x] T028 Record the `src/foundation/support/refactors/endpoint_primary_key_strategies.py` entries as deferred in `specs/3554-admin-token-hygiene/wiring.md`.
- [x] T029 Record the `README.md`, `.github/copilot-instructions.md`, generated menu reference, and menu API map updates as deferred in `specs/3554-admin-token-hygiene/wiring.md`.

---

## Phase 8: Validation and Analysis Readiness

**Purpose**: Prove the owned implementation before the analysis step.

- [x] T030 Run `C:\Users\jmorrison\mh-fleet\3554-admin-token-hygiene\.venv\Scripts\python.exe -m py_compile` for each new Python file under `src/mist/intelligence/reports/admin_token_hygiene/`.
- [x] T031 Run `C:\Users\jmorrison\mh-fleet\3554-admin-token-hygiene\.venv\Scripts\python.exe -m ruff check src\mist\intelligence\reports\admin_token_hygiene tests\unit\reports\admin_token_hygiene`.
- [x] T032 Run `C:\Users\jmorrison\mh-fleet\3554-admin-token-hygiene\.venv\Scripts\python.exe -m black --check src\mist\intelligence\reports\admin_token_hygiene tests\unit\reports\admin_token_hygiene`.
- [x] T033 Run `C:\Users\jmorrison\mh-fleet\3554-admin-token-hygiene\.venv\Scripts\python.exe -m mypy src\mist\intelligence\reports\admin_token_hygiene --config-file pyproject.toml`.
- [x] T034 Run `C:\Users\jmorrison\mh-fleet\3554-admin-token-hygiene\.venv\Scripts\python.exe -m pydocstyle src\mist\intelligence\reports\admin_token_hygiene`.
- [x] T035 Run `C:\Users\jmorrison\mh-fleet\3554-admin-token-hygiene\.venv\Scripts\python.exe -m pytest tests\unit\reports\admin_token_hygiene -q --timeout=120`.
- [x] T036 Run `C:\Users\jmorrison\mh-fleet\3554-admin-token-hygiene\.venv\Scripts\python.exe -m vulture src\mist\intelligence\reports\admin_token_hygiene --min-confidence 70`.
- [x] T037 Run `C:\Users\jmorrison\mh-fleet\3554-admin-token-hygiene\.venv\Scripts\python.exe -m interrogate -v src\mist\intelligence\reports\admin_token_hygiene`.
- [x] T038 Run the SpecKit analyze step and repair each finding before the final push.

---

## Dependencies and Execution Order

### Phase Dependencies

- Phase 1 has no dependencies.
- Phase 2 depends on Phase 1.
- User Stories 1 through 4 depend on Phase 2.
- Phase 7 can run after `wiring.md` exists.
- Phase 8 depends on all implementation and tests.

### User Story Dependencies

- User Story 1 is the MVP and can run after Phase 2.
- User Story 2 can run after Phase 2 and does not require User Story 1.
- User Story 3 can run after Phase 2 and does not require User Story 2.
- User Story 4 can run after Phase 1.

### Parallel Opportunities

- T004, T005, and T007 can run in parallel.
- T008 and T009 can run in parallel.
- T012 and T013 can run in parallel.
- T016, T017, T018, and T019 can run in parallel.
- T026 through T029 can run in parallel because they update different sections
  of the same manifest only when coordinated by one editor.

## Parallel Example: User Story 3

```text
Task: T016 Add token idle and never-used tests.
Task: T017 Add unrestricted write token tests.
Task: T018 Add token key redaction tests.
Task: T019 Add TOKEN_IDLE_DAYS environment tests.
```

## Implementation Strategy

1. Deliver User Story 1 first to prove report generation.
2. Add admin scoring for User Story 2.
3. Add token scoring and redaction for User Story 3.
4. Add release and wiring artifacts for User Story 4.
5. Run all gates before the analyze step.
