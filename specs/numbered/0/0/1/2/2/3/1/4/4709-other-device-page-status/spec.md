# Feature Specification: Other-device event page status

**Feature Branch**: `jmorrison-juniper-other-device-event-audit`

**Created**: 2026-11-09

**Status**: Specified

**Input**: Repair issue #4709 after preserving the local #1794 commit.

## User Scenarios & Testing

### User Story 1 - Reject incomplete exports (Priority: P1)

An operator must receive a failure message when any event page fails.

**Why this priority**: A partial export can cause an incorrect operational decision.

**Independent Test**: Return a failed first or later page and confirm that no writer runs.

**Acceptance Scenarios**:

1. **Given** a first-page 403 or 503, **When** the export runs, **Then** it reports failure instead of no data.
2. **Given** successful records followed by a 503 with an empty body, **When** pagination ends, **Then** no partial export is written.
3. **Given** private response or exception text, **When** a request fails, **Then** exporter logs contain no private text.

### User Story 2 - Preserve complete results (Priority: P2)

An operator retains successful empty, single-page, and multiple-page results.

**Why this priority**: The repair must preserve complete event exports.

**Independent Test**: Supply successful pages and verify every normalized row and the output metadata.

**Acceptance Scenarios**:

1. **Given** a valid empty response, **When** the export runs, **Then** it reports no data without writing.
2. **Given** complete pages, **When** the export runs, **Then** it writes all rows once.
3. **Given** a local transform or writer defect, **When** persistence runs, **Then** the original exception reaches the caller.

### Edge Cases

- Both list pages and search pages with a `results` list require validation.
- A missing status, missing promised page, malformed body, or malformed row list cannot prove completeness.
- Selection cancellation must not start a request.
- Repeated or invalid cursors must stop the read without another request or a partial export.

## Requirements

### Functional Requirements

- **FR-001**: Check every page for a successful HTTP status before accepting its rows.
- **FR-002**: Never write or report a complete export after a failed or missing page.
- **FR-003**: Preserve complete empty, single-page, and multiple-page results and output metadata.
- **FR-004**: Preserve sanitized request-failure reporting and local defect propagation from #1794.
- **FR-005**: Verify the behavior offline with real SDK responses, blocked DNS and sockets, and mocked storage.
- **FR-006**: Reject repeated or invalid cursors and malformed records without exposing private data.

### Mist Cloud Transport Requirements

Retain `searchSiteOtherDeviceEvents` and use the SDK `get_next` helper for subsequent requests.
Do not introduce a transport, change a shared helper, or change the output schema.
Inspect shared helpers before implementation and verify the installed SDK contract offline.

### Key Entities

- **Page**: One status, record payload, and optional next-page link.
- **Complete result**: Rows from every successful page, available only after pagination completes.

## Success Criteria

### Measurable Outcomes

- **SC-001**: All failed-page scenarios produce zero writer calls and zero completion messages.
- **SC-002**: Every successful page contributes its rows in order exactly once.
- **SC-003**: Exporter logs contain zero synthetic private response or exception strings.

## Assumptions

- A successful event payload is a list or an object with a list-valued `results` field.
- Only HTTP 2xx proves success. Missing status cannot prove completeness.
- Third-party SDK logging remains outside this exporter-only change.
