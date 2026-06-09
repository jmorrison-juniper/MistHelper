# Tasks: Decompose Top-5 Complex Functions

**Input**: Design documents from `/specs/195-decompose-top5-functions/`
**Prerequisites**: `plan.md` (required), `spec.md` (required), `research.md`, `data-model.md`, `contracts/compatibility-contract.md`, `quickstart.md`

**Tests**: Included and required by spec (parity/regression + complexity verification).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no unmet dependencies)
- **[Story]**: User story label (`[US1]`, `[US2]`, `[US3]`)
- Every task includes an exact file path

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish baseline measurements and evidence scaffolding.

- [x] T001 Create evidence directory and placeholders in `specs/195-decompose-top5-functions/evidence/`
- [x] T002 Capture baseline top-5 complexity snapshot and save to `specs/195-decompose-top5-functions/evidence/baseline_cc_report.md`
- [x] T003 [P] Create target responsibility map scaffold in `specs/195-decompose-top5-functions/target-boundary-map.md`
- [x] T004 [P] Create verification matrix scaffold for FR-011..FR-016 in `specs/195-decompose-top5-functions/evidence/verification_bundle.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build shared parity/verification harness used by all user stories.

**⚠️ CRITICAL**: No user story implementation should begin before this phase is complete.

- [x] T005 Create shared compatibility fixtures for top-5 workflows in `tests/integration/top5_fixtures.py`
- [x] T006 [P] Create shared parity assertions for prompts/outputs/side-effects in `tests/integration/top5_parity_assertions.py`
- [x] T007 [P] Add complexity check utility for top-5 targets in `scripts/check_top5_complexity.py`
- [x] T008 Create consolidated compatibility test shell in `tests/integration/test_top5_compatibility_paths.py`

**Checkpoint**: Foundational harness is ready; user story work can proceed.

---

## Phase 3: User Story 1 - Preserve Menu and CLI Behavior During Decomposition (Priority: P1) 🎯 MVP

**Goal**: Refactor packet-capture orchestration paths while keeping menu/CLI prompts, outputs, and side effects unchanged.

**Independent Test**: Run packet-capture compatibility tests and confirm prompt sequence, output artifacts, and side effects are unchanged for current entry paths.

### Tests for User Story 1

- [x] T009 [P] [US1] Add org packet-capture parity integration test in `tests/integration/test_packet_capture_org_compatibility.py`
- [x] T010 [P] [US1] Add site capture-loop parity integration test in `tests/integration/test_site_capture_loop_compatibility.py`
- [x] T011 [US1] Register US1 parity scenarios in `tests/integration/test_top5_compatibility_paths.py`

### Implementation for User Story 1

- [x] T012 [P] [US1] Implement organization capture workflow class in `src/capture/org_capture_workflow.py`
- [x] T013 [P] [US1] Implement site capture loop runner class in `src/capture/site_capture_loop.py`
- [x] T014 [US1] Refactor `start_org_packet_capture` orchestration to delegate into workflow classes in `src/capture/packet_capture.py`
- [x] T015 [US1] Refactor `_execute_site_capture_loop` orchestration to delegate loop stages in `src/capture/packet_capture.py`
- [x] T016 [US1] Update compatibility facade wiring for packet capture paths in `MistHelper.py`
- [x] T017 [US1] Record US1 behavior parity evidence in `specs/195-decompose-top5-functions/evidence/us1_packet_capture_parity.md`

### Completion Evidence Criteria (US1 targets)

- **`start_org_packet_capture`**: CC <= 10 at retained entrypoint, parity tests green, prompt/confirmation flow unchanged.
- **`_execute_site_capture_loop`**: CC <= 10 at retained entrypoint, loop/retry/interrupt behavior preserved, parity tests green.

**Checkpoint**: Packet-capture decomposition is complete and independently verifiable.

---

## Phase 4: User Story 2 - Reduce Complexity for Maintainability (Priority: P1)

**Goal**: Decompose the remaining three high-complexity workflows into domain modules with CC <= 10 and no thin-wrapper anti-pattern.

**Independent Test**: Run unit tests for bootstrap/gateway/export modules and confirm each retained entrypoint and responsibility boundary is <= 10.

### Tests for User Story 2

- [x] T018 [P] [US2] Add dependency-check unit coverage in `tests/unit/test_dependency_check.py`
- [x] T019 [P] [US2] Add WAN override analyzer unit coverage in `tests/unit/test_gateway_override_analysis.py`
- [x] T020 [P] [US2] Add 52-week exporter unit coverage in `tests/unit/test_device_events_52w_exporter.py`

### Implementation for User Story 2

- [x] T021 [P] [US2] Implement dependency check orchestrator in `src/bootstrap/dependency_check.py`
- [x] T022 [P] [US2] Implement package install/upgrade strategy helpers in `src/bootstrap/package_installer.py`
- [x] T023 [P] [US2] Implement uv runtime detection/validation helpers in `src/bootstrap/uv_runtime.py`
- [x] T024 [US2] Refactor `_early_dependency_check` facade delegation in `MistHelper.py`
- [x] T025 [P] [US2] Implement device events 52-week exporter in `src/export/device_events_52w_exporter.py`
- [x] T026 [US2] Refactor `device_events_52w` facade delegation in `MistHelper.py`
- [x] T027 [P] [US2] Implement gateway WAN override analyzer in `src/gateway/gateway_override_analysis.py`
- [x] T028 [US2] Delegate `with_wan_overrides` through analyzer in `src/gateway/gateway_export_utils.py`
- [x] T029 [US2] Remove legacy duplicate heavy-body `with_wan_overrides` definition and retain single compatible entrypoint in `MistHelper.py`
- [x] T030 [US2] Update old-vs-new responsibility mappings in `specs/195-decompose-top5-functions/target-boundary-map.md`
- [x] T031 [US2] Record US2 maintainability evidence in `specs/195-decompose-top5-functions/evidence/us2_complexity_and_design.md`

### Completion Evidence Criteria (US2 targets)

- **`_early_dependency_check`**: CC <= 10 at retained entrypoint, dependency guidance and fallback outcomes unchanged.
- **`device_events_52w`**: CC <= 10 at retained entrypoint/responsibility boundary, pagination/checkpoint/output semantics preserved.
- **`with_wan_overrides`**: CC <= 10 at retained entrypoint/responsibility boundary, report schema/API minimization behavior preserved, duplicate legacy body removed.

**Checkpoint**: All five target functions are decomposed with maintainable boundaries.

---

## Phase 5: User Story 3 - Prove Behavioral Parity with Regression Coverage (Priority: P2)

**Goal**: Produce a single verification run proving complexity, parity, regression, and quality-gate compliance across all five targets.

**Independent Test**: Execute full parity + quality + complexity workflow and verify all evidence artifacts are complete and green.

### Tests for User Story 3

- [x] T032 [P] [US3] Expand cross-target parity matrix tests in `tests/integration/test_top5_compatibility_paths.py`
- [x] T033 [P] [US3] Add risk-control regression tests (safe-input/redaction) in `tests/unit/test_top5_risk_controls.py`

### Implementation for User Story 3

- [x] T034 [US3] Run targeted unit/integration suites and capture outputs in `specs/195-decompose-top5-functions/evidence/test_results.md`
- [x] T035 [US3] Run required complexity gates and capture final table in `specs/195-decompose-top5-functions/evidence/final_cc_report.md`
- [x] T036 [US3] Run required quality gates and capture outputs in `specs/195-decompose-top5-functions/evidence/quality_gates.md`
- [x] T037 [US3] Finalize single-run verification bundle mapped to FR-011..FR-016 in `specs/195-decompose-top5-functions/evidence/verification_bundle.md`

### Completion Evidence Criteria (all targets)

- Baseline vs final complexity table shows each target entrypoint/responsibility boundary at **CC <= 10**.
- Parity/regression tests pass for all five workflows in one approval run.
- Menu IDs, labels, prompt behavior, and CLI invocation semantics remain unchanged.

**Checkpoint**: Release-approval evidence is complete.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final hardening, documentation sync, and reviewer readiness.

- [x] T038 [P] Update execution/verification sequence in `specs/195-decompose-top5-functions/quickstart.md`
- [x] T039 [P] Refresh compatibility assertions and matrix wording in `specs/195-decompose-top5-functions/contracts/compatibility-contract.md`
- [x] T040 Add final implementation summary and evidence links in `specs/195-decompose-top5-functions/plan.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies.
- **Phase 2 (Foundational)**: Depends on Phase 1 completion.
- **Phase 3 (US1)**: Depends on Phase 2.
- **Phase 4 (US2)**: Depends on Phase 2; recommended after US1 due to shared `MistHelper.py` touchpoints.
- **Phase 5 (US3)**: Depends on US1 + US2 completion.
- **Phase 6 (Polish)**: Depends on US3 completion.

### User Story Dependencies

- **US1 (P1)**: Starts after foundational setup; no dependency on US2 outcomes.
- **US2 (P1)**: Starts after foundational setup; practically sequenced after US1 to reduce merge/conflict risk in `MistHelper.py`.
- **US3 (P2)**: Requires all decomposition work (US1 + US2) completed.

### Within-Story Ordering Rules

- Tests before implementation changes.
- New module/class creation before facade wiring.
- Facade wiring before evidence capture.
- Evidence capture before story checkpoint sign-off.

---

## Parallel Execution Examples

### US1 Parallel block

- Run in parallel: `T009` and `T010` (different test files).
- Run in parallel: `T012` and `T013` (different module files).

### US2 Parallel block

- Run in parallel: `T018`, `T019`, `T020` (three independent unit test files).
- Run in parallel: `T021`, `T022`, `T023`, `T025`, `T027` (different module files).

### US3 Parallel block

- Run in parallel: `T032` and `T033` (different test files).

---

## Implementation Strategy

### MVP First (US1)

1. Complete Setup + Foundational.
2. Deliver US1 packet-capture decomposition and parity proof.
3. Validate US1 independently before expanding scope.

### Incremental Delivery

1. Deliver US1 (packet-capture parity).
2. Deliver US2 (remaining three targets + maintainability refactor).
3. Deliver US3 (full evidence run + release readiness).
4. Finish polish/docs sync.

### Final Validation Gate (single approval run)

- `python -m radon cc MistHelper.py -s -a`
- `python -m radon cc src -s -a`
- `python -m radon cc MistHelper.py src -s -a`
- `python -m py_compile MistHelper.py`
- `python -m ruff check MistHelper.py src`
- `python -m black --check MistHelper.py src`
- `python MistHelper.py --test`
- Targeted top-5 unit/integration tests added in this feature

---

## Notes

- All tasks strictly follow checklist format requirements.
- Story labels are applied only to user-story tasks.
- Every target function has explicit completion evidence criteria in its story phase.
- This plan is optimized for safe, incremental rollout with rollback-friendly facades.
