# Feature Specification: Terminal Preference Readiness

**Feature Branch**: `fix-3759-terminal-readiness`

**Created**: 2026-10-03

**Status**: Approved for bounded local repair

**Input**: Issue #3759 reports a browser test that reads the terminal preference before initialization.

## User Scenarios & Testing

### User Story 1 - Verify the default terminal preference (Priority: P1)

This test checks the default for copy by selection.
It must wait for the terminal to apply its preference before it reads the control.

**Why this priority**: The current test can read the template's unchecked state before terminal initialization completes.

**Independent Test**: Run the J9 browser test with the native Playwright page and terminal harness.

**Acceptance Scenarios**:

1. **Given** a terminal opens, **When** its preference control initializes, **Then** J9 reads the checked default and keeps its existing assertion.
2. **Given** J9 passes its readiness check, **When** it records evidence, **Then** it creates the existing screenshot.

### User Story 2 - Prove the readiness condition (Priority: P2)

A controlled page checks the wait that J9 uses.

**Why this priority**: A delayed state proves that J9 waits before it reads the control.

**Independent Test**: Run the readiness tests with the native Playwright `page` fixture.

**Acceptance Scenarios**:

1. **Given** an unchecked control becomes checked after a scheduled browser event, **When** the assertion waits, **Then** it passes after the state changes.
2. **Given** a control stays unchecked, **When** the assertion reaches its supplied timeout, **Then** it fails within that bound.

## Edge Cases

- The checkbox exists in the page before preference initialization completes.
- Preference initialization does not complete before the supplied timeout.
- The readiness tests must use browser events and native Playwright assertions, not sleeps or patched wait tools.

## Requirements

### Functional Requirements

- **FR-001**: J9 MUST wait for the copy-by-selection control to become checked before taking its state snapshot.
- **FR-002**: J9 MUST keep the `checked is True` assertion, screenshot call, screenshot name, test ID, existing timeout, page fixture, and terminal harness.
- **FR-003**: A deterministic test MUST show that the J9 wait accepts a delayed checked state.
- **FR-004**: A deterministic test MUST show that the wait fails when initialization does not occur within its explicit timeout.
- **FR-005**: The repair MUST leave runtime files, templates, shared helpers, fixtures, dependencies, policies, baselines, exclusions, and other test cases unchanged.

## Success Criteria

### Measurable Outcomes

- **SC-001**: J9 passes with its original default-checked assertion and screenshot requirement.
- **SC-002**: The delayed-initialization control passes through native Playwright waiting.
- **SC-003**: The control fails before its timeout ends when initialization is unavailable.
- **SC-004**: The original 65 browser memberships and the new control memberships have separate recorded results.

## Assumptions

- The runtime default remains `copyOnSelect: true`.
- The source order supports the report that J9 reads the control too early.
- This repair changes no runtime behavior and needs no release fragment.
- Keep this repair local until the coordinating parent accepts the evidence and grants further delivery.
