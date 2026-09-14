# Tasks: Speckit task record drift

**Input**: Design documents from `specs/1741-speckit-task-drift/`

**Prerequisites**: `spec.md` and `plan.md`

**Tests**: The audit tool needs unit tests for the happy path and the listed edge
cases.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: The task can run at the same time as its neighbors.
- **[Story]**: The user story of the task.
- Each task names the exact file that it creates or changes.

## Phase 1: Setup

- [X] T001 Create the SpecKit specification at
  `specs/1741-speckit-task-drift/spec.md`. (delivered: specs/1741-speckit-task-drift/spec.md)
- [X] T002 Create the implementation plan at
  `specs/1741-speckit-task-drift/plan.md`. (delivered: specs/1741-speckit-task-drift/plan.md)
- [X] T003 Measure all task records before reconciliation. (delivered: specs/1741-speckit-task-drift/analysis.md)

## Phase 2: User Story 1 - Read an accurate delivered spec

- [X] T004 [US1] Reconcile `specs/1026-ste-linter/tasks.md` with file evidence. (delivered: specs/1026-ste-linter/tasks.md)
- [X] T005 [US1] Reconcile `specs/1027-ste-dict-extractor/tasks.md` with file evidence. (delivered: specs/1027-ste-dict-extractor/tasks.md)
- [X] T006 [US1] Reconcile `specs/1028-ste-compliance-cleanup/tasks.md` with file evidence. (delivered: specs/1028-ste-compliance-cleanup/tasks.md)
- [X] T007 [US1] Reconcile `specs/1030-ste-src-cleanup/tasks.md` with file evidence. (delivered: specs/1030-ste-src-cleanup/tasks.md)
- [X] T008 [US1] Leave the five reserved task files unchanged. (delivered: specs/1741-speckit-task-drift/analysis.md)

## Phase 3: User Story 2 - See drift before it merges

- [X] T009 [US2] Add the audit tool at `tools/speckit_task_audit.py`. (delivered: tools/speckit_task_audit.py)
- [X] T010 [US2] Add unit tests at `tests/unit/tools/test_speckit_task_audit.py`. (delivered: tests/unit/tools/test_speckit_task_audit.py)
- [X] T011 [US2] Add the advisory workflow job to `.github/workflows/ci.yml`. (delivered: .github/workflows/ci.yml)

## Phase 4: User Story 3 - Keep the template honest

- [X] T012 [US3] Add the evidence-note rule to `.specify/templates/tasks-template.md`. (delivered: .specify/templates/tasks-template.md)
- [X] T013 Add the release-note fragment. (delivered: changelog.d/issue-1741-speckit-task-drift.md)
- [X] T014 Run the requested quality gates and record the result. (delivered: specs/1741-speckit-task-drift/analysis.md)

## Dependencies

- Phase 1 comes before any edit.
- User Story 1 and User Story 2 can proceed after Phase 1.
- User Story 3 follows the audit design.
- T014 comes last.
