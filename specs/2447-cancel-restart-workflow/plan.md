# Implementation Plan: Cancel and Restart an Upgrade Run

## Approach

1. Add a stop-request reader to the phase-gate dependency record.
2. End the blocking settle loop when the stored run receives a stop request.
3. Let the driver consume that signal before it writes a failed phase outcome.
4. Expand retry eligibility to the three unsuccessful terminal states.
5. Carry the new run and site identifiers into the browser navigation.
6. Teach a blank capture page to bind a query-supplied run and teach the verified-capture action to continue that run.
7. Add deterministic contract, unit, and Playwright coverage.

## Safety

The live-state guard remains unchanged. A new run is permitted only after the old run reaches a terminal state. Retry requires the site lock and always requires a fresh pre-check and typed confirmation before firmware submission.

## Validation

- Targeted route and retry contract tests.
- Phase-gate and driver unit tests.
- Deterministic browser tests using the isolated stand-in portal.
- Live Playwright verification in the rebuilt local container without submitting firmware.
