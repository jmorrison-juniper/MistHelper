# Implementation Plan: Mixed WAN History Summaries

**Branch**: `jmorrison-juniper-4200-migrate-mistwanperformance` (candidate, PR 4208) | **Date**: 2026-11-26 | **Spec**: `specs/numbered/0/0/1/2/3/1/3/4/4794-mixed-wan-history-summaries/spec.md`

**Input**: Numeric record. The route `0/0/1/2/3/1/3/4` is the base-5 form of 4794 with eight digits (design/research.md, decision D-6).

## Summary

The defect is a KeyError in `LinkEventSummaries._complete` for a snapshot hour. Repair commit d7a706d is already on the candidate branch. It makes each event total optional and None-safe. This plan adds the missing inline comments, action logging, and regression tests. It then delivers the change through PR 4208 after a rebase.

## Technical Context

- **Language/Version**: Python 3.15.2 in a worktree venv (`.github/copilot-instructions.md` lines 28 and 29, remote checks 89 and 90).
- **Primary Dependencies**: mistapi 0.64.1 (`requirements.txt` line 129, remote check 25). This change adds no dependency.
- **Storage**: None changed. Summaries compute in memory from the history records. The history store is not changed.
- **Testing**: pytest unit tests in `tests/unit/wan_performance/test_calendar_summaries.py` and one e2e test in `tests/e2e/web_portal/test_wan_performance_live.py`.
- **Target Platform**: Windows 11 development host. The code must also run on macOS and Linux.
- **Project Type**: Domain module in the `interfaces` package, consumed by the Flask web portal.
- **Performance Goals**: No change. Each period build loops over the records once for each helper. The repair adds no loop.
- **Constraints**: Principles VI and VII (inline comments and action logging). ASCII-only log text (Principle V). Line length 120 (`pyproject.toml` line 202, remote check 24).
- **Scale/Scope**: One identity for each call. One complete hour produces six summaries: daily, weekly, monthly, and three rolling windows (`summary.py` lines 124 and 157, remote checks 56 and 57).

## Constitution Check

Each rule has a result and a reason. "FAIL at head" means the candidate head breaks the rule today. The task that repairs it is named.

| Rule | Result | Reason |
| - | - | - |
| I. Five-Item Rule | PASS | The record route adds children only where the route allows them. `specs/numbered/0/0/1/2/3` already holds five children, and the route reuses child `1` (remote checks 34, 35, and 105). New function parameters stay at two. |
| II. Class-Based Architecture | PASS | The change stays inside the `LinkEventSummaries` class. No wrapper function is added. |
| III. Safety-First | PASS | The change reads no external input and runs no destructive operation. |
| IV. Full Deployment Pipeline | PASS with a blocking step | The plan lists local gates, rebase, push, PR, CI, squash merge, and main verification (remote check 9). The rebase is blocking because PR 4208 is a draft with conflicts (design/research.md, Linked work, and decision D-8). |
| V. Observability and Logging | PASS after T003 | The added log lines use `%s` formatting and ASCII text. The candidate head has no log line in `LinkEventSummaries.build` (remote check 53). |
| VI. Inline Comments | FAIL at head, PASS after T003 and T006 | Changed lines in `summary.py` and the three regression tests carry no inline comments (remote checks 50 to 54 and 61 to 64). Constitution text: remote check 10. |
| VII. Action Logging | FAIL at head, PASS after T003 | `LinkEventSummaries.build` has no info or debug log (remote check 53). Constitution text: remote check 11. |
| Technology: mistapi | PASS | The change adds no REST request and no WebSocket transport. |
| Technology: Podman and test containers | PASS | No container starts for this change. |
| Technology: File paths | PASS | The change adds no file path code. |
| Technology: Output backends and operational store | PASS | The change adds no export and no coordination record. |
| Technology: Database keys | PASS | The natural key of `HourlyMeasurement` is unchanged (remote check 60). |
| Development Workflow: Testing | PASS | Tests run with `python -m pytest` in the worktree venv (remote check 91 covers the gate table). |
| Development Workflow: Security findings | PASS | The change adds no suppression comment. |
| Documentation | PASS | The rules already appear in `documentation/wan-performance.md` lines 340 and 341 (remote checks 76 and 77). The changelog names issue 4794 (remote check 79). |
| Complexity-Driven SpecKit Escalation | PASS | The change touches two files and one class. This record exists for that reason (remote check 106). |
| Multi-Agent Git: Issue-first and labels | PASS | Issue 4794 exists with the labels `bug`, `web-portal`, and `in-progress`. |
| Multi-Agent Git: Branch naming | FAIL, justified | The candidate branch is `jmorrison-juniper-4200-migrate-mistwanperformance`, not `fix/4794-<slug>`. Decision D-1 explains why the repair stays on the candidate branch. |
| Multi-Agent Git: PR checklist | FAIL at head, PASS after T-PR | PR 4208 refers to issue 4794 but has no closing keyword (remote check 47). The AGENTS rule requires `Closes #<issue>` (remote check 94). |

## Architecture

The data path from the operator action to the rendered block:

```text
live_service.refresh (line 43) and refresh_port (line 74 builds the port records)
  -> SnapshotRecords.build and snapshot_client status metrics (flap_count at lines 575 and 581)
  -> history store (integration modules hold no link-event field names)
  -> LiveHistory.read (live_routes.py line 76 calls CalendarSummaries.build)
  -> CalendarSummaries.build (summary.py line 121 selects one identity, line 130 calls LinkEventSummaries.build)
  -> LinkEventSummaries.build (summary.py line 332 selects hours by period)
  -> live.html link-event block (lines 404 to 419)
```

The offline dashboard route also calls `CalendarSummaries.build` at `routes.py` line 136 (remote check 67). The repair does not change that call.

## Change Map

| Repository path | Action | Purpose | Requirements | Task |
| - | - | - | - | - |
| `src/interfaces/wan_performance/domain/summary.py` | Modify | Add inline comments and action logging to `LinkEventSummary`, `LinkEventSummaries.build`, `_has_events`, and `_complete`. The behavior comes from repair commit d7a706d. | FR-002, FR-003, FR-006, FR-011 | T003 |
| `tests/unit/wan_performance/test_calendar_summaries.py` | Modify | Extend the mixed-hour test to all period kinds. Add a snapshot-only test. Add inline comments to the regression tests. | FR-001, FR-004, FR-005, FR-008, FR-010, FR-011 | T004, T005, T006 |
| `specs/numbered/0/0/1/2/3/1/3/4/4794-mixed-wan-history-summaries/` | Add | This spec record, committed as one docs commit. | FR-012 | T009 |
| `documentation/wan-performance.md` | Verify only | Lines 340 and 341 already state the event rules. | FR-005, FR-006, FR-007 | T008 |
| `changelog.d/pr-4208.md` | Verify only | Line 19 names issue 4794. | FR-012 | T008 |
| `src/interfaces/wan_performance/presentation/templates/wan_performance/live.html` | Verify only | Guards at lines 409 and 417 render Unknown. | FR-009 | T007 |
| `tests/e2e/web_portal/test_wan_performance_live.py` | Verify only | Test at line 2295 asserts the Unknown text. | FR-009, FR-010 | T007 |
| `src/interfaces/wan_performance/presentation/live_routes.py` | No change | Consumer audit: call at line 76. | None | None |
| `src/interfaces/wan_performance/domain/calendar.py` | No change | Provides `expected_hours` at line 64. | None | None |
| `src/interfaces/wan_performance/collection/snapshot_client.py` | No change | Produces the event metrics at lines 575 and 581. | None | None |

No file is deleted. The change map names no path outside the Spec Kit record and the two test and summary files.

## Dependencies

- Runtime: mistapi 0.64.1, pinned in `requirements.txt` (remote check 25). No version change.
- Gate tools from the local gates table (remote check 91): ruff, black, mypy, pytest, pylint, radon, bandit, vulture, pydocstyle, interrogate, symbol-diff, and ste-linter. Also test-quality-analyzer and pytest-chunks (remote check 92 and 93).
- Git worktree support and the `gh` command for pull request work (AGENTS.md line 203, remote check 95).

## Risks and Mitigations

| Risk | Mitigation |
| - | - |
| PR 4208 conflicts with main. Its merge state is DIRTY (design/research.md, Linked work). | Rebase in a worktree. Stop and report if conflicts exceed 20 lines (decision D-9, remote check 3). |
| The candidate bundles issues 4200, 4793, 4794, and 4795 in one commit. | Keep this change to the lines in this record. Recommend a new issue for the mixed commit (analysis A-04). |
| The mixed-hour test asserts only the daily summary. | Task T004 extends the test to all period kinds (decision D-2). |
| A changed field type breaks a consumer. | The audit lists one consumer, `live.html`, which guards each field (remote checks 68 and 69). Integration modules hold no field name (remote check 83). |
| Added logs add six info lines for each request. | Log one info line and one debug line for each period build. Keep the text ASCII (decision D-4). |
| The rebase changes the SHAs that the record cites. | Repeat the remote checks after the rebase. Update each row that names 843be63, d7a706d, or 07b7751 (task T-PR). |
| The mistapi version wording differs across files (remote checks 7, 23, and 25). | Fix the wording in a separate issue (decision D-11). |
| A Windows gate runs longer than the session allows. | Run the table commands in order. Record the duration of each full-suite shard (remote check 93). |
| The repaired head merges before issue 4200 completes. | Human decision D-5 controls publication. T-MERGE waits for authorization. |

## Rollback Steps

1. Before a merge, revert each added commit on the candidate branch with `git revert <commit>`. Caution: a revert adds a commit, and it keeps the history that the branch already has.
2. After a merge, open a new pull request that reverts the squash commit on main. Caution: a revert changes main, so CI must pass again.
3. The change has no data migration. `LinkEventSummary` is computed on request and no integration module stores it (remote check 83). The rollback restores the float types through the revert only.

## Complexity Tracking

No constitution violation is added by this change. Existing debt: the untouched functions in `summary.py` lack inline comments. This change comments each touched block, as Principle VI requires. The remaining debt stays grandfathered.
