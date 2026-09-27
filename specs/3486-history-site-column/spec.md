# Feature Specification: The Captures table of the history with no site names the site of each row

**Issue**: #3486
**Feature Branch**: `fix/3486-history-site-column`
**Status**: Draft
**Found by**: a browser probe during the work on #3449

## Problem

The history page serves one site or every site. The page with no `site_id`
value lists the stored captures of every site in one table. The table has
these columns: Capture, Started, Role, State, Devices, Device types, Clients,
Stored size, and Action. No column names the site of a row.

In the browser fixtures, the table lists 5 captures from 2 sites. Four rows
belong to "E2E Stand-In Site". The row `e2e-capture-stored-poll-0001` belongs
to "E2E Stored Poll Site". No cell of the table shows that difference.

The Runs table of the same page already has a Site column. An operator can
open a capture of the wrong site. The operator then reads the wrong record
before an upgrade decision.

## User Scenarios & Testing

### User Story 1 (P1): Each row of the history with no site names its site

The operator who opens the history with no site must read the site of each
capture in its row.

**Independent test**: Open `/history` with no `site_id` value. Read the
column headers and the site cell of each row.

**Acceptance scenarios**:

| The stored capture record | The site cell |
| - | - |
| The site name "E2E Stored Poll Site" | E2E Stored Poll Site |
| The site name "E2E Stand-In Site" | E2E Stand-In Site |
| A site identifier and no site name | The site identifier |

The table shows the Site column second, after the Capture column. The hidden
caption of the table reads "The stored captures of every site. Each row holds
the site, the moment, the role, the state, the device count, the device
types, the client count, and the stored size."

### User Story 2 (P1): The history of one site keeps its table

The operator who opens the history of one site reads rows of that site only.
A Site column would repeat one name in each row, so the table does not
change.

**Independent test**: Open the history of one site. Read the column headers.

**Acceptance scenarios**:

1. **Given** the history of one site. **When** the page renders. **Then** the
   table shows the nine columns of today and no Site column.
2. **Given** the same page. **When** a screen reader reads the caption.
   **Then** the caption reads "The stored captures of the site. Each row holds
   the moment, the role, the state, the device count, the device types, the
   client count, and the stored size."

### User Story 3 (P2): The operator reads and sorts the Site column in a real browser

**Acceptance scenarios**:

1. **Given** a real browser and the stored captures of two sites. **When** the
   operator opens `/history` with no site. **Then** the table shows the Site
   column, and each row names its site. The Open control of each row stays on
   one line. A screenshot records the page.
2. **Given** the same page. **When** the operator pushes the Site header.
   **Then** the rows sort by the site text.
3. **Given** the same browser. **When** the operator opens the history of the
   site that holds one capture. **Then** the table shows no Site column. A
   screenshot records the page.

### Edge Cases

- If a site name is long, the cell clips it on one line and shows an
  ellipsis. The `title` attribute of the cell holds the whole name.
- If a record holds no site name and no site identifier, the cell is empty.
  The Site cell of the Runs table follows the same rule.
- If the route gives no column value, the page renders the table of one
  site. Each earlier render test then stays valid.
- If the page with no site holds no capture, the empty row spans the ten
  columns of the table.
- A site name is text from the store. The page escapes it.
- Many journeys share the browser test server, and some journeys store a
  capture. The browser journey therefore reads the rows of the five seed
  captures by their identifiers.

## Requirements

### Functional Requirements

- **FR-001**: If the request holds no `site_id` value, the Captures table
  shows a Site column after the Capture column.
- **FR-002**: Each site cell shows the site name of the capture record. If
  the record holds no site name, the cell shows the site identifier.
- **FR-003**: The site cell holds its whole text in a `title` attribute. It
  clips a long text on one line.
- **FR-004**: Each site cell carries the test identifier
  `history-site-{capture_id}`.
- **FR-005**: If the table shows the Site column, the hidden caption names the
  site in the list of row values.
- **FR-006**: If the request holds a `site_id` value, the table shows no Site
  column. The caption does not change.
- **FR-007**: The Site header sorts the rows in the same way as the other
  headers.
- **FR-008**: The route decides whether the table shows the Site column. The
  template holds no rule.
- **FR-009**: The empty row of the table spans every column of the table.

## Success Criteria

- **SC-001**: On the page with no site, each row names its site.
- **SC-002**: On the page of one site, the table and the caption do not
  change.
- **SC-003**: The change adds no cloud read, no store read, no write, no
  route, and no field of a JSON body.
- **SC-004**: At a window width of 1280 pixels, the Open control of each row
  stays on one line.
- **SC-005**: At a window width of 1280 pixels, the Site column hides no sort
  arrow. Each header that shows its sort arrow on the page of one site also
  shows it on the page with no site. The Site header also shows its sort arrow.

## Assumptions

- Each stored capture record holds the site name and the site identifier.
  The research names the writer of both fields.
- The page with no site reads every capture in the store. Issue #3484 holds
  the change that narrows the list to the selected organization. The Site
  column stays useful after that change, because one organization holds many
  sites.
- The site cell shows text and no link. The Open control of the row stays the
  one control of the row.

## Out of Scope

- The organization scope of the lists. Issue #3484 holds it.
- The notes of the Runs card, the Multi-site upgrades card, and the Audit log
  card. Issue #3485 holds them.
- A site filter control on the history page.
