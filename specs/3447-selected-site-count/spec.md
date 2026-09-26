# Feature Specification: The multi-site options page states the correct site noun

**Issue**: #3447
**Feature Branch**: `fix/3447-selected-site-count`
**Status**: Draft
**Found by**: the journey harness of #3200 during the work on #3439

## Problem

The multi-site options page shows a note above the device table. The note
states the count of the selected sites, and it always uses the noun "sites".
When the plan holds one site, the page says "One operation targets 1 selected
sites."

The operator reads this note to confirm the scope of the plan. A wrong noun
makes the count look wrong. The operator can then leave the page to examine
the selection again, or the operator can report a false defect.

A retry of one site shows the same text. A retry keeps only the sites of the
devices that did not reach the target version.

The single-site mode does not show this note, so the single-site mode does
not change.

## User Scenarios & Testing

### User Story 1 (P1): One selected site reads as one site

The operator must read the correct noun for a plan of one site.

**Independent test**: Select one site in the multi-site mode, and open the
options page. Read the note.

**Acceptance scenarios**:

1. **Given** the multi-site mode and one selected site, **When** the operator
   opens the options page, **Then** the note says "One operation targets 1
   selected site".
2. **Given** a retry of an operation whose failed devices are at one site,
   **When** the options page opens, **Then** the note says "One operation
   targets 1 selected site".
3. **Given** the end of that retry, **When** the options page opens again,
   **Then** the note says "One operation targets 1 selected site". The
   selection of the retry stays in place.

### User Story 2 (P1): Two or more selected sites read as sites

The operator must read the plural noun for a plan of two or more sites.

**Independent test**: Select two sites, and open the options page.

**Acceptance scenarios**:

1. **Given** two selected sites, **When** the operator opens the options page,
   **Then** the note says "One operation targets 2 selected sites".
2. **Given** a retry whose failed devices are at two sites, **When** the
   options page opens, **Then** the note says "One operation targets 2 selected
   sites".

### User Story 3 (P2): The operator sees the correct note in a real browser

**Acceptance scenarios**:

1. **Given** a real browser, **When** the operator selects one site and
   presses Continue, **Then** the note says "1 selected site". A screenshot
   records the note.
2. **Given** a real browser, **When** the operator selects two sites and
   presses Continue, **Then** the note says "2 selected sites". A screenshot
   records the note.

### Edge Cases

- The count is zero. The site check refuses a selection with no site, so the
  page does not open with zero sites. If a later change lets the page open,
  the note says "0 selected sites". English uses the plural noun for zero.
- The count is 11 or 21. The noun is "sites". Only the count 1 takes the
  singular noun.
- The second sentence of the note does not change.

## Requirements

### Functional Requirements

- **FR-001**: The note uses the noun "site" when the plan holds exactly one
  site.
- **FR-002**: The note uses the noun "sites" for each other count.
- **FR-003**: The note keeps its count, its first words, and its second
  sentence.
- **FR-004**: The note carries a stable test identifier. A test then reads
  the note without the text around it.
- **FR-005**: The rules of FR-001 and FR-002 apply to the sites of a retry.

## Success Criteria

- **SC-001**: For a plan of one site, each view of the options page shows the
  singular noun.
- **SC-002**: For a plan of two or more sites, each view of the options page
  shows the plural noun.
- **SC-003**: The change adds no cloud read and no page load.

## Assumptions

- The page uses the English plural rule. The count 1 takes the singular noun.
  Each other count takes the plural noun. The portal has no other language.
- Issue #3449 holds the same defect on the organization page and on the
  capture history page. This change does not repair those pages.

## Out of Scope

- The organization filter note and the capture history note (#3449).
- A shared plural helper for all templates.
