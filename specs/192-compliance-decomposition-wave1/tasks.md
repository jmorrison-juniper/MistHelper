# Tasks: Compliance/Decomposition Wave 1 (Safety Refactor, No Behavior Change)

**Input**: Design documents from `/specs/192-compliance-decomposition-wave1/`
**Prerequisites**: `plan.md` (required), `spec.md` (required), `research.md`, `data-model.md`, `contracts/wave1-compliance-contract.md`, `quickstart.md`

**Tests**: Included because the feature specification explicitly requires guardrail tests and tranche gate validation.

**Organization**: Tasks are grouped by user story and tranche so each story can be implemented and validated independently while enforcing mandatory stop/go quality gates.

## Format: `[ID] [P?] [Story] Description with file path`

- **[P]**: Can run in parallel (different files, no dependency on incomplete tasks)
- **[Story]**: User story label (`[US1]`, `[US2]`, `[US3]`, `[US4]`) used only in user-story phases

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize Wave 1 execution artifacts and gate-run evidence targets.

**Pass Criteria**:
- Wave 1 task artifacts exist under `specs/192-compliance-decomposition-wave1/`.
- Gate evidence destination is created and ready for tranche records.

- [x] T001 Create Wave 1 evidence tracker skeleton in specs/192-compliance-decomposition-wave1/tranche-validation.md
- [x] T002 Create baseline compliance metrics document in specs/192-compliance-decomposition-wave1/baseline-compliance-metrics.md
- [x] T003 Create bounded decomposition scope checklist in specs/192-compliance-decomposition-wave1/bounded-decomposition-checklist.md
- [x] T004 Create high-risk function selection worksheet in specs/192-compliance-decomposition-wave1/high-risk-function-map.md

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Lock baseline compliance metrics, production-path scope, and bounded decomposition rules before any refactor.

**⚠️ CRITICAL**: No user-story implementation starts until this phase is complete.

**Pass Criteria**:
- Baseline prompt inventory and routing/safety baseline expectations are documented.
- Explicit Wave 1 exclusions and bounded decomposition constraints are recorded and testable.
- Tranche gate command set is normalized in one executable helper.

- [x] T005 Inventory in-scope production prompt paths and context labels in specs/192-compliance-decomposition-wave1/baseline-compliance-metrics.md
- [x] T006 Capture baseline entry-routing guardrail matrix in specs/192-compliance-decomposition-wave1/baseline-compliance-metrics.md
- [x] T007 Capture baseline safety-classification guardrail matrix in specs/192-compliance-decomposition-wave1/baseline-compliance-metrics.md
- [x] T008 Define bounded decomposition hard boundaries and out-of-scope exclusions in specs/192-compliance-decomposition-wave1/bounded-decomposition-checklist.md
- [x] T009 [P] Implement tranche gate runner script for CS1 commands in scripts/wave1/run_wave1_gate.ps1
- [x] T010 [P] Add gate-run usage notes for maintainers in specs/192-compliance-decomposition-wave1/quickstart.md
- [x] T011 Add tranche stop/go policy and blocking semantics to specs/192-compliance-decomposition-wave1/tranche-validation.md

**Checkpoint**: Foundation complete; story work can begin in priority order.

---

## Phase 3: User Story 1 - Safe Input Hardening for Production Paths (Priority: P1) 🎯 MVP

**Goal**: Replace in-scope raw production `input()` calls with `InputUtils.safe_input(..., context=...)` without behavior drift.

**Independent Test**: Interactive/EOF flows for all in-scope prompt paths match baseline behavior and terminate cleanly on EOF.

**Pass Criteria**:
- 100% of in-scope production prompt paths are migrated to safe input with explicit context.
- No routing or successful-flow behavior drift in touched paths.

### Tests for User Story 1

- [x] T012 [P] [US1] Add EOF-safe prompt behavior tests for wave-1 prompt paths in tests/guardrails/test_wave1_safe_input_paths.py
- [x] T013 [P] [US1] Add regression tests for valid-input baseline flow equivalence in tests/guardrails/test_wave1_safe_input_paths.py

### Implementation for User Story 1

- [x] T014 [US1] Replace in-scope production raw input calls with InputUtils.safe_input and context labels in MistHelper.py
- [x] T015 [US1] Add/normalize prompt context constants used by safe_input paths in MistHelper.py
- [x] T016 [US1] Update production prompt migration status table and SC-001 evidence in specs/192-compliance-decomposition-wave1/baseline-compliance-metrics.md

### Gate G1 (mandatory before continuing)

**Pass Criteria**:
- All CS1 commands pass with exit code 0.
- Results are recorded in tranche evidence.

- [x] T017 [US1] Execute Wave 1 G1 command set and append output summary to specs/192-compliance-decomposition-wave1/tranche-validation.md

---

## Phase 4: User Story 2 - Preserve Operation Safety Controls (Priority: P1)

**Goal**: Lock routing and destructive/non-destructive classification invariants with guardrail tests.

**Independent Test**: Guardrail suites pass for representative route mappings and boundary-adjacent safety IDs.

**Pass Criteria**:
- Guardrail tests prove route mapping invariants remain unchanged from baseline.
- Guardrail tests prove safety classification and confirmation requirements remain unchanged.

### Tests for User Story 2

- [x] T018 [P] [US2] Implement entry-routing guardrail tests using baseline matrix in tests/guardrails/test_wave1_entry_routing_guardrails.py
- [x] T019 [P] [US2] Implement safety-classification boundary tests using baseline matrix in tests/guardrails/test_wave1_safety_classification_guardrails.py
- [x] T020 [P] [US2] Add representative destructive-confirmation flow assertions in tests/guardrails/test_wave1_safety_classification_guardrails.py

### Implementation for User Story 2

- [x] T021 [US2] Add minimal testability hooks/constants needed for deterministic routing assertions in MistHelper.py
- [x] T022 [US2] Add minimal testability hooks/constants needed for deterministic safety classification assertions in MistHelper.py
- [x] T023 [US2] Record US2 guardrail coverage and SC-002 evidence in specs/192-compliance-decomposition-wave1/baseline-compliance-metrics.md

### Gate G2 (mandatory before continuing)

**Pass Criteria**:
- All CS1 commands pass with exit code 0.
- Results are recorded in tranche evidence.

- [x] T024 [US2] Execute Wave 1 G2 command set and append output summary to specs/192-compliance-decomposition-wave1/tranche-validation.md

---

## Phase 5: User Story 3 - Targeted Logging Envelopes in High-Risk Touched Functions (Priority: P2)

**Goal**: Add pre-action and post-action logging envelopes in selected high-risk functions touched by Wave 1.

**Independent Test**: Targeted paths emit before/after log envelopes without exposing secrets.

**Pass Criteria**:
- Selected high-risk functions emit both pre and post action logs for meaningful actions.
- Logging payloads are redacted/safe and avoid secret leakage.

### Tests for User Story 3

- [x] T027 [US3] Finalize selected high-risk touched function list and rationale in specs/192-compliance-decomposition-wave1/high-risk-function-map.md
- [x] T025 [P] [US3] Add logging envelope presence tests for selected high-risk functions in tests/guardrails/test_wave1_logging_envelopes.py
- [x] T026 [P] [US3] Add secret-exposure negative tests for logging payloads in tests/guardrails/test_wave1_logging_envelopes.py

### Implementation for User Story 3

- [x] T028 [US3] Add pre-action and post-action log envelopes in selected high-risk touched functions in MistHelper.py
- [x] T029 [US3] Add/adjust log redaction helpers used by selected envelopes in src/misthelper/logger_utils.py
- [x] T030 [US3] Record US3 logging coverage and SC-004 evidence in specs/192-compliance-decomposition-wave1/baseline-compliance-metrics.md

### Gate G3 (mandatory before continuing)

**Pass Criteria**:
- All CS1 commands pass with exit code 0.
- Results are recorded in tranche evidence.

- [x] T031 [US3] Execute Wave 1 G3 command set and append output summary to specs/192-compliance-decomposition-wave1/tranche-validation.md

---

## Phase 6: User Story 4 - Tranche-Based Quality Gates and Bounded Decomposition Enforcement (Priority: P2)

**Goal**: Enforce quality gates between tranches and verify Wave 1 remains bounded (no packet-capture decomposition or global sweep).

**Independent Test**: Gate runner blocks progression on failures, and scope-audit checks confirm bounded decomposition constraints.

**Pass Criteria**:
- Mandatory gate workflow is executed and recorded between every tranche.
- Scope-audit checks confirm bounded decomposition constraints were not violated.

### Tests for User Story 4

- [x] T032 [P] [US4] Add gate-runner regression tests for stop/go semantics in tests/guardrails/test_wave1_gate_runner.py
- [x] T033 [P] [US4] Add bounded decomposition scope-audit tests for forbidden change categories in tests/guardrails/test_wave1_scope_boundaries.py

### Implementation for User Story 4

- [x] T034 [US4] Implement scope-audit script to verify Wave 1 exclusion boundaries in scripts/wave1/verify_wave1_scope_boundaries.py
- [x] T035 [US4] Integrate gate runner and scope audit sequence into execution flow notes in specs/192-compliance-decomposition-wave1/quickstart.md
- [x] T036 [US4] Record US4 gate-compliance and bounded-decomposition results in specs/192-compliance-decomposition-wave1/tranche-validation.md

### Gate G4 (final release gate)

**Pass Criteria**:
- All CS1 commands pass with exit code 0.
- Scope boundary audit passes with no violations.
- Final tranche evidence is complete.

- [x] T037 [US4] Execute Wave 1 G4 final command set and append output summary to specs/192-compliance-decomposition-wave1/tranche-validation.md

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final consistency, documentation, and release-readiness evidence collation.

**Pass Criteria**:
- All story evidence maps to spec success criteria SC-001..SC-005.
- Tasks and evidence are audit-ready for implementation/PR execution.

- [x] T038 [P] Align success-criteria evidence mapping SC-001..SC-005 in specs/192-compliance-decomposition-wave1/baseline-compliance-metrics.md
- [x] T039 [P] Add final tranche summary table (T0..T4 and G1..G4) in specs/192-compliance-decomposition-wave1/tranche-validation.md
- [x] T040 Add implementation handoff checklist with gate replay steps in specs/192-compliance-decomposition-wave1/quickstart.md
- [x] T041 Add CS1 command parity verification across spec/plan/quickstart/gate script in specs/192-compliance-decomposition-wave1/tranche-validation.md
- [x] T042 Add explicit SC-005 safety-boundary evidence capture entry in specs/192-compliance-decomposition-wave1/tranche-validation.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies.
- **Phase 2 (Foundational)**: Depends on Phase 1; blocks all user stories.
- **Phase 3 (US1 / T1)**: Depends on Phase 2 completion.
- **Phase 4 (US2 / T2)**: Depends on US1 completion and **G1 pass**.
- **Phase 5 (US3 / T3)**: Depends on US2 completion and **G2 pass**.
- **Phase 6 (US4 / T4)**: Depends on US3 completion and **G3 pass**.
- **Phase 7 (Polish)**: Depends on US4 completion and **G4 pass**.

### User Story Dependencies

- **US1 (P1)**: Starts after Foundational; no dependency on other user stories.
- **US2 (P1)**: Starts after US1 and G1 because guardrails validate post-migration behavior.
- **US3 (P2)**: Starts after US2 and G2 to add observability on stabilized logic.
- **US4 (P2)**: Starts after US3 and G3 to finalize tranche gating and bounded decomposition proof.

### Gate Dependencies (Mandatory Stop/Go)

- **G1** must pass before any US2 tasks.
- **G2** must pass before any US3 tasks.
- **G3** must pass before any US4 tasks.
- **G4** must pass before Polish completion and implementation sign-off.

---

## Parallel Opportunities

- **Setup**: T002-T004 can run in parallel after T001.
- **Foundational**: T009 and T010 can run in parallel after T008.
- **US1**: T012 and T013 can run in parallel before T014.
- **US2**: T018, T019, T020 can run in parallel before T021/T022.
- **US3**: T025 and T026 can run in parallel before T028.
- **US4**: T032 and T033 can run in parallel before T034.
- **Polish**: T038 and T039 can run in parallel before T040.

## Parallel Example: US2 Guardrail Work

- [x] T018 [P] [US2] Implement entry-routing guardrail tests using baseline matrix in tests/guardrails/test_wave1_entry_routing_guardrails.py
- [x] T019 [P] [US2] Implement safety-classification boundary tests using baseline matrix in tests/guardrails/test_wave1_safety_classification_guardrails.py
- [x] T020 [P] [US2] Add representative destructive-confirmation flow assertions in tests/guardrails/test_wave1_safety_classification_guardrails.py

---

## Implementation Strategy

### MVP First (US1 only)

1. Complete Phase 1 and Phase 2.
2. Complete US1 tasks through T017 (G1 pass).
3. Validate safe-input migration behavior equivalence and EOF safety.
4. Demo/commit MVP tranche evidence.

### Incremental Delivery by Tranche

1. **T1 / US1**: Safe input migration + G1.
2. **T2 / US2**: Guardrail tests + G2.
3. **T3 / US3**: Logging envelopes + G3.
4. **T4 / US4**: Gate/boundary enforcement + G4.
5. Final polish and evidence collation.

### Definition of Done for Wave 1

- All tasks T001-T040 completed.
- G1, G2, G3, G4 all recorded as pass in `specs/192-compliance-decomposition-wave1/tranche-validation.md`.
- Evidence in `specs/192-compliance-decomposition-wave1/baseline-compliance-metrics.md` maps to SC-001..SC-005.
- Bounded decomposition constraints remain intact per `specs/192-compliance-decomposition-wave1/bounded-decomposition-checklist.md`.





