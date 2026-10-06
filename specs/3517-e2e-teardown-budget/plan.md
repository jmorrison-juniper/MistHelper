# Implementation Plan: The session teardown of the E2E suite gets a budget of its own

**Issue**: #3517
**Specification**: `specs/3517-e2e-teardown-budget/spec.md`

## Summary

`tests/e2e/conftest.py` gets two new hooks and two new classes. The first hook
replaces the item timer at the start of the teardown of the last item of the
session. The second hook writes one JSON line for each phase report under
`test-artifacts/`. A nested guard proves each decision in a subprocess.

## Technical context

| Item | Value |
| - | - |
| Language | Python 3.13 |
| Test runner | `pytest==9.1.1` |
| Timer plugin | `pytest-timeout==2.4.0`, thread method |
| Files changed | 7 |
| New dependency | None |

## The control flow today

```text
pytest_runtest_protocol (pytest-timeout, hookwrapper)
  pytest_timeout_set_timer(item, Settings(120, "thread", func_only=False, ...))
  yield
    setup   phase
    call    phase
    teardown phase  <-- teardown_exact(None) ends every session fixture here
  pytest_timeout_cancel_timer(item)
```

One `threading.Timer` of 120 seconds covers the three phases. When it fires,
`dump_stacks` runs and `os._exit(1)` ends the process with no report.

## The control flow after the repair

```text
pytest_runtest_protocol (pytest-timeout, hookwrapper)
  pytest_timeout_set_timer(item, Settings(120, ...))
  yield
    setup   phase            <-- the 120 second timer
    call    phase            <-- the 120 second timer
    teardown phase
      pytest_runtest_teardown (this repair, tryfirst hookwrapper)
        nextitem is None?
          pytest_timeout_cancel_timer(item)
          pytest_timeout_set_timer(item, Settings(300, ...))
        yield                <-- the 300 second timer
  pytest_timeout_cancel_timer(item)   <-- cancels the replacement timer
```

`pytest_timeout_set_timer` writes `item.cancel_timeout`. The replacement
assignment overwrites that attribute, so the cancel call that the plugin
already makes after its own `yield` cancels the replacement timer. The repair
adds no second cancel path, which satisfies FR-003.

## Decisions

### The teardown constant

`SessionTeardownBudget.DEFAULT_SECONDS = 300`.

The measured parts of the session teardown are these:

| Step | Bound |
| - | - |
| The portal stop | `STOP_TIMEOUT_SECONDS = 5` in `tests/e2e/upgrade_portal/conftest.py` |
| The run trail replay | A file read, milliseconds in the recorded artifacts |
| The checkout trail compare | A file read, milliseconds in the recorded artifacts |
| The Playwright browser close | No bound. The 2026-09-28 stack stalled here. |

The browser close is the one unbounded step, so the constant must cover it on
a loaded machine. 300 seconds is 2.5 times the per-item budget of 120 seconds.
It gives a slow machine room, and it still ends a hung teardown inside five
minutes. The variable `MISTHELPER_E2E_TEARDOWN_BUDGET_SECONDS` overrides it.

### Why not `timeout_func_only`

`timeout_func_only = true` removes the bound from the setup phase as well as
from the teardown phase. Issue #3516 reports a slow portal start, which runs
in setup, so that setting would remove a bound that the suite needs.

### The phase trail

A fired timer still calls `os._exit(1)`, so a bound alone does not save the
evidence. `pytest_runtest_logreport` runs after each phase report, before the
next phase starts. One append and one close for each record puts the bytes in
the operating system, and `os._exit` does not lose them.

The record holds the node identifier, the phase, the outcome, the duration,
and a UTC ISO 8601 timestamp. It holds no other field, so it carries no
credential, no host name, and no payload.

## The file set

| File | Change |
| - | - |
| `specs/3517-e2e-teardown-budget/spec.md` | New |
| `specs/3517-e2e-teardown-budget/plan.md` | New |
| `specs/3517-e2e-teardown-budget/tasks.md` | New |
| `tests/e2e/conftest.py` | The two hooks and the two classes |
| `tests/guardrails/e2e_timeout_budget/__init__.py` | New, the package marker |
| `tests/guardrails/e2e_timeout_budget/test_timeout_budget.py` | New, the guard |
| `changelog.d/issue-3517-e2e-teardown-budget.md` | New |

`tests/guardrails/` already holds 45 files at its root, so the guard goes in
its own package. `tests/guardrails/local_test_quality_loop/` is the pattern.

## The guard

The guard writes a synthetic project under `tmp_path` and runs it with
`subprocess.run([sys.executable, "-m", "pytest", ...])`. A subprocess is
necessary, because the plugin ends the process with `os._exit(1)`.

The synthetic conftest loads the two repair hooks from the real
`tests/e2e/conftest.py` through `importlib`, so the guard proves the shipped
code and not a copy. The two environment variables point the budget and the
trail at the temporary directory.

| Case | Proves |
| - | - |
| `test_shared_budget_loses_the_report` | SC-001, the red case |
| `test_separate_budget_keeps_the_report` | SC-002, the repaired case |
| `test_teardown_budget_still_ends_an_overrun` | SC-003 |
| `test_phase_trail_survives_the_stop` | SC-004 |
| `test_guard_reports_what_it_measured` | NFR-002 and NFR-003 |

The guard starts no portal, no browser, and no container, and it makes no Mist
call. Each synthetic project uses `time.sleep` only.

## Risks

| Risk | Control |
| - | - |
| The guard costs seconds in CI | Each budget is 1 to 4 seconds, so the package runs in under 30 seconds. |
| A later pytest-timeout release renames a hook | The guard fails at once, because the import of the hook name fails. |
| The trail file grows | The run writes one line for each phase, and `test-artifacts/` is outside git. |

## Gates

Ruff, Black, mypy, Bandit, the complexity gate, `symbol-diff`, the changelog
fragment guard, the test quality ratchet, and the new guard package. The full
browser suite does not run.
