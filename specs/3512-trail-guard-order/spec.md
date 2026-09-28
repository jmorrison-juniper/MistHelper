# Feature Specification: The browser trail guard reads the checkout trail from the root guard

**Issue**: #3512
**Feature Branch**: `fix/3512-trail-guard-order`
**Status**: Draft
**Found by**: a run of `test_existing.py` alone, during the work on #3507

## Problem

Two guards count the checkout trail during a browser run.
The checkout trail is the file `data/upgrade_takeover_audit.jsonl` in the checkout.
In the main checkout, that file is the production audit trail.

| Guard | Issue | Fixture | Source of the path |
| - | - | - | - |
| The root guard | #3503 | `checkout_site_lock_trail_guard` in `tests/conftest.py` | The lock module, before the first test starts |
| The browser guard | #3498 | `checkout_audit_trail_guard` in `tests/e2e/upgrade_portal/conftest.py` | The lock module, when the test portal starts |

The root fixture `isolate_site_lock_trail` moves the trail of each test into the temporary folder of that test.
The browser guard reads its path from the lock module when pytest starts the guard.
If the test portal starts inside the first test, the move of that test already applies.
The browser guard then counts the moved trail of that test, and not the checkout trail.

Eleven browser modules start the test portal through `request.getfixturevalue`.
If one of those modules runs first, the browser guard counts the wrong trail.
A run of `test_existing.py` alone printed this line.

```text
Checkout audit trail guard (issue #3498): checked 1 trail, <basetemp>\test_the_run_page_holds_the_re0\site-lock-trail\upgrade_takeover_audit.jsonl.
```

In that order, the browser guard cannot fail.
Its report line and its record file name a trail that no later test writes.
The journey of the audit log reads the same wrong path for its leak count.

The root guard still counts the checkout trail, so a write to the checkout trail still fails the run.
But in that order, one guard alone protects the production audit trail.

## User Scenarios & Testing

### User Story 1 (P1): A maintainer runs one browser module alone

A maintainer runs one module to find a fault.
The browser guard must count the checkout trail in each order.

**Independent test**: Run `test_run_controls/test_existing.py` alone in Edge, and read the guard line of #3498.

**Acceptance scenarios**:

1. **Given** a new browser run.
   **When** `test_existing.py` runs alone.
   **Then** the guard line of #3498 names `<worktree>\data\upgrade_takeover_audit.jsonl`.
2. **Given** a new browser run.
   **When** `test_capture.py` and `test_existing.py` run together.
   **Then** the guard line of #3498 names the checkout trail.
3. **Given** a new browser run.
   **When** the whole folder `tests/e2e/upgrade_portal` runs in the default order.
   **Then** the guard line of #3498 names the checkout trail, and each test passes.

### User Story 2 (P1): A direct test proves the source of the path

The fault shows only in some orders of the browser run.
A direct test must prove the source of the path with no browser and no network.

**Independent test**: Run the direct tests of the isolation class.

**Acceptance scenarios**:

1. **Given** a test where the move of the root conftest applies.
   **When** the test builds the browser guard.
   **Then** the guard names the trail that the root guard read, and not the moved trail of the test.
2. **Given** no checkout trail value.
   **When** a caller builds the isolation.
   **Then** the build fails, so no default can read a moved trail.
3. **Given** no root guard, because the lock module cannot import.
   **When** a caller builds the browser guard.
   **Then** the build fails, and the message names the lock module.

### User Story 3 (P2): The child process still moves its own trail

The child process of the test portal runs no pytest fixture.
So the lock module reports the checkout trail in the child, before the move of #3498.

**Independent test**: Run the full browser folder, and read the guard line of #3498.

**Acceptance scenarios**:

1. **Given** the child process of the test portal.
   **When** the child builds its isolation.
   **Then** the child names the path of the lock module, and the move of #3498 still applies.
2. **Given** a full browser run.
   **When** the run ends.
   **Then** the trail of the run holds the lock actions, and the checkout trail keeps its line count.

### Edge Cases

- The root guard gives None when the lock module cannot import.
  The browser conftest imports the lock module when pytest loads it, so a browser run cannot reach that case.
  The build still fails with a clear message, and it never reads the lock module in its place.
- A future module can start the test portal late.
  The browser guard no longer depends on the order, so that module needs no change.
- After the change, the root guard and the browser guard count the same file.
  So a browser run prints two guard lines that name one path.
- The child process must not read the root guard, because the child runs outside pytest.

## Requirements

### Functional Requirements

- **FR-001**: The browser guard MUST read the checkout trail from the root guard `checkout_site_lock_trail_guard`.
- **FR-002**: The isolation class MUST need an explicit checkout trail. No default may read the lock module when a caller builds the isolation.
- **FR-003**: The build of the browser guard MUST fail when the root guard is None. The message MUST name the lock module.
- **FR-004**: The child process MUST give the path of the lock module explicitly, before its move.
- **FR-005**: A direct test MUST build the browser guard while the move of the root conftest applies. The test MUST prove that the guard names the trail of the root guard.
- **FR-006**: The docstrings of both guards MUST state the source of the path.
- **FR-007**: The change MUST NOT change the guard line, the record file, or the decision rule of either guard.

### Key Entities

- **The checkout trail**: The file `data/upgrade_takeover_audit.jsonl` in the checkout.
- **The moved trail**: The trail of one test, in the folder `site-lock-trail` of the temporary folder of that test.
- **The run trail**: The trail of one browser run, in the artifact folder of that run.
- **The root guard**: The session guard of #3503. It reads the checkout trail before the first move.
- **The browser guard**: The session guard of #3498. It counts the checkout trail around the test portal.

## Success Criteria

### Measurable Outcomes

- **SC-001**: A run of `test_existing.py` alone in Edge prints a guard line of #3498 that names `<worktree>\data\upgrade_takeover_audit.jsonl`. The same run on the old code names a path in the temporary folder.
- **SC-002**: A run of `test_capture.py` and `test_existing.py` together prints a guard line of #3498 that names the checkout trail.
- **SC-003**: The full browser run gives the result of #3507: 316 tests pass, and 1 test skips for #3380.
- **SC-004**: Each new direct test fails on the old code and passes on the new code.
- **SC-005**: In one browser run, the line of the root guard and the line of the browser guard name the same path.

## Assumptions

- The move fixture of the root conftest depends on the root guard. So pytest starts the root guard before the first move, in each order.
- The change touches test code only. The portal code does not change, so the change needs no deploy and no release note.

## Out of Scope

- The order in which pytest starts the fixtures. The change removes the dependency on that order. It does not change the order.
- The live run that `test_capture.py` leaves on the first site. Issue #3511 holds that fault.
