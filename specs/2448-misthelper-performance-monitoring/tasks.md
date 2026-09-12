# MistHelper performance monitoring tasks

## T01: Add the event model

**Depends on:** None.

- Add typed event and source records.
- Match `contracts/performance-event.schema.json`.
- Reject unknown dimensions and negative measurements.

**Acceptance:** Unit tests validate good events and reject invalid events.

## T02: Add clocks and a disabled configuration

**Depends on:** T01.

- Add injectable wall and process CPU clocks.
- Use `perf_counter_ns` and `process_time_ns`.
- Disable monitoring by default.

**Acceptance:** Disabled monitoring changes no output and emits no event.

## T03: Add the bounded sink

**Depends on:** T01, T02.

- Add a bounded event queue and JSON Lines sink.
- Add a sink failure circuit and one drop counter.
- Bound event size and shutdown flush time.

**Acceptance:** Sink failures do not change an operation result.

## T04: Add privacy and cardinality controls

**Depends on:** T01.

- Add dimension allowlists and value buckets.
- Reject secrets, identifiers, paths, URLs, SQL text, and payload content.
- Limit dimensions to 16 and measurements to 32.

**Acceptance:** Tests prove that disallowed values never reach the sink.

## T05: Add root operation spans

**Depends on:** T02, T03, T04.

- Instrument the root CLI and portal boundaries from the hook catalog.
- Record wall time, process CPU time, status, item count, and error class.
- Preserve exceptions and cleanup.

**Acceptance:** A parent run correlates all enabled child events.

## T06: Add HTTP and Mist transport hooks

**Depends on:** T05.

- Instrument the exact transport symbols in `artifacts/hook-catalog.csv`.
- Count requests, retries, pages, bytes, items, and status classes.
- Separate response decoding from transport time.

**Acceptance:** A paged retry fixture produces correct nonoverlapping counts.

## T07: Add database event hooks

**Depends on:** T05.

- Register SQLAlchemy cursor, transaction, and pool events.
- Instrument ArangoDB, Redis, and SQLite wrappers.
- Normalize statement kind without retaining SQL text.

**Acceptance:** Disposable-store tests reconcile logical writes with physical operations.

## T08: Add file and serializer hooks

**Depends on:** T05.

- Instrument cataloged file and serializer boundaries.
- Count operations, rows, input bytes, and output bytes.
- Keep serialization and file time separate.

**Acceptance:** CSV and JSON fixture sizes reconcile with emitted byte counts.

## T09: Add cache hooks

**Depends on:** T05.

- Instrument hits, misses, populations, invalidations, and evictions.
- Record the configured entry or byte bound.
- Never record keys or values.

**Acceptance:** Cold, warm, invalidation, and eviction tests reconcile all outcomes.

## T10: Add profiler correlation

**Depends on:** T05.

- Add an opt-in `cProfile` runner.
- Map profile entries to the AST inventory.
- Report file, function, method, and class aggregates.

**Acceptance:** Every aggregate catalog row resolves to an inventory symbol.

## T11: Add memory and GC diagnostics

**Depends on:** T05.

- Add bounded `tracemalloc` sessions.
- Add separate RSS sampling.
- Add optional bounded GC callbacks with guaranteed cleanup.

**Acceptance:** Reports keep traced bytes, RSS, and GC counts separate.

## T12: Add startup and import benchmarks

**Depends on:** T02.

- Measure fresh process time to useful readiness.
- Capture `-X importtime` output.
- Measure deferred first use separately.

**Acceptance:** CLI and portal reports contain cold, warm, and first-use results.

## T13: Add Python and native sampling

**Depends on:** T10.

- Select Scalene or py-spy after a platform support check.
- Record tool versions, permissions, and attribution limits.
- Verify sequential native execution.

**Acceptance:** A report separates Python, native, system, and external wait costs.

## T14: Add benchmark workloads

**Depends on:** T06, T07, T08, T09.

- Build small, medium, and large sanitized fixtures.
- Add typical and worst-case variants.
- Add cold and warm state controls.

**Acceptance:** Each workload verifies an expected output outside the timed boundary.

## T15: Establish the baseline

**Depends on:** T10, T11, T12, T13, T14.

- Run uninstrumented timing, profile, memory, I/O, startup, and sampler sessions.
- Preserve commands, environment metadata, raw values, and source state.
- Record unrelated failures separately.

**Acceptance:** The baseline report contains median, spread, sample count, and raw artifact links.

## T16: Validate instrumentation overhead

**Depends on:** T15.

- Compare disabled, enabled-unsampled, and enabled-sampled states.
- Measure each subsystem and the complete workload.
- Reject hooks that exceed the specification budget.

**Acceptance:** Every retained hook meets its isolated and end-to-end overhead limits.

## T17: Run a bounded canary

**Depends on:** T16.

- Enable one subsystem in a controlled environment.
- Monitor event loss, sink failures, cardinality, memory, and latency.
- Verify the global disable switch.

**Acceptance:** The canary stays within resource and privacy limits.

## T18: Evaluate optimization hypotheses

**Depends on:** T15.

- Run benchmarks H-01 through H-06.
- Rank candidates by measured impact, confidence, and risk.
- Reject unmeasured or insignificant changes.

**Acceptance:** Each finding has evidence or the label `Hypothesis` with an exact next benchmark.
