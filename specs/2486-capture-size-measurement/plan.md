# Plan: Upgrade capture stored size measurement

## Measurement plan
Use a local benchmark harness in the session artifact folder. Import the module from `MISTHELPER_REPO_ROOT`. Assert that the imported file is inside the worktree.

## Workloads
- Medium write path with plain and driver fields.
- Large write path with plain and driver fields.
- Medium verification path with driver fields.
- Large verification path with driver fields.
- Edge size calculation.

## Timers
Use `time.perf_counter_ns()` for wall time. Use `time.process_time_ns()` for CPU time. Use 35 samples and 5 warmups.

## Memory plan
Use `tracemalloc` outside the timed loop. Record current and peak traced Python bytes.

## Change plan
Serialize the stable capture body once. Solve the `stored_size_bytes` digit width with arithmetic. Keep `measure_size_bytes()` and `_edge_size_bytes()` byte identical by relying on `ensure_ascii=True`.

## Risk plan
Compare the fast path with the old convergence loop. Test digit boundary sizes. Run the targeted unit and contract tests.
