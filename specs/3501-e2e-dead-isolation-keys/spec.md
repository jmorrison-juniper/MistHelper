# Feature Specification: Each isolation check of the browser test portal can fail

**Issue**: #3501
**Feature Branch**: `fix/3501-e2e-dead-isolation-keys`
**Status**: Draft
**Found by**: the research of #3498

## Problem

The browser test portal installs eight configuration values that no portal
code reads. Four of them are traps for the Mist connector, the ArangoDB connector,
the Redis connector, and the portal record files. No code calls a trap, so
each trap counter always reads 0.

Each response of the test portal carries the four trap counters and three
persistence counters. The portal sets each persistence counter to the fixed
text "0". The browser tests assert the zeros in each page fixture and in two
isolation tests. A session guard also compares the three persistence
counters before and after the run. No one of these checks can fail.

Issue #3498 shows a real leak that these checks did not see. The test portal
wrote 909 lock actions to the production audit trail, and every counter read
0.

The other three dead values are the access store, the audit store, and the
audit reader. The lock module writes its audit rows to a file. The review
route finds its audit reader on a module, not in the configuration. The
audit store therefore holds no row.

The eighth dead value is the run key. The factory reads the run from the
dependency set itself, so no code reads the key.

A reader of a green run trusts seven counters that measure nothing.

## User Scenarios & Testing

### User Story 1 (P1): Each isolation check of the browser suite can fail

A maintainer who reads a green browser run trusts only the checks that can
fail.

**Independent test**: Search the portal source and the test tree for each
removed name. Run the browser suite.

**Acceptance scenarios**:

1. **Given** the portal source and the test tree. **When** a maintainer
   searches for the eight removed configuration keys and the seven removed
   header names. **Then** the search finds 0 matches.
2. **Given** a response of the test portal. **When** a test reads its
   headers. **Then** the response holds the run owner header and no other
   test header.
3. **Given** the browser suite. **When** it runs. **Then** each test that
   passed before the change passes after the change.

### User Story 2 (P1): Each browser test still refuses a portal of another run

A browser test must refuse a stray portal that answers on the same address.
The records of that portal are not the records of this run.

**Independent test**: Call the owner check with no browser and no network.

**Acceptance scenarios**:

1. **Given** headers that name this run. **When** the check runs. **Then**
   the check passes.
2. **Given** headers that name another run. **When** the check runs.
   **Then** the check fails. The message names the header, the found run,
   and the expected run.
3. **Given** headers with no run owner header. **When** the check runs.
   **Then** the check fails. The message names the header and states that
   a portal of another run answered.
4. **Given** a header name in capital letters or in small letters. **When**
   the check runs. **Then** the check reads the header.
5. **Given** an empty expected run. **When** a test builds the check.
   **Then** the build fails.

### User Story 3 (P2): The isolation tests name the real isolation

A maintainer who reads an isolation test learns the real method of
isolation.

**Independent test**: Read the docstring of each isolation test module. Run
the direct tests of the child environment and of the validation.

**Acceptance scenarios**:

1. **Given** each isolation test module. **When** a maintainer reads its
   docstring. **Then** the docstring names the real methods. These are the
   unreachable store addresses, the stand-in cloud sessions, the stores of
   the test process, and the trail guard of #3498.
2. **Given** a parent environment with production values. **When** the
   harness builds the child environment. **Then** the store addresses point
   at port 1 of the loopback address, and no production value remains.
3. **Given** a dependency set with one missing value. **When** the factory
   validates it. **Then** the validation fails and names the missing field.
   No route registers.

### Edge Cases

- A future portal change can add a real reader for a connector key. That
  change must then add a trap and a test that proves a call changes the
  counter. The removal does not block that change.
- A test that replaces a route answer with `page.route` sends the run owner
  header only. The replacement in the viewport test sends the four trap
  headers today, and the change removes them.
- The production portal builds no test value, and it sends no test header.
  The contract test of the header proves it.
- The capture store stays, because the stand-in capture runner writes each
  capture through it.
- The session guard of #3498 stays. It is the check that measures the audit
  trail.
- The removed session guard wrote the record `persistent-store-baselines.json`
  in the artifact directory. No tool reads that record.
- The change moves lines in a test file that holds five accepted findings of
  the test quality ratchet. The ratchet matches a finding by its line, so the
  change repairs the five findings instead of moving them.

## Requirements

### Functional Requirements

- **FR-001**: The test dependency set holds no value that no portal code
  reads. The change removes the four trap values, the access store, the
  audit store, and the audit reader, with their configuration keys. It also
  removes the run key, because the factory reads the run from the dependency
  set.
- **FR-002**: The test dependency set keeps the capture store.
- **FR-003**: Each response of the test portal carries the run owner header.
  It carries no trap counter and no persistence counter.
- **FR-004**: The harness holds no trap class, no audit record store, and no
  session guard that compares fixed values.
- **FR-005**: One support class checks the run owner header of a response.
  If the header is absent or names another run, the check fails. The message
  names the header, the found value, and the expected value.
- **FR-006**: Direct tests with no browser and no network prove FR-005. They
  cover a correct run, a wrong run, an absent header, two letter cases of the
  header name, and an empty expected run.
- **FR-007**: The validation of the dependency set still fails closed. A
  direct test removes one kept value and reads the name of its field in the
  failure.
- **FR-008**: The docstring of each isolation test module names the real
  isolation.
- **FR-009**: The production portal keeps its behavior. The change touches
  only the test values under `src/` and the test branch of the factory.
- **FR-010**: The direct tests of FR-006 prove that the owner check can fail.
  The pull request names them.

## Success Criteria

- **SC-001**: The search covers `src/`, `tests/`, and `wsgi_capture.py`. It
  finds 0 of the 8 removed configuration keys and 0 of the 7 removed header
  names. It also finds 0 of the 5 removed class names.
- **SC-002**: Each of the 6 direct cases of the owner check gives the
  expected result.
- **SC-003**: A response of the test portal holds exactly 1 header whose name
  starts with `X-MistHelper-E2E-`.
- **SC-004**: Each browser test that passed before the change passes after
  the change.
- **SC-005**: The test quality ratchet reports 0 new findings for each
  changed test file.

## Assumptions

- No portal code reads the eight removed keys. A search of `src/` and
  `wsgi_capture.py` found each key in `models.py` only.
- The test branch of the factory runs only when a caller passes a dependency
  set. The production entry point passes none.
- The production container runs the same two files under `src/`. A copy of
  the two files after the merge keeps the container equal to `main`.

## Out of Scope

- The unit tests and the contract tests that write to the checkout audit
  trail. Issue #3503 holds them.
- The test lines in the production audit trail. Their removal needs the
  approval of the owner.
- A guard for other file writes of the test portal under `data/`.