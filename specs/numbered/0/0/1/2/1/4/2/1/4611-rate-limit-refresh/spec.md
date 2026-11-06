# Feature Specification: Preserve Rate-Limit State on HTTP Failure

**Feature Branch**: `jmorrison-juniper-http-4xx-test-quality-campaign`

**Created**: 2026-11-06

**Status**: Draft

**Input**: User description: "Reject failed SDK responses without resetting valid cached rate-limit state, add focused native-response tests for 4xx, 5xx, and success. Do not make live Mist requests."

## User Scenarios & Testing

### User Story 1 - Preserve the Last Valid Quota (Priority: P1)

When the Mist usage request fails, an operator needs the rate limiter to retain the last valid usage values so later operations do not use false quota data.

**Why this priority**: Incorrect quota data can change request pacing and hide an API refusal.

**Independent Test**: Supply local SDK responses with client and server failure statuses and a realistic usage body. Verify that every cached value remains unchanged and that the failure is logged.

**Acceptance Scenarios**:

1. **Given** a valid initialized cache, **When** the usage request returns HTTP 403 with a usage-shaped body, **Then** the cache remains unchanged and the refresh failure is logged.
2. **Given** a valid initialized cache, **When** the usage request returns HTTP 503 with a usage-shaped body, **Then** the cache remains unchanged and the refresh failure is logged.

### User Story 2 - Refresh Quota After Success (Priority: P2)

When the Mist usage request succeeds, an operator needs the rate limiter to use the newest usage values.

**Why this priority**: A successful refresh must continue to update request pacing from current quota data.

**Independent Test**: Supply a local successful SDK response with a valid usage body. Verify that the cache contains the returned usage, limit, refresh time, and reset request count.

**Acceptance Scenarios**:

1. **Given** an initialized cache, **When** the usage request returns a successful response with valid usage data, **Then** the cache records the new data and refresh time.

### Edge Cases

- When the SDK response has no underlying HTTP response, the refresh must preserve the cache and report failure.
- When a failure body contains realistic usage fields, the refresh must not treat those fields as successful quota data.
- When the SDK raises an exception, the refresh must preserve the cache as it does now.
- Tests must not contact the Mist service.

## Requirements

### Functional Requirements

- **FR-001**: The rate limiter MUST accept usage data only from a successful HTTP response.
- **FR-002**: The rate limiter MUST preserve every existing cached value when the usage response fails.
- **FR-003**: The rate limiter MUST report a failed refresh without logging credentials or response payloads.
- **FR-004**: The rate limiter MUST update usage values and refresh metadata after a successful response.
- **FR-005**: Tests MUST verify client failure, server failure, and success with local native SDK response objects.
- **FR-006**: Tests MUST NOT make a live Mist request.

### Mist Cloud Transport Requirements

- The existing REST method is `mistapi.api.v1.self.usage.getSelfApiUsage`.
- This feature adds no transport and sends no direct HTTP request.
- Local response tests must preserve the SDK authentication and endpoint contracts.
- Tests must prove that failed HTTP statuses cannot change cached quota data, that success still updates it, and that logs contain no credentials.

## Key Entities

- **Usage Cache**: The last accepted request count, request limit, refresh time, perceived request count, and initialization state.
- **Usage Response**: The SDK result and its underlying HTTP status.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Both HTTP 4xx and 5xx responses leave all five cached values unchanged.
- **SC-002**: A successful response updates all returned usage values and refresh metadata.
- **SC-003**: All new response tests run without network access.
- **SC-004**: Failed refreshes remain visible in logs without exposing credentials or response bodies.

## Assumptions

- An HTTP status from 200 through 299 is successful.
- Existing exception handling remains the failure boundary for SDK errors.
- The last valid cache is safer than values from a failed response.
