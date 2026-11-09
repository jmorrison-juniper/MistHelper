# Implementation Plan: Long packet capture

**Branch**: `jmorrison-juniper-issue-3575-long-packet-capture` | **Date**: 2026-11-07 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification at `specs/numbered/0/0/1/0/3/3/0/0/3575-long-packet-streams/spec.md`.

## Summary

Add a checked duration field to the existing packet capture utilities. Keep the
current utility runner, stream client, subscription order, capture identifier
filter, and cloud cleanup. Make the monitor ignore first-output and quiet limits
for captures, then finish on the requested duration or a matching capture-end
event. Extend only the capture session life limit.

Do not transplant the recovery branch's separate transport. Its source paths
pre-date the current package move. The current runner already subscribes before
the REST start request and uses the existing Mist API session for REST calls.

## Technical Context

**Language/Version**: Python 3.13 or newer.

**Primary Dependencies**: Existing `mistapi`, Flask, and Playwright packages.
No dependency change.

**Storage**: Existing in-memory WebSocket session buffers.

**Testing**: pytest with `FakeMistCloud`, controlled clocks, Flask test clients,
and the existing local Playwright fixtures.

**Target Platform**: Existing macOS, Windows, Linux, and Podman deployments.

**Project Type**: Existing Python web application with a browser interface.

**Performance Goals**: Accept capture durations from 60 through 3600 seconds.
Keep capture processing bounded by the current session, memory, packet, and
idle limits.

**Constraints**: Start only after subscription confirmation. Start the monitor
duration after the successful capture response. Ignore quiet periods for
captures. Keep a ten-second stream completion margin and a bounded cleanup
margin of 30 seconds beyond the selected capture duration. Do not extend
non-capture sessions.

**Scale/Scope**: The seven existing packet capture utilities. Do not change
other utilities, channel streams, shell sessions, menu operations, packet
limits, or database schemas.

## Constitution Check

*GATE: Pass before implementation, subject to the listed validation evidence.*

- **Managed records**: The specification uses the eight-segment base-5 route.
  The executable route guard passes all 40 tests with checksum-verified
  portable PowerShell 7.6.9. The current worktree branch is already prepared, so do not run
  the branch-creation hook.
- **Feature pointer**: `.specify/feature.json` points to issue #4258. Leave it
  unchanged. Use explicit feature paths for this work.
- **Five-item rule**: Add no source package or source directory. Keep plan
  inputs at the feature root and supporting records under `design/`. The
  feature root has four children. The `design/` directory has five children or
  fewer.
- **Process-folder debt**: The issue-specific changelog fragment is the only
  new direct child under `changelog.d/`. Existing process-folder debt remains
  governed by `tests/guardrails/process_folder_baseline.json`. Track baseline
  reduction in a separate maintenance action.
- **Class and method limits**: Add no more than five parameters to a method.
  Keep new methods at 25 lines or fewer and five logical blocks or fewer.
  Avoid a general refactor of existing classes.
- **Mist transport**: Add no REST endpoint or WebSocket transport. Reuse the
  current SDK session, `UtilityRunner`, and `StreamClient`. Existing trigger
  parity and subscribe-order tests verify the contracts.
- **Safety and logging**: Keep target checks, capture ID checks, regional
  authentication, secret redaction, and structured logs. Use only fake or
  mocked cloud responses in tests.
- **Publication**: Run applicable local gates and keep the result local. Do not
  push, create a pull request, merge, or enable auto-merge without a serial
  publication slot.

## Project Structure

### Documentation

```text
specs/numbered/0/0/1/0/3/3/0/0/3575-long-packet-streams/
  spec.md
  plan.md
  tasks.md
  design/
    checklists/requirements.md
    contracts/capture-session.md
    data-model.md
    quickstart.md
    research.md
```

### Source Code

```text
src/mist/realtime/websocket_streams/
  catalog/
    model.py
    utilities/metadata/utility_text.py
    utilities/utility_fields.py
  intake/fields/scalar_checker.py
  live/runners/utility/
    filters/message_filter.py
    filters/payload_matcher.py
    runner/capture.py
    runner/execution.py
    runner/monitoring.py
    runner/utility_runner.py
    triggers/body_builder.py
    triggers/table.py
  live/sessions/
    manager/lifecycle.py
    settings.py
  web/services/assembly/fallback.py

tests/
  contract/websocket_streams/test_ws_utility_trigger_parity.py
  e2e/websockets_tab/test_websockets_page.py
  unit/websocket_streams/catalog/
  unit/websocket_streams/intake/test_ws_field_checker.py
  unit/websocket_streams/live/runners/utility/test_ws_utility_runner.py
  unit/websocket_streams/live/runners/utility/test_ws_utility_triggers.py
  unit/websocket_streams/live/sessions/
changelog.d/issue-3575-long-packet-streams.md
documentation/wiki/Web-Portal.md
```

**Structure Decision**: Edit the current `src/mist/realtime/websocket_streams/`
packages. Do not restore the retired top-level WebSocket package or add a
second capture runner.

## Design Decisions

1. Add `duration` to the existing capture catalog fields with a 60-second
   default and a 60-to-3600-second range.
2. Reject non-ASCII, non-decimal, and oversized integer input before conversion.
3. Keep the existing capture request builder and its ten-second stream margin.
4. Start the capture monitor clock after the REST start response succeeds.
5. Disable first-output and quiet-time completion only for packet captures.
6. Treat a matching `pcap_dict: null` event as normal capture completion.
7. Check the active status object at `/pcaps/capture` before a scope-wide stop
   at that endpoint. Report an identity mismatch or an unconfirmed stop as failure.
   The status check cannot prevent replacement between the two requests.
8. Extend the session life limit only to `max(configured limit, duration + 30
   seconds)` after the first successful trigger response for captures. Bound
   capture setup with the configured generic limit. Keep idle cleanup and
   every non-capture limit unchanged.

## Complexity Tracking

| Existing constraint | Reason for the narrow edit | Separate remediation |
| - | - | - |
| Catalog, scalar checker, monitor, and session manager are established modules. | They own the current field, validation, timing, and retention contracts. | Split each module only in a separate maintenance issue. |
| The recovery branch has an obsolete flat spec path and source package. | Reusing those paths would violate the managed route and current package layout. | Keep the recovery branch as evidence. Do not modify or delete it. |
| Process-folder baseline entries pre-date this feature. | The feature adds only its required unique changelog fragment. | Reduce one grandfathered entry in a separate maintenance action. |

## Local Verification

Use the focused unit, contract, and browser tests listed in `tasks.md`. Run
Ruff, Black, mypy, and the applicable guardrails for every changed Python file.
Use no live Mist credentials, external cloud requests, or production data.
Complete the test-quality ratchet after the local commit and before any
publication. The current task ends before publication.
