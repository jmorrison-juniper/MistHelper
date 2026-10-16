# Feature Specification: Single console output

**Feature Branch**: `jmorrison-juniper-menu-readability-doubling`

**Created**: 2026-10-16

**Status**: Ready

**Input**: User description: "ok so figure out how to not get it to send everything to the ssh session twice"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read each menu line once (Priority: P1)

The operator connects through SSH and reads one copy of each menu line.

**Why this priority**: Duplicate lines double the menu length and make the menu harder to read.

**Independent Test**: Display the menu with normal and detailed console logging. Count the displayed copies.

**Acceptance Scenarios**:

1. **Given** normal console logging, **When** the menu appears, **Then** each menu row appears once.
2. **Given** detailed console logging, **When** the menu appears, **Then** each menu row still appears once.

### User Story 2 - Retain operational evidence (Priority: P1)

The operator can read warnings and errors and find the menu text in the file log.

**Why this priority**: A display repair must not remove diagnostic evidence.

**Independent Test**: Display a formatted line and emit an unrelated warning. Examine the terminal and file log.

**Acceptance Scenarios**:

1. **Given** file logging at INFO, **When** a menu line appears, **Then** the file log records that line once.
2. **Given** a warning or error, **When** the message is logged, **Then** the terminal preserves that message.

### Edge Cases

- An unset console threshold must not cause duplicate output.
- Repeated startup must not accumulate handlers or filters.
- Blank lines, literal percent signs, and formatted arguments keep their current text.
- A local terminal must receive the same single-copy behavior as SSH.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Display each operator message once, regardless of the console logging threshold.
- **FR-002**: Preserve one file-log record for each operator message when the file logging threshold permits INFO.
- **FR-003**: Preserve unrelated diagnostic messages at their configured thresholds.
- **FR-004**: Preserve the menu text, numbering, selections, and exit behavior.
- **FR-005**: Do not change credentials, network devices, or the running shared container during implementation.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every displayed menu row has exactly one terminal copy.
- **SC-002**: Every tested operator line has exactly one file-log copy at INFO.
- **SC-003**: All tested unrelated warnings and errors remain visible.

## Assumptions

- The request permits a source repair, not a restart or replacement of the shared running container.
- A filter can remove the redundant console log copy without changing the direct operator output.
- A quieter console threshold alone does not satisfy detailed logging.
- Menu grouping and label rewrites are outside this repair.
