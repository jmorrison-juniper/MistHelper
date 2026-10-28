# Tasks: Zone Summary Validation

**Input**: [Specification](spec.md), [plan](plan.md), and the documents under `design/`.

## Phase 1: Setup

- [x] T001 Confirm source and test ownership, current-main content, issue reservations, and the bounded route in `plan.md`. (delivered: plan.md)

## Phase 2: Foundational Evidence

- [x] T002 Reproduce the false zero-site summary in `src/mist/intelligence/analytics/zone_analyzer.py`. The missing dictionary printed zero sites and no deviations. (delivered: design/research.md)

## Phase 3: User Story 1 - Reject Missing Statistics

**Goal**: Refuse incomplete statistics before a zone summary appears.

**Independent test**: Run the parameterized display-contract test through direct and combined display entry points.

- [x] T003 [US1] Add one parameterized test under `TestDisplayResults` in `tests/unit/test_zone_analyzer.py`. All 16 cases failed before repair. (delivered: tests/unit/test_zone_analyzer.py)
- [x] T004 [US1] Validate the required dictionary in `_display_zone_section`. One empty-default read was removed. (delivered: src/mist/intelligence/analytics/zone_analyzer.py)
- [x] T005 [US1] Confirm the refusal and compare accepted output. All 140 focused tests pass. Three original-output comparisons match exactly. (delivered: tests/unit/test_zone_analyzer.py)

## Phase 4: Evidence and Publication

- [x] T006 Add the release note and run local source gates. Ruff, Black, mypy, complexity, Bandit, docstring, symbol, and prose checks pass. (delivered: changelog.d/issue-2753-zone-summary-validation.md)
- [x] T007 Compare `spec.md`, `plan.md`, and `tasks.md`, then commit the exact feature manifest. Nine requirements have task coverage. (delivered: plan.md)
- [x] T008 Run the committed test-quality comparison. The changed-module and full checks both report zero new findings. (delivered: tests/unit/test_zone_analyzer.py)

The changed-module check examined one file and zero findings.
The full check examined 1,209 files and 611 accepted findings.
The baseline remains unchanged.
Publication requires the final evidence commit and the pull request with `Refs #2753`.

## Dependencies

T001 precedes T002. T002 precedes T003. T003 precedes T004. T004 precedes T005.
T005 precedes T006. T006 precedes T007. T007 precedes T008.

## Parallel Opportunities

The independent static gates can run together after T005.
The source and test edits remain serial to preserve the failure proof.

## Implementation Strategy

Deliver one complete display validation repair.
Do not absorb the campaign scan, other defaults, or sibling issue scopes.
Keep issue #2753 open.
Merge only after exact acceptance and every required check pass.
