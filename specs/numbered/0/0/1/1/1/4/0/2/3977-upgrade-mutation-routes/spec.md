# Feature Specification: Upgrade Mutation Routes

**Feature Branch**: `3997-upgrade-mutation-routes`

**Created**: 2026-10-24

**Status**: Draft

**Input**: Issue #3977: Use request-specific dependencies for firmware changes, run-control actions, and comparison approval.

## User Scenarios & Testing

### User Story 1 - Start or cancel a firmware upgrade (Priority: P1)

An authenticated operator starts or cancels an upgrade for the selected run. The portal uses the Mist session and resources that belong to that operator's request.

**Why this priority**: A route that cannot resolve its dependencies can refuse valid work or report success without starting or cancelling an upgrade.

**Independent Test**: Submit start and cancel requests with isolated fake dependencies. Verify the correct request session reaches the service and no other operator's session is used.

**Acceptance Scenarios**:

1. **Given** a valid operator request and available resources, **When** the operator starts or cancels an upgrade, **Then** the portal calls the matching service with that request's identity and resources.
2. **Given** an absent provider or required resource, **When** the operator submits a firmware change, **Then** the portal returns a refusal and makes no firmware change.
3. **Given** an invalid confirmation or authorization, **When** the operator submits a firmware change, **Then** the portal refuses the request before the service can change a device.

### User Story 2 - Submit or reconcile a run action (Priority: P1)

An authenticated operator submits a confirmed run action or reconciles a run. The portal checks the operator, authorization, preview, site lock, and durable action record before it reports success.

**Why this priority**: A run action changes upgrade state and needs one durable record that the operator can inspect after the request ends.

**Independent Test**: Submit fake run-control requests with isolated request resources and a fake durable store. Verify each guard runs before a mutation and the action record keeps the correct actor.

**Acceptance Scenarios**:

1. **Given** valid authorization, confirmation, preview, site lock, and durable storage, **When** the operator submits a run action, **Then** the portal records and reports the action for that operator.
2. **Given** missing request resources or durable storage, **When** the operator submits or reconciles an action, **Then** the portal refuses before it changes run state.
3. **Given** a changed site lock or invalid confirmation, **When** the operator submits a run action, **Then** the portal refuses and records no successful action.

### User Story 3 - Approve comparison results (Priority: P2)

An authorized operator approves comparison results for a run. The portal records the decision and audit entry through resources for the active request.

**Why this priority**: Approval records a safety decision about the result of a firmware change.

**Independent Test**: Submit approval with fake request resources. Verify the decision and audit entry use the current operator and the request-owned database boundary.

**Acceptance Scenarios**:

1. **Given** valid request resources and approval data, **When** the operator approves comparison results, **Then** the portal records the approval and its audit entry.
2. **Given** missing request resources or invalid authorization, **When** the operator submits approval, **Then** the portal refuses without recording an approval.

### Edge Cases

- A provider is missing, has the wrong type, or cannot construct a required resource.
- The operator session is absent or no longer usable.
- Two operators submit protected requests at the same time.
- A durable action write fails or cannot be verified.
- The site lock changes after the operator receives a preview.
- The request contains invalid confirmation, approval data, or run scope.

## Requirements

### Functional Requirements

- **FR-001**: Each protected firmware mutation MUST use the authenticated operator and resources for the active request.
- **FR-002**: A request MUST NOT use another operator's Mist session.
- **FR-003**: Run-control mutations MUST preserve authentication, authorization, preview validation, typed confirmation, site-lock checks, idempotency, audit records, and durable action storage.
- **FR-004**: Comparison approval MUST preserve authorization, request ownership, database writes, and audit records.
- **FR-005**: The portal MUST refuse a mutation when a required provider or resource is missing or invalid.
- **FR-006**: A refused request MUST cause no firmware change, run-state change, comparison approval, or success response.
- **FR-007**: Existing request validation and response behavior MUST remain unchanged when all required resources are available.
- **FR-008**: Tests MUST use fake sessions, services, and stores. Tests MUST NOT use production credentials, live Mist requests, or production stores.
- **FR-009**: This feature MUST NOT change portal startup behavior outside the dependency construction needed by these mutation routes.

### Mist Cloud Transport Requirements

- This feature adds no Mist REST endpoint and no direct HTTP call. Existing upgrade services remain responsible for cloud requests through the supported Mist SDK.
- Tests MUST prove that missing dependencies, authentication failures, and guard refusals make no live or fake firmware mutation call.
- Tests MUST use non-production credentials and MUST verify that logs do not expose credentials.

### Key Entities

- **Authenticated operator**: The verified person and Mist session that own one request.
- **Request resources**: The database and service resources that the portal resolves for one authenticated request.
- **Run action**: A durable record of a confirmed upgrade action and its outcome.
- **Comparison approval**: An operator decision and its audit record for one run.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Every tested firmware mutation refuses when a required request resource is absent, and no service mutation call occurs.
- **SC-002**: Tests with two authenticated sessions show zero use of one operator's Mist session by the other operator's request.
- **SC-003**: Every run-control test proves that invalid confirmation, authorization, preview, or site-lock state produces no successful durable action.
- **SC-004**: Each successful run-control or comparison approval test can read the recorded result and its actor after the request ends.
- **SC-005**: All affected route tests pass without production credentials, live Mist requests, or production-store access.

## Assumptions

- The existing authentication, confirmation, authorization, site-lock, audit, and durable action rules remain authoritative.
- The request provider may reuse a shared durable store when that store contains no operator's Mist session and every record remains actor-scoped.
- Read-only routes and unrelated startup installers remain outside this change.
- Local tests can replace each external boundary with a fake that rejects network and production-store access.
