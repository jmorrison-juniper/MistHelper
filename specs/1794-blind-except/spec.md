# Feature Specification: Blind Exception Handler Cleanup Slice

**Feature Branch**: `refactor/1794-blind-except`

**Created**: 2026-09-16

**Status**: Draft

**Input**: Issue #1794 asks for a bounded repair of blind `except Exception` handlers.

## User Scenarios & Testing

### User Story 1 - Surface firmware programming errors (Priority: P1)

A maintainer must see a malformed Mist SDK call instead of an empty firmware map.

**Why this priority**: Firmware version evidence protects production upgrade decisions.

**Independent Test**: Run `python -m pytest tests\unit\firmware\test_running_version.py -q`.

**Acceptance Scenarios**:

1. **Given** the site stats callable raises `TypeError`, **When** the resolver reads the site, **Then** the error raises.
2. **Given** the site stats callable raises `RuntimeError`, **When** the resolver reads the site, **Then** the caller gets an empty map and an error log.

## Edge Cases

- If Mist rate limits the stats call, the resolver keeps the fallback path with an error log.
- If the SDK call is malformed, the resolver raises so the defect cannot hide.

## Requirements

### Functional Requirements

- **FR-001**: The slice MUST measure current `except Exception` handlers before edits.
- **FR-002**: The slice MUST prioritize firmware, credential, device-write, SDK, and persistence paths.
- **FR-003**: The chosen handler MUST catch only operational failures that it can answer.
- **FR-004**: Programming errors such as `TypeError` MUST propagate.
- **FR-005**: Tests MUST prove that the caller learns about each changed failure path.
- **FR-006**: The pull request MUST state the deferred areas and their issue numbers.

### Key Entities

- **Running firmware version map**: The device id or MAC address map read from `listSiteDevicesStats`.
- **Operational failure**: A runtime fault that the resolver can answer with an empty map and an error log.
- **Programming error**: A malformed call or missing attribute that must raise.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The selected source file has one fewer `except Exception` handler.
- **SC-002**: The targeted unit test proves the runtime failure path and the programming error path.
- **SC-003**: The follow-up issues record all 812 remaining handlers by deferred area.

## Assumptions

- The Mist SDK reports transport limit faults for this path with `RuntimeError`.
- Mist SDK response status handling remains in the existing response parser.
- Issue #1794 stays open because this slice does not repair every handler.
