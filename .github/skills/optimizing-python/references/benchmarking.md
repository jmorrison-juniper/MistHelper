# Benchmark methodology

Read this guide before a baseline or comparison. Select measurements that answer
the optimization contract. Do not collect every metric without a reason.

## 1. Define the contract and environment

Record these fields before editing application code.

| Field | Required information |
| --- | --- |
| Objective | Name latency, throughput per single worker, CPU time, memory, allocations, startup, serialization, or I/O reduction. |
| Workload | Name the entry point, input source, sizes, distributions, expected output, and cold or warm state. |
| Constraints | Record supported versions, public behavior, safety controls, logging, and the prohibition on parallelization. |
| Budget | Set maximum duration, repetitions, input size, memory, external requests, and artifact storage. |
| Acceptance | Define the minimum useful gain and permitted trade-offs before examining candidate results. |

Record the exact Python executable, implementation, version, build, and virtual
environment. Record the operating system, architecture, CPU, dependencies, and
profiler versions. Include relevant database versions, indexes, and client
configuration when they affect the measurement.

Record power mode, background load, filesystem, container or WSL use, and logging
settings. Keep them equivalent across comparisons. Do not combine results from
different interpreters or machines as proof of a source-only improvement.

Save the source revision and local changes with the baseline. `HEAD` alone does
not describe a dirty working tree. Keep the harness revision and input identity
with each result. Hash only nonsecret fixtures when a digest helps identify them.

Use the project's artifact directory. For a project that requires outputs under
`data/`, use a task-specific directory under `data/performance/`. Do not overwrite
another run or publish sensitive artifacts.

## 2. Build equivalent workloads

1. Prefer existing fixtures, integration scenarios, sanitized samples, or recorded
   workloads. Preserve realistic key cardinality, duplicate rates, nesting, and
   payload sizes. Include typical and worst-case inputs.
2. Define the measured boundary. Include setup, conversion, indexing, and cache
   population costs when the production operation pays those costs.
3. Reset mutable inputs, iterators, outputs, and disposable stores for every
   logical operation. Calibration and warmup also execute the workload.
4. Check equivalent outputs outside the timed boundary. Fully consume lazy
   outputs inside that boundary when the application consumes them.
5. Separate cold, warm, cache-miss, cache-hit, and sustained workloads. Record
   which caches remain warm, including filesystem and database caches.

Do not repeatedly measure an exhausted iterator, an already sorted mutable list,
or a cache hit while describing the result as a cold operation. Do not exclude
an index construction that occurs on every real call.

A fresh interpreter does not guarantee a cold filesystem cache. Do not clear
system caches or alter shared machine settings without authorization.

Use read-only replay or disposable stores for I/O tests. A mock can prove a
reduction in request count. It cannot establish real network latency. Keep
timeouts, retries, rate limits, payloads, and transaction behavior equivalent.

## 3. Collect the right measurements

### Tool selection

| Question | Tool | Limitation |
| --- | --- | --- |
| Which calls consume time? | Use `cProfile` and `pstats`. | The default timer is not a CPU-only breakdown. Instrumentation adds cost. |
| Is a small operation cheaper? | Use `timeit` with repeated samples. | Setup exclusions, call overhead, and GC defaults can mislead. |
| Is the change repeatable? | Prefer `pyperf`. | Inspect calibration, warmup, metadata, distributions, and warnings. |
| Which Python allocations remain? | Use `tracemalloc` snapshots. | Snapshots show live traced allocations, not total allocation churn. |
| What is the traced memory peak? | Use `tracemalloc.get_traced_memory()`. | The result is not the total process footprint. |
| Where are Python and native costs? | Use a supported sampler, such as Scalene or py-spy. | Verify the installed version, platform support, permissions, and attribution limits. |
| Which external calls dominate? | Use query logs and application instrumentation. | Counts and elapsed time do not reveal all server execution costs. |
| Which imports delay startup? | Use `-X importtime` on a safe entry point. | Import instrumentation is not a startup benchmark. |

Use the standard-library `profile` module only when its features are necessary
or `cProfile` is unavailable. Its higher overhead also requires separate timing.

### Timing and attribution

Use `time.perf_counter_ns()` for elapsed wall-clock time in a custom harness.
Use `time.process_time_ns()` for the current process's user and system CPU time.
The CPU clock excludes external waiting but does not separate Python from native
execution. The wall-minus-CPU difference is not an exact network-time measure.

Attribute database, network, filesystem, serialization, and lock or queue waiting
with appropriate instrumentation. Mark an unavailable breakdown as **Not
measured**. Do not sum overlapping spans or nested cumulative profiler times.

Run timing without coverage, a debugger, allocation tracing, or a profiler.
Use the production logging configuration on both revisions. Keep required logs.
If production disables debug logs, do not benchmark with debug logs enabled.

### Memory and allocation measurements

Start allocation tracing before the work you intend to observe. Compare snapshots
by allocation site. Record current and peak traced bytes, retained objects, and
the duration of a sustained run where relevant.

Snapshot differences show net live allocations. They can miss objects that are
created and released between snapshots. Do not label a snapshot delta as total
allocation volume. Use an allocation-event profiler when churn is the objective.

Measure process memory separately when native allocations or retained buffers
matter. Name the metric exactly: RSS, private memory, commit charge, or traced
Python bytes. State the platform and sampling method. These metrics are not
interchangeable. `sys.getsizeof()` alone does not measure an entire object graph.

`pyperf` memory modes replace timing values with byte values. Use separate output
files and comparisons for timing, `--tracemalloc`, and `--track-memory`.
Their coverage depends on the command and platform. Do not compare memory output
with timing output or describe every memory mode as RSS.

### I/O and startup measurements

Count logical operations, actual requests, queries, round trips, retries, rows,
and serialized bytes separately. A batch can reduce round trips without reducing
server-side command count. Record both counts when they differ.

For startup, measure fresh process execution and useful completion. Include
imports and initialization in the end-to-end benchmark. Measure first-use costs
separately when a change defers work. Inspect import side effects before invoking
an entry point, including one that advertises `--help`.

## 4. Run repeatable comparisons

### Command recipes

The following names are placeholders, not supplied executables:

- `WORKLOAD.py` names a safe, finite workload selected from the target project.
- `BENCHMARK.py` names a project-specific `pyperf.Runner` harness.
- `BASELINE.json` and `CANDIDATE.json` name distinct raw timing artifacts.
- `PROFILE.pstats` names a trusted local profile artifact.
- `MEMORY.json` names a separate memory artifact.

Replace these names with actual paths before execution. Use the selected virtual
environment's interpreter wherever a recipe says `python`. On Windows, quote a
path with spaces and use the PowerShell call operator when necessary.

| Action | Recipe |
| --- | --- |
| Profile a safe finite workload. | `python -m cProfile -o PROFILE.pstats WORKLOAD.py` |
| Measure a complete command. | `python -m pyperf command -o BASELINE.json -- python WORKLOAD.py` |
| Measure the candidate command. | `python -m pyperf command -o CANDIDATE.json -- python WORKLOAD.py` |
| Run a focused Runner harness. | `python BENCHMARK.py -o BASELINE.json` |
| Check stability warnings. | `python -m pyperf check BASELINE.json CANDIDATE.json` |
| Examine medians and distributions. | `python -m pyperf stats BASELINE.json CANDIDATE.json` |
| Compare the timing artifacts. | `python -m pyperf compare_to --table BASELINE.json CANDIDATE.json` |
| Inspect the environment metadata. | `python -m pyperf metadata BASELINE.json CANDIDATE.json` |
| Inspect individual runs and warmups. | `python -m pyperf dump --verbose BASELINE.json` |
| Measure traced memory separately. | `python BENCHMARK.py --tracemalloc -o MEMORY.json` |

Run the baseline recipe before the application change. Run the candidate recipe
after it. Keep the benchmark names, data, dependency versions, and measured
boundary identical. Repeat the Runner recipe with a separate candidate filename
when using a focused harness.

Confirm optional flags with the installed tool's help. Apply the repository's
command-prefix rules when necessary. Keep any output-filtering proxy outside the
measured workload, and apply it equally on both sides. Do not hide instability
warnings with `--quiet`.

The `pyperf command` recipe includes interpreter startup and shutdown. It also
controls inherited environment variables and standard streams. Verify the child
interpreter and configuration. Do not forward all environment variables or
secrets to make a benchmark work.

### Harness rules

Use `Runner.bench_func()` for a callable with representative inputs. Account for
its call overhead when the operation is extremely small.

Use `Runner.bench_time_func()` only when you need explicit timed boundaries.
Its callback receives `loops` first and returns total elapsed seconds. Runner
normalizes by the loop counts. Do not divide the callback result a second time.

`pyperf` runs its measurement processes sequentially. Keep the workload itself
sequential. If the execution policy prohibits subprocesses, use an in-process
harness with explicit warmup, calibration, repeated wall and CPU measurements,
and raw sample retention. State the reduced isolation.

For `timeit`, inspect the full repeat vector. Normalize each value by its loop
count. Its minimum is a useful lower bound, not a representative latency report.
Report median, spread, and sample count for the experiment as well.

`timeit` disables cyclic GC by default. Enable it in setup when GC is part of
the real workload. Record the choice. Never compare different GC states without
naming that difference as the experiment.

### Noise and decision rules

Start with `pyperf` defaults. Examine warmup values and calibration. Collect
multiple independent before-and-after comparisons on the same host. Use at least
three collections as a starting point when practical, not as statistical proof.

Report the median with MAD or IQR, measured values, runs, loops, and warmup counts.
Loop iterations are not independent samples. Inspect outliers and multimodal
distributions with `pyperf hist` or `pyperf dump`. Do not remove inconvenient
samples without a documented, consistent rule.

Use the comparison's significance result together with effect size, noise, and
workload relevance. A successful command exit is not proof of stable results.
A median does not repair a contaminated experiment. Repeat or mark it inconclusive.

Measure p95 or p99 from enough individual operation latencies when tails matter.
Percentiles of averaged microbenchmark batches are not request-latency percentiles.

## 5. Stop safely and preserve evidence

1. If the environment, inputs, or safety controls prevent a valid run, report the
   blocker and the exact next measurement. Do not fabricate results.
2. If optional tools are unavailable, use supported standard-library tools and
   state their limits. Install optional tools only under the project's rules.
3. Do not change OS governors, security settings, affinity, or shared services
   merely because a profiler suggests system tuning. Obtain authorization first.
4. Preserve baseline artifacts, candidate artifacts, failed attempts, and the
   final decision. Do not mix unrelated experiments in one result file.
5. Rerun correctness and regression checks after the final change. Link their
   results and the exact reproduction commands in the performance report.
