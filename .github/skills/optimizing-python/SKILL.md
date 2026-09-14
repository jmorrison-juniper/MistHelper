---
name: optimizing-python
description: >-
  Use when you profile, benchmark, optimize, or investigate slow Python 3.12+ code.
  Use for CPU time, latency, single-worker throughput, memory, allocations, startup,
  imports, serialization, caching, or database, Redis, network, and filesystem I/O.
  Require representative workloads, repeatable before-and-after measurements,
  correctness tests, and a performance report. Exclude multiprocessing, threads,
  asyncio concurrency, worker-count changes, distributed execution, task sharding,
  GPU parallelization, and all other application parallelization.
---

# Optimize Python with measurements

Prove each retained optimization with repeatable measurements. A shorter
implementation is not evidence of better performance.

## Scope and safety

Optimize a sequential application path on Python 3.12 or newer. Keep the
repository's supported Python versions. Do not lower a higher minimum version.

1. Preserve public APIs, return types, ordering, numeric behavior, and error
   behavior. Preserve protocol and storage compatibility.
2. Preserve validation, authorization, bounds checks, cleanup, and required
   operational logging. Never exchange correctness or security for speed.
3. Do not propose or change multiprocessing, multithreading, or asyncio
   concurrency. Exclude worker-count changes, distributed execution, task
   sharding, GPU parallelization, and other parallelization strategies.
4. Use safe local workloads by default. Prefer fixtures, sanitized recordings,
   and disposable stores. Never repeat destructive production operations for a
   benchmark. Live requests require explicit authorization and a bounded budget.
5. Follow the repository's edit, test, dependency, artifact, and approval rules.
   Keep secrets and private payloads out of reports and benchmark metadata.

Native libraries must not introduce hidden parallel execution. Verify their
execution mode before a comparison. Keep application concurrency settings
unchanged on both sides.

`pyperf` starts measurement processes sequentially. This isolates measurements
without parallelizing the application. If subprocesses are also prohibited,
use repeated in-process measurements and state the isolation limitation.

## Workflow

### 1. Establish the contract and baseline

1. Read the project instructions, entry points, dependencies, tests, and existing
   benchmarks. Verify the selected interpreter and its virtual environment.
2. Name the primary objective and workload. Define typical and worst-case sizes,
   cold and warm states, a resource budget, and acceptance criteria.
3. Run the existing safe test suite before optimization. Record failures and
   skipped tests separately. Do not repair unrelated defects in the same change.
4. Build a repeatable benchmark from representative inputs. Record fixture
   provenance, expected outputs, and the measured boundary.
5. Save the unmodified baseline, source revision, local change state, harness,
   commands, and raw results. Do not overwrite the baseline with candidate data.

Read [the benchmark guide](./references/benchmarking.md) before collecting
measurements. If representative inputs are unavailable, label synthetic results
as exploratory. Do not claim a production improvement from those results.

### 2. Profile the representative path

1. Select the tool for the question. Use `cProfile` for call attribution,
   `tracemalloc` for traced allocations, and a supported sampler when necessary.
2. Separate Python execution, native execution, database time, network time,
   filesystem time, serialization, lock or queue waiting, and startup.
3. Record exact files, functions, line ranges, call counts, and measured costs.
   State tool limitations instead of inventing a breakdown.
4. Distinguish CPU time from wall-clock time. Default profiler timings can include
   waiting and instrumentation overhead.
5. Use separate uninstrumented runs to measure performance. A profile identifies
   a candidate but does not prove an improvement.

### 3. Rank the candidates

Read the relevant parts of
[the optimization checklist](./references/optimization-checklist.md).

Investigate algorithms and repeated work first. Then inspect I/O counts, data
structures, allocations, serialization, bounded caching, and measured Python
loops. Inspect object layout, garbage collection, and startup next. Consider
native acceleration last. Let the stated objective change this order when
necessary, such as a startup-specific request.

Use these estimates to support the ranking:

- `impact = execution_frequency * time_per_call * addressable_fraction`
- `priority = expected_gain * confidence / implementation_risk`

Use consistent units and nonzero risk values. These formulas are ranking aids,
not measurements. Avoid counting the same nested cumulative time twice.
Include maintenance cost and the affected share of the complete workload.

### 4. Change one concern

1. State the measured bottleneck and root cause. Record current and proposed
   complexity when relevant. Estimate the gain conservatively.
2. Choose the smallest safe change. Explain semantic risks, memory costs,
   invalidation rules, and deployment effects before editing.
3. Add tests for equivalent outputs, edge cases, failures, and relevant resource
   behavior. Add a focused benchmark for the candidate.
4. Measure the baseline and candidate with equivalent inputs and settings.
   Measure memory separately from timing. Check the important end-to-end path.
5. Reject or revert an insignificant, unstable, unsafe, or unjustified change.
   Revert only your own edits. Preserve other contributors' work.

If the harness changes, rerun both revisions with that harness. Do not combine
unrelated optimizations or retain speculative rewrites as performance fixes.

### 5. Validate and report

1. Run the functional and regression tests. Run the repository's required quality
   checks. State every skipped or blocked check.
2. Compare outputs, errors, logs, wire data, and stored data as applicable.
3. Report the median, spread, sample count, memory effect, and I/O counts.
   Check warmup, noise, and regressions outside the target path.
4. Review readability, maintenance cost, and the acceptance criteria.
5. Create the twelve-section
   [performance report](./references/report-template.md). Link the raw evidence
   and reproduction commands for each retained change.

If profiling or benchmark evidence is unavailable, use **Hypothesis**. Give the
exact benchmark needed to resolve it. Never claim that unmeasured code is faster.

## Acceptance criteria

For a complexity-increasing micro-optimization, require at least one result:

- A reproducible improvement of at least **5%** in an important end-to-end path.
- A reproducible improvement of at least **10%** in an isolated hotspot.
- A meaningful reduction in memory, latency tails, or I/O counts that satisfies
  an objective defined before the experiment.

The effect must exceed measurement uncertainty. Passing a percentage threshold
does not excuse unstable results or a correctness regression. An isolated gain
does not establish an equivalent end-to-end gain.

Other changes still require a repeatable benefit. Smaller gains need explicit
operational value and maintainable code. Reject workload-specific gains without
a clear reason that the workload matters. These thresholds are policy defaults,
not guarantees from Python or `pyperf`.

## Reference map

| Need | Read |
| --- | --- |
| Establish comparable measurements. | [Benchmark methodology and commands](./references/benchmarking.md) |
| Investigate a measured bottleneck. | [Optimization checklist and risks](./references/optimization-checklist.md) |
| Record evidence and decisions. | [Performance report template](./references/report-template.md) |
| Install, validate, or check a source. | [Installation, scenarios, and sources](./references/installation-and-sources.md) |

Load only the guides needed for the current step.

## Install and invoke

Copy the complete `optimizing-python` folder into `.github/skills/` in the target
repository. Keep `SKILL.md` and `references/` together. Installation needs no
Python package, API token, runtime change, or benchmark execution.

Ask: "Use optimizing-python to profile this path and retain only measured
improvements." For an audit without application edits, add "Report only."
In a compatible VS Code agent, you can also invoke `/optimizing-python`.
