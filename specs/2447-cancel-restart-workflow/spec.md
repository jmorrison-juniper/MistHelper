# Feature Specification: Cancel and Restart an Upgrade Run

**Branch**: `fix/2447-cancel-restart-workflow`  
**Issue**: #2447  
**Status**: In implementation

## Problem

An operator who stops an upgrade during a settling phase can remain blocked by a `stopping` run for the full 30-minute phase deadline. After the run finally stops, the retry control is absent because retry accepts only `failed`. The existing failed-run retry also creates a run without taking the operator to the required fresh pre-check.

## User Scenarios

### US1 — Stop an in-progress run and start again

An operator stops a run during a device settle phase. The portal observes the stop request within one poll interval, completes the post-check, reaches `stopped`, and releases the site for a new run.

**Acceptance**: The previous run no longer produces `upgrade_already_running` after it reaches `stopped`.

### US2 — Retry a terminal unsuccessful run

An operator opens a `failed`, `stopped`, or `cancelled` run and selects **Retry this run**. The portal copies its target plan into a new `created` run, drops stale absolute schedules, and opens a fresh pre-check capture tied to the new run.

**Acceptance**: After the fresh capture verifies, the operator continues to the new run's options page without creating another run.

### US3 — Keep safety gates

A `stopping` or otherwise live run cannot be retried and continues to block competing firmware work. Retry still requires ownership of the site lock. No retry reuses a pre-check from an earlier attempt.

## Requirements

- **FR-001**: The settle loop MUST inspect the stored stop request before each cloud poll round.
- **FR-002**: A detected stop MUST return control to the run driver without waiting for the phase deadline.
- **FR-003**: The driver MUST move an interrupted run through `stopping` to `stopped` and retain the post-check behavior.
- **FR-004**: Retry MUST accept `failed`, `stopped`, and `cancelled` only.
- **FR-005**: Retry MUST copy targets and options but MUST NOT copy the prior pre-check.
- **FR-006**: A successful retry MUST navigate to a fresh capture associated with the new run.
- **FR-007**: A verified run-associated capture MUST continue to that run's options page rather than creating another run.
- **FR-008**: Contract and Playwright tests MUST cover stop interruption, terminal retry, navigation, and fresh-run continuation.

## Non-Goals

- Retrying a live `stopping` run.
- Automatically resubmitting firmware without a fresh capture and confirmation.
- Changing Mist's gateway SSH failure behavior.
