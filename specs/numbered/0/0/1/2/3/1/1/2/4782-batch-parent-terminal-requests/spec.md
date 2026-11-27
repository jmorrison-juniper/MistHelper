# Feature Specification: Batch Parent Terminal Requests

**Feature Branch**: `fix/4782-batch-parent-terminal-requests`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4782, titled "Runtime: portal batch parents request unsupported terminal endpoints." For a selected batch parent, the page requests the terminal read route and the resize route. Both return HTTP 409.

## Clarifications

### Session 2026-11-26

- Q: Is the defect still present on `main`? A: No. Commit `4e81b2a4a7` (PR #4924, merged 2026-11-26) added the guard at `websockets.js` line 1894. Issue #4932 closed with the same symptom.
- Q: Does the retained commit `c07cb9f8` carry the fix? A: No. Its `isTerminalSession` has no `multi_site` check. Merging it removes the guard.
- Q: Does the existing test cover both routes? A: No. The batch parent test checks terminal reads only, at line 1569. It checks no resize request.
- Q: Does the owner ownership hold block the test edit? A: Yes. The edit changes one held file, `tests/e2e/websockets_tab/test_websockets_page.py`. Task T001 checks the release.
- Q: Should the test read console text? A: No. Console wording depends on the browser version. The test reads request URLs instead.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Select a batch parent without terminal requests (Priority: P1)

An operator starts a Multi Site hardware batch. The operator selects the batch parent. The page shows the batch progress and the message view. The page sends no request to the terminal read route or the resize route.

**Why this priority**: Each selection shows HTTP 409 errors in the browser console. Operators see failing requests during normal use.

**Independent Test**: Start a hardware batch in the e2e portal. Record browser requests to session routes for 1500 milliseconds. Verify that no request targets the terminal read route or the resize route.

**Acceptance Scenarios**:

1. **Given** a batch parent exists, **When** the page opens and selects the batch parent, **Then** the page sends no request to the terminal read route.
2. **Given** a batch parent exists, **When** the page selects the batch parent, **Then** the page sends no request to the resize route.
3. **Given** a batch parent is selected, **When** the message view loads, **Then** the page shows the message view and hides the terminal panel.

---

### User Story 2 - Restore a batch parent after a page reload (Priority: P2)

An operator reloads the WebSockets page while a batch parent is selected. The page restores the saved selection. The page sends no terminal read request and no resize request for the restored batch parent.

**Why this priority**: The restore path calls the same selection code. A reload repeats the HTTP 409 errors without any operator action.

**Independent Test**: Start a hardware batch, reload the page, open the Multi Site tab, and record session route requests for 1500 milliseconds.

**Acceptance Scenarios**:

1. **Given** a batch parent is selected, **When** the operator reloads the page, **Then** the progress panel shows again and no terminal or resize request occurs.

---

### User Story 3 - Keep terminal sessions working (Priority: P3)

An operator selects a terminal session. The page reads terminal output and posts each window size change. The existing terminal journeys still pass.

**Why this priority**: The guard must block batch parents only. A broad block removes the shell view for every operator.

**Independent Test**: Run the existing resize journey `test_j5_resize` in `tests/e2e/websockets_tab/test_websockets_terminal.py`.

**Acceptance Scenarios**:

1. **Given** a terminal session is open, **When** the operator changes the window size, **Then** the page posts the new size to the resize route.

### Edge Cases

- A page reload restores a batch parent. Covered by User Story 2.
- A session payload has `output` set to `terminal` and `mode` set to `multi_site`. The guard checks the mode first, so the session is not a terminal session. Covered by reading the guard only. No new test covers it.
- The operator selects a batch parent while a terminal session is open. The page stops the terminal controller first at `websockets.js` line 1855. No new test covers this order. This is a residual risk.
- An older client sends a terminal read to a batch parent. The server returns HTTP 409 with code `not_terminal`. The server contract stays unchanged (FR-006).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The page MUST NOT request the terminal read route for a batch parent.
- **FR-002**: The page MUST NOT request the resize route for a batch parent.
- **FR-003**: The page MUST treat each session with mode `multi_site` as a non-terminal session on every selection path, including a restore after reload.
- **FR-004**: The page MUST keep the terminal read and resize requests for each terminal session.
- **FR-005**: The regression tests MUST fail when a batch parent sends a terminal read request or a resize request.
- **FR-006**: The server MUST keep the HTTP 409 response with code `not_terminal` for a terminal request on a non-terminal session.
- **FR-007**: The change MUST modify no production file. It MUST change only the e2e test module and this record.

### Mist Cloud Transport Requirements

Not applicable. The change makes no Mist Cloud REST call and no Mist Cloud WebSocket call. The two routes are local portal routes.

### Key Entities

- **Batch parent**: A session with `mode` set to `multi_site`. It owns no shell. Its targets run the shells.
- **Terminal session**: A session that `isTerminalSession` accepts. The page opens it with the terminal controller.
- **Message session**: A session that the page reads through the messages route. It shows rows, not a shell.
- **Guard**: The check in `isTerminalSession` that returns false for a batch parent.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The batch parent test records zero requests to the terminal read route and the resize route during 1500 milliseconds after the batch starts.
- **SC-002**: The reload test records zero such requests after the page reload and the restore.
- **SC-003**: The existing `test_j5_resize` test passes in the `websockets-tab` CI shard.
- **SC-004**: The regression tests fail when the guard is removed in a throwaway worktree.
- **SC-005**: The pull request changes one test file and this record. The `gh pr view` file list shows only those paths.

## Assumptions

- The fake services model the server payload. The fake batch payload sets `mode` to `multi_site` at test file line 474. The server sets the same mode at `session.py` line 106.
- The `websockets-tab` CI shard runs every test module in `tests/e2e/websockets_tab` (`ci.yml` lines 797 and 798).
- The bootstrap installs Playwright and downloads Chromium (`development-setup.md` line 265).
- The repository has no open pull request that changes the held test module or `websockets.js` (research rows R-62 and R-63).

## Preconditions

- The owner releases the ownership hold on `tests/e2e/websockets_tab/test_websockets_page.py` before any edit. Task T001 records the release.

## Out of Scope

- Any change to `websockets.js`, the terminal controller files, or the server routes.
- The retained #4773 implementation and commit `c07cb9f8`.
- A live staging smoke test. It needs a credential decision (D-8).
- A changelog fragment and operator documentation changes (D-6).
- The residual edge case listed above.
- Mist API behavior. The OpenAPI grep found no portal route.
