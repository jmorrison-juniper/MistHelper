# Feature Specification: WiFi response failures

**Feature Branch**: `jmorrison-juniper-wifi-response-failures`

**Created**: 2026-10-03

**Status**: Implemented locally. Publication remains prohibited.

**Input**: Repair [issue #3743](https://github.com/jmorrison-juniper/MistHelper/issues/3743) locally, within the coordinator's exact reservations.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Report a failed response (Priority: P1)

The operator selects menu 64 and selects a site. A failed response must produce a failure notice, not an empty-data export.

**Why this priority**: A normal empty-data file hides a failed request.

**Independent Test**: Supply controlled failed client or session responses. Count every final writer and verify the failure notice.

**Acceptance Scenarios**:

1. **Given** an empty or malformed response body, **When** the operator runs the export, **Then** no final writer runs.
2. **Given** a refused first or later page, **When** the operator runs the export, **Then** no partial export occurs.
3. **Given** an unavailable or invalid status, **When** the operator runs the export, **Then** the export reports a failure.

### User Story 2 - Preserve complete successful data (Priority: P2)

The operator receives all client and session records in their existing order. The export retains site information and session details.

**Why this priority**: The repair must not change successful records or output selection.

**Independent Test**: Supply complete single-page and multiple-page responses. Compare record order, site information, session counts, and final writer selection.

**Acceptance Scenarios**:

1. **Given** successful pages, **When** the operator runs the export, **Then** every accepted record reaches the existing final writer.
2. **Given** genuinely empty successful responses, **When** the operator runs the export, **Then** the existing empty-data placeholder remains valid.

### User Story 3 - Identify the failed request (Priority: P3)

The operator sees the failed endpoint, site, page, and HTTP status. Parse failures include useful context without body contents.

**Why this priority**: The operator needs the failed request's scope to investigate the problem.

**Independent Test**: Inspect the exporter's error records after controlled failures. Verify scope, status, page, and safe parse context.

**Acceptance Scenarios**:

1. **Given** a malformed body, **When** the export reports a failure, **Then** the notice identifies the page without exposing the body.
2. **Given** a refused response, **When** the export reports a failure, **Then** the notice retains the actual HTTP status.

### Edge Cases

- Both endpoints can fail on their first or later pages.
- A successful status can accompany an empty body, malformed JSON, or an invalid record shape.
- A response can lack an integer HTTP status.
- A valid empty page can still contain a next-page link.
- List bodies and search bodies can contain complete successful records.
- A missing later response or a repeated next-page link cannot prove a complete export.
- Client and session fields can overlap. Existing field precedence remains unchanged.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Validate each page's HTTP status before accepting its body.
- **FR-002**: Reject unavailable, invalid, and unsuccessful statuses. Never assume HTTP 200.
- **FR-003**: Reject empty bodies, malformed JSON, invalid successful shapes, and non-object records.
- **FR-004**: Stop before final output if either endpoint loses any page.
- **FR-005**: Preserve valid empty-data behavior for complete successful responses.
- **FR-006**: Preserve successful list and search-result shapes.
- **FR-007**: Preserve next-page links, page order, and record order.
- **FR-008**: Preserve site information, session joins, session counts, and field precedence.
- **FR-009**: Preserve output names and final writer selection. Do not repair CSV suffix handling.
- **FR-010**: Report the endpoint, site, page, status, and safe parse context through existing error notices.
- **FR-011**: Use controlled native SDK responses and real final writers for independent runtime evidence.
- **FR-012**: Keep every unreserved path unchanged and keep all publication windows closed.

### Key Entities *(include if feature involves data)*

- **Response page**: One request's status, parsed records, raw-body evidence, and next-page link.
- **Site stamp**: The existing site identifier and site name.
- **Merged record**: A client record or a session-only record with the existing site and session information.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All four original failure categories produce zero final output writes after the repair.
- **SC-002**: First-page and later-page failures from both endpoints produce zero final CSV, router, and SQLite writes.
- **SC-003**: Complete successful controls retain exact record order, site information, session counts, and writer selection.
- **SC-004**: Native runtime cases make zero live HTTP requests.
- **SC-005**: Protected file hashes and every unmodified exporter method remain unchanged.

## Assumptions

- The issue's ownership comment grants local preparation only.
- The app-created branch starts from main `0317b944388fb9f927ce4a20368070408542c4b1`.
- The separate suffix repair remains outside this feature.
- The coordinator released three coupled fixtures in `tests/unit/export/test_wifi_clients_exporter.py`.
- Every other existing test, shared helper, policy input, and dependency input remains read-only.
- No new environment setting, schema, menu, endpoint integration, or browser interface is necessary.
