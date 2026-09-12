---
name: parallelizing-python
description: >-
  Use when you choose, design, review, or repair a Python concurrency or parallelism
  strategy. Use for threads, processes, asyncio, subinterpreters, free-threaded builds,
  thread pools, process pools, task queues, and distributed execution. Use for the global
  interpreter lock, start methods, pickling limits, shared memory, oversubscription,
  backpressure, cancellation, graceful shutdown, and worker failure. Use to select
  between vectorized libraries, compiled extensions, multiple processes, and a cluster.
  Require a measured bottleneck, a scaling measurement, and a correctness test before
  you keep a parallel design. Exclude single-worker sequential optimization, which
  belongs to the optimizing-python skill.
---

# Parallelize Python with evidence

Choose the execution model from a measured bottleneck. A parallel design costs
correctness risk, memory, and maintenance. Prove the gain before you keep it.

## Scope and safety

1. Measure first. Name the bottleneck as processor time, waiting time, memory,
   or a remote service limit. Never parallelize an unmeasured program.
2. Remove the work before you distribute the work. A better algorithm, a cache,
   or a vectorized library often beats every parallel design.
3. Preserve public interfaces, result values, result order, and error behavior.
   Preserve validation, authorization, and required operational logging.
4. Respect the rate limit of each external service. More workers can turn a
   slow program into a refused program.
5. Follow the repository rules for edits, tests, dependencies, and approval.
   Keep secrets and private payloads out of reports and benchmark metadata.

Warning: a parallel defect hides. A race condition can pass a test suite for
months and then corrupt production data under load. Treat every shared mutable
value as a defect until you prove that a lock, a queue, or a copy protects it.

State the target interpreter before you choose a model. The execution rules
differ across Python 3.13 and Python 3.14. Read
[the runtime and version guide](./references/runtime-and-versions.md) first.

## The decision sequence

Answer these questions in order. Stop at the first answer that fits.

| Question | Answer | Model |
| - | - | - |
| Does the program wait for a network, a disk, or a subprocess? | Yes | `asyncio`, or a thread pool for a blocking library |
| Is the hot loop an array or a table operation? | Yes | NumPy, Polars, DuckDB, or PyArrow |
| Is one small compiled kernel the whole cost? | Yes | Numba, Cython, or Rust through PyO3 |
| Are the tasks independent, with small inputs and outputs? | Yes | `ProcessPoolExecutor` |
| Do the workers need the same large array? | Yes | `ProcessPoolExecutor` with `shared_memory` or `mmap` |
| Must the work survive a restart, or run on a schedule? | Yes | A durable task queue, such as Celery |
| Does the data exceed one machine? | Yes | Dask, Ray, or Spark |

Read [the strategy matrix](./references/strategy-matrix.md) for the complete
table of 50 strategies, with the memory model, the transfer cost, and the risks.

## Workflow

### 1. Measure the bottleneck

1. Profile the representative path. Separate processor time from waiting time.
   A profile that reports only wall-clock time cannot select a model.
2. Record the target interpreter, the operating system, the core count, and the
   external service limits.
3. Compute the parallel fraction. Amdahl's law bounds the result. If 20 percent
   of the run is sequential, 8 workers give at most 3.3 times the speed.
4. Record the sequential baseline. Save the command, the inputs, and the raw
   results. Never overwrite the baseline with candidate data.

### 2. Choose the model

1. Apply the decision sequence above. State the reason in one sentence.
2. Check the data transfer cost. A process boundary serializes every argument
   and every result. Read the overhead table in the strategy matrix.
3. Size the unit of work. A task must run far longer than the cost to dispatch
   it. Group small items into batches.
4. Check the failure model. Decide now what happens when one worker fails, when
   the user cancels, and when the process receives a stop signal.

### 3. Implement the smallest safe version

1. Write the worker as a pure function of its arguments. Pass every value
   explicitly. A background worker does not inherit a thread-local value.
2. Bound the queue and the pool. An unbounded queue converts a slow consumer
   into an out-of-memory failure.
3. Add cancellation and shutdown paths before you add speed.
4. Set the start method explicitly. Do not rely on the platform default,
   because the default changed in Python 3.14.

Read [the correctness and safety guide](./references/correctness-and-safety.md)
before you write the worker. It covers races, deadlock, fork safety, worker
failure, oversubscription, and shutdown.

### 4. Prove the gain

1. Run the sequential baseline and the parallel candidate on the same inputs,
   the same machine, and the same settings.
2. Measure a scaling curve. Record the time at 1, 2, 4, and 8 workers. A curve
   that flattens early shows contention, not a benefit.
3. Measure memory. Each process holds a separate interpreter. Report the peak
   total, not the peak of one worker.
4. Test correctness under load. Compare results against the sequential run.
   Repeat the test enough times to expose an ordering defect.
5. Reject the change when the curve is flat, when the memory cost is too high,
   or when the results differ from the sequential run.

Read [the measurement guide](./references/measuring-parallel-gains.md) for the
commands, the scaling table, and the report sections.

### 5. Report and hand over

State the model, the measured speedup, the worker count, the memory cost, and
the failure behavior. Name every check that you could not run. Record the exact
interpreter version, because the result does not transfer across versions.

## Acceptance criteria

Keep a parallel design only when every item below is true.

1. The speedup is at least **1.5 times** on the important path, measured on a
   representative workload. A smaller gain rarely pays for the risk.
2. The scaling curve rises for each added worker up to the chosen count.
3. The parallel run gives the same results as the sequential run.
4. The peak memory fits the deployment budget.
5. The design handles worker failure, cancellation, and shutdown.

These thresholds are policy defaults for this repository. They are not
guarantees from Python. A design that fails one item goes back to sequential.

## Reference map

| Need | Read |
| - | - |
| Select a strategy from 50 options. | [Strategy matrix](./references/strategy-matrix.md) |
| Check a version-specific runtime rule. | [Runtime and versions](./references/runtime-and-versions.md) |
| Avoid a race, a deadlock, or a leak. | [Correctness and safety](./references/correctness-and-safety.md) |
| Prove a speedup. | [Measuring parallel gains](./references/measuring-parallel-gains.md) |
| Check a claim against its source. | [Audit and sources](./references/audit-and-sources.md) |

Load only the guides that the current step needs.

## Install and invoke

Copy the complete `parallelizing-python` folder into `.github/skills/` in the
target repository. Keep `SKILL.md` and `references/` together. Installation
needs no Python package, no API token, and no runtime change.

Ask: "Use parallelizing-python to choose and prove a concurrency model for this
path." For an audit without code changes, add "Report only." In a compatible
VS Code agent, you can also invoke `/parallelizing-python`.

This skill covers parallel and concurrent execution. For sequential
single-worker optimization, use the `optimizing-python` skill instead.
