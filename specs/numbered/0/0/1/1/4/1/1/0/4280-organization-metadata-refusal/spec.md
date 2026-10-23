# Feature Specification: Organization metadata refusal

**Feature Branch**: `jmorrison-juniper-organization-metadata-refusal`

**Created**: 2026-10-23

**Status**: Specified

**Input**: Issue #4280 requires validated organization metadata, a safe refusal warning,
offline tests, and an explicit `Unknown` result for refused requests.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Report a refused lookup (Priority: P1)

The operator must see that an organization name request failed.
The export must retain the `Unknown` label without accepting refused metadata.

**Why this priority**: A silent refusal hides an access problem and can produce misleading bundle metadata.

**Independent Test**: Supply a refused response offline and inspect the returned label and captured logs.

**Acceptance Scenarios**:

1. **Given** a refused request with a name, **When** the lookup completes, **Then** it returns `Unknown` and warns with the status.
2. **Given** a refusal body with sensitive text, **When** the lookup reports failure, **Then** no log contains that text.
3. **Given** a server failure, **When** the lookup completes, **Then** it returns `Unknown` and reports failure.

### User Story 2 - Preserve a successful name (Priority: P2)

The operator must retain the organization name from a successful metadata request.

**Why this priority**: The source name identifies the export bundle.

**Independent Test**: Supply successful metadata offline and compare the returned name and bundle metadata.

**Acceptance Scenarios**:

1. **Given** a successful response with a valid name, **When** the lookup completes, **Then** the bundle retains that name.
2. **Given** absent or invalid metadata, **When** the lookup completes, **Then** it returns `Unknown` and reports unavailable metadata.

### Edge Cases

- A refused response contains both an error and a plausible name.
- A successful response contains an error field, a missing name, or a nontext name.
- A response lacks an HTTP status or contains a nonobject body.
- A request exception contains sensitive text.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Accept names only from successful HTTP results with object metadata, no error field, and a nonblank text name.
- **FR-002**: Return the exact label `Unknown` for refused or invalid results.
- **FR-003**: Report refusal with organization context and HTTP status, without response bodies or returned metadata.
- **FR-004**: Report request exceptions without exception text that can contain sensitive response contents.
- **FR-005**: Preserve export metadata structure and the existing import confirmation boundary.
- **FR-006**: Use offline tests only. Do not execute menus 176 or 177 against production.
- **FR-007**: Require human review before merge. Do not enable automatic merge or close issues #4280 and #4277.

### Mist Cloud Transport Requirements

The existing transport remains `mistapi.api.v1.orgs.orgs.getOrg`.
No direct HTTP transport or WebSocket transport enters this change.
Mock the SDK endpoint and use native SDK response objects to verify HTTP status handling and safe logs.

### Key Entities

- **Organization metadata**: The source organization identifier and its human-readable name.
- **Lookup result**: The HTTP status, metadata validity, and explicit unknown label when the lookup fails.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every tested refusal returns `Unknown` and produces a warning with its HTTP status.
- **SC-002**: No captured lookup log contains the sensitive marker from a response or exception.
- **SC-003**: Every tested valid name reaches the export metadata unchanged.
- **SC-004**: All verification requests remain offline, with zero production configuration changes.

## Assumptions

- A successful request uses an integer HTTP status from 200 through 299.
- An error field invalidates metadata even when the HTTP status indicates success.
- Unknown metadata remains nonfatal, as the existing lookup contract requires.
- Only the metadata lookup changes. Configuration writes, file selection, and typed confirmations remain unchanged.
- The tracked feature selector belongs to another feature and remains unchanged. Commands use an explicit feature directory.
