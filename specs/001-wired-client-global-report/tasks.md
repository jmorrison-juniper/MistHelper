# Tasks: Global Wired Client Search Report

**Input**: Design documents from `/specs/001-wired-client-global-report/`
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data-model.md`, `contracts/`

**Tests**: No explicit automated-test authoring requirement was requested in the feature spec. This task list focuses on implementation + validation tasks.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (`[US1]`, `[US2]`, `[US3]`)
- Every task includes an exact file path

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish menu slot, operation naming, and export identity before feature logic is implemented.

- [x] T001 Add a new read-only menu operation description and callable placeholder in `MistHelper.py` (`menu_actions` mapping section)
- [x] T002 Register the new menu option classification as safe/read-only in `MistHelper.py` (`OperationRegistry._REGISTRY`)
- [x] T003 Add a dedicated export identity for the new report in `MistHelper.py` (`ENDPOINT_PRIMARY_KEY_STRATEGIES` entry for new API function name)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build shared operator/filter infrastructure required by all user stories.

**⚠️ CRITICAL**: No user story implementation should start until this phase is complete.

- [x] T004 Define shared operator catalog and operator-group constants in `MistHelper.py` (value-required vs null/blank operators)
- [x] T005 Implement shared normalization helpers in `MistHelper.py` (MAC delimiter-insensitive normalization + case-insensitive text normalization)
- [x] T006 Implement generic operator evaluator utility in `MistHelper.py` supporting `is`, `is not`, `contains`, `doesn't contain`, `starts with`, `doesn't start with`, `ends with`, `doesn't end with`, `is blank`, `is not blank`, `is null`, `is not null`
- [x] T007 Implement operator/value validation helpers in `MistHelper.py` to fail fast when value-required operators receive empty normalized input
- [x] T008 Implement combined filter application pipeline in `MistHelper.py` that evaluates MAC and manufacturer locally with logical AND and returns decision metadata (`records_retrieved`, `records_matched`, filter mode)

**Checkpoint**: Operator semantics, normalization, and local authoritative filtering are complete.

---

## Phase 3: User Story 1 - Generate global wired client report (Priority: P1) 🎯 MVP

**Goal**: Export organization-wide wired client data with no filters and produce both local artifact + standard export output.

**Independent Test**: Run new menu option without filters and confirm complete retrievable wired-client export appears in both output channels with matching counts.

- [x] T009 [US1] Implement org-wide wired client retrieval with pagination in `MistHelper.py` (using `mistapi.api.v1.orgs.wired_clients.searchOrgWiredClients` + `mistapi.get_all` pattern)
- [x] T010 [US1] Implement report row shaping + summary metadata builder for this operation in `MistHelper.py`
- [x] T011 [US1] Implement standard export integration for this operation in `MistHelper.py` (via `DataExporter.write_with_format_selection`)
- [x] T012 [US1] Implement local report artifact output for the same matched dataset in `MistHelper.py` (write under `data/`)
- [x] T013 [US1] Wire runtime flow from menu action to execution path in `MistHelper.py` with safe prompts and progress visibility aligned to existing org export behavior

**Checkpoint**: US1 is independently functional and produces consistent dual outputs without filters.

---

## Phase 4: User Story 2 - Filter MAC with positional operators reliably (Priority: P2)

**Goal**: Add full MAC operator flow with validation, remote optimization, and authoritative local filtering.

**Independent Test**: Validate contains/starts-with/ends-with/negated/null/blank MAC behavior on known datasets; confirm delimiter-insensitive matching and correct exclusions.

- [x] T014 [US2] Add MAC operator prompt/selection flow in `MistHelper.py` using safe input and explicit operator choices
- [x] T015 [US2] Add MAC value capture + validation flow in `MistHelper.py` for value-required operators
- [x] T016 [US2] Implement best-effort MAC remote prefilter mapping in `MistHelper.py` for the explicit positive subset (`is`, `contains`, `starts with`, `ends with`) as optimization only
- [x] T017 [US2] Apply local authoritative MAC filtering using shared evaluator/normalizer in `MistHelper.py`
- [x] T018 [US2] Add MAC-specific summary metadata fields in `MistHelper.py` output pipeline (selected operator/value and filtering method used)

**Checkpoint**: US2 is independently functional with deterministic MAC operator semantics.

---

## Phase 5: User Story 3 - Filter manufacturer with positional operators (Priority: P3)

**Goal**: Add full manufacturer operator flow with parity to MAC semantics and combined AND filtering.

**Independent Test**: Validate contains/starts-with/ends-with/negated/null/blank manufacturer behavior on known datasets and confirm final result honors MAC+MFG AND logic.

- [x] T019 [US3] Add manufacturer operator prompt/selection flow in `MistHelper.py` using safe input and same operator catalog as MAC
- [x] T020 [US3] Add manufacturer value capture + validation flow in `MistHelper.py` for value-required operators
- [x] T021 [US3] Implement best-effort manufacturer remote prefilter mapping in `MistHelper.py` for the explicit positive subset (`is`, `contains`, `starts with`, `ends with`) as optimization only
- [x] T022 [US3] Apply local authoritative manufacturer filtering with positional parity to MAC semantics in `MistHelper.py`
- [x] T023 [US3] Implement/verify combined MAC+manufacturer AND inclusion logic in `MistHelper.py` including missing/blank manufacturer handling per contract
- [x] T024 [US3] Extend summary and zero-match output messaging in `MistHelper.py` to include manufacturer operator/value and final match rationale

**Checkpoint**: All user stories are independently functional with operator parity across MAC and manufacturer.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation alignment, compatibility checks, and mandatory validation pipeline tasks.

- [x] T025 [P] Update user-facing menu documentation and operation references in `README.md` for the new wired client global report option
- [x] T026 Determine assigned menu number and apply deterministic static-registry policy in `specs/001-wired-client-global-report/quickstart.md`: if menu number is `<= 80`, update `web_portal/menu_registry.py`; if `> 80`, document explicit no-change rationale for `web_portal/menu_registry.py`
- [x] T027 Implement explicit FR-012 failure-path handling in `MistHelper.py` for API exceptions and rate-limit interruptions, ensuring clear failure state and no false success output
- [x] T028 Add FR-012 verification steps to `specs/001-wired-client-global-report/quickstart.md` covering API error and rate-limit interruption behavior
- [x] T029 Add explicit FR-013 compatibility validation in `specs/001-wired-client-global-report/quickstart.md` for additive CSV/SQLite output shape and downstream consumer safety
- [x] T030 Validate syntax with `python -m py_compile MistHelper.py` and resolve any issues in `MistHelper.py`
- [x] T031 Run broad safety regression with `python MistHelper.py --test` and resolve any operation classification/test-harness issues in `MistHelper.py`
- [x] T032 Execute manual semantic verification matrix for all operators and record outcomes in `specs/001-wired-client-global-report/quickstart.md`
- [ ] T033 Execute mandatory deployment workflow steps (commit/push/CI watch/image pull/container restart/verify) in repository root with resulting runtime verification notes in `README.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: starts immediately
- **Phase 2 (Foundational)**: depends on Phase 1 and blocks story work
- **Phase 3 (US1)**: depends on Phase 2
- **Phase 4 (US2)**: depends on Phase 2 and integrates on top of US1 flow
- **Phase 5 (US3)**: depends on Phase 2 and integrates with US1/US2 filtering flow
- **Phase 6 (Polish)**: depends on completion of all selected stories

### User Story Dependencies

- **US1 (P1)**: no dependency on other stories once foundational work is done
- **US2 (P2)**: depends on shared operator/filter pipeline and US1 retrieval/output path
- **US3 (P3)**: depends on shared operator/filter pipeline and combined filter behavior with US2

### Within-Story Order

- Prompt/validation tasks before remote optimization
- Remote optimization before final local authoritative integration
- Output metadata updates after filtering correctness is in place

---

## Parallel Opportunities

- [P] tasks in Phase 6 (`T025`, `T026`) can run in parallel on different files.
- After foundational phase, story phases can be split by implementer:
  - MAC flow (`US2`) and manufacturer flow (`US3`) can be developed concurrently if both teams align on shared operator helper interfaces from Phase 2.

### Parallel Example

```text
Developer A: T014, T015, T016, T017, T018 (MAC path in MistHelper.py)
Developer B: T019, T020, T021, T022, T023, T024 (MFG path in MistHelper.py)
Developer C: T025, T026 documentation updates
```

---

## Implementation Strategy

### MVP First

1. Complete Phase 1 + Phase 2
2. Deliver US1 (global wired report, no filters)
3. Validate dual-output consistency
4. Demo/deploy MVP

### Incremental Delivery

1. Add US2 MAC positional operators
2. Validate MAC semantics
3. Add US3 manufacturer positional operators and AND behavior
4. Validate full parity and edge cases
5. Complete Phase 6 polish and deployment workflow

---

## Notes

- `[P]` means parallelizable with low merge conflict risk.
- `[USx]` labels preserve traceability from task to user story.
- Keep local filtering authoritative whenever any filter is supplied.
- Ensure both output channels always represent the same final matched set.
