# Specification Analysis Report: Tracked Dependency Lock File

**Date**: 2026-11-26

**Scope**: `spec.md`, `plan.md`, `tasks.md`, the design files, the constitution, and the remote code on `main` at commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`.

**Method**: A read-only review. Each remote claim cites a check ID (RC) in `design/research.md`. No test, build, package install, or container ran.

## Findings

| ID | Category | Severity | Location | Summary | Resolution |
|---|---|---|---|---|---|
| A-01 | Inconsistency | HIGH | Legacy `spec.md`, `plan.md`, `tasks.md`, and `design/lock-comparison.md` | The legacy record holds stale claims. The ignore rule is gone (RC-08). The lock has no exclude-newer option (RC-07). The legacy spec states 37 range entries (RC-60) and 16 missing declarations (RC-61). | Replaced by this record (T001, D-9). Research R5 lists each legacy task. |
| A-02 | Defect | HIGH | `.dockerignore` lines 120 and 121 | The build context excludes `uv.lock` (RC-09). The planned `COPY` step would fail. | T016 adds `!uv.lock` after line 121. Case c9 tests it. |
| A-03 | Defect | HIGH | Open pull request #4888 | A Dependabot pip update edits `requirements-dev.txt`, and its lock and export checks fail (RC-59). The pip ecosystem edits exports directly. | T023 moves Dependabot to `uv`. Case c17 names the regeneration command. Follow-up F-1 automates regeneration. |
| A-04 | Inconsistency | MEDIUM | `pyproject.toml` line 101, `requirements-dev.txt` line 470, `.github/workflows/container-build.yml` line 92, and `scripts/bootstrap_worktree.py` lines 449 to 460 | The uv version 0.13.9 appears in the declarations (RC-14), in the dev export (RC-19), and in the container build step (line 92). The bootstrap installs uv without a pin (RC-29). | T010 to T012 add one range and one guard. |
| A-05 | Documentation defect | MEDIUM | `documentation/development-setup.md` lines 28 and 29 | The text says the bootstrap installs the two requirements files (RC-43). The bootstrap runs `uv sync --locked --extra dev` (RC-30). | T022. |
| A-06 | Documentation defect | MEDIUM | `documentation/container-deployment.md` lines 291 and 292 | The trigger list omits `uv.lock` and `pyproject.toml` (RC-44). The workflow trigger includes both (RC-25 and the trigger lines 6 to 16 of `container-build.yml`). | T022. |
| A-07 | Documentation defect | LOW | `.github/copilot-instructions.md` line 21 | The text states mistapi `>=0.64.0,<0.65` (RC-42). `pyproject.toml` line 29 states `>=0.64.1,<0.65` (RC-11). | T022. The brief repeats the 0.64.0 text (A-12). |
| A-08 | Coverage gap | MEDIUM | `tests/guardrails/test_dependency_lock_file.py` | No guard checks that `.gitignore` keeps `uv.lock` tracked (RC-41). | T009, case c1. |
| A-09 | Constitution, Principle I | MEDIUM | `mist-ops-platform/` | The folder holds 11 children (RC-52). The new `uv.lock` adds one. | Complexity Tracking in `plan.md`. Follow-up F-2. Owner review is requested at T-PR. |
| A-10 | Constitution, Principle I | LOW | `.github/` | The folder holds 14 children (RC-51). A composite action would add one more. | Decision D-3 rejects the composite action. |
| A-11 | Overlap | MEDIUM | `mist-ops-platform/requirements.txt` | Open Dependabot pull requests #4889 and #4890 change this file (R2). T020 changes it too. | T020 waits until both pull requests merge or close. |
| A-12 | Brief conflict | LOW | Brief sections 0 and 2 | The brief states `mistapi>=0.64.0,<0.65`. `main` declares `>=0.64.1,<0.65` (RC-11). | `main` wins. T022 aligns the instruction file. |
| A-13 | Brief conflict | MEDIUM | Brief section 4, T-PR rule | The brief requires `Closes #3400` in the pull request body. The issue must stay open until slices 2 to 5 pass (R1). | Decision D-10 uses `Refs #3400` for this record. The final slice uses `Closes #3400`. The orchestrator must accept this deviation. |
| A-14 | Process | HIGH | Issue #3400 comments of 2026-11-17 | The owner holds the next container slice until a separate user approval and a serial-slot assignment. Pull request #4851 merged on 2026-11-19. No comment records the end of the hold (U-G). | Slices 2 to 5 need user approval before publication. The orchestrator confirms the approval before each push. |
| A-15 | Local state | LOW | Working tree (research R6) | Six working-tree files differ from their committed blobs in line endings only (CRLF). Git reports them as unchanged. A read-only status check lists five unrelated files. | Each slice starts from `main`. Stage named files only. |
| A-16 | Path drift | LOW | Bootstrap tests (RC-55) | Pull request #4505 names `tests/unit/bootstrap/test_uv_locked_sync.py`. The file sits at a moved path on `main`. | This record cites the `main` path. |
| A-17 | Hash gap | MEDIUM | Exports (RC-16) and lock (RC-06) | The exports carry no hashes. The lock stores sha256 values. pip installs from exports do not check artifact hashes (U-J). | D-4 moves images to the lock. Follow-up F-4 covers the exports. |
| A-18 | Mutable base | MEDIUM | `Dockerfile` line 22 (RC-33) | The base tag `python:3.15-slim` is mutable. | D-8. Follow-up F-3. |
| A-19 | Legacy artifact | LOW | Legacy task T008 (R5) | The git-ignored freeze file is absent from this checkout and from `main`. | Recorded as absent in `existing_record`. Unverified item U-H. |
| A-20 | Ops export | MEDIUM | `mist-ops-platform/requirements.txt` line 2 (RC-39) | The header names one Windows interpreter. The file does not prove the Linux set. | T020 replaces it with an export of the ops lock. Unverified item U-I. |
| A-21 | Stale issue body | LOW | Issue #3400 body (R1) | Four body facts are stale. | Research R1 lists them. This record uses `main` facts only. |

## Process notes

| ID | Item | Detail | Effect |
|---|---|---|---|
| P-1 | Repository check during research | One research command created an empty folder under the repository root, then removed it. A later check found the folder absent. Git reported no path for it. | The folder is absent now, and git reports no trace of it. Recorded for the orchestrator. |

## Coverage: requirements, tasks, and tests

| Requirement | Tasks | Test cases or existing guard | Coverage |
|---|---|---|---|
| FR-001 | T002 | `test_pyproject_declares_each_requirement` (RC-53) | Existing guard |
| FR-002 | T003 | `test_lock_is_current_with_pyproject` (RC-58) | Existing guard |
| FR-003 | T009 | Case c1 | Planned case |
| FR-004 | T004 | `test_requirements_exports_match_the_lock` (RC-54) | Existing guard |
| FR-005 | T005 | `test_existing_uv_runs_one_locked_sync` (RC-55) | Existing guard |
| FR-006 | T006 | `test_live_job_blocks_on_lock_and_export_drift` (RC-56) | Existing guard |
| FR-007 | T013, T014 | Case c5 | Planned case |
| FR-008 | T008, T013 | Case c6 | Planned case |
| FR-009 | T007 | `test_container_build_uses_the_locked_test_environment` (RC-57) | Existing guard |
| FR-010 | T015, T016 | Cases c7 and c8 | Planned cases |
| FR-011 | T015, T016 | Cases c7, c8, and c9 | Planned cases |
| FR-012 | T017 | Case c10 | Planned case |
| FR-013 | T023 | Cases c16 and c17 | Planned cases |
| FR-014 | T018, T019, T020 | Cases c11, c12, and c13 | Planned cases |
| FR-015 | T010, T011, T012 | Cases c2, c3, and c4 | Planned cases |
| FR-016 | T021, T022 | Cases c14 and c15 | Planned cases |
| FR-017 | T002, T022 | Floor test (RC-53) and case c15 | Existing guard and planned case |

Totals: 17 requirements, 27 tasks, and 17 planned test cases (c1 to c17).

## Unresolved items

- O-1: User approval for slices 2 to 5 (A-14, U-G).
- F-1: Automate export regeneration after Dependabot lock updates (D-7, A-03).
- F-2: Restructure `mist-ops-platform/` into a compliant folder layout (D-5, A-09).
- F-3: Pin the base image digest and the apt inputs (D-8, A-18).
- F-4: Provide hash-checked exports (A-17).

## Deviations from the brief and the legacy plan

- A-12: The brief states `mistapi>=0.64.0,<0.65`. `main` states `>=0.64.1,<0.65`. `main` wins.
- A-13: The brief requires `Closes #3400` in the T-PR body. This record uses `Refs #3400` (D-10).
- The legacy plan proposed `pip-audit --locked .`. D-2 keeps the runtime export audit.
- The legacy plan switched every CI install to `uv sync --locked`. D-3 keeps the existing `python -m` commands and adds a `GITHUB_PATH` step.
- The legacy plan proposed a lock refresh workflow for Dependabot. Follow-up F-1 tracks it.

## Defects in existing work

- Legacy record: A-01.
- Root `.dockerignore`: A-02.
- Open Dependabot pull request #4888: A-03.
- Documentation lines: A-05, A-06, and A-07.
- Guard gap for `.gitignore`: A-08.
- Issue body facts: A-21.

## Consistency review

- `spec.md` and `plan.md`: the requirement IDs and the slice list match.
- `plan.md` and `tasks.md`: each slice names the same tasks, and the change map names the same files.
- `tasks.md` and `design/research.md`: each task status matches the remote check that it cites.
- `design/contracts/lock-install-contract.md` and `tasks.md`: each contract row names a task.
- `analysis.md`, `design/research.md`, and `STATUS.json`: the same remote check count (64), decision count (10), and task count (27) appear.

## Unverified items

The unverified items are U-A to U-N in `design/research.md`, section R8. No task depends on an unverified item as a fact. Each unverified item names its verifying task, or it states that no task verifies it.
