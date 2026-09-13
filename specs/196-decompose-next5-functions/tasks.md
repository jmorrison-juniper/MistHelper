# Tasks: Decompose Next 5 High-Complexity Functions (Ranks 6-10)

**Input**: Design documents from `specs/196-decompose-next5-functions/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/compatibility-contract.md`, `quickstart.md`

**Tests**: This feature explicitly requires parity and regression validation tasks.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: User story label (`[US1]`, `[US2]`, `[US3]`)

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create feature-local scaffolding for evidence and deterministic parity work.

- [X] T001 Create evidence directory structure for this feature in `specs/196-decompose-next5-functions/evidence/`
- [X] T002 [P] Create verification evidence log template in `specs/196-decompose-next5-functions/evidence/verification-results.md`
- [X] T003 [P] Create function mapping evidence template in `specs/196-decompose-next5-functions/evidence/function-module-test-mapping.md`
- [X] T004 [P] Create safety audit index template in `specs/196-decompose-next5-functions/evidence/safety-audit-index.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish shared baseline and test harness elements required by all stories.

**⚠️ CRITICAL**: No user story implementation begins until this phase is complete.

- [X] T005 Capture pre-refactor baseline complexity output in `specs/196-decompose-next5-functions/evidence/verification-results.md` using `python -m radon.complexity MistHelper.py -s -a`
- [X] T006 Capture pre-refactor `src/` complexity output in `specs/196-decompose-next5-functions/evidence/verification-results.md` using `python -m radon.complexity src -s -a`
- [X] T007 [P] Add shared parity fixtures/utilities for next-5 workflows in `tests/fixtures/next5_parity_baseline.py`
- [X] T008 [P] Add compatibility assertion helpers for prompt/output/side-effect parity in `tests/integration/helpers/compatibility_assertions.py`
- [X] T009 [P] Add complexity assertion helper for CC<=10 evidence parsing in `tests/unit/helpers/test_complexity_thresholds.py`
- [X] T010 Add target list and required owner contracts to mapping evidence in `specs/196-decompose-next5-functions/evidence/function-module-test-mapping.md`
- [X] T011 Confirm contract invariants and verification matrix are copied into execution checklist in `specs/196-decompose-next5-functions/evidence/safety-audit-index.md`

**Checkpoint**: Foundation ready for independently testable user-story work.

---

## Phase 3: User Story 1 - Safer Maintenance of High-Complexity Logic (Priority: P1) 🎯 MVP

**Goal**: Decompose the five target functions into semantic modules/classes with compatibility facades preserved.

**Independent Test**: Run targeted unit + integration parity tests and verify each refactored entrypoint behavior remains equivalent.

### Tests for User Story 1

- [X] T012 [P] [US1] Add unit tests for `_start_site_scan_capture_all_aps` extraction in `tests/unit/test_multi_ap_scan_workflow.py`
- [X] T013 [P] [US1] Add unit tests for `_wait_and_download_pcap` extraction in `tests/unit/test_site_pcap_wait_download.py`
- [X] T014 [P] [US1] Add unit tests for `_wait_and_download_pcap_org` extraction in `tests/unit/test_org_pcap_wait_download.py`
- [X] T015 [P] [US1] Add unit tests for `wifi_clients` extraction in `tests/unit/test_wifi_clients_exporter.py`
- [X] T016 [P] [US1] Add unit tests for `run_interactive_test` extraction in `tests/unit/test_interactive_test_runner.py`
- [X] T017 [US1] Add cross-workflow parity integration tests covering all five targets in `tests/integration/test_next5_compatibility_paths.py`

### Implementation for User Story 1

- [X] T018 [US1] Implement `MultiApScanCaptureWorkflow` for `_start_site_scan_capture_all_aps` in `src/capture/multi_ap_scan_workflow.py`
- [X] T019 [US1] Delegate `_start_site_scan_capture_all_aps` facade to extracted workflow in `MistHelper.py`
- [X] T020 [US1] Implement `SitePcapWaitDownloadWorkflow` for `_wait_and_download_pcap` in `src/capture/site_pcap_wait_download_workflow.py`
- [X] T021 [US1] Delegate `_wait_and_download_pcap` facade to extracted workflow in `MistHelper.py`
- [X] T022 [US1] Implement `OrgPcapWaitDownloadWorkflow` for `_wait_and_download_pcap_org` in `src/capture/org_pcap_wait_download_workflow.py`
- [X] T023 [US1] Delegate `_wait_and_download_pcap_org` facade to extracted workflow in `MistHelper.py`
- [X] T024 [US1] Implement `WifiClientsExporter` for `wifi_clients` in `src/export/wifi_clients_exporter.py`
- [X] T025 [US1] Delegate `wifi_clients` facade to extracted exporter in `MistHelper.py`
- [X] T026 [US1] Implement `InteractiveTestRunner` for `run_interactive_test` in `src/troubleshooting/interactive_test_runner.py`
- [X] T027 [US1] Delegate `run_interactive_test` facade to extracted runner in `MistHelper.py`
- [X] T028 [US1] Update imports/wiring for new extraction modules in `MistHelper.py`
- [X] T029 [US1] Record per-target implementation notes and ownership responsibilities in `specs/196-decompose-next5-functions/evidence/function-module-test-mapping.md`

**Checkpoint**: US1 is complete when all five workflows run through compatibility facades with parity tests passing.

---

## Phase 4: User Story 2 - Reliable Verification and Regression Safety (Priority: P2)

**Goal**: Produce objective, repeatable evidence that complexity and quality gates pass after refactor.

**Independent Test**: Execute VC-001..VC-007 and verify all outcomes are documented with pass/fail results.

### Tests and Evidence for User Story 2

- [X] T030 [US2] Execute VC-001 post-refactor complexity check and append results in `specs/196-decompose-next5-functions/evidence/verification-results.md`
- [X] T031 [US2] Execute VC-002 post-refactor `src/` complexity check and append results in `specs/196-decompose-next5-functions/evidence/verification-results.md`
- [X] T032 [US2] Execute VC-003 syntax gate (`python -m py_compile MistHelper.py`) and append results in `specs/196-decompose-next5-functions/evidence/verification-results.md`
- [X] T033 [US2] Execute VC-004 lint gate (`python -m ruff check MistHelper.py src`) and append results in `specs/196-decompose-next5-functions/evidence/verification-results.md`
- [X] T034 [US2] Execute VC-005 format gate (`python -m black --check MistHelper.py src`) and append results in `specs/196-decompose-next5-functions/evidence/verification-results.md`
- [X] T035 [US2] Execute VC-006 targeted parity tests for all five workflows and append results in `specs/196-decompose-next5-functions/evidence/verification-results.md`
- [X] T036 [US2] Execute VC-007 broader regression evidence run and append results in `specs/196-decompose-next5-functions/evidence/verification-results.md`

### Implementation for User Story 2

- [X] T037 [US2] Add CC<=10 proof table for all five target functions in `specs/196-decompose-next5-functions/evidence/verification-results.md`
- [X] T038 [US2] Add baseline-vs-final complexity comparison narrative in `specs/196-decompose-next5-functions/evidence/verification-results.md`
- [X] T039 [US2] Update full function-to-module-to-tests traceability matrix in `specs/196-decompose-next5-functions/evidence/function-module-test-mapping.md`
- [X] T040 [US2] Add parity coverage summary by target workflow in `specs/196-decompose-next5-functions/evidence/function-module-test-mapping.md`

**Checkpoint**: US2 is complete when VC-001..VC-007 evidence is complete and each target has CC<=10 proof.

---

## Phase 5: User Story 3 - Operationally Safe Refactor Execution (Priority: P3)

**Goal**: Verify safety controls, inline comment compliance, and action logging compliance in all touched blocks.

**Independent Test**: Validate touched blocks and safety-path tests confirm preserved confirmations, safe exits, and equivalent failure handling.

### Tests for User Story 3

- [X] T041 [P] [US3] Add/extend invalid-input and safe-exit tests for `run_interactive_test` in `tests/unit/test_interactive_test_runner.py`
- [X] T042 [P] [US3] Add/extend timeout/failure parity tests for `_wait_and_download_pcap` in `tests/unit/test_site_pcap_wait_download.py`
- [X] T043 [P] [US3] Add/extend timeout/failure parity tests for `_wait_and_download_pcap_org` in `tests/unit/test_org_pcap_wait_download.py`
- [X] T044 [US3] Add integration assertions for confirmation/safety gate preservation in `tests/integration/test_next5_compatibility_paths.py`

### Implementation for User Story 3

- [X] T045 [P] [US3] Create touched-block checklist for `_start_site_scan_capture_all_aps` inline comments and action logging in `specs/196-decompose-next5-functions/evidence/checklists/start_site_scan_capture_all_aps.md`
- [X] T046 [P] [US3] Create touched-block checklist for `_wait_and_download_pcap` inline comments and action logging in `specs/196-decompose-next5-functions/evidence/checklists/wait_and_download_pcap.md`
- [X] T047 [P] [US3] Create touched-block checklist for `_wait_and_download_pcap_org` inline comments and action logging in `specs/196-decompose-next5-functions/evidence/checklists/wait_and_download_pcap_org.md`
- [X] T048 [P] [US3] Create touched-block checklist for `wifi_clients` inline comments and action logging in `specs/196-decompose-next5-functions/evidence/checklists/wifi_clients.md`
- [X] T049 [P] [US3] Create touched-block checklist for `run_interactive_test` inline comments and action logging in `specs/196-decompose-next5-functions/evidence/checklists/run_interactive_test.md`
- [X] T050 [US3] Consolidate checklist verdicts and operational safety controls summary in `specs/196-decompose-next5-functions/evidence/safety-audit-index.md`
- [X] T051 [US3] Record explicit confirmation that touched blocks include pre-action `logging.info`, post-action `logging.debug`, and contextual error logging in `specs/196-decompose-next5-functions/evidence/safety-audit-index.md`

**Checkpoint**: US3 is complete when all checklist artifacts confirm safety, inline comment, and action logging compliance.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finalize docs and run end-to-end validation narrative.

- [X] T052 Update execution walkthrough with final command set and artifact locations in `specs/196-decompose-next5-functions/quickstart.md`
- [X] T053 Add completion summary and reviewer handoff notes in `specs/196-decompose-next5-functions/evidence/verification-results.md`
- [X] T054 Run final end-to-end checklist pass and mark completion readiness in `specs/196-decompose-next5-functions/evidence/safety-audit-index.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies.
- **Phase 2 (Foundational)**: Depends on Phase 1; blocks all user stories.
- **Phase 3 (US1 / P1)**: Depends on Phase 2.
- **Phase 4 (US2 / P2)**: Depends on Phase 3 implementation/tests being available.
- **Phase 5 (US3 / P3)**: Depends on Phase 3 extracted implementations; can run in parallel with late Phase 4 evidence writing once tests exist.
- **Phase 6 (Polish)**: Depends on completion of desired user stories.

### User Story Dependency Graph

- **US1 (P1)** → **US2 (P2)**
- **US1 (P1)** → **US3 (P3)**
- **US2 (P2)** and **US3 (P3)** → **Polish**

### Within Each User Story

- Tests before implementation changes for that target.
- Extracted module/class implementation before `MistHelper.py` facade delegation.
- Evidence updates after command/test execution (no speculative evidence).

## Parallel Opportunities

- Setup templates: `T002`, `T003`, `T004`
- Foundational helpers: `T007`, `T008`, `T009`
- US1 unit test creation: `T012` to `T016`
- US3 safety/failure unit tests: `T041`, `T042`, `T043`
- US3 touched-block checklist files: `T045` to `T049`

---

## Parallel Example: User Story 1

- Execute in parallel: `T012`, `T013`, `T014`, `T015`, `T016`
- Then implement extraction modules in sequence with facade delegation:
  - `_start_site_scan_capture_all_aps`: `T018` → `T019`
  - `_wait_and_download_pcap`: `T020` → `T021`
  - `_wait_and_download_pcap_org`: `T022` → `T023`
  - `wifi_clients`: `T024` → `T025`
  - `run_interactive_test`: `T026` → `T027`

---

## Implementation Strategy

### MVP First (US1 only)

1. Complete Setup + Foundational (`T001`-`T011`)
2. Complete US1 extraction + parity tests (`T012`-`T029`)
3. Validate US1 independently before moving on

### Incremental Delivery

1. Deliver US1 (decomposition + parity)
2. Deliver US2 (verification evidence + CC<=10 proof + quality gates)
3. Deliver US3 (safety controls + inline comments/action logging checklist compliance)
4. Finish with Polish evidence and handoff

### Notes

- All five required target functions have explicit implementation, parity, and evidence tasks.
- CC<=10 proof is required per target, not only aggregate.
- Inline comments and action logging checklist verification is mandatory for every touched target block.
