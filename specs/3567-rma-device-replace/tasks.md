# Tasks: RMA Device Replacement

**Input**: Design documents from `specs/3567-rma-device-replace/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, and `contracts/operation-contract.md`

**Tests**: Tests are required because each acceptance criterion must be proved without network access.

**Organization**: Tasks are grouped by user story so each story remains independently testable.

## Phase 1: Setup

- [x] T001 Create `src/mist/resources/inventory/device_replace/__init__.py` and `tests/unit/inventory/device_replace/__init__.py`. (delivered: `src/mist/resources/inventory/device_replace/__init__.py`, `tests/unit/inventory/device_replace/__init__.py`)
- [x] T002 [P] Create `changelog.d/issue-3567-rma-device-replace.md` with one `Added` entry for issue `#3567`. (delivered: `changelog.d/issue-3567-rma-device-replace.md`)
- [x] T003 [P] Create `specs/3567-rma-device-replace/wiring.md` with every section required by the fleet contract. (delivered: `specs/3567-rma-device-replace/wiring.md`)

## Phase 2: Foundational

- [x] T004 [P] Implement pure inventory and request models in `src/mist/resources/inventory/device_replace/models.py`. (delivered: `src/mist/resources/inventory/device_replace/models.py`)
- [x] T005 [P] Add model tests for selector lookup, unassigned filtering, type mismatch refusal, and request body shape in `tests/unit/inventory/device_replace/test_rma_device_replace_model.py`. (delivered: `tests/unit/inventory/device_replace/test_rma_device_replace_model.py`)
- [x] T006 [P] Implement Mist SDK calls in `src/mist/resources/inventory/device_replace/client.py`. (delivered: `src/mist/resources/inventory/device_replace/client.py`)
- [x] T007 [P] Add client tests with fake SDK responses in `tests/unit/inventory/device_replace/test_rma_device_replace_client.py`. (delivered: `tests/unit/inventory/device_replace/test_rma_device_replace_client.py`)
- [x] T008 [P] Implement backup and CSV persistence in `src/mist/resources/inventory/device_replace/persistence.py`. (delivered: `src/mist/resources/inventory/device_replace/persistence.py`)

## Phase 3: User Story 1 - Replace an RMA device safely (Priority: P1)

**Goal**: Send a replacement request only after validation, backup, and typed confirmation.

**Independent Test**: Mock prompts, client, and persistence. Verify backup order and request gating.

- [x] T009 [US1] Implement the destructive operation flow in `src/mist/resources/inventory/device_replace/operation.py`. (delivered: `src/mist/resources/inventory/device_replace/operation.py`)
- [x] T010 [US1] Add operation tests for backup-before-request, confirmation gating, dry-run behavior, and result logging in `tests/unit/inventory/device_replace/test_rma_device_replace_operation.py`. (delivered: `tests/unit/inventory/device_replace/test_rma_device_replace_operation.py`)

## Phase 4: User Story 2 - Select devices from inventory (Priority: P2)

- [x] T011 [US2] Add operation prompt helpers for old selector and replacement choice in `src/mist/resources/inventory/device_replace/operation.py`. (delivered: `src/mist/resources/inventory/device_replace/operation.py`)
- [x] T012 [US2] Extend model and operation tests for ambiguous names, assigned replacement refusal, and same-type filtering. (delivered: `tests/unit/inventory/device_replace/test_rma_device_replace_model.py`)

## Phase 5: User Story 3 - Record operator evidence (Priority: P3)

- [x] T013 [US3] Add persistence tests for backup JSON and `DeviceReplaceLog.csv` rows in `tests/unit/inventory/device_replace/test_rma_device_replace_operation.py`. (delivered: `tests/unit/inventory/device_replace/test_rma_device_replace_operation.py`)
- [x] T014 [US3] Ensure the operation records `sent`, `dry_run`, `cancelled`, and `error` outcomes. (delivered: `src/mist/resources/inventory/device_replace/operation.py`)

## Phase 6: Deferred integration wiring

- [x] T015 Document the menu `287` registration, destructive category table update, primary key strategy, and import line in `specs/3567-rma-device-replace/wiring.md`. (delivered: `specs/3567-rma-device-replace/wiring.md`)
- [ ] T016 Defer the `MistHelper.py`, `src/foundation/support/utils/operation_registry.py`, `src/foundation/support/refactors/endpoint_primary_key_strategies.py`, README, and generated reference edits to the integration pull request. This remains unchecked because another pull request owns those files.

## Phase 7: Validation

- [x] T017 Run `py_compile`, `ruff`, `black --check`, `mypy`, `pydocstyle`, and `pytest` for the package and test directory. (delivered: local gate output)
- [x] T018 Run `vulture`, `interrogate`, `complexity-gate`, and `test-quality-analyzer` before the final commit. (delivered: local gate output)
- [x] T019 Run manual `speckit.analyze` consistency review and repair findings. (delivered: this task evidence update)

## Dependencies & Execution Order

1. Phase 1 finished before code implementation.
2. Phase 2 finished before the operation flow.
3. User Story 1 is the MVP and is complete.
4. User Story 2 and User Story 3 are complete on the shared model and persistence.
5. Deferred integration wiring remains unchecked because another pull request owns those files.

## Analysis Result

Manual `speckit.analyze` review found no requirement gaps across `spec.md`, `plan.md`, and this task list. T016 remains intentionally open because the fleet contract forbids this branch from editing integration-owned files.
