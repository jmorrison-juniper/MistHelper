# Research: Each run-control browser test frees its site, and the two-operator fixture fails on a refusal

**Issue**: #3497
**Spec**: [spec.md](spec.md)

## R1. The red baseline

I ran four modules in one session in Edge.
A temporary test between the retry module and the two-operator module waited 310 seconds.

```powershell
$env:PYTEST_ADDOPTS = "--browser-channel msedge"
python -m pytest tests/e2e/upgrade_portal/test_run_controls/test_bulk.py tests/e2e/upgrade_portal/test_run_controls/test_existing.py tests/e2e/upgrade_portal/test_zz_tmp3497_wait.py tests/e2e/upgrade_portal/test_two_operators.py -p no:cacheprovider -o addopts="" -rs -q
```

The run ended with 19 passes and 18 skips in 380.82 seconds.
Each skip came from `test_two_operators.py`, and each skip reason read as follows:

```text
/api/sites/22222222-2222-2222-2222-222222222222/lock answered 400, so the first operator holds no lock.
```

The trail of the run held 7 lines:

| Time (UTC) | Action | Site | Source |
| - | - | - | - |
| 15:17:37 | take | 2222 | `test_bulk.py`, through the fixture `site_lock` |
| 15:17:37 | release | 2222 | The teardown of `site_lock` |
| 15:17:38 | take | 5555 | `test_bulk.py`, through the fixture `site_lock` |
| 15:17:38 | release | 5555 | The teardown of `site_lock` |
| 15:17:39 | take | 2222 | `test_bulk.py`, through the fixture `site_lock` |
| 15:17:40 | release | 2222 | The teardown of `site_lock` |
| 15:17:51 | take | 2222 | The first create call of `test_existing.py` |

The last take has no release.
The server log shows a take at 10:17:51 local time and a resume at 10:17:52.
It then shows no lock line until the end of the run.

The run proves the cause.
The lock of site 2222 stayed with the default operator for more than 300 seconds.
The fixture `held_site` then posted an empty body, and the lock module asked for the word `continue`.

The run also showed a second gap.
The portal wrote no log line for the 18 refusals.
Issue #3506 records that gap, because it is a gap of the portal and not of the tests.

## R2. The earlier full run

The full browser run of #3503 did not wait.
Its trail held a take of site 2222 at 14:17:38 from `test_existing.py`.
The next release of site 2222 came at 14:20:25, from the teardown of the first `held_site`.

The first `held_site` therefore resumed a lock that `test_existing.py` took.
The take answered 200 with the state `resume`, and the fixture accepted it.
No test reported the leak, because the lock was less than 300 seconds old.

## R3. The owner of a lock

The lock module compares two values to find the owner of a lock.
The two values are the address of the operator and the browser identifier.
The method `held_by` in `src/interfaces/portals/upgrade_portal/runtime/lock.py` compares both values.

The fixture `page` in `tests/e2e/upgrade_portal/conftest.py` adds the same two cookies to each browser context.
So each test that uses `page` has the same owner.
The fixture `first_page` of `test_two_operators.py` also has that owner.

This fact explains both symptoms:

1. The same owner can resume a lock that is less than 300 seconds old.
2. After 300 seconds, the same owner must send the word `continue`.

## R4. Decisions

### D1. Record each built run in a ledger

Each test of `test_existing.py` records each run that it built.
A built run is a run that the create call answered with 201.
A retry run is also a built run.
The test reads the key of a retry run from the address of the capture page.

A run that the create call named in a 409 answer is not a built run.
Another test or a seed built that run, so this test does not end it.

Alternative: cancel each live run of the site at teardown.
I rejected this, because a teardown then ends the seeds that later tests read.

### D2. Read the state before a cancel

The cancel route answers 409 `run_already_started` for each state after the pre-check.
A cancelled run also answers 409.
The teardown therefore reads the state first, and it cancels only a run that is not final.

The final states come from `RunStateMachine.TERMINAL` in `src/interfaces/portals/upgrade_portal/runtime/runs.py`.
The test code copies no state name, so a new final state reaches the teardown with no edit.

A run in a live state after the pre-check cannot receive a cancel.
No test of `test_existing.py` builds such a run.
If one appears, the cancel answers 409, and the teardown fails with the body.

### D3. Free the site with the word `continue`

The release route reads the lock record from the session of the browser.
The teardown therefore takes the lock again before it releases the lock.
The take sends the word `continue`, so the take works after the quiet time of 300 seconds.

If the site is free, the take answers `acquired`, and the release frees the site again.
The trail then holds one take and one release, so the count stays balanced.

### D4. A teardown fails on a refusal

The fixture `site_lock` of `tests/e2e/upgrade_portal/test_run_controls/conftest.py` writes a warning for a failed release.
Its reason reads that a teardown must never replace the result of the test that just ran.

The new teardown raises an error instead.
Pytest reports an error of a teardown apart from the result of the test.
A test that passed still reads as a pass, and the run adds one error.
A warning does not change the result of a run, so a maintainer who reads a green run never sees it.
The leak of #3497 stayed hidden for that reason.

This change does not edit the fixture `site_lock`.
The strict fixture `held_site` of D5 catches a leak from `site_lock` too.

### D5. The fixture `held_site` accepts `acquired` only

The fixture skips on 503 only, because a workstation with no lock store answers 503.
The fixture fails on each other refusal, and the message names the status and the body.
The fixture fails on the state `resume`, because that state means that an earlier test left the lock.

The decision moves to the class `LockTakeAnswer`, so a direct test proves each branch with no browser.

### D6. One support module

The ledger, the body reader, the teardown, and the decision of the take go into one new module.
The module is `tests/support/upgrade_portal_e2e/site_lock.py`.
The package then holds 6 children, which are 5 modules and the subpackage `records`. The 5-item rule allows 5.

I accept the sixth module.
The four classes serve one subject, which is the site lock of a browser test.
A module in another package would place a browser rule away from the other browser rules.

## R5. Precedents

1. The fixture `site_lock` of the run-control package releases each lock that it took.
   Its docstring names the same 18 skips.
   It covers `test_bulk.py` only.
2. The class `RunOwnerHeaderCheck` of `tests/support/upgrade_portal_e2e/owner.py` is the model for the style.
   It logs before and after each step, and it raises `AssertionError` on a refusal.

## R6. The baseline time and the order of the modules

I ran `test_bulk.py` and `test_existing.py` in one session in Edge, with `--durations=0`.
The run ended with 17 passes in 27.25 seconds.
The 11 tests of `test_existing.py` took 14.42 seconds for all phases.
The mean is 1.311 seconds for each test.
SC-005 compares the time after the change with this value.

I also ran `test_existing.py` alone.
The run ended with 1 failure, 7 passes, 2 skips, and 1 error in 23.50 seconds.
The create call met the two stale seed runs of site 2222, because no `test_bulk.py` ran first to end them.
Issue #3507 records that defect.

This change does not repair #3507.
The teardown ends only the runs that the test built, and a seed run is not a built run.

## R7. The red results and the green results

### The direct tests

1. Before the implementation, the run of `test_e2e_site_lock.py` stopped at collection.
   The error was `ModuleNotFoundError: No module named 'tests.support.upgrade_portal_e2e.site_lock'`.
2. After the implementation, 25 tests passed in 0.83 seconds.
3. After the gate repair below, 36 tests passed in 0.78 seconds.

### The proof that the strict fixture fails (FR-007)

I changed the fixture `held_site` only, and I kept the old teardown of `test_existing.py`.
The sequence of `test_bulk.py`, `test_existing.py`, and `test_two_operators.py` ended with 18 passes and 18 errors in 46.12 seconds.
Each error named the state `'resume'` for site 2222.
Before the change, the same leak gave a pass or a skip, so no report showed it.

### The sequence with no wait

After the teardown change, the same sequence ended with 36 passes in 49.32 seconds.
It had 0 skips and 0 errors.
The trail held 64 lines.
Site 2222 had 31 takes and 31 releases, and site 5555 had 1 take and 1 release.

### SC-001 and SC-004

The repro sequence of R1 adds a wait of 310 seconds before `test_two_operators.py`.
After the teardown change, the sequence ended with 37 passes in 369.18 seconds.
Before the change, it ended with 19 passes and 18 skips in 380.82 seconds.
The trail `e2e-96e7f8988a4847a0ab31451f6c003958` held 64 lines.
Each take had a release before the next take, and no lock stayed at the end.
This run used the code before the gate repair. The gate repair changes no lock call.

### SC-002

The full folder `tests/e2e/upgrade_portal` ran in Edge on the final code.
It ended with 316 passes and 1 skip in 568.50 seconds.
The skip is the known skip of #3380 at `test_capture.py:745`.
The module `test_two_operators.py` had 0 skips.

The trail of the run held 120 lines, and it had 0 order faults.
Site 2222 had 43 takes and 43 releases.
Two other sites held a lock at the end of the run.

1. Site `66666666-6666-6666-6666-666666666666` had 1 take and no release.
   The test `test_response_loss_recovers_by_read_and_preserves_actor_scope` of `test_isolation.py` takes the lock through the fixture `site_lock`.
   The test then clears the cookies of the page.
   The teardown of `site_lock` sends the release from that page, and the fixture only logs a warning when the release fails.
2. Site `99999999-0000-0000-0000-000000343903` had 1 take and no release.
   The test `test_the_capture_start_refuses_after_a_lost_page_and_names_the_cause` of `test_later_site_checks.py` takes the lock through the page.
   No step releases that lock.

No later test takes these two sites, so no test fails today.
Both leaks are outside the scope of #3497. I record them in a new issue.

### SC-005

I ran `test_bulk.py` and `test_existing.py` in one session in Edge, with `--durations=0`, on the final code.
The run ended with 17 passes in 30.83 seconds.
The 11 tests of `test_existing.py` took 17.38 seconds for all phases.
The setup took 11.24 seconds, the calls took 2.33 seconds, and the teardowns took 3.81 seconds.
The mean is 1.580 seconds for each test.
The baseline of R6 is 1.311 seconds, so the change adds 0.269 seconds for each test.
SC-005 allows less than 1 second, so the result passes.

### The gate repair

The first run of the test quality gate reported 8 new findings.

1. Six findings were `missing_fm_empty_body` and `missing_fm_malformed_json`, on line 1 of each of the 3 test modules.
   The detector reads the source of each imported class.
   `SiteRelease` and `LockTakeAnswer` each called the JSON parser.
   No test sent an empty body or a body that is not JSON.
2. Two findings were `weak_zero_assertions` in `test_two_operators.py`.
   They were baseline findings at lines 601 and 617.
   The gate keys a finding on its line number, and my edit moved both tests down by 4 lines.

I repaired both groups. I added no suppression.

1. The new class `AnswerBody` holds the only call of the JSON parser.
   An empty body, a body that is not JSON, and JSON that is not an object each fail.
   Each message names the call and the status.
   Eleven new direct tests prove each branch.
   The browser modules import no class that calls the parser, so the rule does not apply to them.
   The Protocol `RequestSource` went away, so the module keeps 5 top-level names.
2. The two read tests of a held site now also check the path of the page that the browser shows.
   A redirect to another page also answers 200, so the status check alone cannot see a redirect.
   The two baseline entries went away.

After the repair, the gate on the changed files reported 0 new findings.
The full gate checked 866 files and 750 findings, and it reported 0 new findings.
A change to the baseline makes the CI job run the full gate, so this result predicts the CI result.
