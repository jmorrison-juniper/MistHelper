# Feature Specification: A short inventory read never looks complete

**Issue**: #3424
**Feature Branch**: `fix/3424-short-inventory-read`
**Status**: Draft
**Found by**: the review of the #3389 fix on 2026-09-26

## Problem

The options page and the options save read the inventory of each site. A read
can stop after the first page. The read then keeps the rows of the first page,
and it records a partial reason. `build_options_view` and
`build_options_record` read the rows only. They drop the partial reason.

The operator then sees a table that looks complete, and the page shows no
warning. The saved plan leaves out the devices of the lost pages. No message
names those devices, so they stay on the old firmware with no record.

The single-site mode and the multi-site mode both use this path.

The code review of this fix found a second gap. `getOrgInventory` answers a
JSON list, and the cloud sends the page total in a header only. The guard
reads a total from the body, so a lost later page gave no partial reason. A
JSON error page also made the row copy raise `ValueError`. The options page
does not catch that error, so it answers status 500. Each save answers status
400 with the raw error text.

## User Scenarios & Testing

### User Story 1 (P1): The single-site page warns about an incomplete device list

The operator must know that the table can leave out devices before the save.

**Independent test**: Open the options page of a run whose site read is short.
Read the banner above the table.

**Acceptance scenarios**:

1. **Given** a site whose inventory read stops after the first page, **When**
   the operator opens the options page, **Then** a banner with the signal word
   Caution states that the device list is not complete. The table shows each
   device that the read found.
2. **Given** a site whose read is complete, **When** the operator opens the
   options page, **Then** no such banner shows.
3. **Given** a site whose read fails, **When** the operator opens the options
   page, **Then** the same banner shows.

### User Story 2 (P1): The single-site save stops on a short read

**Independent test**: Save the options of a run whose site read is short at
the save. Read the answer and the run record.

**Acceptance scenarios**:

1. **Given** a short read at the save, **When** the operator saves the options,
   **Then** the save stops with status 400 and the code `bad_option`. The
   message tells the operator to reload the page and to save again.
2. **Given** the refused save, **When** a test reads the run record, **Then**
   the record keeps its earlier targets.
3. **Given** a complete read at the save, **When** the operator saves the
   options, **Then** the save keeps its current behavior.
4. **Given** a read that finds no device, **When** the operator saves the
   options, **Then** the save keeps the empty-record rule of #3389 (FR-007).

### User Story 3 (P1): The multi-site page and save name each short site

**Independent test**: Select two sites, and make the read of one site short.
Open the options page, then press Review.

**Acceptance scenarios**:

1. **Given** two selected sites, and the read of one site is short, **When**
   the operator opens the options page, **Then** a Caution banner names that
   site.
2. **Given** the same sites, **When** the operator presses Review, **Then** the
   save stops, and the message names that site. The browser session holds no
   saved options, and the store holds no plan.
3. **Given** a complete read on the page and a short read at the save, **When**
   the operator saves the options, **Then** the save stops, and the message
   names that site.
4. **Given** a retry plan of issue #3247 with a short site, **When** the
   operator saves the options, **Then** the save stops and names that site.
5. **Given** one unread site and one short site, **When** the operator saves
   the options, **Then** the refusal names the unread site first, with the
   #3389 message.

### User Story 4 (P2): The operator recovers in a real browser

**Acceptance scenarios**:

1. **Given** the single-site refusal, **When** the operator reads the page,
   **Then** the flash region shows the refusal text.
2. **Given** the multi-site refusal, **When** the operator clears the short
   site on the Sites page and presses Review again, **Then** the confirm page
   opens.

### Edge Cases

- The read finds no device and records no reason. This is an empty site. No
  banner shows, and the #3389 rules apply.
- The read finds no device and records a reason. This is a failed read. The
  banner shows, and the save keeps the #3389 rules.
- The page read is complete, and the save read is short. The save read
  decides, because the page read can be old.
- A saved choice outranks a fresh read in the single-site table. The banner
  still follows the fresh read, because the save reads the site again.
- More than ten sites are short. The refusal names ten sites, and then it
  states the count of the other sites.
- A later page answers an error status, or it holds no list. The read keeps
  the rows of the pages before that page, and the read is short (FR-013).
- The site holds one page of devices. The read asks for no later page.

## Requirements

### Functional Requirements

- **FR-001**: The options view of a site reports each partial reason of its
  inventory read. A complete read reports an empty list.
- **FR-002**: The single-site options page shows a Caution banner when the view
  holds one or more partial reasons. The banner states the risk and the next
  step.
- **FR-003**: The single-site save stops when its inventory read holds one or
  more devices and one or more partial reasons. The answer is status 400 with
  the code `bad_option`. The message tells the operator to reload the page and
  to save again.
- **FR-004**: A refused single-site save does not change the run record.
- **FR-005**: The empty-record rule of the single-site save does not change.
- **FR-006**: The multi-site options page shows one Caution banner. The banner
  names each selected site whose view holds a partial reason.
- **FR-007**: The multi-site save stops when the view read or the save read of
  a selected site is short. The message names each such site with the name
  rule of #3389 (FR-006).
- **FR-008**: The multi-site refusal order is the unread sites first, then the
  short sites, and then the unplanned sites.
- **FR-009**: A retry save applies the FR-007 refusal.
- **FR-010**: A refused multi-site save writes no plan and no saved options.
- **FR-011**: A short read at the save spends no version read.
- **FR-012**: The log records each short read with the site identifier and the
  reason codes. The log holds no device address and no secret.
- **FR-013**: The upgrade inventory read checks the status and the body of each
  later page. A lost later page gives the reason `page_count_mismatch` with the
  status of that page. The read keeps the rows of the pages before that page.
- **FR-014**: The upgrade inventory read never raises. A record that is not a
  map fails the read with the reason `read_failed`.

### Key Entities

- **Inventory read**: the rows of one site and the partial reasons of the read.
  A read is short when it holds one or more rows and one or more reasons.
- **Short-read refusal**: the refusal of a single-site save. It holds the
  site and a copy of the reasons.
- **Short site**: a selected site of a multi-site save whose read is short.

## Out of Scope

- A failed read at the single-site save stores thin target rows. Issue #3435
  covers that case.
- The inventory reads of the run driver.
- The capture reads and the gate read. Issue #3436 moves those reads to the
  page walk of FR-013.
- A confirmation that lets the operator save an incomplete device list.
  `research.md` (D1) states the reason.

## Success Criteria

- **SC-001**: Each new unit test and contract test fails on the old code and
  passes after the change.
- **SC-002**: A browser journey shows the banner and the refusal in each mode.
  A screenshot records each page.
- **SC-003**: The page read and the save make no more cloud calls than before.
  A short read at the save makes one fewer call.
- **SC-004**: Each existing upgrade-portal test passes after the change.
- **SC-005**: A unit test with a real SDK answer and the page headers proves
  FR-013 for an HTML error page and for a JSON error page.

## Assumptions

- A short read is rare. It needs more than one page of devices at one site,
  and one page holds 1,000 devices (`MIST_PAGE_LIMIT`).
- A reload of the page usually gives a complete read.
- The signal word is Caution, because the operator can recover with a reload.
