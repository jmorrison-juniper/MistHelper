# Feature Specification: Mist WAN Performance

**Worktree Branch**: `jmorrison-jnpr-mist-wan-performance-plan`

**Created**: 2026-10-13

**Status**: Ready for review. Implementation is not authorized.

**Input**: Plan one migration, `MistWANPerformance` into MistHelper, through specify, plan, tasks, and analyze. Stop before implementation.

**Issue**: [#4200](https://github.com/jmorrison-juniper/MistHelper/issues/4200)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Identify affected circuits (Priority: P1)

An operator opens WAN Performance from the existing portal navigation.
The overview shows circuit utilization, congestion, availability, and path quality.
The operator selects a site or gateway without losing the selected reporting period.

**Why this priority**: The overview identifies the circuits that need investigation.

**Independent Test**: Open the overview with controlled records. Verify summary values, gateway links, filters, and data-state labels.

**Acceptance Scenarios**:

1. **Given** complete records, **When** the operator opens the overview, **Then** summary cards, charts, and detail links show consistent values.
2. **Given** missing records, **When** the operator opens the overview, **Then** the page identifies missing coverage without reporting zero loss or full availability.
3. **Given** existing portal pages, **When** WAN Performance becomes available, **Then** existing navigation and routes remain unchanged.

### User Story 2 - Investigate a gateway and WAN port (Priority: P1)

An operator opens a gateway from the overview or a direct link.
The gateway page shows health, WAN ports, and peer paths.
The operator opens a WAN port to inspect utilization and receive/transmit bandwidth.

**Why this priority**: These pages identify the circuit behind a site problem.

**Independent Test**: Open gateway and port pages directly with controlled records. Verify identity, metric units, parent links, and reporting-period continuity.

**Acceptance Scenarios**:

1. **Given** a gateway and its site, **When** the operator opens the gateway, **Then** the page retains both identifiers and lists its ports.
2. **Given** a port name containing slashes, **When** the operator opens its link, **Then** the page identifies the exact port and gateway.
3. **Given** a gateway from another site, **When** the operator requests a port, **Then** the page rejects the conflicting identifiers.

### User Story 3 - Investigate a VPN peer (Priority: P2)

An operator selects a peer path to inspect packet loss, latency, jitter, and tunnel details.
The operator returns to the gateway or overview with the selected context.

**Why this priority**: Peer-path evidence distinguishes tunnel problems from circuit congestion.

**Independent Test**: Open a peer directly with controlled records. Verify quality values, tunnel details, peer identity, and return navigation.

**Acceptance Scenarios**:

1. **Given** a site and peer MAC address, **When** the operator opens the peer, **Then** the page retains the peer identity and site.
2. **Given** multiple tunnels, **When** the operator compares quality, **Then** the page separates tunnel records instead of merging unrelated paths.
3. **Given** incomplete tunnel records, **When** the operator opens the peer, **Then** unavailable metrics carry an explicit reason.

### User Story 4 - Compare historical periods (Priority: P2)

An operator compares hourly UTC measurements through daily, weekly, and monthly summaries.
The operator can identify coverage gaps and the last successful collection.

**Why this priority**: Consistent history supports repeated incident investigation.

**Independent Test**: Use controlled hour-boundary and calendar-boundary records. Verify period totals, coverage, and repeat-collection identity.

**Acceptance Scenarios**:

1. **Given** hourly records, **When** the operator selects a period, **Then** every view uses the same UTC boundaries and metric definitions.
2. **Given** a repeated hourly measurement, **When** collection repeats, **Then** history updates that measurement without adding a duplicate.
3. **Given** incomplete history, **When** the operator selects a month, **Then** the page reports measured coverage, not invented measurements.

### User Story 5 - Distinguish live, stale, and synthetic data (Priority: P1)

An operator sees whether a page contains live records, stale records, unavailable records, or synthetic historical fixtures.
Background refresh must not prevent other MistHelper operations from using the shared request allowance.

**Why this priority**: Incorrect freshness labels can produce an incorrect operational decision.

**Independent Test**: Simulate request limits, storage failure, and fixture mode. Verify status labels and the absence of uncontrolled refresh calls.

**Acceptance Scenarios**:

1. **Given** synthetic fixtures, **When** an offline page opens, **Then** every page identifies the records as synthetic and starts no live collection.
2. **Given** a refresh failure, **When** older records exist, **Then** the page shows their age and the failure reason.
3. **Given** exhausted shared request allowance, **When** a refresh becomes due, **Then** collection waits and the page reports the delay.

### Edge Cases

- Missing credentials or organization context must prevent live collection and show a configuration reason.
- Invalid identifiers, encoded separators, traversal text, and mismatched site membership must fail before a cloud request.
- Unknown gateway, port, or peer must show a not-found state without a server error.
- Empty history, late measurements, counter resets, zero bandwidth, and nonfinite values must retain explicit missing-data reasons.
- Calendar boundaries, leap days, daylight-saving changes, and partial weeks must not change UTC hour identity.
- HTTP 401, 403, 404, 429, and 5xx responses must remain distinguishable from successful empty results.
- Cache loss, corrupt cache records, database outages, and duplicate workers must not create false freshness or duplicate collection.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Provide the four source journeys inside the current portal, with shared navigation and no separate application entry point.
- **FR-002**: Preserve site, gateway, port, and peer identifiers, including source query values and tested equivalent destination links.
- **FR-003**: Preserve the source visual hierarchy, metric grouping, detail tables, and return navigation. Compare all four screens with approved reference captures.
- **FR-004**: Show utilization, congestion, availability, path quality, bandwidth, packet loss, latency, jitter, and tunnel details with explicit units.
- **FR-005**: Preserve hourly UTC records and daily, weekly, and monthly aggregation for completed source behavior.
- **FR-006**: Use one shared application database through existing configured MistHelper storage. Do not add Snowflake or another application database.
- **FR-007**: If the existing cache is reused, isolate feature keys and define expiry, serialization, ownership, coordination, and outage behavior.
- **FR-008**: Reuse the existing Mist API session, credential configuration, and portal access controls without another token store.
- **FR-009**: Share request limits between refresh, pagination, retries, and other operations. Bound concurrency and prevent duplicate background collectors.
- **FR-010**: Separate live, stale, unavailable, and synthetic states. Display UTC collection time and coverage. Never replace missing history with synthetic values.
- **FR-011**: Validate identifiers, organization membership, time windows, and measurement values before use. Redact secrets at the logging boundary.
- **FR-012**: Provide stable test selectors and automated end-to-end coverage for all four journeys, direct links, and failed navigation.
- **FR-013**: Preserve HPE Network Operations provenance. Confirm required rights before copying proprietary source code, fixtures, or visual assets.
- **FR-014**: Keep this change planning-only. Do not change runtime, portal, container, database, service, port, or credential implementation.
- **FR-015**: Investigate endpoint mappings, historical table contracts, cache keys, scheduler semantics, and export behavior before treating them as verified features.
- **FR-016**: Exclude source CLI collection and aggregation TODO stubs. Do not promise unverified export routes or long-term reporting coverage.

### Mist Cloud Transport Requirements

Use supported `mistapi` methods through the existing session.
No direct HTTP or owned WebSocket transport is proposed.
Exact method mappings remain an investigation prerequisite, not confirmed behavior.
[Research](research.md) records candidate method names from source documentation and their required verification.
Contract tests must verify explicit SDK arguments, endpoint parity, pagination, failure safety, and secret redaction before implementation approval.

### Key Entities

- **Site and gateway context**: Organization, site, and gateway identity with verified membership.
- **Circuit and peer path**: WAN port identity, capacity, peer identity, and tunnel identity.
- **Hourly measurement**: UTC hour, metric values, units, coverage, source state, and collection time.
- **Period summary**: Reporting interval, valid sample coverage, aggregate values, and calculation version.
- **Refresh state**: Collection owner, request allowance, last result, next due time, and failure reason.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All four journeys and all direct-link examples reach the correct entity and retain their parent context.
- **SC-002**: All required metrics match approved controlled records, including units and explicit missing values.
- **SC-003**: Hourly, daily, weekly, and monthly tests cover UTC boundaries and repeat collection with zero duplicate measurements.
- **SC-004**: All four pages correctly label every synthetic, stale, and unavailable scenario in automated tests.
- **SC-005**: A duplicate-worker test produces one collector per organization, with zero requests outside the shared request allowance.
- **SC-006**: Review confirms zero additional application databases, web services, public ports, or Compose groups.
- **SC-007**: All four approved screen comparisons preserve information order and navigation at the source capture size and a narrow viewport.
- **SC-008**: The planning change contains no product implementation, and every unresolved contract has an assigned investigation task.

## Assumptions

- Operators already have access through the current portal controls. These controls do not imply user authentication.
- Equivalent routes use a feature prefix because MistHelper already owns `/`. Source identity semantics remain unchanged.
- Thirty-one days describes the source cache history TTL, not a confirmed durable reporting retention contract.
- Exact calculation inputs, thresholds, weekly boundaries, tunnel identity, and supported history depth require evidence before release.
- Source documentation can describe intended behavior that the application does not complete. Investigation must distinguish those cases.
- Proprietary, internal-use licensing does not grant copying rights. Planning may proceed, but copying requires written confirmation.
- No historical Snowflake import, new database, second service, or implementation work is authorized by this task.
