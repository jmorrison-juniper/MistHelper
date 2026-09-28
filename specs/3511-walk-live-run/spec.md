# Feature Specification: The capture walk ends each run that it builds

**Issue**: #3511
**Feature Branch**: `fix/3511-walk-live-run`
**Status**: Draft
**Found by**: task T014 of #3507, in a run of `test_capture.py` and `test_existing.py` together

## Problem

The walk of the capture journey builds a run on the first site of the picker.
That site is the stand-in site `22222222-2222-2222-2222-222222222222`.

| Step | What happens |
| - | - |
| 1 | The walk `test_walk_from_the_site_list_reaches_the_confirm_page` clicks the upgrade button. The create call answers 201. |
| 2 | The options page offers no version (#3380), so the walk reports a skip. |
| 3 | The fixture `walking_page` clicks the release control. That control gives back the site lock only. |
| 4 | The run stays in the state `created`. No teardown ends it. |

The create route refuses a new run while a live run holds the site (FR-037).
So each later create call at that site answers 409 with `upgrade_already_running`.

Two tests then use the leftover run in place of their own run.

- The refusal test `test_a_refused_second_start_shows_a_link_to_the_open_run` accepts 201 or 409 for its first create call. After the walk, that call answers 409. The test then proves that the leftover run blocks a create. It does not prove that its own run blocks a create.
- The helper `_create_run` of `test_existing.py` accepts a 409 and opens the run that the refusal names. The ledger of #3497 does not record that run, so no teardown of that module ends it.

No check saw the leftover run, so each test passed.

## User Scenarios & Testing

### User Story 1 (P1): The walk ends its run

A maintainer runs the capture module before the run-control module.
Each module must start from a site that holds no live run of an earlier module.

**Independent test**: Run `test_capture.py` and `test_run_controls/test_existing.py` together in Edge.
Read the debug log of `_create_run`.

**Acceptance scenarios**:

1. **Given** a new browser run.
   **When** the walk builds a run and then stops at the options page.
   **Then** the teardown cancels that run before it releases the site.
2. **Given** the same run.
   **When** `test_existing.py` sends its first create call.
   **Then** the call answers 201, and the ledger of that test records the new run.
3. **Given** a cancel that the portal refuses.
   **When** the teardown of the walk runs.
   **Then** the teardown fails with the call, the status, and the body, and the site release still runs.

### User Story 2 (P1): A module check names each live run that a module leaves

A later module meets a leftover run as a 409, and it can use that run in place of its own run.
A check after each module must find each live run that the module left.

**Independent test**: Run `test_capture.py` alone with the old teardown, and read the teardown error.

**Acceptance scenarios**:

1. **Given** a module that leaves a live run on a site of the picker.
   **When** the module ends.
   **Then** the check fails the module, and the message names the run, its state, and its site.
2. **Given** a run that was live before the module started.
   **When** the module ends.
   **Then** the check does not blame the module for that run.
3. **Given** a full browser run.
   **When** the run ends.
   **Then** the terminal summary states the count of modules, history rows, sites, and leaked live runs.

### User Story 3 (P2): The refusal test proves its own claim

**Independent test**: Run the refusal test alone, and then run it after the walk.

**Acceptance scenarios**:

1. **Given** a site with no live run.
   **When** the refusal test sends its first create call.
   **Then** the call must answer 201, and the ledger records the run.
2. **Given** the second create call answers 409.
   **When** the test reads the link of the refusal.
   **Then** the link names the run that the test built.

### User Story 4 (P2): Direct tests prove each decision

The fault shows only in some orders of the browser run.
Direct tests must prove each decision with no browser and no network.

**Acceptance scenarios**:

1. **Given** a history row in each state of the run model and a row with an unknown state.
   **When** the check reads the row.
   **Then** the check agrees with the portal helper `run_is_live` for each row.
2. **Given** an answer that the check cannot read.
   **When** the check reads it.
   **Then** the check fails, and the message names the call.
3. **Given** a ledger with a live run and a final run.
   **When** the teardown ends the runs of the ledger.
   **Then** the live run gets one cancel, and the final run gets no cancel.

## Requirements

### Functional Requirements

- **FR-001**: The walk and the refusal test must record each run key in a run ledger.
- **FR-002**: The teardown of `walking_page` must end each live run of the ledger before it releases the site. A refused cancel must fail the teardown. The site release must still run.
- **FR-003**: The refusal test must require 201 for its first create call. A 503 may still report a skip. The test must check that the refusal names its own run.
- **FR-004**: After each browser module, a check must read the run history of each site of the picker. It must compare the live runs with the scan before the module. Each new live run must fail the module.
- **FR-005**: The live rule of the check must agree with the portal helper `run_is_live`. A row with an unknown state or a final state is not live.
- **FR-006**: The check must read each page of the history. It must stop at a bound, so a wrong answer cannot start an endless read.
- **FR-007**: The check must fail on four answers. These answers are a refusal, an unreachable portal, a body that is not a JSON object, and a body with no run list. The message must name the call.
- **FR-008**: The terminal summary must print one line for the check. A record file must hold one line for each module.
- **FR-009**: If the measurement finds another module that leaves a live run, that module must end its run with the ledger of #3497.
- **FR-010**: The change must not touch `src/`.

### Key Entities

- **Live run**: one run that the portal still counts as live, with its site, its key, and its state.
- **Module check**: the live runs before and after one module, and the count of rows and sites that the scan read.

## Success Criteria

- **SC-001**: In a run of `test_capture.py` and `test_existing.py` together, each create call of `test_existing.py` answers 201.
- **SC-002**: With the old teardown, the check fails `test_capture.py` and names the run of the walk.
- **SC-003**: A full browser run of `tests/e2e/upgrade_portal` gives 316 passed and 1 skipped (#3380). The check reports 0 leaked live runs.
- **SC-004**: The scans of the check add less than 10 seconds to a full browser run.

## Assumptions

- The picker of the default organization lists five sites. Each browser journey that builds a single-site run chooses one of them.
- A multi-site operation record holds `site_ids` and no top-level `site_id`. So the refusal helper `live_run_at_site` never reads an operation record.
- The history route is free of the site lock (FR-032). A read of that route changes no lock and no run.
