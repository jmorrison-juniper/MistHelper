# Research: A failed multi-site journey ends each operation that it started

**Issue**: #3518
**Spec**: [spec.md](./spec.md)

## Decision 1: Record the id from the answer of the Start request

**Decision**: A route of the browser context holds each request to `POST /api/org-upgrades`.
The class `OrgStartTap` fetches the answer, and the ledger records the id from a 200 answer.
The tap then gives the page the same answer.

**Rationale**:

- The Start route answers 200 with the field `next`.
  That field holds the address `/upgrade/org/jobs/org-run-<hex>`.
  The script `portal.js` then opens that address.
- The ledger records the id before the page gets the answer.
  So the id is known also when the step stops its wait on the confirmation page.
- A route of the context holds the requests of each tab.
  The test `test_a_second_tab_links_to_the_operation_that_runs` opens a second tab.
- A route of a page takes precedence over a route of the context.
  So the retry test can still hold the first Start request with its own route.
- The page gets one request event for each request, as before.
  The fetch of the tap is not a request of the page.
  So the double-click test counts the same requests.

**Alternatives considered**:

- Read the id from the address of the page only.
  The method `cancel_if_running` did this, and issue #3518 shows the gap.
  Rejected as the only source, but kept as a second source (FR-002).
- Read the body in a handler of the answer event of the context.
  The first design did this, and the browser proof of T009 found its fault.
  The handler lost the body of 2 of 2 starts.
  The warning read `Protocol error (Network.getResponseBody): No resource with given identifier found`.
  The script `portal.js` opens the progress page at once after the answer.
  The browser then drops the body of the old document before the handler reads it.
  Rejected.
- Record each request for a progress page.
  A test can open the progress page of an operation that it did not start.
  The teardown would then cancel an operation of another test.
  Rejected.

## Decision 2: Read the body from the fetched answer, and catch each fault

**Decision**: The tap reads the body of the fetched answer.
The tap catches each fault of the fetch, of the body read, and of the answer to the page.
It logs a warning for each fault.

**Rationale**:

- The method `route.fetch()` keeps the whole answer in the memory of the Playwright driver.
  So a navigation of the page cannot drop the body.
- The sync API of Playwright runs each route handler in its own greenlet.
  The class `EventGreenlet` in `playwright/_impl/_connection.py` holds that rule.
  So a blocking call such as `route.fetch()` works inside the handler.
- A fault that escapes a handler goes to `_on_event_listener_error`.
  Playwright stores the fault and raises it at the next API call of the test.
  The test would then fail at a step that has no fault.
  So the tap must catch each fault itself (FR-006).
- If the fetch fails, the tap stops the page request.
  The portal can accept a start after the fetch stopped its wait.
  A second request could then start a second operation.
  The page address of FR-002 can still find the first operation.
- If the answer to the page fails, the page closed first.
  The ledger already holds the id, so the teardown still ends the operation.

**Alternatives considered**:

- Read the body later, in the teardown.
  The body is often gone by then.
  Rejected.
- Send the request again with `route.continue_()` after a failed fetch.
  The second request could start a second operation.
  Rejected.

## Decision 3: Ask the portal whether an operation is live

**Decision**: The teardown reads the field `cancel_allowed` of the status answer.
The value `true` means that the operation is live.

**Rationale**:

- The route builds the field from `FINAL_OPERATION_STATES` of `src/operations/execution/firmware/aggregate_upgrade_service.py`.
  The progress page uses the same field to show the cancel form (issue #3225).
  So the teardown holds no copy of the list of final states.
- A status answer with no boolean field fails the teardown.
  A wrong answer then cannot pass as a final state.

**Alternatives considered**:

- Compare the field `status` with a copy of the final states.
  A copy can drift from the portal.
  Rejected.

## Decision 4: Read the status again after each cancel

**Decision**: After a cancel, the teardown reads the status until `cancel_allowed` is `false`.
The bound is 30 reads, with a pause of 0.5 seconds between two reads.

**Rationale**:

- The status route runs `_refresh_aggregate`.
  That call frees the sites of an operation after each child job settles.
  So the last status read also frees the sites.
- The stand-in cloud cancels each child job at once.
  The bound of 15 seconds matches `RELOAD_TIMEOUT_MS` of the cancel step on the progress page.

## Decision 5: Accept a 409 only when the next read shows a final state

**Decision**: If the cancel answers 409, the teardown reads the status once.
A final state ends the teardown with no fault.
A live state fails the teardown with the body of the 409.

**Rationale**:

- The cancel route answers 409 with `NOT_CANCELLABLE` for a final operation.
  An operation can end between the status read and the cancel (FR-005).
- The route also answers 409 with `CANCEL_FAILED` for a replay or a damaged state.
  That answer is a real fault, and the next read shows a live state.

## Decision 6: The teardown belongs to the fixture `firmware_operator_page`

**Decision**: A new fixture `org_operation_ledger` holds the ledger, and it registers the tap as a route of the browser context.
The fixture `firmware_operator_page` ends each recorded operation before it closes the page.

**Rationale**:

- All six modules start their operation with `firmware_operator_page`.
  So one change covers each module, and no module needs its own teardown.
- A test can ask for `org_operation_ledger` and read the recorded ids.
  The new journey `test_org_operation_teardown.py` uses that fixture as its proof.
- A test that starts no operation leaves the ledger empty.
  The teardown then sends no call (FR-009).

## Decision 7: The start step waits for the answer first

**Decision**: `OrgFormSteps.start` waits for the Start answer with a bound of 45 seconds.
It then waits for the progress page with the bound `RELOAD_TIMEOUT_MS` of 15 seconds.

**Rationale**:

- The run of 2026-09-28 measured 15.15 seconds from the start to the progress page request.
  The bound of 45 seconds is three times that time.
- A slow start then fails with a message about the Start answer, not about the progress page.
- The other five modules wait for the progress page with the default bound of Playwright, which is 30 seconds.
  The new teardown also covers a late start in those modules, so they keep their wait.

## Decision 8: No module check for multi-site operations

**Decision**: The change adds no module check, such as the live-run check of issue #3511.

**Rationale**:

- No JSON route lists the multi-site operations.
  Only the HTML page `/history` lists them.
- No route reads the state of a site lock.
  The lock route accepts a take, a release, and a heartbeat only.
- The teardown of each test fails at the test that leaks.
  The hold check of issue #3508 still finds a held site at the end of each session.

**Alternatives considered**:

- Parse the HTML of `/history` after each module.
  A change to the page would break the check with no signal.
  Rejected.

## Decision 9: Accept the cost of the route

**Decision**: The tap stays a route of the context, and T010 measures its cost.

**Rationale**:

- A route turns off the HTTP cache of its browser context.
  So each page load of such a context reads the style sheet and the page script again.
- Only the fixture `org_operation_ledger` adds the route.
  Only the 14 tests that take `firmware_operator_page` get it.
- The test portal runs on the same machine as the browser.
  So each extra read costs a few milliseconds.
- The tap adds one fetch for each Start request, and no fetch for any other request.

**Alternatives considered**:

- Add the route only in the tests that start an operation.
  Each such test would need its own fixture, and a new test could forget it.
  Rejected.
