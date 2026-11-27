# Implementation Plan: Laptop Branch Archive Verification

**Branch**: `docs/4868-laptop-branch-archive` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification from `specs/numbered/0/0/1/2/3/4/3/3/4868-laptop-branch-archive/spec.md`.

`spec.md`, `plan.md`, `tasks.md`, and `analysis.md` stay at the feature root. Research, data model, quickstart, the contract, and checklists stay under `design/`.

## Summary

Verify the 497 listed names of issue 4868 on origin with GitHub GET requests. Record each archive tip and each counterpart state. Add Markdown files and one changelog fragment. Change no branch and no GitHub item.

## Technical Context

**Language/Version**: Markdown. The checks use PowerShell and the `gh` CLI, version 2.103.3.

**Primary Dependencies**: `gh` with the configured account for GET requests. `ste-linter` from `misthelper-devtools` for the STE gate. No new dependency.

**Storage**: None. The record is text in the repository.

**Testing**: The checks TC-01 to TC-15 in `design/quickstart.md`, the STE gate, and `python -m pytest tests/guardrails`.

**Target Platform**: Windows 11 checkout. The change contains no platform-specific code.

**Project Type**: A documentation record for a branch archive check.

**Performance Goals**: Three listing requests and one compare request cover all 497 names within the GitHub rate limit.

**Constraints**: Every GitHub request is a GET request. Every local git command is a read. No repository script runs in this work.

**Scale/Scope**: 497 listed names, 598 branch refs on origin, and 11,404 tree entries on main.

## Constitution Check

*Gate: passes before research. Re-checked after design: passes.*

| Principle or rule | Gate | Result and evidence |
| - | - | - |
| I. Five-item rule | Each directory holds five children or fewer. New records use the managed route. | Pass. The route adds one child to `specs/numbered/0/0/1/2/3/4/3` (2 to 3). It adds no child to `specs/numbered/0/0/1/2/3`, which already holds five (RC-26). The feature root and `design` each hold five. |
| II. Class-based architecture | Behavior lives in named classes. | Not applicable. The change adds no code. |
| III. Safety first | No destructive step. No secret in output. | Pass. Every command reads. The token value never prints. Deletion needs a human decision (D-8). |
| IV. Full deployment pipeline | Local gates, commit, pull request, CI, merge. | Pass by plan. T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE run in order. T-MERGE waits for orchestrator authorization. |
| V. Observability and logging | ASCII logs. Structured logs for new services. | Not applicable. The change adds no service and no log. |
| VI. Inline comments | Each executable line carries a comment. | Not applicable. The change adds no executable line. |
| VII. Action logging | Log before and after each action. | Not applicable. The change adds no executable line. |
| Technology: Mist REST | Use a mistapi method for each Mist call. | Not applicable. The issue names no Mist request. |
| Technology: file paths | Use path libraries in code. | Not applicable. The change adds no code. |
| Data directory | Product output goes under `data/`. | Pass. The checks write no file. |
| Test containers | Compose group and naming for test containers. | Not applicable. No container runs. |
| Release notes | One fragment for each change. | Pass. Task T012 adds one fragment (FR-014, RC-10). |
| Development workflow | A specification before a change of three or more files. | Pass. The change touches ten files, and this record is its specification. |

For repository structure and generated files:

- The commit subject and the pull request title use the Conventional Commits form, for example `docs(specs): record laptop branch archive verification`.
- The change adds its own record under `specs/numbered/` and one fragment under `changelog.d/`.
- Existing folder debt is recorded in Complexity Tracking, with remediation task T013.
- Product output stays under `data/`. The change writes no product output.

For a feature that uses Juniper Mist Cloud: Not applicable. The issue names no Mist Cloud request, so no mistapi method applies.

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/3/4/3/3/4868-laptop-branch-archive/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      archive-ref-verification.md
    checklists/
      requirements.md
```

### Source Code

None. The change adds no source file and no test file.

## Route Check

The eight route digits are the base-5 digits of 4868, padded to eight places: 0 0 1 2 3 4 3 3. The reference record `4920` follows the same rule. The route helper was not run, because this work runs no repository script. Each row below reads the remote tree on main.

| Directory | Exists on main | Children now | Children after this change | Basis |
| - | - | - | - | - |
| `specs/numbered/0/0/1/2/3` | Yes | 5 | 5 | RC-26 |
| `specs/numbered/0/0/1/2/3/4` | Yes | 3 | 3 | Child `3` already exists. |
| `specs/numbered/0/0/1/2/3/4/3` | Yes | 2 | 3 | RC-25 |
| `specs/numbered/0/0/1/2/3/4/3/3` | No | 0 | 1 | RC-24. This change creates it. |
| `specs/numbered/0/0/1/2/3/4/3/3/4868-laptop-branch-archive` | No | 0 | 5 | The record folder. |

## Architecture

The verification follows six steps:

1. Read the issue body. Parse the 497 listed names and their claimed unpushed commit counts.
2. Read the archive branch listing and the rescue branch listing on origin.
3. Read the full branch listing on origin. Compare each name with it.
4. Classify each counterpart state. Compare the one same-name branch with its archive tip.
5. Read local refs with read-only git commands. Compare the local tips with the archive tips.
6. Write the record in the draft folder, then in the repository through T-PR.

## File-by-File Change Map

| Path | Action | Purpose |
| - | - | - |
| `specs/numbered/0/0/1/2/3/4/3/3/4868-laptop-branch-archive/spec.md` | Add | Requirements, user stories, and clarifications |
| `specs/numbered/0/0/1/2/3/4/3/3/4868-laptop-branch-archive/plan.md` | Add | This plan |
| `specs/numbered/0/0/1/2/3/4/3/3/4868-laptop-branch-archive/tasks.md` | Add | Ordered tasks with status |
| `specs/numbered/0/0/1/2/3/4/3/3/4868-laptop-branch-archive/analysis.md` | Add | Consistency review and findings |
| `specs/numbered/0/0/1/2/3/4/3/3/4868-laptop-branch-archive/design/research.md` | Add | Decisions, remote verification table, and Unverified list |
| `specs/numbered/0/0/1/2/3/4/3/3/4868-laptop-branch-archive/design/data-model.md` | Add | Entities and the 497-name table |
| `specs/numbered/0/0/1/2/3/4/3/3/4868-laptop-branch-archive/design/quickstart.md` | Add | GET checks and expected results |
| `specs/numbered/0/0/1/2/3/4/3/3/4868-laptop-branch-archive/design/contracts/archive-ref-verification.md` | Add | Request and response shape of the GET checks |
| `specs/numbered/0/0/1/2/3/4/3/3/4868-laptop-branch-archive/design/checklists/requirements.md` | Add | Specification quality checklist |
| `changelog.d/issue-4868-laptop-branch-archive.md` | Add | One release-note fragment |

Modify: none. Delete: none.

## Dependencies

- `gh` CLI, version 2.103.3, with the configured account. The change uses read requests only.
- GitHub REST endpoints `git/matching-refs`, `git/ref`, `git/trees`, `git/blobs`, `commits`, and `compare`, plus `gh pr list` and `gh search` for pull request lookups. All are read requests.
- `ste-linter` from `misthelper-devtools`. The command appears in the quality gates (RC-16). T-LOCAL-GATES runs it.
- `speckit-task-audit` from `misthelper-devtools`. CI runs it as an advisory step (RC-17). T-LOCAL-GATES runs it and reports the result.
- No Python package and no new library.

## Risks and Mitigations

| Risk | Effect | Mitigation |
| - | - | - |
| GitHub rate limit (HTTP 403 or 429) | A listing fails. | Wait 60 seconds and retry up to three times. Then mark the check unverified. |
| Archive refs change after 2026-11-26 | The record goes stale. | Rerun TC-01 to TC-05 before merge and before any cleanup decision (T014). |
| The local checkout differs from the laptop | A local count misleads a reader. | Origin is the truth. Local data is a cross-check only (D-1). |
| A branch changes during the work | The record misstates the state. | Every command reads. SC-005 compares counts before and after. |
| A later change deletes archive refs | Unique commits lose their only remote copy. | Decision D-8 needs a human. The spec gives a Warning for deletion. |
| The route parent fills before merge | The route breaks the five-children rule. | Recheck RC-25 and RC-26 in T-LOCAL-GATES. |
| An unverified claim reads as fact | A reader trusts an unchecked claim. | Keep each unverified claim in the Unverified list (FR-010). |

## Rollback

1. Before merge, close the pull request without merge. Delete the branch `docs/4868-laptop-branch-archive`.
2. After merge, open a new issue. Branch from `main` and revert the squash commit. Do not force push `main`.

This change touches no archive ref and no branch. No branch restore is needed.

## Complexity Tracking

| Violation or debt | Why needed | Simpler alternative rejected because |
| - | - | - |
| `changelog.d/` holds 335 direct children on main (RC-28). The folder is a process folder, and the constitution permits unique records there. | The constitution requires one fragment for each change (RC-10). | Skipping the fragment breaks RC-10. Moving the fragments into subfolders changes the release process. Task T013 tracks that remediation in a separate issue. |
| `specs/numbered/0/0/1/2/3` holds five children (RC-26). | The route for issue 4868 passes through it. | No child is added there. The route reuses the existing child `3` under `2`. |
