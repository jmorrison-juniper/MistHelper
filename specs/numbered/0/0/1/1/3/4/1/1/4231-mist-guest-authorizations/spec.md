# Feature Specification: Migrate Mist Guest Authorizations

**Issue**: #4231
**Feature Branch**: `docs/4231-mist-guest-authorizations`
**Created**: 2026-10-15 | **Refreshed**: 2026-11-26
**Status**: Draft. Planning only. Product implementation stays out of scope.
**Input**: Migrate the MistGuestAuthorizations guest WiFi pre-authorization portal into MistHelper. Keep its operator workflows as requirements. Stop before product code.

## Record Scope and Current State

- This record replaces the legacy content at the same route. The identity stays `4231-mist-guest-authorizations`.
- PR #4290 (merged 2026-10-20) restored the legacy planning files. PR #4589 (merged 2026-11-05) planned parity work for issue #4588.
- PR #4279 (merged 2026-10-18) added an offline projection of three fields. It adds no route, no SDK call, and no write.
- Issue #4278 tracks implementation and stays open. Closure of issue #4231 is a maintainer decision. See analysis.md item U-6.
- Source evidence uses the pinned commit `0213240cb9edfa237f763acd156b90a6049363cb`, which equals remote main. The local checkout at `61f6a48f3a4e87a77069201879f81443d088ef16` is nine commits behind and does not prove pinned behavior.
- The MistHelper license and the source license are both CC BY-NC-SA 4.0. Copying source expression still needs a maintainer decision (D-13).
- Guest writes stay disabled until gate G5 closes. G5 must prove how a site-scope grant binds a WLAN and how revoke ends access.

## User Scenarios & Testing (mandatory)

Each story is independent. Test IDs refer to design/quickstart.md.

### User Story 1 - Review guest authorizations for one WLAN (Priority: P1)

An operator selects a site and a guest WLAN. The portal lists the guest authorizations that Mist returns for that WLAN.

**Why this priority**: Operators need accurate status before they change any access.

**Independent Test**: Use fictional records. Check selection, denied access, missing credentials, and unknown values. Denied and missing-credential paths need no Mist call. Covers TC-009, TC-010, TC-031, TC-033, TC-045, and TC-046.

**Acceptance Scenarios**:

1. **Given** permission for a site, **When** the operator selects a guest WLAN, **Then** the table lists only returned records for that WLAN.
2. **Given** a record without an expiry time, **When** the table renders, **Then** the expiry shows "unknown" and the state is not "expired".
3. **Given** no Mist credential, **When** the tab loads, **Then** the portal shows a configuration message and makes no Mist call.
4. **Given** a Mist response that is not an array, **When** the view loads, **Then** the view shows "unknown" and no totals.

### User Story 2 - Grant a guest authorization (Priority: P1)

An operator enters one device MAC address, a duration, and optional details. The operator reviews the change and types GRANT.

**Why this priority**: Headless devices cannot complete a captive portal sign-in.

**Independent Test**: Mock the gateway. Check validation, the typed word, the reviewed-content hash, and each zero-write path. Covers TC-006, TC-007, TC-034 through TC-037, and TC-047.

**Acceptance Scenarios**:

1. **Given** a valid MAC address and duration, **When** the operator opens the review, **Then** the panel shows the full MAC address and UTC expiry.
2. **Given** the typed word GRANT and a matching hash, **When** Mist returns HTTP 2xx, **Then** the portal shows the cloud outcome and the audit outcome.
3. **Given** a wrong typed word, a canceled review, or a denied permission, **When** the operator submits, **Then** the portal sends zero Mist write requests.
4. **Given** an unknown outcome, **When** the action ends, **Then** the portal shows "unknown" and offers reconciliation without a retry.

Warning: A confirmed grant, edit, extension, or revoke changes guest access in the Mist cloud. The portal cannot undo that change.

### User Story 3 - Edit guest details (Priority: P2)

An operator changes company, email, field1, field2, field3, or minutes for one guest authorization.

**Why this priority**: Operators correct details without creating a second authorization.

**Independent Test**: Mock the gateway. Check the allowlist, the typed word CHANGE, and the rejection of name edits. Covers TC-027 and TC-035.

**Acceptance Scenarios**:

1. **Given** a supported field, **When** the operator confirms CHANGE, **Then** the portal sends only the reviewed fields.
2. **Given** a name change, **When** the operator submits, **Then** the portal rejects the change and sends zero write requests.

### User Story 4 - Extend access (Priority: P2)

An operator sets a new duration for one guest authorization and types EXTEND.

**Why this priority**: Long device tests need more time without a new grant.

**Independent Test**: Mock the gateway. Check the bounds and the expiry preview. Covers TC-004 and TC-041.

**Acceptance Scenarios**:

1. **Given** a duration from 1 to 259200 minutes, **When** the operator reviews the change, **Then** the panel shows the new expiry in UTC.
2. **Given** a duration of 0 or 259201, **When** the operator submits, **Then** the portal rejects the value and sends zero write requests.

### User Story 5 - Revoke access (Priority: P2)

An operator ends one guest authorization and types REVOKE.

**Why this priority**: A false revoke result can leave unwanted access active.

**Independent Test**: Mock the write and the follow-up read. Check each outcome branch. Covers TC-038, TC-039, and TC-040.

**Acceptance Scenarios**:

1. **Given** a record whose WLAN differs from the reviewed WLAN, **When** the operator revokes, **Then** the portal refuses and sends zero write requests.
2. **Given** a 2xx write and a follow-up read that shows the record unauthorized, **When** reconciliation ends, **Then** the portal shows "ended".
2. **Given** a 2xx write and a read that still shows the record authorized, **When** reconciliation ends, **Then** the portal shows "not ended".

### User Story 6 - Search connected clients (Priority: P3)

An operator searches connected clients at the selected site by MAC address, hostname, or IP address.

**Why this priority**: Search finds a device that is already online.

**Independent Test**: Use fictional client statistics. Check the site filter and the masked output. Covers TC-044.

**Acceptance Scenarios**:

1. **Given** a search term, **When** results return, **Then** the table lists only clients at the selected site and masks each MAC address.
2. **Given** a Mist failure during search, **When** the search ends, **Then** the portal shows an error instead of an empty result.

### User Story 7 - Import guests from CSV (Priority: P3)

An operator uploads a CSV file, reviews the validation result for each row, and types IMPORT.

**Why this priority**: Import saves time for long device lists but must not skip review.

**Independent Test**: Use fictional CSV files. Check limits, duplicates, the preview, the typed word, and each row outcome. Covers TC-016 through TC-021, TC-042, TC-043, and TC-048.

**Acceptance Scenarios**:

1. **Given** a file larger than 262144 bytes, **When** the operator uploads it, **Then** the portal rejects the file before it parses rows.
2. **Given** a reviewed batch and the typed word IMPORT, **When** the run starts, **Then** rows run in order and each row shows one outcome.
3. **Given** a final 429 response on row 3, **When** the run stops, **Then** rows 4 onward show "not attempted".

### Edge Cases

- Malformed MAC addresses reject before any Mist call.
- Duplicate normalized targets in one batch reject every row after the first occurrence.
- An expiry time in the past shows "expired". A missing expiry shows "unknown".
- A 4xx response other than 429 marks the row failed. The batch continues.
- A 401 or 403 response stops the batch because the credential lacks permission.
- A final 429 response marks the row failed and stops the batch. A 5xx response or a missing status marks the row unknown and stops the batch.
- Revoke for a MAC address that Mist no longer returns shows "not found". It never shows "ended".
- An unavailable journal refuses every write before a Mist call.
- A cloud success followed by a failed audit write blocks the next write until reconciliation.
- The portal keeps none of these source behaviors: organization-scope fallback, unfiltered organization lists, success after HTTP errors, empty results after exceptions, and silent defaults.

## Requirements (mandatory)

### Functional Requirements

- **FR-001**: The portal MUST add a Guest Access tab to the existing web portal on port 8055 when GUEST_ACCESS_ENABLED is true.
- **FR-002**: The feature MUST run in the existing application process and Compose group, and it MUST NOT add a service or published port.
- **FR-003**: The feature MUST store its action journal and audit events in the existing ArangoDB database and MUST NOT create a second database.
- **FR-004**: The feature MUST NOT store guest authorization data, journal entries, or audit events in Redis.
- **FR-005**: Every guest route MUST require an authenticated operator once decision D-11 is approved.
- **FR-006**: Every guest request MUST check organization, site, WLAN, and action permission before it calls Mist.
- **FR-007**: The review MUST show only fields that Mist returns for the selected site WLAN, and it MUST show "unknown" for missing values.
- **FR-008**: A guest authorization MUST show "expired" only when its returned expiry time is earlier than the current UTC time.
- **FR-009**: Grant input MUST validate the MAC address, a duration from 1 to 259200 minutes, field lengths, and the selected site WLAN.
- **FR-010**: Edit MUST send only allowlisted site-scope fields and MUST NOT send name, MAC address, WLAN identifier, or field4.
- **FR-011**: Extend MUST apply the duration rules of FR-009 and MUST show the resulting expiry in UTC before confirmation.
- **FR-012**: Revoke MUST send minutes 0 at site scope only after it confirms that the record belongs to the reviewed WLAN.
- **FR-013**: Revoke MUST show "ended" only when a follow-up read shows the record unauthorized or expired.
- **FR-014**: Each cloud change MUST require its operation-specific typed word and a matching reviewed-content hash.
- **FR-015**: A canceled review, wrong typed word, stale hash, invalid input, or denied permission MUST send zero Mist write requests.
- **FR-016**: A cloud write MUST count as succeeded only when Mist returns an HTTP 2xx status.
- **FR-017**: The feature MUST NOT call organization-scope write methods, and it MUST NOT change scope after an error.
- **FR-018**: The feature MUST NOT retry a write automatically, including after an unknown outcome.
- **FR-019**: The feature MUST write an intent journal entry before each write, and it MUST NOT start the write when the read-back fails.
- **FR-020**: The feature MUST record the cloud and audit outcomes for each write. A failed audit write MUST block later writes.
- **FR-021**: Client search MUST query only the selected site through the wireless client statistics method and MUST filter results locally.
- **FR-022**: CSV import MUST enforce the byte, row, encoding, header, and cell limits in design/contracts/csv-import.md before it parses rows.
- **FR-023**: Import MUST show one validation result for each row, and it MUST write nothing until the typed word IMPORT matches the reviewed batch hash.
- **FR-024**: Import MUST run rows in order and MUST give each row one final outcome: succeeded, failed, unknown, rejected, or not attempted.
- **FR-025**: Import MUST stop after a final 429 response, a 401 or 403 response, an unknown outcome, or a failed audit write.
- **FR-026**: Logs and audit events MUST NOT contain tokens, names, email addresses, field values, raw payloads, or full MAC addresses. The action journal keeps the full MAC address only for reconciliation.
- **FR-027**: Every new Python module MUST sit in a nested package, and each directory level MUST keep five children or fewer.
- **FR-028**: The feature MUST call only allowlisted mistapi methods with explicit keyword arguments and MUST NOT send direct HTTP requests to Mist.
- **FR-029**: Every browser control MUST have a unique data-testid, and each failed browser flow MUST keep a screenshot and a trace under test-artifacts.
- **FR-030**: Tables MUST show masked MAC addresses, and the review panel MUST show the full MAC address for one selected record or import row only.

### Mist Cloud Transport Requirements

- Read: `mistapi.api.v1.sites.guests.listSiteAllGuestAuthorizations` with the `wlan_id` filter. Local SDK file `sites/guests.py` line 17.
- Read: `mistapi.api.v1.sites.guests.getSiteGuestAuthorization` for reconciliation. Local SDK file `sites/guests.py` line 224.
- Write: `mistapi.api.v1.sites.guests.updateSiteGuestAuthorization`, which sends an HTTP PUT. Local SDK file `sites/guests.py` line 280 and `__api_request.py` line 303.
- Read: `mistapi.api.v1.sites.stats.listSiteWirelessClientsStats` for client search. Local SDK file `sites/stats.py` line 960.
- Read: `mistapi.api.v1.sites.wlans.listSiteWlans`, `mistapi.api.v1.orgs.wlans.listOrgWlans`, and `mistapi.api.v1.orgs.sites.listOrgSites` for selectors. Local SDK files start these functions at line 17.
- Not used in v1: `sites.guests.deleteSiteGuestAuthorization`, `sites.guests.searchSiteGuestAuthorization`, every organization guest write, and `orgs.guests.listOrgGuestAuthorizations` because it has no WLAN filter.
- Not used in v1: template and site-group WLAN inheritance. The pinned source resolves it, but it waits for gate G5.
- No owned WebSocket transport. No direct HTTP request.
- Contract evidence: design/contracts/mist-api.md and tests TC-022 through TC-027.

### Key Entities

- **Operator**: An authenticated person who uses the portal. The identity method needs decision D-11.
- **Permission scope**: The organization, site, WLAN, and action for one request.
- **Guest authorization**: The Mist record. The portal reads it and shows only returned fields.
- **Action journal entry**: The intent and outcomes of one write. See design/data-model.md.
- **Audit event**: One masked event with the operator reference, scope, operation, and both outcomes.
- **Import batch and import row**: One reviewed CSV file and one validated row.

## Success Criteria (mandatory)

- **SC-001**: Every unauthorized or out-of-scope request makes zero Mist calls in the offline suite.
- **SC-002**: Every canceled, wrong-word, stale, or invalid write makes zero Mist write calls.
- **SC-003**: Every displayed status field equals a returned field or shows "unknown".
- **SC-004**: Every import row ends with one final outcome, and every row after a stop shows "not attempted".
- **SC-005**: The feature retries no write request automatically. Contract tests count one SDK call per write.
- **SC-006**: All scenario tests use fictional data and make zero live requests in continuous integration.
- **SC-007**: The feature adds zero application services, zero databases, and zero published ports.
- **SC-008**: Every new interactive control has a unique data-testid, and the browser suite asserts each one.

## Assumptions

- The Mist token that the portal uses has read access to organization sites and WLANs, and read and write access to guest authorizations. Source guide lines 170 and 171 describe this model.
- The checked-in OpenAPI 3.1 file describes the Mist cloud at implementation time. Gate G5 confirms this for each method.
- The portal runs as one application process per host. Journal locks still use compare-and-swap, so concurrent workers stay safe.
- Operators use the English interface only.
- This planning PR approves neither integration nor source reuse. Decisions D-11 and D-13 remain open.

## Clarifications

Session 2026-11-26. Each answer states the current decision.

- Q: Can a write run without an operator identity? A: No. D-11 requires an authenticated operator. The identity method needs human approval.
- Q: Which revoke method applies? A: PUT with minutes 0 at site scope, then a GET reconciliation (D-4). DELETE is excluded.
- Q: Which duration range applies? A: 1 to 259200 minutes, based on the schema maximum at documentation/mist-api-openapi31yaml.yaml line 80995 (D-5). The source UI maximum of 2628000 minutes is rejected.
- Q: Does a site-scope grant bind a WLAN? A: Unverified. The site schema marks wlan_id read-only at line 81020. The organization schema requires wlan_id at line 81122. Grants stay disabled until G5 closes (D-16).
- Q: Can an operator edit the name at site scope? A: No. The site schema marks name read-only at line 81002. The form does not offer a name control.
- Q: Does MistHelper write field4? A: No (D-6). The source overwrites field4 with the token name. MistHelper records attribution in the audit event.
- Q: Can source code or screenshots be copied? A: No, by default. D-13 keeps reuse blocked until a maintainer approves a licensing path.
- Q: Does this planning PR close issue #4231? A: The brief requires the closing keyword (D-17). Issue comments and PR #4290 ask to keep #4231 open. analysis.md item U-6 records the conflict.

## Out of Scope

- Live Mist reads, live Mist writes, and production credentials in this planning PR.
- Organization-scope writes and any scope fallback.
- Template and site-group WLAN inheritance until G5 verifies its contract.
- Copying source code, templates, tests, README text, screenshots, or assets.
- WebSocket transport and direct HTTP requests to Mist.
- Browser sign-in for port 8055. Issue #4936 is open and tracks it.
- Docker parity and new Compose services.

Caution: Setting GUEST_ACCESS_ENABLED to false hides the tab. It does not remove journal or audit records.
