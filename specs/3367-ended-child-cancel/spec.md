# Feature Specification: Send no cancel request to a child job that already ended

**Issue**: #3367
**Feature Branch**: `fix/3367-ended-child-cancel`
**Status**: Draft
**Found by**: the work on #3225

## Problem

A cancel of a multi-site operation that still runs sends a cancel request to
each child job that holds an upgrade identifier. The service does not read the
stored state of the child job first. A child job that already ended also gets a
cancel request.

The result then misreports the devices of that child job. For an access point
child job that completed, the cancel sort puts each access point in the
Cancelled list. Each of those access points already runs the new firmware.

The single-site stop refuses a run in a final state with the status 409 and the
code `run_not_stoppable`. It sends no cloud request. A child job of a
multi-site operation is the multi-site match of one run.

## User Story 1 (P1): An ended child job gets no cancel request

**Acceptance scenarios**:

1. **Given** a running operation with one completed child job and one running
   child job, **When** the operator sends the typed cancel, **Then** the portal
   sends one cancel request for the running child job and no request for the
   completed child job.
2. **Given** a child job in the state `completed`, `cancelled`, `failed`, or
   `rejected` that holds an upgrade identifier, **When** the cancel reaches it,
   **Then** the portal sends no cloud request for it.
3. **Given** a child job with no upgrade identifier, **When** the cancel
   reaches it, **Then** the stored result stays `unavailable`, as before.
4. **Given** the cancel of scenario 1, **When** the portal stores the result,
   **Then** the ended child job holds the status `already_ended`, its final
   state, three empty device lists, and the message
   `The child job already ended: completed. The portal sent no cancel request.`
5. **Given** a second cancel of the same operation, **When** it runs, **Then**
   the portal sends no second request to any child job.

## User Story 2 (P2): The page states that the child job already ended

**Acceptance scenarios**:

1. **Given** an ended child job with the result `already_ended`, **When** the
   operator reads the site table, **Then** the Cancellation cell reads
   `Status: already_ended. The child job already ended: completed. The portal
   sent no cancel request.`
2. **Given** the same child job, **When** the operator reads the cancel outcome
   panel, **Then** the panel shows the status, the message, and the note
   `This child job ended before the cancel, so the cancel changed no device of
   it.` The panel lists no device of the child job.
3. **Given** a reload of the page, **When** the page renders again, **Then**
   the panel and the cell show the same text.

## Functional requirements

- **FR-001**: The service reads the stored state of each child job before its
  cancel call. If the state is in `FINAL_CHILD_STATES`, the service sends no
  cloud request for that child job.
- **FR-002**: The identifier check stays first. A child job with no upgrade
  identifier keeps the result `unavailable`.
- **FR-003**: The stored result of an ended child job holds the status
  `already_ended`, the final state, three empty lists, and one message.
- **FR-004**: The cancel outcome panel builds the row of an ended child job
  with the note and with a flag that hides the three lists.
- **FR-005**: The existing claim rule stays. A repeated cancel sends no second
  request to a child job that holds a result.

## Out of scope

- A child job that ends in the cloud after the last status read still gets a
  cancel request. The page reads each child job every 30 seconds, so the
  window is at most one poll interval. The single-site stop uses the stored
  state in the same way.
- The aggregate state of an operation with one completed child job and one
  cancelled child job. The service rule for that mix does not change here.

## Success criteria

- **SC-001**: A unit test proves that a completed child job gets no cancel
  call, and that a running sibling still gets one.
- **SC-002**: A unit test proves the result of each final child state, and the
  unchanged `unavailable` result.
- **SC-003**: Unit and contract tests prove the outcome row and the rendered
  panel of an ended child job.
- **SC-004**: A browser journey cancels a seeded operation with one completed
  child job. The journey reads the note, the missing lists, and the
  Cancellation cell, before and after a reload. Each screenshot is read.
