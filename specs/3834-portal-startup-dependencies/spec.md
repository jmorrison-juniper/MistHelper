# Feature Specification: Per-Request Upgrade Portal Dependencies

**Feature Branch**: `jmorrison-juniper-startup-dependency-reassessment`

**Created**: 2026-10-06

**Status**: Draft

**Input**: Issue #3834: provide Phase 2 and 3 service dependencies during normal startup.

## User Scenarios & Testing

### User Story 1 - Start the portal with working services (Priority: P1)

As a network operator, I need the normal portal startup path to provide the dependencies for
capture, upgrade, settle, and comparison work. This lets me use the portal without test-only
configuration.

**Why this priority**: Operators cannot use the portal services when normal startup omits required
dependencies.

**Independent Test**: Build the application through the default factory path with test doubles.
Verify that each service receives the required database router and that each Mist operation uses
the authenticated operator's session.

**Acceptance Scenarios**:

1. **Given** the portal starts through `wsgi_capture:app` with no factory overrides, **When** the
   factory installs its services, **Then** each service that needs storage has a valid database
   router.
2. **Given** an authenticated operator sends a request that needs Mist, **When** the service makes
   a Mist call, **Then** it uses that request's operator session.
3. **Given** the default factory starts without test overrides, **When** the operator uses a
   supported capture, upgrade, settle, or comparison flow, **Then** the portal does not fail because
   startup omitted a required dependency.

### User Story 2 - Refuse work when a dependency is unavailable (Priority: P1)

As a network operator, I need the portal to stop safely when a request has no valid operator
session or required storage. This prevents incomplete or unauthorized work.

**Why this priority**: These services can read device state and start firmware changes. Missing
dependencies must not lead to partial work or a false success response.

**Independent Test**: Use the default factory with one required dependency unavailable. Send a
request to each affected service route and verify a safe refusal with no service side effect.

**Acceptance Scenarios**:

1. **Given** a request has no valid operator session, **When** it requests a Mist-dependent
   operation, **Then** the portal returns its authentication refusal and makes no Mist call.
2. **Given** a request needs unavailable storage, **When** it requests a service operation, **Then**
   the portal returns a service-unavailable response and makes no storage or Mist call.
3. **Given** a capture, upgrade, or comparison operation fails, **When** the portal reports the
   result, **Then** it shows failure and does not report success or continue with an unsafe action.
4. **Given** the implementation plan is ready, **When** the hierarchy constraints are reviewed,
   **Then** the plan records the nine existing direct children under `runtime`, a separate
   incremental remediation action, and a compliant location for this work.

### User Story 3 - Keep operator sessions and test dependencies separate (Priority: P1)

As a network operator and test maintainer, I need each request to use its own operator session. I
also need existing end-to-end factory overrides to remain complete and isolated.

**Why this priority**: A shared session can expose one operator's Mist access to another operator.
Live network or store calls can also make tests unsafe and unreliable.

**Independent Test**: Run concurrent requests with two distinct fake operator sessions. Verify that
each request uses only its own session. Run the same startup tests with the existing complete
end-to-end overrides.

**Acceptance Scenarios**:

1. **Given** two operators send requests at the same time, **When** both requests use Mist-dependent
   services, **Then** each service call uses only the session of its request.
2. **Given** an end-to-end test supplies its complete factory overrides, **When** the factory
   creates the application, **Then** those overrides remain in effect and no production dependency
   replaces them.
3. **Given** any unit or integration test exercises startup or a service route, **When** the test
   runs, **Then** it makes no live Mist network call or production store call.

### Edge Cases

- The request has no authenticated operator session.
- A database router is absent, invalid, or unable to access its store.
- The portal has a Mist session for a different operator.
- Two operators issue Mist-dependent requests concurrently.
- The factory receives all existing end-to-end overrides.
- A capture, upgrade, settle, or comparison action receives a dependency failure.
- A test attempts to open a network or production-store connection.

## Requirements

### Functional Requirements

- **FR-001**: The default portal factory MUST provide the dependencies required by the capture,
  upgrade, settle-gate, and comparison services without requiring test-only configuration.
- **FR-002**: Each Mist-dependent request MUST use the authenticated Mist session associated with
  that request's operator.
- **FR-003**: The portal MUST NOT reuse one operator's Mist session for another operator or keep a
  single Mist session in module-level or shared application configuration. It MUST NOT expose
  credentials or session contents in browser cookies, logs, output, or error messages.
- **FR-004**: The default factory MUST provide a valid `DatabaseRouter` to every service that
  requires one.
- **FR-005**: Complete end-to-end factory overrides MUST continue to replace the default
  dependencies without being overwritten by production setup.
- **FR-006**: The portal MUST reject a Mist-dependent operation when the request has no valid
  operator session. It MUST reject a storage-dependent operation when its database router is
  unavailable or invalid. It MUST stop a cloud mutation when a storage operation fails.
- **FR-007**: Dependency failures, cancellations, and comparison failures MUST remain visible as
  failures. The portal MUST NOT convert them into success responses.
- **FR-008**: Tests for default startup and service routes MUST use isolated test doubles. They MUST
  not call Mist over a live network or access a production store.
- **FR-009**: The implementation plan MUST record the nine existing direct children in the upgrade
  portal `runtime` directory and a separate incremental remediation action. The implementation
  MUST reuse an existing module or a compliant nested location. It MUST NOT add a direct child to
  `runtime`.

### Mist Cloud Transport Requirements

- This feature adds no Mist REST method and no new transport.
- Mist-dependent work MUST use the session of the authenticated operator for the current request.
- Tests MUST use fake sessions and block live network access. They MUST verify that a missing or
  mismatched session cannot reach a Mist operation.
- Tests MUST verify that failures do not expose credentials or session contents.

### Key Entities

- **Operator request**: One portal request and the authenticated operator identity associated with
  it.
- **Mist session**: The authenticated cloud session used for Mist work by one operator.
- **Database router**: The storage dependency used by services that read or write portal records.
- **Service operation**: A capture, upgrade, settle-gate, or comparison action that uses one or both
  dependencies.

## Success Criteria

### Measurable Outcomes

- **SC-001**: 100% of normal portal starts allow supported service flows to begin with their
  required dependencies.
- **SC-002**: 100% of requests without valid authentication or required storage receive a failure
  response before any cloud mutation.
- **SC-003**: In every two-operator concurrency test, each request uses only its own Mist session.
- **SC-004**: 100% of startup and service tests complete with zero live network calls and zero
  production-store calls.
- **SC-005**: 100% of existing complete end-to-end factory override cases keep their supplied
  dependencies.
- **SC-006**: Operators can distinguish success, dependency failure, cancellation, and comparison
  failure from the portal response in 100% of tested outcomes.

## Assumptions

- The existing sign-in flow remains the source of authenticated operator sessions.
- Issue #3834 records that normal startup leaves `MIST_CLIENT` and `DB_ROUTER` unset, although
  service wiring reads those configuration entries.
- The existing storage settings remain the source of database router configuration.
- The feature changes dependency wiring only. It does not change sign-in, authorization, write
  gates, site locks, audit records, or route ownership.
- The implementation plan will document the existing `runtime` directory debt and a separate
  incremental action to address it. The feature will not add a direct child to that directory.
