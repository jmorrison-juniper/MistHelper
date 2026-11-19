# Feature Specification: Cross-Org Subscription and Stock Inventory Report

**Feature Branch**: `feat/4838-cross-org-subscription-stock-report`

**Created**: 2026-11-19

**Status**: Draft

**Input**: User description: "Pull a view across all customer organizations. Show purchased, in-use, and unused AP, switch, SSR, and other subscriptions. Show start and end dates, including purchases after the December 2023 deal. Also show unassigned or stock equipment that may need licenses."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Review subscriptions across all accessible organizations (Priority: P1)

An operator starts one read-only report after MSP-level authentication.
The report discovers every organization that the active session can access.
It shows purchased, entitled, in-use, unused, expired, and over-entitlement subscription quantities for each organization and subscription type.
It shows the purchase start date and subscription end date for every available license record.

**Why this priority**: A renewal decision needs an MSP-wide purchased and use baseline.
One partial organization view can overstate or understate the renewal quantity.

**Independent Test**: Use synthetic profile, organization, license, amendment, and usage responses.
Run one report operation and verify one cross-org subscription row set for every authorized organization.

**Acceptance Scenarios**:

1. **Given** an active MSP session with two organizations, **When** the operator runs the report, **Then** both organizations appear once or show a visible access failure.
2. **Given** a subscription record with a quantity, start date, and end date, **When** the report reads it, **Then** the output keeps the quantity and both dates.
3. **Given** a purchase dated after 2023-12-31, **When** the report scores the record, **Then** it marks the record as post-the-original-deal.
4. **Given** a purchase dated on or before 2023-12-31, **When** the report scores the record, **Then** it marks the record as in or before the original deal.
5. **Given** entitled quantity and in-use quantity, **When** use is lower than entitlement, **Then** unused entitlement equals entitlement minus in-use quantity.
6. **Given** in-use quantity above entitlement, **When** the report scores the type, **Then** it shows a positive over-entitlement quantity.
7. **Given** a missing start or end date, **When** the report writes the row, **Then** it uses a missing marker and does not infer a date.

---

### User Story 2 - Identify stock equipment that may need licenses (Priority: P1)

An operator receives a stock inventory list beside the subscription view.
The report identifies AP, switch, gateway, SSR, Mist Edge, and other inventoried devices without a site assignment.
It joins available JSI or contract data by serial number when the active account provides that data.

**Why this priority**: Purchased licenses can cover equipment that never deployed.
This stock can require an additional subscription or expose unused purchased capacity.

**Independent Test**: Use synthetic inventory and JSI rows that include assigned and unassigned devices.
Run the report and verify that only unassigned devices appear in the stock section.

**Acceptance Scenarios**:

1. **Given** an unassigned SSR130 inventory record, **When** the report reads inventory, **Then** it emits one stock row with model, type, serial, and organization.
2. **Given** an assigned AP inventory record, **When** the report reads inventory, **Then** it does not place the AP in the stock section.
3. **Given** stock and JSI records with the same serial, **When** the report joins the data, **Then** it shows the available contract state and end date.
4. **Given** stock with no JSI or contract match, **When** the report writes the row, **Then** it marks license review as required and does not claim a contract.
5. **Given** missing serial or model values, **When** the report writes the row, **Then** it keeps the row visible with missing markers.

---

### User Story 3 - Produce one complete report operation (Priority: P2)

An operator starts one menu operation without a separate workflow for each organization or report module.
The operation creates linked CSV reports and prints a concise summary.
The report preserves visible failures and never converts an unsuccessful API request into a zero.

**Why this priority**: A complete renewal packet should have one operator action and deterministic output.

**Independent Test**: Use synthetic authorized and failed organization responses.
Verify that all organization rows and result files finish with one menu operation.

**Acceptance Scenarios**:

1. **Given** a successful all-org read, **When** the operator runs the menu, **Then** the operation exports the subscription, organization, stock, and contract views.
2. **Given** one organization with a failed license request, **When** the report continues, **Then** the organization row shows a failure and a license value does not become zero.
3. **Given** no accessible organization, **When** the report runs, **Then** it states that no organization is accessible and creates no success-shaped data.
4. **Given** no JSI account link, **When** the report runs, **Then** it creates the stock report and marks JSI contract data as unavailable.
5. **Given** a completed report, **When** the operator reviews the console summary, **Then** the summary counts match the exported report rows.

---

### Edge Cases

- A profile grant contains repeated MSP, organization, or site values.
- A live MSP organization list is denied or returns no rows.
- A single organization is accessible without MSP organization access.
- A subscription record contains a null quantity, null date, unknown type, or duplicate record.
- An inventory record contains no site, serial, model, MAC address, or device type.
- JSI contract search has no linked account or returns no contract for a stock serial.
- An API endpoint returns HTTP 429 and one bounded retry fails.
- One organization succeeds and another organization fails.
- Two source records describe the same subscription or stock serial.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide one read-only menu operation for the cross-org subscription and stock report.
- **FR-002**: The system MUST discover direct organization access and MSP organization access from the active Mist session.
- **FR-003**: The system MUST include every distinct accessible organization once.
- **FR-004**: The system MUST include a visible failure row when one organization or MSP discovery request fails.
- **FR-005**: The system MUST show purchased quantity for every available license or subscription record.
- **FR-006**: The system MUST show entitled quantity, in-use quantity, unused entitlement, and over-entitlement quantity.
- **FR-007**: The system MUST show purchase start date and subscription end date for each available record.
- **FR-008**: The system MUST mark a purchase after 2023-12-31 as post-the-original-deal.
- **FR-009**: The system MUST mark a purchase on or before 2023-12-31 as in or before the original deal.
- **FR-010**: The system MUST group duplicate subscription records by subscription type and organization without hiding missing values.
- **FR-011**: The system MUST identify unassigned inventory as stock.
- **FR-012**: The system MUST include AP, switch, gateway, SSR, Mist Edge, and other inventory types.
- **FR-013**: The system MUST join contract evidence to stock by serial number when evidence is available.
- **FR-014**: The system MUST mark stock without contract evidence as requiring license or contract review.
- **FR-015**: The system MUST export the report in CSV or multiple linked CSV reports from one menu operation.
- **FR-016**: The system MUST print a console summary that identifies organization, subscription, and stock result counts.
- **FR-017**: The system MUST not change Mist organizations, subscriptions, devices, or contract state.
- **FR-018**: The system MUST preserve source attribution for the migrated licensing-comparison experience.
- **FR-019**: The system MUST not expose API tokens, passwords, or private credential values in reports or logs.
- **FR-020**: The system MUST provide visible partial-result status for HTTP 4xx and HTTP 5xx failures.

### Mist Cloud Transport Requirements *(include if feature uses Mist Cloud)*

- Use the active Mist session and mistapi methods for profile access, organization discovery, license summaries, license usage, inventory, JSI contracts, and MSP license data.
- Use `getSelf`, `listMspOrgs`, `getOrgLicensesSummary`, `getOrgLicensesBySite`, `getOrgInventory`, `searchOrgJsiAssetsAndContracts`, and `listMspLicenses` when the active session permits each method.
- Do not send direct HTTP requests when a supported mistapi method exists.
- Paginate inventory and JSI contract reads that advertise additional records.
- Retry one HTTP 429 response once after a 60-second wait for the same token.
- Do not retry other HTTP response failures.
- Use bounded request pacing and one request at a time.
- Contract tests MUST cover SDK method availability, shared-session authentication, organization authorization, pagination, partial failures, 429 retry behavior, and secret redaction.
- The feature MUST not require a WebSocket transport.

### Key Entities *(include if feature involves data)*

- **Organization Scope**: One direct or MSP-discovered organization that the active session may read.
- **Subscription Purchase**: A purchased or amended license record with type, quantity, start date, end date, and source identifier.
- **Subscription Balance**: Purchased, entitled, in-use, unused, and over-entitlement quantities for one organization and subscription type.
- **Inventory Asset**: An AP, switch, gateway, SSR, Mist Edge, or other device with identity and assignment fields.
- **Stock Asset**: An inventory asset that has no site assignment and may require a license or support review.
- **Contract Evidence**: JSI or device support evidence with serial number, status, model, and available end date.
- **Report Result**: Organization, subscription, stock, and contract rows plus request and completion status.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: One operator action produces a result for every authorized organization or a visible access failure for that organization.
- **SC-002**: Every available license record appears once with quantity and available purchase and end dates.
- **SC-003**: Purchased, entitled, in-use, unused, and over-entitlement quantities reconcile within 100 percent of valid source values.
- **SC-004**: Every unassigned inventory asset appears in the stock view once and has a license review state.
- **SC-005**: Every JSI contract match uses the same serial number and does not invent an absent end date.
- **SC-006**: The report completes for one organization and for multiple organizations under an authorized MSP session.
- **SC-007**: The console summary matches the exported row counts for the same result categories.
- **SC-008**: A failed organization read remains visible and does not produce a success-shaped zero quantity.

## Assumptions

- The active session is an authorized direct organization session or an authenticated MSP session.
- The active session can list its organization or MSP grants.
- "Unused entitlement" means entitled quantity minus in-use quantity, with a minimum of zero.
- "Purchased after the original deal" means the available purchase or start date is after 2023-12-31.
- "Stock" means the inventory record has no assigned site.
- JSI records use serial number as the preferred stock join.
- Missing JSI account, contract, start date, or end date is unavailable data, not zero or false support.
- The source licensing-comparison repository provides workflow and comparison inspiration.
- The source repository remains separate until the migration and review process is complete.
