# Feature Specification: Statistics Export Processed Count After Failed Fetch

**Issue**: #4746
**Record**: `specs\numbered\0\0\1\2\2\4\4\1\4746-stats-export-failed-fetch`
**Feature Branch**: `fix/4746-stats-export-failed-fetch`
**Created**: 2026-11-26
**Status**: Draft
**Input**: Issue #4746, "Runtime: statistics exports report a processed item after a failed request"

## Clarifications

### Session 2026-11-26

- Q: Which menu does the issue call "menu 13"? A: The progress label "13" of `device_stats`. The registry menu for `device_stats` is 15. Decision D-6 keeps the label.
- Q: Which menu does the issue call "menu 15"? A: The progress label "15" of `vpn_peer_stats`. The registry menu for `vpn_peer_stats` is 16.
- Q: May an empty response report one processed item? A: No. The fetch returns False and writes no file. The processed count is 0 (Decision D-2).
- Q: May the fix change the fetch return contract? A: No. The contract stays unchanged (FR-006, Decision D-1).
- Q: Is the source file free for an edit? A: The issue states that the #1794 slice reserves it. Publication waits for a recorded release (Decision D-5).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Report zero items after a failed device statistics fetch (Priority: P1)

The device statistics export runs with progress label "13". The cloud returns HTTP 403 or HTTP 503, or it returns no rows. The completion event must report zero processed items.

**Why this priority**: A false count tells progress consumers that an export completed. No file exists in that case.

**Independent Test**: Run the new test module. Tests 1, 2, and 3 check the processed count for each failure. The tests use mocked responses only.

**Acceptance Scenarios**:

1. **Given** the fetch returns False, **When** `device_stats` ends, **Then** one completion event reports processed count 0 and no export call runs.
2. **Given** the fetch returns True, **When** `device_stats` ends, **Then** one completion event reports processed count 1 and one export call runs.

---

### User Story 2 - Report zero items after a failed VPN peer statistics fetch (Priority: P1)

The VPN peer statistics export runs with progress label "15". It follows the same rule as User Story 1.

**Why this priority**: The issue names both statistics exports. Both exports contain the same defect.

**Independent Test**: Run tests 5 and 6 of the new test module.

**Acceptance Scenarios**:

1. **Given** the fetch returns False, **When** `vpn_peer_stats` ends, **Then** one completion event reports processed count 0.
2. **Given** the fetch returns True, **When** `vpn_peer_stats` ends, **Then** one completion event reports processed count 1.

---

### User Story 3 - Keep the success path and the reserved files unchanged (Priority: P2)

A successful export keeps one completion event with processed count 1. A fast-mode cache hit still emits no progress event. The reserved exporter test file stays unchanged.

**Why this priority**: The fix must not remove working telemetry. The fix must not edit a file that another owner reserves.

**Independent Test**: Run the existing exporter test module and the menu 13 wiring test after the stub update.

**Acceptance Scenarios**:

1. **Given** a fresh fast-mode cache, **When** `device_stats` runs with `fast=True`, **Then** no progress event is emitted.
2. **Given** the change is complete, **When** a reviewer lists the changed files, **Then** `tests/unit/export/test_org_device_stats_exporter.py` is absent from the list.

---

### Edge Cases

- HTTP 403 from the cloud: the fetcher returns False and logs the status. The completion event reports 0. No pagination call runs.
- HTTP 503 from the cloud: the fetcher retries up to `API_REQUEST_MAX_RETRIES` times. It then returns False. The completion event reports 0.
- Empty response: the fetcher logs a warning and returns False. No file is written. The completion event reports 0.
- Unparsed response body: the fetcher returns False. The completion event reports 0.
- HTTP 429 during pagination: the pagination call raises before it assigns rows. The rate-limit branch writes nothing because no rows exist. The completion event reports 0.
- Any other exception from the fetcher: the fetcher re-raises it. No completion event is emitted. This behavior is unchanged and out of scope.
- Missing progress emitter: no progress call runs, and the fetch still runs.
- Fast-mode cache hit: the function returns before it emits any progress event.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The `device_stats` export MUST report processed count 1 only when `APIDataFetcher.execute()` returns True.
- **FR-002**: The `device_stats` export MUST report processed count 0 when `APIDataFetcher.execute()` returns False.
- **FR-003**: The `vpn_peer_stats` export MUST apply FR-001 and FR-002 to its completion event.
- **FR-004**: Each statistics export that reaches its fetch MUST emit exactly one completion event with `was_stopped` set to False.
- **FR-005**: Both statistics exports MUST keep their progress labels, operation names, and totals unchanged.
- **FR-006**: The change MUST NOT alter the `APIDataFetcher.execute()` return contract or the telemetry event fields.
- **FR-007**: A fast-mode cache hit MUST emit no progress event.
- **FR-008**: Each touched function MUST write an info log line before the fetch and a debug log line after it. Each touched line MUST carry an inline comment.
- **FR-009**: The new test module MUST cover HTTP 403, HTTP 503, an empty response, and success for each statistics export.
- **FR-010**: The existing menu 13 completion test MUST use a fetch stub that returns True, so its processed count of 1 stays tested.
- **FR-011**: The change MUST add one release-note fragment named `issue-4746-stats-export-failed-fetch.md`.

### Coordination Constraints

These constraints govern publication. They add no functional behavior.

- **C-1**: The change MUST NOT edit `tests/unit/export/test_org_device_stats_exporter.py`. Another owner reserves that file.
- **C-2**: The pull request MUST NOT open until the #1794 owner records a release of `src/operations/exporting/export/org_device_stats_exporter.py`.
- **C-3**: The change MUST follow the serial publication hold. One pull request for this change is open for merge at a time.
- **C-4**: The change MUST NOT edit `MistHelper.py`, `src/foundation/support/utils/operation_registry.py`, or `src/mist/intelligence/analytics/telemetry_emitter.py`.
- **C-5**: The implementer MUST run each applicable local gate before the first push and record each result.

Caution: An edit to the reserved test file can conflict with the owner's local branch. Both changes then need rework.

### Mist Cloud Transport Requirements

- The device statistics export calls `mistapi.api.v1.orgs.stats.listOrgDevicesStats` through `APIDataFetcher`.
- The VPN peer statistics export calls `mistapi.api.v1.orgs.stats.searchOrgPeerPathStats` through `APIDataFetcher`.
- The change adds no direct HTTP request and no owned WebSocket transport.
- The new tests mock the SDK response. The tests use no production credential.

### Key Entities

- **ProgressContext**: The identity of one operation for its progress events. Fields are `menu_option`, `operation_name`, and `total`.
- **Completion Event**: The `progress_complete` event. It carries `items_processed`, `was_stopped`, and `duration_seconds`.
- **Fetch Result**: The boolean that `APIDataFetcher.execute()` returns.

The file `design/data-model.md` defines each entity in full.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Before the fix, five of six new tests fail. After the fix, all six pass in the offline run.
- **SC-002**: Every failed or empty fetch in the new tests yields a completion event with processed count 0.
- **SC-003**: The existing menu 13 completion test passes after the stub update, with processed count 1.
- **SC-004**: The change adds no class member and no module-level name. The symbol check reports no module-level name changed.
- **SC-005**: Each applicable local gate reports its expected result before the first push.
- **SC-006**: The changelog guard test passes with the new fragment.

## Assumptions

- A processed count of 1 means one completed export. The existing code uses this meaning.
- Progress consumers read a processed count of 0 as no exported item. A local search found no consumer in the checked folders. The search covered local copies only.
- The reservations named in the issue remain valid until their owners release them.
- The OpenAPI document lists HTTP 403 and no HTTP 5xx response for both operations. The HTTP 503 case in the issue is a synthetic test input.

## Out of Scope

- The completion event after an exception that the fetcher re-raises.
- The mismatch between progress labels "13" and "15" and registry menu numbers 15 and 16.
- Splitting `device_stats` and `vpn_peer_stats` to meet the 25-line limit.
- Other exporters that emit a literal processed count. Research lists them under Unverified.
- The blind exception handlers owned by issue #1794.
- Documentation changes. No Markdown document describes these completion events.
