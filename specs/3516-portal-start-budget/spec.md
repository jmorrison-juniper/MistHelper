# Feature Specification: Give the browser portal a robust start budget

**Issue**: #3516
**Feature Branch**: `jmorrison-juniper-reassess-3516`
**Status**: Approved

## Problem

The browser fixture waits 10 seconds for the capture portal child process.
A loaded workstation needed 12.2 seconds to import the portal and open its
loopback port. The fixture then stopped a healthy child and reported a setup
failure for each test in the module.

The wait also ignores the child process state. A child that stops during an
import cannot open the port, but the fixture still waits for the full budget.

## User scenarios and testing

### User story 1: A slow portal can finish its start

A maintainer runs the browser tests on a loaded workstation.

**Acceptance scenario**:

1. **Given** a portal that needs 12 seconds to open its port.
   **When** the fixture waits for the portal.
   **Then** the default budget permits the start.

### User story 2: A stopped child fails without a delay

A portal child stops before it opens its port.

**Acceptance scenario**:

1. **Given** a child that returns an exit code.
   **When** the fixture checks the child state.
   **Then** the fixture stops the wait and reports the exit code.

### User story 3: A hung child keeps a finite bound

A portal child stays live but never opens its port.

**Acceptance scenario**:

1. **Given** a live child that never answers.
   **When** the start budget ends.
   **Then** the fixture stops the child and reports the measured wait.

## Requirements

- **FR-001**: The default start budget is 60 seconds.
- **FR-002**: `UPGRADE_PORTAL_E2E_READY_SECONDS` continues to override the budget.
- **FR-003**: The fixture checks the child state after each failed port probe.
- **FR-004**: An early child exit reports the exit code and measured seconds.
- **FR-005**: A ready portal reports the measured startup time in the debug log.
- **FR-006**: The focused tests bind no port and start no process.

## Success criteria

- A 12.2-second start fits inside the default budget.
- An early child exit needs no readiness pause.
- A child that never answers uses a finite number of probes and pauses.

## Out of scope

- Production upgrade routes and portal behavior.
- Mist API calls and production credentials.
- Browser journey behavior after the portal starts.
