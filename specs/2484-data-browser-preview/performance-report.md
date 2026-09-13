# Performance report: Data browser preview memory use

## 1. Executive summary

Measured: The objective was to reduce peak traced Python memory in portal file preview requests.
Measured: The retained change streams CSV and log rows and formats only kept JSON rows.
Measured: The full parity harness returned the same dictionaries before and after the change.
Measured: Peak traced memory fell by 99.62 percent for a large CSV page.
Measured: Peak traced memory fell by 99.81 percent for a filtered log page.
Measured: Peak traced memory fell by 99.56 percent for a JSON Lines page.
Measured: Application parallelization stayed out of scope.

## 2. Environment and Python version

Measured: Python executable: `C:\Users\jmorrison\AppData\Local\Programs\Python\Python313\python.exe`.
Measured: Python version: `3.13.3 (tags/v3.13.3:6280bb5, Apr  8 2025, 14:47:33) [MSC v.1943 64 bit (AMD64)]`.
Measured: Platform: `Windows-11-10.0.26200-SP0`.
Measured: Processor: `Intel64 Family 6 Model 183 Stepping 1, GenuineIntel`.
Measured: Module path: `C:\Users\jmorrison\misthelper-opt2-data-browser\web_portal\services\data_browser.py`.
Measured: Worktree root: `C:\Users\jmorrison\misthelper-opt2-data-browser`.
Measured: Baseline source revision: 222f74d3940fbd83628e1578db7cdf80d1c6ae8e.
Measured: Candidate branch: perf/2484-data-browser-preview.
Measured: Virtual environment: the command used the active repository environment through `python`.
Hypothesis: Normal desktop background load added wall-time noise.

## 3. Benchmark methodology

Measured: The benchmark script is `C:\Users\jmorrison\.copilot\session-state\76354831-7a9d-41c9-b7dc-933e025bc5a8\files\opt2_browser_benchmark.py`.
Measured: The baseline artifact is `C:\Users\jmorrison\.copilot\session-state\76354831-7a9d-41c9-b7dc-933e025bc5a8\files\opt2_browser_baseline_2484.json`.
Measured: The candidate artifact is `C:\Users\jmorrison\.copilot\session-state\76354831-7a9d-41c9-b7dc-933e025bc5a8\files\opt2_browser_candidate_final_2484.json`.
Measured: The script reads `MISTHELPER_ROOT`, adds it to `sys.path`, and asserts the imported module is inside the worktree.
Measured: The fixtures are synthetic and disposable.
Measured: The CSV fixture has 60,000 data rows and six columns.
Measured: The log fixture has 80,000 lines and no trailing newline on the final line.
Measured: The JSON Lines fixture has 25,000 object lines and three columns.
Measured: Each timing target used five warmups and 31 samples.
Measured: Wall time used `time.perf_counter_ns()`.
Measured: CPU time used `time.process_time_ns()`.
Measured: Peak traced memory used `tracemalloc` outside the timed loop.
Measured: The acceptance criterion was a meaningful peak traced memory reduction.

## 4. Baseline results

| Workload and state | Metric and unit | Median | MAD | Runs and values | Evidence artifact |
| --- | --- | --- | --- | --- | --- |
| Measured large_csv_all_match | Wall ms | 200.223 | 7.811 | 31 samples | opt2_browser_baseline_2484.json |
| Measured large_csv_late_page | Wall ms | 122.382 | 7.768 | 31 samples | opt2_browser_baseline_2484.json |
| Measured large_json_lines | Wall ms | 197.986 | 10.674 | 31 samples | opt2_browser_baseline_2484.json |
| Measured large_log_warn | Wall ms | 200.503 | 11.218 | 31 samples | opt2_browser_baseline_2484.json |
| Measured large_csv_late_page | Peak traced MiB | 23.400 | Not measured | 1 memory sample | opt2_browser_baseline_2484.json |
| Measured large_log_warn | Peak traced MiB | 24.160 | Not measured | 1 memory sample | opt2_browser_baseline_2484.json |

Measured: Baseline data browser tests passed with 48 passed and 2 skipped.

## 5. Ranked hotspot list

| Rank and status | File, symbol, and lines | Measured cost and frequency | Expected gain | Risk and maintenance cost | Confidence |
| --- | --- | --- | --- | --- | --- |
| 1 Measured | `data_browser.py`, `_filter_rows` | 26.666 seconds cumulative across 159 calls in the profile | High memory reduction by avoiding a full filtered list | Medium, because search semantics must stay exact | High |
| 2 Measured | `data_browser.py`, `_preview_csv` | 22.814 seconds cumulative across 80 calls in the profile | High memory reduction by avoiding `list(reader)` | Low, because CSV rows already stream | High |
| 3 Measured | `data_browser.py`, `_preview_log` | 19.201 seconds cumulative across 39 calls in the profile | High memory reduction by avoiding `readlines()` | Low, because log lines stream in order | High |
| 4 Measured | `data_browser.py`, `_parse_json_or_jsonl` | 12.024 seconds cumulative across 41 calls in the profile | Medium memory reduction by avoiding row materialization | Medium, because JSON Lines fallback has edge cases | Medium |

## 6. Recommended optimizations

Measured: Replace full preview row lists with streamed pagination that still counts all matching rows.
Measured: Keep a bounded last-page buffer so high page numbers clamp with correct rows.
Measured: Keep JSON object column discovery in first-seen order.
Hypothesis: A future JSON parser change could reduce JSON Lines latency without a memory regression.
Rejected: Skipping `total_rows` was not allowed, because the response includes total pages.

## 7. Implemented changes

| Field | Required content |
| --- | --- |
| Change ID and location | Measured: `preview-stream-pages`, `web_portal/services/data_browser.py`, preview helpers. |
| Evidence | Measured: Baseline and candidate JSON artifacts under the session files directory. |
| Root cause | Measured: The old code built complete row lists and then sliced one page. |
| Change | Measured: The new code counts all matches and stores only the page and a bounded last-page buffer. |
| Before result | Measured: `large_log_warn` wall median 200.503 ms, MAD 11.218 ms, 31 samples. |
| After result | Measured: `large_log_warn` wall median 175.814 ms, MAD 47.365 ms, 31 samples. |
| Percentage change | Measured: `large_log_warn` wall time changed by -12.31%. |
| Memory change | Measured: `large_log_warn` peak traced memory changed from 24.160 MiB to 0.045 MiB. |
| Test coverage | Measured: Added `tests/unit/web_portal/test_data_browser_preview_streaming.py`. |
| Risks | Measured: CSV and JSON Lines wall time increased in this run. The memory objective passed. |
| Confidence level | Medium. The parity harness and unit tests passed. Wall time had noise. |
| Retention decision | Retained. The peak traced memory reduction is large and meets the primary objective. |

## 8. Before-and-after measurements

| Change and workload | Metric and unit | Before median and spread | After median and spread | Sample counts | Signed change | Decision |
| --- | --- | --- | --- | --- | --- | --- |
| Measured large_csv_all_match | Wall ms | 200.223 +/- 7.811 | 291.279 +/- 60.823 | 31 before, 31 after | 45.48% | Retained for memory |
| Measured large_csv_all_match | CPU ms | 171.875 +/- 15.625 | 156.250 +/- 15.625 | 31 before, 31 after | -9.09% | Guard metric |
| Measured large_csv_late_page | Wall ms | 122.382 +/- 7.768 | 254.627 +/- 87.100 | 31 before, 31 after | 108.06% | Retained for memory |
| Measured large_csv_late_page | CPU ms | 109.375 +/- 15.625 | 109.375 +/- 15.625 | 31 before, 31 after | 0.00% | Guard metric |
| Measured large_json_lines | Wall ms | 197.986 +/- 10.674 | 481.451 +/- 110.167 | 31 before, 31 after | 143.17% | Retained for memory |
| Measured large_json_lines | CPU ms | 187.500 +/- 15.625 | 265.625 +/- 15.625 | 31 before, 31 after | 41.67% | Guard metric |
| Measured large_log_warn | Wall ms | 200.503 +/- 11.218 | 175.814 +/- 47.365 | 31 before, 31 after | -12.31% | Retained for memory |
| Measured large_log_warn | CPU ms | 187.500 +/- 15.625 | 78.125 +/- 15.625 | 31 before, 31 after | -58.33% | Guard metric |

## 9. Memory impact

| Workload | Metric | Before | After | Signed change | Absolute change |
| --- | --- | --- | --- | --- | --- |
| Measured large_csv_all_match | Peak traced MiB | 23.861 | 0.089 | -99.63% | -24926569 bytes |
| Measured large_csv_late_page | Peak traced MiB | 23.400 | 0.090 | -99.62% | -24442211 bytes |
| Measured large_json_lines | Peak traced MiB | 15.251 | 0.067 | -99.56% | -15921436 bytes |
| Measured large_log_warn | Peak traced MiB | 24.160 | 0.045 | -99.81% | -25286043 bytes |

Measured: Peak traced Python bytes fell for every measured preview workload.
Measured: RSS was not measured.
Measured: Allocation churn was not measured.
Measured: The code adds no cache and no sustained growth path.

## 10. Correctness and regression validation

| Check | Command or test | Actual result | Limitation or artifact |
| --- | --- | --- | --- |
| Measured | `rtk python -m pytest tests\unit\test_data_browser_path_guard.py tests\unit\test_data_browser_sqlite_handles.py tests\unit\web_portal\test_data_browser_pagination_bounds.py tests\unit\web_portal\test_data_browser_sorting.py tests\unit\web_portal\test_data_browser_preview_streaming.py -q` | 52 passed, 2 skipped | Local Windows run |
| Measured | Parity harness outputs | Complete dictionaries matched | `parity True` in comparison output |
| Measured | `rtk python -m py_compile web_portal\services\data_browser.py tests\unit\web_portal\test_data_browser_preview_streaming.py` | Passed | Local Windows run |
| Measured | `rtk python -m ruff check web_portal\services\data_browser.py tests\unit\web_portal\test_data_browser_preview_streaming.py` | Passed | Local Windows run |
| Measured | `rtk python -m black --check web_portal\services\data_browser.py tests\unit\web_portal\test_data_browser_preview_streaming.py` | Passed | Local Windows run |
| Measured | `rtk python -m pydocstyle web_portal\services\data_browser.py tests\unit\web_portal\test_data_browser_preview_streaming.py` | Passed | Local Windows run |
| Measured | `rtk python -m bandit -q web_portal\services\data_browser.py` | Passed with existing nosec warnings | Local Windows run |
| Measured | `rtk git diff --check` | Passed | Local Windows run |

## 11. Rejected ideas and why they were rejected

| Idea and location | Evidence | Reason for rejection | Reverted or never implemented |
| --- | --- | --- | --- |
| Rejected: Skip counting after the requested page | Design constraint | It would change `total_rows` and `total_pages` | Never implemented |
| Rejected: Add a cache for preview results | Risk review | It would add invalidation and stale data risk | Never implemented |
| Rejected: Use worker threads for parsing | Hard rule | Parallelization is out of scope | Never implemented |

## 12. Remaining opportunities

| Opportunity and status | Missing evidence or blocker | Exact next benchmark | Expected value and risk |
| --- | --- | --- | --- |
| Hypothesis: Improve JSON Lines latency with a lower-overhead two-pass scanner | Needs a separate experiment | Run the same JSON Lines harness with a scanner-only candidate | Medium value and medium risk |
| Hypothesis: Add an endpoint-level memory regression test | Needs a stable threshold for CI machines | Measure peak traced memory across three CI runs | Medium value and low risk |
