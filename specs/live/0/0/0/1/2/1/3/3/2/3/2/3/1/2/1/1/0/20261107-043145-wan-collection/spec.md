# Feature Specification: WAN Collection Base

**Feature Branch**: `jmorrison-juniper-wan-collection-layer`

**Created**: 2026-11-07

**Status**: Draft

**Input**: User description: "Prepare the collection layer on a fresh main-based branch. Keep history and presentation for later serial layers."

## User Scenarios & Testing

### User Story 1 - Collect a bounded WAN snapshot (Priority: P1)

A network operator requests the latest WAN data for one organization or one selected gateway.
The collection result identifies its source and reports when the source limits the result.

**Why this priority**: Later layers need a safe and clear source for current WAN data.

**Independent Test**: Use mocked Mist responses and verify scope, limits, and completeness.

**Acceptance Scenarios**:

1. **Given** a valid organization, **When** collection returns rows, **Then** every row belongs to that organization.
2. **Given** a selected gateway, **When** collection returns rows, **Then** every row matches its site and gateway.
3. **Given** a source page is incomplete, **When** collection ends, **Then** the result marks the snapshot as partial.
4. **Given** an HTTP error or malformed response, **When** collection runs, **Then** it reports failure and does not return an empty success.

### User Story 2 - Preserve observation meaning (Priority: P1)

A network operator reviews current WAN observations without confusing absent, invalid, or zero values.

**Why this priority**: Incorrect values can hide a WAN fault or report a healthy link without evidence.

**Independent Test**: Normalize mocked port, peer, and insight rows with valid, missing, zero, and invalid values.

**Acceptance Scenarios**:

1. **Given** a valid measured zero, **When** the row is normalized, **Then** the result preserves zero and its unit.
2. **Given** an absent value, **When** the row is normalized, **Then** the result marks the value as unknown with a reason.
3. **Given** a snapshot timestamp, **When** a record receives an observation-hour key, **Then** it does not claim full-hour coverage.
4. **Given** invalid identity or tenant data, **When** a row is normalized, **Then** collection rejects the row.

### User Story 3 - Control shared collection work (Priority: P2)

A network operator receives recent cached data when another worker owns the refresh or the refresh interval remains active.

**Why this priority**: Shared control prevents duplicate requests and keeps current data available during a refresh.

**Independent Test**: Use a fake shared store to test lease ownership, cache isolation, expiry, and failure handling.

**Acceptance Scenarios**:

1. **Given** a live refresh lease for an organization, **When** another worker requests a refresh, **Then** the second worker receives a refusal.
2. **Given** a valid cached snapshot, **When** a worker reads it, **Then** it receives the snapshot without a Mist request.
3. **Given** the shared store is unavailable, **When** a worker requests a refresh, **Then** collection fails closed.
4. **Given** cached data for another organization or non-live data, **When** a worker reads it, **Then** the cache entry is rejected.

## Edge Cases

- A full page without a total count or continuation marker remains explicitly partial.
- A response that contains a row from another site or gateway is rejected.
- A peer response with duplicate hours, extra rows, or a mismatched time window is rejected.
- A missing or invalid metric stays unknown and does not become zero.
- An expired or replaced refresh lease blocks the next request.
- Redis or Mist API failures do not become empty successful snapshots.

## Requirements

### Functional Requirements

- **FR-001**: The collection service MUST accept one valid organization and an optional gateway scope.
- **FR-002**: The collection service MUST apply a fixed maximum to each source page and MUST report incomplete results.
- **FR-003**: The collection service MUST reject rows that do not match the requested organization, site, or gateway.
- **FR-004**: The collection service MUST preserve source identities and MUST NOT replace them with generated identity values.
- **FR-005**: The collection service MUST preserve measured zero values and MUST represent missing values with an explicit reason.
- **FR-006**: The collection service MUST reject non-finite or invalid metric values.
- **FR-007**: The collection service MUST keep current status metadata separate from numeric measurements.
- **FR-008**: The collection service MUST NOT claim complete-hour coverage from a point-in-time snapshot.
- **FR-009**: The collection service MUST use a shared admission check before each Mist API request.
- **FR-010**: The collection service MUST refuse refresh work when shared admission or its lease is unavailable.
- **FR-011**: The collection service MUST cache only complete, live snapshots for their matching organization.
- **FR-012**: This layer MUST exclude durable history, dashboard routes, templates, and visual presentation.

### Mist Cloud Transport Requirements

- The collector MUST use the `mistapi` methods `searchOrgSwOrGwPorts`, `searchOrgPeerPathStats`, `listOrgDevicesStats`, `listInsightMetrics`, and `getSiteInsightMetricsForGateway`.
- The collector MUST pass the existing authenticated Mist session to each method.
- The collector MUST NOT call a Mist REST endpoint through a separate direct HTTP client.
- This layer does not require an owned WebSocket transport.
- Mocked contract tests MUST verify SDK method arguments, authenticated session use, bounded results, failure handling, and refusal before transport when admission fails.

### Key Entities

- **WAN Snapshot**: A live collection result with an organization, collection time, source rows, and completeness state.
- **WAN Identity**: The source organization, site, gateway, port, or peer-path values that locate an observation.
- **Metric Observation**: A finite value with its unit, sample count, coverage, or explicit missing reason.
- **Refresh Lease**: A time-limited owner record that controls one organization's current refresh.
- **Current Status**: Source status metadata that remains distinct from numeric metrics.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Every accepted row in the test set matches the requested organization and any selected gateway.
- **SC-002**: Every incomplete source page produces a partial snapshot.
- **SC-003**: Every missing or invalid metric in the test set remains unknown rather than becoming zero.
- **SC-004**: Every refresh refusal in the test set prevents a Mist request.
- **SC-005**: The collection tests pass without live Mist credentials or production requests.

## Assumptions

- The operator has selected an organization and, when needed, a gateway before collection starts.
- The Mist API is the source of truth for live observations.
- The cache supports current snapshots only. A later layer owns durable history.
- A later presentation layer owns operator pages and dashboard interaction.
- Tests use mocked Mist responses and a fake shared store.
