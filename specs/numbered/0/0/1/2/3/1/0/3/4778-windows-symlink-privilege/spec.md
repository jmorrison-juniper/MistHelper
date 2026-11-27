# Feature Specification: Windows Symlink Privilege in the Spec-Route Contract Guard

**Feature Branch**: `fix/4778-windows-symlink-privilege`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4778: on Windows, the symlink case of `test_unsafe_feature_selection_fails` stops at setup with WinError 1314, because the account lacks the symlink privilege.

## Clarifications

### Session 2026-11-26

- Q: Should the fix change the production guard? → A: No. `common.ps1` lines 258-259 and `spec-route.ps1` lines 110-111 already reject reparse points. A symlink and a junction both carry that attribute. The failure occurs in the test fixture at line 296.
- Q: Should the Windows run skip the symlink case? → A: Only as the last step. The fixture tries a junction before it skips. It skips only when `mklink /J` also fails, and the skip prints the cause.
- Q: Should the owner grant the symlink privilege or enable Developer Mode? → A: Not in this change. Microsoft limits the right to trusted users. Host policy stays outside this repository.
- Q: Does the change need a changelog fragment? → A: No. `changelog.d/README.md` line 58 says an internal-only change adds no fragment. The pull request states the reason.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run the guard on a Windows host without the symlink privilege (Priority: P1)

A maintainer runs the spec-route contract guard on a Windows host. The account lacks the symlink privilege. The symlink case no longer stops at setup. It creates a junction, runs the same rejection checks, and passes. When the junction also fails, the case skips and prints the cause.

**Why this priority**: The issue blocks the local gate on this host. The guard cannot prove its rejection rule there.

**Independent Test**: On a Windows host without the symlink privilege, run `python -m pytest tests/guardrails/test_spec_route_contract.py -k unsafe_feature_selection --log-cli-level=INFO -rs`. The output names the link kind, or it names the skip cause.

**Acceptance Scenarios**:

1. **Given** a Windows host without the symlink privilege, **When** the symlink case runs, **Then** it creates a junction and the rejection checks pass.
2. **Given** a Windows host where `mklink /J` also fails, **When** the symlink case runs, **Then** the case skips. The skip reason names the symlink privilege and the `mklink` output.
3. **Given** a Windows host with the symlink privilege, **When** the symlink case runs, **Then** it creates a real symlink and the rejection checks pass.

---

### User Story 2 - Keep the real symlink case on Ubuntu CI (Priority: P1)

The continuous integration shard runs on Ubuntu. Ubuntu creates a real symlink in the symlink case. The case proves that a symlink selection fails.

**Why this priority**: The CI shard is the automated proof that uses a real symlink.

**Independent Test**: The `root-and-contracts` shard of the `pytest_coverage_shards` job passes on `ubuntu-latest`. Its test paths include `tests/guardrails`.

**Acceptance Scenarios**:

1. **Given** the Ubuntu shard, **When** the symlink case runs, **Then** it creates a real symlink and the case passes.
2. **Given** a reparse-point check that accepts symlinks, **When** the symlink case runs, **Then** the case fails.

---

### User Story 3 - Prove that the guard still fails without the reparse-point check (Priority: P2)

A maintainer removes the reparse-point check on a task branch. The symlink case fails on each host where it runs. The maintainer reverts the edit before the commit.

**Why this priority**: A guard that passes without its check proves nothing.

**Independent Test**: Remove the `ReparsePoint` condition at `common.ps1` line 258 on the task branch. Run the guard file. Revert the edit.

**Acceptance Scenarios**:

1. **Given** no reparse-point check, **When** the symlink case runs, **Then** at least one assertion fails.
2. **Given** the reverted check, **When** the guard file runs, **Then** every case passes.

---

### Edge Cases

- What happens when `mklink /J` fails? The case skips. The skip reason includes the `mklink` output.
- Caution: a skipped case removes the Windows check on that host. Ubuntu CI still runs the real symlink case.
- What happens when symlink creation raises an error other than WinError 1314? The fixture raises the same error again. The case fails at setup, and the message names the cause.
- What happens when the selection path already exists? Creation raises `FileExistsError`. The fixture raises it again. Each test uses a new `tmp_path`, so this case does not occur in normal runs.
- What happens on Ubuntu and macOS? Symlink creation succeeds. The fallback code does not run.
- Warning: a recursive delete that follows a junction removes the files at the junction target. The junction target must stay inside `tmp_path`.
- What happens when `snapshot_tree` reads a junction? The snapshot lists the junction contents. The before and after snapshots match when nothing changes.
- What happens when pwsh is missing? The existing `pytest.fail` message at line 174 stays unchanged.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The symlink case MUST create a real symlink when the host grants the symlink privilege.
- **FR-002**: When symlink creation raises WinError 1314, the fixture MUST create a junction to the same target.
- **FR-003**: When `mklink /J` fails, the case MUST skip. The skip reason MUST name the symlink privilege and the `mklink` output.
- **FR-004**: The fixture MUST raise again every error that is not WinError 1314.
- **FR-005**: The symlink case MUST keep its three assertions unchanged.
- **FR-006**: The production reparse-point checks MUST remain unchanged.
- **FR-007**: The change MUST NOT remove, skip by default, or weaken any case of the spec-route contract guard.
- **FR-008**: Each link attempt MUST write an info log line before the attempt and a debug log line after it.
- **FR-009**: `documentation/development-setup.md` MUST state the PowerShell 7 requirement and the junction fallback.
- **FR-010**: The pull request MUST state why the change adds no changelog fragment.
- **FR-011**: The Windows run MUST report the link kind that the symlink case used.

### Mist Cloud Transport Requirements

Not applicable: this change calls no Mist REST endpoint and no mistapi method.

### Key Entities

- **Selection link**: The path under `specs` that the fixture passes to the route script as the feature selection.
- **Link kind**: The result of the fixture. The value is `symlink` or `junction`. A skipped case has no link kind.
- **Reparse point**: A file system object with the `ReparsePoint` attribute. A symlink and a junction both carry it.
- **Symlink privilege**: The Windows right `SeCreateSymbolicLinkPrivilege`. By default, members of the Administrators group hold it.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On `ubuntu-latest`, the symlink case creates a real symlink and passes.
- **SC-002**: On a Windows host without the symlink privilege, the symlink case passes or skips with a printed cause. It never fails at setup.
- **SC-003**: The three new test methods and the modified symlink case pass on Ubuntu and on Windows.
- **SC-004**: With the reparse-point check removed, the symlink case fails. Task T008 records the result.
- **SC-005**: Each applicable local gate in `plan.md` reports its expected result. The test-quality gate reports zero new findings.

## Assumptions

- The affected host runs Windows 11 with Python 3.15.2 and PowerShell 7 on PATH.
- CI runs the guard file on `ubuntu-latest`, as `ci.yml` lines 248 and 255 show.
- `mklink /J` creates a junction without the symlink privilege. This claim is unverified. Task T-LOCAL-GATES checks it on the host.
- Each test receives a new `tmp_path` directory.

## Non-Goals

- Granting the symlink privilege or enabling Developer Mode on any host.
- Changes to `common.ps1`, `spec-route.ps1`, or `check-prerequisites.ps1`.
- The O_NOFOLLOW report code of issue #4771. It is a different code path.
- The "in-progress relocation mapping failure" that the issue names. The issue gives no test identifier for it.
- The "structural/SDK/output gate" that the issue names. The issue gives no command for it.
- Changes to the CI runner, the shard matrix, or a new Windows CI job.
- A changelog fragment.
