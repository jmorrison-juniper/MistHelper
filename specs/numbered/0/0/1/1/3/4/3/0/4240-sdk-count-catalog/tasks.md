# Tasks: Count Catalog Completeness

**Input**: Design documents in `specs/numbered/0/0/1/1/3/4/3/0/4240-sdk-count-catalog/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, and `quickstart.md`

**Organization**: Tasks follow the single independently testable user story.

## Phase 1: Setup

**Purpose**: Prepare the existing test environment.

- [x] T001 Confirm main revision and mistapi version before changes in the worktree and `.venv`. (delivered: tests/unit/export/test_count_exporter.py)

## Phase 2: Foundational

**Purpose**: No new infrastructure is required.

## Phase 3: User Story 1 - Select an organization count (Priority: P1)

**Goal**: Make all supported organization count operations available with valid persistence strategies.

**Independent Test**: Run `tests/unit/export/test_count_exporter.py` with mocked SDK and export calls.

### Tests and Implementation

- [x] T002 [US1] Assert exact SDK catalog completeness and expected count persistence strategies in `tests/unit/export/test_count_exporter.py`. (delivered: tests/unit/export/test_count_exporter.py)
- [x] T003 [US1] Add both organization operations, register the variable count strategy, and update the operation count in `src/operations/exporting/export/count_exporter.py` and `src/foundation/support/refactors/endpoint_primary_key_strategies.py`. (delivered: src/operations/exporting/export/count_exporter.py)
- [x] T004 [US1] Add the issue-specific release note in `changelog.d/issue-4240-count-exporter-catalog.md`. (delivered: changelog.d/issue-4240-count-exporter-catalog.md)
- [x] T005 [US1] Run focused tests and applicable lint checks for the changed Python files. (delivered: tests/unit/export/test_count_exporter.py)

## Phase 4: Polish

**Purpose**: Verify the focused change and keep generated references current.

- [x] T006 [US1] Run the documented count exporter quickstart in `specs/numbered/0/0/1/1/3/4/3/0/4240-sdk-count-catalog/quickstart.md`. (delivered: specs/numbered/0/0/1/1/3/4/3/0/4240-sdk-count-catalog/quickstart.md)

## Dependencies & Execution Order

- T001 is complete.
- T002 precedes T003 because the catalog and strategy behavior must be tested.
- T003 and T004 can run independently after T002.
- T005 and T006 follow T003 and T004.

## Parallel Opportunities

- T004 can run independently from T003 after T002.

## Implementation Strategy

Complete User Story 1 as the MVP. Preserve the site fingerprint exclusion and existing organization fingerprint key. Do not change menu numbers or call a live service.
