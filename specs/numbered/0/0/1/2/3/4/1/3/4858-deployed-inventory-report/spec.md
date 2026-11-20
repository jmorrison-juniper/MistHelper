# Feature Specification: Deployed Inventory Report

**Feature Branch**: `fix/4858-deployed-inventory-report`

**Created**: 2026-11-19

**Status**: Draft

**Input**: Issue 4858: Add deployed inventory evidence to menu 308.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Review Deployed Inventory by Organization (Priority: P1)

A renewal operator runs menu 308 for an organization or MSP. The operator sees deployed device counts for each organization and device type, in addition to stock, subscriptions, and contract evidence.

**Why this priority**: This view prevents a large retail organization from appearing as only a small stock pool.

**Independent Test**: Synthetic inventory contains assigned and unassigned devices. The report shows assigned devices as deployed and unassigned devices as stock.

**Acceptance Scenarios**:

1. **Given** an organization has 27,030 deployed devices, **When** the report completes, **Then** the deployed inventory summary reports the live deployed count without mixing stock into it.
2. **Given** T-Mobile USA Retail and its retail kiosk organizations are authorized, **When** the inventory totals are combined, **Then** the report exposes their total deployed count and does not hide inventory behind a 30,000-device threshold.

---

### User Story 2 - Separate Deployed and Stock Equipment (Priority: P1)

A renewal operator reviews deployed AP, switch, gateway, SSR, Mist Edge, and other inventory in the deployed report. The operator reviews unassigned equipment in the existing stock report.

**Why this priority**: The same serial must not appear in both categories with conflicting deployment meaning.

**Independent Test**: Synthetic records use a site ID for assigned devices and no site ID for stock devices. Each serial appears in the correct category only.

**Acceptance Scenarios**:

1. **Given** inventory has a site ID, **When** deployed inventory is built, **Then** the row is marked deployed.
2. **Given** inventory has no site ID, **When** stock inventory is built, **Then** the row remains stock and does not enter the deployed count.

---

### User Story 3 - Preserve Missing and Partial Inventory Results (Priority: P2)

An organization inventory read fails or returns an incomplete shape. The report keeps the failure visible and does not convert the missing count to zero.

**Why this priority**: A false zero would understate device and license exposure.

**Independent Test**: Synthetic HTTP failure and empty result tests verify failure status, Missing counts, and continued reports for other organizations.

**Acceptance Scenarios**:

1. **Given** an organization inventory read fails, **When** the report exports, **Then** organization status records the failure and deployed device counts remain Missing.
2. **Given** one of several organizations fails, **When** the report continues, **Then** other organization results remain visible.

---

### User Story 4 - Read Consistent Structured Console Output (Priority: P2)

A NOC operator starts MistHelper with warning or higher log thresholds. The terminal shows concise warning and error lines, while no structured INFO or DEBUG records leak into the console or the runtime log.

**Why this priority**: This keeps startup, DNS, database, and inventory diagnostics readable without losing operational evidence.

**Independent Test**: A test run configures both logging levels at WARNING and emits INFO, DEBUG, and WARNING records through the structured and standard logging frontends.

**Acceptance Scenarios**:

1. **Given** both logging thresholds are WARNING, **When** structured INFO and DEBUG records are emitted, **Then** neither record appears in the console or script.log.
2. **Given** a structured WARNING record is emitted, **When** the thresholds are WARNING, **Then** the record appears once in the console and once in script.log.
3. **Given** the terminal threshold is WARNING and the file threshold is INFO, **When** an INFO record is emitted, **Then** the record can appear in script.log and remains absent from the console.

---

### Edge Cases

- Inventory pagination crosses more than one page.
- A response contains Virtual Chassis members that share or use different serial identities.
- A device has no site ID, serial, model, or device type.
- A switch has a synthetic 020003 or 020004 virtual identity and a physical chassis identity.
- A VC record contains nested physical member records.
- A list response is split across source payload shapes.
- Inventory is 27,000 rows or more for one organization.
- A license usage count and deployed inventory count differ.
- JSI evidence is absent or does not match a serial.
- Database or DNS diagnostics emit INFO, DEBUG, and WARNING levels.
- A process uses structlog and standard Python logging in the same startup.
- A log contains a token or password.
- A terminal cannot support ANSI color sequences.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Menu 308 MUST export a deployed inventory view for every organization that the active profile and MSP grants authorize.
- **FR-002**: Menu 308 MUST keep deployed inventory separate from unassigned stock inventory.
- **FR-003**: The deployed inventory view MUST identify organization, MSP, site, serial or identity, model, device type, deployment status, and connection status where the source provides it.
- **FR-004**: The deployed inventory view MUST export an organization and device-type summary with one visible count per organization and type.
- **FR-005**: The report MUST reconcile the inventory count across all paginated source pages.
- **FR-006**: The report MUST include each Virtual Chassis member as inventory evidence when the source identifies the member separately.
- **FR-007**: The report MUST retain Missing when device counts or identity fields are unavailable.
- **FR-008**: The report MUST not create a false success or false zero for a denied or failed inventory read.
- **FR-009**: The report MUST continue with visible partial results when another organization succeeds or fails.
- **FR-010**: The report MUST use one read-only menu operation and linked reports.
- **FR-011**: The report MUST not change an organization, device, subscription, or inventory state.
- **FR-012**: Structured database and DNS records MUST use the same console threshold as standard Python log records.
- **FR-013**: Structured records MUST use the same file threshold as standard Python log records.
- **FR-014**: The console frontend MUST keep key-value context available for structured diagnostics.
- **FR-015**: The file backend MUST keep timestamped plain-text records that remain readable and searchable.
- **FR-016**: The console frontend MUST preserve the ASCII-only output rule and avoid a required ANSI color mode.
- **FR-017**: Credentials and secrets MUST remain redacted in both structured and standard log records.
- **FR-018**: Menu 308 MUST prefer a physical chassis serial over a synthetic 020003 or 020004 virtual identity.
- **FR-019**: Deployed and stock inventory reports MUST expose the VC MAC, chassis serial, chassis MAC, and chassis model when the source provides them.

### Mist Cloud Transport Requirements *(include if feature uses Mist Cloud)*

- The inventory source is `getOrgInventory`.
- The existing MSP organization source is `listMspOrgs`.
- The active profile source is `getSelf`.
- The subscription sources are `getOrgLicensesSummary`, `getOrgLicensesBySite`, and `listMspLicenses`.
- The contract evidence source is `searchOrgJsiAssetsAndContracts`.
- Direct HTTP requests are prohibited when a mistapi SDK method exists.
- Pagination contract tests MUST prove more than one inventory page.
- Failure tests MUST prove HTTP denial, partial organization failure, and invalid result shape.
- Authentication and secret-redaction tests MUST keep passwords and tokens out of reports and logs.
- No WebSocket transport is required.

### Logging Transport Requirements

- The standard Python logging system MUST remain the backend for console and file handlers.
- The structlog frontend MUST emit through the same stdlib logger and handler levels.
- The database and DNS modules MUST not create a separate console handler.

### Key Entities *(include if feature involves data)*

- **Deployed Inventory Row**: One device identity that has a site assignment and its organization, MSP, site, model, type, serial, connection status, and source attribution.
- **Deployed Inventory Summary**: One organization and device-type count that reconciles the deployed detail rows.
- **Stock Inventory Row**: One unassigned device identity that requires a license or support review.
- **Organization Status**: Organization authorization and source request status.
- **Structured Console Record**: One structured diagnostic event with a name, level, message, and optional non-sensitive key-value context.
- **Log Threshold**: One console or file minimum severity that suppresses lower-severity records.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A live T-Mobile USA Retail result shows deployed device rows instead of only 152 stock rows.
- **SC-002**: The deployed inventory count for T-Mobile USA Retail is no lower than 27,000 in the existing 2026-11-11 snapshot when the live source is unchanged.
- **SC-003**: T-Mobile USA Retail and its retail kiosk organizations show separate live totals and a combined retail total.
- **SC-004**: The report identifies the number of deployed AP, switch, gateway, SSR, Mist Edge, and other devices for every successful organization.
- **SC-005**: An inventory set with more than 1000 devices yields an exact reconciled count across all pages.
- **SC-006**: Every failed organization has a visible status and Missing deployed count.
- **SC-007**: No stock row with a site ID enters the deployed detail or summary.
- **SC-008**: With both thresholds set to WARNING, 100 percent of INFO and DEBUG records from structlog and standard logging are absent from console and script.log.
- **SC-009**: A structured WARNING record appears exactly once in the console and exactly once in script.log.
- **SC-010**: A structured INFO record can appear in script.log at file level INFO while remaining absent from the console at WARNING.
- **SC-011**: Database and DNS diagnostics retain key-value context without exposing credentials or passwords.
- **SC-012**: The console remains readable in terminals that do not accept ANSI color sequences.

## Assumptions

- The active interactive account has MSP organization access.
- The inventory source distinguishes deployed devices by a site ID.
- The organization license usage result may differ from the inventory count and remains a separate entitlement view.
- The existing 2026-11-11 MSP inventory snapshot is a comparison baseline, not a live source.
- The report keeps deployed detail and stock evidence separate in linked outputs.
- Missing source values remain Missing, and Missing is not zero.
- Standard Python logging remains the backend for console and file output.
- Structlog is the structured frontend for database and DNS diagnostics.
- Terminal ANSI color is optional and not required for correct information.
