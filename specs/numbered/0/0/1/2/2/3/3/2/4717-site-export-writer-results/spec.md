# Feature Specification: Site export write results

**Feature Branch**: `fix/4717-site-export-writes` (merged as PR #4847)

**Record Path**: `specs/numbered/0/0/1/2/2/3/3/2/4717-site-export-writer-results`

**Created**: 2026-11-26

**Status**: Repair merged on `main`. Closure is pending. This record replaces the draft from 2026-11-09.

**Input**: Issue #4717. The application list export and the system event export report success after a failed write.

## Clarifications

### Session 2026-11-26

- Q: Does the defect still exist on `main`? A: No. PR #4847 merged the repair on 2026-11-19 as commit `db06604d18d832c25edb60eaa2edac6c72cea4cc`. Both persistence methods now check the writer result at lines 63-68.
- Q: Is this record new, or does it replace the draft? A: It replaces the draft. The folder name is the same, so the draft files change in place.
- Q: Where is the failed-write text for menus 213 and 214? A: In `documentation/operator-guide.md` line 120. Commit `0788b975ea` (PR #4918) removed the menu text from `README.md`.
- Q: Does a live Mist call verify menus 213 and 214? A: No. Issue #4717 forbids Mist calls. Mocked menu entry-point tests cover both menus.
- Q: Is the publication hold still active? A: Unresolved. The owner merged PR #4847 while the route check was open. No issue comment after 2026-11-10 lifts the hold. See decision R-8 in `design/research.md`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Report a failed write (Priority: P1)

An operator sees an error when a site export fails to save its rows. The error names the endpoint and the output file.

**Why this priority**: Caution: a false success message can hide missing incident data from the operator.

**Independent Test**: Run the four failed-write cases in `TestSiteWriteOutcomes` for both site exports. Each case logs one error and no success message.

**Acceptance Scenarios**:

1. **Given** the writer returns `False`, **When** the application list export persists rows, **Then** one error names `getSiteApplicationList` and the output file.
2. **Given** the writer returns `False`, **When** the system event export persists rows, **Then** one error names `searchSiteSystemEvents` and the output file.
3. **Given** the writer returns `False`, **When** either menu entry point runs, **Then** no message claims persistence or export success.

### User Story 2 - Keep existing results (Priority: P1)

An operator sees the same success, empty, and exception behavior as before the repair.

**Why this priority**: The repair must not change valid exports or hide the exception path.

**Independent Test**: Run the success, empty, and exception cases in `TestSiteWriteOutcomes`. All 12 cases pass.

**Acceptance Scenarios**:

1. **Given** the writer returns `True`, **When** an export persists rows, **Then** the persistence trace and the exported-count notice remain.
2. **Given** an empty response, **When** an export runs, **Then** the writer is not called and the empty notice remains.
3. **Given** the writer raises an exception, **When** a persistence method runs directly, **Then** the exception propagates unchanged.
4. **Given** the writer raises an exception, **When** a menu entry point runs, **Then** the existing menu handler logs the error and returns `None`.

### User Story 3 - Prove the repair and close the issue (Priority: P2)

A maintainer reads the evidence for each requirement. The maintainer then closes issue #4717 through a merged pull request.

**Why this priority**: The owner named two open gates before publication. Issue #4717 remains open.

**Independent Test**: Run the offline harness, the route check, the comment scan, and the remote CI checks. Each result must match its success criterion.

**Acceptance Scenarios**:

1. **Given** the offline harness, **When** the shared test module runs, **Then** the harness reports zero socket, DNS, and SQLite attempts.
2. **Given** the route check, **When** `Resolve-SpecFeaturePath` runs with number 4717, **Then** the result equals the record path.
3. **Given** the touched code, **When** the comment scan runs, **Then** no statement line lacks an inline comment.
4. **Given** a merged pull request that contains `Closes #4717`, **When** GitHub merges it, **Then** issue #4717 closes.

### Edge Cases

- A writer result of `False` is an error, even when the rows are valid. The writer owns the persistence decision.
- A writer result that is not a Boolean is judged by its truth value. The writer contract defines a `bool` return only.
- An empty response returns before flattening, sanitizing, or writing. The writer is not called.
- A writer exception from a direct persistence method propagates unchanged. A menu entry point logs it and returns `None`.
- An operator declines site selection. The menu returns before any SDK call. This path is unchanged.
- Caution: the database mirror can drop a write after the file write succeeds. The writer returns `True` and logs a warning. The export reports success. This limit is out of scope.
- The local checkout can differ from remote `main`. Remote blob SHAs decide each claim in this record.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Each site export MUST log one error when the writer returns `False`.
- **FR-002**: A failed write MUST NOT produce a persistence trace or an exported-count notice.
- **FR-003**: The error for a failed write MUST name the endpoint and the output filename.
- **FR-004**: A successful write MUST keep the sanitized rows, the filename, the endpoint name, and both success messages.
- **FR-005**: An empty response MUST return before any transform or writer call, and MUST keep the empty notice.
- **FR-006**: A writer exception MUST propagate from a persistence method, and MUST reach the existing menu error handler.
- **FR-007**: Each persistence method and each menu entry point MUST keep the `None` return contract.
- **FR-008**: The repair MUST NOT change the shared pagination, the SDK call, the endpoint name, the writer, or any other exporter.
- **FR-009**: Verification MUST block socket, DNS, and SQLite access during each run of the shared test module.
- **FR-010**: Each statement line in the touched persistence methods and in `TestSiteWriteOutcomes` MUST carry an inline comment.
- **FR-011**: The operator guide MUST describe the failed-write behavior for menus 213 and 214.
- **FR-012**: The release note fragment MUST name issue #4717 and describe the user-visible fix.
- **FR-013**: The record path MUST equal the base-5 route for number 4717, which is `0/0/1/2/2/3/3/2`.
- **FR-014**: Each new directory in this record MUST hold five children or fewer.
- **FR-015**: Issue #4717 MUST close only through a merged pull request that contains `Closes #4717`, after remote CI passes.

### Mist Cloud Transport Requirements *(include if feature uses Mist Cloud)*

- The application list export uses `mistapi.api.v1.sites.wxtags.getSiteApplicationList`.
- The system event export uses `mistapi.api.v1.sites.events.searchSiteSystemEvents`.
- Pagination uses `mistapi.get_all`. No direct HTTP request is made.
- No owned WebSocket transport exists. The SDK contract tests for owned transport are not applicable.

### Key Entities *(include if feature involves data)*

- **Writer result**: The Boolean that `DataExporter.write_with_format_selection` returns. `True` means the primary file write succeeded.
- **Site export**: One application list or system event export for one site. It has a site-derived filename and an endpoint name.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Both failed-write cases for both site exports log one error and zero success messages.
- **SC-002**: All 12 success, empty, and exception cases pass in `TestSiteWriteOutcomes`.
- **SC-003**: The offline harness reports zero socket, DNS, and SQLite attempts for the shared test module.
- **SC-004**: The comment scan finds zero statement lines without an inline comment in the touched code.
- **SC-005**: Remote `main` holds the repair at the three owned paths. Blob SHAs are recorded in `design/research.md`.
- **SC-006**: `Resolve-SpecFeaturePath` returns the record path for number 4717.
- **SC-007**: Issue #4717 closes through a merged pull request that names the issue.

## Assumptions

- The writer returns `bool` (`src/operations/exporting/export/data_exporter.py` lines 153-180).
- The installed `mistapi` is version 0.64.1. The installed version satisfies the range in `pyproject.toml` line 29.
- The three owned source and test paths, and this record folder, are the only paths that this issue changes.
- Every test uses synthetic rows. No Mist cloud call occurs during verification.
- The owner account merged PR #4847 on 2026-11-19.

## Out of Scope

- The shared pagination (`mistapi.get_all`) and other SDK calls.
- Other callers of `write_with_format_selection` that ignore the writer result. Issue #4717 names only the two site exports.
- The writer return contract and the database mirror warning path.
- A live Mist dry run of menus 213 and 214.
- The README menu text. PR #4918 removed it on purpose.
- Splitting the shared test module into smaller modules. This record names the split as separate remediation.
- Editing `CHANGELOG.md`. The release coordinator owns that file.
- Reverting PR #4847. Caution: a revert restores the defect in both persistence methods.
