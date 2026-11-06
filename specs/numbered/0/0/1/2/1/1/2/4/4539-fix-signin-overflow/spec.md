# Feature Specification: Sign-In Narrow Viewport Layout

**Feature Branch**: `4539-fix-signin-overflow`

**Created**: 2026-11-06

**Status**: Draft

**Input**: Issue #4539: Keep the upgrade portal sign-in page within a 390-pixel viewport.

## User Scenarios & Testing

### User Story 1 - Sign in on a narrow screen (Priority: P1)

An operator opens the upgrade portal sign-in page on a narrow screen and can read and use the whole page without sideways scrolling.

**Why this priority**: Operators need access to the sign-in form on narrow screens.

**Independent Test**: Open the sign-in page at 390 by 844 pixels and compare the document width with the viewport width.

**Acceptance Scenarios**:

1. **Given** a 390-pixel viewport, **When** an operator opens the sign-in page, **Then** the page has no horizontal document scroll.
2. **Given** a 390-pixel viewport, **When** an operator reads the form, **Then** each sign-in field and the submit control remain visible and usable.
3. **Given** a wider viewport, **When** an operator opens the sign-in page, **Then** the existing sign-in flow remains unchanged.

### Edge Cases

- Long help text must wrap within the page at 390 pixels.
- A narrow viewport must not hide a sign-in field or its label.
- The page must retain its normal layout when the viewport is wider.

## Requirements

### Functional Requirements

- **FR-001**: The sign-in page MUST fit within a 390-pixel viewport without horizontal document scrolling.
- **FR-002**: The sign-in page MUST keep each field, its label, and the submit control visible and usable at 390 pixels.
- **FR-003**: The sign-in page MUST preserve its current sign-in behavior at wider viewports.

## Success Criteria

### Measurable Outcomes

- **SC-001**: At 390 by 844 pixels, the document width is no greater than the viewport width.
- **SC-002**: At 390 pixels, an operator can reach every sign-in field and the submit control without horizontal scrolling.
- **SC-003**: At wider tested viewports, the sign-in page continues to pass its existing layout checks.

## Assumptions

- The change affects page layout only and does not change sign-in behavior.
- The local browser test uses a test portal and does not contact the Mist cloud.
