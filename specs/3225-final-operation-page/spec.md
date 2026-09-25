# Feature Specification: Show a final multi-site operation as final

**Issue**: #3225
**Feature Branch**: `fix/3225-final-operation-page`
**Status**: Draft
**Found by**: the multi-site journey of #3200

## Problem

The progress page of a multi-site operation keeps the cancel form after the
operation reaches a final state. An operator can type CANCEL and press the
button on a completed operation. The route then sends one cloud cancel call
for each child job. The result lists each access point that already upgraded
as a cancelled device.

The single-site stop refuses a final run with the status 409 and the code
`run_not_stoppable`. It sends no cloud request, and its page disables the stop
button when the run ends.

The same page has four more defects.

1. The shared cell rule breaks a word at any letter. At a width of about 960
   pixels the tables print `upgra ded`, `pendin g`, and `gatew ay`.
2. The site table and its poll show `ap` for a child job that stores no device
   family. The cancel outcome panel shows empty brackets for the same child job.
3. The Cancellation cell prints the status word and the message with no
   separator, so the cell reads as one broken sentence.
4. The server render and the poll repaint use two different formats for the
   Cancellation cell. The text changes after the first poll.

## User Story 1 (P1): A final operation offers no cancel request

**Acceptance scenarios**:

1. **Given** an operation in the state `completed`, `cancelled`, or `failed`,
   **When** the operator opens its progress page, **Then** the page shows no
   cancel form and no cancel caution. A note states the final state.
2. **Given** a page of a running operation, **When** the poll reports a final
   state, **Then** the page hides the cancel form, disables its controls, and
   shows the same note with no reload.
3. **Given** an operation in a final state, **When** a client sends the typed
   cancel, **Then** the route answers 409 with the code
   `org_upgrade_not_cancellable`. The portal sends no cloud request and writes
   no change to the stored operation.
4. **Given** an organization job of an earlier release in a final state, **When**
   a client sends the typed cancel, **Then** the route answers the same 409 and
   sends no cloud request.
5. **Given** an operation in the state `running`, `partial`, or
   `attention_required`, **When** the operator sends the typed cancel, **Then**
   the cancel runs as before.

## User Story 2 (P2): The tables keep each word whole

**Acceptance scenarios**:

1. **Given** the progress page at a width of 960 pixels, **When** the page
   shows the site table and the device table, **Then** no family, status,
   type, or state cell breaks inside a word.
2. **Given** a table wider than the page, **When** the operator reads it,
   **Then** the scroll box of the table scrolls sideways, and the page itself
   does not.

## User Story 3 (P3): The page names an unknown family and one cancel format

**Acceptance scenarios**:

1. **Given** a child job that stores no device family, **When** the page and
   the poll show it, **Then** the family reads `unknown`, never `ap`.
2. **Given** a child job that holds a cancel result, **When** the page and the
   poll show the Cancellation cell, **Then** both show one text, for example
   `Status: requested. The cloud stopped 1 device(s). Cancelled: 001122334477.`
3. **Given** an organization job of an earlier release, **When** the page shows
   its site rows, **Then** the family reads `ap`, because that job upgrades
   access points only.

## Functional requirements

- **FR-001**: The final states of an operation are `completed`, `cancelled`,
  and `failed`. One Python constant holds the set, and the page script holds
  the same three words. A test proves that the two lists agree.
- **FR-002**: The aggregate service reads the stored operation before any
  cancel write. If the stored state is final, the service raises a refusal and
  makes no write and no cloud call.
- **FR-003**: The cancel route maps that refusal to 409 with the code
  `org_upgrade_not_cancellable` and the message
  `The operation is final: <state>. The portal sent no cancel request.`
- **FR-004**: The cancel route applies the same rule to an organization job of
  an earlier release. It reads the final state from the signed job marker.
- **FR-005**: The status summary and the poll answer carry the boolean
  `cancel_allowed`. The page renders the cancel form only when the value is
  true. The page script hides the form when a poll reports false.
- **FR-006**: The family cell, the status cell, the type cell, and the state
  cell never break inside a word, in the first render and after each poll.
- **FR-007**: A missing family reads `unknown` in the site table, in the poll
  repaint, and in the cancel outcome panel.
- **FR-008**: The server builds the Cancellation text one time. The page and
  the poll show that same text.

## Out of scope

- A cancel of a running operation still sends a cancel request to a child job
  that already ended. Issue #3367 records that defect.
- The page adds no new links for a final operation. The navigation bar links
  the history, a new upgrade, and the comparison on every page, and the
  single-site page adds no link either.

## Success criteria

- **SC-001**: Contract tests prove the 409, the code, no cloud call, and no
  store write for each final state and for the earlier job marker.
- **SC-002**: Contract tests prove the page and the poll for a final operation
  and for a running operation.
- **SC-003**: A browser journey proves the hidden form after a final poll, the
  whole words at 960 pixels, and one Cancellation text before and after a
  poll. Each screenshot of the journey is read.
