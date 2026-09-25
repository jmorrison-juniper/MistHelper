# Feature Specification: The options page shows a real note under each type control

**Issue**: #3381
**Feature Branch**: `fix/3381-options-none-note`
**Status**: Draft
**Found by**: a screenshot of the #3377 journey on 2026-09-25

## Problem

The options page of a single-site run shows the text `None` under each version
control of a device type. An operator reads `None` and cannot tell whether the
portal found a fault.

`TypedVersionSelector.select` writes the key `warning` for each device type.
The value is `None` when the type has no warning. The template line
`selection.get('warning', <default>)` returns `None`, because the key exists.
Jinja then prints the word `None`, and the default text never shows.

## User Story 1 (P1): A type with no warning shows the default note

**Acceptance scenarios**:

1. **Given** a site with one switch and a shared version for the switch,
   **When** the operator opens the options page, **Then** the note under the
   switch control reads "The portal applies this version only to compatible
   switches."

2. **Given** the same page, **When** the operator reads the note under the
   access point control and the gateway control, **Then** each note names its
   own device type, and no note reads `None`.

## User Story 2 (P1): A type with a warning still shows the warning

**Acceptance scenarios**:

1. **Given** a site with one switch and no shared version for the switch,
   **When** the operator opens the options page, **Then** the note under the
   switch control reads "No common compatible version exists for the switch
   devices."

## Functional requirements

- **FR-001**: If the type selection holds no warning, or holds `None`, the note
  shows the default text for that device type.

- **FR-002**: If the type selection holds a warning text, the note shows that
  text.

- **FR-003**: The change keeps the `warning` key of `TypedVersionSelector`.
  The key is part of the selection shape that other code reads.

- **FR-004**: A contract test renders the page with the shipped selection
  shape. A browser test reads each visible note.

## Out of scope

- The multi-site options page. That page does not read the `warning` key, and
  its failure limit field falls back to a number.

## Success criteria

- **SC-001**: The new contract test fails on the old template and passes after
  the repair.

- **SC-002**: No note of a type control on the options page reads `None`.
