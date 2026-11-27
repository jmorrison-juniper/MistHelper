# Analysis: Main workflow recovery

## Findings

- **F-1**: The legacy specification says `Status: Local implementation` (RC-16). The consumer change is on `main` (RC-47). This record replaces that statement.
- **F-2**: The legacy tasks keep T005 open (RC-19). Eight immediate-path merges now log confirmed merges (RC-56 to RC-63). The delayed path is still open. Task T011 separates the two paths.
- **F-3**: The legacy plan says a guard class exceeds the five-member limit (RC-13). The largest class holds five test functions, so the class statement is stale. The module holds 18 top-level names (RC-12), so the module is above the limit. This record states the module fact.
- **F-4**: The legacy tasks lack requirement IDs, verification commands, and status values. This record adds each field to every task.
- **F-5**: `wiki-publish.yml` also starts on a push to `main` for wiki paths (RC-40). The list omits it by design (D-4), so the comment is imprecise (U-3). The comment at `auto-merge.yml` lines 63-64 says the list names "The workflows that a push to main starts."
- **F-6**: Open pull request #4886 moves the pin to `2239e7bd468fd27e40c43f2b87fcd35a2e49672b` (RC-70). Its Quality Gates run fails the guard assertion at line 145 (RC-71). The shared reusable workflow blob is identical at both commits (RC-35). A pin bump needs a guard change in the same pull request (D-8).
- **F-7**: No scheduled run in the surveyed window logged a start (RC-67). Run 45786075135 logged coverage for all four workflows (RC-65). FR-006 has coverage evidence but no dispatch-on-miss evidence.
- **F-8**: Issues #4769 and #4770 closed about 10.5 hours after the token merge of PR #4772 (RC-69). The linked-issue sweep works on its schedule. The delay is latency, not a failure.
- **F-9**: Three merge commits show a `workflow_dispatch` run named `Close linked issues on merge` (RC-92). The main-workflow list does not name that workflow. Its source remains unknown (U-4).

## Coverage Summary

| Requirement | Tasks | Tests or checks |
| - | - | - |
| FR-001 | T001, T005 | `test_merge_recovery_uses_the_verified_shared_commit` (line 141) and `test_the_job_calls_the_shared_workflow` (line 135) |
| FR-002 | T002, T005 | `test_each_main_workflow_accepts_a_dispatch` (lines 153 to 166) |
| FR-003 | T003 | `TestAutoMergeWorkflowTriggers` (five functions, lines 87 to 129), `test_the_job_grants_each_scope_of_the_shared_jobs` (line 147), and `TestCloseLinkedIssuesJob` (four functions, lines 169 to 209) |
| FR-004 | T004, T008, T011 | `test_the_schedule_backstop_survives` (line 115), and queries H-02 and H-03 |
| FR-005 | T004, T011 | `test_close_job_accepts_only_a_real_pull_request_merge` (line 187), and query H-01 |
| FR-006 | T004, T009 | Query H-04 and the upstream tip check (RC-31) |
| FR-007 | T005 | `test_merge_recovery_uses_the_verified_shared_commit` and `test_each_main_workflow_accepts_a_dispatch` |
| FR-008 | T005, T-REMOTE-CI | `test_each_main_workflow_accepts_a_dispatch` (lines 162 to 166) |
| FR-009 | T007, T011 | Query H-05 (evidence filter) and acceptance item AC-06 |
| FR-010 | T012 | Acceptance items AC-03 to AC-05 |
| FR-011 | T010, T-MERGE | Query H-06 (run 43800244711) |
| FR-012 | T013 | `test_each_main_workflow_accepts_a_dispatch` (exact set, lines 159 to 160) |

| Success criterion | Tasks | Tests or checks |
| - | - | - |
| SC-001 | T007 | Query H-03 on RC-56 to RC-63 |
| SC-002 | T008 | Query H-02 on RC-49 |
| SC-003 | T011 | Query H-01 and quickstart section 4 |
| SC-004 | T-LOCAL-GATES | Three pytest commands |
| SC-005 | T012 | Acceptance item AC-05 |

Each requirement maps to at least one task and at least one test or check.

## Constitution Alignment

No rule fails. The plan lists each rule with its reason. The recorded debt is RC-12. This change adds no new debt.

## Unmapped Tasks

None. Each task maps to at least one requirement or success criterion.

## Exceptions

- **E-1**: Each claim in this record cites a remote check identifier from `design/research.md`. A claim without an identifier does not appear in this record.
- **E-2**: Hosted tasks use the queries in `design/quickstart.md`, section 3. The local gates table has no hosted gate.

## Metrics

- Requirements: 12 functional requirements and 5 success criteria.
- Tasks: 17. Thirteen numbered tasks and four final tasks.
- Test functions gating the record: 49. Seventeen are in `test_auto_merge_issue_close.py`, 23 are in `test_spec_route_contract.py`, and 9 are in `test_process_folder_structure.py`.
- Remote checks: 95 (`design/research.md` and `STATUS.json`).
- Legacy claims: 16 (12 verified, 4 stale, 0 absent).
- Immediate-path merges logged: 8. Delayed-path merges logged: 0. Scheduled starts logged: 0.

## Unresolved Items

- **U-1**: The delayed-path evidence (T011). Open.
- **U-2**: Whether a closed run starts after a delayed merge (A-3).
- **U-3**: The comment at `auto-merge.yml` lines 63-64 (F-5). A manual merge changes it.
- **U-4**: The source of the `Close linked issues on merge` runs (F-9, RC-92).
- **U-5**: Whether the `auto-merge` label counts as approval for acceptance (D-5).
- **U-6**: Scheduled dispatch-on-miss evidence (F-7).
- **U-7**: Pull request #4886 and the pin bump (F-6, D-8).

## Convergence After Implementation

The issue can close when T011 and T012 are complete. A later refresh updates RC-67 and RC-68 and the counts in the STATUS file.

## Defects in the Consumer Change

None found. The pin, the list, the guard test, and the release-note fragment match the reviewed shared revision and four workflows (RC-01, RC-02, RC-08 to RC-10, RC-14).

Caution: A premature closing keyword closes the issue at merge time. Reopen the issue by hand if that happens.
