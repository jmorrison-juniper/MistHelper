# Specification Analysis Report: Upgrade Portal Journeys Gate on PR 4888

## Findings

| ID | Finding | Evidence | Severity | Action |
| - | - | - | - | - |
| A-1 | PR 4888 raises mando to 0.8.2. Radon 6.0.1 requires mando below 0.8, so pip cannot resolve the file. | R-04, R-05, R-62, R-64, R-66 | High | Decline the bump (D-1, D-2). |
| A-2 | The failure exists only on PR 4888. Main passes the same job. | R-63 | Information | No change on main. |
| A-3 | The issue cites merge commit `5bb4b385`. The job ran on PR head `e86098c`. | R-58, R-59, R-62 | Low | The record names both SHAs (research E-3). |
| A-4 | The upload step fails because the harness never starts. The upload uses `if-no-files-found: error`. | R-22, R-34 | Low | No change. The upload passes when the harness starts. |
| A-5 | Dependabot edited the generated export `requirements-dev.txt` but not its sources. The lock still pins mando 0.7.1. | R-03, R-07, R-08, R-09 | Medium | Close PR 4888 after the fix merges (D-4). |
| A-6 | The export guard would fail on the PR after a pip fix, because the lock disagrees with the export. | R-31, R-32 | Medium | No change. The guard confirms the decline. |
| A-7 | The journeys guard checks the job text, not the pip result. It passes on PR 4888 while the job fails. | R-27, R-28, R-29 | Medium | Recorded only. A resolver check is out of scope. |
| A-8 | The aggregators `pytest (coverage gate)` and `E2E smoke tests` fail on upstream results. | R-18 | Information | No change. |
| A-9 | The quality gates guide has no row for the journeys gate. | R-75 | Low | Out of scope. Track separately. |
| A-10 | The instruction file forbids closing update pull requests. D-4 closes PR 4888. | R-42 | Medium | Authorization gate (U-2). |
| A-11 | The fragment README allows no fragment for internal changes. The constitution requires one fragment for each change. | R-36, R-38, R-39 | Low | Add the fragment (D-5). |
| A-12 | `changelog.d/` holds more children than five. | Local listing. Recorded in plan Complexity Tracking. | Low | The release coordinator aggregates merged fragments. |
| A-13 | Gate issues 4891 to 4904 share the same cause. | R-72 | Medium | Close them in the closure step (FR-011). |
| A-14 | Runs 45064235051 and 45064235097 fail with the same resolver error on head `e86098c`. | Research E-2 | Medium | Closing PR 4888 ends these checks for the pull request. No separate work. |
| A-15 | The Dependabot service may reject the pip range form. | U-1 | Medium | Check the first pip run after the merge. |

## Defects in Existing Work

- PR 4888 changes the generated export and not the sources (A-5). Its pin conflicts with radon 6.0.1 (A-1). The PR cannot pass in any form.
- The journeys guard test does not detect a resolver failure (A-7). A future change may fail the install and still pass the guard.
- The Dependabot configuration has no ignore entry for mando (R-10). Dependabot can reopen the same bump after closure. This change adds the entry.
- The quality gates guide omits the journeys gate (A-9). This gap predates the issue, and the record leaves it for a separate change.

## Coverage Summary

| Requirement | Tasks | Tests | Status |
| - | - | - | - |
| FR-001 | T001, T-REMOTE-CI | TST-005, TST-011 | Covered |
| FR-002 | T001 | TST-005 | Covered |
| FR-003 | T001 | TST-006 | Covered |
| FR-004 | T002, T003 | TST-001, TST-004 | Covered |
| FR-005 | T002, T003 | TST-001 | Covered |
| FR-006 | T003, T-REMOTE-CI | TST-002, TST-003 | Covered |
| FR-007 | T004 | TST-007 | Covered |
| FR-008 | T-PR | TST-008 | Covered |
| FR-009 | T-LOCAL-GATES | TST-001 to TST-008 | Covered |
| FR-010 | T-MERGE | TST-009 | Covered |
| FR-011 | T-MERGE | TST-010 | Covered |

## Consistency Review

- The requirement list in `spec.md` matches the change map in `plan.md` and the coverage table in `tasks.md`. Each requirement has at least one task and at least one test or check.
- The decision list in `design/research.md` (D-1 to D-6) matches the decision list of `STATUS.json`. No decision uses a human marker.
- The remote table in `design/research.md` holds 90 rows. The `remote_checks` array of `STATUS.json` must hold the same 90 rows.
- The contract in `design/contracts/dependabot-pip-ignore.md` repeats the entry of `plan.md` and `tasks.md`. The range is `>=0.8` in all three files.
- The checklist `ci-gate.md` names the same failed check, job, run, and step as `research.md`, section E-1.

## Constitution Alignment

- Five-item rule: each record directory holds five children or fewer. `changelog.d/` holds more children, and the debt appears in `plan.md`, Complexity Tracking.
- Inline comments and action logging: the planned test method carries both (`plan.md`, Planned Test Method). T-LOCAL-GATES checks the review of each new executable line.
- Security: the change adds no suppression comment. Bandit runs on the changed test file in T-LOCAL-GATES.
- Governance: the constitution supersedes the README on fragments (D-5).

## Unmapped Tasks

None. Each task maps to at least one requirement in the coverage table.

## Metrics

- Requirements: 11 (FR-001 to FR-011). Success criteria: 4 (SC-001 to SC-004).
- Tasks: 8. Four implementation or evidence tasks and four final tasks.
- Tests planned: 11. Three new, one updated, four unchanged, and three command checks.
- Remote checks: 90 rows.
- Decisions: 6. Human decisions: 0.
- Record files: 11 Markdown files, plus one changelog fragment and two meta files.

## Unresolved Items

- U-1: The Dependabot service accepts the pip range `>=0.8`. Owner: orchestrator. Check: the first pip update run after the merge.
- U-2: The orchestrator authorizes the merge and the closure of PR 4888. Owner: orchestrator.
- U-3: The gates pass on the fix pull request. Owner: implementer. Check: T-REMOTE-CI.
- U-4: `uv lock --check` passes on the fix branch. Owner: implementer. Check: the dependency lock job.
- U-5: Mando 0.8.2 release notes and advisories are not reviewed. Owner: maintainers. The package is dev-only.
- Closure of gate issues 4891 to 4904. Owner: orchestrator. Check: TST-010.

## Convergence After Implementation

After T-MERGE, these facts hold. Main passes the journeys gate (TST-011). PR 4888 reads `CLOSED` (TST-009). The gate issues for PR 4888 close (TST-010). The pip update stream ignores mando 0.8 and later releases, subject to U-1.
