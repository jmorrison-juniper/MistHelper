# Tasks: RMA Device Replacement

**Input**: Design documents from `specs/3567-rma-device-replace/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, and `contracts/operation-contract.md`

**Tests**: Tests are required because each acceptance criterion must be proved without network access.

**Organization**: Tasks are grouped by user story so each story remains independently testable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel when a different file is changed.
- **[Story]**: User story label.
- Include exact file paths in descriptions.
- Tick a task only after the delivered file exists and the matching test passes.

## Phase 1: Setup

**Purpose**: Create the package and test structure.

- [x] T001 Create `src/inventory/device_replace/__init__.py` and `tests/unit/inventory/device_replace/__init__.py`.
- [x] T002 [P] Create `changelog.d/issue-3567-rma-device-replace.md` with one `Added` entry for issue `#3567`.
- [x] T003 [P] Create `specs/3567-rma-device-replace/wiring.md` with every section required by the fleet contract.

---

## Phase 2: Foundational

**Purpose**: Build pure data objects, API seams, and file persistence.

- [x] T004 [P] Implement pure inventory and request models in `src/inventory/device_replace/models.py`.
- [x] T005 [P] Add model tests for selector lookup, unassigned filtering, type mismatch refusal, and request body shape in `tests/unit/inventory/device_replace/test_rma_device_replace_model.py`.
- [x] T006 [P] Implement Mist SDK calls in `src/inventory/device_replace/client.py`.
- [x] T007 [P] Add client tests with fake SDK responses in `tests/unit/inventory/device_replace/test_rma_device_replace_client.py`.
- [x] T008 [P] Implement backup and CSV persistence in `src/inventory/device_replace/persistence.py`.

---

## Phase 3: User Story 1 - Replace an RMA device safely (Priority: P1)

**Goal**: Send a replacement request only after validation, backup, and typed confirmation.

**Independent Test**: Mock prompts, client, and persistence. Verify backup order and request gating.

- [x] T009 [US1] Implement the destructive operation flow in `src/inventory/device_replace/operation.py`.
- [x] T010 [US1] Add operation tests for backup-before-request, confirmation gating, dry-run behavior, and result logging in `tests/unit/inventory/device_replace/test_rma_device_replace_operation.py`.

---

## Phase 4: User Story 2 - Select devices from inventory (Priority: P2)

**Goal**: Let an operator select the old device by MAC or name and choose an unassigned same-type replacement.

**Independent Test**: Use pure model tests to verify lookup and filtering.

- [x] T011 [US2] Add operation prompt helpers for old selector and replacement choice in `src/inventory/device_replace/operation.py`.
- [x] T012 [US2] Extend model and operation tests for ambiguous names, assigned replacement refusal, and same-type filtering.

---

## Phase 5: User Story 3 - Record operator evidence (Priority: P3)

**Goal**: Create durable evidence under `data/`.

**Independent Test**: Use controlled temporary directories under pytest fixtures to verify backup and CSV content.

- [x] T013 [US3] Add persistence tests for backup JSON and `DeviceReplaceLog.csv` rows in `tests/unit/inventory/device_replace/test_rma_device_replace_operation.py`.
- [x] T014 [US3] Ensure the operation records `sent`, `dry_run`, `cancelled`, and `error` outcomes.

---

## Phase 6: Deferred integration wiring

**Purpose**: Hand exact menu and registry edits to the integration pull request.

- [x] T015 Document the menu `287` registration, destructive category table update, primary key strategy, and import line in `specs/3567-rma-device-replace/wiring.md`.
- [ ] T016 Defer the `MistHelper.py`, `src/utils/operation_registry.py`, `src/refactors/endpoint_primary_key_strategies.py`, README, and generated reference edits to the integration pull request.

---

## Phase 7: Validation

**Purpose**: Prove the package is ready for integration.

- [x] T017 Run `py_compile`, `ruff`, `black --check`, `mypy`, `pydocstyle`, and `pytest` for the package and test directory.
- [x] T018 Run `vulture` and `interrogate` once before the final commit.
- [x] T019 Run `speckit.analyze` or a manual consistency analysis and repair findings.

## Dependencies & Execution Order

1. Phase 1 must finish before code implementation.
2. Phase 2 must finish before the operation flow.
3. User Story 1 is the MVP.
4. User Story 2 and User Story 3 can build on the shared model and persistence.
5. Deferred integration wiring remains unchecked because another pull request owns those files.

## Parallel Opportunities

- T004, T006, and T008 touch separate implementation files.
- T005 and T007 touch separate test files.
- Documentation tasks can run independently from code tasks.

## Implementation Strategy

Build the pure model first, then the client, then persistence, then the operation. Run the targeted quality gates before each implementation commit. Push after the implementation milestone and after analysis repairs.
