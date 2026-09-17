# Feature Specification: Module logger sweep for firmware manager

**Feature Branch**: `refactor/1793-module-logger`

**Created**: 2026-09-16

**Status**: Draft

**Input**: User description: "Refactor issue #1793 in a reviewable subset."

## User Scenarios & Testing

### User Story 1 - Filter firmware manager logs by module (Priority: P1)

Operators need log records from `src/firmware/firmware_manager.py` to carry the
module name instead of the root logger name.

**Why this priority**: The firmware manager owns upgrade flow logging. A module
logger lets an operator filter that flow without unrelated root logger records.

**Independent Test**: Run a text count that checks zero eligible
`logging.<level>(...)` calls remain in `src/firmware/firmware_manager.py`.

**Acceptance Scenarios**:

1. **Given** the firmware manager file, **When** the sweep finishes, **Then**
   all 236 eligible root logger calls use `logger.<level>(...)`.
2. **Given** the firmware manager file, **When** the module loads, **Then** the
   file defines one module logger with `logging.getLogger(__name__)`.

### Edge Cases

- The sweep must not change message text, because issue #1766 owns log wording.
- The sweep must not change log levels, because issue #1766 owns level repair.
- The sweep must not change exception handlers, because issue #1794 owns them.
- The sweep must not touch string patch targets in tests.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST replace 236 eligible root logger calls in
  `src/firmware/firmware_manager.py`.
- **FR-002**: The system MUST define one module logger in
  `src/firmware/firmware_manager.py`.
- **FR-003**: The system MUST keep logging message text unchanged.
- **FR-004**: The system MUST keep logging levels unchanged.
- **FR-005**: The system MUST keep `%s` style formatting unchanged.
- **FR-006**: The system MUST keep exception handlers unchanged.
- **FR-007**: The system MUST report the remaining measured areas in follow-up
  issues.

### Key Entities

- **Module logger**: The `logger` object returned by
  `logging.getLogger(__name__)`.
- **Root logger call**: A direct call that starts with `logging.debug`,
  `logging.info`, `logging.warning`, `logging.error`, `logging.exception`,
  `logging.critical`, or `logging.log`.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The measured total before this pull request is 5793 eligible root
  logger calls across Python files.
- **SC-002**: The chosen subset changes 236 eligible calls in
  `src/firmware/firmware_manager.py`.
- **SC-003**: The measured remaining total after this pull request is 5557
  eligible root logger calls by `git grep`.
- **SC-004**: The string patch search for `src.*.logging` targets reports zero
  matches.

## Assumptions

- The current source tree can differ from the original issue count of 4478,
  because later work added or moved logging calls.
- `src/firmware/firmware_manager.py` is the first reviewable subset because it
  has 236 call sites in one coherent area.
- Follow-up work owns the remaining measured areas: #2768, #2769, #2770,
  #2771, #2772, #2773, #2774, #2775, #2776, #2777, #2778, and #2779.
