# Feature Specification: WebSocket Operation Form Cancellation

**Feature Branch**: `3760-websocket-form-cancellation`

**Created**: 2026-10-04

**Status**: Implemented

**Input**: GitHub issue #3888, “feat(web-portal): add explicit cancellation to WebSocket operation forms.” Add explicit cancellation to the 72 live WebSocket operation forms, prevent delayed picker responses from restoring canceled choices, preserve unrelated live session cards, add a normal-user browser regression, and include a release fragment.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Cancel an unsubmitted operation selection (Priority: P1)

As a normal Web Portal user who selected an operation but has not started it, I want a clearly labeled Cancel control so I can discard the pending selection and its field values without starting the operation.

**Why this priority**: Without cancellation, a user can be left with a selected operation and dependent values they no longer intend to run. Cancellation must not accidentally start a stream or utility.

**Independent Test**: Select an operation, populate or begin populating its fields, activate Cancel, and verify the selection and fields are cleared and no operation-start request is sent.

**Acceptance Scenarios**:

1. **Given** any of the 72 live operation entries is selected, **When** the user views its form, **Then** the form presents a clearly labeled Cancel control.
2. **Given** an operation is selected and one or more fields contain values, **When** the user activates Cancel, **Then** the pending selection and its dependent fields are cleared, the form returns to its unselected state, and no operation is started.
3. **Given** no operation is selected, **When** the user views the form, **Then** the form does not imply that a live session can be canceled through this control.

---

### User Story 2 - Keep canceled selections canceled (Priority: P1)

As a user who cancels while a picker is still loading, I want late-arriving picker results to be ignored so the canceled operation and its fields do not reappear.

**Why this priority**: A delayed response must not undo the user's explicit choice or leave values that could be submitted unintentionally.

**Independent Test**: Delay a picker response, select an operation that uses the picker, activate Cancel before the response arrives, then release the response and verify that the form remains unselected and empty.

**Acceptance Scenarios**:

1. **Given** a picker request for the selected operation is outstanding, **When** the user activates Cancel before its response arrives, **Then** the response does not restore the selection, repopulate the canceled form, or affect a later selection.
2. **Given** the user selects a different operation while an earlier operation's picker request is outstanding, **When** the earlier response arrives, **Then** only the current operation's valid picker results may appear.
3. **Given** a picker request fails or returns no rows, **When** the user cancels, **Then** the operation selection and dependent fields are still cleared.

---

### User Story 3 - Preserve live session cards (Priority: P2)

As a user monitoring active WebSocket sessions, I want cancellation to apply only to the unsubmitted form so existing live session cards and their state remain unchanged.

**Why this priority**: Canceling form setup must not stop, alter, or hide work that has already started.

**Independent Test**: Keep at least one live session visible, select and cancel a separate operation, and verify the live session card remains present with unchanged identity and status.

**Acceptance Scenarios**:

1. **Given** one or more live session cards are displayed and an unsubmitted operation is selected, **When** the user cancels that selection, **Then** the cards remain unchanged and no stop or operation-start action is issued for them.
2. **Given** an operation has already been submitted, **When** its session is live, **Then** the form's Cancel control does not act as a session stop control; the existing session controls remain responsible for that session.

### Edge Cases

- Cancel is activated before any picker response arrives, after a response arrives, or after a picker has failed.
- A picker response for a canceled operation arrives after the user selects a different operation.
- The user activates Cancel more than once or while no operation is selected; no operation-start request is sent.
- A selected operation has required, optional, repeatable, confirmation, or dependent fields; cancellation clears the selection-specific values and confirmation.
- A live session exists while a separate unsubmitted form selection is canceled; the session card and session state are not changed.
- Once the user submits an operation, cancellation of the pending selection is no longer the way to control the resulting session.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Each of the 72 live WebSocket operation entries MUST expose a clearly labeled Cancel control when its form is selected.
- **FR-002**: Activating Cancel MUST clear the pending operation selection and all selection-dependent target fields, parameter fields, confirmation input, and selection-specific presentation.
- **FR-003**: Canceling an unsubmitted selection MUST NOT send an operation-start request or create a live session.
- **FR-004**: Cancellation MUST update the authoritative pending-selection state as well as the visible form; clearing visible controls alone is insufficient.
- **FR-005**: Picker results initiated for a canceled or superseded selection MUST be ignored and MUST NOT restore that selection, populate its fields, or alter a later selection.
- **FR-006**: Cancel MUST apply only to the unsubmitted form selection. It MUST NOT stop, remove, or otherwise change any unrelated live session or its card.
- **FR-007**: A normal-user browser regression MUST cover canceling a selected operation, verify that no operation-start request is sent, and verify that a delayed picker response cannot restore canceled state.
- **FR-008**: The change MUST include one release fragment describing the new form-cancellation behavior.

### Key Entities *(include if feature involves data)*

- **Pending operation selection**: The selected catalog operation and its unsent field values, including picker-dependent values and any confirmation text. It exists only while the user is preparing an operation.
- **Picker result**: The available choices returned for a pending selection and its parent fields. A result is relevant only to the selection that requested it.
- **Live session card**: The displayed representation of an already-started WebSocket session. It is independent of an unsubmitted form selection.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 72 live operation entries present a clearly labeled Cancel control when selected.
- **SC-002**: In the normal-user cancellation regression, every cancellation leaves the form unselected and clears its dependent values, with zero operation-start requests sent.
- **SC-003**: In every delayed-picker regression case, a response belonging to a canceled or superseded selection causes zero changes to the current selection and its visible fields.
- **SC-004**: Canceling a form selection leaves every unrelated live session card present with its identity and state unchanged.
- **SC-005**: The release includes exactly one issue-specific fragment describing operation-form cancellation.

## Assumptions

- The 72 entries are the current live catalog of WebSocket channels and device utilities; the scope does not add or remove catalog entries.
- Cancel discards only a selection that has not been submitted. It is not a replacement for controls that stop an existing session.
- Cancel returns the form to its existing unselected presentation and does not preserve discarded values for a later selection.
- A normal-user regression can use a controlled or intercepted picker response so the test does not start a real operation.
