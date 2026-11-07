# Feature Specification: Capture Request Dependencies

**Feature Branch**: `3999-fix-capture-dependencies`

**Created**: 2026-11-07

**Status**: Draft

**Input**: Issue #4653. Resolve capture dependencies during normal portal startup.

## User Scenarios & Testing

### User Story 1 - Start a pre-upgrade capture (Priority: P1)

An authenticated operator starts a pre-upgrade capture from the upgrade portal. The portal uses the operator's authenticated Mist session and resources owned by that request. The operator receives a clear refusal if authentication or storage is unavailable.

**Why this priority**: A pre-upgrade capture is required before the portal can assess device changes safely.

**Independent Test**: Use the normal no-argument application factory and isolated stand-ins. Submit a valid capture request and confirm that the capture service receives the authenticated session and request-owned storage.

**Acceptance Scenarios**:

1. **Given** a valid operator session and available storage, **When** the operator starts a valid pre-upgrade capture, **Then** the portal starts one capture through that session and returns an accepted response.
2. **Given** no valid operator session, **When** a capture request reaches the route, **Then** the portal returns an authentication refusal before it opens storage or starts capture work.
3. **Given** storage cannot be constructed, **When** an authenticated operator starts a capture, **Then** the portal returns a service-unavailable response before it calls Mist or reports success.

## Edge Cases

- Preserve a configured capture-service override used by isolated tests.
- Close request-owned storage during request teardown, and do not close the borrowed operator session.
- Do not start a firmware upgrade as part of a capture request.

## Requirements

### Functional Requirements

- **FR-001**: Normal application startup MUST NOT install a capture service without its required Mist session and database router.
- **FR-002**: The capture route MUST resolve its default service from the authenticated request dependencies.
- **FR-003**: The capture service MUST use only the authenticated operator session and the request-owned database router.
- **FR-004**: A configured capture-service override MUST remain usable by isolated tests.
- **FR-005**: The route MUST refuse missing authentication or storage before it starts capture work.
- **FR-006**: Tests MUST block live Mist requests, database connections, and firmware upgrades.

### Mist Cloud Transport Requirements

The existing capture service uses `listSiteDeviceStats`, `listSiteDeviceConfig`, `listSiteDeviceRadios`, `listSiteNetworkPolicies`, and `listSiteDeviceLldpNeighbors` through the authenticated Mist session. This change adds no transport and no endpoint. Tests MUST prove that the route binds the authenticated session and makes no live request.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Every valid request in the isolated normal-startup test returns an accepted response and binds the service to the authenticated operator session.
- **SC-002**: Every missing-authentication or unavailable-storage test refuses the request before any Mist request or capture operation.
- **SC-003**: The existing capture-service override tests continue to pass.

## Assumptions

- The portal's existing operator identity, authorization, site-lock, and audit controls remain unchanged.
- The capture request remains separate from the firmware-upgrade request.
- The existing request dependency provider remains the owner of the Mist session and database-router lifecycle.
