# Tasks: Isolated AppContext State

**Input**: Design documents from `/specs/2667-appcontext-state/`
**Prerequisites**: `spec.md`, `plan.md`

**Tests**: Included. The regression test must fail before the implementation and pass after it.

## Format: `[ID] [P?] Description`

- **[P]**: Can run in parallel with another task that touches different files.
- Each task names its exact file path.

## Phase 1: Setup

- [x] T001 Read issue #2667, the repository instructions, the SpecKit constitution, the STE guide, the SpecKit templates, and existing feature artifacts.
- [x] T002 Create worktree `..\MistHelper-2667-appcontext` from `origin/main` on branch `fix/2667-appcontext-state`.
- [x] T003 Check open pull requests for `MistHelper.py` overlap before editing.

## Phase 2: Regression Tests

- [x] T004 Update `tests/unit/refactors/test_app_context_session_state.py` so two default `ApplicationBootstrap(parse_cli=False)` objects must not share an `AppContext`.
- [x] T005 Update `tests/unit/refactors/test_main_entrypoint.py` so `MainEntrypoint.run()` passes an invocation context into `ApplicationBootstrap`.

## Phase 3: Implementation

- [x] T006 Update `src/refactors/main_entrypoint.py` so `ApplicationBootstrap` accepts an optional explicit context and creates a new `AppContext` when none is supplied.
- [x] T007 Update `src/refactors/main_entrypoint.py` so bootstrap activation publishes the invocation context before startup side effects.
- [x] T008 Update `src/refactors/main_entrypoint.py` so `MainEntrypoint.run()` creates a fresh context for each invocation.

## Phase 4: Release Note

- [x] T009 Add `changelog.d\issue-2667-appcontext-state.md` with one `Fixed` entry for issue #2667.

## Phase 5: Validation and Delivery

- [x] T010 Run the focused regression test before the implementation and record the failing output.
- [x] T011 Run `python -m py_compile MistHelper.py`.
- [x] T012 Run `python -m ruff check .`.
- [x] T013 Run `python -m black --check .`.
- [x] T014 Run `python -m mypy $MYPY_PATHS --config-file pyproject.toml` with the value from `.github\workflows\ci.yml`.
- [x] T015 Run focused pytest for the changed tests.
- [ ] T016 Commit, push, open the pull request, wait for checks, and add `auto-merge` only after all required checks pass.
