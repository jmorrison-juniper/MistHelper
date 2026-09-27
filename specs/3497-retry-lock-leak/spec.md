# Feature Specification: Each run-control browser test frees its site, and the two-operator fixture fails on a refusal

**Issue**: #3497
**Feature Branch**: `fix/3497-retry-lock-leak`
**Status**: Draft
**Found by**: the full browser run on the branch of #3492

## Problem

The browser tests of the run controls build runs on the stand-in site `22222222-2222-2222-2222-222222222222`.
The create call of a run takes the site lock for the browser of the test.
No test of `tests/e2e/upgrade_portal/test_run_controls/test_existing.py` releases that lock.
The two retry tests also leave a new run in the state `created`.

The two-operator tests run later in the same session.
Their fixture `held_site` takes the lock of the same site with the same operator identity.

- If the lock stays quiet for less than 300 seconds, the take answers `resume`.
  The fixture then holds a lock that an earlier test took, and no test sees the leak.
- If the lock stays quiet for more than 300 seconds, the take answers 400 `confirmation_required`.
  The fixture then skips its test.

A full local run reported 18 skips in `test_two_operators.py`, and no test failed.
Pytest counts a skip as a pass, so 18 checks of site isolation did not run in a green run.

The fixture `held_site` skips on each status other than 200.
Its comment names 503 as the only expected refusal, but its code skips on 400 and 409 too.

## User Scenarios & Testing

### User Story 1 (P1): Each run-control test frees the site at the end

A maintainer runs the browser suite.
Each test of the run controls must leave the stand-in site as it found the site.

**Independent test**: Run the retry module, then wait 310 seconds, then run the two-operator module in one session.
Count the skips and the failures of the two-operator module.

**Acceptance scenarios**:

1. **Given** a test that built a run which is not final.
   **When** the test ends.
   **Then** the teardown cancels that run.
2. **Given** a test that built a run which is already final.
   **When** the test ends.
   **Then** the teardown sends no cancel for that run.
3. **Given** a test that held the site lock.
   **When** the test ends.
   **Then** the teardown releases the lock.
   The next take of the site by the same operator answers `acquired`.
4. **Given** a teardown that cannot cancel a run or cannot release the lock.
   **When** the teardown runs.
   **Then** the teardown fails, and the message names the path, the status, and the refusal body.
5. **Given** a test that pushes Retry.
   **When** the portal builds the retry run.
   **Then** the test records the key of the retry run, and the teardown cancels that run.

### User Story 2 (P1): The two-operator fixture fails on a refusal

A maintainer who reads a green run must know that each two-operator test ran.

**Independent test**: Run the direct tests of the fixture decision with no network.

**Acceptance scenarios**:

1. **Given** a take that answers 200 with the state `acquired`.
   **When** the fixture decides.
   **Then** the fixture holds the lock and gives the test the site.
2. **Given** a take that answers 400 or 409.
   **When** the fixture decides.
   **Then** the test fails, and the message names the status and the refusal body.
3. **Given** a take that answers 503.
   **When** the fixture decides.
   **Then** the test skips, and the reason names the lock store.
4. **Given** a take that answers 401 or 404.
   **When** the fixture decides.
   **Then** the test fails, and the message names the lock route, as before this change.
5. **Given** a take that answers 200 with the state `resume`.
   **When** the fixture decides.
   **Then** the test fails.
   The message states that an earlier test left the lock of this site.
6. **Given** a take that answers any other status.
   **When** the fixture decides.
   **Then** the test fails, and the message names the status and the body.

### User Story 3 (P2): Direct tests prove each decision

A maintainer must see each decision fail without a browser and without a real leak.

**Independent test**: Run the direct tests with no network, no browser, and no portal.

**Acceptance scenarios**:

1. **Given** a stand-in request source that answers a live state and then a successful cancel.
   **When** the teardown ends the runs.
   **Then** the teardown sends one cancel for the run.
2. **Given** a stand-in request source that answers a refused cancel.
   **When** the teardown ends the runs.
   **Then** the teardown fails with the refusal body.
3. **Given** a stand-in request source that refuses the take or the release.
   **When** the teardown frees the site.
   **Then** the teardown fails with the refusal body.

### Edge Cases

- A test skips after its fixture built a run.
  The teardown still runs, so the teardown still cancels the run and releases the lock.
- A test fails after its fixture built a run.
  The teardown still runs, and pytest reports the failure of the test and any error of the teardown apart.
- The create call names a live run that this test did not build.
  The test drives that run, as before this change, and the teardown does not cancel it.
- The page of the test sits on a page that holds no token for the cross-site request check.
  The teardown opens the site picker first, so it reads a fresh token and the site key.
- The status route answers 404 for a run that the store no longer holds.
  The teardown then has no run to end, and it moves on.
- A module outside the run controls can leave the lock of the site.
  The fixture `held_site` then fails with the state `resume`, and the message names the leak.
- The browser binary is absent.
  The page fixture skips before the teardown exists, so no teardown runs.

## Requirements

### Functional Requirements

- **FR-001**: Each test of `test_existing.py` records the key of each run that it built.
  A built run is a run that the create call answered with 201, or a retry run.
- **FR-002**: After each test of `test_existing.py`, a teardown reads the state of each recorded run.
  If the state is not final, the teardown cancels the run.
- **FR-003**: After it ends the runs, the teardown takes the site lock with the word `continue`, and then it releases the lock.
- **FR-004**: The teardown fails when a status read, a cancel, a take, or a release answers a refusal.
  The message names the path, the status, and the body.
- **FR-005**: The fixture `held_site` fails on each status other than 200 and 503.
  The message names the status and the body.
  A 401 and a 404 keep their message that names the lock route.
- **FR-006**: The fixture `held_site` skips on 503 only.
  The reason names the lock store.
- **FR-007**: The fixture `held_site` fails when the take answers the state `resume`.
  The message states that an earlier test left the lock of the site.
- **FR-008**: Direct tests with no network prove each decision of FR-002 through FR-007.
- **FR-009**: The change adds no portal code.
  The change touches no file under `src/`.
- **FR-010**: The final states come from the run model of the portal.
  The tests do not copy the list of state names.

### Key Entities

- **Run ledger**: The list of run keys that one test built.
- **Site release**: The teardown that ends each live run of the ledger and then frees the site lock.
- **Lock take decision**: The rule that turns one answer of the lock take into a held lock, a skip, or a failure.
- **Final state**: A run state from which the run model allows no move.
  The run model names `complete`, `stopped`, `failed`, and `cancelled`.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The repro sequence reports 0 skips and 0 failures in `test_two_operators.py`.
  The sequence runs `test_bulk.py`, `test_existing.py`, a wait of 310 seconds, and `test_two_operators.py` in one session.
  Before the change, the same sequence reports 18 skips.
- **SC-002**: A full run of `tests/e2e/upgrade_portal` in Edge reports 0 skips in `test_two_operators.py`.
  The one known skip of #3380 stays.
- **SC-003**: Each direct test of a refusal fails the decision, and each direct test of a success passes it.
- **SC-004**: After `test_existing.py`, the trail of the run holds one release for each take of the stand-in site by the first operator.
- **SC-005**: The teardown adds less than 1 second to each test of `test_existing.py` on average.

## Assumptions

- The portal keeps one live run for each site.
  A new create call on a site with a live run answers 409 and names that run.
- The lock take with the word `continue` answers 200 for the operator that holds the site, or for a free site.
- The release route reads the lock record from the session of the browser.
  The teardown therefore takes the lock in the same browser context before it releases the lock.
- The browser suite runs in one session with no parallel workers.
- The other modules that take the lock of the stand-in site release it.
  The experiment in `research.md` checks this assumption.
