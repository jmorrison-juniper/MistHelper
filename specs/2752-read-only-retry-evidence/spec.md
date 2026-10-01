# Feature Specification: Read-only retry evidence

**Feature Branch**: `jmorrison-juniper-read-only-retry-evidence`

**Created**: 2026-10-01

**Status**: Implemented locally

**Input**: Preserve the first failed status at the generic fetch boundary.
Part of #2752. The full campaign remains open.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Identify a failed attempt after recovery (Priority: P1)

The operator needs the failed HTTP status when a later attempt succeeds.
The diagnostic must identify the endpoint and the attempt.

**Why this priority**: A recovery must not remove the evidence that explains the retry.

**Independent Test**: Supply a failed response followed by a successful response without a network connection.

**Acceptance Scenarios**:

1. **Given** statuses `503`, then `200`, **When** the fetcher retries, **Then** its warning retains `503`.
2. **Given** different failed statuses, **When** a later attempt succeeds, **Then** warnings retain each failed status in order.
3. **Given** exhausted attempts, **When** the fetcher stops, **Then** diagnostics retain every failed status.

---

### User Story 2 - Report absent evidence safely (Priority: P2)

The operator needs an explicit statement when the SDK provides no HTTP status.
The diagnostic must not invent a transport cause or expose response content.

**Why this priority**: A guessed cause can direct the operator toward the wrong repair.

**Independent Test**: Supply an absent SDK status followed by a successful response.

**Acceptance Scenarios**:

1. **Given** no HTTP status, **When** the fetcher retries, **Then** the diagnostic states that the status is unavailable.
2. **Given** private response content, **When** the fetcher reports a failure, **Then** its diagnostic excludes that content.

---

### User Story 3 - Preserve valid retry behavior (Priority: P3)

The operator receives the same response object, retry decisions, and delays.

**Why this priority**: A diagnostic change must not change network operations.

**Independent Test**: Measure endpoint calls, response identity, sleeps, and blocked network and output boundaries.

**Acceptance Scenarios**:

1. **Given** immediate status `200`, **When** the fetcher runs, **Then** it returns that response without a failure warning.
2. **Given** an HTTP client error, **When** the fetcher runs, **Then** it returns that response without a retry.
3. **Given** exhausted attempts, **When** the fetcher stops, **Then** it returns the last response without an additional sleep.

### Edge Cases

- An absent HTTP status does not prove a timeout or a connection error.
- A non-integer diagnostic value must not expose its string representation.
- A zero retry ceiling still permits the initial call.
- A final failed attempt needs status evidence even though no retry follows.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Diagnostics must retain each failed attempt's HTTP status, endpoint name, and attempt order.
- **FR-002**: Diagnostics must identify an unavailable status without guessing its cause.
- **FR-003**: Diagnostics must exclude response bodies, headers, query values, credentials, and arbitrary object representations.
- **FR-004**: The change must preserve endpoint arguments, response identity, retry ceilings, exponential delays, and sleep counts.
- **FR-005**: Immediate success and client-error responses must produce no retry warning.
- **FR-006**: Final HTTP rejection, body rejection, recovery, exports, and rate limiting must remain unchanged.

### Key Entities *(include if feature involves data)*

- **Failed attempt**: The endpoint name, HTTP status or its absence, attempt number, and existing delay.
- **Returned response**: The exact successful response or the last response after exhaustion.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every controlled failed attempt retains its actual status or an explicit absence statement.
- **SC-002**: Every controlled sequence preserves its exact endpoint calls and sleep series.
- **SC-003**: Controlled diagnostic cases make zero network calls and zero export or store writes.
- **SC-004**: Missing and incorrect first-status evidence each cause a regression test failure.
- **SC-005**: Changed statements and branches receive complete local test coverage.

## Assumptions

- The defect exists at the fetcher's logger boundary. This specification makes no claim about upstream SDK logs.
- The `835` historical inventory candidates are not confirmed failures.
- This slice changes only two existing source methods and their directly related tests and feature documents.
- The parent controls publication and actual-main verification. Position `35` follows #3701.
- No live Mist operation, API token, production store, container, or browser server is necessary.
