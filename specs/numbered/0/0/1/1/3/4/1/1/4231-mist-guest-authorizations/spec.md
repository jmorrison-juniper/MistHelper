# Feature Specification: Migrate Mist Guest Authorizations

**Feature Branch**: `jmorrison-juniper-refresh-guest-migration-spec`

**Created**: 2026-10-15 | **Refreshed**: 2026-10-18

**Status**: Draft migration. Planning reviewed, integration blocked by approval and contract gates.

**Input**: Refresh the existing migration record for [#4231](https://github.com/jmorrison-juniper/MistHelper/issues/4231). Stop before product implementation.

This record preserves the original feature identity. It does not create a second migration.
The prior record survives in Git checkpoint `20cf234e2`, but was absent from `main` at `1e9b280dd`.
[PR #4279](https://github.com/jmorrison-juniper/MistHelper/pull/4279) added an offline projection, not the portal migration.
[Issue #4278](https://github.com/jmorrison-juniper/MistHelper/issues/4278) retains the implementation scope.

## User Scenarios & Testing *(mandatory)*

All portal scenarios below remain conditional on the gates in [research](design/research.md).
No guest-data route, search, or write workflow may become available before all gates pass.

### User Story 1 - Review guest access (Priority: P1)

An approved operator selects a site and guest WLAN, then reviews only the authorizations allowed for that scope.

**Why this priority**: Operators need reliable scope and status information before they change access.

**Independent Test**: Supply fictional scoped records. Check selection, denied access, missing credentials, and unknown status without a cloud request.

**Acceptance Scenarios**:

1. **Given** approved access, **When** an operator selects a site and WLAN, **Then** only permitted matching records appear.
2. **Given** missing authorization or expiry data, **When** a record appears, **Then** the missing value remains unknown.
3. **Given** absent approval or permission, **When** a caller requests guest data, **Then** no guest record is disclosed.
4. **Given** incomplete expired-record coverage, **When** totals appear, **Then** they describe only the returned records.

### User Story 2 - Grant guest access (Priority: P1)

An approved operator grants time-limited access to one device after reviewing the exact target and change.

**Why this priority**: Headless devices cannot complete a browser sign-in.

**Independent Test**: Simulate a permitted grant. Check exact confirmation, scope, invalid input, cancellation, and uncertain results.

**Acceptance Scenarios**:

1. **Given** a valid request, **When** the operator reviews it, **Then** the site or organization scope and requested duration appear.
2. **Given** the exact typed confirmation and valid permission, **When** the request succeeds, **Then** the confirmed result appears.
3. **Given** invalid input, cancellation, or denied permission, **When** submission occurs, **Then** zero cloud writes occur.
4. **Given** an uncertain response, **When** the action ends, **Then** the result remains unknown and no automatic retry occurs.

### User Story 3 - Edit or extend access (Priority: P2)

An approved operator changes a supported field or extends access within the verified duration limits.

**Why this priority**: Operators must correct supported details without broadening device access by mistake.

**Independent Test**: Simulate one supported edit and one extension. Reject unsupported fields and stale scope before submission.

**Acceptance Scenarios**:

1. **Given** a supported field, **When** an edit is confirmed, **Then** only the reviewed change reaches the selected scope.
2. **Given** an extension, **When** the operator confirms it, **Then** the approved duration and expiry rules apply.
3. **Given** an unsupported field or duration, **When** submission occurs, **Then** zero cloud writes occur.

### User Story 4 - Revoke access (Priority: P2)

An approved operator ends device access through a verified operation and checks the resulting state.

**Why this priority**: A false revocation result can leave unwanted access active.

**Independent Test**: Simulate the approved revoke request and state read. Distinguish accepted requests from verified access termination.

**Acceptance Scenarios**:

1. **Given** a selected authorization, **When** revoke is requested, **Then** the exact scope and required typed word appear.
2. **Given** confirmed termination evidence, **When** the action ends, **Then** the portal reports ended access.
3. **Given** only an accepted request or an uncertain state, **When** the action ends, **Then** termination is not claimed.

### User Story 5 - Search clients and import guests (Priority: P3)

An approved operator finds a connected client or reviews a bounded import before changing access.

**Why this priority**: Search and import reduce manual entry but must not bypass scope or confirmation.

**Independent Test**: Use fictional clients and CSV rows. Check approved limits, duplicate detection, preview, confirmation, and each row outcome.

**Acceptance Scenarios**:

1. **Given** a permitted site, **When** a search uses MAC address, hostname, or IP address, **Then** only permitted returned matches appear.
2. **Given** a CSV upload, **When** preview runs, **Then** each accepted row has a validation result and zero writes occur.
3. **Given** a reviewed batch, **When** its exact confirmation is accepted, **Then** valid unique rows run sequentially.
4. **Given** a rate limit, unknown write, or audit failure, **When** processing stops, **Then** remaining rows show not attempted.

### Edge Cases

- Reject malformed MAC addresses, duplicate normalized targets, and a changed scope after preview.
- Reject unsupported fields and durations outside verified limits. Do not assume the source five-year duration claim is valid.
- Distinguish missing authorization from false authorization and missing expiry from expired access.
- Reject an oversized upload before unbounded parsing. Reject excessive rows, malformed encoding, headers, and cells.
- Report permission errors, service errors, partial results, and unavailable audit storage explicitly.
- Do not broaden site scope to organization scope after any error.
- Do not repeat an uncertain write. Require reconciliation before a later operator decision.
- Never place credentials, guest names, email addresses, or full MAC addresses in logs.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The feature MUST use one MistHelper application, its existing data services, and its existing Compose group.
- **FR-002**: The feature MUST keep Mist as the authority. It MUST NOT create a second authorization database.
- **FR-003**: Maintainers MUST approve the implementation rights path before integration. Protected source material MUST NOT be reused without compatible rights.
- **FR-004**: Guest-data routes and all workflows MUST remain absent until access, CSV, audit, and request/response contract gates pass.
- **FR-005**: Access checks MUST bind every read and write to the permitted organization, site, WLAN, and action.
- **FR-006**: Review MUST show only supported returned facts. Missing state MUST remain unknown.
- **FR-007**: Client search MUST use only verified returned fields within the permitted site.
- **FR-008**: Input validation MUST reject malformed identifiers, unsupported edits, and durations outside the verified approved range.
- **FR-009**: Every write MUST show its exact scope and change before an operation-specific typed confirmation.
- **FR-010**: Cancellation, wrong confirmation, stale scope, and denied permission MUST produce zero writes.
- **FR-011**: An uncertain write MUST remain unknown. The feature MUST NOT retry it or switch resource scope.
- **FR-012**: Revocation MUST use verified behavior. Request acceptance alone MUST NOT prove access termination.
- **FR-013**: CSV preview MUST enforce approved byte and row bounds, validate each row, and reject duplicate scoped targets.
- **FR-014**: Import MUST bind one confirmation to the reviewed batch. Changes to its content or scope MUST invalidate confirmation.
- **FR-015**: Import MUST run sequentially and report succeeded, failed, unknown, rejected, or not-attempted outcomes for every row.
- **FR-016**: Rate limits, unknown writes, and audit failures MUST stop later import writes.
- **FR-017**: Audit events MUST include approved operator attribution, exact scope, masked target, outcome, and UTC time without personal fields or secrets.
- **FR-018**: Audit failure MUST remain visible and distinct from cloud failure. Approved recovery behavior MUST precede integration.
- **FR-019**: Offline tests MUST cover every supported workflow without live requests or production credentials.
- **FR-020**: Interactive controls MUST have stable test identifiers, accessible labels, and browser failure evidence.

### Mist Cloud Transport Requirements

Use the existing authenticated session and working `mistapi` methods only. No direct HTTP fallback or owned WebSocket transport is planned.
Candidate methods and unresolved request/response evidence appear in [the API contract](design/contracts/mist-api.md).
Offline contracts must verify authentication forwarding, exact arguments, scope, fields, pagination, failures, and redaction.
Mocked signatures do not prove deployed duration or revocation semantics.

### Key Entities

- **Authorization scope**: The permitted organization, site, WLAN, and operation bound to a request.
- **Guest observation**: Returned authorization and expiry facts. An absent observation is not a negative observation.
- **Import batch**: Bounded validated rows, fixed scope, reviewed content, confirmation, and individual outcomes.
- **Audit event**: An approved operator attribution, exact scope, masked target, outcome, and UTC time.
- **Approval evidence**: A dated maintainer decision or verified contract artifact that resolves a named gate.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every unapproved or out-of-scope request discloses zero guest records and causes zero cloud writes.
- **SC-002**: Every invalid, canceled, or incorrectly confirmed action causes zero cloud writes.
- **SC-003**: Every displayed record preserves missing state and excludes facts not supported by returned observations.
- **SC-004**: Every submitted import row has one final outcome. Every row after a stopping condition remains not attempted.
- **SC-005**: Every unknown write remains unknown until reconciliation. No uncertain write receives an automatic retry.
- **SC-006**: Every scenario runs with fictional records and zero production requests.
- **SC-007**: The migration adds zero application stacks and zero databases.

## Assumptions

Planning completion does not approve integration or source reuse.
The prior statement of source ownership in PR #4279 is evidence of a statement, not a documented compatible rights determination.
The merged projection is the only completed product increment. Its serialization test does not prove route access control.
No numeric CSV limit, audit recovery policy, identity model, or final duration rule is approved by this refresh.
All unresolved gates remain explicit in research rather than invented implementation defaults.
