# Feature Specification: A failed multi-site journey ends each operation that it started

**Issue**: #3518
**Feature Branch**: `fix/3518-org-operation-leak`
**Status**: Draft
**Found by**: the full browser run of 2026-09-28 for issue #3511

## Problem

Six browser modules start a multi-site operation on the stand-in sites 2222 and 3333.
Each module cancels the operation on the progress page at the end of the test.
If a step fails before the cancel, the operation stays running.

| Module | Teardown before this change |
| - | - |
| `test_org_start_double_click.py` | The fixture `operator_page` reads the address of the page only. |
| `test_org_missing_precheck_journey.py` | No teardown |
| `test_org_phase_cascade_journey.py` | No teardown |
| `test_org_postcheck_journey.py` | No teardown |
| `test_org_upgrade_flow.py` | No teardown |
| `test_org_upgrade_history.py` | No teardown |

A running operation holds both stand-in sites.
Each later test that needs one of these sites can then fail.

The step `OrgFormSteps.start` waits 15 seconds for the progress page.
In the run of 2026-09-28, the progress page request reached the server 15.15 seconds after the start.
The step failed while the page still showed the confirmation page.
So the teardown of the double-click module found no progress page, and it cancelled nothing.

## User Scenarios & Testing

### User Story 1 (P1): The teardown ends each operation that a test started

A maintainer runs the multi-site modules in one browser run.
A failed test must not leave an operation that holds a stand-in site.

**Independent test**: Run a journey that starts an operation and then fails before its cancel.
Read the status of the operation after the test.

**Acceptance scenarios**:

1. **Given** a test that starts an operation.
   **When** a step fails before the cancel.
   **Then** the teardown cancels the operation through the API, and the operation reaches a final state.
2. **Given** a test that starts an operation and cancels it on the progress page.
   **When** the test ends.
   **Then** the teardown reads the final state, and it sends no cancel.
3. **Given** a start that the server accepts after the step stopped its wait.
   **When** the teardown runs while the page shows the confirmation page.
   **Then** the teardown finds the operation from the answer of the Start request.
4. **Given** a cancel that the portal refuses.
   **When** the teardown runs.
   **Then** the teardown fails, and the message names issue #3518, the call, the status, and the body.

### User Story 2 (P1): Each multi-site module gets the teardown

All six modules start the operation with the fixture `firmware_operator_page`.
So the teardown belongs to that fixture, and each module gets it with no change to the module.

**Independent test**: Run each of the six modules in Edge, and read the debug log of the teardown.

**Acceptance scenarios**:

1. **Given** a test of each module.
   **When** the test starts an operation.
   **Then** the fixture records the operation.
2. **Given** a test that starts no operation.
   **When** the test ends.
   **Then** the teardown sends no call.

### User Story 3 (P2): The start step names a slow start

**Independent test**: Run the double-click module in Edge on a machine with a heavy load.

**Acceptance scenarios**:

1. **Given** a Start request that answers after 15 seconds.
   **When** the step waits.
   **Then** the step waits for the answer of the Start request first, with its own bound.
   After the answer, the step waits for the progress page.
2. **Given** a Start request that the portal refuses.
   **When** the step reads the answer.
   **Then** the step fails, and the message names the status.

### User Story 4 (P2): Direct tests prove each decision

The fault shows only when a step fails.
Direct tests must prove each decision with no browser and no network.

**Acceptance scenarios**:

1. **Given** each answer that a page of the test can get.
   **When** the ledger reads the answer.
   **Then** the ledger records an id only for a 200 answer to the Start request that names a progress page.
2. **Given** a Start answer that the tap cannot fetch or read.
   **When** the tap runs.
   **Then** the ledger records nothing, and the tap logs a warning.
   The test does not fail at a later call.
3. **Given** a live operation, a final operation, and a cancel that the portal refuses.
   **When** the teardown runs.
   **Then** each case gets the correct calls and the correct result.
4. **Given** a Start answer that the tap fetched.
   **When** the tap gives the answer to the page.
   **Then** the ledger already holds the id of the operation.

## Requirements

### Functional Requirements

- **FR-001**: The fixture `firmware_operator_page` must record the id of each operation that its browser context starts.
  The source is the 200 answer to `POST /api/org-upgrades`.
  A Start request of each tab of the context counts.
- **FR-002**: At the end of the test, the fixture must also record the operation of the progress page that the page shows.
- **FR-003**: The teardown must read the status of each recorded operation.
  It must cancel each operation that the portal still lets the operator cancel.
  It must then read the status again until the operation is final.
  A bound must stop the reads.
- **FR-004**: The teardown must fail on four faults.
  The first two faults are a refused status read and a refused cancel.
  The last two faults are a body that is not a JSON object and an operation that stays live after the bound.
  The message must name issue #3518, the operation, and the call or the state.
- **FR-005**: An operation can end between the status read and the cancel.
  Then the cancel answers 409.
  That race must not fail the teardown if the next status read shows a final state.
- **FR-006**: The tap and the ledger must not fail the test from inside the route handler.
  If the tap cannot fetch or read a Start answer, it must log a warning and record nothing.
  If the fetch fails, the tap must stop the page request, and it must not send the request again.
- **FR-007**: The module `test_org_start_double_click.py` must use the fixture `firmware_operator_page` directly.
  The change must remove the method `cancel_if_running` and the fixture `operator_page`.
- **FR-008**: The step `OrgFormSteps.start` must wait for the answer of the Start request before it waits for the progress page.
  Each wait must have its own bound.
  A refusal must fail the step, and the message must name the status.
- **FR-009**: A test that starts no operation must send no call of the teardown.
- **FR-010**: The change must not touch `src/`.
- **FR-011**: The tap must give the page the same status, headers, and body as the portal.
  A route of a page must still take precedence over the tap.

### Key Entities

- **Operation ledger**: the ids of the multi-site operations that the browser context of one test started, in the order of the start.
- **Start tap**: the route of the browser context that fetches each Start answer for the ledger.
- **Operation release**: the status reads and the cancels that end each live operation of the ledger.

## Success Criteria

- **SC-001**: A test that stops on purpose after the Start request leaves no live operation.
  The server log shows the cancel of the teardown, and the next status read shows `cancelled`.
- **SC-002**: The six multi-site modules and the new journey pass in Edge, with the one skip of #3380.
- **SC-003**: In a full browser run, the hold check of #3508 reports no held site.
- **SC-004**: The teardown adds less than one second to a test that cancelled its operation on the page.

## Assumptions

- Only the fixture `firmware_operator_page` starts a multi-site operation in the browser suite.
  The fixtures `controls_operator_page` and `empty_site_operator_page` open seeded operations, or they stop before the start.
- The stand-in cloud cancels each child job at once.
  So a cancel through the API makes the operation final within a few status reads.
- The status read of the portal frees the sites of a settled operation.
- A route of a browser context turns off the HTTP cache of that context.
  The test portal runs on the same machine as the browser, so each extra read costs little.

## Out of Scope

- A module check for multi-site operations.
  No JSON route lists the multi-site operations.
  The teardown of each test fails at the test that leaks, and the hold check of #3508 still covers each session.
  `research.md` records this decision.
