# Feature Specification: Confirmation dialog keyboard focus

**Feature Branch**: `fix/4737-confirmation-keyboard-focus`

**Created**: 2026-11-19

**Status**: Draft

**Input**: Fix issue #4737. The confirmation dialog does not focus the keyword field when it opens.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Type the keyword at once (Priority: P1)

The operator opens a confirmation dialog that requires a keyword. The operator types the keyword without a mouse click or a Tab key press.

**Why this priority**: A destructive action needs the typed keyword. The keyword field must have focus when the dialog opens.

**Independent Test**: Render the dialog with a keyword and mock callbacks. Wait for two animation frames. Check the focused element.

**Acceptance Scenarios**:

1. **Given** a keyword dialog is the first dialog of a module instance, **When** two animation frames pass, **Then** the keyword field has focus.
2. **Given** an open dialog gains a keyword requirement, **When** the field appears, **Then** the field has focus.
3. **Given** the keyword field has focus, **When** the operator enters the exact keyword, **Then** the Confirm button unlocks and no action starts.

### User Story 2 - Keep the exact keyword gate (Priority: P1)

The operator must enter the exact keyword before the Confirm button unlocks.

**Why this priority**: The gate stops an accidental destructive action.

**Independent Test**: Enter a value with a leading space, a trailing space, a different case, or a near miss.

**Acceptance Scenarios**:

1. **Given** the value has a leading or trailing space, **When** the operator clicks Confirm, **Then** the button stays locked and no action starts.
2. **Given** the field is empty, **When** the dialog opens, **Then** the Confirm button stays locked.

### User Story 3 - Keep focus for a dialog without a keyword (Priority: P2)

The operator opens a dialog that needs no keyword.

**Why this priority**: Existing confirmations must keep their behavior.

**Independent Test**: Render the dialog with no keyword and check the focused element.

**Acceptance Scenarios**:

1. **Given** no keyword is required, **When** the dialog opens, **Then** focus stays in the dialog and no keyword field appears.

### Edge Cases

- The first dialog of a module instance renders its children after an extra pass. The keyword field does not exist when the mount-time effect runs.
- A later dialog renders its children at once. The mount-time effect focuses the field.
- A keyword field added to an open dialog receives focus from the effect.
- Cancel keeps its existing behavior and calls only the cancel callback.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: When a keyword dialog opens, the keyword field receives focus after the focus trap settles.
- **FR-002**: When an open dialog gains a keyword requirement, the keyword field receives focus.
- **FR-003**: The Confirm button unlocks only when the field value equals the keyword exactly.
- **FR-004**: A dialog without a keyword keeps focus in the dialog.
- **FR-005**: The change adds no action, request, or device change. Tests use mock callbacks only.

### Key Entities

- **Confirmation dialog**: The `ConfirmationDialog` component in `ops-portal/`. Its props do not change.
- **Keyword field**: The input with id `confirm-keyword`. It exists only when a keyword is required.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The cold-start test fails when `initialFocus` is removed, and passes with it.
- **SC-002**: The full ops-portal Vitest suite passes.
- **SC-003**: Browser validation of the issue steps is open. It must pass before the pull request is marked ready.

## Assumptions

- The jsdom test reproduces the reported focus result for the first dialog of a module instance.
- The browser check in the issue remains the final acceptance check.
- A human reviews the change. Auto-merge stays off until review and browser validation complete.
