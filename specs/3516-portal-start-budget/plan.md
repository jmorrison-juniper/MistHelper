# Implementation Plan: Give the browser portal a robust start budget

**Issue**: #3516
**Specification**: `specs/3516-portal-start-budget/spec.md`

## Summary

Change the E2E portal fixture only. Raise the default start budget from 10
seconds to 60 seconds. Check the child process after each failed port probe.
Keep the existing environment override, loopback probe, and child cleanup.

## File set

| File | Change |
| - | - |
| `tests/e2e/upgrade_portal/conftest.py` | Add the budget and child-state behavior. |
| `tests/unit/upgrade_portal/test_e2e_start_helper.py` | Prove ready, early-exit, and timeout paths. |
| `specs/3516-portal-start-budget/spec.md` | Define the requirements. |
| `specs/3516-portal-start-budget/plan.md` | Record the implementation design. |
| `specs/3516-portal-start-budget/tasks.md` | Track the implementation and gates. |
| `changelog.d/issue-3516-portal-start-budget.md` | Record the test reliability repair. |

## Design

`PortalStartWait` carries three values. They are the ready state, measured
seconds, and optional child exit code.

`_wait_for_port` probes the loopback port first. If the port does not answer,
the function calls `process.poll()`. A returned exit code ends the wait before
the next pause. A live child keeps the same probe and pause sequence.

`_start_server` keeps the current cleanup. It stops a live child after a
timeout. It does not send a stop signal to a child that already stopped.

The focused tests replace the port probe, child process, clock, and sleep.
They start no process, bind no port, open no browser, and make no Mist call.

## Gates

Run the focused tests, Ruff, Black, the changelog guard, Bandit, complexity,
and the test quality preflight. Run the full browser module only when the
isolated Python 3.13 environment and Chromium are available.
