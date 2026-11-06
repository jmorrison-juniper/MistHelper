# Feature Specification: AP warning report

**Feature Branch**: `jmorrison-juniper-ap-warning-report`

**Created**: 2026-11-05

**Status**: Specified

**Input**: Export AP inventory with warning or error codes across all sites.
The user confirmed inclusion regardless of connection state.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Find AP trouble codes (Priority: P1)

An operator selects the new final menu operation and exports APs that report trouble codes.
The report excludes APs that are merely disconnected.

**Why this priority**: Operators need the affected APs without manually examining each site.

**Independent Test**: Provide healthy, connected-error, and disconnected-error APs, then compare the exported identities with the expected identities.

**Acceptance Scenarios**:

1. **Given** connected and disconnected APs with trouble codes, **When** the report runs, **Then** both appear.
2. **Given** APs without trouble codes, **When** the report runs, **Then** those APs do not appear.
3. **Given** several pages of inventory and sites, **When** the report runs, **Then** later pages contribute matching APs and site names.

### User Story 2 - Understand each code (Priority: P2)

An operator reads the reported code, definition, connection state, and observation time beside the inventory identity.

**Why this priority**: A code without its meaning does not explain the reported condition.

**Independent Test**: Match a zero-padded code to its definition and retain an unknown code with an explicit missing-definition indication.

**Acceptance Scenarios**:

1. **Given** a known code, **When** the report runs, **Then** its key, name, and description appear.
2. **Given** an unknown code, **When** the report runs, **Then** the code remains visible without an invented definition.
3. **Given** a historical trouble observation, **When** the report runs, **Then** its timestamp remains visible without claiming current failure.

### User Story 3 - Recognize incomplete reads (Priority: P1)

An operator receives an explicit failure when a required source cannot be read.

**Why this priority**: An incomplete report must not imply that excluded APs are healthy.

**Independent Test**: Fail a later page and confirm that the exporter writes no report.

**Acceptance Scenarios**:

1. **Given** a failed inventory, site, statistics, or definition read, **When** the report runs, **Then** it reports failure and writes nothing.
2. **Given** no matching codes, **When** the report runs, **Then** it reports zero matches and does not claim all APs are healthy.

### Edge Cases

- Unknown codes remain reportable.
- Missing statistics or trouble fields mean no reported evidence, not proof of health.
- Missing site names retain the site identifier and an explicit lookup status.
- Unassigned inventory APs remain eligible when they carry trouble evidence.
- Invalid response shapes stop the export.
- A missing organization selection stops before cloud requests.
- A failed output write does not produce a success message.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Add the next unused menu number after the last registered operation.
- **FR-002**: Read all organization sites and AP inventory pages without a site or connection filter.
- **FR-003**: Read all AP statistics pages to obtain documented trouble evidence.
- **FR-004**: Include only inventory APs with a nonzero reported trouble code, regardless of connection state.
- **FR-005**: Retrieve the code dictionary once per run and include its code, key, name, and description.
- **FR-006**: Preserve unknown codes and mark the absent definition explicitly.
- **FR-007**: Include organization, AP identity, site identity, connection state, trouble source, and observation time.
- **FR-008**: Use the existing export format selection and an organization-and-AP natural primary key.
- **FR-009**: Stop without a report if any required read fails or returns invalid data.
- **FR-010**: Keep this operation read-only and preserve existing menu behavior.
- **FR-011**: Use UTC ISO 8601 timestamps for report creation and available trouble observation times.
- **FR-012**: Distinguish missing trouble evidence from healthy evidence in the completion summary.

### Mist Cloud Transport Requirements

Use the supported SDK methods `listOrgSites`, `getOrgInventory`,
`listOrgDevicesStats`, and `listApLedDefinition`.
The code dictionary is `/api/v1/const/ap_led_status`, not the general alarm dictionary.
Use SDK pagination with validation of every page.
Use the existing session for authentication and rate-limit handling.
Tests must prove endpoint arguments, pagination failure safety, and absence of credentials from outputs.
No custom HTTP or WebSocket transport is necessary.

### Key Entities

- **Inventory AP**: The organization-scoped device identity, name, MAC address, serial, model, and assignment.
- **Trouble observation**: The most recently reported code, its timestamp, and its source.
- **Code definition**: The code, stable key, display name, and explanation supplied by Mist.
- **Site**: The organization site identifier and its display name.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All connected-error and disconnected-error fixture APs appear exactly once.
- **SC-002**: No fixture AP without a reported nonzero code appears.
- **SC-003**: Every known fixture code has the matching definition.
- **SC-004**: Every unknown fixture code remains visible with a missing-definition indication.
- **SC-005**: Every failed required read produces zero output writes.
- **SC-006**: Every matching AP on a later page appears with its available site identity.

## Assumptions

- Scope is the selected organization, not every organization accessible to the account.
- The latest reported trouble code can be historical and does not prove a current yellow LED state.
- An absent code, empty code, or numeric zero is not trouble evidence.
- Numeric codes retain at least two digits for matching and display.
- Statistics provide documented trouble evidence. Inventory evidence remains usable when statistics do not carry a code.
- The app already created and renamed this worktree branch. The branch hook must not create another checkout.
- The user permits independent work while pull request #4208 owns `README.md`.
  Menu integration and its documentation remain pending until that ownership ends.
