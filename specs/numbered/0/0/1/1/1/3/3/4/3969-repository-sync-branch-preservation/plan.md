# Implementation Plan: Repository Sync Branch Preservation

**Branch**: `docs/3969-repository-sync-branch-preservation` | **Date**: 2026-11-26 | **Spec**: spec.md

**Input**: Numeric specification from `specs/numbered/0/0/1/1/1/3/3/4/3969-repository-sync-branch-preservation/spec.md`.

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Place research, data model, quickstart, and checklists under `design/`. This record omits the contracts folder. Section "Project Structure" gives the reason.

## Summary

The sync report stopped on an ownership collision. It names branches, worktrees, and pull requests that the owner must verify. This plan checks each claim and preserves unique commits with tags. It deletes local branches only after gates pass. It refreshes the container after the claim is released. This plan changes no repository state, and it adds Markdown record files only.

## Technical Context

- **Language/Version**: Not applicable. The record adds Markdown only.
- **Primary Dependencies**: `git` for local reads and for the writer's tag and delete steps. `gh` for GitHub reads. `ste-linter` for the STE gate, configured by `.ste-linter.toml` (R41).
- **Storage**: Git refs only. Preservation tags are lightweight refs under refs/tags/archive/preservation.
- **Testing**: Verification commands VC-01 to VC-16 in design/quickstart.md. The STE gate runs in T-LOCAL-GATES.
- **Target Platform**: Windows 11 with PowerShell for the writer commands. Git and gh commands use the same syntax on each platform.
- **Project Type**: Repository maintenance record.
- **Performance Goals**: Not applicable. The record defines no runtime service.
- **Constraints**: The author role runs read-only commands only. The writer runs no force push, no all-tags push, no hard reset, no stash, and no clean command.
- **Scale/Scope**: 329 local branches besides main, 598 GitHub branches, 14 named pull requests, and 181 new preservation tags.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Rule | Result | Reason |
| - | - | - |
| I. Five-Item Rule | Pass | The record folder holds five children. The design folder holds four. The checklists folder holds one. |
| II. Class-Based Architecture | Not applicable | The record adds no code. |
| III. Safety-First | Pass | Each destructive step has a gate in tasks.md. Owner decision D-5 gates each discard. The deletion runbook requires a typed confirmation word before it runs. |
| IV. Full Deployment Pipeline | Pass | The record ships through T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE. Tag and delete steps follow gates G3 to G5. |
| V. Observability and Logging | Not applicable | The record adds no runtime code. Each command prints its result, and the proof comment records each result. |
| VI. Inline Comments | Not applicable | The record adds no code. |
| VII. Action Logging | Not applicable | The record adds no code. |
| Mist Cloud constraints | Not applicable | The record makes no Mist Cloud request. |
| Container runtime | Pass | The container refresh uses the compose script and the service name (R20, R21). Podman commands match the repository runbook. |
| Data directory | Pass | The refresh writes no product output. Both named volumes stay in place. |
| Multi-agent workflow | Pass | The claim rule comes first (R27). Decision D-7 allows one writer at a time. |

Complexity Tracking: Not applicable. The constitution check has no violation.

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/1/1/3/3/4/3969-repository-sync-branch-preservation/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    checklists/
      requirements.md
```

Contracts: Omitted. This record changes no menu, command, API request, or output format. The tag name rule appears in FR-004 and in decision D-2.

### Source Code

Not applicable. The record adds no source code.

## Architecture

The plan uses six gates. A step runs only after its gate passes.

1. Claim gate G1: the writer comments one claim on issue #3969.
2. Verify gate G2: the writer reruns the 106 remote checks in design/research.md.
3. Inventory gate G3: the owner records the worktree inventory and each modified path. Decision D-5 applies.
4. Preserve gate G4: the writer creates 181 preservation tags. Each tag resolves to its target commit.
5. Delete gate G5: each class recheck passes before its local deletion.
6. Container gate G6: the owner refreshes the container only after claim release. Both volumes remain.

Class rules. The class names come from the classification loop in design/quickstart.md.

| Class | Count | Meaning | Gate before deletion | Tag needed |
| - | - | - | - | - |
| A | 4 | No commit beyond origin/main | Zero commits beyond origin/main | No |
| B | 135 | Tip equals the head of a merged pull request | Tip equals that head | No |
| C | 129 | Tip differs from the head of a merged pull request | Tag check at gate G4 | Yes |
| D | 47 | No pull request and no GitHub branch. At least one commit has no equivalent on origin/main | Tag check at gate G4 | Yes |
| E | 7 | No pull request and no GitHub branch. Every commit has an equivalent on origin/main | No merge commit and one minus line | No |
| F | 7 | GitHub branch exists with the same tip and no pull request | Keep | No |
| G | 0 | Matches the head of an open pull request | Not applicable. No branch matches | Not applicable |

## File-by-file change map

| Path | Action | Purpose |
| - | - | - |
| specs\numbered\0\0\1\1\1\3\3\4\3969-repository-sync-branch-preservation\spec.md | Add | Specification with requirements and success criteria |
| specs\numbered\0\0\1\1\1\3\3\4\3969-repository-sync-branch-preservation\plan.md | Add | This plan |
| specs\numbered\0\0\1\1\1\3\3\4\3969-repository-sync-branch-preservation\tasks.md | Add | Ordered tasks with gates and verification |
| specs\numbered\0\0\1\1\1\3\3\4\3969-repository-sync-branch-preservation\analysis.md | Add | Consistency review and defects |
| specs\numbered\0\0\1\1\1\3\3\4\3969-repository-sync-branch-preservation\design\research.md | Add | Decisions, remote checks, local checks, sources, and unverified items |
| specs\numbered\0\0\1\1\1\3\3\4\3969-repository-sync-branch-preservation\design\data-model.md | Add | Entities, natural keys, and state transitions |
| specs\numbered\0\0\1\1\1\3\3\4\3969-repository-sync-branch-preservation\design\quickstart.md | Add | Read-only checks, writer steps, and verification commands |
| specs\numbered\0\0\1\1\1\3\3\4\3969-repository-sync-branch-preservation\design\checklists\requirements.md | Add | Specification quality checklist |

Repository state that the writer changes. These changes are refs, not files.

| Ref or path | Action | Count | Gate |
| - | - | - | - |
| refs/tags/archive/preservation/3969-* | Add locally, then push to GitHub | 181 | G4 |
| Local branches of classes A to E | Delete locally | 322 | G5 |
| Local branches of class F | Keep | 7 | G3 and FR-008 |
| Modified paths in the main checkout | Keep | 5 | G3 and D-5 |

## Dependencies

- The `gh` command reads the token from the environment variable named `COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper`. Each `gh` command sets `GH_HOST` and `GH_TOKEN` from that name. The token value never appears in output.
- The `git` command runs on the writer host with the clone path set in design/quickstart.md.
- The `ste-linter` command comes from the `misthelper-devtools` package (R22 names the shared command set). Its install state on the writer host is unverified (U-10).

## Risks and Mitigations

- Risk: a tag push stops part way. Mitigation: rerun only the missing tags, then verify the full set with VC-04.
- Risk: a branch name matches the wrong pull request. Mitigation: class B requires tip equality, not name equality.
- Risk: a worktree holds unsaved edits. Mitigation: gate G3 and decision D-5.
- Risk: the counts drift after the evidence date. Mitigation: rerun the checks in task T002 before any write.
- Warning: a container refresh that removes a named volume destroys captures and upgrade runs. Mitigation: the runbook has no volume removal command, and VC-13 checks both volumes after the refresh.
- Risk: the STE gate rejects the record. Mitigation: repair the text and rerun the gate. Do not lower the threshold.

## Rollback

- Preservation tags: Remove a tag only after the owner approves. Run the remote delete and the local delete for that tag name.
- Warning: removing a preservation tag can leave its commits without a remote copy. Confirm another copy exists first.
- Local deletions: Restore a class C or class D branch from its tag with a branch command that names the tag commit. Restore a class A, B, or E branch from the ref snapshot saved in quickstart step S3.
- Container: Start the previous image by its tag. The previous image tag is unverified (U-3).
- Record: Remove the record folder from the branch before the merge.

## Gates that do not apply to this change (T-LOCAL-GATES)

The local gates table in `.github/copilot-instructions.md` lists each gate (R17 points to its STE row). This record changes Markdown only. The following gates do not apply: compile, lint, format, types, and tests. Also not applicable: full tests, safe sweep, coverage, and test quality. Also not applicable: complexity, security lint, dependency audit, and code quality. Also not applicable: dead code, docstrings, menu reference, symbols, ops portal, and ops platform. The STE gate applies to each Markdown file in the record.

## Verification commands

The local gates table has no gate for branch or tag state. Each sync task names a read-only command from design/quickstart.md instead. Analysis item U-GAP-1 records this gap.
