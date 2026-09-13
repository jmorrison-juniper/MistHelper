# Python Performance Report: Performance monitoring memory

## 1. Executive summary

**Measured**: The performance recorder keeps memory bounded by the sink
capacity and by the cache limits. A disabled span kept zero queued events and
4,144 traced Python bytes in the measured harness. A full default queue of
2,048 worst case events retained 14,156,856 traced Python bytes.

The sustained run emitted 50,000 minimal events. The queue retained 2,048
events, dropped 47,952 events, and plateaued at 861,096 traced Python bytes.

## 2. Environment and Python version

**Measured**: CPython 3.13.3 ran from
`C:\Users\jmorrison\mh-mem\.venv\Scripts\python.exe` on
Windows 11 AMD64. The platform string was `Windows-11-10.0.26200-SP0`.

The branch was `perf/2482-memory-measurement`. The worktree was
`C:\Users\jmorrison\mh-mem`. The bootstrap command completed successfully in
that worktree, so no fallback interpreter was needed.

## 3. Benchmark methodology

**Measured**: The harness at `tools/performance_memory.py` ran one bounded
scenario for each memory question. It used `tracemalloc` for traced Python
current bytes, traced Python peak bytes, and the top live allocation sites.

Process memory used the Windows `GetProcessMemoryInfo` API through `ctypes`.
The report keeps Windows working set bytes and private bytes separate from
traced Python bytes. The project did not declare `psutil`, so the harness did
not add or use that dependency.

The memory runs did not measure timing. The harness stopped `tracemalloc`
before any future timing run could execute.

Artifact:

- `data\performance-memory.json`

## 4. Baseline results

| Scenario | Traced current bytes | Traced peak bytes | Process working set after | Process private bytes after |
| --- | ---: | ---: | ---: | ---: |
| Disabled span, level off | 4,144 | 4,288 | 32,661,504 | 15,929,344 |
| One minimal enabled span | 5,024 | 6,682 | 32,698,368 | 15,929,344 |
| One worst case event | 11,712 | 13,178 | 32,727,040 | 15,929,344 |
| Full queue, minimal events | 860,880 | 861,212 | 34,656,256 | 18,923,520 |
| Full queue, worst case events | 14,156,856 | 14,157,315 | 67,608,576 | 52,805,632 |
| Sustained minimal events | 861,096 | 861,656 | 42,356,736 | 26,259,456 |
| Bounded caches | 100,980 | 101,971 | 42,778,624 | 27,557,888 |

## 5. Ranked hotspot list

| Rank and status | File, symbol, and lines | Measured cost and frequency | Expected gain | Risk and maintenance cost | Confidence |
| --- | --- | --- | --- | --- | --- |
| 1, Measured | `tools/performance_memory.py`, worst dimensions | 6,860,800 bytes in the full worst case queue | Low | Low | High |
| 2, Measured | `tools/performance_memory.py`, worst measurements | 6,729,656 bytes in the full worst case queue | Low | Low | High |
| 3, Measured | `tools/performance_memory.py`, minimal measurement dict | 425,112 bytes in the full minimal queue | Low | Low | High |

## 6. Recommended optimizations

**Measured**: Keep the default `RecorderSettings.level` value at `off`. Keep the
`BoundedSink` default capacity at 2,048 events unless an operator accepts the
measured memory cost. Keep cache limits at 1,024 safe values, 256 label keys,
and 512 measurement keys.

## 7. Implemented changes

| Field | Required content |
| --- | --- |
| Change ID and location | `PERF-MEM-001`, `tools/performance_memory.py` |
| Evidence | `data\performance-memory.json` from the local run |
| Root cause | Section 9 had only structural memory claims and no measured values |
| Change | Added a memory harness that reports traced Python memory and Windows process memory separately |
| Before result | Not measured |
| After result | Full worst case queue retained 14,156,856 traced Python bytes |
| Percentage change | Not applicable, because this change replaces an unmeasured claim |
| Memory change | Not applicable, because this change adds measurement evidence |
| Test coverage | `tests\test_performance_memory.py` covers capacity, plateau, and safe value cache bounds |
| Risks | Process working set changes include allocator and operating system effects |
| Confidence level | High for traced Python bytes and cache bounds. Medium for process deltas. |
| Retention decision | Retained. The report now gives the operator measured memory values. |

## 8. Before-and-after measurements

| Change and workload | Metric and unit | Before median and spread | After median and spread | Sample counts | Signed change | Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `PERF-MEM-001`, disabled span | Traced Python current bytes | Not measured | 4,144 | 1 memory run | Not applicable | Retained |
| `PERF-MEM-001`, full worst case queue | Traced Python current bytes | Not measured | 14,156,856 | 1 memory run | Not applicable | Retained |
| `PERF-MEM-001`, sustained minimal queue | Traced Python current bytes | Not measured | 861,096 | 1 memory run | Not applicable | Retained |

## 9. Memory impact

**Measured**: The table below replaces the earlier unmeasured structural claim.
`tracemalloc` reports net live traced Python allocations for each scenario.
Windows process memory reports working set and private bytes as separate
process metrics.

| Scenario | Queued events | Traced current bytes | Traced peak bytes | Process working set before | Process working set after | Process private before | Process private after | Bound evidence |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Disabled span, level off | 0 | 4,144 | 4,288 | 32,522,240 | 32,661,504 | 15,929,344 | 15,929,344 | No event reached the sink |
| One minimal enabled span | 1 | 5,024 | 6,682 | 32,665,600 | 32,698,368 | 15,929,344 | 15,929,344 | One queued span |
| One worst case event | 1 | 11,712 | 13,178 | 32,698,368 | 32,727,040 | 15,929,344 | 15,929,344 | One event with 16 labels and 32 measurements |
| Full queue, minimal events | 2,048 | 860,880 | 861,212 | 32,727,040 | 34,656,256 | 15,929,344 | 18,923,520 | Queue reached capacity with no drops |
| Full queue, worst case events | 2,048 | 14,156,856 | 14,157,315 | 34,660,352 | 67,608,576 | 19,136,512 | 52,805,632 | Queue reached capacity with no drops |
| Sustained minimal events | 2,048 | 861,096 | 861,656 | 42,606,592 | 42,356,736 | 26,615,808 | 26,259,456 | 50,000 events emitted and 47,952 dropped |
| Bounded caches | Not applicable | 100,980 | 101,971 | 42,356,736 | 42,778,624 | 27,041,792 | 27,557,888 | Safe cache held 1 entry. LRU caches held 256 and 512 entries. |

Per-event traced current bytes from the full queue were 420.35 bytes for the
minimal event and 6,912.53 bytes for the worst case event. The one-event runs
measured 5,024 traced current bytes for a minimal enabled span and 11,712
traced current bytes for one worst case event.

The sustained minimal run plateaued at 861,096 traced current bytes. That value
is within 216 bytes of the full minimal queue value, although the sustained run
emitted 47,952 additional events.

Top allocation sites for the full worst case queue:

| Site | Live traced bytes |
| --- | ---: |
| `tools\performance_memory.py:163` | 6,860,800 |
| `tools\performance_memory.py:169` | 6,729,656 |
| `tools\performance_memory.py:151` | 213,080 |
| `tools\performance_memory.py:168` | 130,816 |
| `tools\performance_memory.py:162` | 130,752 |

## 10. Correctness and regression validation

| Check | Command or test | Actual result | Limitation or artifact |
| --- | --- | --- | --- |
| Compile | `python -m compileall src\utils\performance tools -q` | Passed | Windows and Python 3.13.3 |
| Memory harness | `python -m tools.performance_memory` | Passed | Wrote `data\performance-memory.json` |
| Queue capacity | `python -m pytest tests\test_performance_memory.py -q` | Passed | Small deterministic queue |
| Memory plateau | `python -m pytest tests\test_performance_memory.py -q` | Passed | Small deterministic queue |
| Safe value cache | `python -m pytest tests\test_performance_memory.py -q` | Passed | Clears after the limit |

## 11. Rejected ideas and why they were rejected

| Idea and location | Evidence | Reason for rejection | Reverted or never implemented |
| --- | --- | --- | --- |
| Add `psutil` | `pyproject.toml` dependency check | The project did not declare it, and the task forbade a dependency change | Never implemented |
| Report `tracemalloc` bytes as RSS | Measurement contract | Traced Python bytes and process memory are different metrics | Never implemented |
| Use `sys.getsizeof` alone | Honesty requirement | It does not measure an object graph | Never implemented |

## 12. Remaining opportunities

| Opportunity and status | Missing evidence or blocker | Exact next benchmark | Expected value and risk |
| --- | --- | --- | --- |
| Linux process memory, Not measured | This run used Windows only | Run the same harness on Linux with a supported process memory method | Better cross-platform process values, low risk |
| Timing overhead, Not measured here | Timing must run without `tracemalloc` | Run an untraced timing harness for enabled spans | Separate latency evidence, low risk |
| Native memory split, Not measured here | This harness does not sample native allocators | Run a supported sampler in a bounded diagnostic session | More complete attribution, medium tool risk |
