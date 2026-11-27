# Implementation Plan: Firmware Monitor Treats Failed Stats Pages as Failed Checks

**Branch**: `fix/4710-firmware-monitor-failed-pages` | **Date**: 2026-11-26 | **Spec**: `spec.md`

**Input**: Numeric specification from `/specs/numbered/0/0/1/2/2/3/2/0/4710-firmware-monitor-failed-pages/spec.md`.

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Research, data model, quickstart, contracts, and checklists are under `design/`.

## Summary

Change one method in the grandfathered module `src/operations/execution/firmware/firmware_manager.py`. The method `_fetch_device_stats_for_monitoring` walks every stats page through `mistapi.get_next`. It checks the HTTP status and the body of each page. It checks the announced row total. It guards against a repeated next link. A failed page raises an exception. The existing status-check failure path and retry policy handle that exception. No exit code, cadence, menu, or confirmation changes.

## Technical Context

**Language/Version**: Python 3.15 or newer. `pyproject.toml` line 23 sets `requires-python = ">=3.15"`.

**Primary Dependencies**: `mistapi` 0.64.1, installed under `.venv\Lib\site-packages\mistapi`. `requirements.txt` line 129 pins `mistapi==0.64.1`. `pyproject.toml` line 29 allows `>=0.64.1,<0.65`.

**Storage**: None changed. The monitor reads stats and writes no product output.

**Testing**: pytest. The test module is `tests/unit/firmware/test_firmware_manager_monitoring.py`. Each test runs offline with mocked SDK responses.

**Target Platform**: Windows 11, macOS, and Linux.

**Project Type**: Menu-driven command-line tool. The change affects menu 137, scope 5.

**Performance Goals**: The walk requests one page for each 1000 device rows (`limit=1000`). The request count matches the current `mistapi.get_all` walk.

**Constraints**: Five-item rule (`constitution.md` lines 38 to 88). Function limits of 25 lines, 5 logical blocks, and 5 parameters. ASCII log text. No secret in output.

**Scale/Scope**: One method, two existing test classes plus one retry test class, 14 new tests, 2 updated tests, and one changelog fragment.

## Constitution Check

| Principle | Result | Reason |
| - | - | - |
| I. Five-Item Rule (`constitution.md` line 38) | Pass with recorded debt | The change edits one existing method. It adds no direct child, module, class, method, or constant. The parent folder `firmware/` already has 12 children. The debt is recorded in the Five-Item Record below. |
| II. Class-based architecture (`constitution.md` line 91) | Pass | The change adds no wrapper function. The method stays in class `FirmwareManager`. |
| III. Safety-first (`constitution.md` line 113) | Pass | No confirmation rule changes. Menu 137 is not destructive (`MistHelper.py` line 5202). The failure text holds no secret. |
| IV. Full deployment pipeline (`constitution.md` line 143) | Pass by plan | Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE run the pipeline. No task pushes to `main`. |
| V. Observability and logging (`constitution.md` line 182) | Pass by plan | Log text is ASCII. The walk logs `info` before each request, `debug` after each result, and `error` through the existing `logging.exception` call. |
| VI. Inline comments (`constitution.md` line 204) | Pass by plan | Each changed executable line gets an inline comment that gives its cause or purpose. |
| VII. Action logging (`constitution.md` line 235) | Pass by plan | FR-012 and test N13 prove the log lines. |
| Technology: mistapi only (`constitution.md` line 279) | Pass | The calls use `listOrgDevicesStats`, `listSiteDevicesStats`, and `get_next`. No direct HTTP request is added. |
| Technology: paths, containers, data directory, push | Not applicable | The change adds no path handling, container, data file, or push. |
| Output backends and operational store | Not applicable | The monitor writes no export and holds no coordination record. |

Mist Cloud check: every REST request uses a working mistapi method. Test N14 shows that the SDK `get_all` path hides a failed page. That result is the insufficiency evidence.

## Five-Item Record

- Existing violation 1: `src/operations/execution/firmware/firmware_manager.py` holds 4,365 lines (remote decode, research R-06). Its parent folder `firmware/` holds 12 children.
- Existing violation 2: class `FirmwareManager` (line 192) holds far more than five methods. Method definitions appear from line 318 through line 4,341 and later.
- Existing violation 3: test module `tests/unit/firmware/test_firmware_manager_monitoring.py` holds many test classes. Its parent folder `tests/unit/firmware/` holds 9 children.
- New code limit: the changed method holds 24 lines, 5 logical blocks, and 2 parameters after the change.
- Remediation action R-01: move the stats page walk into a compliant nested package. The remediation is a separate issue. It is not part of this pull request. Its entry condition is a compliant parent folder with room for one child.

## Architecture

The call chain for the change follows. The changed step is marked.

```text
Menu 137 (MistHelper.py lines 5192 to 5202)
  -> FirmwareManager.check_firmware_upgrade_status (firmware_manager.py line 318)
  -> _dispatch_status_scope, scope 5 (firmware_manager.py lines 363 to 369)
  -> _continuous_monitoring_mode (line 377) -> _run_monitoring_loop (line 417)
  -> _execute_monitoring_check (line 702)
  -> _fetch_device_stats_for_monitoring (line 637)        [changed]
  -> mistapi.api.v1.orgs.stats.listOrgDevicesStats        (org branch, first page)
     or mistapi.api.v1.sites.stats.listSiteDevicesStats   (site branch, first page)
  -> mistapi.get_next                                      (each later page)
```

The menu does not use the exit code. `_dispatch_status_scope` drops the value of `_continuous_monitoring_mode` (lines 367 to 369). The operator sees console text only. A scripted caller of `_continuous_monitoring_mode` sees the exit code.

## Implementation Outline

The changed method works in this order:

1. Log an `info` line that names the scope and the site filter.
2. Request the first page with the existing org or site call. Keep the arguments unchanged.
3. Read the page. If the status is not the integer 200, or the body is not a list, raise `RuntimeError` with the status only.
4. Log a `debug` line with the status and the row count. Add the rows to the result.
5. If the page has no next link, stop the walk.
6. If the next link repeats, raise `RuntimeError`. Otherwise record the link.
7. Request the next page with `mistapi.get_next`. Log an `info` line before the request. Return to step 3.
8. After the last page, read `X-Page-Total` from the last page headers. If the header is present and the row count is lower, raise `RuntimeError`. A non-integer header raises `ValueError`.
9. Log a `debug` line with the row count. Return the rows.

The status check already catches `Exception` (`firmware_manager.py` line 722). It returns no count. The retry policy then counts the failure through `record_failure` (line 163) and sets the wait through `next_delay_seconds` (line 177).

## Contracts

Two contracts apply. They are `design/contracts/stats-page-walk.md` and `design/contracts/monitor-exit-codes.md`. The menu contract does not change. The scope prompt and the menu 137 wording do not change.

## File-by-File Change Map

| Action | Repository path | Change |
| - | - | - |
| Modify | `src/operations/execution/firmware/firmware_manager.py` | Rewrite the body of `_fetch_device_stats_for_monitoring` (lines 637 to 647). Change no other line. |
| Modify | `tests/unit/firmware/test_firmware_manager_monitoring.py` | Update tests U1 and U2 (fetch doubles at lines 637 to 690). Add tests N1 to N14 to the existing classes for fetch, status check, and loop retry. |
| Create | `changelog.d/issue-4710-firmware-monitor-failed-pages.md` | One release-note fragment for the user-visible change. The folder `changelog.d/` is an established process folder (`constitution.md` line 47). |
| Not changed | `MistHelper.py`, `operation_registry.py`, `pyproject.toml`, `requirements.txt`, `README.md`, `documentation/*` | No menu, registry, pin, or operator text changes. Research item RC-23 shows that no operator document names the exit behavior. |

## Dependencies

No new package is added. The installed `mistapi` 0.64.1 provides every function that the change calls. The tests use `pytest` and `monkeypatch`, which the test module already uses.

## Risks and Mitigations

1. The strict list check rejects a valid body from the site endpoint. The site response references the `stats_devices` array schema (research RC-21). If the live body differs, the status check fails. It does not report completion. The residual risk is a site watch that never completes. Follow-up F-03 covers it.
2. The meaning of `X-Page-Total` differs from the SDK reading. The SDK treats the value as an item total (`__api_response.py` line 84). Research item U-02 records that no live response was checked. Test N7 uses the SDK meaning.
3. A server race announces a larger total than the rows returned. The status check fails and the retry path runs. The operator sees `Error fetching upgrade status.` The failure is visible.
4. The change adds log lines to each check. Each line carries a count or a status. No line carries a response body.
5. Test doubles drift from the SDK types. Test N14 builds responses through the installed SDK `APIResponse` class. The updated doubles use the same attribute names.
6. The grandfathered file grows. The change keeps every edit inside one method. Symbol gate SC-004 proves that no module-level name changes. Remediation R-01 removes the debt.
7. The human review gate is bypassed. Task T-MERGE forbids `auto-merge` while the label `needs-human-review` remains.

Caution: a stopped monitor does not stop the firmware upgrade. The operator must restart the monitor after the cause is fixed.

## Rollback Steps

1. Open a revert pull request for the squash commit on `main`. Do not push to `main` (`AGENTS.md` Merge section, line 233).
2. The revert restores the previous `mistapi.get_all` call. The change writes no data, so no data cleanup is needed.
3. The revert removes the changelog fragment with the code change.

## Complexity Tracking

| Violation | Why it is needed | Simpler alternative rejected because |
| - | - | - |
| The change edits the grandfathered module `firmware_manager.py`. | The only code path for the monitor is in that module. The parent folders `firmware/` (12 children), `execution/` (6 children), `operations/` (5 children), and `mist/` (5 children) cannot take a new child. | A new module under `firmware/` adds a direct child to a noncompliant parent. The constitution forbids it. |
| New tests go into existing test classes in the grandfathered test module. | Each change carries its tests (`AGENTS.md` line 133). The folder `tests/unit/firmware/` holds 9 children. | A new test module adds a direct child to a noncompliant parent. The reserved test module (issue comment of 2026-11-09) is the agreed location. |
| The page walk runs inside one method with five logical blocks. | The method stays near its caller and within the function limits. | A new helper method adds a direct child to the noncompliant class `FirmwareManager`. |
