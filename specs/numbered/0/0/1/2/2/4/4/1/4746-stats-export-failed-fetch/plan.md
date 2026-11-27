# Implementation Plan: Statistics Export Processed Count After Failed Fetch

**Branch**: `fix/4746-stats-export-failed-fetch` | **Date**: 2026-11-26 | **Spec**: `spec.md`

**Input**: Numeric specification at `specs\numbered\0\0\1\2\2\4\4\1\4746-stats-export-failed-fetch\spec.md`. The base-5 route for 4746 uses eight digits: `0\0\1\2\2\4\4\1`.

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Place supporting artifacts under `design\`.

## Summary

Both statistics exports emit a completion event with processed count 1 after `APIDataFetcher.execute()`. They emit it even when the fetch returns False. The change derives the processed count from the fetch result. It edits two methods, adds one focused test module, updates one test stub, and adds one release-note fragment.

## Technical Context

- **Language and Version**: Python 3.15 (`.github/copilot-instructions.md`, lines 18 to 20).
- **Primary Dependencies**: `mistapi` 0.64.1 is installed under `.venv`. The pin is `>=0.64.0,<0.65`. The change adds no dependency.
- **Storage**: None changed. Exports still write through `DataExporter.write_with_format_selection`.
- **Testing**: pytest. The new module reuses the stub pattern of `fake_mh` in `tests/unit/export/test_org_device_stats_exporter.py`, line 28.
- **Target Platform**: Windows 11, macOS, and Linux (`.github/copilot-instructions.md`, section "What this repository is", line 8).
- **Project Type**: Command-line menu application.
- **Performance Goals**: None. The number of Mist API calls does not change.
- **Constraints**: Five-item rule, 25-line function limit, inline comments, action logging, and ASCII log output.
- **Scale and Scope**: Two methods in one module, six new tests, one updated test, and one fragment.

## Constitution Check

Gate result before design: PASS with recorded debt. Gate result after design: PASS with the same debt.

| Rule | Status | Reason |
| - | - | - |
| Five-item rule (constitution Principle I, lines 38 to 43) | PASS with debt | The change adds no class member, no module, and no directory child. The class has 22 methods already (research RC-07). The debt is in Complexity Tracking. |
| Class-based architecture (Principle II) | PASS | The change edits methods of the existing class. It adds no wrapper function. |
| Safety-first (Principle III) | PASS | The change has no keyboard input and no destructive operation. Menus 15 and 16 use the safe category (RC-25, RC-26). |
| Full deployment pipeline (Principle IV) | PASS | Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE cover each step. The container build check runs after the merge. |
| Observability (Principle V) | PASS | New log lines use `%s` formatting and ASCII text. No secret is logged. |
| Inline comments (Principle VI) | PASS | FR-008 requires an inline comment on each touched line. |
| Action logging (Principle VII) | PASS | The new debug line follows the fetch. The existing info line precedes it. |
| mistapi as the only REST interface | PASS | The exports call SDK functions through `APIDataFetcher`. The change adds no direct HTTP request. |
| Package manager | PASS | No dependency manifest changes. |
| Container runtime and test containers | PASS, not applicable | No container runs for this change. |
| File paths | PASS | The change builds no path string. |
| Output backends | PASS | `DataExporter` stays the only write path. The change does not touch it. |
| Database keys | PASS, not applicable | No primary key strategy changes. |
| Data directory | PASS | The change writes no output file. The tests mock the exporter. |
| Testing (Development Workflow) | PASS | Five new tests fail before the fix. The module covers HTTP 4xx and HTTP 5xx cases. |
| Security findings | PASS | The change adds no finding and no suppression. |
| Documentation | PASS | No Markdown document describes these completion events (RC-61). The release-note fragment is added. |
| Complexity-driven escalation | PASS | The change touches four paths. This record is the required specification. |
| Multi-agent workflow | PASS | The branch name follows the `fix/<issue>-<slug>` form. The issue has the bug and MistHelper.py labels. No open pull request overlaps the planned files. |

## Project Structure

### Documentation (this feature)

```text
specs\numbered\0\0\1\2\2\4\4\1\4746-stats-export-failed-fetch\
  spec.md
  plan.md
  tasks.md
  analysis.md
  design\
    research.md
    data-model.md
    quickstart.md
    contracts\
      progress-complete-event.md
      fetch-result.md
    checklists\
      requirements.md
      coordination.md
```

Each folder holds five children or fewer. The root holds five children. The `design\` folder holds five children. The `contracts\` and `checklists\` folders hold two children each.

### Source Code (repository root)

| Path | Action | Change | Requirements |
| - | - | - | - |
| `src\operations\exporting\export\org_device_stats_exporter.py` | Modify | Derive the processed count from the fetch result in `device_stats` (lines 87 to 112) and `vpn_peer_stats` (lines 474 to 501). Add a debug log after each fetch. | FR-001 to FR-008 |
| `tests\unit\prod_readiness\standalone\operations\exporting\stats\test_stats_export_completion.py` | Add | Six focused tests for HTTP 403, HTTP 503, an empty response, and success | FR-009 |
| `tests\unit\prod_readiness\standalone\operations\exporting\inventory\test_menu_13_device_stats.py` | Modify | `MockFetcher.execute` returns True (line 146) | FR-010 |
| `changelog.d\issue-4746-stats-export-failed-fetch.md` | Add | One Fixed bullet | FR-011 |
| `specs\numbered\0\0\1\2\2\4\4\1\4746-stats-export-failed-fetch\` | Add | This record | Principle I unique-record exception |

Files that do not change: `tests\unit\export\test_org_device_stats_exporter.py` (reserved), `src\mist\access\api\api_data_fetcher.py`, `src\mist\intelligence\analytics\telemetry_emitter.py`, `MistHelper.py`, `src\foundation\support\utils\operation_registry.py`, `README.md`, `CHANGELOG.md`, and the `documentation\` folder.

## Architecture

The statistics export runs in five steps. A cache hit returns before step 1 and emits no event (FR-007).

```text
device_stats or vpn_peer_stats
  1. Emit progress start (label, operation name, total 1)
  2. Call APIDataFetcher.execute() and keep the fetch result
  3. Log the fetch result at debug level
  4. Set the processed count to 1 when the fetch result is True, otherwise 0
  5. Emit progress complete (processed count, was_stopped False, duration)
```

## Implementation Outline

The following block shows the required shape for `device_stats`. Each executable line carries an inline comment (FR-008). The implementer formats the block with black before the first push.

```python
        fetch_succeeded = mh.APIDataFetcher(  # Keep the fetch result that sets the processed count
            title="Org Device Stats:",  # Title printed for the operator
            api_call=mh.mistapi.api.v1.orgs.stats.listOrgDevicesStats,  # SDK call that reads device statistics
            filename=output_file,  # Output file that the exporter writes
            sort_key="type",  # Column that orders the rows
            type="all",  # Include every device type
            duration=f"{hours}h",  # Lookback window in hours
            limit=1000,  # Page size requested from the API
        ).execute()  # True only when the cloud returned rows and the export ran
        logger.debug("Device stats fetch finished with success flag %s", fetch_succeeded)  # Log the fetch result after the fetch
        processed_items = 1 if fetch_succeeded else 0  # Count one item only when the export ran
        if emitter:  # Send the completion event only when a progress emitter exists
            emitter.emit_progress_complete(  # Report completion to progress consumers
                mh.ProgressContext("13", "device_stats", 1), processed_items, False, time.time() - op_start
            )
```

The `vpn_peer_stats` method follows the same shape. Its label is `"15"`, its operation name is `"vpn_peer_stats"`, and it calls `searchOrgPeerPathStats`. Its debug text reads "VPN peer stats fetch finished with success flag %s".

The change adds two lines to `device_stats` and two lines to `vpn_peer_stats`. It adds no method, no class member, and no module-level name. The symbol check (T005) confirms this.

## Complexity Tracking

| Violation | Why needed | Simpler alternative rejected because |
| - | - | - |
| `device_stats` spans 26 lines before the change (lines 87 to 112). The 25-line limit applies. | The fix adds the processed count line and the debug log line. | A helper method adds a direct child to `OrgDeviceStatsExporter`. The class already has 22 methods (RC-07). Principle I forbids that child (RC-50). |
| `vpn_peer_stats` spans 28 lines before the change (lines 474 to 501). The 25-line limit applies. | The same as `device_stats`. | The same as `device_stats`. |
| `tests\unit\export\` holds 55 direct children on main (RC-69). | The change adds no file there. | A new file there adds a child to a noncompliant parent (RC-50). |
| `changelog.d\` holds many direct children. | The fragment is one unique record. | Principle I allows one unique record in an established process folder. |

Separate incremental remediation: file a follow-up issue to split both statistics export methods into helpers in a compliant nested module. The follow-up issue removes the two 25-line violations.

## Test Design

The new module is `tests\unit\prod_readiness\standalone\operations\exporting\stats\test_stats_export_completion.py`. It contains six tests. Before the fix, tests 1, 2, 3, 4, and 5 fail. Test 6 passes.

| No. | Test name | Setup | Expected result | Before the fix |
| - | - | - | - | - |
| 1 | `test_device_stats_http_403_reports_zero_items` | SDK stub returns status 403 | Processed count 0 and no export call | Fails on the count |
| 2 | `test_device_stats_http_503_reports_zero_items` | SDK stub returns status 503. The retry ceiling is 1 and the retry delay is 0. | Processed count 0 and no export call | Fails on the count |
| 3 | `test_device_stats_empty_response_reports_zero_items` | SDK stub returns status 200 with no rows | Processed count 0 and no export call | Fails on the count |
| 4 | `test_device_stats_success_reports_one_item` | SDK stub returns status 200 with one row | Processed count 1, one export call, and one DEBUG record "Device stats fetch finished" | Fails on the missing DEBUG record |
| 5 | `test_vpn_peer_stats_http_403_reports_zero_items` | SDK stub returns status 403 | Label "15", processed count 0, and no export call | Fails on the count |
| 6 | `test_vpn_peer_stats_success_reports_one_item` | SDK stub returns status 200 with one row | Label "15", processed count 1, and one export call | Passes |

Test setup rules:

- The fixture installs a stub `MistHelper` module in `sys.modules`. It follows the `fake_mh` pattern.
- The stub sets `PROGRESS_EMITTER` to a mock and `ProgressContext` to the real dataclass.
- The stub sets `RateLimitingUtils.get_rate_limited_delay` to return `(None, 0.0)`, because the fetcher unpacks it.
- The SDK stubs are real functions, because `APIDataFetcher` reads `__name__` for logs.
- The test patches `mistapi.get_all` for the success cases. The fetcher calls it at `src\mist\access\api\api_data_fetcher.py` line 137.
- The test patches the sleep call so that no test waits.
- The exporter stub is a mock. No test writes a file under `data\`.

## Dependencies and Ordering

- T001 runs before T002.
- T002 and T003 land in one commit. The menu 13 stub must return True when the processed count changes.
- T004 has no dependency.
- T005 runs after T002.
- T-LOCAL-GATES runs after T003, T004, and T005.
- T-PR runs after T-LOCAL-GATES and after the coordination checklist is complete.
- T-REMOTE-CI runs after T-PR. T-MERGE runs after T-REMOTE-CI and after the orchestrator authorizes the merge.

## Risks and Mitigations

| Risk | Effect | Mitigation |
| - | - | - |
| A consumer reads count 0 as an unknown state. | A dashboard misreads the result. | The contract file `contracts\progress-complete-event.md` states the rule. Consumers outside the checked folders are unknown (research U-6). |
| The #1794 slice conflicts with the edit. | Rework for both changes. | Publication waits for a recorded release (D-5). The checklist makes the wait visible. |
| The reserved test file conflicts with the owner's branch. | Rework for both changes. | The change does not edit the reserved file (C-1). |
| The menu 13 stub keeps the old behavior. | The remote check fails. | T003 lands in the same commit as T002. |
| The line-count debt grows. | Review rejects the change. | Complexity Tracking records the debt. The follow-up issue removes it. |
| A test module basename collides with another test module. | Pytest import fails. | The basename `test_stats_export_completion.py` and the `stats` folder are absent on main (RC-68). |
| Mock return values are truthy. | An old test passes for the wrong reason. | The new tests use the real fetcher. The old tests need no edit. |
| A count assertion exists outside the checked files. | A late failure in the full suite. | T-LOCAL-GATES runs the full test shards. |

## Rollback Steps

1. Before the merge, close the pull request without merging. Delete the branch and remove its worktree. Caution: Deleting the branch removes its ref. The commits stay recoverable by SHA.
2. After the merge, open a new pull request. It restores the previous method bodies and removes the new test module and the fragment. Warning: Never force-push `main`. A force push removes commits that other agents depend on.
