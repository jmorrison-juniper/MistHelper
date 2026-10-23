# Feature Specification: Reject failed beacon responses

**Feature Branch**: `jmorrison-juniper-menu-209-http-error-export`

**Created**: 2026-10-23

**Status**: Ready

**Input**: Issue #4028 reports that menu 209 exports an HTTP 404 error body as beacon data.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Report a failed beacon request (Priority: P1)

An operator requests a beacon that does not exist. The operation reports the failure without writing an export.

**Why this priority**: An error row gives the operator a false success result.

**Independent Test**: Return a simulated missing-beacon response. Check the failure message and absence of an export.

**Acceptance Scenarios**:

1. **Given** a missing beacon, **When** the service returns HTTP 404, **Then** the operation reports the failure and writes zero rows.
2. **Given** a server failure, **When** the service returns HTTP 503, **Then** the operation reports the failure and writes zero rows.

### User Story 2 - Preserve successful requests and retries (Priority: P2)

An operator exports a valid beacon. A temporary rate limit uses the existing bounded retry procedure.

**Why this priority**: The repair must preserve valid exports.

**Independent Test**: Simulate success, temporary rate limits, and exhausted retries.

**Acceptance Scenarios**:

1. **Given** a successful response, **When** the operator requests the beacon, **Then** the existing filename, rows, and endpoint metadata remain unchanged.
2. **Given** a rate limit followed by success, **When** the request retries, **Then** the operation uses the existing delay and exports once.
3. **Given** repeated rate limits, **When** the retry limit expires, **Then** the operation reports failure without an export.

### Edge Cases

- A redirect must not become a beacon row.
- An empty successful response retains the existing no-data behavior.
- Raw response mappings retain their existing behavior.
- Existing exception-based rate limits retain their retry behavior.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Menu 209 MUST reject a returned integer status outside HTTP 200 through 299 before processing the body.
- **FR-002**: A rejected response MUST produce the existing user-facing failure message with its HTTP status.
- **FR-003**: A failed request MUST NOT write an export or report an export success.
- **FR-004**: Returned HTTP 429 responses MUST use the existing bounded adaptive retries.
- **FR-005**: Successful responses and existing exception behavior MUST remain unchanged.

### Mist Cloud Transport Requirements

The operation uses `mistapi.api.v1.sites.beacons.getSiteBeacon` with the existing session and explicit identifiers.
Tests use local response doubles. The installed SDK source defines the response contract. No test calls the Mist cloud.
The repair adds no transport, authentication path, or payload logging.

### Key Entities

- **Beacon response**: The service status and the beacon data or error body.
- **Export**: Beacon rows with the existing filename and endpoint metadata.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every simulated failed status writes zero rows and produces zero export-success messages.
- **SC-002**: Every simulated successful beacon response writes the expected rows exactly once.
- **SC-003**: Rate-limit retries stop at the configured limit and use the existing delay.

## Assumptions

- The existing public failure path is the required user-facing behavior. Portal state handling remains outside this repair.
- Existing raw mappings remain supported. The repair does not infer HTTP status from body text.
- The installed SDK contract is authoritative: `status_code` holds the HTTP status and `data` can hold an error body.
