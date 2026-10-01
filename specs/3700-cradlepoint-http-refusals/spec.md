# Feature Specification: Cradlepoint HTTP refusals

**Feature Branch**: `jmorrison-juniper-verbose-succotash`

**Created**: 2026-10-01

**Status**: Specified

**Input**: Issue [#3700](https://github.com/jmorrison-juniper/MistHelper/issues/3700)
requires menu 245 to reject HTTP refusals before it constructs or writes a row.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Report a refused request (Priority: P1)

An operator selects the Cradlepoint status operation.
If the cloud refuses the request, the menu reports the HTTP status.
The operation writes no status record.

**Why this priority**: A successful export notice currently hides a refused request.

**Independent Test**: Supply controlled native responses with HTTP `403`, `404`,
`429`, `500`, and `503`. Record the real row and persistence callbacks.

**Acceptance Scenarios**:

1. **Given** a refused response with a dictionary, **When** the operation runs,
   **Then** it reports the exact HTTP status and writes nothing.
2. **Given** a refused response with an empty or list body, **When** the operation
   runs, **Then** it reports a failure instead of an ordinary empty result.
3. **Given** a refusal body with credential markers, **When** the operation
   reports the failure, **Then** its product diagnostics contain none of those markers.

### User Story 2 - Preserve a successful integration status (Priority: P2)

An operator reads a valid HTTP `200` response.
The operation still exports an integration that reports its own configuration error.

**Why this priority**: An integration error differs from an HTTP refusal.

**Independent Test**: Compare the complete exported row, filename, and endpoint
metadata against explicit expected values.

**Acceptance Scenarios**:

1. **Given** HTTP `200` with `last_status` and `error`, **When** the operation
   runs, **Then** the existing row transformation and export notice remain unchanged.
2. **Given** HTTP `200` with an empty or non-dictionary body, **When** the
   operation runs, **Then** the existing empty-result behavior remains unchanged.

### User Story 3 - Report an unavailable transport status (Priority: P3)

An operator receives no trustworthy HTTP status.
The operation reports a transport failure instead of guessing that the cloud returned no status data.

**Why this priority**: A transport failure cannot prove that an integration is absent.

**Independent Test**: Supply the native SDK response for an absent transport
response. Also supply absent and unusable status values.

**Acceptance Scenarios**:

1. **Given** an absent transport response, **When** the operation runs,
   **Then** it reports that the transport status is unavailable.
2. **Given** a status that is absent or unusable, **When** the operation runs,
   **Then** it constructs no row and invokes no persistence callback.

### Edge Cases

- A refusal body can be a dictionary, a list, JSON `null`, or empty bytes.
- A boolean, float, string, or out-of-range integer is not a trustworthy HTTP status.
- A valid non-success status must remain visible, including a redirect.
- A valid HTTP success status is an integer from `200` through `299`.
- A valid integration error field must not determine HTTP success.
- Existing malformed-JSON behavior remains outside this repair.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Check the HTTP status before reading the body or constructing a row.
- **FR-002**: Accept only an integer HTTP status from `200` through `299`.
  Reject valid non-success statuses with their exact status.
- **FR-003**: Name an unavailable transport status explicitly.
  Never substitute HTTP `200` for an absent or unusable status.
- **FR-004**: Keep every refusal inside the menu.
  Include the operation and status in the visible failure.
- **FR-005**: Invoke zero row, persistence, and writer callbacks for a refusal.
  Do not emit an ordinary empty-result notice or a successful export notice.
- **FR-006**: Preserve valid HTTP `200` rows, field transformations, filenames,
  endpoint metadata, and empty-body behavior.
- **FR-007**: Exclude body text, authorization fields, cookies, tokens, and
  configuration credentials from new product diagnostics.
- **FR-008**: Use one endpoint call for each measured operation and zero live requests.
- **FR-009**: Preserve other exporters, shared response helpers, prompts, retry
  behavior, dependencies, database schemas, and primary-key strategies.
- **FR-010**: Prepare a clean local commit only.
  Publication requires the coordinator's explicit verified-main SHA grant.

### Key Entities *(include if feature involves data)*

- **HTTP response**: The supported SDK response holds a transport status and decoded data.
- **Integration status**: A successful response can report an integration configuration error.
- **Export record**: The existing record contains `org_id` and the transformed integration fields.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 30 refusal combinations produce one endpoint call, zero row
  callbacks, zero persistence callbacks, zero writer calls, and zero live requests.
- **SC-002**: The native absent-transport case produces an explicit failure with
  the same zero callback counts.
- **SC-003**: Each refused operation reports its exact HTTP status without any
  ordinary empty-result or successful export notice.
- **SC-004**: Positive controls preserve the complete HTTP `200` output and metadata.
- **SC-005**: Product diagnostics contain zero controlled credential or body markers.
- **SC-006**: The changed methods reach complete statement and branch coverage.
  The affected module reaches at least 80 percent coverage.
- **SC-007**: The unchanged source fails the native refusal tests before the repair.
  The repaired source passes those same tests.

## Assumptions

- The supported runtime uses Python `3.13` or newer and `mistapi` `0.64`.
- The endpoint returns one object and does not require pagination.
- HTTP status, not the integration payload, establishes transport success.
- SDK diagnostics remain distinct from new MistHelper diagnostics.
  This repair does not claim to change the SDK's logging policy.
- Issues [#2746](https://github.com/jmorrison-juniper/MistHelper/issues/2746) and
  [#2747](https://github.com/jmorrison-juniper/MistHelper/issues/2747) remain open.
