# Feature Specification: The portal pages use American spelling

**Issue**: #3384
**Feature Branch**: `fix/3384-american-spelling`
**Status**: Draft
**Found by**: a screenshot of the #3381 work on 2026-09-25

## Problem

The upgrade portal shows the British spelling "neighbour" in four places that
an operator reads. The STE guide at `documentation/ASD-STE100_writing-guide.md`
requires American spelling in every text that the project ships. One Jinja
comment holds the same spelling.

## User Story 1 (P1): The operator reads American spelling

**Acceptance scenarios**:

1. **Given** a single-site plan with an access point, **When** the operator
   opens the options page, **Then** the peer-to-peer legend and its yes choice
   read "neighbor".

2. **Given** a plan with the radio batch strategy, **When** the operator reads
   the hint of the node order control, **Then** the hint reads "neighborhood".

3. **Given** a saved plan, **When** the operator opens the confirm page,
   **Then** the peer-to-peer row name reads "neighbor".

## User Story 2 (P2): A test stops a new British spelling

**Acceptance scenarios**:

1. **Given** a template or the portal script with a British spelling from the
   guard list, **When** the contract suite runs, **Then** the guard test fails
   and names each file, line, and word.

2. **Given** a standard name such as `aria-labelledby`, or the state word
   `cancelled`, **When** the guard reads it, **Then** the guard does not flag
   it.

## Functional requirements

- **FR-001**: The four visible texts and the one Jinja comment use "neighbor"
  or "neighborhood".

- **FR-002**: A contract test reads every template of the portal and the
  portal script. It fails if a British spelling from the guard list occurs.

- **FR-003**: The guard test states the count of files that it read. It fails
  if it reads no file.

- **FR-004**: The guard never flags an identifier that a standard or the state
  model fixes. These identifiers are `aria-labelledby` and `cancelled`.

## Out of scope

- The word "catalogue" in `src/upgrade_portal/upgrade/events.py`. It names the
  class `EventCatalogue`, and STE never changes an identifier.

- The past result in `specs/1823-upgrade-capture-portal/quickstart-results.md`.

- The vendor files under `static/vendor/`.

## Success criteria

- **SC-001**: The guard test fails on the old templates, and it names the five
  lines of the issue.

- **SC-002**: The guard test passes after the repair.
