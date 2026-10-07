# Feature Specification: Operations Portal Concurrent Load

**Feature Branch**: `jmorrison-juniper-assessment-4026`

**Created**: 2026-10-06

**Status**: Planned

**Input**: Issue #4026 reports an unsynchronized lazy singleton race in `web_portal/routes/operations.py::_get_executor()`. Concurrent first requests can create multiple operation executors and worker pools.

## User Scenarios & Testing

### User Story 1 - Start concurrent portal requests safely (Priority: P1)

As a network operator, I can send concurrent first requests to the Operations portal without creating separate operation execution systems.

**Why this priority**: Multiple execution systems create unmanaged worker pools and split active-run state. This condition can make the portal stop responding.

**Independent Test**: Start several first requests at the same time. Verify that all requests use the same executor and that only one executor is constructed.

**Acceptance Scenarios**:

1. **Given** the application has no operation executor, **When** concurrent first requests need the executor, **Then** exactly one executor is constructed and stored.
2. **Given** concurrent first requests wait at the executor construction boundary, **When** the requests continue together, **Then** each request receives the same stored executor.
3. **Given** concurrent run requests arrive before executor initialization, **When** they start operations, **Then** they share one executor and one worker pool.

---

### User Story 2 - Preserve existing Operations routes (Priority: P2)

As a network operator, I retain the existing Operations portal routes and the account-aware MSP selector behavior from PR #4065.

**Why this priority**: The concurrency repair must not remove or change unrelated route behavior that is in active development.

**Independent Test**: Compare the route module before and after the repair. Verify that only executor initialization and its regression test change.

**Acceptance Scenarios**:

1. **Given** the route additions from PR #4065, **When** the concurrency repair is applied, **Then** those route lines remain unchanged.
2. **Given** an executor already exists in application configuration, **When** any Operations route requests it, **Then** the route returns the existing executor without constructing another executor.

### Edge Cases

- An executor can appear after the first check but before a waiting request enters the protected initialization section.
- Many requests can reach the first empty-state check before any request constructs the executor.
- The constructor can take enough time for every competing request to reach the same race boundary.
- A request can arrive after initialization while another request still holds the initialization lock.
- The existing executor can be any valid configured instance. The accessor must return it without replacement.

## Requirements

### Functional Requirements

- **FR-001**: The Operations route module MUST use one module-level lock to control lazy executor initialization.
- **FR-002**: `_get_executor()` MUST check for an existing executor before it acquires the lock.
- **FR-003**: `_get_executor()` MUST check for an existing executor again after it acquires the lock.
- **FR-004**: `_get_executor()` MUST construct and store an executor only when the second check finds no executor.
- **FR-005**: Every concurrent caller MUST receive the single executor stored in application configuration.
- **FR-006**: Concurrent first run requests MUST share the worker pool owned by the single stored executor.
- **FR-007**: The change MUST keep `_get_executor()` as the only executor accessor.
- **FR-008**: The change MUST NOT add a compatibility shim, alias, or second accessor.
- **FR-009**: The change MUST NOT modify `web_portal/services/operation.py`.
- **FR-010**: The change MUST preserve the route lines added by PR #4065 in `web_portal/routes/operations.py`.
- **FR-011**: A regression test MUST force concurrent callers through the uninitialized executor path.
- **FR-012**: The regression test MUST hold competing callers until each caller is ready to exercise the race.
- **FR-013**: The regression test MUST release the competing callers together and prove that exactly one executor is constructed.
- **FR-014**: The regression test MUST prove that every caller receives the same executor instance.
- **FR-015**: The regression test MUST fail against the unsynchronized implementation.
- **FR-016**: The repair MUST preserve current behavior when application configuration already contains an executor.
- **FR-017**: The implementation MUST add one module-level `threading.Lock` and MUST NOT add another synchronization primitive.
- **FR-018**: The deterministic regression test MUST replace the executor constructor and application configuration with controlled test doubles.
- **FR-019**: The deterministic regression test MUST coordinate the first configuration read for each caller before any caller can construct an executor.
- **FR-020**: The implementation MUST add one issue-specific changelog fragment under `changelog.d/`.
- **FR-021**: Planning MUST NOT create the changelog fragment. Implementation MUST create it after the code and test changes.

### Scope Boundaries

**In scope**:

- Synchronization of lazy executor initialization in `web_portal/routes/operations.py`.
- One deterministic regression test for concurrent first access.
- One issue-specific changelog fragment during implementation.
- Preservation of existing route behavior and PR #4065 route lines.

**Out of scope**:

- Changes to executor behavior, worker count, operation scheduling, or shutdown behavior.
- Changes to `web_portal/services/operation.py`.
- New executor accessors, aliases, wrappers, or compatibility paths.
- General portal load testing or changes to server worker configuration.
- Changes to event streaming, Mist API access, or browser controls.
- Product code changes during the planning workflow.
- Changelog fragment creation during the planning workflow.

### Key Entities

- **Operation executor**: The single application-scoped object that owns operation state and its worker pool.
- **Initialization lock**: The module-scoped synchronization control that permits one construction path at a time.
- **Application configuration**: The shared location that stores the initialized executor for all Operations routes.
- **Concurrent caller**: A request that reaches `_get_executor()` while no executor is visible during its first check.

## Success Criteria

### Measurable Outcomes

- **SC-001**: A forced race with at least two concurrent first callers constructs exactly one operation executor in every test run.
- **SC-002**: Every caller in the forced race receives the same executor instance.
- **SC-003**: Concurrent first run requests create no more than one operation worker pool.
- **SC-004**: Requests made after initialization cause zero additional executor constructions.
- **SC-005**: The regression test fails when executor initialization has no synchronization and passes with the required synchronization.
- **SC-006**: All route lines introduced by PR #4065 remain unchanged.
- **SC-007**: No file under `web_portal/services/` changes for this feature.

## Assumptions

- The Flask application configuration remains the source of truth for the application-scoped executor.
- One process can hold one application instance and one executor. Cross-process executor sharing is outside this feature.
- The existing executor constructor continues to create and own one worker pool.
- The regression test can replace the executor constructor with a controlled test constructor that counts calls.
- The regression test can coordinate concurrent callers without external services or production credentials.
- PR #4065 can change the same route module, so implementation work must preserve its route additions during conflict resolution.
