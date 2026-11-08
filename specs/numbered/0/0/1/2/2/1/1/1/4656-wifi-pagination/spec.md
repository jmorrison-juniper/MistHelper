# Feature Specification: WiFi Pagination Failure Handling

**Feature Branch**: `jmorrison-juniper-potential-disco`

**Created**: 2026-11-07

**Status**: Draft

**Input**: User description: "Resolve related WiFi pagination failures by retaining first-page records and reporting partial results after a later transport timeout, rejecting later HTTP error responses, and preserving complete pagination and first-page error behavior."

## User Scenarios & Testing

### User Story 1 - Keep WiFi data after a later timeout (Priority: P1)

An operator starts a WiFi export. A later page request times out after an earlier page succeeds. The operator receives the earlier records and a clear notice that the export is partial.

**Why this priority**: A later network failure must not discard data that the service already returned.

**Independent Test**: Return one valid first page, then raise a controlled timeout for the next page. Check the exported records and the partial-result notice.

**Acceptance Scenarios**:

1. **Given** a successful first page with records and a later transport timeout, **When** the operator runs the export, **Then** the export keeps the first-page records and reports a partial result.
2. **Given** all pages succeed, **When** the operator runs the export, **Then** the export contains all records and reports no partial result.

### User Story 2 - Reject a failed later WiFi page (Priority: P1)

An operator starts a WiFi export. A later page returns an HTTP failure. The export reports the failure and does not present the response as complete data or as a valid empty result.

**Why this priority**: A failed page must not create output that appears complete.

**Independent Test**: Return a successful first page, then a controlled HTTP 403 or 503 response. Check that the exporter rejects the failed page and does not create success-shaped output.

**Acceptance Scenarios**:

1. **Given** a successful first page and a later HTTP 403 response, **When** the operator runs the export, **Then** the export reports failure and creates no success-shaped output.
2. **Given** a successful first page and a later HTTP 503 response, **When** the operator runs the export, **Then** the export reports failure and creates no success-shaped output.

### User Story 3 - Preserve first-page failure behavior (Priority: P2)

An operator starts a WiFi export, but the first page fails. The exporter keeps its current failure behavior and does not create a valid-empty placeholder.

**Why this priority**: The pagination change must not alter the existing response checks or valid-empty behavior.

**Independent Test**: Return a controlled first-page HTTP failure and a controlled valid-empty response in separate runs. Check each existing result.

**Acceptance Scenarios**:

1. **Given** a failed first page, **When** the operator runs the export, **Then** the export reports failure and creates no placeholder.
2. **Given** successful empty pages, **When** the operator runs the export, **Then** the exporter keeps its current valid-empty result behavior.

### Edge Cases

- A failure before any page succeeds must keep the existing first-page error behavior.
- A timeout after one or more successful pages must retain all records from those pages and identify the result as partial.
- An HTTP error on any later page must not be treated as a successful page, an empty result, or a partial successful export.
- A malformed or empty first-page response must keep the current failure behavior.
- An empty result is valid only when all required pages complete successfully.

## Requirements

### Functional Requirements

- **FR-001**: The exporter MUST retain records from every page that completed successfully before a later transport timeout.
- **FR-002**: The exporter MUST clearly identify an export with retained records after a later transport timeout as partial.
- **FR-003**: The exporter MUST reject an HTTP error response from any later page and MUST NOT present the run as complete or valid-empty.
- **FR-004**: The exporter MUST preserve complete results when every page succeeds.
- **FR-005**: The exporter MUST preserve existing behavior for first-page HTTP errors, malformed responses, and successful empty results.
- **FR-006**: Tests MUST use controlled SDK responses and sessions and MUST make no live Mist request.

### Mist Cloud Transport Requirements

- The feature uses the `searchSiteWirelessClients` and `searchSiteWirelessClientSessions` Mist API methods.
- The feature MUST use the supported `mistapi` SDK for each request and MUST NOT send direct HTTP requests to Mist endpoints.
- Controlled SDK evidence MUST show why `mistapi.get_all` cannot meet the required partial-result and failed-page behavior.
- Tests MUST verify SDK session use, endpoint parity, later-page timeout handling, later-page HTTP failure handling, and safe failure reporting.
- Tests MUST verify that failure reporting does not expose credentials or response secrets.

### Key Entities

- **WiFi page**: One ordered set of client or session records returned for an export request, with its request outcome and next-page state.
- **WiFi export result**: The records collected for one site, classified as complete, partial, valid-empty, or failed.

## Success Criteria

### Measurable Outcomes

- **SC-001**: In every controlled timeout case after a successful page, the export retains all records from successful pages and clearly reports a partial result.
- **SC-002**: In every controlled later-page HTTP 403 or 503 case, the exporter rejects the run and creates no output that appears complete or valid-empty.
- **SC-003**: In every all-success case, the export contains all page records and keeps existing complete-result behavior.
- **SC-004**: First-page failure and successful empty-result tests retain their existing outcomes.
- **SC-005**: All pagination tests run with controlled SDK sessions and make zero live HTTP or socket calls.

## Assumptions

- A later transport timeout can produce a useful partial result when one or more earlier pages succeeded.
- A later HTTP error invalidates the run and is not eligible for partial export.
- The existing first-page failure and successful empty-result behaviors remain the compatibility baseline.
- Controlled native SDK responses provide sufficient evidence. No Mist credentials or live cloud access are needed.
