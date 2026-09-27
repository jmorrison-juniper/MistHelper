# Implementation Plan: Each run-control browser test frees its site, and the two-operator fixture fails on a refusal

**Issue**: #3497
**Branch**: `fix/3497-retry-lock-leak`
**Spec**: [spec.md](spec.md)
**Research**: [research.md](research.md)

## Summary

The tests of `test_existing.py` build runs on the stand-in site, and no test ends them or releases the site lock.
This change adds one support module with four classes.
The first class records each run that a test built.
The second class reads the body of each 200 answer as a JSON object.
The third class ends each live run and then frees the site lock.
The fourth class turns one answer of the lock take into a held lock, a skip, or a failure.
The module `test_existing.py` uses the first class and the third class in a teardown.
The fixture `held_site` of `test_two_operators.py` uses the fourth class.

## Technical Context

| Item | Value |
| - | - |
| Language | Python 3.13 |
| Test tools | pytest, pytest-playwright, and the Edge channel of Playwright |
| New dependencies | None |
| Portal code | No change. The change touches no file under `src/`. |
| Storage | None. The stand-in stores of the E2E server hold every record in the server process. |
| Release note | None. The change holds test code only, and no operator sees it. |
| Deploy | None. The portal on port 8056 runs no test code. |

## Constitution Check

| Rule | Result |
| - | - |
| Simplified Technical English | Each Markdown file and each GitHub body scores 80 or more, with 0 errors. |
| Inline comments | Each executable line of new code carries a comment. |
| Action logging | Each call of the support module logs before the step and after the step. |
| Classes and no wrappers | Four classes hold the logic. No function only calls another function. |
| 5-item rule | One deviation. See the Complexity Tracking section. |
| Fix over suppress | The change adds no suppression comment. |

## Files

| File | Change |
| - | - |
| `tests/support/upgrade_portal_e2e/site_lock.py` | New. It holds `RunLedger`, `AnswerBody`, `SiteRelease`, and `LockTakeAnswer`. |
| `tests/unit/upgrade_portal/test_e2e_site_lock.py` | New. It holds the direct tests of each decision. |
| `tests/e2e/upgrade_portal/test_run_controls/test_existing.py` | Edit. It records each built run and frees the site at teardown. |
| `tests/e2e/upgrade_portal/test_two_operators.py` | Edit. The fixture `held_site` uses `LockTakeAnswer`. The two read tests of a held site also check the address of the page. |
| `.github/test-quality-baseline.json` | Edit. It drops the two findings that the two read tests repair. See research R7. |
| `specs/3497-retry-lock-leak/` | New. It holds the SpecKit record of this change. |

## Design

### The class `RunLedger`

1. The method `record` adds one run key. It refuses an empty key, and it keeps each key one time only.
2. The method `record_from_url` reads the `run_id` value from the query of an address.
   It fails when the address names no run, because the test then cannot end the retry run.
3. The property `runs` gives the keys in the order of the record.

### The class `AnswerBody`

The method `read` turns the body of one 200 answer into the fields of a JSON object.

| Body | Decision |
| - | - |
| Empty, or white space only | Fail. The message names the call and the status. |
| Text that is not JSON | Fail. The message names the call, the status, and the body. The parser error stays the cause. |
| JSON that is not an object | Fail. The message names the call, the status, and the body. |
| A JSON object | Give the fields to the caller. |

`SiteRelease` and `LockTakeAnswer` call `read` for each 200 answer.
Only this class calls the JSON parser, so the direct tests of this class prove each failure of a body.

### The class `SiteRelease`

1. The constructor takes the request source of the page and the token for the cross-site request check.
2. The method `end_runs` reads the state of each run.
   - A 404 answer means that the store holds no such run, so the method moves on.
   - A final state needs no cancel.
   - Each other state gets one cancel, and the cancel must answer 200.
   - Each other answer fails, and the message names the path, the status, and the body.
3. The method `free_site` takes the lock with the word `continue`, and then it releases the lock.
   Each call must answer 200. Each other answer fails, and the message names the path, the status, and the body.
4. The final states come from `RunStateMachine.TERMINAL`.

### The class `LockTakeAnswer`

The method `require_token` decides one answer of the lock take.

| Answer | Decision |
| - | - |
| 401 or 404 | Fail. The message states that the portal serves no lock route. |
| 503 | Skip. The reason names the lock store. |
| Each other status except 200 | Fail. The message names the status and the body. |
| 200 with a state other than `acquired` | Fail. The message states that an earlier test left the lock. |
| 200 with the state `acquired` and no token | Fail. The message states that no release can free the lock. |
| 200 with the state `acquired` | Give the token to the fixture. |

### The teardown of `test_existing.py`

1. The fixture `run_ledger` gives each test a new ledger.
2. The fixture `portal_page` yields the page. After the test, it opens the site picker.
   The picker gives a fresh token and the site key.
3. The teardown calls `end_runs` with the runs of the ledger, and then it calls `free_site`.
4. The helper `_create_run` records each run that the create call answered with 201.
5. Each retry test records the retry run from the address of the capture page.

## Validation

1. Run the direct tests before the implementation, and record the red result.
2. Run the direct tests after the implementation. Each test must pass.
3. Run the repro sequence of SC-001. It must report 0 skips and 0 failures in `test_two_operators.py`.
4. Read the trail of the repro run. Each take of site 2222 must have a release (SC-004).
5. Run the full folder `tests/e2e/upgrade_portal` in Edge.
   It must report 0 skips in `test_two_operators.py`, and the skip of #3380 stays (SC-002).
   The strict fixture then shows whether another module leaks the lock of site 2222.
6. Measure the time of `test_existing.py` before and after the change (SC-005).
7. Run ruff, black, py_compile, mypy, and the test quality gate on the changed files.

## Complexity Tracking

| Deviation | Reason | Rejected alternative |
| - | - | - |
| The package `tests/support/upgrade_portal_e2e` holds 6 children, which are 5 modules and the subpackage `records`. The 5-item rule allows 5. | The four classes serve one subject, the site lock of a browser test. The other browser support rules live in the same package. | A module in another package would place a browser rule away from the other browser rules. |
