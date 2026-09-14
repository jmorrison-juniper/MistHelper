# Feature Specification: Speckit task record drift

**Feature Branch**: `chore/1741-speckit-task-drift`

**Created**: 2026-09-13

**Status**: Implemented

**Input**: Reconcile the speckit task records and guard against future drift.

## Background

Issue #1741 records four delivered specs whose task files kept 109 open boxes.
The status headers already say that the work merged. The task files disagreed.

The team decision is complete. Keep the task records. Reconcile the records to
reality. Add an automated guard that reports future drift.

Five task files are reserved for other agents. This feature must not edit them.
The reserved files are in `specs/006-web-interactivity/`,
`specs/001-wired-client-global-report/`,
`specs/003-menu1-compliance-refactor/`, `specs/001-mist-ops-platform/`, and
`specs/1016-misthelper-suppression-cleanup/`.

## User Scenarios & Testing

### User Story 1 - Read an accurate delivered spec (Priority: P1)

A contributor opens one delivered STE spec. The contributor reads checked task
boxes with a file path that proves the work exists.

**Why this priority**: The drift wastes review time and hides the delivery
state.

**Independent Test**: Count open and checked boxes in the four target task files.
The open count must change from 109 to 0.

**Acceptance Scenarios**:

1. **Given** a delivered target spec, **When** a contributor opens `tasks.md`,
   **Then** each delivered task carries a checked box and an evidence path.
2. **Given** a task without file proof, **When** the contributor reads the task,
   **Then** the task stays unchecked.

### User Story 2 - See drift before it merges (Priority: P1)

A maintainer reads a continuous integration report. The report lists each spec
that holds an unchecked task. A complete spec with unchecked tasks returns a
nonzero exit code.

**Why this priority**: The report stops the same drift from returning.

**Independent Test**: Run the audit tool against fixture specs with checked,
unchecked, missing, empty, malformed, nested, and fenced checkbox records.

**Acceptance Scenarios**:

1. **Given** a complete spec with an unchecked task, **When** the audit runs,
   **Then** the process exits nonzero and names the spec.
2. **Given** an allowed spec with an unchecked task, **When** the audit runs with
   the allow list, **Then** the process exits zero and marks the spec allowed.
3. **Given** a fenced code block that contains a checkbox, **When** the audit
   runs, **Then** the checkbox inside the block does not count.

### User Story 3 - Keep the template honest (Priority: P2)

A writer creates a new task file from the template. The template tells the
writer to tick a box only after file proof exists.

**Why this priority**: The template teaches the rule at the source.

**Independent Test**: Read `.specify/templates/tasks-template.md` and confirm it
states the evidence note rule.

## Edge Cases

- A spec directory can miss `tasks.md`. The audit reports the missing file.
- A task file can be empty. The audit reports no unchecked task.
- A task file can hold no checkbox. The audit reports no unchecked task.
- A task file can hold a malformed checkbox. The audit does not count it as a
  task.
- A nested task list can hold a checkbox. The audit counts it.
- A fenced code block can hold a checkbox example. The audit ignores it.

## Requirements

### Functional Requirements

- **FR-001**: The reconciliation MUST measure every `specs/*/tasks.md` file
  before it edits task records.
- **FR-002**: The reconciliation MUST not edit the five reserved task files.
- **FR-003**: The reconciliation MUST tick only tasks with a cited evidence
  file.
- **FR-004**: The reconciliation MUST leave unproved tasks unchecked and record
  them in `analysis.md`.
- **FR-005**: The audit tool MUST walk every direct spec directory under
  `specs/`.
- **FR-006**: The audit tool MUST count unchecked and checked task boxes outside
  fenced code blocks.
- **FR-007**: The audit tool MUST accept an allow-list file of spec names or
  spec paths.
- **FR-008**: The audit tool MUST return a nonzero exit code when a complete
  spec holds an unchecked task that the allow list does not cover.
- **FR-009**: The continuous integration workflow MUST run the audit as a
  non-blocking report.

### Key Entities

- **Task record**: A `tasks.md` file that holds checked and unchecked boxes.
- **Evidence note**: A file path after a checked task that proves delivery.
- **Allow list**: A text file whose lines name specs that may keep open tasks.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The four target specs move from 109 unchecked tasks to 0.
- **SC-002**: The audit test suite covers the happy path and the six edge cases.
- **SC-003**: The continuous integration report cannot block unrelated pull
  requests on day one.
- **SC-004**: `CHANGELOG.md` stays unchanged on this feature branch.

## Assumptions

- A complete spec has a status that contains `Implemented`, `Complete`,
  `Delivered`, or `Merged`.
- A status that contains `Draft`, `Specified`, `Specification`, or `Partly`
  remains in flight.
- The audit is advisory first because current `main` still holds open task
  records outside this issue.
