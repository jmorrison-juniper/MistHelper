# Performance report: Flatten nested fields

## 1. Executive summary

**Measured**: The objective was lower single-worker latency for `DataProcessingUtils.flatten_nested_fields()`.
The workload used 1,000 synthetic export rows with Mist device and site style fields.
The retained change writes flattened nested fields directly into the output dictionary.
It also uses a first-character parse guard for stringified values.
Application parallelization stayed out of scope.

**Measured**: The custom harness median wall time changed from 139.448 ms to 121.898 ms across 31 samples.
This is a 12.59 percent time reduction.
The CPU median changed from 131.250 ms to 103.125 ms across 31 samples.
This is a 21.43 percent time reduction.
The change passes the 5 percent end-to-end threshold.

## 2. Environment and Python version

**Measured**: Python was CPython 3.13.3.
The executable was the system Python at `C:\Users\jmorrison\AppData\Local\Programs\Python\Python313\python.exe`.
The platform was Windows 11 on AMD64 with 32 logical cores.
No virtual environment was present in this worktree.
`PYTHONPATH` was set to `C:\Users\jmorrison\misthelper-opt2-flatten` for Python runs.

**Measured**: The worktree was `C:\Users\jmorrison\misthelper-opt2-flatten`.
The branch was `perf/2485-flatten-nested-fields`.
The baseline source was the unmodified branch before source edits.
The candidate source contains the change in `src\data\data_processing_utils.py`.
Raw artifacts use the `opt2_flatten_` prefix in the session artifact folder.

## 3. Benchmark methodology

**Measured**: The custom harness was `opt2_flatten_benchmark.py`.
It reads `MISTHELPER_REPO_ROOT`, inserts it at the start of `sys.path`, and checks that the imported module is inside the worktree.
It uses 1,000 prebuilt records.
Each record has scalar values, nested dictionaries, lists of dictionaries, scalar lists, stringified JSON, Python literal strings, empty containers, and malformed strings.

**Measured**: Timing used `time.perf_counter_ns()` and `time.process_time_ns()`.
The harness used 5 warmups, 31 samples, and 5 loops per sample.
The reported value is one complete 1,000-record flatten pass.
It consumed output by summing the number of keys.
Memory used `tracemalloc` in a separate pass with tracing outside the loop.

**Measured**: The pyperf harness was `opt2_flatten_pyperf.py`.
It used the same import guard and dataset shape.
`pyperf compare_to` compared `opt2_flatten_baseline_pyperf.json` and `opt2_flatten_candidate2_pyperf.json`.
Pyperf reported instability, so the custom timer result is the primary decision record.

**Measured**: The acceptance rule was at least 5 percent lower median wall time for the end-to-end flatten path.
The change also had to keep value types, key names, key order, and malformed string handling stable.

## 4. Baseline results

| Workload and state | Metric and unit | Median | MAD or IQR | Runs and values | Evidence artifact |
| --- | --- | --- | --- | --- | --- |
| 1,000-row flatten batch, warm | Wall time | 139.448 ms | 11.783 ms MAD | 31 samples, 5 loops each | `opt2_flatten_baseline_custom.json` |
| 1,000-row flatten batch, warm | CPU time | 131.250 ms | 12.500 ms MAD | 31 samples, 5 loops each | `opt2_flatten_baseline_custom.json` |
| 1,000-row flatten batch, traced | Peak traced Python memory | 2,573,377 bytes | Not measured | 5 loops | `opt2_flatten_baseline_custom.json` |
| 1,000-row flatten batch, pyperf | Wall time | 99.1 ms | 20.0 ms MAD | 60 values | `opt2_flatten_baseline_pyperf.json` |

**Measured**: The baseline unit test command was `rtk python -m pytest tests\unit\dataproc\test_data_processing_utils.py -q`.
It passed 22 tests in 3.09 seconds.

## 5. Ranked hotspot list

| Rank and status | File, symbol, and lines | Measured cost and frequency | Expected gain | Risk and maintenance cost | Confidence |
| --- | --- | --- | --- | --- | --- |
| 1, Measured | `src\data\data_processing_utils.py`, `_parse_stringified_value()` | 0.162 s cumulative in one profiled pass, 13,000 calls | Medium | Low risk if parse order stays JSON first | High |
| 2, Measured | `src\data\data_processing_utils.py`, `_flatten_value_into()` | 0.136 s cumulative in one profiled pass, 13,000 calls | Medium | Medium risk from key order and empty container behavior | High |
| 3, Measured | `src\data\data_processing_utils.py`, `flatten_dict()` | 0.085 s cumulative in one profiled pass, 8,000 calls | Medium | Medium risk from duplicate flattened keys | Medium |
| 4, Measured | Standard library `ast.literal_eval()` | 0.071 s cumulative in one profiled pass, 2,000 calls | Low | High behavior risk if removed | High |

## 6. Recommended optimizations

**Measured**: Keep JSON-first parsing.
The baseline already used this order, so no parse order change was needed.

**Measured**: Avoid temporary dictionaries and pair lists in recursive flattening.
The root cause was repeated construction of intermediate dictionaries that were immediately merged.
The smallest safe change writes flattened keys into the caller output dictionary.
The semantic risk is key order and empty container handling.
Tests cover that risk.

**Measured**: Use a first-character parse guard.
The root cause was a tuple-based `startswith()` check for every scalar string.
The smallest safe change reads `value[0]` only after the empty string guard.
The semantic risk is empty string behavior.
The guard returns the string unchanged as before.

## 7. Implemented changes

| Field | Required content |
| --- | --- |
| Change ID and location | FLAT-2485 in `src\data\data_processing_utils.py`, `flatten_dict()`, `_flatten_dict_into()`, `_flatten_list_into()`, `_flatten_entry()`, `_parse_stringified_value()`, and `_flatten_value_into()`. |
| Evidence | Baseline and candidate JSON files under the session artifact folder. Profiles are `opt2_flatten_baseline_profile.pstats` and `opt2_flatten_candidate_profile.pstats`. |
| Root cause | Recursive flattening allocated temporary pair lists and dictionaries before merge. Parse guards ran for every field. |
| Change | Write recursive output directly into the target dictionary. Cache hot static method lookups. Replace tuple `startswith()` with an empty check plus first-character test. |
| Before result | Wall median 139.448 ms, MAD 11.783 ms, 31 samples. CPU median 131.250 ms, MAD 12.500 ms, 31 samples. |
| After result | Wall median 121.898 ms, MAD 12.654 ms, 31 samples. CPU median 103.125 ms, MAD 9.375 ms, 31 samples. |
| Percentage change | Wall time changed by `100 * (after - before) / before = -12.59%`. CPU time changed by `-21.43%`. |
| Memory change | Peak traced Python memory changed from 2,573,377 bytes to 2,575,585 bytes. This is a 2,208 byte increase. |
| Test coverage | Added tests for JSON and Python literal equivalence, key order, empty containers, and malformed strings. |
| Risks | The main risks are key order, empty list behavior, and malformed string handling. Unit tests cover them. |
| Confidence level | Medium. The custom CPU result and pyperf comparison agree. Pyperf still reported noisy samples. |
| Retention decision | Retained. The end-to-end wall median improved by more than 5 percent. |

## 8. Before-and-after measurements

| Change and workload | Metric and unit | Before median and spread | After median and spread | Sample counts | Signed change | Decision |
| --- | --- | --- | --- | --- | --- | --- |
| FLAT-2485, 1,000-row flatten batch | Wall time | 139.448 ms +- 11.783 ms MAD | 121.898 ms +- 12.654 ms MAD | 31 and 31 | -12.59 percent | Retained |
| FLAT-2485, 1,000-row flatten batch | CPU time | 131.250 ms +- 12.500 ms MAD | 103.125 ms +- 9.375 ms MAD | 31 and 31 | -21.43 percent | Retained |
| FLAT-2485, pyperf 1,000-row batch | Wall time | 99.1 ms +- 20.0 ms MAD | 64.6 ms +- 13.3 ms MAD | 60 and 60 | -34.81 percent | Support only |

**Measured**: `pyperf compare_to --table` reported `127 ms` versus `89.3 ms` and `1.42x faster` by mean.
**Measured**: Pyperf reported unstable distributions for both files.
This report uses the custom harness medians for the decision.

## 9. Memory impact

**Measured**: Traced Python peak memory was 2,573,377 bytes before and 2,575,585 bytes after.
The peak increased by 2,208 bytes, or 0.09 percent.
Current traced bytes changed from 15,404 bytes to 4,812 bytes after 5 loops.
This is net live traced memory, not allocation volume.
No speed-versus-memory trade-off was accepted.

## 10. Correctness and regression validation

| Check | Command or test | Actual result | Limitation or artifact |
| --- | --- | --- | --- |
| Baseline unit tests | `rtk python -m pytest tests\unit\dataproc\test_data_processing_utils.py -q` | 22 passed | Baseline run before source edits |
| Candidate unit tests | `rtk python -m pytest tests\unit\dataproc\test_data_processing_utils.py -q` | 25 passed | Covers target module |
| Compile | `rtk python -m py_compile src\data\data_processing_utils.py tests\unit\dataproc\test_data_processing_utils.py` | Passed | Python 3.13.3 only |
| Ruff | `rtk python -m ruff check src\data\data_processing_utils.py tests\unit\dataproc\test_data_processing_utils.py` | Passed | Target files only |
| Black | `rtk python -m black --check src\data\data_processing_utils.py tests\unit\dataproc\test_data_processing_utils.py` | Passed | Target files only |
| Pydocstyle | `rtk python -m pydocstyle src\data\data_processing_utils.py tests\unit\dataproc\test_data_processing_utils.py` | Passed | Target files only |
| Bandit | `rtk python -m bandit -q src\data\data_processing_utils.py` | Passed with existing nosec notices | Target non-test file only |

## 11. Rejected ideas and why they were rejected

| Idea and location | Evidence | Reason for rejection | Reverted or never implemented |
| --- | --- | --- | --- |
| Remove `ast.literal_eval()` fallback in `_parse_stringified_value()` | Existing tests require Python literal strings | It changes behavior for single-quoted Python literal strings | Never implemented |
| Parse only fields with known names | Representative export rows have varied field names | It risks missing valid stringified values | Never implemented |
| Add caching for parsed strings | Export rows carry many unique JSON strings | It adds memory risk and stale behavior risk | Never implemented |

## 12. Remaining opportunities

| Opportunity and status | Missing evidence or blocker | Exact next benchmark | Expected value and risk |
| --- | --- | --- | --- |
| Hypothesis: Reduce exception cost for Python literal strings | Need real export frequency for Python literals | Compare fields with JSON strings only, Python literal strings only, and malformed strings only | Could reduce CPU, but parser behavior risk is high |
| Hypothesis: Export writers can avoid flattening fields that backends do not use | Need backend-specific export profiles | Run full CSV and SQLite export benchmarks around `DataExporter` | Higher value, but broader behavior risk |
