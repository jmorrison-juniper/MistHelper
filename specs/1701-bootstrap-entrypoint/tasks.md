# Tasks: Bootstrap entry point

**Input**: Design documents from `specs/1701-bootstrap-entrypoint/`

**Prerequisites**: `plan.md`, `spec.md`

**Tests**: This change requires regression tests for passive import and single parse.

## Format

- `[P]` means the task can run in parallel with tasks that touch other files.
- Each task names the file that it changes.

## Phase 1: Setup

**Purpose**: Create the required SpecKit artifacts.

- [X] T001 Create `specs/1701-bootstrap-entrypoint/spec.md` with both issue scopes.
- [X] T002 Create `specs/1701-bootstrap-entrypoint/plan.md` with the technical approach.
- [X] T003 Create `specs/1701-bootstrap-entrypoint/tasks.md` with the work list.

## Phase 2: Bootstrap boundary

**Purpose**: Move import-time work behind an explicit class.

- [X] T004 Add `ApplicationBootstrap` to `src/refactors/main_entrypoint.py`.
- [X] T005 Move logging setup, data directory check, `.env` loading, dependency check, and import manager creation into `ApplicationBootstrap`.
- [X] T006 Change `MistHelper.py` to keep passive defaults at import.
- [X] T007 Change `wsgi.py` to call the web bootstrap without command-line parsing.

## Phase 3: Command-line parsing

**Purpose**: Remove raw command-line scans from `MistHelper.py`.

- [X] T008 Parse command-line arguments once in `ApplicationBootstrap`.
- [X] T009 Store the parsed namespace on the bootstrap object.
- [X] T010 Update runtime flags from the stored namespace.
- [X] T011 Remove the active unsupported variant guard from the entrypoint path.

## Phase 4: Regression tests

**Purpose**: Stop the defects from returning.

- [X] T012 Add the passive import regression test in `tests/unit/refactors/test_reject_unsupported_flag_variants.py`.
- [X] T013 Add the parse-count regression test in the same file.
- [X] T014 Update the bad flag test to assert the standard argparse error.

## Phase 5: Release note and analysis

**Purpose**: Record the user-visible change and final evidence.

- [X] T015 Add `changelog.d/issue-1701-bootstrap-entrypoint.md`.
- [X] T016 Add `specs/1701-bootstrap-entrypoint/analysis.md` with acceptance evidence.
- [X] T017 Run the local quality gates that finish promptly. CI must finish the full suite.
- [ ] T018 Open, watch, and merge the pull request.

## Dependencies

- T004 depends on T001 and T002.
- T006 depends on T004 and T005.
- T007 depends on T004.
- T012 through T014 depend on T004 through T011.
- T016 depends on the final gate output.
