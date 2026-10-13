# Feature Specification: Mist Organization Licensing Comparison

**Feature Branch**: `jmorrison-jnpr-4197-mistorglicensingcomparison-integrat`

**Created**: 2026-10-13

**Status**: Draft

**Input**: User description: "Migrate MistOrgLicensingComparison into MistHelper under issue #4197. Preserve its organization comparison dashboard, accessible organizations, license and inventory comparisons, manual organization rows, purchased license inputs, remaining-license calculations with SUB-AI bundle components, and CSV export. Keep browser-session data in that session. Preserve CC BY-NC-SA 4.0 attribution. Use MistHelper's existing Flask portal, shared Mist API session, and shared data services. Do not add a database, Redis service, separate frontend or server, or public port. Plan the implementation but do not start it."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Compare organizations (Priority: P1)

An operator selects organizations that the active Mist session can access and compares their license use and inventory in one view.

**Why this priority**: Operators need a reliable comparison before they can review license balances.

**Independent Test**: Use synthetic Mist responses for two authorized organizations and verify that the page shows each organization's license and inventory values.

**Acceptance Scenarios**:

1. **Given** an active Mist session with access to several organizations, **When** the operator opens the comparison page, **Then** the operator sees the source dashboard layout and can select only organizations available to that session.
2. **Given** two selected organizations, **When** the operator requests a comparison, **Then** the page shows each organization's license use and inventory.
3. **Given** a Mist request fails for one organization, **When** the comparison finishes, **Then** the page identifies that failure and does not show zero as a successful result.

### User Story 2 - Adjust license balances (Priority: P2)

An operator adds a manual organization row, enters purchased license amounts, and reviews remaining balances, including SUB-AI bundle components.

**Why this priority**: Operators need to compare purchased amounts with current use, including organizations that are not returned by Mist.

**Independent Test**: Add synthetic manual values and purchased amounts, then verify each remaining balance and SUB-AI component total.

**Acceptance Scenarios**:

1. **Given** a comparison page, **When** the operator adds a manual organization row, **Then** its validated values appear in the comparison.
2. **Given** a purchased amount and reported use, **When** the operator reviews the balance, **Then** the page shows the remaining amount for each license type.
3. **Given** a SUB-AI bundle amount, **When** the operator reviews its balance, **Then** the page accounts for each bundle component.
4. **Given** invalid or negative manual values, **When** the operator submits them, **Then** the page rejects them and identifies the invalid field.

### User Story 3 - Export the comparison (Priority: P3)

An operator exports the current comparison to a CSV file and retains the source license terms.

**Why this priority**: Operators need a portable report after they confirm the comparison.

**Independent Test**: Export a comparison with Mist and manual rows, then verify that the CSV contains the displayed values and safe cell text.

**Acceptance Scenarios**:

1. **Given** a completed comparison, **When** the operator exports it, **Then** the CSV contains the same organizations, license values, inventory values, and remaining balances.
2. **Given** a value that begins with a spreadsheet formula marker, **When** the operator exports it, **Then** the CSV neutralizes that value.
3. **Given** the exported report, **When** the operator reviews its attribution, **Then** the CC BY-NC-SA 4.0 source terms remain clear.

### Edge Cases

- If the shared Mist session is unavailable, the page reports that it cannot load organization data.
- If no organizations are available, the page offers no empty successful comparison.
- If one organization request fails, successful organizations remain visible and the failed organization has an explicit error.
- If Mist returns a rate-limit response, the comparison follows the source application's 60-second per-token handling.
- If a manual row duplicates an organization already in the comparison, the page prevents duplicate totals.
- If purchased values are absent, the page does not present an invented balance.
- If the browser session ends, manual rows and purchased amounts are not available in a later session.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Operators MUST access the comparison from the existing MistHelper Flask portal. The page MUST preserve the source dashboard layout and comparison workflow.
- **FR-002**: The comparison MUST use the active Mist session and MUST limit Mist-backed organization choices to organizations that session can access.
- **FR-003**: Operators MUST be able to compare license summaries, license use by site, and inventory for multiple organizations.
- **FR-004**: Operators MUST be able to add manual organization rows and purchased license amounts.
- **FR-005**: Manual rows and purchased amounts MUST remain in the current browser session only and MUST NOT enter a new persistent store.
- **FR-006**: The comparison MUST calculate remaining license amounts and include each SUB-AI bundle component.
- **FR-007**: The comparison MUST export the displayed values to CSV and neutralize spreadsheet formula input.
- **FR-008**: The page MUST identify Mist request failures and MUST NOT represent a failed or absent result as a successful zero.
- **FR-009**: The comparison MUST retain the source application's CC BY-NC-SA 4.0 attribution.
- **FR-010**: The migration MUST use MistHelper's existing portal and shared data services. It MUST NOT add a database, Redis service, separate frontend, separate server, or public port.
- **FR-011**: The comparison MUST preserve the source application's 60-second per-token handling for Mist rate-limit responses.

### Mist Cloud Transport Requirements

- Use the existing portal's shared `APISESSION` for each Mist request.
- Use the supported `mistapi` SDK methods `getSelf`, `listMspOrgs`, `getOrgLicensesSummary`, `getOrgLicensesBySite`, and `getOrgInventory` where their access scope applies.
- Do not send direct HTTP requests to Mist REST endpoints when a working SDK method exists.
- Add contract tests for SDK method availability, shared-session authentication, endpoint parity, pagination, visible failure behavior, and secret redaction.
- Do not add an owned WebSocket transport. The feature needs request-response comparison data and has no stated WebSocket output requirement.

### Key Entities

- **Accessible Organization**: An organization that the active Mist session can read.
- **License Summary**: The license types and totals reported for an organization.
- **License Use**: License use reported for an organization or its sites.
- **Inventory Summary**: Device inventory reported for an organization.
- **Manual Organization Row**: Operator-entered comparison values held only for the current browser session.
- **Purchased License Amount**: Operator-entered purchase totals held only for the current browser session.
- **Comparison Export**: A CSV representation of the displayed comparison values.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every selected, accessible organization appears once in the comparison with license and inventory values or an explicit failure status.
- **SC-002**: All valid manual rows and purchased amounts affect the displayed balance in the same browser session.
- **SC-003**: Every displayed comparison value appears in the exported CSV, and formula-like cell values are neutralized.
- **SC-004**: A new browser session contains none of the manual rows or purchased amounts from an ended session.
- **SC-005**: The migration adds zero databases, Redis services, separate frontends, separate servers, and public ports.

## Assumptions

- Operators already have an active Mist session in the MistHelper portal.
- The portal can discover the session's organization and MSP access scopes through supported Mist SDK methods.
- Manual rows and purchased values may disappear when the browser session ends.
- The existing shared data service remains the only export or storage service used by the feature.
- The source application's dashboard layout and CC BY-NC-SA 4.0 terms remain part of the migration.
