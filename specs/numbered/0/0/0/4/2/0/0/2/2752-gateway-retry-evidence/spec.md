# Feature Specification: Preserve First Retry Failure Evidence

**Feature Branch**: `jmorrison-juniper-gateway-retry-evidence`

**Created**: 2026-10-19

**Status**: Draft

**Input**: Issue #2752 requests first-failure evidence in result-based retries for gateway configuration and synthetic test exports.

## User Scenarios & Testing

### User Story 1 - Diagnose a failed gateway read (Priority: P1)

An operator needs to see the first request failure after a retry succeeds or ends with no result.

**Why this priority**: The first error can show a permanent access or request problem. A later timeout or empty result can hide that cause.

**Independent Test**: Mock the Mist API. Cause a first request failure and a later fallback. Confirm the final diagnostic still shows the first failure.

**Acceptance Scenarios**:

1. **Given** the first gateway request fails, **When** a retry succeeds, **Then** the diagnostic shows the first failure and the operator receives the existing result.
2. **Given** a request failure, **When** the fallback returns no data, **Then** the log shows the first error and the operation returns its failure value.

## Requirements

### Functional Requirements

- **FR-001**: The retry diagnostic MUST retain the first request failure for one gateway item.
- **FR-002**: A later failure or empty result MUST NOT replace the first failure in the final retry diagnostic.
- **FR-003**: A successful fallback MUST return the same data shape as before this change.
- **FR-004**: The change MUST preserve the existing retry count, delay, and backoff multiplier.
- **FR-005**: Tests MUST mock API responses and MUST NOT contact the Mist cloud.

### Mist Cloud Transport Requirements

- The existing `getSiteDevice` and `getSiteDeviceSyntheticTest` methods remain the only API calls in scope.
- The change adds no direct HTTP request and does not change SDK authentication or endpoint selection.
- Unit tests MUST prove failure evidence, fallback behavior, and unchanged successful result shapes with mocked calls.
- The change adds no new secret source. Existing redaction and credential-handling paths remain unchanged.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Every tested retry sequence retains the first failure after a later fallback.
- **SC-002**: Existing successful result shapes and failure return values remain unchanged.
- **SC-003**: Existing retry attempt counts and backoff delays remain unchanged.
- **SC-004**: All tests in this slice run without a live Mist API request.

## Assumptions

- The operator uses existing application logs to diagnose gateway reads.
- A retry retains the first failure only for the duration of that item.
- This slice does not change retry behavior in other modules.
