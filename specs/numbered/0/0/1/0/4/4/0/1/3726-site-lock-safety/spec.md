# Feature Specification: Site Lock Safety for Uncertain Upgrade Replies

**Feature Branch**: `jmorrison-juniper-3726-ambiguous-upgrade-submission`

**Created**: 2026-11-09

**Status**: Draft

**Input**: Issue #3726. Keep site locks when the firmware submission result does not prove that the cloud refused the request or created a job.

## User Scenarios & Testing

### User Story 1 - Keep Sites Locked When Submission Is Uncertain (Priority: P1)

An operator submits an aggregate firmware upgrade. The cloud or network returns a result that does not prove whether a firmware job started. The portal keeps the selected site locks and marks the child outcome as unknown.

**Why this priority**: A second upgrade can start while the first cloud job may still run. The duplicate can disrupt production devices.

**Independent Test**: Give the submission boundary mocked uncertain replies. Confirm that the child is unknown and that no site lock release callback runs.

**Acceptance Scenarios**:

1. **Given** a submitted child receives HTTP 503, **When** the portal records the reply, **Then** the child is unknown and its site locks remain held.
2. **Given** a submitted child receives HTTP 429 or HTTP 408, **When** the portal records the reply, **Then** the child is unknown and its site locks remain held.
3. **Given** a successful HTTP response has invalid data or no upgrade identifier, **When** the portal records the reply, **Then** the child is unknown and its site locks remain held.
4. **Given** the transport raises after the write, **When** the portal handles the exception, **Then** existing unknown-outcome behavior remains unchanged and no retry occurs.

### User Story 2 - Release Sites Only After a Proven Refusal (Priority: P2)

An operator submits an upgrade that the cloud refuses, or the portal proves that it did not submit the child. The portal releases the site locks because no firmware job can follow.

**Why this priority**: A proven refusal must not block a later valid operation.

**Independent Test**: Give the submission boundary a documented refusal or a not-submitted result. Confirm that the portal marks the child final and releases its locks.

**Acceptance Scenarios**:

1. **Given** a reply has HTTP 400, 401, 403, or 404 and no upgrade identifier, **When** the portal records the reply, **Then** it records a known refusal and may release the site locks.
2. **Given** a child is marked not submitted, **When** the portal checks the operation, **Then** it may release the site locks.
3. **Given** an earlier record says rejected with HTTP 503, HTTP 408, HTTP 429, HTTP 499, or a successful status, **When** the portal checks the operation, **Then** it keeps the site locks because the record does not prove refusal.

### User Story 3 - Report Uncertain Jobs as Still Writing (Priority: P3)

An operator reviews cancellation results for an upgrade whose submission result is uncertain. The portal lists the child devices as possibly writing firmware.

**Why this priority**: The cancellation page must not report that no job exists when the cloud may have accepted the upgrade.

**Independent Test**: Give the cancellation view an uncertain child record. Confirm that its devices appear in the still-writing list.

**Acceptance Scenarios**:

1. **Given** a child has no complete cancellation result and its submission is uncertain, **When** the operator opens the cancellation result, **Then** each target appears as possibly writing.
2. **Given** a child has a proven refusal or was not submitted, **When** the operator opens the cancellation result, **Then** the portal reports that no device of that child is writing.

### Edge Cases

- An HTTP 200 response without a valid upgrade identifier does not prove acceptance.
- A device response that names accepted devices but has no upgrade identifier remains unknown.
- HTTP 408 and HTTP 429 remain uncertain even though they are client-error responses.
- A non-standard HTTP 499 response remains uncertain.
- A rejected record without an allowed refusal status remains uncertain.
- A rejected record with an upgrade identifier remains uncertain because the evidence conflicts.
- A child that was not submitted remains a known final result.
- A transport exception after a destructive request keeps the existing unknown state and retry behavior.

## Requirements

### Functional Requirements

- **FR-001**: The portal MUST mark a submission as accepted only when the response proves acceptance and includes the required upgrade identifier.
- **FR-002**: The portal MUST mark a submission as rejected only when it has no upgrade identifier and its HTTP status is 400, 401, 403, or 404.
- **FR-003**: The portal MUST mark all other returned submission outcomes as unknown.
- **FR-004**: The portal MUST keep site locks while any child has an unknown outcome.
- **FR-005**: The portal MUST evaluate earlier rejected records by their stored HTTP status and upgrade identifier before releasing locks.
- **FR-006**: The portal MUST release locks when each child is `completed`, `cancelled`, `failed`, `not_submitted`, or has a proven refusal. A `rejected` state alone MUST NOT prove that no firmware write can follow. When a record has no child data, the portal MUST retain the existing `SETTLED_OPERATION_STATES` rule.
- **FR-007**: The cancellation result MUST treat only a proven refusal or a not-submitted child as proof that no firmware job exists.
- **FR-008**: The portal MUST keep uncertain child devices in the possibly-writing list when cancellation evidence is incomplete.
- **FR-009**: The change MUST NOT add a retry, alter a timeout, change a lock lease, or run a live firmware request.
- **FR-010**: Tests MUST use offline stand-ins and MUST verify both lock retention and known-refusal release.

### Mist Cloud Transport Requirements

- Existing calls use the `upgradeOrgDevices`, `upgradeSiteDevices`, and `upgradeOrgSsrs` methods through the Mist SDK. This change adds no request or alternate transport.
- The current OpenAPI lists HTTP 400, 401, 403, 404, and 429 for the relevant submission methods. Only 400, 401, 403, and 404 prove refusal. HTTP 429 does not.
- No owned WebSocket transport is required. Existing SDK authentication and endpoint use remain unchanged.
- Offline tests must cover uncertain replies, known refusal, no retry, lock retention, and secret-free error handling.

### Key Entities

- **Submission outcome**: The stored child result, including its state, HTTP status, upgrade identifier, and error.
- **Site lock**: The operation-owned lock that prevents another firmware operation at a selected site.
- **Cancellation result**: The device lists that show which devices stopped, may still write, or have no cancel path.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Every tested uncertain reply keeps the operation-owned site locks and starts no second firmware request.
- **SC-002**: Every tested documented refusal and not-submitted result remains eligible for lock release.
- **SC-003**: Every tested uncertain child with incomplete cancellation data appears as possibly writing.
- **SC-004**: All focused tests run without a Mist credential, a live service, or a production lock change.

## Assumptions

- The OpenAPI response lists for the existing submission methods define the reviewed refusal allowlist as HTTP 400, 401, 403, and 404.
- HTTP 408, HTTP 429, HTTP 5xx, HTTP 499, missing status, malformed success data, and missing identifiers do not prove that no job exists.
- Earlier stored records do not need a migration. The portal can use their saved status, HTTP status, and identifier.
- Existing lock leases and operator recovery controls remain unchanged.
- The portal keeps its current operation-wide lock scope when one child outcome is unknown.
