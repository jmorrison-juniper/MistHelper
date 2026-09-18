# Feature Specification: Blind Exception Handler Cleanup Slice 2

**Feature Branch**: `refactor/1794-blind-except-slice2`

**Created**: 2026-09-16

**Status**: Draft

**Input**: Continue issue #1794 after pull request #2837 merged.

## User Scenarios & Testing

### User Story 1 - Surface firmware and device programming errors (Priority: P1)

A maintainer must see malformed SDK calls on upgrade and reboot paths.

**Why this priority**: These paths can affect production devices.

**Independent Test**: Run the six targeted unit test files named in `plan.md`.

**Acceptance Scenarios**:

1. **Given** a touched SDK call raises `RuntimeError`, **When** the caller runs, **Then** the existing failure result remains visible.
2. **Given** a touched SDK call raises `TypeError`, **When** the caller runs, **Then** the programming error raises.

## Edge Cases

- A user site-selection parse error still returns an invalid-selection result.
- A service-ping runtime failure still returns `None` with the existing message.
- A derived WLAN runtime failure still falls back to the site-local endpoint.

## Requirements

### Functional Requirements

- **FR-001**: The slice MUST repair 15 to 20 handlers in tier 1 and tier 2 areas.
- **FR-002**: Runtime failures MUST keep the existing failure result shape.
- **FR-003**: Programming errors MUST propagate to the caller.
- **FR-004**: Tests MUST prove that each touched handler exposes the failure.
- **FR-005**: The change MUST not alter issue #1766 log levels or message wording.
- **FR-006**: The change MUST not convert root-logger calls that issue #1793 owns.

### Key Entities

- **Runtime failure**: An operational SDK or workflow failure that returns an explicit failure result.
- **Programming error**: A malformed call, attribute defect, or state defect that must raise.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The `src` blind handler count decreases from 812 to 795.
- **SC-002**: The targeted unit shard passes.
- **SC-003**: The pull request lists each repair shape.

## Assumptions

- Mist SDK transport and rate failures can be represented by `RuntimeError` in existing tests.
- Existing response-status branches continue to handle HTTP errors.
