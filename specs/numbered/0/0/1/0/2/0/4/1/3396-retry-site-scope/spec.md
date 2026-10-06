# Feature Specification: Retry Site Scope

**Feature Branch**: `jmorrison-juniper-assess-3396-stale-site-retry`

**Created**: 2026-10-06

**Status**: Implemented

This status means that the specified product behavior exists. The task record
tracks the separate local commit and validation work.

**Input**: MistHelper issue #3396

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Confirm the Actual Retry Scope (Priority: P1)

As an operator, I need the retry confirmation to show only sites that still
have planned devices after I filter device families.

**Why this priority**: Firmware upgrades are destructive. The typed
confirmation must describe the exact change scope.

**Independent Test**: Start a retry for sites A and B. Clear the only planned
device family at site A. Verify that confirmation shows one site and the
remaining device count.

**Acceptance Scenarios**:

1. **Given** a retry has a switch at site A and an access point at site B,
   **When** the operator clears switches, **Then** confirmation shows site B
   only.
2. **Given** the same filtered retry, **When** the confirmation precheck table
   appears, **Then** each row belongs to site B.
3. **Given** the same filtered retry, **When** the warning describes the
   affected scope, **Then** it does not include site A.

---

### User Story 2 - Save and Lock the Actual Retry Scope (Priority: P1)

As an operator, I need the saved retry and its site locks to match the devices
that the retry can change.

**Why this priority**: A stale site can block another operator and can request
an unnecessary capture at an unaffected site.

**Independent Test**: Save and submit the filtered retry. Verify that the
parent operation, child operations, submission checks, and lock requests use
site B only.

**Acceptance Scenarios**:

1. **Given** site A has no planned retry device after filtering, **When** the
   retry is saved, **Then** the parent operation stores only site B.
2. **Given** the saved retry contains only site B, **When** child operations
   are inspected, **Then** each child site identifier belongs to site B.
3. **Given** the operator submits the retry, **When** submission checks and
   lock acquisition run, **Then** they use site B only.
4. **Given** the saved retry context changes before submission, **When** exact
   context validation runs, **Then** it compares against the durable site B
   scope.

---

### User Story 3 - Preserve Selection and Valid Saves (Priority: P2)

As an operator, I need filtering to narrow the retry operation without changing
my selected-site choices or valid upgrade behavior.

**Why this priority**: The correction must not change normal saves or retries
where each selected site still has a target.

**Independent Test**: Compare plain saves, fully targeted retries, and filtered
retries. Verify that only the filtered retry receives a narrower durable scope.

**Acceptance Scenarios**:

1. **Given** the operator selected sites A and B, **When** filtering removes
   site A from the retry plan, **Then** the selected-site state still contains
   sites A and B.
2. **Given** a plain multi-site save, **When** the operation is saved,
   **Then** its existing site-scope behavior remains unchanged.
3. **Given** a retry where each selected site has a planned target, **When**
   the operation is saved, **Then** each remaining site stays in the durable
   scope.
4. **Given** a retry where filtering removes all planned devices, **When** the
   operator reviews or saves it, **Then** the existing empty-plan protection
   stops the destructive path.

### Edge Cases

- A site has several selected devices, but filtering removes every device at
  that site.
- A site has several device families, and at least one planned family remains.
- Two planned devices at one site must produce one durable site entry.
- Planned targets arrive in an order that differs from selected sites.
- A planned target has an identifier, but its selected-site name is missing.
- A retry becomes stale between confirmation and submission.
- Lock acquisition fails for the only effective site.
- A repeated submission uses the existing idempotency protection.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Retry saves MUST derive the effective site scope from planned
  aggregate targets after device-family filtering.
- **FR-002**: Retry saves MUST leave the operator's selected-site state
  unchanged.
- **FR-003**: The durable parent operation MUST store only unique sites that
  contain at least one planned retry device.
- **FR-004**: The durable parent operation MUST keep each effective site name
  aligned with its site identifier.
- **FR-005**: The durable effective scope MUST preserve the selected-site order
  for sites that retain planned targets.
- **FR-006**: Child operations MUST contain only site identifiers represented
  by their planned devices.
- **FR-007**: The confirmation site count MUST use the durable effective site
  scope.
- **FR-008**: Confirmation precheck rows MUST use the durable effective site
  scope.
- **FR-009**: Submission prechecks MUST use the durable effective site scope.
- **FR-010**: Exact-context validation MUST compare the submitted retry with
  the durable effective site scope.
- **FR-011**: Site-lock acquisition MUST request locks only for the durable
  effective site scope.
- **FR-012**: Authentication and authorization behavior MUST remain unchanged.
- **FR-013**: Typed confirmation MUST remain required before the firmware
  upgrade submission.
- **FR-014**: Site-lock tokens and lock ownership checks MUST remain unchanged.
- **FR-015**: Audit calls MUST retain their existing timing and information.
- **FR-016**: Idempotency and durable transaction behavior MUST remain
  unchanged.
- **FR-017**: Plain multi-site saves MUST retain their existing behavior.
- **FR-018**: Retries MUST retain each site that has at least one planned
  target.
- **FR-019**: Tests MUST use fakes and MUST block external connections.
- **FR-020**: Tests MUST prove the filtered retry stores only site B in parent
  site identifiers and names.
- **FR-021**: Tests MUST prove child site identifiers, confirmation counts,
  confirmation prechecks, submission prechecks, and lock calls use site B only.
- **FR-022**: The change MUST remain within the approved issue #3396 delivery
  boundary.
- **FR-023**: If the correction requires another production component, work
  MUST stop for a scope decision.

### Mist Cloud Transport Requirements

- The feature MUST add no new Mist REST method or direct HTTP request.
- Existing authentication and Mist transport behavior MUST remain unchanged.
- Contract tests MUST use controlled fakes for all external service behavior.
- Contract tests MUST fail if any external network connection is attempted.
- Test evidence MUST verify failure safety without credentials or secrets.

### Operational Store Requirements

- The existing run store MUST fail closed when a write or compare-and-set does
  not verify persistence.
- The existing ArangoDB record and CSV backup behavior remains unchanged.
- Recovery MUST use the existing durable operation, retry lineage, and
  idempotent submission records.
- The portal MUST keep the existing unlimited retention policy for upgrade
  operations and captures.
- This change MUST add no store schema, backup format, recovery path, or
  retention action.

### Key Entities

- **Selected Site Scope**: The sites that the operator chose before retry
  device-family filtering.
- **Planned Aggregate Target**: A retry device that remains after filtering,
  with its effective site identifier.
- **Durable Effective Scope**: The unique site identifiers and names stored on
  the parent operation for planned retry targets.
- **Child Operation**: A device-family upgrade action whose site identifiers
  must belong to the durable effective scope.
- **Site Lock**: The exclusive upgrade lock requested for each durable
  effective site.
- **Precheck Record**: A confirmation or submission result for one durable
  effective site.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In the site A and site B filtered retry, 100 percent of parent
  site identifiers and names refer to site B.
- **SC-002**: In that retry, 100 percent of child site identifiers,
  confirmation rows, submission rows, and lock requests refer to site B.
- **SC-003**: The confirmation shows one site and the exact remaining planned
  device count.
- **SC-004**: The operator's selected-site state still contains sites A and B
  after the retry scope is derived.
- **SC-005**: All covered plain-save scenarios produce the same durable scope
  as before this change.
- **SC-006**: All covered retries where each site retains a target keep every
  remaining site.
- **SC-007**: No automated test for this feature makes an external connection
  or uses a live credential.
- **SC-008**: Existing authentication, confirmation, audit, lock-token,
  idempotency, and transaction checks continue to pass.

## Assumptions

- Planned aggregate targets are the authority for the devices that a retry can
  change.
- Site identifiers are stable and unique within one parent operation.
- Effective site names come from the matching selected-site records.
- The existing empty-plan protection remains the authority when no target
  survives filtering.
- The approved delivery boundary is sufficient. No additional production file
  is required by this specification.
- The focused contract tests can observe durable records, prechecks, and lock
  calls through existing fakes.

## Scope

### In Scope

- Derive and store an effective site scope for retry saves only.
- Use that durable scope for confirmation, validation, prechecks, and locks.
- Preserve selected-site state and all existing destructive safeguards.
- Add focused fake-only contract evidence for issue #3396.

### Out of Scope

- Changes to plain-save site selection rules.
- Changes to retry device selection before device-family filtering.
- New Mist cloud requests or authentication behavior.
- Changes to firmware scheduling, audit content, or lock-token design.
- Changes to portal text that are not necessary for the corrected scope.
