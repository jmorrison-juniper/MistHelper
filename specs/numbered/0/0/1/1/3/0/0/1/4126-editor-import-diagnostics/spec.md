# Feature Specification: Editor Import Diagnostics

**Feature Branch**: `chore/4126-editor-import-diagnostics`

**Created**: 2026-11-26

**Status**: Draft

**Issue**: #4126, state OPEN. Labels: `needs-investigation`, `lint`, `docs`, `in-progress`, `workflow`, `tools`.

**Input**: Issue #4126 reports 534 E0401 and E0611 diagnostics in 27 files. Pylint run from the worktree root reports none. The editor resolves the same imports against the main checkout.

## Clarifications

### Session 2026-11-26

- Q: Which editor does the documented setup target? → A: Visual Studio Code with the Microsoft Python and Pylint extensions. `documentation/development-setup.md` line 204 states this.
- Q: Which closing keyword may the pull request use? → A: `Refs #4126` only. The owner keeps the issue open until live evidence exists. See decision D-6.
- Q: Do the 27 paths in the issue still exist? → A: Ten do not. They moved from `src/org/juniper_rma/` to `src/operations/exporting/juniper_rma/`. See rows R03 to R12 and R28 in `design/research.md`.
- Q: Does the repository Pylint configuration add the working directory? → A: Yes. `pyproject.toml` line 566 adds it through `init-hook`. See row R51.
- Q: Can this agent run the live editor check? → A: No. Analyzers are forbidden for this task. The 2026-10-31 issue comment reports a missing Screen Recording permission.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Confirm no import diagnostics in the worktree editor window (Priority: P1)

An operator opens only the worktree root in an editor window. The operator selects the worktree interpreter and restarts the Pylint server. The editor then shows no E0401 and no E0611 diagnostic for each current path.

**Why this priority**: This check closes the reported defect. The issue cannot close without it.

**Independent Test**: Run the live editor check for the 27 current paths in one worktree window. Run the terminal check for the same paths. Record one evidence row for each path.

**Acceptance Scenarios**:

1. **Given** only the worktree root is open, **When** the operator restarts Pylint and saves each file, **Then** no E0401 or E0611 diagnostic appears.
2. **Given** the main checkout is the window folder, **When** the operator runs the check, **Then** the row records the wrong root and a fail result.
3. **Given** the interpreter is not the worktree `.venv`, **When** the operator runs the check, **Then** the row records the interpreter and a fail result.

---

### User Story 2 - Check the affected file list against main before the live check (Priority: P1)

A maintainer compares the 27 listed paths and the 8 cited lines with the remote `main` branch. The maintainer then uses the current paths and the current line content for the live check.

**Why this priority**: The listed paths and line numbers no longer match `main`. A check on stale paths gives false results.

**Independent Test**: Run the remote tree filter and the remote line check. Compare each result with the remote verification table in `design/research.md`.

**Acceptance Scenarios**:

1. **Given** the issue lists `src/org/juniper_rma` paths, **When** the maintainer reads the remote tree, **Then** the record shows ten moved files.
2. **Given** the issue cites eight lines in `MistHelper.py`, **When** the maintainer reads them on `main`, **Then** the record shows their current content.

---

### User Story 3 - Keep the issue open until live evidence exists (Priority: P2)

A reviewer checks the pull request body and the issue state. The pull request uses `Refs #4126`. The issue stays open after the merge.

**Why this priority**: The owner requires live evidence before closure. An early closure hides the open work.

**Independent Test**: Read the pull request body before the merge. Read the issue state after the merge.

**Acceptance Scenarios**:

1. **Given** the pull request body, **When** the reviewer searches for a closing keyword, **Then** no closing keyword for issue #4126 appears.
2. **Given** the merge completed, **When** the reviewer reads the issue state, **Then** the state is OPEN.

---

### User Story 4 - Record evidence that another reviewer can repeat (Priority: P2)

An operator records the interpreter, root, extension version, time, and counts for each file. Another reviewer repeats the check with the same fields.

**Why this priority**: The owner asks for evidence on the issue. A bare pass gives no audit trail.

**Independent Test**: Compare one evidence row with the output contract in `design/contracts/editor-evidence.md`.

**Acceptance Scenarios**:

1. **Given** a completed live check, **When** a reviewer reads the evidence rows, **Then** each row contains every field of the output contract.

### Edge Cases

- The editor window contains both the main checkout and the worktree. The row records which root Pylint used. The check fails when the main checkout is the root.
- The worktree still uses the old `src/org/juniper_rma/` layout. The moved paths do not exist there. The operator rebases onto `main` before the check.
- The workspace setting `pylint.importStrategy` is `fromEnvironment`. The extension description says `pylint.path` may be ignored in that mode. The evidence row records the Pylint command from the output.
- A moved file moves again. The operator repeats the terminal and live checks for the new current path.
- macOS Screen Recording permission is missing. The live check stops. A terminal pass does not replace the live check.
- The Pylint or VS Code extension updates. The operator repeats the live check and records the new versions.
- The `.vscode/` settings are local and git-ignored. Each new worktree needs its own settings.
- Caution: a commit or pull request body with `Closes #4126` closes the issue at merge. Reopening the issue is a manual step.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The editor window MUST open the worktree root as its only folder during each live check.
- **FR-002**: The editor MUST use the worktree `.venv` interpreter for Pylint and for the Python extension during the check.
- **FR-003**: The check MUST confirm that Pylint runs from the worktree root with the worktree interpreter. The evidence MUST name the Pylint command source.
- **FR-004**: For each current path in the affected file set, the editor MUST show zero E0401 and zero E0611 diagnostics from Pylint.
- **FR-005**: The evidence record MUST contain each field in `design/contracts/editor-evidence.md` for each current path.
- **FR-006**: The record MUST map each listed path to its current path, blob SHA, and move status on `main`.
- **FR-007**: The record MUST state the current content of each cited line. It MUST mark each mismatch as stale or absent.
- **FR-008**: Each claim in the editor setup section MUST match repository or tool evidence, or the claim MUST be marked unverified.
- **FR-009**: The change MUST NOT alter production source, production imports, `pyproject.toml`, CI workflows, or diagnostic suppressions.
- **FR-010**: The pull request MUST use `Refs #4126`. The pull request MUST NOT contain a closing keyword for issue #4126.
- **FR-011**: A terminal Pylint pass MUST NOT count as live editor evidence.
- **FR-012**: Each changed Markdown file MUST score 80 or above on the STE gate.
- **FR-013**: The change MUST add one changelog fragment with a unique name.
- **FR-014**: The evidence and the record MUST NOT contain credentials, environment variable values, or user-profile path segments.
- **FR-015**: If a native permission is missing, the live check MUST stop. The check MUST NOT bypass the permission.
- **FR-016**: The record MUST use the route `specs\numbered\0\0\1\1\3\0\0\1\4126-editor-import-diagnostics`. Each directory MUST hold five children or fewer.
- **FR-017**: The label change MUST remove `needs-investigation` and MUST keep `in-progress` until the issue closes.

### Key Entities *(include if feature involves data)*

- **Affected file**: One file in the issue set. Natural key: current path on `main`. Holds the listed path, blob SHA, move status, and live state.
- **Diagnostic**: One E0401 or E0611 message that the Pylint extension shows for an affected file.
- **Evidence row**: One live or terminal observation for one current path. Natural key: issue number, current path, and UTC time.
- **Cited line**: One line number from the issue and its content on `main`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 27 of 27 affected files have a current path and a blob SHA on `main`.
- **SC-002**: 27 of 27 affected files show zero E0401 and zero E0611 diagnostics in the live check. This check is pending.
- **SC-003**: 27 of 27 current paths exit with code 0 and no output in the terminal check. This check is pending.
- **SC-004**: 8 of 8 cited lines have a recorded status in the research table.
- **SC-005**: The remote check count matches in the status file, the research table, and the summary.
- **SC-006**: Each changed Markdown file scores 80 or above on the STE gate.
- **SC-007**: The pull request body contains `Refs #4126` and no closing keyword for the issue.

## Assumptions

- The editor is Visual Studio Code. The local extension versions on the reviewed machine are Microsoft Python 2026.10.0 and Pylint 2026.8.0.
- The owner runs the live check on a machine that holds the worktree and an editor window.
- Commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` on `main` is the baseline for this record.
- The live check needs no Mist API credential.
- Each new worktree installs Python 3.15.2 through UV before the check.
- Pylint 4.1.4 and mistapi 0.64.1 match the pins in the repository.

## Out of Scope

- Changes to production imports, module layout, the `pyproject.toml` `init-hook`, or CI gates.
- A new CI gate for E0401 or E0611. The analysis recommends a separate issue.
- Changes to the Pylint score threshold of 9.5.
- Changes to the Pylint extension version, the VS Code version, or user settings.
- Mist API behavior, endpoint coverage, or any Mist credential.
- Closing issue #4126. The owner closes the issue after live evidence exists.
- Editing the issue body or posting comments. The orchestrator makes that decision.

## Dependencies

- Pull request #4322 merged on 2026-11-13. Its merge commit is `83d404f66ada402ed9e8d334da8c8df255e9dee0`. It added the editor setup section and the changelog fragment for issue #4126.
