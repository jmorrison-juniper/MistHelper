# Performance report: Upgrade capture stored size measurement

## 1. Executive summary

**Measured**: The objective was lower sequential CPU time for upgrade capture stored size stamping. The workload used medium and large capture documents with and without driver fields. The retained change solves the `stored_size_bytes` digit width after one body serialization. It keeps application parallelization out of scope.

**Measured**: The large write path wall median changed from 72.333 ms to 27.188 ms per operation across 35 samples. This is a 62.4 percent reduction. The result clears the 5 percent end-to-end path threshold and the 10 percent isolated path threshold.

## 2. Environment and Python version

**Measured**: The benchmark ran on Windows 11 with AMD64 architecture. The observed processor was `13th Gen Intel(R) Core(TM) i9-13950HX`. The machine has 32 logical cores per the task environment.

**Measured**: Python was CPython 3.13.3. The benchmark imported `C:\Users\jmorrison\misthelper-opt2-capture-size\src\upgrade_portal\capture\store.py`. The source revision before edits was `222f74d3940fbd83628e1578db7cdf80d1c6ae8e`.

**Measured**: The benchmark harness path was `C:\Users\jmorrison\.copilot\session-state\76354831-7a9d-41c9-b7dc-933e025bc5a8\files\opt2_capture_size_benchmark.py`. The raw baseline path was `C:\Users\jmorrison\.copilot\session-state\76354831-7a9d-41c9-b7dc-933e025bc5a8\files\opt2_capture_size_baseline.json`. The raw candidate path was `C:\Users\jmorrison\.copilot\session-state\76354831-7a9d-41c9-b7dc-933e025bc5a8\files\opt2_capture_size_candidate.json`.

## 3. Benchmark methodology

**Measured**: The harness read `MISTHELPER_REPO_ROOT`, inserted it at the start of `sys.path`, and asserted that `store.__file__` was inside the worktree. This prevented an import from another checkout.

**Measured**: The harness used local disposable fixture documents only. It did not call the Mist API. It did not touch production data.

**Measured**: The timing loop used `time.perf_counter_ns()` and `time.process_time_ns()`. Each workload used 5 warmups and 35 samples. Each sample used a fixed loop count. The memory loop started `tracemalloc` outside the measured work and ran separately from timing.

**Measured**: The workloads were medium write path, large write path, medium verification path, large verification path, and edge size. The write path measured `_stamp_size()`. The verification path measured `verify_write()` with a fake local database handle.

**Hypothesis**: The workload represents real capture writes because each fixture contains capture identity, state, devices, clients, extras, and optional driver fields.

## 4. Baseline results

| Workload and state | Metric and unit | Median | MAD | Runs and values | Evidence artifact |
| --- | --- | --- | --- | --- | --- |
| Medium write path | Wall time, ms per operation | 41.886 | 9.321 | 35 samples | `opt2_capture_size_baseline.json` |
| Large write path | Wall time, ms per operation | 72.333 | 3.177 | 35 samples | `opt2_capture_size_baseline.json` |
| Medium verification path | Wall time, ms per operation | 12.261 | 1.120 | 35 samples | `opt2_capture_size_baseline.json` |
| Large verification path | Wall time, ms per operation | 118.415 | 35.513 | 35 samples | `opt2_capture_size_baseline.json` |
| Edge size | Wall time, ms per operation | 0.021 | 0.006 | 35 samples | `opt2_capture_size_baseline.json` |

**Measured**: The baseline stored size tests passed before the edit. The command was `rtk python -m pytest tests\unit\upgrade_portal\test_store.py tests\unit\upgrade_portal\test_capture_assembly.py tests\unit\upgrade_portal\test_capture_stored_size.py tests\contract\upgrade_portal -q`. The result was 1017 passed in 520.65 seconds.

## 5. Ranked hotspot list

| Rank and status | File, symbol, and lines | Measured cost and frequency | Expected gain | Risk and maintenance cost | Confidence |
| --- | --- | --- | --- | --- | --- |
| 1, Measured | `store.py`, `_stamp_size()` and `measure_size_bytes()` | Baseline profile showed 12 full canonical serializations for 4 large stamp calls. Cumulative time was 0.990 s. | High, because two stable rounds can be removed for each capture. | Medium, because the digit width rule must stay exact. | High |
| 2, Measured | `store.py`, `_edge_size_bytes()` | Baseline edge size median was 0.021 ms. | Low for the write path. | Low, because `ensure_ascii=True` makes character count equal byte count. | High |
| 3, Hypothesis | `store.py`, `measure_size_bytes()` in verification | Large verification median was 118.415 ms. The path also spends time on digest serialization. | Medium if digest and size can share a body. | Medium, because digest behavior must stay unchanged. | Medium |

## 6. Recommended optimizations

**Measured**: Retain one optimization in `_stamp_size()`. Compute the canonical body without `stored_size_bytes` once. Then solve the added field width with arithmetic. The required benchmark is the write path and verification path with medium and large captures.

**Measured**: Retain the byte count simplification in `measure_size_bytes()` and `_edge_size_bytes()`. The canonical JSON uses `ensure_ascii=True`, so the string length equals the UTF-8 byte length.

**Rejected**: Do not replace the JSON module. The storage contract depends on the current canonical JSON behavior, and no compatible replacement was measured.

## 7. Implemented changes

| Field | Required content |
| --- | --- |
| Change ID and location | `capture-size-width`, `src\upgrade_portal\capture\store.py`, `_stamp_size()`, `_stable_capture_size_bytes()`, `_capture_size_bytes()`, and `_edge_size_bytes()`. |
| Evidence | Raw results are in `opt2_capture_size_baseline.json` and `opt2_capture_size_candidate.json`. Profile summaries are in `opt2_capture_size_baseline_profile_stamp_large.txt` and `opt2_capture_size_candidate_profile_stamp_large.txt`. |
| Root cause | `_stamp_size()` serialized the full capture until the size value settled. Large captures paid the whole canonical walk three times. |
| Change | The code now serializes the stable body once and computes only the changing digit width. |
| Before result | Large write path wall median was 72.333 ms per operation. MAD was 3.177 ms across 35 samples. |
| After result | Large write path wall median was 27.188 ms per operation. MAD was 0.790 ms across 35 samples. |
| Percentage change | `100 * (27.188 - 72.333) / 72.333 = -62.4%`. A negative value means less time. |
| Memory change | Large write path peak traced bytes changed from 495,260 to 495,136. This is 124 bytes less. |
| Test coverage | `test_stamp_size_matches_the_slow_convergence_rule` and `test_stamp_size_converges_at_size_digit_boundaries` cover the convergence rule and 99, 100, 999, and 1000 byte transitions. |
| Risks | The size field position in sorted JSON does not affect the length. The tests compare against the slow rule to guard that risk. |
| Confidence level | High for the write path. The effect is much larger than the MAD. |
| Retention decision | Retained. The large write path cleared the 5 percent threshold. |

## 8. Before-and-after measurements

| Change and workload | Metric and unit | Before median and spread | After median and spread | Sample counts | Signed change | Decision |
| --- | --- | --- | --- | --- | --- | --- |
| Capture size width, medium write path | Wall time, ms per operation | 41.886, MAD 9.321 | 14.446, MAD 1.940 | 35 and 35 | -65.5% | Retained |
| Capture size width, large write path | Wall time, ms per operation | 72.333, MAD 3.177 | 27.188, MAD 0.790 | 35 and 35 | -62.4% | Retained |
| Capture size width, medium verification path | Wall time, ms per operation | 12.261, MAD 1.120 | 13.942, MAD 1.844 | 35 and 35 | +13.7% | Recorded as noise or non-target regression |
| Capture size width, large verification path | Wall time, ms per operation | 118.415, MAD 35.513 | 37.156, MAD 2.511 | 35 and 35 | -68.6% | Retained evidence |
| Edge size byte count | Wall time, ms per operation | 0.021, MAD 0.006 | 0.013, MAD 0.001 | 35 and 35 | -35.2% | Retained as a small safe change |

**Measured**: Large write path CPU median changed from 62.500 ms to 23.438 ms per operation. This is a 62.5 percent reduction.

## 9. Memory impact

| Workload | Baseline peak traced bytes | Candidate peak traced bytes | Difference |
| --- | --- | --- | --- |
| Medium write path | 183,566 | 183,442 | -124 |
| Large write path | 495,260 | 495,136 | -124 |
| Medium verification path | 184,363 | 184,363 | 0 |
| Large verification path | 496,057 | 496,057 | 0 |
| Edge size | 2,393 | 2,393 | 0 |

**Measured**: The change does not claim a meaningful memory reduction. The memory result is neutral.

## 10. Correctness and regression validation

| Check | Command or test | Actual result | Limitation or artifact |
| --- | --- | --- | --- |
| Baseline stored size tests | `rtk python -m pytest tests\unit\upgrade_portal\test_store.py tests\unit\upgrade_portal\test_capture_assembly.py tests\unit\upgrade_portal\test_capture_stored_size.py tests\contract\upgrade_portal -q` | 1017 passed in 520.65 seconds | Baseline before application code edits |
| Candidate stored size tests | `rtk python -m pytest tests\unit\upgrade_portal\test_store.py tests\unit\upgrade_portal\test_capture_assembly.py tests\unit\upgrade_portal\test_capture_stored_size.py tests\contract\upgrade_portal -q` | 1022 passed in 634.36 seconds | Includes five new unit cases |
| Compile | `rtk python -m py_compile src\upgrade_portal\capture\store.py tests\unit\upgrade_portal\test_store.py` | Passed | No output from compile |
| Ruff | `rtk python -m ruff check src\upgrade_portal\capture\store.py tests\unit\upgrade_portal\test_store.py` | Passed | `All checks passed!` |
| Black | `rtk python -m black --check src\upgrade_portal\capture\store.py tests\unit\upgrade_portal\test_store.py` | Passed | `2 files would be left unchanged.` |
| pydocstyle | `rtk python -m pydocstyle src\upgrade_portal\capture\store.py tests\unit\upgrade_portal\test_store.py` | Passed | No output |
| Bandit | `rtk python -m bandit -q src\upgrade_portal\capture\store.py` | Passed | No output |
| Diff whitespace | `rtk git diff --check` | Passed | No output |
| STE documents | `rtk python -m tools.ste_linter CHANGELOG.md specs\2486-capture-size-measurement\spec.md specs\2486-capture-size-measurement\plan.md specs\2486-capture-size-measurement\tasks.md specs\2486-capture-size-measurement\performance-report.md --min-score 80 --quiet` | Passed | Scores were 86 through 99 for changed documents. |

## 11. Rejected ideas and why they were rejected

| Idea and location | Evidence | Reason for rejection | Reverted or never implemented |
| --- | --- | --- | --- |
| Replace the standard JSON serializer | Hypothesis | It can change Unicode, float, and default conversion behavior. | Never implemented |
| Cache size results by document identity | Hypothesis | Captures are mutable dictionaries at the boundary. A cache can return stale sizes. | Never implemented |
| Add parallel work for capture serialization | Rejected | The task forbids parallelization. | Never implemented |
| Share digest serialization with size verification | Hypothesis | It may reduce verification cost, but it needs a separate contract review. | Never implemented |

## 12. Remaining opportunities

| Opportunity and status | Missing evidence or blocker | Exact next benchmark | Expected value and risk |
| --- | --- | --- | --- |
| Share canonical body work between size and digest, Hypothesis | Needs proof that digest bytes stay identical. | Extend the harness to measure `verify_write()` with shared canonical output across medium and large captures. | Medium value for verification. Medium risk to digest behavior. |
| Optimize assembly `stamp_size()`, Hypothesis | This task targeted the store path. | Run the same write path harness against `src\upgrade_portal\capture\assembly.py`. | Medium value for capture construction. Medium risk to assembly import boundaries. |
| Profile realistic production captures, Blocked | No sanitized production captures were provided. | Run the harness against sanitized capture JSON files with known provenance. | High confidence if fixtures become available. Low code risk. |
