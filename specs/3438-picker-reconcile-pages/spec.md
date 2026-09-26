# Feature Specification: The site picker and the reconciliation read name a lost page

**Issue**: #3438
**Feature Branch**: `fix/3438-picker-reconcile-pages`
**Status**: Draft
**Found by**: the code review of the #3424 fix on 2026-09-26

## Problem

Two reads outside the capture lose a later page and report nothing.

The site picker reads the site list and the device count of each site. Each
read asks for 1,000 records on one page. An organization with more than 1,000
sites needs a second page. `mistapi.get_all` adds each later page with no
status check. An error page in HTML adds nothing. The picker then shows a short
site list that looks complete. The operator cannot find a site of the lost
page, and the device count of a site can show 0.

The picker also hides a failed first page. The picker then shows an empty site
list with no note, and the operator cannot tell a failed read from an
organization with no site.

The reconciliation step reads the device statistics of one site. A lost later
page leaves some targets with no fresh row. Each such target then shows the
stored version of the run record as its running version. The step reports the
evidence as incomplete, when the portal did not read that evidence at all.

## User Scenarios & Testing

### User Story 1 (P1): The single-site picker warns about an incomplete site list

The operator must know that the site list can leave out sites.

**Independent test**: Choose an organization whose site read loses a later
page. Choose the single-site mode. Read the note above the site table.

**Acceptance scenarios**:

1. **Given** a site read that loses a later page, **When** the operator opens
   the site picker, **Then** a Caution note shows. The note states that the
   site list is not complete. The table shows each site that the read found.
2. **Given** a device count read that loses a later page, **When** the operator
   opens the site picker, **Then** a second Caution note shows. The note
   states that a site can show 0 devices.
3. **Given** two whole reads, **When** the operator opens the site picker,
   **Then** no note shows, and the table does not change.
4. **Given** a site read whose first page fails, **When** the operator opens
   the site picker, **Then** the site list note shows above an empty table.

### User Story 2 (P1): The multi-site picker shows the same note

The multi-site mode uses the same site picker. The operator selects several
sites from it, so an incomplete list matters more.

**Independent test**: Choose the same organization and the multi-site mode.
Read the note above the site table.

**Acceptance scenarios**:

1. **Given** a site read that loses a later page, **When** the operator opens
   the multi-site picker, **Then** the same Caution note shows. The note shows
   above the table of check boxes.
2. **Given** the note, **When** the operator selects a site of the first page
   and presses the forward control, **Then** the options page opens as before.

### User Story 3 (P1): A script reads the completeness of the site list

**Independent test**: Read `GET /api/sites` for the same organization.

**Acceptance scenarios**:

1. **Given** a site read that loses a later page, **When** a script reads the
   site list, **Then** the answer holds `site_list_complete` with the value
   `false`.
2. **Given** a device count read that loses a later page, **When** a script
   reads the site list, **Then** the answer holds `device_counts_complete` with
   the value `false`.
3. **Given** two whole reads, **When** a script reads the site list, **Then**
   both fields hold `true`, and the `sites` rows do not change.

### User Story 4 (P1): Reconciliation marks a target of a lost page as not read

**Independent test**: Reconcile a stale stopping run with two targets. The
statistics read answers page one with the first target and loses page two.

**Acceptance scenarios**:

1. **Given** a lost later page, **When** the portal reconciles the run,
   **Then** each target with no fresh row holds unavailable evidence. Its task
   state and its write state are `unavailable`.
2. **Given** the same read, **When** the portal builds the evidence, **Then**
   the target with no fresh row holds an empty running version. The stored
   version of the run record does not show as a running version.
3. **Given** the same read, **When** the portal reconciles the run, **Then**
   the target with a fresh row keeps its fresh evidence. The result reason is
   `cloud_evidence_unavailable`.
4. **Given** a whole paged read, **When** the portal reconciles the run,
   **Then** the evidence and the result do not change.
5. **Given** a first page that fails, **When** the portal reconciles the run,
   **Then** every target holds unavailable evidence, as it does today.

### Edge Cases

- The organization holds 1,000 sites or fewer. The read asks for no later page,
  and nothing changes.
- A later page answers an error status, answers no status, or holds no list.
  Each case is a lost page.
- The first page answers a body that the portal cannot read. The picker shows
  the site list note, and reconciliation marks every target unavailable.
- An operator opens the picker again within one minute of a lost page. The
  portal reads the cloud again, because it keeps a whole read only.
- An operator opens the picker again within one minute of a whole read. The
  portal uses the kept read, and no note shows.
- The organization holds no site, and the read is whole. The table is empty,
  and no note shows.
- A test stand-in answers a plain list. The portal reads a plain list as a
  whole read.

## Requirements

### Functional Requirements

- **FR-001**: The picker read follows every page of the site list read and of
  the device count read. A lost later page stops the read. The read keeps the
  rows of the pages before that page.
- **FR-002**: The picker read names each fault of the first page. A fault is
  an error status, no status, or a body that the portal cannot read. A count
  that differs from the total in the body is also a fault.
- **FR-003**: The log records each lost read with the read name and the reason
  code. The log holds no token and no site record.
- **FR-004**: The portal keeps a whole read for one minute, as it does today.
  It never keeps a read that lost a page.
- **FR-005**: The site picker shows one Caution note when the site list read
  lost a page. The note states the risk and the next step.
- **FR-006**: The site picker shows a second Caution note when the device count
  read lost a page.
- **FR-007**: The two notes show in the single-site mode and in the multi-site
  mode.
- **FR-008**: `GET /api/sites` and `GET /api/orgs/<org_id>/sites` add the fields
  `site_list_complete` and `device_counts_complete`. The `sites` rows do not
  change.
- **FR-009**: The reconciliation read follows every page of the site statistics
  read. A lost page, or a fault of the first page, marks each target with no
  fresh row as not read.
- **FR-010**: A target that is not read holds the task state and the write state
  `unavailable`, an empty running version, and no observation time. It is never
  complete, and it never proves a firmware success.
- **FR-011**: A target with a fresh row keeps its evidence after a lost page.
- **FR-012**: A whole paged read gives the same rows and the same evidence as
  before.

### Key Entities

- **Picker read**: the records of one cloud read and the partial reasons of
  that read. A read is whole when it holds no partial reason.
- **Site list**: the rows of the site picker, and one flag for each of the two
  reads. Each flag states whether its read is whole.
- **Unread target**: a reconciliation target that has no fresh row after a lost
  page.

## Out of Scope

- A later site check that reads an incomplete list still refuses with "no such
  site" or "choose sites". Issue #3439 tracks an honest refusal for that case.
- The capture reads and the gate read. Issue #3436 moves those reads to the
  page walk.
- A search or a paging control for a site list with more than 1,000 sites.

## Assumptions

- The note also covers a failed first page. The same read and the same fault
  class cause both cases, and an empty list with no note misleads the operator.
- A reload is the recovery step. A lost page is a short cloud fault, so a new
  read usually recovers.
- The signal word is Caution, because a reload recovers the list.

## Success Criteria

- **SC-001**: Each new unit test and contract test fails on the old code and
  passes after the change.
- **SC-002**: A browser journey shows the note in each mode. A screenshot
  records each page. The same journey shows no note for an organization whose
  reads are whole.
- **SC-003**: A whole read makes the same cloud calls as before: one call for
  each page. A second view within one minute still makes no cloud call.
- **SC-004**: No reconciliation evidence shows a stored version as the running
  version of a target on a lost page.
