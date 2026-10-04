# Feature Specification: The browser seed captures hold the counts of a real capture

**Issue**: #3492
**Feature Branch**: `fix/3492-seed-device-type-counts`
**Status**: Implemented
**Found by**: the browser journey of #3486

## Problem

The browser tests store five seed captures. Each seed holds three devices:
one gateway, one switch, and one access point. The count map of each seed
holds three keys only: `devices_total`, `clients_wired`, and
`clients_wireless`.

A real capture holds nine count keys. The shipped function `build_counts` in
`src/interfaces/portals/upgrade_portal/capture/assembly.py` writes them. Three of the nine keys
count the devices of each type.

The Device types cell of the history page reads the three type counts. The
seeds hold no type count, so each seed row reads "No device type". No browser
test therefore proves the device type phrase of issue #2107. No browser test
measures the fit of a real phrase in a row.

The Tier 3 seed also holds one guest client. Its count map holds no guest
count, so the Clients cell of that row reads 3. The real capture of the same
lists reads 4.

## User Scenarios & Testing

### User Story 1 (P1): Each seed row names its device types

The operator who opens the history reads the device types of each capture in
its row.

**Independent test**: Open `/history?limit=200`. Read the Device types cell
of each seed row.

**Acceptance scenarios**:

| The seed capture | The Device types cell |
| - | - |
| `e2e-capture-pre-0001` | 1 gateway, 1 switch, 1 access point |
| `e2e-capture-standalone-0001` | 1 gateway, 1 switch, 1 access point |
| `e2e-capture-post-0001` | 1 gateway, 1 switch, 1 access point |
| `e2e-capture-stored-poll-0001` | 1 gateway, 1 switch, 1 access point |
| `e2e-capture-tier3-0001` | 1 gateway, 1 switch, 1 access point |

The `title` attribute of each cell holds the same phrase.

### User Story 2 (P1): The seed count map is the output of the real builder

A test author who adds a journey reads each seed in the shape that the portal
stores.

**Independent test**: For each seed, build a count map with the shipped
function `build_counts`. Use the device index, the device records, and the
client lists of that seed. Compare the result with the count map of the seed.

**Acceptance scenarios**:

1. **Given** each of the five seeds. **When** the test builds a count map
   from the lists of the seed. **Then** the result equals the count map of
   the seed, key for key.
2. **Given** a replaced builder that returns a marker map. **When** the test
   builds each seed again. **Then** each seed holds the marker map. The seed
   file therefore writes no count by hand.
3. **Given** the Tier 3 seed with one guest client. **When** the history page
   renders its row. **Then** the Clients cell reads 4.

### User Story 3 (P2): The real phrase stays on one line at three widths

The history has two Captures tables. The page with no site holds ten
columns, and the page of one site holds nine columns. The two tables use two
width sets of the stylesheet, so the journey measures each table.

**Acceptance scenarios**:

1. **Given** a real browser at a window width of 1024, 1280, and 1440 pixels.
   **When** the operator opens the history with no site or the history of one
   site. **Then** the height of each seed row is 48 pixels or less. This is
   the row budget of issue #2106. A screenshot records each page at each
   width.
2. **Given** the same page. **When** the cell is too narrow for the whole
   phrase. **Then** the cell clips the phrase on one line and shows an
   ellipsis. The `title` attribute holds the whole phrase.
3. **Given** the same page. **When** the journey reads each cell. **Then**
   the log records the width that the phrase needs and the width that the
   cell gives, at each window width.

### Edge Cases

- The seed index holds no device state, because the seed builds the index
  with no statistics list. The shipped builder therefore counts 0 connected
  devices and 3 disconnected devices. Issue #3494 holds that defect. This
  change keeps the output of the builder and writes no state count by hand.
- The capture page prints the nine counts of a stored capture. After this
  change, the page prints the state counts of a seed too. No browser test
  reads those values.
- The comparison page adds the three client counts of a capture. A journey
  that compares the Tier 3 seed can read 4 clients after this change.
- Many journeys share the browser test server, and some journeys store a
  capture. The new journey reads the rows of the five seeds by their
  identifiers.
- The page of one site shows four seed rows. The stored-poll seed belongs to
  a second site, so it shows on the page with no site only.

## Requirements

### Functional Requirements

- **FR-001**: Each seed capture holds the count map of the shipped function
  `build_counts`. The function reads the device index, the device records,
  and the client lists of that seed.
- **FR-002**: The seed file writes no count value by hand.
- **FR-003**: The Tier 3 seed builds its count map after it adds the guest
  client. The map therefore counts one guest client.
- **FR-004**: The Device types cell of each seed row reads "1 gateway, 1
  switch, 1 access point". The `title` attribute holds the same phrase.
- **FR-005**: A direct test with no browser proves FR-001 through FR-003 for
  each seed.
- **FR-006**: A browser journey proves FR-004. It measures the height of each
  seed row at 1024, 1280, and 1440 pixels on the two history pages. It saves
  one screenshot for each page at each width.
- **FR-007**: The change touches test files and specification files only. It
  changes no file under `src/`.

## Success Criteria

- **SC-001**: Each of the five seed rows reads the device type phrase. No
  seed row reads "No device type".
- **SC-002**: Each of the five seed count maps holds the nine keys of a real
  capture, and each value equals the output of the builder.
- **SC-003**: At each of the three widths on each of the two pages, the
  height of each seed row is 48 pixels or less.
- **SC-004**: Each browser test that passed before the change passes after
  the change.

## Assumptions

- The shipped function `build_counts` is the one writer of the count map in a
  real capture. The research names the call.
- The row budget of issue #2106 holds for the device type phrase. If the
  journey proves that the phrase breaks the budget, a new issue holds that
  finding.

## Out of Scope

- The state of the seed device index and the comparison of versions. Issue
  #3494 holds them.
- The width of the Device types column. The journey proved that the phrase
  clips at each width on each page. Issue #3495 holds that finding.
- The Site column of issue #3486 and the table layout of issue #3491.
