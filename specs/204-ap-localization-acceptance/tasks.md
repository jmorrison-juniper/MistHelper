# Tasks: AP Localization Acceptance (Menu 204)

**Input**: Design documents from `/specs/204-ap-localization-acceptance/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/confirmSiteApLocalizationData.md`, `quickstart.md`

**Tests**: Include unit tests because the feature specification explicitly requires validation, call-wiring, audit, and test-mode protection coverage.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: User story label (`[US1]`, `[US2]`, `[US3]`)
- Every task includes an exact file path

## Path Conventions

- Application logic lives in `MistHelper.py`
- Unit tests live in `tests/unit/`
- Feature docs live in `specs/204-ap-localization-acceptance/`

## Phase 1: Setup (Shared Preparation)

**Purpose**: Prepare implementation touchpoints and test scaffold for Menu 204.

- [ ] T001 Reserve Menu 204 implementation touchpoints in `MistHelper.py`, `README.md`, and `CHANGELOG.md`
- [ ] T002 [P] Create unit test scaffold for Menu 204 in `tests/unit/test_menu_204_ap_localization.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish shared plumbing required before any user story can be completed.

**⚠️ CRITICAL**: User story work depends on this phase.

- [ ] T003 Add `confirmSiteApLocalizationData` to `ENDPOINT_PRIMARY_KEY_STRATEGIES` in `MistHelper.py`
- [ ] T004 Add `ApLocalizationManager` class skeleton and `confirm_site_ap_localization_data()` entry point in `MistHelper.py`
- [ ] T005 Wire menu dispatch entry `204` to `confirm_site_ap_localization_data` in `MistHelper.py`

**Checkpoint**: Menu 204 has a callable entry point and audit/export storage mapping.

---

## Phase 3: User Story 1 - Accept AP localization data with explicit approval (Priority: P1) 🎯 MVP

**Goal**: Let an operator accept or reject pending AP localization data only after explicit typed approval.

**Independent Test**: Run Menu 204 with valid site/map inputs and confirmation phrase, verify exactly one API call occurs and a visible success or cancellation result is shown.

### Tests for User Story 1

- [ ] T006 [P] [US1] Add success-path unit test for accept flow call wiring in `tests/unit/test_menu_204_ap_localization.py`
- [ ] T007 [P] [US1] Add cancellation unit test for incorrect confirmation phrase in `tests/unit/test_menu_204_ap_localization.py`

### Implementation for User Story 1

- [ ] T008 [US1] Implement Menu 204 input collection and action selection in `MistHelper.py`
- [ ] T009 [US1] Implement typed confirmation phrases and destructive warning flow in `MistHelper.py`
- [ ] T010 [US1] Implement `confirmSiteApLocalizationData` request body construction and API invocation in `MistHelper.py`
- [ ] T011 [US1] Implement user-facing success and cancellation result summaries for Menu 204 in `MistHelper.py`

**Checkpoint**: User Story 1 is independently functional and can safely execute or cancel the approval action.

---

## Phase 4: User Story 2 - Prevent unsafe execution through strong validation (Priority: P2)

**Goal**: Block execution when required identifiers or localization type inputs are invalid, incomplete, or unsafe for execution.

**Independent Test**: Enter empty or invalid values for site ID, map ID, and localization type, then verify the workflow stops before any API call and provides corrective guidance.

### Tests for User Story 2

- [ ] T012 [P] [US2] Add unit tests for empty `site_id`, empty `map_id`, and invalid `for_type` validation failures in `tests/unit/test_menu_204_ap_localization.py`
- [ ] T013 [P] [US2] Add unit test for `TEST_MODE` protection skipping the live API call in `tests/unit/test_menu_204_ap_localization.py`

### Implementation for User Story 2

- [ ] T014 [US2] Implement `_validate_inputs()` blocking rules for required identifiers and allowed localization types in `MistHelper.py`
- [ ] T015 [US2] Implement validation-failure exit path and typed-confirmation cancellation path in `MistHelper.py`
- [ ] T016 [US2] Apply required logging and inline safety comments across the Menu 204 workflow block in `MistHelper.py`

**Checkpoint**: User Story 2 blocks unsafe execution before remote state changes and preserves test-mode safety.

---

## Phase 5: User Story 3 - Capture audit-ready evidence of approval actions (Priority: P3)

**Goal**: Export an audit-ready record for every executed or cancelled Menu 204 attempt.

**Independent Test**: Execute one successful flow and one cancelled flow, then verify both produce exporter records containing timestamp, identifiers, outcome, and response summary fields.

### Tests for User Story 3

- [ ] T017 [P] [US3] Add unit test for executed audit export record contents in `tests/unit/test_menu_204_ap_localization.py`
- [ ] T018 [P] [US3] Add unit test for cancelled audit export record contents in `tests/unit/test_menu_204_ap_localization.py`

### Implementation for User Story 3

- [ ] T019 [US3] Implement `_export_audit_record()` with required audit fields in `MistHelper.py`
- [ ] T020 [US3] Capture HTTP status and exception outcome details in Menu 204 audit records in `MistHelper.py`
- [ ] T021 [US3] Document Menu 204 and operation count updates in `README.md` and `CHANGELOG.md`

**Checkpoint**: User Story 3 produces audit-ready records for both executed and cancelled actions.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Validate the completed feature against documented quality gates and quickstart expectations.

- [ ] T022 Run `python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`, `python -m black --check MistHelper.py`, and `pytest tests/unit/test_menu_204_ap_localization.py -v`
- [ ] T023 Validate Menu 204 behavior against `specs/204-ap-localization-acceptance/quickstart.md` and adjust `README.md` wording if the documented operator flow diverges

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1: Setup** → no dependencies
- **Phase 2: Foundational** → depends on Phase 1
- **Phase 3: US1** → depends on Phase 2
- **Phase 4: US2** → depends on Phase 3 because validation and confirmation harden the same Menu 204 workflow
- **Phase 5: US3** → depends on Phases 3 and 4 because audit content must reflect final execution and cancellation paths
- **Phase 6: Polish** → depends on all prior phases

### User Story Dependencies

- **US1 (P1)**: First deliverable and MVP slice
- **US2 (P2)**: Builds on the US1 workflow by adding strict safety gates
- **US3 (P3)**: Builds on final US1/US2 behavior to export complete audit evidence

### Within Each User Story

- Tests should be written before implementation and should fail before code changes
- Input collection and validation precede API execution
- API execution precedes result summary and audit finalization
- Documentation updates follow completed behavior

### Parallel Opportunities

- `T002` can run in parallel with `T001`
- `T006` and `T007` can run in parallel
- `T012` and `T013` can run in parallel
- `T017` and `T018` can run in parallel
- `T021` can run after `T019`/`T020` and can be split by file if multiple implementers are available

---

## Parallel Example: User Story 1

```text
Task: T006 [US1] Add success-path unit test for accept flow call wiring in tests/unit/test_menu_204_ap_localization.py
Task: T007 [US1] Add cancellation unit test for incorrect confirmation phrase in tests/unit/test_menu_204_ap_localization.py
```

## Parallel Example: User Story 2

```text
Task: T012 [US2] Add unit tests for empty site_id, empty map_id, and invalid for_type validation failures in tests/unit/test_menu_204_ap_localization.py
Task: T013 [US2] Add unit test for TEST_MODE protection skipping the live API call in tests/unit/test_menu_204_ap_localization.py
```

## Parallel Example: User Story 3

```text
Task: T017 [US3] Add unit test for executed audit export record contents in tests/unit/test_menu_204_ap_localization.py
Task: T018 [US3] Add unit test for cancelled audit export record contents in tests/unit/test_menu_204_ap_localization.py
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. Validate Menu 204 accept/reject workflow independently

### Incremental Delivery

1. Deliver US1 for explicit approval execution
2. Add US2 safety validation and test-mode protection
3. Add US3 audit/export evidence and documentation
4. Run quality gates and quickstart validation

### Suggested MVP Scope

- Through **Phase 3 / User Story 1** only
- This yields a working destructive-operation flow with explicit typed approval before later hardening and audit completeness

---

## Notes

- All tasks follow the required checklist format: checkbox, task ID, optional `[P]`, required `[US#]` on story tasks, and exact file paths
- Tasks were generated from feature planning artifacts in `specs/204-ap-localization-acceptance/`
- `MistHelper.py` is a hot file, so sequence same-file edits carefully to avoid overlap
