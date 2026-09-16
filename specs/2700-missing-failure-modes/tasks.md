# Tasks: Missing failure mode triage

**Input**: `specs\2700-missing-failure-modes\spec.md` and `specs\2700-missing-failure-modes\plan.md`

**Prerequisites**: Current `origin/main`, a bootstrapped `.venv`, issue labels, and analyzer output.

## Phase 1: Setup

- [x] T001 Read issues #2700 through #2705, issue #2736, and issue #1772. (delivered: issue review in session output)
- [x] T002 Create `chore/2700-missing-failure-modes` in `..\MistHelper-2700-missing-fm`. (delivered: worktree)
- [x] T003 Bootstrap the worktree and verify `mistapi` 0.64.0. (delivered: `.venv`)

## Phase 2: Measurement

- [x] T004 Run the analyzer on current main and record the six current counts. (delivered: `specs\2700-missing-failure-modes\triage.md`)
- [x] T005 Classify each rule group as real, misfire, or accepted. (delivered: `specs\2700-missing-failure-modes\triage.md`)

## Phase 3: Detector repair

- [x] T006 [US1] Add source-under-test inference to `tools\test_quality_analyzer\detection\missing_failure_mode.py`. (delivered: `tools\test_quality_analyzer\detection\missing_failure_mode.py`)
- [x] T007 [US1] Add `MissingFailureModeDetector.inspected_modules` reporting. (delivered: `tools\test_quality_analyzer\detection\missing_failure_mode.py`)
- [x] T008 [US1] Make zero inspected-module metrics fail real analyzer runs. (delivered: `tools\test_quality_analyzer\__main__.py`)
- [x] T009 [US1] Add detector tests for value-object misfire and real Mist SDK scope. (delivered: `tests\tools\test_quality_analyzer\test_meta_fixtures.py`)

## Phase 4: Highest-risk test repair

- [x] T010 [US2] Add empty-body logging in `MistEndpointService._wrap`. (delivered: `mist-ops-platform\src\shared\mist\endpoints.py`)
- [x] T011 [US2] Add timeout, connection error, 5xx, malformed JSON, and empty-body tests. (delivered: `mist-ops-platform\tests\unit\mist\test_endpoint_retry.py`)

## Phase 5: Deferral and release record

- [x] T012 [US3] Create follow-up issues #2743 through #2748 for remaining rule work. (delivered: GitHub issues)
- [x] T013 [US3] Create one release-note fragment. (delivered: `changelog.d\issue-2700-missing-failure-modes.md`)
- [x] T014 [US3] Record the triage table and cut line. (delivered: `specs\2700-missing-failure-modes\triage.md`)

## Phase 6: Validation

- [x] T015 Run Ruff, Black, mypy, radon, targeted pytest, analyzer, guard audit, and suite shards. (delivered: final session report)
- [ ] T016 Open one pull request, watch checks, and add `auto-merge` only after all required checks pass. (delivered: pull request)
