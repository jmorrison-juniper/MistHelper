# Performance report: MistHelper menu and mode cache

## 1. Executive summary

**Measured**: The objective was to reduce repeated sequential work in `MistHelper.py`. The retained change caches the sorted menu key order and the main mode predicate table. Application parallel work stayed out of scope.

**Measured**: The isolated repeated path passed the rule. Menu redraw wall time changed from 1034.642 ms to 214.372 ms for 200 redraws. Mode dispatch wall time changed from 169.752 ms to 35.576 ms for 20000 dispatches.

**Measured**: Startup did not improve. The `--help` median changed from 33457.538 ms to 49010.311 ms in the first candidate run. A second candidate startup run measured 39014.689 ms with high noise.

## 2. Environment and Python version

**Measured**: Python was CPython 3.13.3 at `C:\Users\jmorrison\AppData\Local\Programs\Python\Python313\python.exe`. The host was Windows 11 on AMD64 with 32 logical cores.

**Measured**: The worktree was `C:\Users\jmorrison\mh-opt3-cli-startup`. The branch was `perf/2573-menu-dispatch-cache`. The repository was `jmorrison-juniper/MistHelper`.

**Measured**: The benchmark set `PYTHONPATH` to the worktree path. The harness asserted that `MistHelper.__file__` was inside the worktree.

## 3. Benchmark methodology

**Measured**: Startup ran `python MistHelper.py --help` in a new process 10 times. The harness also ran one `python -X importtime MistHelper.py --help` command.

**Measured**: The menu path called `_print_interactive_menu()` 200 times per sample with standard output captured. The dispatch path called `_dispatch_main_mode()` across all modes 20000 times per sample.

**Measured**: The in-process paths used 7 warmups and 31 samples. Timing used `time.perf_counter_ns()` and `time.process_time_ns()`. Memory used `tracemalloc` outside the timed loop.

**Measured**: Raw artifacts are in `C:\Users\jmorrison\.copilot\session-state\76354831-7a9d-41c9-b7dc-933e025bc5a8\files\`. The files use the `opt3_cli_` prefix.

**Hypothesis**: The `--help` path logs at startup and shutdown. The importtime artifact showed a log rotation conflict during one run. That side effect makes startup results noisy.

## 4. Baseline results

| Workload and state | Metric and unit | Median | MAD | Runs and values | Evidence artifact |
| --- | --- | --- | --- | --- | --- |
| **Measured** startup `--help` | wall ms | 33457.538 | 5618.688 | 10 runs | `opt3_cli_baseline.json` |
| **Measured** menu redraw | wall ms per 200 redraws | 1034.642 | 207.426 | 31 samples | `opt3_cli_baseline.json` |
| **Measured** menu redraw | CPU ms per 200 redraws | 328.125 | 15.625 | 31 samples | `opt3_cli_baseline.json` |
| **Measured** mode dispatch | wall ms per 20000 dispatches | 169.752 | 28.803 | 31 samples | `opt3_cli_baseline.json` |
| **Measured** mode dispatch | CPU ms per 20000 dispatches | 93.750 | 0.000 | 31 samples | `opt3_cli_baseline.json` |
| **Measured** menu redraw | peak traced bytes | 16876356 | Not applicable | 1 memory run | `opt3_cli_baseline.json` |
| **Measured** mode dispatch | peak traced bytes | 174896 | Not applicable | 1 memory run | `opt3_cli_baseline.json` |

## 5. Ranked hotspot list

| Rank and status | File, symbol, and lines | Measured cost and frequency | Expected gain | Risk and maintenance cost | Confidence |
| --- | --- | --- | --- | --- | --- |
| 1 **Measured** | `MistHelper.py`, `_print_interactive_menu()`, near line 6015 | 1034.642 ms per 200 redraws | High, because sorting repeats each redraw | Low, if key changes invalidate the cache | High |
| 2 **Measured** | `MistHelper.py`, `_dispatch_main_mode()`, near line 6181 | 169.752 ms per 20000 dispatches | High, because lambdas and tuples rebuild each call | Low, if handlers stay late-bound | High |
| 3 **Rejected** | sorted safe and unsafe lists near lines 4720 and 4860 | Dynamic input lists drive the output | Low for this issue | Medium, because invalidation is input-specific | Medium |

## 6. Recommended optimizations

**Measured**: Cache the sorted menu keys for the exact current key tuple. Recompute when the key tuple changes. This preserves runtime registry edits and prevents stale menu keys.

**Measured**: Move the main mode predicate table to a module constant. Store handler names instead of handler objects. Resolve handlers at dispatch time to preserve late binding and tests.

**Rejected**: Do not cache safe and unsafe option lists in the systematic test path. Those lists depend on dynamic arguments and credential state.

## 7. Implemented changes

| Field | Required content |
| --- | --- |
| Change ID and location | **Measured**: `OPT3-CLI-CACHE`, `MistHelper.py`, `_print_interactive_menu()` and `_dispatch_main_mode()`. |
| Evidence | **Measured**: `opt3_cli_baseline.json`, `opt3_cli_candidate.json`, and `opt3_cli_candidate_startup_rerun.json`. |
| Root cause | **Measured**: The code sorted menu keys on each redraw and rebuilt dispatch predicates on each call. |
| Change | **Measured**: The code caches the sorted menu key tuple and the mode predicate table. |
| Before result | **Measured**: Menu wall median 1034.642 ms. Dispatch wall median 169.752 ms. |
| After result | **Measured**: Menu wall median 214.372 ms. Dispatch wall median 35.576 ms. |
| Percentage change | **Measured**: Menu wall time changed by -79.28 percent. Dispatch wall time changed by -79.04 percent. |
| Memory change | **Measured**: Menu peak traced memory changed by -10515 bytes. Dispatch peak changed by -1280 bytes. |
| Test coverage | **Measured**: Added tests for menu cache invalidation and dispatch order with late-bound handlers. |
| Risks | **Measured**: A stale key cache would hide new menu entries. The test mutates the registry and proves invalidation. |
| Confidence level | **Measured**: High for repeated path. Low for startup, because the startup data was noisy. |
| Retention decision | **Measured**: Retained. The isolated repeated path exceeded the 10 percent acceptance rule. |

## 8. Before-and-after measurements

| Change and workload | Metric and unit | Before median and spread | After median and spread | Sample counts | Signed change | Decision |
| --- | --- | --- | --- | --- | --- | --- |
| **Measured** startup `--help` | wall ms | 33457.538, MAD 5618.688 | 49010.311, MAD 11395.176 | 10 and 10 | +46.49 percent | Not accepted as a gain |
| **Measured** startup `--help` rerun | wall ms | 33457.538, MAD 5618.688 | 39014.689, MAD 19860.366 | 10 and 10 | +16.61 percent | No stable startup claim |
| **Measured** menu redraw | wall ms per 200 redraws | 1034.642, MAD 207.426 | 214.372, MAD 10.916 | 31 and 31 | -79.28 percent | Retained |
| **Measured** menu redraw | CPU ms per 200 redraws | 328.125, MAD 15.625 | 203.125, MAD 0.000 | 31 and 31 | -38.10 percent | Retained |
| **Measured** mode dispatch | wall ms per 20000 dispatches | 169.752, MAD 28.803 | 35.576, MAD 2.815 | 31 and 31 | -79.04 percent | Retained |
| **Measured** mode dispatch | CPU ms per 20000 dispatches | 93.750, MAD 0.000 | 31.250, MAD 0.000 | 31 and 31 | -66.67 percent | Retained |

## 9. Memory impact

**Measured**: The menu peak traced memory changed from 16876356 bytes to 16865841 bytes. This is a reduction of 10515 bytes.

**Measured**: The dispatch peak traced memory changed from 174896 bytes to 173616 bytes. This is a reduction of 1280 bytes.

**Measured**: The cache stores two tuples of menu keys and one tuple of dispatch entries for the process life. The memory effect was small and favorable in the harness.

## 10. Correctness and regression validation

| Check | Command or test | Actual result | Limitation or artifact |
| --- | --- | --- | --- |
| **Measured** source compile | `rtk python -m py_compile MistHelper.py` | Passed | Local CPython 3.13.3 |
| **Measured** menu and dispatch tests | `rtk python -m pytest tests\guardrails\test_menu_number_uniqueness.py tests\guardrails\test_operation_registry_menu_coverage.py tests\unit\refactors\test_main_entrypoint.py tests\unit\refactors\test_reject_unsupported_flag_variants.py -q --timeout=180` | 30 passed | Targeted scope |
| **Measured** TUI tests | `rtk python -m pytest tests\unit\ui\test_tui.py -q --timeout=180` | 30 passed | Targeted scope |
| **Measured** hook catalog | `rtk python -m pytest tests\guardrails\test_performance_hook_catalog.py -q --timeout=180` | 4 passed | Snapshot did not need an update |
| **Measured** menu reference drift | `rtk python scripts\generate_menu_wiki.py` and `rtk git diff --quiet -- documentation\menu_reference.md documentation\wiki\Menu-Reference.md` | Passed | Generated files matched |
| **Measured** Ruff | `rtk python -m ruff check MistHelper.py` | Passed | Target file |
| **Measured** Black | `rtk python -m black --check MistHelper.py` | Passed | Target file |
| **Blocked** pydocstyle | `rtk python -m pydocstyle MistHelper.py` | Failed | Existing module docstring findings remain outside this change |
| **Measured** Bandit | `rtk python -m bandit -q MistHelper.py` | Passed | Target file |
| **Measured** whitespace | `rtk git diff --check` | Passed | Worktree diff |

## 11. Rejected ideas and why they were rejected

| Idea and location | Evidence | Reason for rejection | Reverted or never implemented |
| --- | --- | --- | --- |
| **Rejected** cache sorted safe and unsafe option lists | Dynamic inputs build those lists | The cache key would need credentials and caller inputs | Never implemented |
| **Rejected** change import or dependency order | Startup path is noisy and has side effects | The task requires conservative edits | Never implemented |
| **Rejected** change public menu structures | Guardrail tests protect menu identity | Public behavior must not change | Never implemented |

## 12. Remaining opportunities

| Opportunity and status | Missing evidence or blocker | Exact next benchmark | Expected value and risk |
| --- | --- | --- | --- |
| **Hypothesis** reduce startup logging side effects | `--help` logs and log rotation affected importtime output | Run isolated startup with logging disabled by a safe entry flag | Medium value, medium risk |
| **Hypothesis** profile option-list sort in systematic tests | This issue measured the repeated menu and mode path first | Run `--test` with placeholder credentials and cProfile | Low value, medium risk |
| **Blocked** pydocstyle cleanup | Existing findings are outside this issue | File a separate issue and run pydocstyle again | Low value, low risk |
