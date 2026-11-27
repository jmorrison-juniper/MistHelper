# Analysis: Pin the verified auto-merge commit

## Scope of Review

No local gate ran. This review covers `spec.md`, `plan.md`, and `tasks.md`. It also covers the failed run 45064239338 and pull request 4886. It covers the guard file and the auto-merge workflow on main. It covers the reusable workflow at two commits and the precedent commit 11569e461.

## Issue and Linked Work Facts

- Issue 4906 is open. Its title is "CI: quality-gate `pytest` failed (PR #4886)". Its labels are `bug`, `ci`, and `quality-gate`. It has no comments. Its author is the GitHub Actions app, and it was created at 2026-11-22T20:27:47Z.
- Its body names the gate `pytest`, pull request 4886, the Dependabot branch, the commit `725fe5e79eb01eee742f5da0794bd53461be60a2`, and run 45064239338. It names no other requirement.
- Run 45064239338 of the Quality Gates workflow has conclusion failure. Its head commit is `9e70001433bae97055b6bbe2825a345c0674273e`. Two jobs fail, and every other job succeeds.
- The failed jobs are `pytest coverage shard (root-and-contracts)` (step 9, "Run tests with coverage") and `pytest (coverage gate)` (step 6, "Verify coverage shards").
- The error text is `FAILED tests/guardrails/test_auto_merge_issue_close.py::TestAutoMergeJob::test_merge_recovery_uses_the_verified_shared_commit - AssertionError`. The expected value is `jmorrison-juniper/misthelper-devtools/.github/workflows/reusable-auto-merge.yml@d63a120487cecf750184cb178387cdc25c0a7635`. The actual value is `jmorrison-juniper/misthelper-devtools/.github/workflows/reusable-auto-merge.yml@2239e7bd468fd27e40c43f2b87fcd35a2e49672b`.
- Pull request 4886 is open. Its base is main, and its head is `9e70001433bae97055b6bbe2825a345c0674273e`. It is not merged. It changes one file, `.github/workflows/auto-merge.yml`, with one addition and one deletion.
- At spec time, the checks of pull request 4886 show 2 failed, 23 skipped, and 36 passed.
- Commit `725fe5e79eb01eee742f5da0794bd53461be60a2` is a merge commit. Its parents are `00d9a16e998b0cb5e10b6ed77da0fa909670d64f` and `9e70001433bae97055b6bbe2825a345c0674273e`.
- A search of pull requests for the term 4906 returns no pull request. The linked pull request is 4886 only.

## Consistency: Requirements, Tasks, and Tests

| Requirement | Tasks | Tests that check it |
| - | - | - |
| FR-001 The job calls the reusable workflow at the verified commit | T001, T002, T004, T-REMOTE-CI, T-MERGE | TP-06 `test_the_job_calls_the_shared_workflow`, TP-07 `test_merge_recovery_uses_the_verified_shared_commit` |
| FR-002 The verified commit names the reviewed commit | T003, T004, T-MERGE | TP-07 `test_merge_recovery_uses_the_verified_shared_commit` |
| FR-003 Pin and verified commit are full SHAs | T002, T003 | TP-06 `test_the_job_calls_the_shared_workflow` (full-SHA pattern) |
| FR-004 The guard fails on a mismatch and reads a literal value | T001, T003, T-REMOTE-CI | TP-07 `test_merge_recovery_uses_the_verified_shared_commit` (failed run 45064239338 shows the failure) |
| FR-005 Changed files pass the local gates | T004, T-LOCAL-GATES | TP-01 to TP-17, all tests in the guard file |
| FR-006 No changelog fragment, reason in the pull request body | T-LOCAL-GATES, T-PR | TP-20 `test_feature_branch_that_edits_no_changelog_passes` |
| FR-007 Record under the route, five children or fewer | T005 | TP-18 `test_specs_structure_matches_baseline`, TP-19 `test_numeric_feature_route_remains_stable` |

Each requirement has at least one task and at least one test. Each task names exact paths and one verification command.

## Consistency With Remote Code

- Main names `d63a120487cecf750184cb178387cdc25c0a7635` at the pin (row R-02) and at the verified commit (row R-03). The guard passes on main by construction.
- The pull request head names `2239e7bd468fd27e40c43f2b87fcd35a2e49672b` at the pin (row R-01). The guard file still names the old commit on that head. The failed run confirms the mismatch.
- The reusable workflow blob is `08870fcd7ab89dc5f9c5abe61f5d407d3721bfb8` at both commits (rows R-14 and R-15).
- The compare between the two commits lists three commits and fifteen files. None of the files is the reusable workflow (row R-16).
- The precedent commit 11569e461 changed the pin and the constant together. Both lines match main today (rows R-36 and R-37).
- The local files cited with line numbers have the same blob SHA as main (`git hash-object` compared with the GitHub tree).

## Defects in Existing Work

- A-1 (blocks the merge). The Dependabot update changes the pin only. The guard keeps the old constant, so the pytest gate fails. Resolution: T002 and T003 change both values in one commit.
- A-2 (record accuracy). The issue body names commit `725fe5e79eb01eee742f5da0794bd53461be60a2`. That commit is a merge commit with parents `00d9a16e998b0cb5e10b6ed77da0fa909670d64f` and `9e70001433bae97055b6bbe2825a345c0674273e`. The head of the pull request is `9e70001433bae97055b6bbe2825a345c0674273e`. Resolution: this record uses the head commit. It names both values.
- A-3 (traceability). The guard file comment at line 143 states that shared commit tests confirmed merge outcomes. The repository holds no evidence for that statement. Resolution: T003 adds the blob evidence beside the constant. The upstream test contents remain unread (U-1 in `design/research.md`).
- A-4 (guard limit). The guard checks equality only. It cannot detect a harmful upstream commit. Resolution: the blob check stays a manual review step. It is part of the security checklist and of T-MERGE.
- A-5 (outdated base). Pull request 4886 merges from base `00d9a16`. Main now names `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. Resolution: the replacement branch starts from current main (decision D-3).
- A-6 (process gap). A Dependabot update changes the pin without the constant. Each such update fails the guard until a person edits the constant. Resolution: the guard comment states the rule. An automated fix is open item U-2.
- A-7 (style). Line 46 of the guard file has no inline comment. `AGENTS.md` line 99 requires one for each executable line of generated code. Resolution: T003 adds the inline comment.

## Unresolved Items

- U-2. Automation for Dependabot updates that require a constant change is not in place. A separate issue should track it, because each concern needs its own issue.
- U-3 The `specs/` root holds 795 direct entries on main. Of these, 792 are grandfathered legacy entries. This change adds none, but the debt remains. The local working tree shows a different count, so this record uses the count from main. A separate remediation issue should track it.
- U-4. Whether Dependabot reopens pull request 4886 after the replacement merges. The answer depends on a future Dependabot event. The closing comment in T-MERGE states the replacement, so a reviewer can close the reopened update.

Evidence limits are listed as U-1 and U-5 to U-9 in `design/research.md`.

## Gate Results at Spec Time

No local gate ran at spec time. The implementation session runs each command in `design/quickstart.md`. Each command must report its expected result before T-PR starts.
