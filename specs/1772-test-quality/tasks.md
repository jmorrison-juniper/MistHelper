# Tasks: Issue 1772 test-quality triage

**Input**: Design documents from `specs\1772-test-quality\`

**Prerequisites**: plan.md and spec.md

**Tests**: A focused regression test proves the analyzer no longer reports pytest helper roots as high-severity untested source.

## Phase 1: Setup

- [X] T001 Read issues #1772 and #1768, then add the `in-progress` label to issue #1772. (delivered: GitHub issue state)
- [X] T002 Create the isolated worktree `..\MistHelper-1772-test-quality` from `origin/main`. (delivered: worktree)
- [X] T003 Bootstrap the virtual environment and confirm `mistapi` version 0.64.0. (delivered: `.venv`)
- [X] T004 Collect tests with `pytest --ignore=tests/e2e --collect-only -q --no-cov`. (delivered: collection output)

## Phase 2: Measurement and Triage

- [X] T005 Run `python -m tools.test_quality_analyzer` before repair. (delivered: `specs\1772-test-quality\triage.md`)
- [X] T006 Classify each high-severity finding by file, line, function, and reason. (delivered: `specs\1772-test-quality\triage.md`)
- [X] T007 Group every finding by severity and rule. (delivered: `specs\1772-test-quality\triage.md`)
- [X] T008 File follow-up issues for each deferred medium-severity group. (delivered: issues #2696 through #2711)

## Phase 3: Analyzer Repair

- [X] T009 Update `tools\test_quality_analyzer\__main__.py` so `UntestedDetector` skips real pytest roots as source-under-test roots. (delivered: `tools\test_quality_analyzer\__main__.py`)
- [X] T010 Preserve analyzer fixture roots as valid `UntestedDetector` source roots. (delivered: `tools\test_quality_analyzer\__main__.py`)
- [X] T011 Add a regression test for pytest helper roots. (delivered: `tests\tools\test_quality_analyzer\test_cli.py`)

## Phase 4: Validation

- [X] T012 Run targeted analyzer regression tests. (delivered: pytest output)
- [X] T013 Run ruff, black, mypy, focused pytest, analyzer, and guard proof audit.
- [X] T014 Run symbol checks for changed Python files if module-level names changed.

## Phase 5: Delivery

- [X] T015 Add the release-note fragment. (delivered: `changelog.d\issue-1772-test-quality.md`)
- [ ] T016 Commit, push, open the pull request, and wait for required checks.
- [ ] T017 Add `auto-merge` after every required check, including CodeQL, reports green.

