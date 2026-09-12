# Monitor vocabulary

This file defines each monitor type in `artifacts/hook-catalog.csv`. A hook row
names one monitor type. That type states the tool, the clock, the metrics, and
the measured boundary.

Read this file before you implement a hook. Use the named monitor. Do not
replace a monitor with a different tool because that tool is easier to add.

## Rules for every monitor

1. Use `time.perf_counter_ns()` for elapsed wall time.
2. Use `time.process_time_ns()` for process CPU time.
3. Read each clock once at the start and once at the end of the boundary.
4. Keep the monitor off by default. One setting enables one monitor group.
5. Preserve the result, the exception, the cleanup, and the required log.
6. Emit one event for one boundary. Never emit an event for each loop pass.
7. Obey the privacy rule in the hook row. Use allowlisted labels only.
8. Measure timing in a run without a profiler and without allocation tracing.

## The monitor types

### operation_span

The monitor measures a named operation from entry through cleanup.

- Tool: the two nanosecond clocks.
- Metrics: `perf.wall_ns`, `perf.process_cpu_ns`, `perf.calls_total`,
  `perf.errors_total`, `work.items_total`.
- Use it for a command entry point, a request handler, or a task.
- Guard: do not time each internal function. Use cProfile for the split.
- Strategies: 1, 2, 7.

### stage_span

The monitor measures one named stage of a pipeline.

- Tool: the two nanosecond clocks and a fixed stage list.
- Metrics: `stage.wall_ns`, `stage.process_cpu_ns`, `stage.items_total`.
- Use it when one operation holds several ordered stages.
- Guard: keep at most one active stage timer for each run.
- Strategies: 1, 2, 7.

### compute_span

The monitor measures a solver or a calculation that does no input or output.

- Tool: the two nanosecond clocks.
- Metrics: `compute.wall_ns`, `compute.process_cpu_ns`, `compute.items_total`,
  `compute.iterations_total`.
- Use it for a route search, a tree solver, a loss calculation, or a difference
  calculation.
- Guard: keep database time and transport time outside this span.
- Strategies: 1, 3, 7.

### loop_counter

The monitor measures a complete loop and counts its passes.

- Tool: a local integer counter and the two nanosecond clocks.
- Metrics: `loop.iterations_total`, `loop.items_total`, `loop.wall_ns`,
  `loop.process_cpu_ns`, `loop.skipped_total`.
- Use it when a loop grows with the input size.
- Guard: increment an integer inside the loop. Read the clock outside the loop.
- Strategies: 7, 1, 4.

### database_events

The monitor registers engine events and reports each physical query.

- Tool: SQLAlchemy `before_cursor_execute`, `after_cursor_execute`, and
  `handle_error`. Use an equivalent event for another driver.
- Metrics: `db.query_wall_ns`, `db.queries_total`, `db.rows_total`,
  `db.transactions_total`, `db.pool_wait_ns`, `db.errors_total`.
- Use it once for each engine.
- Guard: store the start stamp in the execution context. Never retain SQL text.
- Strategies: 1, 2, 6.

### database

The monitor measures one logical database operation.

- Tool: the two nanosecond clocks around the repository call.
- Metrics: `db.wall_ns`, `db.process_cpu_ns`, `db.operations_total`,
  `db.rows_total`, `db.errors_total`.
- Use it to compare a logical read with the physical query count.
- Guard: do not duplicate a span for each physical query.
- Strategies: 1, 2, 3.

### http_transport

The monitor measures a request, a retry, and a page as separate stages.

- Tool: a transport hook in the shared client.
- Metrics: `http.wall_ns`, `http.requests_total`, `http.retries_total`,
  `http.pages_total`, `http.request_bytes`, `http.response_bytes`,
  `http.status_total`.
- Use it for every external service call.
- Guard: keep response decoding in the serializer monitor.
- Strategies: 2, 5, 6.

### cache

The monitor reports the result of each cache operation.

- Tool: a wrapper at the cache boundary.
- Metrics: `cache.operations_total`, `cache.hits_total`, `cache.misses_total`,
  `cache.populations_total`, `cache.invalidations_total`,
  `cache.evictions_total`, `cache.value_bytes`, `cache.wall_ns`.
- Use it for every read-through cache and every memoized result.
- Guard: never record a complete key or a value. Emit one aggregate event for a
  bulk deletion.
- Strategies: 6, 2, 5.

### serializer

The monitor measures encoding, decoding, and validation.

- Tool: the two nanosecond clocks at the serializer boundary.
- Metrics: `serial.wall_ns`, `serial.process_cpu_ns`, `serial.rows_total`,
  `serial.input_bytes`, `serial.output_bytes`.
- Use it for JSON, CSV, YAML, GeoJSON, and model validation.
- Guard: read the existing buffer length. Do not serialize a payload twice to
  obtain a size.
- Strategies: 5, 4, 1.

### file_io

The monitor measures one logical file operation.

- Tool: a wrapper at the file boundary.
- Metrics: `file.wall_ns`, `file.operations_total`, `file.bytes_total`,
  `file.errors_total`.
- Use it for a read, a write, an archive extraction, and a stream.
- Guard: count operations in a loop without a label for each entry.
- Strategies: 2, 4, 5.

### allocation_trace

The monitor reports traced Python memory for a bounded session.

- Tool: `tracemalloc` snapshots.
- Metrics: `mem.traced_current_bytes`, `mem.traced_peak_bytes`,
  `mem.blocks_total`, `mem.top_sites_json`.
- Use it where the code builds a large collection or copies a large structure.
- Guard: run it in a diagnostic session only. Measure timing in a separate run.
- Limit: the result is traced Python memory. It is not the process footprint.
- Strategies: 4, 3, 8.

### gc_diagnostic

The monitor reports cyclic collection cost for a bounded session.

- Tool: `gc` callbacks.
- Metrics: `gc.collections_total`, `gc.collected_total`,
  `gc.uncollectable_total`, `gc.pause_wall_ns`, `gc.tracked_objects`.
- Use it for a large population of small records and for a large object graph.
- Guard: save the enabled state and the thresholds. Restore both in a `finally`
  block on every path.
- Strategies: 8, 4, 3.

### startup_import

The monitor measures a fresh process to useful readiness.

- Tool: the two nanosecond clocks and `python -X importtime` in a separate run.
- Metrics: `startup.wall_ns`, `startup.process_cpu_ns`,
  `startup.import_self_ns`, `startup.import_cumulative_ns`,
  `startup.modules_total`, `startup.first_use_wall_ns`.
- Use it for each entry point.
- Guard: do not run `importtime` in normal service operation. Measure the
  deferred first use separately.
- Strategies: 9, 4, 10.

### native_boundary

The monitor measures a crossing into compiled code.

- Tool: the two nanosecond clocks around the crossing.
- Metrics: `native.wall_ns`, `native.process_cpu_ns`, `native.calls_total`,
  `native.input_items`, `native.output_items`.
- Use it for a geometry call, a compiled parser, and a compiled client.
- Guard: verify documented sequential execution before a comparison. Do not
  enable a hidden thread pool or a device path.
- Strategies: 10, 1, 3.

### subprocess_span

The monitor measures a child process from start through exit.

- Tool: the parent nanosecond clocks.
- Metrics: `proc.wall_ns`, `proc.process_cpu_ns`, `proc.calls_total`,
  `proc.exit_total`.
- Use it for an external command.
- Guard: record an approved operation name. Never label the command text.
- Strategies: 2, 10, 9.

### cProfile correlation

The monitor gives call attribution without a production event.

- Tool: `cProfile` and `pstats`, joined to `artifacts/python-inventory.csv`.
- Metrics: `profile.call_count`, `profile.primitive_call_count`,
  `profile.total_time_ns`, `profile.cumulative_time_ns`.
- Use it for every symbol that needs per-function attribution and no permanent
  timer.
- Guard: do not add a local timer to this symbol. Use a separate run without a
  profiler for the acceptance timing.
- Strategies: 1, 3, 4, 5, 7.

## The strategy map

`artifacts/strategy-coverage.csv` reports the hook count, the file count, and
the monitor types for each of the ten optimization strategies. Read that file to
confirm that a strategy has enough evidence before you rank a candidate.

| Strategy | Monitors that supply its evidence |
| --- | --- |
| 1 algorithms and repeated work | `compute_span`, `loop_counter`, `cProfile correlation` |
| 2 input and output counts | `database_events`, `http_transport`, `file_io`, `database` |
| 3 data structures | `cProfile correlation`, `compute_span`, `allocation_trace` |
| 4 allocations and copying | `allocation_trace`, `loop_counter`, `serializer` |
| 5 serialization and validation | `serializer`, `http_transport`, `cache` |
| 6 bounded caching | `cache`, `database_events`, `http_transport` |
| 7 measured Python loops | `loop_counter`, `compute_span`, `cProfile correlation` |
| 8 object layout and collection | `gc_diagnostic`, `allocation_trace` |
| 9 startup and imports | `startup_import` |
| 10 native acceleration | `native_boundary`, `subprocess_span` |

## What a hook does not do

A hook finds a candidate. A hook does not prove an improvement.

Measure a candidate change against the unmodified baseline with the same inputs
and the same settings. Keep the raw baseline artifact. Retain a change only when
it meets the acceptance threshold in `spec.md`.
