# Feature Specification: Menu 209 HTTP Error Handling

**Feature Branch**: `jmorrison-juniper-false-success-family-4028`

**Created**: 2026-10-06

**Status**: Draft

**Input**: User description: "Issue #4028: Menu 209 exports HTTP 404 as a successful CSV row."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Report Missing Beacon as Failure (Priority: P1)

As a network operations center engineer, I need menu 209 to report a missing beacon as a failed operation. The operation must not convert the error response into exported data.

**Why this priority**: A false success hides an invalid beacon identifier and creates a CSV row that looks like valid Mist data.

**Independent Test**: Run menu 209 with a valid site and a beacon identifier that returns HTTP 404. Confirm that the operation fails and creates no export.

**Acceptance Scenarios**:

1. **Given** a valid site and an unknown beacon identifier, **When** `getSiteBeacon` returns HTTP 404, **Then** menu 209 reports `! Error fetching site beacon detail: HTTP 404 from <url>`.
2. **Given** the HTTP 404 response, **When** menu 209 completes its failure path, **Then** it does not call `DataExporter` and does not create a CSV row or file.

---

### User Story 2 - Reject All HTTP Error Responses (Priority: P1)

As an operator, I need every integer status outside HTTP 200-299 to produce a failure. This behavior prevents redirects and errors from appearing as successful data.

**Why this priority**: Only HTTP 200-299 confirms that the request completed successfully.

**Independent Test**: Return an HTTP 500 native response from `getSiteBeacon`. Confirm that the operation fails before payload normalization and export.

**Acceptance Scenarios**:

1. **Given** valid site and beacon identifiers, **When** `getSiteBeacon` returns HTTP 500, **Then** menu 209 reports a failed operation.
2. **Given** any native `getSiteBeacon` response with an integer status outside 200-299, **When** menu 209 evaluates the response, **Then** it does not read or normalize the payload and does not call `DataExporter`.

---

### User Story 3 - Preserve Successful Export Behavior (Priority: P2)

As an operator, I need successful beacon responses to keep their current export behavior. The fix must not change valid exports or successful empty results.

**Why this priority**: Menu 209 already provides the correct result for successful responses. The defect fix must change only HTTP error handling.

**Independent Test**: Return a successful dictionary response and a separate successful empty response. Confirm that each response follows its existing result path.

**Acceptance Scenarios**:

1. **Given** `getSiteBeacon` returns an HTTP 2xx response with a beacon dictionary, **When** menu 209 processes the response, **Then** it exports one normalized row through `DataExporter`.
2. **Given** `getSiteBeacon` returns an HTTP 2xx response with no beacon data, **When** menu 209 processes the response, **Then** it reports the existing successful no-data result and does not call `DataExporter`.
3. **Given** a successful dictionary response, **When** menu 209 exports the row, **Then** the existing API function name, primary-key behavior, and filename remain unchanged.
4. **Given** a response double with no integer status, **When** menu 209 processes the response, **Then** it preserves the current payload path.

### Edge Cases

- A response can contain any body shape with an HTTP 2xx status. Menu 209 does not inspect the body during status classification.
- A native HTTP 1xx, 3xx, 4xx, or 5xx response is a failure and produces no export.
- A 429 exception continues through the existing bounded adaptive retry path.
- A later non-429 exception after a 429 retry preserves the existing first-error behavior.
- A response with an absent or non-integer status follows the existing payload handling or exception handling.
- The 404 body shape is irrelevant and never enters classification or normalization.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Menu 209 MUST inspect the native `getSiteBeacon` response status before payload normalization.
- **FR-002**: Menu 209 MUST treat an integer status from 200 through 299 as successful.
- **FR-003**: Menu 209 MUST treat every other integer status as a failed operation.
- **FR-004**: An absent or non-integer status MUST preserve the current compatibility payload path.
- **FR-005**: Status classification MUST NOT inspect or log the response body or `data["detail"]`.
- **FR-006**: An HTTP failure MUST NOT read the response body or enter payload normalization.
- **FR-007**: An HTTP failure MUST NOT call `DataExporter`.
- **FR-008**: An HTTP failure MUST NOT create a CSV row or any other export artifact.
- **FR-009**: A failed response MUST emit exactly `! Error fetching site beacon detail: HTTP <status> from <url>` as the operator-facing line.
- **FR-010**: The failure URL MUST use the response URL, with `the requested path` when the URL is absent.
- **FR-011**: An HTTP 2xx dictionary response MUST continue to export one normalized beacon row.
- **FR-012**: An empty HTTP 2xx response MUST continue to use the existing successful no-data handling and MUST NOT call `DataExporter`.
- **FR-013**: The existing adaptive retry behavior for 429 exceptions MUST remain unchanged.
- **FR-014**: Menu 209 registration and portal controls MUST remain unchanged.
- **FR-015**: The `getSiteBeacon` primary-key strategy MUST remain unchanged.
- **FR-016**: The existing `SiteBeacon_<site_id>_<beacon_id>.csv` filename behavior MUST remain unchanged for successful exports.
- **FR-017**: The operation MUST preserve the current site and beacon input flow.
- **FR-018**: The operation MUST preserve the current failure handling for non-HTTP exceptions.

### Mist Cloud Transport Requirements

- Menu 209 MUST continue to use `mistapi.api.v1.sites.beacons.getSiteBeacon`.
- The native response status MUST remain available until the operation classifies the response as successful or failed.
- Direct HTTP access is out of scope because the Mist API method exists in `mistapi`.
- Contract tests MUST prove HTTP 404 and HTTP 500 failure, successful dictionary export, successful empty-response handling, and compatibility handling for absent or non-integer status.
- Contract tests MUST prove that HTTP failures create no exporter call.
- Contract tests MUST prove that the existing adaptive retry path still handles 429 exceptions.
- Contract tests MUST prove that status classification never reads or logs the response body or `data["detail"]`.
- Failure output and logs MUST not expose credentials, response bodies, or request authorization data.

### Key Entities

- **Native beacon response**: The original Mist response with its HTTP status, URL, and payload.
- **Beacon payload**: The beacon dictionary or empty successful data that can enter normalization only after status validation.
- **Operation result**: The failed, successful export, or successful no-data outcome shown to the operator.
- **Export artifact**: The existing successful output that uses the current filename and primary-key behavior.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In all tested HTTP 404 and HTTP 500 cases, menu 209 reports failure and creates zero export rows.
- **SC-002**: For every tested integer status outside 200-299, `DataExporter` receives zero calls.
- **SC-003**: In the HTTP 404 reproduction case, the operator output is exactly `! Error fetching site beacon detail: HTTP 404 from <url>`.
- **SC-004**: In all tested HTTP 2xx dictionary cases, menu 209 exports exactly one row with the existing filename and data identity.
- **SC-005**: In all tested empty HTTP 2xx cases, menu 209 reports no data and creates zero export artifacts.
- **SC-006**: Statusless and non-integer response doubles preserve the current payload path.
- **SC-007**: Existing tests for menu registration, portal controls, primary keys, filenames, and 429 exception retries continue to pass without changed expectations.

## Assumptions

- Issue #4028 defines HTTP 404 as a failed operation, not a successful no-data result.
- The native Mist response normally exposes a readable HTTP status and URL before payload normalization.
- Successful no-data behavior means that the operation completes without an export artifact.
- Only menu 209 and its `getSiteBeacon` response classification are in scope.
- Changes to menu registration, portal controls, primary keys, filenames, and operator prompts are out of scope.
