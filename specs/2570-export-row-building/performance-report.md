# Performance report: Export row building

## 1. Executive summary

Measured: The objective was lower memory for the capture JSON download path.

Measured: The retained change builds JSON row dictionaries directly during export.

Measured: Application parallelization stayed out of scope.

Measured: The typical capture JSON wall median changed from 356.170 ms to 265.421 ms.

Measured: The typical capture JSON peak traced memory changed from 25,266,182 bytes to 18,674,014 bytes.

Measured: The large capture JSON wall median changed from 1,536.204 ms to 1,046.777 ms.

Measured: The large capture JSON peak traced memory changed from 126,558,780 bytes to 93,598,612 bytes.

## 2. Environment and Python version

Measured: The worktree was `C:\Users\jmorrison\mh-opt3-export-rows`.

Measured: The branch was `perf/2570-export-row-building`.

Measured: The interpreter was CPython 3.13.3 on Windows 11 AMD64.

Measured: The session set `PYTHONPATH` and `MISTHELPER_ROOT` to the worktree path.

Measured: The benchmark asserted that imported modules came from the worktree.

Measured: Raw artifacts are under `C:\Users\jmorrison\.copilot\session-state\76354831-7a9d-41c9-b7dc-933e025bc5a8\files`.

## 3. Benchmark methodology

Measured: The benchmark called `export_capture()` from a local capture document to produced bytes.

Measured: The small case used 25 devices and 50 clients.

Measured: The typical case used 1,000 devices and 2,000 clients.

Measured: The large case used 5,000 devices and 10,000 clients.

Measured: The capture also held tier 3 sections for switch ports, power, radios, and alarms.

Measured: Timing used `time.perf_counter_ns()` and `time.process_time_ns()`.

Measured: Peak memory used `tracemalloc.get_traced_memory()` outside the timed loop.

Measured: Small and typical cases used 31 timing samples.

Measured: The large case used 9 timing samples.

Measured: The paired harness alternated the old and new module order.

Measured: The memory pass used 7 samples for small and typical cases.

Measured: The memory pass used 3 samples for the large case.

Measured: Acceptance required a meaningful memory reduction with no wall time regression.

## 4. Baseline results

Measured: The unmodified baseline used `opt3_export_benchmark.py` before source edits.

Measured: The paired baseline used the saved old module `opt3_export_capture_export_before.py`.

| Workload | Metric | Median | MAD | Samples | Evidence |
| - | - | - | - | - | - |
| small capture JSON | wall ms | 6.550 | 0.718 | 31 | `opt3_export_paired_final.json` |
| small capture JSON | CPU ms | 0.000 | 0.000 | 31 | `opt3_export_paired_final.json` |
| small capture JSON | peak traced bytes | 635,184 | 112 | 7 | `opt3_export_paired_final.json` |
| typical capture JSON | wall ms | 356.170 | 39.775 | 31 | `opt3_export_paired_final.json` |
| typical capture JSON | CPU ms | 281.250 | 15.625 | 31 | `opt3_export_paired_final.json` |
| typical capture JSON | peak traced bytes | 25,266,182 | 112 | 7 | `opt3_export_paired_final.json` |
| large capture JSON | wall ms | 1,536.204 | 247.450 | 9 | `opt3_export_paired_final.json` |
| large capture JSON | CPU ms | 1,171.875 | 78.125 | 9 | `opt3_export_paired_final.json` |
| large capture JSON | peak traced bytes | 126,558,780 | 56 | 3 | `opt3_export_paired_final.json` |

Measured: The baseline targeted tests passed, with 138 tests passed.

## 5. Ranked hotspot list

| Rank and status | File and symbol | Measured cost | Expected gain | Risk | Confidence |
| - | - | - | - | - | - |
| 1 Measured | `src/upgrade_portal/capture/export.py`, `export_capture()` JSON path | Typical peak traced memory was 25,266,182 bytes | Remove row objects and one dictionary copy | Low, because output bytes are checked | High |
| 2 Rejected | `src/upgrade_portal/compare/download.py`, full export path | Memory fell in the first candidate run | Large wall time regressed | Medium | High |

## 6. Recommended optimizations

Measured: Retain direct row dictionary generation for capture JSON only.

Rejected: Do not retain the comparison full export streaming experiment.

Rejected: Do not change the capture CSV path, because the paired result did not need it.

Hypothesis: A future JSON streaming writer could reduce memory further.

Hypothesis: The next benchmark must compare complete JSON bytes and parse behavior.

## 7. Implemented changes

| Field | Required content |
| - | - |
| Change ID and location | OPT3-CAPTURE-JSON, `src/upgrade_portal/capture/export.py`, capture JSON path |
| Evidence | `opt3_export_baseline.json`, `opt3_export_candidate_final.json`, `opt3_export_paired_final.json`, `opt3_export_parity.json` |
| Root cause | The old JSON path built `ExportRow` objects, then copied them through `to_dict()` before `json.dumps()` |
| Change | The JSON path now builds final row dictionaries in file order |
| Before result | Typical wall 356.170 ms, MAD 39.775, n 31 |
| After result | Typical wall 265.421 ms, MAD 29.804, n 31 |
| Percentage change | Typical wall changed by -25.5 percent |
| Memory change | Typical peak traced memory fell by 6,592,168 bytes |
| Test coverage | Added exact byte tests for JSON and CSV downloads |
| Risks | Private helper duplication can drift, so tests compare public renderer bytes |
| Confidence level | High for bytes, medium for large timing because the machine was noisy |
| Retention decision | Retained for a 26.1 percent typical memory reduction and no paired wall time regression |

## 8. Before-and-after measurements

| Workload | Metric | Before median and MAD | After median and MAD | Samples | Signed change | Decision |
| - | - | - | - | - | - | - |
| small capture JSON | wall ms | 6.550 +/- 0.718 | 5.114 +/- 0.605 | 31 | -21.9 percent | Retained |
| small capture JSON | CPU ms | 0.000 +/- 0.000 | 0.000 +/- 0.000 | 31 | Not defined | Retained |
| small capture JSON | peak bytes | 635,184 +/- 112 | 471,864 +/- 112 | 7 | -25.7 percent | Retained |
| typical capture JSON | wall ms | 356.170 +/- 39.775 | 265.421 +/- 29.804 | 31 | -25.5 percent | Retained |
| typical capture JSON | CPU ms | 281.250 +/- 15.625 | 218.750 +/- 0.000 | 31 | -20.0 percent | Retained |
| typical capture JSON | peak bytes | 25,266,182 +/- 112 | 18,674,014 +/- 112 | 7 | -26.1 percent | Retained |
| large capture JSON | wall ms | 1,536.204 +/- 247.450 | 1,046.777 +/- 127.579 | 9 | -31.9 percent | Retained |
| large capture JSON | CPU ms | 1,171.875 +/- 78.125 | 875.000 +/- 62.500 | 9 | -25.3 percent | Retained |
| large capture JSON | peak bytes | 126,558,780 +/- 56 | 93,598,612 +/- 56 | 3 | -26.0 percent | Retained |

## 9. Memory impact

Measured: The memory metric is peak traced Python bytes.

Measured: The small capture JSON peak fell by 163,320 bytes.

Measured: The typical capture JSON peak fell by 6,592,168 bytes.

Measured: The large capture JSON peak fell by 32,960,168 bytes.

Measured: The CSV path peak memory did not change in the paired benchmark.

Measured: The change trades no measured wall time for memory in the retained path.

## 10. Correctness and regression validation

| Check | Command or test | Actual result | Limitation or artifact |
| - | - | - | - |
| Baseline tests | `rtk python -m pytest tests\unit\upgrade_portal\test_compare_download.py tests\unit\upgrade_portal\test_compare_download_full.py tests\unit\upgrade_portal\test_capture_export.py -q --timeout=180` | 138 passed | Before source edit |
| Byte parity | `rtk python opt3_export_parity.py` | All small, typical, and large checks passed | Local disposable fixtures |
| Targeted tests | `rtk python -m pytest tests\unit\upgrade_portal\test_compare_download.py tests\unit\upgrade_portal\test_compare_download_full.py tests\unit\upgrade_portal\test_capture_export.py -q --timeout=180` | 140 passed | After source edit |

## 11. Rejected ideas and why they were rejected

| Idea and location | Evidence | Reason for rejection | Reverted or never implemented |
| - | - | - | - |
| Direct full comparison serialization | `opt3_export_candidate.json` | Large comparison wall time regressed by 120.4 percent for CSV and 28.2 percent for JSON | Reverted |
| Direct capture CSV serialization | `opt3_export_paired_final.json` | The paired CSV change was not the objective and did not reduce memory | Not retained |

## 12. Remaining opportunities

| Opportunity and status | Missing evidence or blocker | Exact next benchmark | Expected value and risk |
| - | - | - | - |
| Hypothesis: stream JSON text without the row list | Needs proof of byte-identical JSON with the same key order | Compare full bytes for all fixture sizes and malformed rows | More memory reduction, with higher maintenance risk |
| Hypothesis: reduce `ExportRow.to_dict()` copies for public renderers | Needs a safe public behavior proof for partial `values` maps | Pair old and new public renderer calls | Smaller gain, with compatibility risk |


