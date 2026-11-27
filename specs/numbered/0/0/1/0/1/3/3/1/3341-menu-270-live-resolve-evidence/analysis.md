# Analysis: Menu 270 Live Resolve Acceptance Evidence

This review checks the spec, the plan, the tasks, and the code on `main`. Row numbers refer to the remote verification table in `design\research.md`.

## Consistency Review

| Check | Spec | Plan | Tasks | Code on `main` | Result |
| - | - | - | - | - | - |
| Resolve path exists | FR-007 | Architecture | T001 | Rows 5 to 14 | Consistent |
| Offline tests exist | FR-012 | Testing | T002 | Rows 20 to 23 | Consistent |
| Typed gate exists | FR-003 | Constitution III | T004 | Row 17 | Consistent |
| Endpoint report is current | FR-009 | File change map | T003 | Row 26 states the opposite | Defect, fixed by T003 |
| Installed mistapi version | Assumptions | Dependencies | T003 | Row 51 names 0.64.1. Row 25 names 0.64.0. | Defect, fixed by T003 |
| Category of mode 3 | FR-013 | Constitution III | D-5 | Rows 27, 28, and 33 disagree | Unresolved, human decision |
| Pull request keyword | FR-014 | T-PR | D-7 | Not applicable | Decided |

## Findings

**A-1 (high). Issue record conflict.** The issue title and body, and the task message, state that no live resolve request was sent. Issue comment IC_kwDOQltU8c8AAAABeBNT3g (2026-10-21T06:20:32Z) records one approved request. Mist returned HTTP 403, the outcome was `error`, and the action stayed `open`. This record follows the comment, because it is the later owner record. The owner confirms this reading at T004. Status: resolved in this record, pending owner confirmation.

**A-2 (high). Stale endpoint report.** Row 26 states that the research did not send a live resolve request. Row 25 names mistapi 0.64.0. Row 51 shows that 0.64.1 is installed. T003 corrects both statements.

**A-3 (medium). Pull request paths differ from `main`.** The file list of pull request #3316 names the retired `marvis/actions/client.py` path and related paths. Row 41 shows that the path is absent on `main`. The Marvis package sits at `src/mist/intelligence/marvis/actions/`. This record cites only the current paths.

**A-4 (high). Classification conflict for mode 3.** The registry places menu 270 in `interactive_safe` (rows 3 and 4). The copilot instructions define destructive as a change to the Mist cloud or a production device (row 28). The constitution lists other changes to the Mist cloud as destructive (row 33). Mode 3 changes Mist cloud state (row 14). The registry comment records the reason for the current row: the portal needs the row. The typed gate (row 17) meets the typed-confirmation rule. Decision D-5 gives the owner the choice. Status: unresolved, human decision.

**A-5 (low). No test uses HTTP 403 for the resolve path.** The refused-request tests use 400 (row 21), 429 (test 7 of the test set), and 503 (test 5). The non-2xx branch in `resolve_action` (rows 6 and 7) returns the same result for every non-2xx status. Decision D-4 adds no new test.

**A-6 (medium). Acceptance depends on the owner.** The acceptance criteria in the issue body stay unchecked. Only the owner can run the live check, because the lab organization needs a credential that the agent does not hold. Tasks T004 to T006 record that dependency.

**A-7 (medium). Log evidence is not fully traced.** The debug line that records the HTTP status after the request (research row 7) reaches `data\script.log` only if the file handler accepts DEBUG. The default file level is not traced (unverified item U-4). The `http_status` column of the results file (row 11) is the reliable record. The quickstart reads that column first.

**A-8 (medium). Pull request keyword differs from the brief.** The brief names the Closes keyword for the pull request body. Closing the issue at merge would hide the open acceptance criteria. Decision D-7 uses `Refs #3341` until the owner evidence record shows acceptance.

**A-9 (low). Review label.** The issue carries `needs-human-review`. The T-MERGE task keeps `auto-merge` off until the owner reviews the pull request.

**A-10 (low). Authorization state.** Issue comment IC_kwDOQltU8c8AAAABkIBgGQ (2026-11-08) states that the user authorizes issue-scoped live tests. The same comment states that the worktree has no `.env` file and no Mist token environment value. It also states that the connected tools cannot list the beta actions. The owner can run the live check. This session cannot run it. Decision D-1 records the owner-only path.

**A-11 (low). Retry rule source.** Issue comments IC_kwDOQltU8c8AAAABeBmFAQ (2026-10-21) and IC_kwDOQltU8c8AAAABkIBgGQ (2026-11-08) both name issue #4389 as the tracker of the HTTP 403 cause. The spec uses the 2026-11-08 instruction "Do not retry the resolve" as the retry rule (FR-008).

## Unresolved Items

| Item | Owner | Reason |
| - | - | - |
| Live acceptance (T004 to T006) | Repository owner | Requires a lab credential and an open action. |
| HTTP 403 cause | Issue #4389 | The cause is unknown. Retry is blocked. |
| Category of mode 3 (D-5) | Repository owner | Product priority and safety class. |
| Default file log level (U-4) | Maintainer | Not traced in this run. |
