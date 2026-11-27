# Feature Specification: Windows Bash Guardrail Skips

**Feature Branch**: `fix/4877-windows-bash-guardrails`

**Created**: 2026-11-26

**Status**: Draft

**Issue**: #4877, "Test failure: bash-dependent guardrails cannot run on Windows"

**Input**: Issue #4877, linked pull request #4880, and the remote evidence in `design/research.md`.

## Terms

- **Shell case**: A pytest case that starts `bash` or `/bin/bash` as a subprocess. The issue calls these cases bash-dependent. This record uses one term, shell case.
- **Non-shell case**: A pytest case that starts no shell.
- **POSIX shell mark**: The skip mark named `REQUIRES_POSIX_SHELL`. This change adds it to each shell case.
- **Windows host**: A computer where `sys.platform` equals `win32`.

## Clarifications

### Session 2026-11-26

- Q: Must the shell cases run on a Windows host? A: No. Issue #4877 accepts a named skip. Decision D-1 records this choice.
- Q: Which condition selects the skip? A: The platform value `win32`. Decision D-2 records this choice.
- Q: Must the weak assertion in the None case change in this change? A: No. It is a second defect. Decision D-5 records a follow-up issue.
- Q: Does this change alter the Ubuntu CI result? A: No. Each shell case still runs on `ubuntu-latest`. See checks RC-22 and RC-23 in `design/research.md`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Windows run shows named skips (Priority: P1)

A maintainer on a Windows host runs the two guardrail modules. Each shell case skips and shows a reason that names the cause and issue #4877. Each non-shell case runs and passes.

**Why this priority**: The current failures block a Windows maintainer from reading the guardrail result.

**Independent Test**: Run the two modules on a Windows host. The summary shows 11 passed and 20 skipped, and each skip shows its reason.

**Acceptance Scenarios**:

1. **Given** a Windows host, **When** the two modules run, **Then** 20 shell cases skip, and each skip names the cause.
2. **Given** a Windows host, **When** the two modules run, **Then** 11 non-shell cases run and pass.

---

### User Story 2 - Ubuntu CI keeps every case running (Priority: P1)

A maintainer relies on the Ubuntu CI job for the shell cases. After this change, the job runs all 31 cases with no skip.

**Why this priority**: The mirror script and the start script need a POSIX shell, and Ubuntu provides one.

**Independent Test**: The `pytest_coverage_shards` job on `ubuntu-latest` shows 31 passed and no skipped case for the two modules.

**Acceptance Scenarios**:

1. **Given** an Ubuntu runner, **When** the job runs, **Then** no shell case skips.
2. **Given** an Ubuntu runner and a failing shell case, **When** the job runs, **Then** the case still fails.

---

### User Story 3 - Windows developer reads the expected result (Priority: P2)

A Windows developer reads the development setup page. The page gives the command, the expected counts, the reason for each skip, and the CI authority.

**Why this priority**: A skip must not look like a product defect or a silent pass.

**Independent Test**: The new section in `documentation/development-setup.md` contains the command and the counts. The STE linter scores the page at 80 or above.

**Acceptance Scenarios**:

1. **Given** the development setup page, **When** a developer reads the new section, **Then** the section states the expected summary and the CI authority.

---

## Edge Cases

- A Windows host with Git Bash on `PATH` still skips each shell case. The SNMP case uses `/bin/bash`, and Windows has no such path.
- A Python process that reports `sys.platform` as `cygwin` or `linux` runs each shell case. The skip applies only to `win32`.
- A shell case that fails on Ubuntu still fails. The mark does not change a Linux or macOS result.
- A Linux host without bash raises `FileNotFoundError` in each shell case. This change keeps that result.
- The None case in `test_invalid_mirror_configuration_fails_without_a_write` passes on a host where bash runs and fails. This change keeps that behavior. See Out of Scope.
- A new shell case added later without the mark fails on a Windows host. This change adds no repository guard. See Out of Scope.

Caution: A skip does not prove that the shell case passed. The Ubuntu job is the authority for the 20 shell cases.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The change MUST apply the POSIX shell mark to each shell case when `sys.platform` equals `win32`.
- **FR-002**: Each skip reason MUST name the cause and cite issue #4877.
- **FR-003**: Each non-shell case MUST run on a Windows host and MUST pass.
- **FR-004**: The change MUST keep every case running on Linux and macOS. No skip applies on those platforms.
- **FR-005**: The mark MUST attach to one test function or one parametrized test. A module-level skip MUST NOT appear.
- **FR-006**: A Windows run MUST print the skip count in the pytest summary line.
- **FR-007**: The change MUST NOT alter any assertion, any workflow file, or any path under `src/` or `MistHelper.py`.
- **FR-008**: The change MUST document the expected Windows result, each skip reason, and the CI authority in `documentation/development-setup.md`.
- **FR-009**: The change MUST add one changelog fragment named `issue-4877-windows-bash-guardrails.md`.
- **FR-010**: Each new executable line MUST carry an inline comment. Each reason string MUST use ASCII characters only.
- **FR-011**: The pull request MUST list the two out-of-scope defects as follow-up items.

### Mist Cloud Transport Requirements *(include if feature uses Mist Cloud)*

Not applicable: this change calls no Mist Cloud endpoint and no mistapi method.

### Key Entities *(include if feature involves data)*

Not applicable: this change adds no data entity. See `design/data-model.md`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A Windows run of the two modules reports 11 passed, 20 skipped, and 0 failed.
- **SC-002**: The Ubuntu `pytest_coverage_shards` job reports 31 passed and 0 skipped for the two modules.
- **SC-003**: Each applicable local gate in task T-LOCAL-GATES passes.
- **SC-004**: All 20 skip reasons cite issue #4877 and name the cause.
- **SC-005**: The pull request changes no path under `src/` and no `MistHelper.py` path.

## Assumptions

- The reporting host has bash on `PATH`. The issue error text starts with `/bin/bash:`.
- The CI workflow runs guardrail tests on `ubuntu-latest`. See checks RC-22 and RC-23.
- The two modules on `main` match the reproduction commit `23379f0e0`. See checks RC-55 and RC-56.
- Local Windows runs use Windows 11, PowerShell 7, and the `.venv` environment. See check RC-41.

## Out of Scope

- The three other Windows guardrail failures in issue #4878. Those failures have other causes.
- The weak None-case assertion in `test_invalid_mirror_configuration_fails_without_a_write`. A follow-up issue tracks it.
- A repository-wide guard that requires the POSIX shell mark on every shell case. A follow-up issue can track it.
- Running shell cases on Windows through Git Bash or WSL.
- Changes to the pytest options in `pyproject.toml`.
- Product code, Mist API calls, and container images.

## Dependencies

- Related: issue #4876, closed by PR #4880. PR #4880 names issue #4877 as a tracked item.
- Related: issue #4878, open. It covers other Windows guardrail failures.
- Depends on: none.
