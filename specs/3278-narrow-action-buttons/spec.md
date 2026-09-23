# Feature Specification: Keep each action label on one line on a narrow screen

**Issue**: #3278
**Feature Branch**: `fix/3278-narrow-action-buttons`
**Status**: Implemented
**Found by**: the cross-cut journey of #3200, at a screen size of 390 by 844 pixels

## Problem

The shared cell rule `.portal-table td` of `portal.css` sets
`word-break: break-word`. A control in a cell inherits that rule. At a width of
390 pixels, the table made the action column narrower than the label. The
Choose label of the organization table painted 3 lines, and the Open label of
the site table painted 2 lines.

## User Story (P3): An operator on a phone reads and presses each action control

**Acceptance scenarios**:

1. **Given** a screen of 390 by 844 pixels, **When** the operator opens
   `/select/org`, **Then** each Choose label paints one line.
2. **Given** the single-site mode on the same screen, **When** the operator
   opens `/select/site`, **Then** each Open label paints one line.
3. **Given** the multi-site mode on the same screen, **When** the operator
   opens `/select/site`, **Then** each Select label paints one line.
4. **Given** any of the three pages, **When** a row is wider than the screen,
   **Then** the scroll box of the table scrolls sideways, and the page does not.

## Requirements

- **FR-001**: A table cell that holds one control MUST NOT wrap.
- **FR-002**: The organization table and the site table MUST mark the action
  cell with the class `cell-control`, in both the single-site mode and the
  multi-site mode.
- **FR-003**: The history table MUST keep its own rules of issue #2106. Its
  guard test forbids a `.cell-action` rule outside `.history-table`, so the
  new class uses a different name.

## Non-goals

- A global `nowrap` rule on `.portal-button`. A long button outside a table,
  such as "Show the earlier organizations", then pushes the page past a
  390 pixel screen.
- The background color of a row header cell. That is a separate issue.
