# Feature Specification: License export failure status

**Feature Branch**: `jmorrison-juniper-fix-4714-license-export-status`

**Created**: 2026-11-09

**Status**: Approved for local repair

**Input**: Issue #4714 and its exclusive local file reservation.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Report a failed request (Priority: P1)

An operator must see a failure when the license request fails, rather than a successful export of error data.

**Why this priority**: An incorrect success message can hide a cloud failure.

**Independent Test**: Supply synthetic failed responses through each supported request path. Confirm that no writer receives their bodies.

**Acceptance Scenarios**:

1. **Given** a failed request, **When** an operator exports licenses, **Then** the operation reports the failure and writes nothing.
2. **Given** an absent or malformed response status, **When** an operator exports licenses, **Then** the operation rejects the unverified response.

### User Story 2 - Report the actual write result (Priority: P1)

An operator must see success only after the writer accepts valid license records.

**Why this priority**: A rejected write leaves no reliable export.

**Independent Test**: Supply valid records and vary the writer result between success and failure.

**Acceptance Scenarios**:

1. **Given** valid records and a rejected write, **When** export finishes, **Then** the operation reports a write failure without success.
2. **Given** valid records and an accepted write, **When** export finishes, **Then** the operation reports the exported record count.
3. **Given** a valid empty response, **When** export finishes, **Then** the operation reports no records without claiming a file exists.

### Edge Cases

- Failed responses can contain an error dictionary or an empty body.
- Status values can be absent, null, strings, Boolean values, or numbers outside the successful range.
- An operator can cancel organization selection.
- Request, transform, and writer exceptions must retain their existing propagation behavior without another write.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Validate the initial response status before data consumption through either supported endpoint path.
- **FR-002**: Reject each status except an integer from 200 through 299. Boolean values are not status codes.
- **FR-003**: Never write an error response or attempt an empty recovery write after a failure.
- **FR-004**: Report an explicit writer rejection without a success message.
- **FR-005**: Preserve the public `None` return, valid record processing, and operator cancellation.
- **FR-006**: Report a valid empty result without an empty write or a file creation claim.
- **FR-007**: Use synthetic responses with sockets and DNS blocked for regression tests.
- **FR-008**: Keep the candidate local. Do not change shared pagination or any unreserved existing file.

### Mist Cloud Transport Requirements

The existing paths use `mistapi.api.v1.orgs.licenses.listOrgLicenses` when available and the SDK session's `mist_get` otherwise.
Installed mistapi 0.64.1 has no `listOrgLicenses` method. Preserve SDK session authentication and the existing endpoint path.
Regression tests cover both paths without cloud access. Do not log response bodies or credentials.
Initial response validation does not validate later SDK pages. Shared pagination remains outside this repair.

### Key Entities

- **Response status**: The evidence that the initial request succeeded.
- **License records**: The successful response data that the existing processing pipeline exports.
- **Writer result**: The acceptance or rejection of an export.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every tested failed or unverified response causes zero writer calls and zero success messages.
- **SC-002**: Every tested explicit write rejection causes zero success messages.
- **SC-003**: Both request paths preserve successful exports and valid empty results.
- **SC-004**: Regression tests make zero socket or DNS attempts and fail against the original implementation.

## Assumptions

- The assigned base is `3964d21d03f9f5717cb8eafb7272ecff21f5362a`.
- Request failures raise a descriptive runtime error. Writer rejection preserves the public `None` return and logs an error.
- An empty result requires no output because the shared writer rejects empty input.
- Only the initial SDK response is in scope. Later SDK pages remain a separate limitation.
- PowerShell is unavailable. The route follows the eight-digit base-5 calculation in `spec-route.ps1`.
- The existing worktree branch replaces the branch-creation hook. Shared feature selectors and Git configuration remain unchanged.
