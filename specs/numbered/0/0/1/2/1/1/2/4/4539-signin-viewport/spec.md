# Feature Specification: Sign-in viewport fit

**Feature Branch**: `jmorrison-juniper-upgrade-portal-sign-in-overflow`

**Created**: 2026-10-31

**Status**: Specified

**Input**: Fix #4539 only. Preserve the existing journey viewport coverage and the scoped test-file handoff.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read the complete sign-in page (Priority: P1)

An operator opens the sign-in page on a phone and reads every control without horizontal document scroll.

**Why this priority**: Horizontal scroll hides part of the sign-in page at the reported phone size.

**Independent Test**: Open the sign-in page at 390x844 and compare the document width with the viewport width.

**Acceptance Scenarios**:

1. **Given** a 390x844 viewport, **When** the operator opens sign-in, **Then** the document width does not exceed 390 pixels.
2. **Given** a 1024x768 viewport, **When** the operator opens sign-in, **Then** all existing controls remain visible without horizontal document scroll.

### Edge Cases

- The signed-out sign-in page must fit as well as a sign-in page opened from an authenticated browser.
- Existing organization, site, history, and comparison viewport checks must remain active.
- Content must remain accessible rather than disappear behind a horizontal overflow clip.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The sign-in page MUST fit a 390x844 viewport without horizontal document scroll.
- **FR-002**: The sign-in controls MUST remain visible and usable at the existing phone and tablet sizes.
- **FR-003**: The regression MUST retain every existing viewport and page in `history_comparison_errors_and_viewports`.
- **FR-004**: The change MUST NOT alter authentication, production systems, or the workflow, fixtures, and parity records owned by #4541.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The sign-in document width is at most 390 pixels at 390x844.
- **SC-002**: Both existing viewport sizes pass the complete reported journey.
- **SC-003**: No existing viewport page check is removed or skipped.

## Assumptions

- The existing local browser fixtures provide sufficient test data without production credentials.
- This repair changes layout only and introduces no new interactive control.
- The scoped handoff permits changes only to the released cross-cutting test file among #4541 files.
