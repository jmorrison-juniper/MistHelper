# Feature Specification: Each browser test frees each site lock that it took, and the run fails when a lock stays

**Issue**: #3508
**Feature Branch**: `fix/3508-browser-lock-leaks`
**Status**: Draft
**Found by**: the site lock trail of the full browser run of #3497

## Problem

Two browser tests of the upgrade portal take a site lock and leave it after the test ends.
No later test takes the same site today, so no test fails.

Issue #3497 shows the risk.
A leaked lock of site 2222 hid 18 tests as skips, and pytest counts a skip as a pass.

The full folder `tests/e2e/upgrade_portal` ran in Edge on the branch of #3497.
The site lock trail of the run held 120 lines.
Each site had one release for each take, except two sites.

| Site | Test | Takes | Releases |
| - | - | - | - |
| `66666666-6666-6666-6666-666666666666` | `test_response_loss_recovers_by_read_and_preserves_actor_scope` | 1 | 0 |
| `99999999-0000-0000-0000-000000343903` | `test_the_capture_start_refuses_after_a_lost_page_and_names_the_cause` | 1 | 0 |

The first test takes the lock through the fixture `site_lock`, and then it clears the cookies of the browser.
The page keeps the cross-site request token of the first session, so the release answers 400 `csrf_missing`.
The route also reads the lock record from the signed session, so a release with a new token answers 409 `lock_lost`.
The fixture logs a warning and continues, so no report shows the leak.

The second test takes the lock through the lock control of the capture page, and no step releases the lock.
When a lock already holds the site, the step types the takeover word.
That step would therefore also hide a lock that an earlier test left.

## User Scenarios & Testing

### User Story 1 (P1): The lock fixture of the run controls frees each lock, or fails

A maintainer runs the browser suite.
Each test that takes a lock through the fixture `site_lock` must leave the site free.

**Independent test**: Run `test_run_controls/test_isolation.py` in Edge, and read the teardown result of each test.

**Acceptance scenarios**:

1. **Given** a test that took a lock through the fixture.
   **When** the test ends.
   **Then** the teardown releases the lock, and the release answers 200 with `released` true.
2. **Given** a release that answers a refusal.
   **When** the teardown runs.
   **Then** the teardown fails, and the message names the path, the status, and the body.
3. **Given** a release that answers 200 with a body that is not a JSON object, or with `released` not true.
   **When** the teardown runs.
   **Then** the teardown fails, and the message names the path, the status, and the body.
4. **Given** a release call that cannot run, because the page closed.
   **When** the teardown runs.
   **Then** the teardown fails, and the message names the cause.
5. **Given** a test that released a lock through the fixture before the test ended.
   **When** the test ends.
   **Then** the teardown sends no second release for that lock.
6. **Given** the test of the lost action answer.
   **When** the test has read the result of the action.
   **Then** the test releases the lock before it clears the cookies of the browser.

### User Story 2 (P1): The capture start test of the later site checks frees its site

A maintainer runs the later site checks.
The capture start test must leave the site West free.

**Independent test**: Run `test_later_site_checks.py` in Edge, and read the site lock trail of the run.

**Acceptance scenarios**:

1. **Given** the test took the site West through the lock control.
   **When** the test has checked the refusal.
   **Then** the test presses the release control, and the lock banner shows the site as free.
2. **Given** a site that a lock already holds.
   **When** the step takes the site.
   **Then** the step fails, and the message names the state message of the lock banner.
   The step does not type the takeover word.

### User Story 3 (P1): The browser run fails when a site lock stays

A maintainer who reads a green run must know that no browser test left a site lock.

**Independent test**: Run the direct tests of the trail check with no network, no browser, and no portal.

**Acceptance scenarios**:

1. **Given** a trail where each hold has a later release.
   **When** the check reads the trail after the portal stops.
   **Then** the check passes.
   The terminal summary names the count of records, the count of sites, and 0 held sites.
2. **Given** a trail where a site still holds a lock at the end.
   **When** the check reads the trail.
   **Then** the run fails, and the message names each site and the operator that holds it.
3. **Given** a trail where a take follows an open hold of the same site with no release between them.
   **When** the check reads the trail.
   **Then** the run fails, and the message names the site of the expired hold.
4. **Given** a trail where a takeover closes a hold, and a release follows the takeover.
   **When** the check reads the trail.
   **Then** the check passes.
5. **Given** a trail with a line that is not a JSON object, or a line that names an unknown action.
   **When** the check reads the trail.
   **Then** the run fails, and the message names the line number.
6. **Given** a browser run that wrote no trail.
   **When** the check runs.
   **Then** the check passes, and the summary names 0 records.

### Edge Cases

- A test fails after it took a lock and before its release step.
  The trail check then also names the site of that test.
  The message states that a failed test can leave its lock.
- The same operator takes the same site two times within 300 seconds.
  The second take answers `resume` and writes no trail line, so one release closes the hold.
- A trail row that names no action is a row from before issue #2221.
  The check reads that row as a takeover, as the audit log of the portal does.
- The portal releases a lock when a run reaches `complete`, `stopped`, or `failed`.
  That release writes a `release` line, so the check reads the site as free.
- The checkout trail guard of #3498 fails in the same teardown.
  The terminal summary still prints the measure of both checks.
- A run that starts no portal builds no trail check.

## Requirements

### Functional Requirements

- **FR-001**: The teardown of the fixture `site_lock` fails when a release answers a status other than 200.
  The message names the path, the status, and the body.
- **FR-002**: The teardown fails when a release answers 200 with a body that is not a JSON object, or with `released` not true.
- **FR-003**: The teardown fails when the release call cannot run.
  The message names the site and the cause.
- **FR-004**: The fixture lets a test release one site before the test ends.
  The teardown then sends no release for that site.
- **FR-005**: The test of the lost action answer releases its lock before it clears the cookies.
- **FR-006**: The capture start test of the later site checks releases the site West through the release control.
  The test then proves that the lock banner shows the site as free.
- **FR-007**: The step that takes the site on the capture page fails when the page opens the takeover box.
  The message names the state message of the lock banner.
- **FR-008**: After the test portal stops, a session check replays the site lock trail of the run.
  The check fails when a site ends with a hold, or when a take follows an open hold of the same site.
  The message names each site and the operator of the hold.
- **FR-009**: The check fails when a trail line is not a JSON object.
  The check also fails when a line names an unknown action.
  The message names the line number.
- **FR-010**: The check prints one line in the terminal summary.
  The line names the count of records, the count of sites, and the count of leaked holds.
- **FR-011**: The check reads the action names and the opening actions from the lock modules of the portal.
  The tests do not copy the list of action names.
- **FR-012**: Direct tests with no network prove each decision of FR-001 through FR-004 and FR-008 through FR-010.
- **FR-013**: The change adds no portal code.
  The change touches no file under `src/`.

### Key Entities

- **Lock hold**: The time from a take or a takeover of one site to the next release of that site.
- **Leaked hold**: A hold with no release.
  The check finds one at the end of the trail, or before a later take of the same site.
- **Trail check**: The session check that replays the site lock trail of one browser run.
- **Held site locks**: The record of the fixture `site_lock`, which holds the page, the site, and the token of each lock.

## Success Criteria

### Measurable Outcomes

- **SC-001**: With the trail check alone, a run of `test_run_controls/test_isolation.py` and `test_later_site_checks.py` fails.
  The message names the two sites of the problem.
  After the full change, the same run passes.
- **SC-002**: With the strict release alone, the test of the lost action answer reports a teardown error.
  The message names the lock path, the status 400, and the code `csrf_missing`.
- **SC-003**: A full run of `tests/e2e/upgrade_portal` in Edge passes, with the one known skip of #3380.
  The summary line of the trail check names 0 leaked holds.
- **SC-004**: Each direct test passes.
- **SC-005**: The trail check adds less than 1 second to a full browser run.

## Assumptions

- The trail holds the actions `take`, `release`, and `takeover`.
  The audit log of the portal infers each expiry, and no writer records one.
- The trail records a take only for a fresh hold.
- The browser suite runs in one session with no parallel workers.
- The browser tests that take a lock and are not named above release it.
  The trail of the full run of #3497 proves this assumption.
