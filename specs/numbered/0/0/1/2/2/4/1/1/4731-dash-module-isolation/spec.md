# Feature Specification: Dash module isolation for map callback tests

**Feature Branch**: `4731-dash-module-isolation`

**Created**: 2026-11-26

**Status**: Complete for the specification. Publication waits for the owner to release the hold.

**Input**: User description: "Issue #4731: Test failure: Map callback tests replace the Dash module during collection"

## Clarifications

### Session 2026-11-26

- Q: Which callback test files remain open on main? A: Wave A, wave B/C, wave D, and wave E2. Wave E1 merged through PR #4735 on 2026-11-10.
- Q: Does the issue include the #2708 assertion work? A: Yes. The owner named the wave A and wave E2 assertion candidates. Wave A also has a second weak check at line 134. See D-4.
- Q: Does this record lift the publication hold? A: No. The owner releases the hold. This record prepares the publication only.
- Q: May a slice reuse the held candidate commits? A: No. See D-2.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Keep the real dash entry through collection (Priority: P1)

A test run leaves `sys.modules['dash']` exactly as it was before collection. When Dash was loaded before the run, `from dash import Dash` still succeeds after the run.

**Why this priority**: The leaked stub breaks every later import of Dash in the same process. Unrelated tests and tools fail with it.

**Independent Test**: Run the collection probe in quickstart QS-02 for one slice file. The probe reports an unchanged dash entry and a successful import.

**Acceptance Scenarios**:

1. **Given** Dash is loaded before collection, **When** a slice file is collected, **Then** the dash entry is the same module object after collection.
2. **Given** Dash is absent before collection, **When** a slice file is collected, **Then** Dash is absent after collection.

### User Story 2 - Keep the callback tests and their meaning (Priority: P1)

Every existing callback test keeps its name, its parameters, and its meaning. The only assertion changes are the ones named in FR-007, FR-008, and FR-010.

**Why this priority**: The repair must not reduce the coverage of the callback code.

**Independent Test**: Run `python -m pytest tests/maps`. The run exits 0 after each slice.

**Acceptance Scenarios**:

1. **Given** a slice is applied, **When** its test file runs, **Then** every test in the file passes.
2. **Given** the wave A line 181 check uses identity, **When** the forwarded `html` object differs from the stub `html`, **Then** the test fails.

### User Story 3 - Publish each slice in serial order (Priority: P2)

Each slice becomes one pull request. Only one slice pull request is open at a time. The final pull request closes the issue.

**Why this priority**: The owner holds serial publication. The issue stays open until all five files merge.

**Independent Test**: The publication checklist in design/checklists/publication.md is complete for each pull request.

**Acceptance Scenarios**:

1. **Given** a slice passed its local gates, **When** the owner releases the hold, **Then** its pull request opens after the previous pull request merges.
2. **Given** the final slice merges, **When** its checks pass, **Then** GitHub closes issue 4731.

### Edge Cases

- Dash is loaded before collection: the fixture restores the same module object.
- Dash is absent before collection: the fixture removes the stub and leaves Dash absent.
- The dash entry is None before collection: the fixture restores None. It does not remove the entry.
- A test body raises an exception: the `finally` block still restores the dash entry.
- The launcher import fails during collection: no stub remains, because the module no longer installs one at import time.
- Wave E1 keeps its scoped install from PR #4735: the four slices do not change it.
- Baseline entries for wave A and wave E2 become stale after their findings are fixed: the gate reports them as advisory only.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Each slice MUST NOT assign `sys.modules['dash']` at module import time.
- **FR-002**: Each autouse fixture MUST record whether the dash entry exists before it installs the stub.
- **FR-003**: Each autouse fixture MUST restore the loaded module object, the None entry, or the absent state exactly.
- **FR-004**: Each autouse fixture MUST restore state in a `finally` block, so a failed test still restores state.
- **FR-005**: Each slice MUST keep `_build_dash_stub` unchanged in name, body, and return value.
- **FR-006**: Each slice MUST keep the launcher import at module level with its existing `# noqa: E402` comment.
- **FR-007**: Wave A MUST replace the non-None check at line 134 with a function or bound-method type check.
- **FR-008**: Wave A MUST compare the forwarded `html` object with the stub `html` by identity at line 181.
- **FR-009**: The wave A autouse fixture MUST yield the active stub, so the line 181 test can read `html`.
- **FR-010**: Wave E2 MUST pass named serializer and figure-builder objects into `_make_state` and assert identity.
- **FR-011**: Each slice MUST keep all existing test names, parameters, and assertions, except those in FR-007, FR-008, and FR-010.
- **FR-012**: Each slice MUST NOT add or remove a module-level name, including an import.
- **FR-013**: A changed fixture MUST use a function-local import for `logging`.
- **FR-014**: A changed fixture MUST log info before and debug after each state change, using `%s` arguments.
- **FR-015**: Each changed line MUST carry an inline comment that gives its purpose and fit within 120 characters.
- **FR-016**: Each slice MUST change only its own test file and one changelog fragment.
- **FR-017**: No slice MUST change a baseline file, add a suppression, or edit an existing `noqa` comment.
- **FR-018**: Each slice MUST pass the local Lint, Format, Compile, Test, Test quality, and Symbols gates before publication.
- **FR-019**: Each slice MUST show zero new test-quality findings against the unchanged baseline.
- **FR-020**: Combined collection of the five test files MUST leave the dash entry unchanged, in forward and reverse order.
- **FR-021**: With Dash absent before collection, combined collection MUST leave Dash absent.
- **FR-022**: Each pull request MUST add one changelog fragment named `pr-` followed by the pull request number.
- **FR-023**: Publication MUST NOT start until the owner releases the publication hold.
- **FR-024**: Publication MUST follow this order: wave A, wave B/C, wave D, and wave E2.
- **FR-025**: Each pull request MUST wait until the previous pull request merges.
- **FR-026**: Only the final pull request MUST contain `Closes #4731`. Each earlier pull request MUST contain `Refs #4731`.
- **FR-027**: No slice MUST rebase, amend, or push a held candidate commit.
- **FR-028**: Each pull request body MUST list the local gate results and the red-control result.
- **FR-029**: No slice MUST change the merged wave E1 file.

### Key Entities

- **Dash entry**: The key `dash` in `sys.modules`. Its state is a loaded module, a None entry, or absent.
- **Stub**: The synthetic module that `_build_dash_stub` returns. It exists only while one test runs.
- **Slice**: One test file repair. Its natural key is the repository path.
- **Held candidate commit**: A local commit that the owner keeps unchanged on an owner branch. Its natural key is the commit SHA.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Each slice file leaves the dash entry unchanged after its own collection. Quickstart QS-02 prints True for each file.
- **SC-002**: Each slice file leaves Dash absent when Dash was absent. Quickstart QS-03 prints True for each file.
- **SC-003**: Combined collection of the five files leaves the dash entry unchanged in forward and reverse order. QS-05 and QS-06 print True. QS-07 prints True for the absent state.
- **SC-004**: `python -m pytest tests/maps` exits 0 after the final slice merges. Quickstart QS-13.
- **SC-005**: Each slice shows the expected results for Lint, Format, Compile, Test quality, and Symbols. Quickstart QS-08 to QS-12.
- **SC-006**: Issue 4731 closes when the final slice merges. No earlier pull request closes it.
- **SC-007**: Each slice pull request changes one test file and one changelog fragment. Quickstart QS-16.
- **SC-008**: No slice changes the merged wave E1 file or the test-quality baseline. Quickstart QS-16.

## Assumptions

- The local HEAD equals remote main `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. Research rows R01 and R02 to R11 confirm the blob SHAs.
- The `.venv` directory holds the project dependencies, including dash. Research row R27 confirms the installed package path.
- The owner releases the publication hold before any slice publishes.
- The implementer runs the local gates on a Windows host with the project virtual environment.

## Out of Scope

- Edits to wave E1. PR #4735 merged that slice.
- Edits to any file outside the four slice files, except one changelog fragment for each pull request.
- Edits to `.github/test-quality-baseline.json`.
- Triage of weak assertions beyond wave A lines 134 and 181 and wave E2 lines 174 and 178.
- Issue #4728, which covers the root logger at DEBUG. It is related but separate.
- A permanent collection guard test. The record recommends it as a follow-up issue. See D-3.
- Product code in `src/`.
- Action logging for wave E1. It is existing debt. See D-14.
