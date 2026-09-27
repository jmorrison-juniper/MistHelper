# Research: Each browser test frees each site lock that it took

**Feature**: `specs/3508-browser-lock-leaks` | **Date**: 2026-09-27

This file records the evidence and the decisions of issue #3508.

## Evidence

The full browser run of #3497 wrote a site lock trail of 120 rows.
The table shows the actions of each site in the order of the trail.

| Site | Actions |
| - | - |
| `22222222-...` | 45 pairs of take and release |
| `33333333-...` | 10 pairs of take and release |
| `44444444-...` | 4 pairs of take and release |
| `55555555-...` | 1 pair of take and release |
| `34983498-...` | 1 pair of take and release |
| `66666666-...` | 1 take, and no release |
| `99999999-0000-0000-0000-000000343903` (West) | 1 take, and no release |

The session files hold a copy of this trail for the red proof.

## Decisions

### R1. The cause on the site `66666666`

**Decision**: The test of the lost action answer clears the cookies while it holds the lock.

**Evidence**: The release route reads the lock record from the signed session of the browser.
The function `held_record` in `src/upgrade_portal/app/routes/select.py` compares the token of the body with that record.
The test calls `clear_cookies`, and it then adds the cookies of a renewed session.
The page keeps the cross-site request token of the first session, and the renewed session holds another secret.
The token check refuses the call before the lock check, so the release of the fixture answers 400 `csrf_missing`.
The renewed session also holds no lock record, so a release with a new token answers 409 `lock_lost`.
The red run of R11 read the status 400.
The old fixture logged a warning and went on.

### R2. The cause on the site West

**Decision**: The capture start test takes the site, and no step of the test releases it.

**Evidence**: `PlanSteps.take_the_site` presses the take control.
The test ends after the refusal check, and the page closes with the lock.
The lock then stays for the full lease of 3600 seconds.

### R3. The pass rule of a release

**Decision**: A release passes only when it answers 200 with a JSON object that holds `released` true.

**Rationale**: The route `free_site_lock` answers `{"released": true}` with 200, and each refusal answers another status.
The class `AnswerBody` of #3497 already reads a 200 body and names the call in each failure.
The new class calls it, so the two rules stay the same.

### R4. The home of the new class

**Decision**: The new module `tests/support/upgrade_portal_e2e/lock_holds.py` holds the class `HeldSiteLocks`.

**Rationale**: `site_lock.py` already holds five top-level names, so a sixth name breaks the 5-item rule.
A direct test cannot import a `conftest.py` file in a stable way.
The module is also free of Playwright, so a direct test needs no browser.

### R5. The transport of each lock call

**Decision**: Each call stays a `fetch` from the page, with the cross-site request token that the page shows at call time.

**Rationale**: The call must carry the session cookie of the browser, and the route checks the token.
The old transport already reached the portal for each other release of the run.
A change of transport adds a risk and repairs no fault.

**Alternative rejected**: The request source `page.request` shares the cookies.
It needs a second read of the token, and the passing tests would then change for no cause.

### R6. The teardown with more than one fault

**Decision**: `release_all` tries each hold, newest first, and fails after the last try.
The message names each fault.

**Rationale**: One fault must not leave a second site held for the next test.

### R7. The repair of the test of the lost action answer

**Decision**: The test calls `site_lock.release(SITE_ID)` after it reads the result, and before it clears the cookies.

**Rationale**: The rest of the test reads the action record only, and that read needs no lock.
The release then runs while the session still holds the lock record.

**Alternative rejected**: The teardown could restore the first cookies before the release.
That repair hides the order of the steps from the reader of the test.

### R8. The repair of the capture start test

**Decision**: The new step `PlanSteps.release_the_site` presses the release control.
It then expects the banner state `free` and the sentence "You released this site. Another operator may take it now."

**Rationale**: The release control is the path of an operator.
The sentence proves a real release, because a lost lock paints the state `free` with another sentence.

**Decision**: `PlanSteps.take_the_site` presses the take control, and it waits for the banner state `held`.
If the state does not change, the step fails with the text of `lock-state-message` and `lock-error`.
The step never types the takeover word.

**Rationale**: The old step typed the word when the box opened.
A takeover then closed the hold of an earlier test, and the leak stayed hidden.
The old step also read the box at once after the press, so the answer could arrive after the read.

### R9. The rule of the trail check

**Decision**: The class `TrailHoldCheck` reads the trail line by line.
It fails on a line that is not a JSON object, on a line with no site, and on an unknown action.
It uses the shipped function `mark_expiries` to find each take that follows an open hold.
It then counts each hold that is open at the end of the trail.

**Rationale**: The audit log of the portal infers an expiry with the same rule, so the two readers agree.
The shipped function `read_trail_lines` skips a damaged line, and that rule suits a page.
A guard must fail when it cannot read its input, so the check reads each line itself.
The check reads the action names from `src/upgrade_portal/runtime/lock.py`.
It reads `OPENING_ACTIONS` and `LEGACY_ACTION` from `src/upgrade_portal/compare/lock_audit.py`.

**Note**: The run trail holds the stand-in addresses of the browser fixtures only.
The message names the operator, because the address names the fixture that took the lock.

### R10. The place of the trail check in the run

**Decision**: The new session fixture `run_trail_hold_guard` requests `checkout_audit_trail_guard`.
The fixture `capture_portal_server` requests the new fixture.

**Rationale**: Pytest tears down a fixture after each fixture that requested it.
The check therefore reads the trail after the portal stops, and no write can follow the read.
The fixture reads the path of the run trail from the isolation of #3498.
The fixture stores its measure before the decision, so the summary prints the line when the check fails.

### R11. The red proof

**Decision**: Wire the strict fixture and the trail check first, and keep the two old tests.
Run `test_run_controls/test_isolation.py` and `test_later_site_checks.py` in Edge.

**Expected result**: The isolation test reports a teardown error that names the lock path and the refusal.
The trail check fails and names the sites `66666666-...` and West.
After the two test repairs, the same run passes and names 0 leaked holds.
The direct tests also prove each decision with no network, as the guard proof rule of the repository asks.

**Observed result**: The red run on 2026-09-27 gave 11 passed and 2 errors in 29.39 seconds.
The teardown error named `DELETE /api/sites/66666666-6666-6666-6666-666666666666/lock` and 400 `csrf_missing`.
The trail check read 2 records of 2 sites, and it found 2 leaked holds.
It named the site `66666666-...` and the site West.
