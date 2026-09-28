# Feature Specification: The two stale seed runs move to a site of their own, so `test_existing.py` passes alone

**Issue**: #3507
**Feature Branch**: `fix/3507-stale-seed-site`
**Status**: Draft
**Found by**: a run of one browser module alone, during the work on #3497

## Problem

The module `tests/e2e/upgrade_portal/test_run_controls/test_existing.py` passes only when `test_bulk.py` runs before it in the same session.
When the module runs alone, it reports 1 failure, 1 error, and 2 skips.

The browser server writes two stale seed runs on the first site of the site picker, `22222222-2222-2222-2222-222222222222`.
This document calls that site "the first site".

| Run | State | Test that uses the run |
| - | - | - |
| `e2e-stale-precloud-0001` | `awaiting_confirmation` | The bulk cancel test of `test_bulk.py` |
| `e2e-stale-stopping-0001` | `stopping` | The reconcile test of `test_bulk.py` |

The portal allows one live run for each site.
A live run is a run that is not in a final state.
Each create call of `test_existing.py` names the first site, so the create call answers 409, and the answer names a stale seed run.
The helper `_create_run` then drives that stale seed run.

1. The first seven tests drive `e2e-stale-precloud-0001`, and the seventh test cancels that run.
2. The next create call names `e2e-stale-stopping-0001`.
3. That run is past the pre-check, so its page holds no schedule region.
4. Two tests skip, one test fails, and one test reports an error.

The default order hides the fault.
Pytest groups the modules by fixture, so `test_bulk.py` runs as module 27 and `test_existing.py` runs as module 43.
The module `test_bulk.py` ends both stale seed runs before `test_existing.py` starts.

A skip hides the fault a second time.
The fixture `scheduled_run_page` reports a skip when the run page holds no schedule region, and pytest counts a skip as a pass.

## User Scenarios & Testing

### User Story 1 (P1): A maintainer runs `test_existing.py` alone

A maintainer runs one module to find a fault.
The module must give the same result alone and in the default order.

**Independent test**: Run `test_run_controls/test_existing.py` alone in Edge.

**Acceptance scenarios**:

1. **Given** a new browser server.
   **When** `test_existing.py` runs alone.
   **Then** each test passes, and no test skips.
2. **Given** a new browser server.
   **When** the whole folder `tests/e2e/upgrade_portal` runs in the default order.
   **Then** each test of `test_existing.py` passes, and no test of that module skips.

### User Story 2 (P1): The bulk tests still find both stale seed runs

The bulk cancel test and the reconcile test need a live stale run.
The move must keep both tests whole.

**Independent test**: Run `test_run_controls/test_bulk.py` alone in Edge.

**Acceptance scenarios**:

1. **Given** the two stale seed runs on their new site.
   **When** the bulk cancel test cancels `e2e-stale-precloud-0001`.
   **Then** the result reads "Succeeded: 1".
2. **Given** the same seed.
   **When** the reconcile test reconciles `e2e-stale-stopping-0001`.
   **Then** the result reads "Succeeded: 1", and a reload shows the state `stopped`.

### User Story 3 (P2): A run page with no schedule region fails and names the run

A skip hid this fault, and pytest counted the skip as a pass.

**Independent test**: Run `test_existing.py` alone before the seed move, and read the setup result of each test.

**Acceptance scenarios**:

1. **Given** a run page that holds no schedule region.
   **When** the fixture `scheduled_run_page` opens that page.
   **Then** the fixture fails, and the message names the run key and the state that the page shows.

### User Story 4 (P2): A direct test guards the seed sites

A future seed can put a live run on a site that the journeys pick.
A direct test must find that seed before any browser run.

**Independent test**: Run the direct tests with no browser and no network.

**Acceptance scenarios**:

1. **Given** each run that the browser server seeds.
   **When** the direct test reads those runs.
   **Then** no live seed run holds a site that the stand-in cloud lists, and the test states the count of runs that it read.
2. **Given** a synthetic list with a live run on a listed site.
   **When** the check reads that list.
   **Then** the check names that run, its state, and its site.
3. **Given** a synthetic list with a final run on a listed site, and a live run on a site that the cloud does not list.
   **When** the check reads that list.
   **Then** the check names no run.

### Edge Cases

- The failed seed run and the stopped seed run stay on the first site.
  Both are in a final state, so the live-run guard ignores them.
  The retry tests need them there, because the retry control reads the lock of the first site.
- A multi-site operation names its sites in the `site_ids` field, and its `site_id` field holds no value.
  The site scan of the live-run guard reads the `site_id` field only.
  So the direct test reads the `site_id` field only.
- A run with an unknown state counts as not live, because the shipped rule `run_is_live` reads it that way.
  The direct test uses the same rule, so it cannot disagree with the portal.
- An earlier module can still leave a live run on the first site.
  The module `test_capture.py` does that today.
  That fault is out of scope, and a separate issue records it.
  The module `test_existing.py` keeps its 409 path for that case.

## Requirements

### Functional Requirements

- **FR-001**: The browser server MUST write the two stale seed runs on a new site, the stale site.
  No other seed run uses the stale site, and the stand-in cloud does not list it.
- **FR-002**: One seed module, `tests/e2e/upgrade_portal/stale_run_seeds.py`, MUST hold the stale site, the two run keys, and the class `StaleRunSeeds`.
  The conftest and `test_bulk.py` MUST import the keys from that module, so no second copy of a key exists.
- **FR-003**: The bulk cancel test and the reconcile test MUST take the lock of the stale site.
- **FR-004**: The fixture `scheduled_run_page` MUST fail when the run page holds no schedule region.
  The message MUST name the run key and the state that the page shows.
- **FR-005**: A direct test MUST read each run that the browser server seeds, through the seed writer of that server.
  The test MUST fail when a live seed run holds a site that the stand-in cloud lists.
  The test MUST use the shipped rule `run_is_live`, and its message MUST state the count of runs that it read.
- **FR-006**: A direct test MUST prove the decision of FR-005 with synthetic lists, with no browser and no network.
- **FR-007**: The seed write MUST log one line before the writes and one line after them.
  The write MUST report False when the store refuses either run.
- **FR-008**: The change MUST NOT change portal code.

### Key Entities

- **Stale seed run**: A seeded run with an old update time and a live state. The bulk tests end each one.
- **Stale site**: The site that holds only the two stale seed runs.
- **First site**: The first row of the site picker. Each journey that reads the first row creates runs there.
- **Listed site**: A site that the stand-in cloud returns for the read `listOrgSites`.

## Success Criteria

### Measurable Outcomes

- **SC-001**: `test_existing.py` alone in Edge gives 11 passed, 0 skipped, 0 failed, and 0 errors.
- **SC-002**: `test_bulk.py` alone in Edge gives 6 passed.
- **SC-003**: The folder `test_run_controls` alone in Edge gives each test a pass, with 0 skips.
- **SC-004**: The whole folder `tests/e2e/upgrade_portal` in Edge gives 316 passed and at most the 1 known skip of #3380.
  Both lock guards report 0 leaks.
- **SC-005**: Before the move, the seed-site test fails and names both stale seed runs on the first site.
  After the move, it passes and states the count of runs that it read.
- **SC-006**: Before the move, `test_existing.py` alone reports 0 skips, because the fixture of FR-004 fails instead.

## Assumptions

- The lock route, the bulk cancel route, and the reconcile route accept a site that the stand-in cloud does not list.
  The bulk retry site and the lifecycle site prove that fact today.
- The history page lists the runs of a site that the stand-in cloud does not list.
  The bulk retry run proves that fact today.
- The change touches tests only, so it needs no deploy, no container action, and no release note.
