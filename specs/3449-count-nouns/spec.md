# Feature Specification: The picker note and the history note make the noun agree with the count

**Issue**: #3449
**Feature Branch**: `fix/3449-count-nouns`
**Status**: Draft
**Found by**: a scan of the templates during the work on #3447

## Problem

Two page notes of the upgrade portal print a count beside a fixed plural noun.

| Page | The text for a count of 1 today |
| - | - |
| The organization picker | "The filter matches 1 organizations." |
| The capture history of one site | "The site holds 1 captures." |

The second sentence of each note has two more faults.

- It says "This page starts after N of them". The word "them" cannot refer to
  one organization or to one capture.
- It says "one page holds N rows". The history page can hold 1 row, and the
  note then says "1 rows".

A search for one organization by its full name is a frequent step. The first
page that the operator reads after the search shows the wrong text. An account
that reaches one organization shows the same text on each visit.

## User Scenarios & Testing

### User Story 1 (P1): The picker note agrees with the count

The operator must read a noun that agrees with each count of the picker note.

**Independent test**: Type the full name of one organization in the search
field, press "Search every page", and read the note.

**Acceptance scenarios**:

| Matches | Offset | The note after the fixed first sentence |
| - | - | - |
| 0 | 0 | "The filter matches 0 organizations. This page starts after 0 organizations, and one page holds 25 rows." |
| 1 | 0 | "The filter matches 1 organization. This page starts after 0 organizations, and one page holds 25 rows." |
| 2 | 0 | "The filter matches 2 organizations. This page starts after 0 organizations, and one page holds 25 rows." |
| 2 | 1 | "The filter matches 2 organizations. This page starts after 1 organization, and one page holds 25 rows." |

### User Story 2 (P1): The history note agrees with the count

The operator must read a noun that agrees with each count of the history note.

**Independent test**: Open the history of a site that holds one stored capture,
and read the note.

**Acceptance scenarios**:

| Captures | Offset | Page size | The note after the fixed first sentence |
| - | - | - | - |
| 0 | 0 | 25 | "The site holds 0 captures. This page starts after 0 captures, and one page holds 25 rows." |
| 1 | 0 | 25 | "The site holds 1 capture. This page starts after 0 captures, and one page holds 25 rows." |
| 2 | 0 | 25 | "The site holds 2 captures. This page starts after 0 captures, and one page holds 25 rows." |
| 2 | 1 | 1 | "The site holds 2 captures. This page starts after 1 capture, and one page holds 1 row." |

### User Story 3 (P2): The operator sees the correct note in a real browser

**Acceptance scenarios**:

1. **Given** a real browser and an account that reaches one organization.
   **When** the operator searches for that organization by its full name.
   **Then** the note says "The filter matches 1 organization." A screenshot
   records the page.
2. **Given** a real browser and a site that holds one stored capture. **When**
   the operator opens the history of that site. **Then** the note says "The
   site holds 1 capture." A screenshot records the page.
3. **Given** the same site. **When** the operator opens the history with a page
   size of 1. **Then** the note says "one page holds 1 row." A screenshot
   records the page.

### Edge Cases

- If the history page receives no view, the page still renders. The note then
  says "0 captures" and "0 rows".
- If the picker page receives no view, the note shows no count sentence. This
  behavior does not change.
- An offset past the end of the matches reads as the count of the matches. The
  note states the value that the page uses.
- The history page size can be any value from 1 to 200. The offset can be any
  value from 0 to 1,000,000.
- The picker page size is fixed at 25. The rule still covers a count of 1.
- A count of zero takes the plural noun.

## Requirements

### Functional Requirements

- **FR-001**: The picker note states the count of the matches with the noun
  "organization" for a count of 1. It uses "organizations" for each other
  count.
- **FR-002**: The picker note states the offset with the same noun rule. The
  words "of them" do not appear.
- **FR-003**: The history note states the count of the stored captures with the
  noun "capture" for a count of 1. It uses "captures" for each other count.
- **FR-004**: The history note states the offset with the same noun rule. The
  words "of them" do not appear.
- **FR-005**: Each note states the page size with the noun "row" for a size of
  1. It uses "rows" for each other size.
- **FR-006**: Each note has a stable test identifier. The picker note uses
  `org-search-note`, and the history note uses `history-count-note`.
- **FR-007**: The history page still renders when it receives no view.

## Success Criteria

- **SC-001**: For the counts 0, 1, and 2, each count of each note reads as
  correct English.
- **SC-002**: The change adds no cloud read, no write, no route, and no field
  of a JSON body.

## Assumptions

- The notes use the English rule of #3447, #3453, and #3462. Only a count of
  one takes the singular noun.
- The notes keep each number as digits.

## Out of Scope

- The texts of the bulk action dialog. Issue #3472 holds them.
- The options page. Issue #3447 repaired it.
- The multi-site refusals and the banner. Issue #3462 repaired them.
- The first sentence of each note. This change does not change it.
- The scope words of the organization-wide history. The page with no site
  names the site of the first row, and it says "The site holds". Issue #3482
  holds that defect.
