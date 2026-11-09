# Feature Specification: Upgrade Lock Retention

**Feature Branch**: `jmorrison-juniper-fix-3726-upgrade-lock-retention`

**Created**: 2026-11-09

**Status**: Draft

**Input**: Issue #3726: Keep site locks when the cloud may have accepted a firmware upgrade.

## User Scenarios & Testing

### User Story 1 - Protect a site after an uncertain submission (Priority: P1)

An operator starts a multi-site firmware upgrade. The cloud returns a server error, a damaged success response, or no usable response. The portal keeps each affected site unavailable until it can prove that the upgrade ended.

**Why this priority**: A second upgrade can conflict with a firmware job that the first response did not confirm.

**Independent Test**: Give the portal an uncertain submission result. Check that the site remains locked and that the retry control stays unavailable.

**Acceptance Scenarios**:

1. **Given** a site child has an HTTP 503 result and no upgrade identifier, **When** the portal checks whether the operation ended, **Then** it keeps the site lock.
2. **Given** a site child has an HTTP 200 result without a valid upgrade identifier, **When** the portal checks whether the operation ended, **Then** it keeps the site lock.
3. **Given** an uncertain child has no later status that proves an end, **When** the portal offers retry options, **Then** it offers no retry for that operation.
4. **Given** the operation record already contains a final cloud status, **When** the portal checks the operation, **Then** it follows the existing release rule.

### User Story 2 - Release a site after a proven refusal (Priority: P2)

An operator submits an upgrade that the cloud refuses, or the portal records that it did not send the child request. The portal keeps the existing behavior for these known outcomes.

**Why this priority**: A confirmed refusal must not block later work at the site.

**Independent Test**: Give the portal an HTTP 4xx refusal or a known not-submitted result. Check that the operation can settle under the existing rules.

**Acceptance Scenarios**:

1. **Given** a child has an HTTP 4xx refusal, **When** the portal checks whether the operation ended, **Then** it can release the site lock.
2. **Given** a child was not submitted, **When** the portal checks whether the operation ended, **Then** it can release the site lock.
3. **Given** a child has a server error or a damaged success response, **When** the portal builds cancellation or retry information, **Then** it does not report that no cloud job exists.

### Edge Cases

- Keep the lock when the HTTP status is missing or invalid.
- Keep the lock when a response has a 2xx status but no valid upgrade identity.
- Preserve the existing lock rule when a known cloud job reports its final status.
- Do not release a lock when a phase watch or post-check is still active.
- Preserve the existing lease duration and status-read behavior.

## Requirements

### Functional Requirements

- **FR-001**: The portal MUST distinguish a confirmed HTTP 4xx refusal from an uncertain submission result.
- **FR-002**: The portal MUST treat a server error, an invalid status, or a 2xx response without a valid upgrade identity as uncertain.
- **FR-003**: The portal MUST keep each site lock while any child has an uncertain submission outcome.
- **FR-004**: The portal MUST allow retry only when the operation meets the existing settled-state rules.
- **FR-005**: The portal MUST report that no cloud job exists only for a known refusal or a known not-submitted child.
- **FR-006**: The portal MUST preserve existing behavior for confirmed refusals, known final cloud jobs, phase watches, and post-checks.
- **FR-007**: The portal MUST NOT send an additional cloud request to resolve an uncertain submission.
- **FR-008**: The change MUST preserve the existing lease duration and status-read behavior.

### Key Entities

- **Operation child**: One site or organization firmware submission with its result, HTTP status, upgrade identity, and current state.
- **Site lock**: The existing reservation that prevents a second operation from using a selected site.
- **Submission outcome**: The known refusal, known non-submission, accepted job, or uncertain result for one operation child.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Every tested HTTP 503 result without an upgrade identity keeps the site lock.
- **SC-002**: Every tested HTTP 200 result without a valid upgrade identity keeps the site lock.
- **SC-003**: Every tested HTTP 4xx refusal and known not-submitted result follows the existing release behavior.
- **SC-004**: An uncertain result does not enable retry or claim that no cloud job exists.
- **SC-005**: The focused tests complete without a live Mist request or a production lock change.

## Assumptions

- An HTTP 4xx response proves that the cloud refused the child request, consistent with the existing cancellation rule.
- A server error, missing status, or malformed success response does not prove that the cloud refused the request.
- The current lease duration and status polling remain unchanged. The change prevents an early release but does not extend the lease.
- The issue requires no new Mist API method and no live cloud call.
- The existing `.specify/feature.json` points to another feature and remains unchanged.
