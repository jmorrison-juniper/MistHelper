# Implementation Plan: A failed multi-site journey ends each operation that it started

**Issue**: #3518
**Branch**: `fix/3518-org-operation-leak`
**Spec**: [spec.md](./spec.md)
**Research**: [research.md](./research.md)

## Summary

A new fixture `org_operation_ledger` registers the class `OrgStartTap` as a route of the browser context of each test.
The tap fetches each answer of the Start request, and the ledger records the id of each 200 answer.
The tap then gives the page the same answer.
The fixture `firmware_operator_page` then ends each recorded operation that is still live.
It cancels the operation through the API, and it reads the status until the state is final.
The start step of the double-click module waits for the Start answer before it waits for the progress page.
A new browser journey proves the teardown with a real operation.

## Technical Context

- **Language**: Python 3.13
- **Test tools**: pytest, pytest-playwright, and Microsoft Edge through `--browser-channel msedge`
- **Scope**: Test code only. No portal code changes, so the change needs no deploy and no release note.
- **Performance goal**: The teardown adds less than one second to a test that cancelled its operation on the page (SC-004).

## Constitution Check

| Rule | Result |
| - | - |
| Class-based design, no wrappers | Pass. The rules live in five classes. The fixture calls one class method. |
| No legacy compatibility shims | Pass. The change removes `cancel_if_running` and `operator_page`. No old path stays. |
| Five-Item Rule | Pass. Each new method takes 5 parameters or fewer and holds fewer than 25 lines. |
| Inline comments and action logging | Pass. Each new line carries a comment. Each call and each decision logs before and after. |
| Safe > Fast | Pass. An unreadable status answer fails the teardown. The teardown never reads a fault as a final state. |
| STE | Pass. Each Markdown file must score 80 or more with 0 errors. |

## Project Structure

```text
tests/support/upgrade_portal_e2e/
  org_operations.py                 NEW: OrgStartAnswer, OrgOperationLedger, OrgStartTap, OrgOperationCalls, OrgOperationRelease
tests/e2e/upgrade_portal/
  conftest.py                       CHANGED: the fixture org_operation_ledger, and the teardown of firmware_operator_page
  test_org_start_double_click.py    CHANGED: the start step, and no local fixture
  test_org_operation_teardown.py    NEW: the browser proof of the teardown
tests/unit/upgrade_portal/
  test_e2e_org_operations.py        NEW: direct tests of each decision
```

## Design

### The module `org_operations.py`

| Class | Role |
| - | - |
| `OrgStartAnswer` | Holds three pure decisions. `is_start` accepts only a 200 answer to `POST /api/org-upgrades`. `operation_id` reads the id from the field `next` of the body. `page_operation` reads the id from the address of a progress page. |
| `OrgOperationLedger` | Holds the ids in the order of the start, with no copy. `observe` reads one answer that the tap fetched. `record_page` is the second source of FR-002. |
| `OrgStartTap` | Holds the route of the context for `**/api/org-upgrades`. `pass_start` fetches each Start answer, gives it to the ledger, and then gives the page the same answer. |
| `OrgOperationCalls` | Sends the status read and the cancel through the request source of the page. `for_page` reads the CSRF token from the page head. If the head holds no token, it opens `/history` and reads the token there. |
| `OrgOperationRelease` | Holds the teardown decisions. `end_for` records the page, skips an empty ledger, and ends each live operation. It returns the count of cancels. |

`OrgOperationLedger.observe` obeys these rules.

1. It returns at once for each answer that is not a start. The tap also gives it a refusal of the Start request.
2. It reads the body of a start answer inside a `try` block. A fault logs a warning, and the ledger records nothing (FR-006).
3. It records the id only when `next` names a progress page.

`OrgStartTap.pass_start` obeys these rules.

1. It sends each request that is not a post to the browser as usual, and it fetches nothing.
2. It fetches a post with no redirect and with a bound of 60 seconds. The start step fails first, at 45 seconds.
3. It gives the answer to the ledger before it gives the answer to the page. So the ledger holds the id when the page opens the progress page.
4. If the fetch fails, it logs a warning and stops the page request. It never sends the request a second time (FR-006).
5. If the answer to the page fails, it logs a warning. The ledger keeps the id, so the teardown still ends the operation.

`OrgOperationRelease` obeys these rules.

1. It reads `cancel_allowed` of each recorded operation. A missing flag or a flag that is not a boolean fails the teardown.
2. It sends `{"confirmation": "CANCEL"}` with the headers `X-CSRFToken`, `Content-Type: application/json`, and `Accept: application/json`.
3. A 200 cancel starts the reads of Decision 4 of the research. The reads stop after 30 tries with a pause of 0.5 seconds.
4. A 409 cancel starts one status read. A final state ends the teardown with no fault (FR-005).
5. Each other answer fails the teardown. The message names issue #3518, the call, the status, and the body (FR-004).

### The fixtures in `conftest.py`

| Item | Change |
| - | - |
| `org_operation_ledger` | New fixture. It builds one ledger and one tap. It registers the tap as a route of the browser context, and it removes the route after the test. |
| `firmware_operator_page` | Takes the ledger. After the test, it calls `OrgOperationRelease.end_for` in a `try` block, and it closes the page in the `finally` block. |

### The module `test_org_start_double_click.py`

| Item | Change |
| - | - |
| `START_ANSWER_TIMEOUT_MS` | New bound of 45 seconds for the Start answer. |
| `OrgStartSteps` | New class. It holds `is_start_answer`, `open_progress`, and `wait_for_hold`, so `OrgFormSteps` keeps four methods. |
| `OrgStartSteps.open_progress` | New step. It presses the Start button through a given action, and it waits for the Start answer. A refusal fails the step with its status. Then it waits for the progress page with `RELOAD_TIMEOUT_MS`. |
| `OrgFormSteps.start` | Uses `open_progress` with one click. |
| The double-click test and the retry test | Use `open_progress` with the double click and the retry click. |
| `OrgJourneyCleanup.cancel_if_running` and `operator_page` | Removed. Each test takes `firmware_operator_page` (FR-007). |

### The journey `test_org_operation_teardown.py`

The first test makes the state of the run of 2026-09-28.

1. Start one operation on both stand-in sites. A route holds the progress page request, so the page keeps the confirmation page.
2. Check that the ledger holds the id of the Start answer. This proves FR-001, and the page address gives no id.
3. Call `OrgOperationRelease.end_for`, and check that it returns one cancel.
4. Let the progress page open, check the state `cancelled`, and take a screenshot.
5. Call `end_for` again, and check that it returns no cancel (FR-003).

The second test proves that the release frees both stand-in sites.

1. Start one operation with `OrgFormSteps`, and end it with `end_for`.
2. Start a second operation on the same two sites. A held site would refuse this start.
3. Check that the ledger holds both ids in the order of the start.
4. Cancel the second operation on the progress page.

## Test Strategy

| Step | Command | Expected result |
| - | - | - |
| Red, direct | `pytest tests/unit/upgrade_portal/test_e2e_org_operations.py` | The import of `org_operations` fails, so each test fails. |
| Green, direct | The same command | Each test passes. |
| Proof, browser | A temporary test that stops on purpose after the start | The server log shows the cancel of the teardown, and no site stays held (SC-001). The test file is not committed. |
| Green, browser | The six multi-site modules and the new journey in Edge | Each test passes, with the one skip of #3380 (SC-002). |
| Green, full | The whole folder `tests/e2e/upgrade_portal` in Edge | Each test passes except the one skip of #3380. The hold check reports no held site (SC-003). |
| Gates | py_compile, ruff, black, mypy, the test quality gate, `tests/guardrails`, and the STE linter | Each gate passes. |

## Risks

| Risk | Mitigation |
| - | - |
| The browser drops the body of the Start answer before a reader gets it. | The first design lost 2 of 2 bodies in the browser proof. The tap reads the body from the fetched answer in memory, so no navigation can drop it. |
| The tap changes the network path of the Start request. | The page gets the same status, headers, and body. The fetch of the tap is not a request of the page, so the double-click test counts the same requests. T010 runs each module that starts an operation. |
| The route turns off the HTTP cache of the context. | Only the 14 tests that take `firmware_operator_page` get the route. T010 and T011 compare the time with the runs of issue #3511. |
| The tap slows each test. | The route matches only the Start path. A read of that path goes to the browser at once. The tap fetches one answer for each start. |
| The teardown cancels an operation that another test owns. | The ledger records only the Start answers of its own browser context. A status read or a cancel of another owner fails. |
| The cancel leaves a child job that still writes. | The reads wait until the portal reports a final state. After the bound, the teardown fails and names the state. |
