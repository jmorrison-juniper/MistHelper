# Exclusion drift performance report

## 1. Executive summary

**Measured**: The objective was lower latency for the advisory exclusion drift job. The workload was the CI command `python scripts/check_exclusion_drift.py --format github --output exclusion-drift.json`. The retained change caches repeated scan data and builds larger safe mypy batches. Application parallelization stayed out of scope.

**Measured**: Baseline wall time was 906.732 s. Candidate wall time was 639.941 s. The time reduction was 29.42 percent. This passes the five percent end-to-end rule.

## 2. Environment and Python version

**Measured**: The run used Windows 11 on AMD64 with CPython 3.13.3. The executable was `C:\Users\jmorrison\AppData\Local\Programs\Python\Python313\python.exe`. The worktree was `C:\Users\jmorrison\mh-opt3-exclusion-drift`.

**Measured**: Baseline source revision was `a3584eb60732c0edc4d9cd40d582675074c0d23d`. The branch was `perf/2571-exclusion-drift-cache`. The harness asserted that the imported module file stayed inside the worktree.

## 3. Benchmark methodology

**Measured**: The harness ran the same arguments that CI runs. The harness wrote output files under `C:\Users\jmorrison\.copilot\session-state\76354831-7a9d-41c9-b7dc-933e025bc5a8\files\` with the `opt3_drift_` prefix.

**Measured**: The timers were `time.perf_counter_ns()` and `time.process_time_ns()`. The harness counted `Path.rglob()` calls and `subprocess.run()` calls. `tracemalloc` ran only in separate memory runs.

**Measured**: The filesystem and tool caches were warm. `.venv` and `node_modules` were absent, which matches a fresh CI checkout. Each full sample was slow, so the timing set used one sample for each side.

## 4. Baseline results

| Workload and state | Metric and unit | Median | MAD | Runs and values | Evidence artifact |
| --- | --- | --- | --- | --- | --- |
| CI command, warm cache | Wall time, s | 906.732 | 0 | 1: 906.732 | `opt3_drift_baseline_original_results.json` |
| CI command, warm cache | Parent CPU time, s | 1.969 | 0 | 1: 1.969 | `opt3_drift_baseline_original_results.json` |
| CI command, warm cache | `Path.rglob()` calls | 7 | 0 | 1: 7 | `opt3_drift_baseline_original_results.json` |
| CI command, warm cache | Subprocess launches | 39 | 0 | 1: 39 | `opt3_drift_baseline_original_results.json` |
| CI command, warm cache | Peak traced bytes | 92,766,505 | Not measured | 1 memory run | `opt3_drift_baseline_memory_results.json` |

**Measured**: Baseline contract tests passed before the change. The guardrail test also passed before the change.

## 5. Ranked hotspot list

| Rank and status | File, symbol, and lines | Measured cost and frequency | Expected gain | Risk and maintenance cost | Confidence |
| --- | --- | --- | --- | --- | --- |
| 1. Measured | `scripts/check_exclusion_drift.py`, `_commands_for` | Mypy launched many batches. Full run launched 39 processes. | High, if larger batches keep counts stable. | Medium. Mypy output can change when batch size changes. | High after exact output comparison. |
| 2. Measured | `scripts/check_exclusion_drift.py`, `measure` | Duplicate Bandit scan path launched twice. | Low for one duplicate entry. | Low. Cache key includes manifest digest, gate, and scan path. | High. |
| 3. Hypothesis | `scripts/check_exclusion_drift.py`, `_mypy_files_for` | Scan count was seven calls in the end-to-end run. | Low for this manifest. | Low. | Medium. |

## 6. Recommended optimizations

**Measured**: Build mypy batches from a command length budget. The old fixed count started more mypy processes than needed. The new budget keeps the command below a conservative Windows limit.

**Measured**: Cache completed tool runs by manifest digest, gate, and scan path. This avoids duplicate subprocess work when a manifest keeps two path spellings for the same scan.

**Hypothesis**: A future manifest with repeated mypy scan paths can gain from the file list cache. The exact benchmark is the same CI command after such a manifest change.

## 7. Implemented changes

| Field | Required content |
| --- | --- |
| Change ID and location | OPT3-2571 in `scripts/check_exclusion_drift.py`, `ExclusionDriftReporter`. |
| Evidence | Raw files use the `opt3_drift_` prefix in the session artifact folder. |
| Root cause | The script used a fixed mypy batch size and repeated identical tool runs. |
| Change | Cache by manifest digest and build mypy commands from a length budget. |
| Before result | 906.732 s wall, 1.969 s parent CPU, 39 subprocesses, one sample. |
| After result | 639.941 s wall, 1.438 s parent CPU, 18 subprocesses, one sample. |
| Percentage change | `100 * (639.941 - 906.732) / 906.732 = -29.42%`. |
| Memory change | Peak traced bytes changed from 92,766,505 to 95,114,578. The increase was 2,348,073 bytes. |
| Test coverage | Two contract tests cover the mypy file cache and duplicate scan path cache. |
| Risks | Larger mypy batches can change counts. Exact output comparison passed. |
| Confidence level | Medium. The sample count is one because the workload is slow. |
| Retention decision | Retained. The end-to-end wall time improved by more than five percent. |

## 8. Before-and-after measurements

| Change and workload | Metric and unit | Before median and spread | After median and spread | Sample counts | Signed change | Decision |
| --- | --- | --- | --- | --- | --- | --- |
| OPT3-2571, CI command | Wall time, s | 906.732, MAD 0 | 639.941, MAD 0 | 1 before, 1 after | -29.42% | Retained |
| OPT3-2571, CI command | Parent CPU time, s | 1.969, MAD 0 | 1.438, MAD 0 | 1 before, 1 after | -26.98% | Retained |
| OPT3-2571, CI command | Subprocess launches | 39 | 18 | 1 before, 1 after | -53.85% | Retained |
| OPT3-2571, CI command | `Path.rglob()` calls | 7 | 7 | 1 before, 1 after | 0.00% | Neutral |

## 9. Memory impact

**Measured**: Peak traced Python memory changed from 92,766,505 bytes to 95,114,578 bytes. The increase was 2,348,073 bytes. The cache holds one manifest digest, seven mypy file lists, and completed run objects for repeated scan paths during one invocation.

**Measured**: Current traced bytes changed from 39,507 to 35,344. The memory measurement used `tracemalloc`. It does not include child process memory.

## 10. Correctness and regression validation

| Check | Command or test | Actual result | Limitation or artifact |
| --- | --- | --- | --- |
| Output comparison | Harness compared baseline and candidate stdout and JSON | Passed exactly | No value was normalized. |
| Exit code comparison | Harness captured exit codes | Both were 0 | One sample per side. |
| Contract tests | `rtk python -m pytest tests\contract\test_exclusion_drift.py -q --timeout=180` | 10 passed | None. |
| Guardrail tests | `rtk python -m pytest tests\guardrails\test_performance_hook_catalog.py -q --timeout=180` | 4 passed | Snapshot update was not needed. |
| Compile | `rtk python -m py_compile scripts\check_exclusion_drift.py tests\contract\test_exclusion_drift.py` | Passed | None. |
| Ruff | `rtk python -m ruff check tests\contract\test_exclusion_drift.py` | Passed | `scripts` is excluded in `pyproject.toml`. |
| Black | `rtk python -m black --check scripts\check_exclusion_drift.py tests\contract\test_exclusion_drift.py` | Passed | None. |
| Pydocstyle | `rtk python -m pydocstyle scripts\check_exclusion_drift.py` | Passed | None. |
| Bandit | `rtk python -m bandit -q scripts\check_exclusion_drift.py` | Reported existing B404 and B603 | Suppressing them would change the drift report. |
| Whitespace | `rtk proxy git diff --check` | Passed | None. |

## 11. Rejected ideas and why they were rejected

| Idea and location | Evidence | Reason for rejection | Reverted or never implemented |
| --- | --- | --- | --- |
| Suppress Bandit findings in the script | Bandit reported B404 and B603 | The suppression changed the script count in the drift report. | Reverted. |
| Parallel tool execution | User rule and skill rule | Parallel execution was out of scope. | Never implemented. |
| Change quality gate exclusions | User rule | It would change the measured contract. | Never implemented. |

## 12. Remaining opportunities

| Opportunity and status | Missing evidence or blocker | Exact next benchmark | Expected value and risk |
| --- | --- | --- | --- |
| Use a mypy response file if mypy adds support | Mypy support was not verified here. | Run the same CI command with response-file arguments. | It can cut command size risk. Behavior risk is medium. |
| Move the advisory job to Linux-only tuning data | This task ran on Windows. | Collect three samples on a GitHub runner. | It can prove CI variance. Risk is low. |
