# Implementation Plan: The poll of a stored capture stops

**Issue**: #3378 | **Spec**: [spec.md](spec.md) | **Research**: [research.md](research.md)

## Summary

`stored_progress` sends the content word of a stored capture as its lifecycle
word. The repair sends `verified` when the read-back holds and `failed` in every
other case, which is the rule of the live path.

## Technical context

- **Language**: Python 3.13, and JavaScript in the browser.
- **Dependencies**: No new dependency.
- **Storage**: No schema change. The stored document does not change.
- **Tests**: pytest, the Flask test client, and Playwright with Microsoft Edge.

## Constitution check

- The change reads stored data only. It makes no cloud call and no write.
- The status body keeps the fields of the contract.
- The tests run offline. The browser journey uses the loopback server of the
  harness and a simulated cloud.

## Files

| File | Change |
| - | - |
| `src/upgrade_portal/app/routes/capture.py` | `stored_progress` sends the lifecycle word. The route docstring states the 3-second poll. |
| `src/upgrade_portal/app/routes/org_postcheck.py` | The docstring of `_result` states the new rule. |
| `specs/1823-upgrade-capture-portal/contracts/http-api.md` | The status section states the poll interval and the words that end the poll. |
| `tests/unit/upgrade_portal/test_capture_stored_state.py` | New unit tests for each scenario of user story 2. |
| `tests/contract/upgrade_portal/test_capture_status.py` | The stored seed uses the shipped shape. New cases for `partial` and for a capture that this release cannot compare. |
| `tests/unit/upgrade_portal/test_org_postcheck_bridge.py` | The stub of the stored body uses the shipped word. |
| `tests/e2e/upgrade_portal/conftest.py` | One seed in the shipped shape on its own site. |
| `tests/e2e/upgrade_portal/test_stored_capture_poll_journey.py` | New browser journey. |
| `changelog.d/issue-3378-stored-capture-poll.md` | The release note. |

## Risks

- A reader that expects `complete` or `partial` in the status body. The search
  found one reader, `org_postcheck._result`, and it reads the `verified` flag
  first. Its verdict does not change.
- A new seed that changes a list. Research R6 places the seed where no count,
  picker, or adopter reads it. The full browser suite proves this.
