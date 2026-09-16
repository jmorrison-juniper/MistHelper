# Feature Specification: Browser upgrade start journey

**Feature Branch**: `fix/2632-browser-upgrade`

**Created**: 2026-09-16

**Status**: Draft

**Input**: GitHub issue #2632 reports that the browser suite does not finish an upgrade start journey.

## User Scenarios & Testing

### User Story 1 - Measure the start path (Priority: P1)

A maintainer runs the browser suite and sees proof that one firmware start journey reached the start route.

**Why this priority**: The start route writes firmware. A green browser suite must measure that route.

**Independent Test**: Run `python -m pytest tests/e2e/upgrade_portal/test_upgrade.py::TestUpgradeStart -q --no-cov`.

**Acceptance Scenarios**:

1. **Given** a prepared upgrade run and a reachable test operator, **When** the browser types `CONFIRM`, **Then** the start button unlocks.
2. **Given** the unlocked start button, **When** the browser clicks it, **Then** `POST /api/runs/<run_id>/start` answers 202.
3. **Given** the accepted start response, **When** the browser follows the script, **Then** the run page shows `upgrade_submitting`.

---

### User Story 2 - Keep reserved addresses safe (Priority: P2)

A maintainer keeps the default browser operator on a reserved domain, but uses a separate fixture for firmware writes.

**Why this priority**: A reserved address must not pass the firmware write guard added by issue #2615.

**Independent Test**: Run the full browser suite and confirm that read-only tests still use the reserved operator.

**Acceptance Scenarios**:

1. **Given** a read-only browser test, **When** it uses the default page fixture, **Then** it keeps `e2e.operator@example.invalid`.
2. **Given** a firmware start test, **When** it needs a reachable operator, **Then** it uses `firmware_operator_page`.

---

### User Story 3 - Bound future hangs (Priority: P3)

A maintainer sees a failure with a stack instead of a browser run that never ends.

**Why this priority**: An unbounded hang blocks all remaining browser evidence.

**Independent Test**: Collect E2E tests and confirm that `pytest-timeout` adds a 120-second mark.

**Acceptance Scenarios**:

1. **Given** the E2E suite and the timeout plug-in, **When** pytest collects tests, **Then** each E2E item receives a 120-second timeout.
2. **Given** the timeout plug-in is absent, **When** pytest collects tests, **Then** the suite skips E2E items with a clear reason.

### Edge Cases

- If the seeded start run is not written yet, the test polls the run page for up to 30 seconds.
- If the start control stays disabled, the test fails and states that the start path was not measured.
- If a future request hangs, the existing E2E timeout stops the item after 120 seconds.

## Requirements

### Functional Requirements

- **FR-001**: The browser suite MUST include one test that clicks the site upgrade start button.
- **FR-002**: The start test MUST use a reachable operator fixture, not the default reserved operator.
- **FR-003**: The default operator fixture MUST remain on `example.invalid` for read-only paths.
- **FR-004**: The start test MUST assert the start response status and the following run page state.
- **FR-005**: The start test MUST use a run that no other browser test mutates.
- **FR-006**: The E2E suite MUST keep a per-test timeout of 120 seconds.

### Key Entities

- **Start-ready run**: A browser-only run record in `awaiting_confirmation` state.
- **Firmware operator page**: A test-only browser page with a reachable operator address.
- **E2E timeout guard**: The pytest collection hook that applies a bounded runtime to each E2E item.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The browser suite finishes with one more passing test than the issue baseline.
- **SC-002**: The browser suite reports no hang when the start path runs.
- **SC-003**: The new start test proves the confirm page, typed word, start call, and run page.
- **SC-004**: Unit and contract tests for the upgrade portal pass after the change.

## Assumptions

- The current branch includes issue #2615, which refuses reserved domains for firmware writes.
- The current branch includes issue #2561, which adds the 120-second E2E timeout guard.
- The current branch includes pull request #2714, which changes stale-run reconciliation.
