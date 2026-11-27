# Specification Analysis Report: RADIUS API Failure Test Assertion

## Findings

| ID | Type | Severity | Finding | Evidence | Action |
| - | - | - | - | - | - |
| A-1 | Root cause, tooling | High | The baseline key includes `line_number`. A line shift above a matched finding creates a new finding. | research RC-19 (`baseline.py` line 55), RC-14 (baseline line 694), RC-09 (candidate line 707), RC-20 (gate counts new findings) | The assertion removes the finding. A follow-up issue in misthelper-devtools should key findings by test name. |
| A-2 | Blocker, PR state | High | PR #4208 is a draft (`isDraft` true) with merge state `DIRTY`. | `gh pr view 4208` output (research section 2) | The owner converts the PR and resolves the conflicts. T-MERGE waits. |
| A-3 | Deviation, PR body | Medium | PR #4208 says `Refs #4798`. A squash merge does not close issue #4798. | PR #4208 body (research section 2). `AGENTS.md` line 224 (RC-46). | The owner closes issue #4798 by hand after the merge, as the issue comment states. |
| A-4 | Defect, branch name | Low | PR #4208 uses branch `jmorrison-juniper-4200-migrate-mistwanperformance`. | PR #4208 `headRefName` (research section 2). `AGENTS.md` line 194 (RC-45). | No change in this issue. Renaming a shared PR branch needs owner approval. |
| A-5 | Defect, baseline hygiene | Medium | The baseline holds nine entries for the module. Six `weak_zero_assertions` entries describe functions that contain assert statements now. The entry at line 694 matches no finding after this change. | RC-15, RC-05 (approximate scan), RC-19. The gate ignores removed findings (RC-20). | Keep the baseline unchanged (FR-005). A later cleanup needs owner approval. |
| A-6 | Drift, configuration | Low | The config key `weak_no_assertions` differs from the emitted rule `weak_zero_assertions`. | RC-17 (config line 24), RC-18 (emitted rule line 245) | A follow-up issue should align the key. The effect on the gate is unverified (research U-2). |
| A-7 | Drift, documentation | Low | Three sources give three mistapi bounds. `pyproject.toml` pins `>=0.64.1`. Repository instructions give `>=0.64.0`. The constitution gives `0.59+`. | RC-38 (line 29), RC-37 (line 21), RC-43 (line 279), RC-55 (installed 0.64.1) | A follow-up documentation issue should align the statements. This change does not depend on them. |
| A-8 | Defect, fixture (owned by issue #4797) | High | The `fake_mh` fixture binds the shared resolver and yields with no restore. | RC-03 (lines 45 and 46 on `main`) | Issue #4797 owns the fix. This issue does not change the fixture (FR-006). |
| A-9 | Defect, existing commit | High | Commit `843be63` changes lines 707, 710, and 712 with no inline comment. Principle VI requires an inline comment on each line of generated code. Line 710 sits in the same changed block. | RC-06 (blob `75b4bd`, lines 707, 710, 712), RC-41 (Principle VI) | T001 adds a follow-up commit with the comments. The fix is required before merge. |
| A-10 | Status, remote CI | Info | Head `843be63` shows SUCCESS for `Test quality ratchet (gate)` and 42 other checks. It shows 10 skipped checks and no failure. | `gh pr view 4208` status rollup (research section 2) | T-REMOTE-CI reruns the checks after the follow-up commit. |
| A-11 | Scope, PR contents | Medium | PR #4208 changes 82 files for a web-portal feature. The test fix ships with that feature. | PR #4208 file count (research section 2) | The owner decides the merge order. Decision D-1 records the route. |

## Coverage Summary

| Requirement | Task | Test | Status at PR head `843be63` |
| - | - | - | - |
| FR-001 | T001 | TC-001 | partial. The assertion exists. Its comments are missing (A-9). |
| FR-002 | T001 | TC-001 | partial. `capsys` is in the signature. |
| FR-003 | T006 | TC-002, TC-003 | open. Mutations are not run yet. |
| FR-004 | T002, T004, T005, T-REMOTE-CI | TC-005, TC-006 | partial. The remote job reports SUCCESS at head `843be63`. |
| FR-005 | T002 | TC-007 | verified-present. PR #4208 does not change the baseline. |
| FR-006 | T003 | TC-008 | verified-present. Commit `843be63` changes one file. |
| FR-007 | T001, T-LOCAL-GATES | TC-009 | partial. Comments are missing at lines 707, 710, and 712 (A-9). |
| FR-008 | T007, T-LOCAL-GATES | TC-004, TC-009 | open. No local gate has run in this phase. |
| FR-009 | T-PR, T-MERGE | TC-010 | verified-present for one open PR. The merge waits (A-2). |
| FR-010 | Record self-review | TC-011 | open until the self-review against the Metrics section completes. |

## Consistency Review

- The assertion text in spec FR-001, plan snippet, tasks T001, and contract file is the same string.
- The failing rows in the plan Constitution Check match findings A-4, A-9, and A-3.
- The record path matches the route that `spec-route.ps1` computes for issue 4798 (RC-48, RC-49).
- Each file claim in the spec and plan cites a research row ID. Each row ID exists in `design/research.md`.
- The inline comment plan adds comments only to lines that the change touches or that sit in the same block.
- No task names a path outside the change map in plan section "File-by-File Change Map".

## Unmapped Tasks

None. Each task maps to at least one requirement in the Requirement Coverage table of `tasks.md`.

## Metrics

- Requirements: 10 (FR-001 to FR-010).
- Tasks: 11 (T001 to T007, T-LOCAL-GATES, T-PR, T-REMOTE-CI, T-MERGE).
- Tests planned: 11 (TC-001 to TC-011).
- Decisions: 7 (D-1 to D-7). Human decisions: 0.
- Remote checks: 62. Research table rows: 62. The summary repeats the count 62.
- Analysis findings: 11 (A-1 to A-11).

## Unresolved Items

- The blocker in A-2 stops T-MERGE.
- Follow-up issues for A-1, A-5, A-6, and A-7 need owner approval. Filing them is outside this record.
- The unverified items U-1 to U-7 in `design/research.md` section 7 remain open.
