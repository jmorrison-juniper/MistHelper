# Tasks: Application context

**Input**: Design documents from `specs/1702-app-context/`

**Prerequisites**: `plan.md`, `spec.md`

**Tests**: This change requires regression tests for context ownership and session configuration.

## Format

- `[P]` means the task can run in parallel with tasks that touch other files.
- Each task names the file that it changes.

## Phase 1: Setup

**Purpose**: Create the required SpecKit artifacts.

- [X] T001 Create `specs/1702-app-context/spec.md` for issues #1702 and #1712.
- [X] T002 Create `specs/1702-app-context/plan.md` with the technical approach.
- [X] T003 Create `specs/1702-app-context/tasks.md` with the work list.

## Phase 2: Context ownership

**Purpose**: Move live session state into one explicit object.

- [X] T004 Add `AppContext` to `src/refactors/main_entrypoint.py`.
- [X] T005 Store parsed arguments on the context during bootstrap.
- [X] T006 Replace MistHelper session-state reads with context reads.
- [X] T007 Remove `ConfigUtils` mirror calls from `MistHelper.py`.

## Phase 3: Session construction seam

**Purpose**: Remove run-time patching from normal session setup.

- [X] T008 Add `MistSessionConfigurator` to `src/refactors/initialize_mist_session.py`.
- [X] T009 Configure the request timeout once per context.
- [X] T010 Validate `mist_get` or `get` without adding an attribute.
- [X] T011 Store token login state on `AppContext`.
- [X] T012 Store interactive login state on `AppContext`.

## Phase 4: Regression tests

**Purpose**: Stop the defects from returning.

- [X] T013 Add a no-live-session-global test.
- [X] T014 Add a two-context isolation test.
- [X] T015 Add a configure-once and no-`mist_get` patch test.
- [X] T016 Add missing token, placeholder token, absent `.env`, and second bootstrap tests.

## Phase 5: Release note and analysis

**Purpose**: Record the user-visible change and final evidence.

- [X] T017 Add `changelog.d/issue-1702-app-context.md`.
- [X] T018 Add `specs/1702-app-context/analysis.md` with acceptance evidence.
- [X] T019 Run the local quality gates that finish promptly. CI must finish the full coverage gate.
- [ ] T020 Open, watch, and merge the pull request.

## Dependencies

- T004 depends on T001 and T002.
- T006 depends on T004 and T005.
- T008 depends on T004.
- T013 through T016 depend on T004 through T012.
- T018 depends on final gate output.

