# Implementation Plan: Preserve Repository Versions and Update the Local Main Checkout

**Branch**: `chore/4277-preserve-repository-versions` | **Date**: 2026-11-26 | **Spec**: `specs\numbered\0\0\1\1\4\1\0\2\4277-preserve-repository-versions\spec.md`

**Input**: Numeric specification from `specs\numbered\0\0\1\1\4\1\0\2\4277-preserve-repository-versions\spec.md`. The route digits are the base-5 digits of issue 4277 (research R-30, R-31).

## Summary

Issue 4277 asks for a verified preservation record. The owner already preserved the repository state and moved the primary checkout to GitHub main. This plan finishes the remaining evidence. It records each branch disposition, validates a clean baseline, and lists each unresolved recovery item. The plan changes no product code. It deletes nothing and publishes no private work.

## Technical Context

**Language/Version**: Python 3.15 is the repository runtime (copilot-instructions line 18 section). This record adds Markdown only. PowerShell and Git 2.49.0 run the checks (research L-09).

**Primary Dependencies**: Git for read-only commands and the baseline worktree. GitHub CLI `gh` for read-only API calls, the pull request, and the CI watch. The repository virtual environment for the baseline gates (research R-43).

**Storage**: The primary Git object store. The owner backup, which sits outside the repository. The git-ignored folder `test-artifacts\4277\` (research R-41).

**Testing**: The local gates in `.github\copilot-instructions.md` lines 50-65 and line 74 (research R-18, R-19). The guard test `tests\guardrails\test_process_folder_structure.py` (research R-45).

**Target Platform**: A Windows 11 host with a OneDrive-backed checkout (research R-38).

**Project Type**: A Spec Kit numbered record. No product code.

**Performance Goals**: Each pytest-chunks shard stays within its timeouts. The chunk timeout is 900 seconds and the test timeout is 120 seconds (copilot-instructions line 62 row).

**Constraints**: The authoring phase cannot write to the repository. Deletion is forbidden (FR-008). Publication of private work is forbidden (research D-4). The primary checkout must not change HEAD during the work.

**Scale/Scope**: 330 local heads. 599 remote-tracking refs. 190 tags. One stash. Six preserved refs. 33 worktree admin entries. Five modified entries. All counts were measured on 2026-11-26 (research L-04, L-05, L-07, L-08).

## Constitution Check

*GATE: Passed before the research phase. Rechecked after the design phase.*

| Rule | Result | Reason |
| - | - | - |
| I. Five-item rule (constitution line 38) | Pass | The feature root holds five children: `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, and `design\`. The `design\` folder holds five children. The route adds one child to `specs\numbered\0\0\1\1\4\1`, which then holds two. It creates single-child folders at `0` and `2`. |
| I. Existing process-folder debt (constitution lines 46-48) | Pass with recorded debt | `specs\` holds 813 direct children (research L-11). This record adds no direct child to `specs\`. Remediation action RA-1 moves the direct children into managed roots in a separate issue. The owner files that issue. This record creates no issue. |
| I. Full level `0\0\1\1` (research L-11) | Pass | The level already holds five children. The route uses its existing child `4`, so this record adds no child there. |
| I. Route digits (constitution line 57, spec-route.ps1 line 17) | Pass | The route digits are `0 0 1 1 4 1 0 2`, the base-5 digits of 4277 padded to eight places (research R-30, R-31). |
| II. Class-based architecture (constitution line 91) | Pass | No code is written. No class or wrapper is added. |
| III. Safety first (constitution line 113) | Pass | The plan contains no destructive operation. Deletion is forbidden by FR-008. Typed confirmation does not apply to read-only steps or record writes. |
| IV. Full deployment pipeline (constitution line 143) | Pass | The steps run through T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE. Steps 10 to 12 do not run, because `container-build.yml` runs only for a product-file push (research R-22, D-11). |
| IV. No standalone Git operations (constitution line 175) | Pass with a note | The owner ran standalone preservation steps on 2026-10-17 (research D-12). This plan adds no standalone operation to the primary checkout. Analysis item A-004 keeps the policy conflict with the owner. |
| V. Observability and logging (constitution line 182) | Pass | The record uses ASCII text only. No runtime log is added. |
| VI. Inline comments (constitution line 204) | Pass | No code is written. |
| VII. Action logging (constitution line 235) | Pass | No code is written. |
| Technology: mistapi (constitution lines 274-336) | Pass | No Mist REST request occurs. The installed SDK is 0.64.1 and meets the pin (research R-49). |
| Technology: containers and test containers | Pass | No container starts. |
| Technology: file paths | Pass | No code path is built. |
| Technology: data directory | Pass | No product output is written. Evidence goes to `test-artifacts\4277\`, which Git ignores (research R-41). |
| Development workflow: testing (constitution line 361) | Pass | Tasks T009 to T012 and T-LOCAL-GATES run the applicable gates. |
| Development workflow: security findings (constitution line 373) | Pass | The plan suppresses no finding. |
| Documentation (constitution line 398) | Pass | No menu operation or behavior changes. README needs no update. |
| Release notes (constitution line 409) | Pass with a decision | `changelog.d\README.md` rule 4 applies to internal-only changes (research R-39, D-8). Analysis item A-003 records the wording conflict. |
| Audience standard (constitution line 414) | Pass | The record uses plain words and short sentences. |
| Complexity-driven escalation (constitution line 420) | Pass | The change touches a multi-file record and a destructive-risk area. This specification is the required record. |
| Multi-agent Git: branch name (constitution line 476) | Pass | The branch is `chore/4277-preserve-repository-versions`, created from `main`. |
| Multi-agent Git: required labels (constitution line 487) | Pass with a decision | The labels are type `chore`, scope `docs`, and status `in-progress`. Scope `docs` replaces `tools` (research D-9). |
| Multi-agent Git: file overlap (AGENTS.md, section Parallel agents and shared state) | Pass | Seven open pull requests exist. None names the route prefix (research L-12). |

## Project Structure

### Documentation (this feature)

```text
specs\numbered\0\0\1\1\4\1\0\2\4277-preserve-repository-versions\
  spec.md
  plan.md
  tasks.md
  analysis.md
  design\
    research.md
    data-model.md
    quickstart.md
    contracts\
      branch-disposition-register.md
      recovery-register.md
      validation-report.md
    checklists\
      requirements.md
      safety.md
```

The feature root holds five children. The `design\` folder holds five children. The `contracts\` folder holds three files, and the `checklists\` folder holds two files. Each count stays within the five-child limit.

### Git-ignored evidence (not committed)

```text
test-artifacts\4277\
  branch-register.tsv
  modified-files.patch
  modified-files.sha256
  preserved-files\
  baseline-logs\
```

Git ignores this folder through the `/test-artifacts/` rule (research R-41). The record cites each file by name. The record does not copy the file contents.

### Source Code (repository root)

No source code changes. The plan changes no file under `src\`, `tests\`, `scripts\`, or `documentation\`.

**Structure Decision**: The numbered route holds the record. The evidence folder stays outside Git history.

## File-by-File Change Map

| Action | Exact repository path | Purpose |
| - | - | - |
| Add | `specs\numbered\0\0\1\1\4\1\0\2\4277-preserve-repository-versions\spec.md` | Requirements, user stories, clarifications, and success criteria |
| Add | `specs\numbered\0\0\1\1\4\1\0\2\4277-preserve-repository-versions\plan.md` | Technical context, constitution check, and this plan |
| Add | `specs\numbered\0\0\1\1\4\1\0\2\4277-preserve-repository-versions\tasks.md` | Ordered tasks and the dependency list |
| Add | `specs\numbered\0\0\1\1\4\1\0\2\4277-preserve-repository-versions\analysis.md` | Consistency review, findings, and the coverage matrix |
| Add | `specs\numbered\0\0\1\1\4\1\0\2\4277-preserve-repository-versions\design\research.md` | Decisions, remote table, local evidence, sources, and unverified claims |
| Add | `specs\numbered\0\0\1\1\4\1\0\2\4277-preserve-repository-versions\design\data-model.md` | Entities, natural keys, and state transitions |
| Add | `specs\numbered\0\0\1\1\4\1\0\2\4277-preserve-repository-versions\design\quickstart.md` | Reproduction steps and verification commands |
| Add | `specs\numbered\0\0\1\1\4\1\0\2\4277-preserve-repository-versions\design\contracts\branch-disposition-register.md` | Register columns and rules |
| Add | `specs\numbered\0\0\1\1\4\1\0\2\4277-preserve-repository-versions\design\contracts\recovery-register.md` | Recovery item columns and rules |
| Add | `specs\numbered\0\0\1\1\4\1\0\2\4277-preserve-repository-versions\design\contracts\validation-report.md` | Validation rows and recorded results |
| Add | `specs\numbered\0\0\1\1\4\1\0\2\4277-preserve-repository-versions\design\checklists\requirements.md` | Specification quality checklist |
| Add | `specs\numbered\0\0\1\1\4\1\0\2\4277-preserve-repository-versions\design\checklists\safety.md` | Preservation safety checklist |
| Modify | none | No existing file changes |
| Delete | none | No file or folder is removed |

## Implementation Outline

1. Phase A collects remote and local evidence. Tasks T001 to T005 run in parallel and read only.
2. Phase B builds the branch register and preserves the modified files. Tasks T006 to T008 run in order.
3. Phase C validates the isolated baseline. Tasks T009 to T012 run in order, then T014 removes the worktree.
4. Phase D closes the record. Task T013 finalizes the recovery register. Task T015 creates the pull request worktree and copies the record.
5. Phase E delivers the change. The tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE run in order.

## Dependencies

| Dependency | Use | Source |
| - | - | - |
| Git 2.49.0 | Read-only commands and the detached baseline worktree | Host installation (research L-09) |
| GitHub CLI `gh` | Read-only API calls, the pull request, and the CI watch | Host installation |
| Repository virtual environment | Compile, lint, format, type, and test gates | `scripts\bootstrap_worktree.py` (research R-43) |
| `ste-linter` and `pytest-chunks` | Writing and test gates | `requirements-dev.txt` through the bootstrap (copilot-instructions line 18 section) |

No dependency manifest changes. No package is added.

## Risks and Mitigations

| Risk | Effect | Mitigation |
| - | - | - |
| Same-disk backup loss | Warning: local-only refs and the owner backup fail together | Record the 24-hour window. Create no new same-disk copy in this record. Owner review is recovery item U-002. |
| Local-only ref published by mistake | Warning: private work appears in a public repository | Push only the record branch. Run no push for any other ref (research D-4). |
| Ref deleted by mistake | Warning: the preservation claim fails, and the ref may not return | Count refs before and after the work (V-08). Run no deletion command. |
| Worktree removal deletes files | Warning: uncommitted files in the baseline are lost | Remove only the detached baseline folder. Check its path first. Use no force flag on the primary checkout. |
| GitHub rate limit | Caution: a remote check fails | Wait 60 seconds and retry up to three times. Record an unverified result after that. |
| Bootstrap fails in OneDrive | Caution: the baseline cannot run its gates | Record the cause. The bootstrap sets copy link mode for uv (development-setup.md, installer settings table). Do not run gates in the primary checkout. |
| Test shard times out | Caution: a gate result is incomplete | Rerun the failed chunk alone. Record both results. |
| Counts drift before the work ends | Register and evidence disagree | Recount at T008. Record the counts from both measurements. |
| Closing keyword closes issue 4277 | Caution: the owner loses the open tracker until the issue reopens | Use `Refs #4277` (research D-2). |
| Privacy commit content lost | Warning: recovery work stays unknown, and the content may not return | Record U-001 with the owner condition. Rebuild nothing (research D-7). |

## Rollback Steps

1. Before the merge, close the pull request without merging it. Keep the branch, because branch deletion is outside this issue scope.
2. After the merge, open a new pull request that reverts the squash commit. Do not force-push `main`.
3. The record needs no other file. No product file depends on it.
4. The owner may delete `test-artifacts\4277\` after the record merges. No repository file depends on it.
5. If `git worktree remove` fails for the baseline, record the cause. Do not delete the admin folder by hand.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| - | - | - |
| `specs\` holds 813 direct children (existing debt) | The numbered route is required for numbered records (constitution line 57) | Writing under `specs\live` is rejected, because a numbered issue uses the numbered route (copilot-instructions line 159). |
| `specs\numbered\0\0\1\1` holds five children (full level) | The route passes through that level, using its existing child `4` | Adding a sibling folder is rejected, because the route digits fix the path. |
