# Feature Specification: Upgrade Spec Kit scaffolding to 1.4.3 and keep the routed layout

**Feature Branch**: `chore/4869-speckit-1-4-3`

**Created**: 2026-11-21

**Status**: Draft

**Input**: User description: "Upgrade the Spec Kit scaffolding to 1.4.3 without changing the routed spec layout (issue #4869)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Setup scripts work after the upgrade (Priority: P1)

A maintainer runs the Spec Kit skills. The setup scripts that the skills call read the active feature and return JSON.

**Why this priority**: A script that fails stops every Spec Kit workflow.

**Independent Test**: In the worktree, run `check-prerequisites.ps1 -Json -PathsOnly`, `setup-plan.ps1 -Json`, `setup-tasks.ps1 -Json`, and `resolve-template.ps1 spec-template -Json`. Each command exits 0 and returns JSON.

**Acceptance Scenarios**:

1. **Given** a feature record with `spec.md`, **When** the maintainer runs each setup script, **Then** each script exits 0 and returns JSON.
2. **Given** a read-only command, **When** the command runs, **Then** it does not change `.specify/feature.json`.

---

### User Story 2 - New spec records keep the routed layout (Priority: P1)

A maintainer creates a new feature record. The record goes under `specs/numbered/` with the route that `spec-route.ps1` computes.

**Why this priority**: The rule in `.github/copilot-instructions.md` requires the routed layout.

**Independent Test**: Run `create-new-feature.ps1 -DryRun` in the worktree. The printed feature directory is under `specs/numbered/`.

**Acceptance Scenarios**:

1. **Given** the upgraded worktree, **When** the dry run runs, **Then** the printed path contains `specs/numbered/`.

---

### User Story 3 - Reviewers see what the upgrade keeps (Priority: P2)

A reviewer reads the pull request and the issue. Each file that differs from 1.4.3 gives a reason.

**Why this priority**: A partial upgrade is acceptable only when the reviewer knows what remains.

**Independent Test**: The body of the pull request lists each kept file, its reason, and the follow-up issue.

**Acceptance Scenarios**:

1. **Given** the pull request, **When** a reviewer compares it with the kept-file list, **Then** each kept file has a reason.

---

### Edge Cases

- A feature directory that already has five children makes `setup-plan.ps1` and `setup-tasks.ps1` stop with an error. The guard must remain.
- A missing `spec.md` makes `check-prerequisites.ps1 -RequireSpec` stop with an error.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The change MUST set the version markers in `.specify/init-options.json` and `.specify/integration.json` to 1.4.3.
- **FR-002**: The change MUST add the function `ConvertTo-AsciiJson` to `common.ps1`. The change MUST NOT alter any other function in that file.
- **FR-003**: The change MUST update `check-prerequisites.ps1`, `setup-plan.ps1`, `setup-tasks.ps1`, and `resolve-template.ps1` to 1.4.3. Each script MUST keep the local `-NoPersist` call and the five-children guard.
- **FR-004**: The change MUST NOT change `create-new-feature.ps1`, `spec-route.ps1`, the four routed templates, or the routing code in `common.ps1`.
- **FR-005**: The change MUST NOT change the git extension, the `speckit-git-*` skills, the `speckit-taskstoissues` skill, or the `speckit.git.*` agents.
- **FR-006**: The change MUST NOT add `.specify/.gitignore`. That file would ignore the tracked `.specify/feature.json`.
- **FR-007**: The change MUST add one fragment to the release notes for issue #4869.

### Key Entities

- **Managed file**: A file that the integration manifest lists. The upgrade updates it unless a local rule keeps the repository version.
- **Kept file**: A managed file that keeps the repository version because of a local rule.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The four setup scripts exit with 0 in the worktree test.
- **SC-002**: The dry run prints a path under `specs/numbered/`.
- **SC-003**: Each changed PowerShell file parses with zero errors.
- **SC-004**: The guardrail run states the examined counts and reports zero failures.

## Assumptions

- The routed port of the 1.4.3 scripts, templates, and git extension is a separate follow-up issue.
- SpecKit Companion stays at 0.24.0. The community catalog does not allow updates.
- The git extension stays at 1.0.0. Its scripts do not follow the routed layout.

## Out of Scope

- The git extension update to 1.0.8.
- The SpecKit Companion update to 0.27.0.
- Removal of the old `.github/agents/speckit.*.agent.md` files.
- Removal of the backup folder outside the repository.
