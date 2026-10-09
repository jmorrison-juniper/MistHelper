# Feature Specification: Operation Stream Recovery

**Feature Branch**: `jmorrison-juniper-sse-run-state-4027`

**Feature Path**: `specs/numbered/0/0/1/1/2/1/0/2/4027-operation-stream-recovery/`

**Created**: 2026-10-06

**Status**: Draft

**Input**: Issues #4027 and #4032. Recover terminal operation state when an
open event stream loses its terminal event. Make output replay idempotent
without removing distinct server paths.

## User Scenarios & Testing

### User Story 1 - Recover a lost terminal event (Priority: P1)

As a network operator, I need the Operations page to show the authoritative
terminal state even when the open event stream loses the terminal event.

**Why this priority**: A stale `Running` state hides the actual result. The
operator cannot know whether the operation completed or failed.

**Independent Test**: Keep the event stream open without a terminal event.
Return a terminal state from the status resource. The page must leave
`Running` without an event stream error or a manual reconnect.

**Acceptance Scenarios for Issue #4027**:

1. **Given** an active run with an open event stream, **When** the terminal
   event is lost and the status resource reports `completed`, **Then** the page
   shows the completed state and the final output.
2. **Given** an active run with an open event stream, **When** the terminal
   event is lost and the status resource reports `failed`, **Then** the page
   shows the failed state and the failure message.
3. **Given** an active run whose status remains `running`, **When** the page
   checks the authoritative status, **Then** the page remains in the running
   state and keeps the event stream active.
4. **Given** a run that reaches a terminal state, **When** later recovery work
   would run, **Then** the page does not return the run to a running state.

### User Story 2 - Render each output once (Priority: P1)

As a network operator, I need reconnect and terminal replay to show one link
for each output so I can identify and open the correct result.

**Why this priority**: Duplicate links and repeated preview loading make the
result uncertain and can hide the useful terminal state.

**Independent Test**: Deliver the same output path through status replay and
terminal event replay. The page must show one link and must not restart result
preview loading for the duplicate.

**Acceptance Scenarios for Issue #4032**:

1. **Given** one run and one exact server file path, **When** REST replay and
   terminal event replay both report that path, **Then** the page shows one
   output link.
2. **Given** one run and two distinct server file paths, **When** replay
   reports both paths, **Then** the page shows both output links.
3. **Given** two runs that report the same server file path, **When** each run
   is displayed, **Then** output identity remains separate for each run.
4. **Given** a duplicate output replay, **When** the output already exists for
   the run, **Then** the page does not restart result preview loading.
5. **Given** a terminal result with no output files, **When** the terminal
   state is rendered, **Then** the page clears stale result loading state and
   keeps the terminal message visible.

### User Story 3 - Keep the repair within the browser boundary (Priority: P2)

As a maintainer, I need a focused browser repair so the authoritative server
state and output discovery services remain unchanged.

**Why this priority**: The server already stores terminal state before it
publishes the terminal event. The status resource already returns that state.

**Independent Test**: Review the feature diff. It must contain the browser
controller, one dedicated browser test, two release-note fragments, and the
feature specification records only.

**Acceptance Scenarios**:

1. **Given** the approved scope, **When** the feature diff is reviewed,
   **Then** `web_portal/services/operation.py` is unchanged.
2. **Given** the approved scope, **When** the feature diff is reviewed,
   **Then** `web_portal/services/output_scan.py` is unchanged.
3. **Given** the planned browser proof, **When** the test suite is reviewed,
   **Then** one dedicated Playwright test covers both issue contracts.

### Edge Cases

- A completed run can have no output files and a valid completion message.
- A failed run can have no output files and must clear stale result loading.
- The same exact path can arrive more than once through different replay
  sources for the same run.
- Two distinct paths can have the same base file name and must remain separate.
- The same exact path can belong to different runs and must not share identity.
- A status check can report `running` immediately before a later terminal
  result.
- A terminal event and an authoritative status response can arrive in either
  order.
- A late running response must not replace a terminal page state.

## Requirements

### Functional Requirements

- **FR-001**: The browser MUST use the existing operation status resource as
  the authoritative state for an active run.
- **FR-002**: The browser MUST reconcile active run state while the event
  stream remains open.
- **FR-003**: Recovery MUST NOT require `EventSource.onerror` or a manual
  reconnect.
- **FR-004**: A `completed` status MUST set the completed presentation, show
  the completion message, render the terminal output set, and finish the run.
- **FR-005**: A `failed` status MUST set the failed presentation, show the
  failure message, and finish the run.
- **FR-006**: A `running` status MUST preserve the active run and MUST NOT
  close a healthy event stream.
- **FR-007**: A terminal browser state MUST NOT return to `Running` because of
  a late response or a later recovery action.
- **FR-008**: Output identity MUST use the run identifier and the exact server
  file path.
- **FR-009**: Repeated delivery of the same output identity MUST produce one
  link and one result-preview load for that identity.
- **FR-010**: Distinct exact server file paths MUST always remain available,
  including paths that share a base file name.
- **FR-011**: The same exact server file path from two different runs MUST be
  treated as two run-scoped output identities.
- **FR-012**: A terminal result with an empty output list MUST clear stale
  result loading state.
- **FR-013**: Empty terminal output MUST NOT remove the terminal status message.
- **FR-014**: The implementation MUST change
  `web_portal/static/js/operations.js`.
- **FR-015**: The implementation MUST add one dedicated Playwright test under
  `tests/e2e/web_portal/`.
- **FR-016**: The implementation MUST add separate release-note fragments for
  #4027 and #4032.
- **FR-017**: The implementation MUST NOT change
  `web_portal/services/operation.py`.
- **FR-018**: The implementation MUST NOT change
  `web_portal/services/output_scan.py`.
- **FR-019**: The implementation MUST NOT change the operation status response
  contract or the server output discovery contract.

### Red-Proof Requirements for Issue #4027

- **RP-4027-001**: The dedicated Playwright test MUST keep the event stream
  open and MUST not invoke its error handler.
- **RP-4027-002**: The test MUST first present a running status and then an
  authoritative completed status without a terminal event.
- **RP-4027-003**: The test MUST prove that the current browser behavior stays
  in `Running` before the repair.
- **RP-4027-004**: The repaired test MUST prove that the page reaches the
  completed state without a stream error or manual reconnect.
- **RP-4027-005**: The test MUST cover an authoritative failed status and its
  visible failure message.
- **RP-4027-006**: The test output MUST report the number of status checks and
  terminal transitions that it examined.

### Red-Proof Requirements for Issue #4032

- **RP-4032-001**: The dedicated Playwright test MUST send one exact output
  path through both status replay and terminal event replay.
- **RP-4032-002**: The test MUST prove that the current browser behavior adds
  two links for that one run-scoped output identity before the repair.
- **RP-4032-003**: The repaired test MUST prove that the page shows one link
  and starts one result-preview load for the repeated identity.
- **RP-4032-004**: The test MUST send at least two distinct exact server paths
  and prove that the page keeps each path.
- **RP-4032-005**: The test MUST send an empty terminal output list after a
  loading presentation and prove that the stale loading state clears.
- **RP-4032-006**: The test output MUST report the number of replay sources,
  output paths, rendered links, and preview loads that it examined.

### Mist Cloud Transport Requirements

This feature does not add or change a Mist Cloud transport.

### Key Entities

- **Operation run**: One execution identified by `run_id`.
- **Authoritative status**: The stored run state returned by
  `GET /api/operations/status/<run_id>`.
- **Event stream**: The live operation update channel that can lose a terminal
  event while the connection remains open.
- **Terminal state**: A completed or failed operation state that ends browser
  recovery for the run.
- **Output identity**: The combination of `run_id` and the exact server file
  path.
- **Result loading state**: The visible indication that the browser waits for
  output preview data.

## Scope

### Planned Implementation Files

- `web_portal/static/js/operations.js`
- `tests/e2e/web_portal/test_operation_stream_recovery.py`
- `changelog.d/issue-4027-operation-stream-recovery.md`
- `changelog.d/issue-4032-output-replay-deduplication.md`
- `specs/numbered/0/0/1/1/2/1/0/2/4027-operation-stream-recovery/spec.md`
- `specs/numbered/0/0/1/1/2/1/0/2/4027-operation-stream-recovery/checklists/requirements.md`
- `specs/numbered/0/0/1/1/2/1/0/2/4027-operation-stream-recovery/.spec-context.json`

### Excluded Files

- `web_portal/services/operation.py`
- `web_portal/services/output_scan.py`

### Existing Contracts

- `OperationExecutor` stores terminal state before it publishes terminal SSE.
- `GET /api/operations/status/<run_id>` returns authoritative terminal state.
- The browser currently reads that status after `EventSource.onerror` or a
  manual reconnect.
- REST replay and terminal SSE can both request output rendering.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Each covered run reaches its authoritative terminal page state
  without a stream error or manual reconnect.
- **SC-002**: Each repeated run-scoped output identity produces exactly one
  visible link.
- **SC-003**: Each distinct exact server file path produces one visible link,
  with zero distinct paths removed.
- **SC-004**: A duplicate output replay starts zero additional preview loads.
- **SC-005**: Each empty terminal output case clears the loading presentation
  and keeps the terminal message visible.
- **SC-006**: The dedicated Playwright test fails against the current behavior
  for both issue defects and passes after the planned browser repair.
- **SC-007**: The final implementation diff changes no server operation
  service or output scan service file.

## Assumptions

- The stored terminal state is authoritative because it is written before the
  terminal event is published.
- The existing status resource needs no server contract change.
- The event stream can remain open after it loses a terminal event.
- Exact server file paths are stable within one run.
- Output order can follow first observation, provided each distinct identity
  remains available.
- One dedicated Playwright module can hold separate tests for #4027 and #4032.
- Product implementation starts only after planning. This specification phase
  changes no product code or browser test code.
