# Tasks: Grade Python user text in the STE linter

**Input**: Design documents from `specs/1684-ste-grade-strings/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, and `data-model.md`

**Tests**: Tests are required by issue #1684 and by FR-008.

## Phase 1: Specification

- [x] T001 Create the SpecKit feature directory for issue #1684.
- [x] T002 Write `specs/1684-ste-grade-strings/spec.md` with behavior, constraints, tests, and acceptance criteria.
- [x] T003 Write `specs/1684-ste-grade-strings/plan.md` with the technical approach.
- [x] T004 Write `specs/1684-ste-grade-strings/research.md` and `data-model.md` with real design content.

## Phase 2: Tests

- [x] T005 [P] Add parser tests for logging string spans in `tests/unit/ste_linter/test_parsing.py`.
- [x] T006 [P] Add parser tests for user-facing string spans in `tests/unit/ste_linter/test_parsing.py`.
- [x] T007 [P] Add parser tests for f-strings, lazy `%s` placeholders, implicit concatenation, empty strings, non-ASCII strings, and identifier-only strings.
- [x] T008 [P] Add CLI configuration tests for the opt-in flags.

## Phase 3: Implementation

- [x] T009 Add string-grading fields to `tools/ste_linter/config.py`.
- [x] T010 Pass the active configuration into the Python parser from `tools/ste_linter/parsing/__init__.py` and `tools/ste_linter/cli.py`.
- [x] T011 Implement logging string extraction in `tools/ste_linter/parsing/python_source.py`.
- [x] T012 Implement user-facing string extraction and text cleaning in `tools/ste_linter/parsing/python_source.py`.
- [x] T013 Update `tools/ste_linter/models.py` comments for the new span kinds.

## Phase 4: Release and proof

- [x] T014 Add `changelog.d/issue-1684-ste-grade-strings.md`.
- [x] T015 Run the targeted parser tests.
- [x] T016 Run the local ruff, black, mypy, and targeted pytest gates. Start the full pytest gate and defer the full-suite proof to pull request checks.
- [x] T017 Run the STE linter on itself with the new opt-in flags.
- [x] T018 Write `specs/1684-ste-grade-strings/analysis.md` with acceptance evidence.

## Dependencies and Execution Order

Phase 1 must finish before implementation. Phase 2 tests can run in parallel after Phase 1. Phase 3 depends on the tests. Phase 4 depends on Phase 3.
