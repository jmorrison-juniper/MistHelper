# Feature Specification: Per-port Mist Insights parity in the WAN dashboard

**Feature Branch**: `feat/4330-per-port-mist-insights-parity`

**Created**: 2026-11-26

**Status**: Draft

**Input**: User description: "Define whether and how the canonical MistHelper WAN dashboard can provide per-port Mist Insights parity." Issue #4330.

## Summary

This feature adds the seven-day hourly rate series for each WAN port to the existing WAN dashboard. The refresh worker reads the series. The dashboard routes stay cache-only. The feature uses the pinned mistapi SDK and the shared request admission path. It adds no portal, cache writer, database, service, or published port.

## Terms

- **WAN dashboard**: The existing dashboard at `/wan-dashboard`, served by `src/interfaces/portals/wan_dashboard/`.
- **Port series**: The hourly `rx_bps` and `tx_bps` samples for one WAN port over seven days.
- **Port totals**: The seven-day RX and TX byte totals derived from one port series.
- **Port view**: The per-port detail that shows the port series and port totals.
- **Data state**: One of `live`, `stale`, `partial`, or `unavailable`.
- **Request cap**: The operator setting `WAN_PORT_INSIGHT_REQUEST_CAP`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read seven-day port traffic (Priority: P1)

An operator opens one WAN port in the WAN dashboard. The port view shows hourly RX and TX rates for seven days. It also shows the port totals, the data state, and the UTC collection time.

**Why this priority**: This closes the per-port gap that issue #4220 excluded. Operators receive the value that the source tool provides.

**Independent Test**: Load a mocked bulk snapshot and one mocked port series. Open the port view. Check the rates, totals, data state, and time. Covered by TC-18 to TC-20.

**Acceptance Scenarios**:

1. **Given** a complete mocked port series, **When** the operator opens the port view, **Then** the view shows the samples, totals, state, and UTC time.
2. **Given** a port series with a `next` link, **When** the operator opens the port view, **Then** the view shows state `partial` and the coverage fraction.
3. **Given** no cached port series, **When** the operator opens the port view, **Then** the view shows state `unavailable` and the route makes no Mist request.

---

### User Story 2 - Read port series inside a fixed request budget (Priority: P2)

A maintainer sets the request cap. The refresh worker reads at most that many WAN ports in each refresh. The worker skips the phase when the cap is unset or zero.

**Why this priority**: One request for each port multiplies the request count. Each token has a shared limit of 5,000 calls per hour.

**Independent Test**: Run the worker with a mocked port list and a cap. Count the SDK calls. Covered by TC-10, TC-11, TC-17, and TC-24.

**Acceptance Scenarios**:

1. **Given** the request cap is unset, **When** a refresh runs, **Then** the worker makes no port series call and reports the phase as disabled.
2. **Given** the cap is 3 and 10 ports exist, **When** a refresh runs, **Then** the worker makes 3 calls.
3. **Given** the planned calls exceed the headroom, **When** a refresh starts, **Then** the worker stops before the first port series call.

---

### User Story 3 - Verify the SDK contract and provenance (Priority: P3)

A reviewer checks the request arguments, response keys, units, timestamps, port identity, and source provenance. Each check uses local evidence and the remote tree.

**Why this priority**: The OpenAPI file and the canonical code name the response keys in different ways. A reviewer must resolve that conflict before release.

**Independent Test**: Run the SDK contract tests with mocked responses. Covered by TC-01 to TC-06.

**Acceptance Scenarios**:

1. **Given** the pinned SDK, **When** the contract test builds a port series request, **Then** the call carries `port_id`, `metrics`, `interval`, `limit`, `page`, `start`, and `end`.
2. **Given** a malformed response, **When** the contract test parses it, **Then** the parser rejects the response with an explicit state.

### Edge Cases

- A response has a `next` value. The port series becomes `partial`.
- A response has fewer than 168 samples. The port series becomes `partial`.
- A timestamp lies outside the window or is not on a UTC hour. The response is rejected as malformed.
- A rate value is negative, not finite, or a boolean. That sample becomes absent.
- A port has neither `port_id` nor `name`. The port is skipped and counted as unavailable.
- Mist returns HTTP 429. The runner makes one attempt for each token and starts the 60-second cooldown.
- Mist returns HTTP 4xx or 5xx. The state reflects the status code, and no empty success is published.
- Redis is unavailable. The local last complete value applies only within the stale age limit.
- The worker loses its lease during the phase. The phase stops before the next request and publishes nothing from that phase.
- Shared admission refuses a site-scoped request without a tenant context. The read fails closed before transport.
- The WAN port list changes between refreshes. The cursor wraps, and the list is sorted again.
- A port name contains a slash, for example `ge-0/0/1`. The port identifier pattern accepts it.

### Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST read each port series only through the SDK method `getSiteInsightMetricsForGateway` with `port_id` set.
- **FR-002**: System MUST request `rx_bps` and `tx_bps` at a one-hour interval for seven days ending at the latest completed UTC hour.
- **FR-003**: System MUST request one page of up to 168 samples. System MUST mark the port series partial when `next` is present or the count is short.
- **FR-004**: System MUST read port series only in the refresh worker. A dashboard route MUST NOT call Mist.
- **FR-005**: System MUST read at most the request cap of WAN ports in each refresh. An unset or zero cap disables the phase.
- **FR-006**: System MUST send each request through the shared Mist session and the shared request admission. System MUST NOT use direct HTTP.
- **FR-007**: System MUST make one SDK attempt for each token and each logical read. System MUST NOT allow SDK retries after HTTP 429.
- **FR-008**: System MUST derive each seven-day byte total as the floor of the sum of bits per second times 3600, divided by 8.
- **FR-009**: System MUST report coverage as present samples divided by 168. System MUST mark a port series below full coverage as partial.
- **FR-010**: System MUST show one data state and the UTC collection time for each port view. The states are `live`, `stale`, `partial`, and `unavailable`.
- **FR-011**: System MUST keep a missing sample absent. System MUST NOT replace a missing sample with zero.
- **FR-012**: System MUST validate the response object, window, interval, arrays, and timestamps. System MUST reject a malformed response with an explicit state.
- **FR-013**: System MUST label the overview RX and TX values as cumulative counters since the last device reboot.
- **FR-014**: System MUST keep the refresh queue, the refresh button, and the synthetic example behavior unchanged.
- **FR-015**: System MUST NOT add a portal, cache writer, database, service, or published port.
- **FR-016**: System MUST NOT copy source code, tests, fixtures, screenshots, or assets from the source repository.
- **FR-017**: System MUST NOT write tokens, cookies, credential-bearing URLs, or response bodies to logs or errors.

### Key Entities *(include if feature involves data)*

- **WAN port**: One WAN port on one gateway. The natural key is the gateway MAC address and the `port_id`.
- **Port series**: Up to 168 hourly samples for one WAN port. The natural key is the organization, the gateway device, the `port_id`, and the UTC hour.
- **Port totals**: The seven-day RX and TX bytes, the coverage, the sample count, and the state for one WAN port.
- **Request budget**: The request cap, the planned calls, the refresh interval, and the skip reason for one refresh.
- **Cursor**: The rotation index into the sorted list of WAN ports.

### Mist Cloud Transport Requirements

- The feature uses one SDK method: `mistapi.api.v1.sites.insights.getSiteInsightMetricsForGateway`.
- The bulk snapshot keeps its existing SDK methods. The feature adds no new Mist endpoint.
- No owned WebSocket transport is required. Contract tests prove that the SDK method carries every required argument (TC-01).
- SDK authentication uses the existing shared session. A contract test pins the installed SDK version (TC-02).
- Endpoint parity: the request path is `/api/v1/sites/{site_id}/insights/gateway/{device_id}/stats` (R-37).
- Failure safety: HTTP 429, HTTP 4xx, HTTP 5xx, transport errors, and malformed bodies map to explicit states (TC-04 to TC-06).
- Secret redaction: logs and errors carry no token, cookie, or response body (TC-22).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 25 planned tests pass in the local gates before the pull request opens.
- **SC-002**: In every budget test, the worker makes no more port series calls than the request cap.
- **SC-003**: In every browser test, each port view shows one data state and one UTC collection time.
- **SC-004**: In every route test, the dashboard routes make zero SDK calls.
- **SC-005**: Before production enablement, the record holds measured site, gateway, and port counts from an authorized scope.
- **SC-006**: In the browser test, the overview copy contains no seven-day claim for RX and TX counters.

## Assumptions

- The pinned mistapi 0.64.1 stays installed for this change (R-47).
- The operator sets the refresh interval outside the code (R-19).
- The number of tokens in production is unknown (U-4).
- The source repository is a reference only. No source text enters the product.
- The owner work on the admission module is coordinated before any edit (D-12).
- Validation makes no live Mist call.

## Clarifications

### Session 2026-11-26

- Q: Which WAN dashboard owns the parity work? A: The canonical dashboard under `/wan-dashboard` (D-1).
- Q: Are authorized production counts available? A: No. The owner states that the available account has validation scope only (comment of 2026-11-08T17:41:01Z). The production budget stays unmeasured (D-14).
- Q: May source material enter the product? A: No copy is allowed. The work uses a clean-room implementation. The attribution text needs human approval (D-11).

## Out of Scope

- Link health and SLE insights. Their existing behavior does not change.
- Any live Mist call during this specification or its validation.
- Edits to the files that pull request #4208 changes, until its decision (D-12).
- Export column changes. The hourly CSV keeps its current columns.
- Production enablement of the port series phase (D-14).
