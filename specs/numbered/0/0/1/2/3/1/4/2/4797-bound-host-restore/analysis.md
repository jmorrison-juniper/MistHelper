# Specification Analysis Report: Bound host restore for the WLAN RADIUS fixture

**Scope**: Consistency across `spec.md`, `plan.md`, and `tasks.md`, and against remote content on main and PR #4208. Evidence IDs (RC-nn) refer to the remote verification table in `design/research.md`.

## Findings

| ID | Severity | Finding | Evidence | Action |
| - | - | - | - | - |
| A-1 | High | The issue names a test path and a test name that do not exist on main. The reproduction cannot run on main as written. | RC-27, RC-29 | Use PR head paths before the merge. Use main paths after the merge (decision D-4). |
| A-2 | Medium | PR #4208 body says `Refs #4797`, not `Closes #4797`. A merge will not close the issue automatically. | PR #4208 body from `gh pr view 4208`. Constitution PR checklist (RC-68). | The PR owner edits the body. T-MERGE verifies the closure. This record does not edit GitHub. |
| A-3 | High | PR #4208 changes the same fixture file as this issue. A second open pull request for that file breaks the one-open-PR rule. | RC-30. PR #4208 changes 82 files, including the fixture file. | Gate G-1 and decision D-1. |
| A-4 | Medium | The local working tree differs from HEAD for `request_admission.py` and the wan_dashboard test file. Local searches can mislead. | Local hash check in `design/research.md`, section Local state. | Decision D-10. Run each check in a clean worktree. |
| A-5 | Medium | The baseline holds nine findings for the fixture file. New tests can add findings. | RC-61 | T008 runs the ratchet on the committed change before the pull request. |
| A-6 | Low | The `fake_mh` fixture in PR #4208 has no action logs. Principle VII can require logs in a touched block. | RC-08, RC-40 | The follow-up adds logs to the new fixture only (decision D-6). The PR #4208 owner decides on `fake_mh`. |
| A-7 | Low | Constitution line 409 requires one fragment for each change. The changelog README exempts internal-only changes. | RC-38, RC-41, RC-32 | Decision D-5. The constitution owner aligns the two rules. |
| A-8 | Low | The constitution names mistapi 0.59 or later. The repository instructions name the range 0.64 to 0.65. | RC-67, RC-33 | Out of scope. This record notes the drift only. |
| A-9 | Low | PR #4208 commit messages use the type `test`. The squash title uses the feature type, so the fix has no separate commit on main. | Commit messages of 1f4843c and 843be63 from `gh api` compare. | Review at merge. No action in this record. |
| A-10 | Medium | Main admission does not read the shared resolver. The leaked host has no proven visible failure on main. | RC-21, RC-22 | Unresolved item U-5. The restore tests check the defect directly. |
| A-11 | Low | Principle IV steps 10 to 12 apply to each code change. A test-only change alters no runtime file. | RC-37 | Unresolved item U-9. |

## Coverage Summary

| Requirement | Tasks | Test or gate |
| - | - | - |
| FR-001 Restore the previous bound host at teardown | T005, T-LOCAL-GATES | Restore tests (T005). Mutation check (T006). |
| FR-002 No production code change | T003, T004, T-PR, T-MERGE | Shard 1 and shard 2. Diff review in T-PR. |
| FR-003 Candidate reproduction fails | T001 | Reproduction pair on the candidate commit (Tests row). |
| FR-004 PR head reproduction passes | T002 | Reproduction pair on the PR head (Tests row). |
| FR-005 Shard 1 reports zero failures | T003, T-REMOTE-CI | Full tests row, shard 1. |
| FR-006 Shard 2 reports zero failures and the guard passes | T004, T007, T-REMOTE-CI | Full tests row, shard 2. Process folder guard. |
| FR-007 Restore tests fail without the restore | T005, T006, T-PR | Restore tests and mutation check. |
| FR-008 Lint and Format pass | T-LOCAL-GATES | Lint row (line 58) and Format row (line 59). |
| FR-009 Zero new ratchet findings | T008, T-LOCAL-GATES | Test quality row (line 65). |

Every requirement maps to at least one task and at least one test or gate.

## Constitution Alignment

The constitution check in `plan.md` lists each rule. No rule fails. Principle IV has a condition (U-9). Principle VII passes for the new fixture (decision D-6). Analysis items A-6 and A-7 record the rule conflicts.

## Unmapped Tasks

None. T-REMOTE-CI maps to FR-005 and FR-006. T-MERGE maps to FR-002.

## Metrics

- Functional requirements: 9.
- Success criteria: 5.
- Tasks: 12.
- Decisions: 10, with 1 human decision (D-9).
- Remote checks: 73.
- New tests planned: 2.
- Route children: child `2` joins child `1` under `0/0/1/2/3/1/4`.

## Unresolved Items

- **U-1**: The candidate reproduction failure is a static trace only. No test ran in this session.
- **U-2**: The PR head reproduction pass is not run in this session.
- **U-3**: The shard totals in the issue body (26141 passed, 24 skipped, one failure) are reporter statements. They are unverified.
- **U-4**: Whether MistHelper.py completes its import in a test session is not verified. The conftest records stop cases (RC-19).
- **U-5**: Other readers of the shared resolver in the suite are not enumerated. Main admission does not read it (RC-21).
- **U-6**: A restore after a failed test body is not tested. The design relies on the context manager contract of `patch.object`.
- **U-7**: Whether Principle VII requires logs in test fixtures (A-6) is a reviewer decision.
- **U-8**: Constitution line 409 and changelog README line 58 conflict (A-7). The constitution owner decides.
- **U-9**: Whether Principle IV steps 10 to 12 apply to a test-only change is an orchestrator decision.
- **U-10**: The PR #4208 closing reference (A-2) and the merge timing (D-9) depend on the owner.

## Convergence After Implementation

The record converges when T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE report their acceptance results. Main must then hold the fixture content of the follow-up commit. Issue #4797 must show as closed.
