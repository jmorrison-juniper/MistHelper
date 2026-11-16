# Feature Specification: Windows Audit Report Portability

**Feature Branch**: `4771-windows-audit-report-portability`

**Created**: 2026-11-15

**Status**: Draft

**Input**: User description: "Repair actual report generation without weakening owner-only access, symlink/reparse-point rejection, existing-file safety or cleanup."

## User Scenarios & Testing

### User Story 1 - Save a private audit report on Windows (Priority: P1)

An operator runs the isolated dialog audit on Windows and saves its JSON and Markdown reports in the approved audit folder.

**Why this priority**: Report output must work on every supported desktop platform.

**Independent Test**: Run the writer with synthetic report data on Windows and verify both report files contain the expected data.

**Acceptance Scenarios**:

1. **Given** an approved directory, **When** the operator writes a report on Windows, **Then** the writer creates both report files.
2. **Given** existing report files, **When** the operator writes a new report, **Then** the writer updates the files without exposing them to other accounts.

### User Story 2 - Reject unsafe report paths (Priority: P1)

An operator receives a clear error when the approved directory or a report file uses a symbolic link or another reparse point.

**Why this priority**: An unsafe path can redirect private audit data to an unapproved location.

**Independent Test**: Provide a symbolic link or reparse point at each supported path boundary and verify that the writer rejects it.

**Acceptance Scenarios**:

1. **Given** a linked report file, **When** the writer checks the destination, **Then** it rejects the path without changing the link target.
2. **Given** a linked directory component, **When** the writer checks the destination, **Then** it rejects the path before it writes either report.

### User Story 3 - Preserve report files after a failed write (Priority: P2)

An operator can rely on existing report files when a new report write fails.

**Why this priority**: A failed audit report must not destroy earlier evidence or leave incomplete output.

**Independent Test**: Cause a synthetic write failure and compare prior file contents and temporary files with their initial state.

**Acceptance Scenarios**:

1. **Given** existing report files, **When** a new write fails, **Then** the earlier files remain unchanged.
2. **Given** a failed write, **When** cleanup completes, **Then** no temporary report files remain.

### User Story 4 - Validate report safety on native Windows (Priority: P1)

A maintainer checks the report helper and writer on a native Windows runner before the feature merges.

**Why this priority**: Simulated Windows calls cannot prove that the real Windows security APIs accept the requested handles.

**Independent Test**: Push a feature branch commit and verify that both native regressions pass with zero skips.

**Acceptance Scenarios**:

1. **Given** a feature branch commit, **When** it is pushed, **Then** a separate bounded Windows workflow runs the native helper and writer tests.
2. **Given** a native test is missing or skipped, **When** the workflow checks its results, **Then** the job fails.
3. **Given** the workflow runs, **Then** it uses synthetic data, read-only repository access, and no Mist service or credential.

### Edge Cases

- Reject a missing or invalid file-safety capability instead of treating it as disabled.
- Reject a reparse point in any existing parent directory and at either report path.
- Fail without writing reports when the approved directory cannot receive owner-only access.
- Preserve the existing report pair if the second report cannot be saved.

## Requirements

### Functional Requirements

- **FR-001**: The report writer MUST create the JSON and Markdown reports on Windows.
- **FR-002**: The writer MUST restrict the approved directory and both reports to the current owner.
- **FR-003**: The writer MUST reject symbolic links and reparse points in the destination path and report files.
- **FR-004**: The writer MUST reject a missing safety capability and MUST NOT replace it with an unrestricted default.
- **FR-005**: The writer MUST preserve earlier reports when a write fails.
- **FR-006**: The writer MUST remove temporary files after a failed write.
- **FR-007**: The writer MUST keep existing non-Windows report behavior and path restrictions.
- **FR-008**: A separate optional workflow MUST run the native Windows helper and writer regressions after a non-main branch push.
- **FR-009**: The workflow MUST fail unless both native tests run and pass without a skip.
- **FR-010**: The workflow MUST use no credentials, Mist endpoints, production data, or services and MUST NOT change required checks.

### Key Entities

- **Audit report pair**: The JSON evidence and its Markdown summary for one isolated audit.
- **Approved report directory**: The only directory where the writer can store audit reports.
- **Existing report**: Earlier evidence that must remain intact if a later write fails.

## Success Criteria

### Measurable Outcomes

- **SC-001**: On Windows, one successful write creates both expected reports from synthetic input.
- **SC-002**: Every tested symbolic link or reparse point is rejected before the writer changes a report.
- **SC-003**: The approved directory and reports deny access to accounts other than the current owner.
- **SC-004**: Every injected write failure preserves prior report contents and leaves no temporary files.
- **SC-005**: The existing non-Windows writer tests continue to pass.
- **SC-006**: The Windows workflow reports exactly two passed native regressions and zero skips.
- **SC-007**: The workflow has a read-only token permission and a finite job timeout.

## Assumptions

- The writer continues to accept only `test-artifacts/websocket-dialog-audit` in the current worktree.
- Audit reports contain the existing restricted, redacted fields and do not contain screenshots or private values.
- The native workflow runs on a feature-branch push so it can validate the commit before merge.
- The workflow does not run Mist Cloud operations or change audit evidence rules.
