# Feature Specification: Busy-site upgrade refusal

**Feature Branch**: `jmorrison-juniper-fix-busy-site-refusal-4540`

**Created**: 2026-11-06

**Status**: Draft

**Input**: Issue #4540 reports that a refusal to start an upgrade on a busy site does not appear because the browser cannot call its refusal handler.

## User Scenarios & Testing

### User Story 1 - Understand a busy-site refusal (Priority: P1)

An operator starts an organization upgrade on sites that another operation already holds. The portal explains which site is held, names the owning operation, and links to its progress page.

**Why this priority**: The operator needs to understand why the start failed and how to inspect the operation that owns the site.

**Independent Test**: Start one simulated operation, submit another operation for the same sites, and inspect the refusal and progress link.

**Acceptance Scenarios**:

1. **Given** an operation holds a selected site, **When** the operator starts another operation for that site, **Then** the portal shows the held site and owning operation.
2. **Given** the refusal includes a valid progress path, **When** the portal displays the refusal, **Then** it provides one link to the owning operation.
3. **Given** the second start is refused, **When** the refusal appears, **Then** the confirmation field is cleared and the start control stays disabled.

## Edge Cases

- If the refusal does not include a valid progress path, the portal shows the refusal without a link.
- The portal does not display the internal refusal code as operator-facing text.

## Requirements

### Functional Requirements

- **FR-001**: The portal MUST show the server message when another operation holds a selected site.
- **FR-002**: The portal MUST name the owning operation when the server provides its identifier.
- **FR-003**: The portal MUST link only to a valid progress path for the owning operation.
- **FR-004**: The portal MUST clear the confirmation field and keep the refused start closed.
- **FR-005**: The portal MUST NOT show the internal refusal code as the refusal message.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Every simulated busy-site refusal displays the held site and owning operation.
- **SC-002**: Every refusal with a valid progress path displays exactly one link to the owning operation.
- **SC-003**: Every refused start leaves its confirmation field empty and its start control disabled.
- **SC-004**: No busy-site refusal displays its internal error code to the operator.

## Assumptions

- The service supplies a safe refusal message and a progress path when it can identify the owning operation.
- A refused start does not create or alter an operation.
