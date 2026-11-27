# Implementation Plan: Port the routed layout and the git extension to Spec Kit 1.4.3

**Branch**: `chore/4873-routed-git-extension` | **Issue**: #4873 | **Spec**: `spec.md` in this folder

## Summary

Part 1 (PR #4909) ported the routed core, and `main` holds it. This plan finishes the work in four parts:

1. Replace the git extension 1.0.0 tree with the upstream v1.4.3 tree, which bundles git extension 1.0.8.
2. Apply the routed numbering to the two 1.0.8 git scripts, in the same change, before merge.
3. Update the git skills, remove the `speckit.git.*` agents and the `speckit-taskstoissues` skill and agent.
4. Regenerate both integration manifests, document each local rule, and add guard tests.

Companion 0.27.0 stays deferred. The routed templates stay as they are.

## Technical Context

**Language/Version**: PowerShell 7 (`pwsh`) and Bash for Spec Kit scripts. Python 3.15.2 in `.venv` for guard tests.

**Primary Dependencies**: Spec Kit 1.4.3 integration, git extension 1.0.8 from upstream tag `v1.4.3`, `pytest`, `ruff`, `black`, `ste-linter`, `test-quality-analyzer`.

**Storage**: Git tree only. No database and no product output.

**Testing**: `pytest` guard tests under `tests/guardrails/`. PowerShell behavior runs through `pwsh`, as in `tests/guardrails/test_spec_route_contract.py`.

**Target Platform**: Windows 11 for PowerShell. macOS and Linux for the bash twin.

**Project Type**: Tooling change to the Spec Kit integration and its guards.

**Performance Goals**: None. The recursive scan reads only the `specs\` tree.

**Constraints**: Five-item rule for new folders. Managed hashes match committed content. ASCII-only output. No secret in any file.

**Scale/Scope**: The change map below lists each path. Seventeen git extension paths exist today. Upstream 1.0.8 has twenty-one.

## Constitution Check

Each rule in `.specify/memory/constitution.md` (version 1.9.0) has a result.

| Rule | Result | Reason |
| - | - | - |
| I. Five-Item Rule, new records | PASS | The feature root has five children. `design\` has five children. The route leaf holds one record. |
| I. Five-Item Rule, existing debt | FAIL, justified | `.specify/extensions/git/` has six children today. Complexity row C-1 records it. |
| I. Five-Item Rule, function limits | FAIL, justified | Upstream script bodies exceed 25 lines. Complexity row C-6 records it. |
| II. Class-based architecture | FAIL, justified | Upstream PowerShell and bash use functions. Complexity row C-5 records it. New Python tests use module functions, as `test_routed_core_port.py` does. |
| III. Safety-first | PASS | No new `input()` call. No destructive operation. Removed files stay in git history. |
| IV. Full deployment pipeline | PASS | Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE follow the ten stages. Stage 10 and later do not run: no product file changes. |
| V. ASCII logs and structured logs | PASS | FR-022 adds an ASCII test. No new service or module needs structured logs. |
| VI. Inline comments | PASS for changed lines, FAIL justified for untouched upstream lines | FR-021 requires comments on changed lines. Complexity row C-4 records the untouched lines. |
| VII. Action logging | PASS for Python tests, FAIL justified for upstream scripts | New Python tests do not perform product actions. Complexity row C-4 records the upstream scripts. |
| Technology: Python 3.15 | PASS | `.venv` runs the guard tests on Python 3.15.2. |
| Technology: mistapi | PASS, not applicable | No Mist API request changes. |
| Technology: UV | PASS | The repository bootstrap uses UV. |
| Technology: Podman | PASS, not applicable | No container runs in this change. |
| Technology: file paths | PASS | PowerShell uses `Join-Path` and `-LiteralPath`. Python tests use `pathlib`. |
| Technology: data directory | PASS | No product output goes outside `data\`. |
| Technology: container security and Zscaler | PASS, not applicable | No container build or push. |
| Development workflow: menu operations | PASS, not applicable | No menu change. |
| Security findings | PASS | No suppression comment is added. |
| Documentation | PASS | `.github/copilot-instructions.md` and a changelog fragment change. |
| Audience standard | PASS | New prose uses plain words. |
| SpecKit escalation | PASS | The change touches more than three files. The spec exists. |
| Multi-agent git workflow | PASS | Issue #4873 has the `in-progress` label. One branch, one PR, branched from `main`. |

## Architecture

- **Routed core (done)**: `.specify/scripts/powershell/create-new-feature.ps1`, `common.ps1`, and `spec-route.ps1` on `main`. No change.
- **Git extension 1.0.8 (new tree)**: Upstream v1.4.3 files under `.specify/extensions/git/`. The routed numbering is added to the two new script names.
- **Skills and agents**: Five `speckit-git-*` skills follow the 1.0.8 commands. The `speckit.git.*` agents and the `speckit-taskstoissues` pair are removed.
- **Integration state**: Manifests hold the committed hashes. `.github/copilot-instructions.md` lists each local rule. A new guard test enforces both.
- **Record**: One folder at the route, replacing the part 1 files.

Warning: The local commit `76b920fbc` on `chore/4873-routed-git-extension` is not on GitHub. Deleting that worktree or its branch removes the only copy of that work.

## File-by-File Change Map

Paths start at the repository root. `(add)`, `(modify)`, and `(delete)` name the operation.

### Git extension

- `.specify/extensions/git/extension.yml` (modify): Version 1.0.0 becomes upstream 1.0.8.
- `.specify/extensions/git/README.md` (modify): Upstream 1.0.8 text.
- `.specify/extensions/git/config-template.yml` (modify): Upstream 1.0.8 text.
- `.specify/extensions/git/git-config.yml` (modify): Upstream 1.0.8 text.
- `.specify/extensions/git/commands/speckit.git.commit.md` (modify): Upstream 1.0.8 text.
- `.specify/extensions/git/commands/speckit.git.feature.md` (modify): Upstream 1.0.8 text, with the new script names.
- `.specify/extensions/git/commands/speckit.git.initialize.md` (modify): Upstream 1.0.8 text.
- `.specify/extensions/git/commands/speckit.git.validate.md` (modify): Upstream 1.0.8 text.
- `.specify/extensions/git/commands/speckit.git.remote.md` (keep): Blob matches upstream (R-109).
- `.specify/extensions/git/scripts/powershell/create-new-feature.ps1` (delete): Replaced by the 1.0.8 name.
- `.specify/extensions/git/scripts/powershell/create-new-feature-branch.ps1` (add): Upstream 1.0.8 plus routed numbering (FR-008) and comments on changed lines.
- `.specify/extensions/git/scripts/powershell/auto-commit.ps1` (modify): Upstream 1.0.8 text.
- `.specify/extensions/git/scripts/powershell/git-common.ps1` (modify): Upstream 1.0.8 text.
- `.specify/extensions/git/scripts/powershell/initialize-repo.ps1` (modify): Upstream 1.0.8 text.
- `.specify/extensions/git/scripts/bash/create-new-feature.sh` (delete): Replaced by the 1.0.8 name.
- `.specify/extensions/git/scripts/bash/create-new-feature-branch.sh` (add): Upstream 1.0.8 plus routed numbering (FR-009) and comments on changed lines.
- `.specify/extensions/git/scripts/bash/auto-commit.sh` (modify): Upstream 1.0.8 text.
- `.specify/extensions/git/scripts/bash/git-common.sh` (modify): Upstream 1.0.8 text.
- `.specify/extensions/git/scripts/bash/initialize-repo.sh` (modify): Upstream 1.0.8 text.
- `.specify/extensions/git/scripts/python/auto_commit.py` (add): Upstream 1.0.8 text.
- `.specify/extensions/git/scripts/python/create_new_feature_branch.py` (add): Upstream 1.0.8 text. Its numbering follows FR-008 and FR-009.
- `.specify/extensions/git/scripts/python/git_common.py` (add): Upstream 1.0.8 text.
- `.specify/extensions/git/scripts/python/initialize_repo.py` (add): Upstream 1.0.8 text.
- `.specify/extensions/.registry` (modify): The `git` entry moves to version 1.0.8 and its `manifest_hash`. The `companion` entry does not change.

### Skills and agents

- `.github/skills/speckit-git-commit/SKILL.md` (modify): Names the 1.0.8 scripts.
- `.github/skills/speckit-git-feature/SKILL.md` (modify): Names `create-new-feature-branch.ps1` and `.sh`.
- `.github/skills/speckit-git-initialize/SKILL.md` (modify): Matches the 1.0.8 command text.
- `.github/skills/speckit-git-remote/SKILL.md` (modify): Matches the 1.0.8 command text.
- `.github/skills/speckit-git-validate/SKILL.md` (modify): Matches the 1.0.8 command text.
- `.github/agents/speckit.git.commit.agent.md` (delete).
- `.github/agents/speckit.git.feature.agent.md` (delete).
- `.github/agents/speckit.git.initialize.agent.md` (delete).
- `.github/agents/speckit.git.remote.agent.md` (delete).
- `.github/agents/speckit.git.validate.agent.md` (delete).
- `.github/skills/speckit-taskstoissues/SKILL.md` (delete).
- `.github/agents/speckit.taskstoissues.agent.md` (delete).

Caution: Deleting the agent files removes the `/speckit.git.*` agent commands. The `speckit-git-*` skills keep each command. Restore a file from git history if a user needs it.

### Integration state and docs

- `.specify/integrations/copilot.manifest.json` (modify): Hashes regenerated from committed content. Version stays `1.4.3`.
- `.specify/integrations/speckit.manifest.json` (modify): Hashes regenerated from committed content. Version stays `1.4.3`.
- `.github/copilot-instructions.md` (modify): Adds the list of managed files with a local rule.
- `changelog.d/issue-4873-routed-git-extension.md` (add): One fragment for this change.

### Tests

- `tests/guardrails/test_routed_git_extension_port.py` (add): Git extension numbering, skill names, and agent removal.
- `tests/guardrails/test_integration_local_rules.py` (add): Managed hash and local rule checks.

### Record

- `specs\numbered\0\0\1\2\3\4\4\3\4873-routed-git-port\spec.md` (modify): Replaces the part 1 spec.
- `specs\numbered\0\0\1\2\3\4\4\3\4873-routed-git-port\plan.md` (modify): Replaces the part 1 plan.
- `specs\numbered\0\0\1\2\3\4\4\3\4873-routed-git-port\tasks.md` (modify): Replaces the part 1 tasks.
- `specs\numbered\0\0\1\2\3\4\4\3\4873-routed-git-port\analysis.md` (add).
- `specs\numbered\0\0\1\2\3\4\4\3\4873-routed-git-port\design\` (add): Research, data model, quickstart, contracts, and checklists.

### Unchanged

- `.specify/scripts/powershell/*` (routed core, including `spec-route.ps1`).
- `.specify/templates/*` (routed templates).
- `.specify/.gitignore` and `.specify/feature.json`.
- `tests/guardrails/test_routed_core_port.py`, `test_spec_route_contract.py`, `test_specify_gitignore_keeps_feature_json.py`, and `process_folder_baseline.json`.
- `.github/workflows/ci.yml` and `.specify/memory/constitution.md`.

## Dependencies

- Upstream tag `v1.4.3` at `github/spec-kit`. Blob SHAs are in `design/research.md`.
- `.venv` with Python 3.15.2, `pytest`, `ruff`, `black`, and `pwsh` 7.
- `gh` CLI for read-only remote checks and the PR steps.
- `ste-linter` and `test-quality-analyzer` from `requirements-dev.txt`.

## Risks and Mitigations

| Risk | Mitigation |
| - | - |
| Caution: a later rebase drops the routed lines in the 1.0.8 scripts. | FR-008 and FR-009 tests fail when the scan is not recursive. |
| Caution: the CLI computes a different hash from the byte hash in this record. | U-2 records the uncertainty. SC-001 requires the CLI output in the PR. |
| Caution: removing `speckit-taskstoissues` removes an automation. | The label rule in AGENTS.md blocks its output. Git history restores the file. |
| Caution: a dry run changes `.specify/feature.json`. | FR-020 and SC-006. Use `SPECIFY_FEATURE_DIRECTORY` for every dry run. |
| Warning: deleting the local worktree or branch removes unpushed commit `76b920fbc`. | The orchestrator keeps the worktree until T-PR completes. |
| Ruff and Black scan `.specify/`, so the Python scripts face the gates. | T-LOCAL-GATES runs both commands. Each failure gets a fix or a recorded cause. |
| `pwsh` is missing on a CI runner. | A-2. The PR checks show the guardrails shard result. |
| The symlink case fails on a host without the privilege. | Existing skip rule in part 1. The PR records the host. |

## Rollback

1. Revert the squash commit on `main` with a new branch and a new PR. Never force-push `main`.
2. The revert restores the part 1 spec, plan, and tasks files. Git keeps every removed file.
3. Run `specify integration status` in the reverted tree. Confirm that the manifests match the previous commit.
4. No product output changes. No data migration is needed.

## Complexity Tracking

| Row | Violation | Why Needed | Simpler Alternative Rejected Because | Remediation |
| - | - | - | - | - |
| C-1 | `.specify/extensions/git/` has six children. | Upstream 1.0.8 has the same six entries. | Moving an entry breaks the upstream layout and the extension registry. | Follow-up issue after T-MERGE: reduce the children of `.specify/extensions/git/`. |
| C-2 | `.specify/scripts/powershell/` has nine children. | Existing routed core layout. This change adds no child. | Moving scripts breaks the routed core contract. | Follow-up issue after T-MERGE. |
| C-3 | `.github/skills/` and `.github/agents/` have more than five children. | Existing Copilot integration layout. This change removes entries and adds none. | Splitting the folders breaks the integration discovery. | Follow-up issue after T-MERGE. |
| C-4 | Untouched upstream lines in the adopted scripts lack inline comments and action logs. | Principles VI and VII apply to the lines this change adds or changes. Upstream lines stay identical so future upstream diffs stay small. | Rewriting all upstream lines creates a large unreviewed diff. | Follow-up issue: comment and logging pass on the adopted scripts. |
| C-5 | Upstream PowerShell and bash scripts use functions, not classes. | Upstream design. | Rewriting them into classes creates drift from upstream. | Follow-up issue with the C-4 pass. |
| C-6 | Some upstream script functions exceed 25 lines. | Upstream design. | Splitting them creates drift from upstream. | Follow-up issue with the C-4 pass. |

## Verification Steps

1. Parse each changed `.ps1` file with `pwsh` and expect no parse error.
2. Run the guard tests named in `tasks.md`.
3. Run the commands in `design/quickstart.md`.
4. Record the results in the PR body. Record each gate that does not apply, with its reason.
