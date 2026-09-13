# Performance report: monitoring foundation

This report covers tasks T01 through T04 of the hook catalog. The measured
subject is the instrumentation itself, because a hook must cost less than the
budget before it may wrap an application path.

Status labels: **Measured**, **Hypothesis**, **Rejected**, **Blocked**.

## 1. Executive summary

**Objective.** Build the performance event foundation and prove that one span
costs less than one percent of a representative operation.

**Result. Measured.** One base span costs 20,917 ns to 25,037 ns across three
independent collections against the modules on `main`, which is 0.42 to 0.50
percent of a five millisecond operation. A disabled span costs 506 ns to 592 ns.

| Gate | Budget | Measured | Verdict |
| --- | --- | --- | --- |
| Base level | below 1 percent | 0.42 to 0.50 percent | Pass |
| Targeted level | below 2 percent | below 0.50 percent | Pass |

An earlier branch revision of the same modules measured 15,177 ns to 19,961 ns
with a control value near 500 ns. The two ranges overlap at their edges and both
pass the gate. This report keeps the measurement of the code on `main`, because
that is the code that ships.

The acceptance criteria passed. This work measured the instrumentation only. No
hook wraps an application path yet, so the report claims no end-to-end result.

Application parallelization stayed out of scope. The work changed no concurrency
setting, no worker count, and no asynchronous behavior.

## 2. Environment and Python version

| Field | Value |
| --- | --- |
| Interpreter | CPython 3.13.3, 64 bit |
| Virtual environment | `.venv` |
| Operating system | Windows, x86_64 |
| Base revision | `e7cd9c3`, the hook catalog commit |
| Candidate revision | `0546668`, the foundation commit |
| Harness | `tools/bench_performance_overhead.py` |
| Tools | pytest 9.1.1, ruff, black 26.5.1, cProfile, pstats |

The host is a shared developer workstation. Section 8 states how the report
detects a contaminated window.

## 3. Benchmark methodology

**Entry point.** `tools/bench_performance_overhead.py`.

**Workload.** The harness runs an empty call inside one span, 20,000 times for
each repeat, for 9 repeats. It measures four conditions and interleaves them, so
any drift affects each condition equally.

| Condition | Meaning |
| --- | --- |
| `bare` | The loop and the empty call, with no span. |
| `off` | A span at a level that forbids its family. This is the control value. |
| `base` | A span in the `operation` family at the base level. |
| `targeted` | A span in the `serialization` family at the targeted level. |

**Measured boundary.** The harness reads `perf_counter_ns` once before the loop
and once after it. It subtracts the `bare` median and divides by the call count,
which gives the cost of one span. It drains the queue outside the timed region.

**Why this reports an absolute cost.** An overhead share depends on the size of
the operation the hook wraps. The nanosecond cost of one span does not.

**Budget.** Base below 1 percent, targeted below 2 percent, from `spec.md`.

**Commands.**

```
python tools/bench_performance_overhead.py --calls 20000 --repeats 9
python -m pytest tests/test_performance_monitoring.py -q
python -m ruff check src/utils/performance tests/test_performance_monitoring.py
python -m black --check src/utils/performance tests/test_performance_monitoring.py
```

## 4. Baseline results

This package is new, so there is no earlier revision of it to compare against.
The table records the first valid measurement of the delivered design.

| Condition | Metric | Median | Sample count |
| --- | --- | --- | --- |
| Base span | Cost of one span | 21,831 ns | 3 collections of 9 repeats of 20,000 calls |
| Disabled span, control | Cost of one span | 560 ns | 3 collections of 9 repeats of 20,000 calls |

The design already carried the four optimizations that the fiber-planner report
records, because that repository proved them first. Those are:

1. The sink stores the event and encodes it at flush time.
2. A bounded cache holds the key checks and the proven safe label values.
3. The event holds an integer timestamp and formats it only at output.
4. A forbidden family returns a shared null span, which reads no clock.

## 5. Ranked hotspot list

A `cProfile` run over 20,000 spans produced this attribution. The profiler adds
overhead, so the ranking is relative, not an absolute cost.

| Rank | Location | Measured cost | Note |
| --- | --- | --- | --- |
| 1 | `event._validate_measurements` | 0.299 s of 2.815 s | Every event carries three measurements, and each one is checked. |
| 2 | `json/encoder.py` `iterencode` | 0.292 s | This ran because the profile drained the queue inside its loop. The harness drains outside the timed region. |
| 3 | `event._validate_dimensions` | 0.141 s | A key check for every label. |
| 4 | `event._require`, 420,000 calls | 0.108 s | Twenty-one contract checks for each span. |
| 5 | `datetime.isoformat` | 0.111 s | This ran at drain time, not in the measured path. |

## 6. Recommended optimizations

The profile shows that the contract checks dominate the remaining cost. Section
11 records the one candidate that was tested and rejected. Section 12 states the
next benchmark for the others.

## 7. Implemented changes

No optimization was retained in this repository during this work.

The package was built with the four proven changes already in place, so there is
no before-and-after pair to report for them. The fiber-planner report holds that
evidence, and the two packages share the same design.

The one candidate that was tested here is in section 11.

## 8. Before-and-after measurements

Measured against the modules on `main`, at commit `058679ad`.

| Collection | Disabled span, control | Base span | Share of a five millisecond operation |
| --- | --- | --- | --- |
| 1 | 592 ns | 25,037 ns | 0.5007 percent |
| 2 | 560 ns | 21,831 ns | 0.4366 percent |
| 3 | 506 ns | 20,917 ns | 0.4183 percent |

An earlier branch revision of the same modules measured 19,961 ns, 15,177 ns,
and 16,724 ns, with a control value of 551 ns, 442 ns, and 525 ns. The control
value in that session was about 10 percent lower, so part of the difference is
host state. Both ranges pass the gate.

**A contaminated window, and how the report detected it.** An earlier collection
reported 40,765 ns and then 43,810 ns for a base span. The disabled span rose to
846 ns and 1,386 ns in the same window. The disabled path does not run the code
under test, so a change in that control value shows host load, not a source
change. The report discards that window and keeps the three collections above,
which share a stable control value near 500 ns.

**End-to-end result. Not measured.** No hook wraps an application path yet.

## 9. Memory impact

**Not measured** with `tracemalloc`. The known memory effects are bounded by
design:

- The sink queue holds at most `capacity` events, 2,048 by default. The operator
  setting clamps to 65,536.
- The contract bounds each event at 16 labels of at most 96 characters and 32
  measurements.
- The caches are bounded at 256 and 512 entries, and the safe value set clears
  at 1,024 entries.

## 10. Correctness and regression validation

| Check | Command | Result |
| --- | --- | --- |
| New unit tests | `python -m pytest tests/test_performance_monitoring.py -q` | 71 passed |
| Existing tests | `python -m pytest tests/ -k "utils or logger or console" -q` | 1,503 passed, 14,346 deselected |
| Byte compile | `python -m compileall src/utils/performance -q` | Pass |
| Lint | `python -m ruff check src/utils/performance tests/test_performance_monitoring.py` | All checks passed |
| Format | `python -m black --check src/utils/performance tests/...` | 7 files unchanged |
| Import check | `import src.utils, src.utils.performance` | Pass |

The tests cover the contract, the source attribution, the privacy rules, the
clocks, the sink bounds, the failure circuit, the level gate, and the settings
reader.

Three rules receive a dedicated test, because they protect a guarantee:

1. `test_an_error_records_the_class_and_not_the_message` proves that an
   exception message never reaches an event.
2. `test_an_unlisted_label_is_dropped_before_the_sink` proves that the allowlist
   runs before the sink.
3. `test_a_write_failure_never_raises` proves that a broken sink does not change
   the result of a measured operation.

**Blocked.** The complete suite holds 15,849 collected tests. This change adds a
new subpackage and modifies no existing module, and the 1,503 tests that touch
`src/utils` all pass. A reviewer must still run the full gate before a merge.

## 11. Rejected ideas

| Idea | Evidence | Reason | State |
| --- | --- | --- | --- |
| Replace `_require` with inline checks, to avoid building a message string on each pass | The profile showed 420,000 calls to `_require` for 20,000 spans, rank 4 in section 5 | The change produced no measurable gain. The measurement window was contaminated at the same time, which the control value revealed. | Reverted. The file returned to the `_require` form. |

The idea remains plausible. Section 12 names the benchmark that would settle it
on a quiet host.

## 12. Remaining opportunities

| Opportunity | Missing evidence | Exact next benchmark | Value and risk |
| --- | --- | --- | --- |
| End-to-end overhead on a real command | No hook wraps an application path yet | Wrap `MistHelper.py` `_dispatch_main_mode`, then compare one command with the level off and the level base, 3 collections, with the output compared outside the timed boundary | High value. The one percent budget applies to this result. |
| The rejected inline validation | The window was contaminated | Rerun the harness on an idle host, 3 collections, and accept the change only when the control value stays near 500 ns and the base cost falls by more than the collection spread | Low value, low risk. The current spread is about 4,800 ns, so the change must save more than that to be visible. |
| The cost of `process_time_ns` on this host | Not isolated | Compare the base level with `MISTHELPER_PERF_CPU=1` and `MISTHELPER_PERF_CPU=0`, 9 repeats | Medium value. It decides whether the CPU clock stays on by default on Windows. |
| The Mist transport hooks, T06 | Not implemented | Add the transport hook, then count requests, retries, and pages against a recorded fixture, and compare the counts with the client log | High value. It is the largest measured cost in the product. |
| The remaining catalog hooks | Not implemented | Implement one family at a time and rerun this harness after each family | The budget applies to the sum of the enabled hooks, not to one hook. |
