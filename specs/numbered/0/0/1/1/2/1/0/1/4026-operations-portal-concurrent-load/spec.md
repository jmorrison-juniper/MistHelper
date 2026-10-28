# Feature Specification: Concurrent operations portal access

**Feature Branch**: `jmorrison-juniper-operations-portal-concurrency`

**Created**: 2026-10-23

**Status**: Ready for planning

**Input**: Repair issue #4026 without changing operation execution, event streams, or the separate child-thread evidence defect.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Share operation state (Priority: P1)

Operators who open the portal simultaneously must use the same operation state within one application.

**Why this priority**: Duplicate state managers create additional worker pools and can hide active operations from other requests.

**Independent Test**: Send simultaneous first requests through local test clients with no Mist session.

**Acceptance Scenarios**:

1. **Given** a new application, **When** 16 requests arrive together, **Then** all requests use one operation state manager.
2. **Given** an initialized application, **When** another request arrives, **Then** the application retains its existing state manager.
3. **Given** two applications, **When** both receive requests, **Then** each retains its own state manager.
4. **Given** failed initialization, **When** a later request retries, **Then** it can initialize successfully.

### Edge Cases

- A slow first initialization must not permit duplicate state managers.
- Initialization failure must remain visible and must not leave a partial state manager.
- A running operation must not prevent another request from reading operation state.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Each application MUST create at most one operation state manager during successful simultaneous first access.
- **FR-002**: The portal MUST preserve existing request paths, response bodies, and status codes.
- **FR-003**: The portal MUST synchronize initialization only, not operation execution or stream delivery.
- **FR-004**: Different applications MUST retain separate operation state.
- **FR-005**: Initialization errors MUST remain visible and permit a later retry.

### Key Entities

- **Application**: One portal instance with its own configuration and operation state.
- **Operation state manager**: The shared run registry and worker owner for one application.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 16 simultaneous first requests succeed and share exactly one operation state manager.
- **SC-002**: Existing portal, event-stream, and event-bus behavior tests retain their expected results.
- **SC-003**: A forced initialization failure permits one successful retry without a duplicate retained state manager.
- **SC-004**: A request can read active state while another request remains inside operation submission.

## Assumptions

- Scope is one process. Separate server processes retain their existing independent state.
- Synthetic local requests are sufficient to prove this race. They do not prove the original container timeout has no other cause.
- No Mist cloud call, production device change, dependency change, deployment, merge, or issue closure belongs to this repair.
- Issue #4024 remains separate.
