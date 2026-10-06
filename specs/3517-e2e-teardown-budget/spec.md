# Feature Specification: The session teardown of the E2E suite gets a budget of its own

**Issue**: #3517
**Feature Branch**: `jmorrison-juniper-teardown-timeout-reassessment`
**Status**: Approved
**Found by**: the full browser run of #3511 on 2026-09-28

## Problem

The hook `pytest_collection_modifyitems` in `tests/e2e/conftest.py` adds
`pytest.mark.timeout(120)` to each collected E2E item. The mark carries no
`func_only` keyword, and no settings file sets `timeout_func_only`. The plugin
`pytest-timeout` defaults that setting to `False`, so it arms one timer in
`pytest_runtest_protocol`.

Pytest ends each session fixture inside the teardown phase of the last item.
That phase runs inside the same protocol, so the last test and the whole
session teardown share one budget of 120 seconds.

The method is the thread method. When the timer fires, the plugin dumps the
stacks and calls `os._exit(1)`. Pytest then writes no report.

## Measured evidence

A synthetic project outside the repository copied the collection hook. It used
a budget of 3 seconds and a session teardown of 6 seconds. It started no
portal, no browser, and no container.

| Run | Settings | Elapsed | Report |
| - | - | - | - |
| Defect | The current settings | 4.64 s | No `FAILURES` section and no summary line |
| Control | `-o timeout_func_only=true` | 7.42 s | The complete report, with the failed test named |

The stack of the defect run named the exact boundary:

```text
  File "..._pytest\runner.py", line 144, in runtestprotocol
    reports.append(call_and_report(item, "teardown", log, nextitem=nextitem))
  File "..._pytest\runner.py", line 199, in pytest_runtest_teardown
    item.session._setupstate.teardown_exact(nextitem)
```

## Effect

The full browser run of #3511 ran 317 tests. Five tests failed and two
teardowns stopped with an error. The report named none of them, because the
timer ended the process first. An engineer must then run each module again.

## User Scenarios & Testing

### User Story 1 (P1): The session teardown does not take the budget of the last test

A maintainer runs the browser suite on a loaded machine. The session teardown
stops the portal, replays the run trail, compares the checkout trail, and
closes the browser.

**Independent test**: the guard
`tests/guardrails/e2e_timeout_budget/test_timeout_budget.py` builds a
synthetic project and runs it in a subprocess.

**Acceptance scenarios**:

1. **Given** a session teardown that costs more than one test budget.
   **When** the suite ends.
   **Then** the run prints the complete report, and it names each failed test.
2. **Given** the same suite.
   **When** the teardown exceeds its own budget.
   **Then** the run still ends, so no teardown can block the suite forever.

### User Story 2 (P1): A stopped run still names its failed tests

A maintainer reads the evidence of a run that a budget ended.

**Independent test**: the same guard reads the phase trail of the red run.

**Acceptance scenarios**:

1. **Given** a run that a budget ends during the session teardown.
   **When** the maintainer reads the phase trail file.
   **Then** the file holds one record for the setup and one for the call of
   each item that ran, with the outcome of each record.

### Edge cases

- A machine with no `pytest-timeout` plugin keeps the existing skip path.
- An item that carries its own narrower timeout keeps that timeout.
- A run that collects no item writes no phase record and arms no second timer.
- An invalid value in an override variable fails with a named error. It does
  not fall back without a report.

## Requirements

### Functional requirements

- **FR-001**: The setup and the call of each E2E item keep the budget of
  `E2E_TIMEOUT_SECONDS`.
- **FR-002**: The teardown of the last item of the session carries a separate,
  finite budget.
- **FR-003**: The normal pytest-timeout protocol path cancels the replacement
  timer. The repair installs no second cancel path.
- **FR-004**: The repair uses the published hooks `pytest_timeout_set_timer`
  and `pytest_timeout_cancel_timer`. It reads no private attribute of the
  plugin state.
- **FR-005**: The suite appends one JSON line for each pytest phase report to
  a file under `test-artifacts/`, before a timer can end the process.
- **FR-006**: A phase record holds the node identifier, the phase, the
  outcome, the duration in seconds, and a UTC ISO 8601 timestamp. It holds no
  other field.
- **FR-007**: A file error of the phase trail reports the path and the cause.
  No catch is silent.
- **FR-008**: An environment variable may override the teardown budget and the
  phase trail path. An invalid value raises a named error.

### Non-functional requirements

- **NFR-001**: The guard starts no portal, no browser, and no container, and
  it makes no Mist call.
- **NFR-002**: The guard prints the number of runs that it measured and the
  seconds of each run.
- **NFR-003**: The guard fails when it cannot read its input.

## Success criteria

- **SC-001**: The red case of the guard exits with code 1 and prints no
  summary line.
- **SC-002**: The repaired case prints the summary line and names the failed
  test.
- **SC-003**: The teardown budget case ends the run after the teardown budget,
  not after the test budget.
- **SC-004**: The phase trail of the red case holds the record of the failed
  test.

## Out of scope

- The start budget of the portal. #3516 holds that subject.
- The cost of the session teardown itself. This change bounds it, and it does
  not make it faster.
- Any change to `tests/e2e/upgrade_portal/conftest.py`, which PR #3928 owns.
