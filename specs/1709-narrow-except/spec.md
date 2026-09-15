# Feature Specification: Narrow broad exception handlers

**Feature Branch**: `chore/1709-narrow-except`
**Created**: 2026-09-14
**Status**: Ready for review
**Input**: GitHub issue #1709, `1709-except-plan.md`

## User Scenarios and Tests

### User Story 1 - Preserve tracebacks for fail-open paths (Priority: P1)

A maintainer can diagnose a startup, menu, or test harness fault after the
program keeps the controlled fallback behavior.

**Why this priority**: Silent fail-open paths hide defects. A traceback gives
the maintainer enough context to repair the defect.

**Independent Test**: Force each repaired fallback seam to raise a known
exception. Verify that the old fallback value remains.

**Acceptance Scenarios**:

1. **Given** a missing package, **When** the package version reader fails,
   **Then** it returns the empty string and logs the traceback.
2. **Given** a telemetry file error, **When** runtime options initialize,
   **Then** telemetry is disabled and the program keeps starting.

### User Story 2 - Let stop signals pass through (Priority: P2)

An operator can stop MistHelper even when the stop occurs inside a broad safety
net.

**Why this priority**: A broad handler must not convert a stop request into a
normal fallback.

**Independent Test**: Raise `KeyboardInterrupt` or `SystemExit` from a broad
safety net and verify that it escapes.

**Acceptance Scenarios**:

1. **Given** the dependency upgrade check receives `KeyboardInterrupt`,
   **When** the check runs, **Then** the interrupt escapes.
2. **Given** the TUI raises `SystemExit`, **When** the event loop wrapper runs,
   **Then** the exit escapes.

### User Story 3 - Narrow known exception surfaces (Priority: P3)

A contributor can see which failures the code expects. Unexpected defects escape
instead of becoming false success values.

**Why this priority**: Narrow handlers make the code easier to read and prevent
new defects from hiding behind old fallbacks.

**Independent Test**: For each narrowed seam, prove that a known exception is
caught and an unexpected exception escapes.

**Acceptance Scenarios**:

1. **Given** a requirements file read error, **When** the parser runs,
   **Then** it returns an empty list.
2. **Given** an unexpected parser defect, **When** the parser runs,
   **Then** the defect escapes.

### Edge Cases

- If the package upgrade check fails because the network is offline, startup
  continues. The handler logs a warning with a traceback.
- If logging is not fully configured during tuning file path setup, the handler
  still records the traceback through the root logger.
- If a broad safety net remains, its `except Exception` line states the reason.

## Requirements

### Functional Requirements

- **FR-001**: The code MUST add traceback logging to the seven handlers that
  logged nothing.
- **FR-002**: The code MUST let `KeyboardInterrupt` and `SystemExit` escape from
  each remaining broad safety net.
- **FR-003**: The code MUST narrow each group 1 handler to exception types that
  the protected action can raise.
- **FR-004**: The code MUST keep the package upgrade check fail-open. It MUST
  return `True` when a normal upgrade check failure occurs.
- **FR-005**: The code MUST keep zero suppression comments in `MistHelper.py`.
- **FR-006**: The code MUST add one release-note fragment under `changelog.d/`.

### Key Entities

- **Exception handler**: A `try` block and its `except` arm in `MistHelper.py`.
- **Safety net**: A broad handler that protects startup, the test harness, the
  TUI, or the interactive operator flow.
- **Narrow handler**: A handler that catches only the expected exception classes.

## Success Criteria

### Measurable Outcomes

- **SC-001**: `MistHelper.py` has eight remaining `except Exception` handlers.
- **SC-002**: Each remaining broad handler has a same-line reason comment.
- **SC-003**: Seven handlers that logged nothing before now log a traceback.
- **SC-004**: `tools.symbol_diff` reports `no module-level name changed`.
- **SC-005**: The targeted issue tests pass in less than five seconds.

## Assumptions

- The analyst table in `1709-except-plan.md` is the task source for block
  classification.
- This change does not edit files under `src\refactors\` or `src\config\`.
- This change does not alter production hardware or production configuration.
