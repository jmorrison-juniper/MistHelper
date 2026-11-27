# Contract: Evidence record

This contract defines one evidence row for the acceptance work. Each row records one pull request or one run. The rows appear in `design/research.md` when the orchestrator adds new evidence.

## Fields

| Field | Rule |
| - | - |
| Pull request | Number, state, merged at (UTC), merged by, and merge commit |
| Enable run | Run ID, created at (UTC), event, and enable job result |
| Logged result | One of `merged`, `enabled`, or `blocked`, from the enable step lines (RC-25, RC-26, RC-27) |
| Dispatch result | Result of the dispatch job in the same run and in any later run (RC-28) |
| Started workflows | Files with a `Started <file> on main.` line (RC-34, line 366) |
| Covered workflows | Files with an `already covers the tip.` line (RC-34, line 339) |
| Source | Run URL and pull request URL |

## Acceptance of a row

- The row counts as immediate-path evidence when the logged result is `merged` and the dispatch job result is `success` in the same run.
- The row counts as delayed-path evidence when one run logs `enabled` and its dispatch job reports `skipped`.
- The same row also needs a later closed or scheduled run that covers the merge commit within six hours.
- The row counts as merged-close evidence when a closed and merged run has its enable job `skipped` and its dispatch job `success` (RC-29, RC-49, RC-64).
- The row does not count when a manual call starts the run and no dispatch job line shows the start (H-05).
- The row does not count when the merge is a test-only merge (RC-93).
- The row does not count when the pull request edits a workflow file (RC-27, RC-54).

## Sample row

| Pull request | Enable run | Logged result | Dispatch result | Started workflows | Source |
| - | - | - | - | - | - |
| 4941, merged at 2026-11-26T07:15:01Z by app/github-actions, merge commit f03c6c9 | 45773895615, created 2026-11-26T07:14:54Z | merged | success | ci.yml, codeql.yml, container-build.yml, ste-lint.yml | RC-63 |
