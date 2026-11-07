# Feature Specification: Preserve API Usage After Failed Refresh

**Feature Branch**: `jmorrison-juniper-issue-triage-overlap-analysis`

**Created**: 2026-11-07

**Status**: Draft

**Input**: Issue #4611: Preserve cached API usage when a Mist usage refresh returns an unsuccessful HTTP status.

## User Scenarios & Testing

### User Story 1 - Keep rate limiting based on valid usage data (Priority: P1)

An operations engineer needs the rate limiter to keep its last valid usage values when Mist rejects or fails a usage refresh.

**Why this priority**: Incorrect usage values can cause the rate limiter to make decisions from data that Mist did not accept.

**Independent Test**: Provide unsuccessful 4xx and 5xx responses with valid-looking usage data, then verify that every cached value remains unchanged and that the failure is logged.

**Acceptance Scenarios**:

1. **Given** a populated usage cache, **When** a refresh receives an unsuccessful 4xx response, **Then** the cache remains unchanged and the refresh failure is logged.
2. **Given** a populated usage cache, **When** a refresh receives an unsuccessful 5xx response, **Then** the cache remains unchanged and the refresh failure is logged.
3. **Given** a populated usage cache, **When** a refresh receives a successful response, **Then** the cache stores the returned usage values and marks the refresh time.

### Edge Cases

- When an unsuccessful response contains valid-looking usage data, do not treat that data as authoritative.
- When a successful response omits an optional usage field, preserve the existing default behavior.
- When the refresh call raises an exception, preserve the cache and report the failure.

## Requirements

### Functional Requirements

- **FR-001**: The rate limiter MUST accept usage data only from a successful Mist response.
- **FR-002**: The rate limiter MUST preserve all usage values and refresh metadata when a refresh response is unsuccessful.
- **FR-003**: The rate limiter MUST log an unsuccessful refresh without exposing credentials.
- **FR-004**: A successful refresh MUST retain the existing cache update behavior.
- **FR-005**: Automated tests MUST verify unsuccessful 4xx and 5xx responses without sending a live request.

### Mist Cloud Transport Requirements

- The feature uses `mistapi.api.v1.self.usage.getSelfApiUsage`.
- The existing Mist SDK returns the HTTP status code and response data in its response object.
- Offline tests MUST use native SDK response objects and a controlled session.
- Tests MUST verify the response status, successful endpoint use, cache preservation, and failure logging.
- Tests MUST not send live HTTP requests or log credentials.

### Key Entities

- **Usage cache**: The last accepted usage values, request count, refresh time, and initialization state used by the rate limiter.
- **Refresh response**: The result of one Mist usage request, including its success status and usage data.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Every tested unsuccessful 4xx or 5xx refresh leaves all existing usage and refresh fields unchanged.
- **SC-002**: A successful refresh continues to update the usage values and refresh time.
- **SC-003**: Each unsuccessful refresh produces a warning that identifies the failure without exposing credentials.
- **SC-004**: All response-status tests run offline and prove that the correct result depends on the response status.

## Assumptions

- A successful HTTP status is any status from 200 through 299.
- Existing cache defaults remain unchanged for successful responses that omit optional fields.
- The rate limiter continues to use cached values after a failed refresh.
