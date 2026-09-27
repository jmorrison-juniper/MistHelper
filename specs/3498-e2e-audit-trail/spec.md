# Feature Specification: The browser test portal keeps its lock audit trail inside its own run

**Issue**: #3498
**Feature Branch**: `fix/3498-e2e-audit-trail`
**Status**: Draft
**Found by**: the browser journey of #3492

## Problem

The browser test portal writes each site lock action to
`data/upgrade_takeover_audit.jsonl` in the checkout. In the main checkout,
that file is the production audit trail. The production container mounts the
same `data/` folder. A browser run from the main checkout therefore adds test
records to the production audit trail. The production trail holds 3071
lines, and 909 of them come from browser tests.

In a worktree, the file stays between two test sessions. The Audit log card
of a new session then shows the records of an earlier session.

No gate reported the leak. The session guard of the browser suite compares
three header values before and after the run. The portal sets each of those
values to the fixed text "0", so the guard compares 0 with 0 and cannot fail.

## User Scenarios & Testing

### User Story 1 (P1): The production audit trail holds no test record

The operator who reads the Audit log card of the production portal sees only
the lock actions of real operators.

**Independent test**: Count the lines of the checkout trail. Run the browser
suite. Count the lines again.

**Acceptance scenarios**:

1. **Given** a checkout trail with N lines. **When** a browser run takes and
   releases site locks. **Then** the checkout trail still holds N lines.
2. **Given** the same run. **When** the run ends. **Then** the trail inside
   the artifact directory of the run holds each lock action of the run.

### User Story 2 (P1): Each browser run reads only its own lock actions

A test author who opens the Audit log card of the test portal reads the lock
actions of the current run only.

**Independent test**: The operator opens the capture page of a site that no
other journey uses. The operator takes the site and releases it. The
operator then opens the history of that site and the history with no site.

**Acceptance scenarios**:

1. **Given** a site that no other journey uses. **When** the operator
   presses the take control and then the release control. **Then** the
   banner reads `held` and then `free`.
2. **Given** the same site. **When** the operator opens the history of the
   site. **Then** the Audit log card shows exactly two rows. Row 1 reads
   `release`, and row 2 reads `take`.
3. **Given** the same rows. **When** the operator reads the Operator column.
   **Then** each cell shows a one-way digest, and no cell shows the work
   address of the operator.
4. **Given** the history with no site. **When** the operator reads the Audit
   log card. **Then** the card holds the two rows of the site.

### User Story 3 (P1): The guard measures the checkout trail and can fail

A maintainer who reads the test report sees the path of the checkout trail
and its two line counts. A browser run that writes to the checkout trail
fails.

**Independent test**: Call the guard decision with no browser and no
network. Write one line between the two counts.

**Acceptance scenarios**:

1. **Given** two equal counts. **When** the guard decides. **Then** the guard
   passes and reports the path and the two counts.
2. **Given** a count that grew by one line. **When** the guard decides.
   **Then** the guard fails with a message that names the path, the two
   counts, and the repair.
3. **Given** an absent trail. **When** the guard counts. **Then** the count
   is 0.
4. **Given** a trail that the guard cannot read. **When** the guard counts.
   **Then** the guard fails. It does not report a pass or a skip.
5. **Given** the code of today with no placement. **When** a browser test
   takes and releases a lock. **Then** the guard fails. The pull request
   links this red result.

### Edge Cases

- A take by the operator who already holds the site answers `resume` and
  writes no take row. The journey uses a site that no other journey takes,
  so the take is always a fresh take.
- The production container writes the trail of the main checkout. A lock
  action of a real operator during a browser run in the main checkout also
  changes the count, so the guard fails. Run the browser suite in a worktree.
- The history with no site reads the trail of every organization. Issue
  #3484 holds that gap. The journey reads exact rows on the page of one site
  only.
- The old lines in the trail of a worktree stay. The change deletes no line
  from any trail.
- The placement must happen before the portal registers a route. A route
  that wrote a line before the placement would still reach the checkout
  trail.
- A future change of the lock module can stop the reading of the directory
  at call time. The placement then checks the path that the lock module
  reports, and it stops the test portal when the path is wrong.

## Requirements

### Functional Requirements

- **FR-001**: The test portal writes each site lock action to a trail inside
  the artifact directory of its own run.
- **FR-002**: The Audit log card of the test portal reads the same trail.
- **FR-003**: The placement refuses a run trail that is the checkout trail.
  It also refuses a lock module that reports a different path after the
  placement.
- **FR-004**: The production portal keeps the trail path of today. The change
  touches no file under `src/`.
- **FR-005**: A session guard counts the lines of the checkout trail before
  the test portal starts and after it stops. A changed count fails the run.
  The failure message names the path, the two counts, and the repair.
- **FR-006**: An absent trail counts 0. A trail that the guard cannot read
  fails the run.
- **FR-007**: The guard reports the path, the two counts, and the line count
  of the run trail in the terminal summary. It writes the same values to a
  JSON record in the artifact directory.
- **FR-008**: Direct tests with no browser and no network prove FR-003,
  FR-005, and FR-006.
- **FR-009**: A browser journey proves FR-001 and FR-002 through the pages.
  It saves one screenshot for each state, and the author reads each one.
- **FR-010**: The pull request links a red run of the guard on the code of
  today.

## Success Criteria

- **SC-001**: A complete browser run adds 0 lines to the checkout trail.
- **SC-002**: The Audit log card of the journey site shows exactly 2 rows,
  in the order release, take.
- **SC-003**: Each run reports 1 checked trail and its 2 counts. Each of the
  4 direct guard cases gives the expected result.
- **SC-004**: Each browser test that passed before the change passes after
  the change.

## Assumptions

- The lock module reads its audit directory at call time. The docstring of
  that function names this seam for tests.
- One browser run starts one test portal. The parent process and the child
  process share one artifact directory.
- No production process writes the trail of a worktree.

## Out of Scope

- The 909 test lines in the production trail. Their removal needs the
  approval of the owner, because the trail is an append-only audit record.
- The missing organization filter of the Audit log card. Issue #3484 holds
  it.
- The dead test keys, the trap counters, and the three fixed persistence
  headers. Issue #3501 holds them.