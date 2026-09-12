# Performance report: data browser preview latency

## 1. Executive summary

**Measured**: Issue #2511 repairs the data browser preview latency path.
The retained change keeps bounded memory and removes measured wall time regressions.
The change uses sequential Python only.
No worker count changed.

**Measured**: State C is faster than state A for each measured workload, within measurement noise.
Peak traced memory stays near state B and far below state A.
The parity harness reports identical output dictionaries for states A, B, and C.

## 2. Environment and Python version

**Measured**: Python was CPython 3.13.3 on Windows 11 AMD64.
The benchmark used `C:\Users\jmorrison\AppData\Local\Programs\Python\Python313\python.exe`.
The worktree was `C:\Users\jmorrison\misthelper-opt2-browser-latency`.
The baseline worktree was `C:\Users\jmorrison\misthelper-opt2-browser-baseline`.

**Measured**: State A used commit `29fcb967`.
State B used commit `f4e58d63`.
State C used branch `perf/2511-data-browser-preview-latency`.
The benchmark asserted that `web_portal.services.data_browser` imported from the tested root.

## 3. Benchmark methodology

**Measured**: The harness file was `opt2_browserfix_benchmark.py`.
The fixture directory was `opt2_browser_fixtures` under the session artifact directory.
The harness used local disposable CSV, JSON Lines, JSON, and log files.
It did not call the Mist API.

**Measured**: Each timing run used 5 warmups and 31 samples.
Wall time used `time.perf_counter_ns()`.
CPU time used `time.process_time_ns()`.
Peak traced memory used `tracemalloc` in a separate pass.
Allocation tracing did not run during timing.
The harness ran one preview request per sample.

**Measured**: The parity harness was `opt2_browserfix_parity.py`.
It compared complete returned dictionaries for 13 cases.
The cases covered empty CSV, header-only CSV, small CSV, high pages, searches, malformed JSON, standard JSON, JSON Lines, and logs without a final newline.

## 4. Baseline results

**Measured**: State A results came from `opt2_browserfix_state_a_repeat.json`.
State B results came from `opt2_browserfix_state_b_repeat.json`.
State C results came from `opt2_browserfix_state_c_final2.json`.

| Workload | State A wall median ms | State B wall median ms | State C wall median ms | State C peak KiB |
| --- | ---: | ---: | ---: | ---: |
| CSV late page | 86.462 +/- 10.938 | 58.200 +/- 2.111 | 45.887 +/- 2.717 | 92.2 |
| CSV all match | 134.666 +/- 8.026 | 126.164 +/- 6.637 | 108.252 +/- 7.298 | 90.4 |
| JSON Lines | 114.753 +/- 8.026 | 164.152 +/- 12.985 | 108.292 +/- 18.174 | 60.4 |
| Log search | 124.591 +/- 10.437 | 59.988 +/- 4.346 | 61.511 +/- 4.122 | 46.5 |

## 5. Ranked hotspot list

| Rank and status | File, symbol, and lines | Measured cost and frequency | Expected gain | Risk and maintenance cost | Confidence |
| --- | --- | --- | --- | --- | --- |
| 1 Measured | `web_portal/services/data_browser.py`, JSON Lines preview | State B made 25,001 `json.loads` calls for 25,000 JSON Lines records. | Remove one parse and one partial scan. | Low risk because the first parsed item is reused. | High |
| 2 Measured | `web_portal/services/data_browser.py`, paginator tail buffers | State B made 151,618 deque append calls in the four profiled previews. | Remove appends that cannot affect the common page. | Medium risk because high pages need fallback rows. | High |
| 3 Measured | `web_portal/services/data_browser.py`, JSON Lines row search | State B spent time in row matching after row construction. | Fuse row construction and search. | Low risk because the same string values are searched. | Medium |

## 6. Recommended optimizations

**Measured**: Detect JSON Lines by reading the first two nonblank records.
Reuse the parsed first item when the second record confirms JSON Lines.
This removes the extra first-record parse and keeps bounded memory.

**Measured**: Stop appending every row to the fallback tail after the requested page starts.
A high page request still has the tail it needs, because the requested start is never reached.
A normal page request does not need later fallback rows.

**Rejected**: Restoring the old full-file JSON Lines implementation would recover some speed.
It would also restore file-size memory growth.
That violates the memory objective.

## 7. Implemented changes

| Field | Required content |
| --- | --- |
| Change ID and location | C1, `web_portal/services/data_browser.py`, JSON Lines detection and pagination. |
| Evidence | `opt2_browserfix_state_b_profile_summary.txt`, `opt2_browserfix_state_c_final2_profile_summary.txt`, and the three state JSON files. |
| Root cause | State B parsed the first JSON Lines record twice and appended rows to tail buffers on common requests. |
| Change | The preview reuses the parsed first item and keeps fallback tail rows only until the requested page starts. |
| Before result | State B JSON Lines wall median was 164.152 ms with MAD 12.985 ms. |
| After result | State C JSON Lines wall median was 108.292 ms with MAD 18.174 ms. |
| Percentage change | The JSON Lines wall time changed by -34.0 percent from state B to state C. |
| Memory change | JSON Lines peak traced memory changed from 68.9 KiB to 60.4 KiB. |
| Test coverage | Added JSON Lines single-pass coverage and filtered high page coverage. |
| Risks | The fallback tail logic could affect high page requests. The parity harness covers that case. |
| Confidence level | High. Unit tests, parity tests, profiling, and benchmarks agree. |
| Retention decision | Retain C1 because it meets the latency and memory criteria. |

## 8. Before-and-after measurements

| Workload | Metric | State A median and MAD | State B median and MAD | State C median and MAD | State C versus State A | Decision |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| CSV late page | Wall ms | 86.462 +/- 10.938 | 58.200 +/- 2.111 | 45.887 +/- 2.717 | -46.9 percent | Measured pass |
| CSV all match | Wall ms | 134.666 +/- 8.026 | 126.164 +/- 6.637 | 108.252 +/- 7.298 | -19.6 percent | Measured pass |
| JSON Lines | Wall ms | 114.753 +/- 8.026 | 164.152 +/- 12.985 | 108.292 +/- 18.174 | -5.6 percent | Measured pass |
| Log search | Wall ms | 124.591 +/- 10.437 | 59.988 +/- 4.346 | 61.511 +/- 4.122 | -50.6 percent | Measured pass |

**Measured**: Negative time change means a latency reduction.
Each sample count was 31.

## 9. Memory impact

| Workload | State A peak KiB | State B peak KiB | State C peak KiB |
| --- | ---: | ---: | ---: |
| CSV late page | 23961.2 | 91.8 | 92.2 |
| CSV all match | 24433.7 | 91.4 | 90.4 |
| JSON Lines | 15617.2 | 68.9 | 60.4 |
| Log search | 24739.9 | 46.5 | 46.5 |

**Measured**: State C keeps peak traced memory near the bounded state B result.
It does not restore the state A full-list behavior.

## 10. Correctness and regression validation

| Check | Command or test | Actual result | Limitation or artifact |
| --- | --- | --- | --- |
| Parity | `opt2_browserfix_parity.py` on states A, B, and C | Passed for 13 cases | `opt2_browserfix_parity_state_*.json` |
| Benchmark | `opt2_browserfix_benchmark.py` on states A, B, and C | Passed | `opt2_browserfix_state_*.json` |
| Profile | `opt2_browserfix_profile.py` on states B and C | Passed | `opt2_browserfix_state_*_profile_summary.txt` |
| Unit tests | `python -m pytest tests\unit\web_portal -q` | Passed locally | See validation output in the pull request |
| Compile | `python -m py_compile` on changed Python files | Passed locally | No limitation |
| Ruff | `python -m ruff check` on changed Python files | Passed locally | `web_portal` is excluded, but the command still ran |
| Black | `python -m black --check` on changed Python files | Passed locally | No limitation |
| pydocstyle | `python -m pydocstyle` on changed Python files | Passed locally | No limitation |
| Bandit | `python -m bandit -q` on changed non-test Python files | Passed locally | No limitation |
| Diff check | `git diff --check` | Passed locally | No limitation |

## 11. Rejected ideas and why they were rejected

| Idea and location | Evidence | Reason for rejection | Reverted or never implemented |
| --- | --- | --- | --- |
| Restore old full-list JSON Lines parsing | State A JSON Lines was fast but used 15617.2 KiB peak traced memory. | It violates the bounded memory criterion. | Never implemented |
| Keep a tail buffer for every row | State B profile showed 151,618 deque append calls. | The common page does not need those appends. | Replaced |
| Use threads or processes | The task forbids worker changes. | It would change application concurrency. | Never implemented |

## 12. Remaining opportunities

| Opportunity and status | Missing evidence or blocker | Exact next benchmark | Expected value and risk |
| --- | --- | --- | --- |
| Hypothesis: specialize CSV search row matching | No profile shows it as the top remaining defect. | Add a CSV-only search benchmark with larger rows and compare medians. | Medium value, low risk |
| Hypothesis: reduce log search cell checks | The log path already beats state A. | Add a line-number search and text-only search split. | Low value, low risk |
| Blocked: production data validation | The task forbids production data and Mist API calls. | Use sanitized recordings if a maintainer supplies them. | Higher confidence, privacy risk if unsanitized |

