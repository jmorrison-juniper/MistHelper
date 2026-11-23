# Feature Specification: Port the routed core to Spec Kit 1.4.3

**Feature Branch**: `chore/4873-routed-git-port`

**Created**: 2026-11-23

**Status**: Draft

**Input**: Port the 1.4.3 changes to the routed core, and keep the routed spec layout (issue #4873, part 1 of 2).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The routed dry run prints a routed path (Priority: P1)

A maintainer dry-runs a new feature. The printed record path is under `specs/numbered/`.

**Why this priority**: Every new record depends on the routed numbering.

**Independent Test**: Run `create-new-feature.ps1 -DryRun -Json -ShortName <name> <description>`. The `SPEC_FILE` value contains `specs\numbered\`.

**Acceptance Scenarios**:

1. **Given** the worktree, **When** the dry run runs, **Then** `SPEC_FILE` is under `specs/numbered/`.

---

### User Story 2 - Read-only commands leave the feature pointer unchanged (Priority: P1)

A maintainer runs a setup script that reads the active feature. The script does not write `.specify/feature.json`.

**Why this priority**: The routed layout reads the pointer, and a stray write changes the feature for every later command.

**Independent Test**: Run each setup script with `SPECIFY_FEATURE_DIRECTORY` set. Then run `git status`. The pointer is unchanged.

**Acceptance Scenarios**:

1. **Given** `SPECIFY_FEATURE_NO_PERSIST=1`, **When** a setup script resolves the feature, **Then** no write reaches `.specify/feature.json`.

---

### Edge Cases

- A feature selected outside `specs/` fails with the routing assertion.
- A feature nested inside another feature fails with the routing assertion.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The change MUST keep the recursive numbering scan in `create-new-feature.ps1`.
- **FR-002**: The change MUST keep `Assert-SpecFeatureSelection` and `Get-SpecDesignArtifact` in `common.ps1`.
- **FR-003**: The change MUST adopt the 1.4.3 `-LiteralPath` hardening in the functions it touches.
- **FR-004**: The change MUST honor `SPECIFY_FEATURE_NO_PERSIST` as the environment equivalent of `-NoPersist`.
- **FR-005**: The change MUST NOT adopt the 1.4.3 template priority and composition engine. A separate issue owns that decision.
- **FR-006**: The change MUST NOT change the routed templates. The CLI 1.1.2 and 1.4.3 templates are identical, and the CLI 1.1.2 template matches the manifest.
- **FR-007**: The change MUST add one changelog fragment.

### Key Entities

- **Routed core file**: A file in `.specify/scripts/powershell/` that keeps a routing rule. Its manifest hash differs on purpose.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The routed dry run prints a path under `specs/numbered/`.
- **SC-002**: The four setup scripts exit 0 and print JSON.
- **SC-003**: The spec-route contract guard passes, except the Windows symlink case on a host without the privilege.
- **SC-004**: `.specify/feature.json` is unchanged after the read-only runs.

## Design Decisions

| Item | Decision | Reason |
| - | - | - |
| Routed templates | Keep the repository version | The CLI 1.1.2 output matches the manifest. The CLI 1.4.3 output is identical. |
| Template priority and composition engine | Keep the current resolution | The 1.4.3 engine orders presets and extensions by priority and adds composition strategies. A composition strategy could change a routed template, and no test covers that path. |
| Root detection and `Get-Python3Command` | Keep the repository version | Upstream does not change these functions after 1.1.2. |
| Feature pointer persistence | Adopt the 1.4.3 policy, with the routing assertion first | The policy matches the rule that read-only commands do not write `.specify/feature.json`. |
| Spec write in `create-new-feature.ps1` | Keep the repository version | It writes the routed record and warns when the template is missing. |

## Assumptions

- The git extension 1.0.8 port is part 2, and it follows this change.
- The companion update stays deferred under issue #4873.
