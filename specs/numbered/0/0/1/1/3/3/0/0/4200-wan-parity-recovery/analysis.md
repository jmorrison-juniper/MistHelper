# Recovery coverage and execution status

**Date**: 2026-11-05

This record maps requirements to the new execution sequence.
It is not a completed source comparison or a successful Spec Kit command report.
Historical T001-T087 reconciliation remains T002. No historical task state was changed.

## Skill-guided review and corrections

The local analyze and tasks skills supplied the review and task-refinement rules.
PowerShell setup remains unavailable. Direct document review does not claim successful script execution.
The user authorized these document refinements on 2026-11-05.

| ID | Category | Severity | Location | Finding and correction |
| --- | --- | --- | --- | --- |
| D1 | Dependencies | HIGH | tasks.md: foundation and E8 | Split existing safety prerequisites from later refresh-policy verification. T004 now establishes foundation evidence before T005-T006. |
| D2 | Dependencies | HIGH | tasks.md: duration and E7 | Separate interval/window evidence from retention. T015, T027, and T029 establish their respective prerequisites. |
| U1 | Execution detail | MEDIUM | tasks.md: metric and storage tasks | Replace abbreviated module paths with repository-relative paths and require recorded failing assertions before repairs. |
| C1 | Coverage | HIGH | contracts/parity.md: source goals | Add exportable top offenders and the region-to-circuit chain to the seed inventory and audience tasks. |
| I1 | Evidence accuracy | HIGH | research.md: destination behavior | Existing duration and event-availability sections are provisional behavior, not absent features. Verify their assumptions instead of repeating obsolete absence claims. |
| U2 | Comparison scope | HIGH | contracts/parity.md: seed inventory | Add 20 classified seed rows and ten assertion scenarios. These do not replace exhaustive per-control comparison. |

No requirement was removed. No evidence gate was changed to verified.
All 47 tasks remain open. The revised execution rules preserve stable task IDs.
The manual review maps all 24 FR/SC entries. It does not establish source runtime or visual parity.
There are no uncovered FR/SC entries in this document mapping.
Source behavior classification and historical task reconciliation remain incomplete.

## Additional discovery

The [discovery record](design/contracts/discovery.md) identifies 15 source surface groups and their remaining verification work.
It adds active routes, download callbacks, device charts, MOS, port counters, and peer path details.
It separates source 6h/7-day UI controls from the desired 3h reporting goal.

Static inspection corrects P11's earlier TODO-only classification.
Both source history methods have bodies, but their SDK calls do not match the installed destination SDK.
The gateway symbol is absent. The peer filter arguments are unsupported by the inspected device-insight signature.
No live request established sample shape, scope, units, or historical completeness.

The record also documents existing configured-store selection, cache keys, TTLs, admission bounds, and calendar calculations.
These observations are not new approved contracts.
Portal middleware, metric catalogs, scheduling, exports, visual comparison, retention, and backfill still require evidence.
T001-T004 remain open because partial discovery does not satisfy their full objectives.
No product file, task status, PR metadata, or remote branch changed during this discovery.

## Requirement coverage

| Requirement | Tasks | Acceptance evidence |
| --- | --- | --- |
| FR-001 | T001, T003, T007-T010 | Complete pinned source inventory |
| FR-002 | T002-T003, T043 | Completed/TODO/goal/unverified classifications |
| FR-003 | T007-T012, T033-T036 | Four journeys and reviewed visual hierarchy |
| FR-004 | T013-T016, T021-T022 | Capacity and threshold interval calculations |
| FR-005 | T017-T022 | Status, ranking, failure, and availability cases |
| FR-006 | T023-T024 | Timestamped quality sampling and calculations |
| FR-007 | T025-T026 | Verified SLE contracts and impact navigation |
| FR-008 | T013, T027-T028 | Dimensions, weighting, UTC windows, and coverage |
| FR-009 | T029-T030 | Configured-store history and capacity evidence |
| FR-010 | T031-T032 | Approved audience controls and reports |
| FR-011 | T004-T006, T037-T042 | Host authorization, session, storage, and admission tests |
| FR-012 | T042, T045 | No extra service, port, database, or token store |
| FR-013 | T005-T006, T040-T042 | Synthetic isolation assertions |
| FR-014 | T005, T038-T042 | Positive and negative state assertions |
| FR-015 | T033-T036, T041, T043 | Reviewed source-to-test evidence |
| FR-016 | T043-T047 | Exact-revision acceptance and blocked rows |
| SC-001 | T003, T007-T010, T043 | Zero unclassified inventory rows |
| SC-002 | T011-T042, T043 | Required completed behavior and deviations |
| SC-003 | T014-T030, T040 | Values or explicit unavailable states |
| SC-004 | T014-T030 | Independent expected calculations |
| SC-005 | T011, T021, T026, T032, T035, T040-T042 | All four browser journeys |
| SC-006 | T033-T036, T043 | Visual evidence or explicit blocker |
| SC-007 | T005-T006, T037-T042 | Host isolation and service inventory |
| SC-008 | T043-T047 | Owner decision on exact tested revision |

Document coverage: 16 functional requirements and 8 success criteria have task mappings.
This is 24 of 24 mapped requirements, not 100 percent implementation completion.
There are 47 open tasks and five user stories.
US1 has 10 tasks. US2 has 10. US3 has 4. US4 has 6. US5 has 6.
The remaining 11 tasks cover setup, foundation, and final acceptance.

## Remaining acceptance gaps

| Gap | Evidence gate | Execution tasks |
| --- | --- | --- |
| Complete original look, controls, and functionality | E1, E2 | T003, T007-T012, T033-T036 |
| Region/site/circuit hourly aggregation | E3, E7 | T013-T014, T027-T028 |
| Top-N and primary/secondary failure views | E3, E4 | T019-T022 |
| Continuous and cumulative threshold duration | E3, E7 | T015-T016 |
| Historical status, flaps, and availability | E4 | T017-T018 |
| Historical peer mean, maximum, and p95 | E5 | T023-T024 |
| WAN SLE scores and impact drilldowns | E6 | T025-T026 |
| 3h, 12h, 24h, and calendar windows | E3, E7 | T027-T028 |
| 13-month history and backfill | E7 | T029-T030 |
| Executive, engineering, and SLE views | E1, E3, E6 | T031-T032 |
| Shared refresh and optional Redis safety | E8 | T037-T040 |
| Full end-to-end and host regression evidence | All required gates | T041-T047 |

## Command status

The required Spec Kit prerequisite command failed with exit 127:

```text
pwsh -NoProfile -File .specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireSpec -RequireTasks -IncludeTasks
/bin/bash: pwsh: command not found
```

Spec Kit analysis stopped at prerequisites. No full consistency result is claimed.
The branch hook was loaded but not executed because the app already owns this feature branch.
Optional commit hooks were deferred. No feature pointer or other worktree was changed.
Local structural, format, link, and writing checks must remain separate from the blocked command.

## Local document validation

- STE examined nine files with no skipped files. Scores range from 93 to 97, above the required 80.
- Markdown link validation examined nine indexed Markdown files and found zero broken links.
- A direct format check verified 47 sequential unique open task IDs and 24 requirement coverage rows.
- The same check verified bounded feature and route directories.
- `git diff --cached --check` reported no whitespace errors.
- An initial directory argument to STE read zero files. The corrected explicit file selection examined all nine files.
- An initial link scan before indexing read zero files. Only the subsequent nine-file scan counts as validation.
- No production tests ran for this documentation-only record. The regression commands are future execution instructions, not new results.

The refined record passed another nine-file STE check with scores from 93 to 97 and no skipped files.
The nine-file link scan again found zero broken links.
Direct checks again verified 47 unique sequential open tasks, 24 mapped requirements, and bounded directories.
An isolated task audit examined this feature under a temporary `specs/` root and reported 47 open tasks, exit 0.
The temporary audit copy was removed automatically. No test baseline or feature pointer changed.
`git diff --check` passed after refinement.

The discovery update examined ten Markdown files with no skipped files.
STE scores ranged from 92 to 97.
Direct checks verified 47 sequential open tasks, 24 mapped requirements, and bounded feature directories.
The isolated task audit again reported 47 unchecked tasks and exit 0.
The source tree response was not truncated.
Static callback inspection found three CSV handlers, but did not prove region/site export buttons work.
Offline SDK inspection found the gateway symbol absent and peer filter arguments unsupported.
No production tests ran because only documentation changed.
The final link scan examined ten tracked Markdown files and found zero broken links.
The final STE scan examined ten files, skipped none, and passed with scores from 92 to 97.
`git diff --cached --check` passed.

## Start decision

Proceed with T001-T004 and descriptive comparison.
Do not implement a metric while its dependent gate remains unverified.
Do not accept full visual parity without permissible comparison evidence.
Do not merge or close issue #4200 because the recovery documents exist.

## Progress tracking

Issue [#4200](https://github.com/jmorrison-juniper/MistHelper/issues/4200) remains the migration and recovery tracker.
It has the `in-progress` label and a recovery progress comment.
Do not create a duplicate issue for the same recovery scope.
Update task status only when its full evidence or implementation objective is satisfied.
Future issue updates must identify completed tasks, open gates, exact revisions, and validation results.
