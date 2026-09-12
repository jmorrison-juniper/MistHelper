# Python performance report template

Use all twelve sections below for a completed optimization task. Replace the
guidance with actual evidence. This template contains no benchmark results.

Label every finding **Measured**, **Hypothesis**, **Rejected**, or **Blocked**.
Use **Not measured** for an unavailable metric and explain why. Never use zero
as a substitute for a missing measurement.

## 1. Executive summary

State the objective, representative workload, retained changes, and measured
result. State whether the acceptance criteria passed. Distinguish isolated
improvements from end-to-end improvements. If no change qualifies, say so.

Confirm that application parallelization remained out of scope.

## 2. Environment and Python version

Record the Python executable, implementation, exact version, build, and virtual
environment. Record the operating system, architecture, CPU, power mode,
container or WSL status, and relevant background load.

Record dependencies, tool versions, service versions, and relevant indexes.
Record baseline and candidate source revisions, local changes, and harness
revision. Do not include credentials or sensitive environment values.

## 3. Benchmark methodology

State the entry point, input provenance, sizes, distribution, expected output,
and measured boundary. Explain why the workload represents real use.

Record cold and warm states, cache reset policy, mutable-input reset, output
consumption, logging, GC, calibration, warmups, runs, values, and loop counts.
State the time and resource budget, exact commands, and artifact paths.

Name timers and memory metrics. Explain tool limitations, instrumentation
overhead, noise controls, and the predefined acceptance criteria.

## 4. Baseline results

Record the unmodified workload before discussing a candidate.

| Workload and state | Metric and unit | Median | MAD or IQR | Runs and values | Evidence artifact |
| --- | --- | --- | --- | --- | --- |

Include wall time, CPU time, single-worker throughput, traced memory, process
memory, allocation volume, query counts, I/O counts, or serialized bytes as
relevant. Label unavailable measurements explicitly.

Record the baseline tests and any existing failures or skipped tests.

## 5. Ranked hotspot list

| Rank and status | File, symbol, and lines | Measured cost and frequency | Expected gain | Risk and maintenance cost | Confidence |
| --- | --- | --- | --- | --- | --- |

State the measured contribution to the complete workload. Separate Python CPU,
native work, serialization, external waiting, startup, and unattributed time.
Explain the ranking without adding overlapping cumulative times.

## 6. Recommended optimizations

For each recommendation, state the evidence, root cause, smallest safe change,
expected effect, and required benchmark. Record current and proposed complexity
when relevant. Explain semantic, memory, invalidation, and deployment risks.

Keep unmeasured recommendations under **Hypothesis**. Give the exact workload,
command, metric, and decision criterion needed to test each hypothesis.

## 7. Implemented changes

Repeat this record for each implemented concern. If none qualify, write
"No optimization was retained" and explain the decision.

| Field | Required content |
| --- | --- |
| Change ID and location | Record a stable ID, exact path, symbol, line range, and source revision. |
| Evidence | Link the profile, benchmark, representative input, and raw results. |
| Root cause | Explain the measured cost and current complexity where relevant. |
| Change | Describe the smallest retained change and proposed complexity. |
| Before result | Record the workload, metric, unit, median, spread, and sample count. |
| After result | Record the equivalent candidate measurement. |
| Percentage change | Show the signed change, formula, and practical effect. |
| Memory change | Name the memory metric, before and after values, and absolute difference. |
| Test coverage | Name the added or updated tests, edge cases, and executed results. |
| Risks | Explain semantic, operational, maintenance, and deployment risks. |
| Confidence level | State high, medium, or low confidence and the evidence for it. |
| Retention decision | Name the acceptance criterion and explain why the change qualifies. |

## 8. Before-and-after measurements

| Change and workload | Metric and unit | Before median and spread | After median and spread | Sample counts | Signed change | Decision |
| --- | --- | --- | --- | --- | --- | --- |

Use `100 * (after - before) / before` for the signed percentage change.
For latency, CPU time, bytes, and counts, a negative value means a reduction.
For throughput, a positive value means an increase. State this direction next
to the result. If the baseline is zero, report the absolute change and mark the
percentage undefined.

If reporting a positive time reduction, use
`100 * (before - after) / before` and label it **Time reduction**. Do not mix
this value with a speedup ratio or throughput increase.

Report medians with MAD or IQR and the raw sample count. Record runs, loops, and
warmups separately. Include repeat collections, instability warnings,
significance results, and the observed uncertainty.

Show the important end-to-end result as well as the isolated result. Report
regressions and insignificant changes. Do not report only the fastest sample.

## 9. Memory impact

Record current and peak traced Python bytes separately from RSS, private memory,
or commit charge. State the platform, method, and measurement interval.

Record the absolute byte change, retained objects, cache bounds, and sustained
growth when applicable. Distinguish net live allocations from allocation churn.
Include conversion buffers and native allocations that the Python tracer misses.

Explain any speed-versus-memory trade-off against the original budget.

## 10. Correctness and regression validation

| Check | Command or test | Actual result | Limitation or artifact |
| --- | --- | --- | --- |

Cover functional outputs, types, ordering, duplicates, boundaries, malformed
inputs, numeric extremes, Unicode, exceptions, cleanup, and required logs as
applicable. Cover authorization, freshness, protocol, and storage invariants.

Record unit, integration, property, and end-to-end tests where relevant. Record
the required syntax, lint, format, type, and security checks. Separate passed,
failed, skipped, and blocked checks. A skipped check is not a pass.

Explain regressions outside the target path and how the final result resolves
them. State which supported Python versions and platforms you actually tested.

## 11. Rejected ideas and why they were rejected

| Idea and location | Evidence | Reason for rejection | Reverted or never implemented |
| --- | --- | --- | --- |

Include unstable gains, insignificant effects, unsafe caching, compatibility
changes, excessive complexity, cold-code rewrites, and unjustified native builds.
Explain workload-specific gains that lack operational value.

Confirm that you reverted only your own changes when rejecting a candidate.

## 12. Remaining opportunities

| Opportunity and status | Missing evidence or blocker | Exact next benchmark | Expected value and risk |
| --- | --- | --- | --- |

State the next safe measurement and the inputs or permissions it needs.
Keep unavailable evidence visible. Do not turn hypotheses into speed claims.
