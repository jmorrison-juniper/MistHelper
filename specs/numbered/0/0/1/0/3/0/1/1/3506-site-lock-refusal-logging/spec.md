# Feature Specification: Site Lock Refusal Logging

**Feature Branch**: `jmorrison-juniper-3506-upgrade-portal-lock-refusal-logging`

**Created**: 2026-10-25

**Status**: Draft

**Input**: Issue #3506 and its confirmed assessment.

## User Scenarios & Testing

### User Story 1 - Diagnose a refused site lock (Priority: P1)

An operations engineer reads the portal log after a lock request fails. The log shows the site and the reason for refusal. It does not expose a token, work address, or personal data.

**Why this priority**: The lock prevents two firmware upgrades from changing one site at the same time. A refusal without a log record hides a safety decision.

**Independent Test**: Send refused take, beat, and release requests through a test portal with a fake lock store. Check the log record fields and the unchanged HTTP response.

**Acceptance Scenarios**:

1. **Given** another operator holds the site, **When** a take is refused, **Then** the log records the site, refusal code, and response status.
2. **Given** the operator must enter a confirmation word, **When** the request is refused, **Then** the log records the refusal without the word or personal data.
3. **Given** the session no longer holds the site, **When** a beat or release is refused, **Then** the log records the site and refusal code.

### Edge Cases

- When the lock store is unavailable, the log records the refusal code and response status without repeating sensitive store details.
- When the request succeeds, the log records the action result without recording the lock token.
- When the portal has no selected organization or session owner, the response remains unchanged and the refusal does not expose personal data.

## Requirements

### Functional Requirements

- **FR-001**: The portal MUST record each site lock take, beat, and release action before it runs.
- **FR-002**: The portal MUST record each successful lock action after it completes.
- **FR-003**: The portal MUST record each refused lock request with its site identifier, refusal code, and response status.
- **FR-004**: Lock refusal records MUST NOT contain tokens, email addresses, or raw personal data.
- **FR-005**: Logging MUST NOT change lock decisions, operation order, response bodies, or response statuses.

## Success Criteria

### Measurable Outcomes

- **SC-001**: All 18 currently silent exit paths in the assessed lock routes and lock functions produce a log record.
- **SC-002**: Every route-level refusal record identifies its site, refusal code, and response status.
- **SC-003**: All existing lock response and decision tests pass without changes to their expected outcomes.
- **SC-004**: Tests confirm that refusal records contain no token or email address.

## Assumptions

- The existing route and lock error codes remain the source of refusal reasons.
- Existing logs for lock-store and takeover-audit failures remain in place.
- Tests use fake lock stores and do not connect to Mist Cloud, Redis, or production data.
