# Tasks: Strict entry-point type repairs

## Phase 1: Setup

- [x] T001 Verify current main and the locked environment in `design/research.md`. (delivered: design/research.md)
- [x] T002 Resolve the managed feature route and validate `spec.md`. (delivered: spec.md)

## Phase 2: Foundational contracts

- [x] T003 Confirm the narrow annotation handoffs in `analysis.md` before affected edits.
- [x] T004 Record the complete diagnostic groups and source contract choices in `analysis.md`. (delivered: analysis.md)

## Phase 3: User Story 1 - Trust diagnostics

**Goal**: Zero strict entry-point errors without suppression.

**Independent test**: One analyzed file and zero strict errors.

- [x] T005 [US1] Correct local inferred collections and exception scope in `MistHelper.py`. (delivered: MistHelper.py)
- [x] T006 [US1] Correct optional import contracts and typed dynamic module methods in `MistHelper.py`. (delivered: MistHelper.py)
- [x] T007 [US1] Express actual dynamic dispatch contracts without dummy references in `MistHelper.py`. (delivered: MistHelper.py)
- [x] T008 [US1] Correct required shared callback and record contracts under `src/`.
- [x] T009 [US1] Resolve the reserved portal signature contract in `web_portal/app.py` after handoff. (delivered: web_portal/app.py)
- [ ] T010 [US1] Record a verified zero-error strict report in `analysis.md`.

## Phase 4: User Story 2 - Preserve behavior

**Goal**: Preserve commands, session state, and optional dependency behavior.

**Independent test**: Focused mocked regressions and symbol comparison pass.

- [x] T011 [US2] Add focused edge and integration cases in the established entry-point test tree under `tests/unit/`. (delivered: tests/unit/refactors/test_app_context_session_state.py)
- [x] T012 [US2] Run applicable tests and standard gates, then record exact outcomes in `analysis.md`. (delivered: analysis.md)
- [x] T013 [US2] Compare module-level symbols against the base and record results in `analysis.md`. (delivered: analysis.md)

## Phase 5: Completion

- [x] T014 Record unrelated defects separately and retain their issue references in `analysis.md`. (delivered: analysis.md)
- [x] T015 Update the unique release note in `changelog.d/issue-4758-strict-pyright-repairs.md`. (delivered: changelog.d/issue-4758-strict-pyright-repairs.md)
- [x] T016 Commit verified local work and record the commit identifier without publication. (delivered: analysis.md)

## Dependencies and execution order

T001 and T002 precede every repair.
T003 blocks only reserved files, including T009.
T004 precedes T005 through T008.
T005 through T009 precede T010.
T011 can proceed with each corresponding source repair.
T012 and T013 precede T016.
T014 and T015 precede T016.

## Parallel examples

Ownership review can run with baseline analysis.
Independent source annotations can run with focused tests in separate files.
Do not edit the same file concurrently.

## Implementation strategy

Repair the smallest diagnostic group first.
Measure strict diagnostics after each coherent group.
Preserve unchecked tasks when an ownership blocker prevents completion.
Optional commit hooks remain deferred to the verified local commit.

## Remaining work

T007 includes the approved authentication-status definition and initializer-reference rename.
The initializer audit found no additional private helper without a surviving root caller.
The cleanup removes all nine audited declarations and four helpers used only by the removed code.
The updated tests exercise real help, session validation, and dependency initialization behavior.
T008 and T003 are complete under the later direct authorization.
T010 remains open until the refreshed-main combined strict report passes.
