# Feature Specification: The capture history with no site names every site

**Issue**: #3482
**Feature Branch**: `fix/3482-org-history-scope`
**Status**: Draft
**Found by**: a browser probe during the work on #3449

## Problem

The history page serves one site or every site. The page with no `site_id`
value lists the stored captures of every site. Its Captures card still names
one site.

| Part of the Captures card | The text on the page with no site today |
| - | - |
| The note | "The list shows the stored captures of E2E Stand-In Site. The site holds 5 captures." |
| The hidden table caption | "The stored captures of the site." |

In the browser fixtures, the 5 captures come from 2 sites. The note names the
site of the first row only. The words "The site holds" and "of the site" are
also wrong, because the page shows no single site.

An operator who reads the page can think that every capture belongs to one
site. The operator can then open a capture of the wrong site.

## User Scenarios & Testing

### User Story 1 (P1): The page with no site names every site

The operator who opens the history with no site must read a note that names
every site.

**Independent test**: Open `/history` with no `site_id` value, and read the
note of the Captures card.

**Acceptance scenarios**:

| Stored captures | Offset | Page size | The whole note |
| - | - | - | - |
| 0 | 0 | 25 | "The list shows the stored captures of every site. The portal holds 0 captures. This page starts after 0 captures, and one page holds 25 rows." |
| 1 | 0 | 25 | "The list shows the stored captures of every site. The portal holds 1 capture. This page starts after 0 captures, and one page holds 25 rows." |
| 5 | 0 | 25 | "The list shows the stored captures of every site. The portal holds 5 captures. This page starts after 0 captures, and one page holds 25 rows." |

The hidden caption of the table starts with "The stored captures of every
site".

### User Story 2 (P1): The page of one site keeps the site name

The operator who opens the history of one site must still read the name of
that site.

**Independent test**: Open the history of a site that holds one capture, and
read the note.

**Acceptance scenarios**:

| The site | The name on the rows | The first two sentences of the note |
| - | - | - |
| A site that holds 1 capture | E2E Stored Poll Site | "The list shows the stored captures of E2E Stored Poll Site. The site holds 1 capture." |
| A site that holds no capture | No name | "The list shows the stored captures. The site holds 0 captures." |

The hidden caption of the table starts with "The stored captures of the site".

### User Story 3 (P2): The operator sees the correct note in a real browser

**Acceptance scenarios**:

1. **Given** a real browser and the stored captures of two sites. **When** the
   operator opens `/history` with no site. **Then** the note names every site,
   and it names no single site. A screenshot records the page.
2. **Given** the same browser. **When** the operator opens the history of the
   site that holds one capture. **Then** the note names that site. A
   screenshot records the page.

### Edge Cases

- If the page receives no scope value, the page still renders. The note then
  uses the texts of a site with no name.
- If the page names a site, the portal reads the site name from the rows. It
  makes no cloud read.
- If the page names no site, the portal reads no site name. No row name
  reaches the note or the caption.
- A site name is text from the store. The page escapes it.
- Many journeys share the browser test server, and some journeys store a
  capture. The browser journey therefore reads the count as a number of one or
  more digits.

## Requirements

### Functional Requirements

- **FR-001**: If the request holds no `site_id` value, the note of the Captures
  card names every site. It does not name the site of a row.
- **FR-002**: If the request holds no `site_id` value, the note states the
  count after the words "The portal holds".
- **FR-003**: If the request holds a `site_id` value, the note keeps the site
  name of the rows and the words "The site holds".
- **FR-004**: The hidden caption of the Captures table names the same scope as
  the note.
- **FR-005**: The route builds the scope texts. The template holds no rule.
- **FR-006**: The page still renders when it receives no scope value.

## Success Criteria

- **SC-001**: On the page with no site, no part of the Captures card names a
  single site.
- **SC-002**: On the page of one site, the note and the caption do not change.
- **SC-003**: The change adds no cloud read, no store read, no write, no route,
  and no field of a JSON body.

## Assumptions

- The page with no site reads every capture in the store. Issue #3484 holds the
  change that narrows the list to the selected organization. This change states
  the current behavior, so the note says "every site" and "The portal holds".
  The work of #3484 can change the two texts when it narrows the list.
- The first sentence for a site with no name does not change.

## Out of Scope

- The organization scope of the lists. Issue #3484 holds it.
- The notes of the Runs card, the Multi-site upgrades card, and the Audit log
  card. Issue #3485 holds them.
- A Site column in the Captures table. Issue #3486 holds it.
- The count nouns of the note. Issue #3449 repaired them.
