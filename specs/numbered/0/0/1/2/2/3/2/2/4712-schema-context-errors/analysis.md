# Specification Analysis Report: SQLite schema context errors

This report checks the spec, the plan, the tasks, and the remote code against each other. It also records the defects in the earlier candidate work. Row numbers refer to the remote verification table in `design/research.md`.

## Findings

| ID | Severity | Finding | Evidence | Action |
|---|---|---|---|---|
| A-01 | High | The candidate base commit `343461229` is 84 commits behind `main`. | Row 75 (stale). | T001 creates a new branch from current `main`. The candidate commits are not reused (D-10). |
| A-02 | High | The candidate validation used Python 3.14.7. The repository requires Python 3.15. | Rows 25, 41, and 76 (stale). The environment file names Python 3.15.2. | T002 uses Python 3.15.2. All tests run again. |
| A-03 | High | The candidate and the issue comments name draft #4358 as the owner of the rename. PR #4358 merged on 2026-11-13, and the rename target does not exist. The move belongs to open issue #4142. | Rows 69, 78, and 79. | The legacy test stays in place (D-4). Issue #4142 must carry the updated expectation through its move (open item OI-3). |
| A-04 | Medium | The candidate computed the route by hand, because PowerShell was unavailable. PowerShell now runs. | Row 77 (stale). Rows 21 to 23 and the arithmetic in D-6. | T003 runs `Resolve-SpecFeaturePath`. |
| A-05 | High | The candidate did not update the README. The constitution requires a README update for each behavior change. | Row 49. Issue comment 6764708023 names the gap. | T009 adds two sentences to README line 30 (D-7). |
| A-06 | Medium | Issue comment 6764708023 says the prepared PR text marks the README update as not applicable. That statement is wrong. | Issue comment 6764708023. | The PR body in T-PR states that the README update applies. |
| A-07 | Medium | The candidate test file holds 19 parameterized cases. Some cases test unchanged name matching. One case restates the implementation. | Candidate commit `d9d75e00c`, read locally. | Three new tests and one updated test replace them (D-5). |
| A-08 | Low | The pull request template has no Closes line. | Row 35 (absent). | T-PR adds `Closes #4712` to the PR body. |
| A-09 | Medium | The issue body names `3964d21d` as current `main`. Current `main` is `f03c6c9b`. The defect path still exists on remote `main`. | Rows 1 to 4, 7, 8, 64, and 65. | The spec cites current lines and blob SHAs only. |
| A-10 | Low | The blind handler baseline has no entry for `database_schema_utils.py`. The broad handler binds `error` and uses it, so it is not blind. | Rows 3, 16, and 17. | Removal lowers the broad handler count only. SC-005 checks the guard. |
| A-11 | Medium | Existing debt: `DatabaseSchemaUtils` holds 14 methods. | Row 72 and the Complexity Tracking table in `plan.md`. | This change adds no method. A follow-up action splits the class. Open item OI-2. |
| A-12 | Low | Open pull request #4813 changes `data_exporter.py`. This change does not touch that file. | Open pull request check at planning time. | T004 repeats the check before any file changes. |
| A-13 | Medium | The owner states that an earlier rebase instruction survives only in compressed history. Its provenance is not verified. | Issue comment 6764708023. | This spec does not rely on that instruction. The branch comes from `main`. |
| A-14 | Medium | The candidate validation results (test counts, coverage, STE scores, route check) are not reproduced here. | Unverified items U-1, U-2, and U-4 in `research.md`. | T-LOCAL-GATES runs every applicable gate again. |
| A-15 | Medium | Publication is held by the owner. | Issue comment 6764708023 (2026-11-10). | T-PR and T-MERGE wait for the hold to lift and for orchestrator authorization (D-11). |
| A-16 | Low | `_dispatch_format_write` logs with the root logger. The runtime log file is `data/script.log`. The root logger routing was not read in this session. | Row 11 and row 46. Unverified item U-10 in `research.md`. | The operator paragraph names the runtime log, not a file handler. |

## Coverage Summary

| Requirement | Tasks | Tests or gates |
|---|---|---|
| FR-001 propagate the original error | T005, T006, T007 | TST-2, TST-4 |
| FR-002 propagate a logging failure and do not return `unknown` | T005, T007 | TST-1 |
| FR-003 return `unknown` only for a completed walk with no match | T007 | Existing test `test_returns_unknown_when_no_api_frame_on_stack` in `tests/unit/db/test_database_schema_utils.py` |
| FR-004 keep patterns, order, and cleanup | T007, T008 | Existing detection tests in `tests/unit/db/test_database_schema_utils.py`, and T008 symbol gate |
| FR-005 stop the SQLite write and log the table and format | T005, T007 | TST-3 |
| FR-006 update the legacy expectation in the same change | T006 | TST-4 |
| FR-007 README states the behavior | T009 | STE gate (T009 verification) |
| FR-008 operator guide describes the log line and action | T010 | STE gate (T010 verification) |
| FR-009 one changelog fragment | T011 | `tests/guardrails/test_changelog_fragment_policy.py` |
| FR-010 regression tests fail before the change | T005, T-LOCAL-GATES | TST-1, TST-2, TST-3, TST-4 red run |
| FR-011 no broad handler that ignores its exception | T007 | `tests/guardrails/test_blind_exception_handler_ratchet.py` |
| FR-012 no move or rename of the legacy test | T006 | Run of `tests/unit/db/test_database_schema_utils.py` at its existing path |
| FR-013 record path and route | T001, T003, T012 | `python -m pytest tests/guardrails` |

Each requirement maps to at least one task and at least one test or gate.

## Constitution Alignment

The constitution check in `plan.md` lists each rule. One rule fails for an existing reason: the five-item limit for `DatabaseSchemaUtils` (A-11). This change does not increase that count. The plan records the follow-up action, as the constitution requires.

## Unmapped Tasks

None. Each task maps to a requirement, to a delivery rule, or to the constitution pipeline.

## Metrics

- Requirements: 13 (FR-001 to FR-013).
- Success criteria: 7 (SC-001 to SC-007).
- Tasks: 16 (T001 to T012 and four delivery tasks).
- Tests planned: 4 (three new, one updated).
- Remote checks: 85 rows. Present 73, absent 8, stale 4.
- Legacy record claims: 13 rows. Verified 5, stale 4, absent 4.
- Decisions: 11 (D-1 to D-11). Human-required decisions: 0.
- Record directories checked for five children or fewer: feature root (5), `design` (5), `contracts` (1), `checklists` (2), and the route parent (3 after the change).

## Convergence After Implementation

After implementation, these statements must hold:

- TST-1 to TST-4 pass on the changed source.
- The module-level names of `database_schema_utils.py` are unchanged.
- The README, operator guide, changelog fragment, and record Markdown files each score 80 or above in the STE linter.
- The blind handler ratchet reports no new blind handler.
- The record holds five children or fewer at each level.

## Unresolved Items

- OI-1: The owner lifts the publication hold. T-PR depends on this item.
- OI-2: A follow-up action splits `DatabaseSchemaUtils`. This spec does not open that action. It needs its own ownership reservation.
- OI-3: Issue #4142 carries the updated expectation through its test move.
