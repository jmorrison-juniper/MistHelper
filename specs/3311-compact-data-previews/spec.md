# Feature Specification: Compact data previews

**Feature Branch**: `jmorrison-juniper-compact-data-previews`

**Created**: 2026-10-01

**Status**: Local repair verified. Publication waits for the parent grant.

**Input**: [Issue #3311](https://github.com/jmorrison-juniper/MistHelper/issues/3311)

## User Scenarios & Testing

### User Story 1 - Read a wide preview (Priority: P1)

The operator opens a CSV preview with 43 columns and 112 records.
Long cell values must not hide the next record beneath a tall row.

**Why this priority**: Tall rows prevent the operator from comparing records.

**Independent Test**: Open the actual modal at four viewport widths.
Measure every rendered data row and header row.

**Acceptance Scenarios**:

1. **Given** a wide CSV file, **when** the operator opens its preview, **then** every row is at most 60 pixels tall.
2. **Given** 112 records, **when** page 1 opens, **then** the modal shows 50 records and reports three pages.
3. **Given** a table wider than the modal, **when** the operator scrolls horizontally, **then** headers remain aligned with cells.

### User Story 2 - Read a full value (Priority: P1)

The operator reads the full value of a shortened cell without changing the table height.
The control supports a pointer, a keyboard, and touch.

**Why this priority**: A short display must not remove information.

**Independent Test**: Open the full value with Enter, Space, and touch.
Compare the displayed text with the exact response value.

**Acceptance Scenarios**:

1. **Given** a shortened cell, **when** the pointer stops on it, **then** its title contains the full value.
2. **Given** a focused cell control, **when** the operator presses Enter or Space, **then** a dialog shows the full value.
3. **Given** the full-value dialog, **when** the operator presses Escape, **then** only that dialog closes.
4. **Given** the closed dialog, **then** focus returns to the cell control.
5. **Given** quotes, markup, Unicode, or newlines, **then** the dialog shows text without executing markup.

### User Story 3 - Keep existing behavior (Priority: P2)

The operator uses the existing page controls, sort controls, search, and export.
The repair changes presentation only.

**Why this priority**: Operators must continue to receive the same records and file values.

**Independent Test**: Traverse all three pages, sort both directions, search, and export.
Run the existing data browser and results table tests.

**Acceptance Scenarios**:

1. **Given** page 1, **when** the operator selects Next twice, **then** pages 2 and 3 show 50 and 12 records.
2. **Given** a sort request, **then** the request and response retain the existing sort parameters.
3. **Given** an export, **then** every exported cell retains its full value.
4. **Given** the results table, **then** its dimensions and theme rules remain unchanged.

### Edge Cases

- Empty cells and null values retain the existing empty display.
- Numeric values retain their existing text conversion.
- Long values remain readable without horizontal scrolling inside the full-value dialog.
- A closed or replaced preview does not retain an open full-value dialog.
- An unreadable measurement or an empty row set fails the row-height guard.

## Requirements

### Functional Requirements

- **FR-001**: Scope compact cell rules to `#modalPreviewTable`.
- **FR-002**: Reuse the existing compact rules for `#resultsTable` without changing their values.
- **FR-003**: Keep the full value in cell text and the title through DOM properties.
- **FR-004**: Provide a labeled full-value dialog with keyboard and touch controls.
- **FR-005**: Keep untrusted values out of HTML and attribute string concatenation.
- **FR-006**: Preserve pagination, sorting, search, output files, and CSV export values.
- **FR-007**: Use the real modal template, renderer, and styles in browser tests.
- **FR-008**: Keep test files under temporary directories and keep the server on loopback with an assigned port.
- **FR-009**: Start no production service, database, container, Mist API call, or firmware operation.
- **FR-010**: Save a screenshot for each measured width and retain browser traces on failure.

### Key Entities

- **Preview record**: One unchanged response row with 43 cell values.
- **Cell value**: The complete response text, independent of its shortened display.
- **Measurement**: The bounds of every rendered row, header, column, and scroll area.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The unchanged renderer fails the 60-pixel row budget at 1600 by 1000 pixels.
- **SC-002**: All rows pass at widths 1024, 1280, 1440, and 1600, with a height of 1000 pixels.
- **SC-003**: Page counts remain 50, 50, and 12, with 112 total records and three pages.
- **SC-004**: Full values remain exact through pointer, keyboard, touch, and export.
- **SC-005**: All four shipped themes and the existing results table retain their behavior.
- **SC-006**: The required browser cases run without skips or unexpected console errors.

## Assumptions

The supported browsers provide the native HTML dialog element.
The full-value dialog stays inside the Bootstrap modal for focus control.
The issue requires no backend change or new dependency.
The parent must authorize remote publication with an exact verified main commit.
