# Feature Specification: Timestamp validation

**Feature Branch**: `jmorrison-juniper-issue-4796-timestamp-validation`

**Created**: 2026-11-15

**Status**: Draft

**Input**: Issue #4796 reports acceptance of an invalid hour in a timestamp label.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reject invalid timestamps (Priority: P1)

A contributor needs an invalid timestamp label to fail before a feature record is created.

**Why this priority**: An invalid label must not receive a valid feature route.

**Independent Test**: Submit invalid dates and times and verify that each one fails without creating a record.

**Acceptance Scenarios**:

1. **Given** a label with hour `24`, **When** a contributor resolves its route, **Then** the request fails.
2. **Given** a label with an invalid date, minute, or second, **When** the route is resolved, **Then** the request fails.

### User Story 2 - Preserve valid timestamp routes (Priority: P2)

A contributor needs valid labels to retain their existing deterministic routes.

**Why this priority**: Existing feature records must remain discoverable.

**Independent Test**: Resolve valid boundary labels and compare their routes with independent expected routes.

**Acceptance Scenarios**:

1. **Given** a valid label at midnight or the last second of a day, **When** its route is resolved, **Then** the existing route format is retained.

### Edge Cases

- Reject the first invalid hour, minute, and second.
- Accept `00:00:00` and `23:59:59` for valid dates.
- Retain the existing rejection of dates before 1970 and malformed labels.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The route resolver MUST reject timestamp labels with an hour outside `00` through `23`.
- **FR-002**: The route resolver MUST reject invalid dates, minutes, seconds, and label formats.
- **FR-003**: The route resolver MUST leave the destination unchanged when validation fails.
- **FR-004**: The route resolver MUST retain the existing deterministic route for each valid timestamp.

### Key Entities

- **Timestamp label**: A UTC date and time followed by a feature name.
- **Feature route**: The deterministic destination assigned to a valid label.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All tested invalid boundary labels fail without a destination.
- **SC-002**: All tested valid boundary labels retain their independently calculated routes.
- **SC-003**: The reported `20261013-240000-bad` label fails.

## Assumptions

- Labels use UTC and a 24-hour clock.
- This change does not use Mist credentials or call the Mist API.
