# Feature Specification: History scope descriptions

**Feature Branch**: `jmorrison-juniper-history-scope-descriptions`

**Created**: 2026-10-01

**Status**: Verified for publication

**Input**: Repair [issue #3485](https://github.com/jmorrison-juniper/MistHelper/issues/3485).
The history of one site must not describe the records of the whole organization.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read the history of one site (Priority: P1)

An operator opens the history of one site.
The Runs, Multi-site upgrades, and Audit log cards state that site scope.
An empty card describes only that site, even when other sites hold records.

**Why this priority**: The current empty statements can suggest that the portal lost records from other sites.

**Independent Test**: Open an empty site's history in an organization with records on other sites.
Read each card note, empty row, and accessible caption.

**Acceptance Scenarios**:

1. **Given** an empty site and populated other sites, **When** the operator opens its history, **Then** all nine descriptions name site scope.
2. **Given** a site with a stored name, **When** the operator opens its history, **Then** each card note and caption uses that name.
3. **Given** no stored name for the requested site, **When** the operator opens its history, **Then** the descriptions name the selected site.
4. **Given** a site name with markup characters, **When** the operator opens its history, **Then** the browser shows the name as text.

### User Story 2 - Read the history of the selected organization (Priority: P1)

An operator opens the history without a site filter.
The three cards describe the selected organization.
No card description names one site from its first row.

**Why this priority**: Organization history and site history must describe the same scope that their records use.

**Independent Test**: Open organization history with populated records.
Repeat with an empty organization.
Read each card note, empty row, and accessible caption.

**Acceptance Scenarios**:

1. **Given** records from several sites, **When** the operator opens organization history, **Then** all notes and captions name the selected organization.
2. **Given** an empty selected organization, **When** the operator opens its history, **Then** all three empty rows name that organization.
3. **Given** records from another organization, **When** the operator opens selected organization history, **Then** those records and names remain absent.

### User Story 3 - Keep existing history behavior (Priority: P2)

An operator reads the same records, counts, and page controls after this text repair.
The portal keeps its existing access decisions and operator attribution.

**Why this priority**: A text repair must not change record visibility or upgrade controls.

**Independent Test**: Compare exact record identifiers, counts, page bounds, attribution, and refusal responses with the existing history contracts.

**Acceptance Scenarios**:

1. **Given** a page window, **When** the operator requests history, **Then** the same ordered identifiers and total reach the page and history endpoints.
2. **Given** a missing or invalid organization selection, **When** the operator requests history, **Then** the portal refuses before it reads any source.
3. **Given** an absent or mismatched sign-in cookie, **When** the operator requests history, **Then** the existing sign-in refusal remains unchanged.

### Edge Cases

- An empty site can share an organization with populated sites.
- A populated capture list can accompany empty run, operation, and audit lists.
- A later capture page can hold no site name.
- A requested site can belong to another organization or have no matching record.
- A request can include a conflicting organization or site-name query value.
- A multi-site upgrade can include the selected site and other sites.
- An unavailable operation store must retain its existing unavailable message.
- A site name can contain quotes, ampersands, or markup characters.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Each of the three cards must receive a scope-specific note, empty statement, and accessible caption.
- **FR-002**: Site history must describe single-site runs and lock actions of the requested site only.
- **FR-003**: Site history must describe multi-site upgrades that include the requested site.
- **FR-004**: History without a site filter must describe the selected organization, not the portal or one row's site.
- **FR-005**: The descriptions must reuse the existing trusted display name from the scoped capture rows.
- **FR-006**: If no trusted display name exists, the descriptions must name the selected site without inventing a name.
- **FR-007**: The browser must show stored site names as text, never as executable markup.
- **FR-008**: The history template must print settled descriptions without choosing site or organization rules.
- **FR-009**: Queries, source calls, totals, order, pagination, organization isolation, attribution, authentication, and signed cookies must not change.
- **FR-010**: This repair must not read live cloud data, write production records, or change an upgrade decision.

### Key Entities

- **History scope**: The selected organization with an optional site filter and an existing trusted site name.
- **Card descriptions**: A note, an accessible caption, and an empty statement for one history card.
- **Multi-site upgrade**: An upgrade that can include the selected site and other sites.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All nine descriptions state site scope for an empty site with populated other sites.
- **SC-002**: All six visible notes and accessible captions state the correct scope on populated site and organization pages.
- **SC-003**: All three empty rows state organization scope when the selected organization holds no matching records.
- **SC-004**: A real browser verifies both site history and organization history without skipping any required case.
- **SC-005**: Existing record, count, order, pagination, attribution, and access contracts report no behavior change.

## Assumptions

- The existing signed organization selection remains the access authority.
- A scoped capture row supplies the existing trusted site display name.
- A missing display name requires the words "the selected site", not a cloud read.
- The Captures card, table layout, and upgrade controls remain outside this repair.
- The parent controls publication after the local commit.
