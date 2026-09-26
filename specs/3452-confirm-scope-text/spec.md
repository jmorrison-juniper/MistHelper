# Feature Specification: The multi-site confirm page names one site for a plan of one site

**Issue**: #3452
**Feature Branch**: `fix/3452-confirm-scope-text`
**Status**: Draft
**Found by**: the journey harness of #3200 during the work on #3447

## Problem

The multi-site confirm page states the scope of the upgrade in three places.
Each place uses a fixed plural form.

- The Warning says "the upgrade can interrupt network service at all selected
  sites".
- The button of a full pre-check says "Take new pre-checks for all sites".
- The button of the missing pre-checks says "Take the missing pre-checks".

A plan of one site then reads as a plan of many sites. The operator reads the
Warning just before the typed confirmation. A Warning that names the wrong
scope makes the operator doubt the plan.

The single-site confirm page does not use these texts, so the single-site
mode does not change.

## User Scenarios & Testing

### User Story 1 (P1): A plan of one site names one site

The operator must read a scope of one site for a plan of one site.

**Independent test**: Save a multi-site plan of one site, and open the confirm
page.

**Acceptance scenarios**:

1. **Given** a saved plan of one site. **When** the confirm page opens.
   **Then** the Warning says "the upgrade can interrupt network service at the
   selected site".
2. **Given** the same plan. **When** the confirm page opens. **Then** the
   button of a full pre-check says "Take a new pre-check for the site".
3. **Given** the same plan. **When** the confirm page opens. **Then** the
   button of the missing pre-checks says "Take the missing pre-check".

### User Story 2 (P1): A plan of two or more sites keeps a plural scope

**Independent test**: Save a multi-site plan of two sites, and open the confirm
page.

**Acceptance scenarios**:

1. **Given** a saved plan of two sites. **When** the confirm page opens.
   **Then** the Warning says "the upgrade can interrupt network service at
   each selected site".
2. **Given** the same plan. **When** the confirm page opens. **Then** the
   button of a full pre-check says "Take a new pre-check for each site".
3. **Given** the same plan. **When** the confirm page opens. **Then** the
   button of the missing pre-checks says "Take the missing pre-checks".

### User Story 3 (P2): The operator sees the correct scope in a real browser

**Acceptance scenarios**:

1. **Given** a real browser. **When** the operator saves a plan of one site.
   **Then** the confirm page shows the texts of User Story 1. A screenshot
   records the page.
2. **Given** a real browser. **When** the operator saves a plan of two sites.
   **Then** the confirm page shows the texts of User Story 2. A screenshot
   records the page.

### Edge Cases

- A retry can keep one site of an earlier plan. The confirm page of that
  retry names one site.
- The second sentence of the Warning does not change. It says "Cancellation
  does not restore upgraded devices".
- The buttons keep their test identifiers and their scope values. The page
  script therefore takes the same captures as before.

## Requirements

### Functional Requirements

- **FR-001**: For a plan of one site, the Warning says "Warning: the upgrade
  can interrupt network service at the selected site. Cancellation does not
  restore upgraded devices."
- **FR-002**: For a plan of two or more sites, the Warning says "Warning: the
  upgrade can interrupt network service at each selected site. Cancellation
  does not restore upgraded devices."
- **FR-003**: The button of a full pre-check says "Take a new pre-check for
  the site" for one site. For two or more sites, it says "Take a new pre-check
  for each site".
- **FR-004**: The button of the missing pre-checks says "Take the missing
  pre-check" for one site. For two or more sites, it says "Take the missing
  pre-checks".
- **FR-005**: The Warning gets the test identifier `org-upgrade-scope-warning`.
  The test identifiers and the scope values of the buttons do not change.
- **FR-006**: The count of the sites comes from the saved plan. This count is
  the same count that the line "Sites" shows.

## Success Criteria

- **SC-001**: For one, two, and three sites, each of the three texts reads as
  correct English.
- **SC-002**: The change adds no cloud read, no write, and no route change.

## Assumptions

- The page uses the English plural rule. One site takes the singular form.
  Each other count takes the plural form.
- The texts do not repeat the count. The line "Sites" above the Warning
  already states the count.

## Out of Scope

- The single-site confirm page.
- The note of the options page. Issue #3447 repaired that note.
- The organization page and the capture history page. Issue #3449 covers them.