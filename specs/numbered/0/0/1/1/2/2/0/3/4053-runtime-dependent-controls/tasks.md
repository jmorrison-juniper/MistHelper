# Tasks: Runtime-Dependent Portal Controls

**Input**: Design documents from `specs/numbered/0/0/1/1/2/2/0/3/4053-runtime-dependent-controls/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Tests are required by the specification and must fail before implementation.

**Organization**: Tasks are grouped by the user story they verify.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because tasks change different files and have no incomplete dependencies.
- **[Story]**: Maps a task to a user story in spec.md.
- Include exact file paths in each task.
- Tick a task only after verification, then add `(delivered: path/to/file.py)`.

## Phase 1: Setup

**Purpose**: Confirm issue scope and the clean ownership boundary.

- [x] T001 Confirm the current main baseline, merged #4121 repair, and open pull request ownership in `specs/numbered/0/0/1/1/2/2/0/3/4053-runtime-dependent-controls/research.md` (delivered: `specs/numbered/0/0/1/1/2/2/0/3/4053-runtime-dependent-controls/research.md`)

## Phase 2: Foundational

**Purpose**: Preserve the current registry and prompt contract before the story work.

- [x] T002 Record the parameter and prompt-order contract in `specs/numbered/0/0/1/1/2/2/0/3/4053-runtime-dependent-controls/contracts/operations-parameter-controls.md` (delivered: `specs/numbered/0/0/1/1/2/2/0/3/4053-runtime-dependent-controls/contracts/operations-parameter-controls.md`)

## Phase 3: User Story 1 - Filter the manufacturer report (Priority: P1)

**Goal**: Let a browser operator choose an exact manufacturer or leave the field empty to include all manufacturers.

**Independent Test**: A focused E2E test reads the menu 91 parameter response and stable control identifier. Unit tests prove exact-name, numeric, empty, and invalid behavior.

### Tests for User Story 1

- [x] T003 [P] [US1] Add exact-name, numeric, empty, and invalid parser tests in `tests/unit/reports/test_issue_4053_manufacturer_input.py` (delivered: `tests/unit/reports/test_issue_4053_manufacturer_input.py`)
- [x] T004 [P] [US1] Add the menu 91 browser control and stable identifier test in `tests/e2e/web_portal/test_issue_4053_runtime_controls.py` (delivered: `tests/e2e/web_portal/test_issue_4053_runtime_controls.py`)

### Implementation for User Story 1

- [x] T005 [US1] Add the optional manufacturer parameter to `PARAMETER_REGISTRY` in `web_portal/services/operation.py` (delivered: `web_portal/services/operation.py`)
- [x] T006 [US1] Accept exact manufacturer names while preserving numeric selections in `src/mist/intelligence/reports/wired_client_manufacturer_report_generator.py` (delivered: `src/mist/intelligence/reports/wired_client_manufacturer_report_generator.py`)
- [x] T007 [US1] Add stable test IDs and collect prompt-context answers in `web_portal/static/js/operations.js` (delivered: `web_portal/static/js/operations.js`)

**Checkpoint**: Menu 91 accepts an exact manufacturer name, an empty answer, and the existing numeric CLI answer.

## Phase 4: User Story 2 - Audit a selected address file safely (Priority: P1)

**Goal**: Keep menu 195 browser answers aligned with its runtime prompt sequence and stop safely when answers are stale or invalid.

**Independent Test**: Mocked tests cover zero, one, and multiple files, optional prompts, answer validation, post-table quit, and declined write-back.

### Tests for User Story 2

- [x] T008 [P] [US2] Add menu 195 file-choice and write-back refusal tests in `tests/unit/site/address_audit/test_issue_4053_csv_choices.py` (delivered: `tests/unit/site/address_audit/test_issue_4053_csv_choices.py`)
- [x] T009 [P] [US2] Add runtime parameter, stale-answer, prompt-order, and safe-default tests in `tests/unit/web_portal/test_issue_4053_runtime_answers.py` (delivered: `tests/unit/web_portal/test_issue_4053_runtime_answers.py`)
- [x] T010 [P] [US2] Add menu 195 browser parameter and stable identifier tests in `tests/e2e/web_portal/test_issue_4053_runtime_controls.py` (delivered: `tests/e2e/web_portal/test_issue_4053_runtime_controls.py`)
- [x] T011 [US2] Run the tests before implementation and preserve the failing output in `test-artifacts/issue-4053-red-proof.txt` (delivered: `test-artifacts/issue-4053-red-proof.txt`)

### Implementation for User Story 2

- [x] T012 [US2] Add server-side menu 195 controls from current CSV and TSV files in `web_portal/services/operation.py` (delivered: `web_portal/services/operation.py`)
- [x] T013 [US2] Validate prompt contexts and choice values before starting a worker in `web_portal/services/operation.py` (delivered: `web_portal/services/operation.py`)
- [x] T014 [P] [US2] Accept exact file names for browser selections while preserving numeric CLI selections in `src/mist/resources/site/address_audit/audit_engine.py` (delivered: `src/mist/resources/site/address_audit/audit_engine.py`)
- [x] T015 [US2] Scope named browser answers in `InputUtils` and the portal input hook in `src/foundation/support/utils/input_utils.py` and `web_portal/services/input_hook.py` (delivered: `src/foundation/support/utils/input_utils.py`)

**Checkpoint**: Menu 195 uses current file choices, rejects stale forms before execution, and makes no Mist change without explicit approval.

## Phase 5: Polish and Cross-Cutting Concerns

**Purpose**: Record the visible repair, verify the issue criteria, and run applicable gates.

- [ ] T016 [P] Add the issue #4053 release note in `changelog.d/issue-4053-runtime-dependent-controls.md`
- [ ] T017 Run the focused unit and E2E tests from `specs/numbered/0/0/1/1/2/2/0/3/4053-runtime-dependent-controls/quickstart.md`
- [ ] T018 Run applicable Python lint, type, format, symbol, and JavaScript syntax checks for changed files
- [ ] T019 Run the menu 94–96 regression tests and portal guards
- [ ] T020 Analyze the specification, plan, and tasks for consistency with `specs/numbered/0/0/1/1/2/2/0/3/4053-runtime-dependent-controls/`
- [ ] T021 Inspect `.github/PULL_REQUEST_TEMPLATE.md` and `.github/PULL_REQUEST_TEMPLATE/` before creating the pull request
- [ ] T022 Commit and push the verified change with the required co-author trailer
- [ ] T023 Create one pull request for #4053 and #4029, wait for required checks and merge, then confirm both issues close before starting another bug

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Complete. The current main baseline and file ownership are recorded.
- **Foundational (Phase 2)**: Complete. The contract defines the existing parameter endpoint and prompt order.
- **User Stories (Phases 3 and 4)**: Both depend on the foundational contract. Tests must fail before their matching implementation.
- **Polish (Phase 5)**: Depends on both user stories and their focused test runs.

### User Story Dependencies

- **User Story 1 (P1)**: Independent after Phase 2.
- **User Story 2 (P1)**: Independent after Phase 2. It shares `web_portal/services/operation.py` with User Story 1, so combine that file's edits in one implementation task.

### Parallel Opportunities

- T003 and T004 can run in parallel.
- T008, T009, and T010 can run in parallel.
- The US1 and US2 test tasks can run in parallel because they use separate files.
- Do not edit `web_portal/services/operation.py` in parallel across the two stories.

## Parallel Example: User Story 2

```text
Task: Add audit prompt tests in tests/unit/site/address_audit/test_issue_4053_csv_choices.py
Task: Add executor answer-validation tests in tests/unit/web_portal/test_issue_4053_runtime_answers.py
Task: Add browser parameter tests in tests/e2e/web_portal/test_issue_4053_runtime_controls.py
```

## Implementation Strategy

### MVP First

1. Complete the menu 91 parser and browser-control tests.
2. Implement menu 91 and verify its independent test.
3. Add the menu 195 failure proof before changing production code.
4. Implement menu 195 runtime controls and answer validation.
5. Verify both stories and the existing menu 94–96 controls.

### Incremental Delivery

1. Complete User Story 1 and verify it independently.
2. Complete User Story 2 and verify it independently.
3. Run cross-cutting checks, add the release note, and prepare one pull request for #4053 and its parent tracker #4029.

## Notes

- `[P]` marks tasks that edit different files without incomplete dependencies.
- Keep menus 94 through 96 unchanged.
- Keep Mist API access mocked in tests.
- Save the real red-proof output under the ignored `test-artifacts/` directory.
