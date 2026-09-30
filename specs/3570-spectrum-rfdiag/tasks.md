# Tasks: Spectrum RF Diagnostics

**Input**: Design documents from `specs/3570-spectrum-rfdiag/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/rf-diagnostics.md`, `quickstart.md`, `wiring.md`

**Tests**: Tests are required by the specification. Write the test tasks before implementation tasks and confirm they fail for the missing feature.

**Organization**: Tasks are grouped by user story. Each story can be implemented and tested on its own after the setup and foundation phases.

**Scope note**: This task plan describes later implementation work. This tasks phase edits only files under `specs/3570-spectrum-rfdiag`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches a different file or has no dependency on unfinished work.
- **[Story]**: User story label for story phases only.
- Each task includes an exact file path.
- Keep each task unchecked until the named file is verified.

---

## Phase 1: Setup

**Purpose**: Create the package, test package, release note placeholder, and deferred wiring evidence.

### Client group

- [ ] T001 Create RF diagnostics package directory and public export scaffold in src/troubleshooting/rf_diagnostics/__init__.py
- [ ] T002 [P] Create RF diagnostics client module scaffold in src/troubleshooting/rf_diagnostics/client.py

### Model group

- [ ] T003 [P] Create RF diagnostics model module scaffold in src/troubleshooting/rf_diagnostics/models.py

### Operation group

- [ ] T004 [P] Create operation module scaffold in src/troubleshooting/rf_diagnostics/operation.py
- [ ] T005 [P] Create spectrum module scaffold in src/troubleshooting/rf_diagnostics/spectrum.py
- [ ] T006 [P] Create recording module scaffold in src/troubleshooting/rf_diagnostics/recording.py

### Release note group

- [ ] T007 [P] Create issue 3570 release note fragment in changelog.d/issue-3570-spectrum-rfdiag.md

### Validation group

- [ ] T008 [P] Create RF diagnostics unit test package marker in tests/unit/troubleshooting/rf_diagnostics/__init__.py
- [ ] T009 [P] Update specs/3570-spectrum-rfdiag/wiring.md to state that MistHelper.py registration, operation_registry.py registration, endpoint_primary_key_strategies.py registration, README, generated menu reference, and copilot-instructions category updates are deferred to the integration pull request and documented in wiring.md

---

## Phase 2: Foundational

**Purpose**: Build shared code that all stories need. No user story can start until this phase is complete.

### Model group

- [ ] T010 [P] Define RfDiagnosticRun, SpectrumAnalysisSession, RfDiagnosticRecording, RfDiagnosticFile, and status constants in src/troubleshooting/rf_diagnostics/models.py
- [ ] T011 [P] Implement safe site, AP, client MAC, and timestamp file-name token helpers in src/troubleshooting/rf_diagnostics/file_naming.py

### Client group

- [ ] T012 Implement RfDiagnosticsClient constructor with injected Mist session, SDK callables, and logging in src/troubleshooting/rf_diagnostics/client.py
- [ ] T013 Add spectrum start, spectrum state, recording start, recording stop, recording download, and recording get methods in src/troubleshooting/rf_diagnostics/client.py

### Operation group

- [ ] T014 [P] Implement audit CSV writer with one-row append behavior in src/troubleshooting/rf_diagnostics/audit.py
- [ ] T015 Implement shared confirmation, cancellation, safe prompt, and ASCII output helpers in src/troubleshooting/rf_diagnostics/operation.py

### Tests group

- [ ] T016 [P] Add model and file-name helper tests in tests/unit/troubleshooting/rf_diagnostics/test_file_naming.py
- [ ] T017 [P] Add RF diagnostics client request-shape tests in tests/unit/troubleshooting/rf_diagnostics/test_client_requests.py
- [ ] T018 [P] Add audit CSV writer tests in tests/unit/troubleshooting/rf_diagnostics/test_audit.py

**Checkpoint**: Foundation is ready when the shared model, client, prompt, file-name, and audit tests fail for the missing behavior or pass after implementation.

---

## Phase 3: User Story 1 - Run AP spectrum analysis (Priority: P1) MVP

**Goal**: The operator can choose spectrum mode, select a site and AP, confirm, start analysis, poll state, print the result, and record one audit row.

**Independent Test**: Use fake site, AP, safe input, client, clock, and audit dependencies. Confirm the operation starts only after `y`, polls until final state, prints a clear result, and writes one row.

### Tests group

- [ ] T019 [P] [US1] Add spectrum success, decline, poll-running, poll-timeout, and failure tests in tests/unit/troubleshooting/rf_diagnostics/test_spectrum_flow.py
- [ ] T020 [P] [US1] Add spectrum start body and body-free state call assertions in tests/unit/troubleshooting/rf_diagnostics/test_client_requests.py

### Operation group

- [ ] T021 [US1] Implement SpectrumAnalysisRunner start, bounded polling, final result, timeout, and failure handling in src/troubleshooting/rf_diagnostics/spectrum.py
- [ ] T022 [US1] Connect spectrum mode selection, site selection, AP selection, confirmation, runner call, output, and audit write in src/troubleshooting/rf_diagnostics/operation.py

### Validation group

- [ ] T023 [US1] Run pytest for spectrum flow and client request tests with python -m pytest tests/unit/troubleshooting/rf_diagnostics/test_spectrum_flow.py tests/unit/troubleshooting/rf_diagnostics/test_client_requests.py -q

**Checkpoint**: User Story 1 is complete when the spectrum path works without recording mode and writes one audit row per attempt.

---

## Phase 4: User Story 2 - Record client RF diagnostics (Priority: P1)

**Goal**: The operator can choose recording mode, select a site and client MAC, confirm, wait, stop, download a file under `data/rfdiags/`, print the path, and record one audit row.

**Independent Test**: Use fake site, client MAC, wait, interrupt, file system, client, clock, and audit dependencies. Confirm start requires `y`, Ctrl+C triggers stop, download saves under `data/rfdiags/`, and decline does not call remote actions.

### Tests group

- [ ] T024 [P] [US2] Add recording success, decline, Ctrl+C stop, stop failure, download failure, and empty download tests in tests/unit/troubleshooting/rf_diagnostics/test_recording_flow.py
- [ ] T025 [P] [US2] Add recording start, stop, download, and normalized MAC request assertions in tests/unit/troubleshooting/rf_diagnostics/test_client_requests.py

### Operation group

- [ ] T026 [US2] Implement RfDiagnosticRecordingRunner start, wait, interrupt stop, stop failure, download, and output handling in src/troubleshooting/rf_diagnostics/recording.py
- [ ] T027 [US2] Connect recording mode selection, site selection, client MAC prompt, duration or operator wait, confirmation, runner call, output, and audit write in src/troubleshooting/rf_diagnostics/operation.py

### Validation group

- [ ] T028 [US2] Run pytest for recording flow, file naming, and client request tests with python -m pytest tests/unit/troubleshooting/rf_diagnostics/test_recording_flow.py tests/unit/troubleshooting/rf_diagnostics/test_file_naming.py tests/unit/troubleshooting/rf_diagnostics/test_client_requests.py -q

**Checkpoint**: User Story 2 is complete when recording mode works without spectrum mode and handles normal waits, interrupts, and failed downloads safely.

---

## Phase 5: User Story 3 - Keep a run audit trail (Priority: P2)

**Goal**: Every spectrum, recording, cancelled, and failed attempt writes exactly one row in `data/RfDiagnostics.csv`.

**Independent Test**: Run fake spectrum, recording success, cancelled start, and failed run cases. Confirm rows include mode, site, target, time, status, and result reference.

### Tests group

- [ ] T029 [P] [US3] Add cross-mode one-row-per-attempt tests in tests/unit/troubleshooting/rf_diagnostics/test_audit.py
- [ ] T030 [P] [US3] Add operation-level audit row tests for cancelled and failed outcomes in tests/unit/troubleshooting/rf_diagnostics/test_recording_flow.py

### Operation group

- [ ] T031 [US3] Enforce exactly one audit write for each final spectrum and recording outcome in src/troubleshooting/rf_diagnostics/operation.py
- [ ] T032 [US3] Add audit failure handling that reports a failed run without printing secrets in src/troubleshooting/rf_diagnostics/audit.py

### Validation group

- [ ] T033 [US3] Run pytest for audit and operation flow tests with python -m pytest tests/unit/troubleshooting/rf_diagnostics/test_audit.py tests/unit/troubleshooting/rf_diagnostics/test_spectrum_flow.py tests/unit/troubleshooting/rf_diagnostics/test_recording_flow.py -q

**Checkpoint**: User Story 3 is complete when each tested outcome writes one audit row and no secret text appears in output or CSV rows.

---

## Phase 6: User Story 4 - Prove request and wiring shape (Priority: P2)

**Goal**: Tests prove OpenAPI request shapes, and the wiring manifest proves deferred integration work is visible.

**Independent Test**: Review the request-shape tests and `wiring.md`. Confirm tests assert each start, stop, and spectrum body shape. Confirm `wiring.md` lists all deferred integration files.

### Tests group

- [ ] T034 [P] [US4] Add strict no-extra-fields assertions for spectrum and recording request bodies in tests/unit/troubleshooting/rf_diagnostics/test_client_requests.py
- [ ] T035 [P] [US4] Add wiring manifest content test or review note in tests/unit/troubleshooting/rf_diagnostics/test_client_requests.py

### Validation group

- [ ] T036 [US4] Verify specs/3570-spectrum-rfdiag/wiring.md lists deferred MistHelper.py registration, operation_registry.py registration, endpoint_primary_key_strategies.py registration, README, generated menu reference, and copilot-instructions category updates
- [ ] T037 [US4] Run pytest for request-shape evidence with python -m pytest tests/unit/troubleshooting/rf_diagnostics/test_client_requests.py -q

**Checkpoint**: User Story 4 is complete when request-shape tests and `wiring.md` make integration readiness clear.

---

## Phase 7: Polish and Cross-Cutting Concerns

**Purpose**: Finish quality, release note, and validation work that crosses stories.

### Release note group

- [ ] T038 [P] Fill issue 3570 release note fragment with operator-facing summary and validation notes in changelog.d/issue-3570-spectrum-rfdiag.md

### Validation group

- [ ] T039 Run full RF diagnostics unit tests with python -m pytest tests/unit/troubleshooting/rf_diagnostics -q
- [ ] T040 Run syntax validation for the integration-safe package with python -m py_compile src/troubleshooting/rf_diagnostics/*.py
- [ ] T041 Review implementation against specs/3570-spectrum-rfdiag/quickstart.md and record validation evidence in the pull request notes

### Operation group

- [ ] T042 Confirm src/troubleshooting/rf_diagnostics/operation.py does not edit MistHelper.py, operation_registry.py, endpoint_primary_key_strategies.py, README, generated menu reference, or copilot-instructions category files during the core package pull request

---

## Dependencies and Execution Order

### Phase Dependencies

- **Phase 1 Setup**: No dependencies.
- **Phase 2 Foundational**: Depends on Phase 1.
- **Phase 3 User Story 1**: Depends on Phase 2.
- **Phase 4 User Story 2**: Depends on Phase 2.
- **Phase 5 User Story 3**: Depends on Phase 3 and Phase 4 audit paths.
- **Phase 6 User Story 4**: Depends on Phase 2 and can finish after request-shape tests exist.
- **Phase 7 Polish**: Depends on all selected user stories.

### User Story Dependencies

- **US1 Run AP spectrum analysis**: Starts after foundation. It is the MVP.
- **US2 Record client RF diagnostics**: Starts after foundation. It can run in parallel with US1 after shared code is ready.
- **US3 Keep a run audit trail**: Starts after US1 and US2 have outcome paths.
- **US4 Prove request and wiring shape**: Starts after foundation and completes before integration.

### Within Each Story

- Write tests first and confirm they fail for missing behavior.
- Implement models before client logic.
- Implement client logic before operation flow.
- Implement operation flow before validation commands.
- Validate the story before starting unrelated polish work.

---

## Parallel Execution Examples

### User Story 1

```text
Task: T019 Add spectrum flow tests in tests/unit/troubleshooting/rf_diagnostics/test_spectrum_flow.py
Task: T020 Add spectrum request assertions in tests/unit/troubleshooting/rf_diagnostics/test_client_requests.py
```

### User Story 2

```text
Task: T024 Add recording flow tests in tests/unit/troubleshooting/rf_diagnostics/test_recording_flow.py
Task: T025 Add recording request assertions in tests/unit/troubleshooting/rf_diagnostics/test_client_requests.py
```

### User Story 3

```text
Task: T029 Add audit one-row tests in tests/unit/troubleshooting/rf_diagnostics/test_audit.py
Task: T030 Add operation audit tests in tests/unit/troubleshooting/rf_diagnostics/test_recording_flow.py
```

### User Story 4

```text
Task: T034 Add strict request body assertions in tests/unit/troubleshooting/rf_diagnostics/test_client_requests.py
Task: T036 Verify deferred integration list in specs/3570-spectrum-rfdiag/wiring.md
```

---

## Implementation Strategy

### MVP First

1. Complete Phase 1.
2. Complete Phase 2.
3. Complete Phase 3 for User Story 1.
4. Stop and validate spectrum mode with the US1 tests.

### Incremental Delivery

1. Add User Story 1 for spectrum analysis.
2. Add User Story 2 for client RF recording.
3. Add User Story 3 for complete audit coverage.
4. Add User Story 4 for request and wiring proof.
5. Finish polish and validation.

### Integration Pull Request Boundary

The core package pull request must not wire menu 290. The later integration pull request owns `MistHelper.py`, `operation_registry.py`, `endpoint_primary_key_strategies.py`, README, generated menu reference, and copilot-instructions category updates. The deferred list is documented in `specs/3570-spectrum-rfdiag/wiring.md`.
