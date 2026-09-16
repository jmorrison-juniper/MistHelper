# Feature Specification: Phantom Mist SDK Calls

**Feature Branch**: `fix/2717-phantom-sdk-calls`

**Created**: 2026-09-15

**Status**: Draft

**Input**: GitHub issue #2717 reports five `src` call sites that call Mist SDK site functions that do not exist.

## User Scenarios & Testing

### User Story 1 - Resolve the site name with a real SDK route (Priority: P1)

A NOC engineer runs a site export or a virtual chassis status check. The tool uses `getSiteInfo` to fetch the one site that the caller already selected.

**Why this priority**: The current calls raise `AttributeError` at runtime and hide the error behind fallback output.

**Independent Test**: Unit tests inject a mocked Mist session and assert that each repaired path returns the known site name.

**Acceptance Scenarios**:

1. **Given** a mocked `getSiteInfo` response with `name`, **When** each site-name helper runs, **Then** it returns the site name.
2. **Given** the helper runs, **When** the mock records SDK calls, **Then** no helper calls `sites.getSite` or `sites.listSites`.

---

### User Story 2 - Report site lookup faults (Priority: P2)

A NOC engineer needs a clear log record when the Mist API or SDK returns a fault during site-name lookup.

**Why this priority**: The old broad handlers returned fallback values with no error log.

**Independent Test**: A unit test injects a fault response and asserts that the handler logs the fault.

**Acceptance Scenarios**:

1. **Given** `getSiteInfo` returns HTTP status 503, **When** the handler runs, **Then** it logs an error with the site identifier.
2. **Given** the SDK route is missing, **When** the helper runs, **Then** it logs the SDK drift and raises `AttributeError`.

## Edge Cases

- If `getSiteInfo` returns no `name`, the caller uses the site identifier after it records the lookup result.
- If `getSiteInfo` returns a non-success HTTP status, the caller logs the status and uses its existing fallback value.
- If the SDK route is absent, the caller logs full exception context and raises the programming fault.

## Requirements

### Functional Requirements

- **FR-001**: The five named call sites MUST call `mistapi.api.v1.sites.sites.getSiteInfo(apisession, site_id)`.
- **FR-002**: Each repaired caller MUST handle the single-site response object that `getSiteInfo` returns.
- **FR-003**: Each repaired caller MUST stop using `mistapi.api.v1.sites.getSite`.
- **FR-004**: Each repaired caller MUST stop using `mistapi.api.v1.sites.listSites`.
- **FR-005**: Each repaired handler MUST log Mist API fault status with the affected site identifier.
- **FR-006**: Each repaired handler MUST log SDK drift with full exception context before it raises.
- **FR-007**: The repair MUST NOT import `MistHelper` from a file under `src`.
- **FR-008**: The repair MUST NOT edit vendor API records or generated API documentation.

### Key Entities

- **Site lookup response**: The `APIResponse` object from `getSiteInfo`. Its `data` field is one site object.
- **Site name**: The user-facing name read from the single-site response.
- **Site lookup fault**: A non-success response or SDK mismatch that must appear in logs.

## Success Criteria

### Measurable Outcomes

- **SC-001**: All five targeted unit tests return the expected known site name.
- **SC-002**: One fault test proves the handler logs a non-success API status.
- **SC-003**: `git grep -n "sites\\.getSite(\\|sites\\.listSites(" -- src` returns no rows.
- **SC-004**: `git grep -n "import MistHelper" -- src` returns no rows.
- **SC-005**: The requested local gates pass before the pull request opens.

## Assumptions

- The installed Mist SDK version is 0.64.0.
- `getSiteInfo` has the signature `(mist_session, site_id)`.
- No live Mist API request is required for this repair.
- Existing fallback display values remain acceptable after a reported lookup fault.
