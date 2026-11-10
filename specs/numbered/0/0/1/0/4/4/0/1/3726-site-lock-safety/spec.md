# Feature Specification: Site Lock Safety for Uncertain Submissions

**Feature Branch**: `3726-site-lock-safety`

**Created**: 2026-11-09

**Status**: Draft

**Input**: Issue #3726, “Upgrade portal: ambiguous submission replies enter the site-lock release path”

## User Scenarios & Testing

### User Story 1 - Prevent a duplicate upgrade (Priority: P1)

An operator submits a firmware upgrade. The cloud response does not prove whether the cloud accepted the request. The portal keeps the affected site locked and tells the operator that the outcome needs review.

**Why this priority**: A second upgrade can start while the first cloud request may still run. The duplicate can disrupt production devices.

**Independent Test**: Use offline responses for server errors, timeouts, malformed success replies, and missing upgrade identities. Confirm that each uncertain result keeps its site locked and does not enable a retry.

**Acceptance Scenarios**:

1. **Given** a firmware request receives an HTTP 503 or HTTP 429 response, **When** the portal records the result, **Then** the result remains uncertain and the site lock stays held.
2. **Given** a firmware request receives malformed success data or no required upgrade identity, **When** the portal records the result, **Then** the result remains uncertain and the site lock stays held.
3. **Given** a firmware request has an uncertain result, **When** another upgrade or retry targets the same site, **Then** the portal refuses that action until the existing operation is reconciled.

### User Story 2 - Release a lock after a proven refusal (Priority: P2)

An operator submits a firmware upgrade that the cloud explicitly refuses, or the portal proves that it never sent the request. The portal records that evidence and releases the site lock when no other operation step can use the site.

**Why this priority**: A proven refusal must not block later work after the portal knows that no cloud job can exist.

**Independent Test**: Use an allowlisted client-refusal response and a known not-submitted result. Confirm that each result can settle and release the lock without a live cloud request.

**Acceptance Scenarios**:

1. **Given** the response status is an explicitly allowed refusal, **When** the portal records the result, **Then** the child is a known refusal and can settle.
2. **Given** the portal proves that it did not send a child request, **When** it records the result, **Then** the child is not submitted and can settle.
3. **Given** every child has settled and any required post-upgrade watch has ended, **When** the portal checks the operation, **Then** it releases the operation's site locks.

### Edge Cases

- Treat HTTP 408, HTTP 429, HTTP 5xx, transport failures, and non-allowlisted client responses as uncertain.
- Treat HTTP 200 without a required upgrade identity as uncertain.
- Treat a documented refusal response as uncertain when it retains a job identity or accepted target.
- Treat a refusal response as uncertain when its body is malformed or the normalizer cannot retain all body evidence.
- Preserve the existing release rule for completed operations with no child entries. Require refusal evidence for every recorded `rejected` child.
- Keep earlier records with a rejected status uncertain unless their stored evidence proves a refusal.
- Keep a site locked when a post-upgrade watch remains active, even after every firmware child settles.

## Requirements

### Functional Requirements

- **FR-001**: The portal MUST distinguish accepted submissions, proven refusals, requests that were not sent, and uncertain outcomes.
- **FR-002**: The portal MUST treat transport failures, HTTP 408, HTTP 429, HTTP 5xx, malformed or unretained response bodies, missing required upgrade identities, and non-allowlisted responses as uncertain.
- **FR-003**: The portal MUST treat only explicitly allowlisted client-refusal responses as proof that the cloud did not create a firmware job.
- **FR-004**: The portal MUST keep each affected site locked while any child outcome remains uncertain.
- **FR-005**: The portal MUST prevent a retry while any affected child outcome remains uncertain.
- **FR-006**: The portal MUST release a site lock only when all relevant child actions are proven settled and no post-upgrade watch needs the site.
- **FR-007**: Cancellation reporting and lock release MUST use the same refusal evidence.
- **FR-008**: Validation MUST use offline test doubles and MUST make no live firmware request or production lock change.

### Mist Cloud Transport Requirements

- Keep the existing Mist firmware submission methods and authentication path. Add no REST or WebSocket transport.
- Test refusal, uncertainty, lock retention, retry blocking, and secret-safe error reporting with offline responses.

### Key Entities

- **Submission outcome**: The evidence that states whether a firmware request was accepted, refused, never sent, or remains uncertain.
- **Aggregate operation**: The selected child firmware requests and their durable outcomes.
- **Site lock**: The operation's protection against another firmware action at the same site.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Every tested uncertain response retains its site lock and blocks a retry.
- **SC-002**: Every tested allowlisted refusal and known not-submitted result can settle when no other operation step remains.
- **SC-003**: No validation case sends a live firmware request or changes a production lock.
- **SC-004**: The release decision, retry decision, and cancellation report agree on whether a child outcome proves that no cloud job exists.

## Assumptions

- Treat only HTTP 400, 401, 403, and 404 as refusal candidates because the local OpenAPI lists them for upgrade endpoints. Treat HTTP 429 and undocumented statuses as uncertain.
- Treat a refusal candidate as uncertain when the response or stored child record has a job identity or accepted target.
- Treat HTTP 408, 429, and 499 as uncertain because the response does not prove that the cloud created no job.
- Keep the existing lock lease and operator recovery controls. This change does not add a timeout, retry, migration, or manual lock-clear workflow.
- Treat a missing device upgrade identity as uncertain even when the response otherwise resembles acceptance.
