# Tasks: Masking Default Audit

**Input**: Design documents from `specs\2753-masking-defaults\`

**Prerequisites**: `plan.md` and `spec.md`.

**Tests**: Add tests for each missing input that must fail visibly.

## Phase 1: Setup

- [x] T001 Read issue #2753, parent issue #1924, and the repository instructions. (delivered: local issue read)
- [x] T002 Read `specs\1924-failure-evidence\inventory.md`. (delivered: inventory triage)

## Phase 2: User Story 1 - Refuse a missing upgrade input

**Goal**: The destructive upgrade start route fails visibly when required input is absent.

**Independent Test**: Run `python -m pytest tests\unit\upgrade_portal\test_upgrade_start_input_validator.py -v`.

### Tests

- [x] T003 [US1] Add a test for a missing JSON body. (delivered: `tests\unit\upgrade_portal\test_upgrade_start_input_validator.py`)
- [x] T004 [US1] Add a test for a missing device list. (delivered: `tests\unit\upgrade_portal\test_upgrade_start_input_validator.py`)
- [x] T005 [US1] Add a test for a missing firmware version. (delivered: `tests\unit\upgrade_portal\test_upgrade_start_input_validator.py`)
- [x] T006 [US1] Add a test for a missing strategy. (delivered: `tests\unit\upgrade_portal\test_upgrade_start_input_validator.py`)

### Implementation

- [x] T007 [US1] Add `UpgradeStartInputValidator`. (delivered: `src\upgrade_portal\app\routes\upgrade.py`)
- [x] T008 [US1] Replace unsafe route defaults with validator output. (delivered: `src\upgrade_portal\app\routes\upgrade.py`)

## Phase 3: Follow-up tracking

- [x] T009 File the credential follow-up issue. (delivered: #2861)
- [x] T010 File the upgrade-input follow-up issue. (delivered: #2862)
- [x] T011 File the issue that follows up organization and site identifiers. (delivered: #2863)

## Dependencies & Execution Order

T001 and T002 run before all code changes. T003 through T006 prove T007 and T008. T009 through T011 record deferred work after the triage.
