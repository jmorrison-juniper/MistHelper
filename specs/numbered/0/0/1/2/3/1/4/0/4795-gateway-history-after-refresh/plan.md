# Implementation Plan: Gateway History After an Ordinary Refresh

**Branch**: `jmorrison-juniper-4200-migrate-mistwanperformance` (repair source) | **Date**: 2026-11-26 | **Spec**: `spec.md`

**Input**: Numeric record `specs/numbered/0/0/1/2/3/1/4/0/4795-gateway-history-after-refresh/`, from issue #4795.

## Summary

The repair already exists in the candidate. Commit `d7a706d` changes `LiveHistory.read` so that gateway selection resolves one gateway from gateway, circuit, or peer records. This plan finishes the repair for publication. It adds the missing unit tests, adds the comments and action logs that the constitution requires, extracts the history read to keep `read` within the function limit, and sets the publication rules.

## Technical Context

- **Language/Version**: Python 3.15 or newer, as `pyproject.toml` declares (R98).
- **Primary Dependencies**: The Flask blueprint in `live_routes.py`. `mistapi` 0.64.1, pinned in `requirements.txt` (R72).
- **Storage**: The history store through `HistoryRepository`, and the snapshot cache through `RefreshStore`. No schema change.
- **Testing**: pytest unit tests in `tests/unit/wan_performance/`. pytest end-to-end tests in `tests/e2e/web_portal/` with `UPGRADE_PORTAL_E2E_STRICT=1` (R77).
- **Target Platform**: Windows 11, macOS, and Linux. The portal ships as a Podman container.
- **Project Type**: Presentation module in the `wan_performance` package.
- **Performance Goals**: The refusal path reads no store and performs no I/O. Each page reads the history store at most once.
- **Constraints**: No Mist request in the read path. No cache write. Exact message text. An inline comment and an action log for each changed line.
- **Scale/Scope**: One organization for each process. One gateway for each page.

## Constitution Check

Each rule has a result and a reason. A "Fail" row names the task that repairs it.

| Rule | Result | Reason |
| - | - | - |
| I. Five-item rule, record layout | Pass | The feature root holds five children, and `design/` holds five children. The record sits under the managed root `specs/numbered/`. |
| I. Route | Pass | Route `0\0\1\2\3\1\4\0` is the base-5 digit string of 4795, padded to eight places (research.md, R78 to R80). |
| I. Function limits, `LiveHistory.read` | Fail, then Pass | The read spans 28 lines (R20). The limit is 25. T003 extracts `_read_history`. |
| I. Function limits, `LivePages.render` | Fail, not touched | The method spans 64 lines (R28). This change does not touch it. D-12 defers it. |
| I. Function limits, `LiveHistory._select_identity` | Pass | The method spans 19 lines and has three parameters (R21). |
| II. Class-based architecture | Pass | The helpers are static methods of `LiveHistory`. No wrapper function is added. |
| III. Safety-first | Pass | The refusal runs before any read. The exception log names no secret. |
| IV. Full deployment pipeline | Planned | T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE cover the steps in order. |
| V. ASCII logging | Pass | The new log text is ASCII. |
| VI. Inline comments | Fail, then Pass | The changed methods carry no comments (R26). T003 and T004 add them. |
| VII. Action logging | Fail, then Pass | The read logs nothing before the history read (R27). T004 adds the logs. |
| Technology: mistapi only | Pass | The change adds no Mist REST request. |
| Technology: containers | Pass | The tests start no container. |
| Technology: data directory, export backends, operational store | Not applicable | The change writes no product file, adds no export, and adds no coordination record. |
| Development workflow: menu operations | Not applicable | The change adds no menu operation. |
| Documentation | Pass | Lines 391 and 392 of `documentation/wan-performance.md` state the rule (R45, R46). |
| Release note | Pass | Line 19 of `changelog.d/pr-4208.md` names issue 4795 (R47). |
| SpecKit escalation | Pass | The publication spans 82 files (R49). This record exists. |
| Multi-agent git: branch name | Fail, accepted for publication | The candidate branch does not follow `<type>/<ISSUE>-<slug>`. D-2 accepts it for this publication only. |
| Multi-agent git: one change per pull request | Fail, deferred | Pull request #4208 holds 82 files for six issues (R49, R60). D-11 defers the split. |
| Multi-agent git: closing keyword | Fail, then Pass | The body says `Refs #4795` (R49), and no `Closes #4795` exists (R48). T-PR adds the keyword. |

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/3/1/4/0/4795-gateway-history-after-refresh/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      gateway-history-route.md
      selection-resolution.md
    checklists/
      requirements.md
      security.md
```

The feature root holds five children. The `design` folder holds five children. The `contracts` folder and the `checklists` folder each hold no more than five children.

### Source Code (repository paths touched by this issue)

```text
src/interfaces/wan_performance/presentation/live_routes.py          (modify)
tests/unit/wan_performance/test_gateway_insights.py                 (modify)
tests/e2e/web_portal/test_wan_performance_live.py                   (read only)
documentation/wan-performance.md                                    (read only)
changelog.d/pr-4208.md                                              (read only)
```

## Architecture

```text
Cached snapshot (Redis)
  -> SnapshotRecords.build: port rows -> circuit records, peer rows -> peer records
  -> LivePages.render: select records for the page
  -> LiveHistory.read
       -> _select_identity: one gateway in one organization, or refusal
       -> _read_history: one history read over thirteen months
  -> summary build -> page
```

The repair stays inside the presentation layer. The collection, storage, and Mist layers receive no edit from this issue.

## File-by-File Change Map

| Path | Action | Purpose | Task |
| - | - | - | - |
| `src/interfaces/wan_performance/presentation/live_routes.py` | Modify | Extract `_read_history`, add comments and action logs, keep the messages. The repair logic already exists at head. | T003, T004 |
| `tests/unit/wan_performance/test_gateway_insights.py` | Modify | Add nine unit tests, N1 to N9, for `LiveHistory.read`. | T004, T005, T006, T007 |
| `tests/e2e/web_portal/test_wan_performance_live.py` | Verify | Keep E1 and E2. Run them under the strict environment. | T002 |
| `documentation/wan-performance.md` | Verify | Keep lines 391 and 392. | T009 |
| `changelog.d/pr-4208.md` | Verify | Keep line 19. Create no new fragment. | T010 |
| `specs/numbered/0/0/1/2/3/1/4/0/4795-gateway-history-after-refresh/` | Add | This record. | Record only |

No file is deleted. No other file changes.

## Dependencies

- Pull request #4208 and issue #4200. The repair reaches `main` only through publication of the candidate (D-2).
- Mistapi 0.64.1 in `.venv`. The change adds no dependency.
- The Chromium browser that the end-to-end tests need.

## Risks and Mitigations

- **Publication carries other defects.** The candidate holds 82 files. Mitigation: run every applicable gate on the publication head (T-LOCAL-GATES) and require CI success (T-REMOTE-CI).
- **Head drifts from the reviewed blob.** Mitigation: compare the `live_routes.py` blob before publication. Run T001 and T002 on the new head.
- **A new test passes on the defect.** Mitigation: run N1, N2, N4, N5, N6, and N8 on parent commit `07b7751` (T008). Each must fail there.
- **Closure before main verification.** Mitigation: add `Closes #4795` only after the owner decision (D-2). T-MERGE reruns E1 and E2 on `main`. If either fails, reopen the issue.
- **Skipped checks read as passed.** Mitigation: the ten skipped checks on pull request #4208 count as unknown (analysis.md F-12). T-REMOTE-CI reruns them.
- **Comments or logs change a name or a message.** Mitigation: run `symbol-diff` (T-LOCAL-GATES). Keep the exact-text assertions in N4, N6, N9, and E2.

Caution: a changed message breaks the exact-text assertions in N4, N6, N9, and E2. Revert the message change before any other fix.

## Rollback

1. Revert the publication squash commit on `main` with a new commit.
2. Confirm that the gateway page returns to its pre-publication behavior.
3. Keep the history tables that the candidate created.

Warning: dropping the candidate history tables deletes retained WAN history. Take a verified backup before any table change.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| - | - | - |
| `LivePages.render` spans 64 lines (limit 25) | The page assembly predates this issue. | Changing it now widens the diff to unrelated page code. D-12 records a separate issue. |
| Two refusal texts for one ambiguity (`read` and `window`) | The calendar view and the retained view have separate messages. | Merging them changes quoted strings. FR-009 forbids that change. |
