# Feature Specification: Windows Path and Symlink Guardrails

**Feature Branch**: `fix/4878-windows-path-symlink-guardrails`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4878. Three guard tests fail on a Windows 11 host. The symlink case needs a privilege that the host lacks. Two path guards compare separator styles.

## Clarifications

### Session 2026-11-26

- Q: Should the symlink case fail or skip on a host without the symlink privilege? → A: Skip, with a reason that names the OS error. The issue acceptance criteria require a skip.
- Q: Which OS errors cause the skip? → A: Only error 1314, which Microsoft names ERROR_PRIVILEGE_NOT_HELD. Other errors fail, so a real fault stays visible.
- Q: Does the fix change product behavior? → A: No. All three failures sit in test code. No file under `src/` changes.
- Q: Does a test-only change need a changelog fragment? → A: Yes. The constitution requires one fragment for each change. The changelog README exempts internal changes, so the stricter constitution rule applies.
- Q: Which labels apply to the issue? → A: Add the scope label `tests`. Keep `bug` and `test`, because the pytest failure pipeline names both.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Skip the symlink case without the privilege (Priority: P1)

An operator on Windows 11 runs the guard tests without the symbolic link privilege. The symlink case skips and names the OS error. The other cases still run and pass.

**Why this priority**: A host without the privilege must not fail the suite. A false failure hides the real results of the run.

**Independent Test**: On the reporter host, run the symlink case. Pytest reports one skip with the error 1314 reason and no failure.

**Acceptance Scenarios**:

1. **Given** a host that refuses symlinks, **When** the symlink case runs, **Then** pytest skips it and names the OS error.
2. **Given** the same host, **When** the outside and nested cases run, **Then** each case passes as before.

---

### User Story 2 - Keep the symlink proof where links can exist (Priority: P1)

A maintainer runs the guard on Linux CI or on a Windows host with the privilege. The symlink case creates the link and proves that the guard rejects the selection.

**Why this priority**: The skip must not weaken the proof on a host that can build the fixture.

**Independent Test**: On Linux CI, the symlink case runs and does not skip.

**Acceptance Scenarios**:

1. **Given** a host that creates symlinks, **When** the symlink case runs, **Then** the guard rejects the selection and the tree snapshot stays unchanged.
2. **Given** a symlink error with another code, **When** the fixture builds the link, **Then** the error propagates.

---

### User Story 3 - Compare paths, not separator style (Priority: P2)

A developer on Windows runs the Git root guard and the missing-root guard. Both pass, because each guard compares a path value or one separator style.

**Why this priority**: Two failures come from separator text, not from a defect in the tool under test.

**Independent Test**: Run each guard on Windows and on Linux. Each guard passes.

**Acceptance Scenarios**:

1. **Given** Git reports the repository root with forward slashes, **When** the Git root guard compares the path, **Then** the guard passes.
2. **Given** the inspector reports a missing root, **When** the missing-root guard matches the message, **Then** the guard passes on Windows and on Linux.

### Edge Cases

- A temporary folder path contains regex characters. The missing-root guard escapes the path before it matches.
- A changelog fragment names a removed analytics module path. The active-path guard fails. The fragment text must not name a removed path.
- Git returns a short 8.3 path form for the root. The Git root guard fails. The local check did not observe this form, so T-LOCAL-GATES verifies it on Windows.
- An `OSError` has no `winerror` attribute, as on Linux. The fixture re-raises the error. Linux creates the link without an error.
- The reporter host grants the privilege after the skip. The symlink case runs and proves the rejection.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The symlink case MUST skip with a reason that contains the OS error text when the error code is 1314.
- **FR-002**: The symlink case MUST create the link and run the guard when the host allows symlinks.
- **FR-003**: The symlink fixture MUST re-raise each `OSError` whose code is not 1314.
- **FR-004**: The symlink fixture MUST log the cause at error level before the skip. It MUST log the link action before and after the action.
- **FR-005**: The Git root guard MUST compare the reported top-level path and the resolved root as path values.
- **FR-006**: The missing-root guard MUST build its expected pattern from the forward-slash form of the missing path.
- **FR-007**: The inspector MUST report each missing path in the forward-slash form, with the same failure wording.
- **FR-008**: The change MUST NOT modify a file under `src/`. It MUST NOT add a module-level name to a changed test module.
- **FR-009**: Each changed line MUST carry an inline comment and stay within 120 characters. Each touched block MUST carry action logging.
- **FR-010**: The change MUST add `changelog.d/issue-4878-windows-path-symlink-guardrails.md` with one `Fixed` bullet that names issue #4878.
- **FR-011**: The record MUST be stored at `specs\numbered\0\0\1\2\4\0\0\3\4878-windows-path-symlink-guardrails`.
- **FR-012**: The pull request MUST contain `Closes #4878`, list the local gates with their results, and name each changed guard with its failing path.

### Mist Cloud Transport Requirements *(include if feature uses Mist Cloud)*

Not applicable: this issue does not call the Mist Cloud or the `mistapi` package.

### Key Entities *(include if feature involves data)*

Not applicable: this issue adds no data entity. It changes three test modules and adds one changelog fragment.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On a Windows host without the privilege, `python -m pytest tests/guardrails/test_spec_route_contract.py -q -rs -k symlink` reports one skip and zero failures.
- **SC-002**: On a Windows host, the Git root guard and the missing-root guard each pass.
- **SC-003**: On Linux CI, the `pytest` job passes, and the symlink case does not skip.
- **SC-004**: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py -q` passes with the new fragment.
- **SC-005**: The test-quality gate reports zero new findings against the repository baseline.

## Assumptions

- The three failures reproduce on the reporter host, as the issue states. This record does not run tests, so task T001 confirms the failures.
- The reporter host runs Windows 11 Enterprise and PowerShell 7, as the issue environment states. The local `.venv` uses Python 3.15.2.
- Linux CI runners create symlinks without a privilege error.
- The five unrelated modified files in the local checkout stay out of the pull request.

## Out of Scope

- Bash-dependent guards on Windows, tracked by issue #4877.
- The development setup page, tracked by issue #4879.
- The `pytest.fail` behavior for a missing `pwsh` command.
- Host privileges, Developer Mode, and other Windows configuration.
- The test-quality baseline file.
- The spec route script and the generator script.
- A new repository test for the skip branch. Analysis item U-1 records this follow-up.
