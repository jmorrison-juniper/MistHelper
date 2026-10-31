# Feature Specification: Busy-site refusal

**Feature Branch**: `jmorrison-juniper-4540-busy-site-refusal`

**Created**: 2026-10-31

**Status**: Approved for implementation

**Input**: Fix issue #4540 only. Restore the busy-site refusal message and owning-operation link.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read a busy-site refusal (Priority: P1)

An operator submits a multi-site plan for a site that another operation owns.
The portal explains the refusal and links to the owning operation.

**Why this priority**: The current script error hides the refusal and its recovery link.

**Independent Test**: Return a synthetic busy-site refusal while the operator submits the confirmation form.

**Acceptance Scenarios**:

1. **Given** a confirmed plan, **When** another operation owns a site, **Then** the portal displays the refusal and owning-operation link.
2. **Given** a refused plan, **When** the operator examines the form, **Then** the confirmation is empty and disabled.
3. **Given** an absent or unsafe owning-operation address, **When** the portal displays the refusal, **Then** it creates no link.

### Edge Cases

- The response can omit the owning-operation address.
- The response can contain an external address that the portal must not link.
- A refusal must cause no browser page error or repeated submission.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Display the refusal message and the permitted owning-operation link.
- **FR-002**: Clear and disable the confirmation field and keep the start button disabled.
- **FR-003**: Preserve the existing address validation and replay-refusal behavior.
- **FR-004**: Exercise a synthetic refusal without live cloud requests or a real firmware write.
- **FR-005**: Preserve the released journey file's retrying full-viewport wait.
- **FR-006**: Do not edit PR #4541's workflow, fixtures, or parity records.

### Key Entities

- **Refusal**: A message and an optional address for the operation that owns the site.
- **Confirmation form**: The plan that must remain closed after the refusal.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every synthetic busy-site case displays the exact refusal message with zero browser page errors.
- **SC-002**: A permitted address produces exactly one owning-operation link.
- **SC-003**: Absent and unsafe addresses produce zero owning-operation links.
- **SC-004**: Every refused confirmation remains empty and disabled, with its start control disabled.

## Assumptions

- The existing refusal message and response shape remain authoritative.
- The handoff permits changes only to the named journey file among PR #4541's files.
- The app-managed branch remains active. Specification selection stays command-scoped.
- Merge, auto-merge, deployment, and live cloud requests remain outside this change.
