# Feature Specification: Safe Read Transport Retry

**Feature Branch**: `jmorrison-juniper-fix-3732-stale-read-recovery`

**Created**: 2026-10-06

**Status**: Draft

**Input**: GitHub issue #3732 and the user-defined scope for safe read transport retry and web portal pick-list error reporting.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Recover a Stale Read Connection (Priority: P1)

As an operator, I can open a portal pick list after an idle period without losing the first safe read to a stale connection.

**Why this priority**: A stale pooled connection currently blocks the operator and gives an incorrect report about Mist data.

**Independent Test**: Use a local fake transport that resets the first GET connection and succeeds on the next attempt. Confirm that the pick list receives the successful result without a live Mist call.

**Acceptance Scenarios**:

1. **Given** a pooled HTTPS connection resets during an idempotent GET, **When** the retry budget remains, **Then** the portal repeats the read and returns the successful answer.
2. **Given** a pooled HTTPS connection resets during an idempotent HEAD, **When** the retry budget remains, **Then** the portal can repeat the read within the same bound.
3. **Given** a read exhausts its transport retry budget, **When** no valid response exists, **Then** the portal reports a failed read and does not report a valid empty answer.

---

### User Story 2 - Prevent a Repeated Write (Priority: P1)

As a network operator, I need each write request to use one transport attempt, so a retry cannot repeat a production change.

**Why this priority**: A repeated write can start a second upgrade or repeat another production change.

**Independent Test**: Use a local fake transport that resets a POST request. Confirm that the request has one attempt and no retry.

**Acceptance Scenarios**:

1. **Given** a POST request has a connection reset, **When** the transport handles the failure, **Then** the transport does not repeat the request.
2. **Given** an upgrade portal write session, **When** the session is validated, **Then** its transport retry count remains zero.
3. **Given** any method other than GET or HEAD, **When** a transport error occurs, **Then** the transport does not repeat the request.

---

### User Story 3 - Report a Failed Pick-List Read (Priority: P2)

As an operator, I can distinguish a Mist API failure from a valid response that contains no rows.

**Why this priority**: The current no-rows message can make a failed request look like an empty organization or site.

**Independent Test**: Supply local response objects with no status, an error status, and an empty successful status. Confirm that each result gets the correct operator message.

**Acceptance Scenarios**:

1. **Given** a pick-list read has `status_code` set to `None`, **When** the portal builds the response, **Then** it reports that the portal could not reach the Mist API.
2. **Given** a pick-list read has an HTTP status of 400 or more, **When** the portal builds the response, **Then** it reports that the portal could not reach the Mist API.
3. **Given** a pick-list read has a successful 2xx status and no rows, **When** the portal builds the response, **Then** it reports a valid empty result.
4. **Given** a failed pick-list read, **When** the operator reads the reason, **Then** the message states, "The portal could not reach the Mist API. Try again."

### Edge Cases

- A read reset occurs after the permitted stale-read retry. The request stops with a failed-read result.
- A connection failure occurs before an HTTP status exists. The portal treats the missing status as a failure.
- The Mist API refuses a request with an HTTP 4xx or 5xx status. The portal does not use response data as a successful list.
- The Mist API returns an empty list with an HTTP 2xx status. The portal keeps the existing valid no-rows meaning.
- One client source succeeds with valid rows while the other client source fails. The portal returns the valid rows and records the failed source.
- Both client sources fail. The portal reports a failed read and does not return a success-shaped empty result.
- A response object has no usable status field. The portal treats the response as unavailable.
- A POST or another write method has a reset. The transport makes no second attempt.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST permit transport retries only for idempotent GET and HEAD requests.
- **FR-002**: The system MUST prohibit transport retries for POST and all other write requests.
- **FR-003**: A stale read reset MUST receive no more than one retry after the initial attempt.
- **FR-004**: No safe read MUST exceed three total transport attempts for all eligible connection failures.
- **FR-005**: An HTTP response status MUST NOT trigger a transport retry.
- **FR-006**: Upgrade portal write sessions MUST keep zero transport retries.
- **FR-007**: Write-session validation MUST reject a session that permits any transport retry.
- **FR-008**: `_fetch_org_sites` MUST treat `status_code is None` as a failed read.
- **FR-009**: `_fetch_org_sites` MUST treat each HTTP status of 400 or more as a failed read.
- **FR-010**: The directly related site, device, wireless client, and wired client pick-list reads MUST apply the same response-status rules.
- **FR-011**: A pick-list read with an HTTP 2xx status and no rows MUST remain a valid empty result.
- **FR-012**: A failed pick-list read MUST use the operator message, "The portal could not reach the Mist API. Try again."
- **FR-013**: A failed read MUST NOT use the valid no-rows message.
- **FR-014**: A failed read MUST NOT return an unmarked empty list that appears successful.
- **FR-015**: The system MUST log the failed read with enough non-secret context to identify the operation and status.
- **FR-016**: The system MUST NOT use a broad exception catch to classify response-status failures.
- **FR-017**: The system MUST NOT use a silent fallback when transport or response validation fails.
- **FR-018**: Tests MUST use fake or local transport behavior and MUST make zero live Mist calls.
- **FR-019**: Tests MUST prove a reset followed by a successful GET uses exactly two attempts.
- **FR-020**: Tests MUST prove a reset POST uses exactly one attempt.
- **FR-021**: Tests MUST prove missing status, HTTP refusal, valid empty 2xx, and exhausted reset outcomes.
- **FR-022**: The feature MUST NOT change retry behavior outside the shared safe read session and the named portal pick-list reads.

### Mist Cloud Transport Requirements

- The organization site picker uses `mistapi.api.v1.orgs.sites.listOrgSites`.
- The site device picker uses `mistapi.api.v1.sites.devices.listSiteDevices` with `type="all"` when no narrower device type is selected.
- The wireless client picker uses `mistapi.api.v1.sites.clients.searchSiteWirelessClients`.
- The wired client picker uses `mistapi.api.v1.sites.wired_clients.searchSiteWiredClients`.
- The feature MUST continue to use these mistapi methods. It MUST NOT add direct HTTP calls to Mist REST endpoints.
- Contract evidence MUST prove that the SDK returns an unavailable status after the local transport failure.
- Contract evidence MUST prove that authentication remains under the existing mistapi session.
- Contract evidence MUST prove that each picker still calls the same mistapi endpoint.
- Failure-safety evidence MUST prove that no write method receives a transport retry.
- Failure-safety evidence MUST prove that the upgrade portal write session keeps zero transport retries.
- Test and log evidence MUST contain no API token, password, authorization header, or session secret.

### Key Entities

- **Safe Read Retry Policy**: The allowed methods, retry limits, and failure classes for shared read sessions.
- **Write Session Policy**: The zero-retry rule for requests that can change Mist Cloud or production devices.
- **Pick-List Read Result**: The rows, response status, failure reason, and valid-empty state for one portal picker.
- **Operator Failure Message**: The plain-language reason that tells an operator that the portal did not receive a usable Mist API answer.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A local reset-then-success GET test returns the expected rows after exactly two transport attempts.
- **SC-002**: A local reset POST test records exactly one transport attempt and no repeated write.
- **SC-003**: Every tested unavailable or HTTP error response produces the Mist API reachability message.
- **SC-004**: Every tested empty HTTP 2xx response remains a valid empty result with the no-rows message.
- **SC-005**: The upgrade portal write-session checks report zero permitted transport retries.
- **SC-006**: The feature test set records zero live Mist API calls.
- **SC-007**: All specified failure paths produce an explicit failure reason, with no silent or success-shaped empty failure.
- **SC-008**: An operator can retry the affected pick-list action immediately after the failure message appears.

## Assumptions

- The shared Mist read session serves GET and HEAD requests that are safe to repeat.
- The existing upgrade portal write session remains separate from the shared read-session configuration.
- One retry is sufficient for the observed stale pooled connection reset.
- The broader limit of three total attempts permits bounded connection establishment recovery without unbounded delay.
- HTTP status failures remain application results and do not consume the transport retry budget.
- Directly related pick-list reads are the site, device, wireless client, and wired client readers in the portal operations route.
- Map page readers and other portal routes are outside this feature.
- Production code and test implementation occur during a later Spec Kit phase.
