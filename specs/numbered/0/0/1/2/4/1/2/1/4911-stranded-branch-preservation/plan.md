# Implementation Plan: Stranded branch preservation

**Branch**: `chore/4911-stranded-branch-preservation` | **Date**: 2026-11-26 | **Spec**: `specs/numbered/0/0/1/2/4/1/2/1/4911-stranded-branch-preservation/spec.md`

**Input**: Numeric specification from `/specs/numbered/0/0/1/2/4/1/2/1/4911-stranded-branch-preservation/spec.md`.

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Place research, data model, quickstart, contracts, and checklists under `design/`. The feature root holds five children.

## Summary

Issue 4911 names 505 branches with commits above `main` and no pull request that holds the tip. The plan gives each named branch one lightweight tag at its tip. `AGENTS.md` accepts a pushed tag as a preservation proof. The plan also corrects the branch cleanup section of the contribution guide, adds one changelog fragment, and records the work. The plan deletes no branch. The plan opens no pull request for a named branch.

## Technical Context

**Language/Version**: Not applicable. The change adds no code.

**Primary Dependencies**: `git`, the GitHub CLI (`gh`), and the `ste-linter` command and `pytest` from the development tools pinned in `requirements-dev.txt`.

**Storage**: Git refs on origin under `refs/tags/preserve/`, and the Markdown files in the file change map.

**Testing**: The Tests and STE rows of the Local gates table in `.github/copilot-instructions.md`, and the ref checks in `design/quickstart.md`.

**Target Platform**: Windows 11 with PowerShell. The same `git` and `gh` commands run on macOS and Linux.

**Project Type**: Repository process change with one documentation edit.

**Performance Goals**: 505 tag refs in 11 pushes. The pilot pushes 5 refs. The other pushes hold at most 50 refs each.

**Constraints**: No branch deletion. No pull request for a named branch. No change to a pinned tool or workflow.

**Scale/Scope**: 505 named branches. The named branches hold 1,616 commits above `main` in total. The repository holds 2,396 pull request records.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Rule | Result | Reason |
| - | - | - |
| I. Five-Item Rule | Pass | The record adds one new route under `specs/numbered/`. Each new directory holds at most five children. The feature root holds five children. The folder debt of `changelog.d` and `specs` is recorded below and tracked by FR-017. |
| II. Class-Based Architecture | Not applicable | The change adds no code. |
| III. Safety-First | Pass | The procedure deletes no branch. Its rollback removes only the preservation tags that the procedure pushed. |
| IV. Full Deployment Pipeline | Pass | The record pull request runs the local gates, CI, squash merge, and the main build check. The procedure creates refs only. |
| V. Observability and Logging | Pass | Each batch writes one ledger row for each named branch and one count line. The output uses ASCII only. |
| VI. Inline Comments | Not applicable | The change adds no code. |
| VII. Action Logging | Not applicable | The change adds no code. The procedure logs each action in the ledger. |
| Technology: Python and mistapi | Not applicable | The procedure makes no Mist API call. |
| Technology: Podman | Not applicable | The procedure starts no container. |
| Technology: Data directory | Not applicable | The procedure writes no product output. |
| Technology: Zscaler | Not applicable | The procedure pushes no container image. |
| Documentation | Pass | The contribution guide and the changelog fragment change in the same pull request. |
| Multi-agent Git workflow | Pass | Issue 4911 stays open. The branch is `chore/4911-stranded-branch-preservation` from `main`. The pull request uses a squash merge. |
| SpecKit escalation | Pass | The spec exists because the change alters a process rule and touches three or more files. |

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/4/1/2/1/4911-stranded-branch-preservation/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      preservation-tags.md
    checklists/
      requirements.md
      preservation.md
```

### Source Code (repository root)

Not applicable. The change edits no source file.

## File Change Map

| Path | Action | Reason |
| - | - | - |
| `specs/numbered/0/0/1/2/4/1/2/1/4911-stranded-branch-preservation/spec.md` | Add | The feature specification. It holds FR-001 to FR-017. |
| `specs/numbered/0/0/1/2/4/1/2/1/4911-stranded-branch-preservation/plan.md` | Add | This plan. |
| `specs/numbered/0/0/1/2/4/1/2/1/4911-stranded-branch-preservation/tasks.md` | Add | The ordered tasks T001 to T015 and the final tasks. |
| `specs/numbered/0/0/1/2/4/1/2/1/4911-stranded-branch-preservation/analysis.md` | Add | The consistency review, the defects, and the unresolved items. |
| `specs/numbered/0/0/1/2/4/1/2/1/4911-stranded-branch-preservation/design/research.md` | Add | The decisions, the remote checks, the sources, and the Unverified list. |
| `specs/numbered/0/0/1/2/4/1/2/1/4911-stranded-branch-preservation/design/data-model.md` | Add | The entities, the natural keys, and the state transitions. |
| `specs/numbered/0/0/1/2/4/1/2/1/4911-stranded-branch-preservation/design/quickstart.md` | Add | The commands for each step of the procedure. |
| `specs/numbered/0/0/1/2/4/1/2/1/4911-stranded-branch-preservation/design/contracts/preservation-tags.md` | Add | The tag name and ledger contract. |
| `specs/numbered/0/0/1/2/4/1/2/1/4911-stranded-branch-preservation/design/checklists/requirements.md` | Add | The specification quality checklist. |
| `specs/numbered/0/0/1/2/4/1/2/1/4911-stranded-branch-preservation/design/checklists/preservation.md` | Add | The operator checklist for the procedure. |
| `documentation/contributing.md` | Modify | The Branch cleanup section names the preservation tag. Lines 52 to 79 change. |
| `changelog.d/issue-4911-stranded-branch-preservation.md` | Add | One changelog fragment (FR-013). |
| `documentation/stranded-branch-review.md` | No change | It is a historical review of issue 1980. |
| `.github/workflows/stranded-branch-report.yml` | No change | The reusable workflow pin stays at `79a5e45970e876f1656d69520d9635cea1aa25ef` (FR-016). |
| `requirements-dev.txt` | No change | The tool pin stays at `2239e7bd468fd27e40c43f2b87fcd35a2e49672b` (FR-016). |

The procedure also creates 505 lightweight tags on origin under `refs/tags/preserve/`. The procedure changes no branch.

## Dependencies

- `git` on the path, with push access to origin.
- The GitHub CLI, signed in to `jmorrison-juniper/MistHelper`.
- The `ste-linter` command and `pytest`, from the development tools pinned at `2239e7bd468fd27e40c43f2b87fcd35a2e49672b`.

## Folder Debt

The constitution requires a record of existing folder debt for each process folder that receives a new child.

- `changelog.d` holds 335 children before this change. The change adds one child. The debt is tracked by T015 and FR-017.
- `specs` holds 813 direct children before this change. Of those children, 525 are legacy folders that start with three digits. The change adds no direct child to `specs`. The record sits under `specs/numbered/`. The debt is tracked by T015 and FR-017.
- The route parent folders `0/0/1/2/4/1/2` do not exist before this change. Each new parent holds one child.

## Architecture

The procedure runs in this order.

```text
Report rows of issue 4911
  -> Read tips from GitHub
  -> Classify each tip as held or not held by a PR head commit
  -> Pilot: push 5 preservation tags
  -> Check that no workflow run starts
  -> Batches: push up to 50 preservation tags each
  -> Verify each batch with git ls-remote
  -> Write the ledger to the tracking issue
```

The record pull request changes the guide, one changelog fragment, and the record files. It does not change CI or the report tool.

## Risks and Mitigations

| Risk | Effect | Mitigation |
| - | - | - |
| A tag push starts a workflow run. | Extra CI runs and extra load. | The pilot checks for runs (T006). The rollback removes the pilot tags. |
| A batch push fails for some refs. | A partial batch. | Batches hold at most 50 refs. The procedure retries and stops at the first failure. |
| A wrong tip receives a tag. | The tag keeps the wrong commit. | The tips are read in the same session as the push (FR-005). The ledger compares each tag with the tip. |
| A tag with the same name exists. | An overwrite could move a tag. | Step 4 of the quickstart finds existing tags. The procedure never overwrites a tag. |
| The report keeps naming the rows. | The tracking issue stays open. | T013 files the upstream request. T012 keeps one tracking issue. |
| Maintainers read the tags as releases. | Confusion during a release. | The prefix `preserve/` separates the tags from the version tags. The guide names the prefix (FR-010). |
| A later cleanup deletes a branch without a gate. | The branch name disappears. | T014 gates deletion on the verified tags (FR-012). |
| GitHub tag filter behavior is unverified. | A tag push might start a workflow. | The pilot verifies the behavior before the batches (T006). |

## Rollback

1. Stop the batches when a check fails.
2. Remove only the preservation tags that the procedure pushed. Step 13 of the quickstart names the command.
3. Revert the guide and the fragment through a pull request.
4. Record the rollback in the tracking issue with the ledger.

**Caution:** The rollback command deletes tags only. The named branches stay on origin.

## Complexity Tracking

No constitution violation requires a justification.
