# Feature Specification: SpecKit Task Audit Link and Legend Classification

**Feature Branch**: `fix/4703-speckit-audit-markdown-links`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4703, "CI: SpecKit task audit counts Markdown links and legends as malformed". Labels: `bug`, `ci`, `in-progress`.

## Clarifications

### Session 2026-11-26

- Q: Does MistHelper need a new devtools pin? A: No. `requirements-dev.txt` line 197 already pins commit `2239e7bd` on `main`. That commit holds the repair. Evidence: RC-11, RC-23.
- Q: Does the failure still reproduce on `main`? A: No. Run 45774119357 reports zero malformed markers. Evidence: design/research.md, section R1.
- Q: Is the audit job still advisory? A: Yes. The job sets `continue-on-error: true`, and its step ends with `|| true`. Evidence: RC-01, RC-02.
- Q: Does a second failure mode exist? A: Yes. Run 45064243269 fails at dependency install before the audit runs. That failure is out of scope. Decision D-7.
- Q: Does the issue trail authorize the pin update? A: No explicit authorization appears in issue #4703 or issue #4765. The item is Unverified. Decision D-6.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read an audit report that counts real markers (Priority: P1)

A maintainer reads the SpecKit task audit report in the Quality Gates run. The report does not count a legend bullet or a Markdown link line as a malformed marker.

**Why this priority**: The defect misleads every reader of the report. Commit 3964d21 showed 36 malformed markers with no location.

**Independent Test**: Scan a tasks file that holds one legend bullet and one Markdown link line. The scanner returns zero checked, zero unchecked, and zero malformed markers.

**Acceptance Scenarios**:

1. **Given** a tasks file with a legend bullet and a Markdown link line, **When** the scanner counts the file, **Then** the malformed count is zero.
2. **Given** the pinned devtools commit on `main`, **When** the audit job runs, **Then** the report states zero malformed markers.

### User Story 2 - Find each real malformed marker by file and line (Priority: P1)

A maintainer finds each real malformed marker from the report. The report names the file path and the line number of each marker.

**Why this priority**: An author cannot repair a marker without its location.

**Independent Test**: Scan a tasks file with a legend bullet, a link line, and the marker `- [ab] T009 Broken box` on line 3. The scanner returns one malformed marker at line 3.

**Acceptance Scenarios**:

1. **Given** a real malformed marker on line 3, **When** the scanner counts the file, **Then** the malformed line tuple is `(3,)`.

### User Story 3 - Keep the pin that holds the repair (Priority: P2)

A maintainer changes `requirements-dev.txt` in a later change. The regression test fails when the pinned tool counts the sample lines as malformed.

**Why this priority**: The issue-time pin `e8e093d` reported 36 false positives at commit 3964d21. The regression test catches that change before merge.

**Independent Test**: Run the negative regression test with the issue-time pin. The test fails, because that code counts both sample lines.

**Acceptance Scenarios**:

1. **Given** commit `e8e093d` as the pinned tool, **When** the negative regression test runs, **Then** the test fails.

### Edge Cases

- A legend label followed by a task ID, such as `- [P] T001 Create the file`, stays malformed. The task ID shows a task attempt.
- A bracketed bullet whose label matches a defined reference definition is prose, not a malformed marker.
- A bad box inside a fenced code block is not counted.
- Caution: Do not edit a legend or a link line to silence the audit. The edit hides the defect that the regression test guards.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The SpecKit task audit MUST NOT count a legend bullet or a Markdown link line as a malformed task marker.
- **FR-002**: The SpecKit task audit MUST report the file path and line number of each real malformed task marker.
- **FR-003**: `requirements-dev.txt` MUST pin misthelper-devtools to a commit that contains the repair in `speckit_task_audit.py`.

### Mist Cloud Transport Requirements *(include if feature uses Mist Cloud)*

Not applicable: this feature sends no request to the Mist Cloud.

### Key Entities *(include if feature involves data)*

- **TaskMarkerLine**: One line of a `tasks.md` file. Its natural key is the repository path plus the line number. Its states appear in `design/data-model.md`.
- **PinnedDevtoolsCommit**: The misthelper-devtools commit named in `requirements-dev.txt`. Its natural key is the 40-character commit SHA.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The audit job on `main` reports zero malformed markers in its log.
- **SC-002**: The two regression tests pass in the Quality Gates run for the feature branch.
- **SC-003**: The positive regression test finds exactly one malformed marker, at line 3 of its fixture file.

## Assumptions

- The SpecKit task audit keeps the output strings that `tests/guardrails/test_spec_route_contract.py` asserts.
- The repository owner authorizes the merge before auto-merge is enabled.
- The pinned upstream commit `2239e7bd` does not change during this work.

## Non-Goals

- Change the advisory status of the audit job or its `|| true` step. Decision D-2.
- Fix the unchecked tasks or the missing task files that the audit reports.
- Resolve the `mando` dependency conflict in PR #4888. Decision D-7.
- Change the upstream repository. The repair already merged as commit `da96d6e`.
- Change menus, containers, Mist API code, or the operator guide.
