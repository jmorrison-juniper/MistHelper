# Feature Specification: Each test keeps its site lock actions out of the checkout trail

**Issue**: #3503
**Feature Branch**: `fix/3503-test-site-lock-trail`
**Status**: Draft
**Found by**: the research of #3498

## Problem

The site lock module writes each lock action to one append-only trail.
The trail is `data/upgrade_takeover_audit.jsonl` in the checkout.
In the main checkout, that file is the production audit trail, and the production container mounts it.

The unit tests and the contract tests of the upgrade portal take and release site locks.
Each lock action goes to the checkout trail.
Issue #3498 moved the trail of the browser tests only.

One run of the unit, contract, and guardrail suites wrote 131 lines to the trail of a fresh worktree.
The production trail holds 3071 lines.
Tests wrote 3031 of those lines.
Real operators wrote 40 lines.

The Audit log card of the production portal reads this trail.
An operator who reads the card cannot find the lock actions of real operators.

Four tests move the trail before they write.
Every other test that takes or releases a site lock writes to the checkout trail.
A change of the working directory does not move the trail, because the lock module anchors the relative directory `data` against the checkout.

No gate counts the checkout trail after a unit run, so the leak stays hidden.

## User Scenarios & Testing

### User Story 1 (P1): Each test writes its lock actions to its own trail

A maintainer runs the unit suite in any checkout.
The production audit trail must not change.

**Independent test**: Run the unit, contract, and integration suites in a fresh worktree.
Count the lines of the checkout trail after the run.

**Acceptance scenarios**:

1. **Given** a test that takes and releases a site lock.
   **When** the test runs.
   **Then** each lock action goes to a trail inside the temporary directory of that test.
   The checkout trail keeps its count.
2. **Given** two tests that each take a site lock.
   **When** both tests run.
   **Then** each trail holds the lock actions of its own test only.
3. **Given** a test that sets its own trail directory.
   **When** the test runs.
   **Then** the lock actions go to the directory that the test set.
4. **Given** a new test file in any folder of the test tree.
   **When** the file runs.
   **Then** its lock actions stay out of the checkout trail with no action from the author.

### User Story 2 (P1): A session guard fails a run that writes the checkout trail

A maintainer who reads a green run must know that no test wrote to the checkout trail.

**Independent test**: Read the terminal summary of a test session.
Write one line to a stand-in checkout trail between the two counts of the guard.

**Acceptance scenarios**:

1. **Given** a test session that ran at least one test.
   **When** the session ends.
   **Then** the terminal summary states that the guard checked 1 trail.
   The summary names the path of the trail and the counts before and after the session.
2. **Given** a test session in which a test wrote to the checkout trail.
   **When** the session ends.
   **Then** the run fails.
   The failure message names the path, the two counts, and the repair.
3. **Given** a checkout with no trail file.
   **When** the guard counts the trail.
   **Then** the count is 0.
4. **Given** a trail path that the guard cannot read.
   **When** the guard counts the trail.
   **Then** the run fails, and the guard never reports 0.

### User Story 3 (P2): Direct tests prove the guard decision

A maintainer must see the guard fail without a real leak.

**Independent test**: Run the direct tests of the guard with no network and no production file.

**Acceptance scenarios**:

1. **Given** a stand-in checkout trail with equal counts before and after.
   **When** the guard decides.
   **Then** the guard passes, and its measure names the path and the counts.
2. **Given** a stand-in checkout trail that gains one line between the counts.
   **When** the guard decides.
   **Then** the guard fails with the measure and the repair.
3. **Given** a test that runs under the move.
   **When** the test asks the lock module for the trail path.
   **Then** the path is inside the temporary directory of that test.
   A lock action reaches that path.

### Edge Cases

- The browser suite keeps its own isolation from #3498.
  Its child process moves its own trail, and its parent counts the checkout trail around the portal.
  The new guard counts the same checkout trail, so a browser run reports two guard lines.
- The production container writes the trail of the main checkout.
  A real lock action during a test session in the main checkout fails the new guard.
  The repair text tells the maintainer to run the tests in a worktree.
- A fixture with module scope or session scope runs before the move of a test.
  A lock action from such a fixture goes to the checkout trail, and the guard fails the run.
- A thread that outlives its test can write after the move ends.
  That write goes to the checkout trail, and the guard fails the run.
- A test session that collects no test starts no guard, and it prints no guard line.
- The lock module cannot import, for example when a package of the portal is absent.
  Then no test can write a site lock action.
  The guard skips, and the terminal summary names the reason and the missing capability.
- The change deletes no line from any trail.
  The owner decides about the 3031 test lines in the production trail.

## Requirements

### Functional Requirements

- **FR-001**: Before each test, the harness points the site lock trail at a directory inside the temporary directory of that test.
  After the test, the harness restores the earlier directory.
- **FR-002**: The move applies to each test that the test tree collects.
  A new test file needs no action.
- **FR-003**: A test that sets its own trail directory keeps that directory.
- **FR-004**: A session guard counts the lines of the checkout trail before the first test and after the last test.
  A changed count fails the run.
- **FR-005**: The guard states what it checked in the terminal summary of each session that ran a test.
  The statement names 1 trail, the path, and the two counts.
- **FR-006**: An absent trail counts 0.
  A trail that the guard cannot read fails the run.
- **FR-007**: The failure message names the path, the two counts, and the repair.
  The repair names the production container as a second cause.
- **FR-008**: Direct tests with no network prove the count, the decision, and the move.
- **FR-009**: The change adds no portal code and deletes no trail line.
- **FR-010**: The browser suite guard of #3498 stays unchanged.
- **FR-011**: If the lock module cannot import, the guard skips.
  The terminal summary names the error of the import and the capability that the session lacks.

### Key Entities

- **Checkout trail**: The file `data/upgrade_takeover_audit.jsonl` below the checkout root.
  In the main checkout, it is the production audit trail.
- **Test trail**: The trail of one test, inside the temporary directory of that test.
- **Session guard**: The check that counts the checkout trail before and after one test session.
- **Measure**: The one sentence that states what the guard checked.

## Success Criteria

### Measurable Outcomes

- **SC-001**: After one run of the unit, contract, and integration suites of the portal in a fresh worktree, the checkout trail holds 0 lines.
  Before the change, the same run leaves more than 0 lines.
- **SC-002**: A direct test that writes one line to a stand-in checkout trail between the two counts fails the guard decision.
- **SC-003**: Each test that passed before the change passes after the change.
- **SC-004**: The terminal summary of each session that ran a test holds exactly one line from the new guard.
- **SC-005**: The move adds less than 1 millisecond to each test.
  The guard adds less than 2 seconds to each session.

## Assumptions

- The tests run in a worktree or in the continuous integration service.
  No production portal writes to the trail of a worktree.
- The lock module keeps its rule that it reads the trail directory at call time.
  The move and the guard both depend on that rule.
- The continuous integration service runs each shard as one session with no parallel workers.
- The Audit log card and its reader stay out of scope.
  Issue #3484 tracks the organization gap of that card.