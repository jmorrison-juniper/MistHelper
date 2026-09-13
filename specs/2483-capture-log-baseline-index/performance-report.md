# Performance report: Capture log baseline index

## 1. Executive summary

**Measured**: The objective was to reduce end-to-end latency for `tools.capture_log_baseline` on `MistHelper.py`.
The retained change builds one call index for the parsed libcst module.
The median wall time changed from 22.521 s to 10.421 s across 11 samples.
This is a 53.729 percent time reduction.
The change clears the 5 percent end-to-end acceptance threshold.
Application parallel execution stayed out of scope.

## 2. Environment and Python version

**Measured**: The benchmark ran on Windows 11 AMD64 with CPython 3.13.3.
The Python executable was `C:\Users\jmorrison\AppData\Local\Programs\Python\Python313\python.exe`.
The module path was `C:\Users\jmorrison\misthelper-opt2-capture-log-baseline\tools\capture_log_baseline.py`.
The worktree was `C:\Users\jmorrison\misthelper-opt2-capture-log-baseline`.
The branch was `perf/2483-capture-log-baseline-index`.
The benchmark harness asserted that the import came from this worktree.

## 3. Benchmark methodology

**Measured**: The workload called `module.main(["--source", MistHelper.py, "--output", artifact])`.
The measured boundary included file read, parse, call lookup, rendering, and output write.
The harness used 2 warmups and 11 timed samples.
It used `time.perf_counter_ns()` for wall time.
It used `time.process_time_ns()` for CPU time.
It measured traced Python memory in a separate run with `tracemalloc` active outside the measured loop.
The acceptance rule required at least 5 percent end-to-end improvement.

## 4. Baseline results

| Workload and state | Metric and unit | Median | MAD | Runs and values | Evidence artifact |
| --- | --- | --- | --- | --- | --- |
| `MistHelper.py`, warm file system | wall seconds | 22.521 | 3.933 | 11 samples | `opt2_caplog_baseline_raw.json` |
| `MistHelper.py`, warm file system | CPU seconds | 17.453 | 2.797 | 11 samples | `opt2_caplog_baseline_raw.json` |
| `MistHelper.py`, traced memory | peak traced bytes | 29,168,041 | Not measured | 1 repeat | `opt2_caplog_baseline_raw.json` |

**Measured**: `tests\test_issue_429_log_parity.py` passed with 4 tests and 1 skipped test before the edit.

## 5. Ranked hotspot list

| Rank and status | File, symbol, and lines | Measured cost and frequency | Expected gain | Risk and maintenance cost | Confidence |
| --- | --- | --- | --- | --- | --- |
| 1. Measured | `tools/capture_log_baseline.py`, `_render_call_at_line()` | The profile made 5 metadata wrapper walks. `base.py:327(deep_clone)` used 22.453 s cumulative. | High, because one index can replace repeated walks. | Low, if visit order stays stable. | High |
| 2. Measured | libcst parse | `entrypoints.py:25(_parse)` used about 1.5 s in the candidate profile. | Low for this task. | Medium, because parse reuse can change errors. | Medium |

## 6. Recommended optimizations

**Measured**: Build one line-to-call index after parsing the source module.
This changes fixture lookup from repeated full tree walks to one tree walk plus dictionary lookup.
The risk is same-line call selection.
The tests verify that the first call stays selected.

**Hypothesis**: A future change can parse each per-site source file once and build one index for each file.
This needs a fixture set that exercises the `source` override field.

## 7. Implemented changes

| Field | Required content |
| --- | --- |
| Change ID and location | `CAPLOG-INDEX-2483` in `tools/capture_log_baseline.py`, `_index_calls_by_line()` and `_render_call_at_line()` |
| Evidence | Baseline and candidate raw JSON files in the session artifact folder. Profiles are `opt2_caplog_baseline.prof` and `opt2_caplog_candidate.prof`. |
| Root cause | `_render_call_at_line()` built metadata and walked the libcst tree for each fixture site. |
| Change | Build one index from line number to `cst.Call` list. Reuse it for all fixture sites. |
| Before result | Wall median 22.521 s, MAD 3.933 s, 11 samples. |
| After result | Wall median 10.421 s, MAD 3.419 s, 11 samples. |
| Percentage change | `100 * (after - before) / before = -53.729%` for wall time. |
| Memory change | Peak traced Python bytes changed from 29,168,041 to 29,121,057. This is 46,984 fewer bytes. |
| Test coverage | Added same-line first-call coverage and old collector parity coverage. |
| Risks | The index keeps libcst visit order and selects the first call for a line. |
| Confidence level | High, because output comparison and focused tests passed. |
| Retention decision | Retained, because the end-to-end median improved by more than 5 percent. |

## 8. Before-and-after measurements

| Change and workload | Metric and unit | Before median and spread | After median and spread | Sample counts | Signed change | Decision |
| --- | --- | --- | --- | --- | --- | --- |
| Call line index on `MistHelper.py` | wall seconds | 22.521 median, 3.933 MAD | 10.421 median, 3.419 MAD | 11 before, 11 after | -53.729 percent | Retained |
| Call line index on `MistHelper.py` | CPU seconds | 17.453 median, 2.797 MAD | 5.250 median, 0.891 MAD | 11 before, 11 after | -69.919 percent | Retained |

## 9. Memory impact

**Measured**: Peak traced Python memory changed from 29,168,041 bytes to 29,121,057 bytes.
The measured difference was -46,984 bytes.
This was a separate traced memory run.
Traced memory is not process RSS.

## 10. Correctness and regression validation

| Check | Command or test | Actual result | Limitation or artifact |
| --- | --- | --- | --- |
| Output parity | Compare SHA-256 of baseline and candidate output | Passed. Both files had SHA-256 `e3566b3a06430868d71e9287dfd6c6c520a3da027aabea01951d407ee131dc2f`. | The current fixture output has zero entries. |
| Targeted tests | `rtk python -m pytest tests\test_issue_429_log_parity.py -q` | Passed. 6 passed and 1 skipped. | The skipped site is absent from the fixture file. |
| Compile | `rtk python -m py_compile tools\capture_log_baseline.py tests\test_issue_429_log_parity.py` | Passed. | None. |
| Lint | `rtk python -m ruff check tools\capture_log_baseline.py tests\test_issue_429_log_parity.py` | Passed. | None. |
| Format | `rtk python -m black --check tools\capture_log_baseline.py tests\test_issue_429_log_parity.py` | Passed. | None. |
| Docstrings | `rtk python -m pydocstyle tools\capture_log_baseline.py tests\test_issue_429_log_parity.py` | Passed. | None. |
| Security | `rtk python -m bandit -q tools\capture_log_baseline.py` | Passed. | Test files were out of scope. |
| Diff whitespace | `rtk git diff --check` | Passed. | None. |

## 11. Rejected ideas and why they were rejected

| Idea and location | Evidence | Reason for rejection | Reverted or never implemented |
| --- | --- | --- | --- |
| Parse source only once across process runs | Hypothesis | The CLI process pays parse cost on each run. A persistent cache would change lifecycle behavior. | Never implemented |
| Use parallel fixture lookup | Rejected | The task prohibited parallel execution. | Never implemented |

## 12. Remaining opportunities

| Opportunity and status | Missing evidence or blocker | Exact next benchmark | Expected value and risk |
| --- | --- | --- | --- |
| Source-aware fixture capture. Hypothesis | The current tool does not use the fixture `source` override in `main()`. | Add a workload with multiple source files and compare byte output. | It could improve correctness. It may change current skip behavior. |
