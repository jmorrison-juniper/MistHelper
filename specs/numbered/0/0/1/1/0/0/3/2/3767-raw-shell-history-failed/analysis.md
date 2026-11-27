# Analysis: Raw shell history test failure (issue 3767)

## Consistency Review

| Check | Result | Evidence |
| - | - | - |
| Requirements map to tasks | Pass | FR-001 maps to T001. FR-002 maps to T002. FR-003 maps to T003. FR-004 maps to T006 and T007. FR-005 maps to T004. FR-006 maps to T005. FR-007 and FR-008 map to T008 and T009. FR-009 maps to T-LOCAL-GATES. FR-010 maps to T-PR, T-REMOTE-CI, and T-MERGE. |
| Requirements map to a test or a check | Pass | Each FR has a pytest command, a GET check, an STE check, or a test-quality check in `tasks.md`. |
| Tasks name exact paths | Pass | Each task names a repository path, a `test-artifacts` path, or the record path. |
| Tasks name a local gate command | Pass | T001, T006, T008, and T-REMOTE-CI use the Tests row. T009 uses the Test quality row. T002 to T005, T007, T-LOCAL-GATES, T-PR, and T-MERGE use the STE row. |
| Remote rows match counts | Pass | `design/research.md` has 74 rows in the remote table. `3767-STATUS.json` has 74 `remote_checks`. `3767-summary.md` states 74. |
| Five children per folder | Pass | The feature root holds `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, and `design/`. `design/` holds four children. `design/checklists/` holds one child. |
| Route | Pass | The route is `specs/numbered/0/0/1/1/0/0/3/2/3767-raw-shell-history-failed`. The base-5 rule gives `00110032` (R-41). |
| Contracts folder | Pass | The folder is omitted. `plan.md` states why. |
| Code and test paths | Pass | The failing test path is the same on accepted main and current main (R-01, R-06). The source paths differ (R-31, R-32). The record cites both. |
| SDK claims | Pass | The record cites the installed mistapi file (R-50, R-51). It makes no SDK insufficiency claim. |
| Labels | Pass | The issue has type `bug` and scope `tests`. The record adds `in-progress` (D-7) and keeps `needs-investigation`. |

## Defects in Existing Work

These defects come from the issue text, its comments, and its linked records. The record corrects each one.

1. The issue traceback names the retired `websocket_streams` import path. That path is correct for accepted main (R-08, R-22). Current main moved the package to `src/mist/realtime/websocket_streams/` and changed most blobs (R-31, R-32). The record cites both paths.
2. The issue line numbers 108 and 464 match accepted main (R-02, R-03). The same test moved on current main (R-06, R-07).
3. The issue command passes `--cov-config=coverage.ini`. The repository tree has no such file on either commit (R-29, R-30). The controlled run uses the tracked coverage settings in `pyproject.toml`.
4. The issue names a Python 3.13 environment. The project requires Python 3.15 (R-36, R-37). The controlled run uses 3.15.2 (D-5).
5. The candidate server change is superseded on current main by the `getattr` form (R-25, R-26). The candidate test file is absent on current main (R-28). The change does not reach current main.
6. The legacy handoff branch `recovery/3767-handoff-20261004` is absent (R-66). CI run 37172626352 still names it (R-70). The record reuses none of its content.
7. The search for "3767" in pull requests returned PR #96. That pull request is unrelated (research, "Issue Facts and Linked Work").
8. The issue comment of 2026-10-26 reports one current-main run that passed. The record confirms that no scanned CI log shows FAILED for the test (R-46).

## Unresolved Items

1. The controlled run has not taken place. Tasks T006 and T007 decide hypothesis H1 (U-3).
2. The owner has not authorized a fixture change. Task T008 stays absent until authorization (D-4).
3. The local Python 3.13 result is unexplained (U-4).
4. The private execution log is not in the repository, so its hashes cannot be checked (U-6).
5. Seven scanned logs have no line for the test. The record does not open them (U-9).
6. The reservation scope of #3760 and #3761 is inferred from the issue titles (U-7).

Caution: The closing keyword `Closes #3767` closes issue 3767 on merge. The cause remains unconfirmed until T007 finishes. The orchestrator confirms the closure before T-MERGE (D-6).

## Verdict

The record is consistent with the verified remote evidence. No check fails. The next gate is the controlled run in T006. The fixture change in T008 needs the owner authorization that the issue requires.
