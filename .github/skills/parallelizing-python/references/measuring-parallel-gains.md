# Measuring parallel gains

A parallel change needs a different measurement from a sequential change. One
number does not prove it. You need a scaling curve, a memory figure, and a
correctness comparison.

## What Amdahl's law tells you

The sequential part of a program bounds the whole speedup. If a fraction `p` of
the run is parallel, and `n` workers run it, the best possible speedup is:

$$S(n) = \frac{1}{(1 - p) + \frac{p}{n}}$$

The limit as the worker count grows is `1 / (1 - p)`.

| Parallel fraction | Best speedup with 4 workers | Best speedup with 16 workers | Limit |
| - | - | - | - |
| 50 percent | 1.6 | 1.9 | 2.0 |
| 80 percent | 2.5 | 4.0 | 5.0 |
| 90 percent | 3.1 | 6.4 | 10.0 |
| 95 percent | 3.5 | 9.1 | 20.0 |
| 99 percent | 3.9 | 13.9 | 100.0 |

Two conclusions follow.

1. Measure the parallel fraction before you write parallel code. If the fraction
   is 50 percent, no worker count gives more than twice the speed.
2. The table shows the best case. Real overhead makes every figure smaller.

Warning: the law ignores the cost to dispatch a task and to return a result. A
program that is 90 percent parallel can still run slower with 16 workers when
each task lasts one millisecond.

## Step 1. Record the environment

Save this output beside every result. A measurement without an environment is
not reproducible.

```powershell
python -c "import sys, os, platform; print(sys.version); print(platform.platform()); print('cores:', os.process_cpu_count())"
```

Also record whether the machine ran anything else. A benchmark on a busy laptop
produces noise that hides a real effect.

## Step 2. Measure the sequential baseline

Run the unmodified program on the representative workload. Record at least five
repeats. Report the median and the spread, never one run.

```python
import statistics
import time

durations = []
for _ in range(5):  # Repeat, because one run measures the noise as well
    start = time.perf_counter()
    run_sequential(workload)
    durations.append(time.perf_counter() - start)

print("median:", statistics.median(durations))
print("spread:", max(durations) - min(durations))
```

Use `time.perf_counter` for wall-clock time and `time.process_time` for
processor time. The difference between the two shows how much the program waits.

Warning: never compare a baseline from one machine against a candidate from
another machine. The comparison is meaningless.

## Step 3. Measure the scaling curve

Run the parallel candidate at 1, 2, 4, and 8 workers. Add the core count of the
machine if it is higher. Record this table.

| Workers | Median time | Speedup | Efficiency | Peak memory |
| - | - | - | - | - |
| 1 | | 1.00 | 100 percent | |
| 2 | | | | |
| 4 | | | | |
| 8 | | | | |

Compute the two derived columns:

- `speedup = sequential_time / parallel_time`
- `efficiency = speedup / worker_count`

Read the shape of the curve.

| Shape | Meaning | Action |
| - | - | - |
| Speedup rises near the worker count | The work parallelizes well | Keep the design |
| Speedup flattens early | Contention, or a large sequential part | Find the shared bottleneck |
| Speedup falls after a point | Overhead exceeds the gain | Lower the worker count |
| Speedup below 1 at every count | The dispatch cost exceeds the work | Return to sequential, or use larger batches |

Warning: the one-worker parallel run is not the sequential baseline. It carries
the pool overhead. Report both, because the difference measures that overhead.

## Step 4. Measure memory

Each process holds a separate interpreter and a separate copy of every imported
module. Report the peak total across all processes, not the peak of one process.

```python
import resource  # POSIX only. On Windows, read the peak working set instead.

usage = resource.getrusage(resource.RUSAGE_SELF)
children = resource.getrusage(resource.RUSAGE_CHILDREN)
print("peak self:", usage.ru_maxrss)
print("peak children:", children.ru_maxrss)
```

On Windows, read the peak working set of the process tree through the
performance counters, or use a memory profiler that supports child processes.

Warning: a design that gives twice the speed for eight times the memory usually
fails in a container. Check the memory limit of the deployment before you accept
the result.

## Step 5. Prove correctness

Speed without correctness is worthless. Run these three checks.

1. **Equality.** Compare the parallel result against the sequential result on
   the same input. Compare the values and the order.
2. **Repetition.** Run the parallel path many times. A race that appears once in
   a thousand runs still corrupts production data.
3. **Load.** Run the parallel path while the machine is busy. Contention changes
   the timing, and timing exposes a race.

```python
expected = run_sequential(workload)  # The reference answer
for attempt in range(200):  # One run cannot expose a timing defect
    actual = run_parallel(workload)
    assert actual == expected, f"Mismatch on attempt {attempt}"
```

Use property-based testing when the output is hard to compare directly. Assert
an invariant, such as a total that must not change.

## Step 6. Write the report

Include these ten sections.

1. **Objective.** The path, the workload, and the goal.
2. **Environment.** The interpreter version, the platform, and the core count.
3. **Bottleneck.** The measured cause, with the profile evidence.
4. **Parallel fraction.** The measured value, and the Amdahl bound.
5. **Model.** The chosen strategy, and one sentence on why.
6. **Scaling curve.** The full table from step 3.
7. **Memory.** The peak total for each worker count.
8. **Correctness.** The three checks, and their results.
9. **Failure behavior.** What happens on a worker failure, a cancellation, and a
   shutdown.
10. **Decision.** Keep the change or revert it, and the reason.

Link the raw results and the exact reproduction commands.

## Common measurement mistakes

| Mistake | Effect | Repair |
| - | - | - |
| One run for each configuration | The noise hides the effect | Repeat at least five times, and report the median |
| A synthetic workload only | The result does not transfer | Use representative inputs, or label the result exploratory |
| No warm start | The first run pays the import cost | Discard the first run, or report cold and warm separately |
| Comparing across machines | The comparison is invalid | Measure both sides on one machine |
| Reporting the mean of a noisy set | One outlier moves the mean | Report the median and the spread |
| Only one worker count | The curve stays unknown | Measure at least four counts |
| No memory figure | The design fails in a container | Report the peak total |
| No correctness check | A wrong answer arrives faster | Compare against the sequential result |

## When you cannot measure

Say so. Write **Hypothesis** beside the claim, and name the exact experiment
that would settle it.

Never write that parallel code is faster when you did not measure it. An
unmeasured parallel change adds risk with no proven benefit.
