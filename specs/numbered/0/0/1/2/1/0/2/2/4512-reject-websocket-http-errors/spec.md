# Feature Specification: Reject WebSocket discovery HTTP errors

**Feature Branch**: `jmorrison-juniper-reject-websocket-http-errors`

**Created**: 2026-10-30

**Status**: Ready

**Input**: Repair issue #4512 without live Mist requests.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reject failed discovery data (Priority: P1)

An operator must not receive tenant or service choices from failed device requests.

**Why this priority**: Error bodies can contain plausible names that do not represent device configuration.

**Independent Test**: Inject failed responses with named tenants and services. Confirm that discovery does not store those names.

**Acceptance Scenarios**:

1. **Given** a failed configuration request, **When** discovery runs, **Then** existing device caches remain unchanged and an error is reported.
2. **Given** valid configuration and failed statistics, **When** discovery runs, **Then** configuration names remain available without statistics error names.

### User Story 2 - Preserve successful discovery (Priority: P2)

An operator must retain sorted, unique tenant and service choices from successful requests.

**Why this priority**: The repair must preserve normal service selection.

**Independent Test**: Supply successful configuration and statistics responses and compare exact cache contents.

**Acceptance Scenarios**:

1. **Given** successful requests, **When** discovery runs, **Then** valid configuration and statistics names appear once in sorted order.
2. **Given** an empty successful response, **When** discovery runs, **Then** no false failure is reported.

### Edge Cases

- Failed responses can contain valid-looking dictionaries, empty data, or sensitive error text.
- A response without a valid success status must not authorize data extraction.
- A failed statistics request must not erase valid configuration names.
- Existing transport exceptions remain nonfatal.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Reject configuration data unless the response has the expected success status.
- **FR-002**: Reject statistics data unless the response has the expected success status.
- **FR-003**: Report endpoint, site, device, and failure status without logging response bodies.
- **FR-004**: Preserve successful sorting, filtering, and duplicate removal.
- **FR-005**: Preserve nonfatal discovery behavior and existing caches when configuration retrieval fails.

### Mist Cloud Transport Requirements

Retain `mistapi.api.v1.sites.devices.getSiteDevice` and `mistapi.api.v1.sites.stats.getSiteDeviceStats`.
Use injected SDK responses in tests. Add no REST client, authentication path, or WebSocket transport.

### Key Entities

- **Device configuration**: The device tenant and service definitions.
- **Device statistics**: Additional observed service names.
- **Discovery cache**: The names available for operator selection.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Zero names from failed requests enter normal discovery caches in the regression matrix.
- **SC-002**: All successful discovery cases retain their exact expected names.
- **SC-003**: Both failed request types produce visible failure diagnostics without error-body text.

## Assumptions

- These device GET endpoints succeed with HTTP 200.
- Failed configuration retrieval continues to prevent the subsequent statistics request.
- The repair does not clear previously accepted cache entries.
- No live Mist call or production credential is necessary.
