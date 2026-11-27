# Research: E2E job stops reporting results (issue #3736)

## 1. Method and scope

- Remote facts come from read-only `gh` calls (GET requests only) and from decoded remote file bodies.
- Local facts come from read-only file views, `git hash-object`, and `git check-ignore`. No build, test, linter, or repository script ran.
- One external source was fetched with `web_fetch`. The URL appears in row RC-48.
- Line numbers in section 9 come from decoded `main` bodies or from decoded base bodies at the named commit.
- Log parsing used an in-memory script that matches the verbose pytest outcome lines. No log file was written.
- No skill was loaded. The issue concerns GitHub Actions, pytest, and Playwright, and no listed skill matches that scope. No Podman or Juniper device question applies.

## 2. Issue facts

- Issue #3736 is open. Title: "CI: E2E job stops reporting results before its 15-minute limit". Labels: `bug`, `ci`, `tests`, `in-progress`, `testing`.
- The body cites Quality Gates run 37073211456, attempt 1, job 111057821335, and source head 6fb9f48 in PR #3735.
- The body counts are 429 completed outcomes, 380 passes, 49 skips, and 171 with no result. Comment IC_kwDOQltU8c8AAAABY2yv_A (2026-10-02 23:24:03Z) corrects them to 442 outcomes, 391 passes, 51 skips, and 158 with no result. The local parse in section 3 agrees with the correction.
- The body states that the browser module, shared fixtures, and workflow match the granted base byte for byte. Section 5 shows that this statement holds only for the base commit.
- The ten comments run from 2026-10-02 to 2026-10-23. They record the following stalls and passes:
  - Oct 6 (IC_kwDOQltU8c8AAAABZwn7Qw and IC_kwDOQltU8c8AAAABZw8ILg): PR #3989 hit a screenshot capture error, then passed on retry.
  - Oct 16 (IC_kwDOQltU8c8AAAABciqPiw): PR #4236 run 38860778804 hit the 20-minute limit twice. Its last reported case is the test named in section 3.
  - Oct 22 to Oct 23 (IC_kwDOQltU8c8AAAABegwAqg, IC_kwDOQltU8c8AAAABehIZKQ, IC_kwDOQltU8c8AAAABehbUOA, IC_kwDOQltU8c8AAAABewtn6Q): PR #4403 and PR #4327 cancellations, one passing retry, and a targeted rerun that GitHub refused.
  - Oct 23 (IC_kwDOQltU8c8AAAABe-nyPA): PR #4408 hit the limit twice during APT package transfers.
- Related issues: #3517 (closed, session teardown budget), #3375 (closed, shared capture fixture), #4250 (closed, full suite exceeds the 20-minute limit).
- Other related issues: #4613 (closed, browser dependency download), #4208 (open, WAN dashboards, owner of a planned `ci.yml` edit).
- Pull requests named in the thread, or returned by `gh pr list --search 3736`, have these states. The states are #3735 merged, #3989 merged, #4236 merged, #4242 merged, #4327 merged, #4403 merged, and #4408 merged. PR #4617 merged on 2026-11-12. Its body says its evidence is not proof of the earlier silent test stall in #3736. PR #4251 merged. PR #2166 matched the search text because it quotes openai-python issue #3736. It is unrelated.

## 3. Failing run evidence

Run 37073211456, attempt 1. Head commit 6fb9f483a65f825cd5f8e7e5ea9cc1c1439d0264. Job 111057821335, "E2E smoke tests".

- The job started at 22:36:41Z and completed at 22:51:59Z with conclusion `cancelled`.
- The step "Run E2E smoke tests" ran from 22:38:02Z to 22:51:56Z and ended `cancelled`.
- The check-run annotations include "The job has exceeded the maximum execution time of 15m0s" and "The operation was canceled."
- The log has 1818 cleaned lines. The pytest header reports `timeout: 180.0s`, `timeout method: signal`, and `timeout func_only: False`.
- The collection line reports `collected 600 items` at 22:38:07.684Z.
- The parser found 442 distinct test IDs with an outcome line. There are 391 PASSED lines and 51 SKIPPED lines. No ID repeats. The other 158 collected IDs have no outcome line.
- The last outcome line is at 22:44:48.678Z. It is `PASSED tests/e2e/upgrade_portal/test_capture.py::TestCaptureProgress::test_progress_region_shows_every_section_of_the_status_body`.
- The next log line is `##[error]The operation was canceled.` at 22:51:56.016Z. The silent interval is 427.3 seconds. No line appears inside this interval.
- Four stall logs contain zero pytest-timeout report lines (section 7).

Run 37073211456, attempt 2. Job 111063524387.

- The job ran from 22:57:59Z to 23:07:38Z and ended `success`.
- The parser found 600 distinct IDs: 548 PASSED and 52 SKIPPED.
- The first 442 outcomes match attempt 1 in order. Index 441 is the same test in both attempts.
- The next outcome in attempt 2 is `PASSED tests/e2e/upgrade_portal/test_capture.py::TestCaptureProgress::test_start_button_starts_a_capture` at 23:06:48.636Z. That is 0.25 seconds after the previous outcome.

## 4. Workflow and harness history

Commits that changed the E2E timing or harness, in date order. Each commit below appears in the commits API for `.github/workflows/ci.yml` or `tests/e2e/conftest.py`.

- `4f3fb450e77d856d1bd533f7d6e49ea0c4bfa664` (2026-10-06, PR #3974): adds `SessionTeardownBudget`, the `PhaseTrailWriter` trail, and the teardown hooks to `tests/e2e/conftest.py`.
- `38d06c48aa01c553ff2fa4d16d819f82dd68dc94` (2026-10-03, "feat(websockets): add the operations portal"): changes the single E2E job limit from `timeout-minutes: 15` to `timeout-minutes: 20`. The hunk shows the removed and added lines for the job that carries the comment "Issue #2242".
- `6461bef5e709d7a73593d9786998c5f576bf584c` (2026-10-15): adds `--screenshot only-on-failure --tracing retain-on-failure --output` to the pytest command.
- `0f42cdea6e96b4e5a416e413562a6101aa4f8e37` (2026-10-16, PR #4251): splits the E2E suite into `playwright_shards` and keeps the required aggregator named "E2E smoke tests".
- `de2b4667ae8da573090b4775de4a662160590919` (2026-11-12, PR #4617): adds the Ubuntu package mirror preparation step. The step touches only the slow Azure mirror entry.
- `23379f0e075557cd5c0761a79f23ad8d3583e296` (2026-11-21): the latest commit that changes `ci.yml` in the scanned history.

## 5. Current state of `main`

The current head is `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. The local checkout is on `main` at the same commit.

- The shard job `playwright_shards` has a 20-minute job limit (RC-04). The matrix has three rows (RC-05 to RC-07).
- The aggregator `playwright` keeps the name "E2E smoke tests" and has a 5-minute limit (RC-08, RC-09).
- The shard pytest command keeps `--timeout=180` (RC-10). The shard harness overrides that value for each E2E item (section 7).
- The diagnostics upload uses `failure() || cancelled()` and includes the phase trail (RC-11, RC-12). It does not include a stack dump, because no stack dump exists yet.
- The cancel message says "cancelled at its 20-minute limit" for every cancellation (RC-13).
- The harness on `main` sets `E2E_TIMEOUT_SECONDS = 120` (RC-17). It applies that value as a marker to each E2E item (RC-18). For the last item, it replaces the item timer with a 300-second teardown budget (RC-19). It appends one JSON line for each phase report (RC-20).
- The base commit had `E2E_TIMEOUT_SECONDS = 120` and the marker (RC-21). It did not have the trail or the teardown budget (RC-22).
- Recent shard durations on `main` and on pull requests are as follows:
  - Run 45774119357 (2026-11-26): upgrade-portal 5m35s, web-portal 12m19s, websockets-tab 10m41s.
  - Run 45771114707 (2026-11-26): web-portal 13m02s.
  - Run 44952653930 (2026-11-21): web-portal 11m58s.

## 6. Recurrence evidence

### 6.1 Scan method and coverage

The scan used `gh run list --workflow ci.yml --created <range>`, then the jobs API and the check-run annotations. An E2E job counts as a limit event when its annotation text contains "exceeded the maximum execution time".

The windows below cover 2026-10-16 to 2026-11-26 without a gap.

- Oct 16 to Oct 25: 492 runs. The result is complete because the count is below the 500-run cap.
- Oct 22 to Nov 5: the newest 500 runs. The cap stops at Oct 22, so the window covers Oct 22 to Nov 5 completely.
- Oct 28 to Nov 18: the newest 500 runs. The cap stops at Oct 28, so the window covers Oct 28 to Nov 18 completely.
- Nov 19: 49 runs.
- Nov 20: 36 runs.
- Nov 20 21:58 to Nov 26: the newest 120 runs. The result is complete for Nov 21 to Nov 26.
- Earlier attempts of retried runs from 2026-10-16 to 2026-11-26: 20 retried runs. The scan checked 29 earlier-attempt E2E jobs and found 11 limit events. Without this step, the scan would miss the first attempt of any run that a retry later passed.

### 6.2 Limit events

The scanned windows contain 48 limit events from 2026-10-16 to 2026-11-06. Of these, 37 come from the latest attempt of a run and 11 come from an earlier attempt of a retried run. No limit event occurs after 2026-11-06.

| Period | Events | Latest attempt | Earlier attempt | Note |
| - | - | - | - | - |
| Oct 16 | 7 | 7 | 0 | Six events in the single-job era, before the shard split. Their test steps lasted 18.2 to 19.0 minutes. One web-portal shard event at 18:34. |
| Oct 22 to Oct 23 | 8 | 3 | 5 | Shard era. |
| Oct 26 | 18 | 16 | 2 | Shard era. One upgrade-portal event had no outcome line. |
| Oct 28 | 1 | 0 | 1 | Shard era. The log returns HTTP 404. |
| Nov 5 to Nov 6 | 14 | 11 | 3 | Shard era. Download steps lasted 8.8 to 16.8 minutes in six sampled events. |


### 6.3 Silent interval before each cancellation

For each limit event, the script measured the time from the last outcome line to the cancellation line. Where the cancellation line is absent, the script measured to the last log line.

- **Stall class, silence of 100 seconds or more: 3 events.** All three ran in the single-job era on 2026-10-16.
  - Job 116833147946 (run 38857649062): 581 outcomes, silence 187.6 seconds.
  - Job 116842182317 (run 38860502112): 581 outcomes, silence 104.1 seconds.
  - Job 116850242205 (run 38860778804): 581 outcomes, silence 104.6 seconds. This job matches the PR #4236 timestamps in comment IC_kwDOQltU8c8AAAABciqPiw.
  - In all three logs, the last outcome line is `test_progress_region_shows_every_section_of_the_status_body`. No partial line for the next item appears before the cancellation.
- **Silence of 7.1 seconds or less: 43 events.** These events show outcome lines until the cancellation, or they finished all tests before the limit. Their cause is throughput, setup time, or post-test time.
- **Limit reached after all tests passed: 4 events.**
  - Job 127446107889 (run 42084190844, 2026-11-05): `446 passed, 2 warnings in 674.24s`. The step "Run E2E smoke tests" succeeded at 18:48:36Z. The job reached 20 minutes during the post-test steps.
  - Job 127283916521 (run 42038456653, 2026-11-05, earlier attempt): `446 passed, 2 warnings in 646.90s`. The job reached the limit 7.1 seconds after the last outcome.
  - Job 121754946610 (run 40374418524, 2026-10-26): `414 passed in 655.45s`. The job reached the limit 6.1 seconds after the last outcome.
  - Job 120311010523 (run 39922218945, 2026-10-23): `414 passed in 569.50s`. The job reached the limit 6.4 seconds after the last outcome.
- **No test started: 1 event.** Job 121800667924 (run 40384146224, 2026-10-26) had no collection line and no outcome line. Its step `python -m playwright install --with-deps chromium` lasted 19.2 minutes.
- **Log unavailable: 1 event.** Job 122682105845 (run 40647974378, 2026-10-28, earlier attempt) returns HTTP 404 for its log. Its annotation shows the limit. Its silence is unknown.

### 6.4 Interpretation

- All four stall events in the record (Oct 2 and three on Oct 16) occurred in the single-job era. That job ran 600 items on Oct 2 and 973 to 980 items on Oct 16, in one pytest process.
- No stall event appears after the shard split on 2026-10-16. Each event after the split with silence data has silence of 7.1 seconds or less.
- The stall events end at the same test. The boundary test is the one named in section 3. The next test in the same class is `test_start_button_starts_a_capture`.
- Non-stall limit events in the shard era come from setup time, throughput limits, or post-test time. The setup time, mainly the Playwright browser install step, took 7 to 19 minutes.

### 6.5 Concurrency cancellations

- Run 44962483189 (2026-11-21), job 137024819690: the web-portal shard ran 11 minutes 12 seconds. Its annotations include "Canceling since a higher priority waiting request" and the 20-minute limit message. The cancel message mislabels this concurrency cancel.
- Across the scanned windows, the classifier counted 31, 29, and 42 concurrency cancellations in the three larger windows. These counts cover the E2E shard jobs and the aggregator job named "E2E smoke tests".

## 7. Local source evidence

Installed packages are in `.venv\Lib\site-packages`. The pytest version is 9.2.0 and the pytest-timeout version is 2.4.0.

- `pytest_runtest_protocol` (pytest_timeout.py line 179) arms the item timer before the protocol and cancels it after the protocol (RC-41). The timer covers setup, call, teardown, and the log lines between them.
- `_get_item_settings` (line 388) reads the timeout marker first. It uses the CLI value only when no marker value exists (line 401) (RC-42). The E2E marker therefore sets the effective per-test budget to 120 seconds.
- `timeout_sigalrm` (line 485) returns without output when `is_debugging()` is true. It writes the stack dump and calls `pytest.fail` only after that check (RC-43).
- `is_debugging` (line 262) returns true only in three cases. In the first case, `SUPPRESS_TIMEOUT` is set. In the second case, a trace function comes from `pydevd`, `bdb`, or `pydevd_frame_evaluator` (line 57). In the third case, a tool is registered at `sys.monitoring.DEBUGGER_ID` (RC-44).
- `timeout_timer` (line 505) writes stacks and calls `os._exit(1)` at line 542. This is the thread method (RC-45).
- The `faulthandler` plugin in pytest 9.2.0 duplicates the stderr file descriptor at configure time (`_pytest/faulthandler.py` line 44) (RC-46). It arms `dump_traceback_later` only when `faulthandler_timeout` is greater than zero (line 96) (RC-47). The repository does not set that option.

Negative search results.

- The identifiers `SUPPRESS_TIMEOUT`, `suppress_timeout`, `pytest_timeout`, `settrace`, `set_trace`, `breakpoint(`, `import pdb`, and `import bdb` appear only in two files. `src/operations/execution/ssh/runtime/app_runner.py` contains its own line tracer. `tests/e2e/conftest.py` contains the teardown budget code, which imports `pytest_timeout`. No test or web-portal code sets `SUPPRESS_TIMEOUT`.
- `SIGALRM`, `signal.alarm`, `setitimer`, `SIG_IGN`, `faulthandler`, and `signal.signal(` appear in no file under `src/`, `web_portal/`, or `tests/` except two documentation strings in `tests/guardrails/e2e_timeout_budget/test_timeout_budget.py`. The search also covered `MistHelper.py`, `wsgi.py`, and `wsgi_capture.py`.
- The stall logs have zero pytest-timeout report lines (sections 3 and 6.3).

Conclusion from local source. The silent return in `timeout_sigalrm` does not explain the stalls, because no suppression source exists. The signal handler either did not run or its output did not reach the log. Local source reading cannot decide between these explanations.

## 8. External source

- Python `faulthandler` documentation, fetched 2026-11-26 from `https://docs.python.org/3/library/faulthandler.html`. The `dump_traceback_later` function dumps the tracebacks of all threads after a timeout. It runs on a watchdog thread. The file must stay open until the dump or the cancel call. A second call replaces the first. The module supports only ASCII output and displays filenames, function names, and line numbers (RC-48).

## 9. Remote verification table

Each row is one check. The result column uses `present`, `absent`, `partial`, or `stale`. A line of 0 marks a presence check of the whole path or commit. The 55 rows below match the `remote_checks` array in `3736-STATUS.json` in order. Commit rows put the commit SHA in the blob column.

| Row | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| RC-01 | Commit 66b1a18 exists (granted main). | commits/66b1a1832e069a467d25034bc6024c2c7353e11e | main | 66b1a1832e069a467d25034bc6024c2c7353e11e | present | 0 |
| RC-02 | Commit 6fb9f48 exists (failing run head). | commits/6fb9f483a65f825cd5f8e7e5ea9cc1c1439d0264 | main | 6fb9f483a65f825cd5f8e7e5ea9cc1c1439d0264 | present | 0 |
| RC-03 | The main branch points to f03c6c9. | git/ref/heads/main | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| RC-04 | The shard job has a 20-minute limit. | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 782 |
| RC-05 | The matrix row for upgrade-portal exists. | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 793 |
| RC-06 | The matrix row for web-portal exists. | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 795 |
| RC-07 | The matrix row for websockets-tab exists. | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 797 |
| RC-08 | The aggregator keeps the name "E2E smoke tests". | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 955 |
| RC-09 | The aggregator has a 5-minute limit. | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 962 |
| RC-10 | The shard pytest command keeps `--timeout=180`. | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 909 |
| RC-11 | The diagnostics upload runs on failure or cancellation. | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 939 |
| RC-12 | The diagnostics upload includes the phase trail. | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 945 |
| RC-13 | The cancel message says "20-minute limit" for every cancellation. | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 952 |
| RC-14 | The single E2E job had a 15-minute limit at the base commit. | .github/workflows/ci.yml | 6fb9f483a65f825cd5f8e7e5ea9cc1c1439d0264 | cc41c46b8c23d291b73d9137bc78d5765202ded9 | present | 737 |
| RC-15 | The base commit 66b1a18 has the same workflow blob as the head. | .github/workflows/ci.yml | 66b1a1832e069a467d25034bc6024c2c7353e11e | cc41c46b8c23d291b73d9137bc78d5765202ded9 | present | 737 |
| RC-16 | The base pytest command passes `--timeout=180`. | .github/workflows/ci.yml | 6fb9f483a65f825cd5f8e7e5ea9cc1c1439d0264 | cc41c46b8c23d291b73d9137bc78d5765202ded9 | present | 800 |
| RC-17 | The harness on main sets `E2E_TIMEOUT_SECONDS = 120`. | tests/e2e/conftest.py | main | e450e1855770d2e0ec587935a95233262b118ae1 | present | 33 |
| RC-18 | The harness applies the timeout marker to E2E items. | tests/e2e/conftest.py | main | e450e1855770d2e0ec587935a95233262b118ae1 | present | 218 |
| RC-19 | The harness on main defines the session teardown budget. | tests/e2e/conftest.py | main | e450e1855770d2e0ec587935a95233262b118ae1 | present | 36 |
| RC-20 | The harness on main defines the phase trail writer. | tests/e2e/conftest.py | main | e450e1855770d2e0ec587935a95233262b118ae1 | present | 123 |
| RC-21 | The base harness sets `E2E_TIMEOUT_SECONDS = 120`. | tests/e2e/conftest.py | 6fb9f483a65f825cd5f8e7e5ea9cc1c1439d0264 | d8b848ad716fa8ed78ec43cf4d2e542f58044087 | present | 21 |
| RC-22 | The base harness has no phase trail and no teardown budget. | tests/e2e/conftest.py | 6fb9f483a65f825cd5f8e7e5ea9cc1c1439d0264 | d8b848ad716fa8ed78ec43cf4d2e542f58044087 | absent | 0 |
| RC-23 | The test `test_progress_region_shows_every_section_of_the_status_body` exists on main. | tests/e2e/upgrade_portal/test_capture.py | main | b8e5896c26ac04b42579c943b2facbe40d7e9ad7 | present | 395 |
| RC-24 | The test `test_start_button_starts_a_capture` exists on main. | tests/e2e/upgrade_portal/test_capture.py | main | b8e5896c26ac04b42579c943b2facbe40d7e9ad7 | present | 415 |
| RC-25 | The base commit has the same two test names. | tests/e2e/upgrade_portal/test_capture.py | 6fb9f483a65f825cd5f8e7e5ea9cc1c1439d0264 | b8fed6091946f505548c48d34c3ca9b354a8659e | present | 391 |
| RC-26 | The fixture `capture_page` exists on main. | tests/e2e/upgrade_portal/test_capture.py | main | b8e5896c26ac04b42579c943b2facbe40d7e9ad7 | present | 287 |
| RC-27 | The pyproject lists the pin `pytest-timeout==2.4.0`. | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 111 |
| RC-28 | The development requirements pin `pytest-timeout==2.4.0`. | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 335 |
| RC-29 | The shard guard pins `--timeout=180`. | tests/guardrails/test_e2e_shard_partition.py | main | 8d9f45db72e88e5a48d3f2e561e3e2cba9e89fd3 | present | 27 |
| RC-30 | The runtime budget guard pins the shard limit at 20 minutes. | tests/guardrails/test_ci_runtime_budgets.py | main | 8d7c69490b6566ea16ebb9539b1a9786728c30c3 | present | 33 |
| RC-31 | The browser installation guard pins a 20-minute limit. | tests/guardrails/e2e_timeout_budget/test_browser_installation.py | main | c888d9b8a54fee953fb5db98660a63f44ccfa1c6 | present | 43 |
| RC-32 | The timeout guard pins the thread method. | tests/guardrails/e2e_timeout_budget/test_timeout_budget.py | main | fa1bdd47ebb65d4712f5ae0f9a48c4034d985e01 | present | 272 |
| RC-33 | The quality-gate document lists the `playwright` row without shard details. | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 68 |
| RC-34 | The quality-gate document gives the 120-second budget for coverage shards only. | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 53 |
| RC-35 | Git ignores `/test-artifacts/`. | .gitignore | main | 17eadfadb35a59e191a61c78877569ad747ddcc7 | present | 107 |
| RC-36 | The changelog fragment rule has a section named "Name the file". | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 19 |
| RC-37 | The changelog policy guard exists. | tests/guardrails/test_changelog_fragment_policy.py | main | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 0 |
| RC-38 | The reference record exists on main. | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv | main | 00922155516e4f21e34a0bf75613fae7ab481193 | present | 0 |
| RC-39 | The route folder for issue 3736 does not exist on main. | specs/numbered/0/0/1/0/4/4/2/1 | main | not applicable: path absent | absent | 0 |
| RC-40 | No record for issue 3736 exists on main. | specs/numbered/**/3736-* | main | not applicable: no matching path | absent | 0 |
| RC-41 | The installed plugin sets the item timer before the protocol. | .venv\Lib\site-packages\pytest_timeout.py (pytest-timeout 2.4.0) | installed package | 7c220699e235627c4eb8d0ecbdd7a2683f9978ca | present | 179 |
| RC-42 | The installed plugin prefers the item marker to the CLI value. | .venv\Lib\site-packages\pytest_timeout.py (pytest-timeout 2.4.0) | installed package | 7c220699e235627c4eb8d0ecbdd7a2683f9978ca | present | 388 |
| RC-43 | The installed plugin returns silently when it detects a debugger. | .venv\Lib\site-packages\pytest_timeout.py (pytest-timeout 2.4.0) | installed package | 7c220699e235627c4eb8d0ecbdd7a2683f9978ca | present | 485 |
| RC-44 | The debugger check reads a fixed module list and a registered tool. | .venv\Lib\site-packages\pytest_timeout.py (pytest-timeout 2.4.0) | installed package | 7c220699e235627c4eb8d0ecbdd7a2683f9978ca | present | 262 |
| RC-45 | The thread method ends the process with `os._exit`. | .venv\Lib\site-packages\pytest_timeout.py (pytest-timeout 2.4.0) | installed package | 7c220699e235627c4eb8d0ecbdd7a2683f9978ca | present | 542 |
| RC-46 | The pytest faulthandler plugin duplicates the stderr descriptor at configure time. | .venv\Lib\site-packages\_pytest\faulthandler.py (pytest 9.2.0) | installed package | e92b9893622e10ad05b9dfafa799ccbc37dda997 | present | 44 |
| RC-47 | The pytest faulthandler plugin arms a dump only when its option is above zero. | .venv\Lib\site-packages\_pytest\faulthandler.py (pytest 9.2.0) | installed package | e92b9893622e10ad05b9dfafa799ccbc37dda997 | present | 96 |
| RC-48 | The Python faulthandler documentation describes the watchdog dump. | https://docs.python.org/3/library/faulthandler.html | fetched 2026-11-26 | not applicable: web page | present | 0 |
| RC-49 | The harness on main has module-level hooks that delegate to the classes (teardown hook at line 229 and logreport hook at line 245). | tests/e2e/conftest.py | main | e450e1855770d2e0ec587935a95233262b118ae1 | present | 229 |
| RC-50 | The shard job runs on `ubuntu-latest`. | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 781 |
| RC-51 | Commit 38d06c48 (2026-10-03) changes the single E2E job limit from 15 to 20 minutes. The hunk adds the new value at line 741. | .github/workflows/ci.yml | commit 38d06c48aa01c553ff2fa4d16d819f82dd68dc94 | 38d06c48aa01c553ff2fa4d16d819f82dd68dc94 | present | 741 |
| RC-52 | Commit 0f42cdea (2026-10-16, PR #4251) splits the E2E suite into shards. | .github/workflows/ci.yml | commit 0f42cdea6e96b4e5a416e413562a6101aa4f8e37 | 0f42cdea6e96b4e5a416e413562a6101aa4f8e37 | present | 0 |
| RC-53 | Commit 4f3fb450 (2026-10-06, PR #3974) adds the session teardown budget and the phase trail. | tests/e2e/conftest.py | commit 4f3fb450e77d856d1bd533f7d6e49ea0c4bfa664 | 4f3fb450e77d856d1bd533f7d6e49ea0c4bfa664 | present | 0 |
| RC-54 | Commit de2b4667 (2026-11-12, PR #4617) adds the Ubuntu package mirror preparation step. | .github/workflows/ci.yml | commit de2b4667ae8da573090b4775de4a662160590919 | de2b4667ae8da573090b4775de4a662160590919 | present | 0 |
| RC-55 | The changelog folder holds 335 direct children on main. | changelog.d | main | not applicable: folder count | present | 0 |

Blob SHA values come from the remote tree or the contents API. Local rows use `git hash-object --no-filters` on the installed files, and they name the installed package version.

## 10. Decisions

Each decision gives the alternatives, the chosen option, the reason, and the risk. The decisions cover technical and process choices. No decision falls in a section 6 category, so none needs a human decision.

- **D-1 Stack dump mechanism.** Alternatives: keep the signal method only, switch to the pytest-timeout thread method, enable pytest's `faulthandler_timeout` option, or attach an external sampler. Chosen: arm a `faulthandler.dump_traceback_later` watch per item and write to `test-artifacts/e2e-stack-dumps.txt`. Reason: the watchdog runs on a C thread, so it works when the main thread is blocked (row RC-48). It needs no new dependency. Pytest's option writes to the descriptor captured at configure time (RC-46, RC-47), so its output routing depends on capture state. Risk: dumps occur for slow but healthy items. The dump file has no effect on outcomes.
- **D-2 Threshold of 100 seconds.** Alternatives: 60, 90, and 110 seconds. Chosen: 100 seconds. Reason: the shortest stall silence in section 6.3 was 104.1 seconds, so a 100-second watch fires before that silence ends. The value stays 20 seconds below the 120-second per-test budget. Risk: items longer than 100 seconds produce dump text.
- **D-3 Boundary records in the existing trail.** Alternatives: rely on the pytest item-name line, or create a separate file. Chosen: append `protocol_start` and `protocol_end` records to the existing trail. Reason: the stall logs show no partial line for the next item before the cancellation (section 6.3). A record written before and after each protocol identifies the open item. Risk: the trail grows by two lines for each item.
- **D-4 Budgets unchanged.** Alternatives: set the CLI value to 120, remove the CLI option, or raise the per-test budget or the job limit. Chosen: keep `E2E_TIMEOUT_SECONDS = 120`, `--timeout=180`, the 20-minute shard limit, the 5-minute aggregator limit, and the 30-minute journeys limit. Reason: the issue forbids a timeout increase, and three guards pin these values (RC-29, RC-30, RC-31). Risk: the CLI value stays misleading. D-9 addresses that risk in the documentation.
- **D-5 Signal method retained.** Alternatives: switch to the thread method. Chosen: keep the signal method. Reason: the thread method ends the process at the first overrun (RC-45). Remaining cases would then go unmeasured, and the issue requires a measured result for every case. Risk: the signal timer did not produce a report in the stall events (section 7). The watch from D-1 supplies the evidence that a repair needs.
- **D-6 Cancel message names both causes.** Alternatives: remove the step. Chosen: reword the message to name the job limit, the concurrency cancel, and the artifact. Reason: run 44962483189 showed a concurrency cancel with the limit message. Risk: none for behavior.
- **D-7 Pull request keyword.** Alternatives: use `Closes #3736`. Chosen: use `Refs #3736`. Reason: the owner states on 2026-10-02 (IC_kwDOQltU8c8AAAABY2yv_A) and on 2026-10-06 (IC_kwDOQltU8c8AAAABZw8ILg) that the issue stays open. The root cause remains unknown. The brief template asks for `Closes`, so the orchestrator must confirm this deviation. Risk: the issue stays open after the merge.
- **D-8 Closure rule.** Alternatives: close after a fixed number of green runs. Chosen: no automatic closure rule. The owner closes #3736 after recording a root cause or an accepted no-recurrence result. Reason: the owner controls the issue state. Risk: the issue stays open for a long time.
- **D-9 Documentation of budgets.** Alternatives: leave the document unchanged, or change the CLI value. Chosen: update `documentation/quality-gates.md` for the shard rows, the 20-minute limits, the effective 120-second budget, and the diagnostics artifact. Reason: the document lists `playwright` only, and it gives the 120-second value for coverage shards only (RC-33, RC-34). Risk: the document can drift again.
- **D-10 Plugin object for new hooks.** Alternatives: add module-level hook functions like the existing ones in `tests/e2e/conftest.py`. Chosen: put the new hooks in a class and register an instance in `pytest_configure`. Reason: the constitution (Principle II) forbids a standalone wrapper function that only delegates to a class method. The existing module-level hooks predate this record. Risk: the file mixes two styles.
- **D-11 Shard split retained.** Alternatives: return to one job, or raise the single job limit. Chosen: keep the shards. Reason: the four stall events occurred in the single-job era, and the shard-era events show no stall (section 6.4). Risk: the mechanism remains unknown. D-1 covers that risk.
- **D-12 Changelog name.** Alternatives: name the fragment `pr-<number>.md` after the pull request opens. Chosen: use `issue-3736-e2e-stall-diagnostics.md`. Reason: the pull request number does not exist when the commit is made, and the rule in `changelog.d/README.md` allows the issue form (RC-36). Risk: none for behavior.

## 11. Sources

Local paths and URLs used in this record:

- `.github/workflows/ci.yml` (main blob d51efbc13c0f0a2076680030ed8be7ef7cf64523, base blob cc41c46b8c23d291b73d9137bc78d5765202ded9).
- `tests/e2e/conftest.py` (main blob e450e1855770d2e0ec587935a95233262b118ae1, base blob d8b848ad716fa8ed78ec43cf4d2e542f58044087).
- `tests/e2e/upgrade_portal/test_capture.py` (main blob b8e5896c26ac04b42579c943b2facbe40d7e9ad7, base blob b8fed6091946f505548c48d34c3ca9b354a8659e).
- `.venv\Lib\site-packages\pytest_timeout.py`, `.venv\Lib\site-packages\_pytest\faulthandler.py`.
- `AGENTS.md`, `.github/copilot-instructions.md`, `.specify/memory/constitution.md`, `documentation/quality-gates.md`, and `changelog.d/README.md` on main.
- `https://docs.python.org/3/library/faulthandler.html`.

## 12. Unverified

- U-1: The cause of the four stall events. No stack dump or phase trail exists for those runs.
- U-2: Why the signal timer produced no report during the stall events. Running a test is outside this record's rules, and no local source explains the silence.
- U-3: Whether the Playwright sync dispatcher affects signal delivery. No web source was fetched for this question.
- U-4: The pytest version used by the CI runner at the failing head. The attempt-1 log header omits the pytest version.
- U-5: The artifact retention period for the repository. No API call checked it.
- U-6: The cause of the non-limit E2E failures in the scanned windows. About 230 non-limit jobs were counted and not parsed.
- U-7: Whether a single pytest process causes the stall class. The record states this as a hypothesis, supported only by the era split in section 6.4.
- U-8: The effect of the shard split on the upgrade-portal boundary test. No controlled run exists.
- U-9: Whether the three concurrency-labeled cancellations in section 6.5 hid a limit event. The annotations show no limit text for those jobs.
- U-10: The log of job 122682105845 (run 40647974378, earlier attempt). The API returns HTTP 404, so its silence is unknown.
