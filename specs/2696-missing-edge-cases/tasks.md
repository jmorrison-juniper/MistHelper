# Tasks: Missing Edge Case Triage

**Input**: Design documents from `specs\2696-missing-edge-cases\`

**Prerequisites**: `plan.md`, `spec.md`, and `triage.md`.

**Tests**: The user requested tests and proof that repaired tests can fail.

## Phase 1: Setup

- [x] T001 Read issues #2696, #2697, #2698, #2699, and #1772. (delivered: GitHub issue output)
- [x] T002 Add the `in-progress` label to issues #2696, #2697, #2698, and #2699. (delivered: GitHub issue labels)
- [x] T003 Create worktree `..\MistHelper-2696-missing-ec` from `origin/main`. (delivered: worktree)
- [x] T004 Bootstrap the worktree and verify `mistapi` version `0.64.0`. (delivered: local command output)

## Phase 2: Measurement

- [x] T005 Re-measure `tools.test_quality_analyzer` before repair. (delivered: `tools\test_quality_analyzer\output\report.json`)
- [x] T006 Record current counts against issue counts. (delivered: `specs\2696-missing-edge-cases\triage.md`)
- [x] T007 Select the analyzer rule repair instead of a broad test sweep. (delivered: `specs\2696-missing-edge-cases\plan.md`)

## Phase 3: User Story 1 - Report only meaningful gaps

- [x] T008 Update `MissingEdgeCaseDetector` to require `test-quality: edge-case-required=` before emitting findings. (delivered: `tools\test_quality_analyzer\detection\missing_edge_case.py`)
- [x] T009 Add source-under-test call filtering for mock helpers, fixture factories, and HTTP status helpers. (delivered: `tools\test_quality_analyzer\detection\missing_edge_case.py`)
- [x] T010 Add a regression test that proves support calls do not emit missing edge-case findings. (delivered: `tests\tools\test_quality_analyzer\test_meta_fixtures.py`)

## Phase 4: User Story 2 - Preserve opt-in checks

- [x] T011 Update the bad numeric fixture to use the explicit numeric marker. (delivered: `tools\test_quality_analyzer\fixtures\bad\test_missing_edge_case_bad.py`)
- [x] T012 Update the good numeric fixture to use the explicit numeric marker. (delivered: `tools\test_quality_analyzer\fixtures\good\test_missing_edge_case_good.py`)
- [x] T013 Add a regression test that proves a marked collection gap still emits `missing_ec_empty_input`. (delivered: `tests\tools\test_quality_analyzer\test_meta_fixtures.py`)
- [x] T014 Update the performance hook catalog for the renamed detector helper. (delivered: `specs\2448-misthelper-performance-monitoring\artifacts\hook-catalog.csv`)

## Phase 5: Validation and pull request

- [x] T015 Run targeted detector tests. (delivered: local command output)
- [x] T016 Prove each repaired test can fail by mutation. (delivered: local mutation output)
- [x] T017 Run all requested local gates. (delivered: local gate output)
- [x] T018 Add release note `changelog.d\issue-2696-missing-edge-cases.md`. (delivered: changelog fragment)
- [ ] T019 Commit, push, open the pull request, and wait for required checks. (pending)
- [ ] T020 Verify issue closure or close the issues by hand after merge. (pending)

## Dependencies & Execution Order

Setup tasks T001 through T004 precede measurement. Measurement tasks T005 through T007 precede implementation. Implementation tasks T008 through T014 precede validation. Validation tasks T015 through T017 precede pull request tasks T018 through T020.
