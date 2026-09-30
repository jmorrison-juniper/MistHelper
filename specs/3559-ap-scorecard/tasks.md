# Tasks: Organization Access Point Scorecard

**Input**: Design documents from `specs/3559-ap-scorecard/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/export-contract.md`, and `wiring.md`

**Tests**: The feature specification requires tests for every acceptance criterion. Write the tests first. Confirm that they fail before implementation.

**Organization**: Tasks are grouped by user story so each story can be implemented and tested independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: The task can run in parallel because it touches different files and has no dependency on an incomplete task.
- **[Story]**: The story label maps to `spec.md`.
- Each task names the exact path that it changes or verifies.
- Tick a task only after you verify the delivered file. Add an evidence note in this form: `(delivered: path/to/file.py)`.

## Deferred to the integration pull request

Do not change the shared files below in this feature implementation. Record their exact changes in `specs/3559-ap-scorecard/wiring.md`.

| Shared file or surface | Deferred work |
| - | - |
| `MistHelper.py` | Register menu `278` and import `ApScorecard`. |
| `src/utils/operation_registry.py` | Register menu `278` as a `safe` operation. |
| `src/refactors/endpoint_primary_key_strategies.py` | Add the two AP scorecard primary key strategies. |
| `README.md` | Add the new menu operation to the user documentation. |
| `documentation/menu_reference.md` and `documentation/wiki/**` | Regenerate the generated menu documentation. |
| `.github/copilot-instructions.md` and `agents.md` | Update category counts or instructions only in the integration pull request. |

---

## Phase 1: Setup

**Purpose**: Prepare the package, test package, and support file placeholders.

- [X] T001 Create the AP scorecard package directory with `src/reports/ap_scorecard/__init__.py`
- [X] T002 Create the AP scorecard test package directory with `tests/unit/reports/ap_scorecard/__init__.py`
- [X] T003 [P] Create shared pytest fixtures for AP statistics payloads in `tests/unit/reports/ap_scorecard/conftest.py`
- [X] T004 [P] Verify the integration wiring manifest contains every fleet contract section in `specs/3559-ap-scorecard/wiring.md`

---

## Phase 2: Foundational

**Purpose**: Create the shared seams that all stories need.

**Critical**: No user story work can start until this phase is complete.

- [X] T005 Create scorecard dataclasses and constants in `src/reports/ap_scorecard/model.py`
- [X] T006 [P] Create the Mist AP statistics client class in `src/reports/ap_scorecard/client.py`
- [X] T007 [P] Create the operation orchestrator class `ApScorecard` in `src/reports/ap_scorecard/operation.py`
- [X] T008 Add logging and inline comments to all new executable lines in `src/reports/ap_scorecard/model.py`
- [X] T009 Add logging and inline comments to all new executable lines in `src/reports/ap_scorecard/client.py`
- [X] T010 Add logging and inline comments to all new executable lines in `src/reports/ap_scorecard/operation.py`

**Checkpoint**: The feature has a package, a client seam, model objects, and an operation class.

---

## Phase 3: User Story 1 - Export AP scorecard detail (Priority: P1)

**Goal**: Write `data/ApScorecard.csv` with one row for each AP in the organization payload.

**Independent Test**: Run the unit tests for detail rows with no network. Confirm one row per AP, required columns, VLAN failures, and empty LLDP power fields.

### Tests for User Story 1

- [X] T011 [P] [US1] Add a client test that proves `listOrgDevicesStats` is called with `type="ap"` and `limit=1000` in `tests/unit/reports/ap_scorecard/test_ap_scorecard_client.py`
- [X] T012 [P] [US1] Add a client test that proves the existing pagination seam is used in `tests/unit/reports/ap_scorecard/test_ap_scorecard_client.py`
- [X] T013 [P] [US1] Add a detail export test that proves one `ApScorecard.csv` row is created for each AP in `tests/unit/reports/ap_scorecard/test_ap_scorecard_model.py`
- [X] T014 [P] [US1] Add a detail column test for all required `ApScorecard.csv` fields in `tests/unit/reports/ap_scorecard/test_ap_scorecard_model.py`
- [X] T015 [P] [US1] Add a VLAN failure test for non-empty `inactive_wired_vlans` in `tests/unit/reports/ap_scorecard/test_ap_scorecard_model.py`
- [X] T016 [P] [US1] Add a missing `lldp_stat` test that expects empty LLDP power values and no exception in `tests/unit/reports/ap_scorecard/test_ap_scorecard_model.py`

### Implementation for User Story 1

- [X] T017 [US1] Implement AP statistics fetch and response normalization in `src/reports/ap_scorecard/client.py`
- [X] T018 [US1] Implement predominant version calculation per model in `src/reports/ap_scorecard/model.py`
- [X] T019 [US1] Implement AP detail row creation for `ApScorecard.csv` in `src/reports/ap_scorecard/model.py`
- [X] T020 [US1] Implement detail export through `DataExporter.write_with_format_selection()` in `src/reports/ap_scorecard/operation.py`

**Checkpoint**: User Story 1 can create AP detail rows and export `ApScorecard.csv`.

---

## Phase 4: User Story 2 - Summarize AP health by site (Priority: P1)

**Goal**: Write `data/ApScorecardBySite.csv` with tile percentages, color bands, and redundancy counts per site.

**Independent Test**: Run the unit tests for site summaries. Confirm each site has one row and all color threshold boundaries pass.

### Tests for User Story 2

- [X] T021 [P] [US2] Add color band boundary tests for `98.5`, a value between `80` and `98.5`, and `80` in `tests/unit/reports/ap_scorecard/test_ap_scorecard_model.py`
- [X] T022 [P] [US2] Add a multi-site summary test that proves one `ApScorecardBySite.csv` row per site in `tests/unit/reports/ap_scorecard/test_ap_scorecard_model.py`
- [X] T023 [P] [US2] Add a redundancy classification test for values `1`, `2`, and `3` or more in `tests/unit/reports/ap_scorecard/test_ap_scorecard_model.py`
- [X] T024 [P] [US2] Add a site redundancy count test for none, good, and excellent counts in `tests/unit/reports/ap_scorecard/test_ap_scorecard_model.py`
- [X] T025 [P] [US2] Add a site summary column test for all five tile percentages and bands in `tests/unit/reports/ap_scorecard/test_ap_scorecard_model.py`

### Implementation for User Story 2

- [X] T026 [US2] Implement tile color band calculation with AP thresholds in `src/reports/ap_scorecard/model.py`
- [X] T027 [US2] Implement switch redundancy normalization and classification in `src/reports/ap_scorecard/model.py`
- [X] T028 [US2] Implement site scorecard aggregation in `src/reports/ap_scorecard/model.py`
- [X] T029 [US2] Implement site summary export through `DataExporter.write_with_format_selection()` in `src/reports/ap_scorecard/operation.py`

**Checkpoint**: User Stories 1 and 2 can create both CSV exports without menu wiring.

---

## Phase 5: User Story 3 - See organization-wide AP health (Priority: P2)

**Goal**: Print organization-wide tile percentages after the exports finish.

**Independent Test**: Run the operation unit tests with a known payload. Confirm the console output includes all five organization-wide percentages.

### Tests for User Story 3

- [X] T030 [P] [US3] Add an organization summary calculation test for all five tile percentages in `tests/unit/reports/ap_scorecard/test_ap_scorecard_model.py`
- [X] T031 [P] [US3] Add a console summary test for all five tile names in `tests/unit/reports/ap_scorecard/test_ap_scorecard_operation.py`
- [X] T032 [P] [US3] Add a test-safe operation test that proves no direct prompt occurs and both output file names are used in `tests/unit/reports/ap_scorecard/test_ap_scorecard_operation.py`
- [X] T033 [P] [US3] Add a no-AP payload test that expects a clear log message and no misleading success summary in `tests/unit/reports/ap_scorecard/test_ap_scorecard_operation.py`

### Implementation for User Story 3

- [X] T034 [US3] Implement organization summary aggregation in `src/reports/ap_scorecard/model.py`
- [X] T035 [US3] Implement console summary printing in `src/reports/ap_scorecard/operation.py`
- [X] T036 [US3] Implement no-AP handling with a clear log message in `src/reports/ap_scorecard/operation.py`

**Checkpoint**: User Stories 1, 2, and 3 can run through the operation class with no live Mist API call in tests.

---

## Phase 6: User Story 4 - Prepare integration evidence (Priority: P3)

**Goal**: Provide the wiring manifest and release note fragment required for the integration pull request.

**Independent Test**: Confirm `wiring.md` contains every contract section. Confirm the release note fragment contains one `### Added` heading and one issue `#3559` bullet.

### Tests for User Story 4

- [X] T037 [P] [US4] Add a support file test for every required `wiring.md` section in `tests/unit/reports/ap_scorecard/test_ap_scorecard_support_files.py`
- [X] T038 [P] [US4] Add a release note fragment test for one `### Added` heading and one `#3559` bullet in `tests/unit/reports/ap_scorecard/test_ap_scorecard_support_files.py`

### Implementation for User Story 4

- [X] T039 [US4] Update the integration manifest if a required section is missing in `specs/3559-ap-scorecard/wiring.md`
- [X] T040 [US4] Create the release note fragment in `changelog.d/issue-3559-ap-scorecard.md`

**Checkpoint**: The support evidence exists, and shared file edits remain deferred.

---

## Phase 7: Polish and validation

**Purpose**: Validate the feature-owned files and keep shared changes deferred.

- [X] T041 [P] Run `C:\Users\jmorrison\mh-fleet\3559-ap-scorecard\.venv\Scripts\python.exe -m py_compile src\reports\ap_scorecard\__init__.py src\reports\ap_scorecard\client.py src\reports\ap_scorecard\model.py src\reports\ap_scorecard\operation.py`
- [X] T042 [P] Run `C:\Users\jmorrison\mh-fleet\3559-ap-scorecard\.venv\Scripts\python.exe -m ruff check src\reports\ap_scorecard tests\unit\reports\ap_scorecard`
- [X] T043 [P] Run `C:\Users\jmorrison\mh-fleet\3559-ap-scorecard\.venv\Scripts\python.exe -m black --check src\reports\ap_scorecard tests\unit\reports\ap_scorecard`
- [X] T044 [P] Run `C:\Users\jmorrison\mh-fleet\3559-ap-scorecard\.venv\Scripts\python.exe -m mypy src\reports\ap_scorecard --config-file pyproject.toml`
- [X] T045 [P] Run `C:\Users\jmorrison\mh-fleet\3559-ap-scorecard\.venv\Scripts\python.exe -m pydocstyle src\reports\ap_scorecard`
- [X] T046 [P] Run `C:\Users\jmorrison\mh-fleet\3559-ap-scorecard\.venv\Scripts\python.exe -m pytest tests\unit\reports\ap_scorecard -q --timeout=120`
- [X] T047 [P] Run `C:\Users\jmorrison\mh-fleet\3559-ap-scorecard\.venv\Scripts\python.exe -m vulture src\reports\ap_scorecard --min-confidence 70`
- [X] T048 [P] Run `C:\Users\jmorrison\mh-fleet\3559-ap-scorecard\.venv\Scripts\python.exe -m interrogate -v src\reports\ap_scorecard`
- [X] T049 Verify that `MistHelper.py`, `src/utils/operation_registry.py`, `src/refactors/endpoint_primary_key_strategies.py`, `README.md`, generated docs, and copilot instructions changed only through `specs/3559-ap-scorecard/wiring.md`
- [X] T050 [P] Run `C:\Users\jmorrison\mh-fleet\3559-ap-scorecard\.venv\Scripts\python.exe -m radon cc src\reports\ap_scorecard -j | C:\Users\jmorrison\mh-fleet\3559-ap-scorecard\.venv\Scripts\complexity-gate.exe --max 10`
- [X] T051 [P] Run `C:\Users\jmorrison\mh-fleet\3559-ap-scorecard\.venv\Scripts\test-quality-analyzer.exe --gate --config .github\test-quality-config.toml --baseline .github\test-quality-baseline.json --changed-from origin/main`

---

## Dependencies and execution order

### Phase dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Phase 1.
- **User Story 1 (Phase 3)**: Depends on Phase 2.
- **User Story 2 (Phase 4)**: Depends on Phase 2, but it uses AP detail row semantics from User Story 1.
- **User Story 3 (Phase 5)**: Depends on User Stories 1 and 2.
- **User Story 4 (Phase 6)**: Depends on Phase 1 and can run beside the model work.
- **Polish and validation (Phase 7)**: Depends on all selected user stories.

### User story dependencies

- **User Story 1 (P1)**: Start after Foundational. It is required for the MVP.
- **User Story 2 (P1)**: Start after Foundational. It is required for the MVP.
- **User Story 3 (P2)**: Start after User Stories 1 and 2.
- **User Story 4 (P3)**: Start after Setup. It prepares integration evidence.

### Acceptance criteria coverage

| Acceptance criterion | Test tasks |
| - | - |
| `--test` runs with no prompt and writes both files under `data/` | T032 proves the feature-owned no-prompt and export-name seam. The final `MistHelper.py --test` and `data/` path proof is deferred to the integration pull request because menu `278` registration is deferred in `wiring.md`. |
| Color band uses `98.5%` for green and `80%` for red | T021 |
| Redundancy values `1`, `2`, and `3` or more map to all categories | T023, T024 |
| Non-empty `inactive_wired_vlans` fails the VLAN tile and lists IDs | T015 |
| Missing `lldp_stat` leaves empty power columns and does not fail | T016 |
| `wiring.md` exists with every contract section | T037, T039 |
| Release note fragment exists with the issue entry | T038, T040 |
| Detail export creates one row for each AP and all required columns | T013, T014 |
| Site export creates one row per site and all tile fields | T022, T025 |
| Console summary reports all five organization-wide percentages | T030, T031 |

---

## Parallel execution examples

### User Story 1

```text
Task: "T011 Add a client test that proves listOrgDevicesStats is called with type=\"ap\" and limit=1000 in tests/unit/reports/ap_scorecard/test_ap_scorecard_client.py"
Task: "T013 Add a detail export test that proves one ApScorecard.csv row is created for each AP in tests/unit/reports/ap_scorecard/test_ap_scorecard_model.py"
Task: "T016 Add a missing lldp_stat test that expects empty LLDP power values and no exception in tests/unit/reports/ap_scorecard/test_ap_scorecard_model.py"
```

### User Story 2

```text
Task: "T021 Add color band boundary tests for 98.5, a value between 80 and 98.5, and 80 in tests/unit/reports/ap_scorecard/test_ap_scorecard_model.py"
Task: "T023 Add a redundancy classification test for values 1, 2, and 3 or more in tests/unit/reports/ap_scorecard/test_ap_scorecard_model.py"
Task: "T025 Add a site summary column test for all five tile percentages and bands in tests/unit/reports/ap_scorecard/test_ap_scorecard_model.py"
```

### User Story 3

```text
Task: "T030 Add an organization summary calculation test for all five tile percentages in tests/unit/reports/ap_scorecard/test_ap_scorecard_model.py"
Task: "T031 Add a console summary test for all five tile names in tests/unit/reports/ap_scorecard/test_ap_scorecard_operation.py"
Task: "T033 Add a no-AP payload test that expects a clear log message and no misleading success summary in tests/unit/reports/ap_scorecard/test_ap_scorecard_operation.py"
```

### User Story 4

```text
Task: "T037 Add a support file test for every required wiring.md section in tests/unit/reports/ap_scorecard/test_ap_scorecard_support_files.py"
Task: "T038 Add a release note fragment test for one ### Added heading and one #3559 bullet in tests/unit/reports/ap_scorecard/test_ap_scorecard_support_files.py"
```

---

## Implementation strategy

### MVP first

1. Complete Phase 1.
2. Complete Phase 2.
3. Complete User Story 1.
4. Complete User Story 2.
5. Validate that both CSV outputs can be produced from fixture data.

### Incremental delivery

1. Deliver the AP detail export.
2. Deliver the site summary export.
3. Add the console summary.
4. Add the support evidence and release note fragment.
5. Run all validation gates.

### Parallel team strategy

1. One engineer builds `client.py` and `test_ap_scorecard_client.py`.
2. One engineer builds `model.py` and `test_ap_scorecard_model.py`.
3. One engineer builds `operation.py` and `test_ap_scorecard_operation.py`.
4. One engineer verifies `wiring.md`, the release note fragment, and support file tests.

---

## Notes

- The handler must be `ApScorecard.run()` and must take no positional arguments.
- The implementation must use `listOrgDevicesStats` with `type="ap"`.
- The implementation must not add a custom pagination loop.
- The implementation must use `DataExporter.write_with_format_selection()` for both exports.
- The implementation must not edit shared integration files outside `specs/3559-ap-scorecard/wiring.md`.
