# Tasks: PSK Hygiene Report

**Input**: Design documents from `specs/3555-psk-hygiene-report/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `quickstart.md`, and `contracts/`

**Tests**: Tests are required by the feature specification and contracts.

**Organization**: Tasks are grouped by commit-ready phases. Commit after each checkpoint.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: The task can run in parallel because it changes a different file or has no dependency on incomplete tasks.
- **[Story]**: The task maps to one user story. Setup, foundational, and polish tasks do not use a story label.
- Include exact file paths in each task.
- Tick a task only after you verify the delivered file.

## Deferred integration pull request edits

These edits are not implementation edits for this feature branch. The integration pull request owns them.

- `MistHelper.py` menu 274 registration is deferred to the integration pull request.
- `src/utils/operation_registry.py` menu 274 entry is deferred to the integration pull request.
- `README.md` menu table and operation count edits are deferred to the integration pull request.
- Generated menu reference edits from `scripts/generate_menu_wiki.py` and `python -m scripts.menu_api_map` are deferred to the integration pull request.
- `src/refactors/endpoint_primary_key_strategies.py` edits are deferred to the integration pull request.

## Phase 1: Setup and traceability

**Purpose**: Create the feature-owned skeleton and release evidence.

- [X] T001 Verify fleet contract sections in specs/3555-psk-hygiene-report/wiring.md
- [X] T002 Create package marker in src/reports/psk_hygiene/__init__.py
- [X] T003 Create test package marker in tests/unit/reports/psk_hygiene/__init__.py
- [X] T004 [P] Add release note fragment in changelog.d/issue-3555-psk-hygiene-report.md

**Commit checkpoint**: Commit Phase 1 after `wiring.md`, package markers, and the release note fragment are verified.

---

## Phase 2: Foundational model and client boundaries

**Purpose**: Build the pure scoring model and the read-only Mist client boundary.

- [X] T005 [P] Add failing model tests for sanitized PSK input in tests/unit/reports/psk_hygiene/test_model.py
- [X] T006 [P] Add failing client tests for paginated PSK, WLAN, and template fetches in tests/unit/reports/psk_hygiene/test_client.py
- [X] T007 Implement dataclasses, SSID normalization, and secret stripping in src/reports/psk_hygiene/model.py
- [X] T008 Implement expire-time parsing and days remaining calculation in src/reports/psk_hygiene/model.py
- [X] T009 Implement read-only mistapi client pagination in src/reports/psk_hygiene/client.py
- [X] T010 Verify no model import references mistapi, DataExporter, ConfigUtils, or SourceDependencyResolver in src/reports/psk_hygiene/model.py

**Commit checkpoint**: Commit Phase 2 after the model and client tests pass.

---

## Phase 3: User Story 1 - Run PSK hygiene report without prompts (Priority: P1) MVP

**Goal**: The operator can run the report without prompts and receive one row per PSK.

**Independent Test**: Run unit tests for `PskHygieneReport.run()` with fake dependencies. Confirm no prompt call occurs and export receives sanitized rows.

### Tests for User Story 1

- [X] T011 [P] [US1] Add no-prompt operation test in tests/unit/reports/psk_hygiene/test_operation.py
- [X] T012 [P] [US1] Add export contract test for required PskHygiene columns in tests/unit/reports/psk_hygiene/test_operation.py
- [X] T013 [P] [US1] Add output-row secret redaction test for passphrase and old_passphrase in tests/unit/reports/psk_hygiene/test_model.py

### Implementation for User Story 1

- [X] T014 [US1] Implement PskHygieneReport.run orchestration in src/reports/psk_hygiene/operation.py
- [X] T015 [US1] Connect PskHygieneReport.run to DataExporter.write_with_format_selection in src/reports/psk_hygiene/operation.py
- [X] T016 [US1] Return a menu-test success value from PskHygieneReport.run in src/reports/psk_hygiene/operation.py

**Commit checkpoint**: Commit Phase 3 after the P1 tests pass with fake dependencies.

---

## Phase 4: User Story 2 - See clear findings for risky PSKs (Priority: P2)

**Goal**: The report labels each risky PSK without exposing secrets.

**Independent Test**: Run model tests with controlled PSK, WLAN, and template data. Confirm each expected finding label appears.

### Tests for User Story 2

- [X] T017 [P] [US2] Add expired finding test in tests/unit/reports/psk_hygiene/test_model.py
- [X] T018 [P] [US2] Add expires_soon finding test for an expiring_soon PSK in tests/unit/reports/psk_hygiene/test_model.py
- [X] T019 [P] [US2] Add uncapped_multi_use finding test in tests/unit/reports/psk_hygiene/test_model.py
- [X] T020 [P] [US2] Add rotation_pending finding test in tests/unit/reports/psk_hygiene/test_model.py
- [X] T021 [P] [US2] Add orphan_ssid finding test in tests/unit/reports/psk_hygiene/test_model.py
- [X] T022 [P] [US2] Add template WLAN matching test in tests/unit/reports/psk_hygiene/test_model.py
- [X] T023 [P] [US2] Add log and console secret redaction test in tests/unit/reports/psk_hygiene/test_operation.py

### Implementation for User Story 2

- [X] T024 [US2] Implement stable finding order in src/reports/psk_hygiene/model.py
- [X] T025 [US2] Implement uncapped multi-use detection in src/reports/psk_hygiene/model.py
- [X] T026 [US2] Implement rotation pending detection with old_passphrase_present only in src/reports/psk_hygiene/model.py
- [X] T027 [US2] Implement organization WLAN and template SSID matching in src/reports/psk_hygiene/model.py
- [X] T028 [US2] Implement unknown WLAN scope handling in src/reports/psk_hygiene/model.py

**Commit checkpoint**: Commit Phase 4 after the P2 tests prove all finding labels and secret redaction.

---

## Phase 5: User Story 3 - Read a console summary of hygiene risk (Priority: P3)

**Goal**: The operator sees summary counts that match the report rows.

**Independent Test**: Run operation tests with known rows. Confirm console summary counts match the findings.

### Tests for User Story 3

- [X] T029 [P] [US3] Add summary counts test for all findings in tests/unit/reports/psk_hygiene/test_model.py
- [X] T030 [P] [US3] Add zero-finding summary test in tests/unit/reports/psk_hygiene/test_model.py
- [X] T031 [P] [US3] Add console summary secret redaction test in tests/unit/reports/psk_hygiene/test_operation.py

### Implementation for User Story 3

- [X] T032 [US3] Implement HygieneSummary aggregation in src/reports/psk_hygiene/model.py
- [X] T033 [US3] Print sanitized summary counts in src/reports/psk_hygiene/operation.py
- [X] T034 [US3] Log sanitized summary counts only in src/reports/psk_hygiene/operation.py
- [X] T035 [US3] State that site-level WLANs are outside scope in src/reports/psk_hygiene/operation.py

**Commit checkpoint**: Commit Phase 5 after the P3 summary tests pass.

---

## Phase 6: User Story 4 - Verify release and wiring evidence (Priority: P4)

**Goal**: A reviewer can verify traceability and release evidence before the implementation is accepted.

**Independent Test**: Confirm the wiring manifest and release note fragment exist and contain issue #3555 evidence.

### Tests for User Story 4

- [X] T036 [P] [US4] Add traceability artifact test for specs/3555-psk-hygiene-report/wiring.md in tests/unit/reports/psk_hygiene/test_traceability.py
- [X] T037 [P] [US4] Add release fragment existence test for changelog.d/issue-3555-psk-hygiene-report.md in tests/unit/reports/psk_hygiene/test_traceability.py

### Implementation for User Story 4

- [X] T038 [US4] Update issue #3555 evidence in specs/3555-psk-hygiene-report/wiring.md
- [X] T039 [US4] Write Added release note for PSK hygiene report in changelog.d/issue-3555-psk-hygiene-report.md

**Commit checkpoint**: Commit Phase 6 after traceability tests pass.

---

## Phase 7: Polish and local validation

**Purpose**: Run the smallest gates that prove the feature branch.

- [X] T040 Run pytest for feature tests with python -m pytest tests\unit\reports\psk_hygiene
- [X] T041 Run syntax validation with python -m py_compile MistHelper.py
- [X] T042 Run Ruff validation with python -m ruff check MistHelper.py src\reports\psk_hygiene tests\unit\reports\psk_hygiene
- [X] T043 Run Black validation with python -m black --check MistHelper.py src\reports\psk_hygiene tests\unit\reports\psk_hygiene
- [X] T044 Record local validation evidence in specs/3555-psk-hygiene-report/wiring.md

**Commit checkpoint**: Commit Phase 7 after all local validation commands pass.

---

## Dependencies and execution order

### Phase dependencies

- **Phase 1** has no dependencies.
- **Phase 2** depends on Phase 1.
- **Phase 3** depends on Phase 2 and delivers the MVP.
- **Phase 4** depends on Phase 2 and can start after model boundaries exist.
- **Phase 5** depends on Phase 4 because summary counts read finding labels.
- **Phase 6** depends on Phase 1 and can run when release evidence is ready.
- **Phase 7** depends on the selected implementation phases.

### User story dependencies

- **User Story 1 (P1)** can start after Phase 2.
- **User Story 2 (P2)** can start after Phase 2.
- **User Story 3 (P3)** depends on User Story 2 finding labels.
- **User Story 4 (P4)** can start after Phase 1.

### Parallel opportunities

- T004 can run in parallel with T002 and T003.
- T005 and T006 can run in parallel.
- T011, T012, and T013 can run in parallel.
- T017 through T023 can run in parallel.
- T029 through T031 can run in parallel.
- T036 and T037 can run in parallel.

## Parallel example: User Story 2

```text
Task: "T017 [P] [US2] Add expired finding test in tests/unit/reports/psk_hygiene/test_model.py"
Task: "T018 [P] [US2] Add expires_soon finding test for an expiring_soon PSK in tests/unit/reports/psk_hygiene/test_model.py"
Task: "T019 [P] [US2] Add uncapped_multi_use finding test in tests/unit/reports/psk_hygiene/test_model.py"
Task: "T020 [P] [US2] Add rotation_pending finding test in tests/unit/reports/psk_hygiene/test_model.py"
Task: "T021 [P] [US2] Add orphan_ssid finding test in tests/unit/reports/psk_hygiene/test_model.py"
Task: "T022 [P] [US2] Add template WLAN matching test in tests/unit/reports/psk_hygiene/test_model.py"
Task: "T023 [P] [US2] Add log and console secret redaction test in tests/unit/reports/psk_hygiene/test_operation.py"
```

## Implementation strategy

### MVP first

1. Complete Phase 1.
2. Complete Phase 2.
3. Complete Phase 3.
4. Stop and validate User Story 1 independently.
5. Commit the MVP group before User Story 2 begins.

### Incremental delivery

1. Add User Story 2 finding tests and implementation.
2. Validate User Story 2 independently.
3. Add User Story 3 summary tests and implementation.
4. Validate User Story 3 independently.
5. Add User Story 4 release and wiring evidence.
6. Run Phase 7 local validation.

### Integration pull request boundary

The integration pull request must register menu 274, update the registry, update README, generate menu references, and decide any endpoint primary key strategy entry. This feature branch must keep those edits out of its implementation file set.
