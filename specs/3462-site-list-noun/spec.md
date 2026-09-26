# Feature Specification: The multi-site texts name one site with a singular noun

**Issue**: #3462
**Feature Branch**: `fix/3462-site-list-noun`
**Status**: Draft
**Found by**: a scan of the templates and the refusal texts during the work
on #3447 and #3452

## Problem

Five texts of the multi-site upgrade flow list the names of one or more sites.
Each text puts a fixed plural noun before the list.

- The banner of a short read says "at these sites" and "devices of those
  sites".
- The save refusal of a short read says "at these sites".
- The save refusal of a site with no device says "at these sites".
- The save refusal of a site with no planned device says "at these sites".
- The start refusal of a site with no pre-check capture says "These sites
  hold".

A short read or an empty site at one site is the most frequent case of these
texts. The operator then reads a plural noun beside one site name. The
single-site mode already says "this site", so the two modes do not agree.

## User Scenarios & Testing

### User Story 1 (P1): The banner of a short read names one site

The operator must read a singular noun when the read of one site is short.

**Independent test**: Select two sites. Make the read of one site short, and
open the options page.

**Acceptance scenarios**:

1. **Given** a short read at one site. **When** the options page opens.
   **Then** the banner says "The portal did not read the complete device list
   at this site: Site A. The device table can leave out devices of that site.
   Reload this page before you save the options."
2. **Given** a short read at two sites. **When** the options page opens.
   **Then** the banner says "The portal did not read the complete device list
   at these sites: Site A, Site B. The device table can leave out devices of
   those sites. Reload this page before you save the options."

### User Story 2 (P1): The save refusals name one site

**Independent test**: Save a plan that one site cannot join, and read the
refusal.

**Acceptance scenarios**:

1. **Given** one site with no device. **When** the operator saves the options.
   **Then** the refusal says "The portal read no device at this site: Site A."
2. **Given** one site with no device of the checked types. **When** the
   operator saves the options. **Then** the refusal says "The plan holds no
   device at this site: Site A."
3. **Given** one site with a short read at the save. **When** the operator
   saves the options. **Then** the refusal says "The portal did not read the
   complete device list at this site: Site A."
4. **Given** two sites with no device. **When** the operator saves the
   options. **Then** the refusal says "The portal read no device at these
   sites: Site A, Site B."

### User Story 3 (P2): The start refusal names one site

The confirm page locks the start button while a site holds no pre-check
capture. A script receives the start refusal. A start also receives it when a
capture changes after the page opens.

**Independent test**: Save a plan of two sites. Remove the pre-check capture of
one site, and send the start.

**Acceptance scenarios**:

1. **Given** one site with no pre-check capture. **When** a start arrives.
   **Then** the refusal ends with "The portal found no pre-check capture for
   this site: Site A."
2. **Given** two sites with no pre-check capture. **When** a start arrives.
   **Then** the refusal ends with "The portal found no pre-check capture for
   these sites: Site A, Site B."

### User Story 4 (P2): The operator sees the correct noun in a real browser

**Acceptance scenarios**:

1. **Given** a real browser and a short read at one site. **When** the
   options page opens. **Then** the banner shows the text of User Story 1. A
   screenshot records the page.
2. **Given** a real browser. **When** the save of a short site or an empty
   site stops. **Then** the page shows the refusal of User Story 2. A
   screenshot records the page.

### Edge Cases

- A refusal names 10 sites at most, and then "and N more". That list always
  names 11 or more sites, so the refusal keeps the plural noun.
- The first sentence of the start refusal does not change. The words "each
  selected site" are correct for each count.
- The error codes, the status codes, and the order of the refusals do not
  change.
- A site with no name shows its identifier. The noun rule counts that site
  too.

## Requirements

### Functional Requirements

- **FR-001**: For one short site, the banner says "at this site:" before the
  name, and "devices of that site" after the name.
- **FR-002**: For two or more short sites, the banner says "at these sites:"
  before the names, and "devices of those sites" after the names.
- **FR-003**: For one site, each of the three save refusals says "at this
  site:" before the name. For two or more sites, each says "at these sites:"
  before the names.
- **FR-004**: The start refusal says "The portal found no pre-check capture
  for this site:" before one name. It says "The portal found no pre-check
  capture for these sites:" before two or more names.
- **FR-005**: A refusal that names more than 10 sites keeps the plural noun
  and the text "and N more".
- **FR-006**: The count of the sites decides the noun. One site takes the
  singular noun. Each other count takes the plural noun.

## Success Criteria

- **SC-001**: For one, two, and twelve sites, each of the five texts reads as
  correct English.
- **SC-002**: The change adds no cloud read, no write, and no route change.

## Assumptions

- The texts use the English plural rule of #3447 and #3452.
- The texts do not state the count. The list of names shows the count.

## Out of Scope

- The single-site mode. Its texts already say "this site".
- The note of the options page. Issue #3447 repaired that note.
- The confirm page. Issue #3452 repaired that page.
- The organization page and the capture history page. Issue #3449 covers
  them.
