# Feature Specification: Read-only Mist target discovery for converter proposals

**Feature Branch**: `4642-converter-target-discovery`

**Created**: 2026-11-26

**Status**: Draft

**Issue**: #4642. Parent: #4224. Prerequisites: #4634 and #4641. Both prerequisites remain OPEN.

**Input**: User description: "[Spec]: Add read-only Mist target discovery for converter proposals" (issue #4642, labels `feature` and `web-portal`).

## Context

The Cisco converter preview runs offline. An operator cannot yet see whether Mist answers, whether the operator session can reach an organization, or which sites and gateways exist. This feature adds three read-only checks: status, sites, and gateways. Each check returns exactly one state. A failed read never appears as an empty organization.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Confirm the connection and organization membership (Priority: P1)

An operator runs the status check. The page shows one state: Verified, Unavailable, Denied, or Failed. For a chosen organization, the page also shows whether the operator session belongs to that organization.

**Why this priority**: Every target choice needs a trusted connection and a trusted membership result.

**Independent Test**: Run the status check with synthetic sessions that return each state. Each run shows one state label and no site list.

**Acceptance Scenarios**:

1. **Given** no operator session, **When** the operator runs the status check, **Then** the page shows Unavailable with reason `no_session`, and the preview stays available.
1. **Given** a session without the chosen organization, **When** the operator runs the site check, **Then** the page shows Denied and no site list.
3. **Given** Mist returns HTTP 429 after the SDK retries, **When** the operator runs a check, **Then** the page shows Unavailable with reason `rate_limited`.

### User Story 2 - Select verified sites and gateways by stable identity (Priority: P1)

After a verified site check, the operator selects a site by its identifier. Duplicate site names show a warning, and the identifier stays the only selection key. The gateway check shows each gateway as assigned or unassigned. Selecting a target does not change Mist.

**Why this priority**: A later write issue needs an exact target. The proposal cannot name a target that discovery did not verify.

**Independent Test**: Use a mocked site list over three pages with one duplicate name. Use a mocked gateway inventory with one assigned gateway and one unassigned gateway.

**Acceptance Scenarios**:

1. **Given** a site list over three pages, **When** the site check runs, **Then** every site appears in a verified result.
2. **Given** two sites with the same name, **When** the list renders, **Then** both rows show the duplicate flag, and the identifier is the selection key.
3. **Given** an inventory item with no site identifier, **When** the gateway check runs, **Then** the item shows the assignment `unassigned`.

### User Story 3 - Keep preview and review usable (Priority: P2)

The operator can preview a configuration file while discovery is unavailable. A target change dispatches an event. Issue #4641 uses that event to clear any earlier review.

**Why this priority**: The offline converter remains the main workflow. Discovery adds context and must not block it.

**Independent Test**: Preview a fixture with no session. Change a selected target and observe the event.

**Acceptance Scenarios**:

1. **Given** no operator session, **When** the operator previews a file, **Then** the preview succeeds and no Mist call runs.
2. **Given** a selected site, **When** the operator changes the selection, **Then** the page dispatches the event `cisco-target-changed`.

### Edge Cases

- A first page with zero rows and no next page gives Verified with an empty list. This result is verified absence.
- A later page returns HTTP 500. The result is Failed, and no list appears.
- A full last page has no `X-Page-Total` header. The result is Failed with reason `completion_unproven`.
- A list spans more than 50 pages. The result is Failed with reason `page_limit_exceeded`.
- A status response has no `privileges` list. The result is Failed with reason `unexpected_response`.
- The `org_id` value is not a UUID. The route answers HTTP 400, and no SDK call runs.
- An inventory item has an empty `site_id`. The item shows the assignment `unassigned`.
- The SDK returns no HTTP status. The result is Unavailable with reason `no_response`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Each check returns exactly one state: verified, unavailable, denied, or failed.
- **FR-002**: A verified result with an empty list is verified absence. Only a complete read gives this result.
- **FR-003**: Every state other than verified returns `items` as null. The page never draws an empty list for those states.
- **FR-004**: Discovery calls mistapi functions with explicit keyword arguments. It sends no direct HTTP request and forwards no `*args` or `**kwargs`.
- **FR-005**: Discovery calls only `getSelf`, `listOrgSites`, `getOrgInventory`, and `mistapi.get_next`.
- **FR-006**: Discovery creates no site and no other object. It runs only for a check, never during preview or review.
- **FR-007**: Discovery reads the operator session through `identity.current_session()`. It uses that record's `cloud_session`. It stores no credential in the browser or in a file.
- **FR-008**: Without an operator session, each check returns Unavailable with reason `no_session`. Preview stays available.
- **FR-009**: Each site check and gateway check reads membership from the live `getSelf` privileges. An organization without a matching `org_id` gives Denied.
- **FR-010**: Pagination uses 1000 rows per page and at most 50 pages. A lost page, an incomplete read, or a page bound gives Failed.
- **FR-011**: A site with a duplicate name sets the duplicate flag. The site `id` is the only selection key.
- **FR-012**: Gateway items are read from `getOrgInventory` with `type` set to `gateway`. An item is assigned when `site_id` has a value. Otherwise it is unassigned.
- **FR-013**: The page states that selecting a target does not change Mist. Selection does not authorize a write.
- **FR-014**: A target change dispatches the event `cisco-target-changed`. Issue #4641 owns the listener that clears the review.
- **FR-015**: HTTP 401 and 403 give Denied. HTTP 429, 502, 503, 504, and a missing status give Unavailable. Other HTTP errors and malformed data give Failed. The SDK retry is the only retry.
- **FR-016**: Logs and responses carry state codes and counts. They never carry a token, a cookie, an authorization header, or a source configuration.
- **FR-017**: New code keeps each directory at five children or fewer. Each function keeps five parameters or fewer, five logical blocks or fewer, and 25 lines or fewer.
- **FR-018**: Each discovery route accepts `org_id` only as a UUID. An invalid value returns HTTP 400 before any SDK call.
- **FR-019**: Each discovery response carries `Cache-Control: no-store`.
- **FR-020**: Automated tests use mocked SDK responses and synthetic identities. Tests open no network socket.

### Mist Cloud Transport Requirements *(include if feature uses Mist Cloud)*

- The mistapi REST methods are `getSelf` (GET `/api/v1/self`), `listOrgSites` (GET `/api/v1/orgs/{org_id}/sites`), and `getOrgInventory` (GET `/api/v1/orgs/{org_id}/inventory`). The page helper `mistapi.get_next` issues GET for each later page.
- No owned WebSocket transport is proposed.
- SDK insufficiency: not applicable. The three SDK reads cover each check.
- SDK authentication: discovery uses the cloud session object that the operator session already holds. No new credential path exists.
- SDK endpoint parity: `design/contracts/mist-read.md` maps each function to its OpenAPI path and operation.
- Failure safety: each failure maps to one state. No write function appears in the change.
- Secret redaction: tests check each response and each captured log line for the synthetic token value.

### Key Entities *(include if feature involves data)*

- **DiscoveryResult**: One check outcome with `check`, `state`, `reason`, `org_id`, `pages`, and `items`. The `items` field is null unless the state is verified.
- **SiteTarget**: One site with `id` (natural key), `name` (display text), and `duplicate_name`.
- **GatewayTarget**: One gateway with `id` (natural key), `mac`, `serial`, `model`, `name`, `site_id`, and `assignment`.
- **OrganizationMembership**: One privilege entry with `org_id`, `scope`, and `role`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Each of the four states has at least one passing test.
- **SC-002**: No discovery test calls a write function, and the test asserts the list of calls.
- **SC-003**: A mocked list over three pages returns every row in one verified result.
- **SC-004**: The test run opens no network socket.
- **SC-005**: Every applicable local gate passes before the pull request opens.

## Assumptions

- The converter page receives an operator session only after shared portal registration (#4648). Until then, each check returns `no_session`.
- Mist sends `X-Page-*` headers for list endpoints, as the SDK expects. The live behavior is unverified (research U1).
- The operator enters or selects the organization identifier. The check validates it against live privileges.
- An empty `site_id` means unassigned. Issue #4634 confirms this meaning (research U2).
- Gateways are the only device type in scope.

## Out of Scope

- Writes, site creation, object creation, apply, backup, restore, and administration. These belong to issues #4644, #4645, and #4646.
- Shared portal route registration and shared template changes. These belong to issue #4648.
- A new credential type or a change to the sign-in flow.
- Changes to `models.py` or the state model. These belong to issue #4636.
- Changes to the proposal digest or the review rules. These belong to issue #4641.
- Live Mist requests, production credentials, and customer configurations in any test.
- New Python dependencies.

## Clarifications

- Q: Which existing service gives the Mist session? A: `identity.current_session()` in the upgrade portal runtime (D-3).
- Q: Where does the Mist check client live? A: In `src/mist/access/targets/`. The converter root and `routes.py` cannot take it (D-1, D-2).
- Q: Where do the discovery tests live? A: In `tests/integration/web_portal/cisco_config_converter/`. `tests/contract` cannot take a new child (D-10).
- Q: Does the code retry a 429? A: No. The SDK retry applies (D-8).
- Q: Is membership cached? A: No. Each check reads `getSelf` (D-9).
- Q: Is "Not checked" an API state? A: No. It is the page label before the first check (D-4).

## Dependencies

- Issue #4634 (API contract evidence) and issue #4641 (versioned proposal review) must close before implementation starts. Both remain OPEN.
- Issue #4224 is the parent issue. It remains OPEN.

## Decisions

Decisions D-1 to D-13 appear in `design/research.md`. Each decision names its alternatives, its reason, and its risk. No decision needs a human answer.
