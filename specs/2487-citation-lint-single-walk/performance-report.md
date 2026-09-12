# Performance report: Citation reference lint performance

## 1. Executive summary

Measured. The objective was to reduce the default citation lint path for the real repository tree. The retained change builds the default file index and source list in one repository walk. It also skips regex work on lines that cannot hold a citation. Application parallelization stayed out of scope.

Measured. The baseline wall median was 78,595.081 ms. The candidate wall median was 26,092.488 ms. The signed change was -66.80 percent with 5 samples. This passes the 5 percent end-to-end threshold.

## 2. Environment and Python version

Measured. Python was CPython 3.13.3 on Windows 11 AMD64. The executable was `C:\Users\jmorrison\AppData\Local\Programs\Python\Python313\python.exe` in the local worktree run. The worktree was `C:\Users\jmorrison\misthelper-opt2-check-citations`. The branch was `perf/2487-citation-lint-single-walk`.

Measured. The baseline source was the unmodified branch state before the source edit. The candidate source was the same branch after the retained edit. The benchmark harness was `C:\Users\jmorrison\.copilot\session-state\76354831-7a9d-41c9-b7dc-933e025bc5a8\files\opt2_citations_benchmark.py`.

## 3. Benchmark methodology

Measured. The entry point was `python -m tools.check_citations src tests specs documentation tools`. The input was the real repository tree. The expected output was 1,636 checked citations and 17 unresolved citations. The measured boundary was the `main()` call with stdout capture.

Measured. The timing run used one warmup and five samples. The memory run used `tracemalloc` outside the measured call. The harness used `time.perf_counter_ns()` for wall time and `time.process_time_ns()` for CPU time. The filesystem cache was warm after the warmup. No OS cache reset was attempted.

Measured. The harness inserted the worktree path at `sys.path[0]`. It asserted that `tools.check_citations.__file__` was inside the worktree. The harness counted file opens, file read calls, bytes read, `os.walk` calls, and files seen in a separate counted run.

## 4. Baseline results

| Workload and state | Metric and unit | Median | MAD | Runs and values | Evidence artifact |
| --- | --- | --- | --- | --- | --- |
| Real tree, warm cache | Wall time, ms | 78,595.081 | 4,005.830 | 5 samples | `opt2_citations_baseline.json` |
| Real tree, warm cache | CPU time, ms | 31,265.625 | 4,078.125 | 5 samples | `opt2_citations_baseline.json` |
| Real tree, counted run | File opens | 4,545 | Not measured | 1 counted run | `opt2_citations_baseline.json` |
| Real tree, counted run | Read calls | 2,040,395 | Not measured | 1 counted run | `opt2_citations_baseline.json` |
| Real tree, counted run | `os.walk` calls | 10 | Not measured | 1 counted run | `opt2_citations_baseline.json` |
| Real tree, memory run | Peak traced bytes | 28,027,169 | Not measured | 1 memory run | `opt2_citations_baseline.json` |

Measured. The baseline unit test command passed with 6 tests before source edits.

## 5. Ranked hotspot list

| Rank and status | File, symbol, and lines | Measured cost and frequency | Expected gain | Risk and maintenance cost | Confidence |
| --- | --- | --- | --- | --- | --- |
| 1, Measured | `tools/check_citations.py`, `check_file()` | cProfile showed 24.788 s cumulative across 4,349 calls. Regex ran 1,892,764 times. | High, because most lines cannot hold citations. | Low. The marker check uses characters required by the existing regex. | High |
| 2, Measured | `tools/check_citations.py`, `build_index()` and `walk()` | cProfile showed 10 `os.walk` root calls in the counted run. | Medium for I/O. | Low for the default path. Custom roots keep the old two-walk rule. | High |
| 3, Measured | `tools/check_citations.py`, `line_count()` | The counted run opened 4,545 files. | Low to medium. Some target files are also source files. | Low. A source file count is exact after a successful read. | Medium |

## 6. Recommended optimizations

Measured. Retain a marker check before regex matching. The root cause was regex work on lines that cannot match. The smallest safe change checks for `:` and `/`, because the current pattern requires both characters.

Measured. Retain a single default repository walk. The root cause was separate default walks for the index and source list. The smallest safe change returns both results from one catalog builder. Custom roots keep their previous resolution rule.

Measured. Retain source line count reuse. The root cause was a later target count for a file already read as a source. The smallest safe change stores the source line count after a successful read.

## 7. Implemented changes

| Field | Required content |
| --- | --- |
| Change ID and location | `CIT-2487`, `tools/check_citations.py`, `build_catalog()`, `check_file()`, and `main()`. |
| Evidence | Baseline and candidate JSON files under the session artifact folder. Profiles are `opt2_citations_base.prof` and `opt2_citations_candidate_final.prof`. |
| Root cause | The tool walked default roots twice. It also ran regex matching on almost all source lines. |
| Change | Build the default catalog in one walk. Skip regex work unless a line has `:` and `/`. Cache source line counts. |
| Before result | Wall median 78,595.081 ms, MAD 4,005.830 ms, 5 samples. |
| After result | Wall median 26,092.488 ms, MAD 5,925.323 ms, 5 samples. |
| Percentage change | `100 * (after - before) / before = -66.80 percent`. Negative means reduced latency. |
| Memory change | Peak traced bytes changed from 28,027,169 to 27,725,997, a reduction of 301,172 bytes. |
| Test coverage | Added tests for the regex skip path and the default single-walk path. |
| Risks | A path with no `/` cannot match the current regex. A path with no `:` cannot name a line. Custom roots keep the old two-walk behavior. |
| Confidence level | High. The output and exit code matched exactly. The improvement exceeded the combined MAD. |
| Retention decision | Retained. The measured end-to-end improvement passed the 5 percent threshold. |

## 8. Before-and-after measurements

| Change and workload | Metric and unit | Before median and spread | After median and spread | Sample counts | Signed change | Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `CIT-2487`, real tree | Wall time, ms | 78,595.081, MAD 4,005.830 | 26,092.488, MAD 5,925.323 | 5 before, 5 after | -66.80 percent | Retained |
| `CIT-2487`, real tree | CPU time, ms | 31,265.625, MAD 4,078.125 | 9,484.375, MAD 1,062.500 | 5 before, 5 after | -69.67 percent | Retained |
| `CIT-2487`, counted run | File opens | 4,545 | 4,415 | 1 before, 1 after | -2.86 percent | Retained as supporting evidence |
| `CIT-2487`, counted run | Read calls | 2,040,395 | 1,937,936 | 1 before, 1 after | -5.02 percent | Retained as supporting evidence |
| `CIT-2487`, counted run | `os.walk` calls | 10 | 5 | 1 before, 1 after | -50.00 percent | Retained as supporting evidence |

Measured. The candidate output and exit code matched the baseline output and exit code exactly.

## 9. Memory impact

Measured. The memory metric was peak traced Python bytes from `tracemalloc`. The baseline peak was 28,027,169 bytes. The candidate peak was 27,725,997 bytes. The candidate reduced traced peak memory by 301,172 bytes.

Hypothesis. The small reduction comes from fewer target line count reads. The benchmark did not measure total process RSS or allocation churn.

## 10. Correctness and regression validation

| Check | Command or test | Actual result | Limitation or artifact |
| --- | --- | --- | --- |
| Baseline unit tests | `rtk python -m pytest tests\unit\tools\test_check_citations.py -q` | Passed, 6 tests | Baseline only |
| Candidate unit tests | `rtk python -m pytest tests\unit\tools\test_check_citations.py -q` | Passed, 8 tests | Targeted test file only |
| Syntax | `rtk python -m py_compile tools\check_citations.py tests\unit\tools\test_check_citations.py` | Passed | Changed Python files only |
| Lint | `rtk python -m ruff check tools\check_citations.py tests\unit\tools\test_check_citations.py` | Passed | Changed Python files only |
| Format | `rtk python -m black --check tools\check_citations.py tests\unit\tools\test_check_citations.py` | Passed | Changed Python files only |
| Docstring style | `rtk python -m pydocstyle tools\check_citations.py tests\unit\tools\test_check_citations.py` | Passed | Changed Python files only |
| Security lint | `rtk python -m bandit -q tools\check_citations.py` | Passed | Non-test changed Python file only |
| Whitespace | `rtk git diff --check` | Passed | Worktree diff only |
| Output parity | Benchmark harness captured stdout and exit code | Passed | Same arguments and warm-cache state |

## 11. Rejected ideas and why they were rejected

| Idea and location | Evidence | Reason for rejection | Reverted or never implemented |
| --- | --- | --- | --- |
| Parallel file checks | Policy | Sequential-only rule prohibits it. | Never implemented |
| Pre-count every source file before validation | Hypothesis | It could change internal read timing and needs a larger design. | Never implemented |
| Replace the citation regex | Hypothesis | It carries a higher behavior risk than the required-marker guard. | Never implemented |

## 12. Remaining opportunities

| Opportunity and status | Missing evidence or blocker | Exact next benchmark | Expected value and risk |
| --- | --- | --- | --- |
| Stream source files instead of `readlines()` | Hypothesis | Need output parity and memory evidence. | Run the same harness with a streaming parser branch. | Lower peak memory. Risk is line count timing. |
| Cache line counts after a full source parse phase | Hypothesis | Need proof that error timing stays acceptable. | Measure a branch that parses all sources, then validates citations. | Lower file reads. Risk is higher structural change. |
| Narrow readable suffix roots by CI path | Blocked | Need CI policy confirmation. | Compare the citation job with the exact workflow command. | Lower walk and read volume. Risk is missed citations. |
