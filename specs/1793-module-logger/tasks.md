# Tasks: Module logger sweep for firmware manager

**Input**: Design documents from `specs/1793-module-logger/`

**Prerequisites**: `plan.md` and `spec.md`

**Tests**: Run the local gates and the two pytest shards required by the issue.

## Phase 1: Setup

- [x] T001 Read issue #1793 and the linked chain issues #1794 and #1766.
  (delivered: GitHub issue context)
- [x] T002 Create the worktree `..\MistHelper-1793-module-logger` from
  `origin/main`. (delivered: worktree)
- [x] T003 Bootstrap the worktree virtual environment. (delivered: `.venv`)

## Phase 2: Measurement

- [x] T004 Count eligible root logger calls across Python files.
  (delivered: 5793 before the sweep)
- [x] T005 Select `src/firmware/firmware_manager.py` as the reviewable subset.
  (delivered: 236 call sites)
- [x] T006 Search tests for `src.*.logging` string patch targets.
  (delivered: zero matches)
- [x] T007 Create follow-up issues for remaining areas.
  (delivered: #2768 through #2779)

## Phase 3: Implementation

- [x] T008 Add a module logger to `src/firmware/firmware_manager.py`.
  (delivered: `src/firmware/firmware_manager.py`)
- [x] T009 Replace eligible root logger calls in
  `src/firmware/firmware_manager.py`. (delivered:
  `src/firmware/firmware_manager.py`)
- [x] T010 Add the release note fragment.
  (delivered: `changelog.d/issue-1793-module-logger.md`)

## Phase 4: Validation

- [ ] T011 Run py_compile on `src/firmware/firmware_manager.py`.
- [ ] T012 Run ruff across the repository.
- [ ] T013 Run black check across the repository.
- [ ] T014 Run mypy across the configured scope.
- [ ] T015 Run pylint across the configured scope.
- [ ] T016 Run radon across the configured scope.
- [ ] T017 Run guard proof audit.
- [ ] T018 Run symbol diff for `src/firmware/firmware_manager.py`.
- [ ] T019 Run the `tests/unit` pytest shard.
- [ ] T020 Run the contract, guardrail, and integration pytest shard.

## Dependencies

- T004 depends on T003.
- T008 depends on T005.
- T009 depends on T008.
- T011 through T020 depend on T009.
