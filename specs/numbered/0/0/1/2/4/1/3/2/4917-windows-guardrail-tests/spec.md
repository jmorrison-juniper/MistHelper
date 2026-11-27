# Feature Specification: Windows guardrail test failures

**Feature Branch**: `fix/4917-windows-guardrail-tests`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4917: 23 guardrail tests fail on a Windows workstation. Ubuntu CI runs the same guard files (RC-13). Skip the Bash cases with a reason or name Git Bash, compare normalized paths, and decide the uv and symlink prerequisites.

## Clarifications

### Session 2026-11-26

- Q: Should the Bash cases use Git Bash on Windows? → A: No. The cases skip on Windows with a printed reason, and Ubuntu CI runs them (D-1).
- Q: Should a missing `uv` skip or fail? → A: It fails after the lookup in the environment folder of the running interpreter (D-2).
- Q: Should a missing symbolic link privilege fail the Windows run? → A: No. The symlink case skips with the cause only for WinError 1314 (D-3).
- Q: Should this change add a Windows CI job? → A: No. A follow-up issue records the gap (D-6).
- Q: Does a test-only change need a changelog fragment? → A: Yes. The constitution requires one fragment for each change (D-8).
- Q: Do steps 10 and 11 of constitution Principle IV apply? → A: No. The container build trigger excludes these paths. T-MERGE checks the merged commit instead (D-9).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Windows workstation runs the guardrail suite with no failures (Priority: P1)

A maintainer on a Windows 11 workstation runs the guardrail suite from the repository. The run reports no failed test. Each skipped case prints a reason. The reason names the place where the case runs.

**Why this priority**: The issue reports 23 failures on the workstation. CI does not run these tests on Windows. A red suite hides new regressions.

**Independent Test**: On a Windows 11 workstation with the repository environment folder, run the guardrail suite and read the summary. Expect zero failures and one reason for each skip.

**Acceptance Scenarios**:

1. **Given** a Windows workstation with the environment folder from the bootstrap, **When** the operator runs the guardrail suite, **Then** the summary reports zero failed tests.
2. **Given** a Bash-based case on Windows, **When** pytest reports the case, **Then** the case shows as skipped, and the reason names Ubuntu CI.
3. **Given** `uv` is absent from PATH and `uv.exe` is in the environment folder, **When** the export guard runs, **Then** it finds the pinned tool.
4. **Given** an account without the symbolic link privilege, **When** the symlink case runs, **Then** the case shows as skipped, and the reason names the privilege.

---

### User Story 2 - Ubuntu CI keeps the same guard coverage (Priority: P1)

A CI maintainer reviews a pull request. Each guard that ran on Ubuntu before this change still runs on Ubuntu after it. The only new collected test is the pinned-uv lookup test.

**Why this priority**: The Ubuntu shard is the proof for the cases that skip on Windows. A change that drops those cases weakens the gate.

**Independent Test**: Compare the Ubuntu collection of `tests/guardrails` before and after the change. The count rises by one.

**Acceptance Scenarios**:

1. **Given** the change applied, **When** the Ubuntu shard collects `tests/guardrails`, **Then** the count rises by one, and no case gains a skip.
2. **Given** the Ubuntu shard runs the dependency export guard, **When** PATH holds the pinned `uv`, **Then** the guard result matches the result before the change.
3. **Given** the changed skip conditions, **When** a reader checks each condition, **Then** each condition names Windows and no condition names Linux or macOS.

---

### User Story 3 - Maintainer finds the Windows behavior in the setup guide (Priority: P2)

A new Windows workstation user reads the setup guide before the first test run. The note lists the skip behavior, the uv lookup, and the Ubuntu CI proof.

**Why this priority**: A reader who sees a skip without a reason may treat the skip as a defect.

**Independent Test**: Read the new subsection under Step 4. Check that each named test file exists under `tests/guardrails`.

**Acceptance Scenarios**:

1. **Given** the setup guide after the change, **When** the reader opens Step 4, **Then** the reader finds the subsection `Guardrail tests on Windows`.
2. **Given** the subsection, **When** the reader compares each statement with the pytest output, **Then** each statement matches a skip reason or a lookup result.

## Edge Cases

- A Windows workstation with a grant of the symbolic link privilege runs the symlink case in full. The case does not skip.
- A `uv` on PATH with a version other than `0.13.9` wins over the environment folder copy. The guard uses that version, as it does today.
- Neither PATH nor the environment folder holds `uv`. The guard fails with the existing message `The UV executable is required for export validation.`
- Link creation fails with an error other than WinError 1314. The test re-raises that error, and the test fails.
- The repository path contains spaces, as in the OneDrive folder. The path comparisons still match.
- The Git output and the temporary path differ in the case of the drive letter. The path object comparison still matches.
- The analytics package root is missing. The message prints POSIX paths, and the regex matches the same text.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: On a Windows 11 workstation, the guardrail suite MUST report zero failed tests.
- **FR-002**: On Windows, each Bash-execution case MUST skip with a printed reason that names Ubuntu CI.
- **FR-003**: On Linux and macOS, each Bash-execution case MUST run and assert the same behavior as before this change.
- **FR-004**: On Windows, the YAML-only browser contract tests MUST run and pass.
- **FR-005**: The dependency export guard MUST find `uv` on PATH first, then in the environment folder of the running interpreter. The guard MUST fail when neither lookup finds `uv`.
- **FR-006**: The symlink case MUST skip only when link creation fails with WinError 1314. The case MUST re-raise every other error.
- **FR-007**: The Git root check MUST compare path objects, not separator text.
- **FR-008**: The missing-root message MUST print POSIX paths. The test pattern MUST match the same paths.
- **FR-009**: The change MUST add no file under `tests\guardrails`.
- **FR-010**: The setup guide MUST describe the Windows skip behavior, the uv lookup, and the Ubuntu CI proof.
- **FR-011**: Each changed line MUST carry an inline comment. Each new action MUST log before and after it, as constitution Principles VI and VII require.
- **FR-012**: The change MUST add one fragment named `changelog.d/issue-4917-windows-guardrail-tests.md` with a `Fixed` bullet.
- **FR-013**: The change MUST NOT change any file under `.github\workflows\`, `src\`, or the dependency files.
- **FR-014**: The change MUST follow the Git flow. It needs a claimed issue, a branch from `main`, a Conventional Commit, a squash merge, and a pull request body with `Closes #4917`.

### Key Entities

Not applicable: the change alters test code and one setup note. It adds no entity.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The Windows run of the guardrail suite reports zero failed tests. The predicted result is 1186 passed and 30 skipped. When the symlink privilege exists, the predicted result is 1187 passed and 29 skipped.
- **SC-002**: The Ubuntu shard collects one more test than before the change. No Ubuntu case gains a skip.
- **SC-003**: The diff touches only the files in the change map of `plan.md`. No file under `tests\guardrails` is added.
- **SC-004**: Each applicable local gate in `tasks.md`, under T-LOCAL-GATES, exits with its expected result.
- **SC-005**: The pull request body contains `Closes #4917`, and the pull request title passes the Conventional Commits check.
- **SC-006**: Each skip reason printed on Windows names Ubuntu CI or the symbolic link privilege.

## Assumptions

- The Windows workstation holds the repository environment folder with `uv` 0.13.9. The development requirements pin and the environment folder copy match (RC-21 and the local `uv-0.13.9.dist-info`).
- Ubuntu CI runs `tests/guardrails` in the root and contracts shard (RC-13).
- The local checkout equals `main` at `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` (RC-38 to RC-40, and the blob comparison in `design/research.md`).
- The issue counts of 1,183 passed, 23 failed, and 9 skipped describe the same tree. This record does not reproduce them.
- The Windows workstation runs PowerShell 7, because the spec route tests call `pwsh`.

## Out of Scope

- A Windows CI job for the guardrail tests (D-6).
- Running the Bash cases through Git Bash on Windows (D-1).
- Enabling Developer Mode or any other workstation setting.
- The `None` case of `test_invalid_mirror_configuration_fails_without_a_write`. It passes on Windows today, because Bash fails and leaves no file, and this change skips it there. A follow-up issue owns the repair.
- The five-item debt of `tests\guardrails`, which holds 79 tracked children (RC-40). A follow-up issue owns the remediation.
- Any change under `src\`, `.github\workflows\`, `requirements*.txt`, or `pyproject.toml`.
