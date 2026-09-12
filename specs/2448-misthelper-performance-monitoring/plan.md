# MistHelper performance monitoring plan

## Design

Implement one shared performance event API.
Keep the API disabled by default.
Use it only at cataloged production boundaries.

Use a run context to correlate parent operations, transport calls, database work, file work, and serializer work.
Use `cProfile` to attribute the uncataloged nested calls within that context.
Use a separate benchmark run for timing acceptance.

## Components

### Event model

Create a typed event record that follows `contracts/performance-event.schema.json`.
Store integer nanoseconds and byte counts.
Validate dimensions against an allowlist before emission.

### Clock provider

Use `time.perf_counter_ns()` for elapsed wall time.
Use `time.process_time_ns()` for process CPU time.
Inject clocks in tests.

### Sink

Write bounded JSON lines or send bounded metrics to the existing monitoring path.
Use a fixed queue limit.
Drop performance events after the limit and increment one drop counter.
Do not block the primary operation.

### Span API

Provide a context manager for selected operation boundaries.
Provide explicit counters for requests, retries, pages, rows, bytes, cache outcomes, and database operations.
Do not provide a decorator that instruments all functions.

### Correlation

Assign one run-local identifier to a parent workload.
Attach child events to that identifier.
Map `cProfile` records to `artifacts/python-inventory.csv` by file and qualified symbol.

## Instrumentation layers

### Layer 1: operation spans

Instrument CLI dispatch, portal operation execution, metrics collection, synchronization, capture, upgrade, and SSH execution.
Record wall time, process CPU time, item count, status, and error class.

### Layer 2: resource boundaries

Instrument HTTP, Mist, WebSocket, SSH, database, file, serializer, and cache boundaries.
Keep child stages nonoverlapping.
Count logical and physical operations separately.

### Layer 3: profiler attribution

Run `cProfile` around a complete workload.
Use the inventory to report file, function, method, and class totals.
Do not enable this layer in normal production operation.

### Layer 4: diagnostic memory and GC

Run `tracemalloc`, RSS sampling, and GC callbacks in separate bounded sessions.
Record the tool and method with each result.
Remove every diagnostic callback during cleanup.

### Layer 5: startup and native sampling

Use fresh process timing and `-X importtime` for startup.
Use Scalene or py-spy for Python and native attribution.
Use only a supported tool configuration.

## Implementation order

1. Add the event model, clocks, privacy filter, and disabled configuration.
2. Add the bounded sink and failure circuit.
3. Add operation spans at the root dispatch and portal middleware.
4. Add HTTP transport, retry, page, and byte counters.
5. Add SQLAlchemy and backend database events.
6. Add file and serializer child stages.
7. Add cache outcome and eviction counters.
8. Add the profiler correlation exporter.
9. Add bounded memory, RSS, GC, startup, and sampler commands.
10. Add representative benchmark fixtures and reports.

## Benchmark design

Use the workload matrix in `spec.md`.
Use sanitized fixed fixtures and disposable stores.
Verify outputs outside the timed boundary.
Consume lazy results inside the measured boundary when production consumes them.

Use at least three independent collections when practical.
Report the median, MAD or IQR, sample count, warmup count, and tool warnings.
Preserve raw baseline and candidate artifacts under a task-specific performance directory.

Keep these runs separate:

- Uninstrumented wall and process CPU timing.
- `cProfile` attribution.
- `tracemalloc` current and peak bytes.
- Process RSS.
- SQL, HTTP, and file operation counts.
- `-X importtime`.
- Native and Python sampling.

## Overhead controls

- Disable all hooks by default.
- Sample successful high-frequency events.
- Keep all failures, retries, and slow events.
- Use fixed dimension names and coarse value buckets.
- Bound queues, cache metadata, event sizes, and shutdown flush time.
- Do not inspect payload content.
- Do not calculate metric labels from user or tenant data.
- Do not add permanent timers to aggregate-only files.

## Rollout

Start with a local benchmark sink.
Enable one subsystem at a time.
Measure enabled and disabled overhead before the next subsystem.
Reject a hook that fails its overhead budget.

After local validation, enable a bounded canary configuration.
Compare event loss, sink failures, label counts, and application latency.
Keep a single configuration switch that disables all performance monitoring.

## Deliverable map

| File | Purpose |
| --- | --- |
| `spec.md` | Requirements, workload contract, hypotheses, and acceptance. |
| `research.md` | Scan method, findings, tool choices, and checklist coverage. |
| `plan.md` | Architecture, sequence, overhead controls, and rollout. |
| `tasks.md` | Implementation slices with dependencies and acceptance. |
| `quickstart.md` | Reproduction and validation commands. |
| `data-model.md` | Event, run, workload, and artifact records. |
| `checklists/requirements.md` | Requirement review checklist. |
| `contracts/performance-event.schema.json` | Machine-readable event contract. |
| `artifacts/python-inventory.csv` | One file row with all AST symbols. |
| `artifacts/hook-catalog.csv` | Exact production and aggregate measurement targets. |
| `artifacts/scan-summary.json` | Exact counts, roots, errors, and exclusions. |
| `issue.md` | Self-contained parent issue body. |
