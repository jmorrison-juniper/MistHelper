# Feature Specification: Retry site scope

**Feature Branch**: `jmorrison-juniper-retry-site-scope`

**Created**: 2026-10-31

**Status**: Approved for implementation

**Input**: Issue #3396 and the bounded implementation request.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Confirm only planned retry sites (Priority: P1)

An operator retries a settled operation and clears one device family.
The confirmation and submission must include only sites with a remaining planned device.

**Why this priority**: An exact confirmation prevents unnecessary captures and site locks during destructive firmware work.

**Independent Test**: Retry a failed switch at site A and a failed access point at site B.
Clear switches, save, confirm, and submit through isolated test services.

**Acceptance Scenarios**:

1. **Given** both failed devices, **When** switches are cleared, **Then** the saved parent and each child name only site B.
2. **Given** that saved retry, **When** confirmation opens, **Then** it shows one site, one device, and a pre-check row for B only.
3. **Given** a verified capture at B only, **When** the operator types CONFIRM, **Then** submission checks and locks B only.
4. **Given** that retry, **When** save and submission finish, **Then** the operator selection remains A and B.

### User Story 2 - Preserve complete scopes (Priority: P2)

Plain saves and retries with a planned device at every remaining site keep their existing site scope.

**Why this priority**: The repair must not change unrelated selection rules or safety controls.

**Independent Test**: Save and submit both plain and complete retry plans with two sites.

**Acceptance Scenarios**:

1. **Given** a plain save, **When** every selected site has a target, **Then** both sites remain in the saved scope.
2. **Given** a complete retry, **When** both families remain selected, **Then** both sites remain in confirmation, pre-checks, and locks.

### Edge Cases

- A retry device leaves its site before save. That site leaves the saved scope if no target remains.
- A retry with no remaining target still fails through existing validation.
- A changed planned-site order or missing planned site must fail exact-context validation.
- A site outside the retry plan needs no capture and must not prevent submission through an unrelated lock.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Retry saves MUST derive saved site IDs and names from the aggregate targets after family filtering.
- **FR-002**: Confirmation counts and pre-check rows MUST use the saved effective site scope.
- **FR-003**: Submission pre-checks, exact-context validation, and lock acquisition MUST use that same scope.
- **FR-004**: The operator selection MUST remain unchanged by save, confirmation, and submission.
- **FR-005**: Plain saves and complete retries MUST preserve their existing behavior.
- **FR-006**: Authentication, typed confirmation, lock tokens, audit calls, idempotency, and durable transactions MUST remain intact.
- **FR-007**: Tests MUST block external connections and use no live credentials or firmware operations.

### Key Entities

- **Operator selection**: The sites the operator selected before the retry save.
- **Effective retry scope**: The ordered selected sites that have planned targets.
- **Durable operation**: The saved parent, its site names, and its explicit child targets.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Clearing switches in the two-site example produces exactly one saved site and one planned device.
- **SC-002**: Confirmation and submission each check exactly one site in that example.
- **SC-003**: Submission acquires zero locks at site A and one lock at site B.
- **SC-004**: All regression scenarios preserve the operator selection and complete two-site plans.

## Assumptions

- Existing validated targets identify their sites and preserve the approved selected-site order.
- Existing selection routes invalidate saved choices when the operator changes the site selection.
- Human review is required. The pull request remains a draft, with auto-merge disabled.
