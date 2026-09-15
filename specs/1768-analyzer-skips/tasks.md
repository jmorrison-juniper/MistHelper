---
description: "Task list for feature 1768-analyzer-skips"
---

# Tasks: Analyzer Skip Reporting

**Input**: Design documents from `specs/1768-analyzer-skips/`

**Prerequisites**: `spec.md`, `plan.md`

**Tests**: Required by issue #1768.

**Organization**: Tasks are ordered by dependency. Each story can be verified with a focused pytest target.

## Phase 1: Setup

- [x] T001 Create `specs/1768-analyzer-skips/spec.md` from the SpecKit template. (delivered: `specs/1768-analyzer-skips/spec.md`)
- [x] T002 Create `specs/1768-analyzer-skips/plan.md` from the SpecKit template. (delivered: `specs/1768-analyzer-skips/plan.md`)
- [x] T003 Create `specs/1768-analyzer-skips/tasks.md` from the SpecKit template. (delivered: `specs/1768-analyzer-skips/tasks.md`)

## Phase 2: Foundation

- [x] T004 Implement shared analyzer coverage records and renderers in `tools/analyzer_coverage.py`.
- [x] T005 Add tests for shared analyzer coverage in `tests/tools/test_analyzer_coverage.py`.

## Phase 3: User Story 1 - See the measured files

- [x] T006 Add read and skip coverage to `tools/compliance_analyzer/engine.py`, `tools/compliance_analyzer/__main__.py`, and `tools/compliance_analyzer/reporting.py`.
- [x] T007 Add read and skip coverage to `tools/refactor_analyzer/analysis.py`, `tools/refactor_analyzer/graph.py`, `tools/refactor_analyzer/__main__.py`, and `tools/refactor_analyzer/reporting.py`.
- [x] T008 Add read and skip coverage to `tools/ste_linter/cli.py` and `tools/ste_linter/report.py`.
- [x] T009 Add read and skip coverage to `tools/test_quality_analyzer/discovery.py`, `tools/test_quality_analyzer/__main__.py`, and `tools/test_quality_analyzer/reporting.py`.

## Phase 4: User Story 2 - Fail on an unintended skip

- [x] T010 Add compliance analyzer tests for explicit skipped targets and skip output in `tests/tools/test_compliance_analyzer_coverage.py`.
- [x] T011 Add STE linter tests for unsupported and missing paths in `tests/tools/test_ste_linter_coverage.py`.
- [x] T012 Add test quality analyzer tests for omitted roots and skip output under `tests/tools/test_quality_analyzer/`.

## Phase 5: User Story 3 - Know partial scope

- [x] T013 Add refactor analyzer tests for module graph read files and unresolved imports in `tests/tools/test_refactor_analyzer_coverage.py`.
- [x] T014 Add `scripts/run_repository_analyzers.py` as the documented whole-repository analyzer command.
- [x] T015 Add `tools` to the Bandit targets in `pyproject.toml`.

## Phase 6: Validation and Delivery

- [x] T016 Run focused pytest targets for the changed analyzer behavior.
- [x] T017 Run `python -m ruff check .`.
- [x] T018 Run `python -m black --check .`.
- [x] T019 Run mypy with the `MYPY_PATHS` from `.github/workflows/ci.yml`.
- [x] T020 Run each changed analyzer and record its output.
- [x] T021 Add `changelog.d/issue-1768-analyzer-skips.md`.
- [ ] T022 Commit, push, open the pull request, and wait for checks.
