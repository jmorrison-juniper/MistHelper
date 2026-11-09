# Feature Specification: Webhook response status

**Feature Branch**: `jmorrison-juniper-webhook-write-status`

**Created**: 2026-11-09

**Status**: Ready

**Input**: Issue #4718 requires failed initial webhook responses to remain errors instead of empty results.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Distinguish failures from empty results (Priority: P1)

The operator must see an error when the initial webhook list or delivery response cannot prove success.

**Why this priority**: An empty-result notice hides an authorization, transport, or cloud failure.

**Independent Test**: Return synthetic native responses from both endpoints and inspect pagination, storage, and messages.

**Acceptance Scenarios**:

1. **Given** a non-2xx initial response, **When** either endpoint returns, **Then** the exporter reports an error without pagination or an empty-result notice.
2. **Given** an absent or invalid status, **When** either endpoint returns, **Then** the exporter reports an error without pagination or storage.
3. **Given** a valid empty response, **When** either endpoint returns, **Then** the exporter retains its normal empty-result notice.
4. **Given** successful records, **When** selection and export run, **Then** the operation preserves selection, output metadata, and the #4715 writer behavior.

### Edge Cases

- Reject Boolean values, numeric strings, floats, and other malformed status values.
- Reject redirects and informational statuses.
- Accept integer statuses from 200 through 299.
- Reject a native transport response that has no status.
- Preserve existing exception handling and public return values.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Validate both initial responses before pagination.
- **FR-002**: Accept only non-Boolean integer statuses from 200 through 299.
- **FR-003**: Report an error for rejected responses without empty, completion, or persistence messages.
- **FR-004**: Preserve valid empty and successful responses, selection, return values, and endpoint metadata.
- **FR-005**: Preserve the #4715 writer-result checks without changing shared pagination or later pages.

### Mist Cloud Transport Requirements

Keep the existing `listOrgWebhooks` and `searchOrgWebhooksDeliveries` SDK endpoints.
Use synthetic native SDK responses without a network or database connection.
Add no direct HTTP transport.

### Key Entities

- **Initial response**: The first SDK result from the list or delivery endpoint.
- **Status**: The integer evidence of a successful initial response.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every rejected initial response produces an error and zero pagination or storage calls.
- **SC-002**: Both valid empty controls retain their existing empty-result notices.
- **SC-003**: Successful selection and failed-writer regression controls retain their required results.
- **SC-004**: All verification records zero socket, DNS, and SQLite attempts.

## Assumptions

- The branch remains based on the verified #4715 commit `520da64195d90c54d5160bae0b7c0422d1dc9cf3`.
- The existing exporter and test remain exclusively reserved for both issues.
- Later pagination responses and shared infrastructure remain outside this repair.
- Publication requires a separate decision.
