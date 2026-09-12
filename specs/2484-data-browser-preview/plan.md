# Plan: Data browser preview memory use

## Objective
Measured: Optimize one sequential data browser preview path.
Peak traced Python memory is the primary objective.
Request latency is a secondary guard metric.

## Workload
Measured: The harness creates disposable fixtures under the session artifact directory.
Measured: It previews a 60,000-row CSV, an 80,000-line log, and a 25,000-line JSON Lines file.
Measured: It uses five warmups and 31 samples for each timing target.
Measured: It measures wall time with `time.perf_counter_ns()`.
Measured: It measures CPU time with `time.process_time_ns()`.
Measured: It measures peak traced Python memory with `tracemalloc` outside the timed loop.

## Change plan
1. Replace full CSV row materialization with streamed page collection.
2. Replace full log line materialization with streamed page collection.
3. Keep JSON column order while formatting only rows that can appear in a response.
4. Keep the full response dictionary stable with a parity harness.
5. Add unit tests for pagination, filtering, JSON Lines, and column order.

## Risk controls
Measured: The harness compares complete response dictionaries before and after the change.
Measured: Unit tests cover page clamping, search, JSON Lines fallback, and path safety.
Hypothesis: Some CSV and JSON Lines wall times can increase because the optimized path avoids allocation with more Python loop work.
