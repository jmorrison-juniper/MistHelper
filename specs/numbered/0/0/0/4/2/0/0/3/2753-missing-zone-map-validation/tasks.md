---
description: "Tasks for missing zone map validation"
---

# Tasks: Missing Zone Map Validation

**Input**: Spec and plan in this feature directory, with supporting design files under `design/`.

**Prerequisites**: `spec.md`, `plan.md`, `design/research.md`, `design/data-model.md`, `design/quickstart.md`, and `design/contracts/missing-zone-display.md`

## Phase 1: Setup

**Purpose**: The repository and test structure already exist.

No setup tasks are required.

## Phase 2: Foundational

**Purpose**: The existing analyzer and test fixtures provide all required foundations.

No foundational tasks are required.

## Phase 3: User Story 1 - Trust the missing-zone summary (Priority: P1)

**Goal**: Reject incomplete missing-zone results and preserve valid report output.

**Independent Test**: Run `python -m pytest tests/unit/test_zone_analyzer.py` and confirm that invalid maps fail visibly while explicit empty and nonempty maps retain their output.

### Tests for User Story 1

- [x] T001 [US1] Add missing, null, wrong-type, explicit-empty, real-producer, and empty-section tests in `tests/unit/test_zone_analyzer.py`.

### Implementation for User Story 1

- [x] T002 [US1] Require a dictionary and log a `ValueError` in `_display_missing_zones` in `src/mist/intelligence/analytics/zone_analyzer.py`.
- [x] T003 [P] [US1] Add the issue-specific release note in `changelog.d/issue-2753-missing-zone-map-validation.md`.
- [x] T004 [US1] Temporarily restore the old fallback in `src/mist/intelligence/analytics/zone_analyzer.py` to prove the tests in `tests/unit/test_zone_analyzer.py` fail, restore validation, and run that test file.

## Dependencies and Execution Order

### Phase Dependencies

- Setup and foundational work need no changes.
- User Story 1 tests precede its source validation.
- The changelog task can run in parallel with source validation.
- Mutation evidence and focused tests follow the source and test changes.
- Commit the complete feature before the test-quality checks.

### User Story Dependencies

- **User Story 1 (P1)**: Independent. It needs no other story.

### Parallel Opportunities

- T003 can run while T002 is in progress because the tasks change separate files.
- No other task can run in parallel with T001 or T004 because they share the focused test file or depend on the validation.

## Implementation Strategy

### MVP First

1. Add the failing tests in T001.
2. Implement the contract in T002.
3. Add the release note in T003.
4. Prove the tests reject the old fallback and run the focused test file in T004.
5. Commit the feature files, then run the test-quality checks.

## Notes

- Keep the change limited to `_display_missing_zones`.
- Do not broaden `scripts/scan_2753.py` beyond comparator device IDs.
- Do not change the quality baseline or shared Spec Kit state.
- Stop before push or pull request creation.
