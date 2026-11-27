# Feature Specification: Guest authorization workflows

**Feature Branch**: `feat/4278-guest-authorization-workflows` (planned, not created in this run)

**Record**: `specs\numbered\0\0\1\1\4\1\0\3\4278-guest-authorization-workflows`

**Created**: 2026-11-26

**Status**: Draft. Guest data and writes stay blocked until decision D-4 passes and gates G2 through G5 pass.

**Input**: Issue 4278 asks for guest authorization workflows in the MistHelper web portal. Owner comments of 2026-11-06 and 2026-11-08 keep the scope offline until approvals exist.

## Terms

- **Authorization record**: A Mist guest authorization object for one target at one site.
- **Scope**: The organization, site, and WLAN that one action can affect.
- **Target**: The guest device MAC address for one action.
- **Observation**: A status value that Mist returns. A missing value stays unknown.
- **Write**: A request that changes an authorization record or a client session in Mist.
- **Outcome**: The result class of one write. The classes appear in FR-016 and FR-024.
- **Gate**: An approval or evidence condition that blocks a task until it passes.
- **Projection**: The masked read model in `domain/read_model.py`.

## Purpose and boundary

- The feature adds guest authorization workflows to the existing MistHelper web portal.
- It reuses the existing Flask application, the shared Mist session, and the existing Compose group.
- It adds no second application, database service, port, or environment variable.
- Mist remains the source of truth. The portal stores no authorization snapshot.
- Issue 4231 and issue 4278 stay open. This feature does not close issue 4231.

Warning: a confirmed write changes device access in the Mist cloud. The portal cannot undo a confirmed write.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Review authorization records for one scope (Priority: P1)

An approved operator selects a site and WLAN. The portal shows only the authorization records for that scope.

**Why this priority**: The operator must see the current state before any access change.

**Independent Test**: Use fictional records and mocked Mist responses. Check scope selection, unknown values, and denied identity. Send no write.

**Acceptance Scenarios**:

1. **Given** a trusted identity, **When** the operator selects a site and WLAN, **Then** only the matching records appear.
2. **Given** a missing authorization or expiry value, **When** a record appears, **Then** the value shows as unknown.
3. **Given** no trusted identity, **When** the page loads, **Then** no authorization record appears.
4. **Given** a changed site, **When** an older response arrives, **Then** the older response does not replace the current scope.

### User Story 2 - Grant access to one target (Priority: P1)

An approved operator grants time-limited access to one target after an exact review.

**Why this priority**: A grant changes device access. It needs the strongest review path.

**Independent Test**: Mock the update call. Check the review text, the typed word, the cancel path, and the audit rows.

**Acceptance Scenarios**:

1. **Given** a valid target and minutes, **When** the operator types GRANT, **Then** one update call runs for that scope.
2. **Given** a canceled review or a wrong word, **When** the operator submits, **Then** no write runs.
3. **Given** a timeout after dispatch, **When** the result appears, **Then** the outcome shows unknown and no repeat write runs.
4. **Given** a failed intent write, **When** the operator submits, **Then** no write runs.

### User Story 3 - Edit or extend one authorization (Priority: P2)

An approved operator changes a supported field. An operator extends access only after extension is approved.

**Why this priority**: Operators must fix details without changing access by mistake.

**Independent Test**: Mock the update call. Reject unsupported and read-only fields before any call.

**Acceptance Scenarios**:

1. **Given** a supported field, **When** the operator types UPDATE, **Then** the call sends only the reviewed fields.
2. **Given** a read-only field such as name, **When** the operator submits, **Then** the portal rejects the change before any call.
3. **Given** extension is not approved, **When** the operator opens the extend form, **Then** the form shows a blocked state and sends no write.

### User Story 4 - Revoke one authorization with evidence (Priority: P2)

An approved operator revokes access for one target. The portal reports ended access only after a read-back confirms it.

**Why this priority**: A false revocation result can leave unwanted access active.

**Independent Test**: Mock the unauthorize call and the read-back. Check accepted, verified, and unknown outcomes.

**Acceptance Scenarios**:

1. **Given** a confirmed REVOKE, **When** the call succeeds and the read-back shows ended access, **Then** the portal reports ended access.
2. **Given** a successful call and a read-back without ended access, **When** the result appears, **Then** the portal reports accepted but not verified.
3. **Given** a timeout after the call, **When** the result appears, **Then** the portal reports unknown and sends no repeat call.

### User Story 5 - Find connected clients in one site (Priority: P2)

An operator searches connected clients in one site by MAC address, hostname, or IP address.

**Why this priority**: The operator finds a target without manual lookup.

**Independent Test**: Use fictional client rows. Check each search field and the masked output.

**Acceptance Scenarios**:

1. **Given** a site, **When** the operator searches by MAC address, **Then** only matching rows from that site appear.
2. **Given** no matching row, **When** the search ends, **Then** the portal shows an empty result and no write control.

### User Story 6 - Preview and import a reviewed CSV batch (Priority: P3)

An approved operator uploads a bounded CSV file, reviews each row, types IMPORT, and runs the batch.

**Why this priority**: One batch can change many targets. Each row needs a visible outcome.

**Independent Test**: Use fictional rows and mocked updates. Check limits, preview, duplicates, confirmation, and row outcomes.

**Acceptance Scenarios**:

1. **Given** a valid file, **When** the preview completes, **Then** each row shows a resolved scope or a rejection reason.
2. **Given** duplicate targets in one file, **When** the preview runs, **Then** each duplicate row shows a rejection.
3. **Given** a rate limit on row 3, **When** the batch stops, **Then** rows 4 and later show not attempted.
4. **Given** a file that changed after preview, **When** the operator types IMPORT, **Then** the run sends no write.

### Edge Cases

- A missing, untrusted, or forged identity sends no write and discloses no record.
- Equal SSIDs, duplicate site names, or a missing WLAN identifier never widen the scope.
- An invalid MAC address or mixed separators reject before any call.
- A grant with 0 minutes rejects. The meaning of 0 is unverified.
- A minutes value above 259200 rejects.
- A payload with a read-only field rejects before dispatch.
- A client search returns at most 200 rows. A larger result asks for a narrower search.
- A CSV file above 262144 bytes rejects before parsing.
- A CSV file with more than 200 data rows rejects before any write.
- CSV quoting, escaped quotes, embedded newlines, BOM, CRLF, missing headers, extra fields, and formula text need tests.
- Rate limits, server errors, malformed responses, and timeouts give distinct results.
- An intent write failure stops the write before dispatch. An outcome write failure reports the cloud outcome and the audit failure separately.
- A permission error stops at the requested scope. The portal does not widen to organization scope.
- A portal restart with an intent and no outcome makes the intent visible. The operator reviews it before any new write.
- Keyboard use, reduced motion, narrow screens, long values, and empty results need accessible states.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The portal MUST add one navigation entry and one guest authorization page.
- **FR-002**: Every read and write MUST bind to one organization, one site, and one WLAN.
- **FR-003**: Site and WLAN choices MUST come from Mist discovery. An unknown identifier MUST fail before any call.
- **FR-004**: Reads and writes MUST require a trusted operator identity under decision D-4. Without identity, every action MUST be disabled.
- **FR-005**: Every form MUST carry a CSRF token. Every write MUST check its exact confirmation word on the server.
- **FR-006**: The review MUST list authorization records for the selected site and WLAN through the list call.
- **FR-007**: A missing authorization or expiry value MUST display as unknown.
- **FR-008**: Client search MUST use the site client statistics call and MUST filter the returned rows locally.
- **FR-009**: A grant MUST send one update call. Its minutes value MUST be an integer from 1 through 259200.
- **FR-010**: An update MUST send only the reviewed writable fields. A read-only field MUST NOT reach the payload.
- **FR-011**: An extension MUST stay disabled until gate G5 records verified extension behavior.
- **FR-012**: A revoke MUST call the unauthorize operation once. It MUST report ended access only after a read-back confirms it.
- **FR-013**: The feature MUST NOT call any delete operation.
- **FR-014**: Before a confirmed write, the review MUST show the exact scope, the masked target, and the requested change.
- **FR-015**: A cancel, a wrong word, a changed review digest, a changed scope, or a denied identity MUST send zero writes.
- **FR-016**: A timeout, a connection error, a server error, or a missing response MUST report unknown. The feature MUST NOT retry it or change the scope.
- **FR-017**: Each write MUST store an intent row before dispatch. Each dispatched write MUST store one outcome row after the response.
- **FR-018**: If the intent row fails, the feature MUST NOT dispatch the write.
- **FR-019**: If the outcome row fails after dispatch, the portal MUST report the cloud outcome and the audit failure separately.
- **FR-020**: A CSV upload MUST accept at most 262144 bytes and 200 data rows. It MUST require the ten declared headers.
- **FR-021**: CSV preview MUST validate each row, resolve the scope by identifier, normalize each MAC address, and send no write.
- **FR-022**: CSV confirmation MUST bind to a SHA-256 digest of the reviewed rows and the typed word IMPORT.
- **FR-023**: CSV rows MUST run one at a time. Each row MUST report one outcome.
- **FR-024**: A rate limit, an unknown outcome, or an audit failure MUST stop later rows. Each later row MUST show not attempted.
- **FR-025**: Logs, audit rows, and responses MUST exclude secrets, names, email addresses, field values, and full MAC addresses.
- **FR-026**: New controls MUST carry stable data-testid attributes. A failed browser flow MUST keep a trace or a screenshot.
- **FR-027**: The feature MUST add no application, port, Compose service, or environment variable.
- **FR-028**: Mist calls MUST use mistapi methods only. A direct HTTP request to Mist MUST NOT appear.
- **FR-029**: The feature MUST use site scope only. An organization guest method MUST NOT appear in any call path.
- **FR-030**: Automated tests MUST use mocked Mist responses and fictional data. No automated test MUST send a live write.
- **FR-031**: The operator guide and one changelog fragment MUST describe the feature.
- **FR-032**: The projection module MUST move into a nested package. Its public behavior MUST stay the same.

### Mist Cloud Transport Requirements

- The feature uses these mistapi methods: `listSiteAllGuestAuthorizations`, `getSiteGuestAuthorization`, `updateSiteGuestAuthorization`, `unauthorizeSiteWirelessClient`, `listSiteWirelessClientsStats`, `listSiteWlans`, and `listOrgSites`.
- A direct HTTP fallback is not planned. An owned WebSocket transport is not planned.
- The SDK retries HTTP 429 up to three times for PUT and POST calls. The portal reads the final response as the outcome.
- Contract tests prove exact arguments, site scope, the write allowlist, the absence of delete calls, failure classes, and redaction.

### Key Entities

- **Scope**: One organization identifier, one site identifier, one WLAN identifier, and one action.
- **Authorization observation**: A masked identifier, an authorized value or unknown, and an expiry value or unknown.
- **Write intent**: An operation identifier, action, scope, masked target, minutes, operator identity, and intent time.
- **Write outcome**: An operation identifier, outcome class, status code, and outcome time.
- **Import batch**: A file digest, row count, byte count, row digest, and one outcome for each row.
- **Audit row**: One stored intent or outcome. It holds masked data only.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every request without a trusted identity or an allowed scope shows zero records and sends zero writes in tests.
- **SC-002**: Every canceled, wrong, stale, or denied confirmation sends zero writes in tests.
- **SC-003**: Every displayed authorization value stays unknown when Mist returns no value.
- **SC-004**: Every import row shows one final outcome. Each row after a stop shows not attempted.
- **SC-005**: Every unknown write has zero automatic retries in tests.
- **SC-006**: The feature adds zero applications, zero Compose services, zero ports, and zero environment variables.
- **SC-007**: Automated tests make zero live Mist requests.

## Clarifications

### Session 2026-11-26

- Q: Can the implementation reuse the source application? A: No. The implementation is independent. See D-3.
- Q: Who approves the access model? A: A human decision is required. Reads and writes stay blocked until approval. See D-4.
- Q: What are the CSV limits? A: 262144 bytes and 200 data rows. See D-13. The issue still asks maintainers to approve these limits.
- Q: What happens when an audit write fails? A: An intent failure stops before dispatch. An outcome failure reports separately and stops later writes. See D-15.
- Q: What duration applies? A: Grants accept 1 through 259200 minutes. See D-8.
- Q: How does revocation work? A: One unauthorize call, then a read-back. See D-10.
- Q: Does organization scope apply? A: No. Site scope only. See D-5.
- Q: Does a legacy record exist? A: No. No 4278 folder exists locally or on main. See D-2.
- Q: Is issue 4278 open? A: Yes. GitHub reports it open. The owner reopened the remaining work on 2026-11-08.
- Q: Does the live-test approval decide the gates? A: No. The owner comment states that it does not decide the design gates.

## Assumptions

- The pinned mistapi version is 0.64.1, as requirements.txt states.
- The portal keeps one Gunicorn worker with four threads, as wsgi.py documents.
- The owner approves each live verification run before it starts.
- The shared Mist session remains the only Mist session in the portal.
- Mist returns the authorization list without paging. This assumption is unverified. See Unverified U03.

## Out of Scope

- Organization-scope guest reads and writes.
- Any DELETE of an authorization record.
- Historical guest search through searchSiteGuestAuthorization. Menu 200 stays unchanged.
- Notification controls.
- Template-derived and site-group WLAN discovery before gate G5.
- Visual parity with the source application.
- Reuse of source code, templates, assets, screenshots, or tests.
- Closing issue 4231.
- Live Mist tests in continuous integration.
