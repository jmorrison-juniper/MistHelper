# Research: Operation Stream Recovery

## Decision 1: Use the Existing Status Endpoint

**Decision**: Use `GET /api/operations/status/<run_id>` as the authoritative
state source for an active browser run.

**Rationale**: The operation service stores terminal state before it publishes
the terminal event. The route already returns status, messages, and outputs.
The approved scope prohibits a server contract change.

**Alternatives considered**:

- Reconnect the event stream after each error. This does not recover a lost
  terminal event while the original stream stays open.
- Change `web_portal/services/operation.py`. This violates the approved file
  boundary and adds no required server behavior.
- Change `web_portal/services/output_scan.py`. Output discovery already returns
  the required exact paths.

## Decision 2: Use a Recursive Five-Second Timeout

**Decision**: Schedule one status check with `setTimeout` after 5,000
milliseconds. Schedule the next check only after the current request settles.

**Rationale**: A recursive timeout creates one request chain.
It cannot overlap requests when one response is slow.
It also permits direct timer cleanup at each terminal transition.

**Alternatives considered**:

- Use `setInterval`. A slow response can overlap the next request.
- Start a status request on each heartbeat. Heartbeat timing is a stream
  transport detail and does not guarantee a five-second check.
- Check only after `EventSource.onerror`. This is the current defect.

## Decision 3: Guard Every Asynchronous Result by Run Identity

**Decision**: Capture `runId` in each timer, request, and stream handler.
Apply a result only when it still owns the active run.
Reject each result after that run becomes terminal.

**Rationale**: Fetch responses and stream events can arrive in either order.
A run identity guard prevents an old response from changing a new run.
A terminal guard prevents a late `running` result from restoring `Running`.

**Alternatives considered**:

- Trust response order. Network order is not stable.
- Abort only the fetch. A response can already be ready for its callback.
- Read only the global run identifier inside callbacks. A reconnect can replace
  that value before the callback runs.

## Decision 4: Keep One Browser State Record

**Decision**: Replace the `currentSSE` scalar with one state record.
Keep `currentRunId` for existing active-run call sites.

**Rationale**: The state record can own the stream, timer, request ownership,
terminal identity, and output replay state.
This design adds no top-level declaration to the noncompliant module.

**Alternatives considered**:

- Add several global variables. This increases existing structural debt.
- Add a new browser module. This violates the measured product scope.
- Refactor the whole controller. This mixes unrelated structural work with
  two focused repairs.

## Decision 5: Replace Output Sets Instead of Appending Links

**Decision**: Treat each replay delivery as the complete known output set.
Deduplicate exact paths, compare a canonical run-scoped identity set, and
replace the rendered links only when the set changes.

**Rationale**: The current append behavior creates duplicate links.
Set replacement retains every distinct path and removes stale paths.
The canonical comparison skips identical sets even when their order changes.

**Alternatives considered**:

- Deduplicate by base file name. This removes valid paths from different
  directories.
- Use path identity without `run_id`. Two runs can then share stale state.
- Append only unseen paths. This cannot apply an authoritative empty set.

## Decision 6: Clear Output State Without Resetting Terminal State

**Decision**: A terminal empty output set will clear the link panel and call
`OperationResults.reset()`.
It will not call `resetExecutionPanel`.

**Rationale**: `resetExecutionPanel` changes the status to `Waiting`.
`OperationResults.reset()` clears the preview state without changing the
terminal message.

**Alternatives considered**:

- Return early for an empty list. This leaves stale loading state visible.
- Reset the full execution panel. This removes the required terminal result.
- Change `operation_results.js`. The approved product scope contains only
  `operations.js`.

## Decision 7: Use a Controlled Browser Harness

**Decision**: Add one Playwright module with an init-script `EventSource`
double and route interception for status and preview requests.

**Rationale**: The test can keep the stream open, suppress stream errors, and
deliver terminal events in a controlled order.
It needs no Mist credential and no server service change.

**Alternatives considered**:

- Use a unit test for JavaScript text. It cannot prove browser state or request
  order.
- Modify the existing operations workflow module. The approved scope excludes
  that file.
- Start a live Mist operation. This needs a production credential and cannot
  reliably lose one terminal event.
