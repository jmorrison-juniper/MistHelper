# Implementation Plan: Backlog Handoff Recovery

**Branch**: `chore/4870-backlog-handoff-recovery` | **Date**: 2026-11-26 | **Spec**: specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/spec.md

**Input**: Numeric specification from `specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/spec.md`.

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Place research, data model, quickstart, contracts, and checklists under `design/`. Keep five children or fewer at every new directory level.

## Summary

The record turns the handoff for issue 4870 into a verified state, a decision set, and an ordered task list. The change adds documents only. It changes no code, no workflow, and no repository setting. The GitHub handoff itself changes through the later tasks T021 and T022.

## Technical Context

**Language/Version**: Markdown for the record, JSON for the STATUS file, and PowerShell for read-only checks.

**Primary Dependencies**: The gh CLI for reads now and writes later under decision D-10. Git for read-only checks. The `ste-linter` tool from the devtools pin in `requirements-dev.txt`. The pytest guard tests.

**Storage**: GitHub holds the issues, PRs, and refs. The record stores files only.

**Testing**: The checks TST-01 to TST-37 in `design/quickstart.md`. The Tests and STE rows of the local gates table run in task T-LOCAL-GATES.

**Target Platform**: A Windows 11 coordinator for the checks and GitHub Actions for CI.

**Project Type**: Documentation record in the numbered Spec Kit route.

**Performance Goals**: Not applicable. No runtime path changes.

**Constraints**: GitHub rate limits, one merge at a time, no secret values in files, and no destructive command in this change.

**Scale/Scope**: 166 open issues and 7 open PRs. Also 151 named issues, 36 named PRs, 63 recovery refs, and 169 archive tags. Also 2535 commits on main and 10 devtools uses lines in 8 workflow files.

## Constitution Check

The gate passes before research and after design. Each rule has a result and a reason.

| Rule | Result | Reason |
| - | - | - |
| Principle I: five-item rule (constitution.md:38) | Pass | The record adds one leaf route, 0/0/1/2/3/4/4/0, under `specs/numbered`. Each directory in the record holds five children or fewer (TST-26). |
| Principle I: new records use managed roots and the base-5 route | Pass | The route is the base-5 form of 4870, and the root is `specs/numbered` (R-34, TST-19). |
| Principle I: no new direct child in a noncompliant parent | Pass | The `specs/numbered` root gains no direct child. The numbered chain already exists for other records. |
| Principle II: class-based architecture | Not applicable | The change has no code. |
| Principle III: safety-first and typed confirmation | Pass | The change has no destructive operation. Later destructive steps stay out of scope (FR-011 and FR-016). |
| Principle III: secrets stay out of logs and files | Pass | The record stores no secret value (FR-017). The `.env` file stays in place (D-14). |
| Principle IV: full deployment pipeline | Pass with notes | Local gates, PR, CI, and squash merge apply (T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE). The main build step does not apply, because `container-build.yml` triggers only on product paths (R-45). The deploy step does not apply to a documentation change. |
| Principle V: ASCII output | Pass | Each record file uses ASCII characters only (TST-28). |
| Principle VI: inline comments | Not applicable | The change has no code. |
| Principle VII: action logging | Not applicable | The change has no code. |
| Technology: mistapi is the only Mist interface | Not applicable | The change makes no Mist request. |
| Technology: Podman and compose group rules | Not applicable | The change starts no container. FR-016 keeps the volume rule. |
| Technology: container build through GitHub Actions | Not applicable | The change builds no image. |
| Development workflow: a spec for three or more files | Pass | This record is the specification. |
| Documentation: one changelog fragment for each change (constitution.md:409) | Pass | Task T-PR adds one fragment. The analysis explains the conflict with the user-visible rule in copilot-instructions. |
| Documentation: Markdown passes the STE gate | Pass, planned | Task T-LOCAL-GATES runs the STE gate at score 80 or above (TST-20). |
| Multi-agent git: one type label and one scope label | Pass | Issue 4870 carries `chore` and `docs`. The label check R-30 confirms that the labels exist. |
| Multi-agent git: claim before the branch | Pass, planned | The STATUS file asks for the `in-progress` label. The orchestrator applies it before T-PR. |
| Multi-agent git: branch from main with the issue number | Pass, planned | The branch is `chore/4870-backlog-handoff-recovery`, from main. |
| Multi-agent git: file overlap check | Pass, planned | Task T-PR reads the file lists of the seven open PRs before the branch starts. |
| Multi-agent git: PR body closes the issue | Pass, planned | Task T-PR writes `Closes #4870` in the body. |
| Multi-agent git: squash merge only | Pass, planned | Task T-MERGE uses one squash merge after CI passes. |
| Governance: the constitution outranks practice documents | Pass | The constitution governs the changelog rule (see analysis.md, finding A-07). |

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      inventory-table.md
      decision-comment.md
    checklists/
      requirements.md
      security.md
```

Each directory holds five children or fewer. The record root holds spec.md, plan.md, tasks.md, analysis.md, and design. The design directory holds research.md, data-model.md, quickstart.md, contracts, and checklists.

### Source Code

Not applicable. The change touches no source file.

**Structure Decision**: The record uses the numbered route from `.specify/scripts/powershell/spec-route.ps1` and the layout of the reference record 4920. Supporting artifacts go under `design/`, because the feature root would otherwise exceed five children.

## Architecture

The flow has five steps. GitHub main is the source of state. The verification checks write rows to `design/research.md`. Decisions and tasks come from those rows. Human-approved comments update the handoff. The repository change then carries the record through the serial PR path.

## File-by-File Change Map

| Path | Action | Purpose |
| - | - | - |
| specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/spec.md | Add | Stories, requirements, clarifications, and success criteria |
| specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/plan.md | Add | This plan |
| specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/tasks.md | Add | Ordered tasks with requirement IDs and checks |
| specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/analysis.md | Add | Consistency review and defects |
| specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/design/research.md | Add | Remote table, decisions, sources, and unverified claims |
| specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/design/data-model.md | Add | Entities, keys, and state transitions |
| specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/design/quickstart.md | Add | Reproduction steps and checks TST-01 to TST-37 |
| specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/design/contracts/inventory-table.md | Add | Columns and categories of the refreshed inventory |
| specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/design/contracts/decision-comment.md | Add | Format of each dated decision comment |
| specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/design/checklists/requirements.md | Add | Specification quality checklist |
| specs/numbered/0/0/1/2/3/4/4/0/4870-backlog-handoff-recovery/design/checklists/security.md | Add | Credential, identity, and write checklist |
| changelog.d/issue-4870-backlog-handoff-recovery.md | Add | One changelog fragment, added by task T-PR |

No existing file changes. No file is deleted. `.specify/feature.json` keeps its pinned value (D-1). No path outside the record folder and the fragment changes (FR-022).

## Dependencies

- Open issue 4873 ports the routed layout. Its status affects the route helper.
- Open issue 4910 reports lost hardening in the routed setup scripts.
- Open issues 4877, 4878, and 4917 report guard failures on Windows. They limit the local gate results.
- Open issues 4200 and 4776 track the acceptance of PR 4208 and PR 4813.
- Open quality-gate issues 4891 to 4908 block the Dependabot PRs.
- Tools: the gh CLI under the jmorrison-juniper account, git for read-only checks, and the `.venv` tools for the STE gate and pytest.
- Order: T-LOCAL-GATES runs before T-PR. T-PR runs before T-REMOTE-CI. T-MERGE starts only after T-REMOTE-CI passes.

## Risks and Mitigations

| Risk | Impact | Mitigation |
| - | - | - |
| The handoff drifts again before any action | High. The drift already exists. | Run TST-03, TST-04, and TST-05 before each action. Refresh the inventory with the contract. |
| The route helper regresses (issues 4910 and 4873) | Medium | Run TST-09 and TST-22 before T-PR. T-LOCAL-GATES runs the route contract test. |
| A Windows host fails a local guard (issues 4877, 4878, and 4917) | Medium | Record the local result as it is. The CI run decides. No local pass is claimed. |
| Warning: a write runs under the wrong GitHub identity | High | Decision D-10 and FR-018 require the identity check before each write. |
| Warning: a recovery ref is deleted by mistake | High | FR-011 and TST-07 count the refs before and after the work. |
| Caution: the devtools pin change alters gate results | Medium | Decision D-7 limits the change to one PR. CI runs before the merge. The rollback restores the v0.6.4 pins. |
| A Dependabot PR merges with a red gate | Medium | Decision D-6 and FR-009 block a merge with a red gate. |
| A hold phrase matches ordinary text | Low | Decision D-9 uses whole-word matches. A reviewer decides each match. |
| The feature pointer changes by mistake | Low | FR-006 and TST-29 check the blob before and after T-PR. |
| Warning: a Podman volume is lost | High | FR-016 forbids pruning. The rule appears at container-deployment.md:50 (R-59). |
| A human decision waits too long | High | The four human decisions stay in one list. Routine tasks continue while they wait. |

## Rollback Steps

1. If T-PR is wrong before its merge, close the PR without a merge. Keep the branch until the record exists in another place.
2. If the feature pointer changes, open a new PR that restores blob b86bcad0. Do not edit the pointer directly on main.
3. If a merge breaks main, stop the merge slot. Open a new revert PR for the squash commit.
4. If the devtools pins break CI, open one PR that restores the ten uses lines to 79a5e459. Keep the three Python pins at 2239e7bd.
5. If the handoff body changes wrongly, restore the earlier text from the saved copy in the dated comment.
6. No rollback is needed for the recovery refs, because this work deletes none.

Warning: a force push to main rewrites shared history and cannot be undone for other clones. No rollback step uses a force push to main.
