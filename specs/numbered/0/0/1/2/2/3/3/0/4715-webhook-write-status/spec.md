# Feature Specification: Webhook write status

**Feature Branch**: `jmorrison-juniper-webhook-write-status`

**Created**: 2026-11-09

**Status**: Ready

**Input**: Issue #4715 requires an explicit failure when organization webhook delivery storage fails.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read the correct export result (Priority: P1)

The operator must distinguish a failed write from a completed export.

**Why this priority**: A false completion message can hide missing delivery records.

**Independent Test**: Supply synthetic deliveries and control the storage result without an external connection.

**Acceptance Scenarios**:

1. **Given** delivery records, **When** storage reports failure, **Then** the exporter reports failure without a completion or persistence message.
2. **Given** delivery records, **When** storage reports success, **Then** the exporter retains its completion message.
3. **Given** no delivery records, **When** the exporter runs, **Then** it retains its empty-result message without a storage request.

### Edge Cases

- A storage exception retains the existing entrypoint error behavior.
- A rejected cloud response does not reach pagination or storage.
- The public result remains unchanged for success, failure, and empty input.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Report a failed write explicitly, without a completion or persistence message.
- **FR-002**: Preserve the successful export message and record count.
- **FR-003**: Preserve the empty-result message without a storage request.
- **FR-004**: Preserve the public return contract and storage operation identifier.
- **FR-005**: Preserve the existing entrypoint and error behavior.

### Key Entities

- **Delivery**: A synthetic organization webhook delivery record.
- **Write result**: The storage result that determines whether completion can be reported.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every simulated failed write produces one error and zero completion or persistence messages.
- **SC-002**: Every simulated successful write retains one completion message with the correct record count.
- **SC-003**: Every empty result produces zero storage requests.
- **SC-004**: Verification makes zero socket or DNS attempts.

## Assumptions

- The existing writer returns a Boolean result.
- Only the reserved exporter, its tests, this specification, and the unique release fragment can change.
- Pagination, shared infrastructure, and other exporters remain outside this repair.
- The assigned base is `3964d21d03f9f5717cb8eafb7272ecff21f5362a`.
- Publication requires a separate decision.
