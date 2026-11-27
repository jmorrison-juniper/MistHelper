# Feature Specification: Port the routed layout and the git extension to Spec Kit 1.4.3

**Record Folder**: `specs\numbered\0\0\1\2\3\4\4\3\4873-routed-git-port`

**Feature Branch**: `chore/4873-routed-git-extension`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4873 finishes the Spec Kit 1.4.3 port. Part 1, merged as PR #4909, ported the routed core. This record covers the rest. It covers git extension 1.0.8, the git skills and agents, the integration manifests, and the ignore file for `feature.json`.

## Clarifications

### Session 2026-11-26

- Q: Which folder holds this record? A: `specs\numbered\0\0\1\2\3\4\4\3\4873-routed-git-port`. The route is the base-5 digits of 4873. The folder replaces the part 1 record.
- Q: Does item 5 install companion 0.27.0? A: No. The owner comment dated 2026-11-21 defers the update. Companion 0.24.0 stays in MistHelper.
- Q: Does the git script create the routed record? A: No. The git script creates the branch and the number. The core `/speckit-specify` step creates the record. FR-011 covers acceptance criterion 4.
- Q: Which script names does the git extension use? A: The 1.0.8 names, `create-new-feature-branch.ps1` and `create-new-feature-branch.sh`. The upstream v1.4.3 tree uses these names.
- Q: Does `speckit-taskstoissues` stay? A: No. The skill creates one issue for each task. It sets no labels, and AGENTS.md requires a type label and a scope label.
- Q: Does local commit `76b920fbc` become the implementation? A: No. It is evidence only, and GitHub does not hold it. Implementation may reuse its hunks after review.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Routed record from the core script (Priority: P1)

A maintainer dry-runs a new feature with the routed core script. The printed `SPEC_FILE` is under `specs\numbered\`.

**Why this priority**: Every new record depends on the routed numbering and the routed path.

**Independent Test**: Run `create-new-feature.ps1 -DryRun -Json -ShortName <name> <description>` with `SPECIFY_FEATURE_DIRECTORY` unset. Read `SPEC_FILE`.

**Status**: Delivered by PR #4909. Verified on `main` by R-009 to R-024.

**Acceptance Scenarios**:

1. **Given** a checkout of `main`, **When** the dry run runs, **Then** `SPEC_FILE` contains `specs\numbered\`.
2. **Given** a feature nested inside another feature, **When** a setup script resolves it, **Then** the routing assertion fails.

---

### User Story 2 - Feature number from routed records (Priority: P1)

A maintainer creates a feature branch with git extension 1.0.8. The number is one more than the highest number under `specs\numbered\`, at any depth.

**Why this priority**: Upstream 1.0.8 scans only the direct children of `specs\`. Every routed record hides below that level, so numbering restarts at a low value.

**Independent Test**: Use a fixture repository with record `4870-example` under `specs\numbered\0\0\1\2\3\4\3\4\`. Run the dry run of the PowerShell script and of the bash script. Read `FEATURE_NUM`.

**Acceptance Scenarios**:

1. **Given** a routed record numbered 4870, **When** the PowerShell git script dry-runs, **Then** `FEATURE_NUM` is `4871`.
2. **Given** the same fixture, **When** the bash git script dry-runs, **Then** `FEATURE_NUM` is `4871`.
3. **Given** a timestamp record under `specs\live\`, **When** numbering runs, **Then** the timestamp record does not raise the sequential number.
4. **Given** a folder without a git repository, **When** the script runs, **Then** `HAS_GIT` is `False` and `FEATURE_NUM` is still computed.

---

### User Story 3 - Branch and routed record in one flow (Priority: P1)

A maintainer runs the git script first and the core script second, with the same feature name. The record path is under `specs\numbered\`.

**Why this priority**: Acceptance criterion 4 requires one routed record from the git flow.

**Independent Test**: In a fixture, the git dry run gives `FEATURE_NUM` `4871`. The core dry run with the same name gives a `SPEC_FILE` under `specs\numbered\`.

**Acceptance Scenarios**:

1. **Given** the fixture from User Story 2, **When** both dry runs run, **Then** the core `SPEC_FILE` contains `specs\numbered\` and the number `4871`.

---

### User Story 4 - Integration status without drift (Priority: P1)

An operator runs `specify integration status`. The command reports no managed file that changed without a documented local rule.

**Why this priority**: Integration drift hides real local edits and blocks later upstream syncs.

**Independent Test**: Run `python -m pytest tests/guardrails/test_integration_local_rules.py`. The test fails when a managed hash differs and no local rule names the file.

**Acceptance Scenarios**:

1. **Given** a managed file with a documented local rule, **When** the guard runs, **Then** the guard passes for that file.
2. **Given** a managed file with a changed hash and no local rule, **When** the guard runs, **Then** the guard fails and names the file.

---

### User Story 5 - Skills and agents match 1.0.8 (Priority: P2)

A maintainer uses the `speckit-git-*` skills. The skills name the 1.0.8 script names. The `speckit.git.*` agent files and the `speckit-taskstoissues` skill no longer exist.

**Why this priority**: A stale skill calls a script name that no longer exists.

**Independent Test**: Run `python -m pytest tests/guardrails/test_routed_git_extension_port.py`. The test reads each skill and each agent path.

**Acceptance Scenarios**:

1. **Given** the `speckit-git-feature` skill, **When** the guard reads it, **Then** it names `create-new-feature-branch.ps1` and not `create-new-feature.ps1`.
2. **Given** the repository after the change, **When** the guard checks the agent paths, **Then** no `speckit.git.*` agent file exists.

---

### User Story 6 - Feature pointer stays tracked and unchanged (Priority: P2)

A maintainer runs read-only setup commands. The routing pointer `.specify/feature.json` stays unchanged, and git keeps it tracked.

**Why this priority**: A stray write changes the active feature for every later command.

**Independent Test**: Run `python -m pytest tests/guardrails/test_specify_gitignore_keeps_feature_json.py`. Run `git status --short .specify/feature.json` before and after a read-only command.

**Acceptance Scenarios**:

1. **Given** `SPECIFY_FEATURE_NO_PERSIST` is `1`, **When** a setup script resolves the feature, **Then** no write reaches `.specify/feature.json`.

---

### Edge Cases

- A timestamp name under `specs\live\` uses the timestamp path and does not raise the sequential number.
- A branch name over 244 bytes is truncated, as in version 1.0.0.
- The `GIT_BRANCH_NAME` override bypasses numbering, as in version 1.0.0.
- A parent folder with five children fails the parent-count check in `Assert-SpecFeatureDestination`.
- The symlink case in `test_spec_route_contract.py` skips on a host without the Windows symlink privilege.
- A local draft named `4873-routed-git-extension` exists in a worktree. This record does not use that folder.
- An upstream sync overwrites a local rule. The drift guard fails, and the change stays blocked until the rule is restored.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The routed core keeps the recursive numbering scan in `.specify/scripts/powershell/create-new-feature.ps1`.
- **FR-002**: The routed core keeps the routing assertion and design artifact selection in `.specify/scripts/powershell/common.ps1`.
- **FR-003**: The routed core keeps `-LiteralPath` hardening in each function that it touches.
- **FR-004**: The routed core honors `SPECIFY_FEATURE_NO_PERSIST` as the environment form of `-NoPersist`.
- **FR-005**: The routed core does not adopt the 1.4.3 template priority and composition engine.
- **FR-006**: The routed templates keep their repository content. This change changes no template file.
- **FR-007**: This change adds one changelog fragment, `changelog.d/issue-4873-routed-git-extension.md`.
- **FR-008**: The 1.0.8 PowerShell git script scans `specs\` recursively when it computes the next number. The scan matches the routed core scan.
- **FR-009**: The 1.0.8 bash git script scans `specs/` recursively when it computes the next number.
- **FR-010**: The git extension tree matches upstream Spec Kit v1.4.3 files, with the routed changes of FR-008 and FR-009.
- **FR-011**: After the git script creates a branch, the core dry run returns a `SPEC_FILE` under `specs\numbered\`.
- **FR-012**: The five `speckit-git-*` skills name the 1.0.8 script names. No skill names `create-new-feature.ps1`.
- **FR-013**: The five `speckit.git.*` agent files are removed from `.github/agents/`.
- **FR-014**: The `speckit-taskstoissues` skill and its agent are removed.
- **FR-015**: Companion 0.24.0 stays installed. This change adds no companion 0.27.0 file.
- **FR-016**: Both integration manifests hold the SHA-256 hash of each managed file, as committed.
- **FR-017**: `.github/copilot-instructions.md` lists each managed file that differs from upstream, with its local rule.
- **FR-018**: A guard test fails when a managed file hash differs and no local rule names the file.
- **FR-019**: `.specify/.gitignore` keeps the `!feature.json` re-include. `.specify/feature.json` stays tracked.
- **FR-020**: This change does not write `.specify/feature.json`. Dry runs use `SPECIFY_FEATURE_DIRECTORY` instead.
- **FR-021**: Each line that this change adds or changes has an inline comment. Untouched upstream lines follow the Complexity Tracking table in `plan.md`.
- **FR-022**: Script output that this change adds or changes is ASCII only.

### Key Entities

- **Routed record**: A folder at `specs\numbered\<route>\<NNNN-slug>\`. The eight route digits are the base-5 digits of the issue number.
- **Managed file**: A file listed in `.specify/integrations/copilot.manifest.json` or `.specify/integrations/speckit.manifest.json`, with a SHA-256 hash.
- **Local rule**: A documented reason that a managed file differs from upstream.
- **Git extension tree**: The files under `.specify/extensions/git/`, as released with Spec Kit 1.4.3.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `specify integration status` reports no managed file without a documented local rule. The PR records the command output.
- **SC-002**: Every guard test named in `tasks.md` passes in T-LOCAL-GATES.
- **SC-003**: The core dry run prints a `SPEC_FILE` under `specs\numbered\`.
- **SC-004**: The PowerShell and bash git scripts print the same `FEATURE_NUM` for the same fixture.
- **SC-005**: The `speckit-git-*` skills name only the 1.0.8 script names.
- **SC-006**: `.specify/feature.json` is unchanged after the read-only runs in `quickstart.md`.
- **SC-007**: Each changed Markdown file in the STE list scores 80 or above in `ste-linter`.

## Assumptions

- **A-1**: Upstream tag `v1.4.3` is the reference for git extension 1.0.8. Verified by R-072 and R-073.
- **A-2**: CI runs `tests/guardrails` with `pwsh` installed. Verified in part: `test_spec_route_contract.py` needs `pwsh`, and PR #4909 checks passed.
- **A-3**: The Specify CLI computes managed hashes over file bytes. Not verified in this record (U-2). FR-016 depends on this assumption.
- **A-4**: Local commit `76b920fbc` holds upstream 1.0.8 content with routed numbering. Read only, not diffed against upstream (U-6).

## Out of Scope

- Installing companion 0.27.0. The owner deferred it on 2026-11-21.
- Adopting the template priority and composition engine. A separate issue owns it.
- Mist API, mistapi, and menu code changes. This record makes no Mist API claim.
- Upgrading the Specify CLI or changing its source.
- Branch protection, merge queue, and required status changes.
- Deleting local worktrees or the local commit `76b920fbc`. The orchestrator decides that.
