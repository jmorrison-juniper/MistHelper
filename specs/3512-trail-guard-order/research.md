# Research: The browser trail guard reads the checkout trail from the root guard

**Issue**: #3512
**Spec**: [spec.md](./spec.md)

## R1. The cause of the wrong path

**Finding**: The browser guard reads the path of the lock module when pytest starts the guard. In some orders, the move of the first test already applies at that time.

- The root fixture `isolate_site_lock_trail` of `tests/conftest.py` has the function scope and `autouse=True`.
  For each test, it sets `lock.AUDIT_DIRECTORY` to the folder `site-lock-trail` in the temporary folder of that test.
- The lock module reads `AUDIT_DIRECTORY` at call time.
  So `lock.audit_trail_path()` names the moved trail while a test runs.
- `AuditTrailIsolation.__init__` reads `lock.audit_trail_path()` when the caller gives no `checkout_trail` value.
  The fixture `checkout_audit_trail_guard` gives no value.
- Pytest starts a fixture with a larger scope first, but only among the fixtures that a test names.
  A fixture that a test body requests through `request.getfixturevalue` starts inside that test, after each autouse fixture of that test.

**Evidence**: The run of `test_existing.py` alone on `main` at `65819b80` printed this guard line.

```text
Checkout audit trail guard (issue #3498): checked 1 trail, <basetemp>\test_the_run_page_holds_the_re0\site-lock-trail\upgrade_takeover_audit.jsonl.
```

## R2. The modules that start the portal late

**Finding**: Eleven modules start the test portal through `request.getfixturevalue(SERVER_FIXTURE)`.

| Module |
| - |
| `test_assets.py` |
| `test_capture.py` |
| `test_comparison.py` |
| `test_history.py` |
| `test_narrow_action_cells.py` |
| `test_signin.py` |
| `test_site_selection.py` |
| `test_stop.py` |
| `test_two_operators.py` |
| `test_upgrade.py` |
| `test_run_controls/test_existing.py` |

In the full run, an earlier module names the portal fixtures directly.
Pytest then starts the session fixtures before the first move, so the guard names the checkout trail.
The fault shows only when one of the eleven modules runs first.

## R3. The consumers of the wrong path

**Finding**: Two consumers read `checkout_trail` of the browser guard.

1. The guard itself counts the trail before and after the run, and it writes `checkout-audit-trail-guard.json`.
2. The journey `test_audit_log_journey.py` counts the leaked lines through `journey_trail_facts`.

In the wrong order, both read a trail that no later test writes.
The root guard of #3503 still counts the checkout trail, so a leak still fails the run.

## R4. The repair

**Decision**: The browser guard reads the checkout trail from the root guard `checkout_site_lock_trail_guard`.

**Rationale**:

- The move fixture names the root guard as a parameter.
  So pytest starts the root guard before the first move, in each order.
- The root guard already holds the checkout trail in `checkout_trail`.
  One read of the lock module then serves both guards.
- The two guard lines of one browser run then name the same path.

**Alternatives rejected**:

| Alternative | Reason to reject |
| - | - |
| Make the browser guard `autouse=True`. | The fix still depends on the order of the fixtures. The guard then also counts the trail in a run that starts no portal. |
| Read the path at the import of the browser conftest. | Three direct test modules load that conftest by path inside a test fixture, where the move applies. |
| Read the constant `lock.AUDIT_DIRECTORY` from another source. | The root fixture patches the attribute. No second source of the original value exists. |

## R5. The removal of the default

**Decision**: `checkout_trail` becomes a required parameter of `AuditTrailIsolation.__init__`.

**Rationale**:

- The default is the trap. A default read after a move names the moved trail, and no error shows.
- The docstring of the old default asked each caller to build the isolation before a move. No check held that rule.
- A required parameter makes each caller name the source of the path.

**Callers**:

| Caller | Source of the path after the change |
| - | - |
| The fixture `checkout_audit_trail_guard` | The root guard, through the builder `for_session` |
| The child process in `build_stand_in_app` | `lock.audit_trail_path()`, which the child reads before its move |
| The direct tests | A stand-in trail in `tmp_path`, as before |

The child process runs no pytest fixture.
So no move applies in the child before `place`, and the lock module names the checkout trail.

## R6. The proof

**Decision**: Prove the source of the path with direct tests, and prove the fixture with one browser run in each failing order.

- A direct test builds the guard while the move of the root conftest applies.
  It first proves that the lock module names the moved trail.
  It then proves that the build names the trail of the root guard.
- A direct test proves that a build with no checkout trail fails.
- A direct test proves that a build with no root guard fails and names the lock module.
- The browser runs prove the fixture: `test_existing.py` alone, and the pair `test_capture.py` and `test_existing.py`.

**Rejected**: A direct call of the fixture function.
The internal attributes of a pytest fixture differ across versions of pytest.
