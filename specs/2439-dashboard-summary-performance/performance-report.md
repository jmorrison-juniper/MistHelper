# Python Performance Report: Dashboard data summary

## 1. Executive summary

**Measured**: The web portal dashboard summary now scans the data directory once
and formats only the five rows that the page renders. The 5000-file workload
improved from 289,616,000 ns to 57,109,400 ns median wall time. This is an
80.28 percent time reduction. Application parallelization stayed out of scope.

## 2. Environment and Python version

**Measured**: CPython 3.13.3 ran from
`C:\Users\jmorrison\AppData\Local\Programs\Python\Python313\python.exe` on
Windows 11 AMD64. The host reported 32 logical cores. The repository baseline
was `81dcef84c240ce97f6b2c9cde9b1600da75d5275`. The candidate ran from branch
`chore/2439-dashboard-summary-performance`.

## 3. Benchmark methodology

**Measured**: The harness called
`web_portal.routes.dashboard._build_data_summary(data_dir)`. The fixture was a
disposable local directory with 5000 visible CSV files and hidden CSV files.
Each visible file had a unique timestamp and a small body. The timed boundary
started before the function call and ended after the returned dict was built.

Timing used `time.perf_counter_ns()` and `time.process_time_ns()`. Each run used
7 warmups and 51 samples. Memory used a separate `tracemalloc` interval.

Artifacts:

- `C:\Users\jmorrison\.copilot\session-state\76354831-7a9d-41c9-b7dc-933e025bc5a8\files\opt_dashboard_summary_bench.py`
- `C:\Users\jmorrison\.copilot\session-state\76354831-7a9d-41c9-b7dc-933e025bc5a8\files\opt_dashboard_baseline_v4.json`
- `C:\Users\jmorrison\.copilot\session-state\76354831-7a9d-41c9-b7dc-933e025bc5a8\files\opt_dashboard_candidate_v4.json`
- `C:\Users\jmorrison\.copilot\session-state\76354831-7a9d-41c9-b7dc-933e025bc5a8\files\opt_dashboard_baseline_v4.pstats`
- `C:\Users\jmorrison\.copilot\session-state\76354831-7a9d-41c9-b7dc-933e025bc5a8\files\opt_dashboard_candidate_v4.pstats`

## 4. Baseline results

| Workload and state | Metric and unit | Median | MAD | Runs and values | Evidence artifact |
| --- | --- | --- | --- | --- | --- |
| 5000 files, warm filesystem | Wall time, ns | 289,616,000 | 43,418,100 | 51 samples | `opt_dashboard_baseline_v4.json` |
| 5000 files, warm filesystem | CPU time, ns | 234,375,000 | 46,875,000 | 51 samples | `opt_dashboard_baseline_v4.json` |
| 5000 files, warm filesystem | Traced peak bytes | 1,965,310 | Not measured | 1 memory sample | `opt_dashboard_baseline_v4.json` |

The baseline profile for 10 calls reported 50,000 timestamp format calls.

## 5. Ranked hotspot list

| Rank and status | File, symbol, and lines | Measured cost and frequency | Expected gain | Risk and maintenance cost | Confidence |
| --- | --- | --- | --- | --- | --- |
| 1, Measured | `web_portal/routes/dashboard.py`, `_get_recent_files()` | 50,000 timestamp formats for 10 calls | High | Low if stable order stays intact | High |
| 2, Measured | `web_portal/routes/dashboard.py`, `_build_data_summary()` | Two scans for one dashboard summary | Medium | Low | High |
| 3, Rejected | `web_portal/routes/dashboard.py`, bounded heap | Not retained | Could reduce memory more | Medium tie-order risk | High |

## 6. Recommended optimizations

**Measured**: Combine the count and recent-file scan for the dashboard summary.
Format only the selected rows. Preserve ordering with `heapq.nlargest()` and an
explicit key.

## 7. Implemented changes

| Field | Required content |
| --- | --- |
| Change ID and location | `DASH-SUMMARY-001`, `web_portal/routes/dashboard.py`, `_build_data_summary()` and `_scan_data_summary()` |
| Evidence | Baseline and candidate JSON and profile artifacts in the session folder |
| Root cause | The old path formatted every file and scanned twice although the dashboard renders five rows |
| Change | One scan counts visible files and stores raw metadata, then formats selected rows only |
| Before result | 289,616,000 ns median wall time, 43,418,100 ns MAD, 51 samples |
| After result | 57,109,400 ns median wall time, 11,163,900 ns MAD, 51 samples |
| Percentage change | `100 * (before - after) / before = 80.28%` time reduction |
| Memory change | Traced peak changed from 1,965,310 bytes to 630,294 bytes |
| Test coverage | `tests/unit/web_portal/test_dashboard_readiness.py` covers count, order, ties, empty input, and helper behavior |
| Risks | The main risk was equal timestamp ordering. Tests cover it. |
| Confidence level | High. Output names match, tests pass, and timing exceeds the acceptance threshold. |
| Retention decision | Retained. The end-to-end path improved by more than 5 percent. |

## 8. Before-and-after measurements

| Change and workload | Metric and unit | Before median and spread | After median and spread | Sample counts | Signed change | Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `DASH-SUMMARY-001`, 5000 files | Wall time, ns | 289,616,000, MAD 43,418,100 | 57,109,400, MAD 11,163,900 | 51 before, 51 after | -80.28% | Retained |
| `DASH-SUMMARY-001`, 5000 files | CPU time, ns | 234,375,000, MAD 46,875,000 | 46,875,000, MAD 0 | 51 before, 51 after | -80.00% | Retained |
| `DASH-SUMMARY-001`, 5000 files | Traced peak bytes | 1,965,310 | 630,294 | 1 before, 1 after | -1,335,016 bytes | Retained |

## 9. Memory impact

**Measured**: The traced Python peak changed from 1,965,310 bytes to 630,294
bytes for one measured call. This is a reduction of 1,335,016 bytes. The report
does not measure RSS or native memory.

## 10. Correctness and regression validation

| Check | Command or test | Actual result | Limitation or artifact |
| --- | --- | --- | --- |
| Unit tests | `python -m pytest tests\unit\web_portal\test_dashboard_readiness.py -q` | 25 passed | Windows and Python 3.13.3 |
| Output parity | Benchmark top-five names | Equal | Synthetic fixture |
| Ordering | Equal timestamp unit test | Passed | Test double controls scan order |

## 11. Rejected ideas and why they were rejected

| Idea and location | Evidence | Reason for rejection | Reverted or never implemented |
| --- | --- | --- | --- |
| Bounded heap in `_scan_data_summary()` | Rubber-duck review fuzzed tie cases | It can reorder equal timestamps | Never implemented |
| `heapq.nlargest()` without `key` | Rubber-duck review | Tuple comparison can change ties | Never implemented |
| Cache dashboard summary | Not measured | Freshness and invalidation risk exceed need | Never implemented |

## 12. Remaining opportunities

| Opportunity and status | Missing evidence or blocker | Exact next benchmark | Expected value and risk |
| --- | --- | --- | --- |
| Data browser CSV preview, Hypothesis | Need representative large CSV files | Benchmark `_preview_csv()` with search and no-search cases | Possible memory reduction, medium behavior risk |
| JSON preview streaming, Hypothesis | Need representative JSON and JSONL files | Benchmark `_preview_json()` with large files and malformed input | Possible memory reduction, high error-timing risk |
| Test quality analyzer detector loop, Hypothesis | Audit fleet still running | Profile `tools.test_quality_analyzer.__main__` on the full test tree | Possible CPU reduction, medium maintenance risk |

