# Implementation Plan: Stranded Branch Preservation

**Branch**: `chore/4719-stranded-branch-preservation` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification at `specs/numbered/0/0/1/2/2/3/3/4/4719-stranded-branch-preservation/spec.md`. Route `0/0/1/2/2/3/3/4` is the base-5 form of 4719 with eight levels.

The record root holds `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, and `design/`. The design folder holds the research, the data model, the quickstart, one contract, and two checklists.

## Summary

Issue #4719 reports 51 remote branches with commits above `main` and no pull request. This plan keeps every branch intact. After the owner releases the publication hold, it opens draft preservation pull requests in three batches. It moves the duplicate-issue defect to `misthelper-devtools`, which owns the reusable workflow.

## Technical Context

**Language/Version**: Not applicable. This record adds Markdown files only.

**Primary Dependencies**: `gh` for GitHub reads and, after the hold release, pull request creation. `git` for read-only commit and path listing. `pytest` for the guardrail suite.

**Storage**: None. The inventory follows the CSV contract in `design/contracts/branch-inventory.md`.

**Testing**: Read-only checks TC-01 to TC-12 in `design/quickstart.md`. The guardrail suite `python -m pytest tests/guardrails` runs in the record worktree.

**Target Platform**: Windows 11 workstation with PowerShell, and GitHub.com.

**Project Type**: Process record and repository documentation.

**Performance Goals**: None.

**Constraints**: GitHub API limits. The publication hold. The privacy hold for one branch. No branch deletion.

**Scale/Scope**: 51 branches. 66 commits. 515 changed path entries. Batch 1 holds 46 branches.

## Constitution Check

*Gate: passes before research. Re-checked after design. One rule fails, as recorded below.*

| Principle or rule | Result | Reason |
| - | - | - |
| I. Five-item rule | Pass | The record root holds 5 children. `design` holds 5. `design/contracts` holds 1. `design/checklists` holds 2. The route adds child `4` under `specs/numbered/0/0/1/2/2/3/3`, which holds 4 children on `main` (verified). The node `specs/numbered/0/0/1/2` already holds 5 children. The route reuses its child `2`, so it adds none. |
| II. Class-based architecture | Pass | No code. |
| III. Safety first | Pass | No destructive operation. No secret in the record. The publication hold and the privacy hold stay in force. |
| IV. Full deployment pipeline, steps 1 to 9 | Pass | Local gates run where they apply. Explicit paths are staged. The branch rebases on `origin/main`. The pull request carries the required title and checks. The squash merge waits for authorization. |
| IV. Full deployment pipeline, steps 10 to 12 | Fail | `container-build.yml` runs on a push to `main` that changes a product file (blob `737325976de75e90aa4526ab1cf2978782e648ce`, line 6). This record changes no product file, so no image builds and no image revision exists to verify. The pull request body reports this result. Decision D-10 records it. |
| V. Observability and logging | Pass | No code and no log line. The record uses ASCII only. |
| VI. Inline comments | Pass | No code. |
| VII. Action logging | Pass | No code. Each batch step records its inputs in the pull request body. |
| Mist Cloud transport | Pass | No Mist Cloud call. |
| Output backends and database keys | Pass | Not applicable. No export and no operation. |
| Data directory and container security | Pass | No product output. No container. |
| Test containers and Zscaler | Pass | No container. |
| Menu and operation rules | Pass | No menu operation. |
| Testing and security findings | Pass | No code test changes. The guardrail suite runs in TC-11. |
| Documentation and release notes | Pass | One fragment, `changelog.d/issue-4719-stranded-branch-preservation.md`. `README.md` and `CHANGELOG.md` stay unchanged. |
| Escalation to SpecKit | Pass | This record is the specification for a change that touches many branches and two repositories. |
| Multi-agent git workflow | Pass | The branch name is `chore/4719-stranded-branch-preservation`, which follows the constitution pattern. The labels are `chore`, `ci`, and `in-progress`. The title and body rules apply. No push goes to `main`. |
| Governance | Pass | This table covers each rule that the constitution names for a pull request. |

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/2/3/3/4/4719-stranded-branch-preservation/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      branch-inventory.md
    checklists/
      requirements.md
      preservation.md
```

### Repository change map

| Path | Action | Purpose |
| - | - | - |
| `specs/numbered/0/0/1/2/2/3/3/4/4719-stranded-branch-preservation/` | Add | The ten record files listed above. |
| `changelog.d/issue-4719-stranded-branch-preservation.md` | Add | One release-note fragment. |
| `.github/workflows/stranded-branch-report.yml` | No change | The pin moves in task T021 only. |
| `.github/workflows/close-linked-issues.yml` | No change | The pin moves in task T021 only. |
| `CHANGELOG.md`, `README.md`, `.github/copilot-instructions.md` | No change | The release coordinator owns `CHANGELOG.md`. No menu or operation changes. |

## Architecture

Implementation outline:

1. Verify the inventory on `main` and in the local clone. Tasks T001 to T007 are complete, except T006, which is partial.
2. Merge the record pull request. Tasks T-LOCAL-GATES to T-MERGE run in order.
3. After the owner releases the publication hold, open 46 draft preservation pull requests. Task T011 runs this step.
4. Open the deferred batches after owner review. Tasks T012 and T013 run these steps. Task T014 verifies the local-only branches.
5. Move both workflow pins after the upstream fix ships. Task T021 runs this step. Then close the duplicates in task T022.

## Dependencies

- `gh` CLI with account access to `jmorrison-juniper/MistHelper` and `jmorrison-juniper/misthelper-devtools`.
- `git` for read-only commands in the local clone.
- `misthelper-devtools` tag `v0.6.4` at pin `79a5e45970e876f1656d69520d9635cea1aa25ef`, and any later released tag.
- Owner comments on issue #4719 that release each hold.

## Risks and Mitigations

| Risk | Mitigation |
| - | - |
| A branch head changes after the inventory | Repeat the head check before each batch. Reject a row whose head changed. |
| A preservation pull request conflicts with an open pull request | Use the deferred batch rule (D-6). The owner reconciles first. |
| Private content leaves the clone through a pull request | Use the privacy hold (D-5). Keep metadata only until the review. |
| The weekly report keeps creating issues until the upstream fix ships | Caution: five open duplicates exist. The owner closes them in task T022 after the fix. |
| The closing keyword closes issue #4719 on merge | Decision D-8 accepts the closure. The next report opens a new tracking issue until task T021 lands. |
| Local-only branches are lost on the workstation | Decision D-13. The owner verifies them in their own clone first. |

## Rollback Steps

1. If a preservation pull request opens in error, close it without a merge. Its head stays kept while the head SHA is unchanged.
2. If the record pull request merges in error, open a new pull request that removes the record folder and the fragment.
3. If the pin move in task T021 breaks the weekly report, open a new pull request that restores the previous pin.

Warning: a force-push to `main` removes history for every contributor. Do not force-push to `main`.

## Complexity Tracking

| Violation or debt | Why it exists | Simpler alternative rejected because | Remediation |
| - | - | - | - |
| Five open tracking issues share one title: 4302, 4583, 4719, 4818, and 4911 | The workflow title search misses open issues | Closing them before the upstream fix loses the thread | Tasks T020 to T022 |
| 434 archive rows and 20 other rows in issue #4911 | Branches under `archive/laptop-20261121/` exist on GitHub, and the report lists them | Opening pull requests now publishes unreviewed content | Separate record, task T015 |
| Route node `0/0/1/2` holds 5 children on `main` | Existing numbered records occupy the node | None. The route reuses an existing child. | None needed. The limit stays recorded. |

## Contracts

`design/contracts/branch-inventory.md` defines the inventory columns. This record needs no menu, CLI, or API contract.
